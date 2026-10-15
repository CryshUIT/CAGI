"""Checkpoint C: build features_v2_N20.parquet cho dataset expansion N20
(15 incident cu + 5 incident moi + 125 hard-negative moi), dung pipeline
feature DA SUA leak prefix_ratio (src/models/baselines.py da sua truoc do -
script nay chi build FEATURE, khong dinh nghia lai candidate_columns, nen
khong can sua gi them o day; M1/B3 se tu dong loai prefix_ratio khi fit()).

KHONG ghi de data/processed/features_v2.parquet goc hay bat ky file freeze
nao. Dung metadata/incident_registry_N20.csv, hard_negative_registry_N20.csv,
split_manifest_N20.json qua monkeypatch module-level constants (khong sua
code nguon cua src/pipeline/dataset_builder.py).

LUU Y QUAN TRONG (Checkpoint C'', phat hien qua chinh pytest): monkeypatch
PHAI dat TRONG main() (khong dat o muc module, truoc day da gay regression
THAT - tests/test_n20_reproduces_v1.py bi FAIL vi chi IMPORT module nay (de
dung CONFIG_N20_PATH/verify_config_guard trong tests/test_n20_build_config_guard.py)
da lam THAY DOI vinh vien dataset_builder.REGISTRY_PATH cho CA session pytest,
khien test "default path" khong con dung default nua). Import module nay o
BAT KY DAU (ke ca trong test khac) BAY GIO an toan, khong con side-effect.
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
OUT_PARQUET = REPO_ROOT / "data" / "processed" / "features_v2_N20.parquet"
OUT_SCHEMA = REPO_ROOT / "configs" / "features_v2_computed_N20.json"
CONFIG_N20_PATH = REPO_ROOT / "configs" / "data_N20.yaml"
REQUIRED_DEX_ADDRESSES = {
    "0x66a9893cc07d91d95644aedd05d03f95e1dba8af",  # Uniswap Universal Router v2 (Cork)
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",  # Uniswap Universal Router v1.2 variant (Hedgey)
}

def _apply_n20_monkeypatch() -> None:
    """Monkeypatch CHI khi duoc GOI (trong main()), KHONG o muc module - tranh
    side-effect toan cuc khi module nay bi IMPORT boi file khac (vd test)."""
    dataset_builder.REGISTRY_PATH = REPO_ROOT / "metadata" / "incident_registry_N20.csv"
    dataset_builder.HARD_NEGATIVE_REGISTRY_PATH = REPO_ROOT / "metadata" / "hard_negative_registry_N20_combined.csv"
    # QUAN TRONG: file "_combined" gom CA 536 dong hard-negative CU (15 incident
    # goc) VA 125 dong MOI (5 incident N20) - phat hien bug 2026-10-14: ban build
    # dau tien chi tro thang toi hard_negative_registry_N20.csv (CHI 125 dong
    # moi), VO TINH LAM MAT 536 hard-negative cu cua N=15 khoi dataset N20 (vi
    # monkeypatch GHI DE hoan toan, khong phai THEM VAO). Da sua: dung file gop.
    dataset_builder.SPLIT_MANIFEST_PATH = REPO_ROOT / "metadata" / "split_manifest_N20.json"
    dataset_builder.HARD_NEGATIVE_REGISTRY_V2_COMPLEXITY_PATH = (
        REPO_ROOT / "metadata" / "hard_negative_registry_v2_complexity_N20_combined.csv"
    )
    # Checkpoint C'' muc 2: dong bo vong mine "v2_complexity" (he thong, TARGET=10)
    # cho 5 incident moi (156 dong = 110 cu + 46 moi, xem
    # scripts/_mine_hard_negatives_v2_complexity_N20.py).


def verify_config_guard(config_path_used: Path = CONFIG_N20_PATH):
    """CHOT CHAN CAU HINH (Checkpoint C'', muc 4) - day la lan thu 3 1 loi
    cau hinh tuong tu (quen truyen config N20, xem Checkpoint C' muc 6 - Cork
    bi anh huong that, 1 action voi config goc vs 2 action voi config N20)
    duoc bat qua doi chieu tay; chan truc tiep bang code thay vi dua vao
    nguoi kiem tra lai moi lan. Tra ve TrajectoryConfig da load neu qua
    chot chan, raise AssertionError neu khong (dung cho ca main() va test)."""
    assert config_path_used == CONFIG_N20_PATH, (
        f"CHOT CHAN: duong dan config PHAI la {CONFIG_N20_PATH}, dang dung {config_path_used}"
    )
    assert config_path_used.exists(), f"Khong tim thay file config {config_path_used}"
    config_n20 = load_trajectory_config(str(config_path_used))
    missing_dex = REQUIRED_DEX_ADDRESSES - set(config_n20.allowlist)
    assert not missing_dex, (
        f"CHOT CHAN: allowlist cua {config_path_used} THIEU dia chi Universal Router bat buoc: {missing_dex} "
        "- feature build se KHONG phan anh dung N20 allowlist neu thieu."
    )
    return config_n20


def main():
    print("=== Checkpoint C: build trajectory that cho N20 (15 cu + 5 moi) ===", flush=True)
    _apply_n20_monkeypatch()
    config_n20 = verify_config_guard()
    print(f"[CHOT CHAN] config={CONFIG_N20_PATH}, 2 dia chi Universal Router DA CO trong allowlist.", flush=True)

    items = dataset_builder.load_rq1_trajectories(
        config=config_n20, verbose=True, include_v2_complexity=True,
    )
    n_pos = sum(1 for i in items if i.label == 1)
    n_neg = sum(1 for i in items if i.label == 0)
    n_neg_v2 = sum(1 for i in items if i.kind == "hard_negative_mined_v2_complexity")
    print(f"\nTong trajectory: {len(items)} (positive={n_pos}, negative={n_neg}, "
          f"hard-negative v2 cu={n_neg_v2})", flush=True)

    total_specs = sum(len(generate_prefixes(i.trajectory)) for i in items)
    print(f"Tong prefix row = {total_specs}", flush=True)

    print("\n=== Tinh feature (pipeline da sua leak prefix_ratio o tang model, "
          "khong phai extractor) ===", flush=True)
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
    config_sha256 = hashlib.sha256(CONFIG_N20_PATH.read_bytes()).hexdigest()

    schema = {
        "version": "v2_N20",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(full)),
        "n_positive_trajectories": n_pos,
        "n_negative_trajectories": n_neg,
        "feature_columns": sorted(X.columns),
        "n_feature_columns": len(X.columns),
        "leakage_check": f"PASS - tong action_count_* == prefix_len cho tat ca {len(full)} dong",
        "source": "dataset expansion N20 (2026-10-14) - KHONG ghi de features_v2.parquet goc",
        "config_path_used": str(CONFIG_N20_PATH.relative_to(REPO_ROOT)),
        "config_sha256": config_sha256,
        "config_allowlist_verified_contains": sorted(REQUIRED_DEX_ADDRESSES),
    }
    OUT_SCHEMA.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Da luu {OUT_SCHEMA}", flush=True)


if __name__ == "__main__":
    main()
