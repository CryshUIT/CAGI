# -*- coding: utf-8 -*-
"""Dong bang B3' (XGBFixedColumns tren FLAT_UNTYPED_FEATURES) tren toan bo
36 group - CUNG co che da dung cho M1 (_freeze_final_model_N36.py)."""
from __future__ import annotations

import hashlib
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.model_selection import LeaveOneGroupOut  # noqa: E402

from src.evaluation.nested_eval import _fit_calibrator, dedupe_pooled_prefixes, select_threshold  # noqa: E402
from src.models.baselines import B3FlatGraphRandomForest  # noqa: E402

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N37.parquet"
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TARGET_FPR = 0.01
SEED = 42
M1_XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=SEED, eval_metric="logloss")
B3_FLAT_COLS = list(B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES)

OUT_DIR = ROOT / "results" / "reports" / "extra_v4"
OUT_MODEL = OUT_DIR / "B3prime_FROZEN_final_N36.pkl"
OUT_CALIBRATOR = OUT_DIR / "B3prime_FROZEN_final_N36_platt_calibrator.pkl"
OUT_META = OUT_DIR / "B3prime_FROZEN_final_N36_metadata.json"


class XGBFixedColumns:
    def __init__(self, name: str, columns: list) -> None:
        self.name = name
        self.columns = columns
        self.feature_cols_: list = []

    def fit(self, X_train, y_train, groups_train=None):
        self.feature_cols_ = [c for c in self.columns if c in X_train.columns]
        y_arr = np.asarray(y_train)
        n_pos, n_neg = int((y_arr == 1).sum()), int((y_arr == 0).sum())
        spw = (n_neg / n_pos) if n_pos > 0 else 1.0
        params = dict(M1_XGB_PARAMS)
        params["scale_pos_weight"] = spw
        if _HAS_XGBOOST:
            self.model = XGBClassifier(**params)
        else:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=SEED, class_weight="balanced")
        self.model.fit(X_train[self.feature_cols_], y_train)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.feature_cols_])[:, 1]


def main():
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    n_groups = groups.nunique()
    print(f"Train (toan bo, khong het-out): {len(df)} dong, {n_groups} group (ky vong 36)", flush=True)
    assert n_groups == 36

    print("\n=== Chon theta CO DINH qua inner-LOGO tren toan bo 36 group (B3') ===", flush=True)
    logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    y_arr = y.to_numpy()
    for i, (tr_idx, val_idx) in enumerate(logo.split(X, y, groups=groups)):
        m = XGBFixedColumns("B3prime", B3_FLAT_COLS)
        m.fit(X.iloc[tr_idx], y.iloc[tr_idx], groups.iloc[tr_idx])
        oof_prob[val_idx] = m.predict_proba(X.iloc[val_idx])
        if (i + 1) % 6 == 0:
            print(f"  ... {i + 1}/{n_groups} fold xong", flush=True)
    valid = ~np.isnan(oof_prob)
    theta_frozen = select_threshold(y_arr[valid], oof_prob[valid], target_fpr=TARGET_FPR)
    print(f"theta_frozen B3' (target_fpr={TARGET_FPR}) = {theta_frozen:.6f}", flush=True)

    calibrator = _fit_calibrator(y_arr[valid], oof_prob[valid], "platt")

    print("\n=== Fit model CUOI CUNG tren TOAN BO 36 group (KHONG het-out) ===", flush=True)
    final_model = XGBFixedColumns("B3prime", B3_FLAT_COLS)
    final_model.fit(X, y, groups)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_MODEL, "wb") as f:
        pickle.dump(final_model, f)
    with open(OUT_CALIBRATOR, "wb") as f:
        pickle.dump(calibrator, f)

    features_hash = hashlib.sha256(FEATURES_PATH.read_bytes()).hexdigest()
    model_hash = hashlib.sha256(OUT_MODEL.read_bytes()).hexdigest()
    metadata = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": "B3prime_flat_untyped_xgboost",
        "hyperparameters_fixed": dict(M1_XGB_PARAMS),
        "feature_columns_fixed_14": B3_FLAT_COLS,
        "seed": SEED,
        "target_fpr_for_theta_selection": TARGET_FPR,
        "theta_frozen": theta_frozen,
        "calibration_method": "platt",
        "train_source": "features_v2_N37.parquet (dedupe_pooled_prefixes), TOAN BO 36 group, khong het-out",
        "train_features_file_sha256": features_hash,
        "n_train_rows": int(len(df)),
        "n_train_groups": int(n_groups),
        "model_pickle_sha256": model_hash,
        "note": "KHONG TRAIN LAI SAU THOI DIEM NAY.",
    }
    OUT_META.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDa luu {OUT_MODEL}, {OUT_CALIBRATOR}, {OUT_META}", flush=True)
    print(f"theta_frozen_B3prime = {theta_frozen:.6f}", flush=True)


if __name__ == "__main__":
    main()
