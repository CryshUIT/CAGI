"""EDA v2.0 - ban thay the run_eda_v0.5.py (da CU: 11 positive + 408
hard-negative, freeze v0.9, khong co plot anh that - chi CSS bar div).

Ban nay chay TREN DUNG dataset chinh thuc hien tai dang dung de sinh
results/tables/main_table.csv va data/dataset_card.md: 15 positive incident
+ 612 hard-negative, 3354 prefix row (`data/processed/features_v2.parquet`,
RAW - chua qua dedupe_pooled_prefixes; xem doc string moi phan tich de biet
ro dung RAW hay dedup).

QUY UOC DON VI PHAN TICH (quan trong, tranh gia lap gia):
- Cac phan tich mo ta "1 trajectory" (do dai, chain, motif count, correlation,
  feature theo nhom) deu loc CHI prefix_label=='ratio_100' (dung 1 dong/
  trajectory, la trang thai DAY DU cuoi cung) - KHONG dung toan bo 3354 dong
  (se dem 1 trajectory nhieu lan chi vi no co nhieu checkpoint).
- Positive rate theo checkpoint (Muc J) la phan tich DUY NHAT dung dung
  toan bo cac dong theo tung prefix_label rieng - vi day CHINH LA cau hoi
  "prefix_label nay co ty le duong bao nhieu", khong phai mo ta trajectory.

Khong train lai model, khong doi feature/threshold/ket qua da freeze - chi
DOC de phan tich.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.incident_pipeline import expand_and_build_trajectory  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2.parquet"
FEATURES_CONFIG_PATH = ROOT / "configs" / "features.yaml"
INCIDENT_REGISTRY_PATH = ROOT / "metadata" / "incident_registry.csv"
HN_REGISTRY_PATH = ROOT / "metadata" / "hard_negative_registry.csv"
HN_REGISTRY_V2_PATH = ROOT / "metadata" / "hard_negative_registry_v2_complexity.csv"
PROCESSED_DIR = ROOT / "data" / "processed"

FIG_DIR = ROOT / "results" / "figures"
OUT_MD = ROOT / "results" / "reports" / "eda_v2.0.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

OPTIONAL_FIELDS = ["protocol", "token", "counterparty_type", "source_confidence"]

COLOR_POS = "#d95f5f"
COLOR_NEG = "#4c78a8"

CHECKPOINTS_ABS = ["k_2", "k_3", "k_5", "k_7"]
CHECKPOINTS_REL = ["ratio_25", "ratio_50", "ratio_75", "ratio_100"]

MOTIF_5 = {
    "motif_split": "split",
    "motif_merge": "merge",
    "motif_peel_like_chain": "peel-like chain",
    "motif_bridge_then_swap": "bridge→swap",
    "motif_rapid_token_pivot": "rapid token pivot",
}

# 1-2 feature dai dien moi nhom (doc dung ten tu configs/features.yaml,
# chi chon cot THAT SU co trong features_v2.parquet - vai ten trong config
# la ten nhom logic (vd "inter_action_gaps") khong phai ten cot that
# (vd "inter_action_gap_mean"/"inter_action_gap_std") - anh xa thu cong
# CO CAN CU vao dung cot da xac nhan ton tai, khong doan mo.
FEATURE_GROUP_REPRESENTATIVES = {
    "temporal": ["burstiness", "active_duration_sec"],
    "structural": ["fan_out", "path_depth"],
    "economic": ["log_amount_mean", "value_retention"],
    "semantic_action": ["action_count_swap_ratio", "num_bridge_families"],
    "motif": ["motif_split", "motif_rapid_token_pivot"],
}


def log(msg: str) -> None:
    print(msg, flush=True)


def load_feature_groups():
    cfg = yaml.safe_load(FEATURES_CONFIG_PATH.read_text(encoding="utf-8"))
    return cfg["feature_groups"]


def iqr_stats(values: pd.Series) -> dict:
    values = values.dropna()
    if len(values) == 0:
        return {"n": 0, "min": float("nan"), "q1": float("nan"), "median": float("nan"),
                "q3": float("nan"), "max": float("nan")}
    return {
        "n": int(len(values)), "min": float(values.min()),
        "q1": float(values.quantile(0.25)), "median": float(values.median()),
        "q3": float(values.quantile(0.75)), "max": float(values.max()),
    }


def load_all_raw_events(df_full: pd.DataFrame) -> dict:
    """Nap/rebuild raw event list (list[dict], CHUA qua feature extraction)
    cho MOI trajectory (positive: doc truc tiep data/processed/{id}_events.json;
    hard-negative/control: rebuild qua expand_and_build_trajectory tu cache
    that, do_collect=False) - dung DUY NHAT cho phan tich missingness optional
    field (Muc missingness), vi features_v2.parquet KHONG luu lai cac field
    nay."""
    hn_df = pd.concat([
        pd.read_csv(HN_REGISTRY_PATH), pd.read_csv(HN_REGISTRY_V2_PATH),
    ], ignore_index=True).set_index("hard_negative_id")
    control_df = pd.read_csv(INCIDENT_REGISTRY_PATH)
    control_df = control_df[control_df["label"] == 0].set_index("incident_id")
    config = load_trajectory_config()

    cache: dict[str, list] = {}
    n_rebuilt = 0
    for source_id, kind in df_full[["source_id", "kind"]].drop_duplicates("source_id").itertuples(index=False):
        if kind == "positive":
            path = PROCESSED_DIR / f"{source_id}_events.json"
            cache[source_id] = json.loads(path.read_text(encoding="utf-8"))
        elif kind == "hard_negative_control":
            row = control_df.loc[source_id]
            traj, _, _ = expand_and_build_trajectory(
                row["chain_primary"], row["seed_address"], int(row["start_block"]), source_id, 0,
                config=config, do_collect=False, max_iterations=2,
            )
            cache[source_id] = [json.loads(a.model_dump_json()) for a in traj.actions]
            n_rebuilt += 1
        else:
            row = hn_df.loc[source_id]
            traj, _, _ = expand_and_build_trajectory(
                row["chain"], row["seed_address"], int(row["start_block"]), row["parent_incident_id"], 0,
                config=config, do_collect=False, max_iterations=2,
            )
            cache[source_id] = [json.loads(a.model_dump_json()) for a in traj.actions]
            n_rebuilt += 1
    log(f"  Da nap/rebuild {len(cache)} trajectory raw events ({n_rebuilt} rebuild tu cache) cho missingness check.")
    return cache


def savefig(fig, name: str) -> str:
    path = FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return name


def main():
    log("=== EDA v2.0 - dataset chinh thuc N=15 (15 incident + 612 hard-negative, 3354 prefix row) ===")
    df_full = pd.read_parquet(FEATURES_PATH)
    df_traj = df_full[df_full["prefix_label"] == "ratio_100"].copy()  # 1 dong/trajectory
    log(f"Raw prefix rows: {len(df_full)}; trajectory (ratio_100) rows: {len(df_traj)}")

    report_sections = []

    # ============ A. Class balance ============
    log("\n--- A. Class balance ---")
    n_pos_traj = int((df_traj["label"] == 1).sum())
    n_neg_traj = int((df_traj["label"] == 0).sum())
    n_pos_row = int((df_full["label"] == 1).sum())
    n_neg_row = int((df_full["label"] == 0).sum())
    row_pos_rate = 100 * n_pos_row / len(df_full)
    traj_pos_rate = 100 * n_pos_traj / len(df_traj)
    log(f"Trajectory-level: {n_pos_traj} positive / {n_neg_traj} negative (ratio neg:pos = {n_neg_traj/n_pos_traj:.1f}:1), positive rate = {traj_pos_rate:.4f}%")
    log(f"Prefix-row-level: {n_pos_row} positive / {n_neg_row} negative (ratio neg:pos = {n_neg_row/n_pos_row:.1f}:1), positive rate = {row_pos_rate:.4f}%")

    dataset_card_check = (
        n_pos_traj == 15 and n_neg_traj == 612 and len(df_full) == 3354
    )
    report_sections.append(f"""## A. Class balance

