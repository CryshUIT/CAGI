"""EXPLORATORY / post-hoc, NGOAI analysis_plan_N30_v3.md - leave-one-chain-out:
lan luot giu ETH/BSC/Arbitrum lam test, train tren 2 chain con lai. So
sanh M1 vs B3' va doi chieu voi LOIO v3 (goc, tung incident rieng) CUA
RIENG chain do (da co san trong evaluation_N30_by_chain_table.csv - do
LA PR-AUC pooled CUA CAC INCIDENT thuoc chain do khi NGUOI MOI incident do
la outer-test rieng le, KHAC voi phep nay la CA CHAIN lam outer-test cung
luc, cho thay tac dong cua mat toan bo du lieu "giong" (cung chain) khoi
tap train).
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

OUT_CSV = ROOT / "results" / "tables" / "extra_v3b" / "leave_one_chain_out_N30.csv"
OUT_PER_INC_CSV = ROOT / "results" / "tables" / "extra_v3b" / "leave_one_chain_out_N30_per_incident.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_v3b" / "leave_one_chain_out_N30.md"
V3_BY_CHAIN = ROOT / "results" / "tables" / "evaluation_N30_by_chain_table.csv"

MODEL_FACTORIES = {"M1": M1TypedTemporalMotifModel, "B3prime": make_b3prime_factory()}


def main():
    df, chain_map = load_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    df = df.copy()
    df["chain_of_incident"] = df["group_id"].map(chain_map)
    chains = sorted(df["chain_of_incident"].dropna().unique())
    print(f"Chain co trong N30: {chains}", flush=True)

    v3_by_chain = pd.read_csv(V3_BY_CHAIN).set_index("chain")

    rows = []
    per_inc_rows = []
    for chain in chains:
        test_mask = df["chain_of_incident"] == chain
        train_mask = ~test_mask
        X_train, y_train, g_train = df.loc[train_mask, feature_cols], df.loc[train_mask, "label"], df.loc[train_mask, "group_id"]
        X_test, y_test, g_test = df.loc[test_mask, feature_cols], df.loc[test_mask, "label"], df.loc[test_mask, "group_id"]

        n_incident_test = g_test.nunique()
        n_rows_test = len(X_test)
        pct_positive_test = float((y_test == 1).mean())
        print(f"\n=== Test chain={chain}: {n_incident_test} incident, {n_rows_test} dong, "
              f"%positive={pct_positive_test:.2%} ===", flush=True)

        for name, factory in MODEL_FACTORIES.items():
            prob = fit_predict(factory, X_train, y_train, g_train, X_test)
            pooled = pooled_pr_auc(y_test, prob)
            per_inc = per_incident_pr_auc(y_test, prob, g_test)
            for iid, score in per_inc.items():
                per_inc_rows.append({"chain_test": chain, "model": name, "incident_id": iid, "pr_auc": score})
            macro = sum(per_inc.values()) / len(per_inc) if per_inc else float("nan")

            # v3_by_chain chi co cot M1_pr_auc_pooled/B3_pr_auc_pooled (goc), KHONG co B3prime
            v3_ref_col = f"{name}_pr_auc_pooled" if f"{name}_pr_auc_pooled" in v3_by_chain.columns else None
            v3_ref = float(v3_by_chain.loc[chain, v3_ref_col]) if v3_ref_col else None

            print(f"  [{name}] LOCO pooled={pooled:.4f} macro={macro:.4f} | "
                  f"LOIO v3 (riêng chain, nếu có) = {v3_ref}", flush=True)
            rows.append({
                "chain_test": chain, "model": name, "n_incident_test": n_incident_test,
                "n_rows_test": n_rows_test, "pct_positive_test": pct_positive_test,
                "loco_pooled_pr_auc": pooled, "loco_macro_mean_pr_auc": macro,
                "loio_v3_pooled_pr_auc_same_chain": v3_ref,
                "degradation_vs_loio_v3": (pooled - v3_ref) if v3_ref is not None else None,
            })

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    pd.DataFrame(per_inc_rows).to_csv(OUT_PER_INC_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}, {OUT_PER_INC_CSV}")
    print(out.to_string(index=False))

    md = ["# [EXPLORATORY] Leave-one-chain-out N=30 — M1 vs B3'\n",
          "\nTrain trên 2 chain, test trên TOÀN BỘ incident của chain còn lại (khác LOIO v3 - "
          "nơi mỗi incident là outer-test RIÊNG LẺ, vẫn còn incident CÙNG CHAIN trong train).\n",
          "\n## Bảng tổng hợp\n\n", out.to_string(index=False), "\n"]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
