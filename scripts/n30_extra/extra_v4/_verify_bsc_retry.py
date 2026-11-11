# -*- coding: utf-8 -*-
"""Retry rieng 4 incident BSC bi loi BscTraceAPIError tam thoi (PancakeBunny,
Spartan Protocol, Rikkei Finance, Allbridge) - chay doc lap, tung incident
mot, khong dong thoi, de giam ap luc rate-limit tich luy."""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))

from _verify_final_heldout_9 import bsc_block_for_ts, bsc_client, verify_tx_hash  # noqa: E402

TARGETS = [
    dict(name="PancakeBunny", seed="0xa0acc61547f6bd066f7c9663c17a312b6ad7e187",
         claimed_tx="0x897c2de73dd55d7701e1b69ffb3a17b0f4801ced88b0c75fe1551c5fcce6a979", date_hint="2021-05-20"),
    dict(name="Spartan Protocol", seed="0x3b6e77722e2bbe97c1cfa337b42c0939aeb83671",
         claimed_tx="0xb64ae25b0d836c25d115a9368319902c972a0215bd108ae17b1b9617dfb93af8", date_hint="2021-05-02"),
    dict(name="Rikkei Finance", seed="0x803e0930357ba577dc414b552402f71656c093ab",
         claimed_tx=None, date_hint="2022-04-15"),
    dict(name="Allbridge", seed="0xc578d755cd56255d3ff6e92e1b6371ba945e3984",
         claimed_tx="0x7ff1364c3b3b296b411965339ed956da5d17058f3164425ce800d64f1aef8210", date_hint="2023-04-02"),
]

for t in TARGETS:
    print(f"\n=== {t['name']} ===", flush=True)
    if t["claimed_tx"]:
        try:
            res = verify_tx_hash("bsc", t["claimed_tx"])
            print(f"  claimed_tx_check: {res}", flush=True)
        except Exception as exc:
            print(f"  *** LOI: {type(exc).__name__}: {exc} ***", flush=True)
            res = {"found": False}
    else:
        res = {"found": False}

    if not res.get("found"):
        dt = datetime.strptime(t["date_hint"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ts_start = int(dt.timestamp()) - 3 * 86400
        ts_end = int(dt.timestamp()) + 3 * 86400
        b_start = bsc_block_for_ts(ts_start)
        b_end = bsc_block_for_ts(ts_end)
        try:
            transfers = bsc_client.fetch_asset_transfers(t["seed"], f"verify_retry__{t['name'].replace(' ', '_')}",
                                                            categories=["external"], from_block=b_start, to_block=b_end)
            print(f"  Block range [{b_start},{b_end}] - {len(transfers)} external transfer", flush=True)
            for tr in transfers[:30]:
                to_f = (tr.get("to") or {}).get("address") if isinstance(tr.get("to"), dict) else tr.get("to")
                print(f"    {tr.get('hash')} block={tr.get('blockNum')} to={to_f} value={tr.get('value')} "
                      f"ts={(tr.get('metadata') or {}).get('blockTimestamp')}")
        except Exception as exc:
            print(f"  *** LOI txlist: {type(exc).__name__}: {exc} ***", flush=True)
    time.sleep(2)
