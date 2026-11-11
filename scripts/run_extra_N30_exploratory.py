"""EXPLORATORY / post-hoc cho N=30 — NGOAI `analysis_plan_N30_v3.md`.

KHONG sua bat ky file dong bang (`analysis_plan_N30_v3.md`,
`configs/data_N30.yaml`, `data/processed/features_v2_N30.parquet`,
`scripts/run_evaluation_N30_v3.py`, `results/tables/evaluation_N30_*`).
Dung CUNG LOIO, CUNG seed=42, CUNG bootstrap-cap-incident (n_boot=2000)
nhu `run_evaluation_N30_v3.py`.

Buoc 0 (cong kiem tra): chay lai M1/B3 bang DUNG code/sieu tham so cu,
luu OOF, doi chieu pooled PR-AUC da dang ky (M1=0.7762, B3=0.7543,
sai so <1e-4). Khong khop -> DUNG TAT CA.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.evaluation.metrics import pr_auc
from src.evaluation.nested_eval import dedupe_pooled_prefixes, evaluate_model_nested, per_incident_metric
from src.models.baselines import B3FlatGraphRandomForest, M1TypedTemporalMotifModel

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

FEATURES_PATH = Path("data/processed/features_v2_N30.parquet")
META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
OOF_DIR = Path("results/oof")
OUT_DIR_TABLES = Path("results/tables")
OUT_DIR_REPORTS = Path("results/reports")
LOG_PATH = OUT_DIR_REPORTS / "run_extra_N30_exploratory_log.txt"

REGISTERED_POOLED = {"M1": 0.7762, "B3": 0.7543}
TOLERANCE = 1e-4

# --- Nhom feature (dung lai DUNG NHU scripts/run_ablation_t14_combined.py) ---
B3_FLAT_COLS = list(B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES)  # 14 cot
SEMANTIC_ACTION_COLS = [
    "action_count_transfer_ratio", "action_count_lending_deposit_ratio", "action_count_lending_withdraw_ratio",
    "action_count_swap_ratio", "action_count_split_ratio", "action_count_merge_ratio",
    "action_count_mixer_or_exit_ratio", "action_count_other_ratio",
    "num_distinct_bigrams", "num_distinct_trigrams", "stablecoin_pivot",
]
# MOTIF_COLS_FULL (7) tu run_ablation_t14_combined.py; 2 cot
# motif_bridge_then_swap/motif_nested_bridge nam trong
# BRIDGE_CONTEXT_COLS_EXCLUDED cua M1 (loai 2026-08-28, xem baselines.py) -
# de dam bao "flat+types+motifs" TRUNG CHINH XAC M1 (yeu cau nguoi dung),
# dung MOTIF_COLS_FOR_REPR (5 cot, loai 2 cot bridge-context) DONG NHAT cho
# CA 2 buoc "+motifs" va "+types+motifs" - giu tinh long nhau (monotonic).
MOTIF_COLS_FULL = ["motif_split", "motif_merge", "motif_peel_like_chain", "motif_bridge_then_swap",
                    "motif_swap_then_split", "motif_nested_bridge", "motif_rapid_token_pivot"]
MOTIF_COLS_FOR_REPR = ["motif_split", "motif_merge", "motif_peel_like_chain",
                        "motif_swap_then_split", "motif_rapid_token_pivot"]

M1_XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42, eval_metric="logloss")

_log_lines: list = []


def log(msg: str) -> None:
    print(msg, flush=True)
    _log_lines.append(msg)


class XGBFixedColumns:
    """Dung CHUNG cho B3' va 4 bieu dien: XGBClassifier voi DUNG sieu tham
    so/hyperparam cua M1 (xem M1_XGB_PARAMS), tren 1 danh sach cot CO DINH
    (khong tu chon dong nhu M1._candidate_columns - day la diem khac biet
    CHU DICH, vi B3'/4-bieu-dien can kiem soat CHINH XAC tap feature)."""

    def __init__(self, name: str, columns: list[str]) -> None:
        self.name = name
        self.columns = columns
        self.feature_cols_: list[str] = []

    def fit(self, X_train, y_train, groups_train=None):
        self.feature_cols_ = [c for c in self.columns if c in X_train.columns]
        y_arr = np.asarray(y_train)
        n_pos, n_neg = int((y_arr == 1).sum()), int((y_arr == 0).sum())
        spw = (n_neg / n_pos) if n_pos > 0 else 1.0
        params = dict(M1_XGB_PARAMS)
        params["scale_pos_weight"] = spw
        if _HAS_XGBOOST:
            self.model = XGBClassifier(**params)
        else:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, class_weight="balanced")
        self.model.fit(X_train[self.feature_cols_], y_train)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.feature_cols_])[:, 1]


