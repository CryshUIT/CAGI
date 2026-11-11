# -*- coding: utf-8 -*-
"""Thu thap rieng Spartan Protocol + Allbridge (lan nay BSC quota da nap)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.pipeline.incident_pipeline import PROCESSED_DIR, expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

REG = pd.read_csv(ROOT / "metadata" / "incident_registry_final_heldout.csv")
IDS = ["spartan_protocol_2021", "allbridge_2023"]

results = {}


def main():
    config = load_trajectory_config(str(ROOT / "configs" / "data_final_heldout.yaml"))
    for iid in IDS:
        row = REG[REG.incident_id == iid].iloc[0]
        chain, seed, start_block, label = row["chain_primary"], row["seed_address"], int(row["start_block"]), int(row["label"])
        print(f"\n=== {iid} (seed={seed}, chain={chain}, start_block={start_block}) ===", flush=True)
        try:
            traj, provenance_events, processed = expand_and_build_trajectory(
                chain, seed, start_block, iid, label, config=config, do_collect=True,
            )
        except Exception as exc:
            print(f"*** LOI khi thu thap {iid}: {type(exc).__name__}: {exc} ***", flush=True)
            results[iid] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
            continue

        n_actions = len(traj.actions)
        n_mixer = sum(1 for a in traj.actions if a.event_type == "mixer_or_exit")
        n_bridge = sum(1 for a in traj.actions if a.event_type in ("bridge_deposit", "bridge_withdraw"))
        n_bridge_deposit = sum(1 for a in traj.actions if a.event_type == "bridge_deposit")
        n_lending_deposit = sum(1 for a in traj.actions if a.event_type == "lending_deposit")
        terminal = [a for a in traj.actions if a.event_type in ("bridge_deposit", "mixer_or_exit", "lending_deposit")]
        first_terminal_type = terminal[0].event_type if terminal else "none"

        print(f"n_actions={n_actions}, dia chi da xu ly (frontier)={len(processed)}: {processed}", flush=True)
        print(f"n_mixer_or_exit={n_mixer} n_bridge_deposit={n_bridge_deposit} n_bridge_total={n_bridge} "
              f"n_lending_deposit={n_lending_deposit} first_terminal_type={first_terminal_type}", flush=True)
        for i, a in enumerate(traj.actions[:20]):
            print(f"  [{i}] {a.event_type:16s} {a.src[:10]}->{a.dst[:10]} amount_norm={a.amount_norm:.4f} protocol={a.protocol}")
        if n_actions > 20:
            print(f"  ... con {n_actions - 20} action nua")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = PROCESSED_DIR / f"{iid}_events.json"
        out_path.write_text(
            json.dumps([json.loads(a.model_dump_json()) for a in traj.actions], indent=2), encoding="utf-8",
        )
        print(f"Da luu {out_path}")

        results[iid] = {
            "status": "ok", "n_actions": n_actions, "n_mixer_or_exit": n_mixer,
            "n_bridge_deposit": n_bridge_deposit, "n_bridge_total": n_bridge,
            "n_lending_deposit": n_lending_deposit, "first_terminal_type": first_terminal_type,
            "processed_addresses": processed,
        }

    out_json = ROOT / "results" / "reports" / "extra_v4" / "collect_spartan_allbridge_summary.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n\nDa luu {out_json}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
