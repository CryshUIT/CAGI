"""EXPLORATORY / post-hoc - sua lai hoan toan ban dau (xem lich su: ban
dau nham lan "LOIO v3 cung tap test" = loc OOF toan cuc theo chain, SAI -
xem giai thich duoi). Muc tieu THAT: tai tao DUNG methodology cua
`evaluation_N30_by_chain_table.csv` [v3, dong 282-306 run_evaluation_N30_v3.py]
cho CA M1 VA B3' (v3 CHI co M1/B3 goc, KHONG co B3'), VA lay them per-incident
breakdown (v3 chi luu pooled).

QUAN TRONG - PHAN BIET RO 2 DINH NGHIA "LOIO v3" KHAC NHAU (phat hien khi
doi chieu khong khop):
1. "LOIO-TRONG-CHAIN" (DUNG - khop evaluation_N30_by_chain_table.csv):
   loc df xuong CHI con incident CUNG chain truoc, roi evaluate_model_nested
   TRONG PHAM VI DO - nghia la incident test duoc danh gia boi model train
   tren CAC INCIDENT KHAC **CUNG CHAIN** (khong bao gom 2 chain con lai).
2. "LOIO-TOAN-CUC-loc-sau" (lan dau, SAI, da XOA): loc OOF cua LOIO 30-incident
   toan cuc (train tren CA 29 incident khac, gom ca chain khac) xuong chi
   con dong cua chain do - day la PR-AUC khi model DA THAY du lieu chain
   khac luc train, KHONG PHAI "LOIO v3 cung tap test" nhu yeu cau.

Dinh nghia (1) la dung vi no la DUY NHAT cung "vu tru incident" voi LOCO
(ca 2 deu KHONG cho model thay incident chain khac khi train) - chi khac
o: LOIO-trong-chain train tren (incident CUNG chain - 1), LOCO train tren
(TOAN BO 2 chain khac, KHONG co incident nao cung chain). Day moi la cap
so sanh dung nghia "cung tap test, khac vu tru train" ma nguoi dung yeu cau.

Gate: doi chieu M1 pooled voi evaluation_N30_by_chain_table.csv [v3] - PHAI
khop tuyet doi (sai so <1e-6, vi CUNG dung evaluate_model_nested + bootstrap
giong het, chi chay lai). Khong khop -> DUNG.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from scripts.n30_extra.extra_v3b._common_v3b import META_COLS, load_dataset, make_b3prime_factory  # noqa: E402
from src.evaluation.metrics import pr_auc  # noqa: E402
from src.evaluation.nested_eval import bootstrap_incident_level, evaluate_model_nested, per_incident_metric  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402

REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
LOCO_PER_INC_PATH = ROOT / "results" / "tables" / "extra_v3b" / "leave_one_chain_out_N30_per_incident.csv"
LOCO_POOLED_PATH = ROOT / "results" / "tables" / "extra_v3b" / "leave_one_chain_out_N30.csv"
V3_BY_CHAIN_PATH = ROOT / "results" / "tables" / "evaluation_N30_by_chain_table.csv"

OUT_PER_INC_CSV = ROOT / "results" / "tables" / "extra_v3b" / "loco_vs_loio_within_chain_per_incident_N30.csv"
OUT_POOLED_CSV = ROOT / "results" / "tables" / "extra_v3b" / "loco_vs_loio_within_chain_pooled_N30.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_v3b" / "loco_vs_loio_within_chain_N30.md"

MODEL_FACTORIES = {"M1": M1TypedTemporalMotifModel, "B3prime": make_b3prime_factory()}


def main():
    df, chain_map = load_dataset()
    feature_cols = [c for c in df.columns if c not in META_COLS]
    v3_by_chain = pd.read_csv(V3_BY_CHAIN_PATH).set_index("chain")
    loco_per_inc = pd.read_csv(LOCO_PER_INC_PATH)
    loco_pooled = pd.read_csv(LOCO_POOLED_PATH)

    chains = ["eth", "bsc", "arbitrum"]
    pooled_rows = []
    per_inc_rows = []
    gate_ok = True

    for chain in chains:
        ids_chain = {iid for iid, c in chain_map.items() if c == chain}
        df_chain = df[df["group_id"].isin(ids_chain)].reset_index(drop=True)
        X = df_chain[feature_cols]
        y = df_chain["label"]
        groups = df_chain["group_id"]
        n_incident = groups.nunique()
        print(f"\n=== chain={chain}: {n_incident} incident, {len(df_chain)} dong (LOIO-TRONG-CHAIN) ===", flush=True)

        for name, factory in MODEL_FACTORIES.items():
            result = evaluate_model_nested(factory, X, y, groups, target_fpr=0.01)
            oof = result["oof_prob"].to_numpy()
            y_arr, g_arr = y.to_numpy(), groups.to_numpy()

            boot = bootstrap_incident_level(y_arr, oof, g_arr, pr_auc, n_boot=2000, random_state=42)
            per_inc = per_incident_metric(y_arr, oof, g_arr, pr_auc)

            if name == "M1":
                ref = float(v3_by_chain.loc[chain, "M1_pr_auc_pooled"])
                diff = abs(boot["point"] - ref)
                ok = diff < 1e-6
                gate_ok &= ok
                print(f"  [GATE M1] moi={boot['point']:.6f} v3_da_co={ref:.6f} |diff|={diff:.8f} {'PASS' if ok else 'FAIL'}")

            loco_sub = loco_per_inc[(loco_per_inc.chain_test == chain) & (loco_per_inc.model == name)]
            loco_map = dict(zip(loco_sub.incident_id, loco_sub.pr_auc))
            for iid, score in per_inc.items():
                loco_score = loco_map.get(iid)
                per_inc_rows.append({
                    "chain": chain, "model": name, "incident_id": iid,
                    "pr_auc_LOIO_trong_chain": score, "pr_auc_LOCO": loco_score,
                    "diff_LOCO_minus_LOIO_trong_chain": (loco_score - score) if loco_score is not None else None,
                })

            loco_pooled_val = loco_pooled[(loco_pooled.chain_test == chain) & (loco_pooled.model == name)]["loco_pooled_pr_auc"].iloc[0]
            pooled_rows.append({
                "chain": chain, "model": name, "n_incident": n_incident,
                "pooled_pr_auc_LOIO_trong_chain": boot["point"],
                "ci_low_95_LOIO_trong_chain": boot["ci_low"], "ci_high_95_LOIO_trong_chain": boot["ci_high"],
                "pooled_pr_auc_LOCO": loco_pooled_val,
                "diff_LOCO_minus_LOIO_trong_chain": loco_pooled_val - boot["point"],
            })
            print(f"  [{name}] LOIO-trong-chain pooled={boot['point']:.4f} [{boot['ci_low']:.4f},{boot['ci_high']:.4f}] "
                  f"vs LOCO pooled={loco_pooled_val:.4f} (diff={loco_pooled_val - boot['point']:+.4f})", flush=True)

    if not gate_ok:
        print("\n*** GATE KHONG KHOP voi evaluation_N30_by_chain_table.csv [v3] - DUNG ***")
        raise SystemExit(1)
    print("\n[GATE] Tat ca chain, M1, deu khop tuyet doi voi v3_by_chain_table - PASS.")

    pooled_df = pd.DataFrame(pooled_rows)
    per_inc_df = pd.DataFrame(per_inc_rows)
    OUT_POOLED_CSV.parent.mkdir(parents=True, exist_ok=True)
    pooled_df.to_csv(OUT_POOLED_CSV, index=False)
    per_inc_df.to_csv(OUT_PER_INC_CSV, index=False)
    print(f"\nDa luu {OUT_POOLED_CSV}, {OUT_PER_INC_CSV}")
    print("\n=== POOLED (LOIO-trong-chain vs LOCO, CUNG tap test = toan bo incident cua chain) ===")
    print(pooled_df.to_string(index=False))
    print("\n=== PER-INCIDENT ===")
    print(per_inc_df.to_string(index=False))

    md = [
        "# [EXPLORATORY] LOIO-trong-chain (tái tạo đúng v3) vs LOCO — N=30\n",
        "\n**So sánh CÙNG tập test** (toàn bộ incident của 1 chain), khác NHAU "
        "DUY NHẤT ở vũ trụ train: LOIO-trong-chain (train trên các incident "
        "KHÁC CÙNG CHAIN) vs LOCO (train trên TOÀN BỘ 2 chain khác, không có "
        "incident nào cùng chain). Đây là cặp so sánh đúng nghĩa đã yêu cầu — "
        "**KHÁC** với một lần thử trước đó (đã xóa, lọc OOF của LOIO 30-incident "
        "toàn cục xuống theo chain — đó là model ĐÃ THẤY incident chain khác lúc "
        "train, không cùng vũ trụ với LOCO).\n",
        "\nGate: M1 pooled khớp tuyệt đối với `evaluation_N30_by_chain_table.csv` [v3] "
        "(sai số <1e-6) — PASS ở cả 3 chain.\n",
        "\n## Pooled\n\n", pooled_df.to_string(index=False), "\n",
        "\n## Theo từng incident\n\n", per_inc_df.to_string(index=False), "\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
