"""BAOCAO/diagram/b*.png: the result charts of the report and the slides.

Every chart is drawn from the saved results (results/, BAOCAO/so_lieu); a CSV
with the plotted numbers is written next to each PNG in BAOCAO/so_lieu/bieu_do/.

  b01  mean test error of every dataset / test set (final models), 7 m line
  b02  UJIIndoorLoc error CDF: final model, initial estimate (v4), k-NN references
  b03  error CDFs of the other datasets
  b04  UJIIndoorLoc error per building-floor, v4 vs final
  b05  UJIIndoorLoc floor confusion matrix (final)
  b06  UJIIndoorLoc spatial map of the test errors
  b07  per-query change of the error, v4 -> final
  b08  version history: dev and test mean error
  b09  step 8 variants on dev
  b10  contribution of each group of HUI evidence (permutation on dev)
  b11  dev grid of steps 1-7 (sigma x m)
  b12  mining statistics: HUIs per cell, theta actually used
  b13  dataset description
  b14  UJIIndoorLoc phones: training vs test, error per test phone
  b15  comparison with the k-NN references
  b16  detected APs per fingerprint, training vs test (UJIIndoorLoc)

Run: python src/baocao/make_charts.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
HO = RES / "huim_only"
B = ROOT / "BAOCAO"
OUT = B / "diagram"
CSV = B / "so_lieu" / "bieu_do"
UJI = ROOT / "ujiindoorloc" / "UJIndoorLoc"
GF = 0.766126
NAVY, TEAL, RUST, GREY, GOLD, LIGHT = "#1F3A5F", "#2A7F8F", "#B5532A", "#8A8A85", "#C9A227", "#D9DEE5"
INK = "#1C1C1A"
plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 11, "axes.titlesize": 12.5,
                     "axes.titleweight": "bold", "axes.titlecolor": NAVY, "axes.titlelocation": "left",
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#55554F",
                     "axes.grid": True, "grid.color": "#E6E3DC", "grid.linewidth": 0.6,
                     "legend.frameon": False, "savefig.dpi": 220, "savefig.bbox": "tight",
                     "savefig.facecolor": "white"})
TITLE = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB", "hcxy": "HCXY",
         "hus": "HUS", "hus_dedup": "HUS (khử trùng lặp)"}
ORDER = list(TITLE)


def vn(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def comma_axis(ax, axis="y", d=0):
    f = matplotlib.ticker.FuncFormatter(lambda v, _p: vn(v, d))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def save(fig, name, df=None):
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)
    if df is not None:
        df.to_csv(CSV / f"{name}.csv", index=False)
    print("chart", name)


def preds(k, t):
    f = HO / k / "v6" / "predictions" / f"{t}.csv" if k == "uji" else HO / k / "predictions" / f"{t}.csv"
    return pd.read_csv(f)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CSV.mkdir(parents=True, exist_ok=True)
    D = json.load(open(B / "so_lieu" / "du_lieu_bao_cao.json", encoding="utf-8"))
    tests = [(k, t, v) for k in ORDER for t, v in D["datasets"][k]["tests"].items()]
    P6 = preds("uji", "validationData")
    P4 = pd.read_csv(HO / "uji" / "predictions" / "validationData.csv")
    kd = RES / "multi_dataset" / "uji" / "predictions"
    Kopt = pd.read_csv(kd / "validationData__optimised.csv")
    Kraw = pd.read_csv(kd / "validationData__study_knn.csv")

    # ------------------------------------------------------------- b01
    df = pd.DataFrame([{"bo_du_lieu": TITLE[k], "tap_test": t, "sai_so_tb_m": v["sai_so_tb_m"],
                        "trung_vi_m": v["trung_vi_m"]} for k, t, v in tests])
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = np.arange(len(df))
    col = [NAVY if k == "uji" else TEAL for k, _t, _v in tests]
    ax.bar(x, df.sai_so_tb_m, 0.6, color=col, zorder=3)
    ax.bar(x, df.trung_vi_m, 0.6, color="white", alpha=0.35, zorder=4, hatch="///", edgecolor="white", lw=0)
    for xx, v in zip(x, df.sai_so_tb_m):
        near = abs(v + 0.3 - 7) < 0.4
        ax.text(xx, v - 0.45 if near else v + 0.12, vn(v), ha="center", fontsize=10,
                color="white" if near else INK, fontweight="bold" if near else "normal", zorder=6)
    ax.axhline(7, color=RUST, ls="--", lw=1.3, zorder=5)
    ax.text(len(df) - 0.45, 7.12, "mức mục tiêu 7 m", color=RUST, ha="right", fontsize=10)
    ax.set_xticks(x, [f"{TITLE[k].replace(' (khử trùng lặp)', ' (KTL)')}\n{t}" for k, t, _v in tests], fontsize=9)
    ax.set_ylabel("Sai số (m)")
    ax.set_ylim(0, 8.2)
    ax.grid(axis="x", visible=False)
    comma_axis(ax)
    ax.set_title("Sai số trung bình trên tập kiểm tra của mọi bộ dữ liệu (phần gạch chéo: trung vị)")
    save(fig, "b01_ket_qua_tap_test", df)

    # ------------------------------------------------------------- b02
    curves = [("Mô hình cuối (Bước 1–8)", P6.err_m, NAVY, 2.4), ("Ước lượng ban đầu, Bước 1–7 (v4)", P4.err_m, TEAL, 1.8),
              ("k-NN tối ưu (tham chiếu)", Kopt.err_m, GREY, 1.4), ("k-NN gốc k = 1 (tham chiếu)", Kraw.err_m, GOLD, 1.4)]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    rows = []
    for n, e, c, lw in curves:
        s = np.sort(e.to_numpy())
        ax.plot(s, np.arange(1, len(s) + 1) / len(s) * 100, color=c, lw=lw,
                label=f"{n}: TB {vn(s.mean())} m, trung vị {vn(np.median(s))} m")
        rows += [{"duong": n, "phan_vi": q, "sai_so_m": round(float(np.percentile(s, q)), 4)} for q in (25, 50, 75, 90, 95)]
    ax.axvline(7, color=RUST, ls="--", lw=1.1)
    ax.set_xlim(0, 35); ax.set_ylim(0, 100)
    ax.set_xlabel("Sai số định vị (m)"); ax.set_ylabel("Tỷ lệ vân tay có sai số ≤ x (%)")
    ax.legend(fontsize=9, loc="lower right")
    ax.set_title("UJIIndoorLoc (1 111 vân tay kiểm tra): hàm phân bố tích luỹ của sai số")
    save(fig, "b02_cdf_uji", pd.DataFrame(rows))

    # ------------------------------------------------------------- b03
    others = [k for k in ORDER if k != "uji"]
    fig, axs = plt.subplots(2, 3, figsize=(12, 6.6), sharey=True)
    rows = []
    pal = [NAVY, RUST, TEAL]
    for ax, k in zip(axs.ravel(), others):
        for j, t in enumerate(D["datasets"][k]["tests"]):
            e = np.sort(preds(k, t).err_m.to_numpy())
            ax.plot(e, np.arange(1, len(e) + 1) / len(e) * 100, color=pal[j], lw=2,
                    label=f"{t}: TB {vn(e.mean())} m")
            rows.append({"bo_du_lieu": TITLE[k], "tap_test": t, "p50": np.percentile(e, 50), "p90": np.percentile(e, 90)})
        ax.axvline(7, color=RUST, ls="--", lw=1)
        ax.set_xlim(0, 15); ax.set_ylim(0, 100)
        ax.set_title(TITLE[k], fontsize=11.5)
        ax.legend(fontsize=8.5, loc="lower right")
        comma_axis(ax, "x", 1)
        ax.set_xlabel("Sai số (m)")
    axs[0, 0].set_ylabel("Tỷ lệ (%)"); axs[1, 0].set_ylabel("Tỷ lệ (%)")
    axs[1, 2].axis("off")
    fig.suptitle("Hàm phân bố tích luỹ của sai số trên các bộ dữ liệu bổ sung", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    save(fig, "b03_cdf_cac_bo_khac", pd.DataFrame(rows))

    # ------------------------------------------------------------- b04
    for P in (P4, P6):
        P["bf"] = P.true_building.astype(str) + "_" + P.true_floor.astype(str)
    g4 = P4.groupby("bf").err_m.mean(); g6 = P6.groupby("bf").err_m.mean(); n = P6.groupby("bf").size()
    lab = sorted(g6.index, key=lambda s: tuple(map(int, s.split("_"))))
    df = pd.DataFrame({"toa_tang": lab, "so_mau": n[lab].values, "v4_m": g4[lab].values, "cuoi_m": g6[lab].values})
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = np.arange(len(lab))
    ax.bar(x - 0.2, df.v4_m, 0.4, color=LIGHT, edgecolor=TEAL, label="Bước 1–7 (v4)", zorder=3)
    ax.bar(x + 0.2, df.cuoi_m, 0.4, color=NAVY, label="Mô hình cuối", zorder=3)
    for xx, v, nn in zip(x, df.cuoi_m, df.so_mau):
        ax.text(xx + 0.2, v + 0.2, vn(v, 1), ha="center", fontsize=8.5)
        ax.text(xx, -1.3, f"n={nn}", ha="center", fontsize=8, color=GREY)
    ax.axhline(7, color=RUST, ls="--", lw=1)
    ax.set_xticks(x, [f"T{s.split('_')[0]}–{s.split('_')[1]}" for s in lab])
    ax.set_ylim(-1.8, max(df.v4_m.max(), df.cuoi_m.max()) * 1.15)
    ax.set_xlabel("Tòa nhà – tầng (T0–0 = tòa 0, tầng 0)"); ax.set_ylabel("Sai số trung bình (m)")
    ax.grid(axis="x", visible=False); ax.legend(fontsize=9.5, loc="upper left")
    ax.set_title("UJIIndoorLoc: sai số trung bình theo tòa nhà – tầng")
    save(fig, "b04_sai_so_theo_toa_tang", df)

    # ------------------------------------------------------------- b05
    true = P6.bf.to_numpy(); pred = P6.pred_building_floor.astype(str).to_numpy()
    labs = sorted(set(true) | set(pred), key=lambda s: tuple(map(int, s.split("_"))))
    M = pd.crosstab(pd.Categorical(true, labs), pd.Categorical(pred, labs), dropna=False).to_numpy()
    R = M / np.maximum(M.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    ax.imshow(R, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(labs)):
        for j in range(len(labs)):
            if M[i, j]:
                ax.text(j, i, str(M[i, j]), ha="center", va="center", fontsize=8,
                        color="white" if R[i, j] > 0.55 else INK)
    tl = [f"T{s.split('_')[0]}–{s.split('_')[1]}" for s in labs]
    ax.set_xticks(range(len(labs)), tl, rotation=45, fontsize=8.5); ax.set_yticks(range(len(labs)), tl, fontsize=8.5)
    ax.set_xlabel("Tòa – tầng dự đoán"); ax.set_ylabel("Tòa – tầng thật"); ax.grid(False)
    ax.set_title(f"UJIIndoorLoc: ma trận nhầm lẫn tòa – tầng (đúng {vn(100 * (true == pred).mean(), 1)}%)")
    save(fig, "b05_ma_tran_nham_lan_tang", pd.DataFrame(M, index=labs, columns=labs).reset_index())

    # ------------------------------------------------------------- b06
    tr = pd.read_csv(UJI / "trainingData.csv", usecols=["LONGITUDE", "LATITUDE"])
    x0, y0 = tr.LONGITUDE.min(), tr.LATITUDE.min()
    fig, ax = plt.subplots(figsize=(10.5, 7))
    ax.scatter((tr.LONGITUDE - x0) * GF, (tr.LATITUDE - y0) * GF, s=3, color=LIGHT, label="điểm huấn luyện", zorder=1)
    sc = ax.scatter((P6.true_x - x0) * GF, (P6.true_y - y0) * GF, c=P6.err_m.clip(0, 20), cmap="YlOrRd",
                    s=16, edgecolor="#55554F", linewidth=0.2, zorder=3, label="vân tay kiểm tra (màu = sai số)")
    cb = fig.colorbar(sc, ax=ax, shrink=0.7, pad=0.01)
    cb.set_label("Sai số (m, cắt ở 20 m)")
    cb.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _p: vn(v, 1)))
    ax.set_aspect("equal"); ax.set_xlabel("x (m thực địa)"); ax.set_ylabel("y (m thực địa)")
    ax.legend(fontsize=9, loc="upper right", markerscale=2)
    ax.set_title("UJIIndoorLoc: phân bố không gian của sai số trên tập kiểm tra (mô hình cuối)")
    save(fig, "b06_ban_do_sai_so", P6[["true_x", "true_y", "err_m"]])

    # ------------------------------------------------------------- b07
    d = (P6.v4_err_m - P6.err_m).to_numpy()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    a1.hist(d.clip(-15, 15), bins=60, color=TEAL, edgecolor="white")
    a1.axvline(0, color=INK, lw=1)
    a1.set_xlabel("Sai số v4 − sai số mô hình cuối (m)"); a1.set_ylabel("Số vân tay")
    a1.set_title(f"Mức thay đổi sai số từng vân tay (tốt hơn: {vn(100 * (d > 0).mean(), 1)}%)", fontsize=11.5)
    a2.scatter(P6.v4_err_m, P6.err_m, s=8, color=NAVY, alpha=0.45)
    lim = 40
    a2.plot([0, lim], [0, lim], color=RUST, lw=1)
    a2.set_xlim(0, lim); a2.set_ylim(0, lim); a2.set_aspect("equal")
    a2.set_xlabel("Sai số v4 (m)"); a2.set_ylabel("Sai số mô hình cuối (m)")
    a2.set_title("Từng vân tay: dưới đường chéo là được cải thiện", fontsize=11.5)
    fig.tight_layout()
    save(fig, "b07_cai_thien_tung_van_tay", pd.DataFrame({"v4_m": P6.v4_err_m, "cuoi_m": P6.err_m}))

    # ------------------------------------------------------------- b08
    V = pd.DataFrame(D["versions"])
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    x = np.arange(len(V))
    ax.bar(x - 0.2, V.dev_mean_m, 0.4, color=TEAL, label="dev (chọn mô hình)", zorder=3)
    ax.bar(x + 0.2, V.test_mean_m, 0.4, color=NAVY, label="tập kiểm tra (chấm một lần)", zorder=3)
    for xx, a, b in zip(x, V.dev_mean_m, V.test_mean_m):
        ax.text(xx - 0.2, a + 0.08, vn(a), ha="center", fontsize=8.5)
        ax.text(xx + 0.2, b + 0.08, vn(b), ha="center", fontsize=8.5)
    ax.axhline(7, color=RUST, ls="--", lw=1)
    ax.set_xticks(x, [v.replace(" (final)", "\n(cuối)") for v in V.version])
    ax.set_ylim(5.5, 8.8); ax.set_ylabel("Sai số trung bình (m)"); ax.grid(axis="x", visible=False)
    comma_axis(ax, d=1); ax.legend(fontsize=9.5, loc="upper right")
    ax.set_title("UJIIndoorLoc: sai số dev và sai số kiểm tra qua các phiên bản")
    save(fig, "b08_lich_su_phien_ban", V[["version", "dev_mean_m", "test_mean_m"]])

    # ------------------------------------------------------------- b09
    r = D["datasets"]["uji"]["v6"]["research"]["dev_mean_m"]
    items = [("Bước 1–7 (v4)", r["v4 (baseline)"]), ("+ trọng số IDF của HUI", r["IDF weight of HUIs (best)"]),
             ("Xếp hạng lại: điểm HUI", r["re-rank, HUI scores"]), ("+ hồ sơ cường độ từ HUI", r["re-rank + HUI strength profile"]),
             ("Ứng viên toàn tòa nhà", r["re-rank, candidates over the whole building"]),
             ("+ đặc trưng tương đối (v5)", r["re-rank + features relative to the query's candidates (v5)"]),
             ("v5 học bỏ ô của truy vấn", r["v5 trained leave-own-cell-out"]), ("+ mô hình HUI abs (v6)", r["v5 + abs HUI model (v6)"])]
    df = pd.DataFrame(items, columns=["bien_the", "dev_tb_m"])
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    y = np.arange(len(df))[::-1]
    c = [NAVY if "v6" in s else (GREY if s in ("Ứng viên toàn tòa nhà", "v5 học bỏ ô của truy vấn", "+ trọng số IDF của HUI") else TEAL) for s in df.bien_the]
    ax.barh(y, df.dev_tb_m, color=c, zorder=3)
    for yy, v in zip(y, df.dev_tb_m):
        ax.text(v + 0.02, yy, vn(v), va="center", fontsize=9.5)
    ax.set_yticks(y, df.bien_the); ax.set_xlim(6.5, 7.8); ax.set_xlabel("Sai số trung bình trên dev (m)")
    ax.grid(axis="y", visible=False); comma_axis(ax, "x", 1)
    ax.set_title("Bước 8: các biến thể đã thử trên dev (xám: không dùng)")
    save(fig, "b09_bien_the_buoc8", df)

    # ------------------------------------------------------------- b10
    fi = HO / "uji" / "research" / "importance.json"
    if fi.exists():
        I = json.load(open(fi, encoding="utf-8"))
        df = pd.DataFrame(sorted(I["increase_m"].items(), key=lambda t: t[1]), columns=["nhom", "tang_sai_so_m"])
        fig, ax = plt.subplots(figsize=(9.5, 3.8))
        ax.barh(np.arange(len(df)), df.tang_sai_so_m, color=TEAL, zorder=3)
        for yy, v in enumerate(df.tang_sai_so_m):
            ax.text(v + 0.01, yy, f"+{vn(v)} m", va="center", fontsize=9.5)
        ax.set_yticks(np.arange(len(df)), df.nhom); ax.grid(axis="y", visible=False)
        ax.set_xlabel(f"Sai số dev tăng thêm khi xáo trộn nhóm (m); mốc {vn(I['base_dev_mean_m'])} m")
        ax.set_xlim(0, df.tang_sai_so_m.max() * 1.25)
        comma_axis(ax, "x", 2)
        ax.set_title("Bước 8: mức đóng góp của từng nhóm bằng chứng HUI")
        save(fig, "b10_dong_gop_bang_chung", df)

    # ------------------------------------------------------------- b11
    G = pd.read_csv(HO / "uji" / "dev_grid.csv")
    G = G[(G.utility == "rank")]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    rows = []
    for sg, c in zip(sorted(G.sigma.unique()), [GREY, TEAL, NAVY, RUST]):
        g = G[G.sigma == sg].groupby("m").dev_mean_m.min()
        ax.plot(g.index, g.values, marker="o", color=c, lw=2, label=f"σ = {vn(sg, 0)} m" if sg else "không làm mượt")
        rows += [{"sigma": sg, "m": m, "dev_tb_m": v} for m, v in g.items()]
    ax.set_xlabel("m = số ô dùng để ước lượng toạ độ"); ax.set_ylabel("Sai số dev tốt nhất (m)")
    comma_axis(ax, d=2); ax.legend(fontsize=9.5)
    ax.set_title("UJIIndoorLoc, Bước 1–7: sai số dev theo σ và m (lợi ích rank, θ = 20%)")
    save(fig, "b11_luoi_tham_so_dev", pd.DataFrame(rows))

    # ------------------------------------------------------------- b12
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    runs = {k: pd.read_csv(HO / k / "cell_runs.csv") for k in ORDER}
    a1.boxplot([np.log10(runs[k].n_huis.clip(lower=1)) for k in ORDER], tick_labels=[TITLE[k] for k in ORDER],
               patch_artist=True, boxprops={"facecolor": "#DDEBEE", "edgecolor": TEAL},
               medianprops={"color": NAVY, "lw": 2}, flierprops={"markersize": 2})
    a1.set_yticks([0, 1, 2, 3, 4], ["1", "10", "100", "1 000", "10 000"])
    a1.set_ylabel("Số HUI mỗi ô (thang log)"); a1.tick_params(axis="x", labelsize=8.5, rotation=20)
    a1.set_title("Số HUI khai thác được trên mỗi ô", fontsize=11.5)
    med = [runs[k].theta_used_pct.median() for k in ORDER]
    esc = [100 * (runs[k].n_attempts > 1).mean() for k in ORDER]
    x = np.arange(len(ORDER))
    a2.bar(x - 0.2, med, 0.4, color=NAVY, label="θ trung vị thực dùng (%)", zorder=3)
    a2.bar(x + 0.2, esc, 0.4, color=GOLD, label="tỷ lệ ô phải nâng θ (%)", zorder=3)
    a2.set_xticks(x, [TITLE[k] for k in ORDER], fontsize=8.5, rotation=20); a2.grid(axis="x", visible=False)
    a2.legend(fontsize=9); a2.set_title("Ngưỡng θ thực dùng sau khi tự nâng ngưỡng", fontsize=11.5)
    fig.tight_layout()
    save(fig, "b12_thong_ke_khai_thac", pd.DataFrame({"bo_du_lieu": [TITLE[k] for k in ORDER], "theta_trung_vi": med,
                                                       "ty_le_nang_theta": esc,
                                                       "hui_trung_vi_moi_o": [runs[k].n_huis.median() for k in ORDER]}))

    # ------------------------------------------------------------- b13
    desc = pd.DataFrame([D["datasets"][k]["description"] for k in ORDER])
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    for ax, colname, lab, c in zip(axs, ["so_ap", "mau_huan_luyen", "diem_tham_chieu"],
                                   ["Số AP", "Số vân tay huấn luyện", "Số điểm tham chiếu (ô)"], [NAVY, TEAL, RUST]):
        ax.barh(np.arange(len(desc))[::-1], desc[colname], color=c, zorder=3)
        for yy, v in zip(np.arange(len(desc))[::-1], desc[colname]):
            ax.text(v, yy, " " + vn(v, 0), va="center", fontsize=9)
        ax.set_yticks(np.arange(len(desc))[::-1], desc.ten if ax is axs[0] else [""] * len(desc))
        ax.set_title(lab, fontsize=11.5); ax.grid(axis="y", visible=False)
        ax.set_xlim(0, desc[colname].max() * 1.3); comma_axis(ax, "x")
    fig.suptitle("Quy mô của sáu bộ dữ liệu", x=0.01, ha="left", fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    save(fig, "b13_mo_ta_du_lieu", desc)

    # ------------------------------------------------------------- b14
    trp = pd.read_csv(UJI / "trainingData.csv", usecols=["PHONEID"])
    vap = pd.read_csv(UJI / "validationData.csv", usecols=["PHONEID"])
    P6["PHONEID"] = vap.PHONEID.to_numpy()[P6.src_row.to_numpy() - P6.src_row.min()]
    seen = set(trp.PHONEID)
    g = P6.groupby("PHONEID").agg(so_mau=("err_m", "size"), sai_so_tb_m=("err_m", "mean")).reset_index()
    g["co_trong_huan_luyen"] = g.PHONEID.isin(seen)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
    allp = sorted(set(trp.PHONEID) | set(vap.PHONEID))
    x = np.arange(len(allp))
    a1.bar(x - 0.2, [int((trp.PHONEID == p).sum()) for p in allp], 0.4, color=TEAL, label="huấn luyện", zorder=3)
    a1.bar(x + 0.2, [int((vap.PHONEID == p).sum()) for p in allp], 0.4, color=RUST, label="kiểm tra", zorder=3)
    a1.set_xticks(x, allp, fontsize=8); a1.set_xlabel("PHONEID"); a1.set_ylabel("Số vân tay")
    a1.set_yscale("log"); a1.legend(fontsize=9); a1.grid(axis="x", visible=False)
    a1.set_title("Điện thoại trong tập huấn luyện và tập kiểm tra", fontsize=11.5)
    gx = np.arange(len(g))
    a2.bar(gx, g.sai_so_tb_m, color=[TEAL if s else RUST for s in g.co_trong_huan_luyen], zorder=3)
    for xx, v, nn in zip(gx, g.sai_so_tb_m, g.so_mau):
        a2.text(xx, v + 0.2, f"{vn(v, 1)}\n(n={nn})", ha="center", fontsize=7.5)
    a2.axhline(7, color=RUST, ls="--", lw=1)
    a2.set_xticks(gx, g.PHONEID, fontsize=8.5); a2.set_xlabel("PHONEID của tập kiểm tra")
    a2.set_ylabel("Sai số TB (m)"); a2.grid(axis="x", visible=False)
    a2.set_ylim(0, g.sai_so_tb_m.max() * 1.3)
    a2.set_title("Sai số theo điện thoại (đỏ: không có trong huấn luyện)", fontsize=11.5)
    fig.tight_layout()
    save(fig, "b14_dien_thoai", g)

    # ------------------------------------------------------------- b15
    R = pd.DataFrame(D["references"])
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = np.arange(len(R))
    for off, colname, c, lab in ((-0.27, "chi_huim_m", NAVY, "Chỉ HUIM (đề xuất)"), (0, "knn_goc_m", GOLD, "k-NN gốc"),
                                 (0.27, "knn_toi_uu_m", GREY, "k-NN tối ưu")):
        ax.bar(x + off, R[colname].fillna(0), 0.27, color=c, label=lab, zorder=3)
    ax.set_xticks(x, [f"{a.replace(' (khử trùng lặp)', ' (KTL)')}\n{b}" for a, b in zip(R.ten, R.tap_test)], fontsize=8.5)
    ax.axhline(7, color=RUST, ls="--", lw=1)
    ax.set_ylabel("Sai số trung bình (m)"); ax.grid(axis="x", visible=False); ax.legend(fontsize=9.5)
    comma_axis(ax)
    ax.set_title("So sánh với các hệ thống tham chiếu dùng k-NN (chỉ để đối chiếu)")
    save(fig, "b15_so_sanh_tham_chieu", R)

    # ------------------------------------------------------------- b16
    W = [c for c in pd.read_csv(UJI / "trainingData.csv", nrows=1).columns if c.startswith("WAP")]
    ntr = (pd.read_csv(UJI / "trainingData.csv", usecols=W).to_numpy() != 100).sum(1)
    nva = (pd.read_csv(UJI / "validationData.csv", usecols=W).to_numpy() != 100).sum(1)
    fig, ax = plt.subplots(figsize=(8.5, 4))
    bins = np.arange(0, 55, 2)
    ax.hist(ntr, bins=bins, density=True, color=TEAL, alpha=0.75, label=f"huấn luyện (TB {vn(ntr.mean(), 1)})")
    ax.hist(nva, bins=bins, density=True, color=RUST, alpha=0.6, label=f"kiểm tra (TB {vn(nva.mean(), 1)})")
    ax.set_xlabel("Số AP được phát hiện trong một vân tay"); ax.set_ylabel("Mật độ")
    ax.legend(fontsize=9.5); comma_axis(ax, d=2)
    ax.set_title("UJIIndoorLoc: số AP mỗi vân tay ở tập huấn luyện và tập kiểm tra")
    save(fig, "b16_so_ap_moi_van_tay", pd.DataFrame({"tap": ["huan_luyen", "kiem_tra"], "tb": [ntr.mean(), nva.mean()]}))


if __name__ == "__main__":
    main()
