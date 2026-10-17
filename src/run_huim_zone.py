"""PHASE Z - zone-wise HUIM selects the APs, the PHASE I3 positioner uses them.

Pipeline per dataset (results/huim_zone/<key>/):

    mine      for utility Models A and B and every theta in THETA_GRID:
              EFIM per zone (src/huim_zone.py) on the training data
              -> zone_mining.csv (one row per zone run), hui/<set>.json
                 (per zone: minUtil, the selected WAPs, one witness HUI per
                 WAP, the top HUIs), ap_sets.json
    select    the dataset's own PHASE I3 positioner (positioning.json, chosen
              on its dev folds with all APs, never on test data) is run on the
              SAME dev folds with each HUIM-zone AP set; the set with the
              lowest dev mean error is SELECTED  -> dev_selection.csv
    evaluate  every AP set, the all-AP baseline and matched-budget controls
              (top-n by detection count, top-n by mutual information, 3 random
              draws) on every test set, ONCE each -> test_results.csv,
              predictions/<test>__huim_zone.csv, selected.json

The test data appears only in `evaluate`. Every theta is reported there so the
curve can be drawn, but the selected set was fixed by `select` beforehand.

Run
    python src/run_huim_zone.py --dataset all
    python src/run_huim_zone.py --dataset uji --stage select
"""
from __future__ import annotations

import argparse
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
import optimize_positioning as op
from huim_zone import (ESCALATE, MAX_ESCALATIONS, MAX_HUIS, N_SPATIAL_ZONES, ZoneCache,
                       ZONE_TIME_S, mine_all_zones, union_waps, zone_labels)
from multi_datasets import DATASETS, Bundle, bf_label, class_label, load
from preprocess_uji import NOT_DETECTED, fit_preprocessor
from run_ips import CONTROL_SEEDS
from run_multi_dataset import folds_for, metrics, pred_frame
from utility_models import (build_external_utility,
                            conditional_entropy_reduction, discretise)
from utils import RESULTS, dump_json, environment_info, get_logger, load_json

OUT_ROOT = RESULTS / "huim_zone"
MULTI = RESULTS / "multi_dataset"
THETA_GRID = [10.0, 7.0, 5.0, 4.0, 3.0]
MODELS = {"A": "A_signal", "B": "B_discriminative"}
TARGET_M = 7.0
ORDER = ["uji", "uji_lib3", "dlulib", "hcxy", "hus", "hus_dedup"]
LOG = get_logger("huim_zone", "huim_zone.log")
logging.getLogger("preprocess").setLevel(logging.WARNING)


def outdir(key: str) -> Path:
    p = OUT_ROOT / key
    (p / "hui").mkdir(parents=True, exist_ok=True)
    (p / "predictions").mkdir(exist_ok=True)
    return p


def set_name(code: str, theta: float) -> str:
    return f"huim_zone__{MODELS[code]}__{theta:g}pct"


def positioner_config(key: str) -> op.Config:
    return op.Config(**load_json(MULTI / key / "positioning.json")
                     ["selected_config"])


# ======================================================================= mine
def stage_mine(b: Bundle) -> None:
    out = outdir(b.key)
    tr = b.train
    prep = fit_preprocessor(tr)
    wap = prep.wap_cols
    txs = prep.transactions(tr)[0]
    zones, zone_rule = zone_labels(tr)
    y = class_label(b, tr)
    rows, sets = [], {}
    for code in MODELS:
        um = build_external_utility(code, tr, prep, y, "training")
        cache = ZoneCache()
        for theta in sorted(THETA_GRID, reverse=True):
            t0 = time.perf_counter()
            runs = mine_all_zones(txs, zones, um.external_utility, theta, cache)
            S = union_waps(runs, wap)
            name = set_name(code, theta)
            sets[name] = S
            for r in runs:
                rows.append({"set": name, "utility_model": um.name,
                             "theta_pct": theta, **r.row()})
            dump_json({"set": name, "dataset": b.key,
                       "utility_model": um.name, "theta_pct": theta,
                       "zone_rule": zone_rule, "selected_waps": S,
                       "external_utility": {w: um.external_utility[w]
                                            for w in wap},
                       "zones": [{**r.row(), "waps": r.waps,
                                  "witnesses": r.witnesses,
                                  "top_huis": r.top_huis} for r in runs]},
                      out / "hui" / f"{name}.json")
            pd.DataFrame(rows).to_csv(out / "zone_mining.csv", index=False)
            LOG.info("%s %-36s %3d zones -> %4d/%d WAPs  %.1fs  (escalated "
                     "zones: %d)", b.key, name, len(runs), len(S), len(wap),
                     time.perf_counter() - t0,
                     sum(r.n_attempts > 1 for r in runs))
    dump_json({"dataset": b.key, "zone_rule": zone_rule,
               "n_zones": int(len(set(zones))),
               "zone_sizes": {z: int((zones == z).sum())
                              for z in sorted(set(zones))},
               "theta_grid_pct": THETA_GRID, "models": MODELS,
               "budget": {"zone_time_limit_s": ZONE_TIME_S,
                          "max_huis": MAX_HUIS, "escalate": ESCALATE,
                          "max_escalations": MAX_ESCALATIONS,
                          "n_spatial_zones": N_SPATIAL_ZONES},
               "n_wap_columns": len(wap), "sets": sets,
               "environment": environment_info()}, out / "ap_sets.json")


