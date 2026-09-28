"""Script CHAY 1 LAN (khong phai phan cua demo web) - trich xuat du lieu
THAT da co san trong repo thanh demo/data.json gon nhe, dung cho trang demo
replay tinh (HTML/CSS/JS thuan, khong backend).

Case duoc chon:
- Positive: chibi_finance_2023 (40 action) - da la case study chinh cho
  RQ2/Fig.4 (endpoint_confirmed=True, lead time that da tinh san trong
  results/tables/lead_time_results.csv, risk curve that trong
  data/processed/rq2_oof_predictions.csv).
- Hard-negative: chibi_finance_2023__hn004 (8 action, cung group, luon
  duoi threshold ca 8 moc prefix, max_prob=0.008) - hard-negative DA MINE
  chinh thuc (metadata/hard_negative_registry.csv), khong phai du lieu bia.

SHAP (XGBoost pred_contribs) cho case positive tai moc alert (k_2) duoc
tinh MOI o day, dung DUNG phuong phap da dung trong
scripts/generate_alert_case_studies.py (model fold-specific, KHONG dung
model final de tranh leak) - khong goi API on-chain nao, chi doc lai
features_v2.parquet + cache da co san.

Dia chi vi rut gon con 6 ky tu dau + "..." o moi noi - dung quy uoc da ap
dung cho Fig.2/Fig.4 cua de tai.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OOF_PATH = REPO_ROOT / "data" / "processed" / "rq2_oof_predictions.csv"
LEAD_TIME_PATH = REPO_ROOT / "results" / "tables" / "lead_time_results.csv"
REGISTRY_PATH = REPO_ROOT / "metadata" / "incident_registry.csv"
HN_REGISTRY_PATH = REPO_ROOT / "metadata" / "hard_negative_registry.csv"
POS_EVENTS_PATH = REPO_ROOT / "data" / "processed" / "chibi_finance_2023_events.json"
OUT_PATH = REPO_ROOT / "demo" / "data.js"
# LUU Y: xuat ra .js (khong phai .json thuan) va gan vao bien global
# DEMO_DATA, KHONG dung fetch() de nap - Chrome (va nhieu trinh duyet)
# CHAN fetch() doc file local qua file:// vi CORS, se lam demo KHONG chay
# duoc khi giam khao chi mo truc tiep index.html (khong qua server). Nhung
# <script src="data.js"> load binh thuong nhu moi file JS tinh khac.

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

POSITIVE_ID = "chibi_finance_2023"
NEGATIVE_ID = "chibi_finance_2023__hn004"


def short(addr: str) -> str:
    return addr[:8] + "..." if isinstance(addr, str) and addr.startswith("0x") else addr


def load_events_positive() -> list:
    events = json.loads(POS_EVENTS_PATH.read_text(encoding="utf-8"))
    return sorted(events, key=lambda a: a["timestamp"])


def load_events_hard_negative(hn_id: str) -> list:
    hn_df = pd.read_csv(HN_REGISTRY_PATH)
    row = hn_df[hn_df["hard_negative_id"] == hn_id].iloc[0]
    config = load_trajectory_config()
    traj, _, _ = expand_and_build_trajectory(
        row["chain"], row["seed_address"], int(row["start_block"]), row["parent_incident_id"], 0,
        config=config, do_collect=False, max_iterations=2,
    )
    events = [json.loads(a.model_dump_json()) for a in traj.actions]
    return sorted(events, key=lambda a: a["timestamp"])


def to_relative_actions(events: list) -> list:
    """Chuyen list event tho -> list gon cho demo: loai action, thoi gian
    tuong doi (gio, tinh tu action dau tien), dia chi rut gon + day du,
    tx_hash that, va amount THAT phuc hoi tu amount_norm (log-scale) bang
    expm1 - DUNG QUY UOC da dung san trong src/features/extractor.py
    (raw_v = math.expm1(abs(a.amount_norm))), khong phai gia tri bia."""
    if not events:
        return []
    t0 = pd.Timestamp(events[0]["timestamp"])
    out = []
    for e in events:
        dt_h = (pd.Timestamp(e["timestamp"]) - t0).total_seconds() / 3600.0
        amount_norm = e.get("amount_norm")
        amount = round(math.expm1(abs(amount_norm)), 6) if amount_norm is not None else None
        out.append({
            "event_type": e["event_type"],
            "rel_hours": round(dt_h, 3),
            "src": short(e["src"]),
            "dst": short(e["dst"]),
            "src_full": e["src"],
            "dst_full": e["dst"],
            "token": e.get("token"),
            "amount": amount,
            "tx_hash": e.get("tx_hash"),
        })
    return out


def fit_fold_model(df: pd.DataFrame, feature_cols: list, held_out_group: str, prefix_label: str):
    bucket_df = df[df["prefix_label"] == prefix_label]
    train = bucket_df[bucket_df["group_id"] != held_out_group]
    model = M1TypedTemporalMotifModel()
    model.fit(train[feature_cols], train["label"], train["group_id"])
    return model


def get_contribs(model, row_df: pd.DataFrame) -> pd.Series:
    import xgboost as xgb
    booster = model.model.get_booster()
    dmat = xgb.DMatrix(row_df[model.feature_cols_])
    contribs = booster.predict(dmat, pred_contribs=True)[0]
    feature_names = model.feature_cols_ + ["bias"]
    return pd.Series(contribs, index=feature_names)


def build_prefix_checkpoints(oof_df: pd.DataFrame, source_id: str, group_id: str) -> list:
    sub = oof_df[(oof_df["source_id"] == source_id) & (oof_df["group_id"] == group_id)].copy()
    sub = sub.sort_values("prefix_len")
    return [
        {
            "prefix_label": r["prefix_label"],
            "prefix_len": int(r["prefix_len"]),
            "oof_prob": round(float(r["oof_prob"]), 4),
            "oof_threshold": round(float(r["oof_threshold"]), 4),
        }
        for _, r in sub.iterrows()
    ]


def main() -> None:
    print("=== Nap features_v2.parquet + rq2_oof_predictions.csv ===")
    df = pd.read_parquet(FEATURES_PATH)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    oof_df = pd.read_csv(OOF_PATH)
    lead_time_df = pd.read_csv(LEAD_TIME_PATH)
    registry_df = pd.read_csv(REGISTRY_PATH)

    # ---- Case positive: chibi_finance_2023 ----
    pos_events_raw = load_events_positive()
    pos_actions = to_relative_actions(pos_events_raw)
    pos_checkpoints = build_prefix_checkpoints(oof_df, POSITIVE_ID, POSITIVE_ID)

    lt_row = lead_time_df[lead_time_df["incident_id"] == POSITIVE_ID].iloc[0]
    reg_row = registry_df[registry_df["incident_id"] == POSITIVE_ID].iloc[0]

    alert_prefix_len = int(lt_row["alert_prefix_len"])
    alert_bucket = lt_row["alert_prefix_bucket"]
    te = pd.Timestamp(lt_row["te"])
    te_action_type = lt_row["te_action_type"]
    t0_pos = pd.Timestamp(pos_events_raw[0]["timestamp"])
    te_idx = None
    for i, e in enumerate(pos_events_raw, start=1):
        if pd.Timestamp(e["timestamp"]) == te and e["event_type"] == te_action_type:
            te_idx = i
            break
    assert te_idx is not None, "khong tim thay dung action endpoint trong trajectory - kiem tra lai"
    endpoint_rel_hours = round((te - t0_pos).total_seconds() / 3600.0, 3)

    print(f"positive: {len(pos_actions)} action, alert={alert_bucket} (len={alert_prefix_len}), "
          f"endpoint action #{te_idx} ({te_action_type})")

    # ---- SHAP tai moc alert (k_2, prefix_len=2) - tinh MOI, dung fold-specific model ----
    sub_row = df[
        (df["group_id"] == POSITIVE_ID) & (df["source_id"] == POSITIVE_ID) &
        (df["prefix_label"] == alert_bucket) & (df["prefix_len"] == alert_prefix_len)
    ]
    assert len(sub_row) == 1, f"khong tim thay dung 1 dong feature cho alert prefix: {len(sub_row)}"
    fold_model = fit_fold_model(df, feature_cols, POSITIVE_ID, alert_bucket)
    prob_check = fold_model.predict_proba(sub_row[feature_cols])[0]
    oof_at_alert = oof_df[
        (oof_df["group_id"] == POSITIVE_ID) & (oof_df["source_id"] == POSITIVE_ID) &
        (oof_df["prefix_label"] == alert_bucket)
    ].iloc[0]
    assert abs(prob_check - oof_at_alert["oof_prob"]) < 1e-6, "prob tinh lai KHONG khop OOF da freeze!"

    contribs = get_contribs(fold_model, sub_row)
    top_features_s = contribs.drop("bias").abs().sort_values(ascending=False).head(5)
    motif_contribs = contribs[[c for c in contribs.index if c.startswith("motif_")]]
    top_motifs_s = motif_contribs.abs().sort_values(ascending=False).head(3)

    row0 = sub_row.iloc[0]
    top_features = [
        {"feature": feat, "value": round(float(row0[feat]), 4), "contribution": round(float(contribs[feat]), 4)}
        for feat in top_features_s.index
    ]
    top_motifs = [
        {"feature": feat, "value": round(float(row0[feat]), 4), "contribution": round(float(contribs[feat]), 4)}
        for feat in top_motifs_s.index if abs(contribs[feat]) > 0
    ]
    print("Top feature (SHAP, |value| giam dan):", [f["feature"] for f in top_features])
    print("Top motif (SHAP, |value| giam dan):", [f["feature"] for f in top_motifs])

    positive_case = {
        "id": POSITIVE_ID,
        "label": "Positive (vụ tấn công thật)",
        "name": reg_row["name"],
        "chain": "Arbitrum",
        "source_report": reg_row["source_report"],
        "actions": pos_actions,
        "prefix_checkpoints": pos_checkpoints,
        "alert": {
            "prefix_len": alert_prefix_len,
            "prefix_label": alert_bucket,
            "oof_prob": round(float(oof_at_alert["oof_prob"]), 4),
            "oof_threshold": round(float(oof_at_alert["oof_threshold"]), 4),
        },
        "endpoint": {
            "action_index": te_idx,
            "action_type": te_action_type,
            "rel_hours": endpoint_rel_hours,
        },
        "lead_time": {
            "lead_time_sec": float(lt_row["lead_time_sec"]),
            "lead_time_min": round(float(lt_row["lead_time_sec"]) / 60.0, 2),
            "lead_steps": int(lt_row["lead_steps"]),
        },
        "top_features": top_features,
        "top_motifs": top_motifs,
    }

    # ---- Case hard-negative: chibi_finance_2023__hn004 ----
    neg_events_raw = load_events_hard_negative(NEGATIVE_ID)
    neg_actions = to_relative_actions(neg_events_raw)
    neg_checkpoints = build_prefix_checkpoints(oof_df, NEGATIVE_ID, POSITIVE_ID)
    print(f"hard-negative: {len(neg_actions)} action, max oof_prob="
          f"{max(c['oof_prob'] for c in neg_checkpoints):.4f} (luon duoi threshold)")

    negative_case = {
        "id": NEGATIVE_ID,
        "label": "Hard-negative (ví không liên quan tấn công)",
        "name": "Hard-negative đã mine (band-matched theo chính vụ chibi_finance_2023)",
        "chain": "Arbitrum",
        "source_report": "Mined tự động qua contract Stargate (LayerZero) đã verify — xem metadata/hard_negative_registry.csv",
        "actions": neg_actions,
        "prefix_checkpoints": neg_checkpoints,
        "alert": None,
        "endpoint": None,
        "lead_time": None,
        "top_features": [],
        "top_motifs": [],
    }

    out = {
        "generated_note": (
            "Du lieu trich xuat THAT tu features_v2.parquet / rq2_oof_predictions.csv / "
            "lead_time_results.csv / hard_negative_registry.csv (freeze v2.0, N=15 incident, "
            "M1 khong bridge_context). SHAP cho case positive tinh moi bang XGBoost pred_contribs "
            "tren model fold-specific (khop chinh xac OOF da freeze, sai so <1e-6)."
        ),
        "cases": {"positive": positive_case, "hard_negative": negative_case},
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    js_content = (
        "// File TU DONG SINH boi scripts/build_demo_data.py - KHONG sua tay.\n"
        "// Du lieu THAT trich xuat tu ket qua da freeze (xem generated_note ben duoi).\n"
        "const DEMO_DATA = " + json.dumps(out, indent=2, ensure_ascii=False) + ";\n"
    )
    OUT_PATH.write_text(js_content, encoding="utf-8")
    print(f"\nDa luu {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
