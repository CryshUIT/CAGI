# T12 - Do nhay theo random seed (M1, B3) - chay 2026-09-22

Seed dung: [42, 1, 7, 123, 2026] (42 = seed goc dung trong main_table.csv, giu nguyen moi thu khac: split leave-one-incident-out, feature set, hyperparameter mac dinh).

| Model | Seed | Pooled PR-AUC |
|---|---|---|
| M1 | 42 | 0.6624 |
| M1 | 1 | 0.6624 |
| M1 | 7 | 0.6624 |
| M1 | 123 | 0.6624 |
| M1 | 2026 | 0.6624 |
| B3 | 42 | 0.6875 |
| B3 | 1 | 0.6714 |
| B3 | 7 | 0.7031 |
| B3 | 123 | 0.6944 |
| B3 | 2026 | 0.6790 |

## Tom tat

| Model | Mean | Std | Min | Max |
|---|---|---|---|---|
| B3 | 0.6871 | 0.0125 | 0.6714 | 0.7031 |
| M1 | 0.6624 | 0.0000 | 0.6624 | 0.6624 |
