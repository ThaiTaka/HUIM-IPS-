"""PHASE Q - run the HUIM-only positioner (src/huim_positioning.py) on every
dataset. No k-NN anywhere: the model is the per-cell HUI sets.

    select   for theta in THETA_GRID and every dev fold of the training data
             (src/run_multi_dataset.folds_for: leave-users-out on UJIIndoorLoc):
             mine the cells of the training part, score the held-out part for
             every (gamma, tau, beta, m, p) of the grid; the configuration with
             the lowest dev mean error over all folds is SELECTED
             -> dev_grid.csv, selection.json
    final    mine every cell on the full training data with the selected
             theta, position every test fingerprint ONCE
             -> model/ (every HUI of every cell), cell_runs.csv,
                predictions/<test>.csv, test_results.csv, summary.json

Outputs: results/huim_only/<dataset>/
Run:     python src/run_huim_only.py --dataset uji
"""
from __future__ import annotations

import argparse
import itertools
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_positioning import (CELL_MAX_HUIS, CELL_TIME_S, ESCALATE,
                              HUIPositioner, Params)
from multi_datasets import DATASETS, Bundle, bf_label, load
from preprocess_uji import fit_preprocessor
from run_multi_dataset import folds_for, metrics
from utils import RESULTS, dump_json, environment_info, get_logger, load_json

OUT_ROOT = RESULTS / "huim_only"
THETA_GRID = [30.0, 50.0, 70.0]
GT_GRID = [(1.0, 10.0), (1.0, 20.0), (1.0, 40.0), (2.0, 10.0), (2.0, 20.0),
           (2.0, 40.0)]
BETA_GRID = [1.0, 3.0, 5.0]
M_GRID = [3, 5, 8, 12]
P_GRID = [2.0, 4.0, 8.0]
TARGET_M = 7.0
ORDER = ["uji", "uji_lib3", "dlulib", "hcxy", "hus", "hus_dedup"]
LOG = get_logger("huim_only", "huim_only.log")
logging.getLogger("preprocess").setLevel(logging.WARNING)


def outdir(key: str) -> Path:
    p = OUT_ROOT / key
    (p / "predictions").mkdir(parents=True, exist_ok=True)
    (p / "model").mkdir(exist_ok=True)
    return p


def inputs(b: Bundle):
    tr = b.train
    prep = fit_preprocessor(tr)
    Q = prep.internal_utility_matrix(tr).astype(np.float64)
    return prep, Q, tr["RP"].to_numpy(), tr[["X", "Y"]].to_numpy(np.float64), bf_label(tr)


def err_m(xy, true_xy, gf):
    return np.sqrt(((xy - true_xy) ** 2).sum(axis=1)) * gf


