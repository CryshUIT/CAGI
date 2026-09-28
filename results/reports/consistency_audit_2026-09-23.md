# Rà soát nhất quán số liệu M1 toàn repo (2026-09-23, Việc 3)

## 1. Grep "0.7364"/"0,7364" toàn repo

```
grep -rn "0\.7364\|0,7364" --include=*.py --include=*.md --include=*.csv --include=*.json -I .
```

**Kết quả: KHÔNG có match nào trong toàn bộ repo** (không chỉ giới hạn 2 ngày gần đây — quét toàn bộ,
kể cả các file cũ đã xác định hôm qua thuộc dự án khác/không liên quan — tất cả đều sạch).

## 2. Rà soát mọi file `results/reports/`, `results/tables/` timestamp 2026-09-22 và 2026-09-23

Danh sách file đã kiểm tra (mọi chỗ nhắc "M1"):

**results/reports/ (2026-09-22, 14 file có nhắc "M1"):**
- `ablation_t14_combined_2026-09-22.md` — M1_full=0,6624 (đúng); M1_no_motif/M1_no_semantic_action/M1_no_semantic_and_motif đều có số riêng, không phải 0,6624 (đúng, vì là biến thể ablation).
- `ensemble_1a_average_2026-09-22.md` — M1 gốc=0,6624 (đúng); Ensemble 1a=0,7345 (số riêng, đúng).
- `ensemble_1b_stacking_2026-09-22.md` — M1 gốc=0,6624 (đúng); Stacking=0,5946 (số riêng, đúng).
- `hackerdao_2022_investigation_2026-09-22.md` — chỉ nhắc PR-AUC per-incident (0,5053), không nhắc con số tổng M1 0,6624/0,7364 nào — sạch.
- `m1_improvement_attempts_2026-09-22.md` — bảng tổng hợp, mọi dòng "M1 gốc" đều 0,6624; các biến thể đều có số riêng (0,6062/0,7345/0,5946/0,6210/0,6970) — đúng.
- `nested_feature_selection_2026-09-22.md` — M1 gốc=0,6624 (đúng); FeatureSelection=0,6210 (số riêng, đúng).
- `nested_hpo_m1_2026-09-22.md` — M1 gốc=0,6624 (đúng); sau HPO=0,6062 (số riêng, đúng).
- `rq1_paired_bootstrap_rerun_2026-09-22.md` — M1=0,6624, B3=0,6875 (đúng, khớp main_table.csv).
- `seed_sensitivity_t12_2026-09-22.md` — M1 cả 5 seed đều 0,6624 (đúng, model tất định).
- `t13_logreg_baseline_2026-09-22.md` — M1=0,6624 (đúng); T13=0,7548 (số riêng, đúng).
- `t16_bridge_family_breakdown_2026-09-22.md` — không nhắc con số tổng M1, chỉ per-bridge-family — sạch.
- `t17_mimicry_proportional_2026-09-22.md` — đối chiếu pct=0 với "M1 chính thức (0,6624): KHỚP" (đúng).
- `t17_mimicry_stress_test_2026-09-22.md` — đối chiếu L=0 với "M1 chính thức (0,6624): KHỚP" (đúng).
- `trajectory_fair_weight_2026-09-22.md` — M1 gốc=0,6624 (đúng); TrajFairWeight=0,6970 (số riêng, đúng).

**results/tables/ (2026-09-22, 5 file CSV có cột/giá trị nhắc "M1"):**
- `ablation_t14_combined_2026-09-22.csv` — M1_full=0,6623886984073765 (=0,6624) — đúng.
- `ablation_t14_per_incident_2026-09-22.csv` — không có cột M1 tổng, chỉ per-incident — sạch.
- `nested_hpo_m1_fold_choices_2026-09-22.csv` — cột "baseline (M1 hien tai)" là PR-AUC **inner-CV per-fold** (không phải pooled 0,6624 — đây là giá trị đúng theo thiết kế, không phải lỗi).
- `seed_sensitivity_t12_2026-09-22.csv` — M1 cả 5 seed = 0,6623886984073765 — đúng.
- `t13_logreg_baseline_2026-09-22.csv` — M1=0,6623886984073765 — đúng.

**Các bảng kết quả biến thể khác (đã đối chiếu, đều có số riêng đúng, không lẫn 0,6624 hay 0,7364):**
`ensemble_1a_average_2026-09-22.csv` (0,7345), `ensemble_1a_seed_check_2026-09-22.csv` (0,7345 x5 seed),
`ensemble_1b_stacking_2026-09-22.csv` (0,5946), `nested_feature_selection_2026-09-22.csv` (0,6210),
`nested_hpo_m1_2026-09-22.csv` (bảng per-fold, các giá trị pr_auc là outer-test per-fold — không phải pooled),
`trajectory_fair_weight_2026-09-22.csv` (0,6970), `t17_mimicry_proportional_2026-09-22.csv` (pct=0 → 0,6623886984073765, đúng),
`t17_mimicry_stress_test_2026-09-22.csv` (level=0 → 0,6623886984073765, đúng), `rq1_paired_bootstrap_rerun_2026-09-22.csv`
(m1_mean_pr_auc=0,6623886984073765, b3=0,6874859194543349, đúng khớp main_table.csv).

**results/tables/, results/reports/ (2026-09-23, file mới tạo hôm nay):**
- `recall_precision_f1_at_fpr_2026-09-23.csv` / `.md` — M1 @ target_fpr=0,01 → pooled PR-AUC=0,6624 (đúng, khớp mốc chính thức); B3 @ 0,01 → 0,6875 (đúng, khớp main_table.csv). Các mức 5%/10% không có "điểm chuẩn" cũ để so — đây là số liệu MỚI lần đầu tính, không phải đối chiếu lại.
- `recall_precision_f1_at_fpr_thresholds_2026-09-23.csv` — chi tiết per-fold, không có giá trị pooled cần đối chiếu.
- `m1_improvement_attempts_2026-09-22.md` — đã kiểm tra ở trên (tạo hôm nay 2026-09-23 nhưng đặt tên theo ngày dữ liệu gốc 2026-09-22, đúng theo yêu cầu Việc 2).

## Kết luận

**SẠCH.** Không phát hiện bất kỳ chỗ nào trong repo (toàn bộ, không chỉ 2 ngày gần đây) còn sót số 0,7364.
Mọi chỗ nhắc "M1" trong các file kết quả tạo/sửa trong 2 ngày làm việc gần đây (2026-09-22, 2026-09-23) đều
dùng đúng 0,6624 khi nói về "M1 gốc", và dùng đúng số liệu riêng của từng biến thể khi không phải M1 gốc.
Không cần sửa gì thêm.
