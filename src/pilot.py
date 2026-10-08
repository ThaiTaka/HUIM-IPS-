"""PHASE G - pilot run.

Purpose: find out, cheaply, where the interesting minUtil range actually is
before committing the full 19,937-transaction database to a grid. The brief's
starting grid (5%, 2%, 1%, 0.5%, 0.2%, 0.1% of total database utility) is a
*hypothesis*; this script tests it on a stratified subsample and reports what
the thresholds really produce.

Output: results/metrics/pilot_runs.csv, results/pilot_summary.json
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim.efim import mine_efim
from preprocess_uji import fit_preprocessor, joint_label, load_splits
from utils import METRICS, MemoryMonitor, RESULTS, dump_json, get_logger
from utility_models import build_external_utility

LOG = get_logger("pilot", "pilot.log")

PILOT_ROWS = 2500
PILOT_SEED = 20251007
PILOT_GRID_PCT = [5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
TIME_LIMIT_S = 120.0
MAX_HUIS = 300_000


def main() -> None:
    tr, _va = load_splits()
    prep = fit_preprocessor(tr)
    y = joint_label(tr)

    rng = np.random.default_rng(PILOT_SEED)
    # stratified subsample so every building/floor class survives
    idx = []
    for cls in np.unique(y):
        pool = np.flatnonzero(y == cls)
        take = max(1, int(round(PILOT_ROWS * len(pool) / len(y))))
        idx.extend(rng.choice(pool, size=min(take, len(pool)), replace=False))
    idx = np.sort(np.array(idx))
    sub = tr.iloc[idx]
    LOG.info("pilot subsample: %d rows, %d classes", len(sub), len(np.unique(y[idx])))

    txs_all, _ = prep.transactions(sub)
    txs = [t for t in txs_all if t]
    n_empty = len(txs_all) - len(txs)
    LOG.info("pilot transactions: %d non-empty (%d empty dropped)", len(txs), n_empty)

    rows = []
    for code in ("A", "B", "C"):
        # NOTE: p is still estimated from the FULL trainingData, not from the
        # subsample, because p is part of the model definition, not of the pilot.
        um = build_external_utility(code, tr, prep, y, "training")
        total_u = um.total_database_utility(txs)
        LOG.info("model %s: total pilot DB utility = %.2f", um.name, total_u)
        for pct in PILOT_GRID_PCT:
            mu = total_u * pct / 100.0
            with MemoryMonitor() as mem:
                t0 = time.perf_counter()
                huis, st = mine_efim(txs, um.external_utility, min_util=mu,
                                     time_limit_s=TIME_LIMIT_S,
                                     max_huis=MAX_HUIS)
                el = time.perf_counter() - t0
            lens = [len(x) for x, _u, _s in huis]
            rows.append({
                "utility_model": um.name, "rel_minutil_pct": pct,
                "abs_minutil": round(mu, 4),
                "total_db_utility": round(total_u, 4),
                "n_transactions": len(txs),
                "n_huis": len(huis), "status": st.status,
                "runtime_s": round(el, 4),
                "peak_delta_mb": mem.as_dict()["peak_delta_mb"],
                "items_after_twu_pruning": st.n_items_after_twu_pruning,
                "items_initial": st.n_items_initial,
                "nodes_visited": st.n_nodes_visited,
                "max_hui_len": max(lens) if lens else 0,
                "mean_hui_len": round(float(np.mean(lens)), 3) if lens else 0.0,
                "unique_waps_in_huis": len({w for x, _u, _s in huis for w in x}),
            })
            LOG.info("  %-22s %6.3f%% -> %7d HUIs | %6.2fs | %6.1fMB | "
                     "items %3d/%3d | %s", um.name, pct, len(huis), el,
                     mem.as_dict()["peak_delta_mb"],
                     st.n_items_after_twu_pruning, st.n_items_initial, st.status)
            if st.status != "COMPLETED":
                LOG.info("  -> aborted; stopping descent for %s", um.name)
                break

    df = pd.DataFrame(rows)
    df.to_csv(METRICS / "pilot_runs.csv", index=False)
    dump_json({"pilot_rows_requested": PILOT_ROWS,
               "pilot_rows_used": int(len(sub)),
               "pilot_empty_transactions_dropped": n_empty,
               "pilot_seed": PILOT_SEED,
               "grid_pct": PILOT_GRID_PCT,
               "time_limit_s": TIME_LIMIT_S, "max_huis": MAX_HUIS,
               "runs": rows}, RESULTS / "pilot_summary.json")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
