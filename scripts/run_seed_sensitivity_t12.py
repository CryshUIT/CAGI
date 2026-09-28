"""NSS 2026 - Viec 2 (T12): chay lai M1 va B3 voi 5 random seed khac nhau,
giu nguyen moi thu khac (split leave-one-incident-out, feature, hyperparameter
mac dinh khac random_state). Muc dich: kiem tra do on dinh cua PR-AUC qua
seed - KHONG suy dien/lam nhe neu std lon.

Dung DUNG dataset da dedupe cua RQ1 (dedupe_pooled_prefixes) + evaluate_model_
nested (leave-one-incident-out, threshold chon tren inner-train) - giong het
scripts/run_full_evaluation_v1.py, chi khac o cho lap qua nhieu seed.

M1TypedTemporalMotifModel(random_state=seed) va B3FlatGraphRandomForest(random_state=seed)
deu nhan **kwargs de override random_state mac dinh=42 (xem src/models/baselines.py).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.metrics import pr_auc
from src.evaluation.nested_eval import bootstrap_incident_level, dedupe_pooled_prefixes, evaluate_model_nested
from src.models.baselines import B3FlatGraphRandomForest, M1TypedTemporalMotifModel

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = REPO_ROOT / "data" / "processed" / "features_v2.parquet"
OUT_CSV = REPO_ROOT / "results" / "tables" / "seed_sensitivity_t12_2026-09-22.csv"
OUT_MD = REPO_ROOT / "results" / "reports" / "seed_sensitivity_t12_2026-09-22.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]
SEEDS = [42, 1, 7, 123, 2026]  # 42 = seed goc (dung de doi chieu voi main_table.csv)


def main() -> None:
    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X, y, groups = df[feature_cols], df["label"], df["group_id"]
    print(f"Dataset dedupe: {len(df)} dong, {len(feature_cols)} feature, {groups.nunique()} incident", flush=True)

    rows = []
    for model_name, factory in [
        ("M1", lambda seed: M1TypedTemporalMotifModel(random_state=seed)),
        ("B3", lambda seed: B3FlatGraphRandomForest(random_state=seed)),
    ]:
        for seed in SEEDS:
            print(f"\n=== {model_name} seed={seed} ===", flush=True)
            result = evaluate_model_nested(lambda s=seed, f=factory: f(s), X, y, groups, target_fpr=0.01)
            oof = result["oof_prob"]
            valid = oof.notna()
            ci = bootstrap_incident_level(y[valid].to_numpy(), oof[valid].to_numpy(), groups[valid].to_numpy(), pr_auc, n_boot=500)
            print(f"  pooled PR-AUC = {ci['point']:.4f} [{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]")
            rows.append({"model": model_name, "seed": seed, "pooled_pr_auc": ci["point"],
                         "ci_low_95": ci["ci_low"], "ci_high_95": ci["ci_high"]})

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    summary = out.groupby("model")["pooled_pr_auc"].agg(["mean", "std", "min", "max"])
    print("\n=== Tom tat qua 5 seed ===")
    print(summary.to_string())

    md = [
        "# T12 - Do nhay theo random seed (M1, B3) - chay 2026-09-22\n",
        f"\nSeed dung: {SEEDS} (42 = seed goc dung trong main_table.csv, giu nguyen moi thu khac: "
        "split leave-one-incident-out, feature set, hyperparameter mac dinh).\n",
        "\n| Model | Seed | Pooled PR-AUC |\n|---|---|---|\n",
    ]
    for _, r in out.iterrows():
        md.append(f"| {r['model']} | {int(r['seed'])} | {r['pooled_pr_auc']:.4f} |\n")
    md.append("\n## Tom tat\n\n| Model | Mean | Std | Min | Max |\n|---|---|---|---|---|\n")
    for model_name, r in summary.iterrows():
        flag = " *** std >= 0.02, KHONG on dinh nhu ky vong ***" if r["std"] >= 0.02 else ""
        md.append(f"| {model_name} | {r['mean']:.4f} | {r['std']:.4f} | {r['min']:.4f} | {r['max']:.4f} |{flag}\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"\nDa luu {OUT_CSV} va {OUT_MD}")


if __name__ == "__main__":
    main()
