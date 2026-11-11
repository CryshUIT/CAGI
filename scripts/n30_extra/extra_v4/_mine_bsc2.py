# -*- coding: utf-8 -*-
"""Mine hard-negative (TARGET=50) cho pancakebunny_2021 va rikkei_finance_2022
(2 incident BSC da thu thap thanh cong). Chi chay khi BSCTrace API hoat
dong lai."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.collect.hard_negative_miner as hnm
from src.collect.hard_negative_miner import (
    compute_min_candidate_events,
    load_known_malicious_addresses,
    mine_hard_negatives_for_incident,
    write_hard_negative_registry,
)
from src.collect.etherscan_client import EtherscanAPIError
from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REG = pd.read_csv(REPO_ROOT / "metadata" / "incident_registry_final_heldout.csv")
OUT_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_bsc2_new.csv"
OUT_LOG = REPO_ROOT / "results" / "reports" / "extra_v4" / "mining_truncation_log_bsc2_2026-11-05.json"
TARGET_PER_INCIDENT = 50
MAX_CANDIDATES_CHECKED = 500

IDS_ORDER = ["pancakebunny_2021", "rikkei_finance_2022"]

MINING_CONTRACTS = {
    # pancakebunny: 9/15 action swap toi dia chi THAT trong trajectory - dung contract nay.
    "pancakebunny_2021": [("bsc", "Swap counterparty thuc trong trajectory pancakebunny_2021", "0xc603a00595d5f8ea8d93c5c338c00ff29dba6258")],
    # rikkei: 38/38 action mixer_or_exit toi TornadoProxyLight (BSC) - dung chinh contract nay.
    "rikkei_finance_2022": [("bsc", "TornadoProxyLight (BSC)", "0x0d5550d52428e7e3175bfc9550207e4ad3859b17")],
}


def main():
    config = load_trajectory_config(str(REPO_ROOT / "configs" / "data_final_heldout.yaml"))
    for iid, contracts in MINING_CONTRACTS.items():
        hnm.INCIDENT_MINING_CONTRACTS[iid] = contracts

    existing_hn_addrs = set()
    for p in [
        "metadata/hard_negative_registry_N30_combined.csv",
        "metadata/hard_negative_registry_v2_complexity_N30_combined.csv",
        "metadata/hard_negative_registry_v2_complexity_N37_new.csv",
        "metadata/hard_negative_registry_final_heldout_new.csv",
    ]:
        fp = REPO_ROOT / p
        if fp.exists():
            existing_hn_addrs |= {a.lower() for a in pd.read_csv(fp)["seed_address"].dropna()}
    global_excluded = load_known_malicious_addresses() | existing_hn_addrs
    for iid in REG.incident_id:
        global_excluded.add(REG[REG.incident_id == iid]["seed_address"].iloc[0].lower())

    reports = {}
    truncation_log = {}
    for iid in IDS_ORDER:
        row = REG[REG.incident_id == iid].iloc[0].to_dict()
        traj, _, _ = expand_and_build_trajectory(
            row["chain_primary"], row["seed_address"], int(row["start_block"]), iid, 1,
            config=config, do_collect=False, max_iterations=None,
        )
        pos_len = len(traj.actions)
        min_events = compute_min_candidate_events(pos_len)
        print(f"\n=== {iid} (positive_len={pos_len}, min_candidate_events={min_events}) ===", flush=True)
        try:
            report = mine_hard_negatives_for_incident(
                iid, row, target_count=TARGET_PER_INCIDENT, max_candidates_checked=MAX_CANDIDATES_CHECKED,
                excluded_addresses=global_excluded, do_collect=True, min_candidate_events=min_events,
            )
            truncation_log[iid] = {"truncated": False, "detail": None}
        except EtherscanAPIError as exc:
            msg = str(exc)
            if "max_windows" in msg or "Vượt quá" in msg:
                truncation_log[iid] = {"truncated": True, "detail": msg}
                print(f"*** {iid}: TRUNCATED - bo qua ***", flush=True)
                continue
            raise
        except Exception as exc:
            truncation_log[iid] = {"truncated": False, "error": f"{type(exc).__name__}: {exc}"}
            print(f"*** {iid}: LOI KHI MINING: {type(exc).__name__}: {exc} - bo qua, ghi log ***", flush=True)
            continue
        reports[iid] = report
        global_excluded |= {r.address for r in report.accepted}
        flag = " *** DUOI TARGET 50 - DANH DAU ***" if len(report.accepted) < TARGET_PER_INCIDENT else ""
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} rejected={len(report.rejected)}{flag}", flush=True)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
    if reports:
        write_hard_negative_registry(reports, path=OUT_PATH, id_infix="hnbsc2")
        print(f"\nDa ghi {OUT_PATH}")
    else:
        print("\nKHONG co report nao.")


if __name__ == "__main__":
    main()
