# Ket qua danh gia N=30 (chay MOT LAN theo analysis_plan_N30_v3.md) - 2026-10-15

CHUA viet ket luan - CHI bao cao so lieu theo dung gate da dang ky.

## N=30 (phan tich CHINH)

M1 vs B3 paired: mean_diff=+0.0305, 95% CI=[-0.0168,+0.0878], Wilcoxon stat=120.0, p=0.2528

### PR-AUC pooled theo model (N=30)

| model   |   mean_point_estimate |   ci_low_95 |   ci_high_95 |
|:--------|----------------------:|------------:|-------------:|
| B0      |             0.054298  |   0.0467931 |    0.0676203 |
| B1      |             0.514818  |   0.439936  |    0.593284  |
| B2      |             0.0751562 |   0.0610348 |    0.0986951 |
| B3      |             0.754293  |   0.644948  |    0.857421  |
| M1      |             0.776168  |   0.656652  |    0.897869  |

### Per-incident PR-AUC (M1 vs B3, N=30)

| Incident | do_dai | M1 | B3 | gap |
|---|---|---|---|---|
| 0xinfini_2025 | 25 | 1.0000 | 1.0000 | +0.0000 |
| beanstalk_farms_2022 | 443 | 1.0000 | 0.9705 | +0.0295 |
| bsc_token_hub_2022 | 362 | 0.8374 | 0.8103 | +0.0271 |
| chibi_finance_2023 | 40 | 1.0000 | 1.0000 | +0.0000 |
| cork_protocol_2025 | 1 | 0.0145 | 0.0091 | +0.0054 |
| deltaprime_arbitrum_2024 | 23 | 0.8927 | 0.8482 | +0.0445 |
| dough_finance_2024 | 17 | 0.6364 | 1.0000 | -0.3636 |
| easyfi_2021 | 16560 | 0.9226 | 0.9519 | -0.0293 |
| feg_bridge_2024 | 9 | 1.0000 | 1.0000 | +0.0000 |
| hackerdao_2022 | 35 | 0.6575 | 0.5268 | +0.1307 |
| heco_htx_2023 | 1557 | 0.9750 | 0.8167 | +0.1583 |
| hedgey_finance_2024 | 755 | 1.0000 | 0.9750 | +0.0250 |
| inverse_finance_2022_jun | 11592 | 0.9861 | 1.0000 | -0.0139 |
| lendhub_2023 | 274 | 0.9705 | 1.0000 | -0.0295 |
| magic_abracadabra_arbitrum_2025 | 88 | 0.7875 | 0.6890 | +0.0985 |
| new_free_dao_2022 | 12 | 0.9617 | 0.4731 | +0.4886 |
| onyx_protocol_2023 | 16 | 0.9160 | 0.4544 | +0.4615 |
| paraluni_2022 | 511 | 0.5238 | 0.5221 | +0.0017 |
| popsicle_finance_2021 | 980 | 0.9381 | 0.9861 | -0.0480 |
| prisma_finance_2024 | 70 | 0.8355 | 0.8225 | +0.0130 |
| qbridge_qubit_2022 | 698 | 0.9417 | 0.9519 | -0.0103 |
| radiant_capital_arbitrum_2024 | 248 | 0.9583 | 0.9583 | +0.0000 |
| ronin_bridge_2022 | 1625 | 0.6412 | 0.5597 | +0.0815 |
| thorchain2_2021 | 99 | 0.8742 | 0.9294 | -0.0552 |
| uranium_finance_2021 | 64 | 0.5840 | 0.6259 | -0.0419 |
| utopiasphere_2024 | 37 | 1.0000 | 1.0000 | +0.0000 |
| wault_finance_2021 | 190 | 1.0000 | 0.9861 | +0.0139 |
| wooppv2_2024 | 16 | 0.8726 | 1.0000 | -0.1274 |
| xkingdom_2024 | 73 | 1.0000 | 1.0000 | +0.0000 |
| zunami_protocol_2023 | 31 | 1.0000 | 0.9464 | +0.0536 |

### Spearman(gap, do dai trajectory), loai new_free_dao_2022, N=29

rho=-0.0180, p=0.926050, jackknife_mean=-0.0180, jackknife_se=0.2165

### Subgroup do dai (nguong <=40/>40)

- LONG (>40, n=18): mean_diff=+0.0122, CI=[-0.0104,+0.0387]
- SHORT (<=40, n=12): mean_diff=+0.0578, CI=[-0.0605,+0.1866]

## 4 moc cong don (N=15/20/25/30, thu tu registry, config_N30)

| N | M1 vs B3 mean_diff | 95% CI | Wilcoxon p |
|---|---|---|---|
| 15 | -0.0462 | [-0.1434,+0.0497] | 0.3028 |
| 20 | +0.0341 | [-0.0426,+0.1213] | 0.4997 |
| 25 | +0.0193 | [-0.0349,+0.0866] | 0.8077 |
| 30 | +0.0305 | [-0.0168,+0.0878] | 0.2528 |

Trich N=15 leak-fixed da freeze (khong chay lai o day, chi doi chieu): M1=0.5924, B3=0.6366, diff=-0.0462, CI=[-0.1434,+0.0497], p=0.3028

