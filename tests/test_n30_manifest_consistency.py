"""Batch 1 N30 (2026-10-15): kiem tra tinh nhat quan cua
metadata/split_manifest_N30.json sau khi sua loi "ban sao chua cap nhat"
(thieu 5 group moi cho batch 1, phat hien truoc khi build lan dau).

4 kiem tra duoc yeu cau:
(a) moi incident trong incident_registry_N30.csv co DUNG MOT group trong
    split_manifest_N30.json (role=primary).
(b) moi hard_negative_id xuat hien trong features_v2_N30.parquet thuoc
    DUNG MOT group, khong trung lap giua cac group.
(c) 21 group CU (toan bo groups cua split_manifest_N20.json) phai
    BYTE-IDENTICAL (sau khi serialize JSON) trong split_manifest_N30.json.
(d) moi group trong manifest co incident_id tuong ung ton tai trong
    incident_registry_N30.csv (positive_incident_id).

Test fail = HARD STOP, khong tu sua lang le.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REGISTRY_N30 = Path("metadata/incident_registry_N30.csv")
MANIFEST_N20 = Path("metadata/split_manifest_N20.json")
MANIFEST_N30 = Path("metadata/split_manifest_N30.json")
FEATURES_N30 = Path("data/processed/features_v2_N30.parquet")


@pytest.fixture(scope="module")
def manifests_and_registry():
    for p in (REGISTRY_N30, MANIFEST_N20, MANIFEST_N30, FEATURES_N30):
        if not p.exists():
            pytest.skip(f"Thieu {p} - khong the kiem tra.")
    registry = pd.read_csv(REGISTRY_N30)
    manifest_n20 = json.loads(MANIFEST_N20.read_text(encoding="utf-8"))
    manifest_n30 = json.loads(MANIFEST_N30.read_text(encoding="utf-8"))
    return registry, manifest_n20, manifest_n30


def test_every_registry_incident_has_exactly_one_group(manifests_and_registry):
    """Incident trong registry co the xuat hien o VAI TRO positive_incident_id
    (incident chinh cua group) HOAC original_hard_negative_control_id (5
    benign-control "cung cau chuyen" voi 1 positive incident, xem docstring
    dataset_builder.py) - ca 2 vai tro deu tinh la "co group", nhung moi
    incident chi duoc gan DUNG MOT vai tro trong DUNG MOT group."""
    registry, _, manifest_n30 = manifests_and_registry
    id_role_pairs = []
    for g in manifest_n30["groups"]:
        members = g["members"]
        id_role_pairs.append((members["positive_incident_id"], g["group_id"]))
        if members.get("original_hard_negative_control_id"):
            id_role_pairs.append((members["original_hard_negative_control_id"], g["group_id"]))

    covered_ids = [iid for iid, _ in id_role_pairs]
    counts = pd.Series(covered_ids).value_counts()

    missing = set(registry["incident_id"]) - set(covered_ids)
    duplicated = counts[counts > 1]
    assert not missing, f"Incident trong registry N30 KHONG CO group tuong ung: {sorted(missing)}"
    assert duplicated.empty, f"Incident co NHIEU HON MOT group: {duplicated.to_dict()}"


def test_every_negative_id_belongs_to_exactly_one_group(manifests_and_registry):
    _, _, manifest_n30 = manifests_and_registry
    features = pd.read_parquet(FEATURES_N30)
    negative_source_ids = set(
        features[features["kind"].isin(
            ["hard_negative_mined", "hard_negative_mined_v2_complexity", "hard_negative_control"]
        )]["source_id"]
    )

    id_to_groups: dict = {}
    for g in manifest_n30["groups"]:
        members = g["members"]
        ids_in_group = list(members.get("mined_hard_negative_ids", []))
        if members.get("original_hard_negative_control_id"):
            ids_in_group.append(members["original_hard_negative_control_id"])
        for hn_id in ids_in_group:
            id_to_groups.setdefault(hn_id, []).append(g["group_id"])

    not_found = negative_source_ids - set(id_to_groups)
    assert not not_found, (
        f"{len(not_found)} negative ID dang dung trong features_v2_N30.parquet nhung KHONG xuat hien "
        f"trong bat ky group nao cua manifest: {sorted(not_found)[:10]}"
    )

    duplicated = {hn_id: grps for hn_id, grps in id_to_groups.items() if len(grps) > 1}
    assert not duplicated, f"Negative ID xuat hien o NHIEU HON MOT group (trung lap): {duplicated}"


def test_21_old_groups_byte_identical_to_N20(manifests_and_registry):
    _, manifest_n20, manifest_n30 = manifests_and_registry
    old_groups_n20 = manifest_n20["groups"]
    old_group_ids = {g["group_id"] for g in old_groups_n20}
    n30_by_id = {g["group_id"]: g for g in manifest_n30["groups"]}

    missing = old_group_ids - set(n30_by_id)
    assert not missing, f"Group cu BI MAT khoi split_manifest_N30.json: {sorted(missing)}"

    mismatched = []
    for g20 in old_groups_n20:
        g30 = n30_by_id[g20["group_id"]]
        if json.dumps(g20, sort_keys=True) != json.dumps(g30, sort_keys=True):
            mismatched.append(g20["group_id"])
    assert not mismatched, (
        f"HARD STOP: {len(mismatched)} group cu (trong {len(old_groups_n20)} group N20 goc) "
        f"KHONG byte-identical trong split_manifest_N30.json: {mismatched}"
    )


def test_every_manifest_group_has_corresponding_registry_incident(manifests_and_registry):
    registry, _, manifest_n30 = manifests_and_registry
    registry_ids = set(registry["incident_id"])
    orphan_groups = [
        g["group_id"] for g in manifest_n30["groups"]
        if g["members"]["positive_incident_id"] not in registry_ids
    ]
    assert not orphan_groups, (
        f"Group trong manifest tro toi incident_id KHONG TON TAI trong incident_registry_N30.csv: {orphan_groups}"
    )
