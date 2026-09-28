"""NSS 2026 - Viec 4 (T15): ve lai risk-curve (case chibi_finance_2023) va
latency/RAM (tu results/tables/runtime_table.csv) dang PDF vector, phong
cach khoa hoc cho paper LaTeX — khac ban trinh bay slide/demo truoc day:
KHONG tieu de lon/mau me trong hinh (caption thuoc ve LaTeX, khong bake vao
anh), font serif giong LaTeX mac dinh, mau chu yeu den/xam + 1-2 mau nhan
manh toi thieu, duong net mong, luoi mo nhat.

Du lieu risk-curve DUNG Y HET logic trong scripts/make_fig4_lead_time_curve.py
(khong doi so lieu, chi doi style + xuat PDF). Latency/RAM doc THAT tu
results/tables/runtime_table.csv, khong bia them diem do.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FIG_DIR = REPO_ROOT / "results" / "figures"
INCIDENT_ID = "chibi_finance_2023"

plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.size": 9,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
    "pdf.fonttype": 42,  # embed font dung dang (khong bi vo net/thay the khi in)
})


def load_case_data(incident_id: str) -> dict:
    oof = pd.read_csv(PROCESSED_DIR / "rq2_oof_predictions.csv")
    q = oof[(oof["source_id"] == incident_id) & (oof["label"] == 1)].copy().sort_values("prefix_len").reset_index(drop=True)

    lt = pd.read_csv(REPO_ROOT / "results" / "tables" / "lead_time_results.csv")
    lt_row = lt[lt["incident_id"] == incident_id].iloc[0]

    events = json.loads((PROCESSED_DIR / f"{incident_id}_events.json").read_text(encoding="utf-8"))
    events_sorted = sorted(events, key=lambda a: a["timestamp"])
    n_total = len(events_sorted)

    te = pd.Timestamp(lt_row["te"])
    te_action_type = lt_row["te_action_type"]
    te_idx = None
    for i, ev in enumerate(events_sorted, start=1):
        if pd.Timestamp(ev["timestamp"]) == te and ev["event_type"] == te_action_type:
            te_idx = i
            break
    assert te_idx is not None, "khong tim thay action te - kiem tra lai du lieu"

    q["pct_observed"] = q["prefix_len"] / n_total * 100.0
    return {"q": q, "lt_row": lt_row, "n_total": n_total, "te_idx": te_idx, "te_pct": te_idx / n_total * 100.0}


def draw_risk_curve_paper(out_path: Path) -> None:
    data = load_case_data(INCIDENT_ID)
    q, lt_row, n_total, te_pct = data["q"], data["lt_row"], data["n_total"], data["te_pct"]
    alert_prefix_len = int(lt_row["alert_prefix_len"])
    alert_bucket = lt_row["alert_prefix_bucket"]
    alert_pct = alert_prefix_len / n_total * 100.0

    fig, ax = plt.subplots(figsize=(3.4, 2.6))  # ~ 1 cot bai bao 2-cot
    ax.set_xscale("log")

    ax.plot(q["pct_observed"], q["oof_prob"], marker="o", color="black",
            lw=1.1, markersize=3.5, label="Risk probability (OOF)", zorder=3)
    ax.plot(q["pct_observed"], q["oof_threshold"], marker="none", color="black",
            lw=0.8, linestyle="--", label="Ngưỡng quyết định", zorder=2, alpha=0.65)

    alert_prob = q.loc[q["prefix_label"] == alert_bucket, "oof_prob"].iloc[0]
    ax.axvline(alert_pct, color="black", linestyle=":", lw=0.7, zorder=1)
    ax.scatter([alert_pct], [alert_prob], marker="*", s=70, color="black",
               edgecolor="black", linewidth=0.5, zorder=5, label="Cảnh báo đầu tiên")
    ax.axvline(te_pct, color="black", linestyle="-.", lw=0.8, zorder=1)
    ax.scatter([te_pct], [1.0], marker="^", s=28, color="black", zorder=5, label="Điểm kết thúc (ground truth)")

    ax.set_ylim(-0.03, 1.08)
    ax.set_xlim(q["pct_observed"].min() * 0.7, 115)
    ax.set_xlabel("Trajectory đã quan sát (%, thang log)")
    ax.set_ylabel("Xác suất rủi ro (OOF)")
    ax.grid(True, which="both", axis="both", alpha=0.2, lw=0.4)
    ax.legend(loc="lower left", fontsize=6.5, handlelength=1.6, labelspacing=0.3)
    ax.tick_params(labelsize=7.5)

    fig.tight_layout(pad=0.4)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Da luu {out_path}")


def draw_runtime_paper(out_path: Path) -> None:
    rt = pd.read_csv(REPO_ROOT / "results" / "tables" / "runtime_table.csv").sort_values("n_events")

    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.5))

    ax = axes[0]
    ax.plot(rt["n_events"], rt["median_ms_per_trajectory"], marker="o", color="black", lw=1.0, markersize=3.2, label="Median")
    ax.fill_between(rt["n_events"], rt["median_ms_per_trajectory"], rt["p95_ms_per_trajectory"],
                     color="black", alpha=0.12, lw=0, label="P95")
    ax.set_xscale("log")
    ax.set_xlabel("Số action / trajectory (thang log)")
    ax.set_ylabel("Độ trễ (ms/trajectory)")
    ax.grid(True, which="both", alpha=0.2, lw=0.4)
    ax.legend(fontsize=6.5, handlelength=1.6)
    ax.tick_params(labelsize=7.5)

    ax = axes[1]
    ax.plot(rt["n_events"], rt["peak_ram_delta_mb_tracemalloc"], marker="s", color="black", lw=1.0, markersize=3.2)
    ax.set_xscale("log")
    ax.set_xlabel("Số action / trajectory (thang log)")
    ax.set_ylabel("Đỉnh RAM tăng thêm (MB, tracemalloc)")
    ax.grid(True, which="both", alpha=0.2, lw=0.4)
    ax.tick_params(labelsize=7.5)

    fig.tight_layout(pad=0.6)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Da luu {out_path}")


if __name__ == "__main__":
    draw_risk_curve_paper(FIG_DIR / "fig4_paper_vector.pdf")
    draw_runtime_paper(FIG_DIR / "fig_runtime_paper_vector.pdf")
