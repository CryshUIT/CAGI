"""Checkpoint D: chay RQ1/RQ2 tren N=20, dung DUNG giao thuc N=15
(results/reports/analysis_plan_N20_v2.md) - khong tuning, khong doi tham so.

KHONG ghi de main_table.csv/oof_predictions_v1.csv/rq1_answer.md/
baseline_results_v2.csv goc hay bat ky file freeze nao. Xuat rieng:
- results/tables/checkpointD_N20_main_table.csv
- results/tables/checkpointD_N19_nocork_main_table.csv
- results/reports/checkpointD_N20_results_2026-10-14.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

from src.evaluation.metrics import pr_auc, false_alerts_per_1000
from src.evaluation.nested_eval import (
    bootstrap_incident_level,
    dedupe_pooled_prefixes,
    evaluate_model_nested,
    per_incident_metric,
)
from src.models.baselines import (
    B0MajorityBaseline, B1RuleBasedTypologyScore, B2BagOfActionsLogisticRegression,
    B3FlatGraphRandomForest, M1TypedTemporalMotifModel,
)

FEATURES_PATH = Path("data/processed/features_v2_N20.parquet")
REGISTRY_PATH = Path("metadata/incident_registry_N20.csv")
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
MODEL_FACTORIES = {
    "B0": B0MajorityBaseline, "B1": B1RuleBasedTypologyScore,
    "B2": B2BagOfActionsLogisticRegression, "B3": B3FlatGraphRandomForest,
    "M1": M1TypedTemporalMotifModel,
}


def run_full_eval(df: pd.DataFrame, label: str, out_csv: Path):
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    print(f"\n=== {label}: {len(df)} dong, {groups.nunique()} group ===", flush=True)

    rows = []
    oof_by_model = {}
    for name, factory in MODEL_FACTORIES.items():
        print(f"  --- {name} ---", flush=True)
        result = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
        oof = result["oof_prob"]
        oof_by_model[name] = oof
        y_arr, prob_arr, g_arr = y.to_numpy(), oof.to_numpy(), groups.to_numpy()

        boot = bootstrap_incident_level(y_arr, prob_arr, g_arr, pr_auc, n_boot=2000, random_state=42)
        rows.append({"model": name, "metric": "pr_auc", "mean_point_estimate": boot["point"],
                     "ci_low_95": boot["ci_low"], "ci_high_95": boot["ci_high"],
                     "n_incidents": groups.nunique(), "n_boot_valid": boot["n_boot_valid"]})

        per_inc = per_incident_metric(y_arr, prob_arr, g_arr, pr_auc)
        for inc, v in per_inc.items():
            rows.append({"model": name, "metric": f"pr_auc_incident_{inc}", "mean_point_estimate": v,
                         "ci_low_95": None, "ci_high_95": None, "n_incidents": None, "n_boot_valid": None})

        fold_df = pd.DataFrame(result["fold_rows"])
        mean_fa = fold_df["false_alerts_per_1000"].mean()
        rows.append({"model": name, "metric": "false_alerts_per_1000_mean_fold",
                     "mean_point_estimate": mean_fa, "ci_low_95": None, "ci_high_95": None,
                     "n_incidents": None, "n_boot_valid": None})

    out_df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    print(f"Da luu {out_csv}", flush=True)
    return out_df, oof_by_model


def paired_bootstrap(a: np.ndarray, b: np.ndarray, seed: int = 42, n_boot: int = 2000):
    diffs = a - b
    n = len(diffs)
    rng = np.random.default_rng(seed)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    w_stat, w_p = wilcoxon(a, b)
    return diffs.mean(), lo, hi, w_stat, w_p


def analyze(main_df: pd.DataFrame, label: str, reg: pd.DataFrame):
    m1 = {k[len("pr_auc_incident_"):]: v for k, v in zip(
        main_df[(main_df.model == "M1") & main_df.metric.str.startswith("pr_auc_incident_")].metric,
        main_df[(main_df.model == "M1") & main_df.metric.str.startswith("pr_auc_incident_")].mean_point_estimate)}
    b3 = {k[len("pr_auc_incident_"):]: v for k, v in zip(
        main_df[(main_df.model == "B3") & main_df.metric.str.startswith("pr_auc_incident_")].metric,
        main_df[(main_df.model == "B3") & main_df.metric.str.startswith("pr_auc_incident_")].mean_point_estimate)}
    incs = sorted(set(m1) & set(b3))
    a = np.array([m1[i] for i in incs])
    b = np.array([b3[i] for i in incs])
    diff_mean, lo, hi, w_stat, w_p = paired_bootstrap(a, b)
    print(f"\n[{label}] M1 vs B3 paired: mean_diff={diff_mean:+.4f} CI=[{lo:+.4f},{hi:+.4f}] "
          f"Wilcoxon stat={w_stat:.1f} p={w_p:.4f}")

    len_map = dict(zip(reg.incident_id, reg.trajectory_len)) if "trajectory_len" in reg.columns else {}
    # fallback: tinh tu features neu khong co trajectory_len trong registry
    gap = {i: m1[i] - b3[i] for i in incs}
    return {"incs": incs, "m1": m1, "b3": b3, "gap": gap, "diff_mean": diff_mean,
            "ci_low": lo, "ci_high": hi, "w_stat": w_stat, "w_p": w_p}


def main():
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    reg = pd.read_csv(REGISTRY_PATH)

    # === N=20 (chinh) ===
    main20, oof20 = run_full_eval(df, "N=20 (chinh)", Path("results/tables/checkpointD_N20_main_table.csv"))
    res20 = analyze(main20, "N=20", reg)

    # === N=19 (sensitivity, bo Cork) ===
    df19 = df[df.group_id != "cork_protocol_2025"].reset_index(drop=True)
    main19, oof19 = run_full_eval(df19, "N=19 (bo Cork)", Path("results/tables/checkpointD_N19_nocork_main_table.csv"))
    res19 = analyze(main19, "N=19", reg)

    # === Trajectory length + subgroup + Spearman (N=20) ===
    traj_len = df_raw[(df_raw.prefix_label == "ratio_100") & (df_raw.label == 1)][["group_id", "trajectory_len"]]
    traj_len = dict(zip(traj_len.group_id, traj_len.trajectory_len))
    incs20 = res20["incs"]
    lens = np.array([traj_len[i] for i in incs20])
    gaps = np.array([res20["gap"][i] for i in incs20])

    # outlier: new_free_dao_2022 theo tieu chi da dung o N=15 (gap lon nhat, do dai ngan)
    outlier_id = "new_free_dao_2022"
    mask_no_outlier = np.array([i != outlier_id for i in incs20])
    rho, rho_p = spearmanr(gaps[mask_no_outlier], lens[mask_no_outlier])
    print(f"\nSpearman(gap, traj_len), loai {outlier_id}, N={mask_no_outlier.sum()}: rho={rho:.4f} p={rho_p:.6f}")

    long_mask = lens > 40
    short_mask = ~long_mask
    def boot_mean_ci(vals, seed=42, n_boot=2000):
        n = len(vals)
        rng = np.random.default_rng(seed)
        boot = np.array([vals[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
        return vals.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5)
    long_mean, long_lo, long_hi = boot_mean_ci(gaps[long_mask])
    short_mean, short_lo, short_hi = boot_mean_ci(gaps[short_mask])
    print(f"LONG (>40, n={long_mask.sum()}): mean_diff={long_mean:+.4f} CI=[{long_lo:+.4f},{long_hi:+.4f}]")
    print(f"SHORT (<=40, n={short_mask.sum()}): mean_diff={short_mean:+.4f} CI=[{short_lo:+.4f},{short_hi:+.4f}]")

    # === Ghi report ===
    lines = ["# Checkpoint D - Ket qua RQ1/RQ2 tren N=20 (2026-10-14)\n\n"]
    lines.append("## N=20 (phan tich CHINH)\n\n")
    lines.append(f"M1 vs B3 paired: mean_diff={res20['diff_mean']:+.4f}, "
                  f"95% CI=[{res20['ci_low']:+.4f},{res20['ci_high']:+.4f}], "
                  f"Wilcoxon stat={res20['w_stat']:.1f}, p={res20['w_p']:.4f}\n\n")
    pooled20 = main20[(main20.model.isin(MODEL_FACTORIES)) & (main20.metric == "pr_auc")]
    lines.append("### PR-AUC pooled theo model (N=20)\n\n")
    lines.append(pooled20[["model", "mean_point_estimate", "ci_low_95", "ci_high_95"]].to_markdown(index=False) + "\n\n")

    lines.append("### Per-incident PR-AUC (M1 vs B3, N=20)\n\n")
    lines.append("| Incident | do_dai | M1 | B3 | gap |\n|---|---|---|---|---|\n")
    for i in incs20:
        lines.append(f"| {i} | {traj_len.get(i,'?')} | {res20['m1'][i]:.4f} | {res20['b3'][i]:.4f} | {res20['gap'][i]:+.4f} |\n")

    lines.append(f"\n### Spearman(gap, do dai trajectory), loai {outlier_id}, N={mask_no_outlier.sum()}\n\n")
    lines.append(f"rho={rho:.4f}, p={rho_p:.6f}\n\n")
    lines.append(f"### Subgroup do dai (nguong <=40/>40)\n\n")
    lines.append(f"- LONG (>40, n={long_mask.sum()}): mean_diff={long_mean:+.4f}, CI=[{long_lo:+.4f},{long_hi:+.4f}]\n")
    lines.append(f"- SHORT (<=40, n={short_mask.sum()}): mean_diff={short_mean:+.4f}, CI=[{short_lo:+.4f},{short_hi:+.4f}]\n\n")

    lines.append("## N=19 (sensitivity, bo Cork)\n\n")
    lines.append(f"M1 vs B3 paired: mean_diff={res19['diff_mean']:+.4f}, "
                  f"95% CI=[{res19['ci_low']:+.4f},{res19['ci_high']:+.4f}], "
                  f"Wilcoxon stat={res19['w_stat']:.1f}, p={res19['w_p']:.4f}\n\n")
    pooled19 = main19[(main19.model.isin(MODEL_FACTORIES)) & (main19.metric == "pr_auc")]
    lines.append("### PR-AUC pooled theo model (N=19)\n\n")
    lines.append(pooled19[["model", "mean_point_estimate", "ci_low_95", "ci_high_95"]].to_markdown(index=False) + "\n\n")

    lines.append("## Trich dan N=15 leak-fixed (khong chay lai)\n\n")
    lines.append("M1=0.5924, B3=0.6366, paired diff=-0.0462, 95% CI=[-0.1434,+0.0497], p=0.3028\n")

    Path("results/reports/checkpointD_N20_results_2026-10-14.md").write_text("".join(lines), encoding="utf-8")
    print("\nDa luu results/reports/checkpointD_N20_results_2026-10-14.md")


if __name__ == "__main__":
    main()
