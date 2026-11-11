# -*- coding: utf-8 -*-
"""N37 (v4_heldout): build features_v2_N37.parquet.

Chien luoc (de KHONG dong vao split_manifest_N30.json va KHONG lam vo
load_rq1_trajectories() cho 30 incident cu):
1. Goi dataset_builder.load_rq1_trajectories() VOI DUNG cac file N30 goc
   (registry_N30, split_manifest_N30, hard_negative N30 combined) - gia
   tri HOAN TOAN GIONG build_features_v2_N30.py cho 30 incident cu + hard-
   negative cu. Day la phan dung de KIEM TRA HASH KHONG DOI.
2. Tu xay THEM 6 DatasetItem cho 6 incident moi (positive) + 50
   DatasetItem cho hard-negative v2_complexity moi da mine
   (hard_negative_registry_v2_complexity_N37_new.csv), KHONG di qua
   load_rq1_trajectories (vi ham do loc cung eval_tier=="primary" va can
   split_manifest co san cho group_of - incident v4_heldout KHONG thuoc
   split_manifest cu). group_id cho incident/hard-negative moi = chinh
   incident_id goc (dung quy uoc group_id=positive_incident_id da dung
   cho cac group primary khac).
3. Noi 2 danh sach, tinh feature CHINH XAC pattern build_features_v2_N30.py.

KHONG ghi de features_v2_N30.parquet goc.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import src.pipeline.dataset_builder as dataset_builder
from src.features.extractor import extract_all_prefixes, generate_prefixes
from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_PARQUET = REPO_ROOT / "data" / "processed" / "features_v2_N37.parquet"
OUT_SCHEMA = REPO_ROOT / "configs" / "features_v2_computed_N37.json"
CONFIG_N37_PATH = REPO_ROOT / "configs" / "data_N37.yaml"
REG_N37_PATH = REPO_ROOT / "metadata" / "incident_registry_N37.csv"
HN_V2C_NEW_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N37_new.csv"

NEW_POSITIVE_IDS = [
    "sturdy_finance_2023", "jimbos_protocol_2023", "rodeo_finance_2023",
    "sentiment_protocol_2023", "pike_finance_2024", "uwu_lend_2024",
]  # fortress_protocol_2022 bi loai (loi thu thap thuc)


def _apply_n30_original_monkeypatch() -> None:
    """Y HET build_features_v2_N30.py - dung file N30 GOC, KHONG phai N37
    combined - de phan nay tai tao CHINH XAC 30-incident-cu, phuc vu kiem
    tra hash khong doi."""
    dataset_builder.REGISTRY_PATH = REPO_ROOT / "metadata" / "incident_registry_N30.csv"
    dataset_builder.HARD_NEGATIVE_REGISTRY_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
    dataset_builder.SPLIT_MANIFEST_PATH = REPO_ROOT / "metadata" / "split_manifest_N30.json"
    dataset_builder.HARD_NEGATIVE_REGISTRY_V2_COMPLEXITY_PATH = (
        REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv"
    )


@dataclass
class Item:
    trajectory: object
    group_id: str
    label: int
    chain: str
    kind: str
    source_id: str


def build_old_30_items(config_n30):
    _apply_n30_original_monkeypatch()
    return dataset_builder.load_rq1_trajectories(config=config_n30, verbose=True, include_v2_complexity=True)


def build_new_items(config_n37):
    reg = pd.read_csv(REG_N37_PATH)
    items = []
    for iid in NEW_POSITIVE_IDS:
        row = reg[reg.incident_id == iid].iloc[0]
        traj, _, _ = expand_and_build_trajectory(
            row["chain_primary"], row["seed_address"], int(row["start_block"]),
            iid, int(row["label"]), config=config_n37, do_collect=False,
        )
        items.append(Item(trajectory=traj, group_id=iid, label=int(row["label"]),
                           chain=row["chain_primary"], kind="positive_v4_heldout", source_id=iid))
        print(f"[positive_v4_heldout] {iid}: n_actions={len(traj.actions)}", flush=True)

    hn_df = pd.read_csv(HN_V2C_NEW_PATH)
    n_empty = 0
    for _, row in hn_df.iterrows():
        hn_id = row["hard_negative_id"]
        parent = row["parent_incident_id"]
        traj, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]),
            parent, 0, config=config_n37, do_collect=False, max_iterations=2,
        )
        if len(traj) == 0:
            n_empty += 1
            continue
        items.append(Item(trajectory=traj, group_id=parent, label=0,
                           chain=row["chain"], kind="hard_negative_mined_v2_complexity_v4_heldout", source_id=hn_id))
    print(f"[hard_negative_mined_v2_complexity_v4_heldout] {len(hn_df) - n_empty}/{len(hn_df)} usable (rong: {n_empty})", flush=True)
    return items


def extract_rows(items, leakage_violations, rows, meta_rows):
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


def main():
    print("=== N37 (v4_heldout): build trajectory that (30 cu + 6 moi) ===", flush=True)
    config_n30 = load_trajectory_config(str(REPO_ROOT / "configs" / "data_N30.yaml"))
    config_n37 = load_trajectory_config(str(CONFIG_N37_PATH))

    old_items = build_old_30_items(config_n30)
    new_items = build_new_items(config_n37)
    items = old_items + new_items

    n_pos = sum(1 for i in items if i.label == 1)
    n_neg = sum(1 for i in items if i.label == 0)
    print(f"\nTong trajectory: {len(items)} (positive={n_pos}, negative={n_neg})", flush=True)

    total_specs = sum(len(generate_prefixes(i.trajectory)) for i in items)
    print(f"Tong prefix row = {total_specs}", flush=True)

    rows, meta_rows, leakage_violations = [], [], []
    extract_rows(items, leakage_violations, rows, meta_rows)

    if leakage_violations:
        print(f"\n*** DUNG LAI: {len(leakage_violations)} vi pham invariant chong leakage ***")
        for v in leakage_violations[:20]:
            print("  ", v)
        raise SystemExit(1)
    print(f"Kiem tra leakage tren {len(rows)} prefix row: SACH (0 vi pham).", flush=True)

    X = pd.DataFrame(rows).fillna(0.0)
    meta = pd.DataFrame(meta_rows)
    full = pd.concat([meta, X], axis=1)
    assert len(full) == total_specs

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(OUT_PARQUET, index=False)
    print(f"\nDa luu {OUT_PARQUET} ({len(full)} dong, {len(X.columns)} feature column)", flush=True)

    import hashlib
    config_sha256 = hashlib.sha256(CONFIG_N37_PATH.read_bytes()).hexdigest()
    schema = {
        "version": "v2_N37_v4_heldout",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(full)),
        "n_positive_trajectories": n_pos,
        "n_negative_trajectories": n_neg,
        "feature_columns": sorted(X.columns),
        "n_feature_columns": len(X.columns),
        "leakage_check": f"PASS - tong action_count_* == prefix_len cho tat ca {len(full)} dong",
        "source": "N37 v4_heldout (2026-11-05) - 30 incident cu (nguyen ven) + 6 incident moi + 50 hard-negative v2c moi. fortress_protocol_2022 bi loai (loi thu thap thuc).",
        "new_positive_ids": NEW_POSITIVE_IDS,
        "excluded_incident_ids": ["fortress_protocol_2022"],
        "config_path_used": str(CONFIG_N37_PATH.relative_to(REPO_ROOT)),
        "config_sha256": config_sha256,
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Da luu {OUT_SCHEMA}", flush=True)


if __name__ == "__main__":
    main()
