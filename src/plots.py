"""PHASE J - figures.

Every figure is built from results/metrics/*.csv, and every figure writes the
exact rows it plotted to figures/<name>.csv next to the PNG. That makes each
chart auditable: a reader can check the picture against the numbers without
re-running anything, and no figure can contain a value that is not in the logs.

Axis conventions: units are always in the axis label; log scales are stated in
the label; the y-axis is never truncated to exaggerate a difference unless the
label says so (it never does here).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess_uji import NOT_DETECTED, fit_preprocessor, joint_label, load_splits
from utils import FIGURES, METRICS, RESULTS, get_logger, load_json
from utility_models import conditional_entropy_reduction, discretise

LOG = get_logger("plots", "plots.log")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

MODEL_STYLE = {
    "A_signal": ("#1f3b73", "o", "Model A - Signal utility"),
    "B_discriminative": ("#8c2d04", "s", "Model B - Discriminative utility"),
    "C_rare_discriminative": ("#145a32", "^", "Model C - Rare-discriminative"),
}
FAMILY_STYLE = {
    "huim_topn": ("#8c2d04", "o", "HUIM (top-n by utility contribution)"),
    "control_top_mi": ("#4a148c", "s", "Control: top-n by mutual information"),
    "control_top_support": ("#b8860b", "^", "Control: top-n by detection count"),
    "control_random": ("#777777", "x", "Control: random n (3 seeds)"),
}


def _save(fig, name: str, data: pd.DataFrame) -> None:
    p = FIGURES / f"{name}.png"
    fig.savefig(p)
    plt.close(fig)
    data.to_csv(FIGURES / f"{name}.csv", index=False)
    LOG.info("wrote %s (+ .csv, %d rows)", p.name, len(data))


# ------------------------------------------------------------ minUtil labels
# Every HUIM condition on a chart was produced by one mining run at one minUtil
# threshold. The threshold is printed next to the condition, and the absolute
# value is written into the figure's CSV, so a reader can check the chain
#   minUtil% x total database utility = absolute minUtil  (huim_runs.csv)
# and from there that every HUI behind the selected WAPs has u(X) >= minUtil.
MODEL_LETTER = {"A_signal": "A", "B_discriminative": "B",
                "C_rare_discriminative": "C"}


def huim_thresholds() -> pd.DataFrame:
    """One row per mining run, keyed by (utility_model, rel_minutil_pct)."""
    H = pd.read_csv(METRICS / "huim_runs.csv")
    H = H[["run_tag", "utility_model", "rel_minutil_pct", "abs_minutil",
           "total_db_utility", "n_huis", "status"]].copy()
    H["pct_key"] = H["rel_minutil_pct"].astype(float).round(6)
    return H.rename(columns={"status": "huim_run_status",
                             "n_huis": "huim_run_n_huis",
                             "run_tag": "huim_run_tag"})


def with_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the mining run's absolute minUtil and total utility to IPS rows.
    Non-HUIM rows get empty threshold columns."""
    H = huim_thresholds().drop(columns=["rel_minutil_pct"])
    # idempotent: drop columns a previous call already attached
    out = df.drop(columns=[c for c in H.columns if c in df.columns
                           and c != "utility_model"])
    out["pct_key"] = pd.to_numeric(out["rel_minutil_pct"],
                                   errors="coerce").round(6)
    out = out.merge(H, on=["utility_model", "pct_key"], how="left")
    return out.drop(columns=["pct_key"])


def mu_text(pct) -> str:
    """'minUtil 1.9294%' for a HUIM row, '' for anything else."""
    v = pd.to_numeric(pd.Series([pct]), errors="coerce").iloc[0]
    return "" if pd.isna(v) else f"minUtil {float(v):g}%"


def threshold_footnote(rows: pd.DataFrame, wrap: bool = False) -> str:
    """'A: 1.9294% x 9,058,242 = 174,770 | ...' for the HUIM runs on a chart.
    `wrap` puts the values on their own line, for the narrower figures."""
    t = with_thresholds(rows)
    t = t[t["abs_minutil"].notna()]
    seen, parts = set(), []
    for _, r in t.sort_values(["utility_model", "rel_minutil_pct"]).iterrows():
        key = (r["utility_model"], round(float(r["rel_minutil_pct"]), 6))
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"{MODEL_LETTER.get(r['utility_model'], '?')}: "
                     f"{float(r['rel_minutil_pct']):g}% x "
                     f"{r['total_db_utility']:,.0f} = {r['abs_minutil']:,.0f}")
    if not parts:
        return ""
    return ("Absolute minUtil = minUtil% x total database utility "
            "(results/metrics/huim_runs.csv):" + ("\n" if wrap else "  ")
            + "   |   ".join(parts))


