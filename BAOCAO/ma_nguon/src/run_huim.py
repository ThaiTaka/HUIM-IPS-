"""PHASE H - the full HUIM experiment on trainingData.

Grid design is informed by the pilot (results/metrics/pilot_runs.csv), which
showed the brief's starting grid is too coarse: between 5% and 2% of total
database utility the output goes from ~0 HUIs to hundreds of thousands. The grid
below is therefore refined in that band and extended upwards, and it descends
until a run hits a resource budget - at which point the descent stops for that
model and the run is recorded as ABORTED_RESOURCE_LIMIT rather than discarded.

Outputs
-------
results/metrics/huim_runs.csv       one row per (utility model, minUtil)
results/hui/<model>__<pct>.jsonl.gz the HUI set, when small enough to keep
results/hui/<model>__<pct>__waps.json per-WAP evidence for every run
results/huim_summary.json           everything, including the aborted runs
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_selection import (feature_reduction_pct, hui_length_distribution,
                               per_wap_statistics, rank_agreement, select_waps)
from huim.efim import mine_efim
from preprocess_uji import fit_preprocessor, joint_label, load_splits
from utils import (HUI_DIR, METRICS, MemoryMonitor, RESULTS, dump_json,
                   environment_info, get_logger)
from utility_models import build_external_utility

LOG = get_logger("huim", "huim_full.log")

# Refined around the phase transition the pilot located.
GRID_PCT = [20.0, 15.0, 10.0, 7.5, 5.0, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0]
TIME_LIMIT_S = 600.0
MAX_HUIS = 1_000_000
# Keep the full itemset list on disk only when it is small enough to be useful
# for inspection; otherwise keep the top-1000 by utility plus full aggregates.
SAVE_FULL_HUI_LIMIT = 50_000
TOP_HUI_KEEP = 1000
MODELS = ("A", "B", "C")


def _save_hui_set(tag: str, huis, n_total_waps: int) -> dict:
    """Persist what is needed downstream without writing gigabytes."""
    paths = {}
    ranked = sorted(huis, key=lambda r: -r[1])
    top = [{"itemset": list(x), "utility": float(u), "support": int(s)}
           for x, u, s in ranked[:TOP_HUI_KEEP]]
    p_top = HUI_DIR / f"{tag}__top{TOP_HUI_KEEP}.json"
    dump_json(top, p_top)
    paths["top_huis"] = str(p_top)

    if 0 < len(huis) <= SAVE_FULL_HUI_LIMIT:
        p_full = HUI_DIR / f"{tag}.jsonl.gz"
        with gzip.open(p_full, "wt", encoding="utf-8") as fh:
            for x, u, s in huis:
                fh.write(json.dumps({"itemset": list(x), "utility": float(u),
                                     "support": int(s)}) + "\n")
        paths["full_huis"] = str(p_full)
        paths["full_huis_saved"] = True
    else:
        paths["full_huis_saved"] = False
        paths["full_huis_reason"] = (
            f"{len(huis)} HUIs exceeds SAVE_FULL_HUI_LIMIT={SAVE_FULL_HUI_LIMIT}"
            if len(huis) else "no HUIs")

    wap_stats = per_wap_statistics(huis) if huis else {}
    p_waps = HUI_DIR / f"{tag}__waps.json"
    dump_json({"n_waps_in_huis": len(wap_stats),
               "n_total_wap_columns": n_total_waps,
               "feature_reduction_pct": feature_reduction_pct(
                   len(wap_stats), n_total_waps),
               "rank_agreement_spearman_vs_utility_contribution":
                   rank_agreement(wap_stats) if wap_stats else {},
               "per_wap": wap_stats}, p_waps)
    paths["wap_stats"] = str(p_waps)
    return paths


def main() -> None:
    t_start = time.perf_counter()
    tr, _va = load_splits()
    prep = fit_preprocessor(tr)
    y = joint_label(tr)
    n_total_waps = len(prep.wap_cols)

    txs_all, det_counts = prep.transactions(tr)
    txs = [t for t in txs_all if t]
    n_empty = len(txs_all) - len(txs)
    LOG.info("utility database: %d non-empty transactions of %d rows "
             "(%d empty fingerprints dropped by the miner); %d WAP columns",
             len(txs), len(txs_all), n_empty, n_total_waps)

    model_diag = {}
    rows = []
    for code in MODELS:
        um = build_external_utility(code, tr, prep, y, "training")
        total_u = um.total_database_utility(txs)
        tus = um.transaction_utilities(txs)
        model_diag[um.name] = {
            **um.diagnostics,
            "total_database_utility": round(total_u, 6),
            "transaction_utility_min": round(float(tus.min()), 6),
            "transaction_utility_max": round(float(tus.max()), 6),
            "transaction_utility_mean": round(float(tus.mean()), 6),
            "transaction_utility_median": round(float(np.median(tus)), 6),
            "n_transactions": len(txs),
            "n_distinct_items_present": len({i for t in txs for i in t}),
        }
        LOG.info("=== %s === total DB utility %.2f, TU in [%.2f, %.2f]",
                 um.name, total_u, tus.min(), tus.max())

        for pct in GRID_PCT:
            mu = total_u * pct / 100.0
            tag = f"{um.name}__{pct:g}pct"
            with MemoryMonitor() as mem:
                t0 = time.perf_counter()
                huis, st = mine_efim(txs, um.external_utility, min_util=mu,
                                     time_limit_s=TIME_LIMIT_S,
                                     max_huis=MAX_HUIS)
                el = time.perf_counter() - t0
            dist = hui_length_distribution(huis)
            sel_union, _stats = select_waps(huis, "union") if huis else ([], {})
            paths = _save_hui_set(tag, huis, n_total_waps)

            row = {
                "run_tag": tag,
                "utility_model": um.name,
                "rel_minutil_pct": pct,
                "abs_minutil": round(mu, 6),
                "total_db_utility": round(total_u, 6),
                "n_transactions": len(txs),
                "n_wap_columns_total": n_total_waps,
                "status": st.status,
                "abort_reason": st.abort_reason or "",
                "runtime_s": round(el, 4),
                "peak_rss_mb": mem.as_dict()["peak_rss_mb"],
                "baseline_rss_mb": mem.as_dict()["baseline_rss_mb"],
                "peak_memory_delta_mb": mem.as_dict()["peak_delta_mb"],
                "n_huis": dist["n_huis"],
                "max_hui_len": dist["max_len"],
                "min_hui_len": dist["min_len"],
                "mean_hui_len": dist["mean_len"],
                "median_hui_len": dist["median_len"],
                "hui_utility_min": dist["utility_min"],
                "hui_utility_max": dist["utility_max"],
                "hui_utility_mean": dist["utility_mean"],
                "hui_support_mean": dist["support_mean"],
                "unique_waps_in_huis": len(sel_union),
                "selected_feature_count_union": len(sel_union),
                "feature_reduction_pct_union": feature_reduction_pct(
                    len(sel_union), n_total_waps),
                "items_initial": st.n_items_initial,
                "items_after_twu_pruning": st.n_items_after_twu_pruning,
                "items_pruned_by_local_utility": st.n_items_pruned_by_lu,
                "candidates_pruned_by_subtree_utility":
                    st.n_candidates_pruned_by_su,
                "search_nodes_visited": st.n_nodes_visited,
                "max_search_depth": st.max_depth_reached,
                "transactions_saved_by_merging":
                    st.n_transactions_saved_by_merging,
                "hui_length_distribution_json": json.dumps(dist["by_length"]),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                **{f"path_{k}": v for k, v in paths.items()},
            }
            rows.append(row)
            LOG.info("%-24s %6.3f%% (abs %12.2f) -> %8d HUIs | %7.2fs | "
                     "%7.1fMB | WAPs %3d | items %3d/%3d | %s",
                     um.name, pct, mu, dist["n_huis"], el,
                     mem.as_dict()["peak_delta_mb"], len(sel_union),
                     st.n_items_after_twu_pruning, st.n_items_initial,
                     st.status)
            # flush after every run so a crash never loses finished work
            pd.DataFrame(rows).to_csv(METRICS / "huim_runs.csv", index=False)
            if st.status != "COMPLETED":
                LOG.warning("  descent stopped for %s at %g%% (%s)",
                            um.name, pct, st.abort_reason)
                break

    summary = {
        "phase": "PHASE H - full HUIM experiment",
        "environment": environment_info(),
        "grid_pct": GRID_PCT,
        "time_limit_s": TIME_LIMIT_S,
        "max_huis": MAX_HUIS,
        "save_full_hui_limit": SAVE_FULL_HUI_LIMIT,
        "preprocessor": prep.as_dict(),
        "database": {
            "n_rows": int(len(tr)),
            "n_non_empty_transactions": len(txs),
            "n_empty_fingerprints_dropped": n_empty,
            "detections_per_transaction_mean": round(
                float(det_counts[det_counts > 0].mean()), 4),
            "n_wap_columns": n_total_waps,
        },
        "utility_models": model_diag,
        "runs": rows,
        "total_wall_clock_s": round(time.perf_counter() - t_start, 2),
    }
    dump_json(summary, RESULTS / "huim_summary.json")
    LOG.info("done in %.1fs; %d runs -> %s",
             time.perf_counter() - t_start, len(rows), METRICS / "huim_runs.csv")


if __name__ == "__main__":
    main()
