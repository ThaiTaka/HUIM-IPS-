"""BAOCAO1 / bước 3 - vẽ toàn bộ hình trong BAOCAO1/diagram từ các bảng của so_lieu/.

    python BAOCAO1/ma_nguon/03_ve_bieu_do.py

Mọi hình đều ghi ngưỡng minUtil θ: trên trục x, trên nhãn điểm / cột, hoặc trong tiêu đề.
Nét chấm đỏ = θ của cấu hình được chọn theo dev; nét chấm xám = θ ban đầu.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from hinh_chung import (BEST_COLOR, DEV_COLOR, FILL_SOFT, HIGHLIGHT, INK2, KEYS, MODEL_COLOR,
                        MODEL_NAME, MUTED, SO_LIEU, START_COLOR, TAP_TEST, TEN_DS, TEST_COLOR,
                        VUNG, cau_hinh, luu, plt, theta_txt, vn)
from nhan import lbl, theta_cua

J = cau_hinh()
B = J["bo_du_lieu"]
DU = pd.read_csv(SO_LIEU / "01_du_lieu.csv")
U = pd.read_csv(SO_LIEU / "03_so_AP_theo_minUtil.csv")
EF = pd.read_csv(SO_LIEU / "04_EFIM_so_HUI_thoi_gian_bo_nho.csv")
G = pd.read_csv(SO_LIEU / "05_buoc3_HUIM_chung.csv")
Z = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_vung.csv")
T5 = pd.read_csv(SO_LIEU / "07_buoc5_bo_dinh_vi_chon_lai.csv")
R6 = pd.read_csv(SO_LIEU / "08_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
E7 = pd.read_csv(SO_LIEU / "09_buoc7_ensemble.csv")
TM = pd.read_csv(SO_LIEU / "10_buoc8_thoi_gian_bo_nho.csv")
RANK = pd.read_csv(SO_LIEU / "11_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})
KQ = pd.read_csv(SO_LIEU / "12_ket_qua_theo_tap_test.csv")
PRED = pd.read_csv(SO_LIEU / "13_du_doan_tung_mau_tap_test.csv")
NGUON = ("Nguồn: BAOCAO1/so_lieu/{}. Chọn cấu hình theo dev (6 fold tách từ tập train); "
         "tập test chỉ dùng để báo cáo.")


def th_best(k):
    """θ của cấu hình tốt nhất (ensemble: θ các thành viên)."""
    return sorted(set(theta_cua(B[k]["best"]["config"])))


def th_start(k):
    return float(B[k]["start"]["theta_pct"])


def ke_theta(ax, k, label=True):
    """Đường dọc θ ban đầu (xám) và θ của cấu hình chọn (đỏ)."""
    ys = ax.get_ylim()
    ax.axvline(th_start(k), color=START_COLOR, ls=":", lw=1.3, zorder=1)
    for t in th_best(k):
        ax.axvline(t, color=HIGHLIGHT, ls=":", lw=1.3, zorder=1)
    if label:
        ax.text(th_start(k), ys[1], f" ban đầu\n θ = {theta_txt(th_start(k))}", color=MUTED,
                fontsize=7, va="top", ha="left")
        t = th_best(k)[0]
        ax.text(t, ys[1] - 0.18 * (ys[1] - ys[0]), f" chọn\n θ = {theta_txt(t)}",
                color=HIGHLIGHT, fontsize=7, va="top", ha="left")


def log_x(ax, ths):
    ax.set_xscale("log")
    tk = [t for t in (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50) if min(ths) <= t <= max(ths)]
    ax.set_xticks(tk)
    ax.set_xticklabels([vn(t, 2).rstrip("0").rstrip(",") for t in tk])
    ax.minorticks_off()


def chua(s: str) -> str:
    return str(s).replace("pct", "")


def tren(fig, h, ncol, tieu_de, y_leg=1.0):
    """Chú giải nằm trên các ô, tiêu đề nằm trên chú giải (không đè dòng nguồn ở dưới)."""
    fig.tight_layout()
    fig.legend(handles=h, loc="lower center", ncol=ncol, bbox_to_anchor=(0.5, y_leg))
    fig.suptitle(tieu_de, x=0.01, y=y_leg + 0.47 / fig.get_figheight(), ha="left", fontsize=11,
                 weight="bold")


def th_ngan(ths) -> str:
    """'0,25 / 1 / 1,5 %' - nhiều θ, một dấu %."""
    return " / ".join(f"{float(x):g}".replace(".", ",") for x in ths) + " %"


# ---------------------------------------------------------------- H01 sơ đồ luồng
def h01():
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def hop(x, y, w, h, t, fc, fs=8.6, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                    fc=fc, ec="#c3c2b7", lw=1))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs,
                weight="bold" if bold else "normal")

    def mui(x0, y0, x1, y1):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.3))

    hop(1, 40, 15, 14, "1. Tập train\n(vân tay Wi-Fi\ncó toạ độ)", FILL_SOFT)
    hop(19, 40, 17, 14, "2. Giao dịch utility\nitem = AP thấy được\nq = RSSI chuẩn hoá\np(i): Model A / B / C", FILL_SOFT)
    hop(39, 40, 19, 14, "3. HUIM ở ngưỡng minUtil θ\nunion HUI chính xác\n(tìm kiếm phủ, cận EFIM)\nchung hoặc theo vùng/tầng", "#e6effb")
    hop(61, 40, 16, 14, "4. Tập AP\nđược chọn\n(+ quy tắc top-n,\nfrequent, weighted)", FILL_SOFT)
    hop(80, 40, 19, 14, "5. Bộ định vị k-NN\nchọn trên dev\n(+ ensemble nhiều\ncấu hình HUIM)", FILL_SOFT)
    for a, b in ((16, 19), (36, 39), (58, 61), (77, 80)):
        mui(a + 0.3, 47, b - 0.3, 47)
    hop(80, 23, 19, 12, "6. Tập test\n(các file test của\nbộ dữ liệu)\nchỉ để báo cáo", FILL_SOFT)
    mui(89.5, 39.6, 89.5, 35.4)
    hop(1, 23, 76, 12, "Giao thức: model, θ, phạm vi, quy tắc, bộ định vị, ensemble đều chọn theo sai số "
        "trung bình trên 6 fold dev\ntách từ tập train (nhóm theo tháng / lần lấy mẫu / vị trí như "
        "cách tập test khác tập train). Tập test không tham gia chọn.", "#ffffff", fs=8.2)
    # bảng θ cuối cùng
    y = 18
    ax.text(1, y, "Cấu hình cuối cùng (chọn theo dev) và kết quả trên tập test:", fontsize=8.8,
            weight="bold", va="center")
    for i, k in enumerate(KEYS):
        b, s = B[k]["best"], B[k]["start"]
        kq_ = "; ".join(f"{tn} {vn(b[p + '_mean_m'])} m (ban đầu {vn(s[p + '_mean_m'])} m)"
                        for p, tn in TAP_TEST[k].items())
        ax.text(2, y - 4.2 * (i + 1),
                f"{TEN_DS[k]}: {lbl(b['config'], k, ngan=True)} · {int(b['n_ap'])} AP · {kq_}",
                fontsize=8.1, va="center")
    ax.set_title("Hình 1. Luồng HUIM-IPS trên 4 bộ dữ liệu - ngưỡng minUtil θ ở khối 3",
                 loc="left", fontsize=11)
    luu(fig, "H01_so_do_luong_HUIM_IPS", NGUON.format("00_cau_hinh_cuoi_cung.json"))


# --------------------------------------------- H02 số AP theo θ (chung + theo vùng)
def h02():
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.9))
    for ax, k in zip(axs, KEYS):
        u = U[(U.bo_du_lieu == k) & (U.trang_thai == "COMPLETED")]
        for m in "ABC":
            g = u[(u.pham_vi == "global") & (u.model == m)].sort_values("minUtil_pct")
            ax.plot(g.minUtil_pct, g.so_AP, "-o", ms=3.5, color=MODEL_COLOR[m], label=MODEL_NAME[m])
            z = Z[(Z.bo_du_lieu == k) & (Z.model == m)].dropna(subset=["so_AP"]).sort_values("minUtil_pct")
            if len(z):
                ax.plot(z.minUtil_pct, z.so_AP, "--", lw=1.4, color=MODEL_COLOR[m])
        n_all = int(DU.set_index("bo_du_lieu").loc[k, "so_AP_thay_o_train"])
        ax.axhline(n_all, color=MUTED, lw=0.9)
        ax.text(u.minUtil_pct.min(), n_all * 1.01, f"{n_all} AP thấy ở train", fontsize=7,
                color=MUTED, ha="left", va="bottom")
        log_x(ax, u.minUtil_pct)
        ax.set_ylim(0, n_all * 1.12)
        ke_theta(ax, k)
        ax.set_title(TEN_DS[k])
        ax.set_xlabel("minUtil θ (% tổng utility, thang log)")
    axs[0].set_ylabel("Số AP trong union HUI")
    h = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ms=4, label=MODEL_NAME[m]) for m in "ABC"]
    h += [Line2D([], [], color=INK2, ls="--", label=f"HUIM theo vùng / tầng (hợp các vùng)")]
    tren(fig, h, 4, "Hình 2. Số AP được HUIM chọn theo minUtil θ (union chính xác ở mọi θ)")
    luu(fig, "H02_so_AP_theo_minUtil", NGUON.format("03_so_AP_theo_minUtil.csv, 06_buoc4_HUIM_theo_vung.csv"))


# ------------------------------------- H03 thời gian tìm union so với EFIM
def h03():
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.9), sharey=True)
    for ax, k in zip(axs, KEYS):
        for m in "ABC":
            u = U[(U.bo_du_lieu == k) & (U.pham_vi == "global") & (U.model == m)
                  & (U.trang_thai == "COMPLETED") & ~U.da_du_moi_AP].sort_values("minUtil_pct")
            ax.plot(u.minUtil_pct, u.thoi_gian_tim_union_s.clip(lower=0.01), "-o", ms=3.5,
                    color=MODEL_COLOR[m])
            e = EF[(EF.bo_du_lieu == k) & (EF.model == m)]
            ok = e[e.trang_thai == "COMPLETED"]
            ab = e[e.trang_thai != "COMPLETED"]
            ax.scatter(ok.minUtil_pct, ok.thoi_gian_s.clip(lower=0.01), marker="s", s=22,
                       facecolor="white", edgecolor=MODEL_COLOR[m], zorder=3)
            ax.scatter(ab.minUtil_pct, ab.thoi_gian_s, marker="X", s=55, color=MODEL_COLOR[m], zorder=4)
        ax.set_yscale("log")
        allth = U[U.bo_du_lieu == k].minUtil_pct
        log_x(ax, allth)
        ke_theta(ax, k, label=False)
        ax.set_title(TEN_DS[k])
        ax.set_xlabel("minUtil θ (%, thang log)")
    axs[0].set_ylabel("Thời gian (s, thang log)")
    h = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ms=4, label=MODEL_NAME[m]) for m in "ABC"]
    h += [Line2D([], [], color=INK2, marker="o", ms=4, label="tìm union chính xác (mỗi mức θ)"),
          Line2D([], [], color=INK2, marker="s", mfc="white", ls="", label="EFIM liệt kê đủ HUI"),
          Line2D([], [], color=INK2, marker="X", ls="", ms=7, label="EFIM dừng (600 s / 10⁶ HUI)"),
          Line2D([], [], color=HIGHLIGHT, ls=":", label="θ được chọn")]
    tren(fig, h, 4, "Hình 3. Thời gian tìm union HUI chính xác so với EFIM liệt kê đầy đủ, theo minUtil θ")
    luu(fig, "H03_thoi_gian_union_vs_EFIM", NGUON.format("03_so_AP_theo_minUtil.csv, 04_EFIM_so_HUI_thoi_gian_bo_nho.csv")
        + " Mức θ 'đã đủ mọi AP' không cần tìm nên không vẽ.")


# ------------------------------------------------ H04 sai số theo θ (dev & test)
def h04():
    fig, axs = plt.subplots(1, 4, figsize=(13, 4.0))
    for ax, k in zip(axs, KEYS):
        g = G[G.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
        top = 0
        for m in "ABC":
            d = g[g.model == m].sort_values("minUtil_pct")
            ax.plot(d.minUtil_pct, d.test_sai_so_tb_m, "-o", ms=3.5, color=MODEL_COLOR[m])
            ax.plot(d.minUtil_pct, d.dev_sai_so_tb_m, ":", lw=1.4, color=MODEL_COLOR[m])
            top = max(top, d.test_sai_so_tb_m.quantile(0.8), d.dev_sai_so_tb_m.quantile(0.8))
        lo = min(g.test_sai_so_tb_m.min(), g.dev_sai_so_tb_m.min())
        top = min(top, 2.2 * lo)
        ax.set_ylim(max(0, lo - 0.15 * (top - lo + 0.1)), top * 1.12)
        log_x(ax, g.minUtil_pct)
        ke_theta(ax, k)
        ax.set_title(f"{TEN_DS[k]} ({TAP_TEST[k]['test']})")
        ax.set_xlabel("minUtil θ (%, thang log)")
    axs[0].set_ylabel("Sai số định vị trung bình (m)")
    h = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ms=4, label=MODEL_NAME[m]) for m in "ABC"]
    h += [Line2D([], [], color=INK2, marker="o", ms=4, label="tập test"),
          Line2D([], [], color=INK2, ls=":", label="dev (dùng để chọn)")]
    tren(fig, h, 5, "Hình 4. HUIM chung: sai số theo minUtil θ - dev (dùng để chọn) và tập test (báo cáo)")
    luu(fig, "H04_sai_so_theo_minUtil", NGUON.format("05_buoc3_HUIM_chung.csv")
        + " Trục y cắt để thấy vùng θ thấp (θ cao làm sai số tăng vọt); điểm cao hơn xem trong bảng.")


# ----------------------------------------------- H05 đánh đổi số AP - sai số
def h05():
    fig, axs = plt.subplots(1, 4, figsize=(13, 4.0))
    for ax, k in zip(axs, KEYS):
        g = G[G.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
        z = Z[Z.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"]) if len(Z) else Z
        for m in "ABC":
            d = g[g.model == m].drop_duplicates("so_AP")
            ax.scatter(d.so_AP, d.test_sai_so_tb_m, s=22, color=MODEL_COLOR[m], zorder=3)
            if len(z):
                dz = z[z.model == m].drop_duplicates("so_AP")
                ax.scatter(dz.so_AP, dz.test_sai_so_tb_m, s=26, marker="^", facecolor="white",
                           edgecolor=MODEL_COLOR[m], zorder=3)
        allp = pd.concat([g, z]) if len(z) else g
        top = allp.test_sai_so_tb_m.quantile(0.85)
        lo = allp.test_sai_so_tb_m.min()
        ax.set_ylim(max(0, lo - 0.1 * (top - lo + 0.1)), top * 1.1)
        # nhãn θ cho cấu hình ban đầu và cấu hình đơn tốt nhất
        for vai, col, dy in (("start", START_COLOR, 26), ("best_single", HIGHLIGHT, -30)):
            c = B[k][vai]
            ax.scatter([c["n_ap"]], [c["test_mean_m"]], s=110, facecolor="none", edgecolor=col,
                       lw=1.6, zorder=4)
            ax.annotate(f"{'ban đầu' if vai == 'start' else 'đơn tốt nhất'}: θ = {theta_txt(c['theta_pct'])}",
                        (c["n_ap"], c["test_mean_m"]), xytext=(-10 if k != "uji_lib3" else 10, dy),
                        textcoords="offset points", fontsize=7.2, color=col,
                        ha="right" if k != "uji_lib3" else "left",
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
                        arrowprops=dict(arrowstyle="-", color=col, lw=0.8))
        ax.set_title(TEN_DS[k])
        ax.set_xlabel("Số AP được chọn")
    axs[0].set_ylabel(f"Sai số trung bình trên tập test (m)")
    h = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ls="", label=MODEL_NAME[m]) for m in "ABC"]
    h += [Line2D([], [], color=INK2, marker="o", ls="", label="HUIM chung"),
          Line2D([], [], color=INK2, marker="^", mfc="white", ls="", label="HUIM theo vùng / tầng")]
    tren(fig, h, 5, "Hình 5. Đánh đổi số AP và sai số: mỗi điểm là một (phạm vi, model, θ)")
    luu(fig, "H05_danh_doi_AP_sai_so", NGUON.format("05_buoc3_HUIM_chung.csv, 06_buoc4_HUIM_theo_vung.csv"))


# ----------------------------------------------- H06 theo vùng / tầng vs chung
def h06():
    ks = [k for k in KEYS if VUNG[k]]
    fig, axs = plt.subplots(1, len(ks), figsize=(11.5, 3.9))
    for ax, k in zip(axs, ks):
        for scope, T, ls in (("chung", G, "-"), (f"theo {VUNG[k]}", Z, "--")):
            t = T[T.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
            m = t.sort_values("dev_sai_so_tb_m").iloc[0].model
            d = t[t.model == m].sort_values("minUtil_pct")
            ax.plot(d.minUtil_pct, d.test_sai_so_tb_m, ls, marker="o", ms=3.5, color=MODEL_COLOR[m],
                    label=f"HUIM {scope}, Model {m}")
        t = pd.concat([G[G.bo_du_lieu == k], Z[Z.bo_du_lieu == k]]).dropna(subset=["test_sai_so_tb_m"])
        top, lo = t.test_sai_so_tb_m.quantile(0.8), t.test_sai_so_tb_m.min()
        ax.set_ylim(max(0, lo - 0.15 * (top - lo + 0.1)), top * 1.12)
        log_x(ax, t.minUtil_pct)
        ke_theta(ax, k)
        ax.set_title(f"{TEN_DS[k]} - {3} {VUNG[k]}")
        ax.set_xlabel("minUtil θ (% tổng utility của phạm vi, thang log)")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=7.5, ncol=1)
    axs[0].set_ylabel("Sai số trung bình trên tập test (m)")
    fig.suptitle("Hình 6. HUIM theo vùng / tầng (đoán vùng trước, rồi dùng AP của vùng) so với HUIM chung",
                 x=0.01, y=1.04, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H06_theo_vung_vs_chung", NGUON.format("05_buoc3_HUIM_chung.csv, 06_buoc4_HUIM_theo_vung.csv")
        + " Model của mỗi đường là model tốt nhất theo dev của phạm vi đó.")


# ------------------------------------------ H07 bộ định vị chọn lại (bước 5)
def h07():
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.9))
    for ax, k in zip(axs, KEYS):
        info = B[k]["buoc5_bo_dinh_vi"]
        base = RANK[(RANK.bo_du_lieu == k) & (RANK.cau_hinh == info["selected_on"])].iloc[0]
        t = T5[T5.bo_du_lieu == k]
        bars = [("bộ định vị gốc", base)]
        if len(t):
            bars.append(("chọn lại trên AP HUIM", t.dropna(subset=["dev_sai_so_tb_m"])
                         .sort_values("dev_sai_so_tb_m").iloc[0]))
        x = np.arange(len(bars))
        for i, (nm, r) in enumerate(bars):
            for dx, col, v, lab in ((-0.18, DEV_COLOR, r.dev_sai_so_tb_m, "dev"),
                                    (0.18, TEST_COLOR, r.test_sai_so_tb_m, "tập test")):
                ax.bar(i + dx, v, 0.34, color=col, label=lab if i == 0 else None)
                ax.text(i + dx, v, vn(v, 2), ha="center", va="bottom", fontsize=7.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{nm}\nθ = {theta_txt(r.minUtil_pct)}, {int(r.so_AP)} AP" for nm, r in bars],
                           fontsize=7.4)
        ax.set_title(TEN_DS[k])
        ax.text(0.0, -0.36, ("chọn lại = giữ nguyên: " if info["same_as_base"] else "→ ") +
                info["new_positioner"], transform=ax.transAxes, fontsize=6.8, color=INK2, wrap=True)
        ax.set_ylim(0, max(max(r.dev_sai_so_tb_m, r.test_sai_so_tb_m) for _, r in bars) * 1.25)
        ax.set_xlim(-0.75, 1.75)
    axs[0].set_ylabel("Sai số trung bình (m)")
    h = [plt.Rectangle((0, 0), 1, 1, color=DEV_COLOR, label="dev"),
         plt.Rectangle((0, 0), 1, 1, color=TEST_COLOR, label="tập test")]
    tren(fig, h, 2, "Hình 7. Bước 5: chọn lại bộ định vị trên dev, chỉ dùng các AP mà HUIM chọn")
    luu(fig, "H07_bo_dinh_vi_chon_lai", NGUON.format("07_buoc5_bo_dinh_vi_chon_lai.csv, 07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv"))


# ------------------------------------------------------------ H08 quy tắc
def h08():
    ks = [k for k in KEYS if (R6.bo_du_lieu == k).any()]
    fig, axs = plt.subplots(1, len(ks), figsize=(3.3 * len(ks), 4.0))
    axs = np.atleast_1d(axs)
    for ax, k in zip(axs, ks):
        r = R6[R6.bo_du_lieu == k].reset_index(drop=True)
        y = np.arange(len(r))[::-1]
        for yy, (_, row) in zip(y, r.iterrows()):
            ax.plot([row.dev_sai_so_tb_m, row.test_sai_so_tb_m], [yy, yy], color="#d9d8d2", lw=1.2)
        ax.scatter(r.dev_sai_so_tb_m, y, s=30, color=DEV_COLOR, zorder=3, label="dev")
        ax.scatter(r.test_sai_so_tb_m, y, s=30, color=TEST_COLOR, zorder=3, label="tập test")
        from nhan import QT
        ax.set_yticks(y)
        ax.set_yticklabels([f"{QT.get(q + ('' if pd.isna(p) else str(p)), q)} ({int(n)} AP)"
                            for q, p, n in zip(r.quy_tac, r.tham_so, r.so_AP)], fontsize=7.5)
        ax.set_title(f"{TEN_DS[k]}\nModel {r.model.iloc[0]}, θ = {theta_txt(r.minUtil_pct.iloc[0])}",
                     fontsize=9.5)
        ax.set_xlabel("Sai số trung bình (m)")
    h = [Line2D([], [], color=DEV_COLOR, marker="o", ls="", label="dev"),
         Line2D([], [], color=TEST_COLOR, marker="o", ls="", label="tập test")]
    tren(fig, h, 2, "Hình 8. Bước 6: quy tắc biến tập HUI đầy đủ (EFIM) thành tập AP, ở θ ghi trên mỗi ô")
    luu(fig, "H08_quy_tac_chon_AP", NGUON.format("08_buoc6_quy_tac_chon_AP.csv")
        + " θ = mức EFIM liệt kê đủ gần nhất ở trên θ tốt nhất theo dev (hoặc cùng tập AP).")


# ------------------------------------------------------------ H09 ensemble
def h09():
    fig, axs = plt.subplots(4, 1, figsize=(11.5, 10.5))
    for ax, k in zip(axs, KEYS):
        e = E7[E7.bo_du_lieu == k].sort_values("dev_sai_so_tb_m").head(4)
        s = B[k]["best_single"]
        rows = [(f"đơn tốt nhất: {lbl(s['config'], k, ngan=True)}", s["dev_mean_m"], s["test_mean_m"])]
        rows += [(lbl(c, k, ngan=True), d, t) for c, d, t in
                 zip(e.cau_hinh, e.dev_sai_so_tb_m, e.test_sai_so_tb_m)]
        y = np.arange(len(rows))[::-1]
        for yy, (_, d, t) in zip(y, rows):
            ax.plot([d, t], [yy, yy], color="#d9d8d2", lw=1.2)
        ax.scatter([d for _, d, _ in rows], y, s=30, color=DEV_COLOR, zorder=3, label="dev")
        ax.scatter([t for _, _, t in rows], y, s=30, color=TEST_COLOR, zorder=3, label="tập test")
        ax.set_yticks(y)
        ax.set_yticklabels([r[0] for r in rows], fontsize=7.4)
        ax.set_title(TEN_DS[k])
        lo_, hi_ = min(min(d, t) for _, d, t in rows), max(max(d, t) for _, d, t in rows)
        ax.set_xlim(lo_ - 0.08 * (hi_ - lo_ + 0.01), hi_ + 0.08 * (hi_ - lo_ + 0.01))
    axs[-1].set_xlabel("Sai số trung bình (m)")
    h = [Line2D([], [], color=DEV_COLOR, marker="o", ls="", label="dev"),
         Line2D([], [], color=TEST_COLOR, marker="o", ls="", label="tập test (thứ nhất)")]
    tren(fig, h, 2, "Hình 9. Bước 7: các ensemble tốt nhất theo dev so với cấu hình đơn tốt nhất (θ trong nhãn)",
         y_leg=0.995)
    luu(fig, "H09_ensemble", NGUON.format("09_buoc7_ensemble.csv"))


# ----------------------------------------------- H10 ban đầu vs tốt nhất
def h10():
    items = []
    for k in KEYS:
        for p, tn in TAP_TEST[k].items():
            s = KQ[(KQ.bo_du_lieu == k) & (KQ.tap_test == tn)].set_index("vai_tro")
            items.append((k, tn, s.loc["ban_dau", "sai_so_tb_m"], s.loc["tot_nhat", "sai_so_tb_m"]))
    fig, ax = plt.subplots(figsize=(13.5, 4.8))
    x = np.arange(len(items))
    a = [i[2] for i in items]
    b = [i[3] for i in items]
    ax.bar(x - 0.19, a, 0.36, color=START_COLOR, label="ban đầu (HUIM chung A)")
    ax.bar(x + 0.19, b, 0.36, color=BEST_COLOR, label="tốt nhất theo dev")
    for xx, v1, v2 in zip(x, a, b):
        ax.text(xx - 0.19, v1, vn(v1), ha="center", va="bottom", fontsize=8)
        ax.text(xx + 0.19, v2, vn(v2), ha="center", va="bottom", fontsize=8, weight="bold")
    labs = []
    for k, tn, _, _ in items:
        bt = th_ngan(th_best(k))
        labs.append(f"{TEN_DS[k]}\n{tn}\nθ: {th_ngan([th_start(k)])} → {bt}\n"
                    f"AP: {int(B[k]['start']['n_ap'])} → {int(B[k]['best']['n_ap'])}")
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=7.6)
    ax.set_ylabel("Sai số trung bình trên tập test (m)")
    ax.legend(loc="upper right")
    ax.set_title("Hình 10. Kết quả trên tập test: cấu hình HUIM ban đầu và cấu hình tốt nhất (chọn theo dev)")
    luu(fig, "H10_ban_dau_vs_tot_nhat", NGUON.format("12_ket_qua_theo_tap_test.csv"), nguon_y=-0.07)


# ------------------------------------------------------------- H11 CDF
def h11():
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.7), sharey=True)
    for ax, k in zip(axs, KEYS):
        for tn, ls in zip(TAP_TEST[k].values(), ("-", "--")):
            for vai, col in (("ban_dau", START_COLOR), ("tot_nhat", BEST_COLOR)):
                e = np.sort(PRED[(PRED.bo_du_lieu == k) & (PRED.tap_test == tn)
                                 & (PRED.vai_tro == vai)].sai_so_m)
                ax.plot(e, np.arange(1, len(e) + 1) / len(e) * 100, ls, color=col, lw=1.6,
                        label=f"{'ban đầu' if vai == 'ban_dau' else 'tốt nhất'} · {tn}")
        ax.set_xlim(0, np.percentile(PRED[PRED.bo_du_lieu == k].sai_so_m, 97))
        ax.set_title(f"{TEN_DS[k]}\nθ {theta_txt(th_start(k))} → "
                     + " / ".join(theta_txt(t) for t in th_best(k)), fontsize=9.5)
        ax.set_xlabel("Sai số x (m)")
        ax.legend(fontsize=6.6, loc="lower right")
    axs[0].set_ylabel("% mẫu test có sai số ≤ x")
    fig.suptitle("Hình 11. Phân phối tích luỹ sai số trên tập test: ban đầu và tốt nhất",
                 x=0.01, y=1.06, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H11_CDF_sai_so", NGUON.format("13_du_doan_tung_mau_tap_test.csv"))


# ------------------------------------------------------------- H12 bản đồ
def h12():
    fig, axs = plt.subplots(1, 4, figsize=(13.5, 3.9))
    for ax, k in zip(axs, KEYS):
        tn = TAP_TEST[k]["test"]
        d = PRED[(PRED.bo_du_lieu == k) & (PRED.tap_test == tn) & (PRED.vai_tro == "tot_nhat")]
        if k == "dlulib":
            d = d.groupby(["x_that", "y_that", "tang_that"], as_index=False).sai_so_m.mean()
        else:
            d = d.groupby(["x_that", "y_that"], as_index=False).sai_so_m.mean()
        vmax = np.percentile(d.sai_so_m, 95)
        sc = ax.scatter(d.x_that, d.y_that, c=d.sai_so_m, cmap="viridis_r", s=14, vmin=0, vmax=vmax)
        cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label("sai số TB tại vị trí (m)", fontsize=7.5)
        ax.set_aspect("equal", adjustable="datalim")
        b = B[k]["best"]
        ax.set_title(f"{TEN_DS[k]} · {tn}\nθ = " + " / ".join(theta_txt(t) for t in th_best(k))
                     + f", {int(b['n_ap'])} AP", fontsize=9.3)
        ax.set_xlabel("x (m)")
    axs[0].set_ylabel("y (m)")
    fig.suptitle("Hình 12. Sai số trung bình tại mỗi vị trí test, cấu hình tốt nhất (DLULIB: gộp 3 tầng)",
                 x=0.01, y=1.06, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H12_ban_do_sai_so", NGUON.format("13_du_doan_tung_mau_tap_test.csv")
        + " Toạ độ là lưới mét cục bộ của từng bộ dữ liệu (HCXY không ghi đơn vị; đọc là mét).")


# ------------------------------------------------- H13 thời gian & bộ nhớ online
def h13():
    TEN_VAI = {"ban_dau": "ban đầu", "don_tot_nhat": "đơn tốt nhất", "can_bang_global": "cân bằng (chung)",
               "can_bang_zone": "cân bằng (theo vùng)", "tot_nhat_ensemble": "ensemble tốt nhất"}
    fig, axs = plt.subplots(2, 4, figsize=(13.5, 6.4))
    for j, k in enumerate(KEYS):
        t = TM[TM.bo_du_lieu == k].drop_duplicates("cau_hinh").reset_index(drop=True)
        y = np.arange(len(t))[::-1]
        labs = [f"{TEN_VAI.get(v, v)}\n{'θ ' + theta_txt(th) if not pd.isna(th) else 'θ ' + ' / '.join(theta_txt(x) for x in sorted(set(theta_cua(c))))}"
                f", {int(n)} AP" for v, th, c, n in zip(t.label, t.minUtil_pct, t.cau_hinh, t.so_AP)]
        for i, (col, xl) in enumerate((("ms_per_fp", "ms / vân tay"), ("radio_map_mb", "radio map (MB)"))):
            ax = axs[i, j]
            ax.barh(y, t[col], color=[START_COLOR if v == "ban_dau" else BEST_COLOR for v in t.label],
                    height=0.55)
            for yy, v in zip(y, t[col]):
                ax.text(v, yy, " " + vn(v, 3 if v < 1 else 2), va="center", fontsize=7.2)
            ax.set_yticks(y)
            ax.set_yticklabels(labs, fontsize=6.6)
            ax.set_xlim(0, t[col].max() * 1.35)
            ax.set_ylim(min(-0.6, len(t) - 3.5), len(t) - 0.4)
            ax.set_xlabel(xl)
            if i == 0:
                ax.set_title(TEN_DS[k])
    fig.suptitle("Hình 13. Thời gian định vị (trên) và bộ nhớ radio map (dưới) của các cấu hình, kèm θ",
                 x=0.01, y=1.01, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H13_thoi_gian_bo_nho_dinh_vi", NGUON.format("10_buoc8_thoi_gian_bo_nho.csv")
        + " Định vị tối đa 1.111 vân tay của tập test thứ nhất trong một lô, trung vị 3 lần, máy rảnh.")


# ---------------------------------------------- H14 bộ nhớ khi khai phá
def h14():
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.8), sharey=True)
    for ax, k in zip(axs, KEYS):
        for m in "ABC":
            u = U[(U.bo_du_lieu == k) & (U.pham_vi == "global") & (U.model == m)
                  & (U.trang_thai == "COMPLETED") & ~U.da_du_moi_AP].sort_values("minUtil_pct")
            ax.plot(u.minUtil_pct, u.bo_nho_dinh_MB.clip(lower=0.1), "-o", ms=3.5, color=MODEL_COLOR[m])
            e = EF[(EF.bo_du_lieu == k) & (EF.model == m)]
            ax.scatter(e.minUtil_pct, e.bo_nho_dinh_MB.clip(lower=0.1), marker="s", s=22,
                       facecolor="white", edgecolor=MODEL_COLOR[m], zorder=3)
        ax.set_yscale("log")
        log_x(ax, U[U.bo_du_lieu == k].minUtil_pct)
        ke_theta(ax, k, label=False)
        ax.set_title(TEN_DS[k])
        ax.set_xlabel("minUtil θ (%, thang log)")
    axs[0].set_ylabel("Bộ nhớ tăng thêm lúc đỉnh (MB, log)")
    h = [Line2D([], [], color=MODEL_COLOR[m], marker="o", ms=4, label=MODEL_NAME[m]) for m in "ABC"]
    h += [Line2D([], [], color=INK2, marker="o", label="tìm union chính xác"),
          Line2D([], [], color=INK2, marker="s", mfc="white", ls="", label="EFIM")]
    fig.legend(handles=h, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.12))
    fig.suptitle("Hình 14. Bộ nhớ khi khai phá HUIM theo minUtil θ (RSS tăng thêm, lấy mẫu 20 ms)",
                 x=0.01, y=1.04, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H14_bo_nho_khai_pha", NGUON.format("03_so_AP_theo_minUtil.csv, 04_EFIM_so_HUI_thoi_gian_bo_nho.csv")
        + " Giá trị < 0,1 MB vẽ ở 0,1 MB.")


# ------------------------------------- H15 sai số theo vùng / tầng (tập test)
def h15():
    ks = [k for k in KEYS if VUNG[k]]
    fig, axs = plt.subplots(1, len(ks), figsize=(11.5, 3.7))
    import sys
    from hinh_chung import ROOT
    sys.path.insert(0, str(ROOT / "src"))
    import huim_multi as HM
    for ax, k in zip(axs, ks):
        D = HM.data(k)
        tn = TAP_TEST[k]["test"]
        zt = D.zone_of_test(tn)
        vals = {}
        for vai in ("ban_dau", "tot_nhat"):
            d = PRED[(PRED.bo_du_lieu == k) & (PRED.tap_test == tn) & (PRED.vai_tro == vai)]
            vals[vai] = [d.sai_so_m.to_numpy()[zt == z].mean() for z in range(D.n_zones)]
        x = np.arange(D.n_zones)
        for dx, vai, col in ((-0.19, "ban_dau", START_COLOR), (0.19, "tot_nhat", BEST_COLOR)):
            ax.bar(x + dx, vals[vai], 0.36, color=col,
                   label=f"{'ban đầu' if vai == 'ban_dau' else 'tốt nhất'}")
            for xx, v in zip(x, vals[vai]):
                ax.text(xx + dx, v, vn(v), ha="center", va="bottom", fontsize=7.5)
        ax.set_ylim(0, max(max(v) for v in vals.values()) * 1.3)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{VUNG[k]} {z if VUNG[k] == 'vùng' else z + 1}\n({int((zt == z).sum())} mẫu)"
                            for z in range(D.n_zones)])
        ax.set_title(f"{TEN_DS[k]} · {tn}\nθ {theta_txt(th_start(k))} → "
                     + " / ".join(theta_txt(t) for t in th_best(k)), fontsize=9.3)
        ax.legend(fontsize=7.5)
    axs[0].set_ylabel("Sai số trung bình trên tập test (m)")
    fig.suptitle("Hình 15. Sai số theo vùng / tầng của mẫu test: ban đầu và tốt nhất",
                 x=0.01, y=1.07, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    luu(fig, "H15_sai_so_theo_vung_tang", NGUON.format("13_du_doan_tung_mau_tap_test.csv")
        + " Vùng của mẫu test = vùng có tâm gần vị trí thật nhất (k-means trên vị trí train).")


if __name__ == "__main__":
    for f in (h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11, h12, h13, h14, h15):
        f()
        print("vẽ xong", f.__name__, flush=True)
