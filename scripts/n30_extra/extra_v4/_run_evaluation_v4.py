# -*- coding: utf-8 -*-
"""N37 (v4_heldout) - danh gia (a) held-out va (b) v4 pooled LOIO.

DONG BANG: M1/B3' hyperparameter, Platt, target_fpr=0.01, seed=42 - GIONG
v3 (run_evaluation_N30_v3.py / run_extra_N30_exploratory.py). KHONG
retrain/tune theo incident moi.

(a) Held-out: fit M1/B3' MOT LAN tren 30 incident cu (dung
    load_rq1_trajectories cu + hard-negative cu, KHONG dong vao), du doan
    tren 6 incident moi (+ hard-negative MOI cua chinh chung, KHONG dua
    vao train). Threshold chon qua inner-LOGO tren CHINH 30 train (cung
    co che evaluate_model_nested), Platt calibrator fit tren cung du
    lieu inner-OOF.
(b) v4 pooled: LOIO (evaluate_model_nested) tren TOAN BO 36 group hop le
    (30 cu + 6 moi) - CUNG ham/tham so da dung cho N30.

Ket qua v3 (N=30) KHONG bi dong vao - script nay chi doc features_v2_N37.parquet
(MOI), ghi output rieng vao results/*/extra_v4/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.model_selection import LeaveOneGroupOut  # noqa: E402

from src.evaluation.metrics import false_alerts_per_1000, pr_auc  # noqa: E402
from src.evaluation.nested_eval import (  # noqa: E402
    _apply_calibrator,
    _fit_calibrator,
    bootstrap_incident_level,
    dedupe_pooled_prefixes,
    evaluate_model_nested,
    per_incident_metric,
    select_threshold,
)
from src.models.baselines import B3FlatGraphRandomForest, M1TypedTemporalMotifModel  # noqa: E402

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N37.parquet"
PROCESSED_DIR = ROOT / "data" / "processed"
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TARGET_FPR = 0.01
THETAS = [0.5, 0.7, 0.9]
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}

NEW_POSITIVE_IDS = [
    "sturdy_finance_2023", "jimbos_protocol_2023", "rodeo_finance_2023",
    "sentiment_protocol_2023", "pike_finance_2024", "uwu_lend_2024",
]

M1_XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42, eval_metric="logloss")
B3_FLAT_COLS = list(B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES)

OUT_TABLES = ROOT / "results" / "tables" / "extra_v4"
OUT_REPORTS = ROOT / "results" / "reports" / "extra_v4"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_REPORTS.mkdir(parents=True, exist_ok=True)


class XGBFixedColumns:
    """Y HET run_extra_N30_exploratory.py::XGBFixedColumns - B3' = CUNG
    hyperparameter M1, CHI gioi han FLAT_UNTYPED_FEATURES (khong action-type
    semantics, khong motif)."""

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
            self.model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, class_weight="balanced")
        self.model.fit(X_train[self.feature_cols_], y_train)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.feature_cols_])[:, 1]


MODEL_FACTORIES = {
    "M1": lambda: M1TypedTemporalMotifModel(),
    "B3prime": lambda: XGBFixedColumns("B3prime", B3_FLAT_COLS),
}


def find_te(incident_id: str):
    events = json.loads((PROCESSED_DIR / f"{incident_id}_events.json").read_text(encoding="utf-8"))
    terminal = [a for a in events if a["event_type"] in TERMINAL_TYPES]
    if not terminal:
        return None, None, None
    terminal_sorted = sorted(terminal, key=lambda a: a["timestamp"])
    first = terminal_sorted[0]
    return pd.Timestamp(first["timestamp"]), first["event_type"], sorted(events, key=lambda a: a["timestamp"])


def bootstrap_median_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42):
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n = len(values)
    boot = np.array([np.median(rng.choice(values, size=n, replace=True)) for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(lo), float(hi)


def part_a_held_out(df: pd.DataFrame, feature_cols: list):
    print("\n\n=== (a) HELD-OUT: train 30 incident cu, test 6 incident moi ===", flush=True)
    old_mask = df["kind"].isin(["positive", "hard_negative_control", "hard_negative_mined", "hard_negative_mined_v2_complexity"])
    new_mask = df["group_id"].isin(NEW_POSITIVE_IDS)
    assert not (old_mask & new_mask).any()

    X_train, y_train, g_train = df.loc[old_mask, feature_cols], df.loc[old_mask, "label"], df.loc[old_mask, "group_id"]
    print(f"Train: {len(X_train)} dong, {g_train.nunique()} group (ky vong 30)", flush=True)

    summary_rows = []
    per_incident_rows = []
    lead_time_rows = []

    for model_name, factory in MODEL_FACTORIES.items():
        print(f"\n--- {model_name} ---", flush=True)
        # inner LOGO tren train de chon threshold + fit Platt calibrator (CUNG co che evaluate_model_nested)
        inner_logo = LeaveOneGroupOut()
        inner_oof = np.full(len(y_train), np.nan)
        y_train_arr = y_train.to_numpy()
        for inner_tr_idx, inner_val_idx in inner_logo.split(X_train, y_train, groups=g_train):
            m = factory()
            m.fit(X_train.iloc[inner_tr_idx], y_train.iloc[inner_tr_idx], g_train.iloc[inner_tr_idx])
            inner_oof[inner_val_idx] = m.predict_proba(X_train.iloc[inner_val_idx])
        valid_inner = ~np.isnan(inner_oof)
        theta_frozen = select_threshold(y_train_arr[valid_inner], inner_oof[valid_inner], target_fpr=TARGET_FPR)
        cal = _fit_calibrator(y_train_arr[valid_inner], inner_oof[valid_inner], "platt")
        print(f"  theta (chon tren train, target_fpr={TARGET_FPR}) = {theta_frozen:.6f}", flush=True)

        final_model = factory()
        final_model.fit(X_train, y_train, g_train)

        test_mask = new_mask
        X_test = df.loc[test_mask, feature_cols]
        y_test = df.loc[test_mask, "label"].to_numpy()
        g_test = df.loc[test_mask, "group_id"].to_numpy()
        prob_test = final_model.predict_proba(X_test)
        prob_test_cal = _apply_calibrator(cal, prob_test, "platt")

        pooled_pr_auc = pr_auc(y_test, prob_test)
        boot = bootstrap_incident_level(y_test, prob_test, g_test, pr_auc, n_boot=2000, random_state=42)
        pooled_far = false_alerts_per_1000(y_test, prob_test, threshold=theta_frozen)
        print(f"  Pooled PR-AUC (6 incident moi) = {pooled_pr_auc:.4f} [{boot['ci_low']:.4f}, {boot['ci_high']:.4f}]", flush=True)
        summary_rows.append({
            "model": model_name, "metric": "pooled_pr_auc_6_new", "value": pooled_pr_auc,
            "ci_low_95": boot["ci_low"], "ci_high_95": boot["ci_high"], "theta_frozen": theta_frozen,
            "false_alerts_per_1000_at_theta": pooled_far,
        })

        per_inc = per_incident_metric(y_test, prob_test, g_test, pr_auc)
        for iid, v in per_inc.items():
            n_pos_i = int(((g_test == iid) & (y_test == 1)).sum())
            n_neg_i = int(((g_test == iid) & (y_test == 0)).sum())
            per_incident_rows.append({"model": model_name, "incident_id": iid, "pr_auc": v,
                                        "n_positive_rows": n_pos_i, "n_negative_rows": n_neg_i})
            print(f"    {iid:28s} PR-AUC={v:.4f} (n_pos={n_pos_i}, n_neg={n_neg_i})", flush=True)

        # EDR / lead time / FAR tai THETAS co dinh, dung prob CALIBRATED (giong run_lead_time_by_threshold_N30.py)
        df_test = df.loc[test_mask].copy()
        df_test["prob_cal"] = prob_test_cal
        hard_neg_test = df_test[df_test["kind"] != "positive_v4_heldout"]
        for theta in THETAS:
            n_detected = n_late = n_never = 0
            lead_hours = []
            for iid in NEW_POSITIVE_IDS:
                te, te_type, events_sorted = find_te(iid)
                if te is None:
                    continue
                rows = df_test[(df_test["source_id"] == iid)].sort_values("prefix_len")
                hit = rows[rows["prob_cal"] >= theta]
                if hit.empty:
                    n_never += 1
                    lead_time_rows.append({"model": model_name, "theta": theta, "incident_id": iid,
                                             "status": "never_alerted", "lead_time_hours": None})
                    continue
                alert_prefix_len = int(hit["prefix_len"].min())
                ta = pd.Timestamp(events_sorted[alert_prefix_len - 1]["timestamp"])
                lead_time_sec = (te - ta).total_seconds()
                status = "detected_before_endpoint" if lead_time_sec > 0 else "late_detection"
                if status == "detected_before_endpoint":
                    n_detected += 1
                    lead_hours.append(lead_time_sec / 3600.0)
                else:
                    n_late += 1
                lead_time_rows.append({"model": model_name, "theta": theta, "incident_id": iid,
                                         "status": status, "lead_time_hours": lead_time_sec / 3600.0})
            n_eligible_te = sum(1 for iid in NEW_POSITIVE_IDS if find_te(iid)[0] is not None)
            neg_hit = hard_neg_test[hard_neg_test["prob_cal"] >= theta]["source_id"].nunique()
            neg_total = hard_neg_test["source_id"].nunique()
            far = neg_hit / neg_total if neg_total else float("nan")
            lead_arr = np.array(lead_hours)
            median_h = float(np.median(lead_arr)) if len(lead_arr) else float("nan")
            print(f"  theta={theta}: EDR(detected_before_endpoint)={n_detected}/{n_eligible_te} "
                  f"median_lead_h={median_h:.2f} FAR={far:.4f} ({neg_hit}/{neg_total})", flush=True)
            summary_rows.append({
                "model": model_name, "metric": f"EDR_theta_{theta}", "value": (n_detected / n_eligible_te) if n_eligible_te else float("nan"),
                "n_detected": n_detected, "n_late": n_late, "n_never": n_never, "n_eligible_te": n_eligible_te,
                "median_lead_time_hours": median_h, "false_alert_rate_theta": far,
                "n_neg_flagged": neg_hit, "n_neg_total": neg_total,
            })

    pd.DataFrame(summary_rows).to_csv(OUT_TABLES / "held_out_v4_summary.csv", index=False)
    pd.DataFrame(per_incident_rows).to_csv(OUT_TABLES / "held_out_v4_per_incident.csv", index=False)
    pd.DataFrame(lead_time_rows).to_csv(OUT_TABLES / "held_out_v4_lead_time.csv", index=False)
    print(f"\nDa luu held_out_v4_summary.csv, held_out_v4_per_incident.csv, held_out_v4_lead_time.csv", flush=True)
    return summary_rows, per_incident_rows


def part_b_pooled_loio(df: pd.DataFrame, feature_cols: list):
    print("\n\n=== (b) v4 POOLED LOIO: 36 group (30 cu + 6 moi) ===", flush=True)
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    print(f"Pooled dataset: {len(df)} dong, {groups.nunique()} group (ky vong 36)", flush=True)

    rows = []
    for model_name, factory in MODEL_FACTORIES.items():
        print(f"\n--- {model_name} ---", flush=True)
        result = evaluate_model_nested(factory, X, y, groups, target_fpr=TARGET_FPR, calibration="platt")
        oof = result["oof_prob"]
        y_arr, prob_arr, g_arr = y.to_numpy(), oof.to_numpy(), groups.to_numpy()
        valid = ~np.isnan(prob_arr)

        boot = bootstrap_incident_level(y_arr[valid], prob_arr[valid], g_arr[valid], pr_auc, n_boot=2000, random_state=42)
        print(f"  Pooled PR-AUC (36 group) = {boot['point']:.4f} [{boot['ci_low']:.4f}, {boot['ci_high']:.4f}]", flush=True)
        rows.append({"model": model_name, "metric": "pooled_pr_auc_36groups", "value": boot["point"],
                     "ci_low_95": boot["ci_low"], "ci_high_95": boot["ci_high"], "n_groups": groups.nunique()})

        per_inc = per_incident_metric(y_arr[valid], prob_arr[valid], g_arr[valid], pr_auc)
        for iid, v in per_inc.items():
            rows.append({"model": model_name, "metric": f"pr_auc_incident_{iid}", "value": v})

        fold_df = pd.DataFrame(result["fold_rows"])
        fold_df.to_csv(OUT_TABLES / f"v4_pooled_loio_fold_rows_{model_name}.csv", index=False)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_TABLES / "v4_pooled_loio_summary.csv", index=False)
    print(f"\nDa luu v4_pooled_loio_summary.csv", flush=True)
    return rows


def main():
    df = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    print(f"Tong (sau dedupe): {len(df)} dong, {df['group_id'].nunique()} group", flush=True)

    a_rows, a_per_inc = part_a_held_out(df, feature_cols)
    b_rows = part_b_pooled_loio(df, feature_cols)

    (OUT_REPORTS / "evaluation_v4_raw_results.json").write_text(
        json.dumps({"part_a_held_out": a_rows, "part_a_per_incident": a_per_inc, "part_b_pooled_loio": b_rows}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nDa luu {OUT_REPORTS / 'evaluation_v4_raw_results.json'}", flush=True)


if __name__ == "__main__":
    main()
