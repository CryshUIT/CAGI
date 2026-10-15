# Bang tong hop 30 incident N30 (2026-10-15, SUA LAN 2 — sua 3 loi chain trong bang, doi ten co, them cot trace nho)

**SUA SO VOI BAN TRUOC**: 3 loi nhap lieu `chain` trong CHINH bang nay
(KHONG phai loi trong registry/pipeline — doi chieu `incident_registry_N30.csv`
xac nhan registry dung): `qbridge_qubit_2022` (bang cu ghi sai "eth",
dung la **bsc**), `deltaprime_arbitrum_2024` (bang cu ghi sai "eth", dung
la **arbitrum**), `onyx_protocol_2023` (bang cu ghi sai "bsc", dung la
**eth**). Xem muc 2 cua bao cao kem theo ve nguon goc truong `chain` va
cach dung.

Cot "report_mentions_mixer_not_confirmed" (**doi ten tu "bang chung
yeu"** — ten cu de hieu lam la 1 tieu chi phan tich; ten moi phan anh
dung ban chat: **CHI mo ta**, co quy tac co hoc rieng, xem bao cao kem
theo muc 5 — **KHONG duoc dung trong giao thuc phan tich chinh hay 4
sensitivity (a)(b)(c)(d)**).

Cot moi "trace_nho_hoac_khong_endpoint": `n_actions <= 2 AND
endpoint_confirmed == False`.

| # | incident_id | chain | victim_type | n_actions | endpoint_confirmed | loai endpoint | vi tri action endpoint | neg vong chinh (registry) | neg v2c (registry) | report_mentions_mixer_not_confirmed | trace_nho_hoac_khong_endpoint |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ronin_bridge_2022 | eth | bridge | 1625 | False | khong | khong co | 69 | 10 | | |
| 2 | qbridge_qubit_2022 | **bsc** | bridge | 698 | False | khong | khong co | 35 | 10 | | |
| 3 | feg_bridge_2024 | eth | bridge | 9 | True | mixer | 1/9 | 31 | 10 | | |
| 4 | deltaprime_arbitrum_2024 | **arbitrum** | defi_protocol | 23 | True | bridge | 8/23 | 70 | 10 | | |
| 5 | bsc_token_hub_2022 | bsc | bridge | 362 | True | khac (Venus lending_deposit) | khong co trong mixer/bridge_deposit | 69 | 10 | | |
| 6 | chibi_finance_2023 | arbitrum | defi_protocol | 40 | True | bridge | 19/40 | 25 | 10 | | |
| 7 | wooppv2_2024 | arbitrum | defi_protocol | 16 | True | bridge | 5/16 | 25 | 10 | | |
| 8 | utopiasphere_2024 | bsc | defi_protocol | 37 | True | bridge | 10/37 | 24 | 10 | | |
| 9 | xkingdom_2024 | arbitrum | defi_protocol | 73 | True | mixer+bridge | 1/73 | 22 | 10 | | |
| 10 | wault_finance_2021 | bsc | defi_protocol | 190 | True | mixer (khong co action khop — han che decoder AnySwap burn-to-bridge da biet) | khong co | 22 | 10 | | |
| 11 | paraluni_2022 | bsc | defi_protocol | 511 | True | mixer (cung han che AnySwap) | khong co | 22 | 10 | | |
| 12 | radiant_capital_arbitrum_2024 | arbitrum | defi_protocol | 248 | True | bridge | 7/248 | 25 | 0 | | |
| 13 | magic_abracadabra_arbitrum_2025 | arbitrum | defi_protocol | 88 | True | bridge | 29/88 | 25 | 0 | | |
| 14 | hackerdao_2022 | bsc | defi_protocol | 35 | **False** | mixer (co action, dust ~0,2% gia tri) | 21/35 | 25 | 0 | **x** | |
| 15 | new_free_dao_2022 | bsc | defi_protocol | 12 | True | mixer | 1/12 | 25 | 0 | | |
| 16 | zunami_protocol_2023 | eth | defi_protocol | 31 | True | mixer | 2/31 | 25 | 10 | | |
| 17 | onyx_protocol_2023 | **eth** | defi_protocol | 16 | True | mixer | 2/16 | 25 | 10 | | |
| 18 | beanstalk_farms_2022 | eth | defi_protocol | 443 | True | mixer | 164/443 | 25 | 10 | | |
| 19 | hedgey_finance_2024 | eth | defi_protocol | 755 | False | khong (trajectory doi do KyberSwap - sensitivity c) | khong co | 25 | 6 | | |
| 20 | cork_protocol_2025 | eth | defi_protocol | 1 | False | khong | khong co | 25 | 10 | | **x** |
| 21 | dough_finance_2024 | eth | defi_protocol | 17 | True | mixer | 7/17 | 25 | 9 | | |
| 22 | 0xinfini_2025 | eth | bridge | 25 | True | bridge | 25/25 | 25 | 10 | | |
| 23 | prisma_finance_2024 | eth | defi_protocol | 70 | True | mixer | 12/70 | 25 | 1 | | |
| 24 | uranium_finance_2021 | eth | defi_protocol | 64 | **False** | khong co action khop (mixer bao cao, khong thay trong window) | khong co | 25 | 10 | **x** | |
| 25 | inverse_finance_2022_jun | eth | defi_protocol | 11592 | True | mixer | 122/11592 | 25 | 1 | | |
| 26 | lendhub_2023 | eth | defi_protocol | 274 | True | mixer | 123/274 | 25 | 5 | | |
| 27 | thorchain2_2021 | eth | bridge | 99 | **False** | khong co action khop (mixer ngoai window 72h) | khong co | 25 | 10 | **x** | |
| 28 | popsicle_finance_2021 | eth | defi_protocol | 980 | **False** | khong co action khop (mixer that, khong duoc gan nhan) | khong co | 25 | 10 | **x** | |
| 29 | heco_htx_2023 | eth | bridge+cefi_custodial | 1557 | **False** | co bridge_deposit (LI.FI, 6 action, GIA TRI NHO/khong khop bao cao) | bridge: 475/1557 | 25 | 10 | **x** | |
| 30 | easyfi_2021 | eth | defi_protocol | 16560 | **False** | khong (chi co swap DEX) | khong co | 25 | 10 | **x** | |

