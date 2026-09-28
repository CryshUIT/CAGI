# Điều tra `hackerdao_2022` — ca tệ nhất hiện tại (2026-09-22)

**Bối cảnh:** theo yêu cầu NSS 2026 Việc 2 (Giai đoạn "cải thiện M1 hợp lệ"), áp dụng đúng khuôn mẫu đã dùng cho
`paraluni_2022` (`results/reports/paraluni_2022_reinvestigation.md`) cho ca tệ nhất hiện tại trong `main_table.csv`
(N=15) — ban đầu yêu cầu chỉ định `feg_bridge_2024` (PR-AUC 0.2979), nhưng số đó thuộc bộ dữ liệu 12-incident cũ;
với N=15 hiện tại, `feg_bridge_2024` = 0.8303 (không còn tệ nhất) và ca tệ nhất thật là `hackerdao_2022` (0.5053) —
đã báo cáo và được người dùng xác nhận chuyển hướng điều tra sang `hackerdao_2022`.

## Bước 1 — Xác nhận dữ liệu (trajectory đầy đủ/đúng không, có bug decode không)

**Xác nhận thứ hạng:** `hackerdao_2022` PR-AUC = 0.5053 trên `main_table.csv` (N=15) — tệ nhất trong 15 incident.

| Incident (tệ→tốt) | PR-AUC M1 |
|---|---|
| **hackerdao_2022** | **0.5053** |
| paraluni_2022 | 0.5894 |
| ronin_bridge_2022 | 0.6793 |
| feg_bridge_2024 | 0.8303 |
| ... | ... |

**Đối chiếu metadata (`incident_registry.csv`):**
- `endpoint_confirmed = False`, `bridge_families = "TBD_pending_trajectory_decode"` — chính registry đã tự đánh
  dấu phần decode cross-chain/bridge của incident này **chưa hoàn tất**.
- `mixer_families` ghi chú "Tornado Cash (theo báo cáo CertiK, **chưa xác nhận qua trajectory**)" — **ghi chú này
  SAI/LỖI THỜI**: trajectory đã decode (`hackerdao_2022_events.json`) thực tế CÓ 4 hành động `mixer_or_exit` thật
  (block ~17361883-17361890, gửi BNB tới `TornadoProxyLight`, `source_confidence=1.0`) — cần sửa lại ghi chú này
  trong registry (việc nhỏ, không ảnh hưởng số liệu).
- `notes`: CertiK báo cáo "flash loan exploit ~200 BNB (~65K USD)".

**Kiểm tra trực tiếp trajectory đã decode (35 action, block 17361615→17434033):** toàn bộ giá trị BNB/WBNB gốc
trong 35 action đều **dưới 1 BNB** (0.001–0.183 BNB) — không có action nào thể hiện quy mô ~200 BNB mà CertiK mô
tả. Nghi ngờ trajectory thiếu đúng đoạn giao dịch giá trị lớn.

**Xác minh bằng dữ liệu THÔ (trước decode, `data/raw/bsc/0xcfc591db.../hackerdao_2022/*.json`):**
Trajectory đã decode bắt đầu từ **block 17361615**, nhưng `start_block` trong registry là **17361150** — lệch
465 block (~23 phút, BSC ~3s/block). Quét lại đúng cửa sổ block 17361150–17361614 trong dữ liệu THÔ đã thu thập
(chưa decode): **tìm thấy 5 giao dịch thật** (block 17361153, 17361160, 17361383, 17361392, 17361545 — có tx_hash,
from/to, asset, value hợp lệ) liên quan trực tiếp tới địa chỉ seed, **hoàn toàn KHÔNG xuất hiện trong
`hackerdao_2022_events.json`** đã decode.

→ **XÁC NHẬN: đây là lỗi decode/pipeline thật (không phải suy đoán)** — có transaction thật trong dữ liệu thô bị
rớt trước khi vào file events đã decode. (Giá trị của 5 giao dịch bị rớt này khi quy đổi vẫn nhỏ — lớn nhất
~2976 POS1, ~955 IDO, dưới 1 BNB — nên riêng 5 giao dịch này KHÔNG giải thích được khoản "~200 BNB" CertiK nêu;
nhiều khả năng khoản lớn đó nằm hoàn toàn NỘI BỘ trong 1 transaction thực thi flash loan — mượn/trả trong cùng 1
tx — và không bao giờ hiện ra như 1 transfer đơn giản tới ví EOA seed, chỉ phần lợi nhuận skim nhỏ mới trôi ra
ngoài như các action đã thấy. Đây là suy luận hợp lý dựa trên cơ chế flash loan điển hình, KHÔNG phải đã xác minh
100% — cần thêm bước dò sâu hơn nếu muốn khẳng định chắc chắn, xem "Giới hạn" cuối báo cáo.)