# ===================================================================== select
def stage_select(b: Bundle) -> None:
    out = outdir(b.key)
    _prep, Q, cell, XY, BF = inputs(b)
    folds = folds_for(b, len(Q))
    configs = [Params(g, t, be, m, p) for (g, t), be, m, p in
               itertools.product(GT_GRID, BETA_GRID, M_GRID, P_GRID)]
    rows = []
    for theta in THETA_GRID:
        err = {i: np.zeros(len(Q)) for i in range(len(configs))}
        flo = {i: np.zeros(len(Q), bool) for i in range(len(configs))}
        t0 = time.perf_counter()
        n_huis = []
        for tri, dvi in folds:
            pos = HUIPositioner(theta).fit(Q[tri], cell[tri], XY[tri], BF[tri])
            n_huis.append(len(pos.hui_items))
            P, V = pos.components(Q[dvi], GT_GRID)
            for i, prm in enumerate(configs):
                xy, bf, *_ = pos.estimate(P[(prm.gamma, prm.tau)], V, prm)
                err[i][dvi] = err_m(xy, XY[dvi], b.ground_factor)
                flo[i][dvi] = bf == BF[dvi]
        for i, prm in enumerate(configs):
            e = err[i]
            rows.append({"theta_pct": theta, **asdict(prm),
                         "dev_mean_m": round(float(e.mean()), 4),
                         "dev_median_m": round(float(np.median(e)), 4),
                         "dev_p90_m": round(float(np.percentile(e, 90)), 4),
                         "dev_joint_accuracy": round(float(flo[i].mean()), 6)})
        D = pd.DataFrame(rows)
        D.to_csv(out / "dev_grid.csv", index=False)
        best = D[D.theta_pct == theta].sort_values("dev_mean_m").iloc[0]
        LOG.info("%s theta %g: %d folds in %.0fs, HUIs/fold %s; best dev %.3f m "
                 "(%s)", b.key, theta, len(folds), time.perf_counter() - t0,
                 n_huis, best.dev_mean_m,
                 Params(best.gamma, best.tau, best.beta, int(best.m), best.p).label())
    D = pd.DataFrame(rows)
    best = D.sort_values(["dev_mean_m", "theta_pct"], ascending=[True, False]).iloc[0]
    prm = Params(float(best.gamma), float(best.tau), float(best.beta),
                 int(best.m), float(best.p))
    dump_json({"dataset": b.key, "theta_pct": float(best.theta_pct),
               "params": asdict(prm), "label": prm.label(),
               "dev_mean_m": float(best.dev_mean_m),
               "dev_median_m": float(best.dev_median_m),
               "dev_joint_accuracy": float(best.dev_joint_accuracy),
               "dev_folds": f"{len(folds)} folds, {b.group_note}",
               "n_configurations": len(D),
               "grids": {"theta_pct": THETA_GRID, "gamma_tau": GT_GRID,
                         "beta": BETA_GRID, "m": M_GRID, "p": P_GRID},
               "rule": "lowest dev mean error over all dev rows; ties -> "
                       "larger theta (fewer HUIs)",
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              out / "selection.json")
    LOG.info("%s SELECTED on dev: theta %g%%, %s -> dev %.3f m", b.key,
             best.theta_pct, prm.label(), best.dev_mean_m)


# ====================================================================== final
def stage_final(b: Bundle) -> None:
    out = outdir(b.key)
    sel = load_json(out / "selection.json")
    prm = Params(**sel["params"])
    prep, Q, cell, XY, BF = inputs(b)
    pos = HUIPositioner(sel["theta_pct"]).fit(Q, cell, XY, BF)
    LOG.info("%s final model: %d cells, %d HUIs, mined in %.1fs", b.key,
             len(pos.cells), len(pos.hui_items), pos.fit_seconds)
    lens = np.array([len(x) for x in pos.hui_items])
    np.savez_compressed(out / "model" / "huis.npz",
                        indptr=np.concatenate([[0], np.cumsum(lens)]),
                        items=np.concatenate(pos.hui_items) if len(lens) else np.zeros(0, int),
                        utility=pos.hui_util, support=pos.hui_supp,
                        cell_index=pos.hui_cell)
    pd.DataFrame({"cell_index": np.arange(len(pos.cells)), "cell": pos.cells,
                  "x": pos.cell_xy[:, 0], "y": pos.cell_xy[:, 1],
                  "building_floor": pos.cell_bf}).to_csv(out / "model" / "cells.csv", index=False)
    runs = pd.DataFrame(pos.cell_runs)
    runs.to_csv(out / "cell_runs.csv", index=False)
    rows, tests = [], {}
    for tname, te in b.tests.items():
        Qt = prep.internal_utility_matrix(te).astype(np.float64)
        t0 = time.perf_counter()
        xy, bf, top, a, sc = pos.predict(Qt, prm)
        ms = (time.perf_counter() - t0) / len(Qt) * 1000.0
        m = metrics(te, bf, xy, b.ground_factor)
        P = pd.DataFrame({"src_file": te["SRC_FILE"].to_numpy(),
                          "src_row": te["SRC_ROW"].to_numpy(),
                          "true_building": te["BUILDINGID"].to_numpy(),
                          "true_floor": te["FLOOR"].to_numpy(),
                          "pred_building_floor": bf,
                          "true_x": te["X"].to_numpy(), "true_y": te["Y"].to_numpy(),
                          "pred_x": xy[:, 0], "pred_y": xy[:, 1]})
        P["err_m"] = err_m(xy, te[["X", "Y"]].to_numpy(np.float64), b.ground_factor)
        for j in range(top.shape[1]):
            P[f"cell{j + 1}_index"] = top[:, j]
            P[f"cell{j + 1}_score"] = sc[:, j]
            P[f"cell{j + 1}_weight"] = a[:, j]
        P.to_csv(out / "predictions" / f"{tname}.csv", index=False)
        rows.append({"test_set": tname, **m, "ms_per_fp": round(ms, 4)})
        tests[tname] = {**m, "ms_per_fp": round(ms, 4),
                        "below_target": bool(m["mean_err_m"] < TARGET_M)}
        LOG.info("%s %s: HUIM-only mean %.3f m, median %.3f m, joint %.4f, "
                 "%.2f ms/fp", b.key, tname, m["mean_err_m"], m["median_err_m"],
                 m["joint_accuracy"], ms)
    pd.DataFrame(rows).to_csv(out / "test_results.csv", index=False)
    dump_json({"dataset": b.key, "title": b.title, "selection": sel,
               "model": {"n_cells": int(len(pos.cells)),
                         "n_huis": int(len(pos.hui_items)),
                         "mining_seconds": round(pos.fit_seconds, 2),
                         "cells_escalated": int((runs.n_attempts > 1).sum()),
                         "theta_used_median_pct": float(runs.theta_used_pct.median()),
                         "cell_time_limit_s": CELL_TIME_S,
                         "cell_max_huis": CELL_MAX_HUIS, "escalate": ESCALATE,
                         "n_aps": int(Q.shape[1]),
                         "aps_in_some_hui": int(len(np.unique(np.concatenate(pos.hui_items))))
                         if len(pos.hui_items) else 0},
               "tests": tests, "target_m": TARGET_M,
               "environment": environment_info(),
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              out / "summary.json")


STAGES = {"select": stage_select, "final": stage_final}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="all")
    ap.add_argument("--stage", default="all", choices=["all", *STAGES])
    a = ap.parse_args()
    keys = ORDER if a.dataset == "all" else a.dataset.split(",")
    for key in keys:
        if key not in DATASETS:
            raise SystemExit(f"unknown dataset {key}")
        b = load(key)
        for st in (STAGES if a.stage == "all" else [a.stage]):
            t0 = time.perf_counter()
            STAGES[st](b)
            LOG.info("%s stage %s done in %.0fs", key, st, time.perf_counter() - t0)


if __name__ == "__main__":
    main()
