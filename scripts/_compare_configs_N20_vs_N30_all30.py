"""Dung tat ca 30 incident (positive) duoi config_N20.yaml VA config_N30.yaml
(CHI dung cache, do_collect=False) de xac dinh CHINH XAC danh sach incident
nao co trajectory (n_actions / chuoi event_type) khac nhau giua 2 config -
dung cho sensitivity (c) cua analysis_plan_N30.md."""
from __future__ import annotations

import pandas as pd

from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

cfg20 = load_trajectory_config("configs/data_N20.yaml")
cfg30 = load_trajectory_config("configs/data_N30.yaml")

r = pd.read_csv("metadata/incident_registry_N30.csv")
r = r[(r["eval_tier"] == "primary") & (r["label"] == 1)].reset_index(drop=True)

print(f"{'incident_id':<30}{'n20':>8}{'n30':>8}{'same_len':>10}{'same_seq':>10}")
diffs = []
for _, row in r.iterrows():
    iid = row.incident_id
    t20, _, _ = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), iid, 1,
        config=cfg20, do_collect=False, max_iterations=None,
    )
    t30, _, _ = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), iid, 1,
        config=cfg30, do_collect=False, max_iterations=None,
    )
    seq20 = [a.event_type for a in t20.actions]
    seq30 = [a.event_type for a in t30.actions]
    same_len = len(seq20) == len(seq30)
    same_seq = seq20 == seq30
    print(f"{iid:<30}{len(seq20):>8}{len(seq30):>8}{str(same_len):>10}{str(same_seq):>10}")
    if not same_seq:
        diffs.append((iid, len(seq20), len(seq30)))

print()
print("=== INCIDENT KHAC NHAU GIUA config_N20 va config_N30 ===")
for iid, n20, n30 in diffs:
    print(f"  {iid}: n20={n20} n30={n30}")
