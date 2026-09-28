# T14 - Ablation gop semantic-action + motif (chay 2026-09-22)

## Luu y quan trong ve dinh nghia (can doc truoc khi dung ket qua)

Yeu cau goc de nghi so sanh voi "E4 (no-temporal)" de tinh interaction effect, nhung E4 loai nhom `temporal` (5 cot: time_to_first_bridge, inter_action_gap_mean/std, burstiness, active_duration_sec) - nhom NAY KHONG nam trong to hop dang ablate o day (semantic_action + motif). Dung E4 de tinh interaction effect se SAI ve mat logic. Toi da chay THEM `M1_no_semantic_action` (loai rieng nhom semantic_action) de co interaction effect dung nghia; van bao cao doi chieu voi E4 rieng theo yeu cau, nhung ghi ro day KHONG PHAI mot phep decomposition chuan.

- **semantic_action** (11 cot that con lai sau khi M1 tu loai noi bo action_count_* tho + bridge_context): `['action_count_transfer_ratio', 'action_count_lending_deposit_ratio', 'action_count_lending_withdraw_ratio', 'action_count_swap_ratio', 'action_count_split_ratio', 'action_count_merge_ratio', 'action_count_mixer_or_exit_ratio', 'action_count_other_ratio', 'num_distinct_bigrams', 'num_distinct_trigrams', 'stablecoin_pivot']`
- **motif** (7 cot, giong E5): `['motif_split', 'motif_merge', 'motif_peel_like_chain', 'motif_bridge_then_swap', 'motif_swap_then_split', 'motif_nested_bridge', 'motif_rapid_token_pivot']`

## Bang tong hop (paired diff so voi M1_full, muc incident)

| Model | Mean PR-AUC (pooled) | Paired diff vs M1_full | Paired 95% CI | Wilcoxon p | Cot loai | Nguon |
|---|---|---|---|---|---|---|
| M1_full | 0.6624 | +0.0000 | [+0.0000, +0.0000] | - | 0 | reused oof_predictions_v1.csv |
| M1_no_motif (E5, tai su dung) | - | -0.0277 | [-0.0958, +0.0208] | - | 7 | reused ablation_per_incident.csv |
| M1_no_semantic_action | 0.6495 | -0.0612 | [-0.1580, +0.0026] | 0.0994 | 11 | moi chay trong script nay |
| M1_no_semantic_and_motif | 0.6365 | -0.0979 | [-0.1967, -0.0175] | 0.0329 | 18 | moi chay trong script nay |

## Interaction effect (dinh nghia dung: semantic_action-rieng + motif-rieng vs gop)

- Tac dong rieng le semantic_action (M1_no_semantic_action - M1_full) = -0.0612
- Tac dong rieng le motif (E5, M1_no_motif - M1_full) = -0.0277
- Tong 2 tac dong rieng le = -0.0889
- Tac dong gop thuc te (M1_no_semantic_and_motif - M1_full) = -0.0979
- **Interaction effect = gop - tong rieng le = -0.0090** (gop LON HON tong 2 tac dong rieng le (co interaction am/tuong tac lam nang them))

## Doi chieu voi E4 (no-temporal) theo yeu cau — CHI mang tinh tham khao do khong cung to hop

- E4 (M1_no_temporal - M1_full), da co san = -0.0530 [-0.1535, +0.0079], p=0.2026
- Tac dong gop (semantic_action+motif) = -0.0979 — lon hon (am hon) tac dong cua rieng no-temporal.
