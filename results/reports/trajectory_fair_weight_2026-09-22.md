# Trajectory-fair sample weight cho M1 (LAN THU 6, 2026-09-22)

Gia thuyet: trajectory dai dong gop nhieu dong prefix hon (sau dedupe), co the khien model hoc lech ve dac diem trajectory dai, giam hieu nang tren trajectory ngan.

Trong so: `weight = 1 / so_dong_prefix_cua_chinh_trajectory_do` (tong trong so moi trajectory = 1), NHAN voi scale_pos_weight co san (khong thay the).

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |
| **M1 + trajectory-fair weight** | **0.6970** | [0.5551, 0.9085] |

**Paired diff (TrajFairWeight - M1 goc) = -0.0306, 95% CI = [-0.1205, +0.0458]**

**Trung binh diff tren nhom incident NGAN** (<=40 action, n=7): -0.0731

**Trung binh diff tren nhom incident DAI** (>=73 action, n=8): +0.0065

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc. DUNG o day, khong thu bien the khac.
