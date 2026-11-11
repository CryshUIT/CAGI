# -*- coding: utf-8 -*-
"""Sinh du lieu THAT cho dashboard (Phan 1, 36 incident historical) - chay
MOT LAN, khong phai phan dashboard runtime. Tai su dung NGUYEN VEN:
- evaluate_model_nested (src/evaluation/nested_eval.py) - DUNG ham LOIO +
  Platt + chon nguong da dung xuyen suot du an (target_fpr=0.01, seed=42).
- Mau "fold-specific model + XGBoost pred_contribs" tu
  scripts/generate_alert_case_studies.py (LeaveOneGroupOut + model.fit() +
  booster.predict(pred_contribs=True)).
- get_aadapt_ids() tu src/features/aadapt_mapping.py.

KHONG dung M1_FROZEN_final_N36.pkl/B3prime_FROZEN_final_N36.pkl (model da
thay het 36 incident) - day la OOF THAT, moi fold khong thay chinh group
cua no.

Output: data/dashboard/incidents.json (toan bo du lieu can cho frontend,
1 file duy nhat, nho gon).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import xgboost as xgb  # noqa: E402
from sklearn.model_selection import LeaveOneGroupOut  # noqa: E402

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import (  # noqa: E402
    _apply_calibrator,
    _fit_calibrator,
    dedupe_pooled_prefixes,
    select_threshold,
)
from src.features.aadapt_mapping import get_aadapt_ids  # noqa: E402
from src.models.baselines import B3FlatGraphRandomForest, M1TypedTemporalMotifModel  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "n30_extra" / "extra_v4"))
from _freeze_final_B3prime_N36 import XGBFixedColumns  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N37.parquet"
REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N37.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "data" / "dashboard"
OUT_PATH = OUT_DIR / "incidents.json"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
TARGET_FPR = 0.01
SEED = 42
TERMINAL_TYPES = {"bridge_deposit", "mixer_or_exit", "lending_deposit"}

# 36 group thuoc model dong bang final (30 N30 + 6 N37, loai
# fortress_protocol_2022 - loi thu thap that). Xem AUDIT.md muc 4.
EXCLUDED_FROM_36 = {"fortress_protocol_2022"}

B3_FLAT_COLS = list(B3FlatGraphRandomForest.FLAT_UNTYPED_FEATURES)
M1_XGB_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=SEED, eval_metric="logloss")


def get_contribs_xgb(model, row_df, feature_cols) -> pd.Series:
    booster = model.model.get_booster()
    dmat = xgb.DMatrix(row_df[feature_cols])
    contribs = booster.predict(dmat, pred_contribs=True)[0]
    return pd.Series(contribs, index=feature_cols + ["bias"])


def run_loio_with_shap(df, feature_cols, model_factory, model_name):
    """LeaveOneGroupOut GIONG HET evaluate_model_nested (cung logic chon
    nguong tren inner-train OOF, cung Platt) NHUNG giu lai model moi fold
    de tinh SHAP cho dong test. Khong doi logic cot loi."""
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    oof_prob_cal = np.full(len(y), np.nan)
    shap_rows = {}  # idx -> Series contribs

    for fold_i, (train_idx, test_idx) in enumerate(logo.split(X, y, groups=groups)):
        X_train, y_train, g_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        X_test = X.iloc[test_idx]

        inner_logo = LeaveOneGroupOut()
        inner_oof = np.full(len(y_train), np.nan)
        y_train_arr = y_train.to_numpy()
        for inner_tr, inner_val in inner_logo.split(X_train, y_train, groups=g_train):
            m = model_factory()
            m.fit(X_train.iloc[inner_tr], y_train.iloc[inner_tr], g_train.iloc[inner_tr])
            inner_oof[inner_val] = m.predict_proba(X_train.iloc[inner_val])
        valid = ~np.isnan(inner_oof)
        cal = _fit_calibrator(y_train_arr[valid], inner_oof[valid], "platt")

        final_model = model_factory()
        final_model.fit(X_train, y_train, g_train)
        prob_test = final_model.predict_proba(X_test)
        prob_test_cal = _apply_calibrator(cal, prob_test, "platt")
        oof_prob[test_idx] = prob_test
        oof_prob_cal[test_idx] = prob_test_cal

        model_feat_cols = getattr(final_model, "feature_cols_", feature_cols)
        for local_i, global_i in enumerate(test_idx):
            try:
                contribs = get_contribs_xgb(final_model, X_test.iloc[[local_i]], model_feat_cols)
            except Exception:
                contribs = None
            shap_rows[global_i] = contribs
        print(f"  [{model_name}] fold {fold_i + 1}/{groups.nunique()} xong (held_out={groups.iloc[test_idx].iloc[0]})", flush=True)

    valid_all = ~np.isnan(oof_prob)
    theta = select_threshold(y.to_numpy()[valid_all], oof_prob[valid_all], target_fpr=TARGET_FPR)
    return oof_prob, oof_prob_cal, shap_rows, theta


def find_e_star(events: list):
    for i, a in enumerate(events):
        if a["event_type"] in TERMINAL_TYPES:
            return i + 1, a["event_type"], a.get("protocol")
    return None, None, None


def classify_outcome(e_star, alert_k, endpoint_confirmed):
    if not endpoint_confirmed or e_star is None:
        return "not_evaluable"
    if e_star <= 2:
        return "not_feasible"
    if alert_k is None:
        return "no_alert"
    if alert_k < e_star:
        return "early"
    return "late"


def main():
    import pickle
    CACHE_PATH = OUT_DIR / "_loio_shap_cache.pkl"
    reg = pd.read_csv(REGISTRY_PATH)
    reg_by_id = reg.set_index("incident_id").to_dict("index")
    primary_ids = set(reg[reg.eval_tier == "primary"].incident_id)
    v4_ids = set(reg[reg.eval_tier == "v4_heldout"].incident_id) - EXCLUDED_FROM_36
    group_ids_36 = primary_ids | v4_ids

    if CACHE_PATH.exists():
        print(f"=== Doc cache LOIO+SHAP da co san ({CACHE_PATH}) - BO QUA tinh lai ===", flush=True)
        with open(CACHE_PATH, "rb") as f:
            cache = pickle.load(f)
        df = cache["df"]
        m1_shap, b3_shap = cache["m1_shap"], cache["b3_shap"]
        m1_theta, b3_theta = cache["m1_theta"], cache["b3_theta"]
        pooled_pr_auc_m1, pooled_pr_auc_b3 = cache["pooled_pr_auc_m1"], cache["pooled_pr_auc_b3"]
    else:
        print("=== Nap features_v2_N37.parquet, dedupe ===", flush=True)
        df_raw = pd.read_parquet(FEATURES_PATH)
        df = dedupe_pooled_prefixes(df_raw)
        df = df[df["group_id"].isin(group_ids_36)].reset_index(drop=True)
        feature_cols = [c for c in df.columns if c not in META_COLS]
        n_groups = df["group_id"].nunique()
        print(f"Tong {len(df)} dong, {n_groups} group (ky vong 36)", flush=True)
        assert n_groups == 36, f"Ky vong 36 group, co {n_groups}: {sorted(group_ids_36)}"

        print("\n=== LOIO + SHAP cho M1 ===", flush=True)
        m1_oof, m1_oof_cal, m1_shap, m1_theta = run_loio_with_shap(
            df, feature_cols, lambda: M1TypedTemporalMotifModel(), "M1",
        )
        print(f"M1 theta (out-of-fold, target_fpr={TARGET_FPR}) = {m1_theta:.6f}", flush=True)

        print("\n=== LOIO + SHAP cho B3prime ===", flush=True)
        b3_oof, b3_oof_cal, b3_shap, b3_theta = run_loio_with_shap(
            df, feature_cols, lambda: XGBFixedColumns("B3prime", B3_FLAT_COLS), "B3prime",
        )
        print(f"B3prime theta (out-of-fold, target_fpr={TARGET_FPR}) = {b3_theta:.6f}", flush=True)

        valid = (~np.isnan(m1_oof))
        pooled_pr_auc_m1 = pr_auc(df["label"].to_numpy()[valid], m1_oof[valid])
        pooled_pr_auc_b3 = pr_auc(df["label"].to_numpy()[valid], b3_oof[valid])
        print(f"\nPooled PR-AUC (36 group, OOF): M1={pooled_pr_auc_m1:.4f} B3'={pooled_pr_auc_b3:.4f}", flush=True)

        df = df.copy()
        df["m1_oof_raw"] = m1_oof
        df["m1_oof_cal"] = m1_oof_cal
        df["b3_oof_raw"] = b3_oof
        df["b3_oof_cal"] = b3_oof_cal

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "wb") as f:
            pickle.dump({
                "df": df, "m1_shap": m1_shap, "b3_shap": b3_shap,
                "m1_theta": m1_theta, "b3_theta": b3_theta,
                "pooled_pr_auc_m1": pooled_pr_auc_m1, "pooled_pr_auc_b3": pooled_pr_auc_b3,
            }, f)
        print(f"Da cache LOIO+SHAP vao {CACHE_PATH}", flush=True)

    incidents_out = {}
    for group_id in sorted(group_ids_36):
        # QUAN TRONG: loc THEO source_id==group_id (chinh trajectory
        # positive), KHONG PHAI chi group_id - 1 group chua CA positive
        # LAN moi hard-negative da mine (source_id rieng, vd
        # "bsc_token_hub_2022__hn001") dung CHUNG group_id voi incident
        # goc. Loc sai se GOP du lieu cua hang chuc hard-negative khac
        # nhau vao p_k chart cua 1 incident (bug THAT da phat hien khi
        # smoke-test bsc_token_hub_2022 - xem PROGRESS.md).
        sub = df[(df["group_id"] == group_id) & (df["source_id"] == group_id) & (df["kind"] == "positive")].sort_values("prefix_len")
        if sub.empty:
            continue
        reg_row = reg_by_id.get(group_id, {})
        chain = sub["chain"].iloc[0]
        kind0 = sub["kind"].iloc[0]

        events_path = PROCESSED_DIR / f"{group_id}_events.json"
        events = json.loads(events_path.read_text(encoding="utf-8")) if events_path.exists() else []
        events_sorted = sorted(events, key=lambda a: a["timestamp"])
        e_star, e_star_type, e_star_protocol = find_e_star(events_sorted)
        endpoint_confirmed = bool(reg_row.get("endpoint_confirmed", False))

        prefix_points = []
        for _, row in sub.iterrows():
            idx = row.name
            m1_contribs = m1_shap.get(idx)
            b3_contribs = b3_shap.get(idx)

            def top3(contribs):
                if contribs is None:
                    return []
                c = contribs.drop("bias", errors="ignore")
                top = c.reindex(c.abs().sort_values(ascending=False).index[:3])
                out = []
                for feat, val in top.items():
                    out.append({
                        "feature": feat,
                        "contribution": round(float(val), 4),
                        "feature_value": round(float(row[feat]), 4) if feat in row.index else None,
                        "aadapt_ids": get_aadapt_ids(feat),
                    })
                return out

            prefix_points.append({
                "prefix_label": row["prefix_label"],
                "k": int(row["prefix_len"]),
                "m1_raw": round(float(row["m1_oof_raw"]), 4) if pd.notna(row["m1_oof_raw"]) else None,
                "m1_cal": round(float(row["m1_oof_cal"]), 4) if pd.notna(row["m1_oof_cal"]) else None,
                "b3_raw": round(float(row["b3_oof_raw"]), 4) if pd.notna(row["b3_oof_raw"]) else None,
                "b3_cal": round(float(row["b3_oof_cal"]), 4) if pd.notna(row["b3_oof_cal"]) else None,
                "m1_top_shap": top3(m1_contribs),
                "b3_top_shap": top3(b3_contribs),
            })

        actions_out = []
        for i, a in enumerate(events_sorted):
            actions_out.append({
                "idx": i + 1,
                "event_type": a["event_type"],
                "timestamp": a["timestamp"],
                "src": a["src"], "dst": a["dst"],
                "src_short": (a["src"][:8] + "...") if isinstance(a.get("src"), str) else a.get("src"),
                "dst_short": (a["dst"][:8] + "...") if isinstance(a.get("dst"), str) else a.get("dst"),
                "token": a.get("token"),
                "amount_norm": a.get("amount_norm"),
                "tx_hash": a.get("tx_hash"),
                "protocol": a.get("protocol"),
            })

        incidents_out[group_id] = {
            "incident_id": group_id,
            "name": reg_row.get("name", group_id),
            "chain": reg_row.get("chain_primary", chain),
            "seed_address": reg_row.get("seed_address"),
            "start_block": reg_row.get("start_block"),
            "endpoint_confirmed": endpoint_confirmed,
            "endpoint_type": reg_row.get("endpoint_type"),
            "e_star": e_star,
            "e_star_action_type": e_star_type,
            "e_star_protocol": e_star_protocol,
            "n_actions_total": len(events_sorted),
            "kind": kind0,
            "label": int(sub["label"].iloc[0]),
            "source_report": reg_row.get("source_report"),
            "source_url": reg_row.get("source_url"),
            "prefix_points": prefix_points,
            "actions": actions_out,
        }

    meta_out = {
        "n_incidents": len(incidents_out),
        "m1_theta_oof": round(float(m1_theta), 6),
        "b3_theta_oof": round(float(b3_theta), 6),
        "pooled_pr_auc_m1": round(float(pooled_pr_auc_m1), 4),
        "pooled_pr_auc_b3": round(float(pooled_pr_auc_b3), 4),
        "target_fpr": TARGET_FPR,
        "seed": SEED,
        "generated_note": (
            "Du lieu OOF (leave-one-incident-out) THAT, sinh boi "
            "scripts/dashboard/generate_oof_dashboard_data.py, tai su dung "
            "evaluate_model_nested/select_threshold (src/evaluation/nested_eval.py) "
            "va mau fold-specific pred_contribs tu scripts/generate_alert_case_studies.py. "
            "KHONG dung model da dong bang (da thay 36 incident nay)."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({"meta": meta_out, "incidents": incidents_out}, indent=2, default=str), encoding="utf-8")
    print(f"\nDa luu {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    main()