| Muc do | Positive | Negative | Ty le neg:pos | Positive rate |
|---|---|---|---|---|
| Trajectory-level | {n_pos_traj} | {n_neg_traj} | {n_neg_traj/n_pos_traj:.1f}:1 | {traj_pos_rate:.4f}% |
| Prefix-row-level (RAW, 3354 dong) | {n_pos_row} | {n_neg_row} | {n_neg_row/n_pos_row:.1f}:1 | {row_pos_rate:.4f}% |

**Doi chieu voi dataset_card.md/paper**: ky vong 15 positive incident, 612 hard-negative,
3354 prefix row -> {"KHOP CHINH XAC" if dataset_card_check else "**LECH - xem ghi chu ben duoi**"}.

**Ve con so "positive rate 5.0%" trong paper**: {row_pos_rate:.2f}% (prefix-row RAW) va
{traj_pos_rate:.2f}% (trajectory-level) - **CA HAI DEU KHONG KHOP 5.0%**. Da thu them ca
positive rate tren tap DA DEDUPE (dung cho modeling RQ1, 1785 dong): xem duoi.
KHONG tim thay chuoi "5.0%"/"5,0%" o bat ky report/dataset_card nao trong repo qua grep -
day co the la con so tinh theo cach khac trong paper (vd lam tron/xap xi khac), hoac stale
tu ban truoc. **KHONG tu sua/lam khop - can nguoi dung doi chieu lai voi cong thuc that
dung trong paper.**
""")

    # dedup comparison (modeling dataset)
    try:
        from src.evaluation.nested_eval import dedupe_pooled_prefixes
        df_dedup = dedupe_pooled_prefixes(df_full)
        dedup_pos_rate = 100 * (df_dedup["label"] == 1).sum() / len(df_dedup)
        log(f"[Tham khao] Prefix-row-level tren tap DA DEDUPE (dung cho RQ1 modeling, {len(df_dedup)} dong): positive rate = {dedup_pos_rate:.4f}%")
        report_sections.append(f"[Tham khao] Positive rate tren tap DA DEDUPE (dung cho RQ1 modeling thuc te, "
                                f"`dedupe_pooled_prefixes`, {len(df_dedup)} dong): **{dedup_pos_rate:.4f}%** - "
                                f"van khong khop 5.0% chinh xac nhung gan hon ca (~6.5%).\n")
    except Exception as e:
        log(f"  (Bo qua dedup comparison: {e})")

    # ============ B. Trajectory length distribution + IQR overlap check ============
    log("\n--- B. Trajectory length distribution ---")
    len_pos = df_traj.loc[df_traj["label"] == 1, "trajectory_len"]
    len_neg = df_traj.loc[df_traj["label"] == 0, "trajectory_len"]
    stats_pos = iqr_stats(len_pos)
    stats_neg = iqr_stats(len_neg)
    overlap = not (stats_pos["q3"] < stats_neg["q1"] or stats_neg["q3"] < stats_pos["q1"])
    log(f"Positive: n={stats_pos['n']} min={stats_pos['min']:.0f} Q1={stats_pos['q1']:.1f} median={stats_pos['median']:.1f} Q3={stats_pos['q3']:.1f} max={stats_pos['max']:.0f}")
    log(f"Negative: n={stats_neg['n']} min={stats_neg['min']:.0f} Q1={stats_neg['q1']:.1f} median={stats_neg['median']:.1f} Q3={stats_neg['q3']:.1f} max={stats_neg['max']:.0f}")
    log(f"IQR 2 lop CHONG LAP: {'CO' if overlap else 'KHONG'} (shortcut-check {'KHONG dang lo' if overlap else 'DANG LO - IQR tach biet hoan toan, nghi ngo shortcut theo do dai'})")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist([np.log1p(len_neg), np.log1p(len_pos)], bins=25, color=[COLOR_NEG, COLOR_POS],
                 label=["negative", "positive"], stacked=False, alpha=0.75)
    axes[0].set_xlabel("log(1 + trajectory length)")
    axes[0].set_ylabel("So trajectory")
    axes[0].set_title("Histogram do dai trajectory (log scale)")
    axes[0].legend()
    axes[1].boxplot([len_neg, len_pos], labels=["negative", "positive"],
                     patch_artist=True, boxprops=dict(facecolor=COLOR_NEG))
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Trajectory length (log scale)")
    axes[1].set_title("Boxplot do dai trajectory theo lop")
    fig.tight_layout()
    fig_len = savefig(fig, "eda_v2.0_trajectory_length.png")

    report_sections.append(f"""## B. Phan bo do dai trajectory theo lop

