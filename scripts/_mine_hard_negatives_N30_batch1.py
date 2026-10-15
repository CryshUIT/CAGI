"""N30 Phase 2: khai thac hard-negative cho cac incident CHO PHEP tiep tuc
(Dough Finance, Prisma Finance, Inverse Finance - TAM DUNG Uranium/0xInfini
theo yeu cau nguoi dung). Vong chinh (target=25) + v2_complexity (target=10),
CUNG code/tham so nhu N20, dung config_N30.

Ghi ket qua NGAY SAU MOI incident (khong doi den cuoi) - tranh bug mat du
lieu khi 1 incident loi giua chung (bai hoc da co san tu
mine_hard_negatives_v2_complexity.py, lan dau viet script nay quen ap dung
va da mat 25 dong Dough Finance khi Prisma loi giua chung). Co kha nang
resume: neu CSV output da co du lieu cho 1 incident, bo qua incident do.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.collect.hard_negative_miner as hnm
from src.collect.etherscan_client import EtherscanAPIError
from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

REG = pd.read_csv("metadata/incident_registry_N30.csv")
OUT_MAIN = Path("metadata/hard_negative_registry_N30_batch1_main.csv")
OUT_V2C = Path("metadata/hard_negative_registry_N30_batch1_v2complexity.csv")
OUT_LOG = Path("results/reports/mining_truncation_log_N30_batch1_2026-10-15.json")

IDS_ORDER = ["dough_finance_2024", "prisma_finance_2024", "inverse_finance_2022_jun"]

MINING_CONTRACTS = {
    "dough_finance_2024": [("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b")],
    "prisma_finance_2024": [("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b")],
    "inverse_finance_2022_jun": [("eth", "Tornado Cash Router", "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b")],
}


def safe_fetch(chain, contract, incident_id, start_block, end_block, do_collect):
    try:
        return hnm.fetch_contract_counterparties(chain, contract, incident_id, start_block, end_block, do_collect=do_collect), False, None
    except EtherscanAPIError as exc:
        msg = str(exc)
        if "max_windows" in msg or "Vượt quá" in msg:
            return None, True, msg
        raise


def load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out = {}
    for iid, grp in df.groupby("parent_incident_id"):
        report = hnm.MiningReport(parent_incident_id=iid)
        for _, r in grp.iterrows():
            report.accepted.append(hnm.MiningResult(
                address=r["seed_address"], chain=r["chain"], contract_used=r["contract_used"],
                protocol_name=r["protocol_name"], block_number=int(r["start_block"]),
            ))
        out[iid] = report
    return out


def append_result(path: Path, iid: str, report, id_infix: str) -> None:
    fieldnames = ["hard_negative_id", "parent_incident_id", "seed_address", "chain",
                  "start_block", "contract_used", "protocol_name", "label"]
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=fieldnames)
    existing = existing[existing["parent_incident_id"] != iid]
    new_rows = [{
        "hard_negative_id": f"{iid}__{id_infix}{i:03d}", "parent_incident_id": iid,
        "seed_address": r.address, "chain": r.chain, "start_block": r.block_number,
        "contract_used": r.contract_used, "protocol_name": r.protocol_name, "label": 0,
    } for i, r in enumerate(report.accepted)]
    out_df = pd.concat([existing, pd.DataFrame(new_rows)], ignore_index=True)
    out_df.to_csv(path, index=False)


def mine_round(iid, row, target_count, max_checked, global_excluded):
    contracts = MINING_CONTRACTS[iid]
    excluded = set(global_excluded)
    excluded.add(row["seed_address"].lower())
    protocol_map = hnm.load_protocol_map()
    bridge_index = hnm.build_verified_bridge_address_index(protocol_map)
    mixer_index = hnm.build_verified_mixer_address_index(protocol_map)
    report = hnm.MiningReport(parent_incident_id=iid)

    for chain, protocol_name, contract in contracts:
        if len(report.accepted) >= target_count:
            break
        start_block, end_block = hnm._mining_window(chain, int(row["start_block"]), iid)
        candidates, trunc, err = safe_fetch(chain, contract, iid, start_block, end_block, True)
        if trunc:
            return report, True, {"contract": contract, "error": err}
        is_mixer = contract.lower() in hnm.MIXER_CONTRACTS
        for candidate in candidates:
            if len(report.accepted) >= target_count or report.candidates_checked >= max_checked:
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
                block_number=actual_block if passed else start_block, reject_reason=None if passed else reason,
            )
            if passed:
                report.accepted.append(result)
                excluded.add(candidate)
            else:
                report.rejected.append(result)
    return report, False, None


def main():
    global_excluded = hnm.load_known_malicious_addresses()
    for p in ["metadata/hard_negative_registry.csv", "metadata/hard_negative_registry_N20.csv",
              "metadata/hard_negative_registry_v2_complexity.csv", "metadata/hard_negative_registry_v2_complexity_N20.csv",
              str(OUT_MAIN), str(OUT_V2C)]:
        if Path(p).exists():
            global_excluded |= {a.lower() for a in pd.read_csv(p)["seed_address"].dropna()}
    for iid in REG.incident_id:
        global_excluded.add(REG[REG.incident_id == iid]["seed_address"].iloc[0].lower())

    done_main = load_existing(OUT_MAIN)
    truncation_log = {}
    if OUT_LOG.exists():
        truncation_log = json.loads(OUT_LOG.read_text(encoding="utf-8"))

    for iid in IDS_ORDER:
        if iid in done_main and len(done_main[iid].accepted) >= 25:
            print(f"\n=== {iid}: vong CHINH DA XONG TU TRUOC ({len(done_main[iid].accepted)} dong) - bo qua ===", flush=True)
            global_excluded |= {r.address for r in done_main[iid].accepted}
            continue
        row = REG[REG.incident_id == iid].iloc[0]
        print(f"\n=== {iid}: vong CHINH (target=25) ===", flush=True)
        rep, trunc, detail = mine_round(iid, row, 25, 150, global_excluded)
        truncation_log[f"{iid}_main"] = {"truncated": trunc, "detail": detail}
        OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
        OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
        if trunc:
            print(f"*** TRUNCATED: {detail} - bo qua incident nay ***", flush=True)
            continue
        append_result(OUT_MAIN, iid, rep, "hn30")
        global_excluded |= {r.address for r in rep.accepted}
        print(f"  accepted={len(rep.accepted)} checked={rep.candidates_checked} rejected={len(rep.rejected)} - DA GHI {OUT_MAIN}", flush=True)

    done_v2c = load_existing(OUT_V2C)
    for iid in IDS_ORDER:
        if iid not in pd.read_csv(OUT_MAIN)["parent_incident_id"].unique() if OUT_MAIN.exists() else True:
            continue
        if iid in done_v2c and len(done_v2c[iid].accepted) > 0:
            print(f"\n=== {iid}: vong v2_complexity DA XONG TU TRUOC ({len(done_v2c[iid].accepted)} dong) - bo qua ===", flush=True)
            global_excluded |= {r.address for r in done_v2c[iid].accepted}
            continue
        row = REG[REG.incident_id == iid].iloc[0]
        cfg = load_trajectory_config("configs/data_N30.yaml")
        traj, _, _ = expand_and_build_trajectory(
            row.chain_primary, row.seed_address, int(row.start_block), iid, int(row.label),
            config=cfg, do_collect=False, max_iterations=None,
        )
        min_events = hnm.compute_min_candidate_events(len(traj))
        print(f"\n=== {iid}: vong v2_complexity (target=10, positive_len={len(traj)}, min_events={min_events}) ===", flush=True)
        rep2, trunc2, detail2 = mine_round(iid, row, 10, 150, global_excluded)
        truncation_log[f"{iid}_v2c"] = {"truncated": trunc2, "detail": detail2}
        OUT_LOG.write_text(json.dumps(truncation_log, indent=2), encoding="utf-8")
        if trunc2:
            print(f"*** TRUNCATED: {detail2} - bo qua vong v2c cho incident nay ***", flush=True)
            continue
        append_result(OUT_V2C, iid, rep2, "hnc30")
        global_excluded |= {r.address for r in rep2.accepted}
        print(f"  accepted={len(rep2.accepted)} checked={rep2.candidates_checked} rejected={len(rep2.rejected)} - DA GHI {OUT_V2C}", flush=True)

    print("\nTOM TAT truncation_log:", truncation_log)


if __name__ == "__main__":
    main()
