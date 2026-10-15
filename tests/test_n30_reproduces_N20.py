"""Batch 1 N30 (2026-10-15): kiem tra features_v2_N30.parquet, khi gioi han
lai CHI con 20 incident cu (15 v1.0 + 5 N20, tuc 21 group trong
split_manifest_N20.json), tai tao CHINH XAC features_v2_N20.parquet da
freeze - khong co sai khac nao (khac voi dot N20 truoc, dot nay KHONG co
truong hop nao giong Hedgey vi allowlist N30 chi them KyberSwap cho rieng
Prisma Finance, khong anh huong toi 20 incident cu).

KHONG goi mang - chi doc 2 file parquet da co san (features_v2_N20.parquet
da freeze o Checkpoint C/C'' va features_v2_N30.parquet vua build o
scripts/build_features_v2_N30.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

N20_PARQUET = Path("data/processed/features_v2_N20.parquet")
N30_PARQUET = Path("data/processed/features_v2_N30.parquet")
SPLIT_MANIFEST_N20 = Path("metadata/split_manifest_N20.json")
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

# hedgey_finance_2024 (1 trong 5 incident N20, thuoc "ranh gioi mem") DA
# ĐƯỢC CHẤP NHẬN khac biet 662->755 action truoc do, trong giai doan N20 -
# xem results/reports/N30_allowlist_completion_hedgey_diff_2026-10-14.md.
# features_v2_N20.parquet (frozen) PHAN ANH gia tri CU (662, truoc quyet
# dinh chap nhan), con moi lan build lai (ke ca N30 batch 1) deu ra 755 -
# day KHONG phai drift moi do batch 1 N30 gay ra, ma la do sai khac DA
# duoc khai bao truoc giua file parquet frozen va trang thai registry/
# config hien tai. Loai hedgey ra khoi so sanh GIA TRI tuyet doi (van giu
# trong so sanh SO DONG/DINH DANH ben duoi) - KHONG am tham bo qua toan bo
# kiem tra cho incident nay.
KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS = {"hedgey_finance_2024"}


def _old_20_group_ids() -> set:
    manifest = json.loads(SPLIT_MANIFEST_N20.read_text(encoding="utf-8"))
    return {g["group_id"] for g in manifest["groups"] if g.get("role") == "primary"}


@pytest.fixture(scope="module")
def n30_restricted_and_n20_frozen():
    if not N20_PARQUET.exists() or not N30_PARQUET.exists():
        pytest.skip("Thieu features_v2_N20.parquet hoac features_v2_N30.parquet - khong the so sanh.")
    frozen_n20 = pd.read_parquet(N20_PARQUET)
    full_n30 = pd.read_parquet(N30_PARQUET)
    old_groups = _old_20_group_ids()
    # split_manifest_N20.json co 21 group TONG (20 role=primary + 1 role=
    # auxiliary cho circulate_2023, bi loai khoi RQ1 chinh) - 20 incident
    # "cu" (15 v1.0 + 5 N20) ma bai test nay can so sanh la 20 group
    # role=primary, KHONG phai 21.
    assert len(old_groups) == 20, f"Ky vong 20 group role=primary (N20 cu), thuc te {len(old_groups)}"
    restricted_n30 = full_n30[full_n30["group_id"].isin(old_groups)].reset_index(drop=True)
    return restricted_n30, frozen_n20


def test_same_row_count(n30_restricted_and_n20_frozen):
    restricted_n30, frozen_n20 = n30_restricted_and_n20_frozen
    assert len(restricted_n30) == len(frozen_n20), (
        f"So dong KHAC: N30 (gioi han 20 incident cu)={len(restricted_n30)} vs N20 frozen={len(frozen_n20)} - "
        "them batch 1 N30 da anh huong toi 20 incident cu (khong duoc phep)."
    )


def test_same_identifiers(n30_restricted_and_n20_frozen):
    restricted_n30, frozen_n20 = n30_restricted_and_n20_frozen
    key_n30 = set(zip(restricted_n30["source_id"], restricted_n30["prefix_label"]))
    key_n20 = set(zip(frozen_n20["source_id"], frozen_n20["prefix_label"]))
    only_n30 = key_n30 - key_n20
    only_n20 = key_n20 - key_n30
    assert not only_n30 and not only_n20, (
        f"Dinh danh (source_id, prefix_label) KHAC NHAU.\n"
        f"Chi co o N30 (gioi han): {sorted(only_n30)[:10]}\n"
        f"Chi co o N20 frozen: {sorted(only_n20)[:10]}"
    )


def test_feature_values_match_exactly(n30_restricted_and_n20_frozen):
    restricted_n30, frozen_n20 = n30_restricted_and_n20_frozen
    restricted_n30 = restricted_n30[~restricted_n30["source_id"].isin(KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS)]
    frozen_n20 = frozen_n20[~frozen_n20["source_id"].isin(KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS)]
    n30_idx = restricted_n30.set_index(["source_id", "prefix_label"]).sort_index()
    n20_idx = frozen_n20.set_index(["source_id", "prefix_label"]).sort_index()

    feature_cols = [c for c in frozen_n20.columns if c not in META_COLS]
    max_abs_diff_per_col = {}
    for col in feature_cols:
        if col not in n30_idx.columns:
            max_abs_diff_per_col[col] = float("nan")
            continue
        a = n30_idx.loc[n20_idx.index, col].to_numpy(dtype=float)
        b = n20_idx[col].to_numpy(dtype=float)
        max_abs_diff_per_col[col] = float(np.nanmax(np.abs(a - b)))

    bad_cols = {c: d for c, d in max_abs_diff_per_col.items() if not (d <= 1e-9)}
    assert not bad_cols, (
        f"Chenh lech tuyet doi VUOT NGUONG 1e-9 o {len(bad_cols)} feature column cho 19 incident cu "
        f"(da loai {KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS}) (chi tiet): {bad_cols}"
    )


def test_only_known_soft_boundary_incident_differs(n30_restricted_and_n20_frozen):
    """Kiem tra RANH GIOI CUNG: 19/20 incident con lai (gom TOAN BO 15 v1.0
    va 4/5 incident N20 khac hedgey_finance_2024) KHONG duoc phep co bat ky
    sai khac gia tri nao. Neu test nay FAIL vi mot source_id MOI xuat hien
    (khong phai hedgey_finance_2024), day la HARD STOP - phai bao cao ngay,
    KHONG duoc tu sua lang le."""
    restricted_n30, frozen_n20 = n30_restricted_and_n20_frozen
    n30_idx = restricted_n30.set_index(["source_id", "prefix_label"]).sort_index()
    n20_idx = frozen_n20.set_index(["source_id", "prefix_label"]).sort_index()

    feature_cols = [c for c in frozen_n20.columns if c not in META_COLS]
    affected_source_ids = set()
    for col in feature_cols:
        if col not in n30_idx.columns:
            continue
        a = n30_idx.loc[n20_idx.index, col].to_numpy(dtype=float)
        b = n20_idx[col].to_numpy(dtype=float)
        bad_mask = np.abs(a - b) > 1e-9
        if bad_mask.any():
            affected_source_ids |= {idx[0] for idx in n20_idx.index[bad_mask]}

    unexpected = affected_source_ids - KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS
    assert not unexpected, (
        f"HARD STOP: phat hien sai khac O INCIDENT KHONG NAM TRONG danh sach "
        f"'ranh gioi mem' da duoc khai bao truoc ({KNOWN_SOFT_BOUNDARY_VALUE_DIFF_SOURCE_IDS}): "
        f"{sorted(unexpected)} - phai dung lai bao cao nguoi dung, KHONG tiep tuc build/freeze."
    )
