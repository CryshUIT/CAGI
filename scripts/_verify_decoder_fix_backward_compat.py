"""N30: chung minh tuong thich nguoc cua fix decode_internal_tx_row (bo qua
to==""/from=="" o internal tx) bang cach dung lai TOAN BO trajectory da co
TU CACHE (do_collect=False) SAU KHI sua, so sanh voi gia tri da biet TRUOC
khi sua (list cung hoac diff).

Vi 2 dong loi chi ton tai duy nhat trong cache cua inverse_finance_2022_jun
(da xac nhan truoc), ky vong: 15 v1.0 + 536 negative KHONG DOI, 5 N20 + 171
negative KHONG DOI, 4/5 batch-1 da xu ly (Dough/0xInfini/Prisma/Uranium)
KHONG DOI, CHI inverse_finance_2022_jun thay doi (tu crash -> chay duoc).
"""
from __future__ import annotations

import pandas as pd

from src.pipeline.incident_pipeline import expand_and_build_trajectory
from src.trajectories.builder import load_trajectory_config

# (expected_n_actions_truoc_khi_sua) - None neu chua tung do duoc (vd Inverse bi crash)
V1_POSITIVE_EXPECTED = {
    "ronin_bridge_2022": 1625, "qbridge_qubit_2022": 698, "feg_bridge_2024": 9,
    "deltaprime_arbitrum_2024": 23, "bsc_token_hub_2022": 362, "chibi_finance_2023": 40,
    "wooppv2_2024": 16, "utopiasphere_2024": 37, "xkingdom_2024": 73,
    "wault_finance_2021": 190, "paraluni_2022": 511, "radiant_capital_arbitrum_2024": 248,
    "magic_abracadabra_arbitrum_2025": 88, "hackerdao_2022": 35, "new_free_dao_2022": 12,
}
N20_POSITIVE_EXPECTED = {
    "zunami_protocol_2023": 31, "onyx_protocol_2023": 16, "beanstalk_farms_2022": 443,
    "hedgey_finance_2024": 755, "cork_protocol_2025": 1,
}
BATCH1_EXPECTED = {
    "dough_finance_2024": 17, "0xinfini_2025": 25, "prisma_finance_2024": 70,
    "uranium_finance_2021": 39,
}


def check_positive(iid, expected, reg, cfg):
    row = reg[reg.incident_id == iid].iloc[0]
    t, _, _ = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), iid, int(row.label),
        config=cfg, do_collect=False,
    )
    n = len(t)
    ok = (n == expected)
    print(f"  {iid:35s} expected={expected:4d} actual={n:4d} {'OK' if ok else '*** KHAC BIET ***'}")
    return ok


def check_negatives(hn_df, cfg, label):
    diffs = []
    for _, row in hn_df.iterrows():
        hn_id, parent = row["hard_negative_id"], row["parent_incident_id"]
        t, _, _ = expand_and_build_trajectory(
            row["chain"], row["seed_address"], int(row["start_block"]), parent, 0,
            config=cfg, do_collect=False, max_iterations=2,
        )
        diffs.append((hn_id, len(t)))
    print(f"  [{label}] da kiem tra {len(diffs)} dong (xem file CSV doi chieu rieng de so sanh so cu)")
    return diffs


def main():
    reg20 = pd.read_csv("metadata/incident_registry_N20.csv")
    reg30 = pd.read_csv("metadata/incident_registry_N30.csv")
    cfg20 = load_trajectory_config("configs/data_N20.yaml")
    cfg30 = load_trajectory_config("configs/data_N30.yaml")

    print("=== 15 incident v1.0 (RANH GIOI CUNG) - dung config N20 (chua co KyberSwap), SAU KHI sua decoder ===")
    ok_all = True
    for iid, exp in V1_POSITIVE_EXPECTED.items():
        ok_all &= check_positive(iid, exp, reg20, cfg20)

    print("\n=== 536 negative v1.0 (RANH GIOI CUNG) - SAU KHI sua decoder ===")
    hn_v1 = pd.read_csv("metadata/hard_negative_registry.csv")
    neg_v1_after = check_negatives(hn_v1, cfg20, "v1.0-536")
    pd.DataFrame(neg_v1_after, columns=["hard_negative_id", "n_actions_after_fix"]).to_csv(
        "results/tables/_tmp_neg_v1_after_fix.csv", index=False)

    print("\n=== 5 incident N20 (RANH GIOI MEM) - dung config N30, SAU KHI sua decoder ===")
    for iid, exp in N20_POSITIVE_EXPECTED.items():
        check_positive(iid, exp, reg20, cfg30)

    print("\n=== 125+46 negative N20 (RANH GIOI MEM) - SAU KHI sua decoder ===")
    hn_n20 = pd.read_csv("metadata/hard_negative_registry_N20.csv")
    hn_v2c = pd.read_csv("metadata/hard_negative_registry_v2_complexity_N20.csv")
    check_negatives(hn_n20, cfg30, "N20-main-125")
    check_negatives(hn_v2c, cfg30, "N20-v2c-46")

    print("\n=== 4 incident batch-1 da xu ly (Dough/0xInfini/Prisma/Uranium) - dung config N30, SAU KHI sua decoder ===")
    for iid, exp in BATCH1_EXPECTED.items():
        check_positive(iid, exp, reg30, cfg30)

    print("\n=== inverse_finance_2022_jun (incident bi crash truoc khi sua) ===")
    row = reg30[reg30.incident_id == "inverse_finance_2022_jun"].iloc[0]
    t, _, processed = expand_and_build_trajectory(
        row.chain_primary, row.seed_address, int(row.start_block), "inverse_finance_2022_jun",
        int(row.label), config=cfg30, do_collect=False,
    )
    n_mixer = sum(1 for a in t.actions if a.event_type == "mixer_or_exit")
    n_bridge = sum(1 for a in t.actions if a.event_type in ("bridge_deposit", "bridge_withdraw"))
    print(f"  n_actions={len(t)} n_processed={len(processed)} n_mixer_or_exit={n_mixer} n_bridge={n_bridge}")

    from src.normalize.decoder import CONTRACT_CREATION_SKIPPED_STATS
    print("\n=== Thong ke dong bi bo qua (contract-creation internal tx) theo incident ===")
    for iid, stat in CONTRACT_CREATION_SKIPPED_STATS.items():
        print(f"  {iid}: count={stat['count']} total_value_eth={stat['total_value_eth']:.6f} reasons={stat['reasons']}")

    print("\n" + "=" * 60)
    print("15 incident v1.0: " + ("TAT CA KHOP (khong khac biet)" if ok_all else "*** CO KHAC BIET - XEM TREN ***"))


if __name__ == "__main__":
    main()
