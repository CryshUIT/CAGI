"""EXPLORATORY / post-hoc - trich ngay khai thac THAT cua 30 incident tu
timestamp cua action DAU TIEN trong cache da decode (data/processed/
{incident_id}_events.json) - KHONG doan, KHONG dung ngay viet tay trong
incident_registry_N30.csv['name']. Ghi vao FILE RIENG (KHONG sua registry
goc). Incident nao thieu file se liet ke ro rang trong cot note, KHONG bo
qua am tham.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_CSV = ROOT / "results" / "tables" / "extra_v3b" / "incident_dates_from_cache_N30.csv"


def main():
    reg = pd.read_csv(REGISTRY_PATH)
    ids = reg[(reg.eval_tier == "primary") & (reg.label == 1)].incident_id.tolist()

    rows = []
    missing = []
    for iid in ids:
        p = PROCESSED_DIR / f"{iid}_events.json"
        if not p.exists():
            missing.append(iid)
            rows.append({"incident_id": iid, "first_action_timestamp": None, "note": "THIEU file events.json trong cache"})
            continue
        events = json.loads(p.read_text(encoding="utf-8"))
        if not events:
            missing.append(iid)
            rows.append({"incident_id": iid, "first_action_timestamp": None, "note": "events.json RONG (0 action)"})
            continue
        ts_sorted = sorted(e["timestamp"] for e in events)
        rows.append({"incident_id": iid, "first_action_timestamp": ts_sorted[0], "note": ""})

    out = pd.DataFrame(rows).sort_values("first_action_timestamp", na_position="last")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(out.to_string(index=False))
    print(f"\nDa luu {OUT_CSV}")
    print(f"\nSo incident LAY DUOC ngay: {len(ids) - len(missing)}/{len(ids)}")
    if missing:
        print(f"Incident KHONG lay duoc (liet ke, KHONG doan): {missing}")


if __name__ == "__main__":
    main()
