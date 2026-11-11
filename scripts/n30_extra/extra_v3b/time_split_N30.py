"""EXPLORATORY / post-hoc, NGOAI analysis_plan_N30_v3.md - chia theo thoi
gian (forward-chaining): sap incident theo first_action_timestamp THAT
(tu extract_incident_dates_N30.py, KHONG dung ngay viet tay trong ten).
Train tren 50%/60%/70% incident CU NHAT, test tren phan con lai (MOI).
Neu < 3 incident test thi BAO, KHONG ep chay.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from scripts.n30_extra.extra_v3b._common_v3b import (  # noqa: E402
    META_COLS, fit_predict, load_dataset, make_b3prime_factory, per_incident_pr_auc, pooled_pr_auc,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

DATES_CSV = ROOT / "results" / "tables" / "extra_v3b" / "incident_dates_from_cache_N30.csv"
OUT_CSV = ROOT / "results" / "tables" / "extra_v3b" / "time_split_N30.csv"
OUT_PER_INC_CSV = ROOT / "results" / "tables" / "extra_v3b" / "time_split_N30_per_incident.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_v3b" / "time_split_N30.md"

SPLITS = [0.5, 0.6, 0.7]
MODEL_FACTORIES = {"M1": M1TypedTemporalMotifModel, "B3prime": make_b3prime_factory()}


def main():
    dates = pd.read_csv(DATES_CSV)
    usable = dates[dates["first_action_timestamp"].notna()].copy()
    usable["first_action_timestamp"] = pd.to_datetime(usable["first_action_timestamp"])
    usable = usable.sort_values("first_action_timestamp").reset_index(drop=True)
    n_usable = len(usable)
    n_missing = len(dates) - n_usable
    print(f"Incident co ngay (tu cache): {n_usable}/{len(dates)} (thieu {n_missing})", flush=True)
    print(usable[["incident_id", "first_action_timestamp"]].to_string(index=False))

    df, _ = load_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    # Chi giu incident CO trong ca df (dataset chinh) VA co ngay
    ordered_ids = [i for i in usable["incident_id"] if i in set(df["group_id"].unique())]
    print(f"\nIncident dung duoc cho time-split (co trong dataset chinh): {len(ordered_ids)}")

    summary_rows = []
    per_inc_rows = []
    for frac in SPLITS:
        n_train = int(round(frac * len(ordered_ids)))
        train_ids = ordered_ids[:n_train]
        test_ids = ordered_ids[n_train:]
        print(f"\n=== Split {frac:.0%}: train={len(train_ids)} incident (cu nhat), "
              f"test={len(test_ids)} incident (moi nhat) ===", flush=True)
        if len(test_ids) < 3:
            print(f"  BAO: chi {len(test_ids)} incident test (<3) - KHONG ep chay, bo qua split nay.")
            summary_rows.append({"split_frac_train": frac, "n_train_incidents": len(train_ids),
                                  "n_test_incidents": len(test_ids), "model": None, "status": "bo_qua_qua_it_test",
                                  "pooled_pr_auc": None, "macro_mean_pr_auc": None})
            continue

        train_mask = df["group_id"].isin(train_ids)
        test_mask = df["group_id"].isin(test_ids)
        X_train, y_train, g_train = df.loc[train_mask, feature_cols], df.loc[train_mask, "label"], df.loc[train_mask, "group_id"]
        X_test, y_test, g_test = df.loc[test_mask, feature_cols], df.loc[test_mask, "label"], df.loc[test_mask, "group_id"]

        for name, factory in MODEL_FACTORIES.items():
            prob = fit_predict(factory, X_train, y_train, g_train, X_test)
            pooled = pooled_pr_auc(y_test, prob)
            per_inc = per_incident_pr_auc(y_test, prob, g_test)
            for iid, score in per_inc.items():
                per_inc_rows.append({"split_frac_train": frac, "model": name, "incident_id": iid, "pr_auc": score})
            macro = sum(per_inc.values()) / len(per_inc) if per_inc else float("nan")
            print(f"  [{name}] test incidents={list(per_inc.keys())}", flush=True)
            for iid, score in per_inc.items():
                print(f"    {iid}: pr_auc={score:.4f}")
            print(f"  [{name}] pooled={pooled:.4f} macro={macro:.4f}", flush=True)
            summary_rows.append({"split_frac_train": frac, "n_train_incidents": len(train_ids),
                                  "n_test_incidents": len(test_ids), "model": name, "status": "ok",
                                  "pooled_pr_auc": pooled, "macro_mean_pr_auc": macro})

    summary_df = pd.DataFrame(summary_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_CSV, index=False)
    pd.DataFrame(per_inc_rows).to_csv(OUT_PER_INC_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}, {OUT_PER_INC_CSV}")

    md = ["# [EXPLORATORY] Time-split (forward-chaining) N=30 — M1 vs B3'\n",
          f"\nSắp theo first_action_timestamp THẬT (từ cache, {n_usable}/{len(dates)} incident có ngày, "
          f"thiếu {n_missing}). Train trên incident CŨ NHẤT, test trên incident MỚI NHẤT.\n",
          "\n## Bảng tổng hợp\n\n", summary_df.to_string(index=False), "\n"]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
