# -*- coding: utf-8 -*-
"""N37 (v4_heldout): mine hard-negative 'v2_complexity' (TARGET=10) cho 6
incident moi DA THU THAP THANH CONG (fortress_protocol_2022 bi loai do
loi thu thap thuc - xem decision_log). Dung CHINH XAC code/tham so da
dung cho N30 (`mine_hard_negatives_for_incident`, cua so +-7 ngay doi
xung, KHONG dung before_only override). Mining contract chon tu dia chi
THAT xuat hien trong outbound trajectory cua tung incident (xem
collect_v4_heldout_summary.json) - khong suy doan.
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

REPO_ROOT = Path(__file__).resolve().parents[3]
REG = pd.read_csv(REPO_ROOT / "metadata" / "incident_registry_N37.csv")
OUT_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N37_new.csv"
OUT_LOG = REPO_ROOT / "results" / "reports" / "extra_v4" / "mining_v2complexity_truncation_log_N37_2026-11-05.json"
TARGET_PER_INCIDENT = 10
MAX_CANDIDATES_CHECKED = 150

# CHI 6/7 - fortress_protocol_2022 bi loai (loi thu thap thuc, xem decision_log).
IDS_ORDER = [
    "sturdy_finance_2023", "jimbos_protocol_2023", "rodeo_finance_2023",
    "sentiment_protocol_2023", "pike_finance_2024", "uwu_lend_2024",
]

# Moi contract la dia chi THAT xuat hien trong outbound trajectory da thu
# thap (data/processed/{iid}_events.json), KHONG suy doan:
MINING_CONTRACTS = {
    # sturdy: 16/16 action la mixer_or_exit toi Tornado Cash Router - dung chinh contract nay.
    "sturdy_finance_2023": [("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b")],
    # jimbos: 6/7 bridge_deposit toi LI.FI Diamond (1 toi Stargate) - dung LI.FI (chiem da so).
    "jimbos_protocol_2023": [("arbitrum", "LI.FI Diamond", "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae")],
    # rodeo: 86 bridge_deposit tong, 41 LI.FI Diamond + 39 Across SpokePool (Arbitrum) + 6 Stargate - dung 2 contract chiem da so.
    "rodeo_finance_2023": [
        ("arbitrum", "LI.FI Diamond", "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"),
        ("arbitrum", "Across Protocol SpokePool (Arbitrum)", "0xe35e9842fceaca96570b734083f4a58e8f7c5f2a"),
    ],
    # sentiment: KHONG co bridge/mixer trong trace. Dst pho bien nhat (302/511 action,
    # bao gom hau het swap) la dia chi 1inch v4 AggregationRouter - CUNG dia chi da
    # verify cho chain eth trong protocol_map.yaml (chains:["eth"] - CHUA verify rieng
    # cho arbitrum, nhung day la dia chi THAT xuat hien lap lai trong outbound
    # trajectory cua chinh incident nay, giong tien le hackerdao_2022/radiant_capital).
    "sentiment_protocol_2023": [("arbitrum", "1inch v4 AggregationRouter (dia chi giong eth, chua verify rieng cho arbitrum)", "0x1111111254fb6c44bac0bed2854e76f90643097d")],
    # pike: CHI 1 action (dot USDC qua Circle Token Messenger/CCTP) - dung chinh contract nay.
    "pike_finance_2024": [("arbitrum", "Circle Token Messenger (CCTP)", "0x80c67432656d59144ceff962e8faf8926599bcf8")],
    # uwu_lend: KHONG co bridge/mixer. 1 swap dst THAT xuat hien trong trajectory - dung dia chi nay.
    "uwu_lend_2024": [("eth", "Swap counterparty (dia chi that trong outbound trajectory uwu_lend_2024)", "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640")],
}


def main():
    config_n37 = load_trajectory_config(str(REPO_ROOT / "configs" / "data_N37.yaml"))
    for iid, contracts in MINING_CONTRACTS.items():
        hnm.INCIDENT_MINING_CONTRACTS[iid] = contracts

    existing_hn_addrs = set()
    for p in [
        "metadata/hard_negative_registry.csv", "metadata/hard_negative_registry_N20.csv",
        "metadata/hard_negative_registry_v2_complexity.csv", "metadata/hard_negative_registry_v2_complexity_N20.csv",
        "metadata/hard_negative_registry_N30_combined.csv", "metadata/hard_negative_registry_v2_complexity_N30_combined.csv",
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
            config=config_n37, do_collect=False, max_iterations=None,
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
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} rejected={len(report.rejected)}", flush=True)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
    if reports:
        write_hard_negative_registry(reports, path=OUT_PATH, id_infix="hnc37")
        print(f"\nDa ghi {OUT_PATH}")
    else:
        print("\nKHONG co report nao (tat ca incident loi hoac bi truncate).")


if __name__ == "__main__":
    main()
