# M1_v4 - THAY THE path_depth bang ban bien doi (Attempt #10, 2026-09-26)

2 phuong an: (A) log1p(path_depth) khong hyperparameter; (B) capped=min(path_depth,cap), cap chon qua nested inner-CV moi outer fold (co the khac nhau giua cac fold).

| Model | Mean PR-AUC (pooled) | 95% CI | Diff vs M1 | CI vs M1 | Diff vs B3 | CI vs B3 |
|---|---|---|---|---|---|---|
| M1_v4_log1p | 0.6624 | [0.5234, 0.8864] | +0.0000 | [+0.0000, +0.0000] | +0.0355 | [-0.0286, +0.1288] |
| M1_v4_capped | 0.6603 | [0.5234, 0.8835] | +0.0000 | [+0.0000, +0.0000] | +0.0355 | [-0.0286, +0.1288] |

## Kiem tra dung 2 ca da chan doan

| Variant | source_id | prefix_len | prob moi | prob M1 chinh thuc | threshold |
|---|---|---|---|---|---|
| M1_v4_log1p | ronin_bridge_2022__hn012 | 2 | 0.9999 | 0.9999 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 3 | 0.9999 | 0.9999 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 5 | 0.9988 | 0.9988 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 7 | 0.9997 | 0.9997 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 14 | 0.9894 | 0.9894 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 28 | 0.9720 | 0.9720 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 42 | 0.9456 | 0.9456 | 0.8867 |
| M1_v4_log1p | ronin_bridge_2022__hn012 | 55 | 0.9715 | 0.9715 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 2 | 0.9960 | 0.9960 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 3 | 0.9925 | 0.9925 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 5 | 0.9012 | 0.9012 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 7 | 0.8335 | 0.8335 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 26 | 0.9995 | 0.9995 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 52 | 0.9994 | 0.9994 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 78 | 0.9992 | 0.9992 | 0.8867 |
| M1_v4_log1p | ronin_benign_control_2022 | 103 | 0.9995 | 0.9995 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 2 | 0.9999 | 0.9999 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 3 | 0.9999 | 0.9999 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 5 | 0.9988 | 0.9988 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 7 | 0.9997 | 0.9997 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 14 | 0.9894 | 0.9894 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 28 | 0.9720 | 0.9720 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 42 | 0.9456 | 0.9456 | 0.8867 |
| M1_v4_capped | ronin_bridge_2022__hn012 | 55 | 0.9715 | 0.9715 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 2 | 0.9960 | 0.9960 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 3 | 0.9925 | 0.9925 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 5 | 0.9012 | 0.9012 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 7 | 0.8335 | 0.8335 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 26 | 0.9995 | 0.9995 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 52 | 0.9994 | 0.9994 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 78 | 0.9992 | 0.9992 | 0.8867 |
| M1_v4_capped | ronin_benign_control_2022 | 103 | 0.9995 | 0.9995 | 0.8867 |

## Giai thich CO CO CHE (khong chi la "khong cai thien")

**log1p**: PR-AUC/xac suat GIONG HET M1 chinh thuc o TAT CA outer fold (diff=+0.0000 chinh xac tuyet
doi, khong phai lam tron). Ly do TOAN HOC, khong phai thuc nghiem: log1p la phep bien doi DON DIEU
TANG - XGBoost chi dua vao THU TU (rank) cua gia tri feature de chon split, khong dua vao gia tri
tuyet doi, nen 1 bien doi don dieu tren DUNG 1 cot khong the nao lam thay doi cay quyet dinh da hoc
duoc (moi split threshold tren gia tri goc deu co 1 split tuong duong chinh xac tren gia tri da log).

**capped**: cung cho ket qua GIONG HET (diff=+0.0000) tai fold `ronin_bridge_2022` - kiem tra ky:
cap duoc CHON qua nested inner-CV cho dung fold nay la **cap=2** (inner PR-AUC 0.8243 vs 0.8238 cho
cap=3, chenh lech khong dang ke). Nhung `ronin_bridge_2022__hn012`/`ronin_benign_control_2022` co
`path_depth` THO **DUNG BANG 2** o het cac prefix con dang la nguyen nhan loi - `clip(upper=2)` LA
PHEP KHONG-THAY-DOI (no-op) cho chinh cac dong nay (2 clip len 2 van la 2)! Day la ly do co che chinh
xac, khong phai ngau nhien: cap∈{2,3} duoc chon lam ung vien KHONG BAO GIO cham duoc vao dung vung
gay loi (path_depth==2), vi de "sua" dung 2 ca nay can cap=1 hoac cap=0 - nhung cap do se pha huy gan
het tin hieu that cua path_depth cho 66% positive con lai co path_depth>=2.

**Ket luan sau ca 3 attempt lien quan (#9, #10a, #10b)**: van de KHONG THE sua bang cach them/bien doi
1 feature don le theo huong da thu - can either (a) sua CHINH CACH TINH path_depth (vd chuan hoa theo
so action CAN THIET de dat do sau do, tuong tu #9 nhung phai THAY THE thay vi THEM, hoac (b) mot co
che hoan toan khac (feature interaction, hoac loai bo hoan toan path_depth va bu bang tap feature
khac) - ca 2 huong nay vuot pham vi "sua 1 feature" da dat ra cho track nay va can nghien cuu rieng.

## KET LUAN (thong ke)

log1p: KHONG CAI THIEN CO Y NGHIA THONG KE (dong nhat tuyet doi voi M1, ve mat toan hoc khong the khac)

capped: KHONG CAI THIEN CO Y NGHIA THONG KE (khong cham duoc vao dung vung loi, xem giai thich co che o tren)


