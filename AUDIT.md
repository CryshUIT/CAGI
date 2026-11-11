# AUDIT — CAGI-ED Web Dashboard, Part 1 (historical 36 incidents)

Ngày: 2026-11-10. Audit đọc-only trên repo hiện tại, không sửa pipeline.

## 1. Chạy project / test

- Pipeline: Python 3.13, `pip install -r requirements.txt` (nếu có) hoặc
  các package import trực tiếp: pandas, numpy, scikit-learn, xgboost,
  pydantic, requests, python-dotenv.
- Test: `pytest tests/ -v` — **244 test hiện có, tất cả pass** (xác nhận
  lần chạy gần nhất trong phiên làm việc này, 2026-11-05).
- Không có frontend/web nào đang chạy được trong repo — `demo/` (được
  tham chiếu bởi `scripts/build_demo_data.py`) **không tồn tại trên
  đĩa** (có script sinh dữ liệu nhưng chưa từng chạy/output đã bị xoá).
  Đây là static HTML/JS demo đời cũ (N=15, 1 case positive + 1
  hard-negative), KHÔNG phải dashboard cho N=36 hiện tại — chỉ dùng làm
  **tham khảo phương pháp** (xem mục 3).

## 2. Entry point pipeline (đọc-only, KHÔNG sửa)

