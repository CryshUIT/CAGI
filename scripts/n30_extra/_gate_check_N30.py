"""EXPLORATORY / post-hoc (ngoai analysis_plan_N30_v3.md) - cong kiem tra
dung chung cho moi script trong scripts/n30_extra/: M1 pooled PR-AUC tren
results/oof/oof_M1.parquet phai khop 0.7762 (sai so < 1e-4). Khong khop ->
raise, DUNG lai, khong tu sua.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_M1_POOLED_PRAUC = 0.7762
TOLERANCE = 1e-4


def check_m1_gate() -> float:
    oof = pd.read_parquet(ROOT / "results" / "oof" / "oof_M1.parquet")
    pr_auc = average_precision_score(oof["y_true"], oof["score"])
    if abs(pr_auc - EXPECTED_M1_POOLED_PRAUC) >= TOLERANCE:
        raise RuntimeError(
            f"CONG KIEM TRA KHONG KHOP: M1 pooled PR-AUC = {pr_auc:.6f}, "
            f"ky vong {EXPECTED_M1_POOLED_PRAUC} (+/- {TOLERANCE}). DUNG."
        )
    print(f"[gate OK] M1 pooled PR-AUC (results/oof/oof_M1.parquet) = {pr_auc:.6f} ~ 0.7762", flush=True)
    return pr_auc


if __name__ == "__main__":
    check_m1_gate()
