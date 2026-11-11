"""EXPLORATORY / post-hoc - CHI DOC lai ket qua da co (KHONG train lai,
KHONG goi evaluate_model_nested): extra_N30_lead_time_results.csv (tu
compute_lead_time_N30.py), extra_N30_rq2_oof_predictions.csv (nguon
oof_threshold theo bucket), incident_registry_N30.csv. Xuat Table 5 day
du cho CA 30 incident (ke ca 12 khong eligible), ghi ro ly do.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EVAL30 = [
    "ronin_bridge_2022", "qbridge_qubit_2022", "feg_bridge_2024", "deltaprime_arbitrum_2024",
    "bsc_token_hub_2022", "chibi_finance_2023", "wooppv2_2024", "utopiasphere_2024", "xkingdom_2024",
    "wault_finance_2021", "paraluni_2022", "radiant_capital_arbitrum_2024", "magic_abracadabra_arbitrum_2025",
    "hackerdao_2022", "new_free_dao_2022", "zunami_protocol_2023", "onyx_protocol_2023",
    "beanstalk_farms_2022", "hedgey_finance_2024", "cork_protocol_2025", "dough_finance_2024",
    "0xinfini_2025", "prisma_finance_2024", "uranium_finance_2021", "inverse_finance_2022_jun",
    "lendhub_2023", "thorchain2_2021", "popsicle_finance_2021", "heco_htx_2023", "easyfi_2021",
]
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}

OUT_CSV = ROOT / "results" / "tables" / "extra_N30_table5_per_incident.csv"


def main():
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry_N30.csv").set_index("incident_id")
    lt = pd.read_csv(ROOT / "results" / "tables" / "extra_N30_lead_time_results.csv").set_index("incident_id")
    oof = pd.read_csv(ROOT / "data" / "processed" / "extra_N30_rq2_oof_predictions.csv")

    rows = []
    for iid in EVAL30:
        r = reg.loc[iid]
        chain = r["chain_primary"]
        endpoint_confirmed = bool(r["endpoint_confirmed"])

        if iid in lt.index:
            x = lt.loc[iid]
            eligible = True
            reason = ""
            alert_bucket = x["alert_prefix_bucket"]
            # ngưỡng θ dùng = oof_threshold cua CHINH bucket da kich hoat alert (theo-bucket inner-CV,
            # KHONG phai 1 theta toan cuc - xem data/processed/extra_N30_rq2_oof_predictions.csv)
            th_rows = oof[(oof.source_id == iid) & (oof.prefix_label == alert_bucket)]
            theta_used = float(th_rows["oof_threshold"].iloc[0]) if len(th_rows) else None
            alert_prefix_len = x["alert_prefix_len"]
            lead_steps = x["lead_steps"]
            lead_time_h = x["lead_time_sec"] / 3600.0 if pd.notna(x["lead_time_sec"]) else None
            never = bool(x["never_alerted"])
            if never:
                status = "never_alerted"
            elif bool(x["detected_before_endpoint"]):
                status = "detected_before"
            else:
                status = "detected_late"
        else:
            eligible = False
            if not endpoint_confirmed:
                reason = "endpoint_confirmed=False trong incident_registry_N30.csv"
            else:
                reason = "endpoint_confirmed=True nhung khong tim thay action terminal (bridge_deposit/mixer_or_exit/lending_deposit) thuc trong trajectory da decode"
            theta_used = None
            alert_prefix_len = None
            lead_steps = None
            lead_time_h = None
            status = "not_computable"

        rows.append({
            "incident_id": iid, "chain": chain, "endpoint_confirmed": endpoint_confirmed,
            "eligible_for_lead_time": eligible, "reason_if_not_eligible": reason,
            "theta_threshold_used": theta_used, "alert_prefix_len_n_actions": alert_prefix_len,
            "lead_steps": lead_steps, "lead_time_hours": lead_time_h, "status": status,
        })

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(out.to_string(index=False))
    print(f"\nDa luu {OUT_CSV}")
    print("\nTong hop status:", out["status"].value_counts().to_dict())


if __name__ == "__main__":
    main()
