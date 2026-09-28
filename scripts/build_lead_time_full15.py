"""Viec 0 (NSS 2026): bang lead-time day du cho 15 incident danh gia.

Chi doc lead_time_results.csv (da co) + incident_registry.csv - KHONG suy
doan te cho incident khong tinh duoc. Ly do loai lay tu logic that trong
scripts/compute_lead_time.py.
Xuat: results/tables/lead_time_full15_2026-09-22.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVAL15 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022", "paraluni_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024", "xkingdom_2024",
]


def main() -> None:
    lt = pd.read_csv(ROOT / "results/tables/lead_time_results.csv").set_index("incident_id")
    reg = pd.read_csv(ROOT / "metadata/incident_registry.csv").set_index("incident_id")
    rows = []
    for iid in EVAL15:
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
                base["note"] = "endpoint_confirmed=False trong incident_registry.csv"
            else:
                base["note"] = "endpoint_confirmed=True nhung khong co action terminal (bridge/mixer/lending) trong trajectory da decode"
        rows.append(base)
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results/tables/lead_time_full15_2026-09-22.csv", index=False)
    print(out[["incident_id", "status", "lead_time_sec", "lead_steps"]].to_string(index=False))
    print(out["status"].value_counts().to_dict())
    pos = out[out["status"] == "alerted_before_endpoint"]["lead_time_sec"]
    print("lead_time (s) cua nhom alert truoc endpoint: n=%d median=%.0f min=%.0f max=%.0f" % (len(pos), pos.median(), pos.min(), pos.max()))


if __name__ == "__main__":
    main()
