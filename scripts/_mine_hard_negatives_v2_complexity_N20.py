"""Checkpoint C'' muc 2: dong bo vong mine "v2_complexity" (he thong, TARGET_
PER_INCIDENT=10, tieu chi do phuc tap qua compute_min_candidate_events) cho
5 incident moi N20 - DUNG Y HET code/tham so da dung trong
scripts/mine_hard_negatives_v2_complexity.py cho 11/15 incident cu (vong nay
la vong CO HE THONG, ap dung cho MOI incident eligible tai thoi diem chay,
KHONG phai ad-hoc rieng incident nao - xem
results/reports/dataset_expansion_N20_checkpointCdoublePrime_2026-10-14.md
muc 1 cho phan loai chi tiet).

KHONG tao control thu cong moi (chi la vong mine "v2_complexity", khong
phai control). KHONG nhan ban cac vong "re-mine bo sung" (bug-fix driven,
ad-hoc, khong lien quan 5 incident moi vi code da fix tu truoc khi chung
duoc tao).

Dung config N20 (co Universal Router) cho buoc BUILD TRAJECTORY (positive)
dung de tinh min_candidate_events - khop voi cach features_v2_N20.parquet
da duoc build sau khi sua loi Checkpoint C'.
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

REG = pd.read_csv("metadata/incident_registry_N20.csv")
OUT_PATH = Path("metadata/hard_negative_registry_v2_complexity_N20.csv")
OUT_LOG = Path("results/reports/mining_v2complexity_truncation_log_N20_2026-10-14.json")
TARGET_PER_INCIDENT = 10  # KHOP CHINH XAC voi mine_hard_negatives_v2_complexity.py goc
MAX_CANDIDATES_CHECKED = 150  # khop goc

NEW_IDS_ORDER = [
    "zunami_protocol_2023", "onyx_protocol_2023", "beanstalk_farms_2022",
    "hedgey_finance_2024", "cork_protocol_2025",
]
# CUNG mining contract da dung o Checkpoint B (dung lai, khong doi)
MINING_CONTRACTS = {
    "zunami_protocol_2023": ("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"),
    "onyx_protocol_2023": ("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"),
    "beanstalk_farms_2022": ("eth", "Uniswap V2", "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"),
    "hedgey_finance_2024": ("eth", "Uniswap: Universal Router (v1.2 variant)", "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad"),
    "cork_protocol_2025": ("eth", "Uniswap: Universal Router v2", "0x66a9893cc07d91d95644aedd05d03f95e1dba8af"),
}


def main():
    config_n20 = load_trajectory_config("configs/data_N20.yaml")
    # mine_hard_negatives_for_incident() doc INCIDENT_MINING_CONTRACTS tu
    # MODULE GLOBAL cua hard_negative_miner.py (khong nhan tham so) - them 5
    # entry moi TAI RUNTIME (khong sua file .py nguon) giong cach da lam o
    # Checkpoint B (_mine_hard_negatives_N20.py), chi khac la lan nay goi
    # THANG ham goc thay vi tu viet lai vong lap.
    for iid, (chain, protocol_name, contract) in MINING_CONTRACTS.items():
        hnm.INCIDENT_MINING_CONTRACTS[iid] = [(chain, protocol_name, contract)]

    existing_hn_addrs = set()
    for p in ["metadata/hard_negative_registry.csv", "metadata/hard_negative_registry_N20.csv",
              "metadata/hard_negative_registry_v2_complexity.csv"]:
        if Path(p).exists():
            existing_hn_addrs |= {a.lower() for a in pd.read_csv(p)["seed_address"].dropna()}
    global_excluded = load_known_malicious_addresses() | existing_hn_addrs
    for iid in NEW_IDS_ORDER:
        global_excluded.add(REG[REG.incident_id == iid]["seed_address"].iloc[0].lower())

    reports = {}
    truncation_log = {}

    for iid in NEW_IDS_ORDER:
        row = REG[REG.incident_id == iid].iloc[0].to_dict()
        chain, protocol_name, contract = MINING_CONTRACTS[iid]

        traj, _, _ = expand_and_build_trajectory(
            chain, row["seed_address"], int(row["start_block"]), iid, 1,
            config=config_n20, do_collect=False, max_iterations=None,
        )
        pos_len = len(traj.actions)
        min_events = compute_min_candidate_events(pos_len)
        print(f"\n=== {iid} (positive_len={pos_len}, min_candidate_events={min_events}, "
              f"target={TARGET_PER_INCIDENT}) ===", flush=True)

        try:
            report = mine_hard_negatives_for_incident(
                iid, row, target_count=TARGET_PER_INCIDENT,
                max_candidates_checked=MAX_CANDIDATES_CHECKED,
                excluded_addresses=global_excluded, do_collect=True,
                min_candidate_events=min_events,
            )
            truncation_log[iid] = {"truncated": False, "detail": None}
        except EtherscanAPIError as exc:
            msg = str(exc)
            if "max_windows" in msg or "Vượt quá" in msg:
                truncation_log[iid] = {"truncated": True, "detail": msg}
                print(f"*** {iid}: TRUNCATED ({msg}) - KHONG dung du lieu cat cut, bo qua ***", flush=True)
                continue
            raise

        reports[iid] = report
        global_excluded |= {r.address for r in report.accepted}
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} "
              f"rejected={len(report.rejected)}", flush=True)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")

    if reports:
        write_hard_negative_registry(reports, path=OUT_PATH, id_infix="hnc20")
        print(f"\nDa ghi {OUT_PATH}")

    n_trunc = sum(1 for v in truncation_log.values() if v["truncated"])
    print(f"\n=== TOM TAT: {len(reports)}/{len(NEW_IDS_ORDER)} thanh cong, {n_trunc} truncated ===")


if __name__ == "__main__":
    main()
