# PROGRESS — CAGI-ED SOC Dashboard, Phần 1

## Giai đoạn 0 — Audit
- [x] `AUDIT.md` viết xong (đọc repo, bảng data item có/không sẵn).
- [x] Quyết định: KHÔNG có OOF per-prefix/SHAP cho 36 incident sẵn trên
  đĩa → cần 1 script sinh dữ liệu mới (`scripts/dashboard/generate_oof_dashboard_data.py`),
  tái sử dụng nguyên vẹn `evaluate_model_nested` + mẫu SHAP fold-specific
  đã có (`scripts/generate_alert_case_studies.py`).

## Giai đoạn 1 — Kiến trúc
- [x] Chọn: React + TS + Tailwind v4 + Recharts + React Flow + Lucide,
  build static, FastAPI phục vụ (localhost only). Lý do: repo không có
  frontend sẵn, đúng gợi ý của yêu cầu, toolchain Node/Python đã có sẵn
  trong môi trường.

## Giai đoạn 2 — Sinh dữ liệu thật (Bước 0.5)
- [x] `scripts/dashboard/generate_oof_dashboard_data.py` — chạy LOIO
  (`LeaveOneGroupOut`, 36 fold) cho M1 và B3' (36 fold × 2 model), kèm
  inner-fold threshold selection + Platt (giống hệt `evaluate_model_nested`),
  cộng XGBoost `pred_contribs` (SHAP) cho mỗi dòng test trong fold đó.
- [x] Xác nhận pooled PR-AUC khớp CHÍNH XÁC kết quả đã có trước đó
  (M1=0.7790, B3'=0.7271 — trùng với `v4_pooled_loio_summary.csv` đã
  tính trong phiên làm việc trước) — xác nhận không có sai lệch logic.
- [x] **Bug thật phát hiện qua smoke-test** (`bsc_token_hub_2022`): lần
  đầu lọc theo `group_id` khi lắp ráp JSON per-incident — SAI, vì 1
  group gồm CẢ positive LẪN hàng chục hard-negative đã mine (source_id
  riêng, cùng group_id). Đã SỬA: lọc thêm `source_id==group_id AND
  kind=="positive"`. Thêm cache pickle cho bước LOIO+SHAP (tính toán
  nặng) để sửa lỗi lắp ráp JSON mà không cần chạy lại toàn bộ LOIO.
- [x] Chạy lại sau khi sửa — xem log `generate_oof_dashboard_data.py`.

## Giai đoạn 3 — Backend
- [x] `dashboard/backend/app.py` — FastAPI, CHỈ đọc `data/dashboard/incidents.json`
  (không tính toán, không gọi mạng), bind `127.0.0.1`. Endpoint:
  `/api/meta`, `/api/incidents`, `/api/incidents/{id}`, `/api/new-analysis`
  (trả `enabled: false`, dùng cho Phần 2), `/healthz`.

## Giai đoạn 4 — Frontend
- [x] Scaffold Vite + React + TS.
- [x] Design system: màu/token theo đúng bảng màu yêu cầu (`tailwind.config.js`).
- [x] Shell: Sidebar (6 mục nav, đều hoạt động), Header, `ThetaContext`
  (theta/model chọn 1 lần, dùng xuyên suốt app — KHÔNG tính lại điểm số,
  chỉ đổi ngưỡng so sánh).
- [x] Overview: KPI card tính từ dữ liệu đã phân loại (`classify.ts`),
  donut chart, incident library có thể click vào Investigation.
- [x] Incidents: tìm kiếm, lọc theo chain/outcome.
- [x] Investigation: 5 tab (Overview/Timeline/Flow Graph/SHAP/AADAPT)
  đúng layout trong ảnh tham khảo — biểu đồ p̂_k (M1 + B3', θ selector,
  marker first-alert/exit), 4 summary card (First Alert/Exit
  Point/Lead Time/AADAPT) xử lý đủ 5 trạng thái (Early/Late/Not
  Feasible/No Alert/No Exit), timeline action, flow graph (React Flow,
  layout lưới đơn giản).
- [x] Explainability: tổng hợp tần suất AADAPT technique trên các alert
  thật, link ngược về Investigation.
- [x] New Analysis: trạng thái "chưa bật" rõ ràng, gọi `/api/new-analysis`.
- [x] Settings: model mặc định + theta mặc định (có tác dụng thật qua
  `ThetaContext`), hiển thị theta_frozen đã lưu.
- [x] Build production (`npm run build`) — pass sau khi sửa lỗi TS
  (2 biến không dùng) + Tailwind v4 (cần `@tailwindcss/postcss` +
  `@import "tailwindcss"` thay vì `@tailwind base/...`).

## Giai đoạn 5 — QA
- [x] `tests/test_dashboard_api.py` — chặn socket.connect trong lúc xử
  lý request (xác nhận Mode A không gọi mạng), đối chiếu response API
  với file JSON gốc, test 404/empty-state.
- [x] `tests/test_dashboard_classification.py` — đối chiếu logic phân
  loại outcome (bản Python, dùng để kiểm tra lại định nghĩa) với dữ
  liệu đã lưu — not_feasible khi e*<=2, not_evaluable khi chưa xác
  nhận endpoint, theta tăng thì k alert không giảm.
- [ ] Playwright (nếu cài được) — chụp screenshot từng màn hình, kiểm
  tra console error. Xem báo cáo cuối để biết kết quả thật.
- [ ] Chạy lại TOÀN BỘ `pytest tests/` (244 test cũ + test mới) — xem
  báo cáo cuối.

## Giai đoạn 5 (tiếp) — Bug thật phát hiện qua Playwright + đã sửa
- **Bug 1 (dữ liệu)**: `bsc_token_hub_2022` ban đầu hiển thị 70+ điểm
  trùng lặp trên biểu đồ p̂_k vì script sinh dữ liệu lọc theo `group_id`
  (gồm cả hard-negative) thay vì `source_id==group_id & kind=="positive"`.
  Đã sửa + thêm cache LOIO/SHAP để sửa mà không cần chạy lại toàn bộ
  tính toán.
- **Bug 2 (backend)**: route `/investigation/:id` trả 404 JSON thay vì
  SPA — `StaticFiles(html=True)` không tự fallback cho client-side
  route. Đã sửa bằng catch-all route trả `index.html`.
- **Bug 3 (UI copy)**: card "Lead Time" hiện sai "Không có exit quan sát
  được" cho case `not_feasible` (exit THẬT SỰ có quan sát được, chỉ là
  e*≤2 nên không tính lead time được) — đã sửa message phân biệt rõ
  4 lý do N/A.
- Đã xác nhận qua Playwright: **0 console error** trên toàn bộ 10+3
  screenshot (5 trang chính + 5 tab Investigation của `bsc_token_hub_2022`
  + 3 tab bổ sung của `chibi_finance_2023` để xem case "Early" thật).
- **Phát hiện thật đáng chú ý (không phải lỗi)**: trên CẢ 36 incident ở
  θ=0.5/M1, KHÔNG incident nào có AADAPT ID trong top-3 SHAP tại điểm
  alert — top-3 luôn là feature cấu trúc/thời gian (`path_depth`,
  `log_amount_mean`, `active_duration_sec`...), không phải feature
  `motif_*`. Trang Explainability vì vậy hiện trạng thái rỗng trung
  thực, không phải bug hiển thị.

## Việc còn lại / rủi ro đã biết
- File `data/dashboard/incidents.json` ~26MB (do vài incident rất dài,
  vd `easyfi_2021` 16560+ action) — chấp nhận được cho demo local,
  không tối ưu thêm trong phạm vi Phần 1.
