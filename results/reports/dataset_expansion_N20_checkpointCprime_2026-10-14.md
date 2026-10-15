# Checkpoint C' — Kiem tra doc lap truoc Checkpoint D (2026-10-14)

**KET LUAN NGAN GON: Muc 6 phat hien 1 LOI CAU HINH THAT (config khong duoc
truyen dung vao `load_rq1_trajectories()`, khien toan bo N20 vo tinh dung
allowlist GOC thay vi allowlist N20 co Universal Router). Theo dung quy tac
da CHOT, day la dieu kien DUNG. Da SUA loi nay (chi 1 dong code trong
`scripts/build_features_v2_N20.py`, truyen them `config=`), rebuild lai
toan bo, chay lai pytest (207/207 pass), cap nhat manifest. BAO CAO LAI va
DUNG O DAY — CHUA chay Checkpoint D.**

## 1. Script sach

### git status / git diff --stat (scripts/, src/, configs/)

```
git diff --stat -- src/ scripts/ configs/
 src/models/baselines.py | 18 +++++++++++++++---
 1 file changed, 15 insertions(+), 3 deletions(-)
```

**Chi 1 file tracked bi doi: `src/models/baselines.py`** — day la fix leak
`prefix_ratio` DA DUOC NGUOI DUNG XAC NHAN RIENG o nhiem vu truoc, KHONG
lien quan Checkpoint N20 nay. Khong co file nao khac trong `src/`
(`dataset_builder.py`, `incident_pipeline.py`, `hard_negative_miner.py`,
`trajectories/builder.py`...) bi doi — toan bo tuy chinh cho N20 deu qua
**monkeypatch runtime trong script rieng** (khong sua file nguon).

File moi (untracked, `??`): `configs/data_N20.yaml`,
`configs/features_v2_computed_N20.json`, `scripts/_mine_hard_negatives_N20.py`,
`scripts/_run_real_pipeline_N20_seeds.py`, `scripts/build_features_v2_N20.py`,
cac script kiem tra prefix_ratio tu nhiem vu truoc (khong lien quan N20).

### Script "da restore" — luu y quan trong ve pham vi xac minh

2 script `scripts/_mine_hard_negatives_N20.py` va
`scripts/_run_real_pipeline_N20_seeds.py` **CHUA TUNG duoc commit** (hoan
toan moi, tao trong phien lam viec nay) — nen "giong het HEAD" KHONG AP
DUNG duoc theo nghia git (khong co phien ban HEAD nao de so sanh). Dieu co
the xac minh duoc: sau khi toi lo xoa nham 2 file nay (bang `rm`) o buoc
bao cao Checkpoint B/C truoc, toi da **chep lai y het noi dung** tu chinh
cac lenh `Write` da dung de tao chung ban dau (noi dung van con trong ngu
canh cuoc tro chuyen). Da xac minh lai: ca 2 file parse duoc bang `ast.parse()`
(cu phap hop le), so dong khop (168 va 54 dong), va **da chay lai thanh
cong, cho ra dung ket qua da bao cao truoc do** (hard-negative 125 dong,
trajectory N20 dung so lieu) — day la bang chung GIAN TIEP manh nhat rang
noi dung restore dung, vi neu sai, cac buoc chay lai sau do (feature build,
pytest) se that bai hoac cho so lieu khac.

**Sua tam thoi duy nhat** (khong phai "restore", ma la SUA LOI THAT, xem
muc 6): `scripts/build_features_v2_N20.py` — them `config=load_trajectory_config(data_N20.yaml)`
vao loi goi `load_rq1_trajectories()` (truoc do thieu, mac dinh dung
`configs/data.yaml` goc). Ly do: xem muc 6.

### Cache incident_id tam — xac nhan KHONG con bi pipeline doc

`grep -rl "provenance_check|dryrun_traffic|quota_test_2026" src/ scripts/*.py`
→ **0 ket qua** (ngoai chinh 2 file da kiem tra o tren, cung khong chua
chuoi nay). Cac thu muc cache `data/raw/.../{dia_chi}/{incident_id_tam}/`
(vd `zunami_2023_provenance_check`) van TON TAI tren dia (khong xoa, vo hai,
nam trong `.gitignore`) nhung **khong co bat ky code nao con tham chieu
toi cac incident_id tam nay** — pipeline chinh thuc CHI doc theo incident_id
THAT (`zunami_protocol_2023` v.v.) tu `incident_registry_N20.csv`.

### Khong co incident nao bi dem 2 lan (xac minh bang code, khong doan)

