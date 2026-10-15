"""Chay danh gia MOT LAN cho N=30, dung DUNG giao thuc da khai bao trong
results/reports/analysis_plan_N30_v3.md (SHA-256 da kiem tra truoc khi
chay). KHONG tuning, KHONG doi tham so so voi N=15/N=20
(scripts/run_checkpointD_N20_analysis.py).

Ghi TOAN BO ket qua vao file MOI co hau to _N30, KHONG ghi de bat ky
file freeze/N20/v1.0 nao.
"""
from __future__ import annotations

import json
import sys
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

FEATURES_PATH = Path("data/processed/features_v2_N30.parquet")
REGISTRY_PATH = Path("metadata/incident_registry_N30.csv")
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
MODEL_FACTORIES = {
    "B0": B0MajorityBaseline, "B1": B1RuleBasedTypologyScore,
    "B2": B2BagOfActionsLogisticRegression, "B3": B3FlatGraphRandomForest,
    "M1": M1TypedTemporalMotifModel,
}
RATIO_BUCKETS = ["ratio_25", "ratio_50", "ratio_75", "ratio_100"]
PREFIX_BUCKETS = RATIO_BUCKETS + ["k_2", "k_3", "k_5", "k_7"]
TARGET_FPR = 0.01

SENS_A_EXCLUDE = {"cork_protocol_2025"}
SENS_B_EXCLUDE = {"inverse_finance_2022_jun", "easyfi_2021"}
SENS_C_EXCLUDE = {"hedgey_finance_2024", "prisma_finance_2024", "uranium_finance_2021",
                  "popsicle_finance_2021", "heco_htx_2023", "easyfi_2021"}
SENS_D_INCIDENTS = {"feg_bridge_2024", "new_free_dao_2022", "zunami_protocol_2023",
                     "onyx_protocol_2023", "beanstalk_farms_2022", "dough_finance_2024",
                     "prisma_finance_2024", "inverse_finance_2022_jun", "lendhub_2023"}

OUT_DIR_TABLES = Path("results/tables")
OUT_DIR_REPORTS = Path("results/reports")
LOG_PATH = OUT_DIR_REPORTS / "run_evaluation_N30_v3_log.txt"

_log_lines: list = []


def log(msg: str) -> None:
    print(msg, flush=True)
    _log_lines.append(msg)


def run_full_eval(df: pd.DataFrame, label: str, out_csv: Path):
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    log(f"\n=== {label}: {len(df)} dong, {groups.nunique()} group ===")

    rows = []
    for name, factory in MODEL_FACTORIES.items():
        log(f"  --- {name} ---")
        result = evaluate_model_nested(factory, X, y, groups, target_fpr=TARGET_FPR)
        oof = result["oof_prob"]
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
    log(f"Da luu {out_csv}")
    return out_df


def paired_bootstrap(a: np.ndarray, b: np.ndarray, seed: int = 42, n_boot: int = 2000):
    diffs = a - b
    n = len(diffs)
    rng = np.random.default_rng(seed)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    w_stat, w_p = wilcoxon(a, b)
    return diffs.mean(), lo, hi, w_stat, w_p


def extract_incident_metrics(main_df: pd.DataFrame, model: str) -> dict:
    sub = main_df[(main_df.model == model) & main_df.metric.str.startswith("pr_auc_incident_")]
    return {k[len("pr_auc_incident_"):]: v for k, v in zip(sub.metric, sub.mean_point_estimate)}


def analyze_m1_vs_b3(main_df: pd.DataFrame, label: str):
    m1 = extract_incident_metrics(main_df, "M1")
    b3 = extract_incident_metrics(main_df, "B3")
    incs = sorted(set(m1) & set(b3))
    a = np.array([m1[i] for i in incs])
    b = np.array([b3[i] for i in incs])
    diff_mean, lo, hi, w_stat, w_p = paired_bootstrap(a, b)
    log(f"\n[{label}] M1 vs B3 paired: mean_diff={diff_mean:+.4f} CI=[{lo:+.4f},{hi:+.4f}] "
        f"Wilcoxon stat={w_stat:.1f} p={w_p:.4f}")
    gap = {i: m1[i] - b3[i] for i in incs}
    return {"incs": incs, "m1": m1, "b3": b3, "gap": gap, "diff_mean": diff_mean,
            "ci_low": lo, "ci_high": hi, "w_stat": w_stat, "w_p": w_p}


