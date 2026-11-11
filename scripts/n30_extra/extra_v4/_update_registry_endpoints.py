# -*- coding: utf-8 -*-
"""Cap nhat endpoint_confirmed/endpoint_basis/type_of_first_endpoint_action/
n_mixer_or_exit/n_bridge_deposit cho 7 dong v4_heldout dua tren KET QUA
TRACE THAT (collect_v4_heldout_summary.json), KHONG doan. fortress_protocol_2022
bi loai do loi thu thap thuc (BscTraceAPIError) - ghi chu loai, khong dung
trong feature build / eval."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
reg_path = ROOT / "metadata" / "incident_registry_N37.csv"
reg = pd.read_csv(reg_path)

summary = json.loads((ROOT / "results" / "reports" / "extra_v4" / "collect_v4_heldout_summary.json").read_text(encoding="utf-8"))

updates = {
    "sturdy_finance_2023": dict(endpoint_confirmed=True, endpoint_basis="onchain_value_match",
                                 type_of_first_endpoint_action="mixer_or_exit", n_mixer_or_exit=16, n_bridge_deposit=0,
                                 endpoint_type="confirmed"),
    "jimbos_protocol_2023": dict(endpoint_confirmed=True, endpoint_basis="onchain_value_match",
                                   type_of_first_endpoint_action="bridge_deposit", n_mixer_or_exit=0, n_bridge_deposit=7,
                                   endpoint_type="confirmed"),
    "rodeo_finance_2023": dict(endpoint_confirmed=True, endpoint_basis="onchain_value_match",
                                 type_of_first_endpoint_action="bridge_deposit", n_mixer_or_exit=0, n_bridge_deposit=86,
                                 endpoint_type="confirmed"),
    "sentiment_protocol_2023": dict(endpoint_confirmed=False, endpoint_basis="none",
                                      type_of_first_endpoint_action="none", n_mixer_or_exit=0, n_bridge_deposit=0,
                                      endpoint_type="not_confirmed"),
    "pike_finance_2024": dict(endpoint_confirmed=False, endpoint_basis="none",
                                type_of_first_endpoint_action="none", n_mixer_or_exit=0, n_bridge_deposit=0,
                                endpoint_type="not_confirmed"),
    "uwu_lend_2024": dict(endpoint_confirmed=False, endpoint_basis="none",
                            type_of_first_endpoint_action="none", n_mixer_or_exit=0, n_bridge_deposit=0,
                            endpoint_type="not_confirmed"),
}

for iid, vals in updates.items():
    mask = reg.incident_id == iid
    assert mask.sum() == 1, iid
    for k, v in vals.items():
        reg.loc[mask, k] = v

# fortress_protocol_2022: loai do loi thu thap thuc, ghi chu ro, khong dung trong eval
mask = reg.incident_id == "fortress_protocol_2022"
assert mask.sum() == 1
reg.loc[mask, "endpoint_type"] = "collection_failed_excluded"
reg.loc[mask, "endpoint_confirmed"] = False
reg.loc[mask, "endpoint_basis"] = "none"
reg.loc[mask, "type_of_first_endpoint_action"] = "none"
old_note = reg.loc[mask, "notes"].iloc[0]
reg.loc[mask, "notes"] = old_note + (
    " || DA LOAI KHOI N=37: thu thap thuc qua expand_and_build_trajectory"
    " loi 2 lan doc lap (BscTraceAPIError: het so lan retry (5), loi cuoi:"
    " None) - loi THAT trong pipeline khi goi BSCTrace nhieu lan cho dia"
    " chi nay, KHONG phai het quota chung (da xac nhan 1 lenh don le van"
    " hoat dong). Theo quy tac khong sua code decode/trace de hop incident"
    " moi va quy tac du phong (bo incident, khong thay the), dong nay GIU"
    " LAI (append-only) nhung KHONG dung trong feature build / evaluation."
)

reg.to_csv(reg_path, index=False)
print("Da cap nhat. Cac dong v4_heldout dung duoc (endpoint_type != collection_failed_excluded):")
sub = reg[reg.eval_tier == "v4_heldout"]
print(sub[["incident_id", "endpoint_type", "endpoint_confirmed", "endpoint_basis", "type_of_first_endpoint_action"]].to_string())