## Bước 2 — Phân tích feature/SHAP xem điều gì kéo điểm sai

### 2a. So sánh feature (full trajectory) với 14 incident dương khác

| Nhóm | Feature | hackerdao_2022 | Median 14 khác | Min-Max 14 khác | Outlier? |
|---|---|---|---|---|---|
| economic | **log_amount_mean** | **0.5576** | 1.7368 | [1.0100, 2.4056] | **CÓ — thấp hơn TẤT CẢ 14 incident khác** |
| temporal | **inter_action_gap_mean** | **6440.35** | 516.83 | [81.0, 4252.5] | **CÓ — cao hơn TẤT CẢ 14 incident khác** |
| temporal | **inter_action_gap_std** | **27898.37** | 1262.27 | [89.9, 15739.3] | **CÓ** |
| temporal | burstiness | 0.6249 | 0.3287 | [0.0324, 0.6148] | biên (vượt max rất sát) |
| action_ratio | action_count_mixer_or_exit_ratio | 0.1143 | 0.0000 | — | có (4/35 action là mixer, xác nhận thật) |
| motif | (7 loại) | 3/7 = 0 | trung bình 3.2/7 = 0 | — | không bất thường |
| structural | (6 loại) | không outlier | — | — | không |

### 2b. Volume band: positive vs hard-negative cùng incident

| Incident | positive log_amount_mean | hard-negative median | lệch (positive − hn) | n hard-negative |
|---|---|---|---|---|
| magic_abracadabra... | 2.3191 | 0.2807 | +2.0384 | 24 |
| ... (13 incident khác đều lệch DƯƠNG, positive > hard-negative) | | | | |
| **hackerdao_2022** | **0.5576** | **1.0057** | **−0.4481 (ĐẢO CHIỀU)** | 25 |

**`hackerdao_2022` là incident DUY NHẤT trong 15 incident có chiều lệch ĐẢO NGƯỢC**: ở 14 incident còn lại, giao
dịch của kẻ tấn công (positive) luôn có giá trị trung bình LỚN HƠN ví đối chứng (hard-negative) — hợp lý vì tấn
công thường di chuyển số tiền lớn. Riêng `hackerdao_2022`, giao dịch "tấn công" lại có giá trị NHỎ HƠN chính ví
đối chứng band-matched của nó — nhất quán với giả thuyết Bước 1: trajectory bị thiếu đúng đoạn giá trị lớn.

### 2c. SHAP trên đúng fold (fit M1 trên 14 incident khác, predict `hackerdao_2022`)

PR-AUC tính lại = 0.5053 (khớp `main_table.csv`, xác nhận đúng fold).

8 dòng positive theo prob tăng dần:

| Mốc | prefix_len | prob |
|---|---|---|
| k_2 | 2 | 0.0063 |
| k_3 | 3 | 0.0070 |
| ratio_50 | 18 | 0.2442 |
| ratio_25 | 9 | 0.5015 |
| k_7 | 7 | 0.5574 |
| k_5 | 5 | 0.6904 |
| ratio_75 | 27 | 0.8385 |
| **ratio_100** | 35 | **0.8888** |

→ **Không phải mô hình "không bao giờ nhận ra" — full trajectory (ratio_100) được chấm 0.89 (đúng hướng)**. Vấn đề
tập trung ở 2 mốc SỚM NHẤT (k_2, k_3): 32/115 dòng hard-negative (mọi prefix) được chấm điểm cao hơn dòng
positive khó nhất (k_2, prob=0.0063), kéo PR-AUC pooled toàn incident xuống 0.5053 — **cùng bản chất "early-
detection cụ thể" đã tìm thấy ở `paraluni_2022`**, không phải model kém trên toàn trajectory.

**SHAP top-5, `hackerdao_2022` tại k_2 (prob=0.0063):**

| Feature | Đóng góp | Giá trị thật |
|---|---|---|
| log_amount_mean | −2.2255 | 0.998 |
| path_depth | +2.1876 | 2.0 |
| active_duration_sec | −1.1275 | 0.0 |
| value_retention | −0.7538 | 0.031 |
| fan_out | −0.6338 | 1.0 |

**SHAP top-5, hard-negative `hackerdao_2022__hn001` tại k_2 (prob=0.9659, dòng vượt positive):**

