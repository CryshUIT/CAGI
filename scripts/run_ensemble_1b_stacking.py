"""NSS 2026 - Nang cap M1 (lan thu 4), Viec 1b: stacking M1 + T13 LogReg,
meta-learner (LogisticRegression) hoc trong so ket hop CHI tren inner-CV.

Thiet ke nested DUNG NGHIA (khong bao gio dung outer test de quyet dinh gi):
  Voi MOI outer fold (15 fold, giu 1 incident lam test):
    1. Inner LOGO tren 14 incident con lai -> inner-OOF cho CA M1 va T13
       (predict_proba tu model fit tren 13 incident inner-train).
    2. Fit meta-learner (LogisticRegression 2 feature: [prob_M1, prob_T13])
       TREN inner-OOF (~1600+ dong, 14 incident) - CHI o day meta-learner
       hoc trong so.
    3. Chon threshold tren chinh inner-OOF da qua meta-learner (khong dung
       outer test).
    4. Fit M1, T13 CUOI CUNG tren TOAN BO outer-train (14 incident), du doan
       outer test -> ap dung meta-learner (da fit o buoc 2, KHONG fit lai)
       de ket hop thanh xac suat cuoi cung cho outer test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut

from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, select_threshold, per_incident_metric  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel, T13LogisticRegressionM1Features  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OUT_TABLE = ROOT / "results" / "tables" / "ensemble_1b_stacking_2026-09-22.csv"
OUT_FOLD_TABLE = ROOT / "results" / "tables" / "ensemble_1b_stacking_folds_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "ensemble_1b_stacking_2026-09-22.md"


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
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    outer_logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    fold_rows = []

    for fold_i, (train_idx, test_idx) in enumerate(outer_logo.split(X, y, groups=groups), start=1):
        held_out = groups.iloc[test_idx].iloc[0]
        X_train, y_train, g_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

        inner_logo = LeaveOneGroupOut()
        inner_oof_m1 = np.full(len(y_train), np.nan)
        inner_oof_t13 = np.full(len(y_train), np.nan)
        for inner_tr_idx, inner_val_idx in inner_logo.split(X_train, y_train, groups=g_train):
            m1 = M1TypedTemporalMotifModel()
            m1.fit(X_train.iloc[inner_tr_idx], y_train.iloc[inner_tr_idx], g_train.iloc[inner_tr_idx])
            inner_oof_m1[inner_val_idx] = m1.predict_proba(X_train.iloc[inner_val_idx])
            t13 = T13LogisticRegressionM1Features()
            t13.fit(X_train.iloc[inner_tr_idx], y_train.iloc[inner_tr_idx], g_train.iloc[inner_tr_idx])
            inner_oof_t13[inner_val_idx] = t13.predict_proba(X_train.iloc[inner_val_idx])

        valid = ~np.isnan(inner_oof_m1) & ~np.isnan(inner_oof_t13)
        meta_X = np.column_stack([inner_oof_m1[valid], inner_oof_t13[valid]])
        meta_y = y_train.to_numpy()[valid]
        meta = LogisticRegression(class_weight="balanced", random_state=42)
        meta.fit(meta_X, meta_y)

        meta_inner_prob = meta.predict_proba(meta_X)[:, 1]
        threshold = select_threshold(meta_y, meta_inner_prob, target_fpr=0.01)

        final_m1 = M1TypedTemporalMotifModel()
        final_m1.fit(X_train, y_train, g_train)
        prob_m1_test = final_m1.predict_proba(X_test)
        final_t13 = T13LogisticRegressionM1Features()
        final_t13.fit(X_train, y_train, g_train)
        prob_t13_test = final_t13.predict_proba(X_test)

        meta_test_X = np.column_stack([prob_m1_test, prob_t13_test])
        prob_ensemble_test = meta.predict_proba(meta_test_X)[:, 1]
        oof_prob[test_idx] = prob_ensemble_test

        y_test_arr = y_test.to_numpy()
        fold_rows.append({
            "held_out_group": held_out, "n_val_rows": len(test_idx),
            "meta_coef_m1": meta.coef_[0][0], "meta_coef_t13": meta.coef_[0][1], "meta_intercept": meta.intercept_[0],
            "threshold": threshold, "pr_auc": pr_auc(y_test_arr, prob_ensemble_test),
        })
        print(f"[{fold_i}/15] held_out={held_out:32s} meta_coef=[M1={meta.coef_[0][0]:+.3f}, "
              f"T13={meta.coef_[0][1]:+.3f}] pr_auc_outer={pr_auc(y_test_arr, prob_ensemble_test):.4f}", flush=True)

    valid_all = ~np.isnan(oof_prob)
    ci = bootstrap_incident_level(y.to_numpy()[valid_all], oof_prob[valid_all], groups.to_numpy()[valid_all], pr_auc, n_boot=2000)
    print(f"\nStacking pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    per_inc_stack = per_incident_metric(y.to_numpy()[valid_all], oof_prob[valid_all], groups.to_numpy()[valid_all], pr_auc)
    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    common = sorted(set(per_inc_stack) & set(per_inc_m1))
    diffs = np.array([per_inc_stack[i] - per_inc_m1[i] for i in common])
    mean_diff, lo, hi = paired_bootstrap(diffs)
    print(f"Paired diff (Stacking - M1 goc) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}]")

    if lo > 0:
        verdict = "CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed truoc khi tin day la that."
    else:
        verdict = "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc. DUNG o day, khong thu bien the khac."
    print(f"\n=== KET LUAN ===\n{verdict}")

    pd.DataFrame(fold_rows).to_csv(OUT_FOLD_TABLE, index=False)
    pd.DataFrame([{
        "model": "ensemble_1b_stacking", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff, "paired_ci_low": lo, "paired_ci_high": hi,
    }]).to_csv(OUT_TABLE, index=False)

    md = [
        "# Ensemble 1b - Stacking M1 + T13 LogReg (2026-09-22)\n",
        "\nMeta-learner (LogisticRegression) hoc trong so ket hop [prob_M1, prob_T13] CHI tren inner-CV "
        "(14 incident/outer-train), fit lai model goc tren toan bo outer-train, ap dung meta-learner "
        "DA HOC (khong fit lai) len outer test.\n",
        "\n| Model | Mean PR-AUC | 95% CI |\n|---|---|---|\n",
        "| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |\n",
        f"| **Stacking (meta-learner)** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (Stacking - M1 goc) = {mean_diff:+.4f}, 95% CI = [{lo:+.4f}, {hi:+.4f}]**\n",
        "\n## He so meta-learner qua tung outer fold (co the khac nhau - dung chuan nested)\n",
        "\n| Incident giu lai | coef M1 | coef T13 | intercept | PR-AUC outer |\n|---|---|---|---|---|\n",
    ]
    for r in fold_rows:
        md.append(f"| {r['held_out_group']} | {r['meta_coef_m1']:+.3f} | {r['meta_coef_t13']:+.3f} | {r['meta_intercept']:+.3f} | {r['pr_auc']:.4f} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_FOLD_TABLE}, {OUT_MD}")


if __name__ == "__main__":
    main()
