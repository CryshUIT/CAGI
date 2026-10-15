# Ke hoach phan tich N=30 — PHIEN BAN 3 (2026-10-15)

**CHI la ke hoach/pre-declaration — CHUA chay bat ky model/RQ1/RQ2 nao.**
Thay the v2 lam nguon tham chieu chinh cho buoc chay danh gia tiep theo.
**GIU NGUYEN v1 va v2, khong sua ngam.**

## Changelog so voi v2 (dung 3 thay doi, khong hon)

1. **Them cot `endpoint_basis`** (gia tri: `onchain_value_match` |
   `v1_inherited_report_only` | `other_event_type` | `none`) + 3 cot dem
   (`n_mixer_or_exit`, `n_bridge_deposit`, `type_of_first_endpoint_action`)
   vao `metadata/incident_registry_N30.csv`. **KHONG doi
   `endpoint_confirmed` hay bat ky truong nao khac.**
2. **Dinh nghia lai sensitivity (d) CO HOC, chinh thuc**: `endpoint_confirmed
   == True AND n_mixer_or_exit >= 1` (thay cho mo ta uoc luong khong chinh
   xac truoc day dua tren `mixer_families`). Ket qua: **DUNG 9 incident**
   (khong phai 10 nhu uoc tinh ban dau — xem muc "Known discrepancies").
3. **Bang tong hop 30 incident chuyen sang SINH HOAN TOAN BANG SCRIPT**
   (`scripts/_generate_N30_summary_table.py` ->
   `results/reports/N30_summary_table_generated_2026-10-15.csv`), thay
   cho bang go tay truoc day (da phat hien 3 loi gia tri `chain` do go
   tay trong qua trinh kiem tra v3).

**Giao thuc phan tich chinh (model/split/metric/kiem dinh/4 moc cong
don) KHONG DOI so voi v1/v2. VAN DUNG DUNG 4 sensitivity (a)(b)(c)(d),
KHONG them sensitivity moi.**

## Sensitivity (d) — danh sach CHINH THUC (9 incident, co hoc)

`feg_bridge_2024, new_free_dao_2022, zunami_protocol_2023,
onyx_protocol_2023, beanstalk_farms_2022, dough_finance_2024,
prisma_finance_2024, inverse_finance_2022_jun, lendhub_2023`

(Khong bao gom `xkingdom_2024` — xem Known discrepancies muc 1.)

## Known discrepancies (CHI mo ta, KHONG ket luan nguyen nhan tiep, KHONG sua registry)

Doi chieu nhan `endpoint_type` trong registry voi so dem THAT
(`n_mixer_or_exit`, `n_bridge_deposit`) tu trace — liet ke MOI ca mau
thuan:

1. **xkingdom_2024**: registry ghi `endpoint_type=known_mixer_confirmed`,
   `mixer_families=Tornado Cash Router`. Trace THAT: `n_mixer_or_exit=0`,
   `n_bridge_deposit=20` (Stargate + Across Protocol SpokePool).
   `type_of_first_endpoint_action=bridge_deposit` (vi tri 1/73).
   Nguyen van ghi nhan trong `notes` cua registry (da co tu truoc, KHONG
   phai giai thich moi viet o day): trajectory (chain_primary=arbitrum)
   co 1 bridge_deposit THAT qua Stargate (100,008 ETH); mixer evidence
   (453 ETH vao Tornado Cash Router) duoc xac nhan DOC LAP tren 1 chain
   KHAC (ethereum), NGOAI pham vi trajectory 1-chain-per-incident cua
   schema hien tai — cung mau hinh "evidence thay the" da dung cho FEG
   Bridge truoc do. `endpoint_basis` (co hoc) = `onchain_value_match`
   (qua `bridge_deposit`, KHONG qua mixer, vi mixer nam ngoai trace).
2. **wault_finance_2021**: registry ghi `known_mixer_confirmed`, trace
   THAT `n_mixer_or_exit=0`, `n_bridge_deposit=0`. `endpoint_basis`
   (co hoc) = `v1_inherited_report_only` (han che decoder AnySwap
   burn-to-bridge da biet tu truoc N20).
3. **paraluni_2022**: cung mau hinh voi wault_finance_2021.
   `endpoint_basis` = `v1_inherited_report_only`.
