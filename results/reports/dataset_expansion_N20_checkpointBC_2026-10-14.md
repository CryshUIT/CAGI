# Dataset expansion N20 — Checkpoint B + C (2026-10-14)

**KHONG ghi de bat ky file freeze v1.0/N=15 nao. KHONG chay model o buoc nay
(chi mo ta du lieu). Tat ca file N20 nam rieng, co the doi chieu/quay lai
N=15 bat cu luc nao.**

## Checkpoint B — Dry-run luu luong + khai thac hard-negative

### B.1 — Nguon xac minh Uniswap Universal Router (bo sung vao protocol_map_N20.yaml)

| Dia chi | Ten | Nguon 1 (Etherscan) | Nguon 2 (chinh thuc) |
|---|---|---|---|
| 0x66a9893cc07d91d95644aedd05d03f95e1dba8af | Universal Router v2 | https://etherscan.io/address/0x66a9893cc07d91d95644aedd05d03f95e1dba8af | https://docs.uniswap.org/contracts/v4/deployments (liet ke dung dia chi nay, chain ID 1) |
| 0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad | Universal Router (v1.2 variant) | https://etherscan.io/address/0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad | KHONG tim thay trong trang docs hien tai (chi liet ke ban v4/2.1.1 moi nhat) - chi xac nhan qua nhan Etherscan |

### B.2 — Dry-run dem luu luong (mau nho, chua crawl lon)

| Hop dong | Mau (block) | Tx trong mau | Tx/block | Uoc tinh ±7 ngay (100,800 block) | So "window" can (page_size=10000) | So voi cap (200) |
|---|---|---|---|---|---|---|
| Tornado Cash Router (Zunami window) | 300 | 30 | 0,10 | ~10.080 | 2 | 1% cap |
| Tornado Cash Router (Onyx window) | 300 | 7 | 0,023 | ~2.352 | 1 | 0,5% cap |
| Uniswap V2 Router (Beanstalk window) | 300 | 314 | 1,05 | ~105.538 | 11 | 5,5% cap |
| Universal Router v1.2 (Hedgey window) | 300 | 1000 | 3,33 | ~335.664 | 34 | 17% cap |
| Universal Router v2 (Cork window) | 300 | 1000 | 3,33 | ~335.664 | 34 | 17% cap |

(Sanity check Universal Router v2 them 2 mau nho hon: 30 block->196 tx
(6,53/block), 100 block->525 tx (5,25/block) - xac nhan KHONG phai cap cung
1000, chi la bien dong tu nhien theo kich thuoc cua so, quy mo that su RAT
LON nhung van duoi cap kien truc 200 window.)

**Ket luan B.2**: ca 5 hop dong deu uoc tinh NAM TRONG cap (cao nhat
~17%, con xa 200). Khong co incident nao bi loai truoc khi crawl.

**Quota con lai**: Etherscan V2 khong co endpoint cong khai de truy van
quota con lai truc tiep cho API key free-tier - khong kiem tra duoc con so
chinh xac, chi dua vao: (1) test call thuc te thanh cong (Checkpoint truoc
day); (2) tong so request uoc tinh cho ca 5 incident (~82 window-call cho
buoc liet ke + toi da 150 ung vien x ~3 loai call/ung vien x 5 incident =
~2250 call cho buoc dieu tra ung vien) la nho so voi gioi han hang ngay
thong thuong cua Etherscan free-tier (hang chuc nghin/ngay) - khong chia
ngay la can thiet.

### B.3 — Phat hien cat cut (enumeration_truncated) + thu tu chon candidate

- Da them wrapper `safe_fetch_contract_counterparties()` (script rieng,
  KHONG sua `hard_negative_miner.py` goc) bat `EtherscanAPIError` khi
  `_fetch_all_pages` cham `max_windows=200` - CHI GHI NHAN
  (`results/reports/mining_truncation_log_N20_2026-10-14.json`), khong doi
  hanh vi/cap.
