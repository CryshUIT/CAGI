"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_ablation_t14_combined.py cho N=30.

Thay doi DUY NHAT so voi ban goc:
1. FEATURES_PATH -> features_v2_N30.parquet.
2. M1_full tai su dung results/oof/oof_M1.parquet (join qua source_id/
   prefix_label, da xac nhan khop 1-1 - giong run_ablation_e4_e5_N30.py)
   thay vi oof_predictions_v1.csv (file N15).
3. M1_no_motif (E5) va E4 doc lai tu KET QUA N30 vua chay
   (extra_N30_ablation_per_incident.csv, extra_N30_ablation_table.csv)
   thay vi file N15 goc - BAT BUOC chay run_ablation_e4_e5_N30.py TRUOC
   script nay.
Logic tinh interaction effect / bootstrap / Wilcoxon giu nguyen 100%.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import (  # noqa: E402
    bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
OOF_M1_FULL_PATH = ROOT / "results" / "oof" / "oof_M1.parquet"
E4_E5_TABLE_PATH = ROOT / "results" / "tables" / "extra_N30_ablation_table.csv"
E4_E5_PER_INCIDENT_PATH = ROOT / "results" / "tables" / "extra_N30_ablation_per_incident.csv"
OUT_TABLE = ROOT / "results" / "tables" / "extra_N30_ablation_t14_combined.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_ablation_t14_combined.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

SEMANTIC_ACTION_COLS = [
    "action_count_transfer_ratio", "action_count_lending_deposit_ratio", "action_count_lending_withdraw_ratio",
    "action_count_swap_ratio", "action_count_split_ratio", "action_count_merge_ratio",
    "action_count_mixer_or_exit_ratio", "action_count_other_ratio",
    "num_distinct_bigrams", "num_distinct_trigrams", "stablecoin_pivot",
]
MOTIF_COLS = ["motif_split", "motif_merge", "motif_peel_like_chain", "motif_bridge_then_swap",
              "motif_swap_then_split", "motif_nested_bridge", "motif_rapid_token_pivot"]

NEW_ABLATIONS = {
    "M1_no_semantic_action": SEMANTIC_ACTION_COLS,
    "M1_no_semantic_and_motif": SEMANTIC_ACTION_COLS + MOTIF_COLS,
}


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([rng.choice(diffs, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main() -> None:
    check_m1_gate()
    if not E4_E5_TABLE_PATH.exists() or not E4_E5_PER_INCIDENT_PATH.exists():
        raise RuntimeError(
            f"CAN chay scripts/n30_extra/run_ablation_e4_e5_N30.py TRUOC - thieu "
            f"{E4_E5_TABLE_PATH} hoac {E4_E5_PER_INCIDENT_PATH}."
        )

    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    all_feature_cols = [c for c in df.columns if c not in META_COLS]
    missing = [c for c in SEMANTIC_ACTION_COLS + MOTIF_COLS if c not in all_feature_cols]
    assert not missing, f"Cot khai bao khong ton tai trong data that: {missing}"

    y = df["label"]
    groups = df["group_id"]

    oof_full_df = pd.read_parquet(OOF_M1_FULL_PATH).rename(
        columns={"incident_id": "source_id", "prefix_id": "prefix_label", "score": "oof_prob_M1"}
    )
    key_cols = ["source_id", "prefix_label"]
    merged_check = df[key_cols].merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    assert merged_check["oof_prob_M1"].notna().all() and len(merged_check) == len(df), \
        "M1-full OOF (N30) khong khop 1-1 voi dataset dedupe - PHAI train lai"
    df = df.merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    m1_full_per_inc = per_incident_metric(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    m1_full_ci = bootstrap_incident_level(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)
    print(f"M1_full (tai su dung OOF): mean={m1_full_ci['point']:.4f} [{m1_full_ci['ci_low']:.4f}, {m1_full_ci['ci_high']:.4f}]")

    e5_df = pd.read_csv(E4_E5_PER_INCIDENT_PATH)
    e5_per_inc = dict(zip(e5_df[e5_df.model == "M1_no_motif"].incident_id, e5_df[e5_df.model == "M1_no_motif"].pr_auc))
    assert set(e5_per_inc) == set(m1_full_per_inc), "M1_no_motif (N30) khong khop tap incident voi M1_full o day"
    common0 = sorted(m1_full_per_inc)
    e5_diffs = np.array([e5_per_inc[i] - m1_full_per_inc[i] for i in common0])
    e5_mean, e5_lo, e5_hi = paired_bootstrap(e5_diffs)
    print(f"M1_no_motif (tai su dung E5 N30): paired diff={e5_mean:+.4f} [{e5_lo:+.4f}, {e5_hi:+.4f}]")

    e4_table = pd.read_csv(E4_E5_TABLE_PATH)
    e4_row = e4_table[e4_table.model == "M1_no_temporal"].iloc[0]

    results = {}
    per_incident_rows = [{"model": "M1_full", "incident_id": k, "pr_auc": v} for k, v in m1_full_per_inc.items()]
    for name, drop_cols in NEW_ABLATIONS.items():
        keep_cols = [c for c in all_feature_cols if c not in drop_cols]
        print(f"\n=== {name}: loai {len(drop_cols)} cot, con lai {len(keep_cols)} cot ===", flush=True)
        X = df[keep_cols]
        result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
        oof = result["oof_prob"]
        valid = oof.notna()
        ci = bootstrap_incident_level(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
        per_inc = per_incident_metric(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
        for k, v in per_inc.items():
            per_incident_rows.append({"model": name, "incident_id": k, "pr_auc": v})

        common = sorted(set(per_inc) & set(m1_full_per_inc))
        diffs = np.array([per_inc[i] - m1_full_per_inc[i] for i in common])
        mean_diff, lo, hi = paired_bootstrap(diffs)
        try:
            _, wp = wilcoxon([per_inc[i] for i in common], [m1_full_per_inc[i] for i in common])
        except ValueError:
            wp = float("nan")
        print(f"  Mean PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")
        print(f"  Paired diff vs M1_full = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}], Wilcoxon p={wp}, n={len(common)}")
        results[name] = {"mean_pr_auc": ci["point"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
                          "paired_diff": mean_diff, "paired_lo": lo, "paired_hi": hi, "wilcoxon_p": wp,
                          "n_cols_dropped": len(drop_cols), "n_cols_used": len(keep_cols), "n_incidents_paired": len(common)}

    sem_alone = results["M1_no_semantic_action"]["paired_diff"]
    combined = results["M1_no_semantic_and_motif"]["paired_diff"]
    sum_individual = sem_alone + e5_mean
    interaction = combined - sum_individual

    summary_rows = [
        {"model": "M1_full", "mean_pr_auc": m1_full_ci["point"], "ci_low_95": m1_full_ci["ci_low"], "ci_high_95": m1_full_ci["ci_high"],
         "paired_diff_vs_full": 0.0, "paired_ci_low": 0.0, "paired_ci_high": 0.0, "wilcoxon_p": np.nan,
         "n_cols_dropped": 0, "n_cols_used": len(all_feature_cols), "source": "reused results/oof/oof_M1.parquet"},
        {"model": "M1_no_motif (E5, tai su dung)", "mean_pr_auc": np.nan, "ci_low_95": np.nan, "ci_high_95": np.nan,
         "paired_diff_vs_full": e5_mean, "paired_ci_low": e5_lo, "paired_ci_high": e5_hi, "wilcoxon_p": np.nan,
         "n_cols_dropped": 7, "n_cols_used": np.nan, "source": "reused extra_N30_ablation_per_incident.csv"},
    ]
    for name, r in results.items():
        summary_rows.append({
            "model": name, "mean_pr_auc": r["mean_pr_auc"], "ci_low_95": r["ci_low"], "ci_high_95": r["ci_high"],
            "paired_diff_vs_full": r["paired_diff"], "paired_ci_low": r["paired_lo"], "paired_ci_high": r["paired_hi"],
            "wilcoxon_p": r["wilcoxon_p"], "n_cols_dropped": r["n_cols_dropped"], "n_cols_used": r["n_cols_used"],
            "source": "moi chay trong script nay",
        })
    summary_df = pd.DataFrame(summary_rows)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_TABLE, index=False)
    pd.DataFrame(per_incident_rows).to_csv(ROOT / "results" / "tables" / "extra_N30_ablation_t14_per_incident.csv", index=False)
    print(f"\nDa luu {OUT_TABLE}")

    md = [
        "# [EXPLORATORY/post-hoc, ngoai plan v3] T14 - Ablation gop semantic-action + motif — N=30\n",
        "\n## Lưu ý định nghĩa (giống bản N15)\n",
        "\nE4 (no-temporal) không nằm trong tổ hợp đang ablate (semantic_action+motif) — "
        "dùng nó tính interaction effect sẽ sai logic. Đã chạy thêm `M1_no_semantic_action` "
        "riêng để tính interaction effect đúng nghĩa; đối chiếu với E4 chỉ mang tính tham khảo.\n",
        f"\n- **semantic_action** ({len(SEMANTIC_ACTION_COLS)} cột): `{SEMANTIC_ACTION_COLS}`\n",
        f"- **motif** ({len(MOTIF_COLS)} cột, giống E5): `{MOTIF_COLS}`\n",
        "\n## Bảng tổng hợp (paired diff so với M1_full, mức incident)\n",
        "\n| Model | Mean PR-AUC (pooled) | Paired diff vs M1_full | Paired 95% CI | Wilcoxon p | Cột loại | Nguồn |\n|---|---|---|---|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        mp = f"{r['mean_pr_auc']:.4f}" if pd.notna(r["mean_pr_auc"]) else "-"
        wp = f"{r['wilcoxon_p']:.4f}" if pd.notna(r["wilcoxon_p"]) else "-"
        md.append(f"| {r['model']} | {mp} | {r['paired_diff_vs_full']:+.4f} | "
                   f"[{r['paired_ci_low']:+.4f}, {r['paired_ci_high']:+.4f}] | {wp} | {int(r['n_cols_dropped'])} | {r['source']} |\n")

    md += [
        "\n## Interaction effect\n",
        f"\n- Tác động riêng lẻ semantic_action = {sem_alone:+.4f}\n",
        f"- Tác động riêng lẻ motif (E5) = {e5_mean:+.4f}\n",
        f"- Tổng 2 tác động riêng lẻ = {sum_individual:+.4f}\n",
        f"- Tác động gộp thực tế = {combined:+.4f}\n",
        f"- **Interaction effect = {interaction:+.4f}** "
        f"({'gộp LỚN HƠN tổng riêng lẻ (interaction âm)' if interaction < -1e-6 else ('gộp NHỎ HƠN tổng riêng lẻ (interaction dương)' if interaction > 1e-6 else 'xấp xỉ cộng dồn')})\n",
        "\n## Đối chiếu E4 (no-temporal) — chỉ tham khảo\n",
        f"\n- E4 (N30, đã có) = {e4_row['paired_diff_vs_full']:+.4f} "
        f"[{e4_row['paired_ci_low']:+.4f}, {e4_row['paired_ci_high']:+.4f}], p={e4_row['wilcoxon_p']}\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
