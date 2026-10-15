"""Viec kiem tra rieng le (2026-09-28): tinh lai CHI M1 PR-AUC sau khi sua
bug prefix_ratio_meta -> prefix_ratio trong M1TypedTemporalMotifModel._candidate_columns
(xem src/models/baselines.py, results/reports/prefix_ratio_leak_2026-09-28.md).

KHONG ghi de bat ky file dong cung nao (main_table.csv, oof_predictions_v1.csv,
rq1_answer.md, baseline_results_v2.csv). B0/B1/B2/B3 KHONG duoc tinh lai - lay
nguyen so cu tu main_table.csv/oof_predictions_v1.csv.

Xuat rieng:
- results/tables/m1_prefixratio_fix_check_2026-09-28.csv
- results/reports/prefix_ratio_leak_2026-09-28.md (bao cao day du Buoc 1-3)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.evaluation.metrics import pr_auc
from src.evaluation.nested_eval import (
    dedupe_pooled_prefixes,
    evaluate_model_nested,
    per_incident_metric,
)
from src.models.baselines import M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
MAIN_TABLE = REPO_ROOT / "results" / "tables" / "main_table.csv"
OOF_V1 = REPO_ROOT / "data" / "processed" / "oof_predictions_v1.csv"
OUT_CSV = REPO_ROOT / "results" / "tables" / "m1_prefixratio_fix_check_2026-09-28.csv"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

PREFIX = "pr_auc_incident_"


def old_per_incident(model: str) -> dict:
    df = pd.read_csv(MAIN_TABLE)
    sub = df[(df["model"] == model) & df["metric"].str.startswith(PREFIX)]
    return {m[len(PREFIX):]: v for m, v in zip(sub["metric"], sub["mean_point_estimate"])}


def main() -> None:
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X = df[feature_cols]
    y = df["label"]
    groups = df["group_id"]

    assert "prefix_ratio" in X.columns, "prefix_ratio phai con trong X (chi loai o M1 noi bo, khong xoa khoi extractor)"

    print(f"Tong {len(df)} prefix row, {len(feature_cols)} feature, {groups.nunique()} group", flush=True)
    print("=== M1 (FIXED: loai prefix_ratio) - nested leave-one-incident-out ===", flush=True)
    result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
    oof_prob = result["oof_prob"]

    y_arr = y.to_numpy()
    prob_arr = oof_prob.to_numpy()
    new_pooled_pr_auc = pr_auc(y_arr, prob_arr)

    new_m1_per_incident = per_incident_metric(y_arr, prob_arr, groups.to_numpy(), pr_auc)

    old_m1_per_incident = old_per_incident("M1")
    b3_per_incident = old_per_incident("B3")

    old_m1_pooled = float(pd.read_csv(MAIN_TABLE).query("model=='M1' and metric=='pr_auc'")["mean_point_estimate"].iloc[0])
    b3_pooled = float(pd.read_csv(MAIN_TABLE).query("model=='B3' and metric=='pr_auc'")["mean_point_estimate"].iloc[0])

    print(f"\nOLD M1 pooled PR-AUC (co leak, tu main_table.csv) = {old_m1_pooled:.4f}")
    print(f"NEW M1 pooled PR-AUC (da sua)                     = {new_pooled_pr_auc:.4f}")
    print(f"Delta = {new_pooled_pr_auc - old_m1_pooled:+.4f}")

    incs_new_vs_b3 = sorted(set(new_m1_per_incident) & set(b3_per_incident))
    a_new = np.array([new_m1_per_incident[i] for i in incs_new_vs_b3])
    b = np.array([b3_per_incident[i] for i in incs_new_vs_b3])
    diffs_new = a_new - b
    n = len(diffs_new)
    rng = np.random.default_rng(42)
    boot_new = np.array([diffs_new[rng.integers(0, n, size=n)].mean() for _ in range(2000)])
    lo_new, hi_new = np.percentile(boot_new, [2.5, 97.5])
    w_stat_new, w_p_new = wilcoxon(a_new, b)

    incs_old_vs_b3 = sorted(set(old_m1_per_incident) & set(b3_per_incident))
    a_old = np.array([old_m1_per_incident[i] for i in incs_old_vs_b3])
    b_old = np.array([b3_per_incident[i] for i in incs_old_vs_b3])
    diffs_old = a_old - b_old
    rng2 = np.random.default_rng(42)
    boot_old = np.array([diffs_old[rng2.integers(0, len(diffs_old), size=len(diffs_old))].mean() for _ in range(2000)])
    lo_old, hi_old = np.percentile(boot_old, [2.5, 97.5])
    w_stat_old, w_p_old = wilcoxon(a_old, b_old)

    print(f"\n[OLD] M1(leak) vs B3: mean diff={diffs_old.mean():+.4f}, 95% CI=[{lo_old:+.4f},{hi_old:+.4f}], Wilcoxon p={w_p_old:.4f}")
    print(f"[NEW] M1(fixed) vs B3: mean diff={diffs_new.mean():+.4f}, 95% CI=[{lo_new:+.4f},{hi_new:+.4f}], Wilcoxon p={w_p_new:.4f}")

    out_rows = []
    for inc in incs_new_vs_b3:
        out_rows.append({
            "incident": inc,
            "m1_old_leak": old_m1_per_incident.get(inc, np.nan),
            "m1_new_fixed": new_m1_per_incident.get(inc, np.nan),
            "b3": b3_per_incident.get(inc, np.nan),
            "diff_new_minus_b3": new_m1_per_incident.get(inc, np.nan) - b3_per_incident.get(inc, np.nan),
            "diff_old_minus_b3": old_m1_per_incident.get(inc, np.nan) - b3_per_incident.get(inc, np.nan),
        })
    out_df = pd.DataFrame(out_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)

    summary = {
        "old_m1_pooled_pr_auc": old_m1_pooled,
        "new_m1_pooled_pr_auc": new_pooled_pr_auc,
        "delta_pooled": new_pooled_pr_auc - old_m1_pooled,
        "b3_pooled_pr_auc": b3_pooled,
        "old_mean_diff_m1_minus_b3": float(diffs_old.mean()),
        "old_ci_low": float(lo_old), "old_ci_high": float(hi_old), "old_wilcoxon_p": float(w_p_old),
        "new_mean_diff_m1_minus_b3": float(diffs_new.mean()),
        "new_ci_low": float(lo_new), "new_ci_high": float(hi_new), "new_wilcoxon_p": float(w_p_new),
        "n_incidents": n,
    }
    print("\nSUMMARY:", summary)


if __name__ == "__main__":
    main()
