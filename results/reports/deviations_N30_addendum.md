# Deviations N30 — Addendum (2026-10-15)

File MOI, KHONG sua `deviations_N30.md` (hash cu
`a3f214f12997f6d33254926eaa1a3bd610e1e04be311e3c228708e99462ecc2e` giu
nguyen). KHONG chay model, KHONG sua file dong bang.

## 1. RQ2 — MOI o (20 ca va 9 ca (d), tat ca bucket, tat ca metric)

**Phuong phap**: dem TRUC TIEP tu `features_v2_N30.parquet` (khong chay
lai model) so dong positive/negative cua TUNG incident trong TUNG
bucket - dieu kien NaN cua `pr_auc`/`recall_at_fpr`
(`src/evaluation/metrics.py:25,38`: `if len(set(y_true))<2: return nan`)
chi phu thuoc THANH PHAN LOP cua test-set (tuc 1 incident/1 fold LOIO),
khong phu thuoc gia tri du doan cua model - nen xac dinh duoc CHINH XAC
tu du lieu, khong can chay lai.

**QUAN TRONG - gioi han da biet**: `false_alerts_per_1000`
(`src/evaluation/metrics.py:65-72`) **KHONG CO** dieu kien NaN nay -
metric nay LUON hop le cho MOI fold bat ke thanh phan lop. Vi vay so
fold hop le cho `false_alerts_per_1000` LUON BANG tong so incident cua
tap (20 hoac 9) o MOI bucket - KHAC voi so fold hop le cua
`pr_auc`/`recall_at_fpr`.

Chi tiet per-fold (incident nao thanh cong/that bai trong so fold HOP
LE) **KHONG duoc luu ra dia** trong lan chay
`scripts/run_evaluation_N30_v3.py` (ham `run_rq2_per_bucket` chi luu
GIA TRI TRUNG BINH cuoi cung, khong luu `fold_rows` chi tiet) - **can
chay lai moi biet duoc fold cu the nao thanh cong**, KHONG suy dien.

### Tap 20 ca (endpoint_confirmed=True)

| bucket | pos_total | neg_total | fold hop le (pr_auc/recall) | fold bi loai (1 lop) | fold hop le (false_alerts) |
|---|---|---|---|---|---|
| ratio_25 | 20 | 718 | 20/20 | (khong) | 20/20 |
| ratio_50 | 20 | 718 | 20/20 | (khong) | 20/20 |
| ratio_75 | 20 | 718 | 20/20 | (khong) | 20/20 |
| ratio_100 | 20 | 718 | 20/20 | (khong) | 20/20 |
| k_2 | 20 | 348 | 20/20 | (khong) | 20/20 |
| k_3 | 20 | 226 | **19/20** | feg_bridge_2024 (pos=1,neg=0) | 20/20 |
| k_5 | 20 | 123 | **17/20** | feg_bridge_2024, xkingdom_2024, inverse_finance_2022_jun (deu pos=1,neg=0) | 20/20 |
| k_7 | 20 | 86 | **15/20** | feg_bridge_2024, wooppv2_2024, xkingdom_2024, zunami_protocol_2023, inverse_finance_2022_jun (deu pos=1,neg=0) | 20/20 |

### Tap 9 ca sensitivity (d)

| bucket | pos_total | neg_total | fold hop le (pr_auc/recall) | fold bi loai (1 lop) | fold hop le (false_alerts) |
|---|---|---|---|---|---|
| ratio_25 | 9 | 283 | 9/9 | (khong) | 9/9 |
| ratio_50 | 9 | 283 | 9/9 | (khong) | 9/9 |
| ratio_75 | 9 | 283 | 9/9 | (khong) | 9/9 |
| ratio_100 | 9 | 283 | 9/9 | (khong) | 9/9 |
| k_2 | 9 | 94 | 9/9 | (khong) | 9/9 |
| k_3 | 9 | 52 | **8/9** | feg_bridge_2024 (pos=1,neg=0) | 9/9 |
| k_5 | 9 | 34 | **7/9** | feg_bridge_2024, inverse_finance_2022_jun (deu pos=1,neg=0) | 9/9 |
| k_7 | 9 | 27 | **6/9** | feg_bridge_2024, zunami_protocol_2023, inverse_finance_2022_jun (deu pos=1,neg=0) | 9/9 |

