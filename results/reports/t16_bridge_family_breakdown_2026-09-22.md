# T16 - Breakdown PR-AUC (M1) theo bridge family - chay 2026-09-22

**Canh bao doc ket qua**: chi 2/8 nhom co >=3 incident (Stargate, LI.FI Diamond) — cac nhom con lai n=1 (bang dung 1 gia tri PR-AUC cua incident do, KHONG phai 'dac diem family' co the khai quat hoa). Khong nen dien giai nhom n=1 la 'model manh/yeu voi family X'.

| Incident | Bridge family (chuan hoa) | PR-AUC (M1) |
|---|---|---|
| bsc_token_hub_2022 | BSC Token Hub | 1.0000 |
| chibi_finance_2023 | Stargate (LayerZero) | 1.0000 |
| deltaprime_arbitrum_2024 | Across Protocol | 0.8618 |
| feg_bridge_2024 | FEG SmartBridge | 0.8303 |
| hackerdao_2022 | Chưa giải mã được bridge (TBD_pending_trajectory_decode) | 0.5053 |
| magic_abracadabra_arbitrum_2025 | LI.FI Diamond | 0.9503 |
| new_free_dao_2022 | Chưa giải mã được bridge (TBD_pending_trajectory_decode) | 1.0000 |
| paraluni_2022 | Không dùng bridge (NaN trong registry) | 0.5894 |
| qbridge_qubit_2022 | QBridge (Qubit Finance) | 0.8943 |
| radiant_capital_arbitrum_2024 | LI.FI Diamond | 1.0000 |
| ronin_bridge_2022 | Ronin Bridge | 0.6793 |
| utopiasphere_2024 | LI.FI Diamond | 1.0000 |
| wault_finance_2021 | Không dùng bridge (NaN trong registry) | 0.9284 |
| wooppv2_2024 | Stargate (LayerZero) | 0.8581 |
| xkingdom_2024 | Stargate (LayerZero) | 1.0000 |

## Tom tat theo family

| Bridge family | n | Mean PR-AUC | Std |
|---|---|---|---|
| Stargate (LayerZero) | 3 | 0.9527 | 0.0819 |
| LI.FI Diamond | 3 | 0.9834 | 0.0287 |
| Chưa giải mã được bridge (TBD_pending_trajectory_decode) | 2 | 0.7527 | 0.3498 |
| Không dùng bridge (NaN trong registry) | 2 | 0.7589 | 0.2397 |
| Across Protocol | 1 | 0.8618 | - |
| FEG SmartBridge | 1 | 0.8303 | - |
| BSC Token Hub | 1 | 1.0000 | - |
| QBridge (Qubit Finance) | 1 | 0.8943 | - |
| Ronin Bridge | 1 | 0.6793 | - |
