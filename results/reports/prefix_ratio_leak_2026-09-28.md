# `prefix_ratio` future-leakage — xac minh, sua (M1 va B3), tac dong len RQ1 (2026-09-28)

> **Cap nhat 2026-09-28 (lan 2)**: ban dau nhiem vu chi giao sua M1; sau do
> nguoi dung yeu cau mo rong sang ca B3 (xac nhan bang doi chieu voi mot repo
> khac cung nhom, da sua ca hai noi va dat ten loi "T4"). Bao cao nay da duoc
> viet lai de phan anh ban sua **CA HAI** M1 va B3.

## Ket luan ngan gon

**Day la leak that**, xac nhan qua 2 nguon doc lap: (1) doc code tinh trong
repo nay (`extractor.py` dung `len(trajectory)` day du), va (2) doi chieu voi
mot repo khac cung nhom da tung sua ca hai noi va dat ten "T4". Sau khi sua CA
M1 VA B3, ca hai deu giam PR-AUC, nhung **ket luan thong ke cuoi cung cua RQ1
khong doi**: M1 vs B3 van "khong khac biet co y nghia thong ke" — chi khac la
diem uoc luong (point estimate) doi chieu, B3 hien nhinh hon M1 mot chut thay
vi nguoc lai, nhung van nam trong khoang tin cay chua 0 (p=0.303).

## Buoc 1 — Xac minh (khong doan)

1. `src/features/extractor.py` dong 589: `feats["prefix_ratio"] = float(prefix_len) / len(trajectory)`
   — `trajectory` la object DAY DU (chi `actions = _prefix_actions(trajectory, prefix_len)`
   o dong 577 moi duoc cat de tinh cac nhom feature khac). `prefix_ratio` ma
   hoa ty le da quan sat tren TONG DO DAI CUOI CUNG — chi biet duoc SAU KHI
   trajectory ket thuc, vi pham `configs/features.yaml::anti_leakage_rules`
   (day la leak k/n, khong phai leak "loai giao dich" nhung van la leak thong
   tin tuong lai).
