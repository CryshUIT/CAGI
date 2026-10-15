# Bao cao dong bang dataset expansion N30 (N=30) — 2026-10-15

**CHI mo ta, KHONG chay danh gia RQ1/RQ2/model.** Ke tiep sau
`expansion_N30_predeclaration_v1.md` den `v8.md` (giu nguyen, khong sua).

## 1. Ket qua tong quan

- **N cuoi = 30/30** (dat dung chi tieu da khai bao: N=20 + 10 ung vien
  moi dat cong, khong ha chuan, khong can dung den CeFi du phong).
- 20 incident cu (15 v1.0 + 5 N20) **byte-identical** voi N20 (tru 1
  ngoai le da duyet truoc: `hedgey_finance_2024`, 662->755 action, xem
  `N30_allowlist_completion_hedgey_diff_2026-10-14.md`).
- 10 incident moi: **TAT CA 10/10 ung vien da sang loc deu dat cong
  provenance** (khong co ung vien nao bi loai trong lo 1 va lo 2) ->
  khong can mo rong sang nhom CeFi du phong (Kronos Research, BitMart,
  Liquid Exchange).
- 8/8 test tu dong (`test_n30_reproduces_N20.py`,
  `test_n30_manifest_consistency.py`) PASS. Full `pytest tests/ -v`:
  **228/228 PASS**.
- Freeze manifest SHA-256: `metadata/freeze_manifest_N30.json`.

## 2. Danh sach 10 incident moi — endpoint, chain, victim_type

| incident_id | chain | victim_type | endpoint_type | endpoint_confirmed | do tin cay |
|---|---|---|---|---|---|
| dough_finance_2024 | eth | defi_protocol | known_mixer_confirmed | **True** | cao |
| 0xinfini_2025 | eth | bridge | known_bridge_confirmed | **True** | cao |
| prisma_finance_2024 | eth | defi_protocol | known_mixer_confirmed | **True** | cao |
| uranium_finance_2021 | eth | defi_protocol | reported_mixer_not_found_in_tracking_window | False | trung binh |
| inverse_finance_2022_jun | eth | defi_protocol | known_mixer_confirmed | **True** | cao |
| lendhub_2023 | eth | defi_protocol | known_mixer_confirmed | **True** | cao |
| thorchain2_2021 | eth | bridge | reported_mixer_outside_tracking_window | False | cao |
| popsicle_finance_2021 | eth | defi_protocol | reported_mixer_not_recognized_by_pipeline_label | False | cao |
| heco_htx_2023 | eth | bridge + cefi_custodial (HTX exchange) | reported_mixer_outside_tracking_window | False | cao |
| easyfi_2021 | eth | defi_protocol | verified_dex_swap_no_mixer_label | False | cao |

**endpoint_confirmed=True: 5/10. endpoint_confirmed=False: 5/10** (tat ca
5 van DAT cong (3) qua bang chung on-chain thuc te — mixer/DEX/bridge
xac minh — nhung khong thoa dinh nghia literal "endpoint_confirmed" vi
mixer nam ngoai window 72h, hoac khong duoc nhan dien boi co che gan
nhan hien tai).

## 3. Danh sach "bang chung yeu" (mixer/exit KHONG xac nhan day du trong window)

Theo dung yeu cau, gop ca 10 incident cu + moi co van de tuong tu:

| incident_id | ly do bang chung yeu |
|---|---|
| cork_protocol_2025 (N20) | endpoint chua xac nhan, trajectory qua ngan (1 action) |
| uranium_finance_2021 (lo 1) | bao cao neu mixer nhung KHONG tim thay trong window; dat cong qua swap Uniswap V2 thuc te |
| thorchain2_2021 (lo 2) | Tornado Cash deposit ngay 19/07/2021 nam NGOAI window 72h (tre vai tram block); dat cong qua 7 action swap thuc te |
| popsicle_finance_2021 (lo 2) | SlowMist/BlockSec xac nhan ro rang rua tien qua TornadoProxy (4.100 ETH), nhung pipeline KHONG gan nhan "mixer_or_exit" do han che kien truc (protocol_map_N30.yaml khong duoc doc - xem known_builder_limitations.md) |
| heco_htx_2023 (lo 2) | $63M nam im, chi rua qua Tornado Cash tu thang 3/2024 (~4 thang sau, ngoai window); nhanh DEX phu (619.000 USDC qua MetaSwap/RouteProcessor3_2) la bang chung duy nhat trong window |
| easyfi_2021 (lo 2) | bao cao goc chi noi "dark pool" mo ho (WBTC/renBTC), khong xac dinh duoc; dat cong qua 269 swap action THAT toi Uniswap V2 Router phat hien tu on-chain (khong phai tu bao cao) |

