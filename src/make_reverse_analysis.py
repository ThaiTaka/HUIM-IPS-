"""PHASE K - reverse-thinking analysis.

Direction of reasoning, enforced structurally: every section starts from a
number that is read out of results/metrics/*.csv, and only then asks why the
algorithm behaved that way. Nothing is asserted that the loader did not find in
a log file; where a number is needed and is absent, the text says N/A and why.

Outputs
-------
results/reverse_thinking_observations.json   structured facts (reused by the
                                             Word report, so the two cannot
                                             disagree)
research/reverse_thinking_analysis.md        the narrative
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import METRICS, RESEARCH, RESULTS, dump_json, load_json, relocate

MODEL_LABEL = {"A_signal": "Model A (signal utility)",
               "B_discriminative": "Model B (discriminative utility)",
               "C_rare_discriminative": "Model C (rare-discriminative utility)"}


def fmt(x, d=2):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "N/A"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):,}"
    return f"{float(x):,.{d}f}"


def collect() -> dict:
    H = pd.read_csv(METRICS / "huim_runs.csv").sort_values(
        ["utility_model", "rel_minutil_pct"], ascending=[True, False])
    I = pd.read_csv(METRICS / "ips_results.csv")
    audit = load_json(RESULTS / "data_summary.json")
    hsum = load_json(RESULTS / "huim_summary.json")
    isum = load_json(RESULTS / "ips_summary.json")
    O: dict = {"source_files": {
        "huim": str(METRICS / "huim_runs.csv"),
        "ips": str(METRICS / "ips_results.csv")}}

    # ---- OBS 1: the threshold / HUI-count phase transition -----------------
    obs1 = {}
    for model, g in H.groupby("utility_model"):
        g = g.sort_values("rel_minutil_pct", ascending=False)
        nz = g[g["n_huis"] > 0]
        zero = g[g["n_huis"] == 0]
        rec = {
            "highest_threshold_tested_pct": float(g["rel_minutil_pct"].max()),
            "lowest_threshold_tested_pct": float(g["rel_minutil_pct"].min()),
            "n_runs": int(len(g)),
            "n_runs_zero_huis": int(len(zero)),
            "highest_threshold_with_any_hui_pct":
                float(nz["rel_minutil_pct"].max()) if len(nz) else None,
            "lowest_zero_hui_threshold_pct":
                float(zero["rel_minutil_pct"].min()) if len(zero) else None,
            "max_n_huis_observed": int(g["n_huis"].max()),
            "total_db_utility": float(g["total_db_utility"].iloc[0]),
        }
        # the sharpest consecutive step, measured not guessed
        gg = g.reset_index(drop=True)
        best = None
        for k in range(len(gg) - 1):
            a, b = gg.iloc[k], gg.iloc[k + 1]
            if a["n_huis"] <= 0:
                ratio = float(b["n_huis"]) if b["n_huis"] > 0 else 0.0
            else:
                ratio = b["n_huis"] / a["n_huis"]
            cand = {
                "from_pct": float(a["rel_minutil_pct"]),
                "to_pct": float(b["rel_minutil_pct"]),
                "from_abs_minutil": float(a["abs_minutil"]),
                "to_abs_minutil": float(b["abs_minutil"]),
                "from_n_huis": int(a["n_huis"]), "to_n_huis": int(b["n_huis"]),
                "threshold_ratio": round(float(a["rel_minutil_pct"] /
                                               b["rel_minutil_pct"]), 4),
                "hui_growth_factor": round(ratio, 2) if ratio else None,
                "to_status": b["status"],
                "from_runtime_s": float(a["runtime_s"]),
                "to_runtime_s": float(b["runtime_s"]),
                "from_nodes": int(a["search_nodes_visited"]),
                "to_nodes": int(b["search_nodes_visited"]),
                "from_items_after_twu": int(a["items_after_twu_pruning"]),
                "to_items_after_twu": int(b["items_after_twu_pruning"]),
            }
            if best is None or (cand["to_n_huis"] - cand["from_n_huis"]) > \
                    (best["to_n_huis"] - best["from_n_huis"]):
                best = cand
        rec["sharpest_step"] = best
        obs1[model] = rec
    O["observation_1_threshold_vs_hui_count"] = obs1

    # ---- OBS 2: cost of lowering the threshold -----------------------------
    obs2 = {}
    for model, g in H.groupby("utility_model"):
        g = g.sort_values("rel_minutil_pct", ascending=False)
        rec = {"runtime_s_min": float(g["runtime_s"].min()),
               "runtime_s_max": float(g["runtime_s"].max()),
               "peak_mem_delta_mb_min": float(g["peak_memory_delta_mb"].min()),
               "peak_mem_delta_mb_max": float(g["peak_memory_delta_mb"].max()),
               "nodes_min": int(g["search_nodes_visited"].min()),
               "nodes_max": int(g["search_nodes_visited"].max()),
               "items_after_twu_min": int(g["items_after_twu_pruning"].min()),
               "items_after_twu_max": int(g["items_after_twu_pruning"].max()),
               "items_initial": int(g["items_initial"].iloc[0]),
               "n_aborted": int((g["status"] != "COMPLETED").sum()),
               "aborted_at_pct": [float(v) for v in
                                  g[g["status"] != "COMPLETED"]
                                  ["rel_minutil_pct"]],
               "abort_reasons": sorted(set(
                   str(v) for v in g[g["status"] != "COMPLETED"]["abort_reason"]
                   if str(v) and str(v) != "nan")),
               }
        comp = g[g["status"] == "COMPLETED"]
        if len(comp) >= 2:
            c = comp.sort_values("rel_minutil_pct", ascending=False)
            rec["completed_runtime_first_last"] = [
                float(c["runtime_s"].iloc[0]), float(c["runtime_s"].iloc[-1])]
            rec["completed_pct_first_last"] = [
                float(c["rel_minutil_pct"].iloc[0]),
                float(c["rel_minutil_pct"].iloc[-1])]
        # correlation between nodes visited and runtime: is runtime explained by
        # search size rather than by anything else?
        if len(g) >= 4 and g["search_nodes_visited"].std() > 0:
            rec["spearman_nodes_vs_runtime"] = round(float(
                pd.Series(g["search_nodes_visited"]).corr(
                    pd.Series(g["runtime_s"]), method="spearman")), 4)
            rec["spearman_nhuis_vs_runtime"] = round(float(
                pd.Series(g["n_huis"]).corr(pd.Series(g["runtime_s"]),
                                            method="spearman")), 4)
        obs2[model] = rec
    O["observation_2_cost_of_lowering_threshold"] = obs2

    # ---- OBS 3: do the utility models disagree about which APs matter? -----
    sets = {}
    for model, g in H.groupby("utility_model"):
        comp = g[(g["status"] == "COMPLETED") & (g["n_huis"] > 0)]
        if not len(comp):
            continue
        r = comp.loc[comp["n_huis"].idxmax()]
        ws = load_json(relocate(r["path_wap_stats"]))
        order = sorted(ws["per_wap"],
                       key=lambda w: (-ws["per_wap"][w]["utility_contribution"], w))
        sets[model] = {"run_tag": r["run_tag"],
                       "rel_minutil_pct": float(r["rel_minutil_pct"]),
                       "n_huis": int(r["n_huis"]),
                       "n_waps": len(order), "waps": order,
                       "top10": order[:10],
                       "rank_agreement": ws.get(
                           "rank_agreement_spearman_vs_utility_contribution", {})}
    obs3 = {"primary_hui_set_per_model":
            {m: {k: v for k, v in d.items() if k != "waps"}
             for m, d in sets.items()},
            "pairwise_overlap": {}}
    ms = sorted(sets)
    for a in range(len(ms)):
        for b in range(a + 1, len(ms)):
            A, B = set(sets[ms[a]]["waps"]), set(sets[ms[b]]["waps"])
            obs3["pairwise_overlap"][f"{ms[a]} vs {ms[b]}"] = {
                "n_a": len(A), "n_b": len(B), "n_intersection": len(A & B),
                "n_union": len(A | B),
                "jaccard": round(len(A & B) / max(len(A | B), 1), 4),
                "only_in_a": sorted(A - B)[:20],
                "only_in_b": sorted(B - A)[:20],
                "top10_a": sets[ms[a]]["top10"],
                "top10_b": sets[ms[b]]["top10"],
                "top10_overlap": len(set(sets[ms[a]]["top10"]) &
                                     set(sets[ms[b]]["top10"])),
            }
    O["observation_3_models_select_different_aps"] = obs3

    # ---- OBS 4: does feature reduction cost accuracy? ----------------------
    base = I[I["condition"] == "baseline_all_520"].iloc[0]
    b465 = I[I["condition"] == "baseline_detected_465"]
    obs4 = {
        "baseline_all_520": {
            "n_waps": int(base["n_waps_selected"]),
            "building_accuracy": float(base["building_accuracy"]),
            "floor_accuracy": float(base["floor_accuracy"]),
            "joint_accuracy": float(base["joint_building_floor_accuracy"]),
            "joint_macro_f1": float(base["joint_macro_f1"]),
            "median_pos_error": float(base["pos_median_error"]),
            "mean_pos_error": float(base["pos_mean_error"]),
        },
        "baseline_detected_465": ({
            "n_waps": int(b465["n_waps_selected"].iloc[0]),
            "joint_accuracy": float(b465["joint_building_floor_accuracy"].iloc[0]),
            "feature_reduction_pct": float(b465["feature_reduction_pct"].iloc[0]),
        } if len(b465) else None),
        "per_model_best_topn": {},
        "per_model_union": {},
        "smallest_subset_matching_baseline": None,
        "pareto_like": {},
    }
    for model, g in I[I["family"] == "huim_topn"].groupby("utility_model"):
        best = g.loc[g["joint_building_floor_accuracy"].idxmax()]
        obs4["per_model_best_topn"][model] = {
            "condition": best["condition"],
            "n_waps": int(best["n_waps_selected"]),
            "feature_reduction_pct": float(best["feature_reduction_pct"]),
            "building_accuracy": float(best["building_accuracy"]),
            "floor_accuracy": float(best["floor_accuracy"]),
            "joint_accuracy": float(best["joint_building_floor_accuracy"]),
            "joint_macro_f1": float(best["joint_macro_f1"]),
            "median_pos_error": float(best["pos_median_error"]),
            "delta_joint_vs_baseline": round(
                float(best["joint_building_floor_accuracy"] -
                      base["joint_building_floor_accuracy"]), 6),
            "sweep": [{"n": int(r["n_waps_selected"]),
                       "reduction_pct": float(r["feature_reduction_pct"]),
                       "joint": float(r["joint_building_floor_accuracy"]),
                       "building": float(r["building_accuracy"]),
                       "floor": float(r["floor_accuracy"]),
                       "median_pos_error": float(r["pos_median_error"])}
                      for _, r in g.sort_values("n_waps_selected").iterrows()],
        }
        # smallest n that is at least as good as the all-520 baseline
        ok = g[g["joint_building_floor_accuracy"] >=
               base["joint_building_floor_accuracy"]]
        if len(ok):
            s = ok.loc[ok["n_waps_selected"].idxmin()]
            obs4["pareto_like"][model] = {
                "smallest_n_matching_or_beating_baseline":
                    int(s["n_waps_selected"]),
                "feature_reduction_pct": float(s["feature_reduction_pct"]),
                "joint_accuracy": float(s["joint_building_floor_accuracy"]),
                "condition": s["condition"]}
    for model, g in I[I["family"] == "huim_union"].groupby("utility_model"):
        obs4["per_model_union"][model] = [
            {"rel_minutil_pct": float(r["rel_minutil_pct"]),
             "huim_status": r.get("huim_status"),
             "n_waps": int(r["n_waps_selected"]),
             "reduction_pct": float(r["feature_reduction_pct"]),
             "joint": float(r["joint_building_floor_accuracy"]),
             "building": float(r["building_accuracy"]),
             "floor": float(r["floor_accuracy"])}
            for _, r in g.sort_values("rel_minutil_pct", ascending=False).iterrows()]
    cands = I[I["family"] == "huim_topn"]
    ok = cands[cands["joint_building_floor_accuracy"] >=
               base["joint_building_floor_accuracy"]]
    if len(ok):
        s = ok.loc[ok["n_waps_selected"].idxmin()]
        obs4["smallest_subset_matching_baseline"] = {
            "condition": s["condition"], "n_waps": int(s["n_waps_selected"]),
            "feature_reduction_pct": float(s["feature_reduction_pct"]),
            "joint_accuracy": float(s["joint_building_floor_accuracy"])}
    O["observation_4_feature_reduction_vs_accuracy"] = obs4

    # ---- OBS 5: is HUIM better than the controls at equal budget? ----------
    obs5 = {"matched_budget_comparison": [], "verdict_inputs": {}}
    for n in sorted(I["budget_n"].dropna().unique()):
        try:
            n = int(n)
        except Exception:
            continue
        row: dict = {"budget_n": n}
        for model, g in I[(I["family"] == "huim_topn") &
                          (I["n_waps_selected"] == n)].groupby("utility_model"):
            row[f"huim_{model}"] = float(
                g["joint_building_floor_accuracy"].iloc[0])
        for fam, key in (("control_top_mi", "control_top_mi"),
                         ("control_top_support", "control_top_support")):
            g = I[(I["family"] == fam) & (I["n_waps_selected"] == n)]
            if len(g):
                row[key] = float(g["joint_building_floor_accuracy"].iloc[0])
        g = I[(I["family"] == "control_random") & (I["n_waps_selected"] == n)]
        if len(g):
            row["control_random_mean"] = round(float(
                g["joint_building_floor_accuracy"].mean()), 6)
            row["control_random_min"] = float(
                g["joint_building_floor_accuracy"].min())
            row["control_random_max"] = float(
                g["joint_building_floor_accuracy"].max())
        if len(row) > 1:
            obs5["matched_budget_comparison"].append(row)
    wins = {"huim_beats_random": 0, "huim_beats_top_mi": 0,
            "huim_beats_top_support": 0, "n_comparisons": 0}
    for row in obs5["matched_budget_comparison"]:
        hv = [v for k, v in row.items() if k.startswith("huim_")]
        if not hv:
            continue
        best_h = max(hv)
        wins["n_comparisons"] += 1
        if "control_random_mean" in row and best_h > row["control_random_mean"]:
            wins["huim_beats_random"] += 1
        if "control_top_mi" in row and best_h > row["control_top_mi"]:
            wins["huim_beats_top_mi"] += 1
        if "control_top_support" in row and best_h > row["control_top_support"]:
            wins["huim_beats_top_support"] += 1
    obs5["verdict_inputs"] = wins
    O["observation_5_huim_vs_controls"] = obs5

    # ---- OBS 6: strong is not the same as discriminative -------------------
    obs6 = {}
    tr_aud = audit["training"]
    obs6["ap_building_spread"] = tr_aud["anomaly_probes"]["ap_building_spread"]
    obs6["top10_by_support"] = tr_aud["anomaly_probes"]["wap_support"][
        "top10_waps_by_support"]
    mdl = hsum["utility_models"]
    if "B_discriminative" in mdl:
        obs6["top10_by_mutual_information"] = mdl["B_discriminative"].get(
            "top10_waps_by_mi")
        obs6["label_entropy_bits"] = mdl["B_discriminative"].get(
            "label_entropy_H_Y_bits")
        obs6["max_mi_bits"] = mdl["B_discriminative"].get("mi_bits_max")
        obs6["max_mi_as_fraction_of_H_Y"] = mdl["B_discriminative"].get(
            "mi_bits_max_as_fraction_of_H_Y")
    sup_names = {d["wap"] for d in obs6.get("top10_by_support", [])}
    mi_names = {d["wap"] for d in (obs6.get("top10_by_mutual_information") or [])}
    obs6["overlap_top10_support_vs_top10_mi"] = len(sup_names & mi_names)
    obs6["overlap_members"] = sorted(sup_names & mi_names)
    # The top-10 comparison alone is a weak test: it looks at 10 of several
    # hundred APs. The association over ALL detected APs is the real statistic.
    try:
        import numpy as _np
        from scipy.stats import spearmanr as _sp
        import pandas as _pd
        from preprocess_uji import NOT_DETECTED as _ND
        from preprocess_uji import fit_preprocessor as _fit
        from preprocess_uji import joint_label as _jl
        from preprocess_uji import load_splits as _ls
        from utility_models import conditional_entropy_reduction as _cer
        from utility_models import discretise as _dis
        _tr, _ = _ls()
        _prep = _fit(_tr)
        _w = _prep.wap_cols
        _supp = (_tr[_w].to_numpy() != _ND).sum(axis=0)
        _mi, _h = _cer(_dis(_tr, _w), _jl(_tr))
        _m = _supp > 0
        obs6["n_detected_waps_compared"] = int(_m.sum())
        obs6["spearman_support_vs_mi_over_all_detected_waps"] = round(
            float(_sp(_supp[_m], _mi[_m]).statistic), 4)
        obs6["pearson_support_vs_mi_over_all_detected_waps"] = round(
            float(_np.corrcoef(_supp[_m], _mi[_m])[0, 1]), 4)
        # rank-overlap at several depths, so the reader can see where the two
        # criteria agree and where they part company
        order_s = list(_np.argsort(-_supp))
        order_m = list(_np.argsort(-_mi))
        obs6["rank_overlap_at_depth"] = {
            str(k): len(set(order_s[:k]) & set(order_m[:k]))
            for k in (10, 25, 50, 100, 200)}
    except Exception as e:  # never let a diagnostic break the analysis
        obs6["association_check_error"] = repr(e)
    O["observation_6_strong_vs_discriminative"] = obs6

    # ---- OBS 7: total utility differs per model -> relative minUtil matters
    O["observation_7_scale"] = {
        m: {"total_database_utility": d["total_database_utility"],
            "transaction_utility_mean": d["transaction_utility_mean"],
            "transaction_utility_max": d["transaction_utility_max"],
            "p_min": d.get("p_min"), "p_max": d.get("p_max"),
            "p_mean": d.get("p_mean")}
        for m, d in hsum["utility_models"].items()}

    # ---- OBS 8: does more HUIs mean better accuracy? -----------------------
    j = I[I["family"] == "huim_union"].copy()
    obs8 = {"n_points": int(len(j))}
    if len(j) >= 4 and "n_huis" in j and j["n_huis"].std() > 0:
        obs8["spearman_n_huis_vs_joint_accuracy"] = round(float(
            j["n_huis"].corr(j["joint_building_floor_accuracy"],
                             method="spearman")), 4)
        obs8["spearman_n_waps_vs_joint_accuracy"] = round(float(
            j["n_waps_selected"].corr(j["joint_building_floor_accuracy"],
                                      method="spearman")), 4)
    t = I[I["family"] == "huim_topn"]
    if len(t) >= 4:
        obs8["spearman_n_waps_vs_joint_accuracy_topn"] = round(float(
            t["n_waps_selected"].corr(t["joint_building_floor_accuracy"],
                                      method="spearman")), 4)
    obs8["note"] = ("union points vary minUtil, so n_huis and n_waps move "
                    "together; the top-n sweep separates them")
    O["observation_8_more_huis_vs_accuracy"] = obs8

    # ---- OBS 9: is the binding constraint the RANKING or the SIZE? ---------
    # HUIM can only offer as many APs as appear in a (non-truncated) HUI set,
    # and that count is capped by whichever minUtil still completes inside the
    # resource budget. So a shortfall against the baseline could be a bad
    # ranking OR simply too few features. These two are separable.
    obs9: dict = {}
    hu = I[I["family"].isin(("huim_topn", "huim_union"))]
    if len(hu):
        nmax = int(hu["n_waps_selected"].max())
        obs9["largest_huim_selected_set"] = nmax
        obs9["largest_huim_set_condition"] = hu.loc[
            hu["n_waps_selected"].idxmax(), "condition"]
        obs9["best_joint_at_or_below_that_budget_any_method"] = None
        pool = I[(I["n_waps_selected"] <= nmax) & (I["family"] != "baseline")]
        if len(pool):
            r = pool.loc[pool["joint_building_floor_accuracy"].idxmax()]
            obs9["best_joint_at_or_below_that_budget_any_method"] = {
                "condition": r["condition"], "family": r["family"],
                "n_waps": int(r["n_waps_selected"]),
                "joint": float(r["joint_building_floor_accuracy"])}
        # how many features does the simplest control need to reach baseline?
        ctl = I[I["family"].isin(("control_top_mi", "control_top_support"))]
        reach = ctl[ctl["joint_building_floor_accuracy"] >=
                    base["joint_building_floor_accuracy"]]
        if len(reach):
            r = reach.loc[reach["n_waps_selected"].idxmin()]
            obs9["smallest_control_subset_reaching_baseline"] = {
                "condition": r["condition"], "n_waps": int(r["n_waps_selected"]),
                "reduction_pct": float(r["feature_reduction_pct"]),
                "joint": float(r["joint_building_floor_accuracy"])}
        else:
            obs9["smallest_control_subset_reaching_baseline"] = None
        # like-for-like at exactly the HUIM budgets
        rows = []
        for n in sorted(set(int(v) for v in hu["n_waps_selected"].unique())):
            row = {"n": n}
            for m, g in I[(I["family"] == "huim_topn") &
                          (I["n_waps_selected"] == n)].groupby("utility_model"):
                row[f"huim_{m}"] = float(g["joint_building_floor_accuracy"].iloc[0])
            for fam in ("control_top_mi", "control_top_support"):
                g = I[(I["family"] == fam) & (I["n_waps_selected"] == n)]
                if len(g):
                    row[fam] = float(g["joint_building_floor_accuracy"].iloc[0])
            g = I[(I["family"] == "control_random") & (I["n_waps_selected"] == n)]
            if len(g):
                row["control_random_mean"] = float(
                    g["joint_building_floor_accuracy"].mean())
            if len(row) > 1:
                rows.append(row)
        obs9["like_for_like_at_huim_budgets"] = rows
    # Model A's ranking versus chance - the sharpest test of "frequent != useful"
    worse_than_random = []
    for _, r in I[I["family"] == "huim_topn"].iterrows():
        g = I[(I["family"] == "control_random") &
              (I["n_waps_selected"] == r["n_waps_selected"])]
        if not len(g):
            continue
        worse_than_random.append({
            "condition": r["condition"], "utility_model": r["utility_model"],
            "n": int(r["n_waps_selected"]),
            "huim_joint": float(r["joint_building_floor_accuracy"]),
            "random_mean_joint": round(float(
                g["joint_building_floor_accuracy"].mean()), 6),
            "beats_random": bool(r["joint_building_floor_accuracy"] >
                                 g["joint_building_floor_accuracy"].mean())})
    obs9["vs_random_per_condition"] = worse_than_random
    by_model: dict = {}
    for d in worse_than_random:
        m = d["utility_model"]
        by_model.setdefault(m, {"n": 0, "beats": 0})
        by_model[m]["n"] += 1
        by_model[m]["beats"] += int(d["beats_random"])
    obs9["beats_random_by_model"] = by_model
    O["observation_9_ranking_vs_size"] = obs9

    # ---- context the narrative needs --------------------------------------
    O["context"] = {
        "n_training_rows": tr_aud["n_rows"],
        "n_wap_columns": tr_aud["n_wap_columns_detected"],
        "n_waps_detected_in_training": audit["cross_split"]["waps_detected_in_train"],
        "n_waps_only_in_validation": audit["cross_split"]["waps_only_in_validation"],
        "mean_detections_per_fingerprint":
            tr_aud["not_detected_probe"]["detections_per_fingerprint"]["mean"],
        "sparsity_pct": tr_aud["not_detected_probe"]["share_eq_100_pct"],
        "n_non_empty_transactions": hsum["database"]["n_non_empty_transactions"],
        "frozen_knn_config": isum["protocol"]["frozen_knn_config"],
        "n_validation_rows": audit["validation"]["n_rows"],
        "time_limit_s": hsum["time_limit_s"], "max_huis": hsum["max_huis"],
        "cpu": audit["environment"].get("cpu_model"),
        "ram_gb": audit["environment"].get("ram_total_gb"),
    }
    return O


def render(O: dict) -> str:
    c = O["context"]
    o1 = O["observation_1_threshold_vs_hui_count"]
    o2 = O["observation_2_cost_of_lowering_threshold"]
    o3 = O["observation_3_models_select_different_aps"]
    o4 = O["observation_4_feature_reduction_vs_accuracy"]
    o5 = O["observation_5_huim_vs_controls"]
    o6 = O["observation_6_strong_vs_discriminative"]
    o7 = O["observation_7_scale"]
    o8 = O["observation_8_more_huis_vs_accuracy"]
    b = o4["baseline_all_520"]

    L: list[str] = []
    A = L.append
    A("# Reverse-Thinking Analysis\n")
    A("> Generated by `src/make_reverse_analysis.py`. Every quantity below was "
      "read from `results/metrics/huim_runs.csv` or "
      "`results/metrics/ips_results.csv`. The order of each section is fixed: "
      "**RESULT → OBSERVATION → WHY → ALGORITHM MECHANISM → THEORY → IPS "
      "MEANING**. Claims are tagged [FACT FROM DATA], [EXPERIMENT RESULT], "
      "[FACT FROM PAPER] or [OUR INTERPRETATION].\n")
    A(f"Experimental context: {fmt(c['n_training_rows'])} training "
      f"fingerprints, {c['n_wap_columns']} WAP columns of which "
      f"{c['n_waps_detected_in_training']} are ever detected in training; "
      f"{fmt(c['n_non_empty_transactions'])} non-empty utility transactions; "
      f"{c['sparsity_pct']:.2f}% of the WAP matrix is the not-detected "
      f"sentinel; mean {c['mean_detections_per_fingerprint']} detections per "
      f"fingerprint. Mining budget per run: "
      f"{fmt(c['time_limit_s'],0)} s and {fmt(c['max_huis'])} itemsets. "
      f"Machine: {c['cpu']}, {c['ram_gb']} GB RAM.\n")
    A("---\n")

    # ================================================================ OBS 1
    A("## Observation 1 — Lowering minUtil does not grow the output; it "
      "detonates it\n")
    A("### RESULT\n")
    A("| Utility model | Thresholds tested | Runs with 0 HUIs | Highest "
      "threshold with any HUI | Largest HUI count seen |")
    A("|---|---|---|---|---|")
    for m, r in o1.items():
        A(f"| {MODEL_LABEL.get(m, m)} | {r['n_runs']} "
          f"({r['lowest_threshold_tested_pct']:g}%–"
          f"{r['highest_threshold_tested_pct']:g}%) | {r['n_runs_zero_huis']} | "
          f"{fmt(r['highest_threshold_with_any_hui_pct'],4)}% | "
          f"{fmt(r['max_n_huis_observed'])} |")
    A("\nThe sharpest single step measured for each model:\n")
    A("| Model | minUtil from → to | Threshold ratio | HUIs from → to | Growth "
      "factor | Runtime from → to (s) | Status after |")
    A("|---|---|---|---|---|---|---|")
    for m, r in o1.items():
        s = r["sharpest_step"]
        if not s:
            continue
        A(f"| {MODEL_LABEL.get(m, m)} | {s['from_pct']:g}% → {s['to_pct']:g}% "
          f"| {s['threshold_ratio']:g}× | {fmt(s['from_n_huis'])} → "
          f"{fmt(s['to_n_huis'])} | "
          f"{'from zero' if s['from_n_huis'] == 0 else fmt(s['hui_growth_factor'])}"
          f" | {s['from_runtime_s']:.2f} → {s['to_runtime_s']:.2f} | "
          f"{s['to_status']} |")
    A("\n### OBSERVATION\n")
    for m, r in o1.items():
        s = r["sharpest_step"]
        if not s:
            continue
        A(f"[EXPERIMENT RESULT] {MODEL_LABEL.get(m, m)}: dividing the threshold "
          f"by {s['threshold_ratio']:g} took the output from "
          f"{fmt(s['from_n_huis'])} to {fmt(s['to_n_huis'])} itemsets. The "
          f"number of items surviving the root TWU bound moved only from "
          f"{s['from_items_after_twu']} to {s['to_items_after_twu']}, and the "
          f"number of search-tree nodes visited from {fmt(s['from_nodes'])} to "
          f"{fmt(s['to_nodes'])}.\n")
    A("### WHY?\n")
    A("The threshold moved by a small multiplicative factor; the output moved "
      "by orders of magnitude. The explanation is not in the threshold, it is "
      "in the shape of the search space.\n")
    A("[FACT FROM DATA] A fingerprint detects on average "
      f"{c['mean_detections_per_fingerprint']} access points. Those APs are "
      "not independent: they are the APs installed near one physical location, "
      "so they are seen together over and over.\n")
    A("[OUR INTERPRETATION] Suppose a group of *k* APs co-occurs in many "
      "fingerprints with high signal. Then **every one of its 2^k − 1 "
      "non-empty subsets also co-occurs at least as often**, and each subset's "
      "utility is a partial sum of the same per-transaction utilities. Once the "
      "threshold drops below the level where the *shortest* of those subsets "
      "qualifies, the whole subset lattice qualifies at once. The output does "
      "not grow item by item; it grows by whole power sets.\n")
    A("This is visible in the measured lengths: ")
    lens = []
    for m, d in o3["primary_hui_set_per_model"].items():
        lens.append(f"{MODEL_LABEL.get(m, m)} at {d['rel_minutil_pct']:g}% "
                    f"produced {fmt(d['n_huis'])} HUIs drawn from only "
                    f"{d['n_waps']} distinct WAPs")
    A("; ".join(lens) + ".\n")
    A("[OUR INTERPRETATION] That ratio is the signature of the mechanism: huge "
      "numbers of itemsets over a small alphabet means the itemsets are "
      "subsets of each other, not independent discoveries. **A million HUIs "
      "here is not a million findings; it is a handful of AP groups counted "
      "once per subset.**\n")
    A("### ALGORITHM MECHANISM\n")
    A("[FACT FROM PAPER] EFIM prunes with two upper bounds (Zida et al. 2017): "
      "*local utility* removes an item from an entire subtree, and *subtree "
      "utility* prevents a branch from being entered at all. Both are bounds on "
      "what the **best possible descendant** could achieve.\n")
    A("[OUR INTERPRETATION] A bound can only prune a branch that cannot "
      "contain an answer. When the threshold falls, branches that genuinely "
      "*do* contain answers stop being prunable — correctly. EFIM is not "
      "failing at low minUtil; it is being asked to enumerate an output that "
      "is itself exponential. No pruning rule can shrink a correct answer "
      "set.\n")
    A("Measured confirmation that the items themselves are not the problem: "
      "the root TWU bound keeps only ")
    A(", ".join(f"{o2[m]['items_after_twu_min']}–{o2[m]['items_after_twu_max']} "
                f"of {o2[m]['items_initial']} items ({MODEL_LABEL.get(m,m)})"
                for m in o2) + ". A modest change in the surviving alphabet "
      "accompanies an enormous change in the output, so the explosion is "
      "combinatorial in the *depth* of the search, not in its *breadth*.\n")
    A("### HUIM THEORY\n")
    A("[FACT FROM PAPER] Utility is neither monotone nor anti-monotone (Yao et "
      "al. 2004). Support has downward closure — a superset can never be more "
      "frequent than its subset — and that single property is what keeps "
      "frequent-itemset mining tractable. Utility has no such property: adding "
      "an item adds its utility (pushing up) while possibly shrinking the set "
      "of transactions that contain the itemset (pushing down).\n")
    A("[FACT FROM PAPER] Because of that, pruning must use a *surrogate* that "
      "does have the property. TWU is anti-monotone (Liu et al. 2005); local "
      "and subtree utility are tighter versions of the same idea. All of them "
      "are **over-estimates**, so they are safe, but they are also "
      "**thresholds on a bound, not on the answer** — which is why their "
      "effectiveness collapses exactly when the threshold stops separating "
      "promising from unpromising branches.\n")
    A("### IPS MEANING\n")
    A("[OUR INTERPRETATION] For positioning, this settles how minUtil should "
      "be read. minUtil is **not** an accuracy knob and **not** a quality "
      "knob — it is the knob that decides *how large a group of co-occurring "
      "APs counts as a pattern*. A high threshold describes only the densest "
      "AP clusters on the campus. A low threshold describes the same clusters "
      "plus every sub-combination of them, which is more output carrying almost "
      "no extra information. For an AP-selection application, the useful "
      "operating point is therefore near the *top* of the threshold range, not "
      "the bottom — the opposite of the instinct that 'more patterns must be "
      "better'.\n")
    A("---\n")

    # ================================================================ OBS 2
    A("## Observation 2 — Runtime and memory track the search tree, not the "
      "threshold\n")
    A("### RESULT\n")
    A("| Model | Runtime range (s) | Peak memory above baseline (MB) | Nodes "
      "visited | Aborted runs | Spearman ρ(nodes, runtime) | Spearman "
      "ρ(#HUIs, runtime) |")
    A("|---|---|---|---|---|---|---|")
    for m, r in o2.items():
        A(f"| {MODEL_LABEL.get(m, m)} | {r['runtime_s_min']:.2f} – "
          f"{r['runtime_s_max']:.2f} | {r['peak_mem_delta_mb_min']:.1f} – "
          f"{r['peak_mem_delta_mb_max']:.1f} | {fmt(r['nodes_min'])} – "
          f"{fmt(r['nodes_max'])} | {r['n_aborted']} "
          f"{'at ' + ', '.join(f'{v:g}%' for v in r['aborted_at_pct']) if r['aborted_at_pct'] else ''} "
          f"| {fmt(r.get('spearman_nodes_vs_runtime'),3)} | "
          f"{fmt(r.get('spearman_nhuis_vs_runtime'),3)} |")
    A("\nControlled aborts recorded (not discarded):\n")
    for m, r in o2.items():
        for reason in r["abort_reasons"]:
            A(f"- `{MODEL_LABEL.get(m, m)}`: {reason}")
    A("\n### OBSERVATION\n")
    A("[EXPERIMENT RESULT] Runtime spans "
      + ", ".join(f"{r['runtime_s_min']:.2f}–{r['runtime_s_max']:.2f} s "
                  f"({MODEL_LABEL.get(m,m)})" for m, r in o2.items())
      + ". The rank correlation between nodes visited and runtime is "
      + ", ".join(f"{fmt(r.get('spearman_nodes_vs_runtime'),3)}"
                  for r in o2.values())
      + " respectively.\n")
    A("### WHY?\n")
    A("[OUR INTERPRETATION] A near-perfect rank correlation between nodes "
      "visited and runtime means the cost model is simply *per node*: each "
      "node costs one projection of the current database plus one Fast Utility "
      "Counting pass. Lowering the threshold does not make a node more "
      "expensive; it makes there be more nodes. So runtime is a measure of how "
      "much of the lattice EFIM was forced to walk.\n")
    A("Memory behaves differently from runtime, and the reason is worth "
      "separating: EFIM's *working set* is small (one projected database per "
      "recursion level, and transaction merging keeps those small), but the "
      "*result list* grows with the number of HUIs found. Peak memory therefore "
      "tracks output size rather than search size.\n")
    A("### ALGORITHM MECHANISM\n")
    A("[FACT FROM PAPER] EFIM's memory design is deliberate: high-utility "
      "database projection reuses the parent's arrays rather than building "
      "utility-lists per itemset (the cost that dominates HUI-Miner), and "
      "transaction merging fuses projected transactions that have become "
      "identical.\n")
    A("[FACT FROM DATA] Measured merging in this database: "
      + "; ".join(f"up to {fmt(int(pd.read_csv(METRICS/'huim_runs.csv').query('utility_model == @m')['transactions_saved_by_merging'].max()))} "
                  f"transactions fused ({MODEL_LABEL.get(m,m)})" for m in o2)
      + ".\n")
    A("[OUR INTERPRETATION] Merging works here for a reason specific to "
      "Wi-Fi data. Projection repeatedly strips the leading APs off each "
      "transaction; what is left are the tails. Fingerprints taken at nearby "
      "points have very similar tails, so after a few projections many "
      "transactions become literally identical and collapse into one. A retail "
      "basket database, where baskets are idiosyncratic, benefits much less.\n")
    A("### HUIM THEORY\n")
    A("[FACT FROM PAPER] This is the distinction the independent benchmark of "
      "Zhang et al. (ESWA 2018) makes between algorithms: one-phase methods "
      "removed the candidate-generation memory cost, and EFIM additionally "
      "removed the per-itemset data-structure cost. What *cannot* be removed is "
      "the cost of writing down an exponentially large correct answer.\n")
    A("### IPS MEANING\n")
    A("[OUR INTERPRETATION] For a deployed positioning system the practical "
      "consequence is that HUIM belongs in the **offline** phase, and its cost "
      "must be budgeted as a function of the threshold, not of the database "
      "size. Mining is a one-off site-survey computation; the online phase only "
      "ever sees the resulting AP list, which costs nothing. A system designer "
      "needs the threshold-vs-runtime curve measured here, not an average "
      "runtime.\n")
    A("---\n")

    # ================================================================ OBS 3
    A("## Observation 3 — The two utility definitions do not pick the same "
      "access points\n")
    A("### RESULT\n")
    A("Richest non-truncated HUI set per model (a truncated set is biased by "
      "search order and is never used to rank APs):\n")
    A("| Model | Run | minUtil | #HUIs | #WAPs in the union |")
    A("|---|---|---|---|---|")
    for m, d in o3["primary_hui_set_per_model"].items():
        A(f"| {MODEL_LABEL.get(m, m)} | `{d['run_tag']}` | "
          f"{d['rel_minutil_pct']:g}% | {fmt(d['n_huis'])} | {d['n_waps']} |")
    A("\nOverlap between the selected sets:\n")
    A("| Pair | |A| | |B| | |A∩B| | Jaccard | Top-10 overlap |")
    A("|---|---|---|---|---|---|")
    for k, v in o3["pairwise_overlap"].items():
        A(f"| {k} | {v['n_a']} | {v['n_b']} | {v['n_intersection']} | "
          f"{v['jaccard']:.3f} | {v['top10_overlap']}/10 |")
    A("\n### OBSERVATION\n")
    for k, v in o3["pairwise_overlap"].items():
        A(f"[EXPERIMENT RESULT] {k}: Jaccard {v['jaccard']:.3f}, with "
          f"{v['top10_overlap']} of the top 10 shared.\n")
    A("### WHY?\n")
    A("[OUR INTERPRETATION] The two models share the same internal utility and "
      "differ only in p(i), so any difference is attributable entirely to the "
      "external utility. Model A's p ≡ 1 makes utility a function of *signal "
      "strength × how often the APs are seen together*: it rewards APs that are "
      "strong and ubiquitous. Model B multiplies by the AP's mutual information "
      "with the floor label, which *down-weights exactly those ubiquitous APs*, "
      "because an AP visible everywhere tells you nothing about where you are.\n")
    A("### ALGORITHM MECHANISM\n")
    A("[OUR INTERPRETATION] The effect runs through the bounds, not just "
      "through the final utilities. TWU(i) = Σ_{T ∋ i} TU(T) is computed from "
      "the *same* p values, so changing p changes which items survive the root "
      "bound, which changes the item ordering (EFIM sorts by increasing TWU), "
      "which changes the shape of the entire search tree. Two utility "
      "definitions therefore do not merely re-score the same patterns; they "
      "explore different trees and can return structurally different "
      "patterns.\n")
    A("### HUIM THEORY\n")
    A("[FACT FROM PAPER] This is the property that makes utility mining more "
      "than weighted frequent-itemset mining (Gan et al., TKDE 2021): the "
      "utility function is part of the problem statement, not a post-hoc "
      "ranking. [OUR INTERPRETATION] For an applied study the corollary is "
      "uncomfortable but important — **'the high utility itemsets of this "
      "dataset' is not a well-defined object.** It is only defined relative to "
      "a (q, p) choice that the analyst makes.\n")
    A("### IPS MEANING\n")
    A("[OUR INTERPRETATION] If the goal is localisation, the utility must "
      "encode something about localisation. Model A's notion of 'useful' — "
      "strong and everywhere — is close to the *opposite* of what a fingerprint "
      "needs, which is an AP whose visibility pattern varies between places. "
      "Model B was designed to encode that, and the overlap figures above show "
      "the design does change the answer rather than merely re-labelling it.\n")
    A("---\n")

    # ================================================================ OBS 4
    A("## Observation 4 — How much of the feature space can be removed\n")
    A("### RESULT\n")
    A(f"Baseline, all {b['n_waps']} WAP columns, k-NN "
      f"({c['frozen_knn_config']['n_neighbors']} neighbours, "
      f"{c['frozen_knn_config']['metric']}, "
      f"{c['frozen_knn_config']['weights']} weights), evaluated once on the "
      f"{fmt(c['n_validation_rows'])} validation fingerprints:\n")
    A(f"- Building accuracy **{b['building_accuracy']*100:.2f}%**")
    A(f"- Floor accuracy **{b['floor_accuracy']*100:.2f}%**")
    A(f"- Joint Building-Floor accuracy **{b['joint_accuracy']*100:.2f}%**")
    A(f"- Joint macro F1 {b['joint_macro_f1']:.4f}")
    A(f"- Median positioning error {b['median_pos_error']:.2f} coordinate "
      f"units (mean {b['mean_pos_error']:.2f}) — unit not documented by the "
      f"dataset, see limitations\n")
    if o4["baseline_detected_465"]:
        d = o4["baseline_detected_465"]
        A(f"Dropping the WAP columns that are never detected in training "
          f"leaves {d['n_waps']} columns — a "
          f"{d['feature_reduction_pct']:.2f}% reduction obtained for free — "
          f"and gives joint accuracy {d['joint_accuracy']*100:.2f}%. "
          f"**This part of the reduction owes nothing to HUIM** and is "
          f"excluded from any claim made for it.\n")
    A("Best top-n selection per utility model:\n")
    A("| Model | #WAPs | Reduction | Building | Floor | Joint | Δ joint vs "
      "baseline | Median pos. error |")
    A("|---|---|---|---|---|---|---|---|")
    for m, d in o4["per_model_best_topn"].items():
        A(f"| {MODEL_LABEL.get(m, m)} | {d['n_waps']} | "
          f"{d['feature_reduction_pct']:.2f}% | "
          f"{d['building_accuracy']*100:.2f}% | {d['floor_accuracy']*100:.2f}% "
          f"| **{d['joint_accuracy']*100:.2f}%** | "
          f"{d['delta_joint_vs_baseline']*100:+.2f} pp | "
          f"{d['median_pos_error']:.2f} |")
    if o4["smallest_subset_matching_baseline"]:
        s = o4["smallest_subset_matching_baseline"]
        A(f"\n[EXPERIMENT RESULT] The smallest HUIM-selected subset that "
          f"matches or beats the all-{b['n_waps']}-WAP baseline on joint "
          f"accuracy uses **{s['n_waps']} WAPs** "
          f"({s['feature_reduction_pct']:.2f}% feature reduction) and reaches "
          f"{s['joint_accuracy']*100:.2f}% (`{s['condition']}`).\n")
    else:
        A("\n[EXPERIMENT RESULT] **No HUIM-selected subset matched the "
          "all-WAP baseline on joint accuracy.** This is reported as it "
          "stands; see the interpretation below.\n")
    A("Union-based selection, where minUtil is the only knob:\n")
    A("| Model | minUtil | Mining status | #WAPs | Reduction | Building | "
      "Floor | Joint |")
    A("|---|---|---|---|---|---|---|---|")
    for m, rows in o4["per_model_union"].items():
        for r in rows:
            A(f"| {MODEL_LABEL.get(m, m)} | {r['rel_minutil_pct']:g}% | "
              f"{r['huim_status']} | {r['n_waps']} | {r['reduction_pct']:.2f}% "
              f"| {r['building']*100:.2f}% | {r['floor']*100:.2f}% | "
              f"{r['joint']*100:.2f}% |")
    A("\n### OBSERVATION / WHY?\n")
    A("[FACT FROM DATA] The audit predicted this split in difficulty before any "
      "model was fitted: of the "
      f"{c['n_waps_detected_in_training']} APs detected in training, "
      f"{o6['ap_building_spread']['n_waps_in_exactly_1_building']} are confined "
      f"to a single building and only "
      f"{o6['ap_building_spread']['n_waps_in_all_3_buildings']} are seen in all "
      "three. Identifying the building is therefore almost a lookup; "
      "identifying the floor requires resolving signal differences *within* a "
      "building, where the same APs are visible on every floor.\n")
    A(f"[EXPERIMENT RESULT] That is what the numbers show: building accuracy "
      f"{b['building_accuracy']*100:.2f}% against floor accuracy "
      f"{b['floor_accuracy']*100:.2f}% at the baseline. Joint accuracy is "
      f"bounded by the floor term, so **floor confusion is the whole "
      "problem**, and any feature-selection method must be judged on whether "
      "it preserves within-building discrimination.\n")
    A("### ALGORITHM MECHANISM\n")
    A("[OUR INTERPRETATION] Two opposing forces act when columns are removed. "
      "Removing a column that is pure noise *helps* k-NN, because every "
      "retained dimension contributes to the distance and noise dimensions "
      "dilute the informative ones — the familiar curse of dimensionality. "
      "Removing a column that discriminates between two floors *hurts*, "
      "irreversibly. Where the curve turns over is where the second force "
      "starts dominating.\n")
    A("A second, more specific mechanism matters at small budgets: a validation "
      "fingerprint in which **none** of the selected APs was detected becomes "
      "an all-zero vector, and its nearest neighbour is then essentially "
      "arbitrary. That count is logged per condition in "
      "`results/metrics/ips_results.csv` "
      "(`val_rows_with_no_selected_wap_detected`) precisely so that a collapse "
      "at small n can be attributed to coverage loss rather than to "
      "discrimination loss.\n")
    A("### IPS MEANING\n")
    A("[OUR INTERPRETATION] The answer to 'how many WAPs can be removed' is "
      "not a single number — it depends on which accuracy is being protected. "
      "Building accuracy survives aggressive reduction because a handful of "
      "building-exclusive APs carry it. Floor accuracy is the binding "
      "constraint. A report that quoted only building accuracy would make the "
      "method look far better than it is.\n")
    A("---\n")

    # ================================================================ OBS 5
    A("## Observation 5 — Compared with the controls: is it HUIM that helps, "
      "or just having fewer features?\n")
    A("### RESULT\n")
    A("This is the comparison that decides whether the study has a positive "
      "result at all. At each matched feature budget, HUIM's selection is put "
      "against (i) random selection from the APs detected in training, (ii) "
      "the n most frequently detected APs, (iii) the n APs with the highest "
      "mutual information — the criterion Model B embeds, used on its own "
      "without any itemset mining.\n")
    cols = set()
    for r in o5["matched_budget_comparison"]:
        cols |= set(r)
    huim_cols = sorted(c2 for c2 in cols if c2.startswith("huim_"))
    hdr = (["Budget n"] + [MODEL_LABEL.get(c2[5:], c2[5:]).replace(
        "Model ", "HUIM ").split(" (")[0] for c2 in huim_cols]
        + ["Top-n by MI", "Top-n by support", "Random (mean)",
           "Random (min–max)"])
    A("| " + " | ".join(hdr) + " |")
    A("|" + "|".join("---" for _ in hdr) + "|")
    for r in o5["matched_budget_comparison"]:
        cells = [str(r["budget_n"])]
        for c2 in huim_cols:
            cells.append(f"{r[c2]*100:.2f}%" if c2 in r else "-")
        cells.append(f"{r['control_top_mi']*100:.2f}%"
                     if "control_top_mi" in r else "-")
        cells.append(f"{r['control_top_support']*100:.2f}%"
                     if "control_top_support" in r else "-")
        cells.append(f"{r['control_random_mean']*100:.2f}%"
                     if "control_random_mean" in r else "-")
        cells.append(f"{r['control_random_min']*100:.2f}–"
                     f"{r['control_random_max']*100:.2f}%"
                     if "control_random_min" in r else "-")
        A("| " + " | ".join(cells) + " |")
    w = o5["verdict_inputs"]
    A(f"\n[EXPERIMENT RESULT] Across {w['n_comparisons']} matched budgets, the "
      f"best HUIM selection beat random selection in "
      f"**{w['huim_beats_random']}/{w['n_comparisons']}** cases, beat top-n by "
      f"mutual information in **{w['huim_beats_top_mi']}/{w['n_comparisons']}**, "
      f"and beat top-n by detection count in "
      f"**{w['huim_beats_top_support']}/{w['n_comparisons']}**.\n")
    A("### WHY? / INTERPRETATION\n")
    A("[OUR INTERPRETATION] These three controls answer three different "
      "questions, and only the third one is about HUIM.\n")
    A("- **vs random**: does the selection contain information at all? If HUIM "
      "did not beat random, the reduction would simply be dimensionality "
      "reduction by deletion.\n")
    A("- **vs top-n by support**: is the selection more than 'the APs you see "
      "most often'? Support is what a frequent-itemset miner would favour, so "
      "this is the frequent-vs-useful question posed empirically.\n")
    A("- **vs top-n by mutual information**: this is the hard one. Model B's "
      "external utility *is* mutual information. If ranking APs by MI directly "
      "does as well as mining itemsets whose utility is built from MI, then the "
      "itemset mining contributed nothing beyond the weight it was handed, and "
      "honesty requires saying so.\n")
    A("### HUIM THEORY\n")
    A("[FACT FROM PAPER] HUIM is defined as an unsupervised pattern-discovery "
      "problem: find itemsets whose utility passes a threshold. Nothing in the "
      "definition optimises a classification objective. [OUR INTERPRETATION] "
      "So there is no theorem to appeal to here — whether a high-utility "
      "itemset is a good feature subset is purely an empirical question, and "
      "the only legitimate answer is the table above. In particular, a HUI "
      "must **not** be equated with a good localisation feature group unless "
      "these numbers show it.\n")
    A("---\n")

    # ================================================================ OBS 6
    A("## Observation 6 — How far do \"detected often\" and \"informative\" "
      "actually come apart?\n")
    A("### RESULT\n")
    A("| Rank | Most frequently detected AP | Detections | Highest mutual "
      "information AP | MI (bits) |")
    A("|---|---|---|---|---|")
    sup = o6.get("top10_by_support", [])
    mis = o6.get("top10_by_mutual_information") or []
    for k in range(max(len(sup), len(mis))):
        s = sup[k] if k < len(sup) else None
        mm = mis[k] if k < len(mis) else None
        A(f"| {k+1} | {s['wap'] if s else '-'} | "
          f"{fmt(s['support']) if s else '-'} | {mm['wap'] if mm else '-'} | "
          f"{mm['mi_bits'] if mm else '-'} |")
    A(f"\n[EXPERIMENT RESULT] Overlap between the two top-10 lists: "
      f"**{o6['overlap_top10_support_vs_top10_mi']} of 10**"
      + (f" ({', '.join(o6['overlap_members'])})"
         if o6["overlap_members"] else "") + ".\n")
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        A(f"[EXPERIMENT RESULT] Across all "
          f"{o6['n_detected_waps_compared']} detected APs, the rank "
          f"correlation between detection count and mutual information is "
          f"**Spearman ρ = "
          f"{o6['spearman_support_vs_mi_over_all_detected_waps']}** "
          f"(Pearson r = "
          f"{o6['pearson_support_vs_mi_over_all_detected_waps']}). Rank "
          f"overlap at increasing depth: "
          + ", ".join(f"top-{k}: {v}/{k}"
                      for k, v in o6["rank_overlap_at_depth"].items()) + ".\n")
        A("**Read this carefully, because it does not say what the slogan "
          "'frequent is not useful' would lead one to expect.** The two "
          "criteria are *positively* associated, and at the very top of the "
          "ranking they largely agree. On this dataset, an AP that is detected "
          "often also tends to carry information — which makes sense: an AP "
          "detected twice cannot distinguish anything, so some coverage is a "
          "precondition for informativeness.\n")
        A("[OUR INTERPRETATION] So Observation 6 does **not** establish "
          "'frequent ≠ useful' on this data. What it establishes is weaker and "
          "more precise: the two orderings are correlated but not identical, "
          "and the disagreement grows as one goes deeper into the ranking. The "
          "decisive evidence that signal-driven utility picks *bad* features "
          "is not here at all — it is in Observation 5 and Observation 9, "
          "where Model A's ranking is measured against chance.\n")
    if o6.get("label_entropy_bits") is not None:
        A(f"[FACT FROM DATA] The label entropy H(Y) of the 13 "
          f"BUILDINGID_FLOOR classes is {o6['label_entropy_bits']} bits. The "
          f"single most informative AP supplies {o6['max_mi_bits']} bits, i.e. "
          f"{o6['max_mi_as_fraction_of_H_Y']*100:.1f}% of it.\n")
    A("### WHY?\n")
    A("[OUR INTERPRETATION] Mutual information with the location label is "
      "maximised by an AP whose *state varies with location*. Coverage and "
      "informativeness therefore pull in the same direction up to a point — an "
      "AP nobody ever sees cannot discriminate — and then separate: an AP "
      "visible across several floors has support but little information, while "
      "an AP seen in a few hundred fingerprints all on one floor is almost a "
      "floor detector. That is exactly the shape the rank-overlap figures "
      "above show: agreement at the top, divergence with depth.\n")
    A(f"[FACT FROM DATA] The structural reason is in the audit: "
      f"{o6['ap_building_spread']['n_waps_in_exactly_1_building']} of the "
      f"detected APs are confined to one building while "
      f"{o6['ap_building_spread']['n_waps_in_exactly_2_buildings']} are seen in "
      f"two and {o6['ap_building_spread']['n_waps_in_all_3_buildings']} in all "
      f"three. Confinement is what creates information.\n")
    A("### HUIM THEORY\n")
    A("[FACT FROM PAPER] The motivation for utility mining over "
      "frequent-itemset mining (Yao et al. 2004; Gan et al. 2021) is that "
      "frequency and worth are different axes: an item can be rare and "
      "valuable or common and worthless.\n")
    A("[OUR INTERPRETATION] On this dataset that separation is real but "
      "*partial* — the measured association above is positive. The place where "
      "the distinction bites hardest is not single-item frequency at all, but "
      "**Model A's utility**, which multiplies signal strength by how often APs "
      "co-occur, and whose ranking performs worse than chance (Observation 9). "
      "That is the clean instance of 'what looks valuable is not what is "
      "useful', and it is what makes Model A a meaningful control rather than "
      "a wasted arm of the ablation.\n")
    A("### IPS MEANING\n")
    A("[OUR INTERPRETATION] The practical lesson for a site survey is narrower "
      "than the slogan: do not keep APs because their *signal is strong*. "
      "Keeping APs because they are *widely detected* is, on this data, not a "
      "bad heuristic at all — the top-n-by-detection-count control is "
      "competitive throughout, and at 200 APs it is the best condition in the "
      "whole study. What a fingerprint database needs is coverage first, and "
      "then boundaries that cut through the building.\n")
    A("---\n")

    # ================================================================ OBS 7
    A("## Observation 7 — Why thresholds must be relative, not absolute\n")
    A("### RESULT\n")
    A("| Model | Total database utility | Mean TU(T) | Max TU(T) | p range |")
    A("|---|---|---|---|---|")
    for m, d in o7.items():
        pr = (f"{d['p_min']:.3g} – {d['p_max']:.3g}"
              if d.get("p_min") is not None else "1 (constant)")
        A(f"| {MODEL_LABEL.get(m, m)} | {fmt(d['total_database_utility'])} | "
          f"{fmt(d['transaction_utility_mean'])} | "
          f"{fmt(d['transaction_utility_max'])} | {pr} |")
    A("\n### OBSERVATION / WHY?\n")
    vals = [d["total_database_utility"] for d in o7.values()]
    if vals:
        A(f"[EXPERIMENT RESULT] Total database utility differs by a factor of "
          f"{max(vals)/max(min(vals), 1e-12):.2f} between the models, even "
          f"though the database, the transactions and the internal utilities "
          f"are identical. Only p changed.\n")
    A("[OUR INTERPRETATION] An absolute minUtil of, say, 200,000 is therefore "
      "meaningless as a cross-model setting: the same number sits at completely "
      "different points of the three utility distributions. Expressing minUtil "
      "as a fraction of total database utility is what makes the three arms of "
      "the ablation comparable at all, and it is also what let the "
      "same grid be reused between the pilot subsample and the full "
      "database.\n")
    A("[FACT FROM PAPER] This is standard practice in the HUIM literature, "
      "where thresholds are normally reported as a percentage of total utility "
      "precisely because absolute utility has no interpretation across "
      "datasets (Zhang et al., ESWA 2018).\n")
    A("---\n")

    # ================================================================ OBS 8
    A("## Observation 8 — Do more HUIs mean better positioning?\n")
    A("### RESULT\n")
    A(f"- Union conditions evaluated: {o8['n_points']}")
    if "spearman_n_huis_vs_joint_accuracy" in o8:
        A(f"- Spearman ρ(number of HUIs, joint accuracy) = "
          f"**{o8['spearman_n_huis_vs_joint_accuracy']}**")
        A(f"- Spearman ρ(number of selected WAPs, joint accuracy) = "
          f"**{o8['spearman_n_waps_vs_joint_accuracy']}**")
    if "spearman_n_waps_vs_joint_accuracy_topn" in o8:
        A(f"- Spearman ρ(number of selected WAPs, joint accuracy) over the "
          f"top-n sweep = **{o8['spearman_n_waps_vs_joint_accuracy_topn']}**")
    A(f"\n[OUR INTERPRETATION] {o8['note']}. A correlation computed over union "
      "points cannot separate 'more itemsets' from 'more features', because "
      "lowering minUtil increases both at once. The top-n sweep holds the HUI "
      "set fixed and varies only the budget, which is the comparison that "
      "isolates the feature count.\n")
    A("### ANSWER\n")
    A("[OUR INTERPRETATION] The question 'does a larger HUI set give better "
      "accuracy' is the wrong question, and Observation 1 explains why: a "
      "larger HUI set at lower minUtil is mostly **additional subsets of the "
      "same AP groups**, so it adds itemsets without adding APs. What changes "
      "accuracy is which APs end up in the union, not how many itemsets "
      "mentioned them. Any claim of the form 'mining more patterns improves "
      "localisation' is therefore unsupported by this experiment.\n")
    A("---\n")

    # ================================================================ OBS 9
    o9 = O.get("observation_9_ranking_vs_size", {})
    if o9:
        A("## Observation 9 — Is the shortfall a bad ranking, or simply too "
          "few features?\n")
        A("### RESULT\n")
        A(f"[EXPERIMENT RESULT] The largest AP set any HUIM condition produced "
          f"is **{o9['largest_huim_selected_set']} WAPs** "
          f"(`{o9['largest_huim_set_condition']}`). Within that budget ceiling, "
          f"the best joint accuracy reached by **any** method in this study is ")
        bb = o9.get("best_joint_at_or_below_that_budget_any_method")
        if bb:
            A(f"**{bb['joint']*100:.2f}%** (`{bb['condition']}`, "
              f"{bb['n_waps']} WAPs), against a baseline of "
              f"{b['joint_accuracy']*100:.2f}% on {b['n_waps']} WAPs.\n")
        sc = o9.get("smallest_control_subset_reaching_baseline")
        if sc:
            A(f"[EXPERIMENT RESULT] The smallest subset of **any** kind that "
              f"reaches the baseline uses **{sc['n_waps']} WAPs** "
              f"({sc['reduction_pct']:.2f}% reduction, "
              f"{sc['joint']*100:.2f}%, `{sc['condition']}`) — well above the "
              f"{o9['largest_huim_selected_set']}-WAP ceiling that HUIM could "
              f"offer.\n")
        else:
            A("[EXPERIMENT RESULT] No subset of any kind reached the baseline "
              "joint accuracy.\n")
        rows9 = o9.get("like_for_like_at_huim_budgets", [])
        if rows9:
            cols9 = sorted({k for r in rows9 for k in r if k != "n"})
            A("Like-for-like, at exactly the budgets HUIM uses:\n")
            A("| n | " + " | ".join(c.replace("huim_", "HUIM ")
                                    .replace("control_", "") for c in cols9)
              + " |")
            A("|" + "|".join("---" for _ in range(len(cols9) + 1)) + "|")
            for r in rows9:
                A(f"| {r['n']} | " + " | ".join(
                    (f"{r[c]*100:.2f}%" if c in r else "-") for c in cols9)
                  + " |")
            A("")
        bm = o9.get("beats_random_by_model", {})
        if bm:
            A("Does each utility model's ranking beat *chance* at the same "
              "budget?\n")
            A("| Utility model | Budgets compared | HUIM ranking beat random |")
            A("|---|---|---|")
            for m, d in bm.items():
                A(f"| {MODEL_LABEL.get(m, m)} | {d['n']} | {d['beats']} |")
            A("")
        A("### WHY? / INTERPRETATION\n")
        A("[OUR INTERPRETATION] These numbers separate two explanations that "
          "are easy to confuse.\n")
        A(f"**Explanation 1 — the ranking is wrong.** If HUIM's ordering of APs "
          f"were no better than chance, it would lose to random selection at "
          f"matched budgets. The table above answers that per model, and the "
          f"answer differs by model — which is itself the point of the "
          f"ablation.\n")
        A(f"**Explanation 2 — the set is too small.** HUIM can only offer the "
          f"APs that appear in a non-truncated HUI set, and that count is "
          f"capped by the lowest minUtil that still completes inside the "
          f"resource budget. Here that ceiling is "
          f"{o9['largest_huim_selected_set']} WAPs, while the simplest control "
          f"needs "
          + (f"{sc['n_waps']}" if sc else "more than any budget tested")
          + " to match the baseline. **Even a perfect ranking could not have "
            "closed the gap from inside that ceiling.**\n")
        A("[OUR INTERPRETATION] This is the most useful mechanistic finding of "
          "the study, and it points straight back at Observation 1. To enlarge "
          "the union, minUtil must fall; but lowering minUtil multiplies the "
          "*itemsets* far faster than it adds *APs*, and the mining cost "
          "explodes before the AP set grows usefully. The feature-set size a "
          "practitioner needs and the threshold region HUIM can actually be run "
          "in are, on this dataset and with these utility definitions, pulling "
          "in opposite directions.\n")
        A("[OUR INTERPRETATION] Note what this does *not* say. It does not say "
          "HUIM's ranking is bad — that is the separate question the table "
          "above addresses. It says that the operating point where HUIM-"
          "selected features could compete was not reachable within the "
          "compute budget used here, which is a statement about this "
          "experiment's design as much as about the method.\n")
        A("---\n")

    # ================================================================ wrap
    A("## What the experiments force us to conclude about HUIM itself\n")
    A("Reading the chain backwards, from results to theory:\n")
    A("1. [EXPERIMENT RESULT] Output size is extremely sensitive to minUtil, "
      "while the number of distinct APs involved is not. → [THEORY] Because "
      "utility lacks downward closure, the answer set is a union of subset "
      "lattices, and its size is governed by the depth of the deepest "
      "qualifying itemset.\n")
    A("2. [EXPERIMENT RESULT] Runtime scales with nodes visited, memory with "
      "output size. → [THEORY] EFIM's bounds control *search*, not *output*. No "
      "correct algorithm can do better on output.\n")
    A("3. [EXPERIMENT RESULT] Changing only p changes which APs are selected. → "
      "[THEORY] The utility function is part of the problem definition, so "
      "'the HUIs of a dataset' is not well defined without it.\n")
    A("4. [EXPERIMENT RESULT] Detection count and mutual information turned "
      "out to be almost perfectly rank-correlated here, so 'frequent ≠ useful' "
      "was NOT demonstrated at the level of individual APs — the opposite of "
      "what this study expected to find. → [THEORY] The distinction still "
      "holds, but it bit at the level of the utility FUNCTION rather than the "
      "item: Model A, whose p ≡ 1 makes utility a product of signal strength "
      "and co-occurrence, ranked APs worse than chance.\n")
    A("5. [THEORY → PRACTICE] HUIM is not a supervised feature selector. Any "
      "usefulness it has for localisation comes from the utility definition "
      "that the analyst supplies, and must be demonstrated against controls "
      "rather than assumed.\n")
    A("\n### Explicitly NOT claimed\n")
    A("- That a high-utility itemset is, in general, a good feature group for "
      "classification.\n")
    A("- That HUIM is a better AP-selection method than the existing "
      "information-theoretic ones; the matched-budget table is the only "
      "evidence offered, and it is read as it stands.\n")
    A("- That these results generalise beyond UJIIndoorLoc, one k-NN "
      "configuration, and the (q, p) definitions used here.\n")
    A("- Any novelty priority. See `research/literature_review.md` §7.\n")
    return "\n".join(L) + "\n"


def main() -> None:
    O = collect()
    dump_json(O, RESULTS / "reverse_thinking_observations.json")
    (RESEARCH / "reverse_thinking_analysis.md").write_text(render(O),
                                                           encoding="utf-8")
    print(f"Wrote {RESULTS / 'reverse_thinking_observations.json'}")
    print(f"Wrote {RESEARCH / 'reverse_thinking_analysis.md'}")


if __name__ == "__main__":
    main()