## Bang dem THAT theo incident (tu features_v2_N30.parquet, KHAC voi cot "registry" o tren)

| incident_id | neg main (registry) | neg main (THAT, parquet) | neg v2c (registry) | neg v2c (THAT, parquet) | control (THAT) | prefix row positive | prefix row positive sau dedup |
|---|---|---|---|---|---|---|---|
| ronin_bridge_2022 | 69 | 65 | 10 | 9 | 1 | 8 | 8 |
| qbridge_qubit_2022 | 35 | 35 | 10 | 10 | 1 | 8 | 8 |
| feg_bridge_2024 | 31 | 31 | 10 | 10 | 1 | 8 | 5 |
| deltaprime_arbitrum_2024 | 70 | 66 | 10 | 8 | 1 | 8 | 8 |
| bsc_token_hub_2022 | 69 | 67 | 10 | 10 | 1 | 8 | 8 |
| chibi_finance_2023 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| wooppv2_2024 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| utopiasphere_2024 | 24 | 23 | 10 | 10 | 0 | 8 | 8 |
| xkingdom_2024 | 22 | 22 | 10 | 10 | 0 | 8 | 8 |
| wault_finance_2021 | 22 | 22 | 10 | 10 | 0 | 8 | 8 |
| paraluni_2022 | 22 | 22 | 10 | 10 | 0 | 8 | 8 |
| radiant_capital_arbitrum_2024 | 25 | 25 | 0 | 0 | 0 | 8 | 8 |
| magic_abracadabra_arbitrum_2025 | 25 | 24 | 0 | 0 | 0 | 8 | 8 |
| hackerdao_2022 | 25 | 25 | 0 | 0 | 0 | 8 | 8 |
| new_free_dao_2022 | 25 | 23 | 0 | 0 | 0 | 8 | 7 |
| zunami_protocol_2023 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| onyx_protocol_2023 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| beanstalk_farms_2022 | 25 | 24 | 10 | 9 | 0 | 8 | 8 |
| hedgey_finance_2024 | 25 | 24 | 6 | 5 | 0 | 8 | 8 |
| cork_protocol_2025 | 25 | 24 | 10 | 10 | 0 | 4 | 1 |
| dough_finance_2024 | 25 | 25 | 9 | 9 | 0 | 8 | 7 |
| 0xinfini_2025 | 25 | 24 | 10 | 10 | 0 | 8 | 7 |
| prisma_finance_2024 | 25 | 25 | 1 | 1 | 0 | 8 | 8 |
| uranium_finance_2021 | 25 | 23 | 10 | 10 | 0 | 8 | 8 |
| inverse_finance_2022_jun | 25 | 25 | 1 | 1 | 0 | 8 | 8 |
| lendhub_2023 | 25 | 24 | 5 | 5 | 0 | 8 | 8 |
| thorchain2_2021 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| popsicle_finance_2021 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| heco_htx_2023 | 25 | 25 | 10 | 10 | 0 | 8 | 8 |
| easyfi_2021 | 25 | 24 | 10 | 8 | 0 | 8 | 8 |
| **TONG** | **886** (registry, chua gom 25 dong v1.0 control cu rieng) | **867** | **236** | **225** | **5** | **236** | **220** |