| Lop | n | min | Q1 | median | Q3 | max |
|---|---|---|---|---|---|---|
| Positive | {stats_pos['n']} | {stats_pos['min']:.0f} | {stats_pos['q1']:.1f} | {stats_pos['median']:.1f} | {stats_pos['q3']:.1f} | {stats_pos['max']:.0f} |
| Negative | {stats_neg['n']} | {stats_neg['min']:.0f} | {stats_neg['q1']:.1f} | {stats_neg['median']:.1f} | {stats_neg['q3']:.1f} | {stats_neg['max']:.0f} |

**Shortcut check (IQR chong lap?):** {"CO CHONG LAP" if overlap else "KHONG CHONG LAP"} - "
{"khong phat hien dau hieu 'do dai la shortcut' ro ret nhu ban v0.5 cu." if overlap else "**CANH BAO tuong tu ban v0.5**: 2 lop co the tach duoc chi bang do dai, can kiem tra ky hon truoc khi tin tuong feature khac dang hoc gi that."}

![Trajectory length]({fig_len.replace('.png','')}.png)
""")

    # ============ C. Chain distribution ============
    log("\n--- C. Chain distribution ---")
    chain_ct = df_traj.groupby(["chain", "label"]).size().unstack(fill_value=0)
    log(chain_ct.to_string())
    fig, ax = plt.subplots(figsize=(6, 4.5))
    chains = chain_ct.index.tolist()
    x = np.arange(len(chains))
    width = 0.35
    ax.bar(x - width/2, chain_ct.get(0, pd.Series(0, index=chains)), width, label="negative", color=COLOR_NEG)
    ax.bar(x + width/2, chain_ct.get(1, pd.Series(0, index=chains)), width, label="positive", color=COLOR_POS)
    ax.set_xticks(x)
    ax.set_xticklabels(chains)
    ax.set_ylabel("So trajectory")
    ax.set_title("So trajectory theo chain va lop")
    ax.legend()
    fig.tight_layout()
    fig_chain = savefig(fig, "eda_v2.0_chain_distribution.png")
    report_sections.append(f"""## C. Phan bo theo chain

