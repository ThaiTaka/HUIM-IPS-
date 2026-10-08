"""PHASE I - indoor positioning evaluation.

Conditions evaluated (all with the SAME frozen k-NN configuration):

  baseline_all_520        every WAP column - the mandated primary baseline
  baseline_detected_465   WAPs ever detected in trainingData. Reported because
                          removing never-detected columns is free, so it marks
                          the part of "feature reduction" that owes nothing to
                          HUIM.
  huim_union__*           WAPs appearing in the HUI set of one (model, minUtil)
  huim_topn__*            the n top-ranked WAPs from one HUI set
  control_random_n        n WAPs drawn uniformly from the 465 detected (3 seeds)
  control_top_support_n   the n most frequently detected WAPs
  control_top_mi_n        the n WAPs with the highest mutual information

The three controls exist because "HUIM-selected features reach accuracy X" is
not a result on its own. If a random subset of the same size reaches the same
accuracy, the selection did nothing; if ranking APs by mutual information alone
matches it, HUIM added nothing over the far simpler criterion it embeds. Those
comparisons are the only way the ablation can be read honestly.

Outputs: results/metrics/ips_results.csv, results/ips_summary.json
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
from feature_selection import feature_reduction_pct
from ips_model import (RANDOM_SEED, KNNConfig, evaluate_once, select_knn_config,
                       split_train_dev)
from preprocess_uji import NOT_DETECTED, fit_preprocessor, joint_label, load_splits
from utils import (HUI_DIR, METRICS, RESULTS, dump_json, environment_info,
                   get_logger, load_json)
from utility_models import conditional_entropy_reduction, discretise

LOG = get_logger("ips", "ips_full.log")

BUDGETS = [5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 465]
CONTROL_SEEDS = [1, 2, 3]
RF_CONDITIONS_MAX = 8          # Random Forest is slow; only on key conditions


def _flatten(cond: dict, res: dict) -> dict:
    """One flat CSV row per condition; nested metrics get prefixed keys."""
    row = dict(cond)
    row["status"] = res.get("status")
    row["n_features"] = res.get("n_features")
    row["val_rows_with_no_selected_wap_detected"] = res.get(
        "val_rows_with_no_selected_wap_detected")
    row["train_rows_with_no_selected_wap_detected"] = res.get(
        "train_rows_with_no_selected_wap_detected")
    row["knn_predict_seconds"] = res.get("knn_predict_seconds")
    for clf in ("knn", "random_forest"):
        m = res.get(clf)
        if not m:
            continue
        pre = "" if clf == "knn" else "rf_"
        for k in ("building_accuracy", "floor_accuracy",
                  "joint_building_floor_accuracy", "joint_macro_f1",
                  "building_macro_f1", "floor_macro_f1",
                  "floor_within_1_accuracy"):
            row[pre + k] = m.get(k)
        pe = m.get("positioning_error")
        if pe:
            for k in ("mean_error", "median_error", "p75_error", "p90_error",
                      "p95_error", "mean_error_ground_m",
                      "median_error_ground_m", "p75_error_ground_m",
                      "p90_error_ground_m", "p95_error_ground_m"):
                row[pre + "pos_" + k] = pe.get(k)
    return row


def main() -> None:
    t_start = time.perf_counter()
    tr, va = load_splits()
    prep = fit_preprocessor(tr)
    wap = prep.wap_cols
    n_total = len(wap)
    col_of = {w: j for j, w in enumerate(wap)}

    y_tr, y_va = joint_label(tr), joint_label(va)
    Xtr_full = prep.positive_representation(tr)
    Xva_full = prep.positive_representation(va)
    coords_tr = tr[["LONGITUDE", "LATITUDE"]].to_numpy(dtype=np.float64)
    coords_va = va[["LONGITUDE", "LATITUDE"]].to_numpy(dtype=np.float64)

    detected_mask = (tr[wap].to_numpy() != NOT_DETECTED).any(axis=0)
    detected_waps = [w for w, d in zip(wap, detected_mask) if d]
    support = (tr[wap].to_numpy() != NOT_DETECTED).sum(axis=0)
    mi, h_y = conditional_entropy_reduction(discretise(tr, wap), y_tr)
    LOG.info("%d WAP columns, %d ever detected in training; H(Y)=%.4f bits",
             n_total, len(detected_waps), h_y)

    # ---- one-off hyper-parameter selection, on trainingData, ALL-WAP --------
    tr_idx, dev_idx = split_train_dev(y_tr)
    LOG.info("selecting k-NN config on dev_sub (%d train_sub / %d dev_sub rows)",
             len(tr_idx), len(dev_idx))
    cfg, trace = select_knn_config(Xtr_full, y_tr, tr_idx, dev_idx)
    LOG.info("FROZEN k-NN config: %s", cfg.as_dict())

    conditions: list[tuple[dict, list[str], bool]] = []

    conditions.append(({"condition": "baseline_all_520", "family": "baseline",
                        "utility_model": "", "rel_minutil_pct": "",
                        "selection": "all", "budget_n": n_total},
                       list(wap), True))
    conditions.append(({"condition": "baseline_detected_465",
                        "family": "baseline", "utility_model": "",
                        "rel_minutil_pct": "", "selection": "detected_in_train",
                        "budget_n": len(detected_waps)}, detected_waps, True))

    # ---- HUIM conditions, read from what PHASE H actually produced ----------
    huim = pd.read_csv(METRICS / "huim_runs.csv")
    huim_with_huis = huim[huim["n_huis"] > 0].copy()
    LOG.info("%d HUIM runs on disk, %d produced at least one HUI",
             len(huim), len(huim_with_huis))

    primary_per_model: dict[str, dict] = {}
    for _, r in huim_with_huis.iterrows():
        ws = load_json(Path(r["path_wap_stats"]))
        order = sorted(ws["per_wap"],
                       key=lambda w: (-ws["per_wap"][w]["utility_contribution"], w))
        conditions.append(({
            "condition": f"huim_union__{r['run_tag']}",
            "family": "huim_union",
            "utility_model": r["utility_model"],
            "rel_minutil_pct": r["rel_minutil_pct"],
            "selection": "union_of_HUI_waps",
            "budget_n": len(order),
            "huim_status": r["status"],
            "n_huis": int(r["n_huis"]),
            "huim_runtime_s": float(r["runtime_s"]),
        }, order, False))
        # the primary HUI set per model: the lowest COMPLETED threshold, since
        # that is the richest trustworthy (non-truncated) ranking available
        if r["status"] == "COMPLETED":
            cur = primary_per_model.get(r["utility_model"])
            if cur is None or r["rel_minutil_pct"] < cur["pct"]:
                primary_per_model[r["utility_model"]] = {
                    "pct": r["rel_minutil_pct"], "order": order,
                    "run_tag": r["run_tag"], "n_huis": int(r["n_huis"])}

    for model, info in primary_per_model.items():
        LOG.info("primary HUI set for %s: %s (%d HUIs, %d WAPs)",
                 model, info["run_tag"], info["n_huis"], len(info["order"]))
        for n in BUDGETS:
            if n > len(info["order"]):
                continue
            conditions.append(({
                "condition": f"huim_topn__{model}__{info['pct']:g}pct__n{n}",
                "family": "huim_topn", "utility_model": model,
                "rel_minutil_pct": info["pct"],
                "selection": "top_n_by_utility_contribution", "budget_n": n,
                "huim_status": "COMPLETED", "n_huis": info["n_huis"],
            }, info["order"][:n], False))

    # ---- controls at matched budgets ----------------------------------------
    # The control budgets must include every feature count a HUIM condition
    # actually uses, otherwise the "matched budget" comparison is not matched:
    # a HUIM union of 91 WAPs would end up being compared against controls at
    # 75 and 100. Those extra budgets are added here.
    order_support = [w for _, w in sorted(
        ((-support[col_of[w]], w) for w in detected_waps))]
    order_mi = [w for _, w in sorted(
        ((-mi[col_of[w]], w) for w in detected_waps))]
    huim_ns = sorted({c["budget_n"] for c, _w, _r in conditions
                      if str(c.get("family", "")).startswith("huim")
                      and isinstance(c.get("budget_n"), int)})
    control_budgets = sorted(set(BUDGETS) | set(huim_ns))
    LOG.info("control budgets: %s (HUIM uses %s)", control_budgets, huim_ns)
    for n in control_budgets:
        if n > len(detected_waps) or n < 1:
            continue
        conditions.append(({"condition": f"control_top_support__n{n}",
                            "family": "control_top_support",
                            "utility_model": "", "rel_minutil_pct": "",
                            "selection": "top_n_by_detection_support",
                            "budget_n": n}, order_support[:n], False))
        conditions.append(({"condition": f"control_top_mi__n{n}",
                            "family": "control_top_mi", "utility_model": "",
                            "rel_minutil_pct": "",
                            "selection": "top_n_by_mutual_information",
                            "budget_n": n}, order_mi[:n], False))
        for seed in CONTROL_SEEDS:
            rng = np.random.default_rng(RANDOM_SEED + seed)
            pick = list(rng.choice(detected_waps, size=n, replace=False))
            conditions.append(({"condition": f"control_random__n{n}__s{seed}",
                                "family": "control_random", "utility_model": "",
                                "rel_minutil_pct": "",
                                "selection": f"random_n_seed{seed}",
                                "budget_n": n}, pick, False))

    LOG.info("%d conditions to evaluate", len(conditions))

    rows, detail = [], {}
    rf_budget = RF_CONDITIONS_MAX
    for ci, (cond, waps, want_rf) in enumerate(conditions, 1):
        cols = [col_of[w] for w in waps if w in col_of]
        use_rf = want_rf and rf_budget > 0
        res = evaluate_once(Xtr_full[:, cols], y_tr, coords_tr,
                            Xva_full[:, cols], y_va, coords_va, cfg,
                            also_random_forest=use_rf)
        if use_rf:
            rf_budget -= 1
        cond = dict(cond)
        cond["n_waps_selected"] = len(cols)
        cond["feature_reduction_pct"] = feature_reduction_pct(len(cols), n_total)
        # Store the FULL list: truncating it silently would make the
        # provenance wrong for every condition with more than 300 WAPs, and
        # anything reading this column back (e.g. the cost benchmark) would
        # measure the wrong feature count.
        cond["selected_waps"] = ";".join(waps)
        row = _flatten(cond, res)
        rows.append(row)
        detail[cond["condition"]] = {"condition": cond, "result": res}
        LOG.info("[%3d/%3d] %-46s n=%4d red=%6.2f%% | bld %.4f flr %.4f "
                 "joint %.4f | medErr %.1f",
                 ci, len(conditions), cond["condition"], len(cols),
                 cond["feature_reduction_pct"],
                 row.get("building_accuracy", float("nan")),
                 row.get("floor_accuracy", float("nan")),
                 row.get("joint_building_floor_accuracy", float("nan")),
                 row.get("pos_median_error", float("nan")))
        if ci % 10 == 0 or ci == len(conditions):
            pd.DataFrame(rows).to_csv(METRICS / "ips_results.csv", index=False)

    pd.DataFrame(rows).to_csv(METRICS / "ips_results.csv", index=False)
    dump_json({
        "phase": "PHASE I - IPS evaluation",
        "environment": environment_info(),
        "protocol": {
            "hyperparameter_selection": "stratified 75/25 train_sub/dev_sub "
                                        "split of trainingData, ALL-WAP "
                                        "features, selected once",
            "frozen_knn_config": cfg.as_dict(),
            "final_fit": "full trainingData (19937 rows)",
            "final_test": "validationData, evaluated once per condition",
            "validation_used_for": "evaluation ONLY - never for fitting the "
                                   "preprocessor, the utility weights, the "
                                   "mining, the feature selection or the "
                                   "hyper-parameters",
            "random_seed": RANDOM_SEED,
            "budgets": BUDGETS,
            "control_seeds": CONTROL_SEEDS,
        },
        "knn_grid_search_trace": trace,
        "label_entropy_H_Y_bits": round(h_y, 5),
        "n_wap_columns": n_total,
        "n_waps_detected_in_training": len(detected_waps),
        "primary_hui_sets": {k: {"run_tag": v["run_tag"], "pct": v["pct"],
                                 "n_huis": v["n_huis"],
                                 "n_waps": len(v["order"])}
                             for k, v in primary_per_model.items()},
        "conditions": detail,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_wall_clock_s": round(time.perf_counter() - t_start, 2),
    }, RESULTS / "ips_summary.json")
    LOG.info("done in %.1fs -> %s", time.perf_counter() - t_start,
             METRICS / "ips_results.csv")


if __name__ == "__main__":
    main()
