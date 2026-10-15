# Khai bao truoc — Mo rong N=20 -> N=30 (dot 2) — 2026-10-14

**Viet TRUOC khi sang loc ung vien. Day la cam ket, khong sua ngam (sua se
tao ban v2 co changelog, giu nguyen ban nay + hash).**

## 1. Dich cuoi

**N=30 la dich cuoi CUA DOT NAY, KHONG mo rong them sau do** (tru khi co 1
quyet dinh MOI, rieng biet trong tuong lai, voi ly do rieng — khong phai "vi
chua du y nghia thong ke"). Khong dung som hay tiep tuc dua tren ket qua mo
hinh — chi dua tren so luong ung vien dat cong provenance.

## 2. Tieu chi chon ung vien — GIU NGUYEN 3 cong nhu N20/v1.0

1. Co bao cao cong khai doc lap (CertiK/SlowMist/Beosin/BlockSec/PeckShield/
   Halborn/Chainalysis/Elliptic/SharkTeam/QuillAudits/... hoac tin tuc uy
   tin) quy thuoc dia chi seed.
2. start_block va diem thoat (exit) doi chieu duoc ON-CHAIN THAT voi bao
   cao (khong chi WebSearch).
3. Dong tien roi seed qua bridge/DEX/mixer DA XAC MINH (truc tiep trong
   trajectory HOAC evidence thay the da chap nhan tien le — vd mixer thay
   the hoan toan cho bridge+DEX, nhu FEG Bridge/Zunami/Onyx).

Thu tu xep hang duoc GHI LAI TRUOC KHI thu thap du lieu that (xem
`dataset_expansion_N30_plan.md` sau Giai doan 1). Them tuan tu THEO DUNG thu
tu nay — khong nhay coc chon ung vien "de hon" truoc.

**Moi ung vien phai qua cong provenance (3 tieu chi tren, xac nhan on-chain
that) TRUOC KHI ton quota khai thac hard-negative** — dung quy tac da ap
dung thanh cong o dot N20.

## 3. Gioi han sang loc + quy tac khong ha chuan

- Sang **toi da 20 ung vien MOI** (ngoai 3 dy phong cu da xac minh:
  Dough Finance, 0xInfini, Prisma Finance).
- **Neu it hon 10 dat cong provenance**: N cuoi = 20 + so dat (vi du chi 7
  dat thi dung o N=27) — **KHONG ha chuan de co du 10**.
- Chain: uu tien theo provenance that va kha thi ve quota (KHONG chon theo
  "incident nay se lam mo hinh tot/xau"). Se ghi nhan phan bo chain cuoi
  cung trong bao cao, khong dat muc tieu phan bo truoc.

## 4. Khong chay model cho den khi freeze

**KHONG chay RQ1/RQ2 cho bat ky incident/lo nao cho den khi registry freeze
o N CUOI CUNG cua dot nay** (20+k, toi da 30). Khi do, danh gia **DUNG MOT
LAN**, theo DUNG giao thuc da dung cho N=15/20 (khong doi):
- LeaveOneGroupOut (LOIO), pooled OOF PR-AUC.
- Bootstrap cap incident, n_boot=2000, seed=42.
- Cung 5 baseline (B0-B3, M1), KHONG tuning hyperparameter.
- Bao cao **CONG DON** theo thu tu registry tai cac moc: N=15 (freeze, chi
  trich), N=20 (freeze, chi trich), N=25 (neu dat), N=30 (neu dat) — kem
  bang per-incident va bang 4 checkpoint tuong doi (ratio_25/50/75/100) cho
  M1 va B3.
- **Sensitivity khai bao truoc**: bo cac incident co `n_actions <= 2` (ap
  dung dong nhat cho ca incident cu lan moi neu co — hien tai Cork co
  n_actions=1, da la sensitivity N=19 da bao cao o Checkpoint D truoc).
- **Bao cao MOI ket qua, du tot hay xau** — khong chon loc trinh bay.

## 5. Rang buoc giu nguyen (nhu da cam ket o N20)

- KHONG ghi de/sua file freeze v1.0 (N=15) hay N=20 (manifest SHA-256 da
  ghi: xem `results/reports/freeze_N20_manifest_2026-10-14.json`).
- KHONG chon/loai incident dua tren ket qua mo hinh.
- KHONG doi code/tham so/quy tac hard-negative/trajectory builder/feature
  extractor/hyperparameter/giao thuc danh gia.
- Chi dung API cong khai mien phi (Etherscan V2, NodeReal neu co ung vien
  BSC) — quota khong du thi chia nhieu ngay, KHONG ha chuan.
- KHONG tu commit/push. Giu an danh (khong ten that/email/duong dan ca nhan).

## 6. Buoc tiep theo

Giai doan 1 (kiem ke + de xuat, CHUA thu thap/CHUA doi registry) — xem
`results/reports/dataset_expansion_N30_plan.md`, gui nguoi dung duyet TRUOC
khi vao Giai doan 2.
