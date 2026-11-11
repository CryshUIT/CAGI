"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_ablation_e4_e5.py cho N=30.

Thay doi DUY NHAT so voi ban goc:
1. FEATURES_PATH -> features_v2_N30.parquet.
2. M1_full KHONG tai su dung oof_predictions_v1.csv (file do danh cho N=15,
   co key (source_id, prefix_len) khac schema) - thay vao do tai su dung
   results/oof/oof_M1.parquet (da co san tu addendum 2, DUNG config/dedupe
   N30, pooled PR-AUC = 0.7762 da qua cong kiem tra), join qua
   (source_id=incident_id, prefix_label=prefix_id) - DA XAC NHAN khop 1-1
   TUYET DOI voi dataset dedupe o day (3074/3074 dong) truoc khi chay script
   nay (khong gia dinh).
Logic tinh ablation/bootstrap/Wilcoxon giu nguyen 100%.
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
OUT_TABLE = ROOT / "results" / "tables" / "extra_N30_ablation_table.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_ablation_e4_e5.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

TEMPORAL_COLS = ["time_to_first_bridge", "inter_action_gap_mean", "inter_action_gap_std",
                  "burstiness", "active_duration_sec"]
MOTIF_COLS = ["motif_split", "motif_merge", "motif_peel_like_chain", "motif_bridge_then_swap",
              "motif_swap_then_split", "motif_nested_bridge", "motif_rapid_token_pivot"]
BRIDGE_CONTEXT_COLS = ["time_to_first_bridge", "action_count_bridge_deposit", "action_count_bridge_deposit_ratio",
                        "action_count_bridge_withdraw", "action_count_bridge_withdraw_ratio",
                        "num_bridge_families", "swap_after_bridge", "motif_bridge_then_swap", "motif_nested_bridge"]