# --------------------------------------------------------------- mining figures
def mining_figures(huim: pd.DataFrame) -> None:
    done = huim.copy()
    done["completed"] = done["status"] == "COMPLETED"

    specs = [
        ("fig01_minutil_vs_hui_count", "n_huis",
         "Number of High Utility Itemsets", True,
         "Minimum utility threshold vs number of HUIs"),
        ("fig02_minutil_vs_runtime", "runtime_s", "Runtime (seconds)", True,
         "Minimum utility threshold vs mining runtime"),
        ("fig03_minutil_vs_peak_memory", "peak_memory_delta_mb",
         "Peak memory above baseline (MB)", False,
         "Minimum utility threshold vs peak memory"),
        ("fig04_minutil_vs_selected_waps", "selected_feature_count_union",
         "Number of selected WAPs (union over HUIs)", False,
         "Minimum utility threshold vs size of the selected WAP set"),
        ("fig07_minutil_vs_search_nodes", "search_nodes_visited",
         "Search-tree nodes visited", True,
         "Minimum utility threshold vs search-space explored"),
        ("fig08_minutil_vs_items_surviving_twu", "items_after_twu_pruning",
         "Items surviving the root TWU bound", False,
         "Minimum utility threshold vs items surviving TWU pruning"),
    ]
    for name, col, ylab, logy, title in specs:
        fig, ax = plt.subplots(figsize=(5.6, 3.5))
        for model, g in done.groupby("utility_model"):
            c, mk, lab = MODEL_STYLE.get(model, ("k", "o", model))
            g = g.sort_values("rel_minutil_pct")
            ax.plot(g["rel_minutil_pct"], np.maximum(g[col], 1e-9 if logy else 0),
                    marker=mk, color=c, label=lab, lw=1.3, ms=4.5)
            ab = g[~g["completed"]]
            if len(ab):
                ax.scatter(ab["rel_minutil_pct"],
                           np.maximum(ab[col], 1e-9 if logy else 0),
                           s=120, facecolors="none", edgecolors="red",
                           linewidths=1.4, zorder=5)
        ax.set_xscale("log")
        ax.set_xlabel("Minimum utility threshold, relative to total database "
                      "utility (%, log scale)")
        if logy:
            ax.set_yscale("symlog", linthresh=1)
            ax.set_ylabel(ylab + " (symlog scale)")
        else:
            ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.invert_xaxis()
        h, l = ax.get_legend_handles_labels()
        ax.scatter([], [], s=90, facecolors="none", edgecolors="red",
                   label="aborted at resource limit")
        ax.legend(loc="best")
        _save(fig, name, done[["utility_model", "rel_minutil_pct", "abs_minutil",
                               "status", col]])

    # HUI length distribution for the richest completed run per model
    import json as _json
    rows = []
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    for model, g in done[done["completed"] & (done["n_huis"] > 0)].groupby(
            "utility_model"):
        r = g.sort_values("n_huis").iloc[-1]
        dist = _json.loads(r["hui_length_distribution_json"])
        ks = sorted(int(k) for k in dist)
        vs = [dist[str(k)] for k in ks]
        c, mk, lab = MODEL_STYLE.get(model, ("k", "o", model))
        ax.plot(ks, vs, marker=mk, color=c, lw=1.3, ms=4,
                label=f"{lab}\n({r['rel_minutil_pct']:g}%, "
                      f"{int(r['n_huis'])} HUIs)")
        for k, v in zip(ks, vs):
            rows.append({"utility_model": model,
                         "rel_minutil_pct": r["rel_minutil_pct"],
                         "hui_length": k, "count": v})
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel("High utility itemset length (number of WAPs)")
    ax.set_ylabel("Number of HUIs (symlog scale)")
    ax.set_title("Length distribution of the mined HUIs")
    ax.legend(loc="best")
    _save(fig, "fig05_hui_length_distribution", pd.DataFrame(rows))


