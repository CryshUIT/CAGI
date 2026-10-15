# Ke hoach phan tich N=30 (2026-10-15)

**CHI la ke hoach/pre-declaration — CHUA chay bat ky model/RQ1/RQ2 nao.**
Mo rong truc tiep tu `analysis_plan_N20_v2.md` (giu nguyen, khong sua),
ap dung CUNG giao thuc cho 30 incident.

## Giao thuc chinh (y het N20_v2 muc 1-9, mo rong pham vi du lieu)

1. Du lieu: `data/processed/features_v2_N30.parquet` (**5.973 dong, 1.127
   trajectory, 30 incident positive**), qua `dedupe_pooled_prefixes()`
   truoc khi pool (so dong dedup se tinh khi chay, KHONG tinh truoc o day
   de tranh sai lech voi ket qua thuc te).
2. Model: B0-B3 + M1 (da sua leak `prefix_ratio`), **KHONG doi tham so**
   so voi N15/N20.
3. Split: LeaveOneGroupOut, **30 fold** (tang tu 20 fold o N20).
4. Metric chinh: PR-AUC pooled, bootstrap cap incident (n_boot=2000,
   seed=42) — **giu nguyen seed/n_boot nhu N15/N20, khong doi**.
5. Kiem dinh cap chinh: paired bootstrap (M1-B3) + Wilcoxon.
6. Phan nhom theo do dai trajectory: nguong <=40/>40 action, **GIU
   NGUYEN** (khong doi nguong de tranh p-hacking qua threshold).
7. Tuong quan Spearman(gap, do dai trajectory).
8. False-alert rate (`false_alerts_per_1000`).
9. Bao cao theo tung incident (khong chi pooled) — 30 dong.

## Moc cong don (co dinh truoc, tinh theo THU TU REGISTRY, CUNG 1 config_N30.yaml cho ca 4 moc)

Thu tu dang ky trong `metadata/incident_registry_N30.csv` (cot
`incident_id`, loc `eval_tier=="primary"` va `label==1`) khop CHINH XAC
voi thu tu lich su xay dung dataset — khong can chon lai tay:

| Moc | Pham vi (hang 1..N theo thu tu registry) | Tuong duong |
|---|---|---|
| **N=15** | hang 1-15 (ronin_bridge_2022 .. new_free_dao_2022) | dung 15 incident v1.0 goc |
| **N=20** | hang 1-20 (+ zunami/onyx/beanstalk/hedgey/cork) | dung tap N20 |
| **N=25** | hang 1-25 (+ dough/0xinfini/prisma/uranium/inverse) | dung tap lo 1 |
| **N=30** | hang 1-30 (+ lendhub/thorchain2/popsicle/heco/easyfi) | tap N30 day du |

**QUAN TRONG**: ca 4 moc deu duoc tinh tu CUNG 1 lan build duoi
`configs/data_N30.yaml` (loc `source_id` theo danh sach incident cua
tung moc tu `features_v2_N30.parquet`), **KHONG build lai bang
`data.yaml`/`data_N20.yaml` rieng cho N=15/N=20** — dam bao allowlist
dong nhat xuyen suot 4 moc, chi khac SO LUONG incident dua vao.

**Gia tri N=15 da freeze, trich lai (khong chay lai)**:
M1 = 0,5924; B3 = 0,6366; diff = -0,0462; CI=[-0,1434; +0,0497];
p = 0,3028 (nguon: `analysis_plan_N20_v2.md` muc 10, da freeze tu truoc).

**N=20/25/30**: **CHUA CO SO LIEU** — se tinh khi chay Checkpoint phan
tich (ngoai pham vi file nay). File nay CHI khai bao TRUOC cach tinh,
khong du doan/gia dinh ket qua.

## 4 sensitivity (CO DINH, dung CHINH XAC 4 cai nay — KHONG them sau khi co ket qua)

### (a) Bo incident co n_actions <= 2

Ap dung cho: `cork_protocol_2025` (n_actions=1). Kiem tra lai neu co
incident nao khac n_actions<=2 truoc khi chay (hien tai chi 1).

### (b) Bo incident co n_actions > 5.000

Ap dung cho: `inverse_finance_2022_jun` (11.592), `easyfi_2021`
(16.560-17.166 tuy lan build) — ca 2 incident "hub explosion" da ghi
trong `known_builder_limitations.md`.

### (c) Bo incident co trajectory doi do "allowlist completion"

Ap dung cho: `hedgey_finance_2024` (662->755, Universal Router v1.2 them
o N20), `uranium_finance_2021` (39->64, TornadoProxy them o lo 2 —
xem `expansion_N30_predeclaration_v8.md`). **LUU Y**: Uranium doi do
TornadoProxy duoc them cho Popsicle (khong lien quan truc tiep ban than
Uranium) — day la vi du ro nhat cho loai sensitivity nay.

### (d) RQ2 chi tren incident co endpoint la mixer

Loc theo `endpoint_type` chua chuoi "mixer" HOAC `mixer_families` khac
rong trong `incident_registry_N30.csv` (bao gom CA endpoint_confirmed=
True va False, vi RQ2 quan tam "co bang chung mixer" khong phai "co
duoc pipeline xac nhan tu dong" — xem dinh nghia muc tieu RQ2 da khai
bao o `expansion_N30_predeclaration_v6.md`). Danh sach du kien (tinh
truoc, CHUA chay): `ronin_bridge_2022` (Wintermute - KHONG phai mixer
dung nghia, loai), `feg_bridge_2024`, `wault_finance_2021`,
`paraluni_2022`, `hackerdao_2022`, `new_free_dao_2022`,
`dough_finance_2024`, `prisma_finance_2024`, `inverse_finance_2022_jun`,
`lendhub_2023`, `uranium_finance_2021` (bao cao neu mixer, khong trong
window), `thorchain2_2021` (bao cao neu mixer, khong trong window),
`popsicle_finance_2021` (mixer that nhung khong duoc pipeline nhan
dien), `heco_htx_2023` (mixer ngoai window). Danh sach CHINH XAC se duoc
xac nhan lai khi chay (loc code tu CSV, khong dua vao danh sach tay nay
neu khac).

## Diem dung

N=30 la diem dung CUOI CUNG cho dot mo rong nay (theo
`expansion_N30_predeclaration_v1.md`) — khong mo rong them.

## Rang buoc (giu nguyen tu N20)

- KHONG doi tham so model giua cac moc N.
- KHONG them sensitivity nao ngoai 4 cai da liet ke o tren SAU KHI co
  ket qua — neu phat hien can them, phai ghi THANH 1 v2 moi cua file
  nay (sau khi chay, truoc khi cong bo ket qua), khong sua ngam file v1.

---
*(SHA-256 cua chinh file nay: tinh NGAY SAU KHI viet xong noi dung, xem
`results/reports/analysis_plan_N30_selfhash.json`)*
