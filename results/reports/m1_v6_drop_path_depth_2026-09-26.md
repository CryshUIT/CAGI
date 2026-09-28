# M1_v6 - LOAI BO hoan toan path_depth (Attempt #12, 2026-09-26)

Khong them, khong bien doi - loai han cot `path_depth` khoi feature set cua M1.

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v6 (khong path_depth)** | **0.6936** | [0.5459, 0.8987] |

**Paired diff (M1_v6 - M1 chinh thuc) = -0.0317, 95% CI = [-0.1219, +0.0249]**

**Paired diff (M1_v6 - B3) = +0.0038, 95% CI = [-0.1322, +0.1170]**

## Kiem tra dung 2 ca da chan doan

| source_id | prefix_len | prob moi (M1_v6) | prob M1 chinh thuc | threshold |
|---|---|---|---|---|
| ronin_bridge_2022__hn012 | 2 | 0.9995 | 0.9999 | 0.8135 |
| ronin_bridge_2022__hn012 | 3 | 0.9998 | 0.9999 | 0.8135 |
| ronin_bridge_2022__hn012 | 5 | 0.9984 | 0.9988 | 0.8135 |
| ronin_bridge_2022__hn012 | 7 | 0.9992 | 0.9997 | 0.8135 |
| ronin_bridge_2022__hn012 | 14 | 0.9918 | 0.9894 | 0.8135 |
| ronin_bridge_2022__hn012 | 28 | 0.4807 | 0.9720 | 0.8135 |
| ronin_bridge_2022__hn012 | 42 | 0.2490 | 0.9456 | 0.8135 |
| ronin_bridge_2022__hn012 | 55 | 0.3072 | 0.9715 | 0.8135 |
| ronin_benign_control_2022 | 2 | 0.9923 | 0.9960 | 0.8135 |
| ronin_benign_control_2022 | 3 | 0.9728 | 0.9925 | 0.8135 |
| ronin_benign_control_2022 | 5 | 0.9839 | 0.9012 | 0.8135 |
| ronin_benign_control_2022 | 7 | 0.9737 | 0.8335 | 0.8135 |
| ronin_benign_control_2022 | 26 | 0.9991 | 0.9995 | 0.8135 |
| ronin_benign_control_2022 | 52 | 0.9982 | 0.9994 | 0.8135 |
| ronin_benign_control_2022 | 78 | 0.9978 | 0.9992 | 0.8135 |
| ronin_benign_control_2022 | 103 | 0.9978 | 0.9995 | 0.8135 |

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE.