{chain_ct.to_markdown()}

![Chain distribution]({fig_chain.replace('.png','')}.png)
""")

    # ============ D. Bridge family distribution (positive incidents only, tu incident_registry) ============
    log("\n--- D. Bridge family (positive incident, tu incident_registry.csv) ---")
    reg = pd.read_csv(INCIDENT_REGISTRY_PATH)
    pos_reg = reg[(reg["label"] == 1) & (reg["eval_tier"] == "primary")]
    bridge_raw = pos_reg["bridge_families"].fillna("n/a (khong dung bridge/chua xac dinh)")
    bridge_simplified = bridge_raw.apply(lambda s: s.split(";")[0].split(" (")[0] if s not in
                                          ("nan", "n/a (khong dung bridge/chua xac dinh)", "TBD_pending_trajectory_decode")
                                          else ("TBD/chua decode" if s == "TBD_pending_trajectory_decode" else "n/a"))
    bridge_ct = bridge_simplified.value_counts()
    log(bridge_ct.to_string())
    report_sections.append(f"""## D. Bridge family (CHI 15 positive incident - hard-negative khong co bridge family da xac minh)

{bridge_ct.to_frame("so incident").to_markdown()}

(Ghi chu: hard-negative KHONG co truong bridge_family da xac minh doc lap trong registry - chi
positive incident co du lieu nay, nen phan tich nay CHI tinh tren 15 positive.)
""")

    # ============ E. Event type distribution (tu action_count_* RAW, ratio_100 rows) ============
    log("\n--- E. Event type distribution (RAW action_count_*, tong tren ratio_100 rows) ---")
    action_raw_cols = [c for c in df_traj.columns if c.startswith("action_count_") and not c.endswith("_ratio")]
    event_sum = df_traj.groupby("label")[action_raw_cols].sum().T
    event_sum.index = [c.replace("action_count_", "") for c in event_sum.index]
    log(event_sum.to_string())
    fig, ax = plt.subplots(figsize=(8, 5))
    event_sum.plot(kind="bar", ax=ax, color=[COLOR_NEG, COLOR_POS])
    ax.set_ylabel("Tong so action (log scale)")
    ax.set_yscale("log")
    ax.set_title("So action theo event type va lop (tong tren toan bo trajectory)")
    ax.legend(["negative", "positive"])
    fig.tight_layout()
    fig_event = savefig(fig, "eda_v2.0_event_type_distribution.png")
    report_sections.append(f"""## E. Phan bo theo event type (tong so action, tren trajectory day du)

{event_sum.to_markdown()}

