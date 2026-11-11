"""Final held-out (M1/B3' da dong bang tren 36 group) - kiem tra file dong
bang ton tai, theta_frozen la out-of-fold (khong doi sau khi tao), va 2
incident test khong trung voi 36 group train."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTRA_V4 = ROOT / "results" / "reports" / "extra_v4"


def test_frozen_model_files_exist_and_metadata_consistent():
    for prefix in ["M1_FROZEN_final_N36", "B3prime_FROZEN_final_N36"]:
        assert (EXTRA_V4 / f"{prefix}.pkl").exists()
        assert (EXTRA_V4 / f"{prefix}_platt_calibrator.pkl").exists()
        meta = json.loads((EXTRA_V4 / f"{prefix}_metadata.json").read_text(encoding="utf-8"))
        assert meta["n_train_groups"] == 36
        assert 0.0 < meta["theta_frozen"] < 1.0
        assert meta["seed"] == 42


def test_frozen_models_unpickle_and_predict():
    import sys
    sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))
    from _freeze_final_B3prime_N36 import XGBFixedColumns
    # Pickle luu class duoi module "__main__" (file duoc chay truc tiep luc
    # dong bang) - gan vao sys.modules["__main__"] de unpickle duoc tu test.
    sys.modules["__main__"].XGBFixedColumns = XGBFixedColumns

    with open(EXTRA_V4 / "M1_FROZEN_final_N36.pkl", "rb") as f:
        m1 = pickle.load(f)
    with open(EXTRA_V4 / "B3prime_FROZEN_final_N36.pkl", "rb") as f:
        b3 = pickle.load(f)
    df = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_final_heldout_new.parquet")
    meta_cols = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label", "prefix_label", "prefix_len", "trajectory_len"]
    X = df[[c for c in df.columns if c not in meta_cols]]
    p1 = m1.predict_proba(X)
    p2 = b3.predict_proba(X)
    assert len(p1) == len(df)
    assert len(p2) == len(df)
    assert ((p1 >= 0) & (p1 <= 1)).all()
    assert ((p2 >= 0) & (p2 <= 1)).all()


def test_final_heldout_incidents_not_in_36_group_train():
    train = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
    test = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_final_heldout_new.parquet")
    train_groups = set(train["group_id"].unique())
    test_groups = set(test["group_id"].unique())
    assert train_groups.isdisjoint(test_groups), f"Trung group: {train_groups & test_groups}"
    assert test_groups == {
        "rari_capital_fuse_2022", "curve_crv_eth_attacker_2023",
        "pancakebunny_2021", "rikkei_finance_2022",
    }


def test_final_heldout_registry_append_only():
    reg37 = pd.read_csv(ROOT / "metadata" / "incident_registry_N37.csv")
    reg_fh = pd.read_csv(ROOT / "metadata" / "incident_registry_final_heldout.csv")
    assert len(reg_fh) == 50
    pd.testing.assert_frame_equal(reg_fh.iloc[:43].reset_index(drop=True), reg37.reset_index(drop=True))
