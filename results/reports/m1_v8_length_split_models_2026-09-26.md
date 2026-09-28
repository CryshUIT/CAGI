# M1_v8 - model tach theo do dai trajectory (Attempt #14, 2026-09-26)

Nguong phan nhom: SHORT <= 40 action, LONG > 40 action (khe ho tu nhien trong phan phoi do dai that, dung lai tu attempt #7, KHONG tune moi qua nested-CV o attempt nay - ly do: N=15 tach doi con 7-8/nhom, nested-CV tren nhom nho se nhieu, giong bai hoc tu attempt #13).

## Pooled toan bo (15 incident, dung dung sub-model theo nhom)

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v8 (tach theo do dai)** | **0.6378** | [0.4970, 0.8792] |

**Paired diff (M1_v8 - M1 chinh thuc) = -0.0351, 95% CI = [-0.1542, +0.0561]**

**Paired diff (M1_v8 - B3) = +0.0004, 95% CI = [-0.0726, +0.0535]**

## Breakdown rieng tung nhom

| Nhom | n_incident | PR-AUC M1_v8 | PR-AUC M1 chinh thuc | PR-AUC B3 | Paired diff (v8-M1) | CI |
|---|---|---|---|---|---|---|
| SHORT | 7 | 0.6338 | 0.6255 | 0.6548 | -0.0915 | [-0.3354, +0.0893] |
| LONG | 8 | 0.6756 | 0.7230 | 0.7369 | +0.0142 | [-0.0185, +0.0461] |

## KET LUAN (pooled toan bo)

KHONG CAI THIEN CO Y NGHIA THONG KE (pooled toan bo).


