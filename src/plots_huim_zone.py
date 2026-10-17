"""PHASE ZJ - charts of PHASE Z. Every PNG has a CSV with exactly the rows drawn.

  fig50_zone_theta_curve       theta -> WAPs kept, and theta -> mean error (dev
                               and test), UJIIndoorLoc, Models A and B
  fig51_zone_vs_alternatives   UJIIndoorLoc: HUIM-zone vs all APs, global HUIM,
                               and the matched-budget controls
  fig52_zone_all_datasets      every dataset / test set: all APs vs HUIM-zone
  fig53_zone_cdf_uji           error distribution on UJIIndoorLoc validation
  fig54_zone_per_zone_waps     UJIIndoorLoc: WAPs each building-floor contributes
  fig55_zone_time              UJIIndoorLoc: ms per fingerprint vs WAPs kept

Run: python src/plots_huim_zone.py
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
from run_huim_zone import MODELS, ORDER, OUT_ROOT, TARGET_M
from utils import FIGURES

OUT = FIGURES / "huim_zone"
OUT.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GRAY, INK, MUTED = "#8a8a85", "#1c1c1a", "#6b6b66"
MODEL_COLOR = {"A_signal": BLUE, "B_discriminative": ORANGE}
TITLES = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB",
          "hcxy": "HCXY", "hus": "HUS", "hus_dedup": "HUS (khử trùng lặp)"}

plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.25,
                     "grid.color": "#c8c8c3", "axes.edgecolor": "#9a9a95",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "savefig.dpi": 200,
                     "savefig.bbox": "tight", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED})


def save(fig, name: str, data: pd.DataFrame) -> None:
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)
    data.to_csv(OUT / f"{name}.csv", index=False)


def target_line(ax, horizontal=True):
    (ax.axhline if horizontal else ax.axvline)(TARGET_M, color="#c62828", lw=1.2,
                                               ls="--", zorder=1)


def load(key):
    d = OUT_ROOT / key
    return (pd.read_csv(d / "test_results.csv"), pd.read_csv(d / "dev_selection.csv"),
            json.load(open(d / "selected.json", encoding="utf-8")))


def fig50():
    R, D, S = load("uji")
    t = next(iter(S["tests"]))
    h = R[(R.family == "huim_zone") & (R.test_set == t)].copy()
    h = h.merge(D[["set", "dev_mean_ground_m"]], on="set")
    a = R[(R.set == "all_aps") & (R.test_set == t)].iloc[0]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"wspace": 0.3})
    for m, g in h.groupby("utility_model"):
        g = g.sort_values("theta_pct")
        c = MODEL_COLOR[m]
        lab = "Model A (p = 1)" if m.startswith("A") else "Model B (p ∝ MI)"
        a1.plot(g.theta_pct, g.n_waps, "-o", color=c, lw=2, ms=6, label=lab)
        a2.plot(g.theta_pct, g.mean_err_m, "-o", color=c, lw=2, ms=6,
                label=f"{lab}: validation")
        a2.plot(g.theta_pct, g.dev_mean_ground_m, "--s", color=c, lw=1.4, ms=5,
                alpha=0.75, label=f"{lab}: dev (chọn ngưỡng)")
    a1.axhline(520, color=GRAY, lw=1, ls=":")
    a1.text(9.9, 505, "520 WAP (toàn bộ)", ha="right", va="top", fontsize=8, color=MUTED)
    a1.set_xlabel("θ = minUtil theo vùng (% tổng utility của vùng)")
    a1.set_ylabel("Số WAP được HUIM theo vùng chọn")
    a1.set_ylim(0, 540)
    a1.invert_xaxis()
    a1.legend(fontsize=8, loc="center left")
    a1.set_title("(a) θ giảm → mỗi tầng giữ thêm AP", fontsize=10)
    a2.axhline(a["mean_err_m"], color=GRAY, lw=1.2, ls=":")
    a2.text(9.9, a["mean_err_m"] + 0.08, f"520 WAP: {a['mean_err_m']:.2f} m",
            ha="right", fontsize=8, color=MUTED)
    target_line(a2)
    a2.text(3.05, TARGET_M + 0.08, "ngưỡng yêu cầu 7 m", ha="right", fontsize=8,
            color="#c62828")
    sel = h[h.selected_on_dev]
    a2.scatter(sel.theta_pct, sel.mean_err_m, s=160, facecolor="none",
               edgecolor=INK, lw=1.4, zorder=5)
    r = sel.iloc[0]
    a2.annotate(f"chọn trên dev: {r.n_waps} WAP\n{r.mean_err_m:.2f} m",
                (r.theta_pct, r.mean_err_m), xytext=(12, 22),
                textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "-", "color": MUTED})
    a2.set_xlabel("θ = minUtil theo vùng (% tổng utility của vùng)")
    a2.set_ylabel("Sai số trung bình (m, thực địa)")
    a2.invert_xaxis()
    a2.legend(fontsize=7.2, loc="upper right")
    a2.set_title("(b) Sai số định vị theo θ", fontsize=10)
    save(fig, "fig50_zone_theta_curve",
         h[["set", "utility_model", "theta_pct", "n_waps", "dev_mean_ground_m",
            "mean_err_m", "joint_accuracy", "selected_on_dev"]])


def fig51():
    R, _D, S = load("uji")
    t = next(iter(S["tests"]))
    T = S["tests"][t]
    n = T["huim_zone"]["n_waps"]
    r = R[R.test_set == t]
    G = pd.read_csv(Path(OUT_ROOT).parent / "multi_dataset" / "uji" / "positioning_conditions.csv")
    G = G[(G.family == "huim_union") & (G.test_set == t)]
    rows = [("Toàn bộ 520 WAP (không chọn)", 520, T["all_aps"]["mean_err_m"], GRAY)]
    for _, g in G.sort_values("utility_model").iterrows():
        m = g.utility_model.split("_")[0]
        rows.append((f"HUIM toàn cục Model {m} ({int(g.n_waps)} WAP, θ {g.rel_minutil_pct:g}%)",
                     int(g.n_waps), g.opt_mean_err_m, ORANGE))
    for fam, lab, c in (("control_top_support", "Top-n theo số lần phát hiện", AQUA),
                        ("control_top_mi", "Top-n theo mutual information", YELLOW)):
        v = r[(r.family == fam) & (r.n_waps == n)].mean_err_m.iloc[0]
        rows.append((f"{lab} ({n} WAP)", n, v, c))
    rv = r[(r.family == "control_random") & (r.n_waps == n)].mean_err_m
    rows.append((f"Ngẫu nhiên ({n} WAP, TB 3 seed)", n, rv.mean(), GRAY))
    hz = T["huim_zone"]
    rows.append((f"HUIM THEO VÙNG ({n} WAP, {hz['set'].split('__')[1][0]}, θ {hz['set'].split('__')[2][:-3]}%)",
                 n, hz["mean_err_m"], BLUE))
    df = pd.DataFrame(rows, columns=["label", "n_waps", "mean_err_m", "color"])
    fig, ax = plt.subplots(figsize=(9, 4.4))
    y = np.arange(len(df))[::-1]
    ax.barh(y, df.mean_err_m, color=df.color, height=0.62, edgecolor="white", lw=2)
    for yy, v in zip(y, df.mean_err_m):
        ax.text(v + 0.25, yy, f"{v:.2f} m", va="center", fontsize=8.5, color=INK)
    target_line(ax, horizontal=False)
    ax.text(TARGET_M + 0.2, len(df) - 0.4, "7 m", color="#c62828", fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(df.label, fontsize=8.5)
    ax.set_xlabel("Sai số trung bình trên validationData (m, thực địa), cùng bộ định vị PHASE I3")
    ax.set_xlim(0, df.mean_err_m.max() * 1.15)
    ax.set_title("UJIIndoorLoc: AP do HUIM theo vùng chọn so với các cách chọn khác", fontsize=10.5)
    ax.grid(axis="y", visible=False)
    save(fig, "fig51_zone_vs_alternatives", df.drop(columns="color"))


def fig52():
    rows = []
    for k in ORDER:
        p = OUT_ROOT / k / "selected.json"
        if not p.exists():
            continue
        S = json.load(open(p, encoding="utf-8"))
        for t, T in S["tests"].items():
            rows.append({"dataset": k, "title": TITLES[k], "test_set": t,
                         "all_waps": T["all_aps"]["n_waps"],
                         "all_mean_err_m": T["all_aps"]["mean_err_m"],
                         "huim_zone_waps": T["huim_zone"]["n_waps"],
                         "huim_zone_mean_err_m": T["huim_zone"]["mean_err_m"],
                         "huim_zone_set": T["huim_zone"]["set"],
                         "global_huim_mean_err_m": (T["global_huim_best"] or {}).get("mean_err_m"),
                         "below_7m": T["below_target"]})
    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = np.arange(len(df))
    w = 0.38
    b1 = ax.bar(x - w / 2, df.all_mean_err_m, w, color=GRAY, label="Toàn bộ AP", edgecolor="white", lw=2)
    b2 = ax.bar(x + w / 2, df.huim_zone_mean_err_m, w, color=BLUE,
                label="AP do HUIM theo vùng chọn", edgecolor="white", lw=2)
    for bars, col in ((b1, "all_waps"), (b2, "huim_zone_waps")):
        for r, (_, d) in zip(bars, df.iterrows()):
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.08,
                    f"{r.get_height():.2f}\n{d[col]} AP", ha="center", va="bottom", fontsize=7)
    target_line(ax)
    ax.text(len(df) - 0.5, TARGET_M + 0.1, "7 m", color="#c62828", fontsize=8.5, ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\n{b}" for a, b in zip(df.title, df.test_set)], fontsize=8)
    ax.set_ylabel("Sai số trung bình (m)")
    ax.set_ylim(0, max(TARGET_M, df[["all_mean_err_m", "huim_zone_mean_err_m"]].max().max()) * 1.25)
    ax.legend(fontsize=8.5, loc="upper right")
    ax.set_title("Mọi dataset: sai số khi định vị chỉ bằng các AP do HUIM theo vùng chọn", fontsize=10.5)
    ax.grid(axis="x", visible=False)
    save(fig, "fig52_zone_all_datasets", df)


def fig53():
    d = OUT_ROOT / "uji" / "predictions"
    curves = {"AP do HUIM theo vùng chọn": (pd.read_csv(d / "validationData__huim_zone.csv").err_m, BLUE),
              "Toàn bộ 520 WAP": (pd.read_csv(d / "validationData__all_aps.csv").err_m, GRAY)}
    g = Path(OUT_ROOT).parent / "multi_dataset" / "uji" / "predictions" / "validationData__study_knn.csv"
    curves["k-NN gốc (k=1), 520 WAP"] = (pd.read_csv(g).err_m, YELLOW)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    rows = []
    for name, (e, c) in curves.items():
        s = np.sort(e.to_numpy())
        ax.plot(s, np.arange(1, len(s) + 1) / len(s) * 100, color=c, lw=2,
                label=f"{name}: TB {s.mean():.2f} m, trung vị {np.median(s):.2f} m")
        for q in (50, 75, 90, 95):
            rows.append({"curve": name, "percentile": q, "err_m": round(float(np.percentile(s, q)), 4)})
        rows.append({"curve": name, "percentile": "mean", "err_m": round(float(s.mean()), 4)})
    target_line(ax, horizontal=False)
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Sai số định vị (m, thực địa)")
    ax.set_ylabel("% fingerprint validation có sai số ≤ x")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("UJIIndoorLoc: phân bố sai số (1 111 fingerprint validation)", fontsize=10.5)
    save(fig, "fig53_zone_cdf_uji", pd.DataFrame(rows))


def fig54():
    S = json.load(open(OUT_ROOT / "uji" / "selected.json", encoding="utf-8"))
    name = S["selection"]["selected_set"]
    H = json.load(open(OUT_ROOT / "uji" / "hui" / f"{name}.json", encoding="utf-8"))
    df = pd.DataFrame([{"zone": z["zone"], "n_transactions": z["n_transactions"],
                        "n_items_seen": z["n_items"], "n_waps_selected": z["n_waps"],
                        "n_huis": z["n_huis"], "theta_used_pct": z["theta_used_pct"],
                        "status": z["status"]} for z in H["zones"]])
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(df))
    ax.bar(x, df.n_items_seen, 0.7, color="#d9d9d4", label="AP thấy được trong tầng", edgecolor="white", lw=2)
    ax.bar(x, df.n_waps_selected, 0.7, color=BLUE, label="AP thuộc ít nhất một HUI của tầng", edgecolor="white", lw=2)
    for xx, (_, r) in zip(x, df.iterrows()):
        ax.text(xx, r.n_items_seen + 3, f"{r.n_waps_selected}/{r.n_items_seen}", ha="center", fontsize=7.5)
        if r.theta_used_pct > float(name.split("__")[2][:-3]) + 1e-9:
            ax.text(xx, -14, f"θ {r.theta_used_pct:.2f}%", ha="center", fontsize=6.5, color=MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([f"tòa {z.split('_')[0]}\ntầng {z.split('_')[1]}" for z in df.zone], fontsize=7.5)
    ax.set_ylabel("Số AP")
    ax.set_title(f"UJIIndoorLoc, {name}: AP mỗi tòa–tầng đóng góp (hợp = {len(H['selected_waps'])} WAP)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="x", visible=False)
    save(fig, "fig54_zone_per_zone_waps", df)


def fig55():
    R, _D, S = load("uji")
    t = next(iter(S["tests"]))
    r = R[(R.test_set == t) & R.family.isin(["huim_zone", "baseline"])].copy()
    r = r.sort_values("n_waps")
    fig, ax = plt.subplots(figsize=(7, 4))
    for fam, c, lab in (("huim_zone", BLUE, "Tập AP của HUIM theo vùng"), ("baseline", GRAY, "Toàn bộ 520 WAP")):
        g = r[r.family == fam]
        ax.scatter(g.n_waps, g.ms_per_fp, s=60, color=c, edgecolor="white", lw=1.5, label=lab, zorder=3)
    s = r[r.selected_on_dev].iloc[0]
    ax.annotate(f"chọn: {s.n_waps} WAP, {s.ms_per_fp:.1f} ms", (s.n_waps, s.ms_per_fp),
                xytext=(10, -20), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Số WAP dùng để định vị")
    ax.set_ylabel("ms / fingerprint (wall-clock)")
    ax.set_xlim(0, 560)
    ax.set_ylim(0, r.ms_per_fp.max() * 1.2)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("UJIIndoorLoc: thời gian định vị theo số WAP", fontsize=10.5)
    save(fig, "fig55_zone_time", r[["set", "n_waps", "ms_per_fp", "mean_err_m"]])


def main():
    for f in (fig50, fig51, fig52, fig53, fig54, fig55):
        f()
        print("ok", f.__name__)


if __name__ == "__main__":
    main()
