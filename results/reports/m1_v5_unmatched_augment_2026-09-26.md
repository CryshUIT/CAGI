# M1_v5 - bo sung unmatched-negative vao train (Attempt #11, 2026-09-26)

Them toan bo pool 'unmatched negative' (E6, cac candidate bi loai khoi mining hard-negative vi khong khop tieu chi cau truc) cua 14 incident outer-train lam negative BO SUNG (khong thay the) vao tap train moi outer fold - tap test GIU NGUYEN nhu M1 chinh thuc de so sanh duoc.

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v5 (+unmatched augment)** | **0.6152** | [0.5009, 0.8434] |

**Paired diff (M1_v5 - M1 chinh thuc) = +0.0112, 95% CI = [-0.0425, +0.0712]**

**Paired diff (M1_v5 - B3) = +0.0467, 95% CI = [-0.0251, +0.1261]**

## Kiem tra dung 2 ca da chan doan

| source_id | prefix_len | prob moi (M1_v5) | prob M1 chinh thuc | threshold |
|---|---|---|---|---|
| ronin_bridge_2022__hn012 | 2 | 0.9995 | 0.9999 | 0.9934 |
| ronin_bridge_2022__hn012 | 3 | 0.9972 | 0.9999 | 0.9934 |
| ronin_bridge_2022__hn012 | 5 | 0.9883 | 0.9988 | 0.9934 |
| ronin_bridge_2022__hn012 | 7 | 0.9570 | 0.9997 | 0.9934 |
| ronin_bridge_2022__hn012 | 14 | 0.9358 | 0.9894 | 0.9934 |
| ronin_bridge_2022__hn012 | 28 | 0.9899 | 0.9720 | 0.9934 |
| ronin_bridge_2022__hn012 | 42 | 0.9751 | 0.9456 | 0.9934 |
| ronin_bridge_2022__hn012 | 55 | 0.9929 | 0.9715 | 0.9934 |
| ronin_benign_control_2022 | 2 | 0.9984 | 0.9960 | 0.9934 |
| ronin_benign_control_2022 | 3 | 0.9946 | 0.9925 | 0.9934 |
| ronin_benign_control_2022 | 5 | 0.9674 | 0.9012 | 0.9934 |
| ronin_benign_control_2022 | 7 | 0.8680 | 0.8335 | 0.9934 |
| ronin_benign_control_2022 | 26 | 0.9969 | 0.9995 | 0.9934 |
| ronin_benign_control_2022 | 52 | 0.9969 | 0.9994 | 0.9934 |
| ronin_benign_control_2022 | 78 | 0.9981 | 0.9992 | 0.9934 |
| ronin_benign_control_2022 | 103 | 0.9992 | 0.9995 | 0.9934 |

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE.


