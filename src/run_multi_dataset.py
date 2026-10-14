"""Re-run the HUIM-IPS study on every dataset of dataset-20261013T020803Z-1-001.

Only the data changes. Every step calls the study's own code with the study's
own constants:

    huim         PHASE H + H2  EFIM (src/huim/efim.py) on utility Models A/B/C
                               (src/utility_models.py), grid run_huim.GRID_PCT,
                               budget run_huim.TIME_LIMIT_S / MAX_HUIS, then the
                               refinement rules of src/run_huim_refine.py
    ips          PHASE I       k-NN config chosen once on a stratified 75/25
                               split of the training data (ips_model.
                               select_knn_config), frozen, applied to: all WAPs,
                               detected WAPs, every HUIM union / top-n set, and
                               the random / top-support / top-MI controls
    positioning  PHASE I3      src/optimize_positioning.select_on_dev - stages
                               S0..S4 chosen on grouped folds of the training
                               data only, the test data used once per stage;
                               the selected model is then applied to the HUIM
                               sets (the procedure that gave 5.36 m on UJI)
    timing                     wall-clock cost of locating the test fingerprints
                               with the study k-NN and with the optimised model

What has to be decided per dataset (the label when there is a single floor,
the "not detected" value, the coordinate unit, the CV grouping) is decided in
src/multi_datasets.py and written to dataset_summary.json.

UJIIndoorLoc is in the folder too, byte-identical to the study's copy; its
mining is not repeated (PHASE H's runs are reused), but PHASE I and I3 are
re-run through this generic code and must reproduce the study's numbers -
that is the check that the generic path changes nothing but the data.

Run
    python src/run_multi_dataset.py --dataset all       (every dataset, hours)
    python src/run_multi_dataset.py --dataset hcxy --stage all
    python src/run_multi_dataset.py --dataset uji_lib3 --stage huim --models A
Run the `timing` stage with nothing else running: it measures wall-clock.
Outputs: results/multi_dataset/<dataset>/
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
from sklearn.model_selection import GroupKFold, KFold
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
import optimize_positioning as op
import run_huim
from feature_selection import (feature_reduction_pct, hui_length_distribution,
                               select_waps)
from huim.efim import mine_efim
from ips_model import RANDOM_SEED, KNNConfig, select_knn_config, split_train_dev
from multi_datasets import (DATASETS, Bundle, bf_label, class_label, describe,
                            empty_folders, label_kind, load)
from preprocess_uji import NOT_DETECTED, fit_preprocessor
from run_huim import GRID_PCT, MAX_HUIS, TIME_LIMIT_S
from run_huim_refine import MAX_BISECTIONS, RICH_ENOUGH_HUIS
from run_ips import BUDGETS, CONTROL_SEEDS
from utility_models import (build_external_utility,
                            conditional_entropy_reduction, discretise)
from utils import (LOGS, METRICS, PROJECT_ROOT, RESULTS, MemoryMonitor,
                   dump_json, environment_info, get_logger, load_json, relocate)

OUT_ROOT = RESULTS / "multi_dataset"
MODEL_NAMES = {"A": "A_signal", "B": "B_discriminative",
               "C": "C_rare_discriminative"}
TIMING_REPEATS = 3
TIMING_MAX_ROWS = 1111          # = len(UJIIndoorLoc validationData)
LOG = get_logger("multi")


def outdir(key: str) -> Path:
    p = OUT_ROOT / key
    (p / "logs").mkdir(parents=True, exist_ok=True)
    return p


def redirect_logs(path: Path) -> None:
    """The study's modules log to results/logs/*.log. A run on another dataset
    must not append to those files, so every file handler pointing there is
    swapped for one writing to this dataset's own log."""
    fh = logging.FileHandler(path, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"))
    for lg in list(logging.Logger.manager.loggerDict.values()):
        if not isinstance(lg, logging.Logger):
            continue
        swapped = False
        for h in list(lg.handlers):
            if (isinstance(h, logging.FileHandler)
                    and Path(h.baseFilename).parent == LOGS):
                lg.removeHandler(h)
                h.close()
                swapped = True
        if swapped or lg is LOG:
            lg.addHandler(fh)


def rel(p) -> str:
    """Project-relative path, so result files survive moving the folder."""
    p = Path(p)
    try:
        return p.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(p)


def bf_parts(labels) -> tuple[np.ndarray, np.ndarray]:
    b, f = zip(*(str(s).split("_") for s in labels))
    return np.array(b, int), np.array(f, int)


def metrics(te: pd.DataFrame, pred_bf, xy: np.ndarray, gf: float) -> dict:
    """The study's measures: building / floor / joint accuracy from ONE joint
    prediction (ips_model.classification_metrics) and the planar error, in
    ground metres = coordinate distance x ground factor."""
    pb, pf = bf_parts(pred_bf)
    tb = te["BUILDINGID"].to_numpy(int)
    tf = te["FLOOR"].to_numpy(int)
    d = np.sqrt(((te[["X", "Y"]].to_numpy(float) - xy) ** 2).sum(axis=1))
    g = d * gf
    return {"n_test": int(len(te)),
            "building_accuracy": round(float(np.mean(pb == tb)), 6),
            "floor_accuracy": round(float(np.mean(pf == tf)), 6),
            "joint_accuracy": round(float(np.mean((pb == tb) & (pf == tf))), 6),
            "mean_err_m": round(float(g.mean()), 4),
            "median_err_m": round(float(np.median(g)), 4),
            "p75_err_m": round(float(np.percentile(g, 75)), 4),
            "p90_err_m": round(float(np.percentile(g, 90)), 4),
            "p95_err_m": round(float(np.percentile(g, 95)), 4),
            "max_err_m": round(float(g.max()), 4),
            "mean_err_coord": round(float(d.mean()), 4),
            "share_within_2m": round(float((g <= 2).mean()), 4),
            "share_within_5m": round(float((g <= 5).mean()), 4)}


# ======================================================================= HUIM
def huim_runs(out: Path) -> pd.DataFrame:
    files = sorted(out.glob("huim_runs__*.csv"))
    if not files:
        raise SystemExit(f"no huim_runs__*.csv in {out}; run --stage huim")
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def reuse_study_huim(out: Path) -> None:
    """UJIIndoorLoc: same bytes as the study's data, so PHASE H/H2 would mine
    the same HUIs again. Their run table is reused, split per model."""
    runs = pd.read_csv(METRICS / "huim_runs.csv")
    runs["path_wap_stats"] = [rel(relocate(p)) for p in runs["path_wap_stats"]]
    runs["phase"] = np.where(runs.get("refinement_iteration").notna(),
                             "refine", "grid")
    runs["source"] = "study PHASE H/H2 (results/metrics/huim_runs.csv)"
    for code, name in MODEL_NAMES.items():
        runs[runs["utility_model"] == name].to_csv(
            out / f"huim_runs__{code}.csv", index=False)
    LOG.info("uji: reused %d study HUIM runs", len(runs))


def stage_huim(b: Bundle, models: list[str]) -> None:
    out = outdir(b.key)
    if b.key == "uji":
        reuse_study_huim(out)
        return
    hui_dir = out / "hui"
    hui_dir.mkdir(exist_ok=True)
    run_huim.HUI_DIR = hui_dir             # _save_hui_set writes here
    tr = b.train
    prep = fit_preprocessor(tr)
    y = class_label(b, tr)
    n_total = len(prep.wap_cols)
    txs = [t for t in prep.transactions(tr)[0] if t]
    LOG.info("%s: %d non-empty transactions, %d WAP columns, label %s",
             b.key, len(txs), n_total, label_kind(b))

    for code in models:
        um = build_external_utility(code, tr, prep, y, "training")
        total_u = um.total_database_utility(txs)
        rows: list[dict] = []
        csv = out / f"huim_runs__{code}.csv"

        def run(pct: float, phase: str, it: int | None = None) -> dict:
            mu = total_u * pct / 100.0
            tag = f"{um.name}__{pct:g}pct"
            with MemoryMonitor() as mem:
                t0 = time.perf_counter()
                huis, st = mine_efim(txs, um.external_utility, min_util=mu,
                                     time_limit_s=TIME_LIMIT_S,
                                     max_huis=MAX_HUIS)
                el = time.perf_counter() - t0
            dist = hui_length_distribution(huis)
            union, _ = select_waps(huis, "union") if huis else ([], {})
            paths = run_huim._save_hui_set(tag, huis, n_total)
            row = {
                "run_tag": tag, "utility_model": um.name,
                "rel_minutil_pct": pct, "abs_minutil": round(mu, 6),
                "total_db_utility": round(total_u, 6),
                "n_transactions": len(txs), "n_wap_columns_total": n_total,
                "status": st.status, "abort_reason": st.abort_reason or "",
                "runtime_s": round(el, 4),
                "peak_memory_delta_mb": mem.as_dict()["peak_delta_mb"],
                "n_huis": dist["n_huis"], "max_hui_len": dist["max_len"],
                "mean_hui_len": dist["mean_len"],
                "hui_utility_max": dist["utility_max"],
                "unique_waps_in_huis": len(union),
                "feature_reduction_pct_union": feature_reduction_pct(
                    len(union), n_total),
                "items_after_twu_pruning": st.n_items_after_twu_pruning,
                "search_nodes_visited": st.n_nodes_visited,
                "transactions_saved_by_merging":
                    st.n_transactions_saved_by_merging,
                "hui_length_distribution_json": json.dumps(dist["by_length"]),
                "phase": phase, "refinement_iteration": it,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "path_wap_stats": rel(paths["wap_stats"]),
                "path_top_huis": rel(paths["top_huis"]),
            }
            rows.append(row)
            pd.DataFrame(rows).to_csv(csv, index=False)
            LOG.info("%-22s %8.4f%% -> %8d HUIs | %7.2fs | %6.1fMB | WAPs %3d "
                     "| %s", um.name, pct, dist["n_huis"], el,
                     mem.as_dict()["peak_delta_mb"], len(union), st.status)
            return row

        # PHASE H: descend the grid until a run hits the budget
        for pct in GRID_PCT:
            if run(pct, "grid")["status"] != "COMPLETED":
                break
        # PHASE H2: the refinement rules of run_huim_refine.main
        comp = [r for r in rows if r["status"] == "COMPLETED"]
        ab = [r for r in rows if r["status"] != "COMPLETED"]
        best_n = max((r["n_huis"] for r in comp), default=0)
        lo = min((r["rel_minutil_pct"] for r in comp), default=None)
        mode = None
        if not ab and lo is not None and best_n < RICH_ENOUGH_HUIS:
            mode, hi = "extend_downwards", lo / (2 ** MAX_BISECTIONS)
        elif ab and lo is not None and lo > max(r["rel_minutil_pct"] for r in ab):
            mode, hi = "bisect", max(r["rel_minutil_pct"] for r in ab)
        for it in range(MAX_BISECTIONS if mode else 0):
            if best_n >= RICH_ENOUGH_HUIS:
                break
            if mode == "extend_downwards":
                mid = round(lo / 2.0, 6)
                if mid <= 0:
                    break
            else:
                mid = round(float(np.sqrt(lo * hi)), 4)
                if mid >= lo or mid <= hi:
                    break
            r = run(mid, "refine", it + 1)
            if r["status"] == "COMPLETED":
                lo, best_n = mid, max(best_n, r["n_huis"])
            else:
                hi, mode = mid, "bisect"
        dump_json({"dataset": b.key, "utility_model": um.name,
                   "label": label_kind(b), "diagnostics": um.diagnostics,
                   "total_database_utility": total_u,
                   "n_transactions": len(txs), "runs": rows,
                   "environment": environment_info()},
                  out / f"huim_summary__{code}.json")


# ======================================================================== IPS
def budgets_for(n_det: int) -> list[int]:
    """The study's budgets, cut at the number of detected WAPs; a dataset with
    20 APs or fewer gets every size from 1 to n."""
    if n_det <= 20:
        return list(range(1, n_det + 1))
    return sorted({n for n in BUDGETS if n < n_det} | {n_det})


def knn_predict(Xtr, ycls, Ctr, Xte, cfg: KNNConfig):
    """PHASE I's classifier and coordinate rule (ips_model.evaluate_once)."""
    clf = KNeighborsClassifier(n_neighbors=cfg.n_neighbors, metric=cfg.metric,
                               weights=cfg.weights, n_jobs=-1)
    clf.fit(Xtr, ycls)
    t0 = time.perf_counter()
    pred = clf.predict(Xte)
    dist, nbr = clf.kneighbors(Xte, n_neighbors=cfg.n_neighbors)
    secs = time.perf_counter() - t0
    w = (1.0 / np.maximum(dist, 1e-12) if cfg.weights == "distance"
         else np.ones_like(dist))
    w = w / w.sum(axis=1, keepdims=True)
    xy = np.einsum("ij,ijk->ik", w, Ctr[nbr])
    return pred, xy, nbr, dist, w, secs


def stage_ips(b: Bundle) -> None:
    out = outdir(b.key)
    tr = b.train
    prep = fit_preprocessor(tr)
    wap = prep.wap_cols
    n_total = len(wap)
    col_of = {w: j for j, w in enumerate(wap)}
    ycls = class_label(b, tr)
    bf_of = dict(zip(ycls, bf_label(tr)))
    Xtr = prep.positive_representation(tr)
    Xte = {n: prep.positive_representation(df) for n, df in b.tests.items()}
    Ctr = tr[["X", "Y"]].to_numpy(np.float64)

    det = tr[wap].to_numpy() != NOT_DETECTED
    detected = [w for w, d in zip(wap, det.any(axis=0)) if d]
    support = det.sum(axis=0)
    mi, h_y = conditional_entropy_reduction(discretise(tr, wap), ycls)

    tr_idx, dev_idx = split_train_dev(ycls)
    cfg, trace = select_knn_config(Xtr, ycls, tr_idx, dev_idx)
    LOG.info("%s: frozen k-NN %s", b.key, cfg.as_dict())

    conds: list[tuple[dict, list[str]]] = [
        ({"condition": "baseline_all", "family": "baseline",
          "selection": "all", "budget_n": n_total}, list(wap)),
        ({"condition": "baseline_detected", "family": "baseline",
          "selection": "detected_in_train", "budget_n": len(detected)},
         detected)]
    runs = huim_runs(out)
    primary: dict[str, dict] = {}
    for _, r in runs[runs["n_huis"] > 0].iterrows():
        ws = load_json(PROJECT_ROOT / r["path_wap_stats"])["per_wap"]
        order = sorted(ws, key=lambda w: (-ws[w]["utility_contribution"], w))
        conds.append(({"condition": f"huim_union__{r['run_tag']}",
                       "family": "huim_union",
                       "utility_model": r["utility_model"],
                       "rel_minutil_pct": r["rel_minutil_pct"],
                       "selection": "union_of_HUI_waps",
                       "budget_n": len(order), "huim_status": r["status"],
                       "n_huis": int(r["n_huis"]),
                       "huim_runtime_s": float(r["runtime_s"])}, order))
        # primary HUI set per model = lowest COMPLETED threshold (run_ips.py)
        if r["status"] == "COMPLETED":
            cur = primary.get(r["utility_model"])
            if cur is None or r["rel_minutil_pct"] < cur["pct"]:
                primary[r["utility_model"]] = {
                    "pct": float(r["rel_minutil_pct"]), "order": order,
                    "run_tag": r["run_tag"], "n_huis": int(r["n_huis"]),
                    "runtime_s": float(r["runtime_s"])}
    bud = budgets_for(len(detected))
    for model, info in primary.items():
        for n in bud:
            if n <= len(info["order"]):
                conds.append(({"condition": f"huim_topn__{model}__"
                                            f"{info['pct']:g}pct__n{n}",
                               "family": "huim_topn", "utility_model": model,
                               "rel_minutil_pct": info["pct"],
                               "selection": "top_n_by_utility_contribution",
                               "budget_n": n, "huim_status": "COMPLETED",
                               "n_huis": info["n_huis"],
                               "huim_runtime_s": info["runtime_s"]},
                              info["order"][:n]))
    order_sup = [w for _, w in sorted((-support[col_of[w]], w) for w in detected)]
    order_mi = [w for _, w in sorted((-mi[col_of[w]], w) for w in detected)]
    huim_ns = {c["budget_n"] for c, _ in conds
               if c["family"].startswith("huim")}
    for n in sorted(set(bud) | huim_ns):
        if not 1 <= n <= len(detected):
            continue
        conds.append(({"condition": f"control_top_support__n{n}",
                       "family": "control_top_support",
                       "selection": "top_n_by_detection_support",
                       "budget_n": n}, order_sup[:n]))
        conds.append(({"condition": f"control_top_mi__n{n}",
                       "family": "control_top_mi",
                       "selection": "top_n_by_mutual_information",
                       "budget_n": n}, order_mi[:n]))
        for seed in CONTROL_SEEDS:
            rng = np.random.default_rng(RANDOM_SEED + seed)
            pick = list(rng.choice(detected, size=n, replace=False))
            conds.append(({"condition": f"control_random__n{n}__s{seed}",
                           "family": "control_random",
                           "selection": f"random_n_seed{seed}",
                           "budget_n": n}, pick))
    LOG.info("%s: %d conditions x %d test sets", b.key, len(conds),
             len(b.tests))

    rows = []
    for ci, (cond, waps) in enumerate(conds, 1):
        cols = [col_of[w] for w in waps]
        for tname, te in b.tests.items():
            pred, xy, _n, _d, _w, secs = knn_predict(
                Xtr[:, cols], ycls, Ctr, Xte[tname][:, cols], cfg)
            m = metrics(te, [bf_of[c] for c in pred], xy, b.ground_factor)
            rows.append({**cond, "test_set": tname,
                         "n_waps_selected": len(cols),
                         "feature_reduction_pct": feature_reduction_pct(
                             len(cols), n_total),
                         "test_rows_with_no_selected_wap_detected": int(
                             (Xte[tname][:, cols].sum(axis=1) == 0).sum()),
                         **m, "knn_predict_seconds": round(secs, 4),
                         "selected_waps": ";".join(waps)})
        if ci % 25 == 0 or ci == len(conds):
            LOG.info("  %d/%d conditions", ci, len(conds))
            pd.DataFrame(rows).to_csv(out / "ips_results.csv", index=False)
    pd.DataFrame(rows).to_csv(out / "ips_results.csv", index=False)
    dump_json({"dataset": b.key, "label": label_kind(b),
               "frozen_knn_config": cfg.as_dict(),
               "knn_grid_search_trace": trace,
               "label_entropy_H_Y_bits": round(h_y, 5),
               "n_wap_columns": n_total, "n_waps_detected": len(detected),
               "budgets": bud,
               "primary_hui_sets": {k: {kk: v[kk] for kk in
                                        ("run_tag", "pct", "n_huis",
                                         "runtime_s")}
                                    | {"n_waps": len(v["order"])}
                                    for k, v in primary.items()},
               "random_seed": RANDOM_SEED,
               "environment": environment_info(),
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              out / "ips.json")


# ================================================================ positioning
def folds_for(b: Bundle, n_rows: int):
    if b.group_col:
        return list(GroupKFold(n_splits=op.N_FOLDS).split(
            np.zeros(n_rows), groups=b.train[b.group_col]))
    return list(KFold(n_splits=op.N_FOLDS, shuffle=True,
                      random_state=RANDOM_SEED).split(np.zeros(n_rows)))


def pred_frame(b: Bundle, te: pd.DataFrame, pred_bf, xy: np.ndarray,
               members: list[tuple[str, np.ndarray, np.ndarray]],
               deltas: dict[str, np.ndarray]) -> pd.DataFrame:
    """One row per test fingerprint, with the neighbours and weights that
    produced its estimate, so any row can be recomputed by hand: (x, y) =
    sum_j weight_j * (x_j, y_j) over the listed training rows (and, for an
    ensemble, the mean of the two members)."""
    pb, pf = bf_parts(pred_bf)
    df = pd.DataFrame({
        "src_file": te["SRC_FILE"].to_numpy(),
        "src_row": te["SRC_ROW"].to_numpy(),
        "true_building": te["BUILDINGID"].to_numpy(),
        "true_floor": te["FLOOR"].to_numpy(),
        "pred_building": pb, "pred_floor": pf,
        "true_x": te["X"].to_numpy(), "true_y": te["Y"].to_numpy(),
        "pred_x": xy[:, 0], "pred_y": xy[:, 1]})
    e = np.sqrt((df.true_x - df.pred_x) ** 2 + (df.true_y - df.pred_y) ** 2)
    df["err_coord"] = e
    df["err_m"] = e * b.ground_factor
    for name, d in deltas.items():
        df[name] = d
    multi_file = b.train["SRC_FILE"].nunique() > 1
    src_row = b.train["SRC_ROW"].to_numpy()
    src_file = b.train["SRC_FILE"].to_numpy()
    for pre, nbr, w in members:
        for j in range(nbr.shape[1]):
            if multi_file:
                df[f"{pre}nbr{j + 1}_train_file"] = src_file[nbr[:, j]]
            df[f"{pre}nbr{j + 1}_train_row"] = src_row[nbr[:, j]]
            df[f"{pre}nbr{j + 1}_weight"] = w[:, j]
    return df


def stage_positioning(b: Bundle) -> None:
    out = outdir(b.key)
    pred_dir = out / "predictions"
    pred_dir.mkdir(exist_ok=True)
    op.GROUND = b.ground_factor        # err_ground/stats read this global
    t_start = time.perf_counter()
    tr = b.train
    wap = b.wap_cols
    W = tr[wap].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    ybf = bf_label(tr)
    folds = folds_for(b, len(tr))
    LOG.info("%s: %d dev folds grouped by %s", b.key, len(folds),
             b.group_col or "row (shuffled KFold)")

    ips = load_json(out / "ips.json")
    sc = ips["frozen_knn_config"]
    scfg = KNNConfig(sc["n_neighbors"], sc["metric"], sc["weights"])
    stages, grid = op.select_on_dev(W, C, ybf, folds)
    G = pd.DataFrame(grid)
    G.to_csv(out / "positioning_dev_grid.csv", index=False)
    # S0 is the study k-NN OF THIS DATASET (select_on_dev hard-codes UJI's)
    p0 = 0 if (scfg.weights == "uniform" or scfg.n_neighbors == 1) else 1
    s0 = G[(G.stage == "S1-S2") & (G.representation == "positive")
           & (G.distance == scfg.metric) & (G.k == scfg.n_neighbors)
           & (G.power == p0)].iloc[0]
    stages[0] = {"stage": "S0", "what": "study k-NN as regressor",
                 "cfg": op.Config("positive", scfg.metric, scfg.n_neighbors,
                                  p0),
                 "dev": s0[list(op.STAT_KEYS)].to_dict()}
    final = stages[-1]["cfg"]
    LOG.info("%s: SELECTED on dev %s", b.key, final.label())

    prep = fit_preprocessor(tr)
    Xp = prep.positive_representation(tr)
    ycls = class_label(b, tr)
    bf_of = dict(zip(ycls, bf_label(tr)))
    abl = []
    for tname, te in b.tests.items():
        Wt = te[wap].to_numpy(np.float64)
        for st in stages:
            if st["stage"] == "S0":
                # exactly PHASE I's classifier, so S0 equals ips baseline_all
                pred, xy, nbr, _d, w, _s = knn_predict(
                    Xp, ycls, C, prep.positive_representation(te), scfg)
                pbf = [bf_of[c] for c in pred]
                frame_args = ([("", nbr, w)], {})
            else:
                o = op.Positioner(W, C, ybf, st["cfg"]).predict(Wt)
                pbf, xy = o["label"], o["xy"]
                cf = st["cfg"]
                mem = [("", o["lists"].nbr[:, :cf.k],
                        op.weights(o["lists"].dst, cf.k, cf.power))]
                dl = {"delta_db": o["delta"]} if cf.offset_range else {}
                if "lists2" in o:
                    mem.append(("m2_", o["lists2"].nbr[:, :cf.k],
                                op.weights(o["lists2"].dst, cf.k, cf.power)))
                    dl["m2_delta_db"] = o["delta2"]
                frame_args = (mem, dl)
            m = metrics(te, pbf, xy, b.ground_factor)
            abl.append({"test_set": tname, "stage": st["stage"],
                        "what": st["what"], "config": st["cfg"].label(),
                        **{f"dev_{k}": v for k, v in st["dev"].items()},
                        **{f"test_{k}": v for k, v in m.items()}})
            LOG.info("%s %-10s %s %-36s mean %.3f m  median %.3f m  joint %.4f",
                     b.key, tname, st["stage"], st["what"], m["mean_err_m"],
                     m["median_err_m"], m["joint_accuracy"])
            if st["stage"] == "S0":
                pred_frame(b, te, pbf, xy, *frame_args).to_csv(
                    pred_dir / f"{tname}__study_knn.csv", index=False)
            if st is stages[-1]:
                pred_frame(b, te, pbf, xy, *frame_args).to_csv(
                    pred_dir / f"{tname}__optimised.csv", index=False)
    A = pd.DataFrame(abl)
    A.to_csv(out / "positioning_ablation.csv", index=False)

    # the selected model on the WAP sets of PHASE I (as optimize_positioning)
    I = pd.read_csv(out / "ips_results.csv")
    prim = next(iter(b.tests))
    Ip = I[I["test_set"] == prim]
    picks = ["baseline_all", "baseline_detected"]
    sizes = []
    for fam in ("huim_union", "huim_topn"):
        for _model, g in Ip[Ip["family"] == fam].groupby("utility_model"):
            best = g.sort_values(["joint_accuracy", "mean_err_m"],
                                 ascending=[False, True]).iloc[0]
            picks.append(best["condition"])
            sizes.append(int(best["n_waps_selected"]))
    for n in sizes:
        picks += [f"control_top_mi__n{n}", f"control_top_support__n{n}"]
    col_of = {w: j for j, w in enumerate(wap)}
    rows = []
    for cond in dict.fromkeys(picks):
        for tname, te in b.tests.items():
            r = I[(I["condition"] == cond) & (I["test_set"] == tname)]
            if not len(r):
                continue
            r = r.iloc[0]
            cols = [col_of[w] for w in str(r["selected_waps"]).split(";")]
            o = op.Positioner(W, C, ybf, final, cols).predict(
                te[wap].to_numpy(np.float64))
            m = metrics(te, o["label"], o["xy"], b.ground_factor)
            rows.append({"test_set": tname, "condition": cond,
                         "family": r["family"],
                         "utility_model": r.get("utility_model", ""),
                         "rel_minutil_pct": r.get("rel_minutil_pct", ""),
                         "n_waps": len(cols),
                         "feature_reduction_pct": r["feature_reduction_pct"],
                         "study_building_accuracy": r["building_accuracy"],
                         "study_floor_accuracy": r["floor_accuracy"],
                         "study_mean_err_m": r["mean_err_m"],
                         "study_median_err_m": r["median_err_m"],
                         **{f"opt_{k}": v for k, v in m.items()}})
            LOG.info("%s %-10s %-44s %3d WAP  study %.2f m -> opt %.2f m",
                     b.key, tname, cond, len(cols), r["mean_err_m"],
                     m["mean_err_m"])
    pd.DataFrame(rows).to_csv(out / "positioning_conditions.csv", index=False)

    res = {"dataset": b.key, "ground_factor": b.ground_factor,
           "cv_folds": f"{len(folds)} folds, {b.group_note}",
           "study_knn_config": scfg.as_dict(),
           "stages": [{"stage": s["stage"], "what": s["what"],
                       "config": asdict(s["cfg"]), "label": s["cfg"].label(),
                       "dev": s["dev"]} for s in stages],
           "selected_config": asdict(final), "selected_label": final.label(),
           "test": abl, "conditions": rows,
           "environment": environment_info(),
           "timestamp_utc": datetime.now(timezone.utc).isoformat(),
           "total_wall_clock_s": round(time.perf_counter() - t_start, 1)}
    if b.key == "uji":
        # the generic path must reproduce the study to the last digit
        study = load_json(RESULTS / "positioning_optimisation.json")
        sel = study["validation"]["selected"]
        last = abl[len(stages) - 1]
        res["reproduces_study"] = {
            "study_selected_label": study["selected_label"],
            "study_mean_ground_m": sel["positioning_error"]["mean_error_ground_m"],
            "generic_mean_ground_m": last["test_mean_err_m"],
            "study_joint_accuracy": sel["joint_building_floor_accuracy"],
            "generic_joint_accuracy": last["test_joint_accuracy"],
            "match": bool(study["selected_label"] == final.label()
                          and abs(sel["positioning_error"]["mean_error_ground_m"]
                                  - last["test_mean_err_m"]) < 1e-3)}
        LOG.info("uji reproduction check: %s", res["reproduces_study"])
    dump_json(res, out / "positioning.json")


# ====================================================================== curve
def stage_curve(b: Bundle) -> None:
    """The selected model on EVERY top-n budget of PHASE I - HUIM top-n of each
    utility model and the top-MI / top-support / random sets of the same size -
    on the primary test set: the error-vs-number-of-WAPs curve of the study's
    fig11, drawn with the optimised regressor. The project's own pick rule
    (best set by accuracy) returns the full AP set on a 17-AP dataset, so the
    curve is what shows what fewer APs cost."""
    out = outdir(b.key)
    op.GROUND = b.ground_factor
    tr = b.train
    wap = b.wap_cols
    col_of = {w: j for j, w in enumerate(wap)}
    W = tr[wap].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    ybf = bf_label(tr)
    final = op.Config(**load_json(out / "positioning.json")["selected_config"])
    tname, te = next(iter(b.tests.items()))
    Wt = te[wap].to_numpy(np.float64)
    I = pd.read_csv(out / "ips_results.csv")
    I = I[(I["test_set"] == tname)
          & I["family"].isin(["huim_topn", "control_top_mi",
                              "control_top_support", "control_random",
                              "baseline"])]
    budgets = set(I.loc[I["family"] == "huim_topn", "budget_n"].astype(int))
    I = I[(I["family"] == "baseline") | I["budget_n"].astype(int).isin(budgets)]
    rows = []
    for _, r in I.iterrows():
        cols = [col_of[w] for w in str(r["selected_waps"]).split(";")]
        o = op.Positioner(W, C, ybf, final, cols).predict(Wt)
        m = metrics(te, o["label"], o["xy"], b.ground_factor)
        rows.append({"test_set": tname, "condition": r["condition"],
                     "family": r["family"],
                     "utility_model": r.get("utility_model", ""),
                     "budget_n": int(r["budget_n"]), "n_waps": len(cols),
                     "study_floor_accuracy": r["floor_accuracy"],
                     "study_mean_err_m": r["mean_err_m"],
                     **{f"opt_{k}": v for k, v in m.items()}})
        if len(rows) % 20 == 0:
            LOG.info("  curve %d/%d", len(rows), len(I))
            pd.DataFrame(rows).to_csv(out / "positioning_curve.csv",
                                      index=False)
    pd.DataFrame(rows).to_csv(out / "positioning_curve.csv", index=False)
    LOG.info("%s: curve over %d WAP sets", b.key, len(rows))


# =================================================================== transfer
def stage_transfer(b: Bundle) -> None:
    """The configuration PHASE I3 selected on UJIIndoorLoc (the 5.36 m model)
    applied unchanged, on all WAPs: what reusing that model as-is gives on
    each dataset, next to re-running the selection on the dataset itself."""
    out = outdir(b.key)
    op.GROUND = b.ground_factor
    study = load_json(RESULTS / "positioning_optimisation.json")
    cfg = op.Config(**study["selected_config"])
    tr = b.train
    W = tr[b.wap_cols].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    pos = op.Positioner(W, C, bf_label(tr), cfg)
    rows = []
    for tname, te in b.tests.items():
        o = pos.predict(te[b.wap_cols].to_numpy(np.float64))
        m = metrics(te, o["label"], o["xy"], b.ground_factor)
        rows.append({"test_set": tname, "config": cfg.label(),
                     "source": "results/positioning_optimisation.json "
                               "(selected on UJIIndoorLoc)", **m})
        LOG.info("%s %-10s UJI config as-is: mean %.3f m, joint %.4f", b.key,
                 tname, m["mean_err_m"], m["joint_accuracy"])
    pd.DataFrame(rows).to_csv(out / "positioning_transfer.csv", index=False)


# ===================================================================== timing
def stage_timing(b: Bundle) -> None:
    """Median wall-clock of locating (at most TIMING_MAX_ROWS rows of) the
    primary test set, after one warm-up, for the study k-NN and the optimised
    model, on all WAPs and on the HUIM sets of positioning_conditions.csv. Both use every core (n_jobs=-1,
    as optimize_positioning does); run this stage with nothing else running."""
    out = outdir(b.key)
    op.GROUND = b.ground_factor
    tr = b.train
    wap = b.wap_cols
    col_of = {w: j for j, w in enumerate(wap)}
    W = tr[wap].to_numpy(np.float64)
    C = tr[["X", "Y"]].to_numpy(np.float64)
    ybf = bf_label(tr)
    prep = fit_preprocessor(tr)
    Xp = prep.positive_representation(tr)
    ycls = class_label(b, tr)
    tname, te = next(iter(b.tests.items()))
    # brute-force k-NN costs the same per query whatever the batch, so every
    # dataset is timed on the same batch size: the first TIMING_MAX_ROWS rows
    # of its primary test set (= the size of UJIIndoorLoc's validationData)
    te = te.iloc[:TIMING_MAX_ROWS]
    Wt = te[wap].to_numpy(np.float64)
    Xpt = prep.positive_representation(te)
    sc = load_json(out / "ips.json")["frozen_knn_config"]
    scfg = KNNConfig(sc["n_neighbors"], sc["metric"], sc["weights"])
    final = op.Config(**load_json(out / "positioning.json")["selected_config"])
    I = pd.read_csv(out / "ips_results.csv")
    P = pd.read_csv(out / "positioning_conditions.csv")
    conds = [c for c in dict.fromkeys(P["condition"])
             if not c.startswith("control")]

    def clock(fn) -> tuple[float, list[float]]:
        fn()
        ts = []
        for _ in range(TIMING_REPEATS):
            t0 = time.perf_counter()
            fn()
            ts.append(time.perf_counter() - t0)
        return float(np.median(ts)), ts

    rows = []
    for cond in conds:
        r = I[(I["condition"] == cond) & (I["test_set"] == tname)].iloc[0]
        cols = [col_of[w] for w in str(r["selected_waps"]).split(";")]
        t_s, ts_s = clock(lambda: knn_predict(Xp[:, cols], ycls, C,
                                              Xpt[:, cols], scfg))
        t_o, ts_o = clock(lambda: op.Positioner(W, C, ybf, final, cols)
                          .predict(Wt))
        rows.append({"test_set": tname, "condition": cond,
                     "n_waps": len(cols), "n_train": len(tr),
                     "n_test": len(te),
                     "study_total_s": round(t_s, 4),
                     "study_ms_per_fp": round(1000 * t_s / len(te), 4),
                     "opt_total_s": round(t_o, 4),
                     "opt_ms_per_fp": round(1000 * t_o / len(te), 4),
                     "db_memory_mb": round(len(tr) * len(cols) * 8 / 2 ** 20, 3),
                     "study_samples_s": json.dumps([round(x, 4) for x in ts_s]),
                     "opt_samples_s": json.dumps([round(x, 4) for x in ts_o]),
                     "huim_runtime_s": r.get("huim_runtime_s", np.nan)})
        LOG.info("%s %-44s %3d WAP | study %.3f ms/fp | opt %.3f ms/fp",
                 b.key, cond, len(cols), rows[-1]["study_ms_per_fp"],
                 rows[-1]["opt_ms_per_fp"])
    pd.DataFrame(rows).to_csv(out / "timing.csv", index=False)
    dump_json({"dataset": b.key, "test_set": tname,
               "protocol": f"median of {TIMING_REPEATS} runs after 1 warm-up; "
                           f"first {TIMING_MAX_ROWS} rows of the primary test "
                           "set per run; fit + predict included; n_jobs=-1",
               "rows": rows, "environment": environment_info()},
              out / "timing.json")


# ======================================================================= main
STAGES = ("prepare", "huim", "ips", "positioning", "transfer", "curve",
          "timing")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True,
                    help="one of " + ", ".join(DATASETS) + ", or 'all' (one "
                         "after the other)")
    ap.add_argument("--stage", default="all",
                    help="comma list of " + ", ".join(STAGES) + " or 'all'")
    ap.add_argument("--models", default="A,B,C")
    a = ap.parse_args()
    if a.dataset == "all":
        import subprocess
        for key in DATASETS:
            subprocess.run([sys.executable, __file__, "--dataset", key,
                            "--stage", a.stage, "--models", a.models],
                           check=True)
        return
    stages = STAGES if a.stage == "all" else a.stage.split(",")
    out = outdir(a.dataset)
    redirect_logs(out / "logs" / f"{a.stage.replace(',', '_')}.log")
    t0 = time.perf_counter()
    b = load(a.dataset)
    LOG.info("loaded %s in %.1fs", a.dataset, time.perf_counter() - t0)
    for st in stages:
        t1 = time.perf_counter()
        LOG.info("==== %s / %s ====", a.dataset, st)
        if st == "prepare":
            d = describe(b)
            d["empty_folders_in_dataset_root"] = empty_folders()
            dump_json(d, out / "dataset_summary.json")
        elif st == "huim":
            stage_huim(b, a.models.split(","))
        elif st == "ips":
            stage_ips(b)
        elif st == "positioning":
            stage_positioning(b)
        elif st == "transfer":
            stage_transfer(b)
        elif st == "curve":
            stage_curve(b)
        elif st == "timing":
            stage_timing(b)
        else:
            raise SystemExit(f"unknown stage {st!r}")
        LOG.info("==== %s / %s done in %.1fs ====", a.dataset, st,
                 time.perf_counter() - t1)


if __name__ == "__main__":
    main()
