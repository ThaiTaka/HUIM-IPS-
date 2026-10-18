"""BAOCAO/diagram: the model, from input to output, one step per figure.

Every number drawn is computed here from the saved UJIIndoorLoc model
(results/huim_only/uji/model) and one real test query, so the figures can be
checked against the data.

  d01_tong_quan.png          the whole system: offline training, online positioning
  d02_buoc1_utility.png      step 1  raw RSSI -> internal utility q(i,T) (rank)
  d03_buoc2_o_giao_dich.png  step 2  a cell = a transaction database
  d04_buoc3_efim.png         step 3  EFIM search with its two upper bounds
  d05_buoc4_mo_hinh.png      step 4  the model = HUI sets of every cell
  d06_buoc5_cham_diem.png    step 5  scoring a query against a cell's HUIs
  d07_buoc6_lam_muot_tang.png step 6 spatial smoothing and floor decision
  d08_buoc7_toa_do.png       step 7  position = weighted centroid of the best cells
  d09_giao_thuc.png          evaluation protocol and verification
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from huim_positioning import HUIPositioner, Params, internal_utility  # noqa: E402
from multi_datasets import load  # noqa: E402

OUT = ROOT / "BAOCAO" / "diagram"
MODEL = ROOT / "results" / "huim_only" / "uji"
NAVY, TEAL, RUST, GREY, LIGHT = "#1F3A5F", "#2A7F8F", "#B5532A", "#6B6B66", "#F2F4F7"
TEAL_L, NAVY_L, RUST_L = "#E3F0F2", "#E6ECF4", "#F7E9E2"
INK = "#1C1C1A"
plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 11,
                     "savefig.dpi": 220, "savefig.bbox": "tight",
                     "savefig.facecolor": "white"})


# ------------------------------------------------------------------ helpers
def vn(x, d=2):
    """Vietnamese number format: space for thousands, comma for decimals."""
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(-2, 102)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    ax.text(0, 100 * h / w, title, fontsize=14, fontweight="bold", color=NAVY,
            va="top", ha="left")
    return fig, ax


def box(ax, x, y, w, h, head, lines=(), fc=LIGHT, ec=NAVY, hc=NAVY, fs=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + 1.2, y + h - 1.3, head, fontsize=fs + 0.5, fontweight="bold", color=hc,
            va="top", ha="left")
    for i, ln in enumerate(lines):
        ax.text(x + 1.2, y + h - 4.6 - i * 3.1, ln, fontsize=fs, color=INK, va="top", ha="left")


def arrow(ax, x1, y1, x2, y2, color=GREY, text=None, ts=9.5, off=(0, 1.2)):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.4))
    if text:
        ax.text((x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1], text, fontsize=ts,
                color=color, ha="center", va="bottom")


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)


# ------------------------------------------------------------- the model
def load_model():
    sel = json.load(open(MODEL / "selection.json", encoding="utf-8"))
    M = np.load(MODEL / "model" / "huis.npz")
    cells = pd.read_csv(MODEL / "model" / "cells.csv")
    b = load("uji")
    pos = HUIPositioner(sel["theta_pct"], ground_factor=b.ground_factor)
    ip, items = M["indptr"], M["items"]
    pos.hui_items = [items[ip[k]:ip[k + 1]] for k in range(len(ip) - 1)]
    pos.hui_util, pos.hui_supp = M["utility"], M["support"]
    pos.hui_cell = M["cell_index"]
    pos.cells = cells.cell.to_numpy()
    pos.cell_xy = cells[["x", "y"]].to_numpy(float)
    pos.cell_bf = cells.building_floor.astype(str).to_numpy()
    pos.n_aps = len(b.wap_cols)
    pos._index()
    return sel, pos, cells, b


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.load(open(ROOT / "BAOCAO" / "so_lieu" / "du_lieu_bao_cao.json", encoding="utf-8"))
    sel, pos, cells, b = load_model()
    prm = Params(**sel["params"])
    te = b.tests["validationData"]
    ex = data["worked_example"]
    qi = int(np.flatnonzero(te.SRC_ROW.to_numpy() == ex["src_row"])[0])
    W = te[b.wap_cols].to_numpy(float)[qi:qi + 1]
    q = internal_utility(W, sel["utility"], -104.0, 0.0)
    P, V = pos.components(q, [(prm.gamma, prm.tau)])
    P, V = P[(prm.gamma, prm.tau)], V
    raw = P * V ** prm.beta
    S = pos.cell_scores(P, V, prm.beta, prm.sigma)
    floor = pos.floor_of(S, prm.kf)
    xy, top, a, sc = pos.locate(S, floor, prm.m, prm.p)
    assert np.allclose(xy[0], [ex["pred_x"], ex["pred_y"]]), "diagram model differs from saved predictions"
    det = np.flatnonzero(W[0] != 100)
    order = det[np.argsort(-W[0, det], kind="stable")]
    wap = b.wap_cols
    U = data["datasets"]["uji"]
    T = U["tests"]["validationData"]

    # ---------------------------------------------------------------- d01
    fig, ax = canvas(13, 7.4, "Sơ đồ tổng quát: hệ thống định vị trong nhà chỉ dùng HUIM (không k-NN)")
    ax.text(0, 52.5, "HUẤN LUYỆN (một lần, chỉ dùng trainingData)", fontsize=11, color=TEAL, fontweight="bold")
    box(ax, 0, 33, 19, 17, "Đầu vào", [f"{vn(b.train.shape[0], 0)} fingerprint", f"{len(wap)} AP (RSSI, dBm)", "toạ độ, tòa, tầng"], fc=NAVY_L)
    box(ax, 22.5, 33, 18, 17, "Bước 1", [r"utility nội $q(i,T)$", f"dạng: {sel['utility']}", "(thứ hạng cường độ)"], fc=TEAL_L, ec=TEAL, hc=TEAL)
    box(ax, 44, 33, 17, 17, "Bước 2", ["Ô = điểm tham chiếu", f"{U['model']['n_cells']} ô", "mỗi ô = 1 CSDL giao dịch"], fc=TEAL_L, ec=TEAL, hc=TEAL)
    box(ax, 64.5, 33, 16, 17, "Bước 3", ["EFIM theo từng ô", r"$\mathrm{minUtil}_c=$" + f" {sel['theta_pct']:g}% " + r"$u(D_c)$", r"chặn $lu$, $su$"], fc=TEAL_L, ec=TEAL, hc=TEAL)
    box(ax, 84, 33, 16, 17, "Bước 4: mô hình", [f"{vn(U['model']['n_huis'], 0)} HUI", "+ tâm ô, tòa – tầng", "không lưu fingerprint"], fc=RUST_L, ec=RUST, hc=RUST)
    for x1, x2 in ((19.5, 22), (41, 43.5), (61.5, 64), (81, 83.5)):
        arrow(ax, x1, 41.5, x2, 41.5)
    ax.text(0, 27.5, "ĐỊNH VỊ (cho mỗi fingerprint cần định vị)", fontsize=11, color=RUST, fontweight="bold")
    box(ax, 0, 6, 19, 18, "Truy vấn T", ["1 fingerprint mới", r"$\rightarrow$ giao dịch $q(i,T)$", "(cùng Bước 1)"], fc=NAVY_L)
    box(ax, 22.5, 6, 20, 18, "Bước 5: chấm điểm", [r"$P_c$: khớp mẫu HUI", r"$V_c$: độ phủ truy vấn", r"$\mathrm{score}_c = P_c\,V_c^{\,\beta}$"], fc=RUST_L, ec=RUST, hc=RUST)
    box(ax, 45.5, 6, 17, 18, "Bước 6", [r"làm mượt ($\sigma$)", "chọn tòa – tầng", f"(kf = {prm.kf} ô tốt nhất)"], fc=RUST_L, ec=RUST, hc=RUST)
    box(ax, 65.5, 6, 15.5, 18, "Bước 7", [f"m = {prm.m} ô tốt nhất", "của tầng đã chọn", r"$\rightarrow$ trọng tâm"], fc=RUST_L, ec=RUST, hc=RUST)
    box(ax, 84, 6, 16, 18, "Đầu ra", [r"toạ độ $(\hat x,\hat y)$", "tòa, tầng", "sai số (m)"], fc=NAVY_L)
    for x1, x2 in ((19.5, 22), (43, 45), (63, 65), (81.5, 83.5)):
        arrow(ax, x1, 15, x2, 15)
    arrow(ax, 92, 32.5, 34, 24.5, color=RUST)
    ax.text(63, 30.2, "mô hình HUI được dùng khi định vị", fontsize=10, color=RUST, ha="center", rotation=8)
    save(fig, "d01_tong_quan.png")

    # ---------------------------------------------------------------- d02
    k = min(8, len(order))
    rows = [(wap[j], int(W[0, j]), int(q[0, j])) for j in order[:k]]
    fig, ax = canvas(12, 6.2, "Bước 1 — Từ RSSI đến utility nội q(i,T)")
    ax.text(0, 45.5, f"Ví dụ thật: dòng {ex['src_row']} của validationData, {len(det)} AP được phát hiện "
            f"(hiển thị {k} AP mạnh nhất)", fontsize=10.5, color=GREY)
    ax.text(2, 40, "AP", fontweight="bold"); ax.text(18, 40, "RSSI (dBm)", fontweight="bold")
    ax.text(34, 40, "thứ hạng", fontweight="bold"); ax.text(47, 40, "q(i,T)", fontweight="bold")
    for i, (w_, r_, q_) in enumerate(rows):
        y = 36 - i * 4
        ax.text(2, y, w_); ax.text(20, y, f"{r_}"); ax.text(36, y, f"{i + 1}")
        ax.add_patch(plt.Rectangle((47, y - 0.6), q_ * 0.18, 2.6, color=TEAL, alpha=0.85))
        ax.text(47.6 + q_ * 0.18, y, f"{q_}", fontsize=10)
    ax.text(70, 40, "Định nghĩa (dạng rank)", fontweight="bold", color=NAVY)
    ax.text(70, 34.5, r"$q(i,T) = \mathrm{round}\!\left(1 + 99\,\dfrac{n_T - r_T(i)}{n_T - 1}\right)$", fontsize=13)
    ax.text(70, 27, r"$n_T$ = số AP thấy được trong T", fontsize=10.5)
    ax.text(70, 23.5, r"$r_T(i)$ = thứ hạng của AP i (mạnh nhất = 1)", fontsize=10.5)
    ax.text(70, 20, "AP không thấy: không có trong giao dịch", fontsize=10.5)
    ax.text(70, 13, "Vì sao dùng thứ hạng: điện thoại khác đọc lệch", fontsize=10.5, color=GREY)
    ax.text(70, 9.5, "cả dải vài dB nhưng giữ thứ tự mạnh–yếu.", fontsize=10.5, color=GREY)
    save(fig, "d02_buoc1_utility.png")

    # ---------------------------------------------------------------- d03
    c0 = int(top[0, 0])
    rp = pos.cells[c0]
    rows_c = np.flatnonzero(b.train.RP.to_numpy() == rp)
    Wc = b.train[wap].to_numpy(float)[rows_c]
    Qc = internal_utility(Wc, sel["utility"], -104.0, 0.0)
    runs = pd.read_csv(MODEL / "cell_runs.csv").iloc[c0]
    fig, ax = canvas(12, 6.4, "Bước 2 — Một ô (điểm tham chiếu) là một cơ sở dữ liệu giao dịch")
    ax.text(0, 47, f"Ô số {c0} (tòa {pos.cell_bf[c0].split('_')[0]}, tầng {pos.cell_bf[c0].split('_')[1]}): "
            f"{len(rows_c)} fingerprint huấn luyện = {len(rows_c)} giao dịch", fontsize=10.5, color=GREY)
    common = np.flatnonzero((Qc > 0).sum(0) >= max(2, len(rows_c) // 2))
    common = common[np.argsort(-(Qc[:, common]).sum(0))][:6]
    ax.text(1, 41, "Giao dịch", fontweight="bold")
    for j, c in enumerate(common):
        ax.text(14 + j * 9, 41, wap[c], fontsize=9.5, fontweight="bold")
    for i in range(min(7, len(rows_c))):
        y = 37 - i * 3.6
        ax.text(1, y, f"T{i + 1}", fontsize=10)
        for j, c in enumerate(common):
            v = int(Qc[i, c])
            ax.text(15 + j * 9, y, str(v) if v else "–", fontsize=10, color=INK if v else GREY)
    ax.text(1, 37 - 7 * 3.6, "…", fontsize=11)
    ax.text(70, 41, "Định nghĩa", fontweight="bold", color=NAVY)
    ax.text(70, 35, r"$D_c = \{\,T : T$ đo tại ô $c\,\}$", fontsize=12)
    ax.text(70, 29, r"$u(i,T) = q(i,T)\cdot p(i),\quad p(i)=1$", fontsize=12)
    ax.text(70, 23, r"$u(D_c) = \sum_{T\in D_c}\sum_{i\in T} u(i,T)$", fontsize=12)
    ax.text(70, 16.5, r"$\mathrm{minUtil}_c = \theta\% \cdot u(D_c)$", fontsize=12)
    ax.text(70, 10.5, r"Ô này: $u(D_c)$ = " + vn(runs.total_utility, 0) + f"; θ dùng = {vn(runs.theta_used_pct, 0)}%", fontsize=10.5)
    ax.text(70, 7, r"$\mathrm{minUtil}_c$ = " + vn(runs.abs_minutil, 1), fontsize=10.5)
    save(fig, "d03_buoc2_o_giao_dich.png")

    # ---------------------------------------------------------------- d04
    fig, ax = canvas(12, 6.4, "Bước 3 — EFIM liệt kê đầy đủ các High Utility Itemset của ô")
    nodes = {r"$\emptyset$": (30, 44), "{a}": (12, 33), "{b}": (30, 33), "{c}": (48, 33),
             "{a,b}": (6, 21), "{a,c}": (18, 21), "{b,c}": (36, 21), "{a,b,c}": (6, 9)}
    edges = [(r"$\emptyset$", "{a}"), (r"$\emptyset$", "{b}"), (r"$\emptyset$", "{c}"), ("{a}", "{a,b}"), ("{a}", "{a,c}"),
             ("{b}", "{b,c}"), ("{a,b}", "{a,b,c}")]
    pruned = {"{a,c}", "{b,c}"}
    for u_, v_ in edges:
        (x1, y1), (x2, y2) = nodes[u_], nodes[v_]
        ax.plot([x1, x2], [y1 - 1.6, y2 + 1.8], color=RUST if v_ in pruned else GREY,
                ls="--" if v_ in pruned else "-", lw=1.2)
    for n_, (x, y) in nodes.items():
        c = RUST if n_ in pruned else (TEAL if n_ in ("{a,b}", "{a,b,c}") else NAVY)
        ax.add_patch(FancyBboxPatch((x - 4.5, y - 1.8), 9, 3.6, boxstyle="round,pad=0.2",
                                    fc="white", ec=c, lw=1.3))
        ax.text(x, y, n_, ha="center", va="center", fontsize=10.5, color=c)
    ax.text(27, 15.5, r"nét đứt: nhánh bị cắt ($su < \mathrm{minUtil}$)", fontsize=9.5, color=RUST, ha="left", va="center")
    ax.text(0, 2.5, "Cây liệt kê tập theo chiều sâu, thứ tự item tăng dần theo TWU. Xanh lục: HUI tìm được.", fontsize=9.5, color=GREY)
    ax.text(60, 44, "Hai chặn trên của EFIM", fontweight="bold", color=NAVY)
    ax.text(60, 38, r"$lu(\alpha,z) = \sum_{T \ni \alpha\cup\{z\}} \left[u(\alpha,T) + re(\alpha,T)\right]$", fontsize=12)
    ax.text(60, 33.5, r"$lu < \mathrm{minUtil} \Rightarrow$ bỏ $z$ khỏi cả cây con của $\alpha$", fontsize=10)
    ax.text(60, 26.5, r"$su(\alpha,z) = \sum_{T \ni \alpha\cup\{z\}} \left[u(\alpha,T)+u(z,T)+\sum_{i\succ z} u(i,T)\right]$", fontsize=11.5)
    ax.text(60, 22, r"$su < \mathrm{minUtil} \Rightarrow$ không đi vào nhánh $\alpha \cup \{z\}$", fontsize=10)
    ax.text(60, 15, r"$\mathrm{HUI}_c = \{\,X : u(X) \geq \mathrm{minUtil}_c\,\}$", fontsize=12)
    ax.text(60, 9.5, f"Ô ví dụ: {int(runs.n_huis)} HUI, khai thác trong {vn(runs.runtime_s * 1000, 1)} ms", fontsize=10.5)
    ax.text(60, 6, f"Ngân sách mỗi ô: 10 s hoặc 10 000 HUI; vượt thì θ × 1,25", fontsize=9.5, color=GREY)
    save(fig, "d04_buoc3_efim.png")

    # ---------------------------------------------------------------- d05
    hk = np.flatnonzero(pos.hui_cell == c0)
    hk = hk[np.argsort(-pos.hui_util[hk])][:6]
    fig, ax = canvas(12, 6.0, "Bước 4 — Mô hình định vị = tập HUI của mọi ô (không lưu fingerprint nào)")
    ax.text(0, 44, f"Ô số {c0}: {len(np.flatnonzero(pos.hui_cell == c0))} HUI; 6 HUI có utility lớn nhất", fontsize=10.5, color=GREY)
    ax.text(1, 39, "Itemset X", fontweight="bold"); ax.text(58, 39, "u(X)", fontweight="bold")
    ax.text(68, 39, "s(X)", fontweight="bold"); ax.text(77, 39, r"$\bar q_c(X)=u/(s|X|)$", fontweight="bold")
    for i, kk in enumerate(hk):
        y = 35 - i * 3.8
        items = ", ".join(wap[j] for j in pos.hui_items[kk])
        ax.text(1, y, "{" + (items if len(items) < 62 else items[:59] + "…") + "}", fontsize=9.5)
        ax.text(58, y, f"{pos.hui_util[kk]:.0f}", fontsize=10)
        ax.text(68, y, f"{pos.hui_supp[kk]:.0f}", fontsize=10)
        ax.text(80, y, vn(pos.hui_util[kk] / (pos.hui_supp[kk] * len(pos.hui_items[kk])), 1), fontsize=10)
    ax.text(1, 9, f"Toàn mô hình: {U['model']['n_cells']} ô, {vn(U['model']['n_huis'], 0)} HUI; mỗi ô lưu thêm tâm " + r"$(x_c, y_c)$" + " và tòa – tầng.", fontsize=10.5)
    ax.text(1, 5, f"{U['model']['aps_in_some_hui']}/{U['model']['n_aps']} AP xuất hiện trong ít nhất một HUI.", fontsize=10.5, color=GREY)
    save(fig, "d05_buoc4_mo_hinh.png")

    # ---------------------------------------------------------------- d06
    qv = q[0]
    fig, ax = canvas(12.5, 7.2, "Bước 5 — Chấm điểm truy vấn T với các HUI của một ô")
    ax.text(0, 53, f"Cùng truy vấn dòng {ex['src_row']}, ô số {c0} (ô có điểm cao nhất)", fontsize=10.5, color=GREY)
    ax.text(1, 48, "HUI X", fontweight="bold"); ax.text(30, 48, "|X∩T|/|X|", fontweight="bold")
    ax.text(43, 48, r"$\bar q_T(X)$", fontweight="bold"); ax.text(52, 48, r"$\bar q_c(X)$", fontweight="bold")
    ax.text(61, 48, "agree", fontweight="bold")
    for i, kk in enumerate(hk[:5]):
        X = pos.hui_items[kk]
        inter = [j for j in X if qv[j] > 0]
        frac = len(inter) / len(X)
        qt = np.mean([qv[j] for j in inter]) if inter else 0.0
        qb = pos.hui_util[kk] / (pos.hui_supp[kk] * len(X))
        ag = np.exp(-abs(qt - qb) / prm.tau)
        y = 44 - i * 3.8
        ax.text(1, y, f"X{i + 1} ({len(X)} AP)", fontsize=10)
        ax.text(31, y, f"{len(inter)}/{len(X)} = {vn(frac)}", fontsize=10)
        ax.text(44, y, vn(qt, 1), fontsize=10); ax.text(53, y, vn(qb, 1), fontsize=10)
        ax.text(62, y, vn(ag, 3), fontsize=10)
    f0 = 18
    ax.text(1, f0 + 7, r"$\mathrm{agree}(X,T) = \exp\!\left(-\,|\bar q_T(X)-\bar q_c(X)|\,/\,\tau\right)$", fontsize=12.5)
    ax.text(1, f0, r"$P_c(T) = \sum_{X\in \mathrm{HUI}_c} \dfrac{u(X)}{\sum_{Y} u(Y)}\left(\dfrac{|X\cap T|}{|X|}\right)^{\gamma}\mathrm{agree}(X,T)$", fontsize=12.5)
    ax.text(1, f0 - 9, r"$V_c(T) = \dfrac{\sum_{i\in T\cap I_c} q(i,T)}{\sum_{i\in T} q(i,T)},\qquad \mathrm{score}_c(T) = P_c(T)\,V_c(T)^{\beta}$", fontsize=12.5)
    box(ax, 74, 22, 26, 27, "Ô này", [r"$P_c$ = " + vn(P[0, c0], 4), r"$V_c$ = " + vn(V[0, c0], 4),
                                      r"$\mathrm{score}_c$ = " + vn(raw[0, c0], 4), f"γ = {prm.gamma:g}; τ = {prm.tau:g}; β = {prm.beta:g}"],
        fc=RUST_L, ec=RUST, hc=RUST)
    ax.text(74, 14, r"$P_c$: truy vấn chứa bao nhiêu", fontsize=10); ax.text(74, 10.5, "khối lượng HUI của ô, đúng cường độ.", fontsize=10)
    ax.text(74, 5.5, r"$V_c$: phần truy vấn được", fontsize=10); ax.text(74, 2, "các HUI của ô giải thích.", fontsize=10)
    save(fig, "d06_buoc5_cham_diem.png")

    # ---------------------------------------------------------------- d07
    floors = np.unique(pos.cell_bf)
    fsc = [np.sort(S[0, pos.cell_bf == f])[::-1][:prm.kf].mean() for f in floors]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"wspace": 0.28})
    fig.suptitle("Bước 6 — Làm mượt không gian và chọn tòa–tầng", x=0.05, ha="left", fontsize=14,
                 fontweight="bold", color=NAVY, y=1.02)
    a1.set_title(r"$S_c = \sum_{c'} \mathrm{score}_{c'}\, K(c',c)$, $K \propto e^{-d^2/2\sigma^2}$" + f", σ = {prm.sigma:g} m", fontsize=11)
    same = pos.cell_bf == floor[0]
    order_c = np.argsort(-S[0, same])[:25]
    idx = np.flatnonzero(same)[order_c]
    a1.bar(np.arange(25) - 0.2, raw[0, idx], 0.4, color="#9FB6C9", label=r"$\mathrm{score}_c$ (trước khi làm mượt)")
    a1.bar(np.arange(25) + 0.2, S[0, idx], 0.4, color=TEAL, label=r"$S_c$ (sau khi làm mượt)")
    a1.set_xlabel("25 ô điểm cao nhất của tầng được chọn"); a1.set_ylabel("điểm")
    a1.legend(fontsize=9, frameon=False); a1.spines[["top", "right"]].set_visible(False)
    cols = [RUST if f == floor[0] else "#C9CED6" for f in floors]
    a2.bar(range(len(floors)), fsc, color=cols)
    a2.set_xticks(range(len(floors)))
    a2.set_xticklabels([f"{f.split('_')[0]}-{f.split('_')[1]}" for f in floors], fontsize=9)
    a2.set_xlabel("tòa-tầng"); a2.set_ylabel(f"trung bình {prm.kf} giá trị " + r"$S_c$" + " lớn nhất")
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: vn(v, 2))
    a1.yaxis.set_major_formatter(fmt); a2.yaxis.set_major_formatter(fmt)
    a2.set_title("Tầng được chọn = cột cao nhất" + f" (đúng: {ex and floor[0] == f'{int(te.BUILDINGID.iloc[qi])}_{int(te.FLOOR.iloc[qi])}'})".replace("True", "có").replace("False", "không"), fontsize=11)
    a2.spines[["top", "right"]].set_visible(False)
    save(fig, "d07_buoc6_lam_muot_tang.png")

    # ---------------------------------------------------------------- d08
    gf = b.ground_factor
    fig, ax = plt.subplots(figsize=(10, 6.2))
    x0, y0 = ex["true_x"], ex["true_y"]
    flo = cells[cells.building_floor.astype(str) == floor[0]]
    ax.scatter((flo.x - x0) * gf, (flo.y - y0) * gf, s=14, color="#C9CED6", label="tâm các ô của tầng")
    tc = cells.loc[top[0]]
    ax.scatter((tc.x - x0) * gf, (tc.y - y0) * gf, s=60 + 900 * a[0], color=TEAL, alpha=0.8,
               edgecolor="white", label=f"{prm.m} ô tốt nhất (kích thước tỉ lệ với trọng số " + r"$a_c$" + ")")
    ax.scatter([0], [0], marker="*", s=300, color=NAVY, label="vị trí thật")
    ax.scatter([(ex["pred_x"] - x0) * gf], [(ex["pred_y"] - y0) * gf], marker="X", s=160, color=RUST,
               label=f"vị trí ước lượng, sai số {vn(ex['err_m'])} m")
    ax.set_xlim(-45, 45); ax.set_ylim(-35, 25); ax.set_aspect("equal")
    ax.set_xlabel("Δx so với vị trí thật (m thực địa)"); ax.set_ylabel("Δy (m thực địa)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    ax.set_title("Bước 7 — Toạ độ = trọng tâm có trọng số của m ô tốt nhất trong tầng đã chọn",
                 loc="left", fontsize=13, fontweight="bold", color=NAVY)
    ax.text(5, 18, r"$(\hat x,\hat y) = \sum_{c\in\mathrm{top}\text{-}m} a_c\,(x_c,y_c),\quad a_c = \dfrac{S_c^{\,p}}{\sum S^{\,p}}$", fontsize=13)
    ax.text(5, 11, r"$e = \sqrt{(\hat x - x)^2 + (\hat y - y)^2}\cdot 0{,}766126$", fontsize=12)
    save(fig, "d08_buoc7_toa_do.png")

    # ---------------------------------------------------------------- d09
    fig, ax = canvas(13, 6.6, "Giao thức đánh giá và kiểm chứng (tập test chỉ dùng một lần)")
    box(ax, 0, 25, 21, 21, "trainingData", ["19 937 fingerprint", "16 điện thoại", "6 fold dev, giữ lại", "theo điện thoại"], fc=NAVY_L)
    box(ax, 25, 25, 23, 21, "Chọn trên dev", [f"utility: {', '.join(sel['grids'].get('utility', ['abs']))}",
                                              f"θ = {sel['theta_pct']:g}%", f"{vn(sel['n_configurations'], 0)} cấu hình",
                                              f"dev TB = {vn(sel['dev_mean_m'])} m"], fc=TEAL_L, ec=TEAL, hc=TEAL)
    box(ax, 52, 25, 21, 21, "Mô hình cuối", ["khai thác lại EFIM", "trên toàn bộ", "trainingData", f"{vn(U['model']['n_huis'], 0)} HUI"], fc=TEAL_L, ec=TEAL, hc=TEAL)
    box(ax, 77, 25, 23, 21, "validationData", ["1 111 fingerprint", "9/11 điện thoại lạ", "chấm MỘT lần", f"TB = {vn(T['sai_so_tb_m'])} m"], fc=RUST_L, ec=RUST, hc=RUST)
    for x1, x2 in ((21.5, 24.5), (48.5, 51.5), (73.5, 76.5)):
        arrow(ax, x1, 35.5, x2, 35.5)
    box(ax, 0, 1, 100, 19, "Kiểm chứng độc lập (không gọi EFIM, không gọi bộ định vị)", [
        "M1  minUtil mọi ô tính lại từ dBm gốc        M2  utility và support của HUI quét lại từ dữ liệu",
        "M3  mọi itemset 1–2 AP vượt minUtil đều có trong mô hình        M4  điểm, ô được chọn, toạ độ tính lại bằng vòng lặp",
        f"M5  sai số và độ chính xác đếm lại từ file dự đoán        Kết quả: {data['verification']['n_checks']} phép kiểm, "
        f"{data['verification']['n_failed']} thất bại; sổ Excel so_lieu/kiem_chung_mean.xlsx khớp mọi tập test"],
        fc="white", ec=GREY, hc=INK, fs=10)
    save(fig, "d09_giao_thuc.png")
    print("diagrams:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