Trong tat ca ca bi loai, nguyen nhan GIONG NHAU: incident do co
trajectory_len < k (khong du do dai de co prefix row tai muc k do), nen
test-set LOIO cho fold do CHI co 1 dong (chinh incident day, label=1),
KHONG co dong negative nao (vi hard-negative cua CHINH incident do cung
can >=k action de co prefix row tai muc k, va trong mau hop nay KHONG
co hard-negative nao cua 3 incident tren dat du k=5/7 action).

## 2. Xac minh code M1/B3 khong doi so voi N=15/N=20

**KHONG XAC MINH DUOC bang SHA-256 doi chieu truc tiep voi thoi diem
N=15/N=20 duoc chay** - khong co SHA-256 nao cua `baselines.py` (hay
bat ky file model/feature/eval nao) duoc ghi lai trong bao cao nao
truoc day (`results/reports/analysis_plan_N20.md`,
`dataset_expansion_N20_checkpointCprime_2026-10-14.md`,
`analysis_plan_N30_v3.md` co nhac ten file nhung KHONG ghi hash cu the).
`scripts/run_checkpointD_N20_analysis.py` (script da tao ket qua N=20)
KHONG nam trong git log (untracked, chua tung commit) - khong the dung
`git diff` de so sanh trang thai file nay TAI THOI DIEM N=20 duoc chay
voi hien tai.

**Nhung gi XAC MINH DUOC** (git status + hash hien tai, trong PHAM VI
phien lam viec nay):

| File | git status (so voi commit cuoi 736029a) | SHA-256 hien tai |
|---|---|---|
| `src/models/baselines.py` | **M (co sua)** - khac biet = fix leak `prefix_ratio` 2026-09-28 (xem `results/reports/prefix_ratio_leak_2026-09-28.md`), **TRUOC** phien lam viec nay, KHONG do toi sua | `d9f2a438603fd4b1787b6703bd1b8a434067d2702982ff905bbf46d77fa7d71e` |
| `src/features/extractor.py` | khong doi (clean) | `70aed7ee381bb9db417204e57955579b9e1885a2b6205a04706f8553f6a4894f` |
| `src/evaluation/nested_eval.py` | khong doi (clean) | `ee3d3e1b7db445ce98b2fd466198d74298f4b41b70bc7a2e0c96f919fae11dde` |
| `src/evaluation/metrics.py` | khong doi (clean) | `fa279f841143d22325619581fab1f076a12481fb8d4e2dc364688af71ff34c84` |

**Xac nhan tu lich su hanh dong cua toi trong PHIEN NAY** (tu dau phien
den gio): toi **KHONG tung dung Edit/Write** tren 4 file tren - cac
file toi sua trong phien nay CHI la: `src/normalize/decoder.py`,
`src/pipeline/incident_pipeline.py`, `tests/test_decoders.py` (2 fix
decoder contract-creation, da bao cao chi tiet truoc day), cung cac
file config/metadata (`configs/data_N30.yaml`,
`metadata/incident_registry_N30.csv`, v.v.) - KHONG file model/feature/
eval nao.

**Ket luan trung thuc**: co the xac nhan `baselines.py`/
`extractor.py`/`nested_eval.py`/`metrics.py` **khong doi TRONG PHAM VI
phien lam viec nay** (tu luc bat dau N30 den gio, dung cho ca N20
checkpoint D va N30 evaluation vua chay). **KHONG the xac minh** rang
day la DUNG phien ban da tao ra ket qua N=15/N=20 GOC (truoc phien nay)
vi thieu SHA-256 da ghi lai tu truoc do de doi chieu, va file script
N20 khong duoc version-control.
