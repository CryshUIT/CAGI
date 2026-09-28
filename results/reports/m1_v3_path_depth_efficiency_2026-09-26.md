# M1_v3 - path_depth_per_action (Huong 9, LAN CUOI, 2026-09-26)

Feature moi: `path_depth_per_action = path_depth / prefix_len` - nham sua loi False Positive tap trung (83% toan du an) tai `ronin_bridge_2022__hn012` va `ronin_benign_control_2022`, do `path_depth` (feature gain cao nhat, 185.2, gap 9.5 lan feature thu 2) tao ranh gioi gia tao path_depth>=2 (2.2% negative vs 66% positive).

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |
| B3 (moc) | 0.6875 | - |
| **M1_v3 (+path_depth_per_action)** | **0.6590** | [0.5213, 0.8880] |

**Paired diff (M1_v3 - M1 chinh thuc) = +0.0019, 95% CI = [-0.0069, +0.0119]**

**Paired diff (M1_v3 - B3) = +0.0374, 95% CI = [-0.0253, +0.1276]**

## Breakdown tren vung loi da chan doan (negative co path_depth>=2, n=37)

M1_v3: mean_prob=0.6580, n_FP=16/37

M1 chinh thuc: mean_prob=0.6437 (15/18 FP toan du an nam trong nhom nay)

## KET LUAN (pooled)

KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc (pooled). CI chua 0,
diem uoc luong gan nhu khong doi (+0.0019).

**Quan trong hon**: fix KHONG sua duoc dung cho ca loi da chan doan - xac
suat cua `ronin_bridge_2022__hn012`/`ronin_benign_control_2022` GAN NHU
KHONG DOI o moi prefix_len (vd hn012 prefix=55: 0.9715->0.9271, van vuot xa
threshold 0.8317; benign_control van >=0.90 o MOI diem). So FP trong "vung
loi" (path_depth>=2) con TANG nhe (16/37 vs so sanh tuong duong 15/18 truoc
do tren toan bo dataset). **Nguyen nhan co the**: them 1 feature ty le KHONG
buoc XGBoost ngung dua vao `path_depth` tho - cay quyet dinh van co the tiep
tuc split truc tiep tren `path_depth` (van con nguyen trong tap feature,
khong bi loai bo), nen `path_depth_per_action` chi la them 1 tuy chon ma
model KHONG BAT BUOC phai dung, va voi N=15 qua nho de model tu hoc duoc
loi ich cua no. Mot huong that su khac (vd BOT/chuan hoa lai `path_depth`
thay vi CHI them feature moi) co the can thiet hon - nhung nam ngoai pham
vi "them feature, khong sua feature co san" cua attempt nay, va du an da
dong track cai thien M1 sau lan thu nay (xem m1_improvement_attempts).