2. Ai dung cot nay:
   - **M1** (`M1TypedTemporalMotifModel._candidate_columns`): dinh loai bo qua
     dieu kien `if c in ("prefix_len", "prefix_ratio_meta"): continue` — nhung
     khong co cot nao ten `"prefix_ratio_meta"` (xac minh bang grep toan repo +
     doi chieu `configs/features_v1_computed.json`/`features_v2_computed.json`,
     ca hai chi co `"prefix_ratio"`) -> dieu kien KHONG BAO GIO khop -> loi
     TYPO, khong phai chu y.
   - **B3** (`B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES`): liet ke
     `"prefix_ratio"` CO CHU Y (docstring giai thich "kich thuoc tuong doi cua
     prefix, khong phai thong tin loai"). Day la QUYET DINH THIET KE, khong
     phai bug code — nhung xet lai van la leak k/n.
   - **T13** (`T13LogisticRegressionM1Features._candidate_columns`, dong ~417):
     CUNG CO LOI TYPO GIONG M1 — **chua sua**, ngoai pham vi nhiem vu nay (chi
     M1+B3 duoc giao). Can xu ly rieng.
   - **B0, B1, B2**: xac nhan KHONG dung `prefix_ratio` (B0 bo qua X hoan toan;
     B1 chi dung `RULE_FEATURES` co dinh; B2 chi chon cot `action_count_*`).
     **Khong bi anh huong, khong tinh lai.**
3. `META_COLS` trong `scripts/run_full_evaluation_v1.py` (dong 45-46) KHONG
   loai `prefix_ratio` — viec loai/giu hoan toan phu thuoc logic noi bo tung
   model.
4. `prefix_ratio_meta` KHONG TUNG la ten cot that o bat ky version feature nao
   (v1 hay v2) — loi typo/dat sai ten tu dau, khong phai do doi ten qua cac
   version.
5. `results/reports/model_card_m1_PRE_PREFIXFIX_backup.md` DA CO SAN
   `prefix_ratio` trong feature list voi importance 0.0546 (gan bang 0.0526
   hien tai) -> xac nhan bug "PREFIXFIX" lich su (ve `generate_prefixes()` sinh
   nhan trung lap, sua bang `dedupe_pooled_prefixes()`) la MOT BUG HOAN TOAN
   KHAC, chua tung dung cham den loi nay. Loi ton tai khong bi phat hien tu it
   nhat freeze v1.0 (2026-08-19) den nay.

Bo test hien co (`tests/test_no_future_leakage.py::test_features_at_prefix_identical_regardless_of_future_actions`)
khong bat duoc loi nay vi 2 kich ban test co CUNG SO LUONG action o phan tail
(khac noi dung, giong so luong) -> tong do dai trajectory bang nhau ->
`prefix_ratio` tai prefix_len co dinh trung nhau tinh co, bat ke leak.

## Buoc 2 — Sua (CA M1 va B3)

File duy nhat thay doi: **`src/models/baselines.py`**.

**M1** — `M1TypedTemporalMotifModel._candidate_columns` (dong ~313):

```python
# TRUOC
if c in ("prefix_len", "prefix_ratio_meta"):
    continue
# SAU
if c in ("prefix_len", "prefix_ratio"):
    continue
```

**B3** — `B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES` (dong ~180-187): bo
`"prefix_ratio"` khoi tuple, xoa dong docstring tuong ung ("prefix_ratio: kich
thuoc tuong doi cua prefix..."), them comment giai thich ly do sua.

Khong sua `extractor.py` (van tinh `prefix_ratio` nhu cu cho phan tich khac).
Khong sua B0/B1/B2. Khong sua T13 (cung bug, ngoai pham vi). Khong doi
hyperparameter/`BRIDGE_CONTEXT_COLS_EXCLUDED` hay logic nao khac.

`pytest tests/ -v`: **204/204 passed** ca hai lan (sau khi sua M1, va sau khi
sua them B3), khong regression.

## Buoc 3 — Tinh lai CA M1 va B3, so sanh paired

Script: `scripts/run_m1_b3_prefixratio_fix_check_2026-09-28.py` (khong ghi de
`main_table.csv`/`oof_predictions_v1.csv`/`rq1_answer.md`/`baseline_results_v2.csv`
— tinh lai CA HAI model bang dung methodology cua `run_full_evaluation_v1.py`:
`dedupe_pooled_prefixes` -> 1785 dong, 15 group, `evaluate_model_nested(...,
target_fpr=0.01)`; B0/B1/B2 lay nguyen tu `main_table.csv` vi khong bi anh
huong).

### PR-AUC pooled (micro-average, 1785 dong)

| Model | Cu (co leak) | Moi (da sua) | Delta |
|---|---|---|---|
| M1 | 0.6624 | 0.5924 | **-0.0700** |
| B3 | 0.6875 | 0.6366 | **-0.0508** |

Ca hai deu giam, nhung M1 giam nhieu hon B3 (-0.070 vs -0.051) — hop ly vi B3
la mo hinh don gian hon (Random Forest tren tap feature nho hon, it phu thuoc
vao 1 feature don le hon so voi XGBoost cua M1 khi mat 1 feature dong gop
manh).

### So sanh paired (per-incident, bootstrap muc incident n_boot=2000 seed=42, Wilcoxon)

| | Mean diff (M1-B3) | 95% CI | Wilcoxon p |
|---|---|---|---|
| CU (ca hai deu co leak) | +0.0355 | [-0.0286, +0.1288] | 0.6379 (khong y nghia) |
| **MOI (ca hai da sua)** | **-0.0462** | **[-0.1434, +0.0497]** | **0.3028 (khong y nghia)** |

**Ket luan thong ke KHONG DOI**: ca truoc va sau khi sua, khoang tin cay 95%
cua hieu (M1-B3) deu chua 0 -> "khong co bang chung khac biet co y nghia thong
ke giua M1 va B3" van dung. Diem khac biet duy nhat: **diem uoc luong doi
chieu** — truoc day M1 nhinh hon B3 mot chut (+0.0355, khong y nghia), sau khi
sua ca hai thi B3 nhinh hon M1 mot chut (-0.0462, van khong y nghia). Day
KHONG phai mot thay doi ket luan khoa hoc (van la "hoa"), nhung **cac con so
tuyet doi trong Table 3/RQ1 se thay doi** (M1: 0.662->0.592, B3: 0.688->0.637)
va can duoc cap nhat trong paper de chinh xac.

## Cac so lieu khac co the bi lech theo (chua cap nhat, can quyet dinh)

- **`results/reports/model_card_m1.md`** dong 28: `prefix_ratio` hien xep
  hang 5 trong feature importance (0.052561) cua model M1 CUOI CUNG (train
  boi `scripts/train_and_save_m1_final.py`). Sau khi sua, cot nay se bien mat
  khoi feature importance cua model moi. File nay la file dong cung chinh
  thuc, chi cap nhat duoc neu chay lai `train_and_save_m1_final.py` — ngoai
  pham vi nhiem vu nay, can quyet dinh rieng.
- **`results/reports/alert_case_studies_v1.md`** — Case 1 (`qbridge_qubit_2022`):
  bang "Top-5 feature dong gop" hien co `prefix_ratio` hang 5 (dong gop
  +0.5770). Se can sinh lai (`scripts/generate_alert_case_studies.py`) sau khi
  model M1 duoc train lai — **chua thuc hien**, phu thuoc quyet dinh o tren.
- **B3 co the co case study/feature-importance rieng tham chieu `prefix_ratio`
  o dau do khac trong paper** — chua ra soat toan bo paper (file `.tex` khong
  co trong repo, ngoai kha nang kiem tra truc tiep).

## Danh sach file/dong da thay doi trong nhiem vu nay (ca 2 lan)

- `src/models/baselines.py`:
  - dong ~313 (`M1TypedTemporalMotifModel._candidate_columns`): doi
    `"prefix_ratio_meta"` -> `"prefix_ratio"`, them comment.
  - dong ~175-188 (`B3FlatGraphRandomForest`): bo `"prefix_ratio"` khoi
    `FLAT_UNTYPED_FEATURES`, xoa dong docstring tuong ung, them comment giai
    thich.
  - **Day la 2 thay doi code DUY NHAT trong ca nhiem vu.**
- Them moi (khong ghi de gi cu):
  `scripts/run_m1_prefixratio_fix_check_2026-09-28.py` (ban dau, chi M1),
  `scripts/run_m1_b3_prefixratio_fix_check_2026-09-28.py` (mo rong, ca hai),
  `results/tables/m1_prefixratio_fix_check_2026-09-28.csv`,
  `results/tables/m1_b3_prefixratio_fix_check_2026-09-28.csv`,
  `results/reports/prefix_ratio_leak_2026-09-28.md` (file nay).
- **KHONG** thay doi: `extractor.py`, B0/B1/B2, T13 (cung bug nhung ngoai pham
  vi), `main_table.csv`, `oof_predictions_v1.csv`, `rq1_answer.md`,
  `baseline_results_v2.csv`, `model_card_m1.md`, `alert_case_studies_v1.md`.

## Buoc A (2026-09-28, lan 3) — Correlation + subgroup (phan tich trung tam cua Discussion)

Dung per-incident PR-AUC MOI (M1+B3 da sua, tu bang tren) + do dai trajectory
that cua incident (label=1, ratio_100, `trajectory_len`, khop chinh xac voi
cot "Do dai trajectory" da dung trong `m1_vs_b3_discussion_analysis_2026-09-26.md`).

**Spearman(gap, do dai trajectory), loai `new_free_dao_2022` (outlier, dung
tieu chi cu — van la outlier lon nhat sau khi sua, gap_new=+0.393), N=14:**

| | rho | p |
|---|---|---|
| CU | 0,859 | 0,000084 |
| **MOI** | **0,917** | **0,000004** |

-> Tuong quan **MANH HON** sau khi sua (khong yeu di) — cau chuyen "loi ich cua
typing tap trung o trajectory dai" **van dung, thuc ra ro net hon**.

**Subgroup split <=40 vs >40 action (khong loai outlier, dung 15 incident, giong
nguyen ban goc — 8 dai / 7 ngan), bootstrap muc incident n_boot=2000 seed=42:**

| Nhom | CU mean diff | CU 95% CI | MOI mean diff | MOI 95% CI |
|---|---|---|---|---|
| DAI (>40, n=8) | +0,0372 | [+0,0184, +0,0564] (CO y nghia) | **+0,0144** | **[-0,0328, +0,0692] (KHONG con y nghia)** |
| NGAN (<=40, n=7) | +0,0337 | [-0,0840, +0,2257] (khong y nghia) | **-0,1154** | **[-0,2796, +0,0809] (van khong y nghia)** |

**QUAN TRONG — khong co gang khop voi ket luan cu**: phat hien trung tam cua
paper ("nhom DAI co loi ich CO Y NGHIA thong ke, day la dac diem hoa thong tin
hon ca so trung binh pooled") **KHONG CON DUNG sau khi sua leak** — khoang tin
cay nhom DAI moi (`[-0,033, +0,069]`) CHUA 0, khong con dat nguong y nghia
thong ke. Diem uoc luong van duong (+0,0144, huong dung) nhung khong con
"significant" theo tieu chi 95% CI da dung xuyen suot bai. Day la mot thay doi
ket luan quan trong can nguoi dung can nhac ky truoc khi giu lai doan van nay
trong Discussion — co the can dieu chinh thanh "xu huong" (trend) thay vi
"co y nghia thong ke", hoac tim huong trinh bay khac.

Nhom NGAN: diem uoc luong doi chieu manh (+0,034 -> -0,115, B3 nhinh hon ro),
nhung van khong dat y nghia thong ke o ca 2 phien ban (CI deu chua 0) — ket
luan dinh tinh "nhom ngan khong co khac biet ro rang" van dung.

## Buoc B (2026-09-28, lan 3) — Table 3(b): M1 PR-AUC theo checkpoint (RQ2)

Script: `scripts/run_rq2_prefix_evaluation_prefixratiofix_check_2026-09-28.py`
(khong ghi de `rq2_prefix_evaluation_folds.csv` chinh thuc trong buoc kiem tra
nay — xem ghi chu rieng ben duoi ve viec CO cap nhat file chinh thuc sau do).

| Checkpoint | CU | MOI | Delta |
|---|---|---|---|
| ratio_25 | 0,9333 | 0,9222 | -0,0111 |
| ratio_50 | 0,8491 | 0,8541 | +0,0050 |
| ratio_75 | 0,9350 | 0,9350 | 0,0000 |
| ratio_100 | 0,9407 | 0,9407 | 0,0000 |
| k_2 | 0,7470 | **0,4718** | **-0,2752 (RAT LON)** |
| k_3 | 0,6222 | 0,6484 | +0,0262 |
| k_5 | 0,7097 | 0,7612 | +0,0516 |
| k_7 | 0,7679 | 0,7688 | +0,0010 |

**Giai thich**: cac checkpoint TY LE (ratio_25/50/75/100) hau nhu KHONG doi —
hop ly vi trong 1 bucket ty le, `prefix_ratio` gan nhu HANG SO (~0,25/0,5/
0,75/1,0 theo dinh nghia), nen mang rat it thong tin phan biet GIUA CAC HANG
trong cung 1 bucket -> loai no it anh huong. Nguoc lai, checkpoint TUYET DOI
`k_2` (chi 2 action da quan sat, o RAT NHIEU trajectory co do dai rat khac
nhau) giam MANH (-0,275) — day chinh la truong hop `prefix_ratio` leak MANH
NHAT ly thuyet da du doan tu Buoc 1 (2/do_dai_cuoi_cung dao dong lon giua cac
dong, mang nhieu thong tin ve do dai cuoi cung ngay ca khi chi quan sat 2
action dau). Bang 3(b) hien tai cua paper (neu chi trich dan ratio_25/50/75/
100) hau nhu khong doi; **neu paper co trich dan k_2 o dau do (vi du hinh lead-
time hay bang RQ2 day du), con so 0,747 se can sua thanh ~0,472 — chenh lech
lon, can ra soat.**

## Buoc C (2026-09-28, lan 3) — Dong bo model "final" + case study

- **Da chay lai `scripts/train_and_save_m1_final.py`** (theo yeu cau tuong
  minh cua nguoi dung, khac voi cac lan truoc trong nhiem vu nay). Backup ban
  cu truoc khi ghi de: `results/reports/model_card_m1_PRE_PREFIXRATIOFIX_backup.md`,
  `results/models/m1_final_PRE_PREFIXRATIOFIX_backup.joblib`. Xac nhan
  `model_card_m1.md` MOI khong con `prefix_ratio` trong danh sach feature (28
  cot, truoc la 29) va khong con trong top-15 importance.
- **`alert_case_studies_v1.md` (case Chibi Finance/qbridge_qubit_2022 va
  ronin_benign_control_2022) — CHUA ghi de file chinh thuc**: de sinh lai dung
  cach, `scripts/generate_alert_case_studies.py` doi hoi `rq2_oof_predictions.csv`
  (assert prob tinh lai phai khop OOF luu san) — file nay la OUTPUT CHINH THUC
  cua `scripts/run_rq2_prefix_evaluation.py`, va he thong sandbox **DA TU DONG
  CHAN** lenh chay lai script do (phan loai "Irreversible Local Destruction")
  khi toi thu ghi de. Toi da backup file cu
  (`rq2_prefix_evaluation_folds_PRE_PREFIXRATIOFIX_backup.csv`,
  `rq2_oof_predictions_PRE_PREFIXRATIOFIX_backup.csv`) nhung KHONG ep chay lai
  script chinh thuc — thay vao do tinh mot ban OOF CACH LY rieng
  (`data/processed/rq2_oof_predictions_prefixratiofix_check_2026-09-28.csv`,
  khong dung lam input cho bat ky script chinh thuc nao) de tra loi cau hoi
  "case study doi bao nhieu":

  | Case | CU prob | CU threshold | MOI prob | MOI threshold | Ket luan alert |
  |---|---|---|---|---|---|
  | TP qbridge_qubit_2022 (k_5) | 0,9849 | 0,9424 | 0,9745 | 0,9516 | Van VUOT threshold ca 2 ban — ket luan "phat hien som" KHONG doi |
  | FP ronin_benign_control_2022 (ratio_50) | 0,9980 | 0,9895 | 0,9980 | 0,9900 | Van VUOT threshold ca 2 ban — ket luan "false positive" KHONG doi |

  **Top-5 feature dong gop cua Case TP thay doi ro ret** (fit lai model fold
  voi feature set da sua, dung dung logic `generate_alert_case_studies.py`):
  - CU: `path_depth(+1.7712), inter_action_gap_mean(+0.8575), fan_out(-0.7128),
    value_retention(+0.6435), prefix_ratio(+0.5770)`
  - **MOI**: `path_depth(+2.1071), inter_action_gap_mean(+1.3082),
    fan_out(-0.6431), motif_rapid_token_pivot(+0.6016),
    inter_action_gap_std(-0.3984)` — `prefix_ratio` bien mat (dung ky vong),
    `value_retention` cung roi khoi top-5, thay bang `motif_rapid_token_pivot`
    va `inter_action_gap_std`; `path_depth` van la dong gop lon nhat, TANG
    ti trong (tu +1.77 len +2.11).
  - Case FP (ronin_benign_control_2022): top-5 HAU NHU KHONG DOI (`prefix_ratio`
    chua bao gio nam trong top-5 cua case nay) — `motif_merge(+4.7267 vs
    +4.7292 cu)`, prob 0,9980 vs 0,99798 cu, chenh khong dang ke.

  **Ket luan Buoc C (case study)**: ket luan DINH TINH cua ca 2 case (TP phat
  hien som thanh cong, FP la 1 giao dich benign that bi nham) KHONG DOI. Con so
  DINH LUONG (dac biet top-5 feature cua case TP) THAY DOI RO RET va can duoc
  cap nhat trong paper/report neu duoc trich dan chi tiet. **Viec ghi de chinh
  thuc `alert_case_studies_v1.md` (va `rq2_oof_predictions.csv`/
  `rq2_prefix_evaluation_folds.csv` lam no dua vao) can su xac nhan tuong minh
  cua nguoi dung** vi day la thay doi khong the hoan tac de dang len nhieu file
  dong cung cung luc (khac voi cac buoc kiem tra cach ly khac trong bao cao nay).

## Buoc D (2026-09-28, lan 3) — T13 co nam trong pham vi paper khong

Grep `results/tables/main_table.csv` va `results/tables/baseline_results_v2.csv`
(2 bang RQ1 chinh thuc, nguon duy nhat co the doi chieu voi `.tex` vi file
`.tex` khong nam trong repo): **T13 KHONG xuat hien** trong ca hai. T13 chi ton
tai nhu 1 thu nghiem doc lap, rieng le trong
`results/reports/t13_logreg_baseline_2026-09-22.md` +
`results/tables/t13_logreg_baseline_2026-09-22.csv` (so sanh Logistic Regression
vs M1 tren CUNG feature set, ket luan "khong du bang chung linear hay boosting
tot hon"). File nay CO trich dan lai so M1 CU (0,6624) trong bang so sanh —
neu T13 duoc nhac den trong `.tex` (vi du nhu 1 robustness check phu), con so
0,6624 o day cung stale, nhung **ban than T13 khong nam trong bat ky bang/con
so chinh (Table 3, RQ1 answer) nao dang duoc dong cung chinh thuc** — an toan
de KHONG sua gap, chi ghi chu stale, dung nhu ket luan lan truoc.

## Danh sach file moi/thay doi phat sinh o lan cap nhat nay (Buoc A-D)

- Sua tiep: khong co thay doi code moi (chi `src/models/baselines.py` nhu da
  liet ke o lan truoc).
- Ghi de CHINH THUC (theo yeu cau tuong minh cua nguoi dung, co backup):
  `results/models/m1_final.joblib`, `results/reports/model_card_m1.md`.
  Backup: `*_PRE_PREFIXRATIOFIX_backup.*`.
- Backup nhung KHONG ghi de (bi sandbox chan, chua co xac nhan nguoi dung):
  `results/tables/rq2_prefix_evaluation_folds_PRE_PREFIXRATIOFIX_backup.csv`,
  `data/processed/rq2_oof_predictions_PRE_PREFIXRATIOFIX_backup.csv` (ban goc
  van con nguyen, chua bi doi).
- Them moi, khong ghi de gi: `scripts/run_rq2_prefix_evaluation_prefixratiofix_check_2026-09-28.py`,
  `scripts/run_rq2_oof_prefixratiofix_check_2026-09-28.py`,
  `results/tables/rq2_prefix_evaluation_folds_prefixratiofix_check_2026-09-28.csv`,
  `data/processed/rq2_oof_predictions_prefixratiofix_check_2026-09-28.csv`.

## Viec can nguoi dung quyet dinh tiep theo

1. **Quan trong nhat**: phat hien trung tam cua Discussion ("nhom trajectory
   DAI co loi ich CO Y NGHIA thong ke") **khong con dung sau khi sua leak**
   (CI moi chua 0). Can quyet dinh cach trinh bay lai doan nay trong paper
   (ha xuong thanh "xu huong", bo hoan toan, hay tim cach trinh bay khac) —
   day la anh huong lon nhat cua toan bo viec sua leak nay len noi dung khoa
   hoc cua bai.
2. **Table 3/RQ1**: can cap nhat CON SO tuyet doi (M1: 0,662->0,592; B3:
   0,688->0,637; paired diff/CI/p nhu bao cao lan truoc) — KET LUAN "khong y
   nghia" khong doi.
3. **Table 3(b)/RQ2**: cac checkpoint ty le hau nhu khong doi; **k_2 giam manh
   (0,747->0,472)** — can ra soat xem paper co trich con so nay o dau khong.
4. **Case study TP** (neu duoc trich chi tiet trong paper/appendix): top-5
   feature va contribution can cap nhat theo so MOI o Buoc C. Case FP hau nhu
   khong doi.
5. **Co muon toi thuc su ghi de `rq2_oof_predictions.csv` +
   `rq2_prefix_evaluation_folds.csv` + `alert_case_studies_v1.md` chinh thuc
   khong?** Day la hanh dong bi sandbox tu dong chan do tinh khong-the-hoan-tac
   (dù đã có bản backup) — can nguoi dung xac nhan ro rang truoc khi thu lai.
6. T13 khong nam trong bang chinh thuc nao — an toan, khong can sua gap.
