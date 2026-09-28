# Alert explanation — 2 case study cụ thể (Tuần 7, Bước 6)

Giải thích bằng XGBoost `pred_contribs` (SHAP-like, xấp xỉ chính xác Shapley value cho tree ensemble) — tính trên MODEL CỦA ĐÚNG FOLD đã sinh ra xác suất out-of-fold tương ứng (không dùng model cuối cùng train-trên-toàn-bộ, tránh leak).

## Case 1 — True Positive, phát hiện SỚM (qbridge_qubit_2022)

- **Incident/candidate:** `qbridge_qubit_2022` (group `qbridge_qubit_2022`, label thật = 1)
- **Prefix:** `k_5` — 5/698 action
- **Xác suất model (fold held-out=qbridge_qubit_2022):** 0.9849 (threshold fold này = 0.9424 → VƯỢT threshold, alert được kích hoạt)

**Top-3 motif đóng góp (|SHAP-like value|, XGBoost pred_contribs), kèm AADAPT ID (Table 2, `tab:aadapt`):**

| Motif feature | Giá trị feature | Đóng góp | AADAPT ID |
|---|---|---|---|
| motif_rapid_token_pivot | 4.0000 | +0.4913 | ADT3028.003 |
| motif_split | 2.0000 | +0.0000 | ADT3028, ADT3028.005, ADT3030.003 |
| motif_merge | 2.0000 | +0.0000 | ADT3030.003 |

**Top-5 feature đóng góp (toàn bộ, không chỉ motif), kèm AADAPT ID nếu có:**

| Feature | Giá trị feature | Đóng góp | AADAPT ID |
|---|---|---|---|
| path_depth | 2.0000 | +1.7712 | — |
| inter_action_gap_mean | 53.2500 | +0.8575 | — |
| fan_out | 1.0000 | -0.7128 | — |
| value_retention | 0.5103 | +0.6435 | — |
| prefix_ratio | 0.0072 | +0.5770 | — |

(bias term = -0.0194)

**5 action trong prefix (tx_hash link):**

