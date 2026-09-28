"""NSS 2026 (2026-09-26) - Huong 2: danh gia M1_v2 (them 2 feature moi tu
scripts/build_mid_trajectory_features.py: burstiness_recent_shift,
recent_half_new_counterparty_share) dung DUNG protocol LOIO + nested
threshold selection nhu M1 chinh thuc (evaluate_model_nested, khong
calibration, target_fpr=0.01 - GIONG HET methodology cho 0,6624).

Kiem tra rieng qua giao dich phan tich (khong doan mo, xem docstring
scripts/build_mid_trajectory_features.py): recent_half_new_counterparty_share
o ratio_50 co trung binh 0,374 (label=1, n=15) vs 0,185 (label=0, n=226) -
khac biet ro; burstiness_recent_shift GAN NHU KHONG khac biet (-0,048 vs
-0,074) - dua ca 2 vao model (XGBoost tu chon), khong loai truoc dua tren
gia dinh.

So sanh: M1_v2 (co 2 feature moi) vs M1 chinh thuc (0,6624) - pooled PR-AUC
toan bo VA rieng tai checkpoint ratio_50 (loc tu OOF cua CHINH lan chay nay,
khong chay lai RQ2 dedicated-model). Bootstrap incident-level 2000 lan,
seed=42, dung format E4-E7.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import (  # noqa: E402
    bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OUT_CSV = ROOT / "results" / "tables" / "m1_v2_mid_trajectory_features_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v2_mid_trajectory_features_2026-09-26.md"


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    new_feats = pd.read_parquet(ROOT / "data" / "processed" / "mid_trajectory_features_2026-09-26.parquet")
    df = df.merge(new_feats, on=["source_id", "prefix_len"], how="left")
    assert df["burstiness_recent_shift"].notna().all() and df["recent_half_new_counterparty_share"].notna().all()

    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    print("=== M1_v2 (co burstiness_recent_shift + recent_half_new_counterparty_share) ===", flush=True)
    res = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
    oof_prob = res["oof_prob"]
    valid = oof_prob.notna()

    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"M1_v2 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")

    per_inc_v2 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v2) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v2[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v2 - M1 chinh thuc) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v2) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v2[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v2 - B3) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    # Rieng tai checkpoint ratio_50 - so sanh CUNG rows (source_id, prefix_len) giua M1_v2 va M1 chinh thuc
    r50_mask = (df["prefix_label"] == "ratio_50") & valid
    y50 = y[r50_mask].to_numpy()
    g50 = groups[r50_mask].to_numpy()
    v2_50 = oof_prob[r50_mask].to_numpy()
    m1_50 = merged_check.loc[r50_mask.to_numpy(), "oof_prob_M1"].to_numpy()
    pr_auc_v2_50 = pr_auc(y50, v2_50)
    pr_auc_m1_50 = pr_auc(y50, m1_50)
    print(f"\nPR-AUC rieng tai ratio_50: M1_v2={pr_auc_v2_50:.4f}, M1 chinh thuc={pr_auc_m1_50:.4f}")

    n_pos_50 = int((y50 == 1).sum())
    print(f"(n={len(y50)} dong, n_positive={n_pos_50} tai ratio_50)")

    print(f"\n=== Feature co duoc XGBoost giu khong? (kiem tra 1 fold vi du) ===")
    from sklearn.model_selection import LeaveOneGroupOut
    outer = LeaveOneGroupOut()
    train_idx, _ = next(iter(outer.split(X, y, groups=groups)))
    m = M1TypedTemporalMotifModel()
    m.fit(X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx])
    for feat in ["burstiness_recent_shift", "recent_half_new_counterparty_share"]:
        print(f"  {feat}: {'GIU' if feat in m.feature_cols_ else 'BI LOAI (coverage)'}")

    verdict = (
        "CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc - CAN kiem tra lai qua 5 seed truoc khi tin day la that."
        if lo_m1 > 0 else
        "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc."
    )
    print(f"\n=== KET LUAN ===\n{verdict}")

    pd.DataFrame([{
        "model": "M1_v2_mid_trajectory_features", "mean_pr_auc": ci["point"],
        "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
        "pr_auc_ratio50_m1_v2": pr_auc_v2_50, "pr_auc_ratio50_m1_official": pr_auc_m1_50,
        "n_rows_ratio50": len(y50), "n_positive_ratio50": n_pos_50,
    }]).to_csv(OUT_CSV, index=False)

    md = [
        "# M1_v2 - 2 feature moi cho mid-trajectory dip (Huong 2, 2026-09-26)\n",
        "\nFeature moi: `burstiness_recent_shift` (chenh lech burstiness nua sau vs nua dau prefix), "
        "`recent_half_new_counterparty_share` (ty le counterparty MOI xuat hien trong nua sau) - "
        "xem `scripts/build_mid_trajectory_features.py` cho dong luc du lieu that va cong thuc chi tiet.\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v2 (+2 feature moi)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v2 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v2 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        f"\n## Rieng tai checkpoint ratio_50 ({len(y50)} dong, {n_pos_50} positive)\n",
        f"\nPR-AUC(ratio_50): M1_v2={pr_auc_v2_50:.4f} vs M1 chinh thuc={pr_auc_m1_50:.4f}\n",
        f"\n## KET LUAN\n\n{verdict}\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
