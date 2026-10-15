"""N30 Phase 2: khai thac hard-negative (vong chinh, target=25) cho Uranium
Finance (Uniswap V2 - DEX, khong phai mixer) va 0xInfini (LI.FI Diamond -
bridge, da co trong allowlist).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.collect import hard_negative_miner as hnm
from src.collect.etherscan_client import EtherscanAPIError

REG = pd.read_csv("metadata/incident_registry_N30.csv")
OUT_HN_REGISTRY = Path("metadata/hard_negative_registry_N30_batch1_remainder.csv")
OUT_LOG = Path("results/reports/mining_truncation_log_N30_batch1_remainder_2026-10-14.json")

IDS_ORDER = ["uranium_finance_2021", "0xinfini_2025"]
MINING_CONTRACTS = {
    "uranium_finance_2021": ("eth", "Uniswap V2", "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"),
    "0xinfini_2025": ("eth", "Uniswap: Universal Router v2", "0x66a9893cc07d91d95644aedd05d03f95e1dba8af"),
}


def main() -> None:
    global_excluded = hnm.load_known_malicious_addresses()
    for p in ["metadata/hard_negative_registry.csv", "metadata/hard_negative_registry_N20.csv",
              "metadata/hard_negative_registry_v2_complexity.csv",
              "metadata/hard_negative_registry_v2_complexity_N20.csv",
              "metadata/hard_negative_registry_N30_batch1.csv"]:
        if Path(p).exists():
            global_excluded |= {a.lower() for a in pd.read_csv(p)["seed_address"].dropna()}
    for iid in REG.incident_id:
        global_excluded.add(REG[REG.incident_id == iid]["seed_address"].iloc[0].lower())

    truncation_log = {}
    reports = {}
    for iid in IDS_ORDER:
        row = REG[REG.incident_id == iid].iloc[0]
        chain, protocol_name, contract = MINING_CONTRACTS[iid]
        excluded = set(global_excluded)

        protocol_map = hnm.load_protocol_map()
        bridge_index = hnm.build_verified_bridge_address_index(protocol_map)
        mixer_index = hnm.build_verified_mixer_address_index(protocol_map)

        report = hnm.MiningReport(parent_incident_id=iid)
        truncated, detail = False, None
        start_block, end_block = hnm._mining_window(chain, int(row.start_block), iid)
        try:
            candidates = hnm.fetch_contract_counterparties(chain, contract, iid, start_block, end_block, do_collect=True)
        except EtherscanAPIError as exc:
            msg = str(exc)
            if "max_windows" in msg or "Vượt quá" in msg:
                truncated, detail = True, msg
                candidates = []
            else:
                raise

        if not truncated:
            is_mixer = contract.lower() in hnm.MIXER_CONTRACTS
            for candidate in candidates:
                if len(report.accepted) >= 25 or report.candidates_checked >= 150:
                    break
                if candidate in excluded:
                    continue
                report.candidates_checked += 1
                client = hnm._make_client(chain)
                hnm.collect_address_raw_data(client, chain, candidate, iid, start_block, end_block)
                passed, reason, actual_block = hnm._passes_structural_filter(
                    chain, candidate, contract, iid, is_mixer, start_block, end_block, bridge_index, mixer_index,
                )
                result = hnm.MiningResult(
                    address=candidate, chain=chain, contract_used=contract, protocol_name=protocol_name,
                    block_number=actual_block if passed else start_block,
                    reject_reason=None if passed else reason,
                )
                if passed:
                    report.accepted.append(result)
                    excluded.add(candidate)
                else:
                    report.rejected.append(result)

        truncation_log[iid] = {"truncated": truncated, "detail": detail}
        if truncated:
            print(f"*** {iid}: TRUNCATED - bo qua, danh dau pending ***", flush=True)
            continue
        reports[iid] = report
        global_excluded |= {r.address for r in report.accepted}
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} "
              f"rejected={len(report.rejected)}", flush=True)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
    if reports:
        hnm.write_hard_negative_registry(reports, path=OUT_HN_REGISTRY, id_infix="hn30")
        print(f"\nDa ghi {OUT_HN_REGISTRY}")


if __name__ == "__main__":
    main()
