"""Rebuild features_v2_N30 vao duong dan TAM (scratchpad) de doi chieu
SHA-256/cell-by-cell voi file da dong bang, KHONG ghi de file goc.
Sao chep CHINH XAC logic cua scripts/build_features_v2_N30.py (khong doi
gi khac ngoai duong dan output)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import src.pipeline.dataset_builder as dataset_builder
from src.features.extractor import extract_all_prefixes, generate_prefixes
from src.trajectories.builder import load_trajectory_config

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PARQUET = Path(r"C:\Users\GAMING\AppData\Local\Temp\claude\d--DAI-HOC-cagi-ed\13088f9a-2212-448d-89ca-1bc07963c50b\scratchpad\features_rebuild_check.parquet")
CONFIG_N30_PATH = REPO_ROOT / "configs" / "data_N30.yaml"


def _apply_n30_monkeypatch() -> None:
    dataset_builder.REGISTRY_PATH = REPO_ROOT / "metadata" / "incident_registry_N30.csv"
    dataset_builder.HARD_NEGATIVE_REGISTRY_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
    dataset_builder.SPLIT_MANIFEST_PATH = REPO_ROOT / "metadata" / "split_manifest_N30.json"
    dataset_builder.HARD_NEGATIVE_REGISTRY_V2_COMPLEXITY_PATH = (
        REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv"
    )


def main():
    _apply_n30_monkeypatch()
    config_n30 = load_trajectory_config(str(CONFIG_N30_PATH))

    items = dataset_builder.load_rq1_trajectories(
        config=config_n30, verbose=False, include_v2_complexity=True,
    )

    rows, meta_rows = [], []
    for item in items:
        for spec, feats in extract_all_prefixes(item.trajectory, include_endpoint_context=False):
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

    X = pd.DataFrame(rows).fillna(0.0)
    meta = pd.DataFrame(meta_rows)
    full = pd.concat([meta, X], axis=1)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(OUT_PARQUET, index=False)
    print(f"Da luu {OUT_PARQUET} ({len(full)} dong, {len(X.columns)} feature column)", flush=True)


if __name__ == "__main__":
    main()
