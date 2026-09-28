"""NSS 2026 - Nang cap M1 (LAN THU 6), gia thuyet: trajectory dai (nhieu
dong prefix sau dedupe, vd ronin_bridge_2022) dong gop nhieu sample hon han
trajectory ngan (vd feg_bridge_2024), khien model hoc lech ve dac diem
trajectory dai.

Trong so "moi trajectory dong gop cong bang": voi MOI dong prefix, weight =
1 / (so dong prefix con lai SAU DEDUPE cua CHINH trajectory (source_id) do)
- tong trong so moi trajectory = 1, khong doi theo tung outer fold (vi mot
trajectory hoac o TRON VEN trong outer-train hoac TRON VEN bi giu lai lam
outer-test, khong bao gio bi cat doi) - tinh 1 lan cho toan bo dataset dedupe
la hop le, khong ro ri outer test (gia tri weight cua 1 trajectory CHI phu
thuoc so dong cua CHINH no, khong phu thuoc cac trajectory khac trong fold nao).

NHAN (khong thay the) voi scale_pos_weight da co san trong M1.fit() - dung
tham so sample_weight MOI them (them 2026-09-22, backward-compatible,
mac dinh None giu nguyen hanh vi cu cho MOI noi goi khac).
"""
from __future__ import annotations

import sys
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
OUT_TABLE = ROOT / "results" / "tables" / "trajectory_fair_weight_2026-09-22.csv"
OUT_FOLD_TABLE = ROOT / "results" / "tables" / "trajectory_fair_weight_folds_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "trajectory_fair_weight_2026-09-22.md"

# Incident NGAN (theo do dai trajectory duong that, da xac nhan trong T17/hackerdao
# investigation session nay) - de xem giai thuyet co tac dong ro nhat o day khong.
SHORT_INCIDENTS = {"feg_bridge_2024": 9, "wooppv2_2024": 16, "new_free_dao_2022": 12,
                    "deltaprime_arbitrum_2024": 23, "hackerdao_2022": 35, "utopiasphere_2024": 37,
                    "chibi_finance_2023": 40}
LONG_INCIDENTS = {"xkingdom_2024": 73, "magic_abracadabra_arbitrum_2025": 88, "wault_finance_2021": 190,
                   "radiant_capital_arbitrum_2024": 248, "bsc_token_hub_2022": 362, "paraluni_2022": 511,
                   "qbridge_qubit_2022": 698, "ronin_bridge_2022": 1625}


