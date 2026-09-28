"""NSS 2026 - Viec 3 (T13): them 1 baseline "sequence/don gian hon" de tra
loi cau hoi phan bien "sao khong dung sequence model".

QUYET DINH HUONG (bao cao ly do): chon (b) Logistic Regression tren DUNG
feature vector cua M1 (T13LogisticRegressionM1Features, src/models/baselines.py),
KHONG chon (a) GRU/CNN 1D tren chuoi hanh dong tho, vi:
  1. Chi co 15 incident (leave-one-incident-out => outer fold train tren
     14 incident) - qua nho de huan luyen mot mang neural sequence dang tin
     cay; ket qua nhieu kha nang khong on dinh/kho dien giai, rui ro cao hon
     loi ich trong thoi gian con lai truoc deadline 25/9.
  2. Can code moi dang ke: bo nap chuoi tho, encode categorical (event_type/
     token), padding/mask, vong lap train rieng cho neural net - nguy co bug
     trien khai duoi ap luc deadline cao hon.
  3. Logistic Regression tren feature vector cua M1 van la cau tra loi hop
     le cho chinh cau hoi "co can cay quyet dinh/boosting khong hay linear
     da du" - dung CHINH XAC cung feature representation, cung leave-one-
     incident-out, cung bootstrap CI muc incident nhu moi model khac trong
     du an - so sanh cong bang, chi phi trien khai/tinh toan thap, it rui ro.

Dung DUNG pipeline RQ1 (dedupe_pooled_prefixes + evaluate_model_nested +
bootstrap_incident_level + paired bootstrap/Wilcoxon vs M1) - KHONG danh gia
theo protocol khac.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.evaluation.metrics import pr_auc
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric
from src.models.baselines import T13LogisticRegressionM1Features

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OOF_M1_FULL_PATH = REPO_ROOT / "data" / "processed" / "oof_predictions_v1.csv"
OUT_TABLE = REPO_ROOT / "results" / "tables" / "t13_logreg_baseline_2026-09-22.csv"
OUT_MD = REPO_ROOT / "results" / "reports" / "t13_logreg_baseline_2026-09-22.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([rng.choice(diffs, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main() -> None:
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    y, groups = df["label"], df["group_id"]

    oof_full_df = pd.read_csv(OOF_M1_FULL_PATH)
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    assert merged_check["oof_prob_M1"].notna().all() and len(merged_check) == len(df), \
        "M1 OOF khong khop 1-1 voi dataset dedupe - PHAI train lai"
    df = df.merge(oof_full_df[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    m1_per_inc = per_incident_metric(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    m1_ci = bootstrap_incident_level(y.to_numpy(), df["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)
    print(f"M1 (tai su dung OOF): mean={m1_ci['point']:.4f} [{m1_ci['ci_low']:.4f}, {m1_ci['ci_high']:.4f}]")

    print("\n=== T13 (LogReg tren feature vector M1): nested leave-one-incident-out ===", flush=True)
    X = df[feature_cols]
    result = evaluate_model_nested(T13LogisticRegressionM1Features, X, y, groups, target_fpr=0.01)
    oof = result["oof_prob"]
    for r in result["fold_rows"]:
        print(f"  held_out={r['held_out_group']:32s} pr_auc={r['pr_auc']:.4f}", flush=True)

    valid = oof.notna()
    t13_ci = bootstrap_incident_level(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=2000)
    t13_per_inc = per_incident_metric(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc)

    common = sorted(set(t13_per_inc) & set(m1_per_inc))
    t13_scores = np.array([t13_per_inc[i] for i in common])
    m1_scores = np.array([m1_per_inc[i] for i in common])
    diffs = t13_scores - m1_scores  # T13 - M1
    mean_diff, lo, hi = paired_bootstrap(diffs)
    try:
        w_stat, w_p = wilcoxon(t13_scores, m1_scores)
    except ValueError:
        w_stat, w_p = float("nan"), float("nan")

    print(f"\nT13 mean PR-AUC (pooled) = {t13_ci['point']:.4f} [{t13_ci['ci_low']:.4f}, {t13_ci['ci_high']:.4f}]")
    print(f"Paired diff (T13 - M1) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}], Wilcoxon stat={w_stat}, p={w_p}")

    ci_excludes_zero = (lo > 0) or (hi < 0)
    if ci_excludes_zero and mean_diff > 0:
        verdict = "T13 (linear) VUOT M1 (boosting) co y nghia thong ke tren cung feature vector."
    elif ci_excludes_zero and mean_diff < 0:
        verdict = "M1 (boosting) VUOT T13 (linear) co y nghia thong ke tren cung feature vector — can cay quyet dinh/tuong tac phi tuyen."
    else:
        verdict = "KHONG DU BANG CHUNG: 95% CI cua hieu so (T13 - M1) chua 0 — khong the ket luan linear hay boosting tot hon co y nghia thong ke voi 15 incident hien tai."
    print(f"\n=== KET LUAN T13 ===\n{verdict}")

    rows = [
        {"model": "M1", "mean_pr_auc": m1_ci["point"], "ci_low_95": m1_ci["ci_low"], "ci_high_95": m1_ci["ci_high"], "n_features": len(feature_cols)},
        {"model": "T13_logreg_m1_features", "mean_pr_auc": t13_ci["point"], "ci_low_95": t13_ci["ci_low"],
         "ci_high_95": t13_ci["ci_high"], "n_features": len(feature_cols)},
    ]
    pd.DataFrame(rows).to_csv(OUT_TABLE, index=False)

    md = [
        "# T13 - Logistic Regression tren feature vector cua M1 (chay 2026-09-22)\n",
        "\n## Ly do chon huong (b) thay vi (a) GRU/CNN 1D\n",
        "\n1. Chi 15 incident, leave-one-incident-out => outer train toi da 14 incident - "
        "qua nho de huan luyen sequence model dang tin cay trong thoi gian con lai.\n",
        "2. GRU/CNN can code moi dang ke (encode categorical, padding/mask, training loop rieng) "
        "- rui ro trien khai duoi ap luc deadline cao hon loi ich.\n",
        "3. Logistic Regression tren DUNG feature vector M1 van tra loi dung cau hoi phan bien "
        "(\"can cay quyet dinh/boosting khong hay linear da du\") voi chi phi/rui ro thap hon, "
        "danh gia cong bang bang CUNG protocol (leave-one-incident-out, bootstrap CI muc incident).\n",
        "\n## Ket qua\n",
        f"\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n"
        f"| M1 (XGBoost) | {m1_ci['point']:.4f} | [{m1_ci['ci_low']:.4f}, {m1_ci['ci_high']:.4f}] |\n"
        f"| T13 (LogReg, cung feature) | {t13_ci['point']:.4f} | [{t13_ci['ci_low']:.4f}, {t13_ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (T13 - M1) = {mean_diff:+.4f}, 95% bootstrap CI (muc incident) = [{lo:+.4f}, {hi:+.4f}]**\n",
        f"\nWilcoxon signed-rank: statistic={w_stat}, p-value={w_p}\n",
        "\n| Incident | T13 | M1 | Diff |\n|---|---|---|---|\n",
    ]
    for inc, t, m, d in zip(common, t13_scores, m1_scores, diffs):
        md.append(f"| {inc} | {t:.4f} | {m:.4f} | {d:+.4f} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE} va {OUT_MD}")


if __name__ == "__main__":
    main()
