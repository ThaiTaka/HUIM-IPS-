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
                              internal_utility,
                              HUIPositioner, Params)
from multi_datasets import DATASETS, Bundle, bf_label, load
from preprocess_uji import fit_preprocessor
from run_multi_dataset import folds_for as _folds_default, metrics
from sklearn.model_selection import GroupKFold
from utils import RESULTS, dump_json, environment_info, get_logger, load_json

OUT_ROOT = RESULTS / "huim_only"
THETA_GRID = [10.0, 20.0, 30.0]
GT_GRID = [(1.0, 20.0), (1.0, 40.0), (2.0, 20.0)]
BETA_GRID = [1.0, 3.0]
SIGMA_GRID = [0.0, 3.0, 6.0, 10.0]
KF_GRID = [3, 10]
M_GRID = [5, 8, 12]
P_GRID = [4.0, 8.0]
# UJIIndoorLoc: theta = 10% costs ~25 min per fold, so it was fixed beforehand
# by a pilot on dev folds 1 and 2 (theta_pilot.json); the test data played no part.
THETA_BY_DATASET = {"uji": [20.0]}
THETA_NOTE = {"uji": "fixed at 20% (pilot on dev folds, theta_pilot.json): "
                     "10% mines ~4M HUIs per fold and, with user folds, did not "
                     "transfer to new phones; every other parameter, and the "
                     "internal utility, chosen on all 6 dev folds"}
# internal utility q(i,T): huim_positioning.internal_utility
UTILITY_BY_DATASET = {"uji": ["abs", "rel", "rank"]}
# UJIIndoorLoc: 9 of the 11 validationData phones never occur in trainingData,
# so the dev folds hold out PHONES (leave-devices-out) rather than users
FOLD_GROUP = {"uji": "PHONEID"}
FOLD_NOTE = {"uji": "PHONEID - leave-phones-out (GroupKFold over the 16 "
                    "training phones): validationData is 9 unseen phones of 11"}
TARGET_M = 7.0
ORDER = ["uji", "uji_lib3", "dlulib", "hcxy", "hus", "hus_dedup"]
LOG = get_logger("huim_only", "huim_only.log")
logging.getLogger("preprocess").setLevel(logging.WARNING)


def outdir(key: str) -> Path:
    p = OUT_ROOT / key
    (p / "predictions").mkdir(parents=True, exist_ok=True)
    (p / "model").mkdir(exist_ok=True)
    return p


def utilities(key: str) -> list[str]:
    return UTILITY_BY_DATASET.get(key, ["abs"])


def folds_for(b: Bundle, n: int):
    col = FOLD_GROUP.get(b.key)
    if col:
        return list(GroupKFold(n_splits=6).split(np.zeros(n), groups=b.train[col]))
    return _folds_default(b, n)


def fold_note(b: Bundle) -> str:
    col = FOLD_GROUP.get(b.key)
    return FOLD_NOTE[b.key] if col else b.group_note


def q_matrix(prep, df, kind: str) -> np.ndarray:
    W = df[prep.wap_cols].to_numpy(np.float64)
    return internal_utility(W, kind, prep.rssi_min_train, prep.rssi_max_train)


def inputs(b: Bundle, kind: str = "abs"):
    tr = b.train
    prep = fit_preprocessor(tr)
    Q = q_matrix(prep, tr, kind)
    return prep, Q, tr["RP"].to_numpy(), tr[["X", "Y"]].to_numpy(np.float64), bf_label(tr)


def params_of(r) -> Params:
    return Params(float(r.gamma), float(r.tau), float(r.beta), int(r.m),
                  float(r.p), float(r.sigma), int(r.kf))


def err_m(xy, true_xy, gf):
    return np.sqrt(((xy - true_xy) ** 2).sum(axis=1)) * gf


# ===================================================================== select
def thetas(key: str) -> list[float]:
    return THETA_BY_DATASET.get(key, THETA_GRID)


def grid():
    outer = list(itertools.product(GT_GRID, BETA_GRID, SIGMA_GRID))
    inner = list(itertools.product(KF_GRID, M_GRID, P_GRID))
    configs = [Params(g, t, be, m, p, sg, kf) for (g, t), be, sg in outer
               for kf, m, p in inner]
    return outer, inner, configs


def part_path(out: Path, kind: str, theta: float, fold: int) -> Path:
    return out / "dev_parts" / f"{kind}_theta{theta:g}_fold{fold}.npz"


