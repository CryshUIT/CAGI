"""Checkpoint N30: dung lai 20 incident HIEN CO tu cache (do_collect=False)
bang allowlist N30 (them KyberSwap Meta Aggregation Router v2), so sanh voi
ban dung lai bang allowlist N20 (truoc khi them KyberSwap) de co lap tac
dong. KHONG ghi de features_v2_N20.parquet.
"""
from __future__ import annotations

import pandas as pd

from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

ALL_20_IDS = [
    "ronin_bridge_2022", "qbridge_qubit_2022", "feg_bridge_2024",
    "deltaprime_arbitrum_2024", "bsc_token_hub_2022", "chibi_finance_2023",
    "wooppv2_2024", "utopiasphere_2024", "xkingdom_2024", "wault_finance_2021",
    "paraluni_2022", "radiant_capital_arbitrum_2024",
    "magic_abracadabra_arbitrum_2025", "hackerdao_2022", "new_free_dao_2022",
    "zunami_protocol_2023", "onyx_protocol_2023", "beanstalk_farms_2022",
    "hedgey_finance_2024", "cork_protocol_2025",
]


def main() -> None:
    reg = pd.read_csv("metadata/incident_registry_N20.csv")
    cfg_n20 = load_trajectory_config("configs/data_N20.yaml")
    cfg_n30 = load_trajectory_config("configs/data_N30.yaml")

    diffs = []
    for iid in ALL_20_IDS:
        row = reg[reg.incident_id == iid].iloc[0]
        chain, seed, start_block, label = row.chain_primary, row.seed_address, int(row.start_block), int(row.label)
        t20, _, _ = expand_and_build_trajectory(chain, seed, start_block, iid, label, config=cfg_n20, do_collect=False)
        t30, _, _ = expand_and_build_trajectory(chain, seed, start_block, iid, label, config=cfg_n30, do_collect=False)
        n20, n30 = len(t20), len(t30)
        types20 = [a.event_type for a in t20.actions]
        types30 = [a.event_type for a in t30.actions]
        same = (n20 == n30) and (types20 == types30)
        print(f"{iid:35s} n20={n20:4d} n30={n30:4d} {'GIONG HET' if same else '*** KHAC BIET ***'}")
        if not same:
            diffs.append((iid, n20, n30, types20, types30))

    print("\n" + "=" * 60)
    if diffs:
        print(f"PHAT HIEN {len(diffs)} KHAC BIET:")
        for d in diffs:
            print(d)
    else:
        print("KHONG co khac biet nao - allowlist N30 KHONG anh huong 20 incident hien co.")


if __name__ == "__main__":
    main()