- `set(old_incident_id) & (set(new_incident_id) - set(old_incident_id))` =
  **rong** (5 incident moi hoan toan tach biet voi 15 incident cu).
- `hard_negative_id` trung giua `hard_negative_registry.csv` (cu) va
  `hard_negative_registry_N20.csv` (moi): **rong**.
- Seed address cua 5 incident moi trung voi bat ky hard-negative nao (cu
  hoac moi): **rong** (khong co group leakage).
- `group_id` distinct trong `features_v2_N20.parquet` (ratio_100): **20**
  (dung bang 20 incident, khong nhieu hon).
- `source_id` (tung trajectory) distinct trong ratio_100: **754**, trung
  lap: **0**.

## 2. Bang doi chieu v1.0 (N=15) vs N20 (N=20)

| Chi tieu | v1.0 (freeze, N=15) | N20 (N=20) | Dinh nghia |
|---|---|---|---|
| So incident positive | 15 | 20 | `eval_tier=primary, label=1` trong registry |
| Hard-negative quy tac chinh | 536 | 536 cu + 125 moi = **661** | `hard_negative_registry*.csv`, mine qua `mine_hard_negatives_for_incident` |
| Hard-negative "v2_complexity" | 110 | 110 (khong doi) | `hard_negative_registry_v2_complexity.csv`, tieu chi do phuc tap bo sung (chi ap dung cho 15 incident cu, chua lam cho 5 incident moi) |
| Control thu cong (5 vu dau) | 5 | 5 (khong doi) | `hard_negative_control` trong registry, label=0, khong qua mining |
| Trajectory usable (sau build that) | 627 | **754** | `ratio_100` distinct source_id |
| Prefix row (RAW, truoc dedupe) | 3.354 | **4.004** | Tat ca 8 bucket/trajectory, truoc `dedupe_pooled_prefixes` |
| Prefix row (DEDUP, dung cho RQ1 that) | 1.785 | **2.101** | Sau `dedupe_pooled_prefixes()` |
| Positive rate - TRAJECTORY level (ratio_100) | 2,39% | 2,65% | (so trajectory label=1)/(tong trajectory) |
| Positive rate - PREFIX level, RAW | 3,58% | 3,90% | (so dong label=1)/(tong dong), CHUA dedupe |
| **Positive rate - PREFIX level, DEDUP (so sanh DUNG voi "6,5%")** | **6,50%** | **7,09%** | Sau dedupe, day la ty le THAT dung trong RQ1/main_table.csv |
| So incident endpoint_confirmed=True | 12/15 | **15/20** | Cot `endpoint_confirmed` trong registry, xem muc 5 |

### Giai thich "20 + 661 ≠ 754"

```
754 = 20 (positive, 100% usable)
    + 5 (control, 100% usable)
    + 622 (hard_negative_mined USABLE, trong so 639 dong eligible)
    + 107 (v2_complexity USABLE, trong so 110 dong)
```

- **661 hard-negative "quy tac chinh"** TRU DI **22 dong thuoc
  `circulate_2023`** (incident auxiliary, KHONG thuoc RQ1 chinh, bi loai
  TRUOC KHI build — day la hanh vi co san cua `load_rq1_trajectories`,
  khong phai loi moi) = **639 dong eligible**.
- Trong 639 dong eligible, **17 dong cho ra trajectory RONG** (0 action)
  sau khi build that — day la hien tuong CO THAT (cache xac nhan status=1/OK
  luc mine, tuc la co goi API thanh cong nhung candidate do khong co hoat
  dong NAO trong cua so da loc, hoac hoat dong bi value_share threshold loc
  het) — KHONG phai do quota, KHONG tinh la "khong co giao dich" ma la
  "trajectory rong hop le sau build", giong het co che da ap dung cho N=15
  (v1.0 cung co nhung dong tuong tu bi loai, xem `load_rq1_trajectories`'s
  `n_empty` logic).
- 639 - 17 = **622 usable**.
- v2_complexity: 110 - 3 rong = **107 usable** (KHONG DOI so voi N=15, vi
  file nay chi co entry cho 15 incident cu).
- Tong: 20 + 5 + 622 + 107 = **754**. Khop CHINH XAC.

### Giai thich "positive rate prefix-level 3,89% vs 6,5%"

