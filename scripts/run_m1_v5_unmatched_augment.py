"""NSS 2026 (2026-09-26) - Attempt #11 (LAN CUOI, cung #12): bo sung
"unmatched negative" pool (E6, 591 candidate that bi loai khoi mining vi
khong khop tieu chi cau truc) lam NEGATIVE BO SUNG vao TAP TRAIN cua M1.

Ly do (tu du lieu that, results/reports/e6_robustness_v1.md): unmatched
negative co fan_out trung binh 6.54 (mean, toi da 247) so voi matched
hard-negative dang dung de train chi 1.42 - M1 CHUA TUNG thay 1 vi du benign
nao co do phuc tap cau truc cao trong luc train (tieu chi mining fan_out<=3
da loc sach). Day CHINH XAC la co che gay 2 false positive nghiem trong nhat
(`ronin_bridge_2022__hn012`, `ronin_benign_control_2022`) da chan doan o
attempt #9: path_depth/unique_counterparties/branch_count cao bat thuong so
voi MOI negative khac trong train.

Thiet ke (khong co hyperparameter can chon qua inner-CV - quyet dinh nhi
phan "them toan bo pool unmatched san co cua 14 incident con lai"):
  Voi MOI outer fold (giu incident G lam test):
    outer_train = matched(G loai bo) UNION unmatched(G loai bo, dedupe rieng)
    outer_test = CHINH outer test GOC cua M1 (chi matched, KHONG doi) - de
    so sanh duoc truc tiep voi 0.6624.
    Inner LOGO tren outer_train (ca matched+unmatched, cung group_id) de
    chon threshold - dung dung thiet ke nested, khong dung outer test.
    Fit model cuoi tren TOAN BO outer_train (matched+unmatched), du doan
    outer_test (matched-only).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import (  # noqa: E402
    bootstrap_incident_level, dedupe_pooled_prefixes, per_incident_metric, select_threshold,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OUT_CSV = ROOT / "results" / "tables" / "m1_v5_unmatched_augment_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v5_unmatched_augment_2026-09-26.md"
SEEDS = [42, 1, 7, 123, 2026]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def build_data():
    df_matched = dedupe_pooled_prefixes(pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet"))
    df_e6 = pd.read_parquet(ROOT / "data" / "processed" / "e6_unmatched_negative_features.parquet")
    df_unmatched = dedupe_pooled_prefixes(df_e6[df_e6["kind"] == "unmatched_negative"].copy())
    return df_matched, df_unmatched


def evaluate_with_augment(df_matched, df_unmatched, feature_cols, random_state=None):
    outer_logo = LeaveOneGroupOut()
    y_all, groups_all = df_matched["label"], df_matched["group_id"]
    oof_prob = pd.Series(np.full(len(df_matched), np.nan), index=df_matched.index)
    oof_threshold = pd.Series(np.full(len(df_matched), np.nan), index=df_matched.index)
    n_unmatched_added = []

    for train_idx, test_idx in outer_logo.split(df_matched, y_all, groups=groups_all):
        held_out = groups_all.iloc[test_idx].iloc[0]
        outer_train_matched = df_matched.iloc[train_idx]
        outer_test = df_matched.iloc[test_idx]
        outer_train_unmatched = df_unmatched[df_unmatched["group_id"] != held_out]
        n_unmatched_added.append(len(outer_train_unmatched))

        outer_train = pd.concat([outer_train_matched, outer_train_unmatched], ignore_index=False)
        y_train, g_train = outer_train["label"], outer_train["group_id"]

        inner_logo = LeaveOneGroupOut()
        inner_oof = pd.Series(np.full(len(outer_train), np.nan), index=outer_train.index)
        for inner_tr_idx, inner_val_idx in inner_logo.split(outer_train, y_train, groups=g_train):
            m = M1TypedTemporalMotifModel(random_state=random_state) if random_state else M1TypedTemporalMotifModel()
            inner_tr = outer_train.iloc[inner_tr_idx]
            inner_val = outer_train.iloc[inner_val_idx]
            m.fit(inner_tr[feature_cols], inner_tr["label"], inner_tr["group_id"])
            inner_oof.iloc[inner_val_idx] = m.predict_proba(inner_val[feature_cols])
        valid = inner_oof.notna()
        threshold = select_threshold(y_train[valid].to_numpy(), inner_oof[valid].to_numpy(), target_fpr=0.01)

        final_model = M1TypedTemporalMotifModel(random_state=random_state) if random_state else M1TypedTemporalMotifModel()
        final_model.fit(outer_train[feature_cols], outer_train["label"], outer_train["group_id"])
        prob_test = final_model.predict_proba(outer_test[feature_cols])
        oof_prob.iloc[test_idx] = prob_test
        oof_threshold.iloc[test_idx] = threshold
        print(f"  fold={held_out:32s} n_unmatched_added={len(outer_train_unmatched):4d} "
              f"pr_auc_outer={pr_auc(outer_test['label'].to_numpy(), prob_test):.4f}", flush=True)

    return oof_prob, oof_threshold, n_unmatched_added


def main():
    df_matched, df_unmatched = build_data()
    feature_cols = [c for c in df_matched.columns if c not in META_COLS]
    print(f"Matched (official): {len(df_matched)} dong. Unmatched pool (dedupe): {len(df_unmatched)} dong.")

    print("\n=== M1_v5 (train + unmatched augment) ===", flush=True)
    oof_prob, oof_threshold, n_added = evaluate_with_augment(df_matched, df_unmatched, feature_cols)
    valid = oof_prob.notna()
    y, groups = df_matched["label"], df_matched["group_id"]

    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"\nM1_v5 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df_matched[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")
    merged_check.index = df_matched.index

    per_inc_v5 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v5) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v5[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v5 - M1 chinh thuc) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v5) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v5[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v5 - B3) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    print("\n=== Kiem tra dung 2 ca da chan doan ===")
    case_rows = []
    for sid in ["ronin_bridge_2022__hn012", "ronin_benign_control_2022"]:
        sub = df_matched[df_matched["source_id"] == sid]
        for i in sub.index:
            plen = df_matched.loc[i, "prefix_len"]
            new_prob = oof_prob.loc[i]
            old_prob = merged_check.loc[i, "oof_prob_M1"]
            thr = oof_threshold.loc[i]
            print(f"  {sid} prefix_len={plen}: M1_v5_prob={new_prob:.4f} (threshold={thr:.4f}), "
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
            oof_s, _, _ = evaluate_with_augment(df_matched, df_unmatched, feature_cols, random_state=seed)
            v = oof_s.notna()
            c = bootstrap_incident_level(y[v].to_numpy(), oof_s[v].to_numpy(), groups[v].to_numpy(), pr_auc, n_boot=500)
            print(f"  seed={seed}: pooled PR-AUC = {c['point']:.4f}", flush=True)
            seed_scores.append(c["point"])
        seed_note = f"5-seed: mean={np.mean(seed_scores):.4f} std={np.std(seed_scores):.4f} values={seed_scores}"
        print(seed_note)

    pd.DataFrame([{
        "model": "M1_v5_unmatched_augment", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
        "mean_n_unmatched_added_per_fold": float(np.mean(n_added)),
    }]).to_csv(OUT_CSV, index=False)

    md = [
        "# M1_v5 - bo sung unmatched-negative vao train (Attempt #11, 2026-09-26)\n",
        "\nThem toan bo pool 'unmatched negative' (E6, cac candidate bi loai khoi mining hard-negative "
        "vi khong khop tieu chi cau truc) cua 14 incident outer-train lam negative BO SUNG (khong thay "
        "the) vao tap train moi outer fold - tap test GIU NGUYEN nhu M1 chinh thuc de so sanh duoc.\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v5 (+unmatched augment)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v5 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v5 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        "\n## Kiem tra dung 2 ca da chan doan\n\n| source_id | prefix_len | prob moi (M1_v5) | prob M1 chinh thuc | threshold |\n|---|---|---|---|---|\n",
    ]
    for r in case_rows:
        md.append(f"| {r['source_id']} | {r['prefix_len']} | {r['new_prob']:.4f} | {r['old_prob_m1_official']:.4f} | {r['threshold']:.4f} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n\n{seed_note}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
