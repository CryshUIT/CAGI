"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/build_lead_time_full15.py cho N=30 (30 incident thay vi 15). Chi
doc extra_N30_lead_time_results.csv (vua sinh tu compute_lead_time_N30.py)
+ incident_registry_N30.csv - KHONG suy doan te cho incident khong tinh
duoc. Xuat: results/tables/extra_N30_lead_time_full30.csv
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


def main() -> None:
    lt = pd.read_csv(ROOT / "results/tables/extra_N30_lead_time_results.csv").set_index("incident_id")
    reg = pd.read_csv(ROOT / "metadata/incident_registry_N30.csv").set_index("incident_id")
    rows = []
    for iid in EVAL30:
        r = reg.loc[iid]
        base = {"incident_id": iid, "endpoint_type": r["endpoint_type"], "endpoint_confirmed": bool(r["endpoint_confirmed"])}
        if iid in lt.index:
            x = lt.loc[iid]
            never = bool(x["never_alerted"])
            base.update({
                "trajectory_len": int(x["trajectory_len"]), "alert_prefix_bucket": x["alert_prefix_bucket"],
                "lead_time_sec": x["lead_time_sec"], "lead_steps": x["lead_steps"],
                "status": "never_alerted" if never else ("alerted_before_endpoint" if x["lead_time_sec"] > 0 else "alerted_after_endpoint"),
                "note": "",
            })
        else:
            base.update({"trajectory_len": None, "alert_prefix_bucket": None, "lead_time_sec": None, "lead_steps": None,
                         "status": "not_computable"})
            if not bool(r["endpoint_confirmed"]):
                base["note"] = "endpoint_confirmed=False trong incident_registry_N30.csv"
            else:
                base["note"] = "endpoint_confirmed=True nhung khong co action terminal (bridge/mixer/lending) trong trajectory da decode"
        rows.append(base)
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results/tables/extra_N30_lead_time_full30.csv", index=False)
    print(out[["incident_id", "status", "lead_time_sec", "lead_steps"]].to_string(index=False))
    print(out["status"].value_counts().to_dict())
    pos = out[out["status"] == "alerted_before_endpoint"]["lead_time_sec"]
    if len(pos):
        print("lead_time (s) cua nhom alert truoc endpoint: n=%d median=%.0f min=%.0f max=%.0f" % (len(pos), pos.median(), pos.min(), pos.max()))


if __name__ == "__main__":
    main()