# ------------------------------------------------------------------ IPS figures
def ips_figures(ips: pd.DataFrame) -> None:
    base = ips[ips["condition"] == "baseline_all_520"].iloc[0]
    base465 = ips[ips["condition"] == "baseline_detected_465"]
    base465 = base465.iloc[0] if len(base465) else None

    # --- fig06: selected WAP count vs joint accuracy, HUIM vs controls -------
    sweep = ips[ips["family"].isin(FAMILY_STYLE)].copy()
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for fam, g in sweep.groupby("family"):
        c, mk, lab = FAMILY_STYLE[fam]
        if fam == "control_random":
            agg = g.groupby("budget_n")["joint_building_floor_accuracy"].agg(
                ["mean", "min", "max"]).reset_index()
            # clip: mean-min and max-mean can be ~-1e-16 from float rounding
            lo = np.clip((agg["mean"] - agg["min"]).to_numpy() * 100, 0, None)
            hi = np.clip((agg["max"] - agg["mean"]).to_numpy() * 100, 0, None)
            ax.errorbar(agg["budget_n"], agg["mean"] * 100, yerr=[lo, hi],
                        marker=mk, color=c, lw=1.1, ms=4, capsize=2, label=lab)
        else:
            for model, gg in (g.groupby("utility_model") if fam == "huim_topn"
                              else [("", g)]):
                gg = gg.sort_values("budget_n")
                mc, mmk, mlab = MODEL_STYLE.get(model, (c, mk, lab))
                ax.plot(gg["budget_n"], gg["joint_building_floor_accuracy"] * 100,
                        marker=mmk if fam == "huim_topn" else mk,
                        color=mc if fam == "huim_topn" else c, lw=1.3, ms=4.5,
                        label=(f"HUIM top-n, model {MODEL_LETTER[model]} "
                               f"({mu_text(gg['rel_minutil_pct'].iloc[0])})"
                               if fam == "huim_topn" else lab))
    ax.axhline(base["joint_building_floor_accuracy"] * 100, color="k", ls="--",
               lw=1.1, label=f"Baseline, all {int(base['n_waps_selected'])} WAPs "
                             f"({base['joint_building_floor_accuracy']*100:.2f}%)")
    ax.set_xscale("log")
    ax.set_xlabel("Number of selected WAPs (log scale)")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    ax.set_title("Feature budget vs joint localisation accuracy")
    ax.legend(loc="upper left", ncol=1, fontsize=7.6)
    fig.text(0.01, -0.035, threshold_footnote(sweep, wrap=True),
             fontsize=6.4, color="#444444", ha="left", va="top")
    _save(fig, "fig06_selected_waps_vs_accuracy",
          with_thresholds(sweep)[
              ["condition", "family", "utility_model", "rel_minutil_pct",
               "abs_minutil", "total_db_utility", "budget_n",
               "n_waps_selected", "feature_reduction_pct",
               "building_accuracy", "floor_accuracy",
               "joint_building_floor_accuracy"]])

    # --- fig09: feature reduction vs accuracy -------------------------------
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for fam, g in sweep.groupby("family"):
        c, mk, lab = FAMILY_STYLE[fam]
        if fam == "control_random":
            agg = g.groupby("feature_reduction_pct")[
                "joint_building_floor_accuracy"].mean().reset_index()
            ax.plot(agg["feature_reduction_pct"],
                    agg["joint_building_floor_accuracy"] * 100,
                    marker=mk, color=c, lw=1.1, ms=4, label=lab)
        elif fam == "huim_topn":
            for model, gg in g.groupby("utility_model"):
                mc, mmk, mlab = MODEL_STYLE.get(model, (c, mk, model))
                gg = gg.sort_values("feature_reduction_pct")
                ax.plot(gg["feature_reduction_pct"],
                        gg["joint_building_floor_accuracy"] * 100,
                        marker=mmk, color=mc, lw=1.3, ms=4.5,
                        label=f"HUIM top-n, model {MODEL_LETTER[model]} "
                              f"({mu_text(gg['rel_minutil_pct'].iloc[0])})")
        else:
            g = g.sort_values("feature_reduction_pct")
            ax.plot(g["feature_reduction_pct"],
                    g["joint_building_floor_accuracy"] * 100,
                    marker=mk, color=c, lw=1.2, ms=4, label=lab)
    union = ips[ips["family"] == "huim_union"]
    if len(union):
        # one diamond per (model, minUtil) run; hollow = the run was aborted at
        # the resource limit (truncated HUIs). The points are too dense to
        # label one by one, so only the run each model is compared on (lowest
        # COMPLETED minUtil) is labelled here; fig19 plots every union point
        # against its minUtil.
        text_y = {"C_rare_discriminative": 80.5, "B_discriminative": 76.5,
                  "A_signal": 72.5}
        for model, gg in union.groupby("utility_model"):
            mc = MODEL_STYLE.get(model, ("#4a148c", "D", model))[0]
            done = gg["huim_status"] == "COMPLETED"
            ax.scatter(gg.loc[done, "feature_reduction_pct"],
                       gg.loc[done, "joint_building_floor_accuracy"] * 100,
                       marker="D", s=26, color=mc, lw=1.0, zorder=4,
                       label=f"HUIM union, model {MODEL_LETTER[model]} "
                             "(one point per minUtil, see fig19)")
            ax.scatter(gg.loc[~done, "feature_reduction_pct"],
                       gg.loc[~done, "joint_building_floor_accuracy"] * 100,
                       marker="D", s=26, facecolors="none", edgecolors=mc,
                       lw=1.0, zorder=4)
            prim = gg[done]
            if len(prim):
                r = prim.loc[prim["rel_minutil_pct"].astype(float).idxmin()]
                ax.annotate(f"union {MODEL_LETTER[model]}: "
                            f"{mu_text(r['rel_minutil_pct'])}, "
                            f"{int(r['n_waps_selected'])} WAP, "
                            f"{r['joint_building_floor_accuracy']*100:.1f}%",
                            xy=(r["feature_reduction_pct"],
                                r["joint_building_floor_accuracy"] * 100),
                            xytext=(20, text_y.get(model, 70)),
                            textcoords="data", fontsize=6.6, color=mc,
                            va="center",
                            arrowprops=dict(arrowstyle="-", color=mc, lw=0.6))
        ax.scatter([], [], marker="D", s=26, facecolors="none",
                   edgecolors="#555555",
                   label="hollow = run aborted at the resource limit")
    ax.axhline(base["joint_building_floor_accuracy"] * 100, color="k", ls="--",
               lw=1.1, label="Baseline, all 520 WAPs")
    ax.set_xlabel(f"Feature reduction (%)   =  (1 - selected / "
                  f"{int(base['n_waps_selected'])}) x 100")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    ax.set_title("Feature reduction vs joint localisation accuracy")
    ax.legend(loc="lower left", fontsize=6.8)
    _save(fig, "fig09_feature_reduction_vs_accuracy",
          with_thresholds(pd.concat([sweep, union]))[
              ["condition", "family", "utility_model", "rel_minutil_pct",
               "abs_minutil", "total_db_utility", "huim_status",
               "n_waps_selected", "feature_reduction_pct",
               "joint_building_floor_accuracy"]])

    # --- fig10: the three accuracies side by side for key conditions ---------
    keys = ["baseline_all_520", "baseline_detected_465"]
    for model in ("A_signal", "B_discriminative", "C_rare_discriminative"):
        g = ips[(ips["family"] == "huim_topn") & (ips["utility_model"] == model)]
        if len(g):
            best = g.loc[g["joint_building_floor_accuracy"].idxmax()]
            keys.append(best["condition"])
    sel = ips[ips["condition"].isin(keys)].copy()
    sel = sel.set_index("condition").loc[[k for k in keys if k in
                                          set(ips["condition"])]].reset_index()
    def _short(cond: str, n: int, pct) -> str:
        if cond.startswith("baseline_all"):
            lab = "Baseline\nall WAP"
        elif cond.startswith("baseline_detected"):
            lab = "Baseline\ndetected only"
        elif cond.startswith("control_top_mi"):
            lab = "Control\ntop-n MI"
        elif cond.startswith("control_top_support"):
            lab = "Control\ntop-n support"
        else:
            m = ("A" if "A_signal" in cond else
                 "B" if "B_discr" in cond else
                 "C" if "C_rare" in cond else "?")
            kind = "top-n" if cond.startswith("huim_topn") else "union"
            lab = f"HUIM {m}\n{kind}"
        mu = mu_text(pct)
        return f"{lab}\n{n} WAP" + (f"\n{mu}" if mu else "")

    labels = [_short(c, int(n), p) for c, n, p in
              zip(sel["condition"], sel["n_waps_selected"],
                  sel["rel_minutil_pct"])]
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    x = np.arange(len(sel))
    w = 0.26
    for off, col, lab, c in ((-w, "building_accuracy", "Building", "#1f3b73"),
                             (0.0, "floor_accuracy", "Floor", "#8c2d04"),
                             (w, "joint_building_floor_accuracy", "Joint",
                              "#145a32")):
        ax.bar(x + off, sel[col] * 100, width=w, label=lab, color=c)
        for xi, v in zip(x + off, sel[col] * 100):
            ax.text(xi, v + 0.6, f"{v:.1f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.6)
    ax.set_ylim(0, 118)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Baseline vs best HUIM selection per utility model")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
    fig.text(0.01, -0.075, threshold_footnote(sel), fontsize=6.4,
             color="#444444", ha="left", va="top")
    _save(fig, "fig10_baseline_vs_huim_accuracies",
          with_thresholds(sel)[
              ["condition", "utility_model", "rel_minutil_pct", "abs_minutil",
               "total_db_utility", "n_waps_selected", "feature_reduction_pct",
               "building_accuracy", "floor_accuracy",
               "joint_building_floor_accuracy", "joint_macro_f1"]])

    # --- fig11: positioning error (projected metres) ------------------------
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for fam, g in sweep.groupby("family"):
        c, mk, lab = FAMILY_STYLE[fam]
        if fam == "huim_topn":
            for model, gg in g.groupby("utility_model"):
                mc, mmk, mlab = MODEL_STYLE.get(model, (c, mk, model))
                gg = gg.sort_values("budget_n")
                ax.plot(gg["budget_n"], gg["pos_median_error"], marker=mmk,
                        color=mc, lw=1.3, ms=4.5,
                        label=f"HUIM top-n, model {MODEL_LETTER[model]} "
                              f"({mu_text(gg['rel_minutil_pct'].iloc[0])})")
        elif fam == "control_random":
            agg = g.groupby("budget_n")["pos_median_error"].mean().reset_index()
            ax.plot(agg["budget_n"], agg["pos_median_error"], marker=mk,
                    color=c, lw=1.1, ms=4, label=lab)
        else:
            g = g.sort_values("budget_n")
            ax.plot(g["budget_n"], g["pos_median_error"], marker=mk, color=c,
                    lw=1.2, ms=4, label=lab)
    ax.axhline(base["pos_median_error"], color="k", ls="--", lw=1.1,
               label="Baseline, all 520 WAPs")
    ax.set_xscale("log")
    ax.set_xlabel("Number of selected WAPs (log scale)")
    ax.set_ylabel("Median positioning error\n(dataset coordinate units)")
    ax.set_title("Feature budget vs median positioning error")
    ax.legend(loc="lower left", fontsize=7.0)
    fig.text(0.01, -0.035, threshold_footnote(sweep, wrap=True),
             fontsize=6.4, color="#444444", ha="left", va="top")
    _save(fig, "fig11_selected_waps_vs_positioning_error",
          with_thresholds(sweep)[
              ["condition", "family", "utility_model", "rel_minutil_pct",
               "abs_minutil", "total_db_utility", "budget_n",
               "pos_median_error", "pos_mean_error", "pos_p75_error",
               "pos_p90_error"]])

    # --- fig12: confusion matrices ------------------------------------------
    det = load_json(RESULTS / "ips_summary.json")["conditions"]
    pick = ["baseline_all_520"]
    bb = ips[(ips["family"] == "huim_topn")]
    if len(bb):
        pick.append(bb.loc[bb["joint_building_floor_accuracy"].idxmax()]
                    ["condition"])
    fig, axes = plt.subplots(1, len(pick), figsize=(5.4 * len(pick), 4.6))
    axes = np.atleast_1d(axes)
    rows = []
    for ax, cond in zip(axes, pick):
        m = det[cond]["result"]["knn"]
        cm = np.array(m["confusion_matrix"], dtype=float)
        labs = m["confusion_matrix_labels"]
        norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
        im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(labs)))
        ax.set_xticklabels(labs, rotation=90, fontsize=7)
        ax.set_yticks(range(len(labs)))
        ax.set_yticklabels(labs, fontsize=7)
        ax.set_xlabel("Predicted BUILDINGID_FLOOR")
        ax.set_ylabel("True BUILDINGID_FLOOR")
        n = int(det[cond]["condition"]["n_waps_selected"])
        mu = mu_text(det[cond]["condition"].get("rel_minutil_pct", ""))
        ax.set_title(f"{cond}\n{n} WAPs, " + (f"{mu}, " if mu else "") +
                     f"joint acc {m['joint_building_floor_accuracy']*100:.2f}%",
                     fontsize=9)
        ax.grid(False)
        for i in range(len(labs)):
            for j in range(len(labs)):
                if cm[i, j]:
                    ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                            fontsize=6,
                            color="white" if norm[i, j] > 0.5 else "black")
                rows.append({"condition": cond, "true": labs[i],
                             "pred": labs[j], "count": int(cm[i, j])})
        fig.colorbar(im, ax=ax, fraction=0.046, label="row-normalised share")
    _save(fig, "fig12_confusion_matrices", pd.DataFrame(rows))


