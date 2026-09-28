# Tổng hợp các nỗ lực cải thiện M1 (0,6624) — 2026-09-22 (cập nhật 2026-09-26, ĐÃ ĐÓNG TRACK VĨNH VIỄN)

M1 chính thức (mốc dùng cho RQ1/main results, XGBoost, N=15 incident, nested LOGO):
**mean PR-AUC (pooled) = 0,6624, 95% CI = [0,5234, 0,8864]**.

Tài liệu này tổng hợp toàn bộ **13 hướng đã chạy** (+ 1 đề xuất bị hủy trước khi chạy vì tiền đề sai —
xem mục "Đề xuất bị hủy") để cải thiện M1 một cách hợp lệ (mọi quyết định điều chỉnh — hyperparameter,
ngưỡng, chọn feature, trọng số ensemble, dữ liệu train bổ sung — chỉ dùng inner-CV/inner-train, không
bao giờ chạm outer test fold). Dùng làm nguồn cho phần Discussion/Limitations của bài NSS 2026.

**QUAN TRỌNG cho phần viết bài**: nếu bất kỳ con số nào trong 13 attempt này được trích dẫn trong bài
báo (kể cả các con số "gần cải thiện" như attempt #11), PHẢI nêu rõ đây là **1 trong 13 lần thử đã
pre-register trong quá trình nghiên cứu** (ví dụ: "the Nth of 13 attempts") — không trình bày như một
phát hiện độc lập, để tránh đánh lừa reviewer về mức độ multiple-comparison đã thực hiện.

**Kết luận chung: không có hướng nào cải thiện M1 một cách có ý nghĩa thống kê VÀ vượt trội so với
lựa chọn thay thế đơn giản hơn (T13 LogReg dùng riêng).** Baseline M1 gốc (0,6624) được giữ nguyên
làm mô hình chính thức của bài báo.

**🔒 TRACK "CẢI THIỆN M1" ĐÓNG NGÀY 2026-09-26 SAU ATTEMPT #13** — dừng theo phán đoán của Claude Code
(được người dùng trao toàn quyền tiếp tục hoặc dừng): attempt #13 cho thấy dấu hiệu suy giảm lợi ích rõ
rệt (kết quả tệ hơn cả #11, và bộc lộ giới hạn cấu trúc của chính phương pháp nested-CV khi áp dụng cho
pathology hiếm — xem chi tiết attempt #13) — tiếp tục thử thêm biến thể của "thêm dữ liệu unmatched" khó
có khả năng cho kết quả khác biệt về chất. Chuyển toàn bộ thời gian còn lại sang viết bài (còn 4 ngày
đến hạn nộp NSS 2026).

## Bảng tổng hợp

| # | Hướng thử | Mean PR-AUC (pooled) | Paired diff vs M1 gốc (95% CI) | Kết luận |
|---|---|---|---|---|
| 1 | Nested hyperparameter tuning (7 candidate: depth/lr/n_estimators/scale_pos_weight) | 0,6062 [0,4811; 0,8711] | −0,0647 [−0,1650; +0,0061] | Không cải thiện (CI chứa 0, điểm ước lượng còn tệ hơn) |
| 2 | Điều tra `hackerdao_2022` (incident tệ nhất, 0,5053) — tìm lỗi decode hệ thống | — (không đổi model) | — | Phát hiện lỗi decode boundary thật (5 giao dịch bị bỏ sót ở đầu trajectory) nhưng KHÔNG sửa code — xem mục riêng bên dưới |
| 3 | `min_tainted_share` — phân loại nguyên nhân "gap" giao dịch đầu trajectory trên cả 15 incident | — (không đổi model) | — | Hiệu ứng pha loãng mẫu số chỉ 6/20.879 sự kiện (0,03%) — không đáng để sửa/rebuild — xem mục riêng bên dưới |
| 4 | Ensemble 1a — trung bình Platt-calibrated M1 + T13 (trọng số cố định 0,5/0,5) | 0,7345 [0,6064; 0,9183] | **+0,0401 [+0,0133; +0,0706]** (CI loại 0) | Cải thiện có ý nghĩa thống kê so với M1 gốc — đã xác nhận qua 5 seed (std=0,0000). **Nhưng KHÔNG hơn T13 dùng riêng một cách có ý nghĩa** (diff vs T13 = +0,0138 [−0,0205; +0,0487], CI chứa 0) |
| 5 | Ensemble 1b — Stacking (meta-learner LogisticRegression học trên inner-OOF của M1+T13) | 0,5946 [pooled] | Paired diff +0,0442 [+0,0111; +0,0819] (nhưng pooled TỆ HƠN 0,6624) | Mâu thuẫn giữa 2 cách tính (pooled vs paired) — theo quy ước chính (pooled = số liệu chính thức toàn dự án), kết luận TỆ HƠN, dừng lại, không kiểm tra seed |
| 6 | Nested feature selection (permutation importance trên inner-CV, loại feature importance≤0) | 0,6210 [0,4660; 0,8710] | −0,0812 [−0,1803; −0,0198] (CI loại 0, hướng xấu) | Tệ hơn có ý nghĩa thống kê — dừng lại |
| 7 | Trajectory-fair sample weight (weight=1/số dòng prefix mỗi trajectory sau dedupe) | 0,6970 [0,5551; 0,9085] | −0,0306 [−0,1205; +0,0458] | Không cải thiện (CI chứa 0); giả thuyết "trajectory ngắn bị thiệt" bị ĐẢO NGƯỢC trong dữ liệu thực (nhóm ngắn diff trung bình −0,0731, nhóm dài +0,0065) |
| 8 | 2 feature mới cho mid-trajectory dip (`burstiness_recent_shift`, `recent_half_new_counterparty_share`) — nhắm vào dip PR-AUC tại checkpoint 50% (RQ2) | 0,6528 [0,5128; 0,8836] | −0,0027 [−0,0221; +0,0151] | Không cải thiện (CI chứa 0, gần trung tính); PR-AUC riêng tại ratio_50 còn giảm nhẹ (0,8749→0,8601) — dip hóa ra một phần là artifact phương pháp RQ2 (trường hợp `new_free_dao_2022`: feature không đổi qua các checkpoint), không phải thiếu feature |
| 9 | `path_depth_per_action` (=path_depth/prefix_len) — chẩn đoán trực tiếp từ SHAP+feature-gain+phân phối cho thấy `path_depth` thô (gain=185,2, gấp 9,5 lần feature #2) tạo ranh giới giả tạo gây 83% false-positive toàn dự án | 0,6590 [0,5213; 0,8880] | +0,0019 [−0,0069; +0,0119] | Không cải thiện (CI chứa 0); **quan trọng hơn**: không sửa được đúng 2 ca lỗi đã chẩn đoán (`ronin_bridge_2022__hn012`/`ronin_benign_control_2022` gần như không đổi xác suất) — cây quyết định vẫn tự do split trực tiếp trên `path_depth` thô (không bị loại bỏ), thêm feature tỷ lệ không ép được model bớt phụ thuộc vào nó |
| 10a | THAY THẾ `path_depth` bằng `log1p(path_depth)` (không hyperparameter) | 0,6624 [0,5234; 0,8864] | **+0,0000 [+0,0000; +0,0000]** (đồng nhất tuyệt đối) | Không cải thiện — **về mặt TOÁN HỌC không thể khác**: log1p đơn điệu tăng, XGBoost chỉ dựa vào thứ tự (rank) giá trị để chọn split, không dựa giá trị tuyệt đối, nên biến đổi đơn điệu trên 1 cột không thể thay đổi bất kỳ split nào của cây đã học |
| 10b | THAY THẾ `path_depth` bằng `min(path_depth, cap)`, cap∈{2,3} chọn qua nested inner-CV mỗi outer fold | 0,6603 [0,5234; 0,8835] | +0,0000 [+0,0000; +0,0000] | Không cải thiện; **cơ chế cụ thể tại sao**: fold `ronin_bridge_2022` chọn cap=2 qua inner-CV, nhưng `path_depth` thô của CHÍNH 2 ca lỗi đã chẩn đoán ĐÚNG BẰNG 2 ở mọi prefix — `clip(upper=2)` là phép KHÔNG-THAY-ĐỔI (no-op) cho các dòng này; để thực sự sửa cần cap=1 hoặc 0, nhưng sẽ phá hủy gần hết tín hiệu thật của `path_depth` cho 66% positive có path_depth≥2 |
| 11 | Bổ sung "unmatched negative" (pool E6, 591 candidate) làm negative BỔ SUNG vào tập TRAIN mỗi outer fold (test giữ nguyên) — tự đề xuất, dựa trên phát hiện E6: model chưa từng thấy benign phức tạp cấu trúc cao lúc train | 0,6152 [0,5009; 0,8434] | +0,0112 [−0,0425; +0,0712] | Không cải thiện có ý nghĩa thống kê (CI chứa 0, pooled còn giảm) — **NHƯNG sửa được PHẦN LỚN đúng vùng lỗi đã chẩn đoán**: 8/16 dòng của 2 ca lỗi (chủ yếu `ronin_bridge_2022__hn012` ở prefix trung bình) rơi xuống dưới threshold mới; đánh đổi: threshold bắt buộc tăng mạnh (0,8867→0,9934) làm giảm recall ở nơi khác |
| 12 | LOẠI BỎ hoàn toàn `path_depth` khỏi feature set (không thêm, không biến đổi — loại hẳn) — tự đề xuất, đòn bẩy cuối cùng còn lại sau khi thêm (#9) và biến đổi (#10a/10b) đều thất bại | 0,6936 [0,5459; 0,8987] | −0,0317 [−0,1219; +0,0249] | Không cải thiện có ý nghĩa thống kê (CI chứa 0, dù pooled điểm cao hơn 0,6624); sửa được **MỘT PHẦN NHỎ** vùng lỗi: chỉ 3/16 dòng fix được (`hn012` ở 3 prefix dài nhất: 28/42/55 — xác suất giảm mạnh 0,97→0,25-0,48); toàn bộ `ronin_benign_control_2022` (8/8 dòng) và `hn012` ở prefix ngắn (2-14) vẫn sai |
| 13 | Tinh chỉnh TỶ LỆ pool unmatched thêm vào train (top-K% trajectory theo fan_out cao nhất, K∈{0%,10%,25%,50%} chọn qua nested inner-CV mỗi outer fold) — theo yêu cầu người dùng, khắc phục trade-off threshold quá cao của #11 | 0,6259 [0,4989; 0,8387] | −0,0451 [−0,1157; +0,0135] | Không cải thiện (CI chứa 0, **tệ hơn cả #11 lẫn baseline**); sửa được **5/16 dòng** (ÍT HƠN #11's 8/16) — nguyên nhân: nested inner-CV chọn tỷ lệ theo hiệu năng TRUNG BÌNH của 14 incident khác (đa số "dễ"), không nhạy với 1 pathology hiếm (chỉ 2/1785 dòng); fold `ronin_bridge_2022` tự chọn đúng 50% (outer PR-AUC 0,68→0,79, cải thiện thật) nhưng 2 fold khác cũng chọn 50% do nhiễu inner-CV lại bị hại nặng (`feg_bridge_2024`: 0,83→0,49; `wooppv2_2024`: 0,86→0,50) |
| 11 | (ĐỀ XUẤT, KHÔNG CHẠY) Sample weight ưu tiên hard-negative "matched" — tiền đề: E6 cho thấy matched khó hơn unmatched | — | — | **Tiền đề SAI, đã kiểm tra lại `e6_robustness_v1.md`**: kết quả E6 thực tế NGƯỢC LẠI — matched (đang dùng để train) có PR-AUC=0,6624 (dễ hơn), unmatched (bị loại khỏi mining) có PR-AUC=0,5363 (khó hơn, do fan_out trung bình 6,54 vs 1,42 — giống hành vi rửa tiền hơn). Upweight matched (vốn đã dễ) không có cơ sở lý thuyết để giúp ích; nhóm thật sự khó (unmatched) không có mặt trong training. Người dùng xác nhận HỦY attempt này sau khi nghe giải trình, không chạy |

## Chi tiết từng hướng

### 1. Nested hyperparameter tuning
File: `results/reports/nested_hpo_m1_2026-09-22.md`, `results/tables/nested_hpo_m1_2026-09-22.csv`.
7 candidate (đổi từng trục một so với baseline: `max_depth`∈{3,4,6}, `learning_rate`/`n_estimators`∈{(0,1;200),(0,05;400),(0,2;100)},
`scale_pos_weight`∈{auto=n_neg/n_pos, none, auto_sqrt}), chọn candidate thắng trên inner-CV mỗi outer fold
(15 fold, có thể chọn candidate khác nhau — đúng chuẩn nested CV). Kết quả: 0,6062, tệ hơn baseline.
Wilcoxon signed-rank p=0,386. **Kết luận: KHÔNG cải thiện, dừng lại.**

### 2. Điều tra `hackerdao_2022` (incident tệ nhất)
File: `results/reports/hackerdao_2022_investigation_2026-09-22.md`.
Xác nhận `hackerdao_2022` (PR-AUC 0,5053) là ca tệ nhất trong 15 incident. Phát hiện: trajectory đã decode
bắt đầu từ block 17361615, nhưng `start_block` đăng ký trong registry là 17361150 — lệch 465 block (~23 phút).
Quét dữ liệu thô (chưa decode) trong cửa sổ lệch này tìm thấy 5 giao dịch thật (có tx_hash hợp lệ) liên quan
trực tiếp seed address, hoàn toàn không xuất hiện trong `hackerdao_2022_events.json`. Đây là lỗi decode boundary
thật (khác với cơ chế "provenance event" — tiền chảy VÀO từ bridge — đã xác nhận cho các incident khác).
Cũng phát hiện: `log_amount_mean` toàn trajectory của `hackerdao_2022` (0,5576) là thấp nhất trong 15 incident
dương tính, và là incident DUY NHẤT có `log_amount_mean` dương tính thấp hơn cả trung vị hard-negative
(ngược hướng so với 14 incident còn lại) — liên hệ trực tiếp tới việc SHAP giải thích sai ở checkpoint sớm (k_2).
**Theo yêu cầu người dùng, KHÔNG mở rộng điều tra thêm (không sửa decoder, không rebuild)** — ghi nhận làm
một hạn chế đã biết (known limitation) trong phần Discussion, không phải một cải thiện đã áp dụng.

### 3. `min_tainted_share` — phân loại nguyên nhân "gap" đầu trajectory (toàn bộ 15 incident)
File: `results/tables/early_gap_audit_15incidents_2026-09-22.csv`,
`results/tables/early_gap_reason_breakdown_2026-09-22.csv`, `results/tables/early_gap_reason_detail_2026-09-22.csv`.
Từ phát hiện ở mục 2, mở rộng audit ra toàn bộ 15 incident: 13/15 incident có hiện tượng "gap" (giao dịch thật
trong dữ liệu thô nhưng không vào `events.json` đã decode), tổng 20.879 sự kiện gap. Phân loại nguyên nhân:
`reachability_reject` (bị loại vì không kết nối được tới seed theo thiết kế) = 20.873/20.879 (99,97%);
`tainted_share_reject` (nghi ngờ do pha loãng mẫu số `min_tainted_share`) chỉ **6/20.879 (0,03%)**, rải rác trên
4 incident (`feg_bridge_2024`, `hackerdao_2022`, `radiant_capital_arbitrum_2024`, `utopiasphere_2024`, mỗi nơi 1-3 sự kiện).
**Kết luận: hiệu ứng có thật nhưng quy mô không đáng kể — KHÔNG sửa công thức mẫu số / KHÔNG rebuild lại 15 incident.**
Đóng lại cả câu hỏi decode-gap của `hackerdao_2022` lẫn giả thuyết `min_tainted_share` dưới một kết luận âm tính
trung thực, không có thay đổi code cho decoder/trajectory builder.

### 4. Ensemble 1a — trung bình Platt-calibrated M1 + T13
File: `results/reports/ensemble_1a_average_2026-09-22.md`, `results/reports/ensemble_1a_seed_check_2026-09-22.md`.
Trung bình cố định 0,5/0,5 giữa xác suất đã Platt-calibrate của M1 và T13 (LogReg trên đúng feature set của M1).
Kết quả: 0,7345 [0,6064; 0,9183], paired diff vs M1 = **+0,0401 [+0,0133; +0,0706]** (CI loại 0 — cải thiện thật).
Xác nhận qua 5 seed (42, 1, 7, 123, 2026): std = 0,0000 (pipeline hoàn toàn tất định, kết quả ổn định).
**Tuy nhiên**, so với dùng riêng T13 (0,7548): paired diff = +0,0138 [−0,0205; +0,0487] — CI chứa 0, tức
ensemble KHÔNG chứng minh được tốt hơn một cách có ý nghĩa so với chỉ dùng T13 đơn lẻ (đơn giản hơn).
**Kết luận: cải thiện thật so với M1 gốc, nhưng không rõ ràng hơn phương án đơn giản hơn (T13 một mình)** —
ghi nhận cả hai khía cạnh trong Discussion, không tuyên bố ensemble là lựa chọn tốt nhất một cách dứt khoát.

### 5. Ensemble 1b — Stacking (meta-learner)
File: `results/reports/ensemble_1b_stacking_2026-09-22.md`.
Meta-learner LogisticRegression học trọng số kết hợp [prob_M1, prob_T13] CHỈ trên inner-OOF của outer-train
(không bao giờ dùng outer test để học), threshold chọn trên inner-OOF đã qua meta-learner, model gốc + meta-learner
áp dụng (không fit lại) lên outer test. Kết quả gây mâu thuẫn nội tại: **pooled PR-AUC = 0,5946** (tệ hơn 0,6624)
nhưng **paired diff (theo trung bình per-incident) = +0,0442 [+0,0111; +0,0819]** (có vẻ tốt hơn). Đây là hai cách
tính hợp lệ nhưng khác nhau (pooled = gộp tất cả dòng theo trọng số dòng; paired = trung bình theo từng incident,
trọng số bằng nhau) có thể phân kỳ khi hiệu năng lệch mạnh giữa các incident. **Theo đúng quy ước chính thức của
dự án (pooled = số liệu chính thức, dùng xuyên suốt cho M1=0,6624/B3=0,6875/T13=0,7548), kết luận: TỆ HƠN, dừng
lại, không kiểm tra 5 seed** (vì đã dừng ngay khi phát hiện không cải thiện theo quy ước chính).

### 6. Nested feature selection (permutation importance)
File: `results/reports/nested_feature_selection_2026-09-22.md`.
Phương pháp permutation importance tính trên inner-CV (dùng lại model đã fit ở mỗi inner fold, hoán vị từng cột
feature một lần, đo PR-AUC inner-OOF giảm bao nhiêu — không cần refit, tiết kiệm chi phí so với RFE lặp).
Giữ feature có importance dương, loại feature ≤0. Số feature ứng viên thật (đã xác minh) là **29** (không phải
39-41 như giả định ban đầu). Kết quả: 0,6210 [0,4660; 0,8710], paired diff = **−0,0812 [−0,1803; −0,0198]**
(CI loại 0, hướng xấu — tệ hơn có ý nghĩa thống kê). 4 feature bị loại ở toàn bộ 15/15 outer fold:
`action_count_merge_ratio`, `motif_split`, `motif_swap_then_split`, `outgoing_incoming_ratio`.
**Kết luận: TỆ HƠN có ý nghĩa thống kê, dừng lại.**

### 7. Trajectory-fair sample weight
File: `results/reports/trajectory_fair_weight_2026-09-22.md`.
Giả thuyết: trajectory dài (nhiều dòng prefix sau dedupe, vd `ronin_bridge_2022` 1625 action) đóng góp nhiều
sample hơn hẳn trajectory ngắn (vd `feg_bridge_2024` 9 action), có thể khiến model học lệch về đặc điểm
trajectory dài. Trọng số `weight = 1/(số dòng prefix của chính trajectory đó sau dedupe)` — tổng trọng số mỗi
trajectory = 1,0 (đã kiểm tra), nhân (không thay thế) với `scale_pos_weight` sẵn có. Kết quả: pooled 0,6970
[0,5551; 0,9085], paired diff = **−0,0306 [−0,1205; +0,0458]** (CI chứa 0 → không cải thiện, dừng đúng lúc,
không cần kiểm tra 5 seed). Phân tích nhóm: incident NGẮN (≤40 action, n=7) diff trung bình **−0,0731**;
incident DÀI (≥73 action, n=8) diff trung bình **+0,0065** — **ngược hoàn toàn với giả thuyết ban đầu**
(nhóm ngắn được kỳ vọng hưởng lợi lại bị tệ đi nhiều nhất). **Kết luận: giả thuyết bị bác bỏ bởi dữ liệu thực,
không cải thiện, dừng lại.**

### 8. Feature mới cho mid-trajectory dip
File: `results/reports/m1_v2_mid_trajectory_features_2026-09-26.md`, `scripts/build_mid_trajectory_features.py`.
Xác nhận trước: RQ2 cho thấy PR-AUC per-fold trung bình dip tại `ratio_50` (0,849) so với `ratio_25`
(0,933)/`ratio_75` (0,935). Đào sâu 3 incident điểm thấp nhất tại `ratio_50` (theo OOF pooled M1):
`wooppv2_2024` cho thấy chuyển biến feature RÕ RỆT đúng lúc 50% (bridge_deposit xuất hiện, fan_out 1→3);
nhưng `new_free_dao_2022` có feature **hoàn toàn không đổi** qua các checkpoint (toàn action lặp lại) —
dip của case này là artifact phương pháp RQ2 (bucket riêng có tập huấn luyện khác nhau), không phải thiếu
feature. Xây 2 feature mới từ raw actions thật (không suy đoán): `burstiness_recent_shift` (chênh lệch
burstiness nửa sau vs nửa đầu prefix) và `recent_half_new_counterparty_share` (tỷ lệ counterparty MỚI ở
nửa sau) — feature thứ 2 có khác biệt phân phối thật giữa label=1 (mean 0,374) và label=0 (mean 0,185) tại
`ratio_50`. Kết quả: 0,6528 [0,5128; 0,8836], paired diff = **−0,0027 [−0,0221; +0,0151]** (CI chứa 0,
gần trung tính — khoảng tin cậy hẹp nhất từng thấy trong dự án). PR-AUC riêng tại `ratio_50` sau khi thêm
feature còn **giảm nhẹ** (0,8749→0,8601) — không giải quyết đúng vấn đề nhắm tới.
**Kết luận: KHÔNG cải thiện, dừng lại.**

### 9. `path_depth_per_action` — dựa trên chẩn đoán lỗi thật (LẦN THỬ CUỐI, attempt #9)
File: `results/reports/m1_v3_path_depth_efficiency_2026-09-26.md`, `scripts/run_m1_v3_path_depth_efficiency.py`.
**Chẩn đoán trước khi đề xuất** (không đoán mò): phân tích trực tiếp OOF+threshold cho thấy 15/18 (83%)
false positive toàn dự án tập trung ở đúng 2 trajectory (`ronin_bridge_2022__hn012`,
`ronin_benign_control_2022` — cái sau là benign control đã xác minh provenance thật). 3 góc độ hội tụ
cùng nguyên nhân: (a) SHAP cho thấy `path_depth` đóng góp lớn nhất (+4,1 đến +5,2 log-odds) ở cả 2 ca;
(b) phân phối cho thấy negative với `path_depth>=2` (chỉ 2,2% negative) có oof_prob trung bình nhảy từ
0,027 lên 0,60-0,999, trong khi positive có `path_depth>=2` chiếm 66%; (c) feature-gain trung bình qua
15 fold của `path_depth` = 185,2 — gấp 9,5 lần feature đứng thứ 2. Thêm nữa: các negative gây lỗi cần
55-219 action mới đạt `path_depth`=2 (rất chậm/"phẳng"), trong khi positive đạt cùng độ sâu chỉ sau ~5-7
action. Giả thuyết: thêm `path_depth_per_action = path_depth/prefix_len` giúp model phân biệt "đào sâu
nhanh" (nghi ngờ layering thật) với "đạt cùng độ sâu rất chậm" (relay dài, lành tính).
Kết quả: 0,6590 [0,5213; 0,8880], paired diff vs M1 = **+0,0019 [−0,0069; +0,0119]** (CI chứa 0, gần như
không đổi). **Quan trọng hơn**: kiểm tra riêng đúng 2 ca đã chẩn đoán — xác suất của
`ronin_bridge_2022__hn012`/`ronin_benign_control_2022` GẦN NHƯ KHÔNG ĐỔI ở mọi prefix_len, vẫn vượt xa
threshold; số FP trong "vùng lỗi" (`path_depth>=2`, n=37) còn tăng nhẹ (16 vs so sánh 15 trước đó).
Nguyên nhân khả dĩ: thêm 1 feature tỷ lệ không ép cây quyết định ngừng split trực tiếp trên `path_depth`
thô (vẫn còn nguyên trong tập feature) — sửa triệt để hơn (chuẩn hóa lại/loại bỏ `path_depth` thô) nằm
ngoài phạm vi "chỉ thêm feature" của attempt này.
**Kết luận: KHÔNG cải thiện — kể cả ở đúng vùng lỗi đã chẩn đoán chính xác. Không cần verify 5 seed
(CI chứa 0).**

### 10. THAY THẾ `path_depth` bằng bản biến đổi (log1p / capped) — dựa trên bài học từ attempt #9
File: `results/reports/m1_v4_path_depth_transform_2026-09-26.md`, `scripts/run_m1_v4_path_depth_transform.py`,
`results/tables/m1_v4_capped_fold_choices_2026-09-26.csv`.
Giả thuyết (khác #9): vấn đề không phải thiếu thông tin bổ sung mà là bản thân `path_depth` thô quá
thống trị — cần **THAY THẾ** (không phải thêm bên cạnh) bằng bản chuẩn hóa để giảm độ dốc quyết định
gần-tất-định.
**(A) log1p(path_depth)**: PR-AUC=0,6624, paired diff vs M1 = **+0,0000 [+0,0000; +0,0000]** (đồng nhất
tuyệt đối ở MỌI outer fold, kể cả 2 ca lỗi đã chẩn đoán — xác suất giống hệt tới 4 chữ số thập phân).
Đây là kết quả **tất định về mặt toán học**, không phải thực nghiệm: XGBoost chỉ dùng thứ tự (rank) giá
trị feature để chọn split, không dùng giá trị tuyệt đối — biến đổi đơn điệu tăng trên 1 cột không thể
thay đổi bất kỳ split nào cây đã học.
**(B) capped=min(path_depth,cap)**, cap∈{2,3} chọn qua nested inner-CV mỗi outer fold (giống hệt cấu
trúc attempt #1): PR-AUC=0,6603, paired diff = **+0,0000 [+0,0000; +0,0000]**. Kiểm tra cơ chế: fold
`ronin_bridge_2022` chọn cap=2 (inner PR-AUC 0,8243 vs 0,8238 cho cap=3, chênh không đáng kể) — nhưng
`path_depth` thô của CHÍNH `ronin_bridge_2022__hn012`/`ronin_benign_control_2022` **ĐÚNG BẰNG 2** ở mọi
prefix gây lỗi, nên `clip(upper=2)` là phép **không-thay-đổi tuyệt đối** cho các dòng này. Để thực sự
chạm vào vùng lỗi cần cap=1 hoặc 0 — nhưng cap đó sẽ phá hủy gần hết tín hiệu thật của `path_depth` cho
66% positive có path_depth≥2.
**Kết luận: KHÔNG cải thiện ở cả 2 phương án, với cơ chế thất bại được xác định chính xác (không phải
"không rõ vì sao") — không cần verify 5 seed (CI = [0,0] tuyệt đối cho cả 2).**

### 11. Bổ sung "unmatched negative" (E6) vào tập TRAIN — tự đề xuất
File: `results/reports/m1_v5_unmatched_augment_2026-09-26.md`, `scripts/run_m1_v5_unmatched_augment.py`.
Tự đề xuất (không theo gợi ý người dùng), dựa trên chính kết luận của E6 (`e6_robustness_v1.md`):
unmatched negative (591 candidate bị loại khỏi mining) có `fan_out` trung bình 6,54 (tối đa 247) so với
matched hard-negative đang dùng để train chỉ 1,42 — **M1 chưa từng thấy 1 ví dụ benign nào có độ phức
tạp cấu trúc cao trong lúc train**, đúng cơ chế gây ra 2 ca lỗi đã chẩn đoán ở #9 (`path_depth`/
`unique_counterparties` cao bất thường so với MỌI negative khác trong train). Cách làm: với mỗi outer
fold, thêm TOÀN BỘ pool unmatched của 14 incident train (loại incident held-out) làm negative bổ sung
vào train; **test giữ nguyên (chỉ matched)** để so sánh được với 0,6624.
Kết quả: 0,6152 [0,5009; 0,8434], paired diff vs M1 = **+0,0112 [−0,0425; +0,0712]** (CI chứa 0 — không
cải thiện có ý nghĩa thống kê theo quy ước pooled chính thức, pooled còn giảm).
**Nhưng kiểm tra đúng vùng lỗi cho thấy hiệu quả THẬT, đáng kể**: threshold bắt buộc tăng mạnh (do có
thêm negative khó) từ 0,8867 lên 0,9934 — hệ quả là **8/16 dòng** của 2 ca lỗi rơi xuống dưới threshold
mới (chủ yếu `ronin_bridge_2022__hn012` ở prefix 5-42, xác suất không đổi nhiều nhưng threshold cao hơn
đã đủ để loại chúng ra). Đánh đổi: threshold cao hơn cũng làm giảm recall ở các incident khác (`paraluni_2022`
outer PR-AUC giảm 0,5894→0,5630), trong khi 1 số incident khác lại CẢI THIỆN rõ (`hackerdao_2022`:
0,5053→0,7472; `ronin_bridge_2022`: 0,6793→0,8192) — kết quả lẫn lộn giữa các incident, không nhất quán
đủ để tạo cải thiện pooled/paired có ý nghĩa thống kê.
**Kết luận: KHÔNG cải thiện có ý nghĩa thống kê, nhưng là hướng sửa được PHẦN LỚN vùng lỗi đã chẩn đoán
trong 12 attempt — nếu có thêm dữ liệu/thời gian trong tương lai, đáng thử tinh chỉnh lại (vd chỉ thêm
1 phần pool thay vì toàn bộ, cân bằng lại trade-off recall). Không cần verify 5 seed (CI chứa 0).**

### 12. LOẠI BỎ hoàn toàn `path_depth` khỏi feature set — tự đề xuất (LẦN THỬ CUỐI CÙNG)
File: `results/reports/m1_v6_drop_path_depth_2026-09-26.md`, `scripts/run_m1_v6_drop_path_depth.py`.
Đòn bẩy cuối cùng còn lại trong chuỗi sửa `path_depth` sau khi thêm (#9) và biến đổi (#10a/10b) đều thất
bại vì cây quyết định luôn giữ được cách nào đó để dùng lại `path_depth` gốc — lần này loại bỏ hẳn.
Kết quả: 0,6936 [0,5459; 0,8987] (điểm cao hơn 0,6624 nhưng), paired diff vs M1 = **−0,0317 [−0,1219;
+0,0249]** (CI chứa 0 — không cải thiện có ý nghĩa thống kê).
Kiểm tra đúng vùng lỗi: chỉ sửa được **3/16 dòng** — `ronin_bridge_2022__hn012` ở 3 prefix DÀI NHẤT
(28/42/55, xác suất giảm mạnh 0,97→0,25-0,48, dưới threshold 0,8135); NHƯNG `hn012` ở prefix ngắn (2-14)
và **toàn bộ 8/8 dòng của `ronin_benign_control_2022`** vẫn sai. So với attempt #11 (8/16 dòng sửa
được), đây là hiệu quả sửa lỗi kém hơn — cho thấy `path_depth` không phải nguyên nhân DUY NHẤT khiến
`ronin_benign_control_2022` bị gắn nhãn sai (loại nó ra không đủ, các feature tương quan như
`unique_counterparties`/`branch_count`/`motif_rapid_token_pivot` cùng họ vẫn còn nguyên và vẫn mang
tín hiệu tương tự).
**Kết luận: KHÔNG cải thiện có ý nghĩa thống kê, hiệu quả sửa lỗi cục bộ thấp hơn attempt #11. Không cần
verify 5 seed (CI chứa 0).**

### 13. Tinh chỉnh tỷ lệ unmatched thêm vào train qua nested inner-CV — theo yêu cầu người dùng
File: `results/reports/m1_v7_unmatched_fraction_tuned_2026-09-26.md`, `scripts/run_m1_v7_unmatched_fraction_tuned.py`,
`results/tables/m1_v7_fold_choices_2026-09-26.csv`.
Giả thuyết: attempt #11 (thêm 100% pool unmatched) đẩy threshold quá cao (0,8867→0,9934), hại recall
nhiều incident khác — tinh chỉnh tỷ lệ nhỏ hơn qua nested-CV có thể cân bằng tốt hơn. Cách chọn subset:
top-K% TRAJECTORY theo `fan_out` LỚN NHẤT (không random — chọn candidate "giàu thông tin nhất" cho đúng
cơ chế đã chẩn đoán, tránh pha loãng tín hiệu), K∈{0%,10%,25%,50%} chọn qua nested inner-CV mỗi outer
fold (có thể khác nhau giữa các fold, giống hệt cấu trúc attempt #1/#10b).
Kết quả: 0,6259 [0,4989; 0,8387], paired diff vs M1 = **−0,0451 [−0,1157; +0,0135]** (CI chứa 0) —
**TỆ HƠN CẢ #11 lẫn M1 gốc**. Chỉ sửa được **5/16 dòng** (ít hơn #11's 8/16).
**Phát hiện cơ chế quan trọng**: fold `ronin_bridge_2022` tự chọn đúng K=50% qua inner-CV của chính nó,
và outer PR-AUC của fold đó THẬT SỰ cải thiện (0,6793→0,7877) — nested-CV "đúng" cho đúng fold cần sửa.
Nhưng 2 fold KHÔNG liên quan (`feg_bridge_2024`, `wooppv2_2024`) cũng chọn K=50% (do nhiễu trong so sánh
inner-CV — chênh lệch giữa các K thường chỉ 0,01-0,05, rất dễ nhiễu) và bị HẠI NẶNG (0,83→0,49 và
0,86→0,50). **Đây là giới hạn cấu trúc của việc dùng nested inner-CV để chọn 1 hyperparameter nhằm sửa
1 pathology HIẾM (chỉ 2/1785 dòng, 0,1% dữ liệu)**: tiêu chí chọn dựa trên PR-AUC trung bình của 14
incident (đa số "dễ", không liên quan pathology) sẽ không nhạy hoặc nhiễu loạn khi áp dụng cho pathology
cục bộ — nested-CV tối ưu đúng thiết kế (không nhìn outer test), nhưng tối ưu SAI mục tiêu (trung bình,
không phải worst-case hiếm).
**Kết luận: KHÔNG cải thiện, hiệu quả sửa lỗi còn KÉM HƠN cách "thêm toàn bộ" thô của #11 — tỷ lệ nhỏ
hơn không giải quyết được trade-off, ngược lại tạo thêm bất ổn giữa các fold. Không cần verify 5 seed
(CI chứa 0).**

## Đề xuất bị hủy (không chạy)

**Sample weight ưu tiên hard-negative "matched"** (đề xuất ban đầu của người dùng, trước khi có #11/#12
ở trên): trước khi chạy, kiểm tra lại tiền đề trong `results/reports/e6_robustness_v1.md`: tiền đề đề
xuất ("matched khó hơn unmatched") **SAI, ngược với kết luận chính thức của E6** — matched (0,6624,
đang dùng để train) thực ra DỄ hơn unmatched (0,5363), vì tiêu chí mining `fan_out≤3` đã lọc matched
thành tập "sạch" (fan_out mean=1,42) trong khi pool unmatched bị loại có fan_out trung bình 6,54 (đuôi
tới 247) — giống hành vi rửa tiền hơn, khiến M1 khó phân biệt hơn. Tăng trọng số cho matched (vốn đã dễ)
không có cơ sở lý thuyết để cải thiện; nhóm thật sự khó (unmatched) hoàn toàn không có mặt trong
training hiện tại nên "upweight matched" không thể chạm tới nó. **Người dùng xác nhận HỦY sau khi nghe
giải trình — không chạy, tránh lãng phí thời gian cho một thí nghiệm dựa trên tiền đề sai.** (Chính phát
hiện này — "unmatched mới là nhóm khó" — sau đó trở thành cơ sở trực tiếp cho attempt #11 ở trên.)

## Ý nghĩa cho phần Discussion/Limitations

- M1 (0,6624) là một baseline khá bền: **13 hướng đã chạy** (phương pháp khác nhau: tuning, ensemble đơn
  giản, stacking, feature selection, trọng số mẫu, feature mới có mục tiêu, 5 hướng dựa trên chẩn đoán lỗi
  trực tiếp ở cả cấp độ feature lẫn dữ liệu train) đều không vượt qua được nó một cách rõ ràng và nhất
  quán; 1 hướng đề xuất thêm bị hủy trước khi chạy vì tiền đề dựa trên đọc sai kết quả E6 trước đó — một
  ví dụ cụ thể cho thấy giá trị của việc xác minh lại tiền đề bằng dữ liệu trước khi đầu tư thời gian
  tính toán.
- Chuỗi attempt #9-13 (chẩn đoán → 5 cách sửa độc lập, đều thất bại nhưng MỖI LẦN đều có giải thích cơ chế
  rõ ràng — không phải "thử ngẫu nhiên rồi bỏ"): dù chẩn đoán nguyên nhân lỗi RẤT chính xác (3 góc độ độc
  lập hội tụ: SHAP, phân phối theo bucket, feature-gain toàn cục — `path_depth` thô chiếm ưu thế áp đảo,
  gain gấp 9,5 lần feature #2, gây 83% false-positive toàn dự án tại 2 trajectory cụ thể:
  `ronin_bridge_2022__hn012`, `ronin_benign_control_2022`), CẢ 5 cách sửa đã thử đều thất bại (không đạt
  ý nghĩa thống kê pooled/paired) với cơ chế khác nhau đã xác định rõ:
  (a) THÊM feature tỷ lệ (#9) — cây quyết định không bị ép ngừng dùng feature thô gốc;
  (b) THAY bằng log1p (#10a) — về mặt toán học không thể thay đổi bất kỳ split nào của cây (bất biến với
  biến đổi đơn điệu);
  (c) THAY bằng bản capped (#10b) — cap được chọn qua inner-CV (2 hoặc 3) không bao giờ chạm tới giá trị
  thực tế (=2) của đúng 2 ca gây lỗi;
  (d) Bổ sung TOÀN BỘ dữ liệu train "unmatched negative" (#11) — sửa được **8/16 dòng** lỗi (nhiều nhất
  trong 5 cách) nhưng threshold bắt buộc tăng mạnh làm giảm recall bù trừ ở incident khác, net effect
  trung tính;
  (e) LOẠI BỎ hẳn `path_depth` (#12) — chỉ sửa được 3/16 dòng, vì các feature tương quan cùng họ
  (`unique_counterparties`, `branch_count`, `motif_rapid_token_pivot`) vẫn mang tín hiệu tương tự;
  (f) Tinh chỉnh TỶ LỆ unmatched qua nested inner-CV (#13) — kết quả TỆ HƠN cả #11 (chỉ 5/16 dòng fix
  được, pooled giảm sâu hơn), bộc lộ giới hạn cấu trúc quan trọng: nested-CV chọn hyperparameter theo
  hiệu năng TRUNG BÌNH của 14 incident sẽ không nhạy (hoặc bị nhiễu chi phối) khi mục tiêu thực sự là sửa
  1 pathology hiếm chỉ chiếm 0,1% dữ liệu — tối ưu đúng thiết kế (không leak outer test) nhưng tối ưu SAI
  mục tiêu.
  **Kết luận rút ra**: đây không phải lỗi của riêng 1 feature mà là hệ quả của TOÀN BỘ tập feature đồ thị
  thô (path_depth và các feature tương quan) cùng khuếch đại 1 pattern hiếm trong training (chuỗi dài,
  ít phân nhánh) — sửa 1 feature đơn lẻ (dù thêm/biến đổi/loại bỏ) không đủ, và ngay cả sửa bằng dữ liệu
  train cũng bị giới hạn bởi chính công cụ validation (nested-CV) vốn được thiết kế để tối ưu trung bình,
  không phải để nhắm vào 1 trường hợp hiếm cụ thể. Đây là hướng nghiên cứu tương lai đáng nêu trong
  Limitations (ví dụ: phương pháp validation chuyên biệt hơn cho rare-failure-mode debugging, không dùng
  PR-AUC trung bình làm tiêu chí chọn), ngoài phạm vi 13 attempt đã thử trong track này.
- Hướng duy nhất có cải thiện có ý nghĩa thống kê (Ensemble 1a, +0,0401) lại không rõ ràng hơn phương án đơn
  giản hơn (T13 LogReg một mình, 0,7548) — gợi ý rằng bản thân T13 (không phải ensemble) mới là ứng viên đáng
  cân nhắc thay thế M1, nếu muốn, nhưng đây là quyết định thiết kế nằm ngoài phạm vi cải thiện M1.
- Đã phát hiện và ghi nhận trung thực một lỗi decode-boundary thật ở `hackerdao_2022` cùng một hiệu ứng
  pha loãng mẫu số quy mô rất nhỏ (0,03% sự kiện) trên 4/15 incident — cả hai đều được đánh giá là không đáng
  sửa/rebuild ở quy mô dữ liệu hiện tại (N=15), nhưng đáng nêu như limitation cho công trình tương lai với N lớn hơn.