| Bước | File |
|---|---|
| Collect (on-chain) | `src/collect/etherscan_client.py`, `src/collect/bsctrace_client.py` |
| Decode | `src/normalize/decoder.py` |
| Trace/trajectory | `src/trajectories/builder.py`, `src/pipeline/incident_pipeline.py::expand_and_build_trajectory` |
| Feature extraction | `src/features/extractor.py::extract_features`/`extract_all_prefixes`/`generate_prefixes` |
| Model (XGBoost) | `src/models/baselines.py::M1TypedTemporalMotifModel`, `B3FlatGraphRandomForest` (B3' = `XGBFixedColumns` định nghĩa trong `scripts/run_extra_N30_exploratory.py` / `scripts/n30_extra/extra_v4/_freeze_final_B3prime_N36.py`) |
| LOIO + Platt + ngưỡng | `src/evaluation/nested_eval.py::evaluate_model_nested`, `select_threshold`, `_fit_calibrator`/`_apply_calibrator` |
| TreeSHAP (pred_contribs) | Mẫu đã có sẵn: `scripts/generate_alert_case_studies.py::get_contribs` (dùng `booster.get_booster().predict(dmat, pred_contribs=True)`, model **fold-specific**, không dùng model cuối) |
| AADAPT mapping | `src/features/aadapt_mapping.py::get_aadapt_ids`/`format_aadapt_ids` — 7 technique ID, ánh xạ tĩnh từ tên feature motif/`action_count_mixer_or_exit*` |

## 3. Bảng data item — có sẵn hay không

| Data item | Có sẵn? | Path | Màn hình cần |
|---|---|---|---|
| OOF per-prefix (36 incident, bucket ratio_25/50/75/100+k_2/3/5/7) cho M1 | **KHÔNG** (chỉ có `results/oof/oof_M1.parquet` cho **30** incident cũ, N30, chưa gồm 6 incident N37 mới) | — | Investigation (biểu đồ p_k) |
| OOF per-prefix cho B3' | **KHÔNG** (tương tự, `oof_B3prime.parquet` chỉ N30) | — | Investigation |
| Timestamp từng action + e\* (action thứ mấy là endpoint) | **CÓ** (gián tiếp — tự tính từ `data/processed/{incident_id}_events.json`, field `event_type`+`timestamp`, endpoint = action đầu tiên có `event_type` ∈ {bridge_deposit, mixer_or_exit, lending_deposit}) | `data/processed/*_events.json` | Investigation, Explainability |
| TreeSHAP cho alert cụ thể, model fold-specific (không phải model final) | **KHÔNG CÓ SẴN Ở DẠNG FILE** — chỉ có SCRIPT làm việc này cho đúng 2 case cụ thể (`scripts/generate_alert_case_studies.py`), chưa chạy cho 36 incident | — | Explainability |
| AADAPT mapping | **CÓ**, đầy đủ, dạng hàm Python thuần | `src/features/aadapt_mapping.py` | Explainability |
| Decoded actions (tx hash, timestamp, from/to, token, amount, loại action, protocol) | **CÓ** cho mọi incident đã thu thập | `data/processed/{incident_id}_events.json` | Investigation (timeline + flow graph) |
| Incident metadata (chain, seed, start_block, endpoint_confirmed) | **CÓ** | `metadata/incident_registry_N37.csv` | Overview, Investigation |
| Outcome label chính thức (Early/Late) | **KHÔNG CÓ SẴN dạng bảng** — định nghĩa (so sánh `alert_prefix_len` tương ứng thời điểm so với e\*) tồn tại dưới dạng CODE trong `scripts/n30_extra/run_lead_time_by_threshold_N30.py` / `scripts/n30_extra/extra_v4/_run_evaluation_v4.py` (status: `detected_before_endpoint`/`late_detection`/`never_alerted`), KHÔNG có bảng kết quả đã lưu cho toàn bộ 36 incident ở 1 ngưỡng cố định | — | Overview (KPI), Investigation |
| Lead time đã tính sẵn (N=15 cũ) | CÓ nhưng LỖI THỜI (N=15, không phải N=36) | `results/tables/lead_time_results.csv` | — (không dùng) |

### Quyết định bắt buộc (ghi rõ, không suy luận ngầm)

Vì KHÔNG có OOF per-prefix + outcome label + SHAP cho 36 incident hiện
tại dưới dạng file sẵn, và dashboard không thể hoạt động nếu thiếu
hoàn toàn các mục cốt lõi này, **Bước 0.5** của việc build dashboard là
chạy MỘT SCRIPT MỚI (`scripts/dashboard/generate_oof_dashboard_data.py`)
tái sử dụng NGUYÊN VẸN:
- `evaluate_model_nested(...)` (`src/evaluation/nested_eval.py`) — ĐÚNG
  hàm LOIO + Platt + chọn ngưỡng đã dùng xuyên suốt dự án (không đổi
  tham số, không đổi target_fpr=0.01, không đổi seed=42).
- Mẫu "fold-specific model + `pred_contribs`" từ
  `scripts/generate_alert_case_studies.py` (lặp lại CHÍNH XÁC
  `LeaveOneGroupOut` + `model.fit()` + `booster.predict(pred_contribs=True)`,
  không đổi logic).
- `get_aadapt_ids()` nguyên vẹn.

Đây KHÔNG phải train lại mô hình để triển khai (không tạo ra model mới
dùng để dự đoán incident tương lai), KHÔNG phải "mock" hay "shortcut" —
là chạy lại đúng 1 lần quy trình đánh giá CHÍNH THỐNG đã dùng cho mọi
bảng kết quả trong dự án, rồi LƯU LẠI kết quả per-row (trước đây các
script khác chỉ lưu bản tóm tắt, không lưu chi tiết từng dòng). Toàn bộ
mã nguồn, log chạy, và file kết quả được lưu minh bạch, có thể audit
lại. KHÔNG dùng `M1_FROZEN_final_N36.pkl`/`B3prime_FROZEN_final_N36.pkl`
(model đã thấy cả 36 incident) để hiển thị kết quả "out-of-fold" —
2 file đó CHỈ dùng cho incident hoàn toàn mới (Phần 2, chưa bật).

## 4. Phạm vi 36 incident "historical"

= 30 incident `eval_tier=primary` (N30 gốc) + 6 incident
`eval_tier=v4_heldout` ĐÃ DÙNG ĐỂ TRAIN model đóng băng (N37, trừ
`fortress_protocol_2022` bị loại do lỗi thu thập thật — xem
`results/reports/extra_v4/decision_log_2026-11-04.md`). Đây CHÍNH LÀ
tập 36 group dùng để train `M1_FROZEN_final_N36.pkl`/
`B3prime_FROZEN_final_N36.pkl` — khớp đúng "36 incident, out-of-fold"
yêu cầu của prompt.

4 incident trong `results/reports/extra_v4/decision_log_final_heldout_2026-11-05.md`
(rari_capital_fuse_2022, curve_crv_eth_attacker_2023, pancakebunny_2021,
rikkei_finance_2022) là final held-out TEST set (model đã đóng băng dự
đoán, KHÔNG phải out-of-fold) — **KHÔNG thuộc Part 1**, sẽ thuộc Part 2
("New Analysis") nếu được bật sau.

## 5. Kết luận kiến trúc

Repo hiện KHÔNG có frontend nào sẵn có phù hợp để tái sử dụng — xây mới
theo đúng gợi ý của prompt: React + TypeScript + Tailwind + Lucide +
Recharts (+ React Flow cho flow graph) build ra static files, phục vụ
bởi FastAPI (Python, đã có sẵn trong toolchain môi trường này). Dữ liệu
đọc từ JSON tĩnh sinh 1 lần (Bước 0.5) — API chỉ đọc file, KHÔNG tính
toán lại, KHÔNG gọi mạng.
