"""NSS 2026 - Viec 1 (ngay 2026-09-23): Recall/Precision/F1 cua M1 va B3 tai
cac muc FPR rang buoc (1%, 5%, 10%), dung DUNG threshold da chon qua inner-CV
nhu thiet ke goc (evaluate_model_nested/select_threshold), KHONG chon threshold
moi de "toi uu" Recall tren outer test.

target_fpr=0.01 la muc DA dung cho RQ1/main results (0.6624 cho M1) - chay lai
o day CHI de lay them Recall/Precision/F1 pooled (chua tung luu truoc day,
chi luu recall_at_fpr_0.01 don le). target_fpr=0.05/0.10 CHUA TUNG duoc tinh
truoc day trong repo nay (da grep xac nhan) - day la danh gia THEM diem van
hanh tren model DA DONG BANG, dung chinh xac phuong phap nested-threshold-
selection goc, KHONG PHAI mot no luc cai thien moi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc, recall_precision_f1_at_threshold  # noqa: E402
from src.evaluation.nested_eval import dedupe_pooled_prefixes, evaluate_model_nested  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel, B3FlatGraphRandomForest  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TARGET_FPRS = [0.01, 0.05, 0.10]
MODELS = {"M1": M1TypedTemporalMotifModel, "B3": B3FlatGraphRandomForest}

OUT_CSV = ROOT / "results" / "tables" / "recall_precision_f1_at_fpr_2026-09-23.csv"
OUT_FOLD_CSV = ROOT / "results" / "tables" / "recall_precision_f1_at_fpr_thresholds_2026-09-23.csv"
OUT_MD = ROOT / "results" / "reports" / "recall_precision_f1_at_fpr_2026-09-23.md"


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    rows = []
    threshold_rows = []
    for model_name, model_cls in MODELS.items():
        for target_fpr in TARGET_FPRS:
            print(f"=== {model_name}, target_fpr={target_fpr:.2f} ===", flush=True)
            res = evaluate_model_nested(lambda: model_cls(), X, y, groups, target_fpr=target_fpr)
            oof_prob = res["oof_prob"]
            oof_threshold = res["oof_threshold"]
            valid = oof_prob.notna() & oof_threshold.notna()

            y_valid = y[valid].to_numpy()
            prob_valid = oof_prob[valid].to_numpy()
            thr_valid = oof_threshold[valid].to_numpy()

            auc = pr_auc(y_valid, prob_valid)
            metrics = recall_precision_f1_at_threshold(y_valid, prob_valid, thr_valid)
            actual_fpr = float(((prob_valid >= thr_valid) & (y_valid == 0)).sum()) / max(1, (y_valid == 0).sum())

            print(f"  pooled pr_auc={auc:.4f} recall={metrics['recall']:.4f} "
                  f"precision={metrics['precision']:.4f} f1={metrics['f1']:.4f} "
                  f"actual_pooled_fpr={actual_fpr:.4f}", flush=True)

            rows.append({
                "model": model_name, "target_fpr": target_fpr, "pooled_pr_auc": auc,
                "recall": metrics["recall"], "precision": metrics["precision"], "f1": metrics["f1"],
                "actual_pooled_fpr": actual_fpr, "n_rows": int(valid.sum()),
            })
            for _, fr in pd.DataFrame(res["fold_rows"]).iterrows():
                threshold_rows.append({"model": model_name, "target_fpr": target_fpr, **fr.to_dict()})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    pd.DataFrame(threshold_rows).to_csv(OUT_FOLD_CSV, index=False)

    md = ["# Recall/Precision/F1 cua M1 va B3 tai cac muc FPR rang buoc (2026-09-23)\n",
          "\nThreshold chon qua inner-CV (LOGO tren outer-train), giong het thiet ke "
          "goc dung cho RQ1/main results (`select_threshold`, khong dung outer test) - "
          "KHONG chon threshold moi de toi uu Recall. target_fpr=0.01 la muc chinh thuc "
          "da dung cho 0,6624 (M1)/B3 trong main_table.csv; 0.05/0.10 la danh gia THEM tren "
          "model da dong bang, chua tung tinh truoc day trong repo.\n",
          "\n| Model | Target FPR | Pooled PR-AUC | Recall | Precision | F1 | FPR thuc te (pooled) | N dong |\n",
          "|---|---|---|---|---|---|---|---|\n"]
    for _, r in out.iterrows():
        md.append(f"| {r['model']} | {r['target_fpr']:.0%} | {r['pooled_pr_auc']:.4f} | "
                   f"{r['recall']:.4f} | {r['precision']:.4f} | {r['f1']:.4f} | "
                   f"{r['actual_pooled_fpr']:.4f} | {int(r['n_rows'])} |\n")
    md.append("\nGhi chu: Recall/Precision/F1 tinh POOLED (gop tat ca dong outer-test qua 15 "
               "fold), moi dong dung threshold cua CHINH fold da giu no lam outer test (moi fold "
               "co the co threshold khac nhau vi chon rieng tren inner-CV cua fold do - xem file "
               "*_thresholds_2026-09-23.csv de xem chi tiet tung fold).\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV}, {OUT_FOLD_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
