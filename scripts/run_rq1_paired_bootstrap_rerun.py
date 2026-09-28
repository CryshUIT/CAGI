"""Viec 0 (NSS 2026, T1-T2): chay lai paired bootstrap M1 vs B3 (muc incident).

Logic GIONG HET buoc so sanh paired trong scripts/run_full_evaluation_v1.py
(rng seed 42, 2000 lan resample incident co hoan lai, Wilcoxon signed-rank),
nhung doc PR-AUC per-incident tu results/tables/main_table.csv da freeze
(khong retrain, khong ghi de main_table.csv / rq1_answer.md).

Xuat: results/tables/rq1_paired_bootstrap_rerun_2026-09-22.csv
      results/reports/rq1_paired_bootstrap_rerun_2026-09-22.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_TABLE = REPO_ROOT / "results" / "tables" / "main_table.csv"
OUT_CSV = REPO_ROOT / "results" / "tables" / "rq1_paired_bootstrap_rerun_2026-09-22.csv"
OUT_MD = REPO_ROOT / "results" / "reports" / "rq1_paired_bootstrap_rerun_2026-09-22.md"
PREFIX = "pr_auc_incident_"


def per_incident(df: pd.DataFrame, model: str) -> dict:
    sub = df[(df["model"] == model) & df["metric"].str.startswith(PREFIX)]
    return {m[len(PREFIX):]: v for m, v in zip(sub["metric"], sub["mean_point_estimate"])}


def main() -> None:
    df = pd.read_csv(MAIN_TABLE)
    m1, b3 = per_incident(df, "M1"), per_incident(df, "B3")
    incs = sorted(set(m1) & set(b3))
    a = np.array([m1[i] for i in incs])
    b = np.array([b3[i] for i in incs])
    diffs = a - b
    n = len(diffs)

    rng = np.random.default_rng(42)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(2000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    w_stat, w_p = wilcoxon(a, b)

    m1_mean = float(df[(df.model == "M1") & (df.metric == "pr_auc")]["mean_point_estimate"].iloc[0])
    b3_mean = float(df[(df.model == "B3") & (df.metric == "pr_auc")]["mean_point_estimate"].iloc[0])
    ci_has_zero = lo <= 0 <= hi

    row = {
        "n_incidents": n, "m1_mean_pr_auc": m1_mean, "b3_mean_pr_auc": b3_mean,
        "mean_diff_m1_minus_b3": float(diffs.mean()), "ci_low_95": float(lo), "ci_high_95": float(hi),
        "wilcoxon_stat": float(w_stat), "wilcoxon_p": float(w_p), "ci_contains_zero": bool(ci_has_zero),
        "n_incidents_m1_gt_b3": int((diffs > 1e-12).sum()), "n_incidents_m1_lt_b3": int((diffs < -1e-12).sum()),
        "n_incidents_tie": int((np.abs(diffs) <= 1e-12).sum()),
    }
    pd.DataFrame([row]).to_csv(OUT_CSV, index=False)

    lines = [
        "# RQ1 paired bootstrap (M1 vs B3) - chay lai 2026-09-22\n",
        f"\n- Nguon: `results/tables/main_table.csv` (M1={m1_mean:.4f}, B3={b3_mean:.4f}, {n} incident).\n",
        "- Phuong phap: giong run_full_evaluation_v1.py - bootstrap muc incident (2000 lan, seed 42) tren hieu so paired + Wilcoxon signed-rank.\n",
        f"\n**Mean diff (M1 - B3) = {diffs.mean():+.4f}, 95% CI = [{lo:+.4f}, {hi:+.4f}], Wilcoxon stat={w_stat:.1f}, p={w_p:.4f}**\n",
        f"\nCI chua 0: {'CO' if ci_has_zero else 'KHONG'}. M1>B3 o {row['n_incidents_m1_gt_b3']} incident, "
        f"M1<B3 o {row['n_incidents_m1_lt_b3']}, hoa {row['n_incidents_tie']}.\n",
        "\n| Incident | M1 | B3 | Diff |\n|---|---|---|---|\n",
    ]
    lines += [f"| {i} | {x:.4f} | {y:.4f} | {d:+.4f} |\n" for i, x, y, d in zip(incs, a, b, diffs)]
    OUT_MD.write_text("".join(lines), encoding="utf-8")
    print(row)


if __name__ == "__main__":
    main()
