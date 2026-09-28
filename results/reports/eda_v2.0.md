# EDA v2.0 — Dataset chinh thuc N=15 (2026-09-27)

**Thay the** `results/reports/eda_v0.5.html` (CU: 11 positive + 408 hard-negative, freeze v0.9,
khong co plot anh that). Ban nay chay tren DUNG dataset dang dung de sinh
`results/tables/main_table.csv` / `data/dataset_card.md`: **15 positive incident,
612 hard-negative, 3354 prefix row** (RAW, `data/processed/features_v2.parquet`,
khop CHINH XAC voi dataset_card.md).

Nguon xac dinh dataset chinh thuc: `data/processed/features_v2.parquet` (RAW, 3354 dong,
627 trajectory) - chinh la file duoc `dedupe_pooled_prefixes()` xu ly
truoc khi dua vao moi pipeline RQ1/RQ2/ablation trong `results/tables/main_table.csv`. Khong dung
lai `src/pipeline/dataset_builder.py::load_rq1_trajectories` (nguon CU cua ban v0.5, tro toi
freeze v0.9 11-incident, khong con dung cho ket qua hien tai).

Khong train lai model, khong doi feature/threshold/ket qua da freeze o buoc nao trong file nay.

## A. Class balance

| Muc do | Positive | Negative | Ty le neg:pos | Positive rate |
|---|---|---|---|---|
| Trajectory-level | 15 | 612 | 40.8:1 | 2.3923% |
| Prefix-row-level (RAW, 3354 dong) | 120 | 3234 | 26.9:1 | 3.5778% |

**Doi chieu voi dataset_card.md/paper**: ky vong 15 positive incident, 612 hard-negative,
3354 prefix row -> KHOP CHINH XAC.

**Ve con so "positive rate 5.0%" trong paper**: 3.58% (prefix-row RAW) va
2.39% (trajectory-level) - **CA HAI DEU KHONG KHOP 5.0%**. Da thu them ca
positive rate tren tap DA DEDUPE (dung cho modeling RQ1, 1785 dong): xem duoi.
KHONG tim thay chuoi "5.0%"/"5,0%" o bat ky report/dataset_card nao trong repo qua grep -
day co the la con so tinh theo cach khac trong paper (vd lam tron/xap xi khac), hoac stale
tu ban truoc. **KHONG tu sua/lam khop - can nguoi dung doi chieu lai voi cong thuc that
dung trong paper.**

[Tham khao] Positive rate tren tap DA DEDUPE (dung cho RQ1 modeling thuc te, `dedupe_pooled_prefixes`, 1785 dong): **6.4986%** - van khong khop 5.0% chinh xac nhung gan hon ca (~6.5%).

## B. Phan bo do dai trajectory theo lop

| Lop | n | min | Q1 | median | Q3 | max |
|---|---|---|---|---|---|---|
| Positive | 15 | 9 | 29.0 | 73.0 | 305.0 | 1625 |
| Negative | 612 | 1 | 1.0 | 2.0 | 3.0 | 1000 |

**Shortcut check (IQR chong lap?):** KHONG CHONG LAP - "
**CANH BAO tuong tu ban v0.5**: 2 lop co the tach duoc chi bang do dai, can kiem tra ky hon truoc khi tin tuong feature khac dang hoc gi that.

![Trajectory length](eda_v2.0_trajectory_length.png)

## C. Phan bo theo chain

| chain    |   0 |   1 |
|:---------|----:|----:|
| arbitrum | 226 |   6 |
| bsc      | 269 |   7 |
| eth      | 117 |   2 |

![Chain distribution](eda_v2.0_chain_distribution.png)

## D. Bridge family (CHI 15 positive incident - hard-negative khong co bridge family da xac minh)

| bridge_families           |   so incident |
|:--------------------------|--------------:|
| Stargate                  |             3 |
| LI.FI Diamond             |             3 |
| n/a                       |             2 |
| TBD/chua decode           |             2 |
| Ronin Bridge              |             1 |
| QBridge                   |             1 |
| FEG SmartBridge           |             1 |
| Across Protocol SpokePool |             1 |
| BSC Token Hub             |             1 |

(Ghi chu: hard-negative KHONG co truong bridge_family da xac minh doc lap trong registry - chi
positive incident co du lieu nay, nen phan tich nay CHI tinh tren 15 positive.)

## E. Phan bo theo event type (tong so action, tren trajectory day du)