def stage_dev_part(b: Bundle, theta: float, fold: int, kind: str = "abs") -> None:
    """One (theta, dev fold): mine the training part, score the held-out part
    for every configuration. Written to dev_parts/ so folds can run in
    parallel processes."""
    out = outdir(b.key)
    (out / "dev_parts").mkdir(exist_ok=True)
    _prep, Q, cell, XY, BF = inputs(b, kind)
    tri, dvi = folds_for(b, len(Q))[fold]
    outer, inner, configs = grid()
    t0 = time.perf_counter()
    pos = HUIPositioner(theta, ground_factor=b.ground_factor).fit(
        Q[tri], cell[tri], XY[tri], BF[tri])
    P, V = pos.components(Q[dvi], GT_GRID)
    err = np.zeros((len(configs), len(dvi)), np.float32)
    flo = np.zeros((len(configs), len(dvi)), bool)
    i = 0
    for (g, t), be, sg in outer:
        S = pos.cell_scores(P[(g, t)], V, be, sg)
        fl = {kf: pos.floor_of(S, kf) for kf in KF_GRID}
        for kf, m, p in inner:
            xy, *_ = pos.locate(S, fl[kf], m, p)
            err[i] = err_m(xy, XY[dvi], b.ground_factor)
            flo[i] = fl[kf] == BF[dvi]
            i += 1
    np.savez_compressed(part_path(out, kind, theta, fold),
                        dvi=dvi, err=err, flo=flo, n_huis=len(pos.hui_items),
                        mining_s=pos.fit_seconds,
                        seconds=time.perf_counter() - t0)
    LOG.info("%s dev part %s theta %g fold %d: %d HUIs, mined %.0fs, total %.0fs",
             b.key, kind, theta, fold, len(pos.hui_items), pos.fit_seconds,
             time.perf_counter() - t0)


def stage_select(b: Bundle) -> None:
    """Merge the dev parts (running any that are missing) and select."""
    out = outdir(b.key)
    n = len(b.train)
    folds = folds_for(b, n)
    _o, _i, configs = grid()
    rows = []
    for kind, theta in itertools.product(utilities(b.key), thetas(b.key)):
        err = np.zeros((len(configs), n))
        flo = np.zeros((len(configs), n), bool)
        info = []
        for k in range(len(folds)):
            f = part_path(out, kind, theta, k)
            if not f.exists():
                stage_dev_part(b, theta, k, kind)
            z = np.load(f)
            err[:, z["dvi"]] = z["err"]
            flo[:, z["dvi"]] = z["flo"]
            info.append(int(z["n_huis"]))
        for i, prm in enumerate(configs):
            e = err[i]
            rows.append({"utility": kind, "theta_pct": theta, **asdict(prm),
                         "dev_mean_m": round(float(e.mean()), 4),
                         "dev_median_m": round(float(np.median(e)), 4),
                         "dev_p90_m": round(float(np.percentile(e, 90)), 4),
                         "dev_joint_accuracy": round(float(flo[i].mean()), 6)})
        D = pd.DataFrame(rows)
        best = D[(D.theta_pct == theta) & (D.utility == kind)].sort_values("dev_mean_m").iloc[0]
        LOG.info("%s %s theta %g: HUIs/fold %s; best dev %.3f m (%s)", b.key, kind, theta,
                 info, best.dev_mean_m, params_of(best).label())
    D = pd.DataFrame(rows)
    D.to_csv(out / "dev_grid.csv", index=False)
    best = D.sort_values(["dev_mean_m", "theta_pct"], ascending=[True, False]).iloc[0]
    prm = params_of(best)
    dump_json({"dataset": b.key, "utility": str(best.utility),
               "theta_pct": float(best.theta_pct),
               "params": asdict(prm), "label": prm.label(),
               "dev_mean_m": float(best.dev_mean_m),
               "dev_median_m": float(best.dev_median_m),
               "dev_joint_accuracy": float(best.dev_joint_accuracy),
               "dev_folds": f"{len(folds)} folds, {fold_note(b)}",
               "n_configurations": len(D),
               "grids": {"utility": utilities(b.key),
                         "theta_pct": thetas(b.key), "gamma_tau": GT_GRID,
                         "beta": BETA_GRID, "sigma_m": SIGMA_GRID,
                         "kf": KF_GRID, "m": M_GRID, "p": P_GRID},
               "theta_note": THETA_NOTE.get(b.key, "theta chosen on the dev folds "
                                                   "with the other parameters"),
               "rule": "lowest dev mean error over all dev rows; ties -> "
                       "larger theta (fewer HUIs)",
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              out / "selection.json")
    LOG.info("%s SELECTED on dev: utility %s, theta %g%%, %s -> dev %.3f m",
             b.key, best.utility, best.theta_pct, prm.label(), best.dev_mean_m)


# ====================================================================== final
def stage_final(b: Bundle) -> None:
    out = outdir(b.key)
    sel = load_json(out / "selection.json")
    prm = Params(**sel["params"])
    kind = sel.get("utility", "abs")
    prep, Q, cell, XY, BF = inputs(b, kind)
    pos = HUIPositioner(sel["theta_pct"], ground_factor=b.ground_factor).fit(Q, cell, XY, BF)
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
        Qt = q_matrix(prep, te, kind)
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
    ap.add_argument("--stage", default="all", choices=["all", "dev_part", *STAGES])
    ap.add_argument("--theta", type=float)
    ap.add_argument("--fold", type=int)
    ap.add_argument("--utility", default="abs")
    a = ap.parse_args()
    if a.stage == "dev_part":
        stage_dev_part(load(a.dataset), a.theta, a.fold, a.utility)
        return
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
