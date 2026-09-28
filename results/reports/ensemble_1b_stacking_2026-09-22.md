# Ensemble 1b - Stacking M1 + T13 LogReg (2026-09-22)

Meta-learner (LogisticRegression) hoc trong so ket hop [prob_M1, prob_T13] CHI tren inner-CV (14 incident/outer-train), fit lai model goc tren toan bo outer-train, ap dung meta-learner DA HOC (khong fit lai) len outer test.

| Model | Mean PR-AUC | 95% CI |
|---|---|---|
| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |
| **Stacking (meta-learner)** | **0.5946** | [0.4890, 0.8846] |

**Paired diff (Stacking - M1 goc) = +0.0442, 95% CI = [+0.0111, +0.0819]**

## He so meta-learner qua tung outer fold (co the khac nhau - dung chuan nested)

| Incident giu lai | coef M1 | coef T13 | intercept | PR-AUC outer |
|---|---|---|---|---|
| bsc_token_hub_2022 | +1.041 | +4.396 | -2.354 | 0.9750 |
| chibi_finance_2023 | +1.158 | +4.425 | -2.327 | 1.0000 |
| deltaprime_arbitrum_2024 | +1.845 | +3.940 | -2.293 | 0.9464 |
| feg_bridge_2024 | +1.800 | +3.860 | -1.862 | 0.8455 |
| hackerdao_2022 | +2.008 | +4.673 | -2.295 | 0.7027 |
| magic_abracadabra_arbitrum_2025 | +1.617 | +4.106 | -2.339 | 1.0000 |
| new_free_dao_2022 | +1.623 | +4.178 | -2.014 | 1.0000 |
| paraluni_2022 | +1.054 | +5.064 | -2.668 | 0.5511 |
| qbridge_qubit_2022 | +1.728 | +4.114 | -2.425 | 0.9187 |
| radiant_capital_arbitrum_2024 | +1.820 | +4.006 | -2.337 | 1.0000 |
| ronin_bridge_2022 | +3.147 | +2.802 | -2.197 | 0.8500 |
| utopiasphere_2024 | +2.450 | +3.420 | -2.286 | 1.0000 |
| wault_finance_2021 | +1.598 | +3.914 | -2.254 | 0.9705 |
| wooppv2_2024 | +0.212 | +6.419 | -3.231 | 1.0000 |
| xkingdom_2024 | +1.481 | +4.157 | -2.294 | 1.0000 |

## KET LUAN

CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed truoc khi tin day la that.
