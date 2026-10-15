"""Sinh bang tong hop 30 incident HOAN TOAN tu registry + parquet (khong
go tay bat ky gia tri nao). In markdown table ra stdout va ghi file."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.nested_eval import dedupe_pooled_prefixes
from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

cfg = load_trajectory_config("configs/data_N30.yaml")

r = pd.read_csv("metadata/incident_registry_N30.csv")
r = r[(r["eval_tier"] == "primary") & (r["label"] == 1)].reset_index(drop=True)

df = pd.read_parquet("data/processed/features_v2_N30.parquet")
deduped = dedupe_pooled_prefixes(df)
traj = df.drop_duplicates("source_id")

rows = []
for i, row in r.iterrows():
    iid = row.incident_id
    t, _, _ = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), iid, 1,
        config=cfg, do_collect=False, max_iterations=None,
    )
    n_actions_pipeline = len(t.actions)
    endpoint_idx, endpoint_type_found = None, None
    for j, a in enumerate(t.actions):
        if a.event_type in ("mixer_or_exit", "bridge_deposit"):
            endpoint_idx, endpoint_type_found = j, a.event_type
            break
    pos_str = f"{endpoint_idx + 1}/{n_actions_pipeline}" if endpoint_idx is not None else "khong co"

    grp = traj[traj.group_id == iid]
    n_main = int((grp.kind == "hard_negative_mined").sum())
    n_v2c = int((grp.kind == "hard_negative_mined_v2_complexity").sum())
    n_ctrl = int((grp.kind == "hard_negative_control").sum())

    n_actions_parquet = int(df[df.source_id == iid]["trajectory_len"].iloc[0])
    n_prefix_raw = int((df.source_id == iid).sum())
    n_prefix_dedup = int((deduped.source_id == iid).sum())

    rows.append({
        "idx": i + 1,
        "incident_id": iid,
        "chain_primary": row.chain_primary,
        "n_actions_parquet": n_actions_parquet,
        "n_actions_live_rebuild": n_actions_pipeline,
        "endpoint_confirmed": bool(row.endpoint_confirmed),
        "endpoint_type": row.endpoint_type,
        "vi_tri_endpoint_dau_tien": pos_str,
        "neg_main_that": n_main,
        "neg_v2c_that": n_v2c,
        "neg_control_that": n_ctrl,
        "prefix_row_raw": n_prefix_raw,
        "prefix_row_dedup": n_prefix_dedup,
    })

out = pd.DataFrame(rows)
out.to_csv("results/reports/N30_summary_table_generated_2026-10-15.csv", index=False)

cols = ["idx", "incident_id", "chain_primary", "n_actions_parquet", "n_actions_live_rebuild",
        "endpoint_confirmed", "endpoint_type", "vi_tri_endpoint_dau_tien",
        "neg_main_that", "neg_v2c_that", "neg_control_that", "prefix_row_raw", "prefix_row_dedup"]
print(out[cols].to_string(index=False))

mismatch = out[out.n_actions_parquet != out.n_actions_live_rebuild]
print()
print("=== MISMATCH n_actions_parquet vs n_actions_live_rebuild ===")
print(mismatch[["incident_id", "n_actions_parquet", "n_actions_live_rebuild"]].to_string(index=False) if len(mismatch) else "KHONG CO")

print()
print("TONG: positive=", len(out), "neg_main=", out.neg_main_that.sum(), "neg_v2c=", out.neg_v2c_that.sum(),
      "neg_control=", out.neg_control_that.sum(), "prefix_raw=", df.shape[0], "prefix_dedup=", len(deduped))
