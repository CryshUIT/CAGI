# -*- coding: utf-8 -*-
import pandas as pd

reg = pd.read_csv('metadata/incident_registry_final_heldout.csv')

new_rows = [
    dict(incident_id="pancakebunny_2021", name="PancakeBunny exploit (BNB flash-swap price manipulation, BUNNY mint)",
         label=1, chain_primary="bsc", chains_involved="bsc", seed_address="0xa0acc61547f6bd066f7c9663c17a312b6ad7e187",
         start_block=7556391, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="Knownsec Blockchain Lab (Medium); DN Institute attack database",
         source_url="https://medium.com/@Knownsec_Blockchain_Lab/knownsec-blockchain-lab-binance-smartchain-pancakebunny-bunny-attack-event-analysis-2b2d49795b38",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Xac minh truc tiep 2026-11-05 qua eth_getTransactionByHash (BSCTrace): tx 0x897c2de73dd55d7701e1b69ffb3a17b0f4801ced88b0c75fe1551c5fcce6a979, block 7556391, 2021-05-19T22:34:28Z, from=dung seed, to=0xcc598232a75fb1b361510bce4ca39d7bc39cf498 (attack contract) - KHOP 2 nguon (Knownsec + DN Institute).",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="spartan_protocol_2021", name="Spartan Protocol exploit (LP-share calculation flaw, removeLiquidity())",
         label=1, chain_primary="bsc", chains_involved="bsc", seed_address="0x3b6e77722e2bbe97c1cfa337b42c0939aeb83671",
         start_block=7048833, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="ImmuneBytes hack analysis (1 nguon dia chi/tx); Rekt News/CoinDesk/BeInCrypto xac nhan quy mo",
         source_url="https://immunebytes.com/blog/?p=10661",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Xac minh truc tiep 2026-11-05 qua eth_getTransactionByHash (BSCTrace): tx 0xb64ae25b0d836c25d115a9368319902c972a0215bd108ae17b1b9617dfb93af8, block 7048833, 2021-05-01T16:38:39Z, from=dung seed, to=0x288315639c1145f523af6d7a5e4ccf8238cd6a51 - KHOP ngay bao cao (1/5 hoac 2/5 tuy nguon, lech UTC). confidence=medium vi dia chi/tx chi tu 1 nguon ro rang.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="allbridge_2023", name="Allbridge exploit (flash-loan price manipulation, BUSD/USDT pool BSC)",
         label=1, chain_primary="bsc", chains_involved="bsc", seed_address="0xc578d755cd56255d3ff6e92e1b6371ba945e3984",
         start_block=26982068, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="ImmuneBytes hack analysis (1 nguon dia chi/tx); QuillAudits/CertiK/Cointelegraph xac nhan co che/so tien",
         source_url="https://immunebytes.com/blog/?p=11140",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Xac minh truc tiep 2026-11-05 qua eth_getTransactionByHash (BSCTrace): tx 0x7ff1364c3b3b296b411965339ed956da5d17058f3164425ce800d64f1aef8210, block 26982068, 2023-04-01T21:57:02Z, from=dung seed, to=0x7d83fe202c51982a72e0a1146ec37b4643c725d7 - KHOP ngay bao cao (1/4 hoac 2/4 tuy nguon). Cointelegraph noi ~507.3 BNB chuyen Tornado Cash 5/4/2023 - CHUA tu xac nhan, se kiem tra qua trace.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="rikkei_finance_2022", name="Rikkei Finance exploit (thieu access control ham setOracleData, vay duoi-tin-chap)",
         label=1, chain_primary="bsc", chains_involved="bsc", seed_address="0x803e0930357ba577dc414b552402f71656c093ab",
         start_block=16955246, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="SlowMist forensic analysis (1 nguon dia chi); CertiK xac nhan co che/so tien",
         source_url="https://slowmist.medium.com/slowmist-forensic-analysis-of-rikkei-finance-hack-ba0a77d582bc",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="KHONG co tx hash duoc nguon cong khai neu ro. Xac minh 2026-11-05 qua fetch_asset_transfers(seed) quanh ngay 2022-04-15: 52 external transfer, xac nhan qua eth_getBlockByNumber CA 52 deu dung ngay 2022-04-15. Pattern: 1 cum tx gia-tri-0 luc 02:17 UTC (block 16955246, to=0x0), roi 1 gio sau la chuoi ~22 tx 100-don-vi lien tuc toi CUNG 1 dia chi (0x0d5550d52428e7e3175bfc9550207e4ad3859b17 - giong hanh vi chia nho sau khai thac). start_block=16955246 (tx dau ngay khai thac) la SUY LUAN TU PATTERN ON-CHAIN, KHONG phai trich dan truc tiep nguon cong khai - ghi chu ro muc do suy luan, confidence=medium.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),
]

new_df = pd.DataFrame(new_rows)
new_df = new_df[reg.columns]
combined = pd.concat([reg, new_df], ignore_index=True)
combined.to_csv('metadata/incident_registry_final_heldout.csv', index=False)
print("Tong so dong:", len(combined))
print("Cac dong final_heldout_new:", combined[combined.eval_tier == 'final_heldout_new'].incident_id.tolist())
