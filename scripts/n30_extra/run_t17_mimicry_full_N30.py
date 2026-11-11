"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_t17_mimicry_full.py cho N=30 (chen 0/2/4/8 action co dinh).

Thay doi DUY NHAT so voi ban goc:
1. EVAL15 (15 incident) -> EVAL30 (30 incident, toan bo primary/label=1
   trong incident_registry_N30.csv).
2. REGISTRY_PATH -> incident_registry_N30.csv, HN_REGISTRY_PATH ->
   hard_negative_registry_N30_combined.csv, FEATURES_PATH ->
   features_v2_N30.parquet, config -> data_N30.yaml.
3. Doi chieu level=0 voi M1 pooled PR-AUC = 0.7762 (N30) thay vi 0.6624 (N15).
4. Duong dan output -> hau to extra_N30.
Logic chen mimicry / cham diem / bootstrap giu nguyen 100%.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import DEDUPE_LABEL_PRIORITY, bootstrap_incident_level, dedupe_pooled_prefixes  # noqa: E402
from src.features.extractor import extract_all_prefixes  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402
from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import Trajectory, load_trajectory_config  # noqa: E402

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
EVAL30 = [
    "ronin_bridge_2022", "qbridge_qubit_2022", "feg_bridge_2024", "deltaprime_arbitrum_2024",
    "bsc_token_hub_2022", "chibi_finance_2023", "wooppv2_2024", "utopiasphere_2024", "xkingdom_2024",
    "wault_finance_2021", "paraluni_2022", "radiant_capital_arbitrum_2024", "magic_abracadabra_arbitrum_2025",
    "hackerdao_2022", "new_free_dao_2022", "zunami_protocol_2023", "onyx_protocol_2023",
    "beanstalk_farms_2022", "hedgey_finance_2024", "cork_protocol_2025", "dough_finance_2024",
    "0xinfini_2025", "prisma_finance_2024", "uranium_finance_2021", "inverse_finance_2022_jun",
    "lendhub_2023", "thorchain2_2021", "popsicle_finance_2021", "heco_htx_2023", "easyfi_2021",
]
LEVELS = [0, 2, 4, 8]
REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
HN_REGISTRY_PATH = ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
CONFIG_PATH = ROOT / "configs" / "data_N30.yaml"
OUT_TABLE = ROOT / "results" / "tables" / "extra_N30_t17_mimicry_stress_test.csv"
OUT_DETAIL = ROOT / "results" / "tables" / "extra_N30_t17_mimicry_per_incident.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_t17_mimicry_stress_test.md"


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


def main():
    check_m1_gate()
    config = load_trajectory_config(str(CONFIG_PATH))
    reg = pd.read_csv(REGISTRY_PATH).set_index("incident_id")
    hn_reg = pd.read_csv(HN_REGISTRY_PATH)
    df_v2 = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_v2)
    feature_cols = [c for c in df.columns if c not in META_COLS]

    y_all, prob_all, group_all, level_all = [], [], [], []
    per_incident_rows = []
    detail_rows = []

    for inc in EVAL30:
        print(f"=== {inc} ===", flush=True)
        train = df[df.group_id != inc]
        m = M1TypedTemporalMotifModel()
        m.fit(train[feature_cols], train["label"], train["group_id"])

        neg_rows_real = df[(df.group_id == inc) & (df.label == 0)]
        neg_prob = m.predict_proba(neg_rows_real[feature_cols])

        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        hn_row, hn_traj = pick_best_hard_negative(hn_reg, inc, config)
        rng = np.random.default_rng(42)

        for level in LEVELS:
            aug_actions = insert_mimicry(pos_traj.actions, hn_traj.actions, level, rng)
            aug_traj = Trajectory(trajectory_id=inc, seed_address=pos_traj.seed_address, actions=aug_actions, label=1, incident_id=inc)
            dfN = features_for_trajectory(aug_traj, inc, 1)
            pos_prob = m.predict_proba(dfN[feature_cols])

            y_level = np.concatenate([np.ones(len(pos_prob)), np.zeros(len(neg_prob))])
            prob_level = np.concatenate([pos_prob, neg_prob])
            group_level = np.array([inc] * (len(pos_prob) + len(neg_prob)))
            pr_this = pr_auc(y_level, prob_level)

            y_all.append(y_level); prob_all.append(prob_level); group_all.append(group_level)
            level_all.append(np.array([level] * len(y_level)))
            per_incident_rows.append({"incident_id": inc, "level": level, "trajectory_len_augmented": len(aug_traj),
                                       "pr_auc_this_incident_vs_own_hn": pr_this})
            for lbl, p in zip(dfN.prefix_label, pos_prob):
                detail_rows.append({"incident_id": inc, "level": level, "prefix_label": lbl, "prob": p})
            print(f"  level={level}: len={len(aug_traj)} pr_auc(incident-local)={pr_this:.4f}", flush=True)

    y_all, prob_all, group_all, level_all = map(np.concatenate, (y_all, prob_all, group_all, level_all))
    summary_rows = []
    for level in LEVELS:
        mask = level_all == level
        ci = bootstrap_incident_level(y_all[mask], prob_all[mask], group_all[mask], pr_auc, n_boot=2000)
        summary_rows.append({"level": level, "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"],
                              "n_incidents": len(EVAL30)})
        print(f"LEVEL={level}: pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    summary_df = pd.DataFrame(summary_rows)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_TABLE, index=False)
    pd.DataFrame(per_incident_rows).to_csv(OUT_DETAIL, index=False)
    pd.DataFrame(detail_rows).to_csv(ROOT / "results" / "tables" / "extra_N30_t17_mimicry_prob_detail.csv", index=False)

    l0 = summary_df[summary_df.level == 0].iloc[0]
    match_official = abs(l0["mean_pr_auc"] - 0.7762) < 0.001
    print(f"\nDoi chieu L=0 voi M1 pooled N30 (0.7762): {'KHOP' if match_official else 'KHONG KHOP - CANH BAO'} (tinh duoc {l0['mean_pr_auc']:.4f})")

    md = [
        "# [EXPLORATORY/post-hoc, ngoai plan v3] T17 - Mimicry stress test (muc chen co dinh 0/2/4/8) — N=30\n",
        "\n**Kich ban mo phong (doc truc tiep tu code, khong doan)**: chen 0/2/4/8 action THAT "
        "(lay nguyen tu 1 hard-negative cung incident, KHONG bia) vao khe ngau nhien giua cac action "
        "duong tinh, timestamp noi suy tuyen tinh giua 2 action lang gieng. KHONG mo phong attacker "
        "thich nghi theo thoi gian thuc - chi la 1 lan chen tinh, tai tao qua extract_all_prefixes() "
        "that, cham diem bang M1 fit tren 29 incident con lai (hard-negative giu nguyen). Pool 30 "
        "incident, bootstrap CI muc incident (2000 lan, seed 42).\n",
        f"\n**Doi chieu L=0 voi M1 pooled N30 (0.7762): {'KHOP' if match_official else 'KHONG KHOP'} "
        f"(tinh duoc {l0['mean_pr_auc']:.4f}).**\n",
        "\n## Ket qua\n",
        "\n| Muc chen | Mean PR-AUC (pooled) | 95% CI | n incident |\n|---|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        md.append(f"| {int(r['level'])} action | {r['mean_pr_auc']:.4f} | [{r['ci_low_95']:.4f}, {r['ci_high_95']:.4f}] | {int(r['n_incidents'])} |\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_DETAIL}, {OUT_MD}")


if __name__ == "__main__":
    main()
