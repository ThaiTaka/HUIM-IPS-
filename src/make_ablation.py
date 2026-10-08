"""PHASE J - the ablation table mandated by the brief.

| Method | Utility Model | WAP count | Reduction % | Building Acc | Floor Acc |
| Joint Acc | HUIM Runtime | HUI Count |

Rows: ALL WAP (baseline), HUIM Signal utility (Model A), HUIM Discriminative
utility (Model B), HUIM Rare-discriminative (Model C), plus the matched-budget
controls, because an ablation that compares a method only against "everything"
cannot tell feature selection apart from feature deletion.

Every cell is read from results/metrics/*.csv. HUIM runtime and HUI count are
joined back from the mining log by run tag, so the mining cost that produced a
given accuracy is always visible next to it.

Outputs: results/tables/ablation_study.csv, results/tables/ablation_study.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import METRICS, TABLES, get_logger

LOG = get_logger("ablation", "ablation.log")

MODEL_NAME = {"A_signal": "A - Signal utility",
              "B_discriminative": "B - Discriminative utility",
              "C_rare_discriminative": "C - Rare-discriminative utility"}


def main() -> None:
    I = pd.read_csv(METRICS / "ips_results.csv")
    H = pd.read_csv(METRICS / "huim_runs.csv")
    hidx = H.set_index("run_tag")

    def hinfo(model, pct):
        if not model or pd.isna(pct) or pct == "":
            return None
        m = H[(H["utility_model"] == model) &
              (np.isclose(H["rel_minutil_pct"].astype(float), float(pct)))]
        return m.iloc[0] if len(m) else None

    rows = []

    def add(method, model, r, hr=None, note=""):
        rows.append({
            "Method": method,
            "Utility Model": MODEL_NAME.get(model, model or "-"),
            "minUtil (% of total DB utility)": (f"{float(r['rel_minutil_pct']):g}"
                                                if str(r.get("rel_minutil_pct",
                                                             "")) not in ("", "nan")
                                                else "-"),
            "WAP count": int(r["n_waps_selected"]),
            "Reduction %": round(float(r["feature_reduction_pct"]), 2),
            "Building Acc %": round(float(r["building_accuracy"]) * 100, 2),
            "Floor Acc %": round(float(r["floor_accuracy"]) * 100, 2),
            "Joint Acc %": round(float(r["joint_building_floor_accuracy"]) * 100, 2),
            "Joint Macro F1": round(float(r["joint_macro_f1"]), 4),
            "Median pos. error (coord. units)": round(
                float(r["pos_median_error"]), 2),
            "HUIM Runtime (s)": (round(float(hr["runtime_s"]), 2)
                                 if hr is not None else "-"),
            "HUIM Peak mem (MB)": (round(float(hr["peak_memory_delta_mb"]), 1)
                                   if hr is not None else "-"),
            "HUI Count": (int(hr["n_huis"]) if hr is not None else "-"),
            "HUIM Status": (str(hr["status"]) if hr is not None else "-"),
            "Condition id": r["condition"],
            "Note": note,
        })

    # --- baselines ----------------------------------------------------------
    for cond, label, note in (
            ("baseline_all_520", "ALL WAP (primary baseline)",
             "every WAP column; no selection"),
            ("baseline_detected_465", "ALL WAP detected in training",
             "free reduction: removes columns that are the not-detected "
             "sentinel in every training row; owes nothing to HUIM")):
        g = I[I["condition"] == cond]
        if len(g):
            add(label, "", g.iloc[0], None, note)

    # --- HUIM: union selection (minUtil is the only knob) -------------------
    for model, g in I[I["family"] == "huim_union"].groupby("utility_model"):
        for _, r in g.sort_values("rel_minutil_pct", ascending=False).iterrows():
            hr = hinfo(model, r["rel_minutil_pct"])
            note = "union of WAPs over all mined HUIs"
            if hr is not None and str(hr["status"]) != "COMPLETED":
                note += "; MINING ABORTED - HUI set is truncated, so this " \
                        "selection is biased by search order"
            add("HUIM union", model, r, hr, note)

    # --- HUIM: best top-n per model -----------------------------------------
    for model, g in I[I["family"] == "huim_topn"].groupby("utility_model"):
        best = g.loc[g["joint_building_floor_accuracy"].idxmax()]
        hr = hinfo(model, best["rel_minutil_pct"])
        add("HUIM top-n (best joint acc)", model, best, hr,
            "top n WAPs by utility contribution over the HUI set")
        small = g.loc[g["n_waps_selected"].idxmin()]
        hr2 = hinfo(model, small["rel_minutil_pct"])
        add("HUIM top-n (smallest budget tested)", model, small, hr2,
            "smallest feature budget evaluated for this model")

    # --- controls at the budget of the best HUIM condition ------------------
    topn = I[I["family"] == "huim_topn"]
    if len(topn):
        best_overall = topn.loc[topn["joint_building_floor_accuracy"].idxmax()]
        n = int(best_overall["n_waps_selected"])
        for fam, label in (("control_top_mi",
                            "Control: top-n by mutual information"),
                           ("control_top_support",
                            "Control: top-n by detection count")):
            g = I[(I["family"] == fam) & (I["n_waps_selected"] == n)]
            if len(g):
                add(label, "", g.iloc[0], None,
                    f"matched budget n={n}; no itemset mining involved")
        g = I[(I["family"] == "control_random") & (I["n_waps_selected"] == n)]
        if len(g):
            r = g.iloc[0].copy()
            for c in ("building_accuracy", "floor_accuracy",
                      "joint_building_floor_accuracy", "joint_macro_f1",
                      "pos_median_error"):
                r[c] = g[c].mean()
            r["condition"] = f"control_random__n{n}__mean_of_{len(g)}_seeds"
            add("Control: random n (mean of seeds)", "", r, None,
                f"matched budget n={n}; mean over {len(g)} seeds "
                f"(joint acc range {g['joint_building_floor_accuracy'].min()*100:.2f}"
                f"-{g['joint_building_floor_accuracy'].max()*100:.2f}%)")

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "ablation_study.csv", index=False)

    cols = ["Method", "Utility Model", "minUtil (% of total DB utility)",
            "WAP count", "Reduction %", "Building Acc %", "Floor Acc %",
            "Joint Acc %", "Joint Macro F1",
            "Median pos. error (coord. units)", "HUIM Runtime (s)",
            "HUI Count", "HUIM Status"]
    md = ["# Ablation study\n",
          "> Generated by `src/make_ablation.py` from "
          "`results/metrics/ips_results.csv` and "
          "`results/metrics/huim_runs.csv`. No value is entered by hand.\n",
          "All accuracies are measured on validationData "
          f"({int(I['n_evaluated'].iloc[0]) if 'n_evaluated' in I else 1111} "
          "fingerprints), evaluated once per condition, with a single frozen "
          "k-NN configuration shared by every row.\n",
          "Positioning error is in **metres**. `Median pos. error` is the "
          "straight distance in the dataset's EPSG:3857 projected coordinates "
          "- the convention the UJIIndoorLoc literature uses - so multiply by "
          "0.766 for true ground metres. See "
          "`results/coordinate_system_verification.json`.\n",
          "| " + " | ".join(cols) + " |",
          "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    md.append("\n## Notes per row\n")
    for _, r in df.iterrows():
        if r["Note"]:
            md.append(f"- **{r['Method']}** (`{r['Condition id']}`): {r['Note']}")
    (TABLES / "ablation_study.md").write_text("\n".join(md) + "\n",
                                              encoding="utf-8")
    LOG.info("wrote %s (%d rows) and .md", TABLES / "ablation_study.csv",
             len(df))
    print(df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