**Day la 2 dinh nghia KHAC NHAU, khong phai mau thuan**: con so "6,5%" ban
dang nho (tu `dataset_card.md`/cac trao doi truoc) la ty le tren **DU LIEU
DA DEDUPE** (1.785 dong, dung CHINH THUC cho RQ1/`main_table.csv`), KHONG
phai tren file `features_v2.parquet` RAW (3.354 dong, truoc dedupe). Khi so
sanh DUNG CAP (ca hai deu RAW hoac ca hai deu DEDUP):
- RAW vs RAW: v1.0=3,58% vs N20=3,90% (gan nhau).
- **DEDUP vs DEDUP (dung cho RQ1): v1.0=6,50% vs N20=7,09%** (gan nhau, N20
  HOI CAO HON, khong thap hon nhu bao cao Checkpoint C truoc do dang nham
  lan so sanh RAW cua N20 voi DEDUP cua v1.0).

Bao cao Checkpoint B/C truoc day **da so sanh SAI CAP** (RAW N20 voi DEDUP
v1.0) — day la LOI TRINH BAY (khong phai loi du lieu), da sua trong bang
tren.

## 3. Test tai tao (`tests/test_n20_reproduces_v1.py`)

Da viet va chay: **3/3 PASS** (`test_same_row_count`, `test_same_identifiers`,
`test_feature_values_match_within_tolerance` — nguong 1e-9). Logic: goi
`load_rq1_trajectories()` + `extract_all_prefixes()` **KHONG monkeypatch bat
ky duong dan nao** (dung nguyen `configs/data.yaml`, `incident_registry.csv`,
`hard_negative_registry.csv`, `split_manifest.json` GOC) va so sanh voi
`features_v2.parquet` da freeze — **khop tuyet doi 100%** (3.354/3.354 dong,
tat ca dinh danh khop, chenh lech toi da moi feature column = 0 hoac duoi
1e-9). Day la bang chung manh: cung 1 ham dung cho ca N=15 (mac dinh) va
N=20 (monkeypatch duong dan) khong lam hong duong di mac dinh.

## 4. Phan bo so luong hard-negative (chi bao cao, KHONG khai thac lai)

| Incident (v1.0) | So hard-negative (quy tac chinh) |
|---|---|
| xkingdom_2024, wault_finance_2021, paraluni_2022 | 22 |
| utopiasphere_2024 | 24 |
| chibi_finance_2023, magic_abracadabra, hackerdao, radiant, wooppv2, new_free_dao | 25 |
| feg_bridge_2024 | 31 |
| qbridge_qubit_2022 | 35 |
| bsc_token_hub_2022, ronin_bridge_2022 | 69 |
| deltaprime_arbitrum_2024 | 70 |

**min=22, median=25, max=70.** Day KHONG phai 1 cap co dinh ap dung dong deu
— tim thay 9 script lich su khac nhau (`run_hard_negative_mining*.py`,
`run_hard_negative_remine_*.py`...) voi tham so `target_count`/`TARGET` khac
nhau qua nhieu VONG mine rieng biet theo thoi gian (vd "mo rong 8->12",
"remine sau bug34_fix", "remine sau merge_fix" — 1 incident co the duoc mine
LAI nhieu lan cong don qua cac vong khac nhau, giai thich tai sao mot so
incident (ronin, bsc_token_hub, deltaprime, qbridge, feg) co so luong CAO
HON NHIEU muc 25).

**Tham so quy dinh**: `target_count` (mac dinh=25 trong ham
`mine_hard_negatives_for_incident`) + `max_candidates_checked` (mac dinh=150).
Comment trong `scripts/mine_hard_negatives_new_incident.py` xac nhan ro:
`TARGET_COUNT = 25 # khop quy uoc target_per_incident da dung cho 11 incident
cu (vong mine dau tien)` — **25 la gia tri MAC DINH CHINH THUC cho 1 VONG
MINE DAU TIEN** cua 1 incident moi (khong phai tran cau hinh cung, ma la quy
uoc du an). **5 incident N20 cua toi dung dung gia tri nay (25), khop CHINH
XAC quy uoc da thiet lap cho "vong mine dau tien" — KHONG tu y chon so khac.**
Toi KHONG mine them vong 2 cho 5 incident nay (giu nguyen 25/incident, chua
can mo rong them).

## 5. Endpoint_confirmed — danh sach day du + doi chieu nguon

