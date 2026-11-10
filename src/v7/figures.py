"""Figures of the V7 report, drawn from the CSV tables written by analysis.py (no number is typed in here).

Style: the data-viz skill's reference palette - categorical slots in fixed order (blue, orange, aqua), muted
grey for context series, hairline solid gridlines, 2 px lines, bars <= 24 px with value labels at the tip,
text in ink tokens (never in the series colour), a legend for two or more series.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import PROJECT_ROOT  # noqa: E402

DATA = PROJECT_ROOT / "BAOCAO_V7" / "so_lieu"
FIG = PROJECT_ROOT / "BAOCAO_V7" / "bieu_do"
SURF, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", MUTED
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "axes.unicode_minus": False, "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "axes.facecolor": SURF, "text.color": INK})
vi = FuncFormatter(lambda v, _p: f"{v:g}".replace(".", ","))     # Vietnamese decimal comma on axes


def fmt(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def axes(figsize=(8.2, 4.8), grid="y"):
    fig, ax = plt.subplots(figsize=figsize, dpi=160)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(length=0, colors=INK2, labelsize=9)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.8, ls="-")
        ax.set_axisbelow(True)
    return fig, ax


def titled(fig, ax, title: str, sub: str) -> None:
    fig.text(0.012, 0.975, title, fontsize=12.5, fontweight="bold", color=INK, va="top")
    fig.text(0.012, 0.925, sub, fontsize=9, color=INK2, va="top")
    fig.subplots_adjust(top=0.84)


def save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("saved", name, flush=True)


def cdf_plot(df: pd.DataFrame, cols: list[tuple[str, str, str]], mask, title: str, sub: str, name: str, xmax: float = 40) -> None:
    fig, ax = axes(grid="both")
    for col, label, color in cols:
        e = np.sort(df.loc[mask, col].to_numpy())
        y = np.arange(1, len(e) + 1) / len(e)
        s = f"{label} - TB {fmt(e.mean())} · trung vị {fmt(np.median(e))} · P90 {fmt(np.percentile(e, 90), 1)} m"
        ax.plot(e, y, color=color, lw=1.8, solid_capstyle="round", label=s)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("sai số định vị (m)", color=INK2, fontsize=9.5)
    ax.set_ylabel("tỷ lệ truy vấn có sai số ≤ x", color=INK2, fontsize=9.5)
    ax.xaxis.set_major_formatter(vi)
    ax.yaxis.set_major_formatter(vi)
    leg = ax.legend(loc="lower right", frameon=False, fontsize=8.6, labelcolor=INK2)
    titled(fig, ax, title, sub)
    save(fig, name)


def paired_hist(df: pd.DataFrame, a: str, b: str, mask, title: str, sub: str, name: str, ref: str = "V6*") -> None:
    d = (df.loc[mask, a] - df.loc[mask, b]).to_numpy()           # positive = b (V7) better
    fig, ax = axes(grid="y")
    edges = np.arange(-20, 20.01, 1.0)
    h, _ = np.histogram(np.clip(d, -19.99, 19.99), edges)
    ctr = (edges[:-1] + edges[1:]) / 2
    ax.bar(ctr[ctr < 0], h[ctr < 0], width=0.86, color=ORANGE, label=f"V7 kém hơn {ref}: {int((d < -0.5).sum()):,} truy vấn (> 0,5 m)".replace(",", "."))
    ax.bar(ctr[ctr >= 0], h[ctr >= 0], width=0.86, color=BLUE, label=f"V7 tốt hơn {ref}: {int((d > 0.5).sum()):,} truy vấn (> 0,5 m)".replace(",", "."))
    ax.set_ylim(0, h.max() * 1.18)
    ax.set_xlabel(f"sai số {ref} − sai số V7 (m); dương = V7 chính xác hơn (cắt ở ±20 m)", color=INK2, fontsize=9.5)
    ax.set_ylabel("số truy vấn", color=INK2, fontsize=9.5)
    ax.legend(frameon=False, fontsize=8.8, labelcolor=INK2, loc="upper left")
    titled(fig, ax, title, sub)
    save(fig, name)


def grouped_bars(labels: list[str], series: list[tuple[str, list[float], str]], title: str, sub: str, name: str, ylabel: str,
                 horizontal: bool = False, figsize=(8.2, 4.6), legend_below: bool = False) -> None:
    fig, ax = axes(figsize=figsize, grid="x" if horizontal else "y")
    n = len(series)
    w = 0.36 if n == 2 else 0.8 / n
    x = np.arange(len(labels))
    for i, (lab, vals, col) in enumerate(series):
        pos = x + (i - (n - 1) / 2) * (w + 0.04)
        bars = (ax.barh if horizontal else ax.bar)(pos, vals, w, color=col, label=lab)
        for p, v in zip(pos, vals):
            if horizontal:
                ax.text(v + 0.12, p, fmt(v), va="center", fontsize=7.6, color=INK2)
            else:
                ax.text(p, v + 0.12, fmt(v), ha="center", va="bottom", fontsize=8, color=INK2)
    if horizontal:
        ax.set_yticks(x, labels)
        ax.invert_yaxis()
        ax.set_xlabel(ylabel, color=INK2, fontsize=9.5)
    else:
        ax.set_xticks(x, labels)
        ax.set_ylabel(ylabel, color=INK2, fontsize=9.5)
    (ax.xaxis if horizontal else ax.yaxis).set_major_formatter(vi)
    if legend_below:
        ax.legend(frameon=False, fontsize=8.8, labelcolor=INK2, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    else:
        ax.legend(frameon=False, fontsize=8.8, labelcolor=INK2, loc="lower right" if horizontal else "upper left")
    titled(fig, ax, title, sub)
    save(fig, name)


def main() -> None:
    dev = pd.read_csv(DATA / "dev_per_query.csv")
    inf = dev.informative
    final = "err_C_rel_absL3" if "err_C_rel_absL3" in dev else "err_B_base"
    nm = "V7 cuối (rel + abs mức-3)" if final.endswith("absL3") else "V7-B"
    cdf_plot(dev, [("err_V4", "V4", GREY), ("err_V6*", "V6* (V6, float64)", BLUE), ("err_B_base", "V7-B (đặc trưng V6)", AQUA),
                   (final, nm, ORANGE)] if "err_B_base" in dev else [("err_V6*", "V6*", BLUE), (final, nm, ORANGE)], inf,
             "Phân bố sai số trên dev (OOF, theo điện thoại)", "19.861 vân tay có ≥ 1 AP, 6 fold GroupKFold theo PHONEID; đường càng cao-trái càng tốt",
             "F1_cdf_dev.png")
    paired_hist(dev, "err_V6*", final, inf, "Từng truy vấn: V7 so với V6* (dev, OOF)",
                "Chênh lệch sai số trên 19.861 truy vấn có thông tin", "F2_cai_thien_tung_truy_van_dev.png")
    # floor right / wrong
    fl = pd.read_csv(DATA / "dev_by_floor_correct.csv").set_index(["group", "model"])["mean"]
    grouped_bars(["đúng tầng", "sai tầng"], [("V6*", [fl[("floor_right", "V6*")], fl[("floor_wrong", "V6*")]], BLUE),
                                              (nm, [fl[("floor_right", final[4:])], fl[("floor_wrong", final[4:])]], ORANGE)],
                 "Sai số trung bình theo kết quả chọn tầng (dev, OOF)", "Tầng do bằng chứng HUI quyết định, giống nhau ở V6 và V7",
                 "F3_sai_so_theo_tang_dev.png", "sai số trung bình (m)", figsize=(6.6, 4.4))
    ph = pd.read_csv(DATA / "dev_by_phone.csv").sort_values("V6*", ascending=False)
    grouped_bars([f"điện thoại {int(p)} (n={int(n)})" for p, n in zip(ph.phone, ph.n)], [("V6*", ph["V6*"].tolist(), BLUE),
                                                                                      (nm, ph["V7"].tolist(), ORANGE)],
                 "Sai số trung bình theo điện thoại (dev, OOF)", "Mỗi điện thoại là một nhóm được giữ ra ngoài khi huấn luyện",
                 "F4_sai_so_theo_dien_thoai_dev.png", "sai số trung bình (m)", horizontal=True, figsize=(8.2, 7.2))
    cs = pd.read_csv(DATA / "dev_candidate_selection.csv")
    grouped_bars(["dưới 3 m", "dưới 5 m", "dưới 10 m"],
                 [(r.nguon, [100 * r.duoi_3m, 100 * r.duoi_5m, 100 * r.duoi_10m], c) for r, c in zip(cs.itertuples(), [GREY, AQUA, BLUE, ORANGE])],
                 "Tỷ lệ truy vấn có (ô / tọa độ) cách vị trí thật dưới ngưỡng - dev", "Ô tiên tri = ô gần nhất trong 30 ứng viên HUI (chỉ để phân tích, dùng nhãn thật)",
                 "F5_hieu_qua_chon_o_ung_vien_dev.png", "% truy vấn", legend_below=True)
    s = pd.read_csv(DATA / "dev_summary_informative.csv").set_index("model")
    order = [("V4", "V4"), ("V6*", "V6* (V6, float64)"), ("V7-A", "V7-A hợp nhất thích ứng"), ("B_base", "V7-B tối ưu trực tiếp"),
             ("C_rel", "V7-C1 + HUI rel"), ("C_rel_absL3", "V7-C2 + HUI abs mức-3"), ("D_hier", "V7-D + HUI cấp tầng")]
    order = [(k, v) for k, v in order if k in s.index]
    fig, ax = axes(figsize=(8.2, 3.9), grid="x")
    ys = np.arange(len(order))
    cols = [GREY, BLUE] + [ORANGE] * (len(order) - 2)
    ax.barh(ys, [s.loc[k, "mean"] for k, _ in order], 0.52, color=cols)
    for y, (k, _l) in zip(ys, order):
        ax.text(s.loc[k, "mean"] + 0.06, y, f"{fmt(s.loc[k, 'mean'])} m", va="center", fontsize=9, color=INK2)
    ax.set_yticks(ys, [l for _k, l in order])
    ax.invert_yaxis()
    ax.set_xlim(0, max(s["mean"]) * 1.12)
    ax.set_xlabel("sai số trung bình dev (m), OOF", color=INK2, fontsize=9.5)
    ax.xaxis.set_major_formatter(vi)
    titled(fig, ax, "Cắt bỏ thành phần (ablation) trên dev", "Mỗi thanh thêm đúng một thay đổi so với thanh trước; vân tay có thông tin, OOF theo điện thoại", )
    save(fig, "F6_ablation_dev.png")
    if (DATA / "test_per_query.csv").exists():
        te = pd.read_csv(DATA / "test_per_query.csv")
        tfinal = final
        tcols = [("err_V4", "V4", GREY), ("err_V6", "V6", BLUE)] + ([("err_B_base", "V7-B", AQUA)] if "err_B_base" in te else []) + [(tfinal, nm, ORANGE)]
        cdf_plot(te, tcols, np.ones(len(te), bool), "Phân bố sai số trên tập kiểm tra validationData",
                 "1.111 vân tay, 11 điện thoại (9 chưa từng thấy); tập này đã được dùng nhiều lần từ V1 đến V6", "F7_cdf_test.png")
        paired_hist(te, "err_V6", tfinal, np.ones(len(te), bool), "Từng truy vấn: V7 so với V6 (validationData)", "Chênh lệch sai số trên 1.111 vân tay; V6 = dự đoán đã lưu của V6 (6,866 m)", "F8_cai_thien_tung_truy_van_test.png", ref="V6")
        fr = pd.read_csv(DATA / "test_by_floor_right.csv").set_index("model")["mean"]
        fw = pd.read_csv(DATA / "test_by_floor_wrong.csv").set_index("model")["mean"]
        grouped_bars(["đúng tầng", "sai tầng"], [("V6", [fr["V6"], fw["V6"]], BLUE), (nm, [fr[tfinal[4:]], fw[tfinal[4:]]], ORANGE)],
                     "Sai số trung bình theo kết quả chọn tầng (validationData)", "Cùng quy tắc chọn tầng bằng HUI ở V6 và V7", "F9_sai_so_theo_tang_test.png",
                     "sai số trung bình (m)", figsize=(6.6, 4.4))
        tp = pd.read_csv(DATA / "test_by_phone.csv").sort_values("V6", ascending=False)
        grouped_bars([f"điện thoại {int(p)} (n={int(n)})" for p, n in zip(tp.phone, tp.n)], [("V6", tp["V6"].tolist(), BLUE), (nm, tp["V7"].tolist(), ORANGE)],
                     "Sai số trung bình theo điện thoại (validationData)", "Điện thoại 13 và 14 cũng có trong tập huấn luyện; 9 điện thoại còn lại chưa từng thấy",
                     "F10_sai_so_theo_dien_thoai_test.png", "sai số trung bình (m)", horizontal=True, figsize=(8.2, 5.0))


if __name__ == "__main__":
    main()
