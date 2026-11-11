"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_t17_mimicry_stress_test.py cho N=30.

LUU Y QUAN TRONG (doc code goc, khong doan): file goc hien tai CHI con
`main_pilot()` - mot script PILOT/sanity-check (3 incident, KHONG xuat
CSV/MD, KHONG tinh pooled PR-AUC/CI) dung de doi chieu ratio_100 tai tao
voi features_v2.parquet THAT (qua validate_against_real()). Day KHONG
PHAI "ban full co bang ket qua" - ban day du/co bang that ra la
run_t17_mimicry_full.py (xem output file ten "..._stress_test_2026-09-22.csv"
trong CHINH script do, gay nham ten). Script nay giu dung hanh vi goc:
chay 3 incident pilot (chibi_finance_2023, hackerdao_2022, utopiasphere_2024
- ca 3 deu co trong N30), doi chieu voi features_v2_N30.parquet.

Thay doi DUY NHAT: REGISTRY_PATH -> incident_registry_N30.csv,
HN_REGISTRY_PATH -> hard_negative_registry_N30_combined.csv, FEATURES_PATH
-> features_v2_N30.parquet, config -> data_N30.yaml.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.features.extractor import extract_all_prefixes  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import Trajectory, load_trajectory_config  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
HN_REGISTRY_PATH = ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
CONFIG_PATH = ROOT / "configs" / "data_N30.yaml"


def build_positive_trajectory(incident_id, reg_row, config):
    chain, seed, start_block = reg_row["chain_primary"], reg_row["seed_address"], int(reg_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(chain, seed, start_block, incident_id, label=1, config=config, do_collect=False)
    return traj


def build_hard_negative_trajectory(hn_row, incident_id, config):
    chain, seed, start_block = hn_row["chain"], hn_row["seed_address"], int(hn_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(
        chain, seed, start_block, hn_row["parent_incident_id"], label=0, config=config,
        do_collect=False, max_iterations=2,
    )
    return traj


def insert_mimicry(pos_actions, hn_actions, n_insert: int, rng: np.random.Generator):
    L = len(pos_actions)
    if L < 2 or not hn_actions:
        return list(pos_actions), 0
    gaps = list(range(1, L))
    chosen_gaps = rng.choice(gaps, size=n_insert, replace=(n_insert > len(gaps)))
    chosen_actions_idx = rng.choice(len(hn_actions), size=n_insert, replace=(n_insert > len(hn_actions)))

    inserted = []
    for gap_i, act_i in zip(chosen_gaps, chosen_actions_idx):
        t_before = pos_actions[gap_i - 1].timestamp
        t_after = pos_actions[gap_i].timestamp
        frac = rng.uniform(0.05, 0.95)
        t_new = t_before + (t_after - t_before) * frac
        if t_new <= t_before:
            t_new = t_before
        src_ev = hn_actions[act_i]
        new_ev = src_ev.model_copy(update={"timestamp": t_new, "log_index": src_ev.log_index + 900000 + len(inserted)})
        inserted.append(new_ev)

    merged = sorted(list(pos_actions) + inserted, key=lambda e: (e.timestamp, e.block_number, e.tx_hash, e.log_index))
    return merged, len(inserted)


def features_for_trajectory(traj: Trajectory, incident_id: str, label: int) -> pd.DataFrame:
    rows = []
    for spec, feats in extract_all_prefixes(traj):
        row = dict(feats)
        row.update({"source_id": incident_id, "group_id": incident_id, "label": label,
                    "prefix_label": spec.label, "trajectory_len": len(traj)})
        rows.append(row)
    return pd.DataFrame(rows)


def validate_against_real(df_v2: pd.DataFrame, incident_id: str, recomputed: pd.DataFrame) -> bool:
    real_row = df_v2[(df_v2.source_id == incident_id) & (df_v2.label == 1) & (df_v2.prefix_label == "ratio_100")]
    if len(real_row) == 0:
        print(f"  [CANH BAO] khong tim thay dong ratio_100 that cho {incident_id} de doi chieu")
        return False
    real_row = real_row.iloc[0]
    new_row = recomputed[recomputed.prefix_label == "ratio_100"]
    if len(new_row) == 0:
        print(f"  [CANH BAO] khong tinh duoc dong ratio_100 moi cho {incident_id}")
        return False
    new_row = new_row.iloc[0]
    feat_cols = [c for c in df_v2.columns if c not in META_COLS]
    mismatches = []
    for c in feat_cols:
        if c not in new_row:
            mismatches.append((c, "THIEU COT"))
            continue
        a, b = real_row[c], new_row[c]
        if pd.isna(a) and pd.isna(b):
            continue
        if abs(float(a) - float(b)) > 1e-6:
            mismatches.append((c, f"{a} != {b}"))
    if mismatches:
        print(f"  [SAI LECH] {incident_id}: {len(mismatches)} cot khong khop: {mismatches[:5]}")
        return False
    print(f"  [OK] {incident_id}: ratio_100 recompute khop CHINH XAC voi features_v2_N30.parquet ({len(feat_cols)} cot)")
    return True


def main_pilot():
    check_m1_gate()
    config = load_trajectory_config(str(CONFIG_PATH))
    reg = pd.read_csv(REGISTRY_PATH).set_index("incident_id")
    hn_reg = pd.read_csv(HN_REGISTRY_PATH)
    df_v2 = pd.read_parquet(FEATURES_PATH)

    pilot_incidents = ["chibi_finance_2023", "hackerdao_2022", "utopiasphere_2024"]
    rng = np.random.default_rng(42)

    for inc in pilot_incidents:
        print(f"\n=== PILOT {inc} (N30) ===")
        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        print(f"  positive trajectory: {len(pos_traj)} action")

        df0 = features_for_trajectory(pos_traj, inc, 1)
        validate_against_real(df_v2, inc, df0)

        candidates = hn_reg[hn_reg.parent_incident_id == inc].head(10)
        best_hn_row, best_hn_traj, best_len = None, None, -1
        for _, cand in candidates.iterrows():
            t = build_hard_negative_trajectory(cand.to_dict(), inc, config)
            if len(t) > best_len:
                best_hn_row, best_hn_traj, best_len = cand.to_dict(), t, len(t)
        hn_row, hn_traj = best_hn_row, best_hn_traj
        print(f"  hard-negative da chon ({hn_row['hard_negative_id']}, tot nhat trong {len(candidates)} candidate dau) trajectory: {len(hn_traj)} action")

        for n in [2, 4, 8]:
            merged_actions, n_actually = insert_mimicry(pos_traj.actions, hn_traj.actions, n, rng)
            aug_traj = Trajectory(trajectory_id=inc, seed_address=pos_traj.seed_address, actions=merged_actions, label=1, incident_id=inc)
            dfN = features_for_trajectory(aug_traj, inc, 1)
            has_nan = dfN.isna().any().any()
            print(f"  n_insert={n} (thuc te chen {n_actually}): do dai moi={len(aug_traj)}, "
                  f"so dong prefix={len(dfN)}, prefix_label={sorted(dfN.prefix_label.tolist())}, co_NaN={has_nan}")
            if has_nan:
                print("    [CANH BAO] co NaN trong feature - can kiem tra!")


if __name__ == "__main__":
    main_pilot()
