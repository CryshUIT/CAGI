# N30 — Allowlist completion: bang diff Hedgey (2026-10-14)

Nguyen nhan: them `KyberSwap: Meta Aggregation Router v2`
(`0x6131b5fae19ea4f9d964eac0408e4408b66337b5`) vao `dex_allowlist` cua
`configs/data_N30.yaml` (phat hien qua provenance Prisma Finance) lam thay
doi trajectory Hedgey (da co trong N20) — dia chi nay vo tinh cham vao
trajectory Hedgey tu truoc nhung chua duoc allowlist.

## Bang diff

| | N20 (config cu, chua co KyberSwap) | N30 (config moi, co KyberSwap) |
|---|---|---|
| n_actions | 662 | **755** (+93) |
| n_mixer_or_exit | 0 | 0 (khong doi) |
| n_bridge_deposit/withdraw | 0 | 0 (khong doi) |
| endpoint_confirmed (registry flag) | False | False (khong doi — van KHONG tim thay endpoint) |
| So prefix bucket (k_2/3/5/7, ratio_25/50/75/100) | 8 | 8 (khong doi so luong bucket) |
| So dong positive (label=1) sinh ra | 8 | 8 (khong doi — Hedgey chi co trajectory positive, khong co negative rieng) |

## Action them/mat (phan loai theo event_type)

- **216 action MOI xuat hien** (tat ca la `transfer`, KHONG co `swap`/`mixer_or_exit`/
  `bridge_*` moi) — la cac giao dich tu nhieu dia chi trung gian khac nhau
  **DEN** KyberSwap Router (vd `0xf081470f...`, `0x1e8b6ac3...` -> `0x6131b5fa...`),
  gia tri nho (0,04-0,14 log-scale). Day la cac leg truoc day KHONG duoc giu
  vi KyberSwap chua duoc coi la "sink" da biet.
- **123 action BIEN MAT** — cac leg DI TIEP SAU KyberSwap (frontier truoc day
  mo rong QUA KyberSwap toi cac dia chi khac; nay KyberSwap duoc coi la diem
  dung "sink" nen khong mo rong tiep nhu truoc).
- Net: +216 - 123 = **+93** (662 -> 755), khop voi so da bao cao.

## Ket luan

Thay doi CHI anh huong SO LUONG VA NOI DUNG action, KHONG anh huong co
(endpoint_confirmed=False khong doi) hay so dong positive/bucket sinh ra.
Theo quyet dinh v4: **CHAP NHAN** gia tri moi (755) lam so chinh thuc cho
Hedgey duoi config N30, dua vao sensitivity rieng ("bo incident bi doi do
allowlist completion") de doi chieu.
