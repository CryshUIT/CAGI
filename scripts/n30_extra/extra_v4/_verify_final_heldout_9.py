# -*- coding: utf-8 -*-
"""Xac minh THAT (API, khong WebSearch) cho 9 incident final held-out da
duoc nguoi dung chot. Voi tx hash da co: goi eth_getTransactionByHash xac
nhan ton tai + from khop seed + lay block/ngay thuc. Voi incident CHUA co
tx hash: dung getblocknobytime de uoc luong block theo ngay bao cao, roi
fetch_normal_txs(seed) trong cua so +-3 ngay quanh do de tim tx ung vien,
in ra TOAN BO de tu xet (KHONG tu doan chon 1 cai duy nhat neu co nhieu
ung vien ngang nhau - se ghi chu ro cho buoc sau quyet dinh giu/loai).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.collect.bsctrace_client import BscTraceClient  # noqa: E402
from src.collect.etherscan_client import EtherscanClient  # noqa: E402

eth_client = EtherscanClient()
bsc_client = BscTraceClient(cache_dir=ROOT / "data" / "raw")

# Anchor xac nhan that 2026-11-04 (Fortress Protocol, xem decision_log N37):
# block 17634663 = 2022-05-08T20:34:42Z. Dung lam moc noi suy xap xi 3s/block
# cho BSC (KHONG chinh xac, chi dung trong cua so tim kiem +-5 ngay roi tu
# xem danh sach tx thuc, khong suy luan block chinh xac tu cong thuc nay).
BSC_ANCHOR_BLOCK = 17634663
BSC_ANCHOR_TS = 1652042082  # 2022-05-08T20:34:42Z
BSC_SEC_PER_BLOCK = 3.0


def bsc_block_for_ts(ts: int) -> int:
    return int(BSC_ANCHOR_BLOCK + (ts - BSC_ANCHOR_TS) / BSC_SEC_PER_BLOCK)

INCIDENTS = [
    dict(name="Harvest Finance", chain="eth", seed="0xf224ab004461540778a914ea397c589b677e27bb",
         claimed_tx="0x35f8d2f572fceaac9288e5d462117850ef2694786992a8c3f6d02612277b0877",
         date_hint="2020-10-26"),
    dict(name="PancakeBunny", chain="bsc", seed="0xa0acc61547f6bd066f7c9663c17a312b6ad7e187",
         claimed_tx="0x897c2de73dd55d7701e1b69ffb3a17b0f4801ced88b0c75fe1551c5fcce6a979",
         date_hint="2021-05-20"),
    dict(name="Orion Protocol", chain="eth", seed="0x837962b686fd5a407fb4e5f92e8be86a230484bd",
         claimed_tx="0xb5599f568D3f3e6113B286d010d2BCa40A7745AA",  # NGHI NGO: do dai giong address, khong phai tx hash
         date_hint="2023-02-02"),
    dict(name="Curve_CRV_ETH_attacker", chain="eth", seed="0xb752def3a1fded45d6c4b9f4a8f18e645b41b324",
         claimed_tx=None, date_hint="2023-07-30"),
    dict(name="Spartan Protocol", chain="bsc", seed="0x3b6e77722e2bbe97c1cfa337b42c0939aeb83671",
         claimed_tx="0xb64ae25b0d836c25d115a9368319902c972a0215bd108ae17b1b9617dfb93af8",
         date_hint="2021-05-02"),
    dict(name="Rikkei Finance", chain="bsc", seed="0x803e0930357ba577dc414b552402f71656c093ab",
         claimed_tx=None, date_hint="2022-04-15"),
    dict(name="Allbridge", chain="bsc", seed="0xc578d755cd56255d3ff6e92e1b6371ba945e3984",
         claimed_tx="0x7ff1364c3b3b296b411965339ed956da5d17058f3164425ce800d64f1aef8210",
         date_hint="2023-04-02"),
    dict(name="Cream Finance (hack 3)", chain="eth", seed="0x24354d31bc9d90f62fe5f2454709c32049cf866b",
         claimed_tx=None, date_hint="2021-10-27"),
    dict(name="Rari Capital Fuse", chain="eth", seed="0x6162759edad730152f0df8115c698a42e666157f",
         claimed_tx="0xd9ee4fc5ee0b8815e6aae20e8bc5697ee49b8a1c76619a008bf534a4084197dc",
         date_hint="2022-04-30"),
]

BLOCKS_PER_HOUR = {"eth": 280, "bsc": 1200}


def get_block_for_timestamp(chain: str, ts: int, closest: str = "before") -> int | None:
    if chain == "bsc":
        return bsc_block_for_ts(ts)
    payload = eth_client._get(chain, {"module": "block", "action": "getblocknobytime", "timestamp": ts, "closest": closest})
    if payload.get("status") == "1":
        return int(payload["result"])
    print(f"    [getblocknobytime loi] {payload}")
    return None


def verify_tx_hash(chain: str, tx_hash: str):
    if len(tx_hash) != 66 or not tx_hash.startswith("0x"):
        return {"valid_format": False, "found": False, "reason": f"do dai {len(tx_hash)} ky tu (ky vong 66, '0x'+64 hex) - KHONG phai tx hash hop le"}
    if chain == "bsc":
        payload = bsc_client._rpc_call("eth_getTransactionByHash", [tx_hash])
        result = payload.get("result")
        if not isinstance(result, dict) or not result:
            return {"valid_format": True, "found": False, "raw": payload}
        block_hex = result.get("blockNumber")
        block_payload = bsc_client._rpc_call("eth_getBlockByNumber", [block_hex, False]) if block_hex else None
    else:
        payload = eth_client._get(chain, {"module": "proxy", "action": "eth_getTransactionByHash", "txhash": tx_hash})
        result = payload.get("result")
        if not isinstance(result, dict) or not result:
            return {"valid_format": True, "found": False, "raw": payload}
        block_hex = result.get("blockNumber")
        block_payload = eth_client._get(chain, {"module": "proxy", "action": "eth_getBlockByNumber", "tag": block_hex, "boolean": "false"}) if block_hex else None
    block_num = int(block_hex, 16) if block_hex else None
    ts = None
    if isinstance(block_payload, dict) and isinstance(block_payload.get("result"), dict):
        ts_field = block_payload["result"].get("timestamp")
        if ts_field:
            ts = int(ts_field, 16)
    return {
        "valid_format": True, "found": True, "from": result.get("from"), "to": result.get("to"),
        "block_number": block_num, "timestamp_utc": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None,
    }


def main():
    out = {}
    for inc in INCIDENTS:
        name, chain, seed, claimed_tx, date_hint = inc["name"], inc["chain"], inc["seed"], inc["claimed_tx"], inc["date_hint"]
        print(f"\n=== {name} ({chain}) seed={seed} date_hint={date_hint} ===", flush=True)
        entry = {"chain": chain, "seed": seed, "date_hint": date_hint}

        try:
            if claimed_tx:
                print(f"  Kiem tra claimed_tx={claimed_tx}", flush=True)
                res = verify_tx_hash(chain, claimed_tx)
                entry["claimed_tx_check"] = res
                print(f"    {res}", flush=True)
        except Exception as exc:
            print(f"    *** LOI khi kiem tra claimed_tx: {type(exc).__name__}: {exc} ***", flush=True)
            entry["claimed_tx_check"] = {"error": f"{type(exc).__name__}: {exc}"}

        if not claimed_tx or not entry.get("claimed_tx_check", {}).get("found"):
            try:
                print(f"  Khong co/khong xac nhan duoc tx hash - tim qua txlist seed quanh {date_hint}", flush=True)
                dt = datetime.strptime(date_hint, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                ts_start = int((dt.timestamp())) - 3 * 86400
                ts_end = int((dt.timestamp())) + 3 * 86400
                b_start = get_block_for_timestamp(chain, ts_start, "before")
                b_end = get_block_for_timestamp(chain, ts_end, "after")
                if b_start is None or b_end is None:
                    entry["txlist_search"] = {"error": "khong lay duoc block cho timestamp"}
                elif chain == "bsc":
                    incident_tag = f"verify_final_heldout__{name.replace(' ', '_')}"
                    transfers = bsc_client.fetch_asset_transfers(seed, incident_tag, categories=["external"], from_block=b_start, to_block=b_end)
                    print(f"    Block range [{b_start}, {b_end}] - tim thay {len(transfers)} external transfer tu seed trong +-3 ngay", flush=True)
                    simplified = [{"hash": t.get("hash"), "blockNum": t.get("blockNum"),
                                   "to": (t.get("to") or {}).get("address") if isinstance(t.get("to"), dict) else t.get("to"),
                                   "value": t.get("value"),
                                   "timestamp": (t.get("metadata") or {}).get("blockTimestamp")} for t in transfers]
                    for s in simplified[:30]:
                        print(f"      {s['hash']} block={s['blockNum']} ts={s['timestamp']} to={s['to']} value={s['value']}")
                    entry["txlist_search"] = {"b_start": b_start, "b_end": b_end, "n_txs": len(transfers), "txs": simplified}
                else:
                    txs = eth_client.fetch_normal_txs(chain, seed, f"verify_final_heldout__{name.replace(' ', '_')}", b_start, b_end)
                    print(f"    Block range [{b_start}, {b_end}] - tim thay {len(txs)} tx tu seed trong +-3 ngay", flush=True)
                    simplified = [{"hash": t.get("hash"), "blockNumber": t.get("blockNumber"),
                                   "timeStamp": t.get("timeStamp"), "to": t.get("to"),
                                   "value": t.get("value"), "isError": t.get("isError"),
                                   "methodId": t.get("methodId")} for t in txs]
                    for s in simplified[:30]:
                        ts_h = datetime.fromtimestamp(int(s["timeStamp"]), tz=timezone.utc).isoformat() if s["timeStamp"] else None
                        print(f"      {s['hash']} block={s['blockNumber']} ts={ts_h} to={s['to']} value={s['value']} isError={s['isError']} methodId={s['methodId']}")
                    entry["txlist_search"] = {"b_start": b_start, "b_end": b_end, "n_txs": len(txs), "txs": simplified}
            except Exception as exc:
                print(f"    *** LOI khi tim txlist: {type(exc).__name__}: {exc} ***", flush=True)
                entry["txlist_search"] = {"error": f"{type(exc).__name__}: {exc}"}

        out[name] = entry

    out_path = ROOT / "results" / "reports" / "extra_v4" / "verify_final_heldout_9_raw.json"
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nDa luu {out_path}")


if __name__ == "__main__":
    main()
