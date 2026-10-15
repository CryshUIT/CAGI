"""Viec kiem tra rieng le (2026-09-28, mo rong): tinh lai CA M1 va B3 PR-AUC
sau khi sua bug prefix_ratio o CA HAI model (xem
results/reports/prefix_ratio_leak_2026-09-28.md cho ban sua M1-only truoc do;
day la ban mo rong sang ca B3 theo yeu cau tiep theo).

KHONG ghi de bat ky file dong cung nao (main_table.csv, oof_predictions_v1.csv,
rq1_answer.md, baseline_results_v2.csv). B0/B1/B2 KHONG duoc tinh lai - lay
nguyen so cu tu main_table.csv (xac nhan khong dung prefix_ratio).

Xuat rieng:
- results/tables/m1_b3_prefixratio_fix_check_2026-09-28.csv
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
from src.models.baselines import M1TypedTemporalMotifModel, B3FlatGraphRandomForest

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
MAIN_TABLE = REPO_ROOT / "results" / "tables" / "main_table.csv"
OUT_CSV = REPO_ROOT / "results" / "tables" / "m1_b3_prefixratio_fix_check_2026-09-28.csv"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
PREFIX = "pr_auc_incident_"


def old_per_incident(model: str) -> dict:
    df = pd.read_csv(MAIN_TABLE)
    sub = df[(df["model"] == model) & df["metric"].str.startswith(PREFIX)]
    return {m[len(PREFIX):]: v for m, v in zip(sub["metric"], sub["mean_point_estimate"])}


def old_pooled(model: str) -> float:
    df = pd.read_csv(MAIN_TABLE)
    return float(df.query("model==@model and metric=='pr_auc'")["mean_point_estimate"].iloc[0])


def paired_stats(a: np.ndarray, b: np.ndarray, seed: int = 42, n_boot: int = 2000):
    diffs = a - b
    n = len(diffs)
    rng = np.random.default_rng(seed)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    w_stat, w_p = wilcoxon(a, b)
    return diffs.mean(), lo, hi, w_stat, w_p


def main() -> None:
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X = df[feature_cols]
    y = df["label"]
    groups = df["group_id"]
    assert "prefix_ratio" in X.columns

    print(f"Tong {len(df)} prefix row, {len(feature_cols)} feature, {groups.nunique()} group", flush=True)

    print("=== M1 (FIXED) ===", flush=True)
    res_m1 = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
    print("=== B3 (FIXED: bo prefix_ratio) ===", flush=True)
    res_b3 = evaluate_model_nested(B3FlatGraphRandomForest, X, y, groups, target_fpr=0.01)

    y_arr = y.to_numpy()
    g_arr = groups.to_numpy()

    new_m1_pooled = pr_auc(y_arr, res_m1["oof_prob"].to_numpy())
    new_b3_pooled = pr_auc(y_arr, res_b3["oof_prob"].to_numpy())
    new_m1_inc = per_incident_metric(y_arr, res_m1["oof_prob"].to_numpy(), g_arr, pr_auc)
    new_b3_inc = per_incident_metric(y_arr, res_b3["oof_prob"].to_numpy(), g_arr, pr_auc)

    old_m1_pooled_v = old_pooled("M1")
    old_b3_pooled_v = old_pooled("B3")
    old_m1_inc = old_per_incident("M1")
    old_b3_inc = old_per_incident("B3")

    print(f"\nM1 pooled: cu={old_m1_pooled_v:.4f} moi={new_m1_pooled:.4f} delta={new_m1_pooled-old_m1_pooled_v:+.4f}")
    print(f"B3 pooled: cu={old_b3_pooled_v:.4f} moi={new_b3_pooled:.4f} delta={new_b3_pooled-old_b3_pooled_v:+.4f}")

    incs = sorted(set(new_m1_inc) & set(new_b3_inc))
    a_new = np.array([new_m1_inc[i] for i in incs])
    b_new = np.array([new_b3_inc[i] for i in incs])
    d_new_mean, lo_new, hi_new, w_new, p_new = paired_stats(a_new, b_new)

    incs_old = sorted(set(old_m1_inc) & set(old_b3_inc))
    a_old = np.array([old_m1_inc[i] for i in incs_old])
    b_old = np.array([old_b3_inc[i] for i in incs_old])
    d_old_mean, lo_old, hi_old, w_old, p_old = paired_stats(a_old, b_old)

    print(f"\n[OLD both-leak] M1 vs B3: diff={d_old_mean:+.4f} CI=[{lo_old:+.4f},{hi_old:+.4f}] p={p_old:.4f}")
    print(f"[NEW both-fixed] M1 vs B3: diff={d_new_mean:+.4f} CI=[{lo_new:+.4f},{hi_new:+.4f}] p={p_new:.4f}")

    rows = []
    for inc in incs:
        rows.append({
            "incident": inc,
            "m1_old": old_m1_inc.get(inc, np.nan), "m1_new": new_m1_inc.get(inc, np.nan),
            "b3_old": old_b3_inc.get(inc, np.nan), "b3_new": new_b3_inc.get(inc, np.nan),
        })
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    summary = {
        "m1_pooled_old": old_m1_pooled_v, "m1_pooled_new": new_m1_pooled,
        "b3_pooled_old": old_b3_pooled_v, "b3_pooled_new": new_b3_pooled,
        "old_diff": d_old_mean, "old_ci": [lo_old, hi_old], "old_p": p_old,
        "new_diff": d_new_mean, "new_ci": [lo_new, hi_new], "new_p": p_new,
    }
    print("\nSUMMARY:", summary)


if __name__ == "__main__":
    main()
