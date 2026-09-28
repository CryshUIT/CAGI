"""NSS 2026 - Viec 1 (T17): stress-test "mimicry" - chen action benign THAT
(lay tu hard-negative cung incident) vao giua trajectory positive, o nhieu
muc (2/4/8 action), xem PR-AUC giam bao nhieu khi hanh vi bi "nguy trang".

THIET KE (da bao cao va duoc xac nhan truoc khi chay):
1. Lay trajectory positive THAT (build tu cache, khong goi API moi) va
   trajectory hard-negative THAT CUNG incident (band-matched, tu chinh
   metadata/hard_negative_registry.csv).
2. Chon N action THAT tu hard-negative (khong bia), chen vao N khe ngau
   nhien giua cac action positive da co (seed co dinh de tai lap), gan
   timestamp noi suy giua 2 action lang gieng de giu thu tu thoi gian hop ly.
3. Tinh lai feature O DUNG 8 moc prefix (k_2/3/5/7, ratio_25/50/75/100) tren
   trajectory da keo dai, dung DUNG ham that extract_all_prefixes() (khong
   viet lai logic feature).
4. Cham diem bang model M1 fit tren 14 incident con lai (dung fold, khong
   dung chinh incident do de train) - hard-negative GIU NGUYEN khong bi chen
   (chi kiem tra kha nang "nguy trang" cua trajectory duong).

Pilot truoc tren vai incident (kiem tra sanity: feature khong NaN, tang dan
hop ly, PR-AUC muc L=0 phai KHOP CHINH XAC 0.6624 khi gop toan bo 15 incident).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes  # noqa: E402
from src.features.extractor import extract_all_prefixes  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import Trajectory, load_trajectory_config  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

EVAL15 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022", "paraluni_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024", "xkingdom_2024",
]
LEVELS = [0, 2, 4, 8]


def build_positive_trajectory(incident_id: str, reg_row: dict, config):
    chain, seed, start_block = reg_row["chain_primary"], reg_row["seed_address"], int(reg_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(chain, seed, start_block, incident_id, label=1, config=config, do_collect=False)
    return traj


def build_hard_negative_trajectory(hn_row: dict, incident_id: str, config):
    # QUAN TRONG (da sua sau 2 lan thu sai): cache raw cho hard-negative duoc
    # luu duoi thu muc cua CHINH incident_id GOC (parent_incident_id, vd
    # "chibi_finance_2023"), KHONG PHAI hard_negative_id (vd "..__hn000") -
    # xac nhan bang cach doi chieu voi scripts/build_demo_data.py::
    # load_events_hard_negative (dung dung row["parent_incident_id"]) va
    # kiem tra truc tiep thu muc data/raw/. Dung id sai se tra ve trajectory
    # RONG (khong loi, chi khong tim thay cache) - da phat hien qua 2 lan pilot.
    chain, seed, start_block = hn_row["chain"], hn_row["seed_address"], int(hn_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(
        chain, seed, start_block, hn_row["parent_incident_id"], label=0, config=config,
        do_collect=False, max_iterations=2,
    )
    return traj


def insert_mimicry(pos_actions, hn_actions, n_insert: int, rng: np.random.Generator):
    """Chen n_insert action THAT tu hn_actions vao giua pos_actions (khe ngau
    nhien giua 2 action lang gieng, timestamp noi suy). Tra ve list moi (KHONG
    sua pos_actions goc)."""
    L = len(pos_actions)
    if L < 2 or not hn_actions:
        return list(pos_actions), 0
    gaps = list(range(1, L))  # khe (i-1, i) cho i=1..L-1
    chosen_gaps = rng.choice(gaps, size=n_insert, replace=(n_insert > len(gaps)))
    chosen_actions_idx = rng.choice(len(hn_actions), size=n_insert, replace=(n_insert > len(hn_actions)))

    inserted = []
    for gap_i, act_i in zip(chosen_gaps, chosen_actions_idx):
        t_before = pos_actions[gap_i - 1].timestamp
        t_after = pos_actions[gap_i].timestamp
        frac = rng.uniform(0.05, 0.95)
        t_new = t_before + (t_after - t_before) * frac
        if t_new <= t_before:
            t_new = t_before  # trajectory qua ngan/cach nhau <1s - giu >= t_before, KHONG lui ve truoc
        src_ev = hn_actions[act_i]
        # CanonicalEvent la pydantic BaseModel (khong phai dataclass) -
        # dung model_copy(update=...), KHONG dung dataclasses.replace().
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
    """Doi chieu dong ratio_100 (full trajectory, L=0 khong chen) voi
    features_v2.parquet that - PHAI khop tuyet doi (sanity check bat buoc)."""
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
            mismatches.append((c, "THIEU CỘT"))
            continue
        a, b = real_row[c], new_row[c]
        if pd.isna(a) and pd.isna(b):
            continue
        if abs(float(a) - float(b)) > 1e-6:
            mismatches.append((c, f"{a} != {b}"))
    if mismatches:
        print(f"  [SAI LECH] {incident_id}: {len(mismatches)} cot khong khop: {mismatches[:5]}")
        return False
    print(f"  [OK] {incident_id}: ratio_100 recompute khop CHINH XAC voi features_v2.parquet ({len(feat_cols)} cot)")
    return True


def main_pilot():
    config = load_trajectory_config()
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry.csv").set_index("incident_id")
    hn_reg = pd.read_csv(ROOT / "metadata" / "hard_negative_registry.csv")
    df_v2 = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")

    pilot_incidents = ["chibi_finance_2023", "hackerdao_2022", "utopiasphere_2024"]
    rng = np.random.default_rng(42)

    for inc in pilot_incidents:
        print(f"\n=== PILOT {inc} ===")
        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        print(f"  positive trajectory: {len(pos_traj)} action")

        # L=0 sanity check
        df0 = features_for_trajectory(pos_traj, inc, 1)
        validate_against_real(df_v2, inc, df0)

        # Chon hard-negative co NHIEU action nhat trong toi da 10 candidate dau
        # (thay vi luon lay hang dau) - pool chen can du lon de co the chen
        # thu 8 action THAT khac nhau ma khong phai lap lai qua nhieu.
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