# ===================================================================== select
def stage_select(b: Bundle) -> None:
    out = outdir(b.key)
    op.GROUND = b.ground_factor
    tr = b.train
    wap = b.wap_cols
    col = {w: j for j, w in enumerate(wap)}
    W = tr[wap].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    ybf = bf_label(tr)
    folds = folds_for(b, len(tr))
    cfg = positioner_config(b.key)
    sets = load_json(out / "ap_sets.json")["sets"]
    path = out / "dev_selection.csv"
    done = pd.read_csv(path) if path.exists() else pd.DataFrame()
    rows = done.to_dict("records")
    have = set(done["set"]) if len(done) else set()
    for name, S in [("all_aps", wap), *sets.items()]:
        if name in have:
            continue
        t0 = time.perf_counter()
        o = op.Positioner(W, C, ybf, cfg, [col[w] for w in S]).predict(W, folds)
        e = op.err_ground(o["xy"], C)
        rows.append({"set": name, "n_waps": len(S),
                     "dev_joint_accuracy": round(float(np.mean(o["label"] == ybf)), 6),
                     **{f"dev_{k}": v for k, v in op.stats(e).items()},
                     "dev_seconds": round(time.perf_counter() - t0, 1)})
        pd.DataFrame(rows).to_csv(path, index=False)
        LOG.info("%s dev %-36s %4d WAP  mean %.3f m", b.key, name, len(S),
                 e.mean())
    D = pd.DataFrame(rows)
    H = D[D["set"] != "all_aps"].sort_values(["dev_mean_ground_m", "n_waps"])
    best = H.iloc[0]
    dump_json({"dataset": b.key, "positioner": cfg.label(),
               "positioner_config": asdict(cfg),
               "positioner_source": f"results/multi_dataset/{b.key}/"
                                    "positioning.json (selected on dev folds "
                                    "with all APs)",
               "dev_folds": f"{len(folds)} folds, {b.group_note}",
               "rule": "lowest dev mean error among the HUIM-zone sets; ties "
                       "-> fewer WAPs",
               "selected_set": best["set"], "selected_n_waps": int(best["n_waps"]),
               "selected_dev_mean_m": float(best["dev_mean_ground_m"]),
               "all_aps_dev_mean_m": float(D.loc[D["set"] == "all_aps",
                                                 "dev_mean_ground_m"].iloc[0]),
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              out / "selection.json")
    LOG.info("%s SELECTED on dev: %s (%d WAP, dev %.3f m)", b.key, best["set"],
             best["n_waps"], best["dev_mean_ground_m"])


# =================================================================== evaluate
def control_sets(b: Bundle, n_budgets) -> dict:
    tr = b.train
    wap = b.wap_cols
    det = (tr[wap].to_numpy() != NOT_DETECTED)
    support = det.sum(axis=0)
    detected = [w for w, s in zip(wap, support) if s > 0]
    mi, _ = conditional_entropy_reduction(discretise(tr, wap), class_label(b, tr))
    by_sup = [wap[j] for j in np.lexsort((np.arange(len(wap)), -support))]
    by_mi = [wap[j] for j in np.lexsort((np.arange(len(wap)), -mi))]
    out = {}
    for n in sorted(set(n_budgets)):
        out[f"control_top_support__n{n}"] = ("top_support", n, by_sup[:n])
        out[f"control_top_mi__n{n}"] = ("top_mi", n, by_mi[:n])
        for s in CONTROL_SEEDS:
            rng = np.random.default_rng(s)
            pick = rng.choice(len(detected), size=min(n, len(detected)),
                              replace=False)
            out[f"control_random_s{s}__n{n}"] = (
                "random", n, [detected[j] for j in sorted(pick)])
    return out


def stage_evaluate(b: Bundle) -> None:
    out = outdir(b.key)
    op.GROUND = b.ground_factor
    tr = b.train
    wap = b.wap_cols
    col = {w: j for j, w in enumerate(wap)}
    W = tr[wap].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    ybf = bf_label(tr)
    cfg = positioner_config(b.key)
    sel = load_json(out / "selection.json")
    sets = load_json(out / "ap_sets.json")["sets"]
    todo = {"all_aps": ("baseline", len(wap), wap)}
    for name, S in sets.items():
        todo[name] = ("huim_zone", len(S), S)
    todo.update(control_sets(b, [len(S) for S in sets.values()]))
    rows = []
    for tname, te in b.tests.items():
        Wt = te[wap].to_numpy(np.float64)
        for name, (fam, n, S) in todo.items():
            pos = op.Positioner(W, C, ybf, cfg, [col[w] for w in S])
            t0 = time.perf_counter()
            o = pos.predict(Wt)
            ms = (time.perf_counter() - t0) / len(Wt) * 1000.0
            m = metrics(te, o["label"], o["xy"], b.ground_factor)
            parts = name.split("__")
            rows.append({"test_set": tname, "set": name, "family": fam,
                         "utility_model": parts[1] if fam == "huim_zone" else "",
                         "theta_pct": float(parts[2][:-3]) if fam == "huim_zone" else None,
                         "n_waps": len(S),
                         "feature_reduction_pct": round((1 - len(S) / len(wap)) * 100, 4),
                         "selected_on_dev": name == sel["selected_set"],
                         **m, "ms_per_fp": round(ms, 4)})
            if name in (sel["selected_set"], "all_aps"):
                k = cfg.k
                mem = [("", o["lists"].nbr[:, :k], op.weights(o["lists"].dst, k, cfg.power))]
                dl = {"delta_db": o["delta"]} if cfg.offset_range else {}
                if "lists2" in o:
                    mem.append(("m2_", o["lists2"].nbr[:, :k],
                                op.weights(o["lists2"].dst, k, cfg.power)))
                    dl["m2_delta_db"] = o["delta2"]
                tag = "huim_zone" if name != "all_aps" else "all_aps"
                pred_frame(b, te, o["label"], o["xy"], mem, dl).to_csv(
                    out / "predictions" / f"{tname}__{tag}.csv", index=False)
            if fam != "control":
                LOG.info("%s %-10s %-36s %4d WAP  mean %.3f m  joint %.4f",
                         b.key, tname, name, len(S), m["mean_err_m"],
                         m["joint_accuracy"])
    for r in rows:
        if r["family"] in ("top_support", "top_mi", "random"):
            r["family"] = "control_" + r["family"]
    R = pd.DataFrame(rows)
    R.to_csv(out / "test_results.csv", index=False)

    # global HUIM (PHASE H/H2, one database for the whole site) for contrast
    gcsv = MULTI / b.key / "positioning_conditions.csv"
    G = pd.read_csv(gcsv)
    G = G[G["family"] == "huim_union"]
    summary = {"dataset": b.key, "title": b.title,
               "positioner": cfg.label(), "selection": sel, "tests": {}}
    for tname in b.tests:
        r = R[(R.test_set == tname)]
        s = r[r.set == sel["selected_set"]].iloc[0]
        a = r[r.set == "all_aps"].iloc[0]
        n = int(s["n_waps"])
        ctl = {f: r[(r.family == f) & (r.n_waps == n)]["mean_err_m"]
               for f in ("control_top_support", "control_top_mi", "control_random")}
        g = G[G["test_set"] == tname].sort_values("opt_mean_err_m")
        summary["tests"][tname] = {
            "n_test": int(s["n_test"]),
            "huim_zone": {k: (None if pd.isna(v) else v) for k, v in s.items()
                          if k in ("set", "n_waps", "feature_reduction_pct",
                                   "building_accuracy", "floor_accuracy",
                                   "joint_accuracy", "mean_err_m",
                                   "median_err_m", "p75_err_m", "p90_err_m",
                                   "p95_err_m", "ms_per_fp")},
            "all_aps": {k: a[k] for k in ("n_waps", "joint_accuracy",
                                          "mean_err_m", "median_err_m",
                                          "p90_err_m", "ms_per_fp")},
            "controls_same_budget_mean_err_m": {
                "top_support": float(ctl["control_top_support"].iloc[0]),
                "top_mi": float(ctl["control_top_mi"].iloc[0]),
                "random_mean_of_3": float(ctl["control_random"].mean()),
                "random_each": [float(v) for v in ctl["control_random"]]},
            "global_huim_best": ({"set": g.iloc[0]["condition"],
                                  "n_waps": int(g.iloc[0]["n_waps"]),
                                  "mean_err_m": float(g.iloc[0]["opt_mean_err_m"])}
                                 if len(g) else None),
            "below_target": bool(s["mean_err_m"] < TARGET_M),
            "target_m": TARGET_M}
        LOG.info("%s %s SELECTED %s: %d WAP, %.3f m (all APs %.3f m)", b.key,
                 tname, sel["selected_set"], n, s["mean_err_m"], a["mean_err_m"])
    summary["environment"] = environment_info()
    summary["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    dump_json(summary, out / "selected.json")


STAGES = {"mine": stage_mine, "select": stage_select, "evaluate": stage_evaluate}


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
            LOG.info("%s stage %s done in %.0fs", key, st,
                     time.perf_counter() - t0)


if __name__ == "__main__":
    main()
