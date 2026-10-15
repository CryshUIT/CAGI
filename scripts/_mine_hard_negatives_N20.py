"""Checkpoint B: khai thac hard-negative cho 5 incident moi (N20), tuan tu
theo thu tu Zunami -> Onyx -> Beanstalk -> Hedgey -> Cork.

KHONG ghi de metadata/hard_negative_registry.csv/incident_registry.csv goc.
Dung lai mine_hard_negatives_for_incident() CO SAN (khong doi logic/tham so),
chi: (1) tro registry_path/output path sang ban N20 rieng, (2) dinh nghia
INCIDENT_MINING_CONTRACTS cho 5 incident moi O MUC RUNTIME (khong sua file
nguon), (3) wrap moi lan goi fetch_contract_counterparties bang try/except
de phat hien EtherscanAPIError do cham max_windows=200 (enumeration_truncated),
CHI GHI NHAN, khong doi hanh vi/cap.

Neu 1 incident bi truncated: DUNG xu ly incident do (khong lay mau/khong
dung danh sach bi cat), danh dau pending, chuyen sang incident tiep theo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.collect import hard_negative_miner as hnm
from src.collect.etherscan_client import EtherscanAPIError

REGISTRY_N20 = Path("metadata/incident_registry_N20.csv")
OUT_HN_REGISTRY = Path("metadata/hard_negative_registry_N20.csv")
OUT_LOG = Path("results/reports/mining_truncation_log_N20_2026-10-14.json")

NEW_INCIDENT_IDS_ORDER = [
    "zunami_protocol_2023", "onyx_protocol_2023", "beanstalk_farms_2022",
    "hedgey_finance_2024", "cork_protocol_2025",
]

# Hop dong mining cho 5 incident moi - dung CHINH contract da xac nhan THAT
# xuat hien trong outbound trajectory/provenance cua tung incident (cung
# nguyen tac docstring INCIDENT_MINING_CONTRACTS trong hard_negative_miner.py).
NEW_MINING_CONTRACTS = {
    "zunami_protocol_2023": [
        ("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"),
    ],
    "onyx_protocol_2023": [
        ("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"),
    ],
    "beanstalk_farms_2022": [
        ("eth", "Uniswap V2", "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"),
    ],
    "hedgey_finance_2024": [
        ("eth", "Uniswap: Universal Router (v1.2 variant)", "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad"),
    ],
    "cork_protocol_2025": [
        ("eth", "Uniswap: Universal Router v2", "0x66a9893cc07d91d95644aedd05d03f95e1dba8af"),
    ],
}


def safe_fetch_contract_counterparties(chain, contract_address, incident_id, start_block, end_block, do_collect):
    """Wrapper CHI-GHI-NHAN quanh fetch_contract_counterparties() goc - khong
    doi logic/cap ben trong. Bat EtherscanAPIError do cham max_windows=200,
    tra ve (candidates_or_None, truncated_bool, error_message_or_None)."""
    try:
        candidates = hnm.fetch_contract_counterparties(
            chain, contract_address, incident_id, start_block, end_block, do_collect=do_collect,
        )
        return candidates, False, None
    except EtherscanAPIError as exc:
        msg = str(exc)
        if "max_windows" in msg or "Vượt quá" in msg:
            return None, True, msg
        raise


def main() -> None:
    reg = pd.read_csv(REGISTRY_N20)
    # excluded toan cuc: known malicious (AMLGuard + incident_registry.csv GOC)
    # + TOAN BO seed_address cua 5 incident moi (tranh tu-chon chinh minh/nhau)
    # + TOAN BO hard-negative DA CO cua 15 incident cu (tranh trung dia chi
    # giua incident cu va moi - group leakage).
    global_excluded = hnm.load_known_malicious_addresses()
    for iid in NEW_INCIDENT_IDS_ORDER:
        global_excluded.add(reg[reg.incident_id == iid]["seed_address"].iloc[0].lower())
    old_hn = pd.read_csv("metadata/hard_negative_registry.csv")
    global_excluded |= {a.lower() for a in old_hn["seed_address"].dropna()}
    old_hn2_path = Path("metadata/hard_negative_registry_v2_complexity.csv")
    if old_hn2_path.exists():
        old_hn2 = pd.read_csv(old_hn2_path)
        global_excluded |= {a.lower() for a in old_hn2["seed_address"].dropna()}

    truncation_log = {}
    reports = {}

    for iid in NEW_INCIDENT_IDS_ORDER:
        row = reg[reg.incident_id == iid].iloc[0].to_dict()
        contracts = NEW_MINING_CONTRACTS[iid]

        # --- Mo phong lai vong lap ben trong mine_hard_negatives_for_incident,
        # nhung dung safe_fetch_contract_counterparties() de bat truncation ---
        excluded = set(global_excluded)
        excluded.add(row["seed_address"].lower())

        protocol_map = hnm.load_protocol_map()
        bridge_index = hnm.build_verified_bridge_address_index(protocol_map)
        mixer_index = hnm.build_verified_mixer_address_index(protocol_map)

        report = hnm.MiningReport(parent_incident_id=iid)
        incident_truncated = False
        trunc_detail = None

        for chain, protocol_name, contract_address in contracts:
            if len(report.accepted) >= 25:
                break
            start_block, end_block = hnm._mining_window(chain, int(row["start_block"]), iid)
            candidates, truncated, err = safe_fetch_contract_counterparties(
                chain, contract_address, iid, start_block, end_block, do_collect=True,
            )
            if truncated:
                incident_truncated = True
                trunc_detail = {"contract": contract_address, "protocol": protocol_name, "error": err}
                break  # KHONG dung danh sach bi cat, dung lai incident nay

            is_mixer = contract_address.lower() in hnm.MIXER_CONTRACTS
            for candidate in candidates:
                if len(report.accepted) >= 25 or report.candidates_checked >= 150:
                    break
                if candidate in excluded:
                    continue
                report.candidates_checked += 1
                client = hnm._make_client(chain)
                hnm.collect_address_raw_data(client, chain, candidate, iid, start_block, end_block)
                passed, reason, actual_block = hnm._passes_structural_filter(
                    chain, candidate, contract_address, iid, is_mixer, start_block, end_block,
                    bridge_index, mixer_index,
                )
                result = hnm.MiningResult(
                    address=candidate, chain=chain, contract_used=contract_address,
                    protocol_name=protocol_name, block_number=actual_block if passed else start_block,
                    reject_reason=None if passed else reason,
                )
                if passed:
                    report.accepted.append(result)
                    excluded.add(candidate)
                else:
                    report.rejected.append(result)

        truncation_log[iid] = {"truncated": incident_truncated, "detail": trunc_detail}
        if incident_truncated:
            print(f"*** {iid}: ENUMERATION TRUNCATED tai {trunc_detail['contract']} "
                  f"({trunc_detail['protocol']}) - DUNG incident nay, danh dau pending ***")
            continue

        reports[iid] = report
        global_excluded |= {r.address for r in report.accepted}
        print(f"{iid}: accepted={len(report.accepted)} checked={report.candidates_checked} "
              f"rejected={len(report.rejected)}")

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")

    if reports:
        hnm.write_hard_negative_registry(reports, path=OUT_HN_REGISTRY, id_infix="hn20")
        print(f"\nDa ghi {OUT_HN_REGISTRY}")

    n_truncated = sum(1 for v in truncation_log.values() if v["truncated"])
    print(f"\n=== TOM TAT: {len(reports)}/{len(NEW_INCIDENT_IDS_ORDER)} incident mine thanh cong, "
          f"{n_truncated} bi truncated (pending) ===")


if __name__ == "__main__":
    main()