![Event type distribution]({fig_event.replace('.png','')}.png)
""")

    # ============ F. 5 feature-group distributions (pos vs neg) ============
    log("\n--- F. Phan bo feature theo 5 nhom (temporal/structural/economic/semantic_action/motif) ---")
    n_groups = len(FEATURE_GROUP_REPRESENTATIVES)
    fig, axes = plt.subplots(n_groups, 2, figsize=(10, 3.2 * n_groups))
    group_md = []
    for gi, (group, feats) in enumerate(FEATURE_GROUP_REPRESENTATIVES.items()):
        group_md.append(f"\n### Nhom `{group}`\n")
        for fi, feat in enumerate(feats):
            ax = axes[gi, fi]
            vpos = df_traj.loc[df_traj["label"] == 1, feat].dropna()
            vneg = df_traj.loc[df_traj["label"] == 0, feat].dropna()
            ax.boxplot([vneg, vpos], labels=["neg", "pos"], patch_artist=True,
                       boxprops=dict(facecolor=COLOR_NEG))
            ax.set_title(f"{group}: {feat}", fontsize=9)
            s_pos, s_neg = iqr_stats(vpos), iqr_stats(vneg)
            group_md.append(f"- `{feat}`: pos median={s_pos['median']:.4g} (Q1-Q3 {s_pos['q1']:.4g}-{s_pos['q3']:.4g}), "
                             f"neg median={s_neg['median']:.4g} (Q1-Q3 {s_neg['q1']:.4g}-{s_neg['q3']:.4g})\n")
    fig.tight_layout()
    fig_groups = savefig(fig, "eda_v2.0_feature_group_boxplots.png")
    report_sections.append("## F. Phan bo feature theo 5 nhom (positive vs negative, tren trajectory day du)\n"
                            + "".join(group_md) +
                            f"\n![Feature group boxplots]({fig_groups.replace('.png','')}.png)\n")

    # ============ G. Motif count distributions (5 motif) ============
    log("\n--- G. Phan bo 5 motif count theo lop ---")
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    motif_md = ["\n| Motif | pos median | pos Q1-Q3 | neg median | neg Q1-Q3 |\n|---|---|---|---|---|\n"]
    for i, (col, label_name) in enumerate(MOTIF_5.items()):
        vpos = df_traj.loc[df_traj["label"] == 1, col].dropna()
        vneg = df_traj.loc[df_traj["label"] == 0, col].dropna()
        axes[i].boxplot([vneg, vpos], labels=["neg", "pos"], patch_artist=True,
                         boxprops=dict(facecolor=COLOR_POS if False else COLOR_NEG))
        axes[i].set_title(label_name, fontsize=9)
        s_pos, s_neg = iqr_stats(vpos), iqr_stats(vneg)
        motif_md.append(f"| {label_name} | {s_pos['median']:.2f} | {s_pos['q1']:.2f}-{s_pos['q3']:.2f} | "
                         f"{s_neg['median']:.2f} | {s_neg['q1']:.2f}-{s_neg['q3']:.2f} |\n")
    fig.tight_layout()
    fig_motif = savefig(fig, "eda_v2.0_motif_counts.png")
    report_sections.append("## G. Phan bo 5 motif count theo lop\n" + "".join(motif_md) +
                            f"\n![Motif counts]({fig_motif.replace('.png','')}.png)\n")

    # ============ H. Positive rate per checkpoint ============
    log("\n--- H. Positive rate theo checkpoint ---")
    checkpoint_md = ["\n| Checkpoint | n dong | n positive | positive rate |\n|---|---|---|---|\n"]
    checkpoint_rates = {}
    for cp in CHECKPOINTS_ABS + CHECKPOINTS_REL:
        sub = df_full[df_full["prefix_label"] == cp]
        n = len(sub)
        npos = int((sub["label"] == 1).sum())
        rate = 100 * npos / n if n else float("nan")
        checkpoint_rates[cp] = rate
        checkpoint_md.append(f"| {cp} | {n} | {npos} | {rate:.4f}% |\n")
        log(f"  {cp}: n={n} n_pos={npos} rate={rate:.4f}%")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    order = CHECKPOINTS_ABS + CHECKPOINTS_REL
    ax.bar(order, [checkpoint_rates[c] for c in order], color=COLOR_POS)
    ax.set_ylabel("Positive rate (%)")
    ax.set_title("Positive rate theo tung checkpoint (absolute k va relative %)")
    ax.axhline(row_pos_rate, color="gray", linestyle="--", label=f"Positive rate tong the RAW ({row_pos_rate:.2f}%)")
    ax.legend()
    fig.tight_layout()
    fig_checkpoint = savefig(fig, "eda_v2.0_positive_rate_by_checkpoint.png")
    report_sections.append("## H. Positive rate theo checkpoint\n" + "".join(checkpoint_md) +
                            f"\n![Positive rate by checkpoint]({fig_checkpoint.replace('.png','')}.png)\n")

    # ============ I. Correlation heatmap ============
    log("\n--- I. Correlation heatmap ---")
    numeric_cols = [c for c in df_traj.columns if c not in META_COLS and df_traj[c].dtype != object]
    corr = df_traj[numeric_cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(16, 14))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=90, fontsize=6)
    ax.set_yticklabels(numeric_cols, fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman correlation")
    ax.set_title("Correlation heatmap (tat ca feature, tren trajectory day du)")
    fig.tight_layout()
    fig_corr = savefig(fig, "eda_v2.0_correlation_heatmap.png")

    # kiem chung "motif_split correlated by construction voi fan_out/branch_count"
    check_pairs = [("motif_split", "branch_count"), ("motif_split", "fan_out"),
                   ("action_count_merge_ratio", "outgoing_incoming_ratio")]
    check_md = ["\n**Kiem chung 'correlated by construction' (paper claim):**\n\n| Cap feature | Spearman corr |\n|---|---|\n"]
    for a, b in check_pairs:
        if a in corr.index and b in corr.columns:
            check_md.append(f"| `{a}` vs `{b}` | {corr.loc[a,b]:+.4f} |\n")
    report_sections.append("## I. Correlation heatmap\n" + "".join(check_md) +
                            f"\n![Correlation heatmap]({fig_corr.replace('.png','')}.png)\n")

    # ============ J. Missingness cua optional field (RAW event level, can rebuild) ============
    log("\n--- J. Missingness optional field (raw event level) ---")
    events_cache = load_all_raw_events(df_full)
    miss_counts = {f: [0, 0] for f in OPTIONAL_FIELDS}  # [n_missing, n_total]
    for events in events_cache.values():
        for e in events:
            for f in OPTIONAL_FIELDS:
                miss_counts[f][1] += 1
                if e.get(f) is None:
                    miss_counts[f][0] += 1
    miss_md = ["\n| Optional field | % missing | n_missing / n_total |\n|---|---|---|\n"]
    for f, (nmiss, ntotal) in miss_counts.items():
        pct = 100 * nmiss / ntotal if ntotal else float("nan")
        miss_md.append(f"| {f} | {pct:.2f}% | {nmiss}/{ntotal} |\n")
        log(f"  {f}: {pct:.2f}% missing ({nmiss}/{ntotal})")
    report_sections.append("## J. Missingness theo optional field (muc raw event, tinh tren TOAN BO action that)\n"
                            + "".join(miss_md))

    # ============ Ghep report ============
    header = f"""# EDA v2.0 — Dataset chinh thuc N=15 (2026-09-27)

