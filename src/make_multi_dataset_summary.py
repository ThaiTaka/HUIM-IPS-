"""Cross-dataset comparison of the HUIM-IPS study (reads results/multi_dataset).

Every number in the outputs is read from the files src/run_multi_dataset.py
wrote; nothing is typed here.

Outputs
  results/multi_dataset/comparison.csv        one row per dataset x test set x
                                              method (accuracy, metres, time)
  results/multi_dataset/huim_vs_controls.csv  optimised error of each HUIM set
                                              against top-MI / top-support sets
                                              of the same size
  results/multi_dataset/TONG_HOP_DA_DATASET.md   the summary, in Vietnamese
  figures/multi_dataset/fig40_*.png (+ .csv), fig41_*.png (+ .csv)
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
from utils import FIGURES, RESULTS, load_json

ROOT = RESULTS / "multi_dataset"
FIG = FIGURES / "multi_dataset"
ORDER = ["uji", "uji_lib3", "dlulib", "hcxy", "hus_dedup", "hus"]
SHORT = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3",
         "dlulib": "DLULIB", "hcxy": "HCXY",
         "hus_dedup": "HUS (bỏ dòng chép)", "hus": "HUS nguyên bản"}
MODEL = {"A_signal": "A", "B_discriminative": "B",
         "C_rare_discriminative": "C"}
GRAY, BLUE, ORANGE, AQUA = "#9a9a9a", "#2a78d6", "#eb6834", "#1baf7a"
# The study's own UJIIndoorLoc result, which names the procedure ("the 5.36 m
# model") - read, not typed.
_PO = load_json(RESULTS / "positioning_optimisation.json")
UJI_S0_M = float(_PO["validation"]["ablation"][0]["val_mean_ground_m"])
UJI_SEL_M = float(_PO["validation"]["selected"]["positioning_error"]
                  ["mean_error_ground_m"])
M_S0 = f"{UJI_S0_M:.2f}".replace(".", ",") + " m"
M_SEL = f"{UJI_SEL_M:.2f}".replace(".", ",") + " m"
TRANSFER = f"Cấu hình UJI {M_SEL} áp nguyên"
# Provenance of each dataset. The two DOIs were checked against Crossref
# (UJIIndoorLoc in research/doi_verification.json; UJI_LIB on 2026-10-13).
SOURCES = {
    "uji": "Torres-Sospedra et al., IPIN 2014, DOI 10.1109/IPIN.2014.7275492",
    "uji_lib3": "Mendoza-Silva, Richter, Torres-Sospedra, Lohan, Huerta, "
                "\"Long-Term WiFi Fingerprinting Dataset for Research on Robust "
                "Indoor Positioning\", Data 3(1):3, 2018, DOI "
                "10.3390/data3010003 (Crossref)",
    "dlulib": "không có tài liệu mô tả đi kèm trong thư mục",
    "hcxy": "không có tài liệu mô tả đi kèm; đơn vị toạ độ không được ghi",
    "hus": "không có tài liệu mô tả đi kèm trong thư mục",
}
SOURCES["hus_dedup"] = SOURCES["hus"]


def load_ds(key: str) -> dict | None:
    d = ROOT / key
    need = ["dataset_summary.json", "ips.json", "positioning.json",
            "positioning_ablation.csv", "positioning_conditions.csv",
            "ips_results.csv"]
    if not all((d / f).exists() for f in need):
        return None
    out = {"key": key, "summary": load_json(d / "dataset_summary.json"),
           "ips": load_json(d / "ips.json"),
           "pos": load_json(d / "positioning.json"),
           "abl": pd.read_csv(d / "positioning_ablation.csv"),
           "cond": pd.read_csv(d / "positioning_conditions.csv"),
           "ipsr": pd.read_csv(d / "ips_results.csv"),
           "huim": pd.concat([pd.read_csv(f) for f in
                              sorted(d.glob("huim_runs__*.csv"))],
                             ignore_index=True),
           "timing": (pd.read_csv(d / "timing.csv")
                      if (d / "timing.csv").exists() else None),
           "curve": (pd.read_csv(d / "positioning_curve.csv")
                     if (d / "positioning_curve.csv").exists() else None),
           "transfer": (pd.read_csv(d / "positioning_transfer.csv")
                        if (d / "positioning_transfer.csv").exists()
                        else None)}
    return out


def timing_of(D: dict, cond: str) -> tuple[float, float]:
    t = D["timing"]
    if t is None:
        return np.nan, np.nan
    r = t[t["condition"] == cond]
    if not len(r):
        return np.nan, np.nan
    return float(r["study_ms_per_fp"].iloc[0]), float(r["opt_ms_per_fp"].iloc[0])


def comparison(DS: list[dict]) -> pd.DataFrame:
    rows = []
    for D in DS:
        s = D["summary"]
        prim = next(iter(s["tests"]))
        st_all, op_all = timing_of(D, "baseline_all")
        last = D["pos"]["stages"][-1]["stage"]
        base = {"dataset": D["key"], "dataset_name": SHORT[D["key"]],
                "n_buildings": s["n_buildings"],
                "n_floor_classes": s["n_building_floor_classes"],
                "n_train": s["train"]["rows"]}
        for tname, g in D["abl"].groupby("test_set", sort=False):
            timed = tname == prim
            for stage, method, ms in (("S0", "k-NN nghiên cứu (S0)", st_all),
                                      (last, f"Tối ưu PHASE I3 ({last})",
                                       op_all)):
                r = g[g["stage"] == stage].iloc[0]
                rows.append({**base, "test_set": tname,
                             "n_test": int(r["test_n_test"]),
                             "method": method, "wap_set": "all",
                             "n_waps": s["n_wap_columns"],
                             "config": r["config"],
                             **{k: r[f"test_{k}"] for k in (
                                 "building_accuracy", "floor_accuracy",
                                 "joint_accuracy", "mean_err_m",
                                 "median_err_m", "p75_err_m", "p90_err_m",
                                 "p95_err_m")},
                             "ms_per_fp": ms if timed else np.nan,
                             "huim_minutil_pct": np.nan,
                             "huim_mining_s": np.nan})
            T = D["transfer"]
            if T is not None and (T["test_set"] == tname).any():
                r = T[T["test_set"] == tname].iloc[0]
                rows.append({**base, "test_set": tname,
                             "n_test": int(r["n_test"]),
                             "method": TRANSFER, "wap_set": "all",
                             "n_waps": s["n_wap_columns"],
                             "config": r["config"],
                             **{k: r[k] for k in (
                                 "building_accuracy", "floor_accuracy",
                                 "joint_accuracy", "mean_err_m",
                                 "median_err_m", "p75_err_m", "p90_err_m",
                                 "p95_err_m")},
                             "ms_per_fp": np.nan, "huim_minutil_pct": np.nan,
                             "huim_mining_s": np.nan})
            C = D["cond"]
            for _, r in C[(C["test_set"] == tname)
                          & (C["family"] == "huim_union")].iterrows():
                _st, ms = timing_of(D, r["condition"])
                h = D["huim"]
                hr = h[h["run_tag"] == r["condition"].split("__", 1)[1]]
                rows.append({**base, "test_set": tname,
                             "n_test": int(r["opt_n_test"]),
                             "method": f"Tối ưu + HUIM Model "
                                       f"{MODEL[r['utility_model']]}",
                             "wap_set": r["condition"],
                             "n_waps": int(r["n_waps"]),
                             "config": D["pos"]["selected_label"],
                             **{k: r[f"opt_{k}"] for k in (
                                 "building_accuracy", "floor_accuracy",
                                 "joint_accuracy", "mean_err_m",
                                 "median_err_m", "p75_err_m", "p90_err_m",
                                 "p95_err_m")},
                             "ms_per_fp": ms if timed else np.nan,
                             "huim_minutil_pct": float(r["rel_minutil_pct"]),
                             "huim_mining_s": float(hr["runtime_s"].iloc[0])
                             if len(hr) else np.nan})
    return pd.DataFrame(rows)


def huim_vs_controls(DS: list[dict]) -> pd.DataFrame:
    rows = []
    for D in DS:
        C = D["cond"]
        for tname, g in C.groupby("test_set", sort=False):
            allw = g[g["condition"] == "baseline_all"].iloc[0]
            for _, r in g[g["family"].str.startswith("huim")].iterrows():
                n = int(r["n_waps"])
                def opt(c):
                    x = g[g["condition"] == c]
                    return float(x["opt_mean_err_m"].iloc[0]) if len(x) else np.nan
                rows.append({"dataset": D["key"], "dataset_name": SHORT[D["key"]],
                             "test_set": tname, "condition": r["condition"],
                             "family": r["family"],
                             "utility_model": MODEL[r["utility_model"]],
                             "minutil_pct": float(r["rel_minutil_pct"]),
                             "n_waps": n,
                             "feature_reduction_pct": float(
                                 r["feature_reduction_pct"]),
                             "opt_mean_err_huim_m": float(r["opt_mean_err_m"]),
                             "opt_mean_err_top_mi_m": opt(
                                 f"control_top_mi__n{n}"),
                             "opt_mean_err_top_support_m": opt(
                                 f"control_top_support__n{n}"),
                             "opt_mean_err_all_waps_m": float(
                                 allw["opt_mean_err_m"]),
                             "opt_floor_acc_huim": float(
                                 r["opt_floor_accuracy"]),
                             "opt_floor_acc_all_waps": float(
                                 allw["opt_floor_accuracy"])})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- figures
def _style() -> None:
    plt.rcParams.update({"font.family": "serif",
                         "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "font.size": 9.5, "axes.grid": True,
                         "grid.alpha": 0.3, "axes.spines.top": False,
                         "axes.spines.right": False, "legend.frameon": False,
                         "savefig.dpi": 200, "savefig.bbox": "tight"})


def fig40(cmp: pd.DataFrame) -> None:
    """Mean error, floor accuracy and time per test set: study k-NN (gray)
    against the optimised model (blue)."""
    base = cmp[cmp["wap_set"] == "all"].copy()
    base["row"] = base["dataset_name"] + " · " + base["test_set"]
    s0 = base[base["method"].str.startswith("k-NN")].set_index("row")
    op = base[base["method"].str.startswith("Tối ưu")].set_index("row")
    tr = base[base["method"] == TRANSFER].set_index("row")
    rows = list(dict.fromkeys(s0.index))
    y = np.arange(len(rows))[::-1]
    h = 0.27
    _style()
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 0.55 * len(rows) + 1.8),
                           gridspec_kw={"wspace": 0.08})
    # floor accuracies sit within a point of 100%, so the panel shows the
    # complement on a zero-based axis: the share of fingerprints put on the
    # wrong floor
    panels = [("mean_err_m", "Sai số trung bình (m)", "{:.2f}", False),
              ("floor_accuracy", "Tỉ lệ đoán sai tầng (%) = 100 - độ chính "
                                 "xác tầng", "{:.2f}", False),
              ("ms_per_fp", "Thời gian định vị (ms / fingerprint, log)",
               "{:.3g}", True)]
    for a, (col, title, fmt, log) in zip(ax, panels):
        series = [(h, s0, GRAY, "k-NN nghiên cứu (S0)"),
                  (0.0, tr.reindex(rows), ORANGE, TRANSFER),
                  (-h, op, BLUE, "Tối ưu lại PHASE I3 trên bộ đó")]
        for off, src, color, lab in series:
            if col == "ms_per_fp" and src is not s0 and src is not op:
                continue
            v = src.loc[rows, col].to_numpy(dtype=float)
            if col == "floor_accuracy":
                multi = s0.loc[rows, "n_floor_classes"].to_numpy() > 1
                v = np.where(multi, (1 - v) * 100, np.nan)
            ok = ~np.isnan(v)
            a.barh(y[ok] + off, v[ok], h, color=color, label=lab)
            for yy, vv in zip(y[ok] + off, v[ok]):
                a.text(vv, yy, " " + fmt.format(vv), va="center", fontsize=7)
        if col == "floor_accuracy":
            single = s0.loc[rows, "n_floor_classes"].to_numpy() == 1
            for yy in y[single]:
                a.text(0.02, yy, "1 tầng - không áp dụng",
                       transform=a.get_yaxis_transform(), va="center",
                       fontsize=7.5, color="#52514e")
        if log:
            a.set_xscale("log")
            if np.all(np.isnan(s0.loc[rows, col].to_numpy(dtype=float))):
                a.text(0.5, 0.5, "chưa đo", transform=a.transAxes,
                       ha="center")
        else:
            a.set_xlim(left=0)
            a.set_xlim(right=a.get_xlim()[1] * 1.15)
        a.set_ylim(-0.7, len(rows) - 0.3)
        a.set_yticks(y)
        a.set_yticklabels(rows if a is ax[0] else [""] * len(rows))
        a.set_title(title, fontsize=10)
        a.grid(axis="y", visible=False)
    ax[0].legend(loc="lower right", fontsize=8)
    fig.text(0.01, -0.02,
             "Mô hình tối ưu được chọn trên các fold nhóm của tập huấn luyện "
             "(không dùng tập test); mỗi tập test chỉ dùng một lần. Thời gian "
             "đo trên tập test chính của mỗi bộ dữ liệu.", fontsize=7.5,
             color="#52514e")
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "fig40_multi_dataset_comparison.png")
    plt.close(fig)
    base.drop(columns=["row"]).to_csv(
        FIG / "fig40_multi_dataset_comparison.csv", index=False)


def fig41(hv: pd.DataFrame) -> None:
    """Optimised mean error of each HUIM union set against the top-MI and
    top-support sets of the same size (primary test set of each dataset)."""
    d = hv[hv["family"] == "huim_union"].copy()
    prim = d.groupby("dataset")["test_set"].transform("first")
    d = d[d["test_set"] == prim]
    if not len(d):
        return
    d["row"] = (d["dataset_name"] + " · Model " + d["utility_model"] + " ("
                + d["n_waps"].astype(str) + " WAP, minUtil "
                + d["minutil_pct"].map(lambda v: f"{v:g}") + "%)")
    y = np.arange(len(d))[::-1]
    _style()
    fig, a = plt.subplots(figsize=(9.5, 0.42 * len(d) + 1.4))
    for col, color, mk, lab in (
            ("opt_mean_err_huim_m", BLUE, "o", "Tập WAP do HUIM chọn"),
            ("opt_mean_err_top_mi_m", ORANGE, "s",
             "Top-n theo mutual information"),
            ("opt_mean_err_top_support_m", AQUA, "D",
             "Top-n theo số lần phát hiện")):
        a.scatter(d[col], y, s=42, color=color, marker=mk, label=lab,
                  zorder=3, edgecolor="white", linewidth=1)
    a.scatter(d["opt_mean_err_all_waps_m"], y, s=60, marker="|",
              color="#0b0b0b", label="Mọi WAP", zorder=4)
    a.set_yticks(y)
    a.set_yticklabels(d["row"], fontsize=7.8)
    a.set_xlabel("Sai số trung bình của mô hình tối ưu (m)")
    a.set_xlim(left=0)
    a.grid(axis="y", visible=False)
    a.legend(fontsize=7.8, loc="lower right")
    a.set_title("HUIM so với đối chứng cùng số WAP (tập test chính)",
                fontsize=10)
    fig.savefig(FIG / "fig41_multi_dataset_huim_vs_controls.png")
    plt.close(fig)
    d.drop(columns=["row"]).to_csv(
        FIG / "fig41_multi_dataset_huim_vs_controls.csv", index=False)


CURVE_TOL = 1.10     # "as good as all WAPs" = within 10% of its mean error


def curve_table(DS: list[dict]) -> pd.DataFrame:
    """Mean optimised error per family and budget on the primary test set;
    random = mean of its seeds; HUIM per utility model."""
    out = []
    for D in DS:
        c = D["curve"]
        if c is None:
            continue
        c = c.copy()
        c["series"] = np.where(c["family"] == "huim_topn",
                               "HUIM " + c["utility_model"].map(MODEL).fillna(""),
                               c["family"])
        g = (c[c["family"] != "baseline"]
             .groupby(["series", "budget_n"], as_index=False)
             [["opt_mean_err_m", "opt_floor_accuracy"]].mean())
        allw = c[c["condition"] == "baseline_all"].iloc[0]
        g["dataset"], g["dataset_name"] = D["key"], SHORT[D["key"]]
        g["test_set"] = c["test_set"].iloc[0]
        g["all_waps_mean_err_m"] = allw["opt_mean_err_m"]
        g["all_waps_floor_accuracy"] = allw["opt_floor_accuracy"]
        g["n_wap_columns"] = D["summary"]["n_wap_columns"]
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


SERIES = [("HUIM B", BLUE, "o", "HUIM Model B, top-n"),
          ("control_top_mi", ORANGE, "s", "Top-n theo MI"),
          ("control_top_support", AQUA, "D", "Top-n theo số lần phát hiện"),
          ("control_random", GRAY, "^", "Ngẫu nhiên (TB 3 seed)")]


def log_counts(a, values) -> None:
    """Log x-axis for AP counts with plain-number ticks (no 3x10^1 labels)."""
    a.set_xscale("log")
    lo, hi = float(np.min(values)), float(np.max(values))
    a.set_xticks([t for t in (1, 2, 5, 10, 20, 50, 100, 200, 500)
                  if lo * 0.9 <= t <= hi * 1.1])
    a.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    a.xaxis.set_minor_formatter(plt.NullFormatter())


def fig42(cv: pd.DataFrame) -> None:
    if not len(cv):
        return
    keys = list(dict.fromkeys(cv["dataset"]))
    _style()
    n = len(keys)
    ncol = min(3, n)
    nrow = int(np.ceil(n / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(5.0 * ncol, 3.5 * nrow),
                            squeeze=False, gridspec_kw={"hspace": 0.45,
                                                        "wspace": 0.25})
    for a, key in zip(axs.flat, keys):
        g = cv[cv["dataset"] == key]
        for ser, color, mk, lab in SERIES:
            h = g[g["series"] == ser].sort_values("budget_n")
            if len(h):
                a.plot(h["budget_n"], h["opt_mean_err_m"], color=color, lw=2,
                       marker=mk, ms=4.5, label=lab)
        a.axhline(g["all_waps_mean_err_m"].iloc[0], color="#0b0b0b", lw=1,
                  ls=":", label="Mọi WAP")
        if g["budget_n"].max() > 30:
            log_counts(a, g["budget_n"])
        a.set_title(f"{g['dataset_name'].iloc[0]} · {g['test_set'].iloc[0]}",
                    fontsize=9.5)
        a.set_xlabel("Số WAP giữ lại")
        a.set_ylabel("Sai số TB (m)")
        a.set_ylim(bottom=0)
    for a in list(axs.flat)[n:]:
        a.set_visible(False)
    axs.flat[0].legend(fontsize=7.2, loc="upper right")
    fig.suptitle("Sai số của mô hình tối ưu theo số WAP (tập test chính)",
                 fontsize=11, y=1.0)
    fig.savefig(FIG / "fig42_multi_dataset_error_vs_waps.png")
    plt.close(fig)
    cv.to_csv(FIG / "fig42_multi_dataset_error_vs_waps.csv", index=False)


# -------------------------------------------------------------------- markdown
def pct(v) -> str:
    return "—" if pd.isna(v) else f"{100 * float(v):.2f}%"


def num(v, f="{:.2f}") -> str:
    return "—" if pd.isna(v) else f.format(float(v))


def markdown(DS: list[dict], cmp: pd.DataFrame, hv: pd.DataFrame,
             cv: pd.DataFrame) -> str:
    L = ["# So sánh HUIM-IPS trên nhiều bộ dữ liệu", "",
         "Chỉ thay bộ dữ liệu; tiền xử lý, 3 mô hình utility, EFIM, lưới "
         "minUtil, k-NN của nghiên cứu và quy trình tối ưu PHASE I3 (quy trình "
         f"đã cho {M_SEL} trên UJIIndoorLoc) giữ nguyên. Mọi số dưới đây được "
         "`src/make_multi_dataset_summary.py` đọc từ `results/multi_dataset/`.",
         ""]
    empt = DS[0]["summary"].get("empty_folders_in_dataset_root") if DS else None
    if empt:
        L += [f"Thư mục rỗng (cả trong file zip), không chạy được: "
              f"{', '.join('`' + e + '`' for e in empt)}.", ""]

    L += ["## 1. Dữ liệu", "",
          "| Bộ dữ liệu | Train | Test | Số AP (phát hiện ở train) | Vị trí train"
          " | Tòa / lớp tòa-tầng | Nhãn vị trí | Nhóm CV (PHASE I3) |",
          "|---|---|---|---|---|---|---|---|"]
    for D in DS:
        s = D["summary"]
        tests = "; ".join(f"{n}: {v['rows']} dòng, {v['positions']} vị trí "
                          f"({v['positions_also_in_training']} có trong train)"
                          for n, v in s["tests"].items())
        L.append(f"| {SHORT[D['key']]} | {s['train']['rows']} | {tests} | "
                 f"{s['n_wap_columns']} ({s['train']['aps_ever_detected']}) | "
                 f"{s['train']['positions']} | {s['n_buildings']} / "
                 f"{s['n_building_floor_classes']} | {s['location_label']} | "
                 f"{s['cv_group'].split(' - ')[0]} |")
    L += ["", "Nguồn dữ liệu:", ""]
    for D in DS:
        L.append(f"- **{SHORT[D['key']]}**: {SOURCES[D['key']]}.")
    L += ["", "Làm sạch / ghi chú dữ liệu:", ""]
    for D in DS:
        for c in D["summary"]["cleaning"]:
            L.append(f"- **{SHORT[D['key']]}**: {c}")
    L.append("")

    L += ["## 2. Độ chính xác tòa, tầng, khoảng cách và thời gian (mọi WAP)",
          "",
          "| Bộ dữ liệu · tập test | Phương pháp | Tòa | Tầng | Sai số TB (m) |"
          " Trung vị (m) | P90 (m) | ms / fingerprint |",
          "|---|---|---|---|---|---|---|---|"]
    allw = cmp[cmp["wap_set"] == "all"]
    for _, r in allw.iterrows():
        b = pct(r["building_accuracy"]) if r["n_buildings"] > 1 else "— (1 tòa)"
        f = (pct(r["floor_accuracy"]) if r["n_floor_classes"] > 1
             else "— (1 tầng)")
        L.append(f"| {r['dataset_name']} · {r['test_set']} | {r['method']} | "
                 f"{b} | {f} | {num(r['mean_err_m'])} | "
                 f"{num(r['median_err_m'])} | {num(r['p90_err_m'])} | "
                 f"{num(r['ms_per_fp'], '{:.3f}')} |")
    L += ["", "Cấu hình PHASE I3 được chọn (chỉ trên tập train):", ""]
    for D in DS:
        p = D["pos"]
        stg = ", ".join(f"{s['stage']} {s['dev']['mean_ground_m']:.3f} m"
                        for s in p["stages"])
        L.append(f"- **{SHORT[D['key']]}**: `{p['selected_label']}` — sai số "
                 f"dev theo giai đoạn được giữ: {stg}. k-NN nghiên cứu của bộ "
                 f"này: k={p['study_knn_config']['n_neighbors']}, "
                 f"{p['study_knn_config']['metric']}, "
                 f"{p['study_knn_config']['weights']}.")
        if "reproduces_study" in p:
            r = p["reproduces_study"]
            L.append(f"  - Kiểm tra tái lập UJI: bản chung cho "
                     f"{r['generic_mean_ground_m']:.4f} m, nghiên cứu gốc "
                     f"{r['study_mean_ground_m']:.4f} m → "
                     f"{'KHỚP' if r['match'] else 'KHÔNG KHỚP'}.")
    L.append("")

    L += ["## 3. HUIM: tập WAP được chọn, thời gian khai thác, so với đối chứng",
          "",
          "| Bộ dữ liệu · tập test | Model | Cách lấy WAP | minUtil | "
          "Số WAP (giảm) | Khai thác EFIM (s) | Sai số TB HUIM (m) | "
          "Top-MI cùng n | Top-support cùng n | Mọi WAP | "
          "Tầng HUIM / mọi WAP |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in hv.iterrows():
        tag = r["condition"].split("__", 1)[1]
        if r["family"] == "huim_topn":
            tag = tag.rsplit("__n", 1)[0]
        h = next(D["huim"] for D in DS if D["key"] == r["dataset"])
        hr = h[h["run_tag"] == tag]
        mine = float(hr["runtime_s"].iloc[0]) if len(hr) else np.nan
        multi = cmp[(cmp["dataset"] == r["dataset"])]["n_floor_classes"].iloc[0] > 1
        fl = (f"{pct(r['opt_floor_acc_huim'])} / {pct(r['opt_floor_acc_all_waps'])}"
              if multi else "—")
        how = "union" if r["family"] == "huim_union" else "top-n"
        L.append(f"| {r['dataset_name']} · {r['test_set']} | {r['utility_model']}"
                 f" | {how} | {r['minutil_pct']:g}% | {r['n_waps']} "
                 f"({r['feature_reduction_pct']:.1f}%) | {num(mine)} | "
                 f"{num(r['opt_mean_err_huim_m'])} | "
                 f"{num(r['opt_mean_err_top_mi_m'])} | "
                 f"{num(r['opt_mean_err_top_support_m'])} | "
                 f"{num(r['opt_mean_err_all_waps_m'])} | {fl} |")
    L.append("")

    if len(cv):
        L += ["## 4. Cần giữ bao nhiêu WAP? (mô hình tối ưu, tập test chính)", "",
              f"Số WAP nhỏ nhất (trong các ngân sách top-n đã thử) mà sai số TB "
              f"không vượt quá {CURVE_TOL:g} x sai số khi dùng mọi WAP.", "",
              "| Bộ dữ liệu · tập test | Mọi WAP: số WAP / sai số (m) | "
              "HUIM A | HUIM B | HUIM C | Top-MI | Top-support | Ngẫu nhiên |",
              "|---|---|---|---|---|---|---|---|"]
        for key in dict.fromkeys(cv["dataset"]):
            g = cv[cv["dataset"] == key]
            lim = CURVE_TOL * g["all_waps_mean_err_m"].iloc[0]
            cells = []
            for ser in ("HUIM A", "HUIM B", "HUIM C", "control_top_mi",
                        "control_top_support", "control_random"):
                h = g[(g["series"] == ser) & (g["opt_mean_err_m"] <= lim)]
                cells.append("không đạt" if not len(h) else
                             f"{int(h['budget_n'].min())} WAP "
                             f"({h.sort_values('budget_n')['opt_mean_err_m'].iloc[0]:.2f} m)")
            L.append(f"| {g['dataset_name'].iloc[0]} · {g['test_set'].iloc[0]} | "
                     f"{g['n_wap_columns'].iloc[0]} / "
                     f"{g['all_waps_mean_err_m'].iloc[0]:.2f} | "
                     + " | ".join(cells) + " |")
        L.append("")
    return "\n".join(L)


def efim_tests() -> dict:
    """Run the study's correctness tests (EFIM against the brute-force oracle,
    utility models) once and record the counts, so the documents can quote
    them instead of a typed number."""
    import re
    import subprocess
    from datetime import datetime, timezone
    from utils import PROJECT_ROOT, dump_json
    r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q",
                        "-p", "no:cacheprovider"], cwd=PROJECT_ROOT,
                       capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    count = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|"
                                              r"errors?)", tail)}
    out = {"command": "python -m pytest tests -q", "summary_line": tail,
           "returncode": r.returncode, **count,
           "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    dump_json(out, ROOT / "efim_tests.json")
    return out


def main() -> None:
    DS = [D for D in (load_ds(k) for k in ORDER) if D is not None]
    if not DS:
        raise SystemExit("no finished dataset in results/multi_dataset")
    cmp = comparison(DS)
    hv = huim_vs_controls(DS)
    cmp.to_csv(ROOT / "comparison.csv", index=False)
    hv.to_csv(ROOT / "huim_vs_controls.csv", index=False)
    cv = curve_table(DS)
    if len(cv):
        cv.to_csv(ROOT / "error_vs_waps.csv", index=False)
    fig40(cmp)
    fig41(hv)
    fig42(cv)
    (ROOT / "TONG_HOP_DA_DATASET.md").write_text(markdown(DS, cmp, hv, cv),
                                                encoding="utf-8")
    t = efim_tests()
    print(f"{len(DS)} datasets: {', '.join(D['key'] for D in DS)}; tests: "
          f"{t['summary_line']}")


if __name__ == "__main__":
    main()
