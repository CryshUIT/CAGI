"""NSS 2026 - Viec 1 (T17) full run: 15 incident duong x 4 muc chen
(0/2/4/8 action benign that tu hard-negative cung incident), bao cao PR-AUC
pooled + bootstrap CI muc incident cho tung muc.

Phuong phap (da pilot va xac nhan o run_t17_mimicry_stress_test.py):
- L=0 = trajectory duong that, khong doi (dung de doi chieu dung 0.6624).
- Voi L>0: chen L action THAT tu 1 hard-negative cung incident (chon tot
  nhat trong 10 candidate dau) vao khe ngau nhien giua cac action duong,
  timestamp noi suy. Tinh lai feature bang extract_all_prefixes() that.
- Cham diem bang M1 fit tren 14 incident con lai (KHONG doi qua cac muc L -
  data train khong bi anh huong boi viec chen vao incident dang la outer
  test) - hard-negative GIU NGUYEN, cham diem lai cung fold model (khong
  tai su dung oof cu, de dam bao nhat quan tuyet doi trong 1 lan chay).
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
LEVELS = [0, 2, 4, 8]
OUT_TABLE = ROOT / "results" / "tables" / "t17_mimicry_stress_test_2026-09-22.csv"
OUT_DETAIL = ROOT / "results" / "tables" / "t17_mimicry_per_incident_2026-09-22.csv"
OUT_MD = ROOT / "results" / "reports" / "t17_mimicry_stress_test_2026-09-22.md"


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
    """QUAN TRONG (bug phat hien sau lan chay full dau tien - L=0 khong khop
    0.6624 chinh thuc, lech 0.0070): extract_all_prefixes() KHONG tu dedupe
    cac prefix_label trung DO DAI (vd trajectory ngan: "ratio_25" va "k_3"
    co the cung length, sinh 2 DONG TRUNG feature nhung khac nhan) - dedupe
    nay CHI co trong dedupe_pooled_prefixes() (dung cho toan bo dataset
    chinh thuc), khong co san trong extract_all_prefixes(). Neu khong dedupe
    o day, cac incident trajectory NGAN (feg_bridge_2024, wooppv2_2024,
    new_free_dao_2022...) bi DEM LAP 1 do dai nhu 2 quan sat doc lap, lam
    sai lech pooled PR-AUC. Ap dung DUNG cung uu tien DEDUPE_LABEL_PRIORITY
    da dung cho toan bo dataset chinh thuc, dam bao nhat quan."""
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
    config = load_trajectory_config()
    reg = pd.read_csv(ROOT / "metadata" / "incident_registry.csv").set_index("incident_id")
    hn_reg = pd.read_csv(ROOT / "metadata" / "hard_negative_registry.csv")
    df_v2 = pd.read_parquet(ROOT / "data" / "processed" / "features_v2.parquet")
    df = dedupe_pooled_prefixes(df_v2)
    feature_cols = [c for c in df.columns if c not in META_COLS]

    y_all, prob_all, group_all, level_all = [], [], [], []
    per_incident_rows = []
    detail_rows = []

    for inc in EVAL15:
        print(f"=== {inc} ===", flush=True)
        train = df[df.group_id != inc]
        m = M1TypedTemporalMotifModel()
        m.fit(train[feature_cols], train["label"], train["group_id"])

        # --- hard-negative (KHONG doi qua cac muc) cua CHINH incident nay, cham 1 lan ---
        neg_rows_real = df[(df.group_id == inc) & (df.label == 0)]
        neg_prob = m.predict_proba(neg_rows_real[feature_cols])

        pos_traj = build_positive_trajectory(inc, reg.loc[inc].to_dict(), config)
        hn_row, hn_traj = pick_best_hard_negative(hn_reg, inc, config)
        rng = np.random.default_rng(42)  # 1 rng lien tuc qua cac muc trong CUNG 1 incident (khong reset) - tai lap duoc, khong "chon lai" moi lan

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

    # --- pool TOAN BO 15 incident theo tung muc, bootstrap CI muc incident ---
    y_all, prob_all, group_all, level_all = map(np.concatenate, (y_all, prob_all, group_all, level_all))
    summary_rows = []
    for level in LEVELS:
        mask = level_all == level
        ci = bootstrap_incident_level(y_all[mask], prob_all[mask], group_all[mask], pr_auc, n_boot=2000)
        summary_rows.append({"level": level, "mean_pr_auc": ci["point"], "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"]})
        print(f"LEVEL={level}: pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUT_TABLE, index=False)
    pd.DataFrame(per_incident_rows).to_csv(OUT_DETAIL, index=False)
    pd.DataFrame(detail_rows).to_csv(ROOT / "results" / "tables" / "t17_mimicry_prob_detail_2026-09-22.csv", index=False)

    l0 = summary_df[summary_df.level == 0].iloc[0]
    match_official = abs(l0["mean_pr_auc"] - 0.6624) < 0.001
    print(f"\nDoi chieu L=0 voi M1 chinh thuc (0.6624): {'KHOP' if match_official else 'KHONG KHOP - CANH BAO'} (tinh duoc {l0['mean_pr_auc']:.4f})")

    md = [
        "# T17 - Mimicry stress test (chay 2026-09-22)\n",
        "\n## Phuong phap\n",
        "\nChen 0/2/4/8 action THAT (lay tu hard-negative cung incident, khong bia) vao trajectory "
        "duong o khe ngau nhien, tinh lai feature qua extract_all_prefixes() that, cham diem bang M1 "
        "fit tren 14 incident con lai (hard-negative giu nguyen). Pool 15 incident, bootstrap CI muc incident.\n",
        f"\n**Doi chieu L=0 voi M1 chinh thuc (0.6624): {'KHOP' if match_official else 'KHONG KHOP'} "
        f"(tinh duoc {l0['mean_pr_auc']:.4f}) - xac nhan pipeline dung dan.**\n",
        "\n## Ket qua\n",
        "\n| Muc chen | Mean PR-AUC (pooled) | 95% CI |\n|---|---|---|\n",
    ]
    for _, r in summary_df.iterrows():
        md.append(f"| {int(r['level'])} action | {r['mean_pr_auc']:.4f} | [{r['ci_low_95']:.4f}, {r['ci_high_95']:.4f}] |\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_TABLE}, {OUT_DETAIL}, {OUT_MD}")


if __name__ == "__main__":
    main()