def paired_bootstrap(diffs: np.ndarray, n_boot: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.array([diffs[rng.integers(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(diffs.mean()), float(lo), float(hi)


def evaluate_with_weight(X, y, groups, sample_weight, target_fpr=0.01):
    outer_logo = LeaveOneGroupOut()
    oof_prob = np.full(len(y), np.nan)
    fold_rows = []
    for train_idx, test_idx in outer_logo.split(X, y, groups=groups):
        held_out = groups.iloc[test_idx].iloc[0]
        X_train, y_train, g_train = X.iloc[train_idx], y.iloc[train_idx], groups.iloc[train_idx]
        w_train = sample_weight.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

        inner_logo = LeaveOneGroupOut()
        inner_oof = np.full(len(y_train), np.nan)
        for inner_tr_idx, inner_val_idx in inner_logo.split(X_train, y_train, groups=g_train):
            m = M1TypedTemporalMotifModel()
            m.fit(X_train.iloc[inner_tr_idx], y_train.iloc[inner_tr_idx], g_train.iloc[inner_tr_idx],
                  sample_weight=w_train.iloc[inner_tr_idx].to_numpy())
            inner_oof[inner_val_idx] = m.predict_proba(X_train.iloc[inner_val_idx])
        valid = ~np.isnan(inner_oof)
        threshold = select_threshold(y_train.to_numpy()[valid], inner_oof[valid], target_fpr=target_fpr)

        final_model = M1TypedTemporalMotifModel()
        final_model.fit(X_train, y_train, g_train, sample_weight=w_train.to_numpy())
        prob_test = final_model.predict_proba(X_test)
        oof_prob[test_idx] = prob_test

        y_test_arr = y_test.to_numpy()
        fold_rows.append({"held_out_group": held_out, "n_val_rows": len(test_idx),
                           "threshold": threshold, "pr_auc": pr_auc(y_test_arr, prob_test)})
        print(f"  held_out={held_out:32s} pr_auc={pr_auc(y_test_arr, prob_test):.4f}", flush=True)
    return oof_prob, fold_rows


def main():
    df_raw = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]

    # --- trong so "moi trajectory cong bang": 1 / so dong CUA CHINH source_id do (sau dedupe) ---
    rows_per_traj = df.groupby("source_id")["source_id"].transform("count")
    sample_weight = 1.0 / rows_per_traj
    print(f"So trajectory (source_id) khac nhau: {df['source_id'].nunique()}")
    print(f"Phan phoi so dong/trajectory: min={rows_per_traj.min()} max={rows_per_traj.max()} "
          f"median={rows_per_traj.median()}")
    # xac nhan tong trong so moi trajectory = 1 (kiem tra nhanh)
    check = df.assign(w=sample_weight).groupby("source_id")["w"].sum()
    assert np.allclose(check, 1.0), "Loi thiet ke trong so: tong khong bang 1 cho moi trajectory!"
    print("Xac nhan: tong trong so moi trajectory = 1.0 (dung nhu thiet ke).\n")

    print("=== Nested LOGO voi trong so trajectory-fair ===")
    oof_prob, fold_rows = evaluate_with_weight(X, y, groups, sample_weight)

    valid = ~np.isnan(oof_prob)
    ci = bootstrap_incident_level(y.to_numpy()[valid], oof_prob[valid], groups.to_numpy()[valid], pr_auc, n_boot=2000)
    print(f"\nTrajectory-fair-weight pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    per_inc_new = per_incident_metric(y.to_numpy()[valid], oof_prob[valid], groups.to_numpy()[valid], pr_auc)
    m1_oof = pd.read_csv(ROOT / "data" / "processed" / "oof_predictions_v1.csv")
    key_cols = ["source_id", "prefix_len"]
    merged_check = df[key_cols].merge(m1_oof[key_cols + ["oof_prob_M1"]], on=key_cols, how="left")
    per_inc_m1 = per_incident_metric(y.to_numpy(), merged_check["oof_prob_M1"].to_numpy(), groups.to_numpy(), pr_auc)

    common = sorted(set(per_inc_new) & set(per_inc_m1))
    diffs = np.array([per_inc_new[i] - per_inc_m1[i] for i in common])
    mean_diff, lo, hi = paired_bootstrap(diffs)
    print(f"Paired diff (TrajFairWeight - M1 goc) = {mean_diff:+.4f} [{lo:+.4f}, {hi:+.4f}]")

    print("\n=== So sanh per-incident, tach rieng NGAN vs DAI ===")
    print(f"{'incident':32s} {'do_dai':>7s} {'M1_goc':>8s} {'TrajFair':>9s} {'diff':>8s} {'nhom':>6s}")
    short_diffs, long_diffs = [], []
    for inc in common:
        d = per_inc_new[inc] - per_inc_m1[inc]
        if inc in SHORT_INCIDENTS:
            grp, ln = "NGAN", SHORT_INCIDENTS[inc]
            short_diffs.append(d)
        elif inc in LONG_INCIDENTS:
            grp, ln = "DAI", LONG_INCIDENTS[inc]
            long_diffs.append(d)
        else:
            grp, ln = "?", -1
        print(f"{inc:32s} {ln:7d} {per_inc_m1[inc]:8.4f} {per_inc_new[inc]:9.4f} {d:+8.4f} {grp:>6s}")

    print(f"\nTrung binh diff tren nhom NGAN (n={len(short_diffs)}): {np.mean(short_diffs):+.4f}")
    print(f"Trung binh diff tren nhom DAI (n={len(long_diffs)}): {np.mean(long_diffs):+.4f}")

    if lo > 0:
        verdict = "CAI THIEN CO Y NGHIA THONG KE so voi M1 goc - CAN kiem tra lai qua 5 seed truoc khi tin day la that."
    else:
        verdict = "KHONG CAI THIEN CO Y NGHIA THONG KE so voi M1 goc. DUNG o day, khong thu bien the khac."
    print(f"\n=== KET LUAN ===\n{verdict}")

    pd.DataFrame(fold_rows).to_csv(OUT_FOLD_TABLE, index=False)
    pd.DataFrame([{
        "model": "trajectory_fair_weight", "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
        "paired_diff_vs_m1": mean_diff, "paired_ci_low": lo, "paired_ci_high": hi,
        "mean_diff_short_incidents": float(np.mean(short_diffs)), "mean_diff_long_incidents": float(np.mean(long_diffs)),
    }]).to_csv(OUT_TABLE, index=False)

    md = [
        "# Trajectory-fair sample weight cho M1 (LAN THU 6, 2026-09-22)\n",
        "\nGia thuyet: trajectory dai dong gop nhieu dong prefix hon (sau dedupe), co the khien model "
        "hoc lech ve dac diem trajectory dai, giam hieu nang tren trajectory ngan.\n",
        "\nTrong so: `weight = 1 / so_dong_prefix_cua_chinh_trajectory_do` (tong trong so moi trajectory = 1), "
        "NHAN voi scale_pos_weight co san (khong thay the).\n",
        "\n| Model | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
        "| M1 goc (moc chinh thuc) | 0.6624 | [0.5234, 0.8864] |\n",
        f"| **M1 + trajectory-fair weight** | **{ci['point']:.4f}** | [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}] |\n",
        f"\n**Paired diff (TrajFairWeight - M1 goc) = {mean_diff:+.4f}, 95% CI = [{lo:+.4f}, {hi:+.4f}]**\n",
        f"\n**Trung binh diff tren nhom incident NGAN** (<=40 action, n={len(short_diffs)}): {np.mean(short_diffs):+.4f}\n",
        f"\n**Trung binh diff tren nhom incident DAI** (>=73 action, n={len(long_diffs)}): {np.mean(long_diffs):+.4f}\n",
        f"\n## KET LUAN\n\n{verdict}\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_FOLD_TABLE}, {OUT_MD}")


if __name__ == "__main__":
    main()