- **Ket qua: CA 5/5 incident KHONG bi truncated** (xem file log - tat ca
  `"truncated": false`).
- **Thu tu chon candidate trong `max_candidates_checked=150`**: DOC code
  xac nhan - candidate duoc lay theo thu tu: (1) TOAN BO counterparty tu
  **tokentx** (ERC20 transfer) THEO THU TU BLOCK TANG DAN, roi (2) TOAN BO
  tu **txlist** (ETH transfer thuong) THEO THU TU BLOCK TANG DAN, roi (3)
  TOAN BO tu **txlistinternal**. Day la **TAT DINH** (cung cache -> cung
  danh sach -> cung 150 candidate dau, tai lap duoc 100%), nhung **KHONG
  phai thuan tuy theo thoi gian** - co uu tien NGAM theo LOAI giao dich
  (token-transfer counterparty luon duoc xet TRUOC normal-tx counterparty,
  bat ke block nao som hon) - can luu y neu sau nay muon giai thich "tai
  sao candidate X duoc chon ma khong phai Y".

### B.4 — Ket qua khai thac hard-negative (thuc te, tuan tu Zunami->...->Cork)

| Incident | Checked | Accepted | Rejected | Truncated |
|---|---|---|---|---|
| zunami_protocol_2023 | 85 | 25 | 60 | Khong |
| onyx_protocol_2023 | 61 | 25 | 36 | Khong |
| beanstalk_farms_2022 | 74 | 25 | 49 | Khong |
| hedgey_finance_2024 | 105 | 25 | 80 | Khong |
| cork_protocol_2025 | 97 | 25 | 72 | Khong |

Tong **125 hard-negative moi** (25/incident, dat target_count), ghi vao
`metadata/hard_negative_registry_N20.csv` (KHONG ghi de
`hard_negative_registry.csv` goc). Khong co response nao bi danh dau thieu
do quota (tat ca request thanh cong, status=1/OK).

**LOI PHAT HIEN VA SUA (2026-10-14, sau lan build feature dau tien)**: ban
build dau tien chi tro `HARD_NEGATIVE_REGISTRY_PATH` toi
`hard_negative_registry_N20.csv` (CHI 125 dong MOI) thay vi GOP voi 536 dong
CU - vi day la **monkeypatch GHI DE** (khong phai THEM VAO), nen 536
hard-negative cua 15 incident cu bi **MAT HOAN TOAN** khoi dataset N20 mot
cach am tham (script van chay thanh cong, khong bao loi, chi la so lieu sai
- phat hien qua kiem tra cheo thu cong so luong, khong phai do script tu
bao). **Da sua**: tao `metadata/hard_negative_registry_N20_combined.csv`
(536 cu + 125 moi = 661 dong, khong trung `hard_negative_id`), dung file nay
lam `HARD_NEGATIVE_REGISTRY_PATH` cho buoc build feature - xem muc duoi.

## Checkpoint C — Trajectory, feature, pytest, manifest

### Loi phat hien VA SUA giua Checkpoint B va C

Lan build feature DAU TIEN (`build_features_v2_N20.py`, truoc khi sua) cho
**n_actions=0 cho CA 5 incident moi**. Nguyen nhan: cac buoc kiem tra
provenance (Checkpoint truoc) da dung incident_id TAM (vd
`"zunami_2023_provenance_check"`) de goi API thu nghiem - cache cua
`EtherscanClient` duoc SCOPE theo incident_id (`data/raw/{chain}/{dia_chi}/
{incident_id}/...`), nen pipeline chinh thuc (doc du lieu voi incident_id
THAT `"zunami_protocol_2023"`) khong tim thay cache nao, dan den 0 action.
Day KHONG phai loi quota - la loi quy trinh (chua chay buoc thu thap THAT
duoi incident_id chinh thuc cho chinh dia chi seed, chi moi lam cho hop
dong mining + ung vien hard-negative).

