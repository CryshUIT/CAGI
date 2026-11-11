"""EXPLORATORY / post-hoc - ban copy cua run_efficiency_benchmark_N30.py,
CHI them: do RIENG thoi gian extract_features() va predict_proba() (ban
goc do CHUNG ca 2 trong 1 vong lap _run_once()). Cung config may, cung so
lan lap (N_WARMUP=20, N_MEASURE_PER_BUCKET=15), cung cac do dai trajectory
(2..11592 event) nhu ban da chay. KHONG doi logic nao khac.
"""
from __future__ import annotations

import gc
import platform
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import psutil  # noqa: E402
import sklearn  # noqa: E402
import xgboost  # noqa: E402

import src.pipeline.dataset_builder as dataset_builder  # noqa: E402
from scripts.n30_extra._gate_check_N30 import check_m1_gate  # noqa: E402
from src.evaluation.nested_eval import dedupe_pooled_prefixes  # noqa: E402
from src.features.extractor import extract_features  # noqa: E402
from src.models.baselines import M1TypedTemporalMotifModel  # noqa: E402
from src.trajectories.builder import load_trajectory_config  # noqa: E402

FEATURES_PATH = ROOT / "data" / "processed" / "features_v2_N30.parquet"
CONFIG_N30_PATH = ROOT / "configs" / "data_N30.yaml"
OUT_TABLE = ROOT / "results" / "tables" / "extra_N30_runtime_split.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_runtime_split.md"

META_COLS = ["trajectory_id", "source_id", "group_id", "kind", "chain", "label",
             "prefix_label", "prefix_len", "trajectory_len"]

N_WARMUP = 20
N_MEASURE_PER_BUCKET = 15


def _apply_n30_monkeypatch() -> None:
    dataset_builder.REGISTRY_PATH = ROOT / "metadata" / "incident_registry_N30.csv"
    dataset_builder.HARD_NEGATIVE_REGISTRY_PATH = ROOT / "metadata" / "hard_negative_registry_N30_combined.csv"
    dataset_builder.SPLIT_MANIFEST_PATH = ROOT / "metadata" / "split_manifest_N30.json"
    dataset_builder.HARD_NEGATIVE_REGISTRY_V2_COMPLEXITY_PATH = (
        ROOT / "metadata" / "hard_negative_registry_v2_complexity_N30_combined.csv"
    )