## 4. Han che builder da ghi nhan (xem known_builder_limitations.md chi tiet)

- **Hub explosion**: `inverse_finance_2022_jun` (11.592 action) va **moi**
  `easyfi_2021` (16.560-17.166 action, LON HON Inverse) - frontier cham
  cac dia chi do-ket-noi-cao khong lien quan truc tiep (CEX, DEX pho
  bien chua allowlist). Cung co che anh huong CA `ronin_bridge_2022` va
  `radiant_capital_arbitrum_2024` (N=15, da freeze).
- **v2_complexity yield khong deu**: Prisma (1/10), Inverse (1/10) do
  chia se mining contract (Tornado Cash Router) + thu tu xu ly tich luy
  `global_excluded`.
- **protocol_map_N20/N30.yaml chi la tai lieu tham khao**: khong duoc
  `load_protocol_map()` doc, chi anh huong `endpoint_confirmed` cua
  Popsicle Finance (xem muc 3).

## 5. So negative theo incident va vong mine (10 incident moi)

| incident_id | main (muc tieu=25) | v2_complexity (muc tieu=10) | tong |
|---|---|---|---|
| dough_finance_2024 | 25 | 9 | 34 |
| 0xinfini_2025 | 25 | 10 | 35 |
| prisma_finance_2024 | 25 | 1 | 26 |
| uranium_finance_2021 | 25 | 10 | 35 |
| inverse_finance_2022_jun | 25 | 1 | 26 |
| lendhub_2023 | 25 | 5 | 30 |
| thorchain2_2021 | 25 | 10 | 35 |
| popsicle_finance_2021 | 25 | 10 | 35 |
| heco_htx_2023 | 25 | 10 | 35 |
| easyfi_2021 | 25 | 10 | 35 |
| **Tong moi** | **250** | **76** | **326** |

Cong voi negative cu (536 v1.0 main + 110 v1.0 v2c + 125 N20 main + 46 N20
v2c + 5 control = 822): tong RAW = 1148. Sau khi loai cac dong "rong"
(trajectory_len=0, xem `N30_batch1_negative_accounting_2026-10-15.md` ve
co che) va circulate_2023 (auxiliary): **1097 negative thuc su dung
trong `features_v2_N30.parquet`** (1065 mined + 24 control + 8 — xem chi
tiet kind-count muc 6).

## 6. n_actions: min/median/max va danh sach >1000 action

- **min = 1** (cork_protocol_2025), **median = 80.5**, **max = 16.560**
  (easyfi_2021).
- Incident co >1.000 action: `heco_htx_2023` (1.557),
  `ronin_bridge_2022` (1.625, N=15), `inverse_finance_2022_jun` (11.592),
  `easyfi_2021` (16.560) — 4/30 incident, ca 2 incident moi lon nhat
  (`inverse_finance_2022_jun`, `easyfi_2021`) deu la ung vien chiu anh
  huong "hub explosion" (muc 4).

## 7. Tong hop dataset cuoi (features_v2_N30.parquet)

- **1127 trajectory** (30 positive + 1097 negative), **5973 prefix row**.
- Prefix row theo kind: positive=236, hard_negative_control=24,
  hard_negative_mined=4476, hard_negative_mined_v2_complexity=1237.
- **Positive rate sau dedup (muc trajectory, khong phai prefix row)**:
  30/1127 = **2,66%**.
- 0 vi pham invariant chong leakage (action_count_* == prefix_len cho
  toan bo 5973 dong).

## 8. Cac file dong bang (SHA-256 trong `metadata/freeze_manifest_N30.json`)

- `metadata/incident_registry_N30.csv` (36 dong: 30 positive + 5 control
  + 1 auxiliary circulate_2023)
- `metadata/hard_negative_registry_N30_combined.csv` (911 dong)
- `metadata/hard_negative_registry_v2_complexity_N30_combined.csv` (232 dong)
- `metadata/split_manifest_N30.json` (31 group)
- `metadata/protocol_map_N30.yaml`
- `configs/data_N30.yaml`
- `data/processed/features_v2_N30.parquet`
- `configs/features_v2_computed_N30.json`

## 9. Sensitivity analyses da khai bao truoc (chua chay, chi ghi nhan lai)

- N=19 (bo Cork, tu N20).
- N tru Inverse Finance (tu v7).
- **MOI**: N tru EasyFi (de xuat, tuong tu Inverse - da ghi muc 4).
- N tru Cork + Inverse (ket hop).

## 10. DUNG tai day

Theo dung chi dao: KHONG chay bat ky danh gia RQ1/RQ2/model nao o buoc
nay. Cho duyet truoc khi tiep tuc.
