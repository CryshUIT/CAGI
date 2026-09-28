# M1_v7 - tinh chinh ty le unmatched-negative them vao train (Attempt #13, 2026-09-26)

Chon top-K% TRAJECTORY unmatched theo fan_out LON NHAT (do phuc tap cau truc cao nhat) - K chon qua nested inner-CV moi outer fold trong {0%, 10%, 25%, 50%}.

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v7 (ty le unmatched tuned)** | **0.6259** | [0.4989, 0.8387] |

**Paired diff (M1_v7 - M1 chinh thuc) = -0.0451, 95% CI = [-0.1157, +0.0135]**

**Paired diff (M1_v7 - B3) = -0.0096, 95% CI = [-0.1302, +0.1151]**

## Kiem tra dung 2 ca da chan doan: 5/16 dong fixed

| source_id | prefix_len | prob moi (M1_v7) | prob M1 chinh thuc | threshold | fixed? |
|---|---|---|---|---|---|
| ronin_bridge_2022__hn012 | 2 | 0.9997 | 0.9999 | 0.9452 | KHONG |
| ronin_bridge_2022__hn012 | 3 | 0.9986 | 0.9999 | 0.9452 | KHONG |
| ronin_bridge_2022__hn012 | 5 | 0.9351 | 0.9988 | 0.9452 | CO |
| ronin_bridge_2022__hn012 | 7 | 0.4442 | 0.9997 | 0.9452 | CO |
| ronin_bridge_2022__hn012 | 14 | 0.9612 | 0.9894 | 0.9452 | KHONG |
| ronin_bridge_2022__hn012 | 28 | 0.9958 | 0.9720 | 0.9452 | KHONG |
| ronin_bridge_2022__hn012 | 42 | 0.9848 | 0.9456 | 0.9452 | KHONG |
| ronin_bridge_2022__hn012 | 55 | 0.9924 | 0.9715 | 0.9452 | KHONG |
| ronin_benign_control_2022 | 2 | 0.9863 | 0.9960 | 0.9452 | KHONG |
| ronin_benign_control_2022 | 3 | 0.9189 | 0.9925 | 0.9452 | CO |
| ronin_benign_control_2022 | 5 | 0.5075 | 0.9012 | 0.9452 | CO |
| ronin_benign_control_2022 | 7 | 0.4239 | 0.8335 | 0.9452 | CO |
| ronin_benign_control_2022 | 26 | 0.9995 | 0.9995 | 0.9452 | KHONG |
| ronin_benign_control_2022 | 52 | 0.9967 | 0.9994 | 0.9452 | KHONG |
| ronin_benign_control_2022 | 78 | 0.9993 | 0.9992 | 0.9452 | KHONG |
| ronin_benign_control_2022 | 103 | 0.9996 | 0.9995 | 0.9452 | KHONG |

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE.


