"""NSS 2026 - kiem tra bat buoc (giong T12) truoc khi tin Ensemble 1a la cai
thien that: chay lai voi 5 random_state khac nhau cho CA M1 va T13 (+
Platt calibrator ben trong evaluate_model_nested cung dung random_state
ngam dinh cua LogisticRegression - kiem tra luon)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel, T13LogisticRegressionM1Features  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
SEEDS = [42, 1, 7, 123, 2026]
OUT_CSV = ROOT / "results" / "tables" / "ensemble_1a_seed_check_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "ensemble_1a_seed_check_2026-09-22.md"


def main():
    df = dedupe_pooled_prefixes(pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet"))
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    rows = []
    for seed in SEEDS:
        m1_factory = lambda s=seed: M1TypedTemporalMotifModel(random_state=s)
        t13_factory = lambda s=seed: T13LogisticRegressionM1Features(random_state=s)
        res_m1 = evaluate_model_nested(m1_factory, X, y, groups, target_fpr=0.01, calibration="platt")
        res_t13 = evaluate_model_nested(t13_factory, X, y, groups, target_fpr=0.01, calibration="platt")
        cal_m1, cal_t13 = res_m1["oof_prob_calibrated"], res_t13["oof_prob_calibrated"]
        valid = cal_m1.notna() & cal_t13.notna()
        ens = (cal_m1[valid] + cal_t13[valid]) / 2
        ci = bootstrap_incident_level(y[valid].to_numpy(), ens.to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=500)
        print(f"seed={seed}: ensemble pooled PR-AUC = {ci['point']:.4f}", flush=True)
        rows.append({"seed": seed, "ensemble_pr_auc": ci["point"]})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    summary = out["ensemble_pr_auc"].agg(["mean", "std", "min", "max"])
    print("\n=== Tom tat qua 5 seed ===")
    print(summary.to_string())

    md = ["# Ensemble 1a - kiem tra do nhay seed (5 seed, giong T12) - 2026-09-22\n",
          f"\nSeed dung: {SEEDS}\n", "\n| Seed | Ensemble PR-AUC |\n|---|---|\n"]
    for _, r in out.iterrows():
        md.append(f"| {int(r['seed'])} | {r['ensemble_pr_auc']:.4f} |\n")
    flag = " *** std >= 0.02 - KHONG on dinh ***" if summary["std"] >= 0.02 else ""
    md.append(f"\n**Mean={summary['mean']:.4f}, Std={summary['std']:.4f}, Min={summary['min']:.4f}, Max={summary['max']:.4f}**{flag}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
