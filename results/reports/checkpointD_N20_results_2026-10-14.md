# Checkpoint D - Ket qua RQ1/RQ2 tren N=20 (2026-10-14)

## N=20 (phan tich CHINH)

M1 vs B3 paired: mean_diff=+0.0283, 95% CI=[-0.0560,+0.1204], Wilcoxon stat=71.0, p=0.5277

### PR-AUC pooled theo model (N=20)

| model   |   mean_point_estimate |   ci_low_95 |   ci_high_95 |
|:--------|----------------------:|------------:|-------------:|
| B0      |             0.0494602 |   0.0417575 |    0.0637887 |
| B1      |             0.434316  |   0.341409  |    0.536196  |
| B2      |             0.0921734 |   0.0704792 |    0.151352  |
| B3      |             0.672888  |   0.563158  |    0.810685  |
| M1      |             0.700088  |   0.551176  |    0.878036  |

### Per-incident PR-AUC (M1 vs B3, N=20)

| Incident | do_dai | M1 | B3 | gap |
|---|---|---|---|---|
| beanstalk_farms_2022 | 443 | 0.9705 | 0.9705 | +0.0000 |
| bsc_token_hub_2022 | 362 | 0.8297 | 0.8102 | +0.0195 |
| chibi_finance_2023 | 40 | 1.0000 | 1.0000 | +0.0000 |
| cork_protocol_2025 | 1 | 0.0169 | 0.0091 | +0.0079 |
| deltaprime_arbitrum_2024 | 23 | 0.8340 | 0.8004 | +0.0336 |
| feg_bridge_2024 | 9 | 1.0000 | 0.9029 | +0.0971 |
| hackerdao_2022 | 35 | 0.6565 | 0.5207 | +0.1359 |
| hedgey_finance_2024 | 662 | 0.9526 | 0.9861 | -0.0335 |
| magic_abracadabra_arbitrum_2025 | 88 | 0.8387 | 0.7147 | +0.1240 |
| new_free_dao_2022 | 12 | 1.0000 | 0.5215 | +0.4785 |
| onyx_protocol_2023 | 16 | 0.9583 | 0.3857 | +0.5726 |
| paraluni_2022 | 511 | 0.5281 | 0.5284 | -0.0003 |
| qbridge_qubit_2022 | 698 | 1.0000 | 0.9519 | +0.0481 |
| radiant_capital_arbitrum_2024 | 248 | 0.9363 | 0.9306 | +0.0057 |
| ronin_bridge_2022 | 1625 | 0.5471 | 0.7450 | -0.1979 |
| utopiasphere_2024 | 37 | 0.8661 | 0.9861 | -0.1200 |
| wault_finance_2021 | 190 | 0.7951 | 0.9284 | -0.1333 |
| wooppv2_2024 | 16 | 0.3497 | 0.7886 | -0.4389 |
| xkingdom_2024 | 73 | 0.9464 | 1.0000 | -0.0536 |
| zunami_protocol_2023 | 31 | 0.9861 | 0.9659 | +0.0202 |

### Spearman(gap, do dai trajectory), loai new_free_dao_2022, N=19

rho=-0.3231, p=0.177263

### Subgroup do dai (nguong <=40/>40)

- LONG (>40, n=10): mean_diff=-0.0221, CI=[-0.0786,+0.0292]
- SHORT (<=40, n=10): mean_diff=+0.0787, CI=[-0.0809,+0.2535]

## N=19 (sensitivity, bo Cork)

M1 vs B3 paired: mean_diff=+0.0342, 95% CI=[-0.0564,+0.1293], Wilcoxon stat=60.0, p=0.6791

### PR-AUC pooled theo model (N=19)

| model   |   mean_point_estimate |   ci_low_95 |   ci_high_95 |
|:--------|----------------------:|------------:|-------------:|
| B0      |             0.0528906 |   0.0458755 |    0.0681878 |
| B1      |             0.438403  |   0.353724  |    0.543605  |
| B2      |             0.0933591 |   0.0719099 |    0.150841  |
| B3      |             0.677097  |   0.567577  |    0.817431  |
| M1      |             0.726473  |   0.607342  |    0.876755  |

## Trich dan N=15 leak-fixed (khong chay lai)

M1=0.5924, B3=0.6366, paired diff=-0.0462, 95% CI=[-0.1434,+0.0497], p=0.3028
