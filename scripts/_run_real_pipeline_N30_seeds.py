"""N30: chay THAT expand_and_build_trajectory (do_collect=True) cho cac seed
moi, DUNG incident_id THAT (khop incident_registry_N30.csv), dung
config=data_N30.yaml. Ghi output events.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from src.pipeline.incident_pipeline import PROCESSED_DIR, expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

REG = pd.read_csv("metadata/incident_registry_N30.csv")


def main(ids):
    config = load_trajectory_config("configs/data_N30.yaml")
    for iid in ids:
        row = REG[REG.incident_id == iid].iloc[0]
        chain, seed, start_block, label = row["chain_primary"], row["seed_address"], int(row["start_block"]), int(row["label"])
        print(f"\n=== {iid} (seed={seed}, chain={chain}, start_block={start_block}) ===", flush=True)
        traj, provenance_events, processed = expand_and_build_trajectory(
            chain, seed, start_block, iid, label, config=config, do_collect=True,
        )
        print(f"n_actions={len(traj)}, dia chi da xu ly (frontier)={len(processed)}: {processed}", flush=True)
        n_mixer = sum(1 for a in traj.actions if a.event_type == "mixer_or_exit")
        n_bridge = sum(1 for a in traj.actions if a.event_type in ("bridge_deposit", "bridge_withdraw"))
        print(f"n_mixer_or_exit={n_mixer} n_bridge={n_bridge}", flush=True)
        for i, a in enumerate(traj.actions[:15]):
            print(f"  [{i}] {a.event_type:16s} {a.src[:10]}->{a.dst[:10]} amount_norm={a.amount_norm:.4f} protocol={a.protocol}")
        if len(traj.actions) > 15:
            print(f"  ... con {len(traj.actions)-15} action nua")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = PROCESSED_DIR / f"{iid}_events.json"
        out_path.write_text(
            json.dumps([json.loads(a.model_dump_json()) for a in traj.actions], indent=2), encoding="utf-8",
        )
        print(f"Da luu {out_path}")


if __name__ == "__main__":
    ids = sys.argv[1:] if len(sys.argv) > 1 else []
    main(ids)
