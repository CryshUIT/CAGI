# Ensemble 1a - trung binh calibrate (Platt) M1 + T13 LogReg (2026-09-22)

Gia thuyet: M1 (XGBoost) va T13 (LogReg tren cung feature) co the bat tin hieu khac nhau, trung binh co nguyen tac (Platt calibration, trong so co dinh 0.5/0.5) co the giam phuong sai.

| Model | Mean PR-AUC | 95% CI |
|---|---|---|
| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |
| T13 goc (moc, da co) | 0.7548 | [0.6459, 0.8980] |
| **Ensemble 1a (trung binh Platt)** | **0.7345** | [0.6064, 0.9183] |

**Paired diff (Ensemble - M1 goc) = +0.0401, 95% CI = [+0.0133, +0.0706]**

## KET LUAN

CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed (T12-style) truoc khi tin day la that.
