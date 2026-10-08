"""PHASE I (part 2) - time and memory cost of the positioning system itself.

The group's brief asks for an evaluation of "thoi gian, bo nho". Mining cost is
already measured in results/metrics/huim_runs.csv; this script measures the
*other* half, which is where feature selection actually pays off:

    * offline  - time to build the fingerprint index, memory it occupies
    * online   - time to locate one fingerprint, and the peak memory of doing so

Measurement discipline
----------------------
* Timings use n_jobs=1 so the number is a portable single-core cost rather than
  an artefact of how many cores happened to be free. The accuracy numbers in
  run_ips.py are unaffected: n_jobs changes speed, not predictions.
* Every timing is repeated REPEATS times and the MEDIAN is kept, because a
  single wall-clock sample on a desktop OS is dominated by scheduling noise.
* A warm-up prediction runs first and is discarded (BLAS threads, caches).
* Database memory is reported exactly (n x d x itemsize) rather than estimated,
  alongside the measured peak RSS, because RSS includes the interpreter and is
  not what a deployed system would budget for.

Output: results/metrics/ips_cost.csv, results/ips_cost_summary.json
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ips_model import KNNConfig
from preprocess_uji import NOT_DETECTED, fit_preprocessor, joint_label, load_splits
from utils import (METRICS, MemoryMonitor, RESULTS, dump_json,
                   environment_info, get_logger, load_json)

LOG = get_logger("ipscost", "ips_cost.log")

REPEATS = 5
WARMUP = 1
# A single prediction over 1,111 queries takes only tens of milliseconds at
# small feature counts, which is the same order as OS scheduling jitter. Each
# timed sample therefore repeats the prediction until it has accumulated at
# least this much work, and the per-prediction cost is the quotient. This is
# ordinary benchmarking practice and it is what makes the small-d end of the
# curve meaningful rather than noise.
MIN_SAMPLE_SECONDS = 0.5


def measure(X_tr, y_tr, X_va, cfg: KNNConfig) -> dict:
    """One (fit, predict) cost measurement at a given feature count."""
    d = int(X_tr.shape[1])
    res: dict = {
        "n_features": d,
        "n_train_rows": int(X_tr.shape[0]),
        "n_query_rows": int(X_va.shape[0]),
        # exact, not estimated: this is what the fingerprint index costs
        "db_memory_float64_mb": round(X_tr.nbytes / 1024 ** 2, 4),
        "db_memory_float32_mb": round(
            X_tr.shape[0] * d * 4 / 1024 ** 2, 4),
        "db_memory_int8_mb": round(X_tr.shape[0] * d * 1 / 1024 ** 2, 4),
    }
    if d == 0:
        return res

    # calibrate how many predictions one timed sample needs
    clf = KNeighborsClassifier(n_neighbors=cfg.n_neighbors, metric=cfg.metric,
                               weights=cfg.weights, n_jobs=1)
    clf.fit(X_tr, y_tr)
    t0 = time.perf_counter()
    clf.predict(X_va)
    one = max(time.perf_counter() - t0, 1e-6)
    inner = max(1, min(50, int(np.ceil(MIN_SAMPLE_SECONDS / one))))
    res["inner_repeats_per_sample"] = inner
    # Which index sklearn actually chose. It matters: with algorithm="auto"
    # sklearn switches to a tree index at low dimensionality, and on data this
    # sparse a tree can be slower per query than brute force - which is why the
    # cost curve is not monotone at the smallest feature counts.
    res["sklearn_algorithm"] = getattr(clf, "_fit_method", "unknown")

    fit_times, pred_times = [], []
    peak_mb = 0.0
    for r in range(WARMUP + REPEATS):
        clf = KNeighborsClassifier(n_neighbors=cfg.n_neighbors,
                                   metric=cfg.metric, weights=cfg.weights,
                                   n_jobs=1)
        t0 = time.perf_counter()
        clf.fit(X_tr, y_tr)
        t_fit = time.perf_counter() - t0
        with MemoryMonitor(interval=0.01) as mem:
            t0 = time.perf_counter()
            for _ in range(inner):
                clf.predict(X_va)
            t_pred = (time.perf_counter() - t0) / inner
        if r >= WARMUP:
            fit_times.append(t_fit)
            pred_times.append(t_pred)
            peak_mb = max(peak_mb, mem.delta_mb)

    tf, tp = float(np.median(fit_times)), float(np.median(pred_times))
    res.update({
        "fit_seconds": round(tf, 5),
        "fit_seconds_min": round(min(fit_times), 5),
        "fit_seconds_max": round(max(fit_times), 5),
        "predict_total_seconds": round(tp, 5),
        "predict_total_seconds_min": round(min(pred_times), 5),
        "predict_total_seconds_max": round(max(pred_times), 5),
        "predict_ms_per_fingerprint": round(1000.0 * tp / X_va.shape[0], 4),
        "predict_peak_rss_delta_mb": round(peak_mb, 2),
        "throughput_fingerprints_per_second": round(X_va.shape[0] / tp, 1)
        if tp > 0 else None,
        "n_repeats": REPEATS,
        "n_jobs": 1,
    })
    return res


def main() -> None:
    t_start = time.perf_counter()
    tr, va = load_splits()
    prep = fit_preprocessor(tr)
    wap = prep.wap_cols
    col_of = {w: j for j, w in enumerate(wap)}
    y_tr = joint_label(tr)
    Xtr = prep.positive_representation(tr)
    Xva = prep.positive_representation(va)

    isum = load_json(RESULTS / "ips_summary.json")
    cfgd = isum["protocol"]["frozen_knn_config"]
    cfg = KNNConfig(n_neighbors=cfgd["n_neighbors"], metric=cfgd["metric"],
                    weights=cfgd["weights"])
    LOG.info("frozen config: k=%d %s %s", cfg.n_neighbors, cfg.metric,
             cfg.weights)

    I = pd.read_csv(METRICS / "ips_results.csv")
    # Measure the cost of the conditions that actually matter: the two
    # baselines, the best HUIM selection per utility model, and the controls at
    # matched budgets. Cost depends only on the NUMBER of columns, but the
    # condition label is carried so the table can be joined with accuracy.
    picks: list[tuple[str, str, list[str]]] = []
    for cond in ("baseline_all_520", "baseline_detected_465"):
        g = I[I["condition"] == cond]
        if len(g):
            picks.append((cond, g.iloc[0]["family"],
                          str(g.iloc[0]["selected_waps"]).split(";")))
    for fam in ("huim_topn", "huim_union"):
        for model, g in I[I["family"] == fam].groupby("utility_model"):
            best = g.loc[g["joint_building_floor_accuracy"].idxmax()]
            picks.append((best["condition"], fam,
                          str(best["selected_waps"]).split(";")))
    for fam in ("control_top_mi", "control_top_support"):
        g = I[I["family"] == fam]
        for n in (10, 25, 50, 91, 100, 200, 300):
            gg = g[g["n_waps_selected"] == n]
            if len(gg):
                picks.append((gg.iloc[0]["condition"], fam,
                              str(gg.iloc[0]["selected_waps"]).split(";")))

    rows = []
    seen = set()
    for cond, fam, waps in picks:
        if cond in seen:
            continue
        seen.add(cond)
        cols = [col_of[w] for w in waps if w in col_of]
        if not cols:
            continue
        r = measure(Xtr[:, cols], y_tr, Xva[:, cols], cfg)
        g = I[I["condition"] == cond]
        r.update({
            "condition": cond, "family": fam,
            "feature_reduction_pct": float(g["feature_reduction_pct"].iloc[0])
            if len(g) else None,
            "joint_building_floor_accuracy":
                float(g["joint_building_floor_accuracy"].iloc[0])
                if len(g) else None,
            "pos_median_error": float(g["pos_median_error"].iloc[0])
            if len(g) else None,
            "pos_median_error_ground_m":
                float(g["pos_median_error_ground_m"].iloc[0])
                if len(g) and "pos_median_error_ground_m" in g else None,
        })
        rows.append(r)
        LOG.info("%-46s d=%4d | fit %7.4fs | predict %7.4fs "
                 "(%6.3f ms/fp) | db %7.2f MB | peak +%6.1f MB",
                 cond, r["n_features"], r["fit_seconds"],
                 r["predict_total_seconds"], r["predict_ms_per_fingerprint"],
                 r["db_memory_float64_mb"], r["predict_peak_rss_delta_mb"])

    df = pd.DataFrame(rows).sort_values("n_features", ascending=False)
    df.to_csv(METRICS / "ips_cost.csv", index=False)

    base = df[df["condition"] == "baseline_all_520"]
    summary = {
        "phase": "PHASE I part 2 - IPS time and memory cost",
        "environment": environment_info(),
        "protocol": {
            "timing_n_jobs": 1,
            "repeats": REPEATS, "warmup_runs": WARMUP,
            "statistic": "median of the repeats",
            "rationale": "single-core timing is portable; the median removes "
                         "scheduling noise; n_jobs does not change predictions",
            "frozen_knn_config": cfg.as_dict(),
            "db_memory": "exact n x d x itemsize, reported for float64 (what "
                         "this implementation uses), float32 and int8 (what a "
                         "deployed system could use)",
        },
        "rows": rows,
        "total_wall_clock_s": round(time.perf_counter() - t_start, 2),
    }
    if len(base):
        b = base.iloc[0]
        rel = []
        for _, r in df.iterrows():
            rel.append({
                "condition": r["condition"], "n_features": int(r["n_features"]),
                "speedup_vs_all_wap": round(
                    b["predict_total_seconds"] / r["predict_total_seconds"], 3)
                if r["predict_total_seconds"] else None,
                "memory_fraction_vs_all_wap": round(
                    r["db_memory_float64_mb"] / b["db_memory_float64_mb"], 4),
                "joint_accuracy": r["joint_building_floor_accuracy"],
            })
        summary["relative_to_all_wap_baseline"] = rel
    dump_json(summary, RESULTS / "ips_cost_summary.json")
    LOG.info("wrote %s (%d rows) in %.1fs", METRICS / "ips_cost.csv", len(df),
             time.perf_counter() - t_start)
    print(df[["condition", "n_features", "fit_seconds",
              "predict_total_seconds", "predict_ms_per_fingerprint",
              "db_memory_float64_mb", "predict_peak_rss_delta_mb",
              "joint_building_floor_accuracy"]].to_string(index=False))


if __name__ == "__main__":
    main()