# ------------------------------------------------------------------ EDA figures
def eda_figures() -> None:
    tr, va = load_splits()
    prep = fit_preprocessor(tr)
    wap = prep.wap_cols
    W = tr[wap].to_numpy()

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    det = W[W != NOT_DETECTED]
    axes[0].hist(det, bins=np.arange(-105, 2, 2), color="#1f3b73")
    axes[0].set_xlabel("RSSI of detected access points (dBm)")
    axes[0].set_ylabel("Number of readings")
    axes[0].set_title(f"Detected RSSI values (n={det.size:,})")
    cnt = (W != NOT_DETECTED).sum(axis=1)
    axes[1].hist(cnt, bins=np.arange(0, cnt.max() + 2), color="#8c2d04")
    axes[1].set_xlabel("Access points detected per fingerprint")
    axes[1].set_ylabel("Number of fingerprints")
    axes[1].set_title(f"Sparsity: mean {cnt.mean():.1f} of {len(wap)} WAPs")
    _save(fig, "fig13_eda_rssi_and_sparsity",
          pd.DataFrame({"detections_per_fingerprint": cnt}))

    # mutual information across WAPs, which is Model B's external utility
    y = joint_label(tr)
    mi, h_y = conditional_entropy_reduction(discretise(tr, wap), y)
    support = (W != NOT_DETECTED).sum(axis=0)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    axes[0].hist(mi[support > 0], bins=40, color="#145a32")
    axes[0].set_xlabel("Mutual information with BUILDINGID_FLOOR (bits)")
    axes[0].set_ylabel("Number of WAPs")
    axes[0].set_title(f"Discriminativeness of the {int((support>0).sum())} "
                      f"detected WAPs\n(label entropy H(Y) = {h_y:.3f} bits)")
    axes[1].scatter(support[support > 0], mi[support > 0], s=9, alpha=0.6,
                    color="#145a32")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Detection count in trainingData (log scale)")
    axes[1].set_ylabel("Mutual information (bits)")
    axes[1].set_title("Being detected often is not the same as\nbeing "
                      "informative")
    _save(fig, "fig14_mutual_information_vs_support",
          pd.DataFrame({"wap": wap, "support": support, "mi_bits": mi}))

    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    ct = pd.crosstab(tr["BUILDINGID"], tr["FLOOR"])
    bottom = np.zeros(len(ct))
    for f in ct.columns:
        ax.bar(ct.index.astype(str), ct[f], bottom=bottom, label=f"Floor {f}")
        bottom += ct[f].to_numpy()
    ax.set_xlabel("BUILDINGID")
    ax.set_ylabel("Number of training fingerprints")
    ax.set_title("trainingData: fingerprints per building and floor")
    ax.legend(ncol=5, fontsize=8)
    _save(fig, "fig15_building_floor_distribution", ct.reset_index())


