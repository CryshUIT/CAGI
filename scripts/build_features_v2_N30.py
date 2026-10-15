"""Batch 1 cua dataset expansion N30: build features_v2_N30.parquet
(20 incident cu + 5 incident moi batch-1 + hard-negative moi), dung CHINH
XAC pattern cua scripts/build_features_v2_N20.py (monkeypatch TRONG main(),
verify_config_guard() rieng - xem lich su regression test-isolation da ghi
trong build_features_v2_N20.py).

KHONG ghi de data/processed/features_v2.parquet goc hay features_v2_N20.parquet.
Dung metadata/incident_registry_N30.csv, hard_negative_registry_N30_combined.csv,
hard_negative_registry_v2_complexity_N30_combined.csv, split_manifest_N30.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import src.pipeline.dataset_builder as dataset_builder
from src.features.extractor import extract_all_prefixes, generate_prefixes
from src.trajectories.builder import load_trajectory_config

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PARQUET = REPO_ROOT / "data" / "processed" / "features_v2_N30.parquet"
OUT_SCHEMA = REPO_ROOT / "configs" / "features_v2_computed_N30.json"
CONFIG_N30_PATH = REPO_ROOT / "configs" / "data_N30.yaml"
REQUIRED_DEX_ADDRESSES = {
    "0x66a9893cc07d91d95644aedd05d03f95e1dba8af",  # Uniswap Universal Router v2 (Cork, 0xInfini)
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",  # Uniswap Universal Router v1.2 variant (Hedgey)
    "0x6131b5fae19ea4f9d964eac0408e4408b66337b5",  # KyberSwap Meta Aggregation Router v2 (Prisma)
}


def _apply_n30_monkeypatch() -> None:
    """Monkeypatch CHI khi duoc GOI (trong main()), KHONG o muc module - tranh
    side-effect toan cuc khi module nay bi IMPORT boi file khac (vd test),
    dung pattern da sua trong build_features_v2_N20.py."""
    dataset_builder.REGISTRY_PATH = REPO_ROOT / "metadata" / "incident_registry_N30.csv"
    dataset_builder.HARD_NEGATIVE_REGISTRY_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
    dataset_builder.SPLIT_MANIFEST_PATH = REPO_ROOT / "metadata" / "split_manifest_N30.json"
    dataset_builder.HARD_NEGATIVE_REGISTRY_V2_COMPLEXITY_PATH = (
        REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv"
    )


def verify_config_guard(config_path_used: Path = CONFIG_N30_PATH):
    """CHOT CHAN CAU HINH (lap lai pattern da dung cho N20) - dam bao config
    dung dia chi va allowlist co du cac dia chi DEX bat buoc (bao gom
    KyberSwap moi them cho Prisma Finance)."""
    assert config_path_used == CONFIG_N30_PATH, (
        f"CHOT CHAN: duong dan config PHAI la {CONFIG_N30_PATH}, dang dung {config_path_used}"
    )
    assert config_path_used.exists(), f"Khong tim thay file config {config_path_used}"
    config_n30 = load_trajectory_config(str(config_path_used))
    missing_dex = REQUIRED_DEX_ADDRESSES - set(config_n30.allowlist)
    assert not missing_dex, (
        f"CHOT CHAN: allowlist cua {config_path_used} THIEU dia chi bat buoc: {missing_dex} "
        "- feature build se KHONG phan anh dung N30 allowlist neu thieu."
    )
    return config_n30


def main():
    print("=== Batch 1 N30: build trajectory that (20 cu + 5 moi batch-1) ===", flush=True)
    _apply_n30_monkeypatch()
    config_n30 = verify_config_guard()
    print(f"[CHOT CHAN] config={CONFIG_N30_PATH}, 3 dia chi DEX bat buoc DA CO trong allowlist.", flush=True)

    items = dataset_builder.load_rq1_trajectories(
        config=config_n30, verbose=True, include_v2_complexity=True,
    )
    n_pos = sum(1 for i in items if i.label == 1)
    n_neg = sum(1 for i in items if i.label == 0)
    n_neg_v2 = sum(1 for i in items if i.kind == "hard_negative_mined_v2_complexity")
    print(f"\nTong trajectory: {len(items)} (positive={n_pos}, negative={n_neg}, "
          f"hard-negative v2={n_neg_v2})", flush=True)

    total_specs = sum(len(generate_prefixes(i.trajectory)) for i in items)
    print(f"Tong prefix row = {total_specs}", flush=True)

    print("\n=== Tinh feature (pipeline da sua leak prefix_ratio o tang model) ===", flush=True)
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
    assert len(full) == total_specs

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(OUT_PARQUET, index=False)
    print(f"\nDa luu {OUT_PARQUET} ({len(full)} dong, {len(X.columns)} feature column)", flush=True)

    import hashlib
    config_sha256 = hashlib.sha256(CONFIG_N30_PATH.read_bytes()).hexdigest()

    schema = {
        "version": "v2_N30_batch1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(full)),
        "n_positive_trajectories": n_pos,
        "n_negative_trajectories": n_neg,
        "feature_columns": sorted(X.columns),
        "n_feature_columns": len(X.columns),
        "leakage_check": f"PASS - tong action_count_* == prefix_len cho tat ca {len(full)} dong",
        "source": "dataset expansion N30 batch 1 (2026-10-15) - KHONG ghi de features_v2.parquet/features_v2_N20.parquet goc",
        "config_path_used": str(CONFIG_N30_PATH.relative_to(REPO_ROOT)),
        "config_sha256": config_sha256,
        "config_allowlist_verified_contains": sorted(REQUIRED_DEX_ADDRESSES),
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Da luu {OUT_SCHEMA}", flush=True)


if __name__ == "__main__":
    main()
