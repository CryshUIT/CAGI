"""NSS 2026 - Viec 1 (T14): ablation gop "bo semantic-action VA motif cung
luc" tren M1, de tra loi cau hoi "typed semantics co giup ich khong".

Dung DUNG pipeline RQ1/E4-E5 (pool 8 prefix bucket, dedupe_pooled_prefixes,
leave-one-incident-out qua evaluate_model_nested, bootstrap CI muc incident,
paired bootstrap tren hieu so per-incident + Wilcoxon) - KHONG doi phuong
phap. M1_full va M1_no_motif TAI SU DUNG ket qua da co (oof_predictions_v1.csv,
ablation_per_incident.csv) sau khi XAC NHAN khop 1-1 voi dataset dedupe o day.

Chay THEM 2 model MOI (khong co san):
  - M1_no_semantic_action : loai RIENG nhom semantic_action (can de tinh
    interaction effect dung nghia - "no-temporal" (E4) KHONG the dung thay
    vi temporal khong nam trong to hop dang ablate o day).
  - M1_no_semantic_and_motif : loai CA HAI nhom cung luc (ablation chinh
    duoc yeu cau).

SEMANTIC_ACTION_COLS chi gom cac cot THAT con lai trong candidate columns
cua M1 sau khi M1 tu loai noi bo (action_count_* THO va BRIDGE_CONTEXT_COLS_
EXCLUDED) - liet ke tu features_v2.parquet, khong suy doan.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.evaluation.metrics import pr_auc
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric
from src.models.baselines import M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OOF_M1_FULL_PATH = REPO_ROOT / "data" / "processed" / "oof_predictions_v1.csv"
ABLATION_PER_INCIDENT_PATH = REPO_ROOT / "results" / "tables" / "ablation_per_incident.csv"
OUT_TABLE = REPO_ROOT / "results" / "tables" / "ablation_t14_combined_2026-09-22.csv"
OUT_MD = REPO_ROOT / "results" / "reports" / "ablation_t14_combined_2026-09-22.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

# Nhom "semantic_action" THAT con lai trong candidate columns cua M1 (18 cot
# action_count_/bridge_context da bi M1 tu loai noi bo truoc do, xem docstring).
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
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    all_feature_cols = [c for c in df.columns if c not in META_COLS]
    missing = [c for c in SEMANTIC_ACTION_COLS + MOTIF_COLS if c not in all_feature_cols]
    assert not missing, f"Cot khai bao khong ton tai trong data that: {missing}"

    y = df["label"]
    groups = df["group_id"]

    # --- M1_full: tai su dung OOF co san, xac nhan khop 1-1 (giong run_ablation_e4_e5.py) ---
    oof_full_df = pd.read_csv(OOF_M1_FULL_PATH)
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    assert merged_check["oof_prob_M1"].notna().all() and len(merged_check) == len(df), \
        "M1-full OOF khong khop 1-1 voi dataset dedupe - PHAI train lai"
    df = df.merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    m1_full_per_inc = per_incident_metric(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    m1_full_ci = bootstrap_incident_level(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)
    print(f"M1_full (tai su dung OOF): mean={m1_full_ci['point']:.4f} [{m1_full_ci['ci_low']:.4f}, {m1_full_ci['ci_high']:.4f}]")

    # --- M1_no_motif (E5): tai su dung tu ablation_per_incident.csv da co ---
    e5_df = pd.read_csv(ABLATION_PER_INCIDENT_PATH)
    e5_per_inc = dict(zip(e5_df[e5_df.model == "M1_no_motif"].incident_id, e5_df[e5_df.model == "M1_no_motif"].pr_auc))
    assert set(e5_per_inc) == set(m1_full_per_inc), "M1_no_motif da co khong khop tap incident voi M1_full o day"
    common0 = sorted(m1_full_per_inc)
    e5_diffs = np.array([e5_per_inc[i] - m1_full_per_inc[i] for i in common0])
    e5_mean, e5_lo, e5_hi = paired_bootstrap(e5_diffs)
    print(f"M1_no_motif (tai su dung E5): paired diff={e5_mean:+.4f} [{e5_lo:+.4f}, {e5_hi:+.4f}]")

    # --- E4 (no-temporal) da co, chi doc lai ket qua tu ablation_table.csv de doi chieu ---
    e4_table = pd.read_csv(REPO_ROOT / "results" / "tables" / "ablation_table.csv")
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
        print(f"  Paired diff vs M1_full = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}], Wilcoxon p={wp:.4f}")
        results[name] = {"mean_pr_auc": ci["point"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
                          "paired_diff": mean_diff, "paired_lo": lo, "paired_hi": hi, "wilcoxon_p": wp,
                          "n_cols_dropped": len(drop_cols), "n_cols_used": len(keep_cols)}

    sem_alone = results["M1_no_semantic_action"]["paired_diff"]
    combined = results["M1_no_semantic_and_motif"]["paired_diff"]
    sum_individual = sem_alone + e5_mean
    interaction = combined - sum_individual

    summary_rows = [
        {"model": "M1_full", "mean_pr_auc": m1_full_ci["point"], "ci_low_95": m1_full_ci["ci_low"], "ci_high_95": m1_full_ci["ci_high"],
         "paired_diff_vs_full": 0.0, "paired_ci_low": 0.0, "paired_ci_high": 0.0, "wilcoxon_p": np.nan,
         "n_cols_dropped": 0, "n_cols_used": len(all_feature_cols), "source": "reused oof_predictions_v1.csv"},
        {"model": "M1_no_motif (E5, tai su dung)", "mean_pr_auc": np.nan, "ci_low_95": np.nan, "ci_high_95": np.nan,
         "paired_diff_vs_full": e5_mean, "paired_ci_low": e5_lo, "paired_ci_high": e5_hi, "wilcoxon_p": np.nan,
         "n_cols_dropped": 7, "n_cols_used": np.nan, "source": "reused ablation_per_incident.csv"},
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
    pd.DataFrame(per_incident_rows).to_csv(REPO_ROOT / "results" / "tables" / "ablation_t14_per_incident_2026-09-22.csv", index=False)
    print(f"\nDa luu {OUT_TABLE}")

    md = [
        "# T14 - Ablation gop semantic-action + motif (chay 2026-09-22)\n",
        "\n## Luu y quan trong ve dinh nghia (can doc truoc khi dung ket qua)\n",
        "\nYeu cau goc de nghi so sanh voi \"E4 (no-temporal)\" de tinh interaction effect, "
        "nhung E4 loai nhom `temporal` (5 cot: time_to_first_bridge, inter_action_gap_mean/std, "
        "burstiness, active_duration_sec) - nhom NAY KHONG nam trong to hop dang ablate o day "
        "(semantic_action + motif). Dung E4 de tinh interaction effect se SAI ve mat logic. "
        "Toi da chay THEM `M1_no_semantic_action` (loai rieng nhom semantic_action) de co "
        "interaction effect dung nghia; van bao cao doi chieu voi E4 rieng theo yeu cau, "
        "nhung ghi ro day KHONG PHAI mot phep decomposition chuan.\n",
        f"\n- **semantic_action** ({len(SEMANTIC_ACTION_COLS)} cot that con lai sau khi M1 tu loai noi bo "
        f"action_count_* tho + bridge_context): `{SEMANTIC_ACTION_COLS}`\n",
        f"- **motif** ({len(MOTIF_COLS)} cot, giong E5): `{MOTIF_COLS}`\n",
        "\n## Bang tong hop (paired diff so voi M1_full, muc incident)\n",
        "\n| Model | Mean PR-AUC (pooled) | Paired diff vs M1_full | Paired 95% CI | Wilcoxon p | Cot loai | Nguon |\n|---|---|---|---|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        mp = f"{r['mean_pr_auc']:.4f}" if pd.notna(r["mean_pr_auc"]) else "-"
        wp = f"{r['wilcoxon_p']:.4f}" if pd.notna(r["wilcoxon_p"]) else "-"
        md.append(f"| {r['model']} | {mp} | {r['paired_diff_vs_full']:+.4f} | "
                   f"[{r['paired_ci_low']:+.4f}, {r['paired_ci_high']:+.4f}] | {wp} | {int(r['n_cols_dropped'])} | {r['source']} |\n")

    md += [
        "\n## Interaction effect (dinh nghia dung: semantic_action-rieng + motif-rieng vs gop)\n",
        f"\n- Tac dong rieng le semantic_action (M1_no_semantic_action - M1_full) = {sem_alone:+.4f}\n",
        f"- Tac dong rieng le motif (E5, M1_no_motif - M1_full) = {e5_mean:+.4f}\n",
        f"- Tong 2 tac dong rieng le = {sum_individual:+.4f}\n",
        f"- Tac dong gop thuc te (M1_no_semantic_and_motif - M1_full) = {combined:+.4f}\n",
        f"- **Interaction effect = gop - tong rieng le = {interaction:+.4f}** "
        f"({'gop LON HON tong 2 tac dong rieng le (co interaction am/tuong tac lam nang them)' if interaction < -1e-6 else ('gop NHO HON tong 2 tac dong rieng le (co interaction duong/bu tru mot phan)' if interaction > 1e-6 else 'xap xi cong dong, khong co interaction ro ret')})\n",
        "\n## Doi chieu voi E4 (no-temporal) theo yeu cau — CHI mang tinh tham khao do khong cung to hop\n",
        f"\n- E4 (M1_no_temporal - M1_full), da co san = {e4_row['paired_diff_vs_full']:+.4f} "
        f"[{e4_row['paired_ci_low']:+.4f}, {e4_row['paired_ci_high']:+.4f}], p={e4_row['wilcoxon_p']:.4f}\n",
        f"- Tac dong gop (semantic_action+motif) = {combined:+.4f} — "
        f"{'lon hon (am hon)' if combined < e4_row['paired_diff_vs_full'] else 'nho hon hoac tuong duong'} tac dong cua rieng no-temporal.\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
