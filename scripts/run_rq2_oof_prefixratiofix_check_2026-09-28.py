"""Ban ISOLATED (khong ghi de rq2_oof_predictions.csv/rq2_prefix_evaluation_folds.csv
chinh thuc) cua run_rq2_prefix_evaluation.py, dung M1 DA SUA leak prefix_ratio,
de kiem tra case study (qbridge_qubit_2022 k_5, ronin_benign_control_2022
ratio_50) thay doi bao nhieu. Xuat rieng ten khac, KHONG dung lam input cho
generate_alert_case_studies.py chinh thuc.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.nested_eval import evaluate_model_nested
from src.models.baselines import M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OUT_OOF_CSV = REPO_ROOT / "data" / "processed" / "rq2_oof_predictions_prefixratiofix_check_2026-09-28.csv"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
PREFIX_BUCKETS = ["ratio_25", "ratio_50", "ratio_75", "ratio_100", "k_2", "k_3", "k_5", "k_7"]
TARGET_FPR = 0.01


def main():
    df = pd.read_parquet(FEATURES_PATH)
    feature_cols = [c for c in df.columns if c not in META_COLS]

    all_oof_rows = []
    for bucket in PREFIX_BUCKETS:
        sub = df[df["prefix_label"] == bucket].reset_index(drop=True)
        n_groups_with_pos = sub[sub["label"] == 1]["group_id"].nunique()
        if n_groups_with_pos < 2:
            continue
        X, y, groups = sub[feature_cols], sub["label"], sub["group_id"]
        result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=TARGET_FPR)
        sub_oof = sub[META_COLS].copy()
        sub_oof["oof_prob"] = result["oof_prob"].to_numpy()
        sub_oof["oof_threshold"] = result["oof_threshold"].to_numpy()
        all_oof_rows.append(sub_oof)
        print(f"{bucket}: done", flush=True)

    oof_df = pd.concat(all_oof_rows, ignore_index=True)
    oof_df.to_csv(OUT_OOF_CSV, index=False)
    print(f"Da luu {OUT_OOF_CSV} ({len(oof_df)} dong)")


if __name__ == "__main__":
    main()
