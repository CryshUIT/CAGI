"""NSS 2026 (2026-09-26) - Attempt #10: THAY THE (khong phai them ben canh
nhu attempt #9) `path_depth` bang ban bien doi, de giam do doc quyet dinh
gan-tat-dinh ma XGBoost dang hoc (gain=185.2, gap 9.5 lan feature #2, gay
83% false positive toan du an - xem chan doan attempt #9).

2 phuong an:
  (A) log1p(path_depth) - KHONG co hyperparameter can chon, ap dung dong
      nhat cho moi outer fold (khong co rui ro leak vi day la 1 phep bien
      doi CO DINH, deterministic, khong tune tren du lieu nao ca).
  (B) capped: min(path_depth, cap) - cap la hyperparameter, CHON QUA
      NESTED INNER-CV (giong het cau truc nested_hpo_m1.py): voi MOI outer
      fold, thu cap in {2,3} tren inner LOGO (14 incident con lai), chon cap
      co inner-OOF PR-AUC cao nhat CHO OUTER FOLD DO (co the khac nhau giua
      cac fold - dung chuan nested CV), roi fit lai tren toan bo outer-train
      voi cap thang, du doan outer test.

Ca 2 deu THAY THE cot `path_depth` (khong giu cot goc, khong them cot moi)
- khac han attempt #9 (chi THEM feature ben canh, khong dung).

Kiem tra rieng 2 ca da chan doan (ronin_bridge_2022__hn012,
ronin_benign_control_2022): xac suat co giam ve muc hop ly khong - day la
bang chung QUAN TRONG HON ca so pooled tong.
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
    bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric, select_threshold,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
CAP_CANDIDATES = [2, 3]
OUT_CSV = ROOT / "results" / "tables" / "m1_v4_path_depth_transform_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "m1_v4_path_depth_transform_2026-09-26.md"
SEEDS = [42, 1, 7, 123, 2026]

PROBLEM_CASES = ["ronin_bridge_2022__hn012", "ronin_benign_control_2022"]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def build_base_dataset():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    return dedupe_pooled_prefixes(df_raw)


def evaluate_log1p(df, feature_cols):
    df2 = df.copy()
    df2["path_depth"] = np.log1p(df2["path_depth"])
    X, y, groups = df2[feature_cols], df2["label"], df2["group_id"]
    return evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01)


def evaluate_capped_nested(df, feature_cols):
    """Nested selection cua cap qua inner-CV, giong het cau truc
    nested_hpo_m1.py nhung chi 1 hyperparameter (cap in {2,3})."""
    outer_logo = LeaveOneGroupOut()
    n = len(df)
    oof_prob = pd.Series(np.full(n, np.nan), index=df.index)
    oof_threshold = pd.Series(np.full(n, np.nan), index=df.index)
    fold_choices = []

    y_all, groups_all = df["label"], df["group_id"]

    for train_idx, test_idx in outer_logo.split(df, y_all, groups=groups_all):
        held_out = groups_all.iloc[test_idx].iloc[0]
        outer_train = df.iloc[train_idx]
        outer_test = df.iloc[test_idx]

        inner_logo = LeaveOneGroupOut()
        y_train, g_train = outer_train["label"], outer_train["group_id"]
        candidate_scores = {}
        for cap in CAP_CANDIDATES:
            inner_oof = pd.Series(np.full(len(outer_train), np.nan), index=outer_train.index)
            for inner_tr_idx, inner_val_idx in inner_logo.split(outer_train, y_train, groups=g_train):
                inner_tr = outer_train.iloc[inner_tr_idx].copy()
                inner_val = outer_train.iloc[inner_val_idx].copy()
                inner_tr["path_depth"] = inner_tr["path_depth"].clip(upper=cap)
                inner_val["path_depth"] = inner_val["path_depth"].clip(upper=cap)
                m = M1TypedTemporalMotifModel()
                m.fit(inner_tr[feature_cols], inner_tr["label"], inner_tr["group_id"])
                inner_oof.iloc[inner_val_idx] = m.predict_proba(inner_val[feature_cols])
            valid = inner_oof.notna()
            score = pr_auc(y_train[valid].to_numpy(), inner_oof[valid].to_numpy())
            candidate_scores[cap] = score

        best_cap = max(candidate_scores, key=candidate_scores.get)
        fold_choices.append({"held_out_group": held_out, **{f"cap_{c}_inner_pr_auc": s for c, s in candidate_scores.items()}, "chosen_cap": best_cap})
        print(f"  fold={held_out:32s} inner scores={candidate_scores} -> chosen cap={best_cap}", flush=True)

        # threshold: dung lai inner-OOF cua cap thang (fit lai 1 lan nua voi cap thang de lay inner-OOF cho threshold)
        inner_oof_best = pd.Series(np.full(len(outer_train), np.nan), index=outer_train.index)
        for inner_tr_idx, inner_val_idx in inner_logo.split(outer_train, y_train, groups=g_train):
            inner_tr = outer_train.iloc[inner_tr_idx].copy()
            inner_val = outer_train.iloc[inner_val_idx].copy()
            inner_tr["path_depth"] = inner_tr["path_depth"].clip(upper=best_cap)
            inner_val["path_depth"] = inner_val["path_depth"].clip(upper=best_cap)
            m = M1TypedTemporalMotifModel()
            m.fit(inner_tr[feature_cols], inner_tr["label"], inner_tr["group_id"])
            inner_oof_best.iloc[inner_val_idx] = m.predict_proba(inner_val[feature_cols])
        valid_best = inner_oof_best.notna()
        threshold = select_threshold(y_train[valid_best].to_numpy(), inner_oof_best[valid_best].to_numpy(), target_fpr=0.01)

        final_train = outer_train.copy()
        final_test = outer_test.copy()
        final_train["path_depth"] = final_train["path_depth"].clip(upper=best_cap)
        final_test["path_depth"] = final_test["path_depth"].clip(upper=best_cap)
        final_model = M1TypedTemporalMotifModel()
        final_model.fit(final_train[feature_cols], final_train["label"], final_train["group_id"])
        prob_test = final_model.predict_proba(final_test[feature_cols])
        oof_prob.iloc[test_idx] = prob_test
        oof_threshold.iloc[test_idx] = threshold

    return {"oof_prob": oof_prob, "oof_threshold": oof_threshold, "fold_choices": fold_choices}


def report_variant(name, oof_prob, oof_threshold, df, m1_oof_official, results_summary, problem_rows_out):
    valid = oof_prob.notna()
    y = df["label"]
    groups = df["group_id"]

    ci = bootstrap_incident_level(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    print(f"\n=== {name}: pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] ===")

    per_inc_v = per_incident_metric(y[valid].to_numpy(), oof_prob[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), m1_oof_official["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    per_inc_b3 = per_incident_metric(y.to_numpy(), m1_oof_official["oof_prob_B3"].to_numpy(), groups.to_numpy(), pr_auc)

    common_m1 = sorted(set(per_inc_v) & set(per_inc_m1))
    diffs_m1 = np.array([per_inc_v[i] - per_inc_m1[i] for i in common_m1])
    mean_diff_m1, lo_m1, hi_m1 = paired_bootstrap(diffs_m1)
    print(f"{name}: Paired diff vs M1 chinh thuc = {mean_diff_m1:+.4f} [{lo_m1:+.4f}, {hi_m1:+.4f}]")

    common_b3 = sorted(set(per_inc_v) & set(per_inc_b3))
    diffs_b3 = np.array([per_inc_v[i] - per_inc_b3[i] for i in common_b3])
    mean_diff_b3, lo_b3, hi_b3 = paired_bootstrap(diffs_b3)
    print(f"{name}: Paired diff vs B3 = {mean_diff_b3:+.4f} [{lo_b3:+.4f}, {hi_b3:+.4f}]")

    print(f"\n{name}: kiem tra 2 ca da chan doan:")
    case_rows = []
    for sid in PROBLEM_CASES:
        sub = df[df["source_id"] == sid]
        for i in sub.index:
            plen = df.loc[i, "prefix_len"]
            new_prob = oof_prob.loc[i]
            old_prob = m1_oof_official.loc[i, "oof_prob_M1"] if i in m1_oof_official.index else float("nan")
            thr = oof_threshold.loc[i]
            print(f"  {sid} prefix_len={plen}: {name}_prob={new_prob:.4f} (threshold={thr:.4f}), "
                  f"M1_chinh_thuc_prob={old_prob:.4f}")
            case_rows.append({"variant": name, "source_id": sid, "prefix_len": int(plen),
                               "new_prob": float(new_prob), "old_prob_m1_official": float(old_prob),
                               "threshold": float(thr)})
    problem_rows_out.extend(case_rows)

    results_summary.append({
        "model": name, "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff_m1, "paired_ci_low_vs_m1": lo_m1, "paired_ci_high_vs_m1": hi_m1,
        "paired_diff_vs_b3": mean_diff_b3, "paired_ci_low_vs_b3": lo_b3, "paired_ci_high_vs_b3": hi_b3,
    })
    return mean_diff_m1, lo_m1, hi_m1


def run_5seed_check(df, feature_cols, transform_kind, cap=None):
    seed_results = []
    for seed in SEEDS:
        df2 = df.copy()
        if transform_kind == "log1p":
            df2["path_depth"] = np.log1p(df2["path_depth"])
        else:
            df2["path_depth"] = df2["path_depth"].clip(upper=cap)
        X, y, groups = df2[feature_cols], df2["label"], df2["group_id"]
        factory = lambda s=seed: M1TypedTemporalMotifModel(random_state=s)
        r = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
        v = r["oof_prob"].notna()
        c = bootstrap_incident_level(y[v].to_numpy(), r["oof_prob"][v].to_numpy(), groups[v].to_numpy(), pr_auc, n_boot=500)
        print(f"    seed={seed}: pooled PR-AUC = {c['point']:.4f}", flush=True)
        seed_results.append(c["point"])
    return seed_results


def main():
    df = build_base_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]

    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    m1_oof_official = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1", "oof_prob_B3"]], on=key_cols, how="left")
    m1_oof_official.index = df.index

    results_summary = []
    problem_rows = []

    print("=== (A) log1p(path_depth) ===", flush=True)
    res_log = evaluate_log1p(df, feature_cols)
    mean_diff_log, lo_log, hi_log = report_variant(
        "M1_v4_log1p", res_log["oof_prob"], res_log["oof_threshold"], df, m1_oof_official, results_summary, problem_rows,
    )

    print("\n=== (B) capped(path_depth), cap chon qua nested inner-CV ===", flush=True)
    res_cap = evaluate_capped_nested(df, feature_cols)
    pd.DataFrame(res_cap["fold_choices"]).to_csv(ROOT / "results" / "tables" / "m1_v4_capped_fold_choices_2026-09-26.csv", index=False)
    mean_diff_cap, lo_cap, hi_cap = report_variant(
        "M1_v4_capped", res_cap["oof_prob"], res_cap["oof_threshold"], df, m1_oof_official, results_summary, problem_rows,
    )

    pd.DataFrame(results_summary).to_csv(OUT_CSV, index=False)
    pd.DataFrame(problem_rows).to_csv(ROOT / "results" / "tables" / "m1_v4_problem_cases_2026-09-26.csv", index=False)

    seed_check_notes = []
    if lo_log > 0:
        print("\n=== log1p cai thien CI loai 0 - kiem tra 5 seed ===", flush=True)
        seeds_log = run_5seed_check(df, feature_cols, "log1p")
        seed_check_notes.append(f"log1p 5-seed: mean={np.mean(seeds_log):.4f} std={np.std(seeds_log):.4f} values={seeds_log}")
    if lo_cap > 0:
        print("\n=== capped cai thien CI loai 0 - kiem tra 5 seed (dung cap pho bien nhat qua cac fold) ===", flush=True)
        chosen_caps = [fc["chosen_cap"] for fc in res_cap["fold_choices"]]
        most_common_cap = max(set(chosen_caps), key=chosen_caps.count)
        print(f"  cap pho bien nhat qua 15 fold: {most_common_cap} (dung co dinh cho 5-seed check)")
        seeds_cap = run_5seed_check(df, feature_cols, "capped", cap=most_common_cap)
        seed_check_notes.append(f"capped(cap={most_common_cap}) 5-seed: mean={np.mean(seeds_cap):.4f} std={np.std(seeds_cap):.4f} values={seeds_cap}")

    verdict_log = "CAI THIEN CO Y NGHIA THONG KE" if lo_log > 0 else "KHONG CAI THIEN CO Y NGHIA THONG KE"
    verdict_cap = "CAI THIEN CO Y NGHIA THONG KE" if lo_cap > 0 else "KHONG CAI THIEN CO Y NGHIA THONG KE"
    print(f"\n=== KET LUAN ===\nlog1p: {verdict_log}\ncapped: {verdict_cap}")

    md = [
        "# M1_v4 - THAY THE path_depth bang ban bien doi (Attempt #10, 2026-09-26)\n",
        "\n2 phuong an: (A) log1p(path_depth) khong hyperparameter; (B) capped=min(path_depth,cap), "
        "cap chon qua nested inner-CV moi outer fold (co the khac nhau giua cac fold).\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI | Diff vs M1 | CI vs M1 | Diff vs B3 | CI vs B3 |\n|---|---|---|---|---|---|---|\n",
    ]
    for r in results_summary:
        md.append(f"| {r['model']} | {r['mean_pr_auc']:.4f} | [{r['ci_low_95']:.4f}, {r['ci_high_95']:.4f}] | "
                   f"{r['paired_diff_vs_m1']:+.4f} | [{r['paired_ci_low_vs_m1']:+.4f}, {r['paired_ci_high_vs_m1']:+.4f}] | "
                   f"{r['paired_diff_vs_b3']:+.4f} | [{r['paired_ci_low_vs_b3']:+.4f}, {r['paired_ci_high_vs_b3']:+.4f}] |\n")
    md.append("\n## Kiem tra dung 2 ca da chan doan\n\n| Variant | source_id | prefix_len | prob moi | prob M1 chinh thuc | threshold |\n|---|---|---|---|---|---|\n")
    for r in problem_rows:
        md.append(f"| {r['variant']} | {r['source_id']} | {r['prefix_len']} | {r['new_prob']:.4f} | "
                   f"{r['old_prob_m1_official']:.4f} | {r['threshold']:.4f} |\n")
    md.append(f"\n## KET LUAN\n\nlog1p: {verdict_log}\n\ncapped: {verdict_cap}\n\n" + "\n".join(seed_check_notes) + "\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
