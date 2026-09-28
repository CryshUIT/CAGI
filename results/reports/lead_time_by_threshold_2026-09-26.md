# Lead time theo nguong co dinh theta in {0.5, 0.7, 0.9} - xac suat M1 Platt-calibrated (2026-09-26)

Nguon: `evaluate_model_nested(M1TypedTemporalMotifModel, calibration='platt')` tren pooled dataset da dedupe (methodology giong het M1=0,6624 chinh thuc), khong chon threshold qua CV - ap 3 nguong co dinh de minh hoa trade-off. t_e/t_a dung dung dinh nghia trong `scripts/compute_lead_time.py` (10/15 incident duong tinh du dieu kien: endpoint_confirmed=True va co it nhat 1 action terminal that trong trajectory da decode; 5 bi loai: `ronin_bridge_2022`/`qbridge_qubit_2022`/`hackerdao_2022` co endpoint_confirmed=False, `wault_finance_2021`/`paraluni_2022` co endpoint_confirmed=True nhung khong co action terminal that trong trajectory da decode. Con so nay khac "7/11" trong `results/tables/lead_time_results.csv` cu vi dataset da mo rong tu N=11 len N=15 incident).

**Trade-off quan sat duoc (dung theo so thuc te, khong gia dinh truoc)**: nguong cang cao → tỷ lệ detect-truoc-endpoint giam manh (40% → 30% → 0%) VA false-alert rate tren hard-negative cung giam (0.82% → 0.33% → 0.33%) — ca 2 chieu cung giam, khong phai trade-off "danh doi" theo huong thong thuong (cao hon = it detect hon nhung an toan hon ve false-alert). Ly do: rat it hard-negative dat xac suat cao (>=0.7) ngay tu dau, nen false-alert rate da thap va bao hoa som; trong khi nhieu incident duong tinh CUNG khong bao gio dat xac suat >=0.9 (7/10 "never_alerted" o theta=0.9) vi xac suat sau Platt-calibrate cua nhieu prefix ngan/trung binh khong vuot 0.9 du la true positive — cho thay theta=0.9 qua khat khe cho use-case canh bao som voi model/du lieu hien tai, theta=0.5 la lua chon hop ly hon neu uu tien phat hien truoc endpoint.

| theta | Detected before t_e | Median lead time (h) | IQR lead time (h) | Late detection | Never alerted | False-alert rate (matched negatives) |
|---|---|---|---|---|---|---|
| 0.5 | 4/10 (40%) | 0.68 | [0.12, 1.51] | 4 | 2 | 0.0082 (5/612) |
| 0.7 | 3/10 (30%) | 0.12 | [0.11, 0.21] | 5 | 2 | 0.0033 (2/612) |
| 0.9 | 0/10 (0%) | nan | [nan, nan] | 3 | 7 | 0.0033 (2/612) |