**Thay the** `results/reports/eda_v0.5.html` (CU: 11 positive + 408 hard-negative, freeze v0.9,
khong co plot anh that). Ban nay chay tren DUNG dataset dang dung de sinh
`results/tables/main_table.csv` / `data/dataset_card.md`: **{n_pos_traj} positive incident,
{n_neg_traj} hard-negative, {len(df_full)} prefix row** (RAW, `data/processed/features_v2.parquet`,
khop {"CHINH XAC" if dataset_card_check else "**KHONG khop - xem muc A**"} voi dataset_card.md).

Nguon xac dinh dataset chinh thuc: `data/processed/features_v2.parquet` (RAW, {len(df_full)} dong,
{df_full['source_id'].nunique()} trajectory) - chinh la file duoc `dedupe_pooled_prefixes()` xu ly
truoc khi dua vao moi pipeline RQ1/RQ2/ablation trong `results/tables/main_table.csv`. Khong dung
lai `src/pipeline/dataset_builder.py::load_rq1_trajectories` (nguon CU cua ban v0.5, tro toi
freeze v0.9 11-incident, khong con dung cho ket qua hien tai).

Khong train lai model, khong doi feature/threshold/ket qua da freeze o buoc nao trong file nay.

"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(header + "\n".join(report_sections), encoding="utf-8")
    log(f"\nDa luu report: {OUT_MD}")
    log(f"Da luu {6} anh PNG vao {FIG_DIR}")


if __name__ == "__main__":
    main()
