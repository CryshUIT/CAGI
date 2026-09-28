# T17 - Mimicry stress test (chay 2026-09-22)

## Phuong phap

Chen 0/2/4/8 action THAT (lay tu hard-negative cung incident, khong bia) vao trajectory duong o khe ngau nhien, tinh lai feature qua extract_all_prefixes() that, cham diem bang M1 fit tren 14 incident con lai (hard-negative giu nguyen). Pool 15 incident, bootstrap CI muc incident.

**Doi chieu L=0 voi M1 chinh thuc (0.6624): KHOP (tinh duoc 0.6624) - xac nhan pipeline dung dan.**

## Ket qua

| Muc chen | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| 0 action | 0.6624 | [0.5234, 0.8864] |
| 2 action | 0.6577 | [0.5154, 0.8677] |
| 4 action | 0.6646 | [0.5193, 0.8846] |
| 8 action | 0.6505 | [0.5101, 0.8655] |
