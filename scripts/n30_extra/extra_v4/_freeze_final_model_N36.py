# -*- coding: utf-8 -*-
"""Dong bang mo hinh CUOI (final held-out cho incident HOAN TOAN MOI sau
nay) - theo yeu cau nguoi dung 2026-11-05:
"Dong bang mo hinh train tren toan bo N hop le hien co (36 incident), luu
hash, sieu tham so, theta, seed. Khong train lai sau buoc nay."

Train = TOAN BO features_v2_N37.parquet (30 cu + 6 moi, da dedupe prefix),
KHONG LOIO, KHONG het-out gi - day la fit CUOI CUNG, se dung predict_proba
tren incident HOAN TOAN MOI (chua ton tai) sau khi danh sach do duoc chot.

theta chon qua CUNG co che da dung xuyen suot du an: inner leave-one-group-out
tren toan bo 36 group de sinh OOF, select_threshold(target_fpr=0.01) tren
OOF do - CHINH LA theta se dung CO DINH cho moi test sau nay, KHONG doi.
"""
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
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N37.parquet"
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TARGET_FPR = 0.01
SEED = 42

OUT_DIR = ROOT / "results" / "reports" / "extra_v4"
OUT_MODEL = OUT_DIR / "M1_FROZEN_final_N36.pkl"
OUT_CALIBRATOR = OUT_DIR / "M1_FROZEN_final_N36_platt_calibrator.pkl"
OUT_META = OUT_DIR / "M1_FROZEN_final_N36_metadata.json"


def main():
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    n_groups = groups.nunique()
    print(f"Train (toan bo, khong het-out): {len(df)} dong, {n_groups} group (ky vong 36)", flush=True)
    assert n_groups == 36, f"Ky vong dung 36 group, co {n_groups}"

    print("\n=== Chon theta CO DINH qua inner-LOGO tren toan bo 36 group ===", flush=True)
    logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    y_arr = y.to_numpy()
    for i, (tr_idx, val_idx) in enumerate(logo.split(X, y, groups=groups)):
        m = M1TypedTemporalMotifModel()
        m.fit(X.iloc[tr_idx], y.iloc[tr_idx], groups.iloc[tr_idx])
        oof_prob[val_idx] = m.predict_proba(X.iloc[val_idx])
        if (i + 1) % 6 == 0:
            print(f"  ... {i + 1}/{n_groups} fold xong", flush=True)
    valid = ~np.isnan(oof_prob)
    theta_frozen = select_threshold(y_arr[valid], oof_prob[valid], target_fpr=TARGET_FPR)
    print(f"theta_frozen (target_fpr={TARGET_FPR}) = {theta_frozen:.6f}", flush=True)

    print("\n=== Fit Platt calibrator tren CUNG OOF (de co prob_calibrated khi test incident moi) ===", flush=True)
    calibrator = _fit_calibrator(y_arr[valid], oof_prob[valid], "platt")

    print("\n=== Fit model CUOI CUNG tren TOAN BO 36 group (KHONG het-out) ===", flush=True)
    final_model = M1TypedTemporalMotifModel()
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
        "model_name": "M1_typed_temporal_motif_xgboost",
        "hyperparameters_fixed": dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=SEED, eval_metric="logloss"),
        "seed": SEED,
        "target_fpr_for_theta_selection": TARGET_FPR,
        "theta_frozen": theta_frozen,
        "calibration_method": "platt",
        "train_source": "features_v2_N37.parquet (dedupe_pooled_prefixes), TOAN BO 36 group, khong het-out",
        "train_features_file_sha256": features_hash,
        "n_train_rows": int(len(df)),
        "n_train_groups": int(n_groups),
        "n_feature_columns": len(feature_cols),
        "feature_columns": sorted(feature_cols),
        "model_pickle_sha256": model_hash,
        "note": "KHONG TRAIN LAI SAU THOI DIEM NAY. theta_frozen va calibrator CO DINH cho final held-out test tren incident hoan toan moi (xem yeu cau nguoi dung 2026-11-05).",
    }
    OUT_META.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDa luu {OUT_MODEL}", flush=True)
    print(f"Da luu {OUT_CALIBRATOR}", flush=True)
    print(f"Da luu {OUT_META}", flush=True)
    print(f"\ntheta_frozen = {theta_frozen:.6f}", flush=True)
    print(f"train_features_file_sha256 = {features_hash}", flush=True)
    print(f"model_pickle_sha256 = {model_hash}", flush=True)


if __name__ == "__main__":
    main()
