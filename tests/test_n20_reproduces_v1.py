"""Checkpoint C' (dataset expansion N20, 2026-10-14): kiem tra pipeline xay
dung feature (dataset_builder.load_rq1_trajectories + extract_all_prefixes,
CHINH CODE da dung cho build_features_v2_N20.py, KHONG sua gi) khi chay
VOI DUONG DAN MAC DINH (15 incident cu, 536+110 hard-negative cu,
split_manifest.json cu - KHONG dung bat ky file *_N20.* nao) tai tao
CHINH XAC features_v2.parquet da freeze (v1.0).

Day la bang chung gian tiep rang viec them 5 incident/125 hard-negative N20
(qua cac file *_N20.* RIENG, monkeypatch duong dan o scripts/build_features_v2_N20.py)
KHONG lam thay doi cach tinh feature cho 15 incident cu - vi day CUNG 1 ham
(dataset_builder.load_rq1_trajectories, src.features.extractor.extract_all_prefixes)
duoc dung cho ca N=15 (mac dinh) va N=20 (monkeypatch duong dan rieng).

KHONG goi mang (do_collect=False mac dinh trong load_rq1_trajectories).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.features.extractor import extract_all_prefixes
from src.pipeline.dataset_builder import load_rq1_trajectories

FROZEN_PARQUET = Path("data/processed/features_v2.parquet")
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]


def _build_features_from_scratch() -> pd.DataFrame:
    items = load_rq1_trajectories(verbose=False, include_v2_complexity=True)
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
    return pd.concat([meta, X], axis=1)


@pytest.fixture(scope="module")
def rebuilt_and_frozen():
    if not FROZEN_PARQUET.exists():
        pytest.skip(f"{FROZEN_PARQUET} không tồn tại — không thể so sánh.")
    frozen = pd.read_parquet(FROZEN_PARQUET)
    rebuilt = _build_features_from_scratch()
    return rebuilt, frozen


def test_same_row_count(rebuilt_and_frozen):
    rebuilt, frozen = rebuilt_and_frozen
    assert len(rebuilt) == len(frozen), (
        f"Số dòng KHÁC: rebuilt={len(rebuilt)} vs frozen={len(frozen)} — "
        "dataset_builder mặc định không còn tái tạo đúng v1.0."
    )


def test_same_identifiers(rebuilt_and_frozen):
    rebuilt, frozen = rebuilt_and_frozen
    key_rebuilt = set(zip(rebuilt["source_id"], rebuilt["prefix_label"]))
    key_frozen = set(zip(frozen["source_id"], frozen["prefix_label"]))
    only_rebuilt = key_rebuilt - key_frozen
    only_frozen = key_frozen - key_rebuilt
    assert not only_rebuilt and not only_frozen, (
        f"Định danh (source_id, prefix_label) KHÁC NHAU.\n"
        f"Chỉ có ở bản rebuild: {sorted(only_rebuilt)[:10]}\n"
        f"Chỉ có ở bản freeze: {sorted(only_frozen)[:10]}"
    )


def test_feature_values_match_within_tolerance(rebuilt_and_frozen):
    rebuilt, frozen = rebuilt_and_frozen
    rebuilt_idx = rebuilt.set_index(["source_id", "prefix_label"]).sort_index()
    frozen_idx = frozen.set_index(["source_id", "prefix_label"]).sort_index()

    feature_cols = [c for c in frozen.columns if c not in META_COLS]
    max_abs_diff_per_col = {}
    for col in feature_cols:
        if col not in rebuilt_idx.columns:
            max_abs_diff_per_col[col] = float("nan")
            continue
        a = rebuilt_idx.loc[frozen_idx.index, col].to_numpy(dtype=float)
        b = frozen_idx[col].to_numpy(dtype=float)
        max_abs_diff_per_col[col] = float(np.nanmax(np.abs(a - b)))

    worst = max(max_abs_diff_per_col.values())
    bad_cols = {c: d for c, d in max_abs_diff_per_col.items() if not (d <= 1e-9)}
    assert not bad_cols, (
        f"Chênh lệch tuyệt đối VƯỢT NGƯỠNG 1e-9 ở {len(bad_cols)} feature column "
        f"(chênh lệch tối đa toàn cục={worst:.2e}): {bad_cols}"
    )
