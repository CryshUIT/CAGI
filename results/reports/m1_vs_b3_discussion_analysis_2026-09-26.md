# Vì sao M1 (typed) ≈ B3 (flat) — phân tích cho phần Discussion (2026-09-26)

**Lưu ý phạm vi**: đây là phân tích thuần túy (đọc dữ liệu đã có, tính tương quan, so sánh
per-incident) — KHÔNG train model mới, KHÔNG phải một attempt cải thiện M1 (track đó đã đóng
sau 13 lần thử, xem `m1_improvement_attempts_2026-09-22.md`). Mục đích: giải thích cơ chế đằng sau
kết quả RQ1 (M1=0,6624 vs B3=0,6875, paired diff +0,0355 95% CI [−0,0286, +0,1288], không có ý
nghĩa thống kê) cho phần Discussion, không phải để bào chữa hay tìm cách sửa.

## Câu hỏi 1 — B3 có "vô tình" nắm được tín hiệu type qua cấu trúc đồ thị thô không?

**Có, một phần — mức độ phụ thuộc RẤT nhiều vào loại hành động.**

Huấn luyện 1 RandomForest đơn giản (GroupKFold 5-fold, không liên quan gì đến M1/B3) để dự đoán
"trajectory này có chứa hành động loại X hay không" **CHỈ dùng 15 feature cấu trúc/kinh
tế/thời gian của B3** (không có bất kỳ nhãn loại hành động nào):

| Loại hành động cần dự đoán | Tỷ lệ dương tính | AUC dự đoán từ CHỈ feature B3 |
|---|---|---|
| có swap | 26,3% | **0,892** (rất mạnh) |
| có bridge (deposit/withdraw) | 35,2% | **0,679** (trung bình) |
| có mixer/exit | 3,3% | 0,11 (KHÔNG đáng tin — chỉ 59 dòng dương tính, tập trung 50/59 ở 1 incident, GroupKFold suy biến) |

**Diễn giải**: cấu trúc thô (đặc biệt `log_amount_mean`, `value_retention`, `burstiness` —
swap thường tạo ra chữ ký giá trị/thời gian đặc trưng do đổi token) đã mang phần lớn thông tin
"có swap hay không" mà không cần nhãn tường minh — B3 KHÔNG "mù" như giả định ban đầu của RQ1.
Với "bridge", tín hiệu gián tiếp yếu hơn nhiều (AUC 0,68, chỉ hơn ngẫu nhiên vừa phải) — bridge
interaction không tạo chữ ký cấu trúc thô đặc trưng rõ như swap. Không đủ dữ liệu để kết luận
đáng tin cậy về mixer (quá hiếm, tập trung 1 incident).

**Kết luận Câu 1**: đây là lời giải thích THẬT nhưng KHÔNG ĐỒNG ĐỀU theo loại hành động — B3
"đoán được" swap gần như tốt như có nhãn, nhưng "mù" hơn nhiều với bridge. Phần gain của M1 đến
từ đúng những loại hành động mà B3 không đoán được gián tiếp (bridge, và các tổ hợp motif liên
quan đến bridge) — nhưng những incident có bridge lại thường cũng có swap đi kèm, nên gain ròng
bị pha loãng.

## Câu hỏi 2 — Lợi ích của typing có tập trung ở 1 nhóm nhỏ incident không?

**Có — và đây là bằng chứng RÕ RÀNG NHẤT, mạnh nhất về mặt thống kê trong 4 câu hỏi.**

So sánh PR-AUC per-incident (`rq1_paired_bootstrap_rerun_2026-09-22.md`):

| Nhóm | Incident | Diff (M1−B3) | Độ dài trajectory | Số loại hành động khác nhau |
|---|---|---|---|---|
| **M1 thắng rõ** | new_free_dao_2022* | +0,574 | 12 | 1 |
| | ronin_bridge_2022 | +0,078 | 1625 | 4 |
| | magic_abracadabra_arbitrum_2025 | +0,065 | 88 | 5 |
| | bsc_token_hub_2022 | +0,058 | 362 | 5 |
| | paraluni_2022 | +0,043 | 511 | 4 |
| | qbridge_qubit_2022 | +0,041 | 698 | 5 |
| | radiant_capital_arbitrum_2024 | +0,014 | 248 | 4 |
| **Hòa** | chibi_finance_2023, utopiasphere_2024, xkingdom_2024, wault_finance_2021 | ≈0 | 37–190 | 2–4 |
| **B3 thắng rõ** | deltaprime_arbitrum_2024 | −0,042 | 23 | 3 |
| | wooppv2_2024 | −0,060 | 16 | 3 |
| | hackerdao_2022 | −0,099 | 35 | 3 |
| | feg_bridge_2024 | −0,136 | 9 | 1 |

