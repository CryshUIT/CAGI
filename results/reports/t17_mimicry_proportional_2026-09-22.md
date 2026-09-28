# T17 (ban sua, ty le %) - Mimicry stress test theo % do dai trajectory (2026-09-22)

**Ban truoc (so co dinh 2/4/8 action)** van giu nguyen KHONG xoa lam phu luc: `results/tables/t17_mimicry_stress_test_2026-09-22.csv`, `results/reports/t17_mimicry_stress_test_2026-09-22.md` - KHONG dung lam ket qua chinh vi cuong do nhieu khong dong deu giua incident ngan/dai (da xac nhan).

## Phuong phap

Chen action THAT (tu hard-negative cung incident) theo TY LE % do dai trajectory goc (5%/10%/20%, toi thieu 1 action) thay vi so co dinh - dam bao cuong do nguy trang tuong doi dong deu giua trajectory ngan/dai. Giu nguyen co che chen (khe ngau nhien, noi suy timestamp), cham diem (M1 fit tren 14 incident con lai), va fix dedupe checkpoint.

**Doi chieu pct=0 voi M1 chinh thuc (0.6624): KHOP (tinh duoc 0.6624).**

## Kiem tra do dong deu cuong do nhieu (dieu kien de bang duoc coi la dang tin cay)

| Muc % danh nghia | Ty le thuc te TB | Std | Min | Max |
|---|---|---|---|---|
| 5% | 5.8% | 1.8% | 4.3% | 11.1% |
| 10% | 10.2% | 1.0% | 8.3% | 12.5% |
| 20% | 20.0% | 1.3% | 16.7% | 22.2% |

## Ket qua pooled (15 incident)

| Muc % | Mean PR-AUC (pooled) | 95% CI |
|---|---|---|
| 0% | 0.6624 | [0.5234, 0.8864] |
| 5% | 0.6466 | [0.4936, 0.8703] |
| 10% | 0.6519 | [0.4922, 0.8800] |
| 20% | 0.6317 | [0.4768, 0.8519] |

## Ket qua per-incident (PR-AUC cuc bo, chinh incident do vs hard-negative rieng no)

| Incident | 0% | 5% | 10% | 20% |
|---|---|---|---|---|
| bsc_token_hub_2022 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| chibi_finance_2023 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| deltaprime_arbitrum_2024 | 0.8618 | 0.8629 | 0.8333 | 0.7501 |
| feg_bridge_2024 | 0.8303 | 0.1277 | 0.1120 | 0.4585 |
| hackerdao_2022 | 0.5053 | 0.5053 | 0.4951 | 0.3948 |
| magic_abracadabra_arbitrum_2025 | 0.9503 | 0.9503 | 0.9381 | 0.9472 |
| new_free_dao_2022 | 1.0000 | 0.3494 | 0.7929 | 0.5543 |
| paraluni_2022 | 0.5894 | 0.5933 | 0.6037 | 0.5994 |
| qbridge_qubit_2022 | 0.8943 | 0.8943 | 0.8943 | 0.8943 |
| radiant_capital_arbitrum_2024 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| ronin_bridge_2022 | 0.6793 | 0.6227 | 0.6168 | 0.5402 |
| utopiasphere_2024 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| wault_finance_2021 | 0.9284 | 0.9284 | 0.9381 | 0.9381 |
| wooppv2_2024 | 0.8581 | 0.8956 | 0.8923 | 0.8923 |
| xkingdom_2024 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