## Sensitivity (a)(b)(c)

| Sensitivity | n_incident_loai | mean_diff | 95% CI | Wilcoxon p |
|---|---|---|---|---|
| a_exclude_leq2_actions | 1 | +0.0342 | [-0.0174,+0.0924] | 0.2124 |
| b_exclude_gt5000_actions | 2 | +0.0355 | [-0.0194,+0.0981] | 0.2305 |
| c_exclude_allowlist_completion_changed | 6 | +0.0265 | [-0.0425,+0.1128] | 0.8405 |

## Table 3b (4 checkpoint ratio_25/50/75/100, N=30 toan bo)

| prefix_bucket   |   n_rows |   n_positive |   M1_pr_auc |   M1_ci_low |   M1_ci_high |   B3_pr_auc |   B3_ci_low |   B3_ci_high |   gap_M1_minus_B3 |
|:----------------|---------:|-------------:|------------:|------------:|-------------:|------------:|------------:|-------------:|------------------:|
| ratio_25        |     1127 |           30 |    0.841496 |    0.732738 |     0.941069 |    0.753405 |    0.591174 |     0.91132  |         0.0880913 |
| ratio_50        |     1127 |           30 |    0.909596 |    0.819192 |     0.977304 |    0.842051 |    0.719302 |     0.94221  |         0.0675454 |
| ratio_75        |     1127 |           30 |    0.933032 |    0.849064 |     0.990568 |    0.842636 |    0.720869 |     0.942329 |         0.0903962 |
| ratio_100       |     1127 |           30 |    0.928193 |    0.845011 |     0.987247 |    0.788373 |    0.638164 |     0.949929 |         0.13982   |

## RQ2: 20 incident endpoint-confirmed

| subset                | prefix_bucket   |   mean_pr_auc |   mean_recall_at_fpr1 |   mean_false_alerts_per_1000 |   n_folds |
|:----------------------|:----------------|--------------:|----------------------:|-----------------------------:|----------:|
| endpoint_confirmed_20 | ratio_25        |      0.975    |              0.95     |                      7.85742 |        20 |
| endpoint_confirmed_20 | ratio_50        |      0.918056 |              0.9      |                     10.049   |        20 |
| endpoint_confirmed_20 | ratio_75        |      0.922222 |              0.9      |                      5.59524 |        20 |
| endpoint_confirmed_20 | ratio_100       |      0.975    |              0.95     |                     11.6435  |        20 |
| endpoint_confirmed_20 | k_2             |      0.762302 |              0.65     |                     13.6574  |        20 |
| endpoint_confirmed_20 | k_3             |      0.821692 |              0.789474 |                      2.63158 |        20 |
| endpoint_confirmed_20 | k_5             |      0.897386 |              0.882353 |                      3.84615 |        20 |
| endpoint_confirmed_20 | k_7             |      0.872222 |              0.8      |                     16.6667  |        20 |

## RQ2: 9 incident sensitivity (d)

| subset          | prefix_bucket   |   mean_pr_auc |   mean_recall_at_fpr1 |   mean_false_alerts_per_1000 |   n_folds |
|:----------------|:----------------|--------------:|----------------------:|-----------------------------:|----------:|
| sensitivity_d_9 | ratio_25        |      0.750441 |              0.666667 |                     19.6078  |         9 |
| sensitivity_d_9 | ratio_50        |      0.901235 |              0.888889 |                      9.52381 |         9 |
| sensitivity_d_9 | ratio_75        |      0.901235 |              0.888889 |                      6.79012 |         9 |
| sensitivity_d_9 | ratio_100       |      0.777778 |              0.555556 |                     10.4644  |         9 |
| sensitivity_d_9 | k_2             |      0.759259 |              0.555556 |                      0       |         9 |
| sensitivity_d_9 | k_3             |      0.697115 |              0.5      |                      7.40741 |         9 |
| sensitivity_d_9 | k_5             |      0.690476 |              0.428571 |                      0       |         9 |
| sensitivity_d_9 | k_7             |      0.527778 |              0.166667 |                     37.037   |         9 |

## Bang mo ta theo chain

| chain    |   n_incident |   n_positive |   n_negative |   M1_pr_auc_pooled |   B3_pr_auc_pooled |
|:---------|-------------:|-------------:|-------------:|-------------------:|-------------------:|
| eth      |           17 |           17 |          602 |           0.641682 |           0.656812 |
| bsc      |            7 |            7 |          269 |           0.763615 |           0.75204  |
| arbitrum |            6 |            6 |          226 |           0.750144 |           0.787238 |

## Limitations da biet

- Builder mo rong qua hub khong allowlist (xem known_builder_limitations.md).
- protocol_map v1.0 dong bang - TornadoProxy khong duoc nhan la mixer boi pipeline.
- Cua so mining khac cua so tracking (72h).
- Yield cua v2_complexity phu thuoc thu tu xu ly incident.
- Horizon 72h loai tru rua tien tre (HECO, Uranium, THORChain-2).
- Nhan endpoint khong co nguong gia tri co dinh.
- xkingdom va FEG Bridge co phan mixer nam o chain khac (ngoai trajectory tracked).
