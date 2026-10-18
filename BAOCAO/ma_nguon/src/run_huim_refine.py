"""PHASE H (stage 2) - adaptive refinement of the minUtil grid.

The starting grid is explicitly a hypothesis, and the stage-1 results falsified
its resolution: for Model A the output goes from 2 HUIs at 2.5% to over a
million at 2.0%. A grid that steps straight across a phase transition cannot
describe it.

This script therefore brackets, per utility model, the interval between

    lo_pct = the lowest threshold that COMPLETED
    hi_pct = the highest threshold that ABORTED            (hi_pct < lo_pct)

and evaluates geometric interior points by bisection, keeping whichever side
needs resolving. Two things come out of it:

  * a description of the transition instead of a jump across it;
  * the richest *non-truncated* HUI set per model, which is what the feature
    selection experiment needs (a truncated HUI list is biased by DFS order and
    must not be used to rank APs).

New rows are appended to results/metrics/huim_runs.csv with the same schema, so
every downstream consumer picks them up without change.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_selection import (feature_reduction_pct, hui_length_distribution,
                               select_waps)
from huim.efim import mine_efim
from preprocess_uji import fit_preprocessor, joint_label, load_splits
from run_huim import MAX_HUIS, TIME_LIMIT_S, _save_hui_set
from utils import METRICS, MemoryMonitor, RESULTS, dump_json, get_logger
from utility_models import build_external_utility

LOG = get_logger("refine", "huim_refine.log")

MAX_BISECTIONS = 3
# A completed run is "rich enough" once it has this many HUIs: beyond that the
# per-WAP ranking is stable and further refinement buys nothing.
RICH_ENOUGH_HUIS = 20_000


def main() -> None:
    runs = pd.read_csv(METRICS / "huim_runs.csv")
    tr, _va = load_splits()
    prep = fit_preprocessor(tr)
    y = joint_label(tr)
    n_total_waps = len(prep.wap_cols)
    txs = [t for t in prep.transactions(tr)[0] if t]

    new_rows: list[dict] = []
    plan = {}
    for model, g in runs.groupby("utility_model"):
        comp = g[g["status"] == "COMPLETED"]
        ab = g[g["status"] != "COMPLETED"]
        if not len(ab):
            # Nothing aborted: the grid never reached the transition. Extend it
            # downwards geometrically instead of bisecting, but only while the
            # richest completed run is still thin - otherwise there is nothing
            # left to learn and we would just be burning the budget.
            lo = float(comp["rel_minutil_pct"].min())
            richest = int(comp["n_huis"].max())
            if richest >= RICH_ENOUGH_HUIS:
                LOG.info("%s: nothing aborted and richest completed run has "
                         "%d HUIs (>= %d); no extension needed",
                         model, richest, RICH_ENOUGH_HUIS)
                continue
            LOG.info("%s: nothing aborted; extending the grid below %g%% "
                     "(richest completed run so far: %d HUIs)",
                     model, lo, richest)
            plan[model] = {"mode": "extend_downwards",
                           "lo_completed_pct": lo,
                           "hi_aborted_pct": lo / (2 ** MAX_BISECTIONS),
                           "n_huis_at_lo": int(
                               comp[comp["rel_minutil_pct"] == lo]
                               ["n_huis"].iloc[0]),
                           "best_completed_n_huis": richest}
            continue
        lo = float(comp["rel_minutil_pct"].min()) if len(comp) else None
        hi = float(ab["rel_minutil_pct"].max())
        if lo is None or lo <= hi:
            LOG.warning("%s: no usable bracket (lo=%s hi=%s)", model, lo, hi)
            continue
        best_completed = (comp.loc[comp["n_huis"].idxmax()]
                          if len(comp) else None)
        plan[model] = {"mode": "bisect", "lo_completed_pct": lo,
                       "hi_aborted_pct": hi,
                       "n_huis_at_lo": int(comp[comp["rel_minutil_pct"] == lo]
                                           ["n_huis"].iloc[0]),
                       "best_completed_n_huis": int(best_completed["n_huis"])
                       if best_completed is not None else 0}
        LOG.info("%s: bracket (%g%% COMPLETED, %d HUIs) .. (%g%% ABORTED)",
                 model, lo, plan[model]["n_huis_at_lo"], hi)

    for model, br in plan.items():
        code = {"A_signal": "A", "B_discriminative": "B",
                "C_rare_discriminative": "C"}[model]
        um = build_external_utility(code, tr, prep, y, "training")
        total_u = um.total_database_utility(txs)
        lo, hi = br["lo_completed_pct"], br["hi_aborted_pct"]
        best_n = br["best_completed_n_huis"]

        for it in range(MAX_BISECTIONS):
            if best_n >= RICH_ENOUGH_HUIS:
                LOG.info("%s: already have a completed run with %d HUIs "
                         "(>= %d); stopping refinement", model, best_n,
                         RICH_ENOUGH_HUIS)
                break
            if br.get("mode") == "extend_downwards":
                mid = round(lo / 2.0, 6)         # geometric step downwards
                if mid <= 0:
                    break
            else:
                mid = round(float(np.sqrt(lo * hi)), 4)   # geometric midpoint
                if mid >= lo or mid <= hi:
                    LOG.info("%s: bracket exhausted at numeric resolution",
                             model)
                    break
            mu = total_u * mid / 100.0
            tag = f"{um.name}__{mid:g}pct"
            with MemoryMonitor() as mem:
                t0 = time.perf_counter()
                huis, st = mine_efim(txs, um.external_utility, min_util=mu,
                                     time_limit_s=TIME_LIMIT_S,
                                     max_huis=MAX_HUIS)
                el = time.perf_counter() - t0
            dist = hui_length_distribution(huis)
            sel_union, _ = select_waps(huis, "union") if huis else ([], {})
            paths = _save_hui_set(tag, huis, n_total_waps)
            new_rows.append({
                "run_tag": tag, "utility_model": um.name,
                "rel_minutil_pct": mid, "abs_minutil": round(mu, 6),
                "total_db_utility": round(total_u, 6),
                "n_transactions": len(txs), "n_wap_columns_total": n_total_waps,
                "status": st.status, "abort_reason": st.abort_reason or "",
                "runtime_s": round(el, 4),
                "peak_rss_mb": mem.as_dict()["peak_rss_mb"],
                "baseline_rss_mb": mem.as_dict()["baseline_rss_mb"],
                "peak_memory_delta_mb": mem.as_dict()["peak_delta_mb"],
                "n_huis": dist["n_huis"], "max_hui_len": dist["max_len"],
                "min_hui_len": dist["min_len"], "mean_hui_len": dist["mean_len"],
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
                "refinement_iteration": it + 1,
                **{f"path_{k}": v for k, v in paths.items()},
            })
            LOG.info("%-24s %7.4f%% -> %8d HUIs | %7.2fs | %7.1fMB | "
                     "WAPs %3d | %s", um.name, mid, dist["n_huis"], el,
                     mem.as_dict()["peak_delta_mb"], len(sel_union), st.status)
            if st.status == "COMPLETED":
                lo = mid
                best_n = max(best_n, dist["n_huis"])
            else:
                hi = mid
                # the transition has now been bracketed, so stop stepping and
                # start bisecting the interval we just found
                br["mode"] = "bisect"
            pd.concat([runs, pd.DataFrame(new_rows)]).to_csv(
                METRICS / "huim_runs.csv", index=False)

    if new_rows:
        out = pd.concat([runs, pd.DataFrame(new_rows)])
        out = out.sort_values(["utility_model", "rel_minutil_pct"],
                              ascending=[True, False])
        out.to_csv(METRICS / "huim_runs.csv", index=False)
    dump_json({"phase": "PHASE H stage 2 - adaptive grid refinement",
               "rationale": "the stage-1 grid stepped across the phase "
                            "transition instead of describing it",
               "max_bisections": MAX_BISECTIONS,
               "rich_enough_huis": RICH_ENOUGH_HUIS,
               "brackets": plan, "new_runs": new_rows},
              RESULTS / "huim_refinement.json")
    LOG.info("added %d refinement runs", len(new_rows))


if __name__ == "__main__":
    main()
