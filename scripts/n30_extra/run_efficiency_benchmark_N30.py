"""EXPLORATORY / post-hoc (NGOAI analysis_plan_N30_v3.md) - ban copy cua
scripts/run_efficiency_benchmark.py. Thay doi DUY NHAT: FEATURES_PATH ->
features_v2_N30.parquet, va monkeypatch dataset_builder TRUOC khi goi
load_rq1_trajectories() de lay dung trajectory THAT cua N30 (lap lai CHINH
XAC pattern monkeypatch-trong-main() cua scripts/build_features_v2_N30.py -
KHONG mutate module o muc import). Logic do latency/RAM giu nguyen 100%.
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
OUT_TABLE = ROOT / "results" / "tables" / "extra_N30_runtime_table.csv"
OUT_MD = ROOT / "results" / "reports" / "extra_N30_runtime.md"

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

    def _run_once(traj):
        feats = extract_features(traj, len(traj), include_endpoint_context=False)
        row = pd.DataFrame([feats])[model.feature_cols_].fillna(0.0)
        prob = model.predict_proba(row)[0]
        return prob

    print(f"\n=== Warm-up ({N_WARMUP} lan, khong tinh vao ket qua) ===", flush=True)
    warmup_traj = traj_by_len[sorted(traj_by_len)[len(traj_by_len) // 2]]
    for _ in range(N_WARMUP):
        _run_once(warmup_traj)

    process = psutil.Process()
    rows = []
    print(f"\n=== Benchmark ({N_MEASURE_PER_BUCKET} lan/bucket, sau warm-up) ===", flush=True)
    for n_events in sorted(traj_by_len):
        traj = traj_by_len[n_events]
        gc.collect()
        latencies_ms = []
        tracemalloc.start()
        rss_before = process.memory_info().rss
        for _ in range(N_MEASURE_PER_BUCKET):
            t0 = time.perf_counter()
            _run_once(traj)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)
        _, peak_tracemalloc = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rss_after = process.memory_info().rss

        latencies_ms = np.array(latencies_ms)
        row = {
            "n_events": n_events,
            "median_ms_per_trajectory": float(np.median(latencies_ms)),
            "mean_ms_per_trajectory": float(latencies_ms.mean()),
            "p95_ms_per_trajectory": float(np.percentile(latencies_ms, 95)),
            "ms_per_event": float(np.median(latencies_ms) / n_events),
            "peak_ram_delta_mb_tracemalloc": peak_tracemalloc / 1e6,
            "rss_mb_before": rss_before / 1e6,
            "rss_mb_after": rss_after / 1e6,
            "n_measurements": N_MEASURE_PER_BUCKET,
        }
        rows.append(row)
        print(f"  n_events={n_events:6d}  median={row['median_ms_per_trajectory']:.3f}ms  "
              f"p95={row['p95_ms_per_trajectory']:.3f}ms  ms/event={row['ms_per_event']:.4f}  "
              f"peak_ram_delta={row['peak_ram_delta_mb_tracemalloc']:.3f}MB", flush=True)

    table_df = pd.DataFrame(rows)
    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    table_df.to_csv(OUT_TABLE, index=False)
    print(f"\nDa luu {OUT_TABLE}")

    x = np.log(table_df["n_events"].to_numpy())
    y_lat = np.log(table_df["median_ms_per_trajectory"].to_numpy())
    slope_lat = float(np.polyfit(x, y_lat, 1)[0])

    hardware = {
        "platform": platform.platform(), "processor": platform.processor(),
        "python_version": platform.python_version(), "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": psutil.virtual_memory().total / 1e9,
        "sklearn_version": sklearn.__version__, "xgboost_version": xgboost.__version__,
        "process_count": 1,
    }

    latency_ratio = table_df["median_ms_per_trajectory"].iloc[-1] / table_df["median_ms_per_trajectory"].iloc[0]
    n_ratio = table_df["n_events"].iloc[-1] / table_df["n_events"].iloc[0]
    md = [
        "# [EXPLORATORY/post-hoc, ngoai plan v3] Efficiency benchmark N=30 — M1\n",
        "\nCHỈ đo model processing latency (extract_features + predict_proba), KHÔNG đo "
        "data-availability delay hay alert lead time (RQ2). Dùng trajectory THẬT từ N=30 "
        f"(bao gồm inverse_finance_2022_jun, n_actions=11.592 — incident dài nhất trong dataset).\n",
        f"\nĐo sau {N_WARMUP} lần warm-up, {N_MEASURE_PER_BUCKET} lần đo/bucket độ dài.\n",
        "\n## Hardware / môi trường\n\n```\n" + "\n".join(f"{k}: {v}" for k, v in hardware.items()) + "\n```\n",
        "\n## Kết quả theo số event/trajectory\n\n",
        table_df.to_string(index=False),
        f"\n\nHệ số góc hồi quy log(latency) ~ log(n_events) = **{slope_lat:.3f}**. "
        f"Khoảng đo: {table_df['n_events'].iloc[0]:.0f}→{table_df['n_events'].iloc[-1]:.0f} event "
        f"(tăng {n_ratio:.0f} lần), latency {table_df['median_ms_per_trajectory'].iloc[0]:.1f}ms → "
        f"{table_df['median_ms_per_trajectory'].iloc[-1]:.1f}ms (tăng ~{latency_ratio:.2f} lần).\n",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"Da luu {OUT_MD}")


if __name__ == "__main__":
    main()
