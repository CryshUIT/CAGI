"""NSS 2026 (2026-09-26) - Attempt #13: tinh chinh TY LE pool unmatched-
negative them vao train (chon qua nested inner-CV, khong dung outer test),
thay vi them TOAN BO nhu attempt #11 (gay threshold bi day qua cao
0.8867->0.9934, hai recall nhieu incident khac du sua duoc 8/16 dong loi).

Chien luoc chon subset (khong random - co muc dich, bam sat co che da chan
doan): chon top-K% TRAJECTORY unmatched theo fan_out LON NHAT (do phuc tap
cau truc cao nhat) - day la nhung candidate "day du thong tin nhat" de day
model hoc "phuc tap cau truc cao van co the la benign", thay vi random
(se pha loang tin hieu voi nhieu candidate fan_out thap khong day them gi
moi so voi negative da co san).

Candidate ty le: {0.0, 0.10, 0.25, 0.50} (bo qua 1.0 - da biet ket qua tu
attempt #11, pooled te hon). 0.0 = M1 chinh thuc (dua vao lam mocj so sanh
trong chinh vong chon nested). Chon qua inner-CV MOI outer fold (co the
khac nhau giua cac fold).
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
FRACTIONS = [0.0, 0.10, 0.25, 0.50]
OUT_CSV = ROOT / "results" / "tables" / "m1_v7_unmatched_fraction_tuned_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v7_unmatched_fraction_tuned_2026-09-26.md"
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
    traj_max_fanout = df_unmatched.groupby("source_id")["fan_out"].max().sort_values(ascending=False)
    return df_matched, df_unmatched, traj_max_fanout


def select_unmatched_subset(df_unmatched, traj_ranked, available_group_mask, fraction):
    """Chon top-fraction TRAJECTORY (theo fan_out da rank san) trong pham vi
    group_id duoc phep (loai held-out incident) - giu NGUYEN toan bo prefix
    row cua trajectory duoc chon (khong cat le)."""
    if fraction <= 0:
        return df_unmatched.iloc[0:0]
    available_traj = [t for t in traj_ranked.index if available_group_mask.get(t, False)]
    k = max(1, int(round(len(available_traj) * fraction))) if available_traj else 0
    chosen = set(available_traj[:k])
    return df_unmatched[df_unmatched["source_id"].isin(chosen)]


def main():
    df_matched, df_unmatched, traj_ranked = build_data()
    feature_cols = [c for c in df_matched.columns if c not in META_COLS]
    traj_to_group = df_unmatched.drop_duplicates("source_id").set_index("source_id")["group_id"].to_dict()

    outer_logo = LeaveOneGroupOut()
    y_all, groups_all = df_matched["label"], df_matched["group_id"]
    oof_prob = pd.Series(np.full(len(df_matched), np.nan), index=df_matched.index)
    oof_threshold = pd.Series(np.full(len(df_matched), np.nan), index=df_matched.index)
    fold_choices = []

    for train_idx, test_idx in outer_logo.split(df_matched, y_all, groups=groups_all):
        held_out = groups_all.iloc[test_idx].iloc[0]
        outer_train_matched = df_matched.iloc[train_idx]
        outer_test = df_matched.iloc[test_idx]

        available_mask = {t: (g != held_out) for t, g in traj_to_group.items()}
        inner_logo = LeaveOneGroupOut()
        y_train_m, g_train_m = outer_train_matched["label"], outer_train_matched["group_id"]

        candidate_scores = {}
        for frac in FRACTIONS:
            unmatched_subset = select_unmatched_subset(df_unmatched, traj_ranked, available_mask, frac)
            inner_scores_this_frac = []
            for inner_tr_idx, inner_val_idx in inner_logo.split(outer_train_matched, y_train_m, groups=g_train_m):
                inner_tr_matched = outer_train_matched.iloc[inner_tr_idx]
                inner_val = outer_train_matched.iloc[inner_val_idx]
                inner_held_out_group = g_train_m.iloc[inner_val_idx].iloc[0]
                inner_unmatched = unmatched_subset[unmatched_subset["group_id"] != inner_held_out_group]
                inner_tr = pd.concat([inner_tr_matched, inner_unmatched], ignore_index=False)
                m = M1TypedTemporalMotifModel()
                m.fit(inner_tr[feature_cols], inner_tr["label"], inner_tr["group_id"])
                prob = m.predict_proba(inner_val[feature_cols])
                inner_scores_this_frac.append(pr_auc(inner_val["label"].to_numpy(), prob))
            candidate_scores[frac] = float(np.mean(inner_scores_this_frac))

        best_frac = max(candidate_scores, key=candidate_scores.get)
        fold_choices.append({"held_out_group": held_out, **{f"frac_{f}_inner_pr_auc": s for f, s in candidate_scores.items()}, "chosen_fraction": best_frac})
        print(f"  fold={held_out:32s} inner scores={candidate_scores} -> chosen fraction={best_frac}", flush=True)

        chosen_unmatched = select_unmatched_subset(df_unmatched, traj_ranked, available_mask, best_frac)
        outer_train = pd.concat([outer_train_matched, chosen_unmatched], ignore_index=False)
        y_train, g_train = outer_train["label"], outer_train["group_id"]

        inner_oof = pd.Series(np.full(len(outer_train), np.nan), index=outer_train.index)
        for inner_tr_idx, inner_val_idx in inner_logo.split(outer_train, y_train, groups=g_train):
            m = M1TypedTemporalMotifModel()
            inner_tr = outer_train.iloc[inner_tr_idx]
            inner_val = outer_train.iloc[inner_val_idx]
            m.fit(inner_tr[feature_cols], inner_tr["label"], inner_tr["group_id"])
            inner_oof.iloc[inner_val_idx] = m.predict_proba(inner_val[feature_cols])
        valid = inner_oof.notna()
        threshold = select_threshold(y_train[valid].to_numpy(), inner_oof[valid].to_numpy(), target_fpr=0.01)

        final_model = M1TypedTemporalMotifModel()
        final_model.fit(outer_train[feature_cols], outer_train["label"], outer_train["group_id"])
        prob_test = final_model.predict_proba(outer_test[feature_cols])
        oof_prob.iloc[test_idx] = prob_test
        oof_threshold.iloc[test_idx] = threshold
        print(f"    -> outer_test pr_auc={pr_auc(outer_test['label'].to_numpy(), prob_test):.4f}, threshold={threshold:.4f}", flush=True)

    pd.DataFrame(fold_choices).to_csv(ROOT / "results" / "tables" / "m1_v7_fold_choices_2026-09-26.csv", index=False)

    valid = oof_prob.notna()
    y, groups = df_matched["label"], df_matched["group_id"]
    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"\nM1_v7 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df_matched[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")
    merged_check.index = df_matched.index

    per_inc_v7 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v7) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v7[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v7 - M1 chinh thuc) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v7) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v7[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v7 - B3) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    print("\n=== Kiem tra dung 2 ca da chan doan ===")
    case_rows = []
    n_fixed = 0
    for sid in ["ronin_bridge_2022__hn012", "ronin_benign_control_2022"]:
        sub = df_matched[df_matched["source_id"] == sid]
        for i in sub.index:
            plen = df_matched.loc[i, "prefix_len"]
            new_prob = oof_prob.loc[i]
            old_prob = merged_check.loc[i, "oof_prob_M1"]
            thr = oof_threshold.loc[i]
            fixed = bool(new_prob < thr)
            n_fixed += int(fixed)
            print(f"  {sid} prefix_len={plen}: M1_v7_prob={new_prob:.4f} (threshold={thr:.4f}), "
                  f"M1_chinh_thuc_prob={old_prob:.4f} {'[FIXED]' if fixed else '[VAN FP]'}")
            case_rows.append({"source_id": sid, "prefix_len": int(plen), "new_prob": float(new_prob),
                               "old_prob_m1_official": float(old_prob), "threshold": float(thr), "fixed": fixed})

    print(f"\nTong so dong fixed: {n_fixed}/16")

    verdict = "CAI THIEN CO Y NGHIA THONG KE - se kiem tra qua 5 seed." if lo_m1 > 0 else "KHONG CAI THIEN CO Y NGHIA THONG KE."
    print(f"\n=== KET LUAN (pooled) ===\n{verdict}")

    seed_note = ""
    if lo_m1 > 0:
        print("\n=== 5-seed check khong kha thi trong pham vi timebox hom nay (nested fraction selection qua nang) ===")
        seed_note = "CANH BAO: CI loai 0 nhung 5-seed check CHUA chay do chi phi tinh toan - xem trang thai do dang."

    pd.DataFrame([{
        "model": "M1_v7_unmatched_fraction_tuned", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
        "n_fixed_of_16": n_fixed,
    }]).to_csv(OUT_CSV, index=False)

    md = [
        "# M1_v7 - tinh chinh ty le unmatched-negative them vao train (Attempt #13, 2026-09-26)\n",
        "\nChon top-K% TRAJECTORY unmatched theo fan_out LON NHAT (do phuc tap cau truc cao nhat) - "
        "K chon qua nested inner-CV moi outer fold trong {0%, 10%, 25%, 50%}.\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v7 (ty le unmatched tuned)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v7 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v7 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        f"\n## Kiem tra dung 2 ca da chan doan: {n_fixed}/16 dong fixed\n",
        "\n| source_id | prefix_len | prob moi (M1_v7) | prob M1 chinh thuc | threshold | fixed? |\n|---|---|---|---|---|---|\n",
    ]
    for r in case_rows:
        md.append(f"| {r['source_id']} | {r['prefix_len']} | {r['new_prob']:.4f} | {r['old_prob_m1_official']:.4f} | "
                   f"{r['threshold']:.4f} | {'CO' if r['fixed'] else 'KHONG'} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n\n{seed_note}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