**Tong negative THAT (muc trajectory, khop CHINH XAC voi
`df.kind.value_counts()` tren toan bo `features_v2_N30.parquet`,
KHONG loc theo group) = 867 (hard_negative_mined) + 225
(hard_negative_mined_v2_complexity) + 5 (hard_negative_control) =
**1097** — khop dung voi so da bao cao cac lan truoc.** (Loi tinh tay
truoc do khi cong cot "main (THAT)" bi ghi nham 843 — da sua lai dung
867; cac dong theo tung incident trong bang tren luon dung, chi dong
TONG bi tinh sai o 1 lan bao cao truoc.)

## Tong (giu nguyen cac so da xac nhan on dinh, KHONG bi anh huong boi
dinh chinh o tren)

- **Positive: 30.**
- **Prefix row (raw): 5973. Sau dedup (`dedupe_pooled_prefixes`): 3074.**
- **Positive rate**: raw = 3,95%; **sau dedup = 7,38%**.
- **endpoint_confirmed**: 20/30 True, 10/30 False.
- **report_mentions_mixer_not_confirmed (6 incident, CHI MO TA — khong
  dung trong phan tich chinh/4 sensitivity)**: hackerdao_2022,
  uranium_finance_2021, thorchain2_2021, popsicle_finance_2021,
  heco_htx_2023, easyfi_2021. Quy tac co hoc: `endpoint_confirmed==False
  AND mixer_families khac rong`.
- **trace_nho_hoac_khong_endpoint (1 incident)**: cork_protocol_2025
  (n_actions=1, endpoint_confirmed=False).
- **Sensitivity (c) — 6 incident (xem analysis_plan_N30_v2.md)**:
  hedgey_finance_2024, prisma_finance_2024, uranium_finance_2021,
  popsicle_finance_2021, heco_htx_2023, easyfi_2021.
- **SHA-256 freeze manifest BAN CUOI** (`metadata/freeze_manifest_N30.json`,
  xac nhan `features_v2_N30.parquet` KHONG DOI hash truoc/sau 2 lan sua):
  - incident_registry_N30.csv: `0e9272e8ae966e723bfbf3e1f8fcf30920b0585a5ddf1ab4243e61057e2cacfe`
  - hard_negative_registry_N30_combined.csv: `52e50d081ce7ac1f6d3b3e71c5f9c27dce7583dec385269ecdee9368d7bf4d62`
  - hard_negative_registry_v2_complexity_N30_combined.csv: `eed15f7136a8ef7d339ecf4926fa1cce0180c8be076c9d7d0f5032d718bfffc1`
  - split_manifest_N30.json: `94b46b9c655709521a199e81ff4b1c8db54d2fa21d77ec219ece9ae23e9228bf`
  - protocol_map_N30.yaml: `6f9fa7225a3f4796f2df3cb30f67ef82a86bae8c06c6e3400622984813a0a8fc`
  - data_N30.yaml: `68715892d3be71fe3f2cca7fd4b4d45aff01937dca6ac759acacf865ccb15738`
  - **features_v2_N30.parquet: `848d334199645ab07bba1522712ec0296595b5856245b134d5e332b242cf3535` (KHONG DOI truoc/sau 2 sua doi tren — da xac nhan truc tiep)**
  - features_v2_computed_N30.json: `292954d995323e5ac3844b93c2695c0bcaeff934f90e35e45e328a6f239bff00`
- **`results/reports/N30_DECISIONS_NEEDED.md`**: KHONG TON TAI.
