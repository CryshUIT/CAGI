"""NSS 2026 - Viec 2 (dao sau, xac nhan pham vi anh huong): kiem tra CO HE
THONG tren 15 incident xem co bi mat giao dich SOM (giua start_block va
block dau tien trong trajectory da decode) giong hackerdao_2022 khong.

Doc lai file RAW da thu thap (khong goi API moi) cho dia chi seed cua tung
incident, doi chieu voi block dau tien trong <incident>_events.json.
Ho tro ca 2 dinh dang: Etherscan-style (txlist/tokentx/txlistinternal,
blockNumber thap phan) va Alchemy-style/BscTrace (assettransfers, blockNum hex).
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVAL15 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022", "paraluni_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024", "xkingdom_2024",
]


def load_raw_blocks_for_seed(chain: str, seed: str, incident_id: str) -> list:
    """Doc TAT CA file raw da thu thap cho (chain, seed, incident) - tra ve
    list (block_number:int, tx_hash, event_kind) cua MOI entry co seed la
    from/src HOAC to/dst (khong loc chieu, chi de xac dinh block co giao
    dich lien quan hay khong - viec loc chieu/dieu kien value_share da co
    trong builder.py, o day CHI kiem tra "co ton tai giao dich thoi").
    """
    seed_l = seed.lower()
    folder = ROOT / "data" / "raw" / chain / seed_l / incident_id
    if not folder.exists():
        return []
    out = []
    for fp in glob.glob(str(folder / "*.json")):
        try:
            d = json.loads(Path(fp).read_text(encoding="utf-8"))
        except Exception:
            continue
        resp = d.get("response", {})
        result = resp.get("result")
        if isinstance(result, list):  # Etherscan-style (txlist/tokentx/txlistinternal)
            for tx in result:
                bn = tx.get("blockNumber")
                if bn is None:
                    continue
                try:
                    out.append((int(bn), tx.get("hash"), Path(fp).name.split("_w")[0]))
                except (ValueError, TypeError):
                    continue
        elif isinstance(result, dict) and "transfers" in result:  # Alchemy/BscTrace-style
            for tx in result["transfers"]:
                bn_hex = tx.get("blockNum")
                if not bn_hex:
                    continue
                try:
                    out.append((int(bn_hex, 16), tx.get("hash"), "assettransfers"))
                except (ValueError, TypeError):
                    continue
    return out


def main() -> None:
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry.csv").set_index("incident_id")
    rows = []
    for inc in EVAL15:
        r = reg.loc[inc]
        chain = r["chain_primary"]
        seed = r["seed_address"]
        start_block = int(r["start_block"])

        events_path = ROOT / "data" / "processed" / f"{inc}_events.json"
        events = json.loads(events_path.read_text(encoding="utf-8"))
        decoded_blocks = [e["block_number"] for e in events]
        min_decoded_block = min(decoded_blocks) if decoded_blocks else None

        raw = load_raw_blocks_for_seed(chain, seed, inc)
        raw_blocks_in_window = sorted(set(b for b, _, _ in raw if b >= start_block))
        min_raw_block = raw_blocks_in_window[0] if raw_blocks_in_window else None

        gap_txs = []
        if min_decoded_block is not None:
            gap_txs = sorted(set((b, h, k) for b, h, k in raw if start_block <= b < min_decoded_block))

        rows.append({
            "incident_id": inc, "chain": chain, "start_block": start_block,
            "min_raw_block_in_window": min_raw_block, "min_decoded_block": min_decoded_block,
            "block_gap": (min_decoded_block - min_raw_block) if (min_raw_block and min_decoded_block) else None,
            "n_raw_files_found": len(raw) > 0,
            "n_distinct_raw_tx_before_first_decoded": len(gap_txs),
            "gap_tx_hashes": ";".join(h[:12] for _, h, _ in gap_txs[:10]),
        })
        print(f"{inc:32s} start_block={start_block:>10} min_raw={str(min_raw_block):>10} "
              f"min_decoded={str(min_decoded_block):>10} raw_tx_truoc_decode_dau_tien={len(gap_txs)}")

    out_df = pd.DataFrame(rows)
    out_df.to_csv(ROOT / "results" / "tables" / "early_gap_audit_15incidents_2026-09-22.csv", index=False)
    print("\nDa luu results/tables/early_gap_audit_15incidents_2026-09-22.csv")


if __name__ == "__main__":
    main()
