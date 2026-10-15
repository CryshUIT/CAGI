"""N30 lo 2, batch 1: vong mine 'v2_complexity' (he thong, TARGET=10) cho
Lendhub, THORChain-2, Popsicle Finance, HECO Chain/HTX - dung code/tham so
CHINH XAC nhu da dung o N20/lo 1.
"""
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

REG = pd.read_csv("metadata/incident_registry_N30.csv")
OUT_PATH = Path("metadata/hard_negative_registry_v2_complexity_N30_lo2_batch1.csv")
OUT_LOG = Path("results/reports/mining_v2complexity_truncation_log_N30_lo2_batch1_2026-10-15.json")
TARGET_PER_INCIDENT = 10
MAX_CANDIDATES_CHECKED = 150

IDS_ORDER = ["lendhub_2023", "thorchain2_2021", "popsicle_finance_2021", "heco_htx_2023"]
MINING_CONTRACTS = {
    "lendhub_2023": ("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"),
    "thorchain2_2021": ("eth", "Uniswap V2", "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"),
    "popsicle_finance_2021": ("eth", "TornadoProxy", "0x722122df12d4e14e13ac3b6895a86e84145b6967"),
    "heco_htx_2023": ("eth", "MetaSwap", "0x881d40237659c251811cec9c364ef91dc08d300c"),
}


def main():
    config_n30 = load_trajectory_config("configs/data_N30.yaml")
    for iid, (chain, protocol_name, contract) in MINING_CONTRACTS.items():
        hnm.INCIDENT_MINING_CONTRACTS[iid] = [(chain, protocol_name, contract)]

    existing_hn_addrs = set()
    for p in ["metadata/hard_negative_registry.csv", "metadata/hard_negative_registry_N20.csv",
              "metadata/hard_negative_registry_v2_complexity.csv", "metadata/hard_negative_registry_v2_complexity_N20.csv",
              "metadata/hard_negative_registry_N30_batch1.csv", "metadata/hard_negative_registry_N30_batch1_remainder.csv",
              "metadata/hard_negative_registry_v2_complexity_N30_batch1.csv",
              "metadata/hard_negative_registry_N30_lo2_batch1.csv"]:
        if Path(p).exists():
            existing_hn_addrs |= {a.lower() for a in pd.read_csv(p)["seed_address"].dropna()}
    global_excluded = load_known_malicious_addresses() | existing_hn_addrs
    for iid in REG.incident_id:
        global_excluded.add(REG[REG.incident_id == iid]["seed_address"].iloc[0].lower())

    reports = {}
    truncation_log = {}
    for iid in IDS_ORDER:
        row = REG[REG.incident_id == iid].iloc[0].to_dict()
        traj, _, _ = expand_and_build_trajectory(
            row["chain_primary"], row["seed_address"], int(row["start_block"]), iid, 1,
            config=config_n30, do_collect=False, max_iterations=None,
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
        reports[iid] = report
        global_excluded |= {r.address for r in report.accepted}
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} rejected={len(report.rejected)}", flush=True)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
    if reports:
        write_hard_negative_registry(reports, path=OUT_PATH, id_infix="hnc30l2")
        print(f"\nDa ghi {OUT_PATH}")


if __name__ == "__main__":
    main()