def main() -> None:
    huim = pd.read_csv(METRICS / "huim_runs.csv")
    mining_figures(huim)
    p = METRICS / "ips_results.csv"
    if p.exists():
        I = pd.read_csv(p)
        ips_figures(I)
        error_in_metres_figure(I)
        minutil_union_figure(I)
    else:
        LOG.warning("%s missing - skipping IPS figures", p)
    cost_figures()
    eda_figures()
    LOG.info("figures in %s", FIGURES)




# ------------------------------------------------- cost and accuracy-in-metres
def cost_figures() -> None:
    """PHASE I part 2 - the time/memory evaluation the group's brief asks for."""
    p = METRICS / "ips_cost.csv"
    if not p.exists():
        LOG.warning("%s missing - skipping cost figures", p)
        return
    C = pd.read_csv(p).sort_values("n_features")
    # the cost table has no threshold column; join it from the IPS results so
    # each HUIM point can carry the minUtil of the mining run behind it
    ipsp = METRICS / "ips_results.csv"
    if ipsp.exists():
        I = pd.read_csv(ipsp)[["condition", "utility_model", "rel_minutil_pct"]]
        C = C.merge(I, on="condition", how="left")
    else:
        C["utility_model"], C["rel_minutil_pct"] = "", np.nan
    base = C[C["condition"] == "baseline_all_520"]
    b = base.iloc[0] if len(base) else None

    fam_col = {"baseline": "#1a1a1a", "control_top_mi": "#4a148c",
               "control_top_support": "#b8860b"}
    fam_mk = {"baseline": "*", "control_top_mi": "s",
              "control_top_support": "^"}
    fam_lab = {"baseline": "Baseline (all / detected WAPs)",
               "control_top_mi": "Control: top-n by mutual information",
               "control_top_support": "Control: top-n by detection count"}
    huim_mk = {"huim_union": "o", "huim_topn": "D"}

    def scatter_all(ax, xcol, ycol, ys=1.0, label=True):
        for fam, g in C[~C["family"].str.startswith("huim")].groupby("family"):
            ax.scatter(g[xcol], g[ycol] * ys, s=42, color=fam_col.get(fam, "k"),
                       marker=fam_mk.get(fam, "o"),
                       label=fam_lab.get(fam, fam) if label else None, zorder=3)
        hu = C[C["family"].str.startswith("huim")].sort_values(
            ["family", "utility_model"], ascending=[False, True])
        for _, r in hu.iterrows():
            mc = MODEL_STYLE.get(r["utility_model"], ("#8c2d04",))[0]
            kind = "union" if r["family"] == "huim_union" else "top-n"
            ax.scatter(r[xcol], r[ycol] * ys, s=46, color=mc,
                       marker=huim_mk.get(r["family"], "o"),
                       edgecolors="white", linewidths=0.6, zorder=4,
                       label=(f"HUIM {kind} {MODEL_LETTER.get(r['utility_model'], '?')}, "
                              f"{mu_text(r['rel_minutil_pct'])}, "
                              f"{int(r['n_features'])} WAP") if label else None)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2))

    ax = axes[0]
    ax.plot(C["n_features"], C["predict_ms_per_fingerprint"], color="#999999",
            lw=1.0, zorder=1)
    scatter_all(ax, "n_features", "predict_ms_per_fingerprint")
    ax.set_xlabel("Number of selected WAPs")
    ax.set_ylabel("Online cost: prediction time\nper fingerprint (ms, 1 core)")
    ax.set_title("Time to locate one fingerprint")
    kd = C[C["sklearn_algorithm"] != "brute"]
    if len(kd):
        ax.annotate("sklearn switches to a\ntree index here, which is\n"
                    "slower on data this sparse",
                    xy=(kd["n_features"].iloc[0],
                        kd["predict_ms_per_fingerprint"].iloc[0]),
                    xytext=(60, 0.62), fontsize=7.5, color="#555555",
                    arrowprops=dict(arrowstyle="->", color="#555555", lw=0.8))

    ax = axes[1]
    ax.plot(C["n_features"], C["db_memory_float64_mb"], color="#1f3b73",
            marker="o", ms=4, lw=1.3, label="float64 (this implementation)")
    ax.plot(C["n_features"], C["db_memory_float32_mb"], color="#145a32",
            marker="s", ms=4, lw=1.3, ls="--", label="float32")
    ax.plot(C["n_features"], C["db_memory_int8_mb"], color="#b8860b",
            marker="^", ms=4, lw=1.3, ls=":", label="int8")
    ax.set_xlabel("Number of selected WAPs")
    ax.set_ylabel("Fingerprint database size (MB)")
    ax.set_title("Memory held by the index")
    ax.legend(fontsize=7.5, loc="upper left")

    ax = axes[2]
    scatter_all(ax, "predict_ms_per_fingerprint",
                "joint_building_floor_accuracy", ys=100, label=False)
    if b is not None:
        ax.axhline(b["joint_building_floor_accuracy"] * 100, color="k",
                   ls="--", lw=1.0)
        ax.axvline(b["predict_ms_per_fingerprint"], color="k", ls="--", lw=1.0)
        ax.annotate("baseline\nall 520 WAP",
                    xy=(b["predict_ms_per_fingerprint"],
                        b["joint_building_floor_accuracy"] * 100),
                    xytext=(-62, -24), textcoords="offset points",
                    fontsize=7.5, color="k",
                    arrowprops=dict(arrowstyle="->", color="k", lw=0.8))
    ax.set_xlabel("Prediction time per fingerprint (ms)")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    ax.set_title("Cost against accuracy\n(up and to the left is better)")
    # the six HUIM points sit on top of each other at ~0.2 ms; zoom in on them
    # so each can be read together with its minUtil
    hu = C[C["family"].str.startswith("huim")]
    if len(hu):
        axin = ax.inset_axes([0.36, 0.05, 0.56, 0.47])
        xs = hu["predict_ms_per_fingerprint"]
        ys = hu["joint_building_floor_accuracy"] * 100
        x0, x1 = xs.min() - 0.024, xs.max() + 0.022
        y0, y1 = ys.min() - 4, ys.max() + 4
        # label offsets (points) per HUIM condition, chosen so that the two
        # top-n points that almost coincide (B and C) do not overprint
        lab_off = {("huim_union", "A_signal"): (5, -3, "left"),
                   ("huim_union", "B_discriminative"): (5, 2, "left"),
                   ("huim_union", "C_rare_discriminative"): (5, -3, "left"),
                   ("huim_topn", "A_signal"): (-5, -3, "right"),
                   ("huim_topn", "B_discriminative"): (-5, 5, "right"),
                   ("huim_topn", "C_rare_discriminative"): (0, -11, "center")}
        near = C[C["predict_ms_per_fingerprint"].between(x0, x1)
                 & (C["joint_building_floor_accuracy"] * 100).between(y0, y1)]
        for _, r in near.iterrows():
            if r["family"].startswith("huim"):
                mc = MODEL_STYLE.get(r["utility_model"], ("#8c2d04",))[0]
                axin.scatter(r["predict_ms_per_fingerprint"],
                             r["joint_building_floor_accuracy"] * 100, s=34,
                             color=mc, marker=huim_mk.get(r["family"], "o"),
                             edgecolors="white", linewidths=0.5, zorder=4)
                kind = "union" if r["family"] == "huim_union" else "top-n"
                dx, dy, ha = lab_off.get((r["family"], r["utility_model"]),
                                         (5, -2, "left"))
                axin.annotate(f"{kind} {MODEL_LETTER.get(r['utility_model'], '?')}"
                              f" {float(r['rel_minutil_pct']):g}%",
                              (r["predict_ms_per_fingerprint"],
                               r["joint_building_floor_accuracy"] * 100),
                              xytext=(dx, dy), textcoords="offset points",
                              fontsize=5.8, color=mc, ha=ha)
            else:
                axin.scatter(r["predict_ms_per_fingerprint"],
                             r["joint_building_floor_accuracy"] * 100, s=26,
                             color=fam_col.get(r["family"], "k"),
                             marker=fam_mk.get(r["family"], "o"), zorder=3)
                axin.annotate(f"n={int(r['n_features'])}",
                              (r["predict_ms_per_fingerprint"],
                               r["joint_building_floor_accuracy"] * 100),
                              xytext=(4, 2), textcoords="offset points",
                              fontsize=5.4, color="#555555")
        axin.set_xlim(x0, x1)
        axin.set_ylim(y0, y1)
        axin.tick_params(labelsize=6)
        axin.set_title("zoom: HUIM points (label = minUtil)", fontsize=6.6,
                       pad=2)
        ax.indicate_inset_zoom(axin, edgecolor="#777777", lw=0.6)
    # one shared legend under the three panels: it has to name every HUIM
    # point together with the minUtil threshold of the run that produced it
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3,
               fontsize=7.4, frameon=False)
    foot = threshold_footnote(C[C["family"].str.startswith("huim")])
    if foot:
        fig.text(0.5, -0.165, foot, fontsize=6.6, color="#444444",
                 ha="center", va="top")
    _save(fig, "fig16_ips_time_and_memory",
          with_thresholds(C)[
              ["condition", "family", "utility_model", "rel_minutil_pct",
               "abs_minutil", "total_db_utility", "n_features",
               "sklearn_algorithm", "fit_seconds", "predict_total_seconds",
               "predict_ms_per_fingerprint", "db_memory_float64_mb",
               "db_memory_float32_mb", "db_memory_int8_mb",
               "predict_peak_rss_delta_mb", "joint_building_floor_accuracy"]])


