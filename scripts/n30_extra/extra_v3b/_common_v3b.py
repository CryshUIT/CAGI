"""EXPLORATORY / post-hoc (nhom v3b: learning curve, leave-one-chain-out,
time-split) - module dung chung, tai su dung CHINH XAC cac lop/ham da co
trong scripts/run_extra_N30_exploratory.py (B3', XGBFixedColumns,
M1_XGB_PARAMS) va src/evaluation/nested_eval.py. KHONG doi logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import dedupe_pooled_prefixes, per_incident_metric  # noqa: E402
from src.models.baselines import B3FlatGraphRandomForest, M1TypedTemporalMotifModel  # noqa: E402

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

B3_FLAT_COLS = list(B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES)  # 14 cot, dung DUNG nhu addendum 2
M1_XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42, eval_metric="logloss")


class XGBFixedColumns:
    """B3' - COPY NGUYEN VEN tu scripts/run_extra_N30_exploratory.py: cung
    learner/hyperparam XGBoost cua M1, tren 14 cot flat-untyped CO DINH
    cua B3 (KHONG tu chon cot nhu M1._candidate_columns)."""

    def __init__(self, name: str, columns: list[str]) -> None:
        self.name = name
        self.columns = columns
        self.feature_cols_: list[str] = []

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
            self.model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, class_weight="balanced")
        self.model.fit(X_train[self.feature_cols_], y_train)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.feature_cols_])[:, 1]


def make_b3prime_factory():
    return lambda: XGBFixedColumns("B3prime", B3_FLAT_COLS)


def load_dataset():
    """Chay cong kiem tra (M1 pooled = 0.7762) truoc, roi tra ve dataset
    da dedupe + bang chain/label cho tung incident."""
    check_m1_gate()
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    reg = pd.read_csv(REGISTRY_PATH)
    chain_map = reg.set_index("incident_id")["chain_primary"].to_dict()
    return df, chain_map


def fit_predict(factory, X_train, y_train, g_train, X_test):
    model = factory()
    model.fit(X_train, y_train, g_train)
    return model.predict_proba(X_test)


def pooled_pr_auc(y, prob):
    return pr_auc(np.asarray(y), np.asarray(prob))


def per_incident_pr_auc(y, prob, groups):
    return per_incident_metric(np.asarray(y), np.asarray(prob), np.asarray(groups), pr_auc)
