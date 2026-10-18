"""PHASE QJ - charts of the HUIM-only positioner. Each PNG has its CSV.

  fig60_huim_only_all_datasets   mean error per dataset / test set
  fig61_huim_only_cdf_uji        error distribution, UJIIndoorLoc
  fig62_huim_only_dev            dev mean error: theta x m (best of the rest)
  fig63_huim_only_example        one UJIIndoorLoc query: cell scores on the map
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_huim_only import ORDER, OUT_ROOT, TARGET_M
from utils import FIGURES, RESULTS

OUT = FIGURES / "huim_only"
OUT.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GRAY, INK, MUTED, RED = "#8a8a85", "#1c1c1a", "#6b6b66", "#c62828"
TITLES = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB",
          "hcxy": "HCXY", "hus": "HUS", "hus_dedup": "HUS-dedup"}
plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.dpi": 200,
                     "savefig.bbox": "tight", "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": "#9a9a95"})


def save(fig, name, data):
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)
    data.to_csv(OUT / f"{name}.csv", index=False)


def knn_reference() -> pd.DataFrame:
    C = pd.read_csv(RESULTS / "multi_dataset" / "comparison.csv")
    C = C[C.wap_set == "all"]
    s0 = C[C.method.str.startswith("k-NN")][["dataset", "test_set", "mean_err_m"]]
    s4 = C[C.method.str.startswith("Tối ưu PHASE I3")][["dataset", "test_set", "mean_err_m"]]
    return s0.rename(columns={"mean_err_m": "knn_study_m"}).merge(
        s4.rename(columns={"mean_err_m": "knn_opt_m"}), on=["dataset", "test_set"])


def fig60():
    ref = knn_reference()
    rows = []
    for k in ORDER:
        p = OUT_ROOT / k / "summary.json"
        if not p.exists():
            continue
        S = json.load(open(p, encoding="utf-8"))
        for t, T in S["tests"].items():
            rows.append({"dataset": k, "title": TITLES[k], "test_set": t,
                         "huim_only_mean_m": T["mean_err_m"],
                         "huim_only_median_m": T["median_err_m"],
                         "huim_only_joint_accuracy": T["joint_accuracy"]})
    df = pd.DataFrame(rows).merge(ref, on=["dataset", "test_set"], how="left")
    fig, ax = plt.subplots(figsize=(13, 4.6))
    x = np.arange(len(df))
    ax.bar(x, df.huim_only_mean_m, 0.55, color=BLUE, edgecolor="white", lw=2,
           label="Chỉ HUIM (khớp HUI, không k-NN)")
    for xx, v in zip(x, df.huim_only_mean_m):
        ax.text(xx, v + 0.1, f"{v:.2f} m", ha="center", fontsize=8.5, color=INK)
    ax.axhline(TARGET_M, color=RED, ls="--", lw=1.2)
    ax.text(len(df) - 0.5, TARGET_M + 0.1, "7 m", color=RED, ha="right", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\n{b}" for a, b in zip(df.title, df.test_set)], fontsize=8)
    ax.set_ylabel("Sai số trung bình trên tập test (m)")
    ax.set_ylim(0, max(TARGET_M, df.huim_only_mean_m.max()) * 1.2)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="x", visible=False)
    ax.set_title("Định vị chỉ bằng HUIM: sai số trung bình trên mọi dataset", fontsize=11)
    save(fig, "fig60_huim_only_all_datasets", df)


def fig61():
    P = pd.read_csv(OUT_ROOT / "uji" / "predictions" / "validationData.csv")
    d = RESULTS / "multi_dataset" / "uji" / "predictions"
    curves = {"Chỉ HUIM (khớp HUI)": (P.err_m, BLUE),
              "k-NN tối ưu, 520 WAP (tham chiếu)": (pd.read_csv(d / "validationData__optimised.csv").err_m, GRAY),
              "k-NN gốc k=1, 520 WAP (tham chiếu)": (pd.read_csv(d / "validationData__study_knn.csv").err_m, YELLOW)}
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    rows = []
    for n, (e, c) in curves.items():
        s = np.sort(e.to_numpy())
        ax.plot(s, np.arange(1, len(s) + 1) / len(s) * 100, color=c, lw=2,
                label=f"{n}: TB {s.mean():.2f} m, trung vị {np.median(s):.2f} m")
        for q in (50, 75, 90, 95):
            rows.append({"curve": n, "percentile": q, "err_m": round(float(np.percentile(s, q)), 4)})
        rows.append({"curve": n, "percentile": "mean", "err_m": round(float(s.mean()), 4)})
    ax.axvline(TARGET_M, color=RED, ls="--", lw=1.2)
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Sai số định vị (m, thực địa)")
    ax.set_ylabel("% fingerprint test có sai số ≤ x")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("UJIIndoorLoc validationData (1 111 fingerprint): phân bố sai số", fontsize=10.5)
    save(fig, "fig61_huim_only_cdf_uji", pd.DataFrame(rows))


def fig62():
    G = pd.read_csv(OUT_ROOT / "uji" / "dev_grid.csv")
    sel = json.load(open(OUT_ROOT / "uji" / "selection.json", encoding="utf-8"))
    G = G[G.theta_pct == sel["theta_pct"]]
    best = G.groupby(["sigma", "m"]).dev_mean_m.min().reset_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    cols = [GRAY, YELLOW, BLUE, ORANGE, AQUA]
    for (sg, g), c in zip(best.groupby("sigma"), cols):
        lab = "không làm mượt" if sg == 0 else f"σ = {sg:g} m"
        ax.plot(g.m, g.dev_mean_m, "-o", color=c, lw=2, ms=6, label=lab)
    sp = sel["params"]
    ax.scatter([sp["m"]], [sel["dev_mean_m"]], s=170, facecolor="none",
               edgecolor=INK, lw=1.4, zorder=5)
    ax.annotate(f"chọn: σ={sp['sigma']:g} m, m={sp['m']}, dev {sel['dev_mean_m']:.2f} m",
                (sp["m"], sel["dev_mean_m"]), xytext=(10, -26),
                textcoords="offset points", fontsize=8)
    ax.axhline(TARGET_M, color=RED, ls="--", lw=1.2)
    ax.text(30, TARGET_M + 0.03, "7 m", color=RED, ha="right", va="bottom", fontsize=8.5)
    ax.set_xlabel("m = số ô điểm cao nhất dùng để ước lượng toạ độ")
    ax.set_ylabel("Sai số TB trên dev (m)")
    lo = min(TARGET_M, best.dev_mean_m.min()) - 0.3
    ax.set_ylim(lo, best.dev_mean_m.max() + 0.3)
    ax.legend(fontsize=8.5, loc="upper right", ncol=2)
    note = sel.get("dev_folds", "").split(" - ")[0]
    ax.set_title(f"UJIIndoorLoc, utility {sel.get('utility', 'abs')}, θ = {sel['theta_pct']:g}%: dev ({note})", fontsize=9.5)
    save(fig, "fig62_huim_only_dev", best)


def fig63():
    out = OUT_ROOT / "uji"
    P = pd.read_csv(out / "predictions" / "validationData.csv")
    cells = pd.read_csv(out / "model" / "cells.csv")
    sel = json.load(open(out / "selection.json", encoding="utf-8"))
    i = int((P.err_m - P.err_m.median()).abs().idxmin())
    r = P.loc[i]
    bf = f"{int(r.true_building)}_{int(r.true_floor)}"
    same = cells[cells.building_floor == bf]
    m = sel["params"]["m"]
    top = [int(r[f"cell{j + 1}_index"]) for j in range(m)]
    wts = [float(r[f"cell{j + 1}_weight"]) for j in range(m)]
    fig, ax = plt.subplots(figsize=(7.4, 5))
    ax.scatter(same.x, same.y, s=14, color="#d0d0cb", label=f"ô của tòa {bf.split('_')[0]} tầng {bf.split('_')[1]}")
    tc = cells.loc[top]
    ax.scatter(tc.x, tc.y, s=[40 + 400 * w for w in wts], color=BLUE, alpha=0.75,
               edgecolor="white", lw=1.5, label=f"{m} ô có điểm khớp HUI cao nhất (kích thước = trọng số)")
    ax.scatter([r.true_x], [r.true_y], marker="*", s=220, color=AQUA, edgecolor=INK, lw=0.8, label="vị trí thật", zorder=6)
    ax.scatter([r.pred_x], [r.pred_y], marker="X", s=140, color=ORANGE, edgecolor=INK, lw=0.8,
               label=f"vị trí HUIM ước lượng (sai số {r.err_m:.2f} m)", zorder=6)
    pad = 40
    x0, y0 = float(r.true_x), float(r.true_y)
    for coll in ax.collections:
        off = coll.get_offsets()
        coll.set_offsets(off - [x0, y0])
    same, tc = same.assign(x=same.x - x0, y=same.y - y0), tc.assign(x=tc.x - x0, y=tc.y - y0)
    r = r.copy(); r["pred_x"] -= x0; r["pred_y"] -= y0; r["true_x"] = 0.0; r["true_y"] = 0.0
    xs = list(tc.x) + [r.true_x, r.pred_x]
    ys = list(tc.y) + [r.true_y, r.pred_y]
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.set_xlabel("ΔX so với vị trí thật (m chiếu, EPSG:3857)")
    ax.set_ylabel("ΔY so với vị trí thật (m chiếu)")
    ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.01, 1))
    ax.set_title(f"Một truy vấn (dòng {int(r.src_row)} của validationData): HUIM chọn ô và ước lượng vị trí", fontsize=9.5)
    data = pd.DataFrame({"cell_index": top, "x": tc.x.to_numpy(), "y": tc.y.to_numpy(),
                         "weight": wts,
                         "score": [float(r[f"cell{j + 1}_score"]) for j in range(m)]})
    save(fig, "fig63_huim_only_example", data)


def main():
    for f in (fig60, fig61, fig62, fig63):
        f()
        print("ok", f.__name__)


if __name__ == "__main__":
    main()
