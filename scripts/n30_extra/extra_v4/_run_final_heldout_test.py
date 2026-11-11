# -*- coding: utf-8 -*-
"""Test MOT LAN final held-out bang model DA DONG BANG (M1_FROZEN_final_N36,
B3prime_FROZEN_final_N36) tren 2 incident hoan toan moi (rari_capital_fuse_2022,
curve_crv_eth_attacker_2023). KHONG train lai, KHONG doi threshold sau khi
xem ket qua. 4 nguong da khai bao TRUOC: 0.5 (CHINH), 0.7, 0.9, theta_frozen
(rieng cho tung model). Them B0 (fit tren 36 group train, CHI dung
prevalence) de so sanh."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.evaluation.metrics import false_alerts_per_1000, pr_auc  # noqa: E402
from src.evaluation.nested_eval import _apply_calibrator, dedupe_pooled_prefixes  # noqa: E402
from src.models.baselines import B0MajorityBaseline  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))
from _freeze_final_B3prime_N36 import XGBFixedColumns  # noqa: E402,F401  (can thiet de unpickle B3prime_FROZEN)

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}
PROCESSED_DIR = ROOT / "data" / "processed"
TEST_IDS = ["rari_capital_fuse_2022", "curve_crv_eth_attacker_2023", "pancakebunny_2021", "rikkei_finance_2022"]

FROZEN_DIR = ROOT / "results" / "reports" / "extra_v4"
OUT_TABLES = ROOT / "results" / "tables" / "extra_v4"
OUT_REPORTS = ROOT / "results" / "reports" / "extra_v4"


def load_frozen(name: str):
    with open(FROZEN_DIR / f"{name}.pkl", "rb") as f:
        model = pickle.load(f)
    with open(FROZEN_DIR / f"{name}_platt_calibrator.pkl", "rb") as f:
        cal = pickle.load(f)
    meta = json.loads((FROZEN_DIR / f"{name}_metadata.json").read_text(encoding="utf-8"))
    return model, cal, meta


def find_te(incident_id: str):
    path = PROCESSED_DIR / f"{incident_id}_events.json"
    if not path.exists():
        return None, None, None
    events = json.loads(path.read_text(encoding="utf-8"))
    terminal = [a for a in events if a["event_type"] in TERMINAL_TYPES]
    if not terminal:
        return None, None, None
    terminal_sorted = sorted(terminal, key=lambda a: a["timestamp"])
    first = terminal_sorted[0]
    return pd.Timestamp(first["timestamp"]), first["event_type"], sorted(events, key=lambda a: a["timestamp"])


def main():
    df_train_full = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
    df_train_full = dedupe_pooled_prefixes(df_train_full)
    y_train_full = df_train_full["label"]
    b0 = B0MajorityBaseline()
    b0.fit(df_train_full[[c for c in df_train_full.columns if c not in META_COLS]], y_train_full)
    print(f"B0 prevalence (fit tren 36 group train) = {b0.prevalence_:.6f}", flush=True)

    df_test = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_final_heldout_new.parquet")
    df_test = dedupe_pooled_prefixes(df_test)
    feature_cols = [c for c in df_test.columns if c not in META_COLS]

    models = {
        "M1": load_frozen("M1_FROZEN_final_N36"),
        "B3prime": load_frozen("B3prime_FROZEN_final_N36"),
    }

    all_rows = []
    lead_time_rows = []

    for model_name, (model, cal, meta) in models.items():
        theta_frozen = meta["theta_frozen"]
        thresholds = {"0.5_CHINH": 0.5, "0.7": 0.7, "0.9": 0.9, f"theta_frozen_{theta_frozen:.6f}": theta_frozen}
        print(f"\n\n=== {model_name} (theta_frozen={theta_frozen:.6f}) ===", flush=True)

        X_test = df_test[feature_cols]
        prob_test = model.predict_proba(X_test)
        prob_test_cal = _apply_calibrator(cal, prob_test, "platt")

        df_t = df_test.copy()
        df_t["prob_raw"] = prob_test
        df_t["prob_cal"] = prob_test_cal
        b0_prob = b0.predict_proba(df_test)

        pooled_pr_auc_m1 = pr_auc(df_t["label"].to_numpy(), prob_test)
        pooled_pr_auc_b0 = pr_auc(df_t["label"].to_numpy(), b0_prob)
        print(f"  Pooled PR-AUC (2 incident, raw prob, chua calibrate) = {pooled_pr_auc_m1:.4f} (B0={pooled_pr_auc_b0:.4f})", flush=True)

        for iid in TEST_IDS:
            sub = df_t[df_t["group_id"] == iid]
            y_i = sub["label"].to_numpy()
            prob_i = sub["prob_raw"].to_numpy()
            prob_i_cal = sub["prob_cal"].to_numpy()
            b0_i = b0.predict_proba(sub[feature_cols])
            n_pos = int((y_i == 1).sum())
            n_neg = int((y_i == 0).sum())
            if n_neg == 0:
                pr_i, pr_i_b0 = float("nan"), float("nan")
                print(f"  {iid:28s} n_pos={n_pos:3d} n_neg={n_neg:3d} PR-AUC=KHONG TINH DUOC (0 hard-negative)", flush=True)
            else:
                pr_i = pr_auc(y_i, prob_i)
                pr_i_b0 = pr_auc(y_i, b0_i)
                print(f"  {iid:28s} n_pos={n_pos:3d} n_neg={n_neg:3d} PR-AUC={pr_i:.4f} (B0={pr_i_b0:.4f})", flush=True)

            te, te_type, events_sorted = find_te(iid)
            for theta_label, theta in thresholds.items():
                hard_neg_sub = sub[sub["kind"] != "positive_final_heldout"]
                neg_hit = int((hard_neg_sub["prob_cal"] >= theta).sum())
                neg_total = len(hard_neg_sub)
                far = neg_hit / neg_total if neg_total else float("nan")
                far_1000 = false_alerts_per_1000(y_i, prob_i_cal, threshold=theta)

                if te is not None:
                    pos_rows = sub[sub["source_id"] == iid].sort_values("prefix_len")
                    hit = pos_rows[pos_rows["prob_cal"] >= theta]
                    if hit.empty:
                        status, lead_h, alert_len = "never_alerted", None, None
                    else:
                        alert_len = int(hit["prefix_len"].min())
                        ta = pd.Timestamp(events_sorted[alert_len - 1]["timestamp"])
                        lead_sec = (te - ta).total_seconds()
                        status = "detected_before_endpoint" if lead_sec > 0 else "late_detection"
                        lead_h = lead_sec / 3600.0
                else:
                    status, lead_h, alert_len = "no_confirmed_endpoint", None, None

                row = {
                    "model": model_name, "incident_id": iid, "theta_label": theta_label, "theta_value": theta,
                    "n_positive_rows": n_pos, "n_negative_rows": n_neg,
                    "pr_auc": pr_i, "pr_auc_b0": pr_i_b0,
                    "false_alert_rate_matched_negatives": far, "n_neg_flagged": neg_hit, "n_neg_total": neg_total,
                    "false_alerts_per_1000": far_1000,
                    "edr_status": status, "lead_time_hours": lead_h, "alert_prefix_len": alert_len,
                }
                all_rows.append(row)
                print(f"    theta={theta_label:24s} FAR(matched_neg)={far:.4f} ({neg_hit}/{neg_total}) "
                      f"status={status} lead_h={lead_h}", flush=True)

    out_df = pd.DataFrame(all_rows)
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_TABLES / "final_heldout_test_results.csv", index=False)
    print(f"\nDa luu {OUT_TABLES / 'final_heldout_test_results.csv'}", flush=True)


if __name__ == "__main__":
    main()
