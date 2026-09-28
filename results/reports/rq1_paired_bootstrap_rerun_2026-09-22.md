# RQ1 paired bootstrap (M1 vs B3) - chay lai 2026-09-22

- Nguon: `results/tables/main_table.csv` (M1=0.6624, B3=0.6875, 15 incident).
- Phuong phap: giong run_full_evaluation_v1.py - bootstrap muc incident (2000 lan, seed 42) tren hieu so paired + Wilcoxon signed-rank.

**Mean diff (M1 - B3) = +0.0355, 95% CI = [-0.0286, +0.1288], Wilcoxon stat=33.0, p=0.6379**

CI chua 0: CO. M1>B3 o 7 incident, M1<B3 o 5, hoa 3.

| Incident | M1 | B3 | Diff |
|---|---|---|---|
| bsc_token_hub_2022 | 1.0000 | 0.9417 | +0.0583 |
| chibi_finance_2023 | 1.0000 | 1.0000 | +0.0000 |
| deltaprime_arbitrum_2024 | 0.8618 | 0.9042 | -0.0424 |
| feg_bridge_2024 | 0.8303 | 0.9667 | -0.1364 |
| hackerdao_2022 | 0.5053 | 0.6041 | -0.0988 |
| magic_abracadabra_arbitrum_2025 | 0.9503 | 0.8854 | +0.0649 |
| new_free_dao_2022 | 1.0000 | 0.4263 | +0.5737 |
| paraluni_2022 | 0.5894 | 0.5465 | +0.0429 |
| qbridge_qubit_2022 | 0.8943 | 0.8534 | +0.0410 |
| radiant_capital_arbitrum_2024 | 1.0000 | 0.9861 | +0.0139 |
| ronin_bridge_2022 | 0.6793 | 0.6009 | +0.0784 |
| utopiasphere_2024 | 1.0000 | 1.0000 | +0.0000 |
| wault_finance_2021 | 0.9284 | 0.9306 | -0.0021 |
| wooppv2_2024 | 0.8581 | 0.9184 | -0.0603 |
| xkingdom_2024 | 1.0000 | 1.0000 | +0.0000 |
