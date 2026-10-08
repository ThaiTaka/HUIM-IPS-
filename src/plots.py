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
                        label=(f"HUIM top-n, {mlab.split(' - ')[-1]}"
                               if fam == "huim_topn" else lab))
    ax.axhline(base["joint_building_floor_accuracy"] * 100, color="k", ls="--",
               lw=1.1, label=f"Baseline, all {int(base['n_waps_selected'])} WAPs "
                             f"({base['joint_building_floor_accuracy']*100:.2f}%)")
    ax.set_xscale("log")
    ax.set_xlabel("Number of selected WAPs (log scale)")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    ax.set_title("Feature budget vs joint localisation accuracy")
    ax.legend(loc="upper left", ncol=1, fontsize=8)
    _save(fig, "fig06_selected_waps_vs_accuracy",
          sweep[["condition", "family", "utility_model", "budget_n",
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
                        label=f"HUIM top-n, {mlab.split(' - ')[-1]}")
        else:
            g = g.sort_values("feature_reduction_pct")
            ax.plot(g["feature_reduction_pct"],
                    g["joint_building_floor_accuracy"] * 100,
                    marker=mk, color=c, lw=1.2, ms=4, label=lab)
    union = ips[ips["family"] == "huim_union"]
    if len(union):
        ax.scatter(union["feature_reduction_pct"],
                   union["joint_building_floor_accuracy"] * 100,
                   marker="D", s=28, facecolors="none", edgecolors="#4a148c",
                   lw=1.2, label="HUIM union (minUtil as the only knob)")
    ax.axhline(base["joint_building_floor_accuracy"] * 100, color="k", ls="--",
               lw=1.1, label="Baseline, all 520 WAPs")
    ax.set_xlabel(f"Feature reduction (%)   =  (1 - selected / "
                  f"{int(base['n_waps_selected'])}) x 100")
    ax.set_ylabel("Joint Building-Floor Accuracy (%)")
    ax.set_title("Feature reduction vs joint localisation accuracy")
    ax.legend(loc="lower left", fontsize=8)
    _save(fig, "fig09_feature_reduction_vs_accuracy",
          pd.concat([sweep, union])[
              ["condition", "family", "utility_model", "n_waps_selected",
               "feature_reduction_pct", "joint_building_floor_accuracy"]])

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
    def _short(cond: str, n: int) -> str:
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
        return f"{lab}\n{n} WAP"

    labels = [_short(c, int(n)) for c, n in
              zip(sel["condition"], sel["n_waps_selected"])]
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
    _save(fig, "fig10_baseline_vs_huim_accuracies",
          sel[["condition", "n_waps_selected", "feature_reduction_pct",
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
                        label=f"HUIM top-n, {mlab.split(' - ')[-1]}")
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
    ax.legend(loc="best")
    _save(fig, "fig11_selected_waps_vs_positioning_error",
          sweep[["condition", "family", "utility_model", "budget_n",
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
        ax.set_title(f"{cond}\n{n} WAPs, joint acc "
                     f"{m['joint_building_floor_accuracy']*100:.2f}%",
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
    base = C[C["condition"] == "baseline_all_520"]
    b = base.iloc[0] if len(base) else None

    fam_col = {"baseline": "#1a1a1a", "huim_union": "#8c2d04",
               "huim_topn": "#8c2d04", "control_top_mi": "#4a148c",
               "control_top_support": "#b8860b"}
    fam_mk = {"baseline": "*", "huim_union": "o", "huim_topn": "D",
              "control_top_mi": "s", "control_top_support": "^"}

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.9))

    ax = axes[0]
    ax.plot(C["n_features"], C["predict_ms_per_fingerprint"], color="#999999",
            lw=1.0, zorder=1)
    for fam, g in C.groupby("family"):
        ax.scatter(g["n_features"], g["predict_ms_per_fingerprint"], s=42,
                   color=fam_col.get(fam, "k"), marker=fam_mk.get(fam, "o"),
                   label=fam, zorder=3)
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
    ax.legend(fontsize=7.5, loc="upper left")

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
    for fam, g in C.groupby("family"):
        ax.scatter(g["predict_ms_per_fingerprint"],
                   g["joint_building_floor_accuracy"] * 100, s=42,
                   color=fam_col.get(fam, "k"), marker=fam_mk.get(fam, "o"),
                   label=fam, zorder=3)
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
    ax.legend(fontsize=7.5, loc="lower right")
    _save(fig, "fig16_ips_time_and_memory",
          C[["condition", "family", "n_features", "sklearn_algorithm",
             "fit_seconds", "predict_total_seconds",
             "predict_ms_per_fingerprint", "db_memory_float64_mb",
             "db_memory_float32_mb", "db_memory_int8_mb",
             "predict_peak_rss_delta_mb", "joint_building_floor_accuracy"]])


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
    sel = ips.set_index("condition").loc[order].reset_index()

    fig, ax = plt.subplots(figsize=(9.6, 4.3))
    x = np.arange(len(sel))
    w = 0.19
    series = [("pos_median_error_ground_m", "Median", "#1f3b73"),
              ("pos_mean_error_ground_m", "Mean", "#8c2d04"),
              ("pos_p75_error_ground_m", "75th pct", "#145a32"),
              ("pos_p90_error_ground_m", "90th pct", "#b8860b")]
    ax.axhspan(7, 8, color="#2e7d32", alpha=0.13, zorder=0)
    ax.text(len(sel) - 0.45, 7.5, "target band\n7-8 m", fontsize=8,
            color="#2e7d32", va="center", ha="right")
    for i, (col, lab, c) in enumerate(series):
        off = (i - 1.5) * w
        ax.bar(x + off, sel[col], width=w, label=lab, color=c, zorder=2)
        for xi, v in zip(x + off, sel[col]):
            ax.text(xi, v + 1.2, f"{v:.1f}", ha="center", fontsize=6.6,
                    rotation=90, va="bottom")
    def short(cond: str, n: int) -> str:
        if cond.startswith("baseline_all"):
            lab = "Baseline\ntất cả WAP"
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
        return f"{lab}\n{n} WAP"

    ax.set_xticks(x)
    ax.set_xticklabels([short(c, int(n)) for c, n in
                        zip(sel["condition"], sel["n_waps_selected"])],
                       fontsize=7.4)
    ax.set_ylabel("Positioning error, true ground metres\n"
                  "(Web Mercator scale correction applied)")
    ax.set_ylim(0, float(sel[[c for c, _l, _co in series]].to_numpy().max())
                * 1.22)
    ax.set_title("Positioning error against the 7-8 m target")
    ax.legend(fontsize=8, ncol=4, loc="upper left")
    _save(fig, "fig17_positioning_error_metres",
          sel[["condition", "n_waps_selected"] + need +
              ["pos_median_error", "pos_mean_error",
               "joint_building_floor_accuracy"]])

if __name__ == "__main__":
    main()
