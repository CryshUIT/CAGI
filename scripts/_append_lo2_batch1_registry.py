"""Them 4 incident lo 2 batch 1 (Lendhub, THORChain-2, Popsicle, HECO) vao
metadata/incident_registry_N30.csv. Chi chay 1 lan, khong giu lai lau dai."""
import pandas as pd

r = pd.read_csv("metadata/incident_registry_N30.csv")

new_rows = [
{
 "incident_id": "lendhub_2023",
 "name": "LendHub exploit (12/01/2023, lBSV token duplicate market manipulation)",
 "label": 1, "chain_primary": "eth", "chains_involved": "eth",
 "seed_address": "0x9d0163e76bbcf776001e639d65f573949a53ab03",
 "start_block": 16386495, "is_cross_chain": False,
 "bridge_families": "", "dex_families": "", "mixer_families": "Tornado Cash Router",
 "source_report": "The Block; Bitcoinist; TodayInTheMarkets",
 "source_url": "https://www.theblock.co/post/202047/self-proclaimed-safest-defi-lender-loses-6-million-in-hack",
 "confidence": "high", "endpoint_type": "known_mixer_confirmed", "endpoint_confirmed": True,
 "annotator_1": "AI-assisted (Claude Code) pipeline, dataset expansion N30 lo 2, 2026-10-15",
 "annotator_2": "",
 "notes": ("Seed xac nhan doc lap boi The Block/Bitcoinist/TodayInTheMarkets (chinh xac dia chi nay). "
           "On-chain khop ngay hack 2023-01-12. Build thuc te: n_actions=274, mixer_or_exit=11 (Tornado "
           "Cash Router, trong window 72h) - khop bao cao '100 ETH gas dau vao, 1100+ ETH gui ra Tornado "
           "Cash'. Endpoint CONFIRMED manh."),
 "eval_tier": "primary",
},
{
 "incident_id": "thorchain2_2021",
 "name": "THORChain exploit #2 (15-16/07/2021, Bifrost ETH Router fake transferOut)",
 "label": 1, "chain_primary": "eth", "chains_involved": "eth",
 "seed_address": "0x3a196410a0f5facd08fd7880a4b8551cd085c031",
 "start_block": 12832728, "is_cross_chain": False,
 "bridge_families": "", "dex_families": "Uniswap (swap that, chua xac dinh dia chi cu the trong window)",
 "mixer_families": "",
 "source_report": 'SlowMist; Halborn; TRM Labs; rekt.news; Etherscan label "THORChain Exploiter 2"',
 "source_url": "https://rekt.news/thorchain-rekt2",
 "confidence": "high", "endpoint_type": "reported_mixer_outside_tracking_window", "endpoint_confirmed": False,
 "annotator_1": "AI-assisted (Claude Code) pipeline, dataset expansion N30 lo 2, 2026-10-15",
 "annotator_2": "",
 "notes": ('Seed tu Etherscan gan nhan doc lap "THORChain Exploiter 2"; hop ke (0x4a338620...) la '
           '"THORChain Exploit Contract" (Etherscan). On-chain khop ngay 2021-07-15. Dong tien tiep tuc '
           "toi dia chi holding (0xace2d948...) roi Tornado Cash (xac nhan qua phan tich Medium/"
           "breadcrumbs) NHUNG giao dich Tornado dau tien (19/07/2021) nam NGOAI window 72h (chi tre vai "
           "tram block). Build thuc te: n_actions=97, mixer_or_exit=0, nhung co 7 action swap THAT trong "
           "window - dat cong (3) qua DEX, KHONG qua mixer. endpoint_confirmed=False (giong mau Uranium "
           "Finance - bao cao neu mixer nhung khong bat duoc trong window)."),
 "eval_tier": "primary",
},
{
 "incident_id": "popsicle_finance_2021",
 "name": "Popsicle Finance exploit (03-04/08/2021, Sorbetto Fragola LP fee accounting flaw)",
 "label": 1, "chain_primary": "eth", "chains_involved": "eth",
 "seed_address": "0xf9e3d08196f76f5078882d98941b71c0884bea52",
 "start_block": 12954903, "is_cross_chain": False,
 "bridge_families": "",
 "dex_families": "",
 "mixer_families": "TornadoProxy (bao cao xac nhan, pipeline KHONG tu nhan dien - xem notes)",
 "source_report": "SlowMist; BlockSec",
 "source_url": "https://slowmist.medium.com/slowmist-an-analysis-of-the-attack-on-popsicle-credentials-750d195944c8",
 "confidence": "high", "endpoint_type": "reported_mixer_not_recognized_by_pipeline_label", "endpoint_confirmed": False,
 "annotator_1": "AI-assisted (Claude Code) pipeline, dataset expansion N30 lo 2, 2026-10-15",
 "annotator_2": "",
 "notes": ("Seed xac nhan doc lap boi SlowMist/BlockSec (dung dia chi H2 attacker). On-chain khop ngay "
           "2021-08-03/04. Seed gui lap lai nhieu lan 100 ETH truc tiep toi TornadoProxy "
           "(0x722122df...), DA them vao configs/data_N30.yaml allowlist (kiem tra dong nhat v1.0 PASS, "
           "612/612 negative khop) nhung KHONG duoc gan nhan 'mixer_or_exit' vi load_protocol_map() CHI "
           "doc metadata/protocol_map.yaml GOC (khong doc protocol_map_N30.yaml) - xem "
           "known_builder_limitations.md muc 'protocol_map_N20/N30 chi la tai lieu tham khao'. "
           "endpoint_confirmed=False theo co lay tu ket qua build THAT (khong override tay), MAC DU bao "
           "cao doc lap xac nhan ro rang rua tien qua Tornado Cash (4,100 ETH). Xep vao danh sach bang "
           "chung YEU cung Cork/Uranium/HECO."),
 "eval_tier": "primary",
},
{
 "incident_id": "heco_htx_2023",
 "name": "HECO Chain bridge + HTX hot wallet exploit (22/11/2023, suspected operator key compromise)",
 "label": 1, "chain_primary": "eth", "chains_involved": "eth",
 "seed_address": "0xfc146d1caf6ba1d1ce6dcb5b35dcbf895f50b0c4",
 "start_block": 18626577, "is_cross_chain": False,
 "bridge_families": "Khong xac dinh (6 bridge_deposit trong window, chua xac dinh ten cu the)",
 "dex_families": "MetaSwap; SushiSwap RouteProcessor3_2",
 "mixer_families": "Tornado Cash (bao cao xac nhan, NGOAI window 72h - xem notes)",
 "source_report": "ImmuneBytes; Hacken; Cointelegraph; forklog; Elliptic (Lazarus Group attribution)",
 "source_url": "https://hacken.io/insights/heco-bridge-hack-explained/",
 "confidence": "high", "endpoint_type": "reported_mixer_outside_tracking_window", "endpoint_confirmed": False,
 "annotator_1": "AI-assisted (Claude Code) pipeline, dataset expansion N30 lo 2, 2026-10-15",
 "annotator_2": "",
 "notes": ("Seed xac nhan doc lap boi nhieu nguon (ImmuneBytes/Hacken/Cointelegraph/forklog); so token "
           "danh cap khop CHINH XAC on-chain (489 HBTC, 173.200 UNI, 619.000 USDC, 42.399 LINK, 346.994 "
           "TUSD). Phan lon tien ($63M) nam im tai 1 dia chi holding, CHI rua qua Tornado Cash tu thang "
           "3/2024 (~4 thang sau hack) - NGOAI window 72h. Mot nhanh vi phu (phan tan 619,000 USDC) co "
           "goi toi MetaSwap + SushiSwap RouteProcessor3_2 (DA them allowlist, kiem tra dong nhat v1.0 "
           "PASS) CUNG NGAY voi hack - dat cong (3) qua nhanh phu nay. endpoint_confirmed=False: nhanh "
           "DEX la phan NHO gia tri tong thiet hai, rua tien CHINH ngoai window. 'Trace 72h chu yeu la "
           "nhanh phu, rua tien chinh ngoai cua so'. Xep vao danh sach bang chung YEU cung Cork/Uranium/"
           "Popsicle."),
 "eval_tier": "primary",
},
]

for row in new_rows:
    for col in r.columns:
        if col not in row:
            row[col] = ""
new_df = pd.DataFrame(new_rows)[r.columns.tolist()]
out = pd.concat([r, new_df], ignore_index=True)
out.to_csv("metadata/incident_registry_N30.csv", index=False)
print("Da them", len(new_rows), "incident. Tong hien tai:", len(out))