def jackknife_spearman(x: np.ndarray, y: np.ndarray):
    n = len(x)
    rho_full, p_full = spearmanr(x, y)
    jk_rhos = []
    for i in range(n):
        mask = np.arange(n) != i
        r, _ = spearmanr(x[mask], y[mask])
        jk_rhos.append(r)
    jk_rhos = np.array(jk_rhos)
    jk_mean = jk_rhos.mean()
    jk_se = np.sqrt((n - 1) / n * np.sum((jk_rhos - jk_mean) ** 2))
    return rho_full, p_full, jk_mean, jk_se, jk_rhos


def run_rq2_per_bucket(df_raw: pd.DataFrame, allowed_group_ids: set, label: str, out_csv: Path):
    sub_all = df_raw[df_raw.group_id.isin(allowed_group_ids)].reset_index(drop=True)
    feature_cols = [c for c in sub_all.columns if c not in META_COLS]
    rows = []
    for bucket in PREFIX_BUCKETS:
        sub = sub_all[sub_all["prefix_label"] == bucket].reset_index(drop=True)
        n_pos = int((sub["label"] == 1).sum())
        n_groups_with_pos = sub[sub["label"] == 1]["group_id"].nunique()
        log(f"  [{label}] bucket={bucket} n={len(sub)} positive={n_pos} groups_with_pos={n_groups_with_pos}")
        if n_groups_with_pos < 2:
            log(f"    BO QUA: <2 group co positive.")
            continue
        X, y, groups = sub[feature_cols], sub["label"], sub["group_id"]
        result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=TARGET_FPR)
        fold_df = pd.DataFrame(result["fold_rows"])
        rows.append({
            "subset": label, "prefix_bucket": bucket,
            "mean_pr_auc": fold_df["pr_auc"].mean(),
            "mean_recall_at_fpr1": fold_df[f"recall_at_fpr_{TARGET_FPR}"].mean(),
            "mean_false_alerts_per_1000": fold_df["false_alerts_per_1000"].mean(),
            "n_folds": len(fold_df),
        })
    out_df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    log(f"Da luu {out_csv}")
    return out_df


def table_3b_ratio_checkpoints(df_raw: pd.DataFrame, out_csv: Path):
    """Bang 4 checkpoint (ratio_25/50/75/100) cho M1 va B3, tren TOAN BO N=30."""
    feature_cols = [c for c in df_raw.columns if c not in META_COLS]
    rows = []
    for bucket in RATIO_BUCKETS:
        sub = df_raw[df_raw["prefix_label"] == bucket].reset_index(drop=True)
        X, y, groups = sub[feature_cols], sub["label"], sub["group_id"]
        row = {"prefix_bucket": bucket, "n_rows": len(sub), "n_positive": int((y == 1).sum())}
        for name in ["M1", "B3"]:
            factory = MODEL_FACTORIES[name]
            result = evaluate_model_nested(factory, X, y, groups, target_fpr=TARGET_FPR)
            oof = result["oof_prob"].to_numpy()
            boot = bootstrap_incident_level(y.to_numpy(), oof, groups.to_numpy(), pr_auc, n_boot=2000, random_state=42)
            row[f"{name}_pr_auc"] = boot["point"]
            row[f"{name}_ci_low"] = boot["ci_low"]
            row[f"{name}_ci_high"] = boot["ci_high"]
        row["gap_M1_minus_B3"] = row["M1_pr_auc"] - row["B3_pr_auc"]
        rows.append(row)
        log(f"  [Table3b] {bucket}: M1={row['M1_pr_auc']:.4f} B3={row['B3_pr_auc']:.4f} gap={row['gap_M1_minus_B3']:+.4f}")
    out_df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    log(f"Da luu {out_csv}")
    return out_df


