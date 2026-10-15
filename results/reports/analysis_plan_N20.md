# Ke hoach phan tich N=20 (dang ky TRUOC khi chay Checkpoint D) — 2026-10-14

**Trang thai: VIET TRUOC KHI CHAY D.** Checkpoint D hien dang TAM DUNG cho
toi khi nguoi dung xac nhan sau khi xem Checkpoint C' (phat hien 1 loi cau
hinh that o muc 6, da sua - xem
`results/reports/dataset_expansion_N20_checkpointCprime_2026-10-14.md`).

## Ghi chu minh bach cho paper/thesis (theo yeu cau nguoi dung)

Viec mo rong N=15 -> N=20 duoc QUYET DINH SAU KHI da thay ket qua N=15 (CI
rong, khong co y nghia thong ke). Dieu nay KHONG sai ve mat phuong phap,
NHUNG phai khai bao thang trong paper/thesis la **"mo rong sau phan tich so
bo (post-hoc expansion), dung o N=20 da dinh truoc"** — khong trinh bay nhu
the N=20 la co' muc tieu mau tu dau. Quy tac dung duoi day (da CHOT truoc
khi chay D) chinh la bang chung cho "da dinh truoc", tranh p-hacking qua
nhieu vong mo rong tuy tien.

## Giao thuc chinh (y het N=15, KHONG tuning)

1. **Du lieu**: `data/processed/features_v2_N20.parquet` (4.004 dong, 754
   trajectory, 20 incident positive) qua `dedupe_pooled_prefixes()` (cung
   ham da dung cho N=15) truoc khi pool.
2. **Model**: B0-B3 + M1 (`src/models/baselines.py`, DA SUA leak
   `prefix_ratio`) — KHONG doi hyperparameter/tham so nao.
3. **Split**: Leave-one-incident-out (LeaveOneGroupOut), **20 fold** (thay vi
   15) - `src/evaluation/nested_eval.py::evaluate_model_nested`, threshold
   chon tren inner-train OOF, `target_fpr=0.01` (khong doi).
4. **Metric chinh**: PR-AUC pooled (toan bo outer-test OOF), bootstrap cap
   **incident** (`bootstrap_incident_level`, **n_boot=2000, seed=42**,
   khong doi).
5. **Kiem dinh cap chinh**: paired bootstrap (M1 - B3) muc incident, cung
   `n_boot=2000, seed=42`, Wilcoxon signed-rank — bao cao mean diff, 95% CI,
   p-value.
6. **Phan nhom theo do dai trajectory**: **NGUONG <=40 action vs >40 action
   GIU NGUYEN nhu N=15** (khong doi theo du lieu moi) — bootstrap cap
   incident tung nhom, bao cao mean diff + CI tung nhom.
7. **Tuong quan**: Spearman(gap PR-AUC per-incident, do dai trajectory) —
   bao cao rho + p, loai outlier THEO CUNG TIEU CHI da dung o N=15
   (new_free_dao_2022, neu van la outlier ro ret nhat sau khi tinh lai -
   KHONG tu dong loai them bat ky incident nao khac chi vi no "la outlier"
   o N=20, phai neu ro neu co outlier MOI xuat hien).
8. **False-alert rate**: `false_alerts_per_1000` (metric co san trong
   `evaluate_model_nested`, khong doi cach tinh).
9. **Bao cao THEO TUNG INCIDENT** (khong chi pooled) — bang per-incident
   PR-AUC cho M1 va B3, giong cau truc `rq1_paired_bootstrap_rerun_2026-09-22.md`.
10. **Trich dan N=15 leak-fixed** (KHONG chay lai, chi trich so da co san tu
    `results/reports/prefix_ratio_leak_2026-09-28.md`): M1=0,5924, B3=0,6366,
    paired diff=-0,0462, 95% CI=[-0,1434,+0,0497], p=0,3028 — dat canh N=20 de
    so sanh truc tiep.

## Sensitivity da khai bao TRUOC (declared before seeing D's results)

- **N=19 (bo Cork)**: chay LAI dung giao thuc tren nhung loai
  `cork_protocol_2025` khoi tap incident (19 fold thay vi 20). Ly do khai bao
  truoc: Cork co trajectory MONG NHAT (1 action, endpoint_confirmed=False) -
  muon biet ket qua co nhay cam voi 1 incident duy nhat nay khong. **Day la
  sensitivity check, KHONG phai tieu chi loai/giu Cork khoi phan tich
  CHINH** (Cork van nam trong phan tich chinh vi da dat cong provenance —
  xem quyet dinh duoi).

## Quyet dinh ve Cork (CHOT TRUOC khi chay D, theo dung yeu cau nguoi dung)

Sau khi dieu tra chi tiet (Checkpoint C'), xac nhan: trajectory 1-action cua
Cork la **DU LIEU THAT** (1 giao dich ETH that, block that, da xac minh qua
on-chain truc tiep - khong phai loi cau hinh/bug lam mat du lieu). Loi cau
hinh THAT duoc tim thay o buoc nay (config khong duoc truyen dung) **DA DUOC
SUA** va KET QUA 1-action la ket qua SAU KHI sua, khong phai truoc. Theo dung
nguyen tac "khong chon/loai theo ket qua mo hinh, chi theo provenance" da
ap dung xuyen suot du an: **Cork VAN NAM TRONG phan tich CHINH** (dat gate
RQ1 qua 1 DEX action that toi Uniswap Universal Router da xac minh, dung
allowlist N20) — chi bi loai khoi tap tinh lead-time/RQ2 (endpoint_confirmed
=False, da quyet dinh tu truoc). N=19 (bo Cork) la **sensitivity phu**, dua
vao bang canh ket qua chinh, KHONG thay the ket qua chinh N=20.

## Diem dung (CHOT, khong mo rong them)

**N=20 la diem dung CUOI CUNG.** Du ket qua Checkpoint D the nao (CI hep lai
hay khong, ket luan doi hay khong), **KHONG tiep tuc mo rong len N=21+** dua
tren ket qua do. Neu muon mo rong tiep trong tuong lai, phai la 1 quyet dinh
MOI, rieng biet, co ly do rieng (khong phai "vi N=20 van chua du y nghia").

## Xac nhan khong vi pham rang buoc

- Khong doi code/tham so/giao thuc danh gia nao so voi N=15.
- Khong chon/loai incident dua tren ket qua mo hinh (Cork giu lai vi
  provenance, khong vi ket qua).
- Khong ghi de bat ky file freeze v1.0/N=15 nao (xac nhan lai o Checkpoint C').
- Khong tu commit/push.
- Giu an danh (khong co thong tin dinh danh tac gia trong file nay).

---

## SHA-256 cua chinh file ke hoach nay (tu-tham-chieu, tinh SAU KHI noi dung o tren da viet xong, truoc khi chay D)

*(xem file `results/reports/analysis_plan_N20_selfhash.json` — tach rieng vi
khong the tu include hash cua chinh minh trong noi dung)*