*new_free_dao_2022 là ngoại lệ đặc biệt (trajectory ngắn nhưng diff cực lớn — toàn bộ 12 action
đều là `mixer_or_exit` lặp lại 1 counterparty duy nhất; B3 thất bại vì không có feature nào phân
biệt được kiểu lặp lại đơn điệu này, trong khi `action_count_mixer_or_exit_ratio`=1.0 của M1 bắt
được ngay — loại trừ ngoại lệ này khỏi phân tích tương quan bên dưới).

**Tương quan định lượng** (loại trừ new_free_dao_2022, N=14 incident còn lại):
- Spearman(diff, độ dài trajectory) = **0,859**, p = 0,00008 — tương quan rất mạnh, có ý nghĩa
  thống kê rõ dù N nhỏ.
- Spearman(diff, số loại hành động khác nhau) = **0,840**, p = 0,00017 — tương tự.
- Trung vị độ dài trajectory: nhóm M1-thắng = 511 action; nhóm hòa = 73; nhóm B3-thắng = 19,5.

**Kết luận Câu 2**: lợi ích của typing **có thật nhưng tập trung mạnh ở trajectory DÀI và ĐA DẠNG
loại hành động** (thường là các vụ có bridge/multi-protocol thật, path phức tạp). Ở trajectory
NGẮN (dưới ~40 action, thường chỉ 1-3 loại hành động), typed feature không có đủ "chất liệu" để
phát huy — sự khác biệt giữa 2 model ở nhóm này gần như là nhiễu ngẫu nhiên của cây quyết định
trên mẫu nhỏ, đôi khi nghiêng về B3 chỉ vì ít tham số hơn (ít overfit hơn) trên trajectory đơn
giản. Đây là câu chuyện "typing giúp thật, nhưng có điều kiện" — không phải "typing vô dụng".

## Câu hỏi 3 — E4/E5 không có ý nghĩa thống kê: do N nhỏ hay do redundancy thật?

**Redundancy thật, có bằng chứng cụ thể và mạnh — không chỉ là vấn đề power thống kê.**

Tính tương quan Spearman giữa 22 feature nhóm "type-specific" (action_count_*_ratio, motif_*,
num_distinct_bigrams/trigrams, num_bridge_families, time_to_first_bridge...) với 15 feature nhóm
structural/economic/temporal của B3 (toàn bộ 1785 dòng, pooled):

- **9/22 (41%) type-feature có |corr| > 0,5** với ít nhất 1 feature của B3; **6/22 (27%) có
  |corr| > 0,7**.
- **2 cặp gần như TRÙNG TUYỆT ĐỐI** (không phải trùng hợp thống kê — trùng vì ĐỊNH NGHĨA):
  - `motif_split` và `branch_count`: **r = 1,000 chính xác**. Đọc code (`src/features/extractor.py`):
    `branch_count` đếm số địa chỉ nguồn có out-degree > 1 (dòng 151); `motif_split` đếm số địa
    chỉ nguồn có ≥2 outgoing edge trong prefix (dòng 275) — **2 công thức giống hệt nhau**, chỉ
    được cài đặt lặp lại ở 2 nhóm feature khác nhau (structural vs motif). M1's "motif_split" —
    một trong những feature "typed" được quảng bá của bài — về bản chất là feature `branch_count`
    của B3 dưới tên khác.
  - `action_count_merge_ratio` và `outgoing_incoming_ratio`: **r = −0,99999**. Tỷ lệ hành động
    "merge" (nhiều dòng tiền hội tụ) gần như là nghịch đảo tuyến tính hoàn hảo của tỷ lệ
    outgoing/incoming đã có sẵn trong B3 — về mặt thông tin, gần như là cùng 1 tín hiệu.
  - Các cặp mạnh khác: `num_distinct_trigrams`/`bigrams` (0,85–0,89 với B3), `motif_merge` (0,78),
    `motif_rapid_token_pivot` (0,74), `motif_swap_then_split` (0,65).
