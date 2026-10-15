"""Checkpoint N30 muc (b): kiem tra dong nhat cho TOAN BO negative (khong
chi positive) duoi config N30 (co them KyberSwap Meta Aggregation Router v2)
so voi config N20 (chua co).

Tang 1 (CUNG, khong duoc khac): 536 hard-negative "quy tac chinh" cua v1.0
(metadata/hard_negative_registry.csv).
Tang 2 (MEM, duoc phep khac nhung phai bao cao): 125 hard-negative "quy tac
chinh" + 46 "v2_complexity" cua 5 incident N20.

KHONG ghi de gi. Chi doc cache (do_collect=False).
"""
from __future__ import annotations

import pandas as pd

from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config


def check(hn_df: pd.DataFrame, cfg20, cfg30, max_iterations_negative: int = 2):
    diffs = []
    n_checked = 0
    for _, row in hn_df.iterrows():
        hn_id = row["hard_negative_id"]
        parent = row["parent_incident_id"]
        t20, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]), parent, 0,
            config=cfg20, do_collect=False, max_iterations=max_iterations_negative,
        )
        t30, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]), parent, 0,
            config=cfg30, do_collect=False, max_iterations=max_iterations_negative,
        )
        n_checked += 1
        n20, n30 = len(t20), len(t30)
        types20 = [a.event_type for a in t20.actions]
        types30 = [a.event_type for a in t30.actions]
        if n20 != n30 or types20 != types30:
            diffs.append((hn_id, parent, n20, n30))
    return n_checked, diffs


def main():
    cfg20 = load_trajectory_config("configs/data_N20.yaml")
    cfg30 = load_trajectory_config("configs/data_N30.yaml")

    print("=== TANG 1: 536 hard-negative v1.0 (RANH GIOI CUNG) ===", flush=True)
    hn_v1 = pd.read_csv("metadata/hard_negative_registry.csv")
    n1, diffs1 = check(hn_v1, cfg20, cfg30)
    print(f"Da kiem tra {n1}/536. Khac biet: {len(diffs1)}")
    for d in diffs1[:30]:
        print("  ", d)

    print("\n=== TANG 2a: 125 hard-negative N20 'quy tac chinh' (RANH GIOI MEM) ===", flush=True)
    hn_n20 = pd.read_csv("metadata/hard_negative_registry_N20.csv")
    n2a, diffs2a = check(hn_n20, cfg20, cfg30)
    print(f"Da kiem tra {n2a}/125. Khac biet: {len(diffs2a)}")
    for d in diffs2a:
        print("  ", d)

    print("\n=== TANG 2b: 46 hard-negative N20 'v2_complexity' (RANH GIOI MEM) ===", flush=True)
    hn_v2c = pd.read_csv("metadata/hard_negative_registry_v2_complexity_N20.csv")
    n2b, diffs2b = check(hn_v2c, cfg20, cfg30)
    print(f"Da kiem tra {n2b}/46. Khac biet: {len(diffs2b)}")
    for d in diffs2b:
        print("  ", d)

    print("\n" + "=" * 60)
    if diffs1:
        print(f"*** TANG 1 (CUNG) CO {len(diffs1)} KHAC BIET - DUNG THEO QUY TAC ***")
    else:
        print("TANG 1 (CUNG): SACH, khong khac biet nao - duoc phep tiep tuc Phase 2.")
    print(f"TANG 2 (MEM): tong {len(diffs2a) + len(diffs2b)} khac biet (CHAP NHAN, da bao cao).")


if __name__ == "__main__":
    main()