| Feature | Đóng góp | Giá trị thật |
|---|---|---|
| log_amount_mean | +1.9876 | 1.642 |
| inter_action_gap_mean | +0.9848 | 45.0 |
| fan_out | +0.7625 | 2.0 |
| prefix_ratio | +0.6211 | 0.167 |
| motif_merge | −0.5769 | 0.0 |

**`log_amount_mean` là feature quyết định ở cả 2 phía** — đúng 2 hành động đầu tiên của kẻ tấn công thật có giá
trị nhỏ hơn 2 hành động đầu của chính ví đối chứng band-matched, khiến mô hình xếp nhầm ngay từ mốc sớm nhất.

## Bước 3 — Kết luận nguyên nhân

**Nguyên nhân chính: LỖI DỮ LIỆU/DECODE (đã xác nhận bằng chứng cụ thể, không phải suy đoán)** — tối thiểu 5
giao dịch thật trong khoảng block 17361150–17361614 (đúng tại điểm bắt đầu incident theo registry) có trong dữ
liệu thô đã thu thập nhưng KHÔNG xuất hiện trong trajectory đã decode. Registry cũng tự đánh dấu
`bridge_families="TBD_pending_trajectory_decode"` — xác nhận độc lập rằng decode cho incident này chưa hoàn
tất từ trước.

**Hệ quả xuống feature/model:** vì thiếu dữ liệu đầu trajectory, `log_amount_mean` toàn trajectory của
`hackerdao_2022` thấp nhất trong 15 incident VÀ là incident DUY NHẤT có volume band đảo chiều so với hard-negative
— hệ quả trực tiếp là early-detection thất bại ở đúng 2 mốc sớm nhất (k_2, k_3), kéo PR-AUC toàn incident từ
mức full-trajectory hợp lý (0.89) xuống còn 0.5053.

**Không phải đặc điểm hành vi thật cần feature mới** — đây không giống phát hiện residual ở `paraluni_2022` (nơi
early-detection vẫn khó dù dữ liệu đã đúng); ở đây gốc rễ là dữ liệu ĐẦU VÀO bị thiếu, sửa decode có khả năng
thay đổi cả `log_amount_mean` lẫn số action ở đúng các mốc sớm đang gây lỗi.

## Giới hạn của điều tra này (trung thực, chưa làm)

- Chưa xác định được CHÍNH XÁC dòng code/logic nào trong pipeline decode làm rớt 5 giao dịch này (chỉ xác nhận
  CÓ rớt, dựa trên đối chiếu raw JSON vs events.json) — cần đọc kỹ `src/normalize/decoder.py` phần liên quan tới
  cắt cửa sổ theo block/thời gian hoặc merge nhiều file `assettransfers_w*.json` mới khẳng định được cơ chế cụ
  thể.
  Đã có bằng chứng KHÔNG PHẢI trùng lặp/dedupe overlap thông thường (5 hash khác nhau, không hash nào trong đó
  trùng với hash bắt đầu ở block 17361615) — nhiều khả năng là do CỬA SỔ THỜI GIAN/BLOCK dùng để quyết định
  "trajectory bắt đầu từ đâu" bị lệch so với `start_block` đã ghi trong registry, nhưng chưa lần ra nguyên nhân
  gốc trong code.
- Chưa xác minh được khoản "~200 BNB" CertiK báo cáo nằm ở đâu trong toàn bộ dữ liệu thô (chỉ quét đúng cửa sổ
  block bị thiếu, chưa quét toàn bộ). Giả thuyết "giá trị lớn nằm nội bộ trong 1 tx flash loan, không hiện ra
  như transfer đơn giản tới EOA" là suy luận hợp lý dựa trên cơ chế kỹ thuật, chưa xác minh 100%.
- **CHƯA đề xuất/thực hiện bất kỳ thay đổi code nào** — đúng theo yêu cầu, dừng lại ở đây để chờ xác nhận trước
  khi sửa decoder/rebuild.

## Về `feg_bridge_2024` nhạy hyperparameter (từ Việc 1, ghi lại cho Limitations của bài báo)

Dưới cấu hình nested HPO (đã bị loại bỏ vì tệ hơn tổng thể), fold `feg_bridge_2024` chọn `max_depth=3` và
outer-test PR-AUC rớt xuống 0.2311 (so với 0.8303 của M1 gốc `max_depth=4`) — incident này rất nhạy với độ sâu
cây quyết định, dù chỉ có 9 action. Ghi nhận làm hạn chế của nghiên cứu (model sensitivity tới hyperparameter
trên incident có trajectory ngắn), KHÔNG điều tra thêm/không cần thí nghiệm bổ sung theo đúng chỉ đạo.
