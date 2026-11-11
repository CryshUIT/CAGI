"""N37 (v4_heldout) - kiem tra: khong trung incident, schema hop le, hash
cache khop, so dong registry dung, train/test (30 cu vs incident moi)
khong giao nhau. KHONG dong vao features_v2_N30.parquet/registry N30 goc."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NEW_POSITIVE_IDS = [
    "sturdy_finance_2023", "jimbos_protocol_2023", "rodeo_finance_2023",
    "sentiment_protocol_2023", "pike_finance_2024", "uwu_lend_2024",
]
EXCLUDED_IDS = {"fortress_protocol_2022"}  # loi thu thap thuc, xem decision_log


def test_registry_N37_row_count_and_append_only():
    reg30 = pd.read_csv(ROOT / "metadata" / "incident_registry_N30.csv")
    reg37 = pd.read_csv(ROOT / "metadata" / "incident_registry_N37.csv")
    assert len(reg30) == 36
    assert len(reg37) == 43, f"Ky vong 43 dong (36 cu + 7 moi, bao gom fortress bi loai nhung van giu dong), co {len(reg37)}"
    # append-only: 36 dong dau cua N37 PHAI giong y nguyen N30
    pd.testing.assert_frame_equal(reg37.iloc[:36].reset_index(drop=True), reg30.reset_index(drop=True))


def test_registry_N37_no_duplicate_incident_id_seed_or_tx():
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry_N37.csv")
    assert reg["incident_id"].is_unique, "incident_id trung lap trong registry N37"
    # seed_address co the trung giua 1 incident va control cua no (khong trung giua 2 incident KHAC NHAU thuc su)
    dup_seed = reg[reg["seed_address"].notna()].groupby(reg["seed_address"].str.lower())["incident_id"].nunique()
    bad = dup_seed[dup_seed > 1]
    # loai truong hop benign_control cung ten goc (vd ronin_bridge_2022 vs ronin_benign_control_2022 KHAC dia chi, khong anh huong)
    assert len(bad) == 0, f"seed_address trung giua >1 incident_id: {bad.index.tolist()}"


def test_v4_heldout_tier_has_exactly_7_rows_6_usable():
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry_N37.csv")
    v4 = reg[reg.eval_tier == "v4_heldout"]
    assert len(v4) == 7, f"Ky vong 7 dong eval_tier=v4_heldout, co {len(v4)}"
    assert set(v4.incident_id) == set(NEW_POSITIVE_IDS) | EXCLUDED_IDS
    excluded_row = v4[v4.incident_id == "fortress_protocol_2022"].iloc[0]
    assert excluded_row["endpoint_type"] == "collection_failed_excluded"


def test_features_v2_N37_schema_valid():
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
    required_cols = {"trajectory_id", "source_id", "group_id", "kind", "chain", "label", "prefix_label", "prefix_len", "trajectory_len"}
    assert required_cols.issubset(set(df.columns))
    assert df["label"].isin([0, 1]).all()
    assert not df.isnull().any().any(), "features_v2_N37.parquet khong duoc co gia tri null (da fillna(0.0) o buoc build)"
    # khong co incident bi loai nao lot vao dataset
    assert not set(df["group_id"].unique()) & EXCLUDED_IDS
    assert not set(df["source_id"].unique()) & EXCLUDED_IDS


def test_features_v2_N37_contains_6_new_positive_incidents():
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
    positives_v4 = df[df["kind"] == "positive_v4_heldout"]["source_id"].unique()
    assert set(positives_v4) == set(NEW_POSITIVE_IDS)
    old_positives = df[df["kind"] == "positive"]["source_id"].unique()
    assert len(old_positives) == 30


def test_held_out_train_test_groups_disjoint():
    """Train = 30 incident cu (+ hard-negative cua chinh ho); Test = 1
    incident moi. group_id cua test KHONG duoc xuat hien trong train -
    bao gom loai het hard-negative cua incident test khoi train (dung
    yeu cau nguoi dung)."""
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
    old_group_ids = set(df[df["kind"].isin(["positive", "hard_negative_control", "hard_negative_mined", "hard_negative_mined_v2_complexity"])]["group_id"].unique())
    for test_iid in NEW_POSITIVE_IDS:
        test_mask = df["group_id"] == test_iid
        assert test_mask.any(), f"Khong tim thay group_id={test_iid} trong features_v2_N37.parquet"
        train_mask = df["group_id"].isin(old_group_ids)
        assert not (train_mask & test_mask).any(), f"Train/test giao nhau cho {test_iid}"
        assert test_iid not in old_group_ids, f"{test_iid} khong duoc o trong nhom 30 incident cu dung lam train"


def test_no_hard_negative_address_shared_across_new_and_old_incidents():
    hn_old_main = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_N30_combined.csv")
    hn_old_v2 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv")
    hn_new = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity_N37_new.csv")
    all_hn = pd.concat([hn_old_main, hn_old_v2, hn_new], ignore_index=True)
    n_parents_per_address = all_hn.groupby(all_hn["seed_address"].str.lower())["parent_incident_id"].nunique()
    shared = n_parents_per_address[n_parents_per_address > 1]
    assert len(shared) == 0, f"Dia chi hard-negative bi dung chung giua >1 incident: {shared.index.tolist()}"


def test_data_N37_config_hash_matches_N30():
    """configs/data_N37.yaml la ban sao chinh xac configs/data_N30.yaml -
    khong co thay doi allowlist/decode de hop incident moi (dung quy tac cung)."""
    h30 = hashlib.sha256((ROOT / "configs" / "data_N30.yaml").read_bytes()).hexdigest()
    h37 = hashlib.sha256((ROOT / "configs" / "data_N37.yaml").read_bytes()).hexdigest()
    assert h30 == h37, "data_N37.yaml PHAI giong byte-for-byte data_N30.yaml (khong sua allowlist cho incident moi)"
