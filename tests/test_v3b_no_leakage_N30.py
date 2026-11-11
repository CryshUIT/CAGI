"""EXPLORATORY / post-hoc (nhom v3b: learning curve, leave-one-chain-out,
time-split) - kiem tra khong co leakage train/test theo incident va khong
co hard-negative dung chung giua 2 incident khac nhau trong N=30."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_group_id_equals_parent_incident_for_all_hard_negatives():
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N30.parquet")
    hard_neg = df[df["kind"] != "positive"][["source_id", "group_id"]].drop_duplicates()
    positives = df[df["kind"] == "positive"][["source_id", "group_id"]].drop_duplicates()
    positive_ids = set(positives["source_id"])
    for _, row in hard_neg.iterrows():
        assert row["group_id"] in positive_ids, (
            f"hard-negative {row['source_id']} co group_id={row['group_id']} khong khop incident duong tinh nao"
        )
    assert df["group_id"].nunique() == 30, f"Ky vong 30 group_id (= 30 incident), co {df['group_id'].nunique()}"


def test_no_hard_negative_address_shared_across_parent_incidents():
    hn_main = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_N30_combined.csv")
    hn_v2 = pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv")
    all_hn = pd.concat([hn_main, hn_v2], ignore_index=True)
    n_parents_per_address = all_hn.groupby("seed_address")["parent_incident_id"].nunique()
    shared = n_parents_per_address[n_parents_per_address > 1]
    assert len(shared) == 0, f"Co {len(shared)} dia chi hard-negative bi dung chung giua >1 incident: {shared.index.tolist()}"


def test_loio_train_test_groups_disjoint():
    """Mo phong 1 fold LOIO: train/test PHAI khong giao nhau theo group_id."""
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N30.parquet")
    all_groups = sorted(df["group_id"].unique())
    held_out = all_groups[0]
    train_mask = df["group_id"] != held_out
    test_mask = df["group_id"] == held_out
    train_groups = set(df.loc[train_mask, "group_id"].unique())
    test_groups = set(df.loc[test_mask, "group_id"].unique())
    assert train_groups.isdisjoint(test_groups), "Train/test group_id giao nhau - leakage!"
    assert test_groups == {held_out}


def test_leave_one_chain_out_groups_disjoint():
    """Mo phong leave-one-chain-out: cac incident CUNG chain voi test PHAI
    khong xuat hien trong train (khac LOIO, noi incident cung chain VAN o
    trong train)."""
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N30.parquet")
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry_N30.csv")
    chain_map = reg.set_index("incident_id")["chain_primary"].to_dict()
    df = df.copy()
    df["chain_of_incident"] = df["group_id"].map(chain_map)
    for chain in df["chain_of_incident"].dropna().unique():
        test_mask = df["chain_of_incident"] == chain
        train_mask = ~test_mask
        train_chains = set(df.loc[train_mask, "chain_of_incident"].unique())
        assert chain not in train_chains, f"Chain {chain} van con trong train sau khi leave-one-chain-out"
