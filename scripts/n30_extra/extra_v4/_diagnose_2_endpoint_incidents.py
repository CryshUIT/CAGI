# -*- coding: utf-8 -*-
"""Chan doan chi tiet rari_capital_fuse_2022 va rikkei_finance_2022 - CHI
DOC SO LIEU, KHONG train lai, KHONG doi nguong. Voi moi incident: e*
(action thu may la endpoint), tong so action truoc e*, thoi diem tung
action, diem p_hat cua M1/B3' (raw + calibrated) tai moi prefix k=1..e*.
Them: phan tich 0/50 hard-negative cua rikkei_finance_2022 (bo loc nao
loai het 150 ung vien, so sanh nguong voi 30 vu cu)."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))

import pandas as pd  # noqa: E402

from _freeze_final_B3prime_N36 import XGBFixedColumns  # noqa: E402,F401
from src.evaluation.nested_eval import _apply_calibrator  # noqa: E402
from src.features.extractor import extract_features  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

REG = pd.read_csv(ROOT / "metadata" / "incident_registry_final_heldout.csv")
PROCESSED_DIR = ROOT / "data" / "processed"
FROZEN_DIR = ROOT / "results" / "reports" / "extra_v4"
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
THETAS = {"0.5": 0.5, "0.7": 0.7, "0.9": 0.9}
TARGETS = ["rari_capital_fuse_2022", "rikkei_finance_2022"]


def load_frozen(name: str):
    with open(FROZEN_DIR / f"{name}.pkl", "rb") as f:
        model = pickle.load(f)
    with open(FROZEN_DIR / f"{name}_platt_calibrator.pkl", "rb") as f:
        cal = pickle.load(f)
    meta = json.loads((FROZEN_DIR / f"{name}_metadata.json").read_text(encoding="utf-8"))
    return model, cal, meta


def main():
    config = load_trajectory_config(str(ROOT / "configs" / "data_final_heldout.yaml"))
    m1_model, m1_cal, m1_meta = load_frozen("M1_FROZEN_final_N36")
    b3_model, b3_cal, b3_meta = load_frozen("B3prime_FROZEN_final_N36")
    theta_frozen_m1 = m1_meta["theta_frozen"]
    theta_frozen_b3 = b3_meta["theta_frozen"]
    feature_cols_m1 = sorted(m1_meta["feature_columns"])

    report_lines = []

    for iid in TARGETS:
        row = REG[REG.incident_id == iid].iloc[0]
        events = json.loads((PROCESSED_DIR / f"{iid}_events.json").read_text(encoding="utf-8"))
        terminal_idx = next((i for i, a in enumerate(events) if a["event_type"] in
                              ("bridge_deposit", "mixer_or_exit", "lending_deposit")), None)
        e_star = terminal_idx + 1 if terminal_idx is not None else None  # 1-indexed action thu may
        n_before = (e_star - 1) if e_star else None

        print(f"\n\n=== {iid} ===", flush=True)
        print(f"e* (action thu may la endpoint, 1-indexed) = {e_star}", flush=True)
        print(f"Tong so action TRUOC e* = {n_before}", flush=True)
        report_lines.append(f"\n## {iid}\n")
        report_lines.append(f"- e* = {e_star} (action thu {e_star} la endpoint dau tien, loai `{events[terminal_idx]['event_type']}`, protocol=`{events[terminal_idx].get('protocol')}`)\n")
        report_lines.append(f"- Tong so action TRUOC e* = {n_before}\n")

        traj, _, _ = expand_and_build_trajectory(
            row["chain_primary"], row["seed_address"], int(row["start_block"]),
            iid, int(row["label"]), config=config, do_collect=False,
        )

        report_lines.append(f"\n| k | timestamp (action thu k) | M1 p_hat (raw) | M1 p_hat (calibrated) | B3' p_hat (raw) | B3' p_hat (calibrated) |\n")
        report_lines.append("|---|---|---|---|---|---|\n")
        print(f"{'k':>3} {'timestamp':25s} {'M1_raw':>8} {'M1_cal':>8} {'B3_raw':>8} {'B3_cal':>8}", flush=True)

        rows_for_df = []
        for k in range(1, e_star + 1):
            feats = extract_features(traj, k, include_endpoint_context=False)
            feats.pop("prefix_len", None)
            rows_for_df.append(feats)
        X = pd.DataFrame(rows_for_df).fillna(0.0)
        for c in feature_cols_m1:
            if c not in X.columns:
                X[c] = 0.0
        X = X[feature_cols_m1]

        p_m1_raw = m1_model.predict_proba(X)
        p_m1_cal = _apply_calibrator(m1_cal, p_m1_raw, "platt")
        p_b3_raw = b3_model.predict_proba(X)
        p_b3_cal = _apply_calibrator(b3_cal, p_b3_raw, "platt")

        crossed = {name: [] for name in list(THETAS.keys()) + ["theta_frozen_M1", "theta_frozen_B3"]}
        for idx, k in enumerate(range(1, e_star + 1)):
            ts = events[k - 1]["timestamp"]
            print(f"{k:>3} {ts:25s} {p_m1_raw[idx]:8.4f} {p_m1_cal[idx]:8.4f} {p_b3_raw[idx]:8.4f} {p_b3_cal[idx]:8.4f}", flush=True)
            report_lines.append(f"| {k} | {ts} | {p_m1_raw[idx]:.4f} | {p_m1_cal[idx]:.4f} | {p_b3_raw[idx]:.4f} | {p_b3_cal[idx]:.4f} |\n")
            for name, th in THETAS.items():
                if p_m1_cal[idx] >= th:
                    crossed[name].append(("M1", k))
                if p_b3_cal[idx] >= th:
                    crossed[name].append(("B3prime", k))
            if p_m1_cal[idx] >= theta_frozen_m1:
                crossed["theta_frozen_M1"].append(("M1", k))
            if p_b3_cal[idx] >= theta_frozen_b3:
                crossed["theta_frozen_B3"].append(("B3prime", k))

        print(f"\ne*={e_star}, n_before={n_before}", flush=True)
        report_lines.append(f"\n**e* = {e_star}, số action trước e* = {n_before}**\n")

        if e_star <= 2:
            msg = "e* <= 2 -> KHONG THE CANH BAO SOM (khong co prefix nao truoc endpoint de danh gia)."
            print(msg, flush=True)
            report_lines.append(f"\n{msg}\n")
        else:
            print(f"\nPrefix k VUOT nguong TRUOC e* (k < {e_star}):", flush=True)
            report_lines.append(f"\n**Prefix k vuot nguong TRUOC e* (k < {e_star}):**\n")
            for name, hits in crossed.items():
                before = [h for h in hits if h[1] < e_star]
                th_val = (THETAS.get(name) if name in THETAS else
                          (theta_frozen_m1 if name == "theta_frozen_M1" else theta_frozen_b3))
                line = f"  theta={name} (gia tri={th_val:.6f} neu la theta_frozen, {th_val} neu co dinh): "
                if before:
                    line += f"CO - {before}"
                else:
                    line += "KHONG CO prefix nao vuot truoc e*"
                print(line, flush=True)
                report_lines.append(f"- theta={name}: " + (f"CO - {before}" if before else "KHONG CO prefix nao vuot truoc e*") + "\n")

    # --- Phan tich 0/50 hard-negative cua rikkei_finance_2022 ---
    print("\n\n=== Phan tich 0/50 hard-negative rikkei_finance_2022 ===", flush=True)
    report_lines.append("\n\n## Phan tich 0/50 hard-negative cua rikkei_finance_2022\n")

    from src.collect.hard_negative_miner import (
        _mining_window, _passes_structural_filter, compute_min_candidate_events,
        fetch_contract_counterparties, load_protocol_map,
    )
    from src.normalize.decoder import build_verified_bridge_address_index, build_verified_mixer_address_index

    row = REG[REG.incident_id == "rikkei_finance_2022"].iloc[0]
    traj, _, _ = expand_and_build_trajectory(
        row["chain_primary"], row["seed_address"], int(row["start_block"]), "rikkei_finance_2022",
        int(row["label"]), config=config, do_collect=False,
    )
    pos_len = len(traj.actions)
    min_events = compute_min_candidate_events(pos_len)
    print(f"positive_len (rikkei) = {pos_len}, min_candidate_events (bo loc do dai) = {min_events}", flush=True)
    report_lines.append(f"- `positive_len` (so action cua rikkei_finance_2022) = {pos_len}\n")
    report_lines.append(f"- `min_candidate_events` (nguong do phuc tap toi thieu, tinh theo `compute_min_candidate_events(positive_len)`) = {min_events}\n")

    contract = "0x0d5550d52428e7e3175bfc9550207e4ad3859b17"
    start_block, end_block = _mining_window("bsc", int(row["start_block"]), "rikkei_finance_2022")
    candidates = fetch_contract_counterparties("bsc", contract, "rikkei_finance_2022", start_block, end_block, do_collect=False)
    protocol_map = load_protocol_map()
    bridge_index = build_verified_bridge_address_index(protocol_map)
    mixer_index = build_verified_mixer_address_index(protocol_map)

    reject_reasons = {}
    n_checked = 0
    for cand in candidates:
        if n_checked >= 150:
            break
        n_checked += 1
        passed, reason, _ = _passes_structural_filter(
            "bsc", cand, contract, "rikkei_finance_2022", True, start_block, end_block,
            bridge_index, mixer_index, min_candidate_events=min_events,
        )
        key = reason if not passed else "PASSED"
        reject_reasons[key] = reject_reasons.get(key, 0) + 1

    print(f"Tong candidate kiem tra lai: {n_checked}", flush=True)
    report_lines.append(f"- Tong candidate kiem tra lai de xac nhan: {n_checked}\n")
    print("Phan bo ly do loai:", flush=True)
    report_lines.append("\n| Ly do | So candidate |\n|---|---|\n")
    for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}", flush=True)
        report_lines.append(f"| {reason} | {count} |\n")

    # So sanh nguong voi 30 vu cu
    df30 = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N30.parquet")
    df30_full = df30[df30["prefix_label"] == "ratio_100"]
    pos30 = df30_full[df30_full["kind"] == "positive"][["source_id", "trajectory_len"]].drop_duplicates()
    print("\nmin_candidate_events cho 30 vu cu (de so sanh cong thuc, KHONG doi code):", flush=True)
    report_lines.append("\n### So sanh min_candidate_events voi 30 vu cu (CUNG cong thuc compute_min_candidate_events, KHONG doi code)\n")
    report_lines.append("\n| incident_id (30 vu cu) | trajectory_len | min_candidate_events |\n|---|---|---|\n")
    for _, r in pos30.sort_values("trajectory_len").iterrows():
        mce = compute_min_candidate_events(int(r["trajectory_len"]))
        report_lines.append(f"| {r['source_id']} | {int(r['trajectory_len'])} | {mce} |\n")
        print(f"  {r['source_id']:32s} len={int(r['trajectory_len']):5d} min_candidate_events={mce}")

    OUT_MD = ROOT / "results" / "reports" / "extra_v4" / "diagnostic_2_endpoint_incidents_2026-11-05.md"
    OUT_MD.write_text("".join(report_lines), encoding="utf-8")
    print(f"\nDa luu {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
