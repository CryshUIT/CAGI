# N30 Progress Tracker (che do khong giam sat, bat dau 2026-10-15)

Cap nhat file nay sau MOI buoc. Neu phien bi ngat, noi "tiep tuc tu
N30_progress.md" - doc muc "Buoc tiep theo" de biet lenh can chay.

## Da hoan tat

- **Lo 1 (5 incident)**: dough_finance_2024, prisma_finance_2024,
  uranium_finance_2021, 0xinfini_2025, inverse_finance_2022_jun - DAT cong
  provenance, da mining (main+v2c), da vao registry/manifest.
- **Lo 2 batch 1 (4 incident)**: lendhub_2023 (PASS, endpoint_confirmed=True),
  thorchain2_2021 (PASS, endpoint_confirmed=False - mixer ngoai window),
  popsicle_finance_2021 (PASS, endpoint_confirmed=False - TornadoProxy
  khong duoc pipeline nhan dien, xem known_builder_limitations.md),
  heco_htx_2023 (PASS, endpoint_confirmed=False - nhanh DEX la phu, rua
  tien chinh ngoai window) - da mining (main+v2c), da vao registry/manifest.
- Allowlist da them (predeclaration v8): MetaSwap, SushiSwap
  RouteProcessor3_2 (cho HECO), TornadoProxy (cho Popsicle) - CA 3 da
  kiem tra dong nhat TACH RIENG + gop, 612 negative v1.0 KHONG DOI.
- Phat hien quan trong (da ghi known_builder_limitations.md):
  protocol_map_N20.yaml/protocol_map_N30.yaml CHI la tai lieu tham khao,
  KHONG duoc pipeline doc (load_protocol_map() luon doc file goc).
- metadata/hard_negative_registry_N30_combined.csv: 886 dong (536 v1.0 +
  125 N20 + 125 lo1 + 100 lo2b1).
- metadata/hard_negative_registry_v2_complexity_N30_combined.csv: 222 dong
  (110 v1.0 + 46 N20 + 31 lo1 + 35 lo2b1).
- metadata/split_manifest_N30.json: 30 group (21 N20 cu + 5 lo1 + 4 lo2b1).
- metadata/incident_registry_N30.csv: 35 dong (26 cu + 5 lo1 + 4 lo2b1).
- **N hien tai = 29** (20 cu + 5 lo1 + 4 lo2b1).

## Da hoan tat (tiep)

- Build `features_v2_N30.parquet` voi 29 incident (20 cu + 5 lo1 + 4
  lo2 batch1): 1094 trajectory (29 positive, 1065 negative), 5793 prefix
  row, 0 vi pham leakage. 8/8 test (`test_n30_reproduces_N20.py` +
  `test_n30_manifest_consistency.py`) PASS - ranh gioi cung (612 negative
  v1.0) nguyen ven, chi hedgey_finance_2024 (N20, soft boundary) khac
  (da duoc duyet truoc).
- **N hien tai = 29.**
- EasyFi: dang kiem tra provenance (WebSearch cho thay nguon cu "khong
  tim thay bang chung exit" nhung kiem tra on-chain THAT lai phat hien
  seed co goi truc tiep toi Uniswap V2 Router (0x7a250d563...) da
  allowlist - DANG build thuc te de xac nhan (lenh dang chay nen).

## Da hoan tat (tiep 2)

- **EasyFi: DAT cong (3)** qua on-chain THAT (khong phai tu bao cao - bao
  cao goc chi noi "dark pool" mo ho) - seed goi TRUC TIEP Uniswap V2
  Router 269/2166 swap action. Build thuc te BUNG NO cuc lon (n_actions
  16560-17166 tuy lan build, n_processed ~2369) - **LON HON Inverse
  Finance**, ghi vao known_builder_limitations.md. endpoint_confirmed=
  False (chi co swap, khong co mixer_or_exit).
- Mining EasyFi: main 25/25, v2_complexity 10/10 (Uniswap V2 Router lam
  mining contract, cung fallback Uranium/THORChain-2).
- Merge negative cuoi: main combined=911 dong, v2c combined=232 dong.
- split_manifest_N30.json: 31 group (30 primary + 1 auxiliary
  circulate_2023).
- Build feature CUOI: 1127 trajectory (30 positive + 1097 negative),
  5973 prefix row, 0 leakage violation.
- **8/8 test dong nhat PASS** (test_n30_reproduces_N20.py +
  test_n30_manifest_consistency.py) - ranh gioi cung (612 negative v1.0)
  nguyen ven o N=30.
- **N = 30/30 - DAT MUC TIEU.** DUNG tim them ung vien (khong can CeFi
  du phong).

## DA XONG — TRANG THAI CUOI (2026-10-15)

- **Full `pytest tests/ -v`: 228/228 PASS.**
- `metadata/freeze_manifest_N30.json` da tinh SHA-256 cho 8 file dataset
  chinh.
- Bao cao mo ta cuoi cung da viet:
  `results/reports/N30_final_freeze_report_2026-10-15.md` (day du: so
  incident, endpoint_confirmed, victim_type, chain, n_actions, danh sach
  bang chung yeu, so negative theo incident/vong, positive rate sau
  dedup).
- **N = 30/30. DA DONG BANG. DA DUNG theo chi dao - KHONG chay RQ1/RQ2.**

Khong co viec gi con lai o buoc nay. Neu quay lai phien sau, doc
`N30_final_freeze_report_2026-10-15.md` truoc khi lam gi tiep (vd chay
RQ1/RQ2 - can duoc duyet rieng).

## Lenh de tiep tuc (neu phien bi ngat)

```
cd "D:\DAI HOC\cagi-ed"
python -m pytest tests/test_n30_reproduces_N20.py tests/test_n30_manifest_consistency.py -v
```
Neu pass, tiep tuc kiem tra provenance EasyFi (buoc 2 tren).

## Ghi chu cam

- KHONG sua/ghi de/xoa file freeze v1.0/N20.
- KHONG sua code pipeline (load_protocol_map, decoder, builder).
- KHONG commit/push.
- KHONG chay model/RQ1/RQ2.
- Gap quyet dinh ngoai pham vi quy tac da khai bao (v1-v8) -> ghi
  `results/reports/N30_DECISIONS_NEEDED.md`, danh dau ung vien "do",
  tiep tuc ung vien ke.