ABLATIONS = {
    "M1_no_temporal": (TEMPORAL_COLS, M1TypedTemporalMotifModel),
    "M1_no_motif": (MOTIF_COLS, M1TypedTemporalMotifModel),
    "M1_with_bridge_context": ([], lambda: M1TypedTemporalMotifModel(include_bridge_context=True)),
}


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([rng.choice(diffs, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main():
    check_m1_gate()
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    print(f"Dedupe pooled prefixes N30: {len(df_raw)} -> {len(df)} dong", flush=True)

    all_feature_cols = [c for c in df.columns if c not in META_COLS]
    y = df["label"]
    groups = df["group_id"]

    oof_full_df = pd.read_parquet(OOF_M1_FULL_PATH).rename(
        columns={"incident_id": "source_id", "prefix_id": "prefix_label", "score": "oof_prob_M1"}
    )
    key_cols = ["source_id", "prefix_label"]
    merged_check = df[key_cols].merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    assert merged_check["oof_prob_M1"].notna().all(), "M1-full OOF (N30) khong khop 1-1 voi df da dedupe - PHAI train lai"
    assert len(merged_check) == len(df)
    df = df.merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    m1_full_oof = df["oof_prob_M1"]
    print(f"Xac nhan: M1-full OOF (results/oof/oof_M1.parquet) khop 1-1 voi N30 dedupe ({len(df)}/{len(df)}).", flush=True)

    m1_full_per_inc = per_incident_metric(y.to_numpy(), m1_full_oof.to_numpy(), groups.to_numpy(), pr_auc)
    m1_full_ci = bootstrap_incident_level(y.to_numpy(), m1_full_oof.to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)

    summary_rows = [{
        "model": "M1_full", "mean_pr_auc": m1_full_ci["point"], "ci_low_95": m1_full_ci["ci_low"],
        "ci_high_95": m1_full_ci["ci_high"], "n_incidents": len(m1_full_per_inc),
        "paired_diff_vs_full": 0.0, "paired_ci_low": 0.0, "paired_ci_high": 0.0,
        "wilcoxon_p": np.nan, "n_cols_dropped": 0, "n_cols_used": len(all_feature_cols),
    }]
    per_incident_rows = [{"model": "M1_full", "incident_id": k, "pr_auc": v} for k, v in m1_full_per_inc.items()]

    for name, (drop_cols, model_factory) in ABLATIONS.items():
        drop_cols_present = [c for c in drop_cols if c in all_feature_cols]
        missing = [c for c in drop_cols if c not in all_feature_cols]
        if missing:
            print(f"CANH BAO: {name} - cot khong ton tai trong du lieu: {missing}")
        keep_cols = [c for c in all_feature_cols if c not in drop_cols_present]
        print(f"\n=== {name}: loai {len(drop_cols_present)} cot, con lai {len(keep_cols)} cot ===", flush=True)

        X = df[keep_cols]
        result = evaluate_model_nested(model_factory, X, y, groups, target_fpr=0.01)
        oof = result["oof_prob"]
        for r in result["fold_rows"]:
            print(f"  held_out={r['held_out_group']:32s} pr_auc={r['pr_auc']:.4f}", flush=True)

        valid = oof.notna()
        ci = bootstrap_incident_level(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
        per_inc = per_incident_metric(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
        for k, v in per_inc.items():
            per_incident_rows.append({"model": name, "incident_id": k, "pr_auc": v})

        common = sorted(set(per_inc) & set(m1_full_per_inc))
        ablation_scores = np.array([per_inc[i] for i in common])
        full_scores = np.array([m1_full_per_inc[i] for i in common])
        valid_mask = ~(np.isnan(ablation_scores) | np.isnan(full_scores))
        diffs = (ablation_scores - full_scores)[valid_mask]
        mean_diff, ci_lo, ci_hi = paired_bootstrap(diffs)
        try:
            _, wp = wilcoxon(ablation_scores[valid_mask], full_scores[valid_mask])
        except ValueError:
            wp = float("nan")

        print(f"  Mean PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")
        print(f"  Paired diff ({name} - M1_full) = {mean_diff:+.4f} [{ci_lo:+.4f}, {ci_hi:+.4f}], Wilcoxon p={wp}, n={valid_mask.sum()}")

        summary_rows.append({
            "model": name, "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
            "n_incidents": len(per_inc), "paired_diff_vs_full": mean_diff,
            "paired_ci_low": ci_lo, "paired_ci_high": ci_hi, "wilcoxon_p": wp,
            "n_cols_dropped": len(drop_cols_present), "n_cols_used": len(keep_cols),
            "n_incidents_paired": int(valid_mask.sum()),
        })

    summary_df = pd.DataFrame(summary_rows)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_TABLE, index=False)
    print(f"\nDa luu {OUT_TABLE}")

    overlap_temporal_bridge = set(TEMPORAL_COLS) & set(BRIDGE_CONTEXT_COLS)
    overlap_motif_bridge = set(MOTIF_COLS) & set(BRIDGE_CONTEXT_COLS)

    md = [
        "# [EXPLORATORY/post-hoc, ngoai plan v3] Ablation E4 (no-temporal) + E5 (no-motif) "
        "+ with-bridge-context — N=30\n",
        "\nPhương pháp: giống hệt RQ1/N15/N20 — pool 8 prefix bucket, dedupe theo "
        "(source_id, prefix_len), leave-one-incident-out, bootstrap CI mức incident, paired "
        "bootstrap + Wilcoxon trên hiệu số per-incident. M1_full tái sử dụng OOF có sẵn từ "
        f"`{OOF_M1_FULL_PATH.relative_to(ROOT)}` (đã xác nhận khớp 1-1 với N30 dedupe, {len(df)}/{len(df)}).\n",
        "\n## Bảng tổng hợp\n",
        "\n| Model | Mean PR-AUC | 95% CI | Diff vs M1_full | Paired 95% CI | Wilcoxon p | n (incident ghép đôi) | Cột loại/thêm |\n|---|---|---|---|---|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        n_paired = int(r["n_incidents_paired"]) if pd.notna(r.get("n_incidents_paired")) else "-"
        md.append(f"| {r['model']} | {r['mean_pr_auc']:.4f} | [{r['ci_low_95']:.4f}, {r['ci_high_95']:.4f}] | "
                   f"{r['paired_diff_vs_full']:+.4f} | [{r['paired_ci_low']:+.4f}, {r['paired_ci_high']:+.4f}] | "
                   f"{r['wilcoxon_p']} | {n_paired} | {int(r['n_cols_dropped'])} |\n")

    md += [
        "\n## Cột liên quan từng ablation\n",
        f"\n- **no-temporal** ({len(TEMPORAL_COLS)} cột LOẠI): `{TEMPORAL_COLS}`\n",
        f"- **no-motif** ({len(MOTIF_COLS)} cột LOẠI): `{MOTIF_COLS}`\n",
        f"- **with-bridge-context** ({len(BRIDGE_CONTEXT_COLS)} cột THÊM LẠI): `{BRIDGE_CONTEXT_COLS}`\n",
        "\n## Lưu ý overlap (giống N15)\n",
        f"\n- Trùng với temporal: `{sorted(overlap_temporal_bridge)}`\n",
        f"- Trùng với motif: `{sorted(overlap_motif_bridge)}`\n",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")

    pd.DataFrame(per_incident_rows).to_csv(ROOT / "results" / "tables" / "extra_N30_ablation_per_incident.csv", index=False)


if __name__ == "__main__":
    main()