def main():
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    reg = pd.read_csv(REGISTRY_PATH)
    reg_primary = reg[(reg.eval_tier == "primary") & (reg.label == 1)].reset_index(drop=True)
    ordered_ids = reg_primary.incident_id.tolist()
    assert len(ordered_ids) == 30, f"Ky vong 30 incident, thuc te {len(ordered_ids)}"

    traj_len = df_raw[(df_raw.prefix_label == "ratio_100") & (df_raw.label == 1)][["group_id", "trajectory_len"]]
    traj_len = dict(zip(traj_len.group_id, traj_len.trajectory_len))

    # ================= MAIN N=30 =================
    main30 = run_full_eval(df, "N=30 (chinh)", OUT_DIR_TABLES / "evaluation_N30_main_table.csv")
    res30 = analyze_m1_vs_b3(main30, "N=30")

    # ================= 4 moc cong don N=15/20/25/30 =================
    checkpoint_results = {}
    for k in [15, 20, 25, 30]:
        ids_k = set(ordered_ids[:k])
        if k == 30:
            checkpoint_results[30] = res30
            continue
        df_k = df[df.group_id.isin(ids_k)].reset_index(drop=True)
        main_k = run_full_eval(df_k, f"N={k} (moc cong don)", OUT_DIR_TABLES / f"evaluation_N30_checkpoint_N{k}_table.csv")
        checkpoint_results[k] = analyze_m1_vs_b3(main_k, f"N={k}")

    # ================= Sensitivity (a)(b)(c) =================
    sens_results = {}
    for sens_name, exclude_set in [("a_exclude_leq2_actions", SENS_A_EXCLUDE),
                                     ("b_exclude_gt5000_actions", SENS_B_EXCLUDE),
                                     ("c_exclude_allowlist_completion_changed", SENS_C_EXCLUDE)]:
        df_sens = df[~df.group_id.isin(exclude_set)].reset_index(drop=True)
        main_sens = run_full_eval(df_sens, f"sensitivity_{sens_name}",
                                   OUT_DIR_TABLES / f"evaluation_N30_sensitivity_{sens_name}_table.csv")
        sens_results[sens_name] = analyze_m1_vs_b3(main_sens, sens_name)

    # ================= Subgroup <=40/>40 + Spearman + jackknife (N=30 main) =================
    incs30 = res30["incs"]
    lens = np.array([traj_len[i] for i in incs30])
    gaps = np.array([res30["gap"][i] for i in incs30])

    outlier_id = "new_free_dao_2022"
    mask_no_outlier = np.array([i != outlier_id for i in incs30])
    rho, p, jk_mean, jk_se, jk_rhos = jackknife_spearman(gaps[mask_no_outlier], lens[mask_no_outlier])
    log(f"\nSpearman(gap, traj_len), loai {outlier_id}, N={mask_no_outlier.sum()}: "
        f"rho={rho:.4f} p={p:.6f} jackknife_mean={jk_mean:.4f} jackknife_se={jk_se:.4f}")

    long_mask = lens > 40
    short_mask = ~long_mask

    def boot_mean_ci(vals, seed=42, n_boot=2000):
        n = len(vals)
        rng = np.random.default_rng(seed)
        boot = np.array([vals[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
        return vals.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5)

    long_mean, long_lo, long_hi = boot_mean_ci(gaps[long_mask])
    short_mean, short_lo, short_hi = boot_mean_ci(gaps[short_mask])
    log(f"LONG (>40, n={long_mask.sum()}): mean_diff={long_mean:+.4f} CI=[{long_lo:+.4f},{long_hi:+.4f}]")
    log(f"SHORT (<=40, n={short_mask.sum()}): mean_diff={short_mean:+.4f} CI=[{short_lo:+.4f},{short_hi:+.4f}]")

    # ================= Table 3b (ratio checkpoints, N=30) =================
    table3b = table_3b_ratio_checkpoints(df_raw, OUT_DIR_TABLES / "evaluation_N30_table3b_ratio_checkpoints.csv")

    # ================= RQ2: 20 endpoint-confirmed + 9 sensitivity-d =================
    endpoint_confirmed_ids = set(reg_primary[reg_primary.endpoint_confirmed == True].incident_id)
    assert len(endpoint_confirmed_ids) == 20, f"Ky vong 20, thuc te {len(endpoint_confirmed_ids)}"
    assert SENS_D_INCIDENTS.issubset(endpoint_confirmed_ids)

    rq2_20 = run_rq2_per_bucket(df_raw, endpoint_confirmed_ids, "endpoint_confirmed_20",
                                 OUT_DIR_TABLES / "evaluation_N30_RQ2_endpoint_confirmed_20.csv")
    rq2_9 = run_rq2_per_bucket(df_raw, SENS_D_INCIDENTS, "sensitivity_d_9",
                                OUT_DIR_TABLES / "evaluation_N30_RQ2_sensitivity_d_9.csv")

    # ================= Per-incident table (N=30 main) =================
    per_inc_rows = []
    for i in incs30:
        per_inc_rows.append({
            "incident_id": i, "trajectory_len": traj_len.get(i), "M1_pr_auc": res30["m1"][i],
            "B3_pr_auc": res30["b3"][i], "gap_M1_minus_B3": res30["gap"][i],
        })
    per_inc_df = pd.DataFrame(per_inc_rows)
    per_inc_df.to_csv(OUT_DIR_TABLES / "evaluation_N30_per_incident_table.csv", index=False)
    log(f"Da luu {OUT_DIR_TABLES / 'evaluation_N30_per_incident_table.csv'}")

    # ================= Bang mo ta theo chain (dien PR-AUC) =================
    chain_rows = []
    for chain in ["eth", "bsc", "arbitrum"]:
        ids_chain = set(reg_primary[reg_primary.chain_primary == chain].incident_id)
        df_chain = df[df.group_id.isin(ids_chain)].reset_index(drop=True)
        n_inc = len(ids_chain)
        n_pos = int((df_chain.label == 1).sum() > 0) and df_chain[df_chain.label == 1].source_id.nunique()
        n_neg = df_chain[df_chain.label == 0].source_id.nunique()
        row = {"chain": chain, "n_incident": n_inc, "n_positive": n_pos, "n_negative": n_neg}
        for name in ["M1", "B3"]:
            factory = MODEL_FACTORIES[name]
            feature_cols = [c for c in df_chain.columns if c not in META_COLS]
            X, y, groups = df_chain[feature_cols], df_chain["label"], df_chain["group_id"]
            if groups.nunique() < 2:
                row[f"{name}_pr_auc_pooled"] = None
                continue
            result = evaluate_model_nested(factory, X, y, groups, target_fpr=TARGET_FPR)
            oof = result["oof_prob"].to_numpy()
            boot = bootstrap_incident_level(y.to_numpy(), oof, groups.to_numpy(), pr_auc, n_boot=2000, random_state=42)
            row[f"{name}_pr_auc_pooled"] = boot["point"]
        chain_rows.append(row)
        log(f"  [chain] {chain}: {row}")
    chain_df = pd.DataFrame(chain_rows)
    chain_df.to_csv(OUT_DIR_TABLES / "evaluation_N30_by_chain_table.csv", index=False)
    log(f"Da luu {OUT_DIR_TABLES / 'evaluation_N30_by_chain_table.csv'}")

    # ================= Ghi bao cao tong hop =================
    lines = ["# Ket qua danh gia N=30 (chay MOT LAN theo analysis_plan_N30_v3.md) - 2026-10-15\n\n"]
    lines.append("CHUA viet ket luan - CHI bao cao so lieu theo dung gate da dang ky.\n\n")

    lines.append("## N=30 (phan tich CHINH)\n\n")
    lines.append(f"M1 vs B3 paired: mean_diff={res30['diff_mean']:+.4f}, "
                 f"95% CI=[{res30['ci_low']:+.4f},{res30['ci_high']:+.4f}], "
                 f"Wilcoxon stat={res30['w_stat']:.1f}, p={res30['w_p']:.4f}\n\n")
    pooled30 = main30[(main30.model.isin(MODEL_FACTORIES)) & (main30.metric == "pr_auc")]
    lines.append("### PR-AUC pooled theo model (N=30)\n\n")
    lines.append(pooled30[["model", "mean_point_estimate", "ci_low_95", "ci_high_95"]].to_markdown(index=False) + "\n\n")

    lines.append("### Per-incident PR-AUC (M1 vs B3, N=30)\n\n")
    lines.append("| Incident | do_dai | M1 | B3 | gap |\n|---|---|---|---|---|\n")
    for i in incs30:
        lines.append(f"| {i} | {traj_len.get(i,'?')} | {res30['m1'][i]:.4f} | {res30['b3'][i]:.4f} | {res30['gap'][i]:+.4f} |\n")

    lines.append(f"\n### Spearman(gap, do dai trajectory), loai {outlier_id}, N={mask_no_outlier.sum()}\n\n")
    lines.append(f"rho={rho:.4f}, p={p:.6f}, jackknife_mean={jk_mean:.4f}, jackknife_se={jk_se:.4f}\n\n")
    lines.append("### Subgroup do dai (nguong <=40/>40)\n\n")
    lines.append(f"- LONG (>40, n={long_mask.sum()}): mean_diff={long_mean:+.4f}, CI=[{long_lo:+.4f},{long_hi:+.4f}]\n")
    lines.append(f"- SHORT (<=40, n={short_mask.sum()}): mean_diff={short_mean:+.4f}, CI=[{short_lo:+.4f},{short_hi:+.4f}]\n\n")

    lines.append("## 4 moc cong don (N=15/20/25/30, thu tu registry, config_N30)\n\n")
    lines.append("| N | M1 vs B3 mean_diff | 95% CI | Wilcoxon p |\n|---|---|---|---|\n")
    for k in [15, 20, 25, 30]:
        r = checkpoint_results[k]
        lines.append(f"| {k} | {r['diff_mean']:+.4f} | [{r['ci_low']:+.4f},{r['ci_high']:+.4f}] | {r['w_p']:.4f} |\n")
    lines.append("\nTrich N=15 leak-fixed da freeze (khong chay lai o day, chi doi chieu):"
                  " M1=0.5924, B3=0.6366, diff=-0.0462, CI=[-0.1434,+0.0497], p=0.3028\n\n")

    lines.append("## Sensitivity (a)(b)(c)\n\n")
    lines.append("| Sensitivity | n_incident_loai | mean_diff | 95% CI | Wilcoxon p |\n|---|---|---|---|---|\n")
    for sens_name, exclude_set in [("a_exclude_leq2_actions", SENS_A_EXCLUDE),
                                     ("b_exclude_gt5000_actions", SENS_B_EXCLUDE),
                                     ("c_exclude_allowlist_completion_changed", SENS_C_EXCLUDE)]:
        r = sens_results[sens_name]
        lines.append(f"| {sens_name} | {len(exclude_set)} | {r['diff_mean']:+.4f} | "
                      f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}] | {r['w_p']:.4f} |\n")

    lines.append("\n## Table 3b (4 checkpoint ratio_25/50/75/100, N=30 toan bo)\n\n")
    lines.append(table3b.to_markdown(index=False) + "\n\n")

    lines.append("## RQ2: 20 incident endpoint-confirmed\n\n")
    lines.append(rq2_20.to_markdown(index=False) + "\n\n")
    lines.append("## RQ2: 9 incident sensitivity (d)\n\n")
    lines.append(rq2_9.to_markdown(index=False) + "\n\n")

    lines.append("## Bang mo ta theo chain\n\n")
    lines.append(chain_df.to_markdown(index=False) + "\n\n")

    lines.append("## Limitations da biet\n\n")
    lines.append(
        "- Builder mo rong qua hub khong allowlist (xem known_builder_limitations.md).\n"
        "- protocol_map v1.0 dong bang - TornadoProxy khong duoc nhan la mixer boi pipeline.\n"
        "- Cua so mining khac cua so tracking (72h).\n"
        "- Yield cua v2_complexity phu thuoc thu tu xu ly incident.\n"
        "- Horizon 72h loai tru rua tien tre (HECO, Uranium, THORChain-2).\n"
        "- Nhan endpoint khong co nguong gia tri co dinh.\n"
        "- xkingdom va FEG Bridge co phan mixer nam o chain khac (ngoai trajectory tracked).\n"
    )

    OUT_DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    (OUT_DIR_REPORTS / "evaluation_N30_results_2026-10-15.md").write_text("".join(lines), encoding="utf-8")
    log(f"\nDa luu {OUT_DIR_REPORTS / 'evaluation_N30_results_2026-10-15.md'}")

    LOG_PATH.write_text("\n".join(_log_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
