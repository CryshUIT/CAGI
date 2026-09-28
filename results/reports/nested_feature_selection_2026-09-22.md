# Nested feature selection cho M1 (permutation importance, 2026-09-22)

Phuong phap: permutation importance tinh TREN INNER-CV (14 incident/outer-train) - KHONG dung RFE lap greedy vi chi phi tinh toan qua lon (xem docstring script). Giu feature co importance>0 (hoan vi lam GIAM PR-AUC inner-CV), loai feature <=0.

| Model | Mean PR-AUC | 95% CI |
|---|---|---|
| M1 goc (moc chinh thuc, 48 cot tho -> ~39-41 cot sau loc coverage) | 0.6624 | [0.5234, 0.8864] |
| **M1 + nested feature selection** | **0.6210** | [0.4660, 0.8710] |

**Paired diff (FeatureSelection - M1 goc) = -0.0812, 95% CI = [-0.1803, -0.0198]**

## Feature bi loai thuong xuyen nhat qua 15 outer fold

| Feature | Bi loai o so fold | % fold |
|---|---|---|
| action_count_merge_ratio | 15/15 | 100% |
| motif_split | 15/15 | 100% |
| motif_swap_then_split | 15/15 | 100% |
| outgoing_incoming_ratio | 15/15 | 100% |
| motif_rapid_token_pivot | 13/15 | 87% |
| stablecoin_pivot | 12/15 | 80% |
| inter_action_gap_std | 10/15 | 67% |
| motif_peel_like_chain | 10/15 | 67% |
| active_duration_sec | 9/15 | 60% |
| token_category_diversity | 9/15 | 60% |
| action_count_lending_deposit_ratio | 7/15 | 47% |
| action_count_transfer_ratio | 6/15 | 40% |
| local_ego_density | 6/15 | 40% |
| value_retention | 3/15 | 20% |
| action_count_swap_ratio | 2/15 | 13% |

## KET LUAN

KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc. DUNG o day, khong thu bien the khac.
