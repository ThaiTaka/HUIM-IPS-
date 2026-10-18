"""BAOCAO / bước 3 - vẽ toàn bộ hình vào BAOCAO/diagram từ các bảng trong so_lieu/.

    python BAOCAO/ma_nguon/03_ve_bieu_do.py

Mỗi hình đều ghi ngưỡng minUtil θ (trên trục, trong nhãn điểm/cột, hoặc chú giải).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from hinh_chung import (AXIS, BUILDING_COLOR, FILL_SOFT, HIGHLIGHT, INK, INK2,
                        MODEL_COLOR, MODEL_NAME, MUTED, SCOPE_NAME, SCOPE_STYLE,
                        SO_LIEU, luu, theta_txt, vn)
from nhan import lbl_ngan, thanh_vien

J = json.loads((SO_LIEU / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))
BEST, START = J["tot_nhat"], J["ban_dau"]
T2 = pd.read_csv(SO_LIEU / "02_so_AP_theo_minUtil.csv")
E3 = pd.read_csv(SO_LIEU / "03_EFIM_so_HUI_thoi_gian_bo_nho.csv")
S3 = pd.read_csv(SO_LIEU / "05_buoc3_minUtil_HUIM_chung.csv")
S4 = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_toa.csv")
S6 = pd.read_csv(SO_LIEU / "07_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
S7 = pd.read_csv(SO_LIEU / "08_buoc7_ensemble.csv")
S8 = pd.read_csv(SO_LIEU / "09_buoc8_thoi_gian_bo_nho.csv")
RANK = pd.read_csv(SO_LIEU / "10_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})
TOA = pd.read_csv(SO_LIEU / "11_sai_so_theo_toa.csv", dtype={"toa": str})
CELL = pd.read_csv(SO_LIEU / "12_sai_so_theo_toa_tang.csv")
PRED = pd.read_csv(SO_LIEU / "13_du_doan_tung_mau_tap_test.csv")
NGUON = ("Nguồn: BAOCAO/so_lieu/{}. Chọn cấu hình theo dev (6 fold leave-users-out của "
         "trainingData); tập test = validationData, 1.111 mẫu, chỉ dùng để báo cáo.")
TV = thanh_vien(BEST["config"])                 # thành viên của cấu hình chọn
TEN_BEST = lbl_ngan(BEST["config"])
TEN_START = lbl_ngan(START["config"])


def theta_chon(scope: str) -> list[float]:
    """θ của các thành viên cấu hình chọn thuộc phạm vi `scope`."""
    tag = "G" if scope == "global" else "PB"
    return sorted({t for s, _, t in TV if s == tag})


def danh_dau_theta(ax, th, text, color=MUTED, y=0.97):
    ax.axvline(th, color=color, lw=1, ls=":", zorder=1)
    ax.text(th, y, " " + text, transform=ax.get_xaxis_transform(), fontsize=7.5,
            color=color, va="top", ha="left")


def danh_dau_chon(ax, scope, y=0.86):
    for th in theta_chon(scope):
        danh_dau_theta(ax, th, f"θ của cấu hình chọn = {theta_txt(th)}", HIGHLIGHT, y)


def truc_theta(ax, ticks=(0.5, 0.75, 1, 1.5, 1.9294, 2.5, 3, 4, 5, 7.5, 10)):
    ax.set_xscale("log")
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([theta_txt(t).replace(" %", "") for t in ticks], fontsize=7.5)
    ax.minorticks_off()
    ax.set_xlabel("Ngưỡng minUtil θ (% tổng utility của phạm vi khai phá, thang log)")


def chu_giai_duoi(ax, ncol=2, **kw):
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=ncol,
              frameon=False, **kw)


# ---------------------------------------------------------------- H01 sơ đồ luồng
def h01():
    fig, ax = plt.subplots(figsize=(11.5, 4.3))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 36)
    ths = sorted({t for _, _, t in TV})
    th = " / ".join(theta_txt(t) for t in ths)
    n_g = sum(s == "G" for s, _, _ in TV)
    n_pb = sum(s == "PB" for s, _, _ in TV)
    if len(TV) > 1:
        tap = f"{len(TV)} tập AP:\n{n_g} chung + {n_pb} theo tòa\n{int(BEST['n_ap'])} AP (hợp)"
        s5 = f"5. Bộ định vị S4 × {len(TV)}\n+ trung vị toạ độ\n(ensemble {len(TV)} cấu hình)"
    else:
        tap = ("riêng từng tòa" if n_pb else "chung 3 tòa") + f"\n{int(BEST['n_ap'])} AP"
        s5 = "5. Bộ định vị S4\nBray-Curtis, k = 12\nw = 1/d⁴, ±6 dB"
    boxes = [
        (1, 20, 15, 14, "1. trainingData\n19.937 fingerprint\n520 AP, 3 tòa", FILL_SOFT),
        (19, 20, 17, 14, "2. Giao dịch utility\nitem = AP thấy được\nq = RSSI chuẩn hoá\np(i): Model A / B / C", FILL_SOFT),
        (39, 20, 19, 14, f"3. HUIM\nminUtil θ = {th}\nunion HUI chính xác\n(tìm kiếm phủ, cận EFIM)", "#e6effb"),
        (61, 20, 17, 14, "4. Tập AP được chọn\n" + tap, FILL_SOFT),
        (81, 20, 18, 14, s5, FILL_SOFT),
        (81, 2, 18, 13, "6. Tập test\n(validationData)\n1.111 fingerprint\nchỉ để báo cáo", FILL_SOFT),
        (52, 2, 26, 13, f"7. Kết quả trên tập test\nsai số TB {vn(BEST['test_mean_m'])} m\n"
         f"(dev {vn(BEST['dev_mean_m'])} m) · đúng tòa-tầng {vn(100 * BEST['test_joint_acc'], 1)} %", "#fdecea"),
        (1, 2, 47, 13, "Giao thức: mọi lựa chọn (model, θ, phạm vi, quy tắc chọn AP,\n"
         "ensemble) dựa trên sai số dev - GroupKFold 6 fold theo USERID\n"
         "trên trainingData. Tập test (validationData) không tham gia chọn.", "#ffffff"),
    ]
    for x, y, w, h, t, fc in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc=fc, ec=AXIS, lw=1))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=8.6,
                color=INK, linespacing=1.35)
    for a, b in [((16.4, 27), (18.6, 27)), ((36.4, 27), (38.6, 27)), ((58.4, 27), (60.6, 27)),
                 ((78.4, 27), (80.6, 27)), ((90, 19.6), (90, 15.4)), ((80.6, 8.5), (78.4, 8.5))]:
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.3))
    ax.set_title("Hình 1. Luồng HUIM-IPS trên UJIIndoorLoc - cấu hình cuối cùng: " + TEN_BEST,
                 fontsize=10)
    luu(fig, "H01_so_do_luong_HUIM_IPS",
        "Nguồn: BAOCAO/so_lieu/00_cau_hinh_cuoi_cung.json; src/huim/union_search.py (khối 3), "
        "src/optimize_positioning.py (khối 5).")


# ------------------------------------------------- H02 số AP trong union theo θ
def h02():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True)
    for ax, scope in zip(axs, ("global", "per_building")):
        for m in "ABC":
            d = T2[(T2.pham_vi == scope) & (T2.model == m)].sort_values("minUtil_pct")
            ax.plot(d.minUtil_pct, d.so_AP, SCOPE_STYLE[scope], color=MODEL_COLOR[m],
                    marker="o", ms=4, label=MODEL_NAME[m])
            for _, r in d[d.trang_thai != "COMPLETED"].iterrows():
                ax.annotate(f"Model {m}, θ = {theta_txt(r.minUtil_pct)}:\nchưa tính xong (> 30 phút)",
                            (r.minUtil_pct, 128), textcoords="offset points", xytext=(-20, 40),
                            fontsize=7.2, color=MODEL_COLOR[m], ha="center",
                            arrowprops=dict(arrowstyle="-", color=MODEL_COLOR[m], lw=0.8))
        truc_theta(ax)
        danh_dau_theta(ax, 1.9294, "θ ban đầu 1,9294 %")
        danh_dau_chon(ax, scope, y=0.22)
        ax.set_title(f"({'a' if scope == 'global' else 'b'}) {SCOPE_NAME[scope]}")
    axs[0].set_ylabel("Số AP trong union HUI")
    axs[1].legend(loc="lower left")
    fig.suptitle("Hình 3. Số AP được HUIM chọn giảm khi minUtil θ tăng", x=0.01,
                 ha="left", fontweight="bold", fontsize=10.5)
    fig.tight_layout()
    luu(fig, "H03_so_AP_theo_minUtil", NGUON.format("02_so_AP_theo_minUtil.csv")
        + " Theo tòa: tổng số AP khác nhau của 3 tập AP_tòa.")


# ------------------------------------------ H03 EFIM bùng nổ & chi phí tìm union
def h03():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6))
    ax = axs[0]
    for m in "ABC":
        d = E3[(E3.model == m) & (E3.so_HUI > 0)].sort_values("minUtil_pct")
        ok, ab = d[d.trang_thai == "COMPLETED"], d[d.trang_thai != "COMPLETED"]
        ax.plot(ok.minUtil_pct, ok.so_HUI, "-o", ms=4, color=MODEL_COLOR[m], label=MODEL_NAME[m])
        ax.plot(ab.minUtil_pct, ab.so_HUI, "x", ms=8, mew=2, color=MODEL_COLOR[m])
    ax.set_yscale("log")
    truc_theta(ax)
    ax.set_ylabel("Số HUI EFIM liệt kê (thang log)")
    ax.set_title("(a) EFIM: số HUI theo θ (× = dừng vì 600 s / 10⁶ HUI)")
    ax.legend(loc="upper right")
    ax = axs[1]
    for m in "ABC":
        d = E3[(E3.model == m) & (E3.trang_thai == "COMPLETED") & (E3.so_HUI > 0)].sort_values("minUtil_pct")
        ax.plot(d.minUtil_pct, d.thoi_gian_s, ":", marker="s", ms=4, color=MODEL_COLOR[m],
                label=f"EFIM liệt kê đủ - {m}")
        u = T2[(T2.pham_vi == "global") & (T2.model == m)].sort_values("minUtil_pct")
        uo = u[u.trang_thai == "COMPLETED"]
        ax.plot(uo.minUtil_pct, uo.thoi_gian_tim_union_s, "-", marker="o", ms=4,
                color=MODEL_COLOR[m], label=f"Tìm union - {m}")
    ax.set_yscale("log")
    truc_theta(ax)
    ax.set_ylabel("Thời gian khai phá (s, thang log)")
    ax.set_title("(b) Thời gian, HUIM chung (tìm union đo khi chạy song song)")
    chu_giai_duoi(ax, ncol=3, fontsize=7.5)
    fig.suptitle("Hình 2. Chi phí khai phá theo minUtil θ: EFIM liệt kê mọi HUI, tìm union chỉ cần một HUI mỗi AP",
                 x=0.01, ha="left", fontweight="bold", fontsize=10.5)
    fig.tight_layout()
    luu(fig, "H02_EFIM_bung_no_va_thoi_gian_tim_union",
        NGUON.format("03_EFIM_so_HUI_thoi_gian_bo_nho.csv, 02_so_AP_theo_minUtil.csv"))


# ------------------------------------------------------- H04 bộ nhớ khai phá
def h04():
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    for m in "ABC":
        d = E3[(E3.model == m) & (E3.so_HUI > 0)].sort_values("minUtil_pct")
        ok, ab = d[d.trang_thai == "COMPLETED"], d[d.trang_thai != "COMPLETED"]
        ax.plot(ok.minUtil_pct, ok.bo_nho_dinh_MB, ":", marker="s", ms=4,
                color=MODEL_COLOR[m], label=f"EFIM - {m}")
        ax.plot(ab.minUtil_pct, ab.bo_nho_dinh_MB, "x", ms=8, mew=2, color=MODEL_COLOR[m])
        u = T2[(T2.pham_vi == "global") & (T2.model == m) & (T2.trang_thai == "COMPLETED")]
        ax.plot(u.minUtil_pct, u.bo_nho_dinh_MB, "-o", ms=4, color=MODEL_COLOR[m],
                label=f"Tìm union - {m}")
    truc_theta(ax)
    ax.set_ylabel("Bộ nhớ đỉnh tăng thêm (MB)")
    ax.set_title("Hình 11. Bộ nhớ khai phá theo minUtil θ, HUIM chung 3 tòa (× = EFIM dừng giữa chừng)")
    chu_giai_duoi(ax, ncol=3, fontsize=7.5)
    luu(fig, "H11_bo_nho_khai_pha", NGUON.format("03_EFIM_so_HUI_thoi_gian_bo_nho.csv, 02_so_AP_theo_minUtil.csv")
        + " RSS đo bằng psutil, lấy mẫu 20 ms.")


# --------------------------------------------- H05 sai số theo θ (dev & val)
def h05():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, (scope, S) in zip(axs, (("global", S3), ("per_building", S4))):
        for m in "ABC":
            d = S[(S.model == m)].dropna(subset=["test_sai_so_tb_m"]).sort_values("minUtil_pct")
            ax.plot(d.minUtil_pct, d.test_sai_so_tb_m, SCOPE_STYLE[scope], marker="o",
                    color=MODEL_COLOR[m], label=f"{MODEL_NAME[m]} - tập test")
            ax.plot(d.minUtil_pct, d.dev_sai_so_tb_m, ":", marker="^", ms=4, lw=1.2,
                    color=MODEL_COLOR[m], alpha=0.85, label=f"Model {m} - dev")
        truc_theta(ax)
        danh_dau_theta(ax, 1.9294, "θ ban đầu", y=0.6)
        danh_dau_chon(ax, scope, y=0.97)
        ax.set_title(f"({'a' if scope == 'global' else 'b'}) {SCOPE_NAME[scope]}")
        ax.set_ylim(0, 60)
    axs[0].set_ylabel("Sai số định vị trung bình (m, trục cắt ở 60 m)")
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=7.8, frameon=False,
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Hình 4. Sai số trung bình theo minUtil θ: dev (dùng để chọn) và tập test (báo cáo)",
                 x=0.01, ha="left", fontweight="bold", fontsize=10.5)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    luu(fig, "H04_sai_so_theo_minUtil", NGUON.format("05_buoc3_minUtil_HUIM_chung.csv, 06_buoc4_HUIM_theo_toa.csv")
        + " Điểm vượt 60 m (θ ≥ 2,5 % chung; θ = 7,5 % theo tòa) xem trong bảng.")


# ---------------------------------------------- H06 đánh đổi số AP - sai số
def h06():
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 4.6), sharey=True)
    cb = {v["config"]: k for k, v in J["can_bang"].items()}
    for ax, m in zip(axs, "ABC"):
        placed = []
        for scope, S, mk in (("global", S3, "o"), ("per_building", S4, "s")):
            d = S[S.model == m].dropna(subset=["test_sai_so_tb_m"]).sort_values("so_AP")
            ax.plot(d.so_AP, d.test_sai_so_tb_m, SCOPE_STYLE[scope], marker=mk, ms=5,
                    color=MODEL_COLOR[m], lw=1.4, label=SCOPE_NAME[scope],
                    mfc=MODEL_COLOR[m] if scope == "global" else "white")
            for _, r in d.iterrows():
                x, y = r.so_AP, r.test_sai_so_tb_m
                if y > 40 or any(abs(x - a) < 22 and abs(y - b) < 2.2 for a, b in placed):
                    continue                  # nhãn trùng chỗ: bỏ, số có trong bảng 05/06
                placed.append((x, y))
                ax.annotate(theta_txt(r.minUtil_pct).replace(" ", ""), (x, y),
                            textcoords="offset points", xytext=(3, 4), fontsize=7, color=INK2)
            for _, r in d[d.cau_hinh.isin(cb)].iterrows():
                ax.scatter([r.so_AP], [r.test_sai_so_tb_m], s=140, marker="D", facecolors="none",
                           edgecolors=INK, lw=1.4, zorder=5)
                ax.annotate("cân bằng", (r.so_AP, r.test_sai_so_tb_m), textcoords="offset points",
                            xytext=(-8, -16), fontsize=7.5, color=INK, ha="right")
        ax.set_title(MODEL_NAME[m])
        ax.set_xlabel("Số AP (nhãn = minUtil θ)")
        ax.set_ylim(0, 40)
        ax.set_xlim(0, 330)
    axs[0].set_ylabel("Sai số trung bình trên tập test (m)")
    axs[0].legend(loc="upper right", fontsize=7.8)
    fig.suptitle("Hình 6. Đánh đổi số AP - sai số; mỗi điểm là một ngưỡng minUtil θ "
                 f"(cấu hình chọn: {TEN_BEST}, {int(BEST['n_ap'])} AP, {vn(BEST['test_mean_m'])} m)",
                 x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout()
    luu(fig, "H06_danh_doi_so_AP_sai_so", NGUON.format("05_buoc3_..., 06_buoc4_...")
        + " Trục tung cắt ở 40 m. ◇ = θ cân bằng (ít AP nhất có dev ≤ 105 % dev tốt nhất của phạm vi).")


# --------------------------------------------- H07 số AP mỗi tòa trong tập chọn
def h07():
    s3 = S3.set_index("cau_hinh")
    best3 = S3.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
    best4 = S4.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
    rows = [("Ban đầu: " + TEN_START, [s3.loc[START["config"], f"so_AP_toa{b}"] for b in range(3)]),
            ("HUIM chung tốt nhất: " + lbl_ngan(best3.cau_hinh), [best3[f"so_AP_toa{b}"] for b in range(3)]),
            ("HUIM theo tòa tốt nhất: " + lbl_ngan(best4.cau_hinh), [best4[f"so_AP_toa{b}"] for b in range(3)])]
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    y = np.arange(len(rows))[::-1]
    for i, (lab, v) in enumerate(rows):
        left = 0
        for b in range(3):
            ax.barh(y[i], v[b], left=left, color=BUILDING_COLOR[b], height=0.55,
                    edgecolor="white", lw=2, label=f"Tòa {b}" if i == 0 else None)
            ax.text(left + v[b] / 2, y[i], str(int(v[b])), ha="center", va="center",
                    color="white", fontsize=8.5, fontweight="bold")
            left += v[b]
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlabel("Số AP trong tập chọn, chia theo tòa (HUIM chung: tòa mà AP được thấy nhiều nhất)")
    ax.set_title("Hình 5. Ở θ ban đầu tòa 1 chỉ có 29 AP; hạ θ hoặc khai phá theo tòa cho tòa 1 đủ AP")
    ax.legend(ncol=3, loc="upper right")
    ax.grid(axis="y", visible=False)
    luu(fig, "H05_so_AP_moi_toa", NGUON.format("05_buoc3_..., 06_buoc4_..."))


# --------------------------------------------- H08 sai số theo tòa: trước/sau
def h08():
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    lab = {"ban_dau": "Ban đầu: " + TEN_START, "tot_nhat": "Tốt nhất: " + TEN_BEST}
    col = {"ban_dau": "#9a9a9a", "tot_nhat": "#2a78d6"}
    x = np.arange(4)
    for j, k in enumerate(("ban_dau", "tot_nhat")):
        d = TOA[TOA.cau_hinh == k].set_index("toa").loc[["0", "1", "2", "Tong"]]
        v = d.sai_so_tb_m.to_numpy()
        bars = ax.bar(x + (j - 0.5) * 0.38, v, 0.36, color=col[k], label=lab[k])
        for r, val in zip(bars, v):
            ax.text(r.get_x() + r.get_width() / 2, val + 0.4, vn(val, 1), ha="center",
                    fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["Tòa 0 (536 mẫu)", "Tòa 1 (307 mẫu)", "Tòa 2 (268 mẫu)", "Toàn bộ (1.111)"])
    ax.set_ylabel("Sai số trung bình trên tập test (m)")
    ax.set_title("Hình 12. Sai số theo tòa trước và sau tối ưu HUIM")
    chu_giai_duoi(ax, ncol=1, fontsize=8)
    ax.grid(axis="x", visible=False)
    luu(fig, "H12_sai_so_theo_toa", NGUON.format("11_sai_so_theo_toa.csv"))


# --------------------------------------------------- H09 quy tắc chọn AP
def h09():
    d = S6.copy()
    if not len(d):
        return
    d["nhan"] = d.apply(lambda r: f"{r.quy_tac}" + ("" if pd.isna(r.tham_so) or r.tham_so == "" else f" ({r.tham_so})")
                        + f"\n{int(r.so_AP)} AP", axis=1)
    fig, ax = plt.subplots(figsize=(11.0, 4.2))
    x = np.arange(len(d))
    ax.bar(x - 0.19, d.dev_sai_so_tb_m, 0.36, color="#86b6ef", label="dev (dùng để chọn)")
    ax.bar(x + 0.19, d.test_sai_so_tb_m, 0.36, color="#1c5cab", label="tập test")
    for i, (a, b) in enumerate(zip(d.dev_sai_so_tb_m, d.test_sai_so_tb_m)):
        ax.text(i - 0.19, a + 0.4, vn(a, 1), ha="center", fontsize=7.5)
        ax.text(i + 0.19, b + 0.4, vn(b, 1), ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(d.nhan, fontsize=7.8)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Sai số trung bình (m)")
    ax.legend(fontsize=8)
    r0 = d.iloc[0]
    ax.set_title(f"Hình 8. Quy tắc chuyển HUI thành tập AP - {SCOPE_NAME[r0.pham_vi]}, Model {r0.model}, "
                 f"θ = {theta_txt(r0.minUtil_pct)} (θ thấp nhất ≥ θ tốt nhất mà EFIM liệt kê đủ)", fontsize=9.6)
    luu(fig, "H08_quy_tac_chon_AP", NGUON.format("07_buoc6_quy_tac_chon_AP.csv")
        + " HUIM theo tòa: EFIM không liệt kê đủ tòa 1 ở θ nào (so_lieu/03b), nên chỉ có quy tắc union.")


# ------------------------------------------------------------ H10 ensemble
def h10():
    single = RANK[RANK.loai == "don"].iloc[0]
    top = S7.sort_values("dev_sai_so_tb_m").head(6)
    labs = [lbl_ngan(single.cau_hinh) + " (đơn lẻ tốt nhất)"] + [lbl_ngan(c) for c in top.cau_hinh]
    dev = [single.dev_sai_so_tb_m] + list(top.dev_sai_so_tb_m)
    val = [single.test_sai_so_tb_m] + list(top.test_sai_so_tb_m)
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    y = np.arange(len(labs))[::-1]
    for yy, a, b in zip(y, dev, val):
        ax.plot([b, a], [yy, yy], color=AXIS, lw=1.5, zorder=1)
    ax.scatter(dev, y, s=60, color="#86b6ef", zorder=3, label="dev (dùng để chọn)")
    ax.scatter(val, y, s=60, color="#1c5cab", zorder=3, label="tập test")
    for yy, a, b in zip(y, dev, val):
        ax.text(a + 0.02, yy + 0.18, vn(a, 2), fontsize=7.5, color=INK2)
        ax.text(b - 0.02, yy + 0.18, vn(b, 2), fontsize=7.5, color=INK2, ha="right")
    ax.set_yticks(y)
    ax.set_yticklabels(labs, fontsize=7.8)
    ax.set_xlim(min(val) - 0.25, max(dev) + 0.25)
    ax.set_xlabel("Sai số trung bình (m) - trục phóng to, không bắt đầu từ 0")
    ax.set_title("Hình 9. Ensemble các cấu hình HUIM so với cấu hình đơn lẻ tốt nhất (θ trong nhãn)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", visible=False)
    luu(fig, "H09_ensemble", NGUON.format("08_buoc7_ensemble.csv") +
        " Ensemble: toạ độ = trung bình (TB) hoặc trung vị của các thành viên; tầng = đa số.")


# ------------------------------------------------------------- H11 CDF
def h11():
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    for k, c, lab in (("ban_dau", "#9a9a9a", "Ban đầu: " + TEN_START),
                      ("tot_nhat", "#2a78d6", "Tốt nhất: " + TEN_BEST)):
        e = np.sort(PRED[PRED.cau_hinh == k].sai_so_m.to_numpy())
        ax.plot(e, np.arange(1, len(e) + 1) / len(e) * 100, color=c,
                label=f"{lab}\n  TB {vn(e.mean())} m, trung vị {vn(np.median(e))} m")
    for t in (5, 10):
        ax.axvline(t, color=MUTED, lw=0.8, ls=":")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Sai số định vị (m)")
    ax.set_ylabel("% mẫu test có sai số ≤ x")
    ax.set_title("Hình 14. Phân phối tích luỹ sai số trên tập test (1.111 mẫu)")
    ax.legend(fontsize=7.8, loc="lower right")
    luu(fig, "H14_CDF_sai_so", NGUON.format("13_du_doan_tung_mau_tap_test.csv"))


# --------------------------------------------------------- H12 heatmap tòa × tầng
def h12():
    fig, axs = plt.subplots(1, 2, figsize=(11.0, 3.9))
    vmax = CELL.sai_so_tb_m.max()
    for ax, k, ten in ((axs[0], "ban_dau", "Ban đầu:\n" + TEN_START),
                       (axs[1], "tot_nhat", "Tốt nhất:\n" + TEN_BEST)):
        d = CELL[CELL.cau_hinh == k].pivot(index="toa", columns="tang", values="sai_so_tb_m")
        n = CELL[CELL.cau_hinh == k].pivot(index="toa", columns="tang", values="so_mau")
        im = ax.imshow(d.to_numpy(), cmap="Blues", vmin=0, vmax=vmax, aspect="auto")
        for i in range(d.shape[0]):
            for j in range(d.shape[1]):
                v = d.to_numpy()[i, j]
                if np.isnan(v):
                    ax.text(j, i, "—", ha="center", va="center", color=MUTED)
                    continue
                ax.text(j, i, f"{vn(v, 1)} m\nn={int(n.to_numpy()[i, j])}", ha="center", va="center",
                        fontsize=7.5, color="white" if v > vmax * 0.55 else INK)
        ax.set_xticks(range(d.shape[1]))
        ax.set_xticklabels([f"Tầng {c}" for c in d.columns])
        ax.set_yticks(range(d.shape[0]))
        ax.set_yticklabels([f"Tòa {r}" for r in d.index])
        ax.grid(False)
        ax.set_title(ten, fontsize=8.6)
    fig.colorbar(im, ax=axs, label="Sai số trung bình (m)", shrink=0.9)
    fig.suptitle("Hình 13. Sai số trung bình theo tòa × tầng (tập test)", x=0.01, y=1.08, ha="left",
                 fontweight="bold", fontsize=10.5)
    luu(fig, "H13_heatmap_sai_so_toa_tang", NGUON.format("12_sai_so_theo_toa_tang.csv") + " —: tầng không có ở tòa đó.")


# ------------------------------------------------------------ H13 bản đồ
def h13():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4), sharex=True, sharey=True)
    x0, y0 = PRED.x_that.min(), PRED.y_that.min()
    for ax, k, ten in ((axs[0], "ban_dau", "Ban đầu:\n" + TEN_START),
                       (axs[1], "tot_nhat", "Tốt nhất:\n" + TEN_BEST)):
        d = PRED[PRED.cau_hinh == k]
        sc = ax.scatter(d.x_that - x0, d.y_that - y0, c=np.clip(d.sai_so_m, 0, 40), cmap="Blues",
                        s=9, vmin=0, vmax=40, edgecolors="none")
        ax.set_title(f"{ten}\nTB {vn(d.sai_so_m.mean())} m", fontsize=8.6)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m chiếu, tính từ góc tây nam)")
    axs[0].set_ylabel("y (m chiếu, tính từ góc tây nam)")
    fig.colorbar(sc, ax=axs, label="Sai số (m, cắt ở 40 m)", shrink=0.85)
    fig.suptitle("Hình 15. Vị trí thật của 1.111 mẫu test, tô màu theo sai số", x=0.01, y=1.02,
                 ha="left", fontweight="bold", fontsize=10.5)
    luu(fig, "H15_ban_do_sai_so", NGUON.format("13_du_doan_tung_mau_tap_test.csv")
        + " Toạ độ EPSG:3857 trừ đi góc nhỏ nhất.")


# ------------------------------------------- H14 thời gian & bộ nhớ định vị
def h14():
    d = S8.copy()
    d["nhan"] = [lbl_ngan(c) + f" · {int(n)} AP" for c, n in zip(d.cau_hinh, d.so_AP)]
    fig, axs = plt.subplots(1, 2, figsize=(11.8, 4.4), sharey=True)
    y = np.arange(len(d))[::-1]
    for ax, col, xl, nd in ((axs[0], "ms_per_fp", "Thời gian định vị (ms / fingerprint)", 2),
                            (axs[1], "radio_map_mb", "Bộ nhớ radio map (MB, float64)", 1)):
        ax.barh(y, d[col], 0.6, color="#2a78d6")
        for yy, v in zip(y, d[col]):
            ax.text(v, yy, " " + vn(v, nd), va="center", fontsize=7.5)
        ax.set_xlabel(xl)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(y)
    axs[0].set_yticklabels(d.nhan, fontsize=7.4)
    fig.suptitle("Hình 10. Chi phí trực tuyến của các cấu hình HUIM (θ ghi trong nhãn)",
                 x=0.01, ha="left", fontweight="bold", fontsize=10.5)
    fig.tight_layout()
    luu(fig, "H10_thoi_gian_bo_nho_dinh_vi", NGUON.format("09_buoc8_thoi_gian_bo_nho.csv")
        + " Trung vị 3 lần chạy sau 1 lần khởi động, 1.111 mẫu một lô, mọi nhân CPU, máy rảnh.")


# ------------------------------------------- H15 độ chính xác tòa-tầng theo θ
def h15():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.0), sharey=True)
    for ax, (scope, S) in zip(axs, (("global", S3), ("per_building", S4))):
        for m in "ABC":
            d = S[S.model == m].dropna(subset=["test_dung_toa_tang"]).sort_values("minUtil_pct")
            ax.plot(d.minUtil_pct, 100 * d.test_dung_toa_tang, SCOPE_STYLE[scope], marker="o",
                    color=MODEL_COLOR[m], label=MODEL_NAME[m])
        truc_theta(ax)
        danh_dau_chon(ax, scope, y=0.5)
        ax.set_title(f"({'a' if scope == 'global' else 'b'}) {SCOPE_NAME[scope]}")
    axs[0].set_ylabel("Đúng cả tòa và tầng trên tập test (%)")
    axs[0].legend(loc="lower left")
    fig.suptitle("Hình 7. Độ chính xác tòa-tầng theo minUtil θ", x=0.01, ha="left",
                 fontweight="bold", fontsize=10.5)
    fig.tight_layout()
    luu(fig, "H07_do_chinh_xac_toa_tang_theo_minUtil", NGUON.format("05_buoc3_..., 06_buoc4_..."))


if __name__ == "__main__":
    for f in (h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11, h12, h13, h14, h15):
        f()
        print("vẽ xong", f.__name__)