def _with_optimised_row(sel: pd.DataFrame) -> pd.DataFrame:
    """Insert the PHASE I3 positioning model (all WAPs) right after the
    baseline, so one chart shows the error of the study's k-NN AND the error
    after optimisation against the same 7-8 m band.

    The statistics are computed from the per-row prediction file with numpy,
    exactly as ips_model.positioning_error does for the study's k-NN. If PHASE
    I3 has not been run the chart is returned unchanged."""
    pp = RESULTS / "predictions" / "val_predictions_optimised.csv"
    pj = RESULTS / "positioning_optimisation.json"
    if not (pp.exists() and pj.exists()):
        return sel
    P = pd.read_csv(pp)
    g, d = P["err_ground_m"].to_numpy(), P["err_projected_m"].to_numpy()
    base_i = int(np.flatnonzero(sel["condition"] == "baseline_all_520")[0])
    row = {"condition": "optimised_all_520",
           "family": "optimised_positioning",
           "n_waps_selected": int(sel.iloc[base_i]["n_waps_selected"]),
           "pos_median_error_ground_m": float(np.median(g)),
           "pos_p75_error_ground_m": float(np.percentile(g, 75)),
           "pos_p90_error_ground_m": float(np.percentile(g, 90)),
           "pos_p95_error_ground_m": float(np.percentile(g, 95)),
           "pos_mean_error_ground_m": float(g.mean()),
           "pos_median_error": float(np.median(d)),
           "pos_mean_error": float(d.mean()),
           "joint_building_floor_accuracy": load_json(pj)["validation"][
               "selected"]["joint_building_floor_accuracy"]}
    return pd.concat([sel.iloc[:base_i + 1], pd.DataFrame([row]),
                      sel.iloc[base_i + 1:]], ignore_index=True)


