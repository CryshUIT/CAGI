"""NSS 2026 - Viec 2+3 gop: phan loai CHINH XAC ly do tung giao dich bi loai
o dau trajectory, cho 13/15 incident bi anh huong (xem
early_gap_audit_15incidents_2026-09-22.csv):
  (1) reachability - src chua duoc "den" tu seed (dung thiet ke, KHONG sua)
  (2) tainted_share - value_share < nguong, MAU SO la TONG outflow (src,token)
      CONG DON TOAN BO cua so thoi gian (nghi ngo la van de that)
  (3) khac (max_depth / time_horizon)

DONG THOI tinh COUNTERFACTUAL: neu mau so la CONG DON DEN THOI DIEM HIEN TAI
(chi tinh cac event CO timestamp <= event dang xet, dung nguyen tac khong
nhin tuong lai - nhat quan voi cach feature tai prefix k chi dung event <=k),
bao nhieu event bi loai o (2) se DUOC CHAP NHAN neu doi mau so.

Sao chep TRUC TIEP logic that trong src/trajectories/builder.py::build_trajectory
(khong doan/viet lai thuat toan) - ap dung tren object CanonicalEvent that,
KHONG parse text debug (tranh nham lan khi nhieu event chung 1 tx_hash).
KHONG goi API moi (expand_and_build_trajectory do_collect=False, chi doc cache).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.normalize.decoder import (  # noqa: E402
    build_verified_bridge_address_index, build_verified_lending_address_index,
    build_verified_mixer_address_index, load_protocol_map,
)
from src.pipeline.incident_pipeline import (  # noqa: E402
    compute_end_block, expand_and_build_trajectory, load_events_for_addresses,
)
from src.trajectories.builder import _dedup, _sort_key, load_trajectory_config  # noqa: E402

AFFECTED_13 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024",
]


def _raw_value(ev) -> float:
    return math.expm1(abs(ev.amount_norm))


def classify_incident(incident_id: str, reg_row: dict, config, bridge_index, mixer_index, lending_index) -> dict:
    chain, seed, start_block = reg_row["chain_primary"], reg_row["seed_address"].lower(), int(reg_row["start_block"])

    traj, _, processed = expand_and_build_trajectory(
        chain, seed, start_block, incident_id, label=1, config=config, do_collect=False,
    )
    end_block = compute_end_block(chain, start_block, config)
    if not traj.actions:
        return {"incident_id": incident_id, "error": "trajectory rong"}
    min_decoded_block = min(a.block_number for a in traj.actions)

    all_events = load_events_for_addresses(chain, processed, incident_id, bridge_index, mixer_index=mixer_index, lending_index=lending_index)
    all_events = [e for e in all_events if start_block <= e.block_number <= end_block]
    all_events = _dedup(all_events)
    all_events.sort(key=_sort_key)

    # --- Tai lap CHINH XAC logic that (whole-window denominator) ---
    outflow_whole_window: dict = {}
    for ev in all_events:
        key = (ev.src, ev.token)
        outflow_whole_window[key] = outflow_whole_window.get(key, 0.0) + _raw_value(ev)

    node_depth = {seed: 0}
    allowlist = config.allowlist
    start_time = None

    # --- Song song tinh mau so CUMULATIVE-DEN-THOI-DIEM-HIEN-TAI (counterfactual) ---
    outflow_cumulative: dict = {}

    rows = []
    n_reach, n_tainted, n_other, n_accept_in_gap = 0, 0, 0, 0
    n_would_flip = 0
    for ev in all_events:
        in_gap = start_block <= ev.block_number < min_decoded_block
        key = (ev.src, ev.token)
        # cap nhat mau so cumulative TRUOC khi danh gia event nay (event nay tu no cung tinh vao mau so cua chinh no - >=, khong phai > - giong quy uoc "feature tai prefix k dung event <=k")
        outflow_cumulative[key] = outflow_cumulative.get(key, 0.0) + _raw_value(ev)

        if ev.src not in node_depth:
            reason = "reachability"
            if in_gap: n_reach += 1
        else:
            depth = node_depth[ev.src]
            if depth >= config.max_depth:
                reason = "max_depth"
                if in_gap: n_other += 1
            else:
                if start_time is None:
                    start_time = ev.timestamp
                elapsed_hours = (ev.timestamp - start_time).total_seconds() / 3600.0
                if elapsed_hours > config.time_horizon_hours:
                    reason = "time_horizon"
                    if in_gap: n_other += 1
                else:
                    total_out_whole = outflow_whole_window.get(key, 0.0)
                    value_share_whole = (_raw_value(ev) / total_out_whole) if total_out_whole > 0 else 0.0
                    counterparty_allowed = ev.dst in allowlist or ev.src in allowlist
                    accepted_real = (value_share_whole >= config.min_tainted_share) or counterparty_allowed

                    total_out_cum = outflow_cumulative.get(key, 0.0)
                    value_share_cum = (_raw_value(ev) / total_out_cum) if total_out_cum > 0 else 0.0
                    accepted_counterfactual = (value_share_cum >= config.min_tainted_share) or counterparty_allowed

                    if accepted_real:
                        reason = "accepted"
                        if in_gap: n_accept_in_gap += 1
                        # cap nhat frontier CHI khi that su accept (giong code that)
                        if ev.dst not in allowlist and (ev.dst not in node_depth or node_depth[ev.dst] > depth + 1):
                            node_depth[ev.dst] = depth + 1
                    else:
                        reason = "tainted_share"
                        if in_gap:
                            n_tainted += 1
                            if accepted_counterfactual and not counterparty_allowed:
                                n_would_flip += 1
                    if in_gap:
                        rows.append({
                            "incident_id": incident_id, "tx_hash": ev.tx_hash, "block_number": ev.block_number,
                            "src": ev.src, "dst": ev.dst, "token": ev.token, "raw_value": _raw_value(ev),
                            "value_share_whole_window": value_share_whole, "value_share_cumulative_to_date": value_share_cum,
                            "min_tainted_share": config.min_tainted_share, "reason": reason,
                            "would_flip_under_cumulative": bool(accepted_counterfactual and not accepted_real and not counterparty_allowed),
                        })
                    continue
        if in_gap and reason in ("reachability", "max_depth", "time_horizon"):
            rows.append({
                "incident_id": incident_id, "tx_hash": ev.tx_hash, "block_number": ev.block_number,
                "src": ev.src, "dst": ev.dst, "token": ev.token, "raw_value": _raw_value(ev),
                "value_share_whole_window": None, "value_share_cumulative_to_date": None,
                "min_tainted_share": config.min_tainted_share, "reason": reason, "would_flip_under_cumulative": False,
            })

    return {
        "incident_id": incident_id, "start_block": start_block, "min_decoded_block": min_decoded_block,
        "n_gap_events": n_reach + n_tainted + n_other + n_accept_in_gap,
        "reachability_reject": n_reach, "tainted_share_reject": n_tainted, "other_reject": n_other,
        "accepted_but_still_in_gap_window": n_accept_in_gap,
        "tainted_share_would_flip_under_cumulative_denominator": n_would_flip,
        "detail_rows": rows,
    }


def main() -> None:
    config = load_trajectory_config()
    protocol_map = load_protocol_map()
    bridge_index = build_verified_bridge_address_index(protocol_map)
    mixer_index = build_verified_mixer_address_index(protocol_map)
    lending_index = build_verified_lending_address_index(protocol_map)
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry.csv").set_index("incident_id")

    summary_rows, detail_rows = [], []
    for inc in AFFECTED_13:
        print(f"=== {inc} ===", flush=True)
        try:
            r = classify_incident(inc, reg.loc[inc].to_dict(), config, bridge_index, mixer_index, lending_index)
        except Exception as e:
            print(f"  LOI: {type(e).__name__}: {e}")
            summary_rows.append({"incident_id": inc, "error": f"{type(e).__name__}: {e}"})
            continue
        if "error" in r:
            print(f"  {r['error']}")
            summary_rows.append(r)
            continue
        detail_rows.extend(r.pop("detail_rows"))
        summary_rows.append(r)
        print(f"  gap={r['n_gap_events']} reachability={r['reachability_reject']} "
              f"tainted_share={r['tainted_share_reject']} other={r['other_reject']} "
              f"would_flip_neu_doi_mau_so={r['tainted_share_would_flip_under_cumulative_denominator']}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(ROOT / "results" / "tables" / "early_gap_reason_breakdown_2026-09-22.csv", index=False)
    pd.DataFrame(detail_rows).to_csv(ROOT / "results" / "tables" / "early_gap_reason_detail_2026-09-22.csv", index=False)

    print("\n=== TOM TAT TOAN BO 13 INCIDENT ===")
    ok = summary_df[summary_df.get("error").isna()] if "error" in summary_df.columns else summary_df
    cols = ["incident_id", "n_gap_events", "reachability_reject", "tainted_share_reject", "other_reject",
            "tainted_share_would_flip_under_cumulative_denominator"]
    print(ok[cols].to_string(index=False))
    print("\nTONG reachability_reject:", ok["reachability_reject"].sum())
    print("TONG tainted_share_reject:", ok["tainted_share_reject"].sum())
    print("TONG other_reject:", ok["other_reject"].sum())
    print("TONG se DUOC CHAP NHAN neu doi mau so thanh cumulative-den-thoi-diem-hien-tai:",
          ok["tainted_share_would_flip_under_cumulative_denominator"].sum())


if __name__ == "__main__":
    main()
