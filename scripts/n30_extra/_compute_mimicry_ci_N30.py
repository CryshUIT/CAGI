"""EXPLORATORY / post-hoc - CHI DOC lai ket qua da luu (extra_N30_t17_mimicry_per_incident.csv,
extra_N30_t17_mimicry_proportional_per_incident.csv) - KHONG chay lai mimicry.
Tinh CI bootstrap cap incident (2000 lan, seed 42) cho PR-AUC CUC BO tung
incident (pr_auc_this_incident_vs_own_hn) O TUNG MUC (KHONG phai diff so
voi muc 0 - khac voi extra_N30_mimicry_paired_ci.csv da tinh truoc).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "results" / "tables" / "extra_N30_mimicry_ci.csv"


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(values)
    boot = np.array([rng.choice(values, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(values.mean()), float(lo), float(hi)


def main():
    rows = []

    df_full = pd.read_csv(ROOT / "results" / "tables" / "extra_N30_t17_mimicry_per_incident.csv")
    for level in sorted(df_full["level"].unique()):
        vals = df_full[df_full.level == level]["pr_auc_this_incident_vs_own_hn"].to_numpy()
        mean_v, lo, hi = bootstrap_mean_ci(vals)
        rows.append({"kich_ban": "co_dinh", "muc_chen": level, "mean_pr_auc_cuc_bo": mean_v,
                     "ci_low_95": lo, "ci_high_95": hi, "n_incidents": len(vals)})
        print(f"[co_dinh] level={level}: mean_local_pr_auc={mean_v:.4f} 95% CI=[{lo:.4f}, {hi:.4f}] n={len(vals)}", flush=True)

    df_prop = pd.read_csv(ROOT / "results" / "tables" / "extra_N30_t17_mimicry_proportional_per_incident.csv")
    for pct in sorted(df_prop["pct_nominal"].unique()):
        vals = df_prop[df_prop.pct_nominal == pct]["pr_auc_this_incident_vs_own_hn"].to_numpy()
        mean_v, lo, hi = bootstrap_mean_ci(vals)
        rows.append({"kich_ban": "ty_le", "muc_chen": pct, "mean_pr_auc_cuc_bo": mean_v,
                     "ci_low_95": lo, "ci_high_95": hi, "n_incidents": len(vals)})
        print(f"[ty_le] pct={pct}: mean_local_pr_auc={mean_v:.4f} 95% CI=[{lo:.4f}, {hi:.4f}] n={len(vals)}", flush=True)

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}")
    print("\nLUU Y: day la PR-AUC CUC BO tung incident (vs hard-negative CUA RIENG incident do), "
          "KHONG PHAI PR-AUC pooled (CI pooled rieng tung muc da co trong "
          "extra_N30_t17_mimicry_stress_test.csv / extra_N30_t17_mimicry_proportional.csv).")


if __name__ == "__main__":
    main()
