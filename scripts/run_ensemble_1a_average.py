"""NSS 2026 - Nang cap M1 (lan thu 4), Viec 1a: ensemble trung binh don gian
2 xac suat da hieu chinh (M1 + T13 LogReg), dung PLATT scaling - phuong
phap calibration DA CHOT chinh thuc cho M1 o N=15 (results/reports/
calibration_v1.md: "Method tot nhat theo ECE: platt", ECE=0.0106).

Tai su dung TRUC TIEP evaluate_model_nested(calibration="platt") - calibrator
fit TREN INNER-TRAIN OOF (khong bao gio dung outer test), giong het co che
da dung cho run_calibration.py - khong viet lai logic calibration.

Trong so ensemble CO DINH 0.5/0.5 (khong hoc/chon tren du lieu nao) - khong
co rui ro leakage o buoc nay (chi Viec 1b - stacking - moi can hoc trong so).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel, T13LogisticRegressionM1Features  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OUT_TABLE = ROOT / "results" / "tables" / "ensemble_1a_average_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "ensemble_1a_average_2026-09-22.md"


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

    print("=== M1 (calibration=platt) ===", flush=True)
    res_m1 = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01, calibration="platt")
    print("=== T13 LogReg (calibration=platt) ===", flush=True)
    res_t13 = evaluate_model_nested(T13LogisticRegressionM1Features, X, y, groups, target_fpr=0.01, calibration="platt")

    cal_m1 = res_m1["oof_prob_calibrated"]
    cal_t13 = res_t13["oof_prob_calibrated"]
    valid = cal_m1.notna() & cal_t13.notna()
    print(f"n dong valid ca 2 model calibrate duoc: {valid.sum()}/{len(df)}")

    ensemble_prob = (cal_m1[valid] + cal_t13[valid]) / 2.0
    y_v, g_v = y[valid].to_numpy(), groups[valid].to_numpy()

    ci_ens = bootstrap_incident_level(y_v, ensemble_prob.to_numpy(), g_v, pr_auc, n_boot=2000)
    ci_m1_raw = bootstrap_incident_level(y.to_numpy(), res_m1["oof_prob"].to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)
    ci_t13_raw = bootstrap_incident_level(y.to_numpy(), res_t13["oof_prob"].to_numpy(), groups.to_numpy(), pr_auc, n_boot=2000)

    print(f"\nM1 goc (raw, khong calibrate) = {ci_m1_raw['point']:.4f} [{ci_m1_raw['ci_low']:.4f}, {ci_m1_raw['ci_high']:.4f}] (moc chinh thuc: 0.6624)")
    print(f"T13 goc (raw) = {ci_t13_raw['point']:.4f} [{ci_t13_raw['ci_low']:.4f}, {ci_t13_raw['ci_high']:.4f}] (moc T13 chinh thuc: 0.7548)")
    print(f"Ensemble trung binh (ca 2 da calibrate platt) = {ci_ens['point']:.4f} [{ci_ens['ci_low']:.4f}, {ci_ens['ci_high']:.4f}]")

    # paired vs M1 goc (per-incident, tren dung tap dong valid)
    per_inc_ens = per_incident_metric(y_v, ensemble_prob.to_numpy(), g_v, pr_auc)
    per_inc_m1 = per_incident_metric(y.to_numpy(), res_m1["oof_prob"].to_numpy(), groups.to_numpy(), pr_auc)
    common = sorted(set(per_inc_ens) & set(per_inc_m1))
    diffs = np.array([per_inc_ens[i] - per_inc_m1[i] for i in common])
    mean_diff, lo, hi = paired_bootstrap(diffs)
    print(f"\nPaired diff (Ensemble - M1 goc) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}]")

    ci_excludes_zero_positive = lo > 0
    if ci_excludes_zero_positive:
        verdict = "CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed (T12-style) truoc khi tin day la that."
    else:
        verdict = "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc (95% CI hieu so chua 0). DUNG o day, khong thu bien the khac."
    print(f"\n=== KET LUAN ===\n{verdict}")

    pd.DataFrame([{
        "model": "ensemble_1a_average", "mean_pr_auc": ci_ens["point"], "ci_low_95": ci_ens["ci_low"], "ci_high_95": ci_ens["ci_high"],
        "paired_diff_vs_m1": mean_diff, "paired_ci_low": lo, "paired_ci_high": hi,
    }]).to_csv(OUT_TABLE, index=False)

    md = [
        "# Ensemble 1a - trung binh calibrate (Platt) M1 + T13 LogReg (2026-09-22)\n",
        "\nGia thuyet: M1 (XGBoost) va T13 (LogReg tren cung feature) co the bat tin hieu khac nhau, "
        "trung binh co nguyen tac (Platt calibration, trong so co dinh 0.5/0.5) co the giam phuong sai.\n",
        "\n| Model | Mean PR-AUC | 95% CI |\n|---|---|---|\n",
        f"| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |\n",
        f"| T13 goc (moc, da co) | 0.7548 | [0.6459, 0.8980] |\n",
        f"| **Ensemble 1a (trung binh Platt)** | **{ci_ens['point']:.4f}** | [{ci_ens['ci_low']:.4f}, {ci_ens['ci_high']:.4f}] |\n",
        f"\n**Paired diff (Ensemble - M1 goc) = {mean_diff:+.4f}, 95% CI = [{lo:+.4f}, {hi:+.4f}]**\n",
        f"\n## KET LUAN\n\n{verdict}\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_MD}")


if __name__ == "__main__":
    main()