def error_in_metres_figure(ips: pd.DataFrame) -> None:
    """Positioning error against the 7-8 m accuracy target the group set."""
    need = ["pos_median_error_ground_m", "pos_p75_error_ground_m",
            "pos_p90_error_ground_m", "pos_p95_error_ground_m",
            "pos_mean_error_ground_m"]
    if not all(c in ips.columns for c in need):
        LOG.warning("ground-metre columns missing - skipping error figure")
        return
    keys = ["baseline_all_520"]
    for fam in ("huim_union", "huim_topn"):
        g = ips[ips["family"] == fam]
        for model, gg in g.groupby("utility_model"):
            keys.append(gg.loc[gg["joint_building_floor_accuracy"].idxmax()]
                        ["condition"])
    for fam in ("control_top_mi", "control_top_support"):
        g = ips[(ips["family"] == fam) & (ips["n_waps_selected"] == 200)]
        if len(g):
            keys.append(g.iloc[0]["condition"])
    seen, order = set(), []
    for k in keys:
        if k not in seen and (ips["condition"] == k).any():
            seen.add(k)
            order.append(k)
    sel = _with_optimised_row(ips.set_index("condition").loc[order]
                              .reset_index())
    opt_i = [i for i, c in enumerate(sel["condition"])
             if str(c).startswith("optimised")]

    fig, ax = plt.subplots(figsize=(10.8, 4.5))
    x = np.arange(len(sel))
    w = 0.19
    for i in opt_i:                       # highlight the optimised model
        ax.axvspan(i - 0.5, i + 0.5, color="#1f3b73", alpha=0.07, zorder=0)
    series = [("pos_median_error_ground_m", "Median", "#1f3b73"),
              ("pos_mean_error_ground_m", "Mean", "#8c2d04"),
              ("pos_p75_error_ground_m", "75th pct", "#145a32"),
              ("pos_p90_error_ground_m", "90th pct", "#b8860b")]
    ax.axhspan(7, 8, color="#2e7d32", alpha=0.13, zorder=0)
    # label in the right margin, outside the bars it used to overlap
    ax.annotate("target band\n7-8 m", xy=(1.005, 7.5),
                xycoords=("axes fraction", "data"), fontsize=8,
                color="#2e7d32", va="center", ha="left")
    for i, (col, lab, c) in enumerate(series):
        off = (i - 1.5) * w
        ax.bar(x + off, sel[col], width=w, label=lab, color=c, zorder=2)
        for xi, v in zip(x + off, sel[col]):
            ax.text(xi, v + 1.2, f"{v:.2f}", ha="center", fontsize=6.6,
                    rotation=90, va="bottom")
    def short(cond: str, n: int, pct) -> str:
        if cond.startswith("baseline_all"):
            lab = "Baseline\nk-NN cũ"
        elif cond.startswith("optimised"):
            lab = "Mô hình tối ưu\n(PHASE I3)"
        elif cond.startswith("control_top_mi"):
            lab = "Control\ntop-n MI"
        elif cond.startswith("control_top_support"):
            lab = "Control\ntop-n support"
        else:
            m = ("A" if "A_signal" in cond else
                 "B" if "B_discr" in cond else
                 "C" if "C_rare" in cond else "?")
            kind = "top-n" if cond.startswith("huim_topn") else "union"
            lab = f"HUIM {m}\n{kind}"
        mu = mu_text(pct)
        return f"{lab}\n{n} WAP" + (f"\n{mu}" if mu else "\n ")

    ax.set_xticks(x)
    ax.set_xticklabels([short(c, int(n), p) for c, n, p in
                        zip(sel["condition"], sel["n_waps_selected"],
                            sel["rel_minutil_pct"])],
                       fontsize=7.4)
    ax.set_ylabel("Positioning error, true ground metres\n"
                  "(Web Mercator scale correction applied)")
    ax.set_ylim(0, float(sel[[c for c, _l, _co in series]].to_numpy().max())
                * 1.22)
    ax.set_title("Positioning error against the 7-8 m target")
    ax.legend(fontsize=8, ncol=4, loc="upper left")
    note = ""
    if opt_i:
        note = ("All other bars use the study's k-NN (k=1, Manhattan); the "
                "shaded group is the PHASE I3 model, selected on leave-users-"
                "out folds of trainingData.\n")
    fig.text(0.01, -0.03, note + threshold_footnote(sel), fontsize=6.8,
             color="#444444", ha="left", va="top")
    _save(fig, "fig17_positioning_error_metres",
          with_thresholds(sel)[
              ["condition", "utility_model", "rel_minutil_pct", "abs_minutil",
               "total_db_utility", "n_waps_selected"] + need +
              ["pos_median_error", "pos_mean_error",
               "joint_building_floor_accuracy"]])