def main():
    check_m1_gate()
    print("=== Nap trajectory that N30 (cache local) ===", flush=True)
    _apply_n30_monkeypatch()
    config_n30 = load_trajectory_config(str(CONFIG_N30_PATH))
    items = dataset_builder.load_rq1_trajectories(config=config_n30, verbose=False, include_v2_complexity=True)
    lengths = sorted(set(len(i.trajectory) for i in items if len(i.trajectory) > 0))
    print(f"Tong {len(items)} trajectory, do dai distinct: {len(lengths)} (min={min(lengths)}, max={max(lengths)})", flush=True)

    df_raw = pd.read_parquet(FEATURES_PATH)
    df = dedupe_pooled_prefixes(df_raw)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    model = M1TypedTemporalMotifModel()
    model.fit(df[feature_cols], df["label"], df["group_id"])
    print(f"Da train M1 (N30) tren {len(df)} dong, {len(model.feature_cols_)} feature.", flush=True)

    length_buckets = sorted(set(min(lengths, key=lambda l: abs(l - target))
                                 for target in [2, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 11592]))
    traj_by_len = {}
    for i in items:
        n = len(i.trajectory)
        if n in length_buckets and n not in traj_by_len:
            traj_by_len[n] = i.trajectory
    print(f"Bucket do dai dung de benchmark: {sorted(traj_by_len.keys())}", flush=True)

    def _run_extract(traj):
        return extract_features(traj, len(traj), include_endpoint_context=False)

    def _run_predict(feats):
        row = pd.DataFrame([feats])[model.feature_cols_].fillna(0.0)
        return model.predict_proba(row)[0]

    print(f"\n=== Warm-up ({N_WARMUP} lan, khong tinh vao ket qua) ===", flush=True)
    warmup_traj = traj_by_len[sorted(traj_by_len)[len(traj_by_len) // 2]]
    for _ in range(N_WARMUP):
        f = _run_extract(warmup_traj)
        _run_predict(f)

    process = psutil.Process()
    rows = []
    print(f"\n=== Benchmark TACH 2 giai doan ({N_MEASURE_PER_BUCKET} lan/bucket, sau warm-up) ===", flush=True)
    for n_events in sorted(traj_by_len):
        traj = traj_by_len[n_events]
        gc.collect()
        extract_ms, predict_ms, total_ms = [], [], []
        tracemalloc.start()
        rss_before = process.memory_info().rss
        for _ in range(N_MEASURE_PER_BUCKET):
            t0 = time.perf_counter()
            feats = _run_extract(traj)
            t1 = time.perf_counter()
            _run_predict(feats)
            t2 = time.perf_counter()
            extract_ms.append((t1 - t0) * 1000.0)
            predict_ms.append((t2 - t1) * 1000.0)
            total_ms.append((t2 - t0) * 1000.0)
        _, peak_tracemalloc = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rss_after = process.memory_info().rss

        extract_ms, predict_ms, total_ms = map(np.array, (extract_ms, predict_ms, total_ms))
        row = {
            "n_events": n_events,
            "median_extract_features_ms": float(np.median(extract_ms)),
            "p95_extract_features_ms": float(np.percentile(extract_ms, 95)),
            "median_predict_proba_ms": float(np.median(predict_ms)),
            "p95_predict_proba_ms": float(np.percentile(predict_ms, 95)),
            "median_total_ms": float(np.median(total_ms)),
            "p95_total_ms": float(np.percentile(total_ms, 95)),
            "peak_ram_delta_mb_tracemalloc": peak_tracemalloc / 1e6,
            "rss_mb_before": rss_before / 1e6,
            "rss_mb_after": rss_after / 1e6,
            "n_measurements": N_MEASURE_PER_BUCKET,
        }
        rows.append(row)
        print(f"  n_events={n_events:6d}  extract_median={row['median_extract_features_ms']:.3f}ms  "
              f"predict_median={row['median_predict_proba_ms']:.3f}ms  total_median={row['median_total_ms']:.3f}ms  "
              f"total_p95={row['p95_total_ms']:.3f}ms", flush=True)

    table_df = pd.DataFrame(rows)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    table_df.to_csv(OUT_TABLE, index=False)
    print(f"\nDa luu {OUT_TABLE}")

    # --- Doi chieu voi latency tong da bao cao truoc (ban khong tach, run_efficiency_benchmark_N30.py) ---
    PREVIOUSLY_REPORTED_TOTAL_MS = {2: 15.043, 11592: 382.073}
    print("\n=== Doi chieu tong (extract+predict) vs ban KHONG tach da bao cao truoc ===")
    for n_events, prev_total in PREVIOUSLY_REPORTED_TOTAL_MS.items():
        if n_events in traj_by_len:
            row = table_df[table_df.n_events == n_events].iloc[0]
            diff = row["median_total_ms"] - prev_total
            print(f"  n_events={n_events}: tong tach={row['median_total_ms']:.3f}ms vs tong khong tach (da bao cao)={prev_total:.3f}ms "
                  f"(chenh lech={diff:+.3f}ms — do nhieu do giua 2 lan chay doc lap, KHONG phai sai logic)")

    hardware = {
        "platform": platform.platform(), "processor": platform.processor(),
        "python_version": platform.python_version(), "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": psutil.virtual_memory().total / 1e9,
        "sklearn_version": sklearn.__version__, "xgboost_version": xgboost.__version__,
        "process_count": 1,
    }
    md = [
        "# [EXPLORATORY/post-hoc] Efficiency benchmark N=30 — TÁCH 2 giai đoạn (extract_features vs predict_proba)\n",
        "\nCùng cấu hình/số lần lặp với `extra_N30_runtime_table.csv` (bản không tách) — "
        f"{N_WARMUP} lần warm-up, {N_MEASURE_PER_BUCKET} lần đo/bucket.\n",
        "\n## Hardware\n\n```\n" + "\n".join(f"{k}: {v}" for k, v in hardware.items()) + "\n```\n",
        "\n## Kết quả\n\n", table_df.to_string(index=False), "\n",
    ]
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
