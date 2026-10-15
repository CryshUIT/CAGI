# Deviations N30 — sai lech giua ket qua da chay va noi dung dang ky trong analysis_plan_N30_v3.md (2026-10-15)

**CHI mo ta, KHONG suy luan ket qua, KHONG sua analysis_plan_N30_v3.md hay
bat ky file dong bang nao. KHONG chay model moi khi viet file nay.**

## (i) Loai tru Spearman khong dang ky

`scripts/run_evaluation_N30_v3.py` dung `outlier_id = "new_free_dao_2022"`
(copy tu `scripts/run_checkpointD_N20_analysis.py:131`, comment "theo tieu
chi da dung o N=15") de loai 1 incident truoc khi tinh Spearman(gap, do
dai trajectory). Grep toan bo `analysis_plan_N30.md`, `_v2.md`, `_v3.md`
cho "new_free_dao"/"outlier": **KHONG co dong nao dang ky quy tac nay**.

Tinh lai TRUC TIEP tu `results/tables/evaluation_N30_per_incident_table.csv`
(da co san, KHONG chay model moi):

| Tap | rho | p | jackknife_mean | jackknife_se |
|---|---|---|---|---|
| **n=30 (day du, KHONG loai ai) — CHINH (khong co co so loai trong v3)** | -0.09945389692267213 | 0.6010547350294163 | -0.09936541518613021 | 0.21174096366774714 |
| n=29 (loai new_free_dao_2022, nhu da bao cao truoc) | -0.01802696650971533 | 0.9260502902569467 | -0.01802548034466065 | 0.2165371991361877 |

## (ii) CI them cho Table 3b, ngoai yeu cau v3

`analysis_plan_N30_v3.md` khong co dong nao yeu cau CI cho Table 3b hay
RQ2 (chi "Kiem dinh cap chinh: paired bootstrap + Wilcoxon" gan voi RQ1
pooled). Ham `table_3b_ratio_checkpoints()` trong
`scripts/run_evaluation_N30_v3.py` da TU THEM
`bootstrap_incident_level(n_boot=2000, seed=42)` cho ca M1 va B3 o moi
bucket ratio - vuot yeu cau toi thieu, KHONG phai vi pham dang ky truoc
(khong doi dinh nghia/giao thuc chinh) nhung la 1 bo sung KHONG duoc ghi
truoc trong v3. RQ2 (20 ca va 9 ca) **KHONG co CI nao** - dung mo ta
(trung binh qua fold), dung yeu cau "mo ta, khong suy luan".

## (iii) mean_diff la macro-gap, hieu pooled la dai luong KHAC

- `mean_diff=+0.0305` (da bao cao o ket qua chinh) = trung binh 30 gap
  PR-AUC THEO TUNG INCIDENT (`paired_bootstrap()`,
  `scripts/run_evaluation_N30_v3.py:99-106`: `diffs = a - b; diffs.mean()`
  voi a/b la mang PR-AUC tung incident cua M1/B3).
- Hieu PR-AUC pooled = PR-AUC(M1) - PR-AUC(B3) = 0.7761684329544181 -
  0.7542925486477836 = **0.021875884306634452** (≈0.0219) - mot DAI
  LUONG KHAC, tinh tu 1 gia tri PR-AUC tong hop (gop toan bo OOF roi
  tinh 1 duong cong PR duy nhat), KHONG phai trung binh cac gap rieng le.
- Thong ke "chinh" theo dang ky v1-v3 ("Kiem dinh cap chinh: paired
  bootstrap (M1-B3) + Wilcoxon") la **macro-gap** (+0.0305, CI=[-0.0168,
  +0.0878], Wilcoxon p=0.2528), vi Wilcoxon doi hoi du lieu ghep cap theo
  don vi (incident).
- **CI bootstrap cua hieu pooled (0.0219) CHUA tinh duoc** - can mang
  OOF tho (chua duoc luu ra dia) de resample dong thoi ca 2 mo hinh;
  tinh lai se can goi `evaluate_model_nested()` lan nua, vi pham rang
  buoc "khong chay model moi" hien tai.

## (iv) Ket qua muc 2 (RQ2 (d) k_7) - co che recall@FPR1%=0.1667

Dem truc tiep tu `features_v2_N30.parquet` (KHONG chay model), bucket
`k_7`, 9 incident sensitivity (d): **3/9 fold (feg_bridge_2024,
zunami_protocol_2023, inverse_finance_2022_jun) co test-set CHI 1 lop**
(1 dong positive, **0 dong negative**) -> `recall_at_fpr()`
(`src/evaluation/metrics.py:38`: `if len(set(y_true))<2: return nan`)
tra NaN cho 3 fold nay. `pandas.mean()` bo qua NaN mac dinh -> chi con
**6 fold hop le** (new_free_dao_2022, onyx_protocol_2023,
beanstalk_farms_2022, dough_finance_2024, prisma_finance_2024,
lendhub_2023), trong do 1/6 dat recall=1, 5/6 dat recall=0 -> mean =
1/6 = 0.16666... (khop dung 0.1667 da bao cao). KHONG phai noi suy -
`recall_at_fpr` dung `sklearn.roc_curve` (diem dat duoc THAT, chon TPR
lon nhat tai FPR<=1%). KHONG biet fold cu the nao la "1/6 thanh cong"
vi chi tiet tung fold cua RQ2 khong duoc luu ra dia trong lan chay nay -
can chay lai moi biet, KHONG suy dien them.

Tong so lieu bucket k_7/(d): 36 dong = 9 positive (1/incident) + 27
negative (phan bo rat lech: 0,0,0,6,2,13,2,2,2 theo tung incident).
