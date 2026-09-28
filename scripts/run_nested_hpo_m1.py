"""NSS 2026 - Cai thien M1 hop le, Viec 1: nested hyperparameter tuning
(bao gom ca chien luoc xu ly mat can bang lop) cho M1.

QUAN TRONG - dinh chinh mot dieu trong yeu cau: M1 hien tai KHONG PHAI
"khong co scale_pos_weight" - src/models/baselines.py da tu dong tinh
scale_pos_weight = n_neg/n_pos (rieng cho tung fold) ben trong fit(), tu
truoc gio. Diem chua tung tune la CAC GIA TRI n_estimators/max_depth/
learning_rate (co dinh) va CHIEN LUOC ap dung scale_pos_weight (luon la
"auto" = n_neg/n_pos, chua thu chien luoc khac). Script nay tune ca 2.

Thiet ke nested CV DUNG NGHIA (khong cham outer test cho toi buoc predict
cuoi):
  Voi MOI outer fold (leave-one-incident-out, 15 fold):
    outer-train = 14 incident con lai.
    Voi MOI candidate hyperparameter (7 candidate, xem CANDIDATES ben duoi,
    moi candidate doi DUNG 1 truc so voi baseline - khong phai full grid
    factorial, vi ly do chi phi tinh toan voi 15 incident):
      - Chay inner leave-one-group-out TRONG outer-train (~14 inner fold)
        voi CHINH candidate do -> gop inner-OOF prediction.
      - Diem candidate = PR-AUC pooled tren inner-OOF (chi outer-train,
        KHONG dung outer test).
    Chon candidate co diem inner-CV cao nhat cho outer fold NAY (co the
    KHAC nhau giua cac outer fold - dung chuan nested CV, khong phai loi).
    Dung LAI inner-OOF cua candidate thang de chon threshold (select_threshold,
    giong evaluate_model_nested) - khong tinh lai.
    Fit lai model CUOI voi candidate thang tren TOAN BO outer-train, du doan
    outer test (incident bi giu lai) - CHI o buoc nay outer test moi duoc dung.

Sau khi co oof_prob tong hop qua 15 outer fold: bootstrap CI muc incident
(bootstrap_incident_level, giong M1 goc) + paired bootstrap/Wilcoxon so
voi M1 goc (oof_predictions_v1.csv, mean=0.6624 - KHONG doi/ghi de).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.model_selection import LeaveOneGroupOut

from src.evaluation.metrics import false_alerts_per_1000, macro_f1, pr_auc, recall_at_fpr
from src.evaluation.nested_eval import (
    bootstrap_incident_level, dedupe_pooled_prefixes, per_incident_metric, select_threshold,
)
from src.models.baselines import M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OOF_M1_ORIGINAL_PATH = REPO_ROOT / "data" / "processed" / "oof_predictions_v1.csv"
OUT_TABLE = REPO_ROOT / "results" / "tables" / "nested_hpo_m1_2026-09-22.csv"
OUT_FOLD_TABLE = REPO_ROOT / "results" / "tables" / "nested_hpo_m1_fold_choices_2026-09-22.csv"
OUT_MD = REPO_ROOT / "results" / "reports" / "nested_hpo_m1_2026-09-22.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

# 7 candidate, MOI candidate doi DUNG 1 truc so voi baseline (candidate 0 =
# M1 hien tai het suc chinh xac) - khong phai grid factorial day du, chon de
# gioi han chi phi tinh toan (15 outer x 7 candidate x ~14 inner fit).
CANDIDATES = [
    {"name": "baseline (M1 hien tai)", "max_depth": 4, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight_strategy": "auto"},
    {"name": "depth=3", "max_depth": 3, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight_strategy": "auto"},
    {"name": "depth=6", "max_depth": 6, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight_strategy": "auto"},
    {"name": "lr=0.05,n_est=400", "max_depth": 4, "learning_rate": 0.05, "n_estimators": 400, "scale_pos_weight_strategy": "auto"},
    {"name": "lr=0.2,n_est=100", "max_depth": 4, "learning_rate": 0.2, "n_estimators": 100, "scale_pos_weight_strategy": "auto"},
    {"name": "spw=none", "max_depth": 4, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight_strategy": "none"},
    {"name": "spw=auto_sqrt", "max_depth": 4, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight_strategy": "auto_sqrt"},
]


def make_factory(cand: dict):
    def factory():
        return M1TypedTemporalMotifModel(
            max_depth=cand["max_depth"], learning_rate=cand["learning_rate"], n_estimators=cand["n_estimators"],
            scale_pos_weight_strategy=cand["scale_pos_weight_strategy"],
        )
    return factory


def inner_cv_score(factory, X_train, y_train, g_train) -> float:
    inner_logo = LeaveOneGroupOut()
    inner_oof = np.full(len(y_train), np.nan)
    for tr_idx, val_idx in inner_logo.split(X_train, y_train, groups=g_train):
        m = factory()
        m.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx], g_train.iloc[tr_idx])
        inner_oof[val_idx] = m.predict_proba(X_train.iloc[val_idx])
    valid = ~np.isnan(inner_oof)
    return pr_auc(y_train.to_numpy()[valid], inner_oof[valid]), inner_oof, valid


def main() -> None:
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    print(f"Dataset dedupe: {len(df)} dong, {len(feature_cols)} feature, {groups.nunique()} incident, "
          f"{len(CANDIDATES)} candidate hyperparameter", flush=True)

    outer_logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    oof_threshold = np.full(len(y), np.nan)
    fold_rows = []
    fold_choice_rows = []

    for fold_i, (train_idx, test_idx) in enumerate(outer_logo.split(X, y, groups=groups), start=1):
        held_out = groups.iloc[test_idx].iloc[0]
        X_train, y_train, g_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

        best_score, best_cand, best_inner_oof, best_valid = -np.inf, None, None, None
        cand_scores = []
        for cand in CANDIDATES:
            factory = make_factory(cand)
            score, inner_oof, valid = inner_cv_score(factory, X_train, y_train, g_train)
            cand_scores.append((cand["name"], score))
            if score > best_score:
                best_score, best_cand, best_inner_oof, best_valid = score, cand, inner_oof, valid

        threshold = select_threshold(y_train.to_numpy()[best_valid], best_inner_oof[best_valid], target_fpr=0.01)
        final_model = make_factory(best_cand)()
        final_model.fit(X_train, y_train, g_train)
        prob_test = final_model.predict_proba(X_test)

        oof_prob[test_idx] = prob_test
        oof_threshold[test_idx] = threshold

        y_test_arr = y_test.to_numpy()
        fold_rows.append({
            "held_out_group": held_out, "n_val_rows": len(test_idx),
            "chosen_candidate": best_cand["name"], "inner_cv_pr_auc": best_score,
            "threshold_chosen_on_inner_train_oof": threshold,
            "pr_auc": pr_auc(y_test_arr, prob_test),
            "recall_at_fpr_0.01": recall_at_fpr(y_test_arr, prob_test, max_fpr=0.01),
            "macro_f1": macro_f1(y_test_arr, prob_test, threshold=threshold),
            "false_alerts_per_1000": false_alerts_per_1000(y_test_arr, prob_test, threshold=threshold),
        })
        fold_choice_rows.append({"held_out_group": held_out, **{name: sc for name, sc in cand_scores}})
        print(f"[{fold_i}/15] held_out={held_out:32s} chosen={best_cand['name']:20s} "
              f"inner_cv_pr_auc={best_score:.4f} outer_test_pr_auc={pr_auc(y_test_arr, prob_test):.4f}", flush=True)

    valid = ~np.isnan(oof_prob)
    ci = bootstrap_incident_level(y.to_numpy()[valid], oof_prob[valid], groups.to_numpy()[valid], pr_auc, n_boot=2000)
    per_inc_new = per_incident_metric(y.to_numpy()[valid], oof_prob[valid], groups.to_numpy()[valid], pr_auc)

    oof_orig = pd.read_csv(OOF_M1_ORIGINAL_PATH)
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(oof_orig[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    assert merged_check["oof_prob_M1"].notna().all() and len(merged_check) == len(df)
    orig_per_inc = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)

    common = sorted(set(per_inc_new) & set(orig_per_inc))
    new_scores = np.array([per_inc_new[i] for i in common])
    orig_scores = np.array([orig_per_inc[i] for i in common])
    diffs = new_scores - orig_scores
    rng = np.random.default_rng(42)
    boot = np.array([diffs[rng.integers(0, len(diffs), size=len(diffs))].mean() for _ in range(2000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    mean_diff = float(diffs.mean())
    try:
        w_stat, w_p = wilcoxon(new_scores, orig_scores)
    except ValueError:
        w_stat, w_p = float("nan"), float("nan")

    print(f"\n=== M1 sau nested HPO: pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] ===")
    print(f"M1 goc (moc so sanh, KHONG doi): 0.6624 [0.5234, 0.8864]")
    print(f"Paired diff (HPO - goc) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}], Wilcoxon p={w_p}")
    ci_excludes_zero_positive = lo > 0
    if ci_excludes_zero_positive:
        verdict = "CAI THIEN CO Y NGHIA THONG KE: nested HPO giup M1 tot hon ban goc (95% CI hieu so > 0)."
    elif hi < 0:
        verdict = "TE HON CO Y NGHIA THONG KE: nested HPO lam M1 kem hon ban goc — GIU BAN GOC (0.6624), khong doi hyperparameter."
    else:
        verdict = "KHONG CAI THIEN CO Y NGHIA THONG KE: 95% CI hieu so chua 0 — nested HPO KHONG chung minh duoc tot hon ban goc voi 15 incident hien tai. Theo dung rang buoc da dat ra, DUNG o day, khong thu bien the khac de 'cuu' ket qua."
    print(f"\n=== KET LUAN ===\n{verdict}")

    pd.DataFrame(fold_rows).to_csv(OUT_TABLE, index=False)
    pd.DataFrame(fold_choice_rows).to_csv(OUT_FOLD_TABLE, index=False)

    md = [
        "# Nested hyperparameter tuning cho M1 (chay 2026-09-22)\n",
        "\n## Dinh chinh mot dieu truoc khi doc ket qua\n",
        "\nM1 hien tai (0.6624) DA tu dong tinh `scale_pos_weight = n_neg/n_pos` rieng cho tung fold "
        "ben trong `fit()` (xem `src/models/baselines.py`) - khong phai \"chua xu ly mat can bang lop\" "
        "nhu mo ta ban dau. Diem thuc su chua tune la GIA TRI CO DINH cua max_depth/learning_rate/"
        "n_estimators va CHIEN LUOC ap dung scale_pos_weight (luon la n_neg/n_pos, chua thu chien luoc khac).\n",
        f"\n## 7 candidate da thu (moi candidate doi 1 truc so voi baseline)\n",
        "\n| Candidate | max_depth | learning_rate | n_estimators | scale_pos_weight |\n|---|---|---|---|---|\n",
    ]
    for c in CANDIDATES:
        md.append(f"| {c['name']} | {c['max_depth']} | {c['learning_rate']} | {c['n_estimators']} | {c['scale_pos_weight_strategy']} |\n")
    md += [
        "\n## Ket qua\n",
        f"\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n"
        f"| M1 goc (moc, KHONG doi) | 0.6624 | [0.5234, 0.8864] |\n"
        f"| M1 sau nested HPO | {ci['point']:.4f} | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (HPO - goc) = {mean_diff:+.4f}, 95% bootstrap CI = [{lo:+.4f}, {hi:+.4f}]**\n",
        f"\nWilcoxon signed-rank: statistic={w_stat}, p-value={w_p}\n",
        "\n## Hyperparameter duoc chon o tung outer fold (co the khac nhau - dung chuan nested CV)\n",
        "\n| Incident giu lai | Candidate thang | Inner-CV PR-AUC | PR-AUC outer test |\n|---|---|---|---|\n",
    ]
    for r in fold_rows:
        md.append(f"| {r['held_out_group']} | {r['chosen_candidate']} | {r['inner_cv_pr_auc']:.4f} | {r['pr_auc']:.4f} |\n")
    md.append(f"\n## KET LUAN\n\n{verdict}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_FOLD_TABLE}, {OUT_MD}")


if __name__ == "__main__":
    main()
