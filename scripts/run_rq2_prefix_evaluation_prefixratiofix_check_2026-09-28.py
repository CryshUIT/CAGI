"""Tinh lai Table 3(b) (RQ2, M1 PR-AUC theo tung prefix bucket) sau khi sua
leak prefix_ratio o M1 (xem results/reports/prefix_ratio_leak_2026-09-28.md).

KHONG ghi de results/tables/rq2_prefix_evaluation_folds.csv hay
data/processed/rq2_oof_predictions.csv (file dong cung, duoc dung boi
alert_case_studies + lead-time). Chi tinh lai va so sanh, xuat rieng ten khac.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.nested_eval import evaluate_model_nested
from src.models.baselines import M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OLD_FOLD_CSV = REPO_ROOT / "results" / "tables" / "rq2_prefix_evaluation_folds.csv"
OUT_FOLD_CSV = REPO_ROOT / "results" / "tables" / "rq2_prefix_evaluation_folds_prefixratiofix_check_2026-09-28.csv"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
PREFIX_BUCKETS = ["ratio_25", "ratio_50", "ratio_75", "ratio_100", "k_2", "k_3", "k_5", "k_7"]
TARGET_FPR = 0.01


def main():
    df = pd.read_parquet(FEATURES_PATH)
    feature_cols = [c for c in df.columns if c not in META_COLS]

    all_fold_rows = []
    for bucket in PREFIX_BUCKETS:
        sub = df[df["prefix_label"] == bucket].reset_index(drop=True)
        n_groups_with_pos = sub[sub["label"] == 1]["group_id"].nunique()
        if n_groups_with_pos < 2:
            print(f"BO QUA {bucket}: <2 group co positive")
            continue
        X, y, groups = sub[feature_cols], sub["label"], sub["group_id"]
        result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=TARGET_FPR)
        for r in result["fold_rows"]:
            r2 = dict(r)
            r2["prefix_bucket"] = bucket
            all_fold_rows.append(r2)
        print(f"{bucket}: done", flush=True)

    fold_df = pd.DataFrame(all_fold_rows)
    fold_df.to_csv(OUT_FOLD_CSV, index=False)

    new_summary = fold_df.groupby("prefix_bucket")["pr_auc"].mean().reindex(PREFIX_BUCKETS)
    old_df = pd.read_csv(OLD_FOLD_CSV)
    old_summary = old_df.groupby("prefix_bucket")["pr_auc"].mean().reindex(PREFIX_BUCKETS)

    cmp_df = pd.DataFrame({"old_pr_auc": old_summary, "new_pr_auc": new_summary})
    cmp_df["delta"] = cmp_df["new_pr_auc"] - cmp_df["old_pr_auc"]
    print("\n=== Table 3(b) - CU vs MOI (M1, sau khi bo prefix_ratio) ===")
    print(cmp_df.to_string())


if __name__ == "__main__":
    main()
