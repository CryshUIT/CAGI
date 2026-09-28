"""NSS 2026 (2026-09-26) - Huong 9 (LAN CUOI): them feature
`path_depth_per_action = path_depth / prefix_len` de sua loi da chan doan
truc tiep tu du lieu (xem bao cao chan doan trong hoi thoai): `path_depth`
(feature THO, khong co ban chuan hoa) co gain trung binh 185.2 qua 15 fold -
gap 9.5 lan feature dung thu 2 - va tao ranh gioi gia tao: path_depth>=2 chi
chiem 2.2% negative nhung 66% positive, khien negative "vo tinh" dat
path_depth=2 (thuong sau RAT NHIEU action, vd 55-219 action, khac han
positive dat cung do sau chi sau ~5-7 action) bi gan nhan sai voi xac suat
gan 1.0 - day chinh la nguyen nhan 15/18 (83%) false positive toan du an tap
trung o `ronin_bridge_2022__hn012` va `ronin_benign_control_2022`.

Gia thuyet: `path_depth_per_action` (KHONG THAY THE path_depth, chi THEM)
giup model phan biet "dat do sau X NHANH" (dau hieu layering chu dong that)
voi "dat CUNG do sau X sau rat nhieu action" (chuoi relay/tich luy dai,
lanh tinh).
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
OUT_CSV = ROOT / "results" / "tables" / "m1_v3_path_depth_efficiency_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v3_path_depth_efficiency_2026-09-26.md"
SEEDS = [42, 1, 7, 123, 2026]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def build_dataset():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    df = df.copy()
    df["path_depth_per_action"] = df["path_depth"] / df["prefix_len"].clip(lower=1)
    return df


def main():
    df = build_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    print("=== M1_v3 (+ path_depth_per_action) ===", flush=True)
    res = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)
    oof_prob = res["oof_prob"]
    oof_threshold = res["oof_threshold"]
    valid = oof_prob.notna()

    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"M1_v3 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")

    per_inc_v3 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v3) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v3[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v3 - M1 chinh thuc) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v3) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v3[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v3 - B3) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    # --- Breakdown tren dung vung loi da chan doan: negative co path_depth>=2 ---
    problem_mask = (df["label"] == 0) & (df["path_depth"] >= 2) & valid
    n_problem = int(problem_mask.sum())
    v3_pred_problem = (oof_prob[problem_mask] >= oof_threshold[problem_mask]).astype(int)
    n_fp_v3_problem = int(v3_pred_problem.sum())
    m1_prob_problem = merged_check.loc[problem_mask.to_numpy(), "oof_prob_M1"]
    print(f"\n=== Breakdown tren vung loi da chan doan (negative co path_depth>=2, n={n_problem}) ===")
    print(f"M1_v3: mean_prob={oof_prob[problem_mask].mean():.4f}, n_FP (>=threshold cua fold)={n_fp_v3_problem}/{n_problem}")
    print(f"M1 chinh thuc: mean_prob={m1_prob_problem.mean():.4f} (tu oof_predictions_v1.csv, threshold rieng - xem bao cao Buoc 1 cho FP dem duoc: 18 tong, 15 o day)")

    for sid in ["ronin_bridge_2022__hn012", "ronin_benign_control_2022"]:
        sub = df[df["source_id"] == sid]
        idx = sub.index
        print(f"\n{sid}:")
        for i in idx:
            plen = df.loc[i, "prefix_len"]
            print(f"  prefix_len={plen}: M1_v3_prob={oof_prob.loc[i]:.4f} (threshold={oof_threshold.loc[i]:.4f}), "
                  f"M1_chinh_thuc_prob={merged_check.loc[i, 'oof_prob_M1']:.4f}")

    verdict = (
        "CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc - se kiem tra qua 5 seed."
        if lo_m1 > 0 else
        "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 chinh thuc (pooled)."
    )
    print(f"\n=== KET LUAN (pooled) ===\n{verdict}")

    pd.DataFrame([{
        "model": "M1_v3_path_depth_efficiency", "mean_pr_auc": ci["point"],
        "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
        "n_problem_zone": n_problem, "n_fp_v3_problem_zone": n_fp_v3_problem,
        "mean_prob_v3_problem_zone": float(oof_prob[problem_mask].mean()),
        "mean_prob_m1_official_problem_zone": float(m1_prob_problem.mean()),
    }]).to_csv(OUT_CSV, index=False)

    seed_check_note = ""
    if lo_m1 > 0:
        print("\n=== Cai thien co CI loai 0 - chay kiem tra 5 seed ===", flush=True)
        seed_results = []
        for seed in SEEDS:
            factory = lambda s=seed: M1TypedTemporalMotifModel(random_state=s)
            r = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
            v = r["oof_prob"].notna()
            c = bootstrap_incident_level(y[v].to_numpy(), r["oof_prob"][v].to_numpy(), groups[v].to_numpy(), pr_auc, n_boot=500)
            print(f"  seed={seed}: pooled PR-AUC = {c['point']:.4f}", flush=True)
            seed_results.append(c["point"])
        seed_arr = np.array(seed_results)
        seed_check_note = f"\n5-seed check: mean={seed_arr.mean():.4f}, std={seed_arr.std():.4f}, seeds={SEEDS}, values={seed_results}\n"
        print(seed_check_note)

    md = [
        "# M1_v3 - path_depth_per_action (Huong 9, LAN CUOI, 2026-09-26)\n",
        "\nFeature moi: `path_depth_per_action = path_depth / prefix_len` - nham sua loi False "
        "Positive tap trung (83% toan du an) tai `ronin_bridge_2022__hn012` va `ronin_benign_control_2022`, "
        "do `path_depth` (feature gain cao nhat, 185.2, gap 9.5 lan feature thu 2) tao ranh gioi gia tao "
        "path_depth>=2 (2.2% negative vs 66% positive).\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v3 (+path_depth_per_action)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v3 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v3 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        f"\n## Breakdown tren vung loi da chan doan (negative co path_depth>=2, n={n_problem})\n",
        f"\nM1_v3: mean_prob={oof_prob[problem_mask].mean():.4f}, n_FP={n_fp_v3_problem}/{n_problem}\n",
        f"\nM1 chinh thuc: mean_prob={m1_prob_problem.mean():.4f} (15/18 FP toan du an nam trong nhom nay)\n",
        f"\n## KET LUAN (pooled)\n\n{verdict}\n",
        seed_check_note,
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
