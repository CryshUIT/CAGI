"""Checkpoint C (sua loi phat hien): chay THAT expand_and_build_trajectory
(do_collect=True) cho 5 seed address moi, DUNG incident_id THAT (khop
metadata/incident_registry_N20.csv) - truoc do cac buoc kiem tra provenance
(Checkpoint truoc) dung incident_id tam ("..._provenance_check"), nen cache
khong nam dung cho pipeline chinh thuc doc (cache scoped theo incident_id,
xem annotation_guide.md bug #6). Day la nguyen nhan n_actions=0 cho ca 5
incident moi trong lan build feature truoc.

Dung config=data_N20.yaml (co Universal Router cho Hedgey/Cork). Ghi output
events.json vao data/processed/{incident_id}_events.json (file MOI, khong
trung ten voi 15 incident cu).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.pipeline.incident_pipeline import PROCESSED_DIR, expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

REG = pd.read_csv("metadata/incident_registry_N20.csv")
NEW_IDS = [
    "zunami_protocol_2023", "onyx_protocol_2023", "beanstalk_farms_2022",
    "hedgey_finance_2024", "cork_protocol_2025",
]


def main():
    config = load_trajectory_config("configs/data_N20.yaml")
    for iid in NEW_IDS:
        row = REG[REG.incident_id == iid].iloc[0]
        chain, seed, start_block, label = row["chain_primary"], row["seed_address"], int(row["start_block"]), int(row["label"])
        print(f"\n=== {iid} (seed={seed}, chain={chain}, start_block={start_block}) ===", flush=True)
        traj, provenance_events, processed = expand_and_build_trajectory(
            chain, seed, start_block, iid, label, config=config, do_collect=True,
        )
        print(f"n_actions={len(traj)}, dia chi da xu ly (frontier)={len(processed)}: {processed}", flush=True)
        for i, a in enumerate(traj.actions[:10]):
            print(f"  [{i}] {a.event_type:16s} {a.src[:10]}->{a.dst[:10]} amount_norm={a.amount_norm:.4f} protocol={a.protocol}")
        if len(traj.actions) > 10:
            print(f"  ... con {len(traj.actions)-10} action nua")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = PROCESSED_DIR / f"{iid}_events.json"
        out_path.write_text(
            json.dumps([json.loads(a.model_dump_json()) for a in traj.actions], indent=2), encoding="utf-8",
        )
        print(f"Da luu {out_path}")


if __name__ == "__main__":
    main()
