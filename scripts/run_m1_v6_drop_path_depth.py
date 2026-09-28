"""NSS 2026 (2026-09-26) - Attempt #12 (LAN CUOI, cung #11): LOAI BO HOAN
TOAN `path_depth` khoi feature set cua M1 (khong them, khong bien doi -
loai han).

Ly do: chuoi #9 (them feature ben canh - that bai, cay van dung path_depth
goc), #10a/#10b (thay bang ban bien doi - that bai vi bat bien voi bien doi
don dieu / cap khong cham dung gia tri gay loi) da loai het cac cach "sua"
con giu lai path_depth duoi mot hinh thuc nao do. Day la lua chon con lai
duy nhat trong chuoi sua path_depth: loai bo hoan toan. Permutation
importance (attempt #6) KHONG loai path_depth (do gain TRUNG BINH qua inner-
CV la duong, nhung SHAP da chi ro no la driver lon nhat CHI RIENG cho 2 ca
loi te nhat, thiet hai co the bi che boi trung binh toan cuc).
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
             "prefix_label", "prefix_len", "trajectory_len", "path_depth"]
OUT_CSV = ROOT / "results" / "tables" / "m1_v6_drop_path_depth_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v6_drop_path_depth_2026-09-26.md"
SEEDS = [42, 1, 7, 123, 2026]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    assert "path_depth" not in feature_cols
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    print("=== M1_v6 (khong co path_depth) ===", flush=True)
    res = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
    oof_prob = res["oof_prob"]
    oof_threshold = res["oof_threshold"]
    valid = oof_prob.notna()

    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"M1_v6 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")

    per_inc_v6 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v6) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v6[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v6 - M1 chinh thuc) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v6) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v6[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v6 - B3) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    print("\n=== Kiem tra dung 2 ca da chan doan ===")
    case_rows = []
    for sid in ["ronin_bridge_2022__hn012", "ronin_benign_control_2022"]:
        sub = df[df["source_id"] == sid]
        for i in sub.index:
            plen = df.loc[i, "prefix_len"]
            new_prob = oof_prob.loc[i]
            old_prob = merged_check.loc[i, "oof_prob_M1"]
            thr = oof_threshold.loc[i]
            print(f"  {sid} prefix_len={plen}: M1_v6_prob={new_prob:.4f} (threshold={thr:.4f}), "
                  f"M1_chinh_thuc_prob={old_prob:.4f}")
            case_rows.append({"source_id": sid, "prefix_len": int(plen), "new_prob": float(new_prob),
                               "old_prob_m1_official": float(old_prob), "threshold": float(thr)})

    verdict = "CAI THIEN CO Y NGHIA THONG KE - se kiem tra qua 5 seed." if lo_m1 > 0 else "KHONG CAI THIEN CO Y NGHIA THONG KE."
    print(f"\n=== KET LUAN (pooled) ===\n{verdict}")

    seed_note = ""
    if lo_m1 > 0:
        print("\n=== Kiem tra 5 seed ===", flush=True)
        seed_scores = []
        for seed in SEEDS:
            factory = lambda s=seed: M1TypedTemporalMotifModel(random_state=s)
            r = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
            v = r["oof_prob"].notna()
            c = bootstrap_incident_level(y[v].to_numpy(), r["oof_prob"][v].to_numpy(), groups[v].to_numpy(), pr_auc, n_boot=500)
            print(f"  seed={seed}: pooled PR-AUC = {c['point']:.4f}", flush=True)
            seed_scores.append(c["point"])
        seed_note = f"5-seed: mean={np.mean(seed_scores):.4f} std={np.std(seed_scores):.4f} values={seed_scores}"
        print(seed_note)

    pd.DataFrame([{
        "model": "M1_v6_drop_path_depth", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
    }]).to_csv(OUT_CSV, index=False)

    md = [
        "# M1_v6 - LOAI BO hoan toan path_depth (Attempt #12, 2026-09-26)\n",
        "\nKhong them, khong bien doi - loai han cot `path_depth` khoi feature set cua M1.\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v6 (khong path_depth)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v6 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v6 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        "\n## Kiem tra dung 2 ca da chan doan\n\n| source_id | prefix_len | prob moi (M1_v6) | prob M1 chinh thuc | threshold |\n|---|---|---|---|---|\n",
    ]
    for r in case_rows:
        md.append(f"| {r['source_id']} | {r['prefix_len']} | {r['new_prob']:.4f} | {r['old_prob_m1_official']:.4f} | {r['threshold']:.4f} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n\n{seed_note}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