| Incident | endpoint_confirmed | Nguon |
|---|---|---|
| bsc_token_hub_2022 | True | `incident_registry.csv` (freeze v1.0) |
| chibi_finance_2023 | True | nt |
| deltaprime_arbitrum_2024 | True | nt |
| feg_bridge_2024 | True | nt |
| magic_abracadabra_arbitrum_2025 | True | nt |
| new_free_dao_2022 | True | nt |
| paraluni_2022 | True | nt |
| radiant_capital_arbitrum_2024 | True | nt |
| utopiasphere_2024 | True | nt |
| wault_finance_2021 | True | nt |
| wooppv2_2024 | True | nt |
| xkingdom_2024 | True | nt |
| **hackerdao_2022** | **False** | nt |
| **qbridge_qubit_2022** | **False** | nt |
| **ronin_bridge_2022** | **False** | nt |
| zunami_protocol_2023 | True | Checkpoint truoc (2026-10-14) — xac nhan on-chain that 1183,8 ETH -> Tornado Cash |
| onyx_protocol_2023 | True | nt — 1140,0 ETH -> Tornado Cash (khop tuyet doi) |
| beanstalk_farms_2022 | True | nt — DEX truc tiep + 24.849 ETH -> Tornado Cash |
| **hedgey_finance_2024** | **False** | nt — khong tim thay bridge/mixer trong 72h |
| **cork_protocol_2025** | **False** | nt — trajectory chi 1 action (seed->Universal Router), khong co buoc thoat tiep theo |

**12/15 (v1.0) + 3/5 (N20 moi) = 15/20.** Doi chieu doc lap: file chinh
thuc `results/tables/lead_time_full15_2026-09-22.csv` (script
`scripts/build_lead_time_full15.py`, dung CHINH tieu chi `endpoint_confirmed`
tu `incident_registry.csv`) liet ke CHINH XAC 12 dong `endpoint_confirmed=True`
trong 15 incident ("hackerdao_2022", "qbridge_qubit_2022", "ronin_bridge_2022"
la 3 dong "False"/"not_computable" do thieu co) — **khop CHINH XAC 100% voi
con so toi tinh lai tu registry**, khong co mau thuan.

## 6. Cork — phan tich chi tiet (LOI CAU HINH THAT phat hien o day)

### 2 hanh dong cua Cork (TRUOC khi sua loi, voi config SAI)

```json
[0] transfer 0xea6f30e3...(seed) -> 0x66a9893c...(Universal Router v2), amount_norm=0.7925, block=22524866, tx=0x82edd98c...
[1] transfer 0x66a9893c...(Universal Router v2) -> 0xea6f30e3...(seed), amount_norm=0.005996, block=22524866 (CUNG block/tx), tx=0x82edd98c...
```

### Sau khi SUA loi cau hinh (dung `config=data_N20.yaml` nhu dung y dinh)

```
n_actions = 1 (CHI con hanh dong [0] o tren)
```

**Nguyen nhan chenh lech 1 vs 2 action**: `scripts/build_features_v2_N20.py`
(ban DAU) **KHONG truyen `config=` vao `load_rq1_trajectories()`**, nen ham
nay tu dong dung `config=None -> load_trajectory_config()` (duong dan MAC
DINH `configs/data.yaml` GOC, khong co Universal Router trong `dex_allowlist`).
Da xac minh THUC TE (goi truc tiep `expand_and_build_trajectory` 2 lan, 1
lan voi moi config):
- **Config GOC (khong co Universal Router trong allowlist)**: builder GIU
  CA 2 leg (seed->router VA router->seed) nhu 2 "transfer" rieng biet — vi
  khong biet day la 1 DEX, builder xu ly router nhu 1 counterparty THUONG,
  giu lai leg tra ve vi no cham toi dia chi da duoc track (seed).
- **Config N20 (CO Universal Router trong allowlist)**: builder nhan ra
  router la 1 "sink" DEX da biet — xu ly leg [0] la hanh dong KET THUC tai
  sink do, **KHONG con coi leg tra ve [1] la 1 hanh dong rieng can track**
  (coi nhu tien da "roi" khoi pham vi theo dung ngu nghia bridge/dex/mixer
  sink, giong cach cac bridge/mixer allowlist khac hoat dong).

