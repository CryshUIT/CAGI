"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/compute_lead_time.py cho N=30. Thay doi DUY NHAT: REGISTRY_PATH ->
incident_registry_N30.csv, OOF_PATH -> extra_N30_rq2_oof_predictions.csv
(sinh tu scripts/n30_extra/run_rq2_prefix_evaluation_N30.py, BUOC TIEN QUYET
da chay truoc), output -> hau to extra_N30. Logic giu nguyen 100%.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402

REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OOF_PATH = ROOT / "data" / "processed" / "extra_N30_rq2_oof_predictions.csv"
OUT_CSV = ROOT / "results" / "tables" / "extra_N30_lead_time_results.csv"

TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}


def _find_te(incident_id: str):
    events = json.loads((PROCESSED_DIR / f"{incident_id}_events.json").read_text(encoding="utf-8"))
    terminal = [a for a in events if a["event_type"] in TERMINAL_TYPES]
    if not terminal:
        return None, None
    terminal_sorted = sorted(terminal, key=lambda a: a["timestamp"])
    first = terminal_sorted[0]
    return pd.Timestamp(first["timestamp"]), first["event_type"]


def main():
    check_m1_gate()
    reg_df = pd.read_csv(REGISTRY_PATH)
    reg_df = reg_df[(reg_df["eval_tier"] == "primary") & (reg_df["label"] == 1)]
    oof_df = pd.read_csv(OOF_PATH, parse_dates=False)

    eligible_rows = []
    excluded_rows = []
    for _, row in reg_df.iterrows():
        iid = row["incident_id"]
        if not bool(row["endpoint_confirmed"]):
            excluded_rows.append((iid, "endpoint_confirmed=False trong incident_registry_N30.csv"))
            continue
        te, te_type = _find_te(iid)
        if te is None:
            excluded_rows.append((iid, "endpoint_confirmed=True NHUNG khong tim thay action "
                                        "bridge_deposit/mixer_or_exit/lending_deposit nao trong "
                                        "trajectory da decode - khong suy doan te"))
            continue
        eligible_rows.append((iid, te, te_type))

    print("=== Incident DU DIEU KIEN tinh lead time (N30) ===")
    for iid, te, te_type in eligible_rows:
        print(f"  {iid:32s} te={te} (tu action {te_type})")
    print(f"\n=== Incident BI LOAI ===")
    for iid, reason in excluded_rows:
        print(f"  {iid:32s} - {reason}")

    results = []
    for iid, te, te_type in eligible_rows:
        events = json.loads((PROCESSED_DIR / f"{iid}_events.json").read_text(encoding="utf-8"))
        events_sorted = sorted(events, key=lambda a: a["timestamp"])
        n_total = len(events_sorted)

        rows = oof_df[(oof_df["source_id"] == iid) & (oof_df["label"] == 1)].copy()
        if rows.empty:
            print(f"  CANH BAO: khong tim thay OOF prediction cho {iid}, bo qua.")
            continue
        rows = rows.sort_values("prefix_len")

        alert_prefix_len = None
        alert_ta = None
        alert_bucket = None
        for _, r in rows.iterrows():
            if pd.notna(r["oof_prob"]) and pd.notna(r["oof_threshold"]) and r["oof_prob"] >= r["oof_threshold"]:
                prefix_len = int(r["prefix_len"])
                if alert_prefix_len is None or prefix_len < alert_prefix_len:
                    alert_prefix_len = prefix_len
                    alert_bucket = r["prefix_label"]

        if alert_prefix_len is not None:
            alert_ta = pd.Timestamp(events_sorted[alert_prefix_len - 1]["timestamp"])
            lead_time_sec = (te - alert_ta).total_seconds()
            lead_steps = n_total - alert_prefix_len
            detected_before_endpoint = lead_time_sec > 0
        else:
            lead_time_sec = None
            lead_steps = None
            detected_before_endpoint = None

        results.append({
            "incident_id": iid, "te": te, "te_action_type": te_type,
            "trajectory_len": n_total, "alert_prefix_len": alert_prefix_len,
            "alert_prefix_bucket": alert_bucket, "alert_ta": alert_ta,
            "lead_time_sec": lead_time_sec, "lead_steps": lead_steps,
            "detected_before_endpoint": detected_before_endpoint,
            "never_alerted": alert_prefix_len is None,
        })

    result_df = pd.DataFrame(results)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUT_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}")
    print(result_df.to_string(index=False))

    n_eligible = len(result_df)
    n_never = int(result_df["never_alerted"].sum())
    detected = result_df[result_df["detected_before_endpoint"] == True]
    late = result_df[result_df["detected_before_endpoint"] == False]
    print(f"\n=== TOM TAT ({n_eligible} incident du dieu kien, N30) ===")
    print(f"Chua bao gio alert: {n_never}/{n_eligible}")
    print(f"Phat hien TRUOC endpoint (lead_time > 0): {len(detected)}/{n_eligible}")
    print(f"Phat hien SAU endpoint (late detection): {len(late)}/{n_eligible}")
    if len(detected):
        lt = detected["lead_time_sec"] / 3600.0
        print(f"Lead time (gio) trong so phat hien truoc: median={lt.median():.2f} "
              f"IQR=[{lt.quantile(0.25):.2f}, {lt.quantile(0.75):.2f}]")
        ls = detected["lead_steps"]
        print(f"Lead steps (so action con lai): median={ls.median():.1f} IQR=[{ls.quantile(0.25):.1f}, {ls.quantile(0.75):.1f}]")


if __name__ == "__main__":
    main()
