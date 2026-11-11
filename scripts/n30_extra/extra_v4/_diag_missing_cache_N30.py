# -*- coding: utf-8 -*-
"""Chan doan: rebuild 30-incident-cu tra it hon frozen (5936 vs 5973 dong,
864/867 hard_negative_mined, 221/225 v2_complexity). Tim CHINH XAC hard-
negative nao tra trajectory RONG (len==0) khi do_collect=False, kiem tra
xem co phai do CACHE THIEU (file raw khong ton tai) hay khong - neu dung,
day la tinh huong GIONG lendhub_2023 (tai tao bang do_collect=True)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.pipeline.incident_pipeline import RAW_DIR, expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

config_n30 = load_trajectory_config(str(ROOT / "configs" / "data_N30.yaml"))

hn1 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_N30_combined.csv")
hn2 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv")

empty_rows = []
for label, df in [("hard_negative_mined", hn1), ("hard_negative_mined_v2_complexity", hn2)]:
    for _, row in df.iterrows():
        hn_id = row["hard_negative_id"]
        parent = row["parent_incident_id"]
        traj, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]),
            parent, 0, config=config_n30, do_collect=False, max_iterations=2,
        )
        if len(traj) == 0:
            cache_dir = RAW_DIR / row["chain"] / str(row["seed_address"]).lower() / parent
            has_cache = cache_dir.exists() and any(cache_dir.glob("*.json"))
            empty_rows.append({
                "kind": label, "hard_negative_id": hn_id, "parent": parent,
                "chain": row["chain"], "seed_address": row["seed_address"],
                "start_block": row["start_block"], "cache_dir": str(cache_dir),
                "has_cache_dir_with_json": has_cache,
            })

print(f"Tong so hard-negative tra trajectory RONG: {len(empty_rows)}")
for r in empty_rows:
    print(r)
