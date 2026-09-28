"""NSS 2026 (2026-09-26) - Huong 2: xay 2 feature moi nham vao "dip" tai
checkpoint quan sat 50% (RQ2): burstiness_recent_shift va
recent_half_new_counterparty_share.

Dong luc (nhin truc tiep vao du lieu that, KHONG doan mo): so sanh feature
vector cua 3 positive diem thap nhat tai ratio_50 (wooppv2_2024 prefix_len=8,
hackerdao_2022 prefix_len=18, new_free_dao_2022 prefix_len=6, dung
data/processed/oof_predictions_v1.csv de xac dinh) qua 4 checkpoint
25/50/75/100 - phat hien wooppv2_2024 co chuyen bien RO RET dung luc 50%
(bridge_deposit xuat hien, fan_out 1->3, unique_counterparties 1->3,
value_retention 0.998->0.567) nhung feature HIEN TAI cua M1 chi co burstiness/
inter_action_gap TINH TREN TOAN BO prefix (1 con so duy nhat cho ca prefix),
KHONG bat duoc "THAY DOI trong nua sau so voi nua dau" - day la khoang trong
cu the co the lap duoc bang feature moi, khong phai suy doan.

2 feature moi (CHI dua tren action DA quan sat trong prefix hien tai, KHONG
leak tuong lai):

1. burstiness_recent_shift = burstiness(nua sau prefix) - burstiness(nua dau
   prefix) (cong thuc Goh-Barabasi giong het _temporal_features, tinh rieng
   tren 2 nua). Can >=4 action de co it nhat 2 gap moi nua; <4 action -> 0.0
   (trung lap, khong xac dinh - dung quy uoc mac dinh giong cac feature khac).
2. recent_half_new_counterparty_share = (so counterparty MOI xuat hien lan
   dau trong nua sau) / (tong so unique counterparty trong ca prefix) - bat
   truc tiep hien tuong "fan-out xay ra GAN DAY" (wooppv2_2024: 2/3 = 0.667
   tai ratio_50, vs 0/1=0 tai ratio_25 vi chua co fan-out).

Nguon actions: positive tu data/processed/{source_id}_events.json (co san);
hard-negative rebuild qua expand_and_build_trajectory (giong het
generate_alert_case_studies.py::_rebuild_hard_negative_events), CACHE 1 lan
moi source_id (khong rebuild lai cho tung prefix_len cua cung 1 trajectory).

Xuat: data/processed/mid_trajectory_features_2026-09-26.parquet (chi 2 cot
moi + key source_id/prefix_len, de merge vao features_v2.parquet o buoc sau,
KHONG ghi de features_v2.parquet goc).
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.nested_eval import dedupe_pooled_prefixes  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

PROCESSED_DIR = ROOT / "data" / "processed"
OUT_PATH = PROCESSED_DIR / "mid_trajectory_features_2026-09-26.parquet"


def burstiness_of(timestamps) -> float:
    if len(timestamps) < 2:
        return 0.0
    gaps = [(timestamps[i] - timestamps[i - 1]).total_seconds() for i in range(1, len(timestamps))]
    n = len(gaps)
    mean = sum(gaps) / n
    var = sum((g - mean) ** 2 for g in gaps) / n
    std = math.sqrt(var)
    return (std - mean) / (std + mean) if (std + mean) > 0 else 0.0


def compute_features_for_prefix(actions: list) -> dict:
    n = len(actions)
    if n < 4:
        burstiness_recent_shift = 0.0
    else:
        mid = n // 2
        ts_first = [pd.Timestamp(a["timestamp"]) for a in actions[: mid + 1]]
        ts_second = [pd.Timestamp(a["timestamp"]) for a in actions[mid:]]
        burstiness_recent_shift = burstiness_of(ts_second) - burstiness_of(ts_first)

    mid = n // 2
    first_half_dsts = {a["dst"] for a in actions[:mid]}
    all_dsts = {a["dst"] for a in actions}
    new_in_second_half = {a["dst"] for a in actions[mid:]} - first_half_dsts
    total_unique = len(all_dsts)
    recent_half_new_counterparty_share = (
        len(new_in_second_half) / total_unique if total_unique > 0 else 0.0
    )
    return {
        "burstiness_recent_shift": float(burstiness_recent_shift),
        "recent_half_new_counterparty_share": float(recent_half_new_counterparty_share),
    }


def load_positive_events(source_id: str):
    path = PROCESSED_DIR / f"{source_id}_events.json"
    events = json.loads(path.read_text(encoding="utf-8"))
    return sorted(events, key=lambda a: a["timestamp"])


def main():
    df_raw = pd.read_parquet(PROCESSED_DIR / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)

    hn_df = pd.concat([
        pd.read_csv(ROOT / "metadata" / "hard_negative_registry.csv"),
        pd.read_csv(ROOT / "metadata" / "hard_negative_registry_v2_complexity.csv"),
    ], ignore_index=True).set_index("hard_negative_id")
    # "hard_negative_control" (24 dong, 5 trajectory) khong nam trong 2 file
    # tren - day la cac benign-control GOC nam ngay trong incident_registry.csv
    # (label=0), dung ten cot khac (chain_primary, khong co parent_incident_id
    # rieng vi khong phai "mined" tu incident nao - tu ban than no).
    control_df = pd.read_csv(ROOT / "metadata" / "incident_registry.csv")
    control_df = control_df[control_df["label"] == 0].set_index("incident_id")
    config = load_trajectory_config()

    events_cache: dict[str, list] = {}
    t0 = time.time()
    n_rebuilt = 0
    for source_id, kind in df[["source_id", "kind"]].drop_duplicates("source_id").itertuples(index=False):
        if source_id in events_cache:
            continue
        if kind == "positive":
            events_cache[source_id] = load_positive_events(source_id)
        elif kind == "hard_negative_control":
            row = control_df.loc[source_id]
            traj, _, _ = expand_and_build_trajectory(
                row["chain_primary"], row["seed_address"], int(row["start_block"]), source_id, 0,
                config=config, do_collect=False, max_iterations=2,
            )
            events_cache[source_id] = sorted(
                (json.loads(a.model_dump_json()) for a in traj.actions), key=lambda a: a["timestamp"],
            )
            n_rebuilt += 1
        else:
            row = hn_df.loc[source_id]
            traj, _, _ = expand_and_build_trajectory(
                row["chain"], row["seed_address"], int(row["start_block"]), row["parent_incident_id"], 0,
                config=config, do_collect=False, max_iterations=2,
            )
            events_cache[source_id] = sorted(
                (json.loads(a.model_dump_json()) for a in traj.actions), key=lambda a: a["timestamp"],
            )
            n_rebuilt += 1
    print(f"Da nap/rebuild {len(events_cache)} trajectory ({n_rebuilt} hard-negative rebuild) trong {time.time()-t0:.1f}s")

    rows = []
    n_mismatch = 0
    for source_id, prefix_len in df[["source_id", "prefix_len"]].itertuples(index=False):
        events = events_cache[source_id]
        prefix = events[: int(prefix_len)]
        if len(prefix) != int(prefix_len):
            n_mismatch += 1
            continue
        feats = compute_features_for_prefix(prefix)
        rows.append({"source_id": source_id, "prefix_len": int(prefix_len), **feats})

    print(f"So dong tinh duoc: {len(rows)}/{len(df)} (mismatch do dai: {n_mismatch})")
    out_df = pd.DataFrame(rows).drop_duplicates(["source_id", "prefix_len"])
    out_df.to_parquet(OUT_PATH, index=False)
    print(f"Da luu {OUT_PATH}")
    print(out_df.describe())


if __name__ == "__main__":
    main()