- **Feature ÍT redundant nhất** (còn mang thông tin riêng, không thể suy ra từ B3): các feature
  liên quan bridge cụ thể — `action_count_bridge_deposit_ratio` (0,34), `num_bridge_families`
  (0,31), `time_to_first_bridge` (0,29). Đáng chú ý: đây CHÍNH LÀ nhóm feature đã bị loại khỏi M1
  chính thức (`BRIDGE_CONTEXT_COLS_EXCLUDED`) vì gây overfitting theo protocol cụ thể (xem
  `bridge_context_ablation_investigation.md`) — tức phần thông tin "độc nhất, không redundant"
  của type hóa ra lại là phần GÂY HẠI khi đưa vào model, không phải phần giúp ích.

**Kết luận Câu 3**: E4 (bỏ temporal)/E5 (bỏ motif) không có ý nghĩa thống kê **chủ yếu vì
redundancy thật**, không chỉ vì N=15 nhỏ — ít nhất 2 feature "motif" là bản sao toán học của
feature "structural" đã có sẵn, và một phần đáng kể còn lại có tương quan vừa-mạnh. Phần thông
tin type THỰC SỰ độc lập (bridge-specific) lại là phần đã được xác nhận RIÊNG là có hại khi dùng
trực tiếp (protocol-specific overfitting). N nhỏ vẫn góp phần (không loại trừ khả năng 1 phần nhỏ
tín hiệu thật bị nhiễu che khuất), nhưng không phải nguyên nhân chính.

## Câu hỏi 4 — Tổng hợp: xếp hạng nguyên nhân

| Hạng | Nguyên nhân | Mức độ bằng chứng | Ghi chú |
|---|---|---|---|
| **1** | **(c) Lợi ích typing có thật nhưng cục bộ** (tập trung ở trajectory dài/đa dạng loại hành động) | **Mạnh nhất** — Spearman rho=0,86-0,84, p<0,001 (N=14) | Câu chuyện tinh tế nhất, đáng làm trọng tâm Discussion |
| **2** | **(d) Redundancy giữa motif/temporal và structural/economic** | **Mạnh, cụ thể** — 2 cặp feature trùng gần tuyệt đối (r≈1,0 và r≈-1,0), 41% type-feature có \|corr\|>0,5 | Giải thích trực tiếp tại sao E4/E5 không có ý nghĩa TK |
| **3** | **(a) B3 gián tiếp nắm được tín hiệu type qua cấu trúc thô** | **Trung bình, không đều** — AUC=0,89 cho swap nhưng chỉ 0,68 cho bridge | Bổ sung, giải thích một phần vì sao gain nhỏ hơn kỳ vọng, đặc biệt cho incident có swap chiếm ưu thế |
| **4** | **(b) N=15 quá nhỏ để phát hiện chênh lệch thật** | **Có thật nhưng là yếu tố PHỤ/khuếch đại**, không phải nguyên nhân gốc | CI paired rộng ([−0,03,+0,13]) nhất quán với việc thiếu power, nhưng pattern per-incident (#1) quá có hệ thống để chỉ là nhiễu thuần túy — N nhỏ làm cho 1 hiệu ứng CÓ THẬT nhưng KHÔNG ĐỒNG ĐỀU (bị pha loãng giữa incident dài và ngắn) khó đạt ngưỡng ý nghĩa thống kê khi pool chung |

**Câu chuyện tổng hợp cho Discussion**: M1 không "thua" B3 về mặt khái niệm — typed representation
mang lại lợi ích thật và có thể định lượng, nhưng (i) lợi ích đó tập trung ở các trajectory dài,
nhiều loại hành động, mô phỏng layering đa bước thật (đúng use-case mà typed motif được thiết kế
cho); (ii) một phần đáng kể tín hiệu "type" hóa ra trùng lặp về mặt toán học với tín hiệu cấu trúc
thô đã có sẵn (motif_split≡branch_count); (iii) phần tín hiệu type ĐỘC NHẤT còn lại (đặc thù
bridge) dễ bị overfit theo protocol cụ thể ở N=15 hơn là mang lại lợi ích ổn định; và (iv) khi
pool tất cả 15 incident (ngắn lẫn dài) vào 1 phép so sánh trung bình, lợi ích cục bộ mạnh ở nhóm
dài bị pha loãng bởi nhóm ngắn (nơi 2 model gần như tương đương hoặc B3 nhỉnh hơn), khiến kết quả
tổng thể không đạt ý nghĩa thống kê dù hiệu ứng cục bộ là thật. Đây là giới hạn tự nhiên của N=15
kết hợp với một hiệu ứng không đồng nhất theo bối cảnh — không phải bằng chứng "typing không giúp
gì", cũng không phải "N nhỏ nên chưa biết được".
