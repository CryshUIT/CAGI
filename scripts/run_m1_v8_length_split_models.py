"""NSS 2026 (2026-09-26) - Attempt #14: model tach rieng theo do dai
trajectory (SHORT <=40 action vs LONG >40 action), dua tren phat hien root-
cause: loi ich cua M1 so voi B3 tuong quan RAT MANH voi do dai trajectory
(Spearman rho=0.859, p=0.00008, xem m1_vs_b3_discussion_analysis_2026-09-26.md).

NGUONG PHAN NHOM: 40 action (khe ho tu nhien 40->73 trong phan phoi do dai
that cua 15 incident - xem lenh kiem tra truc tiep truoc khi viet script
nay). Day la nguong DA CO SAN tu attempt #7 (trajectory-fair-weight,
SHORT_INCIDENTS/LONG_INCIDENTS), chon TRUOC KHI biet ket qua attempt nay,
KHONG tune lai qua nested-CV o day - ly do: voi N=15, tach doi con 7-8
incident/nhom, nested-CV chon nguong tren tung nhom con nay se cuc ky nhieu
(dung bai hoc tu attempt #13: nested-CV tren nhom nho <10 rat de bi nhieu
chi phoi). Dung nguong CO SAN, da xac lap boi phan phoi that (khe ho tu
nhien), khong phai "mo" hom nay, la lua chon an toan hon.

CANH BAO METHODOLOGY (bat buoc neu ket qua "thang"): N=15 tach doi thanh 7
va 8 incident/nhom la RAT nho - inner-CV cho tung nhom con chi co 6-7 fold,
rui ro overfit/nhieu cao. Bat ky ket qua duong tinh nao PHAI kiem tra ky qua
5 seed truoc khi tin, va neu dua vao bai PHAI neu ro "lan thu 14/14+" (xem
yeu cau minh bach multiple-comparison).

Thiet ke: voi MOI outer fold (LOIO tren toan bo 15 incident nhu binh
thuong), xac dinh nhom (SHORT/LONG) cua incident dang giu lai, CHI dung cac
incident CUNG NHOM (da loai incident giu lai) lam outer-train - fit 1 model
M1 rieng cho nhom do. Inner LOGO threshold selection cung CHI tren cac
incident cung nhom (6-7 fold). Du doan outer test bang model cua dung nhom.
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
LENGTH_THRESHOLD = 40  # <=40 SHORT, >40 LONG - khe ho tu nhien 40->73, dung tu attempt #7
OUT_CSV = ROOT / "results" / "tables" / "m1_v8_length_split_models_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v8_length_split_models_2026-09-26.md"
SEEDS = [42, 1, 7, 123, 2026]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def build_data():
    df = dedupe_pooled_prefixes(pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet"))
    group_len = df[df["kind"] == "positive"].groupby("group_id")["trajectory_len"].first()
    group_bucket = group_len.apply(lambda L: "SHORT" if L <= LENGTH_THRESHOLD else "LONG")
    return df, group_bucket


def evaluate_length_split(df, group_bucket, feature_cols, random_state=None):
    outer_logo = LeaveOneGroupOut()
    y_all, groups_all = df["label"], df["group_id"]
    oof_prob = pd.Series(np.full(len(df), np.nan), index=df.index)
    oof_threshold = pd.Series(np.full(len(df), np.nan), index=df.index)
    fold_info = []

    for train_idx, test_idx in outer_logo.split(df, y_all, groups=groups_all):
        held_out = groups_all.iloc[test_idx].iloc[0]
        bucket = group_bucket[held_out]
        same_bucket_groups = [g for g in group_bucket.index if group_bucket[g] == bucket and g != held_out]

        outer_train = df[df["group_id"].isin(same_bucket_groups)]
        outer_test = df.iloc[test_idx]
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

        outer_pr = pr_auc(outer_test["label"].to_numpy(), prob_test)
        fold_info.append({"held_out_group": held_out, "bucket": bucket,
                           "n_train_incidents": len(same_bucket_groups), "outer_pr_auc": outer_pr})
        print(f"  fold={held_out:32s} bucket={bucket:5s} n_train_incidents={len(same_bucket_groups)} "
              f"outer_pr_auc={outer_pr:.4f}", flush=True)

    return oof_prob, oof_threshold, fold_info


def main():
    df, group_bucket = build_data()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    print("Phan nhom incident:")
    for g, b in group_bucket.items():
        print(f"  {g:32s} {b}")
    print(f"So incident SHORT: {(group_bucket=='SHORT').sum()}, LONG: {(group_bucket=='LONG').sum()}")

    print("\n=== M1_v8 (model tach theo do dai) ===", flush=True)
    oof_prob, oof_threshold, fold_info = evaluate_length_split(df, group_bucket, feature_cols)
    pd.DataFrame(fold_info).to_csv(ROOT / "results" / "tables" / "m1_v8_fold_info_2026-09-26.csv", index=False)

    valid = oof_prob.notna()
    y, groups = df["label"], df["group_id"]
    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"\nM1_v8 pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")
    merged_check.index = df.index

    per_inc_v8 = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v8) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v8[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"Paired diff (M1_v8 - M1 chinh thuc, pooled toan bo) = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v8) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v8[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"Paired diff (M1_v8 - B3, pooled toan bo) = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    # --- Breakdown rieng SHORT vs LONG (v8 vs M1 chinh thuc vs B3) ---
    results_by_bucket = {}
    for bucket in ["SHORT", "LONG"]:
        bucket_groups = [g for g in group_bucket.index if group_bucket[g] == bucket]
        mask = groups.isin(bucket_groups) & valid
        y_b = y[mask].to_numpy()
        g_b = groups[mask].to_numpy()
        v8_b = oof_prob[mask].to_numpy()
        m1_b = merged_check.loc[mask.to_numpy(), "oof_prob_M1"].to_numpy()
        b3_b = merged_check.loc[mask.to_numpy(), "oof_prob_B3"].to_numpy()

        pr_v8 = pr_auc(y_b, v8_b)
        pr_m1 = pr_auc(y_b, m1_b)
        pr_b3 = pr_auc(y_b, b3_b)

        per_inc_v8_b = per_incident_metric(y_b, v8_b, g_b, pr_auc)
        per_inc_m1_b = per_incident_metric(y_b, m1_b, g_b, pr_auc)
        common_b = sorted(set(per_inc_v8_b) & set(per_inc_m1_b))
        diffs_b = np.array([per_inc_v8_b[i] - per_inc_m1_b[i] for i in common_b])
        mean_diff_b, lo_b, hi_b = paired_bootstrap(diffs_b, n_boot=2000)

        results_by_bucket[bucket] = {
            "n_incidents": len(bucket_groups), "n_rows": int(mask.sum()),
            "pr_auc_v8": pr_v8, "pr_auc_m1_official": pr_m1, "pr_auc_b3": pr_b3,
            "paired_diff_v8_vs_m1": mean_diff_b, "paired_ci_low": lo_b, "paired_ci_high": hi_b,
        }
        print(f"\n=== Nhom {bucket} ({len(bucket_groups)} incident, {int(mask.sum())} dong) ===")
        print(f"  PR-AUC pooled: M1_v8={pr_v8:.4f}, M1 chinh thuc={pr_m1:.4f}, B3={pr_b3:.4f}")
        print(f"  Paired diff (M1_v8 - M1 chinh thuc) = {mean_diff_b:+.4f} [{lo_b:+.4f}, {hi_b:+.4f}]")

    verdict = ("CAI THIEN CO Y NGHIA THONG KE (pooled toan bo) - se kiem tra qua 5 seed."
               if lo_m1 > 0 else "KHONG CAI THIEN CO Y NGHIA THONG KE (pooled toan bo).")
    print(f"\n=== KET LUAN (pooled toan bo) ===\n{verdict}")

    seed_note = ""
    if lo_m1 > 0:
        print("\n=== Kiem tra 5 seed ===", flush=True)
        seed_scores = []
        for seed in SEEDS:
            oof_s, _, _ = evaluate_length_split(df, group_bucket, feature_cols, random_state=seed)
            v = oof_s.notna()
            c = bootstrap_incident_level(y[v].to_numpy(), oof_s[v].to_numpy(), groups[v].to_numpy(), pr_auc, n_boot=500)
            print(f"  seed={seed}: pooled PR-AUC = {c['point']:.4f}", flush=True)
            seed_scores.append(c["point"])
        seed_note = f"5-seed: mean={np.mean(seed_scores):.4f} std={np.std(seed_scores):.4f} values={seed_scores}"
        print(seed_note)

    pd.DataFrame([{
        "model": "M1_v8_length_split", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
        **{f"{k}_{bucket}": v for bucket, res in results_by_bucket.items() for k, v in res.items()},
    }]).to_csv(OUT_CSV, index=False)

    md = [
        "# M1_v8 - model tach theo do dai trajectory (Attempt #14, 2026-09-26)\n",
        f"\nNguong phan nhom: SHORT <= {LENGTH_THRESHOLD} action, LONG > {LENGTH_THRESHOLD} action "
        "(khe ho tu nhien trong phan phoi do dai that, dung lai tu attempt #7, KHONG tune moi qua nested-CV "
        "o attempt nay - ly do: N=15 tach doi con 7-8/nhom, nested-CV tren nhom nho se nhieu, giong bai hoc "
        "tu attempt #13).\n",
        "\n## Pooled toan bo (15 incident, dung dung sub-model theo nhom)\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 chinh thuc (moc) | 0.6624 | [0.5234, 0.8864] |\n",
        "| B3 (moc) | 0.6875 | - |\n",
        f"| **M1_v8 (tach theo do dai)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (M1_v8 - M1 chinh thuc) = {mean_diff_m1:+.4f}, 95% CI = [{lo_m1:+.4f}, {hi_m1:+.4f}]**\n",
        f"\n**Paired diff (M1_v8 - B3) = {mean_diff_b3:+.4f}, 95% CI = [{lo_b3:+.4f}, {hi_b3:+.4f}]**\n",
        "\n## Breakdown rieng tung nhom\n",
        "\n| Nhom | n_incident | PR-AUC M1_v8 | PR-AUC M1 chinh thuc | PR-AUC B3 | Paired diff (v8-M1) | CI |\n|---|---|---|---|---|---|---|\n",
    ]
    for bucket, res in results_by_bucket.items():
        md.append(f"| {bucket} | {res['n_incidents']} | {res['pr_auc_v8']:.4f} | {res['pr_auc_m1_official']:.4f} | "
                   f"{res['pr_auc_b3']:.4f} | {res['paired_diff_v8_vs_m1']:+.4f} | "
                   f"[{res['paired_ci_low']:+.4f}, {res['paired_ci_high']:+.4f}] |\n")
    md.append(f"\n## KET LUAN (pooled toan bo)\n\n{verdict}\n\n{seed_note}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
