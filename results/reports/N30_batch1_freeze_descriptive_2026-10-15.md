# N30 Batch 1 — Freeze mo ta (CHUA chay model) — 2026-10-15

**TRANG THAI**: Dong bang `incident_registry_N30_active.csv` (23 incident:
20 N20 cu + 3 moi: Dough Finance, Prisma Finance, Inverse Finance 06/2022).
**Uranium Finance va 0xInfini TAM DUNG** (da qua cong provenance, CHUA mine
negative, CHUA co trong file active/feature nay) — xem
`results/reports/N30_batch1_gate_and_endpoint_review_2026-10-15.md`.

`pytest tests/`: **222/222 PASS**. Manifest SHA-256 day du:
`results/reports/freeze_N30_batch1_manifest_2026-10-15.json`.

## Bang mo ta day du (theo yeu cau — se duoc ra soat truoc khi chay danh gia)

| Incident | victim_type | chain | n_actions | endpoint_confirmed | Vi tri endpoint (index/ty le) | So negative (chinh+v2c) |
|---|---|---|---|---|---|---|
| ronin_bridge_2022 | bridge | eth | 1625 | False | — | 79 |
| qbridge_qubit_2022 | bridge | bsc | 698 | False | — | 45 |
| feg_bridge_2024 | bridge | eth | 9 | True | — (chua do lai) | 41 |
| deltaprime_arbitrum_2024 | defi_protocol | arbitrum | 23 | True | — | 80 |
| bsc_token_hub_2022 | bridge | bsc | 362 | True | — | 79 |
| chibi_finance_2023 | defi_protocol | arbitrum | 40 | True | — | 35 |
| wooppv2_2024 | defi_protocol | arbitrum | 16 | True | — | 35 |
| utopiasphere_2024 | defi_protocol | bsc | 37 | True | — | 34 |
| xkingdom_2024 | defi_protocol | arbitrum | 73 | True | — | 32 |
| wault_finance_2021 | defi_protocol | bsc | 190 | True | — | 32 |
| paraluni_2022 | defi_protocol | bsc | 511 | True | — | 32 |
| radiant_capital_arbitrum_2024 | defi_protocol | arbitrum | 248 | True | — | 25 |
| magic_abracadabra_arbitrum_2025 | defi_protocol | arbitrum | 88 | True | — | 25 |
| hackerdao_2022 | defi_protocol | bsc | 35 | False | — | 25 |
| new_free_dao_2022 | defi_protocol | bsc | 12 | True | — | 25 |
| zunami_protocol_2023 | defi_protocol | eth | 31 | True | 1/31 (0,032) | 35 |
| onyx_protocol_2023 | defi_protocol | eth | 16 | True | 1/16 (0,062) | 35 |
| beanstalk_farms_2022 | defi_protocol | eth | 443 | True | 162/443 (0,366)* | 35 |
| **hedgey_finance_2024** | defi_protocol | eth | **755**\*\* | False | — | 31 |
| cork_protocol_2025 | defi_protocol | eth | 1 | False | — | 35 |
| **dough_finance_2024** | defi_protocol | eth | **17** | **True** | **6/17 (0,353)** | **35 (25+10)** |
| **prisma_finance_2024** | defi_protocol | eth | **70** | **True** | **11/70 (0,157)** | **30 (25+5)** |
| **inverse_finance_2022_jun** | defi_protocol | eth | **11.592** | **True** | **121/11.592 (0,0104)** | **35 (25+10)** |

\* Vi tri cho beanstalk/zunami/onyx tinh TRUOC khi them batch 1 (chua tinh
lai duoi config N30, nhung Checkpoint truoc xac nhan n_actions cua 3
incident nay KHONG doi giua N20/N30, nen vi tri van dung).
\*\* hedgey_finance_2024 thay doi tu 662 -> 755 do "allowlist completion"
(KyberSwap), CHAP NHAN theo quyet dinh v4, dua vao sensitivity rieng.

**In dam** = 3 incident moi cua batch 1 nay.

## Tong hop so

- **So incident active (dua vao feature)**: 23 (20 N20 + 3 moi).
- **So incident TAM DUNG (da qua provenance, chua tinh)**: 2 (Uranium
  Finance, 0xInfini).
- **endpoint_confirmed=True**: 18/23 active (= 15/20 N20 + Dough + Prisma +
  Inverse, ca 3 incident moi deu True).
- **lead-time-evaluable (dieu kien CAN — co terminal action + endpoint_confirmed,
  CHUA tinh dieu kien DU phu thuoc model)**: can tinh lai chinh xac cho 23
  incident (da tinh truoc cho 20 incident N20 = 13/20 — xem Checkpoint C''),
  **CHUA tinh rieng cho 3 incident moi o day (ngoai pham vi "chi mo ta")
  nhung CA 3 deu CO endpoint action THAT trong trajectory (6/54/65 action
  tuong ung) nen CA 3 deu DAT dieu kien CAN**.
- **victim_type**: 23/23 la `defi_protocol` hoac `bridge` — **0
  `cefi_custodial`** (Kronos/BitMart/Liquid van chua duoc xu ly, nam trong
  danh sach xep hang nhung chua den luot).
- **Phan bo chain** (901 trajectory, ratio_100): eth=393, bsc=276,
  arbitrum=232.
- **So hard-negative**: 697 usable "chinh" (tren 714 eligible, 17 rong) +
  176 usable "v2_complexity" (tren 181, 5 rong) = **873 hard-negative usable
  tong cong**.
- **Prefix row (RAW, truoc dedupe)**: 4.713.
- **Prefix row (DEDUP, dung cho RQ1 that)**: 2.403.
- **Positive rate (DEDUP)**: **7,16%** (so voi N20: 7,09%, N=15: 6,50% —
  tang nhe, NHAT QUAN voi xu huong tang nhe da thay khi mo rong tu N=15 len
  N=20).

## Luu y quan trong cho ban khi ra soat

1. **Inverse Finance la incident DAI NHAT trong toan bo dataset** (11.592
   action, gap xa so voi ronin_bridge_2022 1.625) — da xac nhan la bung no
   DIEN RONG (khong qua 1 hub, xem bao cao rieng), KHONG phai loi.
2. **0xInfini's endpoint (neu resume) la truong hop "dust" nhat tu truoc
   den nay** (9,62 USDC / $49,5M) — can quyet dinh co ap dung them nguong
   gia tri hay khong (hien CHUA co, giu nguyen quy tac dinh tinh cu).
3. **hedgey_finance_2024 la incident DUY NHAT bi doi so voi freeze N=20**
   (755 vs 662, do allowlist completion) — da co sensitivity rieng.
4. **Uranium Finance va 0xInfini dang TAM DUNG** — can quyet dinh resume
   hay loai truoc khi tiep tuc Phase 2 (Lendhub va cac ung vien sau trong
   hang doi vong 1).

## Diem dung

Theo dung yeu cau: **DUNG O DAY, CHUA chay RQ1/RQ2/danh gia nao** — gui bang
mo ta nay de nguoi dung ra soat truoc.
