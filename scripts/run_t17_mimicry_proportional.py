"""NSS 2026 - T17 (ban sua): chen action mimicry theo TY LE % do dai
trajectory (5%/10%/20%) thay vi so co dinh (2/4/8), de cuong do "nguy trang"
tuong duong nhau giua trajectory ngan/dai - sua han che da phat hien o ban
truoc (run_t17_mimicry_full.py, GIU LAI lam phu luc, KHONG xoa/ghi de).

n_insert = max(1, round(pct * do_dai_trajectory_goc)) - toi thieu 1 de moi
incident deu co it nhat 1 action chen o moi muc (voi trajectory rat ngan,
lam ty le thuc te > pct danh nghia - bao cao ro rang, khong giau).

Giu nguyen TOAN BO logic pilot->full, co che chen (khe ngau nhien + noi suy
timestamp, action THAT tu hard-negative cung incident), cach cham diem
(M1 fit tren 14 incident con lai, hard-negative giu nguyen), va fix dedupe
checkpoint (DEDUPE_LABEL_PRIORITY) da phat hien o ban truoc.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import DEDUPE_LABEL_PRIORITY, bootstrap_incident_level, dedupe_pooled_prefixes  # noqa: E402
from src.features.extractor import extract_all_prefixes  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import Trajectory, load_trajectory_config  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
EVAL15 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022", "paraluni_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024", "xkingdom_2024",
]
PCT_LEVELS = [0.0, 0.05, 0.10, 0.20]
OUT_TABLE = ROOT / "results" / "tables" / "t17_mimicry_proportional_2026-09-22.csv"
OUT_DETAIL = ROOT / "results" / "tables" / "t17_mimicry_proportional_per_incident_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "t17_mimicry_proportional_2026-09-22.md"


def build_positive_trajectory(incident_id, reg_row, config):
    chain, seed, start_block = reg_row["chain_primary"], reg_row["seed_address"], int(reg_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(chain, seed, start_block, incident_id, label=1, config=config, do_collect=False)
    return traj


def build_hard_negative_trajectory(hn_row, config):
    chain, seed, start_block = hn_row["chain"], hn_row["seed_address"], int(hn_row["start_block"])
    traj, _, _ = expand_and_build_trajectory(
        chain, seed, start_block, hn_row["parent_incident_id"], label=0, config=config,
        do_collect=False, max_iterations=2,
    )
    return traj


def pick_best_hard_negative(hn_reg, incident_id, config):
    candidates = hn_reg[hn_reg.parent_incident_id == incident_id].head(10)
    best_row, best_traj, best_len = None, None, -1
    for _, cand in candidates.iterrows():
        t = build_hard_negative_trajectory(cand.to_dict(), config)
        if len(t) > best_len:
            best_row, best_traj, best_len = cand.to_dict(), t, len(t)
    return best_row, best_traj


def n_insert_for_pct(orig_len: int, pct: float) -> int:
    if pct <= 0:
        return 0
    return max(1, round(pct * orig_len))


def insert_mimicry(pos_actions, hn_actions, n_insert, rng):
    L = len(pos_actions)
    if L < 2 or not hn_actions or n_insert == 0:
        return list(pos_actions)
    gaps = list(range(1, L))
    chosen_gaps = rng.choice(gaps, size=n_insert, replace=(n_insert > len(gaps)))
    chosen_idx = rng.choice(len(hn_actions), size=n_insert, replace=(n_insert > len(hn_actions)))
    inserted = []
    for gap_i, act_i in zip(chosen_gaps, chosen_idx):
        t_before, t_after = pos_actions[gap_i - 1].timestamp, pos_actions[gap_i].timestamp
        frac = rng.uniform(0.05, 0.95)
        t_new = t_before + (t_after - t_before) * frac
        if t_new <= t_before:
            t_new = t_before
        src_ev = hn_actions[act_i]
        new_ev = src_ev.model_copy(update={"timestamp": t_new, "log_index": src_ev.log_index + 900000 + len(inserted)})
        inserted.append(new_ev)
    return sorted(list(pos_actions) + inserted, key=lambda e: (e.timestamp, e.block_number, e.tx_hash, e.log_index))


def features_for_trajectory(traj, incident_id, label):
    """Dedupe checkpoint trung do dai (bug da phat hien va sua o ban truoc -
    xem run_t17_mimicry_full.py) - AP DUNG LAI o day, bat buoc."""
    rows = []
    for spec, feats in extract_all_prefixes(traj):
        row = dict(feats)
        row.update({"source_id": incident_id, "group_id": incident_id, "label": label,
                    "prefix_label": spec.label, "trajectory_len": len(traj), "prefix_len": spec.length})
        rows.append(row)
    df_rows = pd.DataFrame(rows)
    prio_map = {lbl: i for i, lbl in enumerate(DEDUPE_LABEL_PRIORITY)}
    df_rows["_prio"] = df_rows["prefix_label"].map(prio_map).fillna(len(DEDUPE_LABEL_PRIORITY))
    df_rows = df_rows.sort_values("_prio", kind="stable").drop_duplicates(subset=["prefix_len"], keep="first")
    df_rows = df_rows.sort_index().drop(columns="_prio")
    return df_rows.reset_index(drop=True)


def run_pilot(config, reg, hn_reg):
    pilot_incidents = ["chibi_finance_2023", "hackerdao_2022", "feg_bridge_2024"]  # 2 dai + 1 NGAN (case nhay cam nhat ban truoc)
    print("\n========== PILOT (ty le %) ==========")
    for inc in pilot_incidents:
        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        hn_row, hn_traj = pick_best_hard_negative(hn_reg, inc, config)
        orig_len = len(pos_traj)
        print(f"\n--- {inc}: do dai goc={orig_len}, hard-negative pool={len(hn_traj)} ---")
        rng = np.random.default_rng(42)
        for pct in PCT_LEVELS:
            n_ins = n_insert_for_pct(orig_len, pct)
            aug_actions = insert_mimicry(pos_traj.actions, hn_traj.actions, n_ins, rng)
            aug_traj = Trajectory(trajectory_id=inc, seed_address=pos_traj.seed_address, actions=aug_actions, label=1, incident_id=inc)
            dfN = features_for_trajectory(aug_traj, inc, 1)
            has_nan = dfN.isna().any().any()
            actual_ratio = n_ins / orig_len if orig_len else 0
            print(f"  pct={pct:.0%}: n_insert={n_ins} (ty le thuc te={actual_ratio:.1%}) "
                  f"do dai moi={len(aug_traj)} so dong prefix={len(dfN)} co_NaN={has_nan}")
            if has_nan:
                print("    [CANH BAO] NaN phat hien!")


def run_full(config, reg, hn_reg, df, feature_cols):
    print("\n========== FULL (ty le %, 15 incident) ==========")
    y_all, prob_all, group_all, level_all = [], [], [], []
    per_incident_rows = []
    ratio_check_rows = []

    for inc in EVAL15:
        print(f"=== {inc} ===", flush=True)
        train = df[df.group_id != inc]
        m = M1TypedTemporalMotifModel()
        m.fit(train[feature_cols], train["label"], train["group_id"])

        neg_rows_real = df[(df.group_id == inc) & (df.label == 0)]
        neg_prob = m.predict_proba(neg_rows_real[feature_cols])

        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        hn_row, hn_traj = pick_best_hard_negative(hn_reg, inc, config)
        orig_len = len(pos_traj)
        rng = np.random.default_rng(42)

        for pct in PCT_LEVELS:
            n_ins = n_insert_for_pct(orig_len, pct)
            aug_actions = insert_mimicry(pos_traj.actions, hn_traj.actions, n_ins, rng)
            aug_traj = Trajectory(trajectory_id=inc, seed_address=pos_traj.seed_address, actions=aug_actions, label=1, incident_id=inc)
            dfN = features_for_trajectory(aug_traj, inc, 1)
            pos_prob = m.predict_proba(dfN[feature_cols])

            y_level = np.concatenate([np.ones(len(pos_prob)), np.zeros(len(neg_prob))])
            prob_level = np.concatenate([pos_prob, neg_prob])
            group_level = np.array([inc] * (len(pos_prob) + len(neg_prob)))
            pr_this = pr_auc(y_level, prob_level)

            y_all.append(y_level); prob_all.append(prob_level); group_all.append(group_level)
            level_all.append(np.array([pct] * len(y_level)))
            actual_ratio = n_ins / orig_len if orig_len else 0
            per_incident_rows.append({
                "incident_id": inc, "pct_nominal": pct, "orig_len": orig_len, "n_insert": n_ins,
                "actual_ratio": actual_ratio, "trajectory_len_augmented": len(aug_traj),
                "pr_auc_this_incident_vs_own_hn": pr_this,
            })
            ratio_check_rows.append({"incident_id": inc, "pct_nominal": pct, "actual_ratio": actual_ratio})
            print(f"  pct={pct:.0%}: n_insert={n_ins} (ty le thuc={actual_ratio:.1%}) "
                  f"len={len(aug_traj)} pr_auc(incident-local)={pr_this:.4f}", flush=True)

    y_all, prob_all, group_all, level_all = map(np.concatenate, (y_all, prob_all, group_all, level_all))
    summary_rows = []
    for pct in PCT_LEVELS:
        mask = level_all == pct
        ci = bootstrap_incident_level(y_all[mask], prob_all[mask], group_all[mask], pr_auc, n_boot=2000)
        summary_rows.append({"pct": pct, "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"]})
        print(f"PCT={pct:.0%}: pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUT_TABLE, index=False)
    detail_df = pd.DataFrame(per_incident_rows)
    detail_df.to_csv(OUT_DETAIL, index=False)

    l0 = summary_df[summary_df.pct == 0.0].iloc[0]
    match_official = abs(l0["mean_pr_auc"] - 0.6624) < 0.001
    print(f"\nDoi chieu pct=0 voi M1 chinh thuc (0.6624): {'KHOP' if match_official else 'KHONG KHOP - CANH BAO'} "
          f"(tinh duoc {l0['mean_pr_auc']:.4f})")

    # --- kiem tra do dong deu cuong do nhieu (yeu cau bat buoc de coi bang moi dang tin cay) ---
    ratio_df = detail_df[detail_df.pct_nominal > 0]
    uniformity = ratio_df.groupby("pct_nominal")["actual_ratio"].agg(["mean", "std", "min", "max"])
    print("\n=== Do dong deu cuong do nhieu (actual_ratio = n_insert/orig_len) theo tung muc % ===")
    print(uniformity.round(4).to_string())

    return summary_df, detail_df, uniformity, match_official


def main():
    config = load_trajectory_config()
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry.csv").set_index("incident_id")
    hn_reg = pd.read_csv(ROOT / "metadata" / "hard_negative_registry.csv")
    df_v2 = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_v2)
    feature_cols = [c for c in df.columns if c not in META_COLS]

    run_pilot(config, reg, hn_reg)
    summary_df, detail_df, uniformity, match_official = run_full(config, reg, hn_reg, df, feature_cols)

    md = [
        "# T17 (ban sua, ty le %) - Mimicry stress test theo % do dai trajectory (2026-09-22)\n",
        "\n**Ban truoc (so co dinh 2/4/8 action)** van giu nguyen KHONG xoa lam phu luc: "
        "`results/tables/t17_mimicry_stress_test_2026-09-22.csv`, `results/reports/t17_mimicry_stress_test_2026-09-22.md` "
        "- KHONG dung lam ket qua chinh vi cuong do nhieu khong dong deu giua incident ngan/dai (da xac nhan).\n",
        "\n## Phuong phap\n",
        "\nChen action THAT (tu hard-negative cung incident) theo TY LE % do dai trajectory goc "
        "(5%/10%/20%, toi thieu 1 action) thay vi so co dinh - dam bao cuong do nguy trang tuong doi "
        "dong deu giua trajectory ngan/dai. Giu nguyen co che chen (khe ngau nhien, noi suy timestamp), "
        "cham diem (M1 fit tren 14 incident con lai), va fix dedupe checkpoint.\n",
        f"\n**Doi chieu pct=0 voi M1 chinh thuc (0.6624): {'KHOP' if match_official else 'KHONG KHOP'} "
        f"(tinh duoc {summary_df[summary_df.pct==0.0].iloc[0]['mean_pr_auc']:.4f}).**\n",
        "\n## Kiem tra do dong deu cuong do nhieu (dieu kien de bang duoc coi la dang tin cay)\n",
        "\n| Muc % danh nghia | Ty le thuc te TB | Std | Min | Max |\n|---|---|---|---|---|\n",
    ]
    for pct, r in uniformity.iterrows():
        md.append(f"| {pct:.0%} | {r['mean']:.1%} | {r['std']:.1%} | {r['min']:.1%} | {r['max']:.1%} |\n")
    md += [
        "\n## Ket qua pooled (15 incident)\n",
        "\n| Muc % | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        md.append(f"| {r['pct']:.0%} | {r['mean_pr_auc']:.4f} | [{r['ci_low_95']:.4f}, {r['ci_high_95']:.4f}] |\n")
    md += ["\n## Ket qua per-incident (PR-AUC cuc bo, chinh incident do vs hard-negative rieng no)\n",
           "\n| Incident | 0% | 5% | 10% | 20% |\n|---|---|---|---|---|\n"]
    piv = detail_df.pivot(index="incident_id", columns="pct_nominal", values="pr_auc_this_incident_vs_own_hn")
    for inc in EVAL15:
        row = piv.loc[inc]
        md.append(f"| {inc} | {row[0.0]:.4f} | {row[0.05]:.4f} | {row[0.10]:.4f} | {row[0.20]:.4f} |\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_DETAIL}, {OUT_MD}")


if __name__ == "__main__":
    main()
