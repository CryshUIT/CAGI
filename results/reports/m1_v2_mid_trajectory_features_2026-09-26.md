# M1_v2 - 2 feature moi cho mid-trajectory dip (Huong 2, 2026-09-26)

Feature moi: `burstiness_recent_shift` (chenh lech burstiness nua sau vs nua dau prefix), `recent_half_new_counterparty_share` (ty le counterparty MOI xuat hien trong nua sau) - xem `scripts/build_mid_trajectory_features.py` cho dong luc du lieu that va cong thuc chi tiet.

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v2 (+2 feature moi)** | **0.6528** | [0.5128, 0.8836] |

**Paired diff (M1_v2 - M1 chinh thuc) = -0.0027, 95% CI = [-0.0221, +0.0151]**

**Paired diff (M1_v2 - B3) = +0.0328, 95% CI = [-0.0304, +0.1230]**

## Rieng tai checkpoint ratio_50 (241 dong, 15 positive)

PR-AUC(ratio_50): M1_v2=0.8601 vs M1 chinh thuc=0.8749

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc.
