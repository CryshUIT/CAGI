"""NSS 2026 (2026-09-26) - Bang lead time theo 3 nguong CO DINH theta in
{0.5, 0.7, 0.9} tren xac suat M1 DA Platt-calibrate.

Khac voi results/tables/lead_time_results.csv (dung threshold rieng CHON QUA
INNER-CV cho tung bucket prefix, phuong phap RQ2 goc) - bang nay dung
evaluate_model_nested(..., calibration="platt") TREN POOLED DATASET (dedupe,
giong het methodology cho M1=0,6624 chinh thuc), roi ap 3 nguong co dinh
(khong chon qua CV) de minh hoa trade-off detect-som vs false-alert khi
NGUOI VAN HANH tu chon nguong xac suat truc quan thay vi nguong toi uu FPR.

- t_e (endpoint): thoi diem action terminal (bridge_deposit/mixer_or_exit/
  lending_deposit) DAU TIEN trong trajectory da decode - dung LAI dung logic
  _find_te() cua scripts/compute_lead_time.py (10/15 incident du dieu kien:
  endpoint_confirmed=True VA co it nhat 1 action terminal that, khong suy doan;
  con so nay > "7/11" trong lead_time_results.csv cu vi dataset da mo rong N=11->N=15).
- t_a (alert): thoi diem action CUOI CUNG cua prefix NGAN NHAT ma
  oof_prob_calibrated (Platt) >= theta.
- lead_time = t_e - t_a. detected_before_endpoint = lead_time > 0.
  late detection = da alert NHUNG t_a >= t_e (lead_time <= 0) - tach rieng,
  KHONG gop vao median/IQR lead time duong.
  never_alerted = khong prefix nao (ke ca prefix day du) vuot theta.
- false-alert rate: tren HARD-NEGATIVE da mined (matched voi tung incident
  duong tinh, "negative da matched" theo dung thuat ngu cua du an) - 1
  hard-negative trajectory duoc tinh la "false alert" neu CO IT NHAT 1 prefix
  cua no (bat ky do dai nao) co oof_prob_calibrated >= theta (tuong duong
  "he thong se canh bao sai it nhat 1 lan neu quan sat toan bo trajectory nay").
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.nested_eval import dedupe_pooled_prefixes, evaluate_model_nested  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
REGISTRY_PATH = ROOT / "metadata" / "incident_registry.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}
THRESHOLDS = [0.5, 0.7, 0.9]

OUT_CSV = ROOT / "results" / "tables" / "lead_time_by_threshold_2026-09-26.csv"
OUT_DETAIL_CSV = ROOT / "results" / "tables" / "lead_time_by_threshold_per_incident_2026-09-26.csv"
OUT_MD = ROOT / "results" / "reports" / "lead_time_by_threshold_2026-09-26.md"


def find_te(incident_id: str):
    events = json.loads((PROCESSED_DIR / f"{incident_id}_events.json").read_text(encoding="utf-8"))
    terminal = [a for a in events if a["event_type"] in TERMINAL_TYPES]
    if not terminal:
        return None, None, None
    terminal_sorted = sorted(terminal, key=lambda a: a["timestamp"])
    first = terminal_sorted[0]
    return pd.Timestamp(first["timestamp"]), first["event_type"], sorted(events, key=lambda a: a["timestamp"])


def eligible_positive_incidents():
    reg_df = pd.read_csv(REGISTRY_PATH)
    reg_df = reg_df[(reg_df["eval_tier"] == "primary") & (reg_df["label"] == 1)]
    eligible, excluded = {}, []
    for _, row in reg_df.iterrows():
        iid = row["incident_id"]
        if not bool(row["endpoint_confirmed"]):
            excluded.append((iid, "endpoint_confirmed=False"))
            continue
        te, te_type, events_sorted = find_te(iid)
        if te is None:
            excluded.append((iid, "endpoint_confirmed=True nhung khong co action terminal that"))
            continue
        eligible[iid] = (te, te_type, events_sorted)
    return eligible, excluded


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    print("=== Chay evaluate_model_nested(M1, calibration='platt') tren pooled dataset ===", flush=True)
    res = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01, calibration="platt")
    df = df.copy()
    df["oof_prob_calibrated"] = res["oof_prob_calibrated"].to_numpy()
    valid = df["oof_prob_calibrated"].notna()
    print(f"So dong co calibrated prob hop le: {valid.sum()}/{len(df)}")

    eligible, excluded = eligible_positive_incidents()
    print(f"\n=== {len(eligible)} incident duong tinh du dieu kien tinh lead time ===")
    for iid, (te, te_type, _) in eligible.items():
        print(f"  {iid:32s} te={te} (tu action {te_type})")
    print(f"=== {len(excluded)} incident bi loai ===")
    for iid, reason in excluded:
        print(f"  {iid:32s} - {reason}")

    hard_neg_df = df[(df["kind"] != "positive") & valid]

    summary_rows = []
    detail_rows = []
    for theta in THRESHOLDS:
        print(f"\n=== theta={theta} ===", flush=True)
        n_detected, n_late, n_never = 0, 0, 0
        lead_hours = []
        for iid, (te, te_type, events_sorted) in eligible.items():
            rows = df[(df["source_id"] == iid) & valid].sort_values("prefix_len")
            hit = rows[rows["oof_prob_calibrated"] >= theta]
            if hit.empty:
                n_never += 1
                detail_rows.append({"theta": theta, "incident_id": iid, "status": "never_alerted",
                                     "alert_prefix_len": None, "lead_time_hours": None})
                continue
            alert_prefix_len = int(hit["prefix_len"].min())
            ta = pd.Timestamp(events_sorted[alert_prefix_len - 1]["timestamp"])
            lead_time_sec = (te - ta).total_seconds()
            if lead_time_sec > 0:
                n_detected += 1
                lead_hours.append(lead_time_sec / 3600.0)
                status = "detected_before_endpoint"
            else:
                n_late += 1
                status = "late_detection"
            detail_rows.append({"theta": theta, "incident_id": iid, "status": status,
                                 "alert_prefix_len": alert_prefix_len,
                                 "lead_time_hours": lead_time_sec / 3600.0})
            print(f"  {iid:32s} alert_prefix_len={alert_prefix_len} lead_time_h={lead_time_sec/3600.0:+.3f} ({status})")

        n_eligible = len(eligible)
        lead_hours_arr = np.array(lead_hours)
        median_h = float(np.median(lead_hours_arr)) if len(lead_hours_arr) else float("nan")
        iqr_lo = float(np.percentile(lead_hours_arr, 25)) if len(lead_hours_arr) else float("nan")
        iqr_hi = float(np.percentile(lead_hours_arr, 75)) if len(lead_hours_arr) else float("nan")

        neg_traj_hit = hard_neg_df[hard_neg_df["oof_prob_calibrated"] >= theta]["source_id"].nunique()
        neg_traj_total = hard_neg_df["source_id"].nunique()
        false_alert_rate = neg_traj_hit / neg_traj_total if neg_traj_total else float("nan")

        print(f"  Detected before endpoint: {n_detected}/{n_eligible}, late: {n_late}/{n_eligible}, "
              f"never: {n_never}/{n_eligible}")
        print(f"  Median lead time (h) = {median_h:.3f}, IQR=[{iqr_lo:.3f}, {iqr_hi:.3f}]")
        print(f"  False-alert rate (matched hard-negative trajectories) = {false_alert_rate:.4f} "
              f"({neg_traj_hit}/{neg_traj_total})")

        summary_rows.append({
            "theta": theta, "n_eligible_incidents": n_eligible,
            "detected_before_endpoint": n_detected, "detected_before_endpoint_pct": n_detected / n_eligible,
            "late_detection": n_late, "never_alerted": n_never,
            "median_lead_time_hours": median_h, "lead_time_iqr_low_hours": iqr_lo, "lead_time_iqr_high_hours": iqr_hi,
            "false_alert_rate_matched_negatives": false_alert_rate,
            "n_matched_negative_trajectories_flagged": neg_traj_hit, "n_matched_negative_trajectories_total": neg_traj_total,
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUT_CSV, index=False)
    pd.DataFrame(detail_rows).to_csv(OUT_DETAIL_CSV, index=False)

    md = [
        "# Lead time theo nguong co dinh theta in {0.5, 0.7, 0.9} - xac suat M1 Platt-calibrated (2026-09-26)\n",
        "\nNguon: `evaluate_model_nested(M1TypedTemporalMotifModel, calibration='platt')` tren pooled "
        "dataset da dedupe (methodology giong het M1=0,6624 chinh thuc), khong chon threshold qua CV - "
        f"ap {len(THRESHOLDS)} nguong co dinh de minh hoa trade-off. t_e/t_a dung dung dinh nghia "
        "trong `scripts/compute_lead_time.py` (chi 7/15 incident duong tinh du dieu kien: endpoint_confirmed=True "
        "va co it nhat 1 action terminal that trong trajectory da decode).\n",
        "\n| theta | Detected before t_e | Median lead time (h) | IQR lead time (h) | Late detection | "
        "Never alerted | False-alert rate (matched negatives) |\n|---|---|---|---|---|---|---|\n",
    ]
    for r in summary_rows:
        md.append(
            f"| {r['theta']} | {r['detected_before_endpoint']}/{r['n_eligible_incidents']} "
            f"({r['detected_before_endpoint_pct']:.0%}) | {r['median_lead_time_hours']:.2f} | "
            f"[{r['lead_time_iqr_low_hours']:.2f}, {r['lead_time_iqr_high_hours']:.2f}] | "
            f"{r['late_detection']} | {r['never_alerted']} | "
            f"{r['false_alert_rate_matched_negatives']:.4f} "
            f"({r['n_matched_negative_trajectories_flagged']}/{r['n_matched_negative_trajectories_total']}) |\n"
        )
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_DETAIL_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
