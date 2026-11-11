# -*- coding: utf-8 -*-
import pandas as pd

reg = pd.read_csv('metadata/incident_registry_final_heldout.csv')

new_rows = [
    dict(incident_id="harvest_finance_2020", name="Harvest Finance exploit (Curve Y pool price manipulation, flash loan)",
         label=1, chain_primary="eth", chains_involved="eth", seed_address="0xf224ab004461540778a914ea397c589b677e27bb",
         start_block=11129474, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="Harvest Finance official post-mortem (Medium); SlowMist forensic analysis",
         source_url="https://medium.com/harvest-finance/harvest-flashloan-economic-attack-post-mortem-3cf900d65217",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Xac minh truc tiep 2026-11-05 qua eth_getTransactionByHash: tx 0x35f8d2f572fceaac9288e5d462117850ef2694786992a8c3f6d02612277b0877, block 11129474, 2020-10-26T02:53:58Z, from=dung seed, to=attack contract 0xc6028a9fa486f52efd2b95b949ac630d287ce0af - KHOP bao cao (Harvest post-mortem). Post-mortem noi tien cuoi chuyen toi 0x3811765a53c3188c24d412daec3f60faad5f119b - CHUA tu xac nhan day co phai known exit/mixer, se kiem tra qua trace.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="rari_capital_fuse_2022", name="Rari Capital Fuse (TribeDAO) exploit (reentrancy cEther, nhieu Fuse pool)",
         label=1, chain_primary="eth", chains_involved="eth,arbitrum", seed_address="0x6162759edad730152f0df8115c698a42e666157f",
         start_block=14684402, is_cross_chain=True, bridge_families="", dex_families="", mixer_families="",
         source_report="ImmuneBytes hack analysis (1 nguon dia chi/tx); TheBlock/CertiK/CoinDesk xac nhan quy mo/co che",
         source_url="https://immunebytes.com/blog/?p=9527",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Xac minh truc tiep 2026-11-05 qua eth_getTransactionByHash: tx 0xd9ee4fc5ee0b8815e6aae20e8bc5697ee49b8a1c76619a008bf534a4084197dc, block 14684402, 2022-04-30T07:58:50Z, from=dung seed, to=0x32075bad9050d4767018084f0cb87b3182d36c45 - KHOP ngay bao cao. confidence=medium vi dia chi/tx chi tu 1 nguon ro rang (ImmuneBytes), nhung DA duoc nang len qua xac nhan truc tiep tren-chain (khong con chi dua vao 1 nguon bao chi). Co phan Arbitrum trong vu nay (theo Coinfirm) - chains_involved ghi ca 2, nhung seed/start_block nay CHI thuoc nhanh Ethereum.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="curve_crv_eth_attacker_2023", name="Curve Finance Vyper reentrancy exploit (CRV/ETH pool, ke tan cong THAT - khong phai whitehat)",
         label=1, chain_primary="eth", chains_involved="eth", seed_address="0xb752def3a1fded45d6c4b9f4a8f18e645b41b324",
         start_block=17807829, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="Rekt News; Anchain AI flow-of-funds analysis",
         source_url="https://rekt.news/curve-vyper-rekt",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="KHONG co tx hash duoc nguon cong khai neu ro. Xac minh 2026-11-05 qua fetch_normal_txs(seed) quanh ngay 2023-07-30: tim thay tong 29 tx trong +-3 ngay, nhung CHI 3 tx dung NGAY 2023-07-30 (block 17807829 tao contract methodId=0x60806040, 17807830+17807831 goi 0x83e056ba00beae4d8aa83deb326a90a4e100d0c1 methodId=0xb61d27f6/0x4f491f0b) - tach biet ro voi cac tx 'thu nghiem' ngay 07-28/07-29 (cung pattern tao-roi-goi contract nhung target KHAC). start_block=17807829 (tx dau cua chuoi khai thac CHINH) la SUY LUAN TU PATTERN ON-CHAIN, KHONG phai trich dan truc tiep tu 1 nguon cong khai neu ro 'day la tx khai thac' - ghi chu ro muc do suy luan nay, confidence=medium.",
         eval_tier="final_heldout_new", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),
]

new_df = pd.DataFrame(new_rows)
new_df = new_df[reg.columns]
combined = pd.concat([reg, new_df], ignore_index=True)
combined.to_csv('metadata/incident_registry_final_heldout.csv', index=False)
print("Tong so dong:", len(combined))
print("3 dong moi:", combined[combined.eval_tier == 'final_heldout_new'].incident_id.tolist())