- `2022-01-27T21:54:47Z` swap 0xd01ae1a7…→0x00000000… qXETH (amount_norm=5.298) — tx [`0x715f5c59015bd4…`](https://bscscan.com/tx/0x715f5c59015bd44759738fda20cda6995e95123df16659717e3f97d0adddc3ef)
- `2022-01-27T21:55:41Z` transfer 0xd01ae1a7…→0x00000000… xETH (amount_norm=5.298) — tx [`0x974410d882893b…`](https://bscscan.com/tx/0x974410d882893bac9547f044563850549c6ddb66335efe1f7364c782b88d8e1b)
- `2022-01-27T21:58:20Z` transfer 0x00000000…→0xf6e65b33… beltDAI (amount_norm=2.736) — tx [`0x72601524bf96c8…`](https://bscscan.com/tx/0x72601524bf96c8a20598b2323c932a651d93502c8bdfae25936080f0858ef8f3)
- `2022-01-27T21:58:20Z` transfer 0x00000000…→0x7a59bf07… bVoidV2USDC (amount_norm=2.773) — tx [`0x72601524bf96c8…`](https://bscscan.com/tx/0x72601524bf96c8a20598b2323c932a651d93502c8bdfae25936080f0858ef8f3)
- `2022-01-27T21:58:20Z` transfer 0x00000000…→0xf6e65b33… bMultiUSDC (amount_norm=2.704) — tx [`0x72601524bf96c8…`](https://bscscan.com/tx/0x72601524bf96c8a20598b2323c932a651d93502c8bdfae25936080f0858ef8f3)

---

## Case 2 — False Positive (ronin_benign_control_2022)

- **Incident/candidate:** `ronin_benign_control_2022` (group `ronin_bridge_2022`, label thật = 0)
- **Prefix:** `ratio_50` — 52/103 action
- **Xác suất model (fold held-out=ronin_bridge_2022):** 0.9980 (threshold fold này = 0.9895 → VƯỢT threshold, alert được kích hoạt)

> **Cập nhật 2026-09-27**: `ronin_benign_control_2022` là false positive tin cậy nhất trong toàn bộ `rq2_oof_predictions.csv` hiện tại (case cũ `paraluni_2022__hn013` không còn kích hoạt alert sau các lần sửa bug value_share/token_diversity). Đây là 1 giao dịch BENIGN đã xác minh provenance thật (người chơi Axie Infinity rút tiền hợp pháp 2 ngày TRƯỚC vụ hack Ronin Bridge, xem `metadata/incident_registry.csv`) nhưng bị mine "khớp cấu trúc" (bridge_withdraw→swap) với chính `ronin_bridge_2022` nên rất khó phân biệt. Đây cũng là 1 trong 2 trajectory gây 83% false positive toàn dự án đã chẩn đoán kỹ trong quá trình cải thiện M1 (`path_depth` bị model học thành ranh giới gần-tuyệt-đối — xem `results/reports/m1_v3_path_depth_efficiency_2026-09-26.md`). 3 lần thử sửa (thêm feature tỷ lệ, biến đổi path_depth, loại bỏ hẳn) đều KHÔNG sửa được ca này — xem `results/reports/m1_improvement_attempts_2026-09-22.md` attempt #9/10/12.

**Top-3 motif đóng góp (|SHAP-like value|, XGBoost pred_contribs), kèm AADAPT ID (Table 2, `tab:aadapt`):**

| Motif feature | Giá trị feature | Đóng góp | AADAPT ID |
|---|---|---|---|
| motif_merge | 6.0000 | +4.7292 | ADT3030.003 |
| motif_split | 3.0000 | +0.0000 | ADT3028, ADT3028.005, ADT3030.003 |
| motif_peel_like_chain | 0.0000 | +0.0000 | ADT3028.005 |

**Top-5 feature đóng góp (toàn bộ, không chỉ motif), kèm AADAPT ID nếu có:**

| Feature | Giá trị feature | Đóng góp | AADAPT ID |
|---|---|---|---|
| motif_merge | 6.0000 | +4.7292 | ADT3030.003 |
| unique_counterparties | 8.0000 | +1.2724 | — |
| log_amount_mean | 1.5290 | +0.8219 | — |
| inter_action_gap_mean | 440.9608 | -0.4761 | — |
| action_count_mixer_or_exit_ratio | 0.0000 | -0.4670 | ADT3030, ADT3030.003 |

(bias term = -0.0474)

**52 action trong prefix (tx_hash link):**

- `2022-03-23T09:24:50Z` transfer 0xcc13d589…→0x74de5d4f… USDC (amount_norm=6.839) — tx [`0x1f1ad65c52abac…`](https://etherscan.io/tx/0x1f1ad65c52abac4b06dfcdc44d3830212ed98fdd28e68bb55b898636b35d1b39)
- `2022-03-23T09:24:50Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.164) — tx [`0xba75a13367b1dd…`](https://etherscan.io/tx/0xba75a13367b1dd3e504af16306735699a180f969ed2099bf1022ed0895704c95)
- `2022-03-23T09:37:46Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.606) — tx [`0x02acb73e185b64…`](https://etherscan.io/tx/0x02acb73e185b6426980bc4ecf7ec1f32ade2abde4ff2c94cdc1118be6d2e9994)
- `2022-03-23T09:44:53Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.173) — tx [`0x17fcc8e686049f…`](https://etherscan.io/tx/0x17fcc8e686049f651ab73f3183ce1d6506bdef866934fcfcf39befbbd6786863)
- `2022-03-23T09:59:38Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=2.390) — tx [`0xe4b1c6e1e58d59…`](https://etherscan.io/tx/0xe4b1c6e1e58d59ea5df6e0b61af437d1eb0395047cd589a08e52275f2d669705)
- `2022-03-23T10:13:21Z` transfer 0x74de5d4f…→0xdef171fe… ETH (amount_norm=0.007) — tx [`0xbd71e57aee113d…`](https://etherscan.io/tx/0xbd71e57aee113db3399c8db2c5f28e21559e4b1953c38935b4a44a4cc19209cc)
- `2022-03-23T10:14:07Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.112) — tx [`0x5845f2e3cd8aab…`](https://etherscan.io/tx/0x5845f2e3cd8aab6809da9ac1f4165c6154f205e26ccf3d4b09b017c70b743860)
- `2022-03-23T10:19:10Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.036) — tx [`0x2da2fc115cd07b…`](https://etherscan.io/tx/0x2da2fc115cd07b973e3ea24a494c1a84dee2ed6694c7636df6429b94ce74bb82)
- `2022-03-23T10:25:39Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.039) — tx [`0x7c92e37549d054…`](https://etherscan.io/tx/0x7c92e37549d054ab9647ab4e420348ca8f011def59b6d88a561f9c8b133e203d)
- `2022-03-23T10:26:31Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.095) — tx [`0x16bc7550f4ce2c…`](https://etherscan.io/tx/0x16bc7550f4ce2ce102f26862af0dc2b2f783182f5559a480a4015f5a6961b5a5)
- `2022-03-23T10:26:31Z` transfer 0x74de5d4f…→0x11111112… ETH (amount_norm=0.082) — tx [`0x1a9566aad4cd05…`](https://etherscan.io/tx/0x1a9566aad4cd05b10ca260a1665191e3bbc105fdd0d1f2e951d969ff403dbbf1)
- `2022-03-23T23:48:34Z` transfer 0xcc13d589…→0xfd5ef736… ZUG (amount_norm=5.872) — tx [`0xef6b049ae9a80c…`](https://etherscan.io/tx/0xef6b049ae9a80c194b0eebcac87785411f4ad74a11c510bc931dd1bd219689ee)
- `2022-03-25T04:38:46Z` transfer 0x74de5d4f…→0xfd5ef736… ZUG (amount_norm=4.675) — tx [`0xd16513567a8416…`](https://etherscan.io/tx/0xd16513567a84164aab1f54b8a75abc496339f44b66b0ad3fab5c53ff195ebcc8)
- `2022-03-25T04:57:12Z` transfer 0x74de5d4f…→0xfd5ef736… ZUG (amount_norm=6.774) — tx [`0x5d5338ed2904cb…`](https://etherscan.io/tx/0x5d5338ed2904cbf03fa7661c5d246b13a07d769ee45373ea69b2c16c76f39c9a)
- `2022-03-25T17:58:42Z` transfer 0x74de5d4f…→0xfd5ef736… ZUG (amount_norm=4.663) — tx [`0xb8ac2848f25e1e…`](https://etherscan.io/tx/0xb8ac2848f25e1e69dc9bc18456728d7bfb12c13a02338d1e83328ae5896d24bf)
- `2022-03-25T21:21:14Z` transfer 0xcc13d589…→0x74de5d4f… USDC (amount_norm=6.910) — tx [`0xb7419bfc9cc965…`](https://etherscan.io/tx/0xb7419bfc9cc9651314ab2ba4ac9a21a461307ef2deb578d5be5805270d4a681f)
- `2022-03-25T22:52:12Z` transfer 0x74de5d4f…→0xfd5ef736… ZUG (amount_norm=5.249) — tx [`0xcf64e167bbee81…`](https://etherscan.io/tx/0xcf64e167bbee81ab12ebacba2c1cfcc2455942bd08db23eb53f1f90522ca0ce9)
- `2022-03-26T07:51:41Z` transfer 0x74de5d4f…→0xfd5ef736… ZUG (amount_norm=5.111) — tx [`0x41576ff002a961…`](https://etherscan.io/tx/0x41576ff002a96148fff2ca73f32d7199796717ad53aa532b1daa98de2c5667c9)
