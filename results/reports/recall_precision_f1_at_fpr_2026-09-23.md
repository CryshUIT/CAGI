# Recall/Precision/F1 cua M1 va B3 tai cac muc FPR rang buoc (2026-09-23)

Threshold chon qua inner-CV (LOGO tren outer-train), giong het thiet ke goc dung cho RQ1/main results (`select_threshold`, khong dung outer test) - KHONG chon threshold moi de toi uu Recall. target_fpr=0.01 la muc chinh thuc da dung cho 0,6624 (M1)/B3 trong main_table.csv; 0.05/0.10 la danh gia THEM tren model da dong bang, chua tung tinh truoc day trong repo.

| Model | Target FPR | Pooled PR-AUC | Recall | Precision | F1 | FPR thuc te (pooled) | N dong |
|---|---|---|---|---|---|---|---|
| M1 | 1% | 0.6624 | 0.5172 | 0.7692 | 0.6186 | 0.0108 | 1785 |
| M1 | 5% | 0.6624 | 0.7931 | 0.4767 | 0.5955 | 0.0605 | 1785 |
| M1 | 10% | 0.6624 | 0.8793 | 0.3849 | 0.5354 | 0.0977 | 1785 |
| B3 | 1% | 0.6875 | 0.5259 | 0.8133 | 0.6387 | 0.0084 | 1785 |
| B3 | 5% | 0.6875 | 0.7414 | 0.5059 | 0.6014 | 0.0503 | 1785 |
| B3 | 10% | 0.6875 | 0.8707 | 0.3755 | 0.5247 | 0.1007 | 1785 |

Ghi chu: Recall/Precision/F1 tinh POOLED (gop tat ca dong outer-test qua 15 fold), moi dong dung threshold cua CHINH fold da giu no lam outer test (moi fold co the co threshold khac nhau vi chon rieng tren inner-CV cua fold do - xem file *_thresholds_2026-09-23.csv de xem chi tiet tung fold).
