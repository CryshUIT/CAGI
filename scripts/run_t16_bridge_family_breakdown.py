"""NSS 2026 - Viec 5 (T16): breakdown PR-AUC cua M1 theo bridge family.

Doc lai PR-AUC per-incident CUA M1 da co san trong results/tables/main_table.csv
(cung protocol RQ1, khong tinh lai) + metadata/incident_registry.csv (cot
bridge_families, dang chuoi tu do, doi khi liet ke nhieu bridge cach nhau boi
";", doi khi la "TBD_pending_trajectory_decode" (chua giai ma) hoac NaN
(khong dung bridge)) - KHONG suy doan family cho incident chua xac dinh.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVAL15 = [
    "bsc_token_hub_2022", "chibi_finance_2023", "deltaprime_arbitrum_2024", "feg_bridge_2024",
    "hackerdao_2022", "magic_abracadabra_arbitrum_2025", "new_free_dao_2022", "paraluni_2022",
    "qbridge_qubit_2022", "radiant_capital_arbitrum_2024", "ronin_bridge_2022", "utopiasphere_2024",
    "wault_finance_2021", "wooppv2_2024", "xkingdom_2024",
]


def normalize_family(raw) -> str:
    if pd.isna(raw):
        return "Không dùng bridge (NaN trong registry)"
    if "TBD_pending" in str(raw):
        return "Chưa giải mã được bridge (TBD_pending_trajectory_decode)"
    first = str(raw).split(";")[0]
    if "Stargate" in first:
        return "Stargate (LayerZero)"
    if "LI.FI" in first:
        return "LI.FI Diamond"
    if "Across" in first:
        return "Across Protocol"
    if "Ronin" in first:
        return "Ronin Bridge"
    if "QBridge" in first or "Qubit" in first:
        return "QBridge (Qubit Finance)"
    if "BSC Token Hub" in first:
        return "BSC Token Hub"
    if "FEG" in first:
        return "FEG SmartBridge"
    return first.split(" (")[0]


def main() -> None:
    main_table = pd.read_csv(ROOT / "results/tables/main_table.csv")
    m1 = main_table[(main_table.model == "M1") & main_table.metric.str.startswith("pr_auc_incident_")].copy()
    m1["incident_id"] = m1["metric"].str.replace("pr_auc_incident_", "", regex=False)
    m1 = m1.set_index("incident_id")["mean_point_estimate"]

    reg = pd.read_csv(ROOT / "metadata/incident_registry.csv").set_index("incident_id")

    rows = []
    for iid in EVAL15:
        raw = reg.loc[iid, "bridge_families"]
        rows.append({"incident_id": iid, "bridge_family_raw": raw, "bridge_family": normalize_family(raw),
                     "m1_pr_auc": m1.get(iid, float("nan"))})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results/tables/t16_bridge_family_breakdown_2026-09-22.csv", index=False)

    summary = df.groupby("bridge_family")["m1_pr_auc"].agg(["mean", "std", "count"]).sort_values("count", ascending=False)
    print(df[["incident_id", "bridge_family", "m1_pr_auc"]].to_string(index=False))
    print("\n=== Tom tat theo family ===")
    print(summary.round(4).to_string())

    md = [
        "# T16 - Breakdown PR-AUC (M1) theo bridge family - chay 2026-09-22\n",
        "\n**Canh bao doc ket qua**: chi 2/8 nhom co >=3 incident (Stargate, LI.FI Diamond) — "
        "cac nhom con lai n=1 (bang dung 1 gia tri PR-AUC cua incident do, KHONG phai 'dac diem "
        "family' co the khai quat hoa). Khong nen dien giai nhom n=1 la 'model manh/yeu voi family X'.\n",
        "\n| Incident | Bridge family (chuan hoa) | PR-AUC (M1) |\n|---|---|---|\n",
    ]
    for _, r in df.iterrows():
        md.append(f"| {r['incident_id']} | {r['bridge_family']} | {r['m1_pr_auc']:.4f} |\n")
    md += ["\n## Tom tat theo family\n", "\n| Bridge family | n | Mean PR-AUC | Std |\n|---|---|---|---|\n"]
    for fam, r in summary.iterrows():
        std_str = f"{r['std']:.4f}" if pd.notna(r["std"]) else "-"
        md.append(f"| {fam} | {int(r['count'])} | {r['mean']:.4f} | {std_str} |\n")
    (ROOT / "results/reports/t16_bridge_family_breakdown_2026-09-22.md").write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu results/tables/t16_bridge_family_breakdown_2026-09-22.csv va bao cao .md")


if __name__ == "__main__":
    main()