Day la hanh vi **DUNG Y DO THIET KE** cua builder (allowlist = "diem ket
thuc", khong phai "diem tiep tuc mo rong") — KHONG phai bug trong builder,
ma la bug Ở SCRIPT CUA TOI (quen truyen config). **Da sua (1 dong code),
rebuild lai, 207/207 test pass.**

### Vi sao tx den Universal Router bi phan loai "transfer" chu khong phai "swap"

Doc code `merge_events_into_semantic_actions` (khong sua, chi doc): phan
loai "swap" doi hoi mot CAU TRUC 2-LEG CU THE (vd amount tra ve LA MOT TOKEN
KHAC voi token gui di, trong cung mot nhom giao dich duoc coi la round-trip
swap). Giao dich Cork: CA 2 leg deu la **ETH** (cung token, chi khac so
luong do phi/slippage) — khong khop mau "doi token" ma logic swap tim kiem,
nen bi giu nguyen dang 2 "transfer" (hoac 1 "transfer" sau khi sua config,
vi leg con lai bi an di do allowlist-sink logic) thay vi duoc gop thanh 1
"swap". Day la GIOI HAN CAU TRUC da biet cua decoder (tuong tu cac truong
hop "unknown_dex" o nhieu incident cu, vd circulate_2023), KHONG PHAI loi
moi phat sinh tu N20.

### Kiem tra hieu luc THAT cua entry Universal Router v2 trong `protocol_map_N20.yaml`

**Dia chi khop chinh xac** (ca 2 file, lowercase, khong co loi chu
hoa/thuong): `0x66a9893cc07d91d95644aedd05d03f95e1dba8af` trong CA
`configs/data_N20.yaml::dex_allowlist` VA `metadata/protocol_map_N20.yaml::dexes[].router_addresses.eth`.

**NHUNG phat hien quan trong**: `metadata/protocol_map_N20.yaml` (va ca
`protocol_map.yaml` GOC) **section `dexes:` KHONG DUOC CHUONG TRINH DOC O
DAU CA** — doc lai `src/pipeline/incident_pipeline.py::expand_and_build_trajectory`
xac nhan: chi co `build_verified_bridge_address_index(protocol_map)`,
`build_verified_mixer_address_index(protocol_map)`,
`build_verified_lending_address_index(protocol_map)` duoc goi — **KHONG CO
`build_verified_dex_address_index` nao ca**. Section `dexes:` trong
`protocol_map.yaml`/`protocol_map_N20.yaml` la **THUAN TUY TAI LIEU THAM
KHAO CHO NGUOI DOC**, khong co hieu luc lap trinh — day KHONG PHAI loi rieng
cua entry Universal Router toi them, ma la QUY UOC DA CO SAN TU TRUOC cho
TAT CA entry trong section `dexes:` (Uniswap V2, PancakeSwap V2, 1inch...
deu cung tinh trang). **Allowlist THAT SU co hieu luc la
`configs/data_N20.yaml::dex_allowlist`** (qua `TrajectoryConfig.allowlist`,
`.lower()`-hoa tu dong, khong nhay case) — entry nay DA CO HIEU LUC THAT,
da chung minh qua chenh lech 1-vs-2 action cua Cork o tren.

### So sanh voi Hedgey

Da kiem tra THUC TE: Hedgey's trajectory **KHONG DOI** (661 action, 102 dia
chi frontier) du dung config nao (goc hay N20). Ly do: trajectory cua Hedgey
da "no" qua RAT NHIEU nhanh khac (NOBL token arbitrage cham toi hang chuc
dia chi khong lien quan Universal Router) TRUOC KHI toi diem tiep xuc voi
Universal Router (0x3fc91a3a...) — bo sung 1 entry allowlist duy nhat vao 1
nhanh nho trong 1 trajectory da qua phuc tap khong du de thay doi tong the.
Cork, nguoc lai, CHI CO DUY NHAT 1 tuong tac — nen thay doi allowlist anh
huong truc tiep, ro rang den TOAN BO trajectory cua no.

## Ket luan Checkpoint C'

- Muc 1, 3: **SACH**, khong phat hien van de.
- Muc 2, 4, 5: chenh lech deu **GIAI THICH DUOC day du** (dedupe-vs-raw,
  nhieu vong mine lich su, khop chinh xac voi bao cao freeze).
- **Muc 6: PHAT HIEN 1 LOI CAU HINH THAT** (thieu truyen `config=` vao
  `load_rq1_trajectories()`) — **DA SUA**, rebuild lai, 207/207 test pass,
  manifest SHA-256 da cap nhat.

**Theo dung quy tac da CHOT ("neu 1,3,6 phat hien van de... DUNG va bao
cao"): DUNG O DAY, bao cao day du truoc khi chay Checkpoint D**, ke ca khi
loi da duoc sua — vi day la quyet dinh cua nguoi dung, khong tu dong tiep
tuc.

Ke hoach phan tich (`results/reports/analysis_plan_N20.md`, da co SHA-256 tai
`results/reports/analysis_plan_N20_selfhash.json`) da duoc viet SAN, san
sang chay ngay khi duoc xac nhan.
