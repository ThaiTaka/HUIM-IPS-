"""Academic illustrations for the slide deck, drawn with matplotlib shapes.

No copyrighted imagery is used: every figure is generated from primitives.
Style is deliberately plain - thin strokes, one accent colour, serif labels - so
the deck stays austere rather than decorative.

Two constraints learned the hard way and now enforced here:

1. Times New Roman does not contain several mathematical glyphs (EMPTY SET,
   PRECEDES, ELEMENT OF, N-ARY SUMMATION). Rendering them produces tofu boxes,
   so this module uses only characters Times New Roman actually has. The
   formulas that genuinely need those symbols live in the Word report, where
   they are typed as text rather than drawn.
2. Boxes are sized from the text they hold - `box()` takes the number of lines
   and the font size and grows accordingly - because a box sized by eye
   overflows as soon as the text changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import FIGURES, RESULTS, get_logger, load_json

LOG = get_logger("diagrams", "diagrams.log")

INK = "#1a1a1a"
ACCENT = "#8c2d04"
BLUE = "#1f3b73"
GREEN = "#145a32"
GREY = "#8a8a8a"
FAINT = "#d6d6d6"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})


def canvas(w_in: float, h_in: float):
    """Coordinate system: x in [0,100], y scaled to keep squares square."""
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    hy = 100.0 * h_in / w_in
    ax.set_xlim(0, 100)
    ax.set_ylim(0, hy)
    ax.axis("off")
    return fig, ax, hy


def box(ax, cx, cy, w, text, fs=9.0, ec=INK, fc="white", lw=1.1, tc=None,
        bold=False, pad_lines=0.9, line_h=None, aspect=1.0):
    """Centred rounded box whose height follows the line count.

    `aspect` converts font points to y-units for this canvas: callers pass the
    canvas height ratio so text never spills out vertically.
    """
    lines = text.split("\n")
    lh = line_h if line_h is not None else fs * 0.195 * aspect
    h = (len(lines) + pad_lines) * lh
    ax.add_patch(mp.FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                   boxstyle="round,pad=0.35,rounding_size=1.2",
                                   fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color=tc or ec if tc is not None else (tc or INK), zorder=3,
            fontweight="bold" if bold else "normal", linespacing=1.5)
    return h


def arrow(ax, x1, y1, x2, y2, color=INK, lw=1.3, ls="-"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle=ls, shrinkA=1, shrinkB=1,
                                mutation_scale=13), zorder=4)


# ---------------------------------------------------------------------------
def cover_illustration() -> None:
    """Building -> Wi-Fi signals -> fingerprint -> HUIM -> indoor location."""
    W_IN, H_IN = 10.0, 3.6
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY  # ~1
    mid = HY * 0.52

    # --- building with an AP per floor -------------------------------------
    bx, bw = 2.0, 15.0
    by, bh = HY * 0.10, HY * 0.80
    ax.add_patch(mp.Rectangle((bx, by), bw, bh, fc="#f5f5f3", ec=INK, lw=1.3,
                              zorder=2))
    for k in range(1, 4):
        ax.plot([bx, bx + bw], [by + bh * k / 4] * 2, color=INK, lw=0.7,
                zorder=3)
    ax.text(bx + bw / 2, by + bh + HY * 0.045, "Toà nhà", ha="center",
            fontsize=10, color=INK)
    for fy in [by + bh * (0.125 + 0.25 * k) for k in range(4)]:
        ax.add_patch(mp.Circle((bx + bw - 2.0, fy), 0.55, fc=ACCENT, ec=ACCENT,
                               zorder=5))
        for r in (1.9, 3.1, 4.3):
            ax.add_patch(mp.Arc((bx + bw - 2.0, fy), r * 2, r * 2 / asp,
                                theta1=-58, theta2=58, color=ACCENT, lw=0.8,
                                alpha=0.8, zorder=4))
    px, py = bx + 4.0, by + bh * 0.37
    ax.add_patch(mp.Circle((px, py), 0.75, fc=BLUE, ec=BLUE, zorder=5))
    ax.plot([px, px], [py - 0.9, py - HY * 0.10], color=BLUE, lw=1.4, zorder=5)
    ax.text(px, py - HY * 0.165, "?", ha="center", fontsize=13, color=BLUE,
            fontweight="bold")

    # --- the four stages ----------------------------------------------------
    stages = [
        (33.0, 20.0, "Wi-Fi fingerprint\n\nWAP007:  −52 dBm\n"
                     "WAP131:  −78 dBm\nWAP442:  −91 dBm\n"
                     "517 WAP còn lại:\nkhông phát hiện", 7.6, INK),
        (55.5, 19.0, "Utility transaction\n\nitem  =  Access Point\n"
                     "q(i,T)  =  RSSI chuẩn hoá\np(i)  =  mức phân biệt\n"
                     "vị trí của AP", 7.6, BLUE),
        (78.0, 17.0, "HUIM  —  EFIM\n\nu(X)  ≥  minUtil", 8.6, ACCENT),
    ]
    for cx, w, txt, fs, col in stages:
        box(ax, cx, mid, w, txt, fs=fs, ec=col, aspect=asp)
    arrow(ax, bx + bw + 1.2, mid, 33.0 - 10.0 - 1.0, mid, color=ACCENT, lw=1.5)
    arrow(ax, 33.0 + 10.0 + 0.8, mid, 55.5 - 9.5 - 0.8, mid)
    arrow(ax, 55.5 + 9.5 + 0.8, mid, 78.0 - 8.5 - 0.8, mid)
    box(ax, 78.0, HY * 0.13, 24.0,
        "Nhóm AP hữu ích\n→  định vị toà nhà / tầng", fs=8.2, ec=GREEN,
        aspect=asp)
    arrow(ax, 78.0, mid - HY * 0.13, 78.0, HY * 0.13 + HY * 0.075, color=GREEN)

    p = FIGURES / "fig20_cover_illustration.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def _audit() -> dict:
    """Diagrams that state numbers read them from the audit, never hard-code."""
    return load_json(RESULTS / "data_summary.json")


def ips_workflow() -> None:
    A = _audit()["training"]
    n_wap = A["n_wap_columns_detected"]
    det = A["not_detected_probe"]["detections_per_fingerprint"]["mean"]
    sparse = A["not_detected_probe"]["share_eq_100_pct"]
    W_IN, H_IN = 9.6, 2.9
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY
    ytop, ybot = HY * 0.80, HY * 0.42
    box(ax, 16.0, ytop, 26.0, "OFFLINE  —  pha khảo sát", fs=10.5, ec=BLUE,
        fc="#eef1f7", bold=True, aspect=asp)
    box(ax, 16.0, ybot, 26.0,
        "Đi tới các điểm đã biết vị trí\nQuét Wi-Fi, ghi RSSI mọi AP\n"
        "→ cơ sở dữ liệu (vân tay → vị trí)", fs=8.2, aspect=asp)
    box(ax, 52.0, ytop, 26.0, "ONLINE  —  pha định vị", fs=10.5, ec=ACCENT,
        fc="#f8f0ec", bold=True, aspect=asp)
    box(ax, 52.0, ybot, 26.0,
        "Điện thoại quét Wi-Fi → vân tay mới\nSo khớp cơ sở dữ liệu (k-NN)\n"
        "→ vị trí dự đoán", fs=8.2, aspect=asp)
    arrow(ax, 29.5, ybot, 38.5, ybot, lw=1.5)
    ax.text(34.0, ybot + HY * 0.12, "cơ sở dữ liệu\nvân tay", ha="center",
            fontsize=7.8, color=GREY, linespacing=1.4)
    box(ax, 85.0, (ytop + ybot) / 2, 26.0,
        f"Vấn đề của bài tìm hiểu\n\n{n_wap} chiều, nhưng trung bình\n"
        f"chỉ {det:.1f} AP được phát hiện\n"
        f"→ {sparse:.1f}% ma trận là rỗng", fs=8.2, ec=GREEN, aspect=asp)
    arrow(ax, 65.5, (ytop + ybot) / 2, 71.5, (ytop + ybot) / 2, color=GREEN)
    p = FIGURES / "fig21_ips_workflow.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def huim_concepts() -> None:
    W_IN, H_IN = 9.6, 2.9
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY
    row1 = HY * 0.78
    items = [
        ("Item  i", "một Access Point", BLUE),
        ("Transaction  T", "một fingerprint", BLUE),
        ("q(i,T)", "RSSI đã chuẩn hoá\ninternal utility", ACCENT),
        ("p(i)", "mức phân biệt vị trí\nexternal utility", ACCENT),
    ]
    for k, (a, b, c) in enumerate(items):
        box(ax, 13.0 + k * 24.7, row1, 22.0, f"{a}\n\n{b}", fs=8.4, ec=c,
            aspect=asp)
    row2 = HY * 0.30
    box(ax, 29.0, row2, 42.0,
        "u(X)  =  tổng, trên các giao dịch chứa X,\n"
        "của tổng theo item  q(i,T) × p(i)", fs=9.4, aspect=asp)
    box(ax, 76.0, row2, 38.0, "X là High Utility Itemset\n\nkhi  u(X) ≥ minUtil",
        fs=9.4, ec=GREEN, aspect=asp)
    for k in range(4):
        arrow(ax, 13.0 + k * 24.7, row1 - HY * 0.13, 29.0, row2 + HY * 0.14,
              color=GREY, lw=0.9)
    arrow(ax, 50.5, row2, 56.5, row2, color=GREEN)
    p = FIGURES / "fig22_huim_concepts.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def uji_to_utility() -> None:
    S = load_json(RESULTS / "huim_summary.json")
    pr = S["preprocessor"]
    W_IN, H_IN = 10.4, 2.6
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY
    y = HY * 0.55
    steps = [
        ("Một dòng CSV", "520 cột WAP\n+ nhãn vị trí", INK),
        ("Lọc AP phát hiện", "giữ ô có giá trị ≠ 100\n(100 = không phát hiện)",
         BLUE),
        ("Chuẩn hoá RSSI", f"q(i,T) trong [1, {pr['q_max']}]\n"
                           f"fit trên trainingData", ACCENT),
        ("Trọng số AP", "p(i) từ mutual information\n(cũng chỉ trên training)",
         ACCENT),
        ("Utility transaction", "tập (item, q)\nsẵn sàng cho EFIM", GREEN),
    ]
    w = 17.2
    gap = (100.0 - 2.0 - len(steps) * w) / (len(steps) - 1)
    for k, (a, b, c) in enumerate(steps):
        cx = 1.0 + w / 2 + k * (w + gap)
        box(ax, cx, y, w, f"{a}\n\n{b}", fs=7.8, ec=c, aspect=asp)
        if k:
            arrow(ax, cx - w / 2 - gap + 0.4, y, cx - w / 2 - 0.4, y,
                  color=GREY, lw=1.1)
    p = FIGURES / "fig23_uji_to_utility.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def efim_tree() -> None:
    """Schematic set-enumeration tree showing what each bound prunes.

    Note the root is drawn as "{ }" rather than the empty-set glyph, and the
    item order is written "<" rather than PRECEDES, because Times New Roman has
    neither character.
    """
    W_IN, H_IN = 9.2, 4.2
    fig, ax, HY = canvas(W_IN, H_IN)
    R = 3.2
    ry = R * (100.0 / W_IN) / (HY / H_IN) * (H_IN / W_IN) * (W_IN / H_IN)
    ry = R * H_IN / W_IN * (100.0 / HY) * (HY / 100.0)  # circle stays round
    levels = {0: HY * 0.86, 1: HY * 0.66, 2: HY * 0.46, 3: HY * 0.26}
    nodes = {
        "root": (50.0, levels[0], "{ }"),
        "a": (17.0, levels[1], "{a}"), "b": (39.0, levels[1], "{b}"),
        "c": (63.0, levels[1], "{c}"), "d": (86.0, levels[1], "{d}"),
        "ab": (9.0, levels[2], "{a,b}"), "ac": (25.0, levels[2], "{a,c}"),
        "bc": (34.0, levels[2], "{b,c}"), "bd": (50.0, levels[2], "{b,d}"),
        "cd": (65.0, levels[2], "{c,d}"),
        "abc": (16.0, levels[3], "{a,b,c}"), "bcd": (42.0, levels[3], "{b,c,d}"),
    }
    pruned_su = {"d", "cd"}
    pruned_lu = {"ac", "abc"}
    hui = {"b", "bd", "bcd"}
    edges = [("root", "a"), ("root", "b"), ("root", "c"), ("root", "d"),
             ("a", "ab"), ("a", "ac"), ("b", "bc"), ("b", "bd"),
             ("c", "cd"), ("ab", "abc"), ("bc", "bcd")]
    for u, v in edges:
        x1, y1, _ = nodes[u]
        x2, y2, _ = nodes[v]
        dead = v in pruned_su or v in pruned_lu
        ax.plot([x1, x2], [y1 - 2.2, y2 + 2.2],
                color=FAINT if dead else GREY, lw=0.9,
                ls=":" if dead else "-", zorder=1)
    for key, (x, y, lab) in nodes.items():
        if key in pruned_su:
            fc, ec, tc = "#f3f3f3", GREY, GREY
        elif key in pruned_lu:
            fc, ec, tc = "white", FAINT, GREY
        elif key in hui:
            fc, ec, tc = "#eaf3ec", GREEN, GREEN
        else:
            fc, ec, tc = "white", INK, INK
        ax.add_patch(mp.Ellipse((x, y), 7.2, 7.2 * (W_IN / H_IN) * (H_IN / W_IN)
                                * 100.0 / 100.0 * (HY / HY) * 1.0 * 0 + 5.4,
                                fc=fc, ec=ec, lw=1.1, zorder=2))
        ax.text(x, y, lab, ha="center", va="center", fontsize=7.6, color=tc,
                zorder=3)
    ax.text(50.0, HY * 0.975,
            "Thứ tự item  <  = TWU tăng dần;  duyệt theo chiều sâu",
            ha="center", fontsize=9.0, color=INK)
    legend = [
        (GREEN, "#eaf3ec", "High Utility Itemset  →  xuất kết quả"),
        (GREY, "#f3f3f3", "subtree utility < minUtil  →  KHÔNG bước vào nhánh"),
        (FAINT, "white", "local utility < minUtil  →  loại item khỏi cả cây con"),
    ]
    ly = HY * 0.125
    for k, (ec, fc, txt) in enumerate(legend):
        yy = ly - k * HY * 0.060
        ax.add_patch(mp.Ellipse((6.0, yy), 3.4, 2.3, fc=fc, ec=ec, lw=1.1,
                                zorder=2))
        ax.text(9.8, yy, txt, va="center", fontsize=8.2, color=INK)
    p = FIGURES / "fig24_efim_tree.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def pipeline() -> None:
    A = _audit()
    n_tr = f"{A['training']['n_rows']:,}"
    n_va = f"{A['validation']['n_rows']:,}"
    W_IN, H_IN = 10.4, 3.1
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY
    ytop = HY * 0.95
    ymid = HY * 0.48
    ax.add_patch(mp.FancyBboxPatch((1.0, HY * 0.20), 70.0, HY * 0.66,
                                   boxstyle="round,pad=0.5,rounding_size=1.6",
                                   fc="#f6f7fa", ec=BLUE, lw=1.3, zorder=1))
    ax.text(36.0, ytop, f"trainingData  —  {n_tr} fingerprint", ha="center",
            fontsize=9.6, color=BLUE, fontweight="bold")
    steps = ["Tiền xử lý\nRSSI → q(i,T)", "Utility model\np(i) từ MI",
             "EFIM\nkhai thác HUI", "Xếp hạng HUI\n→ tập AP",
             "Huấn luyện\nk-NN"]
    w = 11.8
    gap = (69.0 - len(steps) * w) / (len(steps) - 1)
    for k, s in enumerate(steps):
        cx = 2.0 + w / 2 + k * (w + gap)
        box(ax, cx, ymid, w, s, fs=7.8, aspect=asp)
        if k:
            arrow(ax, cx - w / 2 - gap + 0.3, ymid, cx - w / 2 - 0.3, ymid,
                  color=GREY, lw=1.0)
    ax.add_patch(mp.FancyBboxPatch((76.5, HY * 0.20), 22.0, HY * 0.66,
                                   boxstyle="round,pad=0.5,rounding_size=1.6",
                                   fc="#f9f1ee", ec=ACCENT, lw=1.3, zorder=1))
    ax.text(87.5, ytop, f"validationData\n{n_va} fingerprint", ha="center",
            va="center", fontsize=9.0, color=ACCENT, fontweight="bold",
            linespacing=1.3)
    box(ax, 87.5, ymid, 19.0,
        "ĐÁNH GIÁ\nmột lần duy nhất\ncho mỗi điều kiện", fs=8.0, ec=ACCENT,
        aspect=asp)
    arrow(ax, 71.5, ymid, 77.5, ymid, color=ACCENT, lw=1.7)
    ax.plot([74.2, 74.2], [HY * 0.12, HY * 0.89], color=ACCENT, lw=1.6,
            ls="--", zorder=5)
    ax.text(50.0, HY * 0.075,
            "Không có mũi tên nào đi ngược chiều qua đường đứt nét: "
            "validationData không được dùng để fit bất cứ thứ gì",
            ha="center", fontsize=8.4, color=ACCENT)
    p = FIGURES / "fig25_pipeline.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def reverse_chain() -> None:
    O = load_json(RESULTS / "reverse_thinking_observations.json")
    o1 = O["observation_1_threshold_vs_hui_count"]
    biggest = None
    for m, r in o1.items():
        s = r.get("sharpest_step")
        if s and (biggest is None or s["to_n_huis"] > biggest[1]["to_n_huis"]):
            biggest = (m, s)
    W_IN, H_IN = 6.6, 5.0
    fig, ax, HY = canvas(W_IN, H_IN)
    asp = 100.0 / W_IN * H_IN / HY
    if biggest:
        _m, s = biggest
        top = (f"HÀNH VI QUAN SÁT ĐƯỢC\n"
               f"minUtil {s['from_pct']:g}%  →  {s['to_pct']:g}%   "
               f"({s['threshold_ratio']:g} lần)\n"
               f"số HUI  {s['from_n_huis']:,}  →  {s['to_n_huis']:,}")
    else:
        top = "HÀNH VI QUAN SÁT ĐƯỢC"
    chain = [
        (top, ACCENT, True),
        ("Bùng nổ tổ hợp\nmột nhóm k AP đạt ngưỡng\n→ cả 2^k − 1 tập con "
         "cũng đạt", INK, False),
        ("Cơ chế EFIM\nchặn trên điều khiển TÌM KIẾM,\nkhông điều khiển KẾT "
         "QUẢ", INK, False),
        ("Lý thuyết HUIM\nutility không có downward closure\n→ phải prune "
         "bằng TWU / local / subtree", INK, False),
        ("Ý NGHĨA CHO IPS\nminUtil = 'nhóm AP lớn đến đâu là một mẫu',\n"
         "KHÔNG phải núm điều chỉnh độ chính xác", GREEN, True),
    ]
    n = len(chain)
    span = HY * 0.94
    step = span / n
    y = HY - step * 0.55
    for txt, col, bold in chain:
        h = box(ax, 50.0, y, 92.0, txt, fs=8.8, ec=col, tc=col, bold=bold,
                aspect=asp)
        nxt = y - step
        if nxt > 0:
            arrow(ax, 50.0, y - h / 2 - 0.3, 50.0, nxt + h / 2 * 0.75,
                  color=col)
        y = nxt
    p = FIGURES / "fig26_reverse_thinking_chain.png"
    fig.savefig(p)
    plt.close(fig)
    LOG.info("wrote %s", p.name)


# ---------------------------------------------------------------------------
def main() -> None:
    cover_illustration()
    ips_workflow()
    huim_concepts()
    uji_to_utility()
    efim_tree()
    pipeline()
    reverse_chain()
    LOG.info("diagrams written to %s", FIGURES)


if __name__ == "__main__":
    main()
