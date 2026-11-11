# -*- coding: utf-8 -*-
"""Phat hien: rebuild 30-incident-cu (do_collect=False, cache hien co)
THIEU DUNG 7 hard-negative cua easyfi_2021 so voi features_v2_N30.parquet
dong bang (5936 vs 5973 dong). Cache hien co cho 7 dia chi nay co file
txlist "No transactions found" (hop le) nhung co the tokentx/window da
bi ghi de boi 1 lan fetch truoc do trong phien lam viec (mtime 2026-11-03,
truoc giai doan N37 nay) tra it du lieu hon luc dau. Ap dung CHINH XAC
co che da dung cho lendhub_2023: do_collect=True de tai tao lai, roi so
sanh hash lai - KHONG doan, chi bao cao THAT."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

TARGET_IDS = {
    "easyfi_2021__hn30ez003", "easyfi_2021__hn30ez010", "easyfi_2021__hn30ez017",
    "easyfi_2021__hnc30ez000", "easyfi_2021__hnc30ez001", "easyfi_2021__hnc30ez004",
    "easyfi_2021__hnc30ez009",
}

config_n30 = load_trajectory_config(str(ROOT / "configs" / "data_N30.yaml"))
hn1 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_N30_combined.csv")
hn2 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv")
all_hn = pd.concat([hn1, hn2], ignore_index=True)

for _, row in all_hn.iterrows():
    if row["hard_negative_id"] not in TARGET_IDS:
        continue
    print(f"\n=== refetch {row['hard_negative_id']} (do_collect=True) ===", flush=True)
    traj, _, _ = expand_and_build_trajectory(
        row["chain"], row["seed_address"], int(row["start_block"]),
        row["parent_incident_id"], 0, config=config_n30, do_collect=True, max_iterations=2,
    )
    print(f"  n_actions sau refetch = {len(traj.actions)}", flush=True)
