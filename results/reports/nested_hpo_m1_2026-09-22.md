# Nested hyperparameter tuning cho M1 (chay 2026-09-22)

## Dinh chinh mot dieu truoc khi doc ket qua

M1 hien tai (0.6624) DA tu dong tinh `scale_pos_weight = n_neg/n_pos` rieng cho tung fold ben trong `fit()` (xem `src/models/baselines.py`) - khong phai "chua xu ly mat can bang lop" nhu mo ta ban dau. Diem thuc su chua tune la GIA TRI CO DINH cua max_depth/learning_rate/n_estimators va CHIEN LUOC ap dung scale_pos_weight (luon la n_neg/n_pos, chua thu chien luoc khac).

## 7 candidate da thu (moi candidate doi 1 truc so voi baseline)

| Candidate | max_depth | learning_rate | n_estimators | scale_pos_weight |
|---|---|---|---|---|
| baseline (M1 hien tai) | 4 | 0.1 | 200 | auto |
| depth=3 | 3 | 0.1 | 200 | auto |
| depth=6 | 6 | 0.1 | 200 | auto |
| lr=0.05,n_est=400 | 4 | 0.05 | 400 | auto |
| lr=0.2,n_est=100 | 4 | 0.2 | 100 | auto |
| spw=none | 4 | 0.1 | 200 | none |
| spw=auto_sqrt | 4 | 0.1 | 200 | auto_sqrt |

## Ket qua

| Model | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| M1 goc (moc, KHONG doi) | 0.6624 | [0.5234, 0.8864] |
| M1 sau nested HPO | 0.6062 | [0.4811, 0.8711] |

**Paired diff (HPO - goc) = -0.0647, 95% bootstrap CI = [-0.1650, +0.0061]**

Wilcoxon signed-rank: statistic=19.0, p-value=0.3862707203664827

## Hyperparameter duoc chon o tung outer fold (co the khac nhau - dung chuan nested CV)

| Incident giu lai | Candidate thang | Inner-CV PR-AUC | PR-AUC outer test |
|---|---|---|---|
| bsc_token_hub_2022 | spw=none | 0.6333 | 1.0000 |
| chibi_finance_2023 | spw=none | 0.6528 | 1.0000 |
| deltaprime_arbitrum_2024 | spw=none | 0.7001 | 0.8518 |
| feg_bridge_2024 | depth=3 | 0.6575 | 0.2311 |
| hackerdao_2022 | depth=3 | 0.6940 | 0.5023 |
| magic_abracadabra_arbitrum_2025 | spw=none | 0.6582 | 0.9861 |
| new_free_dao_2022 | spw=none | 0.6562 | 0.6159 |
| paraluni_2022 | depth=3 | 0.6743 | 0.6111 |
| qbridge_qubit_2022 | spw=auto_sqrt | 0.6661 | 0.8572 |
| radiant_capital_arbitrum_2024 | spw=none | 0.6488 | 1.0000 |
| ronin_bridge_2022 | depth=3 | 0.8375 | 0.7276 |
| utopiasphere_2024 | spw=none | 0.7181 | 1.0000 |
| wault_finance_2021 | spw=none | 0.6688 | 0.8822 |
| wooppv2_2024 | spw=none | 0.6881 | 0.8614 |
| xkingdom_2024 | spw=none | 0.6524 | 1.0000 |

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE: 95% CI hieu so chua 0 — nested HPO KHONG chung minh duoc tot hon ban goc voi 15 incident hien tai. Theo dung rang buoc da dat ra, DUNG o day, khong thu bien the khac de 'cuu' ket qua.
