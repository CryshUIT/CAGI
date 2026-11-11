"""EXPLORATORY / post-hoc - trich xuat reliability bins cho ca 3 phuong
phap (raw/isotonic/platt) tu CHINH logic da dung trong
run_calibration_N30.py (evaluate_model_nested + expected_calibration_error),
CHI them buoc LUU bin_stats ra CSV (ban goc khong luu, chi in ECE tong).
Logic tinh ECE/Brier/bin GIU NGUYEN TUYET DOI (copy ham tu run_calibration_N30.py,
khong doi 1 dong) - chi them phan ghi CSV + kiem tra khop lai.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.nested_eval import dedupe_pooled_prefixes, evaluate_model_nested  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
OUT_CSV = ROOT / "results" / "tables" / "extra_N30_calibration_bins.csv"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

# Gia tri ECE da bao cao truoc (tu run_calibration_N30.py), dung de doi chieu
EXPECTED_ECE = {"raw": 0.0251, "isotonic": 0.0145, "platt": 0.0136}


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10):
    """Chia DEU theo xac suat (10 bin rong 0.1, KHONG phai theo quantile) -
    CHINH XAC nhu run_calibration_N30.py, khong doi."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    bin_stats = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi) if hi < 1.0 else (y_prob >= lo) & (y_prob <= hi)
        if mask.sum() == 0:
            bin_stats.append((lo, hi, 0, np.nan, np.nan))
            continue
        acc = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(acc - conf)
        bin_stats.append((lo, hi, int(mask.sum()), float(acc), float(conf)))
    return float(ece), bin_stats


def main():
    check_m1_gate()
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X = df[feature_cols]
    y = df["label"]
    groups = df["group_id"]
    print(f"Dataset N30 (dedupe pooled): {len(df)} dong", flush=True)

    rows = []
    recomputed_ece = {}
    for method in [None, "isotonic", "platt"]:
        label = "raw" if method is None else method
        print(f"\n=== evaluate_model_nested calibration={method} ===", flush=True)
        result = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01, calibration=method)
        prob_col = "oof_prob" if method is None else "oof_prob_calibrated"
        prob = result[prob_col]
        valid = prob.notna()
        y_valid = y[valid].to_numpy()
        p_valid = prob[valid].to_numpy()
        ece, bin_stats = expected_calibration_error(y_valid, p_valid, n_bins=10)
        recomputed_ece[label] = ece
        print(f"  ECE tinh lai = {ece:.4f} (da bao cao truoc: {EXPECTED_ECE[label]})", flush=True)
        for i, (lo, hi, n, acc, conf) in enumerate(bin_stats):
            rows.append({"method": label, "bin": i, "bin_range": f"[{lo:.1f},{hi:.1f}{']' if hi==1.0 else ')'}",
                         "n": n, "mean_pred": conf, "frac_pos": acc})

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}")
    print(out.to_string(index=False))

    print("\n=== Doi chieu ECE tinh lai tu bin vs ECE da bao cao ===")
    all_match = True
    for label, expected in EXPECTED_ECE.items():
        got = recomputed_ece[label]
        match = abs(got - expected) < 1e-4
        all_match = all_match and match
        print(f"  {label}: tinh lai={got:.6f} da bao cao={expected} khop={match}")
    print(f"\nTAT CA KHOP: {all_match}")


if __name__ == "__main__":
    main()
