"""NSS 2026 - Nang cap M1 (lan thu 4), Viec 2: nested feature selection cho
M1 qua PERMUTATION IMPORTANCE tinh TREN INNER-CV (khong bao gio dung outer
test de quyet dinh giu/bo feature nao).

Chon permutation importance (khong phai RFE lap greedy) vi ly do chi phi
tinh toan: RFE lap greedy tren ~41 feature x 15 outer fold se can hang chuc
nghin lan fit lai XGBoost - khong kha thi trong thoi gian con lai. Permutation
importance CHI can predict lai (khong fit lai) tren model da fit san cua
tung inner fold - re hon nhieu, van la phuong phap nested hop le.

Thiet ke moi outer fold (15 fold):
  1. Inner LOGO (14 incident) - fit model, luu LAI CA MODEL DA FIT cho tung
     inner fold (khong chi predict) de tai su dung cho buoc permutation.
  2. Baseline inner-OOF PR-AUC (pooled qua 14 inner fold) = diem chuan.
  3. Voi MOI feature f trong feature_cols_ CUA outer-train (candidate cols
     M1 tu chon): hoan vi (permute) cot f trong TOAN BO X_train (1 permutation
     co dinh, seed=42+fold_i), roi dung LAI cac model inner DA FIT (khong fit
     lai) de predict tren inner-val TUONG UNG (da bi hoan vi) - tinh permuted
     inner-OOF PR-AUC (pooled). Importance(f) = baseline - permuted.
  4. Giu feature co importance > 0 (permute lam GIAM diem - feature co ich).
     Loai feature co importance <= 0 (permute khong lam giam hoac lam TANG
     diem - feature la nhieu/co hai tren INNER-CV cua fold nay).
  5. Fit model CUOI tren TOAN BO outer-train, CHI voi feature da giu, du doan
     outer test.

Danh sach feature giu lai CO THE khac nhau giua cac outer fold - dung chuan
nested, khong phai loi.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, select_threshold, per_incident_metric  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OUT_TABLE = ROOT / "results" / "tables" / "nested_feature_selection_2026-09-22.csv"
OUT_FOLD_TABLE = ROOT / "results" / "tables" / "nested_feature_selection_folds_2026-09-22.csv"
OUT_DROP_FREQ = ROOT / "results" / "tables" / "nested_feature_selection_drop_freq_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "nested_feature_selection_2026-09-22.md"


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    all_feature_cols = [c for c in df.columns if c not in META_COLS]
    X_full, y, groups = df[all_feature_cols], df["label"], df["group_id"]

    outer_logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    fold_rows = []
    drop_counter = Counter()
    n_outer_folds = 0

    for fold_i, (train_idx, test_idx) in enumerate(outer_logo.split(X_full, y, groups=groups), start=1):
        held_out = groups.iloc[test_idx].iloc[0]
        X_train, y_train, g_train = X_full.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        X_test, y_test = X_full.iloc[test_idx], y.iloc[test_idx]
        n_outer_folds += 1

        # --- Buoc 1: inner LOGO, luu model DA FIT tung inner fold ---
        inner_logo = LeaveOneGroupOut()
        inner_models = []  # (inner_val_idx, model)
        inner_oof_baseline = np.full(len(y_train), np.nan)
        for inner_tr_idx, inner_val_idx in inner_logo.split(X_train, y_train, groups=g_train):
            m = M1TypedTemporalMotifModel()
            m.fit(X_train.iloc[inner_tr_idx], y_train.iloc[inner_tr_idx], g_train.iloc[inner_tr_idx])
            inner_oof_baseline[inner_val_idx] = m.predict_proba(X_train.iloc[inner_val_idx])
            inner_models.append((inner_val_idx, m))

        valid = ~np.isnan(inner_oof_baseline)
        baseline_score = pr_auc(y_train.to_numpy()[valid], inner_oof_baseline[valid])

        # Candidate feature: hop cua feature_cols_ THAT SU duoc dung boi CAC
        # inner model (co the khac nhau nhe do coverage filter tren tung inner-train).
        candidate_features = sorted(set().union(*[set(m.feature_cols_) for _, m in inner_models]))

        rng = np.random.default_rng(42 + fold_i)
        importances = {}
        for feat in candidate_features:
            X_train_perm = X_train.copy()
            X_train_perm[feat] = rng.permutation(X_train_perm[feat].to_numpy())
            permuted_oof = np.full(len(y_train), np.nan)
            for inner_val_idx, m in inner_models:
                if feat in m.feature_cols_:
                    permuted_oof[inner_val_idx] = m.predict_proba(X_train_perm.iloc[inner_val_idx])
                else:
                    permuted_oof[inner_val_idx] = inner_oof_baseline[inner_val_idx]  # feature nay model khong dung - khong doi
            permuted_score = pr_auc(y_train.to_numpy()[valid], permuted_oof[valid])
            importances[feat] = baseline_score - permuted_score  # duong = feature co ich (hoan vi lam giam diem)

        kept_features = [f for f, imp in importances.items() if imp > 0]
        dropped_features = [f for f, imp in importances.items() if imp <= 0]
        for f in dropped_features:
            drop_counter[f] += 1

        if len(kept_features) < 3:  # an toan: khong bao gio con qua it feature
            kept_features = sorted(importances, key=lambda f: -importances[f])[:max(3, len(candidate_features) // 2)]

        # --- Buoc 5: fit model CUOI tren outer-train, CHI voi feature giu lai ---
        final_model = M1TypedTemporalMotifModel()
        final_model.fit(X_train[kept_features], y_train, g_train)
        threshold = select_threshold(
            y_train.to_numpy()[valid],
            np.array([inner_oof_baseline[i] for i in range(len(y_train))])[valid],  # dung inner-OOF baseline (tren full feature) de chon threshold - nhat quan voi cach outer fold khac lam
            target_fpr=0.01,
        )
        prob_test = final_model.predict_proba(X_test[kept_features])
        oof_prob[test_idx] = prob_test

        y_test_arr = y_test.to_numpy()
        fold_rows.append({
            "held_out_group": held_out, "n_candidate_features": len(candidate_features),
            "n_kept": len(kept_features), "n_dropped": len(dropped_features),
            "baseline_inner_pr_auc": baseline_score, "pr_auc_outer": pr_auc(y_test_arr, prob_test),
            "kept_features": ";".join(kept_features), "dropped_features": ";".join(dropped_features),
        })
        print(f"[{fold_i}/15] held_out={held_out:32s} kept={len(kept_features)}/{len(candidate_features)} "
              f"baseline_inner_pr_auc={baseline_score:.4f} pr_auc_outer={pr_auc(y_test_arr, prob_test):.4f}", flush=True)

    valid_all = ~np.isnan(oof_prob)
    ci = bootstrap_incident_level(y.to_numpy()[valid_all], oof_prob[valid_all], groups.to_numpy()[valid_all], pr_auc, n_boot=2000)
    print(f"\nNested feature selection pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    per_inc_fs = per_incident_metric(y.to_numpy()[valid_all], oof_prob[valid_all], groups.to_numpy()[valid_all], pr_auc)
    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)
    common = sorted(set(per_inc_fs) & set(per_inc_m1))
    diffs = np.array([per_inc_fs[i] - per_inc_m1[i] for i in common])
    mean_diff, lo, hi = paired_bootstrap(diffs)
    print(f"Paired diff (FeatureSelection - M1 goc) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}]")

    if lo > 0:
        verdict = "CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed truoc khi tin day la that."
    else:
        verdict = "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc. DUNG o day, khong thu bien the khac."
    print(f"\n=== KET LUAN ===\n{verdict}")

    drop_freq_df = pd.DataFrame(
        [{"feature": f, "n_folds_dropped": c, "pct_folds_dropped": c / n_outer_folds} for f, c in drop_counter.most_common()]
    )
    print("\n=== Feature bi loai thuong xuyen nhat (qua 15 outer fold) ===")
    print(drop_freq_df.head(15).to_string(index=False))

    pd.DataFrame(fold_rows).to_csv(OUT_FOLD_TABLE, index=False)
    drop_freq_df.to_csv(OUT_DROP_FREQ, index=False)
    pd.DataFrame([{
        "model": "nested_feature_selection", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff, "paired_ci_low": lo, "paired_ci_high": hi,
    }]).to_csv(OUT_TABLE, index=False)

    md = [
        "# Nested feature selection cho M1 (permutation importance, 2026-09-22)\n",
        "\nPhuong phap: permutation importance tinh TREN INNER-CV (14 incident/outer-train) - "
        "KHONG dung RFE lap greedy vi chi phi tinh toan qua lon (xem docstring script). "
        "Giu feature co importance>0 (hoan vi lam GIAM PR-AUC inner-CV), loai feature <=0.\n",
        "\n| Model | Mean PR-AUC | 95% CI |\n|---|---|---|\n",
        "| M1 goc (moc chinh thuc, 48 cot tho -> ~39-41 cot sau loc coverage) | 0.6624 | [0.5234, 0.8864] |\n",
        f"| **M1 + nested feature selection** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (FeatureSelection - M1 goc) = {mean_diff:+.4f}, 95% CI = [{lo:+.4f}, {hi:+.4f}]**\n",
        "\n## Feature bi loai thuong xuyen nhat qua 15 outer fold\n",
        "\n| Feature | Bi loai o so fold | % fold |\n|---|---|---|\n",
    ]
    for _, r in drop_freq_df.head(15).iterrows():
        md.append(f"| {r['feature']} | {int(r['n_folds_dropped'])}/15 | {r['pct_folds_dropped']:.0%} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_FOLD_TABLE}, {OUT_DROP_FREQ}, {OUT_MD}")


if __name__ == "__main__":
    main()
