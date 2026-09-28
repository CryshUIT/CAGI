# T13 - Logistic Regression tren feature vector cua M1 (chay 2026-09-22)

## Ly do chon huong (b) thay vi (a) GRU/CNN 1D

1. Chi 15 incident, leave-one-incident-out => outer train toi da 14 incident - qua nho de huan luyen sequence model dang tin cay trong thoi gian con lai.
2. GRU/CNN can code moi dang ke (encode categorical, padding/mask, training loop rieng) - rui ro trien khai duoi ap luc deadline cao hon loi ich.
3. Logistic Regression tren DUNG feature vector M1 van tra loi dung cau hoi phan bien ("can cay quyet dinh/boosting khong hay linear da du") voi chi phi/rui ro thap hon, danh gia cong bang bang CUNG protocol (leave-one-incident-out, bootstrap CI muc incident).

## Ket qua

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 (XGBoost) | 0.6624 | [0.5234, 0.8864] |
| T13 (LogReg, cung feature) | 0.7548 | [0.6459, 0.8980] |

**Paired diff (T13 - M1) = +0.0263, 95% bootstrap CI (muc incident) = [-0.0217, +0.0794]**

Wilcoxon signed-rank: statistic=24.0, p-value=0.4235963177660037

| Incident | T13 | M1 | Diff |
|---|---|---|---|
| bsc_token_hub_2022 | 0.9417 | 1.0000 | -0.0583 |
| chibi_finance_2023 | 1.0000 | 1.0000 | +0.0000 |
| deltaprime_arbitrum_2024 | 0.9750 | 0.8618 | +0.1132 |
| feg_bridge_2024 | 0.8625 | 0.8303 | +0.0322 |
| hackerdao_2022 | 0.7567 | 0.5053 | +0.2514 |
| magic_abracadabra_arbitrum_2025 | 1.0000 | 0.9503 | +0.0497 |
| new_free_dao_2022 | 0.9341 | 1.0000 | -0.0659 |
| paraluni_2022 | 0.5524 | 0.5894 | -0.0370 |
| qbridge_qubit_2022 | 0.8966 | 0.8943 | +0.0022 |
| radiant_capital_arbitrum_2024 | 1.0000 | 1.0000 | +0.0000 |
| ronin_bridge_2022 | 0.8015 | 0.6793 | +0.1222 |
| utopiasphere_2024 | 1.0000 | 1.0000 | +0.0000 |
| wault_finance_2021 | 0.7714 | 0.9284 | -0.1570 |
| wooppv2_2024 | 1.0000 | 0.8581 | +0.1419 |
| xkingdom_2024 | 1.0000 | 1.0000 | +0.0000 |

## KET LUAN

KHONG DU BANG CHUNG: 95% CI cua hieu so (T13 - M1) chua 0 — khong the ket luan linear hay boosting tot hon co y nghia thong ke voi 15 incident hien tai.
