# -*- coding: utf-8 -*-
"""Build features CHI cho 2 incident final_heldout_new (positive + 53
hard-negative moi mine) - dung de du doan bang model DA DONG BANG
(KHONG retrain). Dung CUNG logic extract_all_prefixes/generate_prefixes
nhu cac lan build truoc, KHONG sua code."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.features.extractor import extract_all_prefixes, generate_prefixes  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

REG = pd.read_csv(ROOT / "metadata" / "incident_registry_final_heldout.csv")
HN_PATHS = [
    ROOT / "metadata" / "hard_negative_registry_final_heldout_new.csv",
    ROOT / "metadata" / "hard_negative_registry_bsc2_new.csv",
]
OUT_PARQUET = ROOT / "data" / "processed" / "features_v2_final_heldout_new.parquet"

NEW_POSITIVE_IDS = [
    "rari_capital_fuse_2022", "curve_crv_eth_attacker_2023",
    "pancakebunny_2021", "rikkei_finance_2022",
]


@dataclass
class Item:
    trajectory: object
    group_id: str
    label: int
    chain: str
    kind: str
    source_id: str


def main():
    config = load_trajectory_config(str(ROOT / "configs" / "data_final_heldout.yaml"))
    items = []
    for iid in NEW_POSITIVE_IDS:
        row = REG[REG.incident_id == iid].iloc[0]
        traj, _, _ = expand_and_build_trajectory(
            row["chain_primary"], row["seed_address"], int(row["start_block"]),
            iid, int(row["label"]), config=config, do_collect=False,
        )
        items.append(Item(trajectory=traj, group_id=iid, label=int(row["label"]),
                           chain=row["chain_primary"], kind="positive_final_heldout", source_id=iid))
        print(f"[positive_final_heldout] {iid}: n_actions={len(traj.actions)}", flush=True)

    hn_df = pd.concat([pd.read_csv(p) for p in HN_PATHS if p.exists()], ignore_index=True)
    n_empty = 0
    for _, row in hn_df.iterrows():
        hn_id = row["hard_negative_id"]
        parent = row["parent_incident_id"]
        traj, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]),
            parent, 0, config=config, do_collect=False, max_iterations=2,
        )
        if len(traj) == 0:
            n_empty += 1
            continue
        items.append(Item(trajectory=traj, group_id=parent, label=0,
                           chain=row["chain"], kind="hard_negative_mined_final_heldout", source_id=hn_id))
    print(f"[hard_negative_mined_final_heldout] {len(hn_df) - n_empty}/{len(hn_df)} usable (rong: {n_empty})", flush=True)

    rows, meta_rows, leakage_violations = [], [], []
    for item in items:
        for spec, feats in extract_all_prefixes(item.trajectory, include_endpoint_context=False):
            action_count_keys = [k for k in feats if k.startswith("action_count_") and not k.endswith("_ratio")]
            total_counted = sum(feats[k] for k in action_count_keys)
            if total_counted != spec.length:
                leakage_violations.append((item.source_id, spec.label, spec.length, total_counted))
            feats = dict(feats)
            feats.pop("prefix_len", None)
            rows.append(feats)
            meta_rows.append({
                "trajectory_id": item.trajectory.trajectory_id,
                "source_id": item.source_id,
                "group_id": item.group_id,
                "kind": item.kind,
                "chain": item.chain,
                "label": item.label,
                "prefix_label": spec.label,
                "prefix_len": spec.length,
                "trajectory_len": len(item.trajectory),
            })

    if leakage_violations:
        print(f"\n*** DUNG LAI: {len(leakage_violations)} vi pham invariant chong leakage ***")
        for v in leakage_violations[:20]:
            print("  ", v)
        raise SystemExit(1)
    print(f"Kiem tra leakage tren {len(rows)} prefix row: SACH (0 vi pham).", flush=True)

    X = pd.DataFrame(rows).fillna(0.0)
    meta = pd.DataFrame(meta_rows)
    full = pd.concat([meta, X], axis=1)
    full.to_parquet(OUT_PARQUET, index=False)
    print(f"\nDa luu {OUT_PARQUET} ({len(full)} dong, {len(X.columns)} feature column)", flush=True)
    print(full.groupby(["group_id", "kind"]).size())


if __name__ == "__main__":
    main()
