"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_lead_time_by_threshold.py cho N=30. Thay doi DUY NHAT:
REGISTRY_PATH -> incident_registry_N30.csv, FEATURES_PATH -> features_v2_N30.parquet,
duong dan output -> hau to extra_N30. Logic (evaluate_model_nested platt,
3 nguong co dinh, false-alert tren hard-negative) giu nguyen 100%.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.nested_eval import dedupe_pooled_prefixes, evaluate_model_nested  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
FEATURES_PATH = PROCESSED_DIR / "features_v2_N30.parquet"
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}
THRESHOLDS = [0.5, 0.7, 0.9]

OUT_CSV = ROOT / "results" / "tables" / "extra_N30_rq2_lead_time_by_threshold.csv"
OUT_DETAIL_CSV = ROOT / "results" / "tables" / "extra_N30_rq2_lead_time_by_threshold_per_incident.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_rq2_lead_time_by_threshold.md"


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


def bootstrap_median_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42):
    """CI 95% bootstrap CAP INCIDENT cho median lead time (them moi cho N30,
    khong co trong ban N15 goc - yeu cau cua nguoi dung)."""
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n = len(values)
    boot_medians = np.array([np.median(rng.choice(values, size=n, replace=True)) for _ in range(n_boot)])
    lo, hi = np.percentile(boot_medians, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    check_m1_gate()
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    print("=== Chay evaluate_model_nested(M1, calibration='platt') tren pooled dataset N30 ===", flush=True)
    res = evaluate_model_nested(M1TypedTemporalMotifModel, X, y, groups, target_fpr=0.01, calibration="platt")
    df = df.copy()
    df["oof_prob_calibrated"] = res["oof_prob_calibrated"].to_numpy()
    valid = df["oof_prob_calibrated"].notna()
    print(f"So dong co calibrated prob hop le: {valid.sum()}/{len(df)}")

    eligible, excluded = eligible_positive_incidents()
    print(f"\n=== {len(eligible)} incident duong tinh du dieu kien tinh lead time (N30) ===")
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
        ci_lo, ci_hi = bootstrap_median_ci(lead_hours_arr)

        neg_traj_hit = hard_neg_df[hard_neg_df["oof_prob_calibrated"] >= theta]["source_id"].nunique()
        neg_traj_total = hard_neg_df["source_id"].nunique()
        false_alert_rate = neg_traj_hit / neg_traj_total if neg_traj_total else float("nan")

        print(f"  Detected before endpoint: {n_detected}/{n_eligible}, late: {n_late}/{n_eligible}, "
              f"never: {n_never}/{n_eligible}")
        print(f"  Median lead time (h) = {median_h:.3f}, IQR=[{iqr_lo:.3f}, {iqr_hi:.3f}], "
              f"95% CI bootstrap cap incident=[{ci_lo:.3f}, {ci_hi:.3f}] (n={len(lead_hours_arr)})")
        print(f"  False-alert rate (matched hard-negative trajectories) = {false_alert_rate:.4f} "
              f"({neg_traj_hit}/{neg_traj_total})")

        summary_rows.append({
            "theta": theta, "n_eligible_incidents": n_eligible,
            "detected_before_endpoint": n_detected, "detected_before_endpoint_pct": n_detected / n_eligible,
            "late_detection": n_late, "never_alerted": n_never,
            "median_lead_time_hours": median_h, "lead_time_iqr_low_hours": iqr_lo, "lead_time_iqr_high_hours": iqr_hi,
            "median_lead_time_ci95_low_hours": ci_lo, "median_lead_time_ci95_high_hours": ci_hi,
            "n_detected_for_median": len(lead_hours_arr),
            "false_alert_rate_matched_negatives": false_alert_rate,
            "n_matched_negative_trajectories_flagged": neg_traj_hit, "n_matched_negative_trajectories_total": neg_traj_total,
        })

    summary_df = pd.DataFrame(summary_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_CSV, index=False)
    pd.DataFrame(detail_rows).to_csv(OUT_DETAIL_CSV, index=False)

    md = [
        "# [EXPLORATORY/post-hoc, ngoai plan v3] Lead time theo nguong co dinh — N=30\n",
        "\nNguon: `evaluate_model_nested(M1TypedTemporalMotifModel, calibration='platt')` tren "
        f"pooled N=30 dataset da dedupe, ap {len(THRESHOLDS)} nguong co dinh theta.\n",
        "\n| theta | Detected before t_e | Median lead time (h) | IQR (h) | 95% CI bootstrap (incident, n) | "
        "Late detection | Never alerted | False-alert rate (matched negatives) |\n|---|---|---|---|---|---|---|---|\n",
    ]
    for r in summary_rows:
        md.append(
            f"| {r['theta']} | {r['detected_before_endpoint']}/{r['n_eligible_incidents']} "
            f"({r['detected_before_endpoint_pct']:.0%}) | {r['median_lead_time_hours']:.2f} | "
            f"[{r['lead_time_iqr_low_hours']:.2f}, {r['lead_time_iqr_high_hours']:.2f}] | "
            f"[{r['median_lead_time_ci95_low_hours']:.2f}, {r['median_lead_time_ci95_high_hours']:.2f}] (n={r['n_detected_for_median']}) | "
            f"{r['late_detection']} | {r['never_alerted']} | "
            f"{r['false_alert_rate_matched_negatives']:.4f} "
            f"({r['n_matched_negative_trajectories_flagged']}/{r['n_matched_negative_trajectories_total']}) |\n"
        )
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_DETAIL_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