**Da sua**: chay `expand_and_build_trajectory(..., incident_id=<id_that>,
do_collect=True)` THAT cho ca 5 seed (script
`scripts/_run_real_pipeline_N20_seeds.py`), dung `configs/data_N20.yaml`.
Ton THEM mot it quota (frontier expansion that cho 5 dia chi, da trinh bay
chi tiet trong output) nhung can thiet de co du lieu dung - khong phai
"crawl lon" ngoai du kien (Hedgey mo rong toi 102 dia chi do ban chat flash
loan NOBL cham nhieu counterparty, nhung van hoan thanh binh thuong, khong
cham cap).

### Ket qua trajectory THAT cho 5 incident moi

| Incident | n_action | Dia chi frontier | Endpoint (mixer_or_exit) dau tien | Ty le vi tri |
|---|---|---|---|---|
| zunami_protocol_2023 | 31 | 2 | index 1/31 | 0,032 |
| onyx_protocol_2023 | 16 | 2 | index 1/16 | 0,062 |
| beanstalk_farms_2022 | 440 | 11 | index 162/440 | 0,368 |
| hedgey_finance_2024 | 661 | 102 | KHONG co (endpoint_confirmed=False) | — |
| cork_protocol_2025 | 2 | 1 | KHONG co (endpoint_confirmed=False) | — |

**Luu y quan trong ve Cork**: trajectory CHINH THUC chi co **2 action**
(mong hon nhieu so voi uoc luong thu cong o Checkpoint truoc) - hanh dong
duy nhat la 1 `transfer` (khong phai `swap`) toi Universal Router (gia tri
0,79, log-scale) - builder giu lai VI dia chi nay nam trong allowlist, chi
KHONG duoc merge_events_into_semantic_actions phan loai thanh "swap" day du
(thieu leg phan hoi/erc20 khop mau 2-leg). Day la bang chung DEX **yeu hon**
so voi danh gia ban dau trong Checkpoint A - van dat gate ky thuat (co cham
allowlist DEX trong trajectory) nhung RAT MONG, can luu y khi vao paper.

### Ket qua `pytest tests/ -v` sau khi them du lieu N20 (CHAY LAI sau khi sua loi gop hard-negative)

**204/204 PASSED** (299,23s) - khong regression nao tu viec them du lieu/
cau hinh N20 (chay lai lan 2 sau khi sua loi gop file hard-negative, van
204/204 pass).

### Mo ta du lieu N=20 (CHUA chay model, chi thong ke — SO LIEU DA SUA SAU KHI GOP DUNG HARD-NEGATIVE)

- **So incident chinh thuc (eval_tier=primary, label=1): 20** (15 cu + 5
  moi).
- **So incident endpoint_confirmed=True: 15/20** (10 cu + Zunami + Onyx +
  Beanstalk; 5 KHONG: ronin_bridge_2022, qbridge_qubit_2022, hackerdao_2022
  (cu) + hedgey_finance_2024, cork_protocol_2025 (moi)).
- **So hard-negative**: 536 cu (v1) + 125 moi (N20) = **661 dong trong
  `hard_negative_registry_N20_combined.csv`**, + 110 dong v2_complexity cu
  (khong doi) = 771 hard-negative row dinh nghia tong cong. Sau khi build
  trajectory that: **620/639 usable** tu nhom "hard_negative_mined" (19
  rong — tang so voi 5 ban dau vi gio bao gom CA cac trajectory rong von da
  co san tu 15 incident cu, khong phai loi moi) + **107/110 usable** tu
  nhom "v2_complexity" (khong doi, 3 rong tu truoc).
- **Tong trajectory su dung duoc**: 752 (20 positive + 5 hard_negative_control
  + 620 hard_negative_mined + 107 hard_negative_mined_v2_complexity).