def make_factory(name: str, columns: list[str]):
    return lambda: XGBFixedColumns(name, columns)


def joint_bootstrap_pooled_diff(y, prob_a, prob_b, groups, n_boot=2000, seed=42):
    """Bootstrap CAP INCIDENT, CUNG 1 tap incident resample moi lan cho CA
    HAI mo hinh (joint resample) - dung cho CI cua HIEU pooled PR-AUC."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    point = pr_auc(y, prob_a) - pr_auc(y, prob_b)
    diffs = []
    for _ in range(n_boot):
        sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        idx = np.concatenate([np.where(groups == g)[0] for g in sampled])
        a_score = pr_auc(y[idx], prob_a[idx])
        b_score = pr_auc(y[idx], prob_b[idx])
        if not (np.isnan(a_score) or np.isnan(b_score)):
            diffs.append(a_score - b_score)
    diffs = np.asarray(diffs)
    return {
        "point": point,
        "ci_low": float(np.percentile(diffs, 2.5)),
        "ci_high": float(np.percentile(diffs, 97.5)),
        "n_boot_valid": len(diffs),
    }


def bootstrap_pooled_single(y, prob, groups, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    point = pr_auc(y, prob)
    scores = []
    for _ in range(n_boot):
        sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        idx = np.concatenate([np.where(groups == g)[0] for g in sampled])
        s = pr_auc(y[idx], prob[idx])
        if not np.isnan(s):
            scores.append(s)
    scores = np.asarray(scores)
    return {"point": point, "ci_low": float(np.percentile(scores, 2.5)), "ci_high": float(np.percentile(scores, 97.5)),
            "n_boot_valid": len(scores)}


def run_one_model(factory, df, name) -> dict:
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    result = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
    oof = result["oof_prob"].to_numpy()
    y_arr, g_arr = y.to_numpy(), groups.to_numpy()

    oof_df = df[["source_id", "group_id", "prefix_label", "label"]].copy()
    oof_df.columns = ["incident_id", "group_id", "prefix_id", "y_true"]
    oof_df["score"] = oof
    oof_df["model"] = name
    OOF_DIR.mkdir(parents=True, exist_ok=True)
    oof_df.to_parquet(OOF_DIR / f"oof_{name}.parquet", index=False)

    pooled_boot = bootstrap_pooled_single(y_arr, oof, g_arr)
    per_inc = per_incident_metric(y_arr, oof, g_arr, pr_auc)
    macro_mean = float(np.nanmean(list(per_inc.values())))

    log(f"  [{name}] pooled PR-AUC={pooled_boot['point']:.4f} CI=[{pooled_boot['ci_low']:.4f},{pooled_boot['ci_high']:.4f}] "
        f"macro_mean={macro_mean:.4f}")
    return {"name": name, "oof": oof, "y": y_arr, "groups": g_arr, "pooled": pooled_boot,
            "per_incident": per_inc, "macro_mean": macro_mean}


def main():
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    log(f"Dataset: {len(df)} dong (dedup), {df.group_id.nunique()} group.")

    # ================= Buoc 0: cong kiem tra =================
    log("\n=== Buoc 0: cong kiem tra (chay lai M1, B3 goc) ===")
    res_m1 = run_one_model(M1TypedTemporalMotifModel, df, "M1")
    res_b3 = run_one_model(B3FlatGraphRandomForest, df, "B3")

    gate_ok = True
    for name, res in [("M1", res_m1), ("B3", res_b3)]:
        diff = abs(res["pooled"]["point"] - REGISTERED_POOLED[name])
        ok = diff < TOLERANCE
        gate_ok &= ok
        log(f"  CONG {name}: moi={res['pooled']['point']:.6f} dang_ky={REGISTERED_POOLED[name]:.4f} "
            f"|diff|={diff:.6f} {'PASS' if ok else 'FAIL'}")

    if not gate_ok:
        log("\n*** CONG KIEM TRA BUOC 0 KHONG KHOP - DUNG TAT CA ***")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("\n".join(_log_lines), encoding="utf-8")
        raise SystemExit(1)
    log("  -> CONG KIEM TRA PASS, tiep tuc.")

    # ================= Buoc 1: B3' =================
    log("\n=== Buoc 1: B3' (14 flat feature cua B3 + XGBoost/sieu tham so M1) ===")
    res_b3p = run_one_model(make_factory("B3prime", B3_FLAT_COLS), df, "B3prime")

    # ================= Buoc 2: 4 bieu dien =================
    log("\n=== Buoc 2: 4 bieu dien (cung learner XGBoost cua M1) ===")
    repr_defs = {
        "repr_flat": B3_FLAT_COLS,
        "repr_flat_types": B3_FLAT_COLS + SEMANTIC_ACTION_COLS,
        "repr_flat_motifs": B3_FLAT_COLS + MOTIF_COLS_FOR_REPR,
        "repr_flat_types_motifs": B3_FLAT_COLS + SEMANTIC_ACTION_COLS + MOTIF_COLS_FOR_REPR,
    }
    # Xac nhan repr_flat_types_motifs TRUNG CHINH XAC M1 (yeu cau nguoi dung)
    m1_cols = set(M1TypedTemporalMotifModel()._candidate_columns(df[[c for c in df.columns if c not in META_COLS]]))
    combo_cols = set(repr_defs["repr_flat_types_motifs"])
    same_as_m1 = combo_cols == m1_cols
    log(f"  Xac nhan repr_flat_types_motifs == M1._candidate_columns(): {same_as_m1} "
        f"(combo={len(combo_cols)}, M1={len(m1_cols)}, diff combo-M1={combo_cols-m1_cols}, diff M1-combo={m1_cols-combo_cols})")

    repr_results = {}
    for repr_name, cols in repr_defs.items():
        repr_results[repr_name] = run_one_model(make_factory(repr_name, cols), df, repr_name)

    # ================= Hieu M1 - X (pooled, CI joint bootstrap + macro gap + Wilcoxon) =================
    log("\n=== Hieu M1 - X (pooled PR-AUC, CI tu joint resample incident) ===")
    all_models = {"B3": res_b3, "B3prime": res_b3p, **repr_results}
    diff_rows = []
    for name, res in all_models.items():
        assert np.array_equal(res_m1["groups"], res["groups"]), f"groups khong khop giua M1 va {name}"
        jb = joint_bootstrap_pooled_diff(res_m1["y"], res_m1["oof"], res["oof"], res_m1["groups"])
        incs_common = sorted(set(res_m1["per_incident"]) & set(res["per_incident"]))
        a = np.array([res_m1["per_incident"][i] for i in incs_common])
        b = np.array([res["per_incident"][i] for i in incs_common])
        macro_gap = float((a - b).mean())
        w_stat, w_p = wilcoxon(a, b) if name in ("B3", "B3prime") else (None, None)
        log(f"  M1 - {name}: pooled_diff={jb['point']:+.4f} CI=[{jb['ci_low']:+.4f},{jb['ci_high']:+.4f}] "
            f"macro_gap={macro_gap:+.4f}" + (f" Wilcoxon p={w_p:.4f}" if w_p is not None else ""))
        diff_rows.append({"comparison": f"M1_minus_{name}", "pooled_diff": jb["point"], "ci_low": jb["ci_low"],
                           "ci_high": jb["ci_high"], "macro_gap": macro_gap,
                           "wilcoxon_p": w_p, "n_boot_valid": jb["n_boot_valid"]})

    diff_df = pd.DataFrame(diff_rows)
    OUT_DIR_TABLES.mkdir(parents=True, exist_ok=True)
    diff_df.to_csv(OUT_DIR_TABLES / "extra_N30_model_diffs.csv", index=False)

    summary_rows = []
    for name, res in all_models.items():
        summary_rows.append({"model": name, "pooled_pr_auc": res["pooled"]["point"],
                              "pooled_ci_low": res["pooled"]["ci_low"], "pooled_ci_high": res["pooled"]["ci_high"],
                              "macro_mean": res["macro_mean"]})
    summary_rows.append({"model": "M1", "pooled_pr_auc": res_m1["pooled"]["point"],
                          "pooled_ci_low": res_m1["pooled"]["ci_low"], "pooled_ci_high": res_m1["pooled"]["ci_high"],
                          "macro_mean": res_m1["macro_mean"]})
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUT_DIR_TABLES / "extra_N30_model_summary.csv", index=False)
    log(f"\nDa luu {OUT_DIR_TABLES / 'extra_N30_model_summary.csv'} va extra_N30_model_diffs.csv")

    # ================= Buoc 3: TreeSHAP cho M1 =================
    log("\n=== Buoc 3: TreeSHAP cho M1 (tren OOF-fold, model cua tung fold) ===")
    try:
        import shap
        feature_cols = [c for c in df.columns if c not in META_COLS]
        X, y, groups = df[feature_cols], df["label"], df["group_id"]
        from sklearn.model_selection import LeaveOneGroupOut
        logo = LeaveOneGroupOut()
        shap_rows = []
        for train_idx, test_idx in logo.split(X, y, groups=groups):
            m1 = M1TypedTemporalMotifModel()
            m1.fit(X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx])
            explainer = shap.TreeExplainer(m1.model)
            sv = explainer.shap_values(X.iloc[test_idx][m1.feature_cols_])
            sv = np.asarray(sv)
            if sv.ndim == 3:
                sv = sv[..., 1]
            for i, col in enumerate(m1.feature_cols_):
                for row_val in sv[:, i]:
                    shap_rows.append({"feature": col, "abs_shap": abs(float(row_val))})
        shap_df = pd.DataFrame(shap_rows)
        mean_abs = shap_df.groupby("feature")["abs_shap"].mean().sort_values(ascending=False)
        top15 = mean_abs.head(15)
        top15.to_csv(OUT_DIR_TABLES / "extra_N30_shap_top15.csv")
        log("  Top 15 (mean |SHAP|):")
        for feat, val in top15.items():
            log(f"    {feat}: {val:.6f}")

        def group_of(col):
            if col in B3_FLAT_COLS:
                return "flat"
            if col in SEMANTIC_ACTION_COLS:
                return "types"
            if col in MOTIF_COLS_FULL:
                return "motifs"
            return "other"

        shap_df["group"] = shap_df["feature"].map(group_of)
        group_mean = shap_df.groupby("group")["abs_shap"].mean().sort_values(ascending=False)
        group_mean.to_csv(OUT_DIR_TABLES / "extra_N30_shap_by_group.csv")
        log("  Theo nhom feature:")
        for g, v in group_mean.items():
            log(f"    {g}: {v:.6f}")
        shap_ran = True
    except Exception as e:
        log(f"  TreeSHAP LOI: {e}")
        shap_ran = False

    # ================= Buoc 4: S1 (GRU) - tuy chon =================
    log("\n=== Buoc 4: S1 (GRU tren chuoi typed action token) - tuy chon ===")
    s1_status = "KHONG CHAY"
    s1_reason = ""
    try:
        import torch  # noqa
        max_len = int(df_raw["trajectory_len"].max())
        s1_reason = (
            f"torch CO SAN (CPU, {torch.__version__}), nhung protocol danh gia dung NESTED LOGO "
            f"(30 outer fold x ~29 inner fold = ~870 lan fit) va co incident dai toi {max_len} token "
            f"(easyfi_2021) - uoc tinh thoi gian huan luyen GRU vuot qua ngan sach hop ly cua phien "
            f"lam viec nay (khac voi B0-B3/M1/B3'/4-bieu-dien la cay quyet dinh/boosting, fit nhanh "
            f"ke ca voi ~870 lan). KHONG thay bang mo hinh khac theo dung chi dan."
        )
    except ImportError:
        s1_reason = "torch khong cai duoc/khong co trong moi truong"
    log(f"  S1: {s1_status} - {s1_reason}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(_log_lines), encoding="utf-8")

    meta = {
        "gate_pass": gate_ok,
        "repr_flat_types_motifs_equals_M1": same_as_m1,
        "shap_ran": shap_ran,
        "s1_status": s1_status,
        "s1_reason": s1_reason,
    }
    (OUT_DIR_REPORTS / "run_extra_N30_exploratory_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log("\nHOAN TAT Buoc 0-3 (+ghi chu Buoc 4).")


if __name__ == "__main__":
    main()
