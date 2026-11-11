# -*- coding: utf-8 -*-
"""Bat buoc theo mac dinh da chot: "Cache thieu: tai tao bang co che da dung
cho lendhub_2023, xac nhan features_v2_N30.parquet khong doi hash." Tai tao
RIENG 30-incident-cu (dung logic build_old_30_items trong
_build_features_v2_N37.py) vao file TAM, so sanh SHA-256 voi file goc dong
bang (data/processed/features_v2_N30.parquet) - PHAI giong byte-for-byte."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))
from _build_features_v2_N37 import build_old_30_items, extract_rows  # noqa: E402
from src.features.extractor import generate_prefixes  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

FROZEN = ROOT / "data" / "processed" / "features_v2_N30.parquet"
TEMP_OUT = ROOT / "data" / "processed" / "_temp_check_features_v2_N30_rebuild.parquet"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    config_n30 = load_trajectory_config(str(ROOT / "configs" / "data_N30.yaml"))
    items = build_old_30_items(config_n30)

    total_specs = sum(len(generate_prefixes(i.trajectory)) for i in items)
    rows, meta_rows, leakage_violations = [], [], []
    extract_rows(items, leakage_violations, rows, meta_rows)
    assert not leakage_violations, leakage_violations

    X = pd.DataFrame(rows).fillna(0.0)
    meta = pd.DataFrame(meta_rows)
    full = pd.concat([meta, X], axis=1)
    assert len(full) == total_specs

    full.to_parquet(TEMP_OUT, index=False)

    h_frozen = sha256_file(FROZEN)
    h_new = sha256_file(TEMP_OUT)
    print(f"Frozen  ({FROZEN.name}): {h_frozen}")
    print(f"Rebuild ({TEMP_OUT.name}): {h_new}")
    if h_frozen == h_new:
        print("\n*** KHOP HOAN TOAN - features_v2_N30.parquet KHONG DOI HASH. OK tiep tuc. ***")
    else:
        print("\n*** KHAC HASH - DUNG LAI, BAO CAO NGUOI DUNG TRUOC KHI TIEP TUC. ***")
        raise SystemExit(1)

    TEMP_OUT.unlink()


if __name__ == "__main__":
    main()