- **So prefix row (CHUA dedupe, giong nguyen tac features_v2.parquet goc)**:
  **4.037 dong** (752 trajectory x toi da 8 bucket, tru trajectory qua ngan).
- **Positive rate pooled (toan bo 4.037 dong, tho)**: **3,89%**.
- **Positive rate per-trajectory (bucket ratio_100 = 1 dong/trajectory,
  752 trajectory)**: **2,66%**.
- **Phan bo chain (ratio_100, 752 trajectory)**: bsc=276, eth=244,
  arbitrum=232 (can bang hon nhieu so voi ban dau — vi gio tinh ca 15 incident
  cu voi phan lon hard-negative tren bsc/arbitrum).
- **Do dai trajectory (20 incident positive, action)**: min=2 (Cork),
  25%=21,25, median=56,5, 75%=381,5, max=1625 (ronin_bridge_2022), mean=
  255,85, std=394,6 (KHONG doi so voi lan truoc — chi 20 incident positive,
  khong bi anh huong boi viec gop hard-negative). 5 incident moi them vao CA
  2 cuc: Cork (2, cuc ngan) va Hedgey (661, rat dai, hang thu 2 sau
  ronin_bridge_2022).

**Luu y ve positive rate**: ty le pooled/per-trajectory GIAM MANH so voi
lan tinh sai truoc do (11,18%/7,94% -> 3,89%/2,66%) sau khi sua loi gop -
day la so lieu DUNG (gan voi ty le that cua N=15 goc, ~6,5% theo
dataset_card.md, chi lech do them 5 incident moi voi ty le am/duong khac
biet chut it). Day la minh chung ro cho thay loi gop hard-negative anh
huong truc tiep den so lieu mo ta neu khong duoc phat hien va sua.

## Manifest dong bang (SHA-256) — TRUOC khi chay bat ky model nao (DA CAP NHAT sau khi sua loi gop)

File: `results/reports/freeze_N20_manifest_2026-10-14.json`

| File | SHA-256 (16 ky tu dau) | Kich thuoc |
|---|---|---|
| metadata/incident_registry_N20.csv | d7888bbb6d5e5030... | 48.595 B |
| metadata/hard_negative_registry_N20.csv (chi 125 dong moi) | f05b60e2b1c0588a... | 22.002 B |
| **metadata/hard_negative_registry_N20_combined.csv (661 dong, dung de build feature)** | 23ae7338fe9649d7... | 111.542 B |
| metadata/split_manifest_N20.json | 57cf32b9e79dd0e4... | 40.262 B |
| configs/data_N20.yaml | 7672d381aaa1193f... | 4.699 B |
| metadata/protocol_map_N20.yaml | b5abaeb5730868be... | 14.456 B |
| data/processed/features_v2_N20.parquet (4.037 dong) | e2ee82a26fb85567... | 169.134 B |
| configs/features_v2_computed_N20.json | 77414820f5ff5cd7... | 1.829 B |

## Xac nhan KHONG dong cham file freeze v1.0/N=15

`git status --short` xac nhan: khong co file nao trong so
`incident_registry.csv`, `hard_negative_registry.csv`,
`hard_negative_registry_v2_complexity.csv`, `split_manifest.json`,
`configs/data.yaml`, `metadata/protocol_map.yaml`,
`data/processed/features_v2.parquet` bi doi - toan bo thay doi nam o file
`*_N20.*` moi hoac file `data/processed/{incident_id}_events.json` MOI (ten
khac hoan toan voi 15 incident cu, khong ghi de).

## DUNG tai day truoc Checkpoint D (theo dung yeu cau)

Theo quy tac da CHOT: ca 5 incident deu crawl sach, khong co incident nao
bi skip/truncated -> da hoan thanh Checkpoint C, dung truoc khi chay
RQ1/RQ2 tren N=20 (Checkpoint D) de cho xac nhan tiep tuc.