|                  |     0 |    1 |
|:-----------------|------:|-----:|
| transfer         | 20273 | 3259 |
| bridge_deposit   |  2307 |  103 |
| bridge_withdraw  |     0 |    0 |
| lending_deposit  |     0 |    5 |
| lending_withdraw |     0 |    0 |
| swap             |   608 |  418 |
| split            |   152 |  110 |
| merge            |     1 |   47 |
| mixer_or_exit    |    42 |   25 |
| other            |     0 |    0 |

![Event type distribution](eda_v2.0_event_type_distribution.png)

## F. Phan bo feature theo 5 nhom (positive vs negative, tren trajectory day du)

### Nhom `temporal`
- `burstiness`: pos median=0.3794 (Q1-Q3 0.1895-0.5), neg median=0 (Q1-Q3 -0.3049-0)
- `active_duration_sec`: pos median=8.372e+04 (Q1-Q3 4.551e+04-2.435e+05), neg median=90.5 (Q1-Q3 0-3.362e+04)

### Nhom `structural`
- `fan_out`: pos median=3 (Q1-Q3 2.5-6), neg median=1 (Q1-Q3 1-2)
- `path_depth`: pos median=3 (Q1-Q3 2.5-4.5), neg median=1 (Q1-Q3 1-1)

### Nhom `economic`
- `log_amount_mean`: pos median=1.689 (Q1-Q3 1.238-2.009), neg median=0.2768 (Q1-Q3 0.0392-1.095)
- `value_retention`: pos median=0.6742 (Q1-Q3 0.4869-7.223), neg median=1 (Q1-Q3 0.9915-1.007)

### Nhom `semantic_action`
- `action_count_swap_ratio`: pos median=0.06831 (Q1-Q3 0.02309-0.169), neg median=0 (Q1-Q3 0-0)
- `num_bridge_families`: pos median=0 (Q1-Q3 0-1), neg median=0 (Q1-Q3 0-1)

### Nhom `motif`
- `motif_split`: pos median=6 (Q1-Q3 3.5-21.5), neg median=1 (Q1-Q3 0-1)
- `motif_rapid_token_pivot`: pos median=21 (Q1-Q3 10-198.5), neg median=0 (Q1-Q3 0-0)

![Feature group boxplots](eda_v2.0_feature_group_boxplots.png)

## G. Phan bo 5 motif count theo lop

| Motif | pos median | pos Q1-Q3 | neg median | neg Q1-Q3 |
|---|---|---|---|---|
| split | 6.00 | 3.50-21.50 | 1.00 | 0.00-1.00 |
| merge | 9.00 | 3.50-32.00 | 0.00 | 0.00-1.00 |
| peel-like chain | 0.00 | 0.00-1.00 | 0.00 | 0.00-0.00 |
| bridge→swap | 0.00 | 0.00-0.00 | 0.00 | 0.00-0.00 |
| rapid token pivot | 21.00 | 10.00-198.50 | 0.00 | 0.00-0.00 |

![Motif counts](eda_v2.0_motif_counts.png)

## H. Positive rate theo checkpoint

| Checkpoint | n dong | n positive | positive rate |
|---|---|---|---|
| k_2 | 350 | 15 | 4.2857% |
| k_3 | 241 | 15 | 6.2241% |
| k_5 | 143 | 15 | 10.4895% |
| k_7 | 112 | 15 | 13.3929% |
| ratio_25 | 627 | 15 | 2.3923% |
| ratio_50 | 627 | 15 | 2.3923% |
| ratio_75 | 627 | 15 | 2.3923% |
| ratio_100 | 627 | 15 | 2.3923% |

![Positive rate by checkpoint](eda_v2.0_positive_rate_by_checkpoint.png)

## I. Correlation heatmap

**Kiem chung 'correlated by construction' (paper claim):**

| Cap feature | Spearman corr |
|---|---|
| `motif_split` vs `branch_count` | +1.0000 |
| `motif_split` vs `fan_out` | +0.6381 |
| `action_count_merge_ratio` vs `outgoing_incoming_ratio` | -1.0000 |

![Correlation heatmap](eda_v2.0_correlation_heatmap.png)

## J. Missingness theo optional field (muc raw event, tinh tren TOAN BO action that)

| Optional field | % missing | n_missing / n_total |
|---|---|---|
| protocol | 90.93% | 24868/27350 |
| token | 0.00% | 0/27350 |
| counterparty_type | 100.00% | 27350/27350 |
| source_confidence | 0.00% | 0/27350 |
