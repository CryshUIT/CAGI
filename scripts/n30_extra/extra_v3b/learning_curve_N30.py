"""EXPLORATORY / post-hoc, NGOAI analysis_plan_N30_v3.md - duong cong hoc
(learning curve) cho M1 va B3' tren 30 incident N30.

Thiet ke (dung DUNG yeu cau da chot voi nguoi dung):
- Voi moi n trong {5,10,15,20,25,29}: lap 20 lan (seed ghi lai).
- Moi lan lap, voi MOI incident i trong 30 incident lam test: chon ngau
  nhien (khong lap lai) n incident TU 29 incident con lai (KHONG bao gom i)
  lam train. Fit M1 va B3' tren hop cac dong cua n incident do, du doan
  tren CAC DONG cua incident i.
- Tong hop CA 30 incident test trong 1 lan lap: PR-AUC POOLED (gop het
  dong) VA PR-AUC trung binh theo incident (macro).
- Qua 20 lan lap: bao cao mean/std/khoang 95% (percentile 2.5/97.5) cua
  CA 2 chi so tren, cho CA 2 model.

Train/test tach theo INCIDENT (group_id) - khong co leakage (da xac nhan
hard-negative moi incident la rieng, group_id = incident cha).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra.extra_v3b._common_v3b import (  # noqa: E402
    META_COLS, fit_predict, load_dataset, make_b3prime_factory, per_incident_pr_auc, pooled_pr_auc,
)
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

N_VALUES = [5, 10, 15, 20, 25, 29]
N_REPEATS = 20
BASE_SEED = 42000

OUT_CSV = ROOT / "results" / "tables" / "extra_v3b" / "learning_curve_N30.csv"
OUT_FIG = ROOT / "results" / "figures" / "extra_v3b" / "learning_curve_N30.png"
OUT_MD = ROOT / "results" / "reports" / "extra_v3b" / "learning_curve_N30.md"

MODEL_FACTORIES = {"M1": M1TypedTemporalMotifModel, "B3prime": make_b3prime_factory()}


def run_one_repeat(df, feature_cols, all_incidents, n, seed):
    rng = np.random.default_rng(seed)
    results = {name: {"y": [], "prob": [], "test_incident": []} for name in MODEL_FACTORIES}
    for test_inc in all_incidents:
        pool = [i for i in all_incidents if i != test_inc]
        train_incidents = rng.choice(pool, size=n, replace=False)
        train_mask = df["group_id"].isin(train_incidents)
        test_mask = df["group_id"] == test_inc
        X_train, y_train, g_train = df.loc[train_mask, feature_cols], df.loc[train_mask, "label"], df.loc[train_mask, "group_id"]
        X_test, y_test = df.loc[test_mask, feature_cols], df.loc[test_mask, "label"]
        if y_train.nunique() < 2:
            continue  # train khong co ca 2 lop (hiem, bo qua, se it hon 30 test o n nho)
        for name, factory in MODEL_FACTORIES.items():
            prob = fit_predict(factory, X_train, y_train, g_train, X_test)
            results[name]["y"].append(y_test.to_numpy())
            results[name]["prob"].append(prob)
            results[name]["test_incident"].append(np.full(len(y_test), test_inc))
    return results


def main():
    df, _ = load_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    all_incidents = sorted(df["group_id"].unique())
    assert len(all_incidents) == 30, f"Ky vong 30 incident, co {len(all_incidents)}"
    print(f"30 incident: {all_incidents}", flush=True)

    rows = []
    t_start = time.time()
    for n in N_VALUES:
        for rep in range(N_REPEATS):
            seed = BASE_SEED + rep
            res = run_one_repeat(df, feature_cols, all_incidents, n, seed)
            for name in MODEL_FACTORIES:
                y_cat = np.concatenate(res[name]["y"]) if res[name]["y"] else np.array([])
                prob_cat = np.concatenate(res[name]["prob"]) if res[name]["prob"] else np.array([])
                groups_cat = np.concatenate(res[name]["test_incident"]) if res[name]["test_incident"] else np.array([])
                n_test_incidents_used = len(res[name]["y"])
                if len(y_cat) == 0:
                    pooled, macro = float("nan"), float("nan")
                else:
                    pooled = pooled_pr_auc(y_cat, prob_cat)
                    per_inc = per_incident_pr_auc(y_cat, prob_cat, groups_cat)
                    macro = float(np.nanmean(list(per_inc.values())))
                rows.append({"model": name, "n_train_incidents": n, "repeat": rep, "seed": seed,
                             "pooled_pr_auc": pooled, "macro_mean_pr_auc": macro,
                             "n_test_incidents_used": n_test_incidents_used})
            print(f"  n={n} repeat={rep} seed={seed} xong ({time.time()-t_start:.0f}s tong)", flush=True)

    detail_df = pd.DataFrame(rows)
    detail_df.to_csv(ROOT / "results" / "tables" / "extra_v3b" / "learning_curve_N30_detail.csv", index=False)

    summary_rows = []
    for name in MODEL_FACTORIES:
        for n in N_VALUES:
            sub = detail_df[(detail_df.model == name) & (detail_df.n_train_incidents == n)]
            for metric in ["pooled_pr_auc", "macro_mean_pr_auc"]:
                vals = sub[metric].dropna().to_numpy()
                if len(vals) == 0:
                    summary_rows.append({"model": name, "n_train_incidents": n, "metric": metric,
                                          "mean": float("nan"), "std": float("nan"),
                                          "ci_low_95": float("nan"), "ci_high_95": float("nan"), "n_repeats_valid": 0})
                    continue
                summary_rows.append({
                    "model": name, "n_train_incidents": n, "metric": metric,
                    "mean": float(vals.mean()), "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                    "ci_low_95": float(np.percentile(vals, 2.5)), "ci_high_95": float(np.percentile(vals, 97.5)),
                    "n_repeats_valid": len(vals),
                })
    summary_df = pd.DataFrame(summary_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_CSV, index=False)
    print(f"\nDa luu {OUT_CSV}")
    print(summary_df.to_string(index=False))

    # --- Ve PNG ---
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = {"M1": "#4c78a8", "B3prime": "#e45756"}
    for name in MODEL_FACTORIES:
        sub = summary_df[(summary_df.model == name) & (summary_df.metric == "pooled_pr_auc")].sort_values("n_train_incidents")
        ax.plot(sub["n_train_incidents"], sub["mean"], marker="o", color=colors[name], label=f"{name} (pooled)")
        ax.fill_between(sub["n_train_incidents"], sub["ci_low_95"], sub["ci_high_95"], color=colors[name], alpha=0.15)
    ax.set_xlabel("Số incident dùng để train (n)")
    ax.set_ylabel("PR-AUC pooled (qua 20 lần lặp, dải = percentile 2.5-97.5)")
    ax.set_title("Learning curve N=30 — M1 vs B3'")
    ax.legend()
    fig.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=150)
    plt.close(fig)
    print(f"Da luu {OUT_FIG}")

    # --- Ket luan (CHI 1 trong 3 mo ta, dua tren do rong CI va xu huong n lon nhat) ---
    def classify_trend(sub):
        sub = sub.sort_values("n_train_incidents")
        last2 = sub.tail(2)
        if len(last2) < 2:
            return "khong du du lieu de ket luan"
        delta = last2["mean"].iloc[-1] - last2["mean"].iloc[0]
        ci_width_last = last2["ci_high_95"].iloc[-1] - last2["ci_low_95"].iloc[-1]
        if last2["n_repeats_valid"].min() < 10:
            return "khong du du lieu de ket luan"
        if abs(delta) > 0.5 * ci_width_last and delta > 0:
            return "con tang"
        return "chua thay tang them (trong sai so)"

    md = ["# [EXPLORATORY] Learning curve N=30 — M1 vs B3'\n",
          f"\n{N_VALUES} incident train, {N_REPEATS} lần lặp/mức, seed={BASE_SEED}..{BASE_SEED+N_REPEATS-1}.\n",
          "\n## Bảng tổng hợp\n\n", summary_df.to_string(index=False), "\n",
          "\n## Kết luận (chỉ 1 trong 3 mô tả cho phép)\n"]
    for name in MODEL_FACTORIES:
        sub = summary_df[(summary_df.model == name) & (summary_df.metric == "pooled_pr_auc")]
        verdict = classify_trend(sub)
        md.append(f"\n- **{name}** (PR-AUC pooled): {verdict}\n")
        print(f"[{name}] ket luan: {verdict}")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
