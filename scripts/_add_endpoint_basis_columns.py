"""Them cot endpoint_basis + 3 cot dem (n_mixer_or_exit, n_bridge_deposit,
type_of_first_endpoint_action) vao incident_registry_N30.csv. CHI THEM COT
MOI, KHONG doi endpoint_confirmed hay bat ky truong nao khac."""
from __future__ import annotations

import pandas as pd

from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

cfg = load_trajectory_config("configs/data_N30.yaml")
r = pd.read_csv("metadata/incident_registry_N30.csv")

V1_INHERITED = {"wault_finance_2021", "paraluni_2022"}
OTHER_EVENT_TYPE = {"bsc_token_hub_2022"}

n_mixer_col, n_bridge_col, first_type_col, basis_col = [], [], [], []

primary_positive = r[(r["eval_tier"] == "primary") & (r["label"] == 1)]
cache = {}
for _, row in primary_positive.iterrows():
    iid = row.incident_id
    t, _, _ = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), iid, 1,
        config=cfg, do_collect=False, max_iterations=None,
    )
    n_mixer = sum(1 for a in t.actions if a.event_type == "mixer_or_exit")
    n_bridge = sum(1 for a in t.actions if a.event_type == "bridge_deposit")
    first_type = None
    for a in t.actions:
        if a.event_type in ("mixer_or_exit", "bridge_deposit"):
            first_type = a.event_type
            break
    cache[iid] = (n_mixer, n_bridge, first_type)
    print(iid, n_mixer, n_bridge, first_type, flush=True)

for _, row in r.iterrows():
    iid = row.incident_id
    if iid not in cache:
        n_mixer_col.append(pd.NA)
        n_bridge_col.append(pd.NA)
        first_type_col.append(pd.NA)
        basis_col.append(pd.NA)
        continue
    n_mixer, n_bridge, first_type = cache[iid]
    n_mixer_col.append(n_mixer)
    n_bridge_col.append(n_bridge)
    first_type_col.append(first_type if first_type else "none")

    if not bool(row.endpoint_confirmed):
        basis = "none"
    elif iid in V1_INHERITED:
        basis = "v1_inherited_report_only"
    elif iid in OTHER_EVENT_TYPE:
        basis = "other_event_type"
    elif n_mixer >= 1 or n_bridge >= 1:
        basis = "onchain_value_match"
    else:
        basis = "none"  # khong nen xay ra, giu an toan
    basis_col.append(basis)

r["n_mixer_or_exit"] = n_mixer_col
r["n_bridge_deposit"] = n_bridge_col
r["type_of_first_endpoint_action"] = first_type_col
r["endpoint_basis"] = basis_col

r.to_csv("metadata/incident_registry_N30.csv", index=False)
print("\nDa them 4 cot moi. Phan bo endpoint_basis:")
print(r[r.eval_tier == "primary"].endpoint_basis.value_counts(dropna=False))
