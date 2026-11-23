"""Ảnh cho slide V7 (cùng phong cách slide cũ: phông STIX/Times, bảng màu navy–teal–rust–gold), vẽ từ số liệu thật.

    formulas   fm_*.png  công thức (mathtext) để hiển thị giống nhau trên mọi máy
    art        art_title.png, art_section.png  nền bản đồ UJIIndoorLoc, chấm màu là vân tay kiểm tra theo sai số V7
    figures    ex_map.png (ví dụ một vân tay thật), cdf_test.png, cdf_dev.png, hist_dev.png

Chạy: python src/baocao/make_slide_v7_assets.py <thư mục ra>     (build_slides_v7.js tự gọi)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SO = ROOT / "BAOCAO_V7" / "so_lieu"
DATA = json.load(open(ROOT / "BAOCAO" / "so_lieu_V7" / "du_lieu_bao_cao_V7.json", encoding="utf-8"))
GF = 0.766126
NAVY, INK, TEAL, RUST, GOLD, GREY = "#1F3A5F", "#1B2A3D", "#2A7F8F", "#B5532A", "#C9A227", "#8A8A85"
# Times New Roman cho chữ (đủ dấu tiếng Việt), STIX cho ký hiệu toán còn thiếu (∑, ∫ lớn, ...)
plt.rcParams.update({"mathtext.fontset": "custom", "mathtext.rm": "Times New Roman", "mathtext.it": "Times New Roman:italic",
                     "mathtext.bf": "Times New Roman:bold", "mathtext.fallback": "stix", "font.family": "Times New Roman",
                     "axes.unicode_minus": False})

F = {
    "fm_hui": [r"$u(i,T)=q(i,T)\cdot p(i)$",
               r"$u(X,T)=\sum_{i\in X}u(i,T)\quad(X\subseteq T)$",
               r"$u(X)=\sum_{T\in D,\;X\subseteq T}u(X,T)$",
               r"$X$ là HUI  $\Longleftrightarrow$  $u(X)\geq\mathrm{minUtil}$"],
    "fm_util3": [r"$q_{\mathrm{rank}}(i,T)=\mathrm{round}\left(1+99\,\dfrac{n_T-r_T(i)}{n_T-1}\right)$",
                 r"$q_{\mathrm{abs}}(i,T)=\mathrm{round}\left(1+99\,\dfrac{\mathrm{RSSI}_T(i)-L}{H-L}\right),\quad L=-104,\ H=0$",
                 r"$q_{\mathrm{rel}}(i,T)=\mathrm{round}\left(1+99\cdot\mathrm{clip}\left(\dfrac{\mathrm{RSSI}_T(i)-\max_j\mathrm{RSSI}_T(j)+W}{W},0,1\right)\right),\ W=40$"],
    "fm_efim": [r"$\mathrm{TWU}(X)=\sum_{T\supseteq X}\mathrm{TU}(T)$",
                r"$\mathrm{lu}(\alpha,z)=\sum_{T\ni\alpha\cup\{z\}}\left[u(\alpha,T)+\mathrm{re}(\alpha,T)\right]$",
                r"$\mathrm{su}(\alpha,z)=\sum_{T\ni\alpha\cup\{z\}}\left[u(\alpha,T)+u(z,T)+\sum_{i\in T,\ i\succ z}u(i,T)\right]$"],
    "fm_cell": [r"$\mathrm{minUtil}_c=\theta\cdot u(D_c),\qquad\theta=20\%$",
                r"$\mathrm{HUI}_c=\{X:\ u(X)\geq\mathrm{minUtil}_c\}$",
                r"$\bar q_c(X)=\dfrac{u(X)}{s(X)\,|X|},\qquad w(X)=\dfrac{u(X)}{\sum_{Y\in\mathrm{HUI}_c}u(Y)}$"],
    "fm_match": [r"$\rho(X,T)=\dfrac{|X\cap T|}{|X|},\qquad\mathrm{agree}(X,T)=\exp\left(-\dfrac{|q_T(X)-\bar q_c(X)|}{\tau}\right)$",
                 r"$P_c(T)=\sum_{X\in\mathrm{HUI}_c}w(X)\;\rho(X,T)^{\gamma}\;\mathrm{agree}(X,T),\qquad\gamma=2,\ \tau=20$",
                 r"$V_c(T)=\dfrac{\sum_{i\in T\cap I_c}q(i,T)}{\sum_{i\in T}q(i,T)},\qquad\mathrm{score}_c(T)=P_c(T)\,V_c(T)^{3}$"],
    "fm_smooth": [r"$S_c(T)=\sum_{c'}\mathrm{score}_{c'}(T)\,K(c',c),\qquad K(c',c)\propto e^{-d(c',c)^2/2\sigma^2},\ \sigma=3\ \mathrm{m}$",
                  r"$f(T)=\arg\max_f\ \dfrac{1}{20}\sum_{c\in\mathrm{top}_{20}(f)}S_c(T)$"],
    "fm_v4": [r"$(\hat x,\hat y)_{V4}=\sum_{c\in\mathrm{top}\text{-}12(f)}a_c\,(x_c,y_c),\qquad a_c=\dfrac{S_c^{\,8}}{\sum_{c'}S_{c'}^{\,8}}$"],
    "fm_v6": [r"$\hat d_c=\exp\left(g(\varphi_c)\right)-1$   ($g$: GBM học trên $\log(1+d)$)",
              r"$a_c\propto\exp\left(-\dfrac{\hat d_c-\hat d_{\min}}{\lambda}\right),\quad\lambda=2,\quad c\in\mathrm{top}\text{-}20(\hat d)$",
              r"$(\hat x,\hat y)_{V6}=\sum_{c}a_c\,(x_c,y_c)$"],
    "fm_feat": [r"$\hat q_c(i)=\dfrac{\sum_{X\ni i}w(X)\,\bar q_c(X)}{\sum_{X\ni i}w(X)},\qquad m_c(i)=\sum_{X\ni i}\dfrac{w(X)}{|X|}$",
                r"$R_c(T)=\sum_{i\in T}m_c(i)$",
                r"$\mathrm{MAE}_c(T)=\dfrac{\sum_{i\in T\cap I_c}q(i,T)\,|q(i,T)-\hat q_c(i)|}{\sum_{i\in T\cap I_c}q(i,T)}$",
                r"$\cos_c(T)=\dfrac{\langle q_T,\ m_c\odot\hat q_c\rangle}{\|q_T\|\ \|m_c\odot\hat q_c\|}$"],
    "fm_rel": [r"$\tilde x_i=x_i-\max_j x_j,\qquad\bar x_i=\dfrac{x_i-\min_j x_j}{\max_j x_j-\min_j x_j},\qquad r_i$ = hạng của $x_i$",
               r"$\mathrm{slog}(x)=\mathrm{sign}(x)\,\ln(1+|x|),\qquad z=\dfrac{\mathrm{slog}(x)-\mu}{\sigma}$"],
    "fm_scorer": [r"$h_i=\mathrm{ReLU}(W_1 z_i+b_1)\in\mathbb{R}^{32}$",
                  r"$\bar h=\dfrac{1}{K}\sum_{j=1}^{K}h_j,\qquad K=30$",
                  r"$g_i=\mathrm{ReLU}\left(W_2\,[h_i;\bar h]+b_2\right)\in\mathbb{R}^{16},\qquad s_i=w_3^{\top}g_i$"],
    "fm_softmax": [r"$w_i=\dfrac{\exp(s_i)}{\sum_{j=1}^{K}\exp(s_j)},\qquad w_i\geq0,\quad\sum_i w_i=1$",
                   r"$\hat x=\sum_{i=1}^{K}w_i\,x_i,\qquad\hat y=\sum_{i=1}^{K}w_i\,y_i$"],
    "fm_loss": [r"$L=\dfrac{1}{N}\sum_{n=1}^{N}g\,\sqrt{(\hat x_n-x_n)^2+(\hat y_n-y_n)^2+\varepsilon}$",
                r"$g=0{,}766126$ (m trên một đơn vị toạ độ),   $\varepsilon=10^{-6}$"],
    "fm_grad": [r"$\dfrac{\partial L}{\partial\hat c_n}=\dfrac{g}{N}\,\dfrac{\hat c_n-c_n}{\|\hat c_n-c_n\|},\qquad\dfrac{\partial\hat c_n}{\partial s_i}=w_i\,(c_i-\hat c_n)$",
                r"$\dfrac{\partial L}{\partial s_i}=w_i\,\left\langle c_i-\hat c_n,\ \dfrac{\partial L}{\partial\hat c_n}\right\rangle$"],
    "fm_fusion": [r"cắt: $\mathcal{S}=\{i:\ \hat d_i-\hat d_{\min}\leq\delta\}$",
                  r"nhiệt độ thích ứng: $T=T_0\,(1+c\,\hat d_{\min}),\ \ w_i\propto e^{-(\hat d_i-\hat d_{\min})/T}$",
                  r"loại ô yếu: $\mathcal{S}=\{i:\ S_i/S_1\geq s_{\min}\}$",
                  r"chọn cụm: $\mathcal{S}=\{i:\ \|c_i-c_{k^*}\|\leq r\},\ \ k^*=\arg\max_k\sum_{j:\,\|c_j-c_k\|\leq r}w_j$"],
    "fm_err": [r"$e_n=g\,\sqrt{(\hat x_n-x_n)^2+(\hat y_n-y_n)^2},\qquad\bar e=\dfrac{1}{N}\sum_{n=1}^{N}e_n$"],
    "fm_neff": [r"$N_{\mathrm{eff}}=\dfrac{1}{\sum_i w_i^{2}}$"],
    "fm_boot": [r"$\bar e^{(b)}=\dfrac{\sum_{p\in B_b}\sum_{n\in p}e_n}{\sum_{p\in B_b}|p|},\qquad B_b$: lấy mẫu có hoàn lại các điện thoại"],
    "fm_hier": [r"$\mathrm{minUtil}_f=\theta_f\cdot u(D_f),\qquad\theta_f=12{,}5\%$ (nhân 1,25 khi một lần chạy vượt 150 000 HUI)",
                r"ngữ cảnh: $P_{f^*},\ V_{f^*},\ R_{f^*},\ P_{f^*}-\max_{f\neq f^*}P_f,\ \ldots$ (11 số)"],
}


def render(lines: list[str], out: Path, size: float = 22) -> None:
    parts = []
    for s in lines:
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, s, fontsize=size, color=INK)
        buf = io.BytesIO()
        fig.savefig(buf, dpi=200, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)
        parts.append(Image.open(io.BytesIO(buf.getvalue())).convert("RGBA"))
    gap = int(size * 200 / 72 * 0.5)
    W = max(p.size[0] for p in parts)
    H = sum(p.size[1] for p in parts) + gap * (len(parts) - 1)
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    y = 0
    for p in parts:
        img.paste(p, (0, y), p)
        y += p.size[1] + gap
    img.save(out)


def art(dst: Path) -> None:
    tr = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv", usecols=["LONGITUDE", "LATITUDE"])
    P = pd.read_csv(ROOT / "results" / "huim_only" / "uji" / "v7" / "predictions" / "C_rel_absL3.csv")
    x0, y0 = tr.LONGITUDE.min(), tr.LATITUDE.min()
    for name, alpha_t, show_test in (("art_title.png", 0.55, True), ("art_section.png", 0.28, False)):
        fig = plt.figure(figsize=(13.333, 7.5), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        fig.patch.set_facecolor(NAVY)
        ax.set_facecolor(NAVY)
        ax.scatter(tr.LONGITUDE - x0, tr.LATITUDE - y0, s=2.5, color="#7FB3BF", alpha=alpha_t, lw=0)
        if show_test:
            ax.scatter(P.true_x - x0, P.true_y - y0, s=7, c=P.err_m.clip(0, 15), cmap="YlOrBr", alpha=0.85, lw=0)
        ax.set_xlim(-400, 330)
        ax.set_ylim(-70, 330)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.savefig(dst / name, facecolor=NAVY)
        plt.close(fig)


def ex_map(dst: Path) -> None:
    ex = DATA["example"]
    cells = ex["cells"]
    dx = np.array([c["dx"] for c in cells]) * GF
    dy = np.array([c["dy"] for c in cells]) * GF
    fig, axs = plt.subplots(1, 2, figsize=(12.0, 5.0), dpi=200, sharex=True, sharey=True)
    fig.patch.set_facecolor("white")
    for ax, key, col, title in ((axs[0], "w6", RUST, f"V6: sai {ex['v6']['err_m']:.2f} m".replace(".", ",")),
                                (axs[1], "w7", TEAL, f"V7: sai {ex['v7']['err_m']:.2f} m".replace(".", ","))):
        w = np.array([c[key] for c in cells])
        ax.scatter(dx, dy, s=14, color="#C9C5BA", zorder=1)
        big = w > 0.003
        ax.scatter(dx[big], dy[big], s=2600 * w[big], color=col, alpha=0.55, edgecolor=col, lw=1.2, zorder=2)
        for k in np.argsort(-w)[:4]:
            r_pt = float(np.sqrt(2600 * w[k] / np.pi))                      # bán kính chấm (điểm in) để đặt nhãn ngoài chấm
            ax.annotate(f"{100 * w[k]:.1f}%".replace(".", ","), (dx[k], dy[k]), xytext=(r_pt * 0.75 + 5, r_pt * 0.75 + 5), textcoords="offset points",
                        ha="left", va="bottom", fontsize=11, color="#1B2A3D", fontweight="bold", zorder=7,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ex_x, ex_y = float((w * dx).sum()), float((w * dy).sum())
        ax.scatter([0], [0], marker="*", s=420, color=GOLD, edgecolor=INK, lw=0.9, zorder=6, label="vị trí thật")
        ax.scatter([ex_x], [ex_y], marker="X", s=190, color=col, edgecolor=INK, lw=1.0, zorder=6, label="tọa độ ước lượng")
        ax.plot([0, ex_x], [0, ex_y], color=INK, lw=1.2, ls="--", zorder=4)
        ax.set_title(title, fontsize=17, color=NAVY, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(color="#E3E0D8", lw=0.6)
        ax.set_axisbelow(True)
        ax.set_xlabel("Đông–Tây so với vị trí thật (m)", fontsize=12, color=INK)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.legend(loc="upper left", fontsize=11, frameon=False)
    axs[0].set_ylabel("Bắc–Nam so với vị trí thật (m)", fontsize=12, color=INK)
    lim = float(max(np.abs(dx).max(), np.abs(dy).max())) * 0.72
    axs[0].set_xlim(-lim, lim)
    axs[0].set_ylim(-lim * 0.8, lim * 0.95)
    fig.tight_layout()
    fig.savefig(dst / "ex_map.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def cdf(dst: Path) -> None:
    for name, csv, cols, mask, title in (
        ("cdf_test.png", SO / "test_per_query.csv", [("err_V4", "V4", GREY), ("err_V6", "V6", NAVY), ("err_B_base", "V7-B", GOLD), ("err_C_rel_absL3", "V7-C2", TEAL)], None,
         "Phân bố sai số trên tập kiểm tra (1 111 vân tay)"),
        ("cdf_dev.png", SO / "dev_per_query.csv", [("err_V4", "V4", GREY), ("err_V6*", "V6*", NAVY), ("err_B_base", "V7-B", GOLD), ("err_C_rel_absL3", "V7-C2", TEAL)], "informative",
         "Phân bố sai số trên dev, out-of-fold (19 861 vân tay có thông tin)")):
        df = pd.read_csv(csv)
        if mask:
            df = df[df[mask]]
        fig, ax = plt.subplots(figsize=(6.2, 5.3), dpi=200)
        for col, lab, c in cols:
            e = np.sort(df[col].to_numpy())
            y = np.arange(1, len(e) + 1) / len(e)
            ax.plot(e, y, color=c, lw=2.2, label=f"{lab}: TB {e.mean():.2f} · trung vị {np.median(e):.2f} · P90 {np.percentile(e, 90):.1f} m".replace(".", ","))
        ax.set_xlim(0, 40)
        ax.set_ylim(0, 1)
        ax.grid(color="#E3E0D8", lw=0.7)
        ax.set_xlabel("sai số định vị (m)", fontsize=13)
        ax.set_ylabel("tỷ lệ truy vấn có sai số ≤ x", fontsize=13)
        ax.set_title(title, fontsize=12.5, color=NAVY, fontweight="bold")
        ax.legend(loc="lower right", fontsize=10.5, frameon=False)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        fig.tight_layout()
        fig.savefig(dst / name, facecolor="white")
        plt.close(fig)


def hist(dst: Path) -> None:
    df = pd.read_csv(SO / "dev_per_query.csv")
    df = df[df.informative]
    d = (df["err_V6*"] - df["err_C_rel_absL3"]).to_numpy()
    edges = np.arange(-20, 20.01, 1.0)
    h, _ = np.histogram(np.clip(d, -19.99, 19.99), edges)
    ctr = (edges[:-1] + edges[1:]) / 2
    fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=200)
    ax.bar(ctr[ctr < 0], h[ctr < 0], width=0.86, color=RUST, label=f"V7 kém hơn V6*: {int((d < -0.5).sum()):,} truy vấn".replace(",", "."))
    ax.bar(ctr[ctr >= 0], h[ctr >= 0], width=0.86, color=TEAL, label=f"V7 tốt hơn V6*: {int((d > 0.5).sum()):,} truy vấn".replace(",", "."))
    ax.set_ylim(0, h.max() * 1.18)
    ax.grid(axis="y", color="#E3E0D8", lw=0.7)
    ax.set_axisbelow(True)
    ax.set_xlabel("sai số V6* − sai số V7 (m); dương = V7 chính xác hơn (cắt ở ±20 m)", fontsize=12)
    ax.set_ylabel("số truy vấn", fontsize=12)
    ax.legend(loc="upper left", fontsize=11.5, frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(dst / "hist_dev.png", facecolor="white")
    plt.close(fig)


def main(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name, lines in F.items():
        render(lines, dst / f"{name}.png")
    art(dst)
    ex_map(dst)
    cdf(dst)
    hist(dst)
    print("assets:", len(list(dst.glob("*.png"))), "ảnh trong", dst)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
