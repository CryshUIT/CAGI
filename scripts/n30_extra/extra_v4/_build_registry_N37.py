# -*- coding: utf-8 -*-
import pandas as pd

reg = pd.read_csv('metadata/incident_registry_N30.csv')

new_rows = [
    dict(incident_id="sturdy_finance_2023", name="Sturdy Finance exploit (read-only reentrancy via Balancer B-stETH-STABLE oracle)",
         label=1, chain_primary="eth", chains_involved="eth", seed_address="0x1E8419E724d51E87f78E222D935fbbdeb631a08B",
         start_block=17460610, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="Sturdy Finance official post-mortem (Medium); Forklog; EigenPhi forensic analysis",
         source_url="https://sturdyfinance.medium.com/exploit-post-mortem-49261493307a",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA (Etherscan nhan 'Sturdy Finance Exploiter'). Xac minh truc tiep qua eth_getTransactionByHash (API thuc, 2026-11-04): tx 0xeb87ebc0a18aca7d2a9ffcabf61aa69c9e8d3c6efade9e2303f8857717fb9eb7, block 17460610, 2023-06-12 01:06:35 UTC, from=dung seed, 442.455 ETH chuyen vao dia chi nay trong chinh tx nay (khop ~442 ETH/$800K bao cao). Bao cao cong khai (Forklog/EigenPhi) noi tien chuyen Tornado Cash ~2 phut sau - CHUA tu xac nhan doc lap trong pipeline nay, se kiem tra khi trace.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="jimbos_protocol_2023", name="Jimbos Protocol exploit (flash-loan JIMBO pool price manipulation + slippage control flaw)",
         label=1, chain_primary="arbitrum", chains_involved="arbitrum", seed_address="0x102be4bccc2696c35fd5f5bfe54c1dfba416a741",
         start_block=95144408, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="Numen Cyber Labs analysis (Medium); Forklog; Cryptonomist",
         source_url="https://medium.com/numen-cyber-labs/a-detailed-analysis-of-arbitrum-based-jimbos-protocol-7-5-million-hack-36af84faee2",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA (Arbiscan nhan 'Jimbos Protocol Exploiter'). Xac minh truc tiep qua eth_getTransactionByHash (API thuc, 2026-11-04): tx 0x44a0f5650a038ab522087c02f734b80e6c748afb207995e757ed67ca037a5eda, block 95144408, 2023-05-28 00:24:53 UTC, from=dung seed. Khong thay bao cao cong khai nhac mixer/bridge o buoc exit - se kiem tra qua trace.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="rodeo_finance_2023", name="Rodeo Finance exploit (TWAP oracle manipulation via Investor.earn())",
         label=1, chain_primary="arbitrum", chains_involved="arbitrum", seed_address="0x2f3788F2396127061c46fC07BD0fcb91faAcE328",
         start_block=110045546, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="QuillAudits hack analysis; PeckShield (via Decrypt/TheBlock)",
         source_url="https://quillaudits.com/blog/hack-analysis/rodeo-finance-hack",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA (Arbiscan nhan 'Rodeo Finance Exploiter', xac nhan truc tiep 2026-11-04 qua eth_getTransactionByHash: tx 0x98f1e234faac8b7f7ceaffe4e8e0581038678d95710b646db45ec3de47e6c3af, block 110045546, 2023-07-11 07:54:08 UTC, from=dung seed - KHOP). Confidence=medium vi dia chi/tx ban dau chi tu 1 nguon bao chi (QuillAudits), nhung DA duoc nang cap qua nhan truc tiep tu explorer (khong con chi dua vao 1 nguon bao chi). PeckShield noi tien chuyen Arbitrum->Ethereum->Tornado Cash - CHUA tu xac nhan doc lap, se kiem tra qua trace.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="sentiment_protocol_2023", name="Sentiment Protocol exploit (read-only reentrancy via Balancer, price manipulation)",
         label=1, chain_primary="arbitrum", chains_involved="arbitrum", seed_address="0xdd0cdb4c3b887bc533957bc32463977e432e49c3",
         start_block=77026913, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="QuillAudits; TheBlock; Cointelegraph; Sentiment official recovery plan (hackmd)",
         source_url="https://hackmd.io/@sentimentxyz/Bk8XxMRbh",
         confidence="medium", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA (Arbiscan nhan 'Sentimentxyz Exploiter', xac nhan truc tiep 2026-11-04 qua eth_getTransactionByHash: tx 0xa9ff2b587e2741575daf893864710a5cbb44bb64ccdc487a100fa20741e0f74d, block 77026913, 2023-04-04 17:50:29 UTC, from=dung seed - KHOP, nhan ~0.517 WBTC/29.97 WETH/538399 USDC.e/360000 USDT0). Confidence=medium vi dia chi ban dau chi tu 1 nguon ro rang (QuillAudits) nhung da duoc nang cap qua nhan truc tiep tu explorer. Bao cao noi tien 'chuyen sang Ethereum mainnet, con giu o dia chi attacker' - khong ro mixer/bridge cu the, se kiem tra qua trace.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="pike_finance_2024", name="Pike Finance exploit (vu 1, 26/04/2024 - CCTP/USDC cross-chain logic bug)",
         label=1, chain_primary="arbitrum", chains_involved="arbitrum", seed_address="0xAdaF1626aEC26A7937aE7d1Fa0664e6E0904C1d0",
         start_block=204830567, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="CertiK incident analysis; Rekt News; Merkle Science; SlowMist",
         source_url="https://www.certik.com/blog/pike-finance-incident-analysis",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA. Xac minh truc tiep 2026-11-04 qua eth_getTransactionByHash: tx 0x979ad9b7f5331ea8034305a83b5cd50aea88adec395fff8298dd90eb1b87667f, block 204830567, 2024-04-25 23:48:09 UTC, from=dung seed, dot 162537 USDC qua Circle Token Messenger (DepositForBurn, co che CCTP) - KHOP mo ta exploit. DA LOAI 1 hash canh tranh (0xdac6af56...) vi tx do tu dia chi KHAC (0x19066f74...) thuoc vu Pike Finance NGAY 30/04 KHAC (vu thu 2, khong lay o day). CertiK xac nhan tien chuyen Tornado Cash - se kiem tra qua trace.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="fortress_protocol_2022", name="Fortress Protocol exploit (malicious governance proposal + oracle manipulation, JetFuel Finance lending arm)",
         label=1, chain_primary="bsc", chains_involved="bsc", seed_address="0xA6AF2872176320015f8ddB2ba013B38Cb35d22Ad",
         start_block=17634663, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="SlowMist hack analysis; Rekt News; Knownsec Blockchain Lab; CertiK",
         source_url="https://www.rekt.news/fortress-rekt/",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA. Xac minh truc tiep 2026-11-04 qua eth_getTransactionByHash (BSC, NodeReal MegaNode JSON-RPC): tx 0x13d19809b19ac512da6d110764caee75e2157ea62cb70937c8d9471afcb061bf, block 17634663, 2022-05-08 20:34:42 UTC - KHOP CHINH XAC ngay 2022-05-08 da duoc xac dinh truoc, from=dung seed. SlowMist/Rekt/Knownsec deu xac nhan tien chuyen Tornado Cash (1048 ETH + 400k DAI) - se kiem tra qua trace. Sua loi tu truoc: ban dau toi ghi nham hash nay 'dai hon 64-hex 1 ky tu' - kiem tra lai bang len() cho thay DUNG 64 ky tu, loi dem tay.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),

    dict(incident_id="uwu_lend_2024", name="UwU Lend exploit (lan 1, 10/06/2024 - price oracle manipulation qua Curve pools)",
         label=1, chain_primary="eth", chains_involved="eth", seed_address="0x841dDf093f5188989fA1524e7B893de64B421f47",
         start_block=20061489, is_cross_chain=False, bridge_families="", dex_families="", mixer_families="",
         source_report="SlowMist analysis; QuillAudits; Cube3; multiple outlets (Catenaa, Cryptoslate)",
         source_url="https://slowmist.medium.com/analysis-of-the-uwu-lend-hack-9502b2c06dbe",
         confidence="high", endpoint_type="not_yet_traced", endpoint_confirmed=False,
         annotator_1="", annotator_2="",
         notes="Seed=attacker EOA (Etherscan nhan 'UwU Lend Exploiter'). Xac minh truc tiep 2026-11-04 qua eth_getTransactionByHash: tx 0x0014833205b29994a078941e6d088e62ae4acfa9c93f60a6e58f56006d7e650e, block 20061489, 2024-06-10 12:39:59 UTC, from=dung seed - KHOP. Day la 1 trong 3 giao dich khai thac that (UwU Lend bi khai thac qua 3 tx trong ngay 10/06) - dung lam tx KHAI THAC DAU TIEN theo dung chi dao cua nguoi dung ('tx khai thac dau tien ngay 2024-06-10'). Tx noi bo truoc do (0x939b91bb..., 07/06, nhan 0.98 ETH tu Tornado Cash) la NAP GAS truoc khai thac, KHONG dung lam start_block.",
         eval_tier="v4_heldout", n_mixer_or_exit=None, n_bridge_deposit=None, type_of_first_endpoint_action="", endpoint_basis="none"),
]

new_df = pd.DataFrame(new_rows)
new_df = new_df[reg.columns]
combined = pd.concat([reg, new_df], ignore_index=True)
combined.to_csv('metadata/incident_registry_N37.csv', index=False)
print("Tong so dong:", len(combined))
print("7 dong moi:", combined[combined.eval_tier == 'v4_heldout'].incident_id.tolist())
