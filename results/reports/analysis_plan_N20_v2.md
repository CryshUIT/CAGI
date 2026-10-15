# Ke hoach phan tich N=20 — PHIEN BAN 2 (2026-10-14, sau Checkpoint C'')

## Changelog so voi v1

- **v1**: `results/reports/analysis_plan_N20.md`
  (SHA-256 cua v1, tinh luc viet xong: xem
  `results/reports/analysis_plan_N20_selfhash.json` ->
  `40a607c57e00b4bb41475d04cbb87451c1dc9c1e202df7530fe6547e62119e86`).
  **GIU NGUYEN, khong sua ngam.**
- **v2 (file nay)**: cap nhat SO DEM du lieu sau khi dong bo vong mine
  "v2_complexity" (he thong) cho 5 incident moi o Checkpoint C'' (muc 2):
  `data/processed/features_v2_N20.parquet` tu 4.004 dong (754 trajectory)
  **-> 4.247 dong (798 trajectory)**. Giao thuc phan tich CHINH (muc 1-10
  cua v1) **KHONG DOI MOT CHU NAO** — chi so lieu dau vao thay doi.

## Giao thuc chinh (y het v1, KHONG tuning) — nhac lai de doi chieu

1. Du lieu: `data/processed/features_v2_N20.parquet` (**4.247 dong, 798
   trajectory, 20 incident positive**, da qua `dedupe_pooled_prefixes()` ->
   **2.234 dong dedup, positive rate = 6,67%**) truoc khi pool.
2. Model: B0-B3 + M1 (da sua leak `prefix_ratio`), KHONG doi tham so.
3. Split: LeaveOneGroupOut, **20 fold**.
4. Metric chinh: PR-AUC pooled, bootstrap cap incident (n_boot=2000, seed=42).
5. Kiem dinh cap chinh: paired bootstrap (M1-B3) + Wilcoxon.
6. Phan nhom theo do dai trajectory: nguong <=40/>40 action, GIU NGUYEN.
7. Tuong quan Spearman(gap, do dai trajectory).
8. False-alert rate (`false_alerts_per_1000`).
9. Bao cao theo tung incident (khong chi pooled).
10. Trich N=15 leak-fixed (khong chay lai): M1=0,5924, B3=0,6366, diff=-0,0462,
    CI=[-0,1434,+0,0497], p=0,3028.

## Sensitivity da khai bao truoc

- **N=19 (bo Cork)** — khong doi so voi v1.

## Quyet dinh ve Cork (khong doi so voi v1)

Cork van nam trong phan tich CHINH (dat cong provenance qua Uniswap Universal
Router — xac nhan lai o Checkpoint C'': trajectory CHI 1 action, sinh 4 dong
prefix (tat ca ratio_25/50/75/100, deu label=1), KHONG co bucket k_2/3/5/7).
N=19 la sensitivity phu.

## Diem dung (khong doi)

N=20 la diem dung CUOI CUNG — khong mo rong them du ket qua D the nao.

## Xac nhan dieu kien truoc khi chay (Checkpoint C'')

- v2_complexity da dong bo cho 5 incident moi: 0/5 truncated (Hedgey
  chi dat 6/10 do cham max_candidates_checked — nang suat tu nhien, khong
  phai loi).
- Tap negative "chinh" (125 dong, Checkpoint B) xac nhan KHONG bi anh huong
  boi loi cau hinh (buoc mine khong doc allowlist).
- `pytest tests/`: 211/211 PASS (ke ca sau khi phat hien+sua 1 regression
  test-isolation moi phat sinh).
- Test tai tao (`test_n20_reproduces_v1.py`): 3/3 PASS.

**-> Du dieu kien, tien hanh Checkpoint D ngay sau file nay.**

---
*(SHA-256 cua chinh file v2 nay: xem
`results/reports/analysis_plan_N20_v2_selfhash.json`, tinh NGAY SAU KHI
viet xong noi dung, TRUOC khi chay Checkpoint D.)*