4. **bsc_token_hub_2022**: registry ghi
   `known_bridge_provenance_confirmed`, trace THAT `n_bridge_deposit=0`
   (xac nhan THAT qua `lending_deposit=3`, Venus Protocol — mot
   event_type KHAC, khong phai bridge_deposit). `endpoint_basis` =
   `other_event_type`.

Tat ca 4 ca tren DA duoc giai thich/ghi nhan boi cac bao cao truoc day
trong du an (khong phai phat hien moi lam thay doi ket luan nao) —
muc nay CHI liet ke lai theo yeu cau doi chieu co hoc, KHONG sua bat ky
truong nao trong registry.

## Phan bo endpoint_basis (30 incident positive)

| endpoint_basis | so luong |
|---|---|
| onchain_value_match | 17 |
| none | 10 |
| v1_inherited_report_only | 2 |
| other_event_type | 1 |

## Xac nhan tu code (doc truc tiep, khong suy doan)

`grep -rln "endpoint_confirmed\|endpoint_basis" src/` tra ve **RONG** —
khong co file nao trong `src/` (bao gom `src/models/baselines.py`,
`src/evaluation/nested_eval.py`, `src/features/extractor.py`,
`src/pipeline/dataset_builder.py`) tham chieu toi `endpoint_confirmed`
hay `endpoint_basis`. **RQ1 (PR-AUC pooled, B0-B3, M1, LeaveOneGroupOut,
bootstrap, Wilcoxon) hoan toan KHONG dung 2 truong nay hay vi tri
endpoint** — chi RQ2 va sensitivity (d) dung (qua buoc loc THU CONG
danh sach incident truoc khi dua vao ham danh gia, khong qua feature).

## Bang mo ta theo chain (KHONG suy luan, khong thuoc 4 sensitivity)

| chain | API thu thap | so incident | so positive | so negative | PR-AUC pooled (M1) | PR-AUC pooled (B3) |
|---|---|---|---|---|---|---|
| eth | Etherscan API V2 (chainid=1) | 17 | 17 | 602 | *chua chay* | *chua chay* |
| bsc | NodeReal/MegaNode JSON-RPC | 7 | 7 | 269 | *chua chay* | *chua chay* |
| arbitrum | Etherscan API V2 (chainid=42161) | 6 | 6 | 226 | *chua chay* | *chua chay* |
| **Tong** | | **30** | **30** | **1097** | | |

Cot PR-AUC se duoc dien SAU buoc chay danh gia (ngoai pham vi file nay).

## SHA-256 (sau khi them cot, BAN CUOI dung cho buoc chay danh gia)

- `metadata/incident_registry_N30.csv`: `6c627fdd213423cc962b10e2ea0065ffecc0ef9a9f61a6bfb7476589d08856f9`
  (**DOI so voi v2** — da them 4 cot moi)
- `configs/data_N30.yaml`: `68715892d3be71fe3f2cca7fd4b4d45aff01937dca6ac759acacf865ccb15738`
  (khong doi so voi v2)
- `data/processed/features_v2_N30.parquet`: `848d334199645ab07bba1522712ec0296595b5856245b134d5e332b242cf3535`
  (**KHONG DOI** — xac nhan byte-identical qua 2 lan rebuild doc lap vao
  duong dan tam, truoc va sau khi them cot registry)
- `metadata/freeze_manifest_N30.json`: xem file (da cap nhat ban cuoi,
  bao gom hash moi cua registry)

## Diff v2 -> v3 (tom tat)

```
+ Them cot endpoint_basis, n_mixer_or_exit, n_bridge_deposit,
  type_of_first_endpoint_action vao incident_registry_N30.csv
+ Dinh nghia lai sensitivity (d) co hoc: 9 incident (thay cho uoc tinh
  khong chinh xac truoc day), loai xkingdom_2024 (giai thich trong
  Known discrepancies)
+ Bang tong hop 30 incident sinh hoan toan bang script (khong go tay)
+ Muc "Known discrepancies" (4 ca: xkingdom, wault, paraluni,
  bsc_token_hub) - CHI mo ta, khong sua registry
+ Bang mo ta theo chain (incident/positive/negative, PR-AUC placeholder)
= Giao thuc phan tich chinh, 4 moc cong don, dinh nghia (a)(b)(c) KHONG
  DOI so voi v1/v2
= VAN DUNG DUNG 4 sensitivity (a)(b)(c)(d), khong them sensitivity moi
```

---
*(SHA-256 cua chinh file v3 nay: xem
`results/reports/analysis_plan_N30_v3_selfhash.json`)*