def minutil_union_figure(ips: pd.DataFrame) -> None:
    """fig19 - for the 'union' selection minUtil is the ONLY knob. Left: a
    lookup table with one row per mining run (threshold as a percentage AND as
    an absolute utility, run status, HUI count, WAP count, accuracy). Right:
    joint accuracy against minUtil, every run at its own tick. Together they
    let a reader trace any HUIM union value on another chart back to the
    threshold that produced it."""
    U = with_thresholds(ips[ips["family"] == "huim_union"])
    if not len(U):
        return
    U = U.sort_values(["utility_model", "rel_minutil_pct"],
                      ascending=[True, False])
    fig, (axt, ax) = plt.subplots(1, 2, figsize=(11.4, 4.6),
                                  gridspec_kw={"width_ratios": [1.25, 1.0]})

    # ---- left: lookup table ----------------------------------------------
    axt.axis("off")
    head = ["Model", "minUtil\n(%)", "minUtil\n(absolute)", "Run status",
            "HUIs", "WAPs\nselected", "Joint\nacc. (%)"]
    cells, colours = [], []
    for _, r in U.iterrows():
        done = r["huim_status"] == "COMPLETED"
        cells.append([MODEL_LETTER.get(r["utility_model"], "?"),
                      f"{float(r['rel_minutil_pct']):g}",
                      f"{r['abs_minutil']:,.0f}",
                      "completed" if done else "ABORTED (truncated)",
                      f"{int(r['n_huis']):,}",
                      f"{int(r['n_waps_selected'])}",
                      f"{r['joint_building_floor_accuracy']*100:.2f}"])
        colours.append(MODEL_STYLE[r["utility_model"]][0] if done
                       else "#9a9a9a")
    tb = axt.table(cellText=cells, colLabels=head, loc="upper center",
                   cellLoc="center", colLoc="center",
                   colWidths=[0.08, 0.11, 0.16, 0.25, 0.13, 0.12, 0.12])
    tb.auto_set_font_size(False)
    tb.set_fontsize(6.6)
    tb.scale(1.0, 1.08)
    for (ri, ci), cell in tb.get_celld().items():
        cell.set_linewidth(0.3)
        cell.set_edgecolor("#bbbbbb")
        if ri == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#eeeeee")
            cell.set_height(cell.get_height() * 1.7)
        else:
            cell.get_text().set_color(colours[ri - 1])
    axt.set_title("Every HUIM union run: threshold -> WAP set -> accuracy",
                  fontsize=9)

    # ---- right: accuracy against minUtil ------------------------------------
    for model, g in U.groupby("utility_model"):
        c, mk, lab = MODEL_STYLE[model]
        g = g.sort_values("rel_minutil_pct")
        done = g["huim_status"] == "COMPLETED"
        ax.plot(g["rel_minutil_pct"], g["joint_building_floor_accuracy"] * 100,
                color=c, lw=1.1, label=lab)
        ax.scatter(g.loc[done, "rel_minutil_pct"],
                   g.loc[done, "joint_building_floor_accuracy"] * 100,
                   marker=mk, color=c, s=30, zorder=3)
        ax.scatter(g.loc[~done, "rel_minutil_pct"],
                   g.loc[~done, "joint_building_floor_accuracy"] * 100,
                   marker=mk, s=34, facecolors="white", edgecolors=c, lw=1.2,
                   zorder=3)
    ticks = sorted(U["rel_minutil_pct"].astype(float).unique())
    ax.set_xscale("log")
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks], rotation=90, fontsize=7)
    ax.minorticks_off()
    ax.invert_xaxis()
    ax.set_xlabel("minUtil threshold (% of total database utility, log scale)")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    base = ips[ips["condition"] == "baseline_all_520"]
    if len(base):
        ax.axhline(base["joint_building_floor_accuracy"].iloc[0] * 100,
                   color="k", ls="--", lw=1.0, label="Baseline, all 520 WAPs")
    ax.scatter([], [], marker="o", s=30, facecolors="white",
               edgecolors="#555555",
               label="hollow = run aborted at the resource limit")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=7, loc="lower left", bbox_to_anchor=(0.0, 0.36))
    ax.set_title("minUtil vs joint accuracy of the union selection", fontsize=9)
    fig.text(0.01, -0.03, "Absolute minUtil = minUtil% x total database "
             "utility of the model (A 9,058,242; B 4,354,299; C 6,211,852 - "
             "results/metrics/huim_runs.csv). Grey rows: aborted runs, whose "
             "truncated HUI sets are never used to rank WAPs.",
             fontsize=6.6, color="#444444", ha="left", va="top")
    _save(fig, "fig19_minutil_vs_union_selection",
          U[["condition", "utility_model", "rel_minutil_pct", "abs_minutil",
             "total_db_utility", "huim_status", "n_huis", "n_waps_selected",
             "joint_building_floor_accuracy", "pos_mean_error_ground_m"]])


if __name__ == "__main__":
    main()
