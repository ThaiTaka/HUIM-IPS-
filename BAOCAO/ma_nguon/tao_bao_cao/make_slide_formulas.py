"""Ảnh công thức cho slide (mathtext, phông STIX), để hiển thị giống nhau trên mọi máy.

Chạy: python src/baocao/make_slide_formulas.py <thư mục ra>   (build_slides.js tự gọi)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

plt.rcParams.update({"mathtext.fontset": "stix", "font.family": "STIXGeneral"})
INK = "#1B2A3D"

F = {
    "f_util": [r"$u(i,T) = q(i,T)\cdot p(i)$",
               r"$u(X,T) = \sum_{i\in X} u(i,T)$",
               r"$u(X) = \sum_{T\in D,\; X\subseteq T} u(X,T)$",
               r"$X$ là HUI  khi  $u(X) \geq \mathrm{minUtil}$"],
    "f_efim": [r"$\mathrm{TWU}(X) = \sum_{T\supseteq X} \mathrm{TU}(T)$",
               r"$\mathrm{lu}(\alpha,z) = \sum_{T\ni \alpha\cup\{z\}} \left[u(\alpha,T) + \mathrm{re}(\alpha,T)\right]$",
               r"$\mathrm{su}(\alpha,z) = \sum_{T\ni \alpha\cup\{z\}} \left[u(\alpha,T) + u(z,T) + \sum_{i\in T,\ i\succ z} u(i,T)\right]$"],
    "f_rank": [r"$q_{\mathrm{rank}}(i,T) = \mathrm{round}\left(1 + 99\cdot\dfrac{n_T - r_T(i)}{n_T - 1}\right)$"],
    "f_cell": [r"$\mathrm{minUtil}_c = \theta\cdot u(D_c),\qquad \mathrm{HUI}_c = \{X : u(X) \geq \mathrm{minUtil}_c\}$"],
    "f_score": [r"$\rho(X,T) = \dfrac{|X\cap T|}{|X|},\qquad \mathrm{agree}(X,T) = \exp\left(-\dfrac{|\bar q_T(X) - \bar q_c(X)|}{\tau}\right)$",
                r"$P_c(T) = \sum_{X\in \mathrm{HUI}_c} \dfrac{u(X)}{\sum_{Y\in\mathrm{HUI}_c} u(Y)}\;\rho(X,T)^{\gamma}\;\mathrm{agree}(X,T)$",
                r"$V_c(T) = \dfrac{\sum_{i\in T\cap I_c} q(i,T)}{\sum_{i\in T} q(i,T)},\qquad \mathrm{score}_c(T) = P_c(T)\,V_c(T)^{\beta}$"],
    "f_smooth": [r"$S_c(T) = \sum_{c'} \mathrm{score}_{c'}(T)\,K(c',c),\qquad K(c',c) \propto e^{-d(c',c)^2/2\sigma^2}$",
                r"$f(T) = \arg\max_{f}\ \dfrac{1}{k_f}\, \sum_{c\in \mathrm{top}_{k_f}(f)} S_c(T)$"],
    "f_coord": [r"$(\hat x,\hat y) = \sum_{c\in \mathrm{top}\text{-}m(f)} a_c\,(x_c,y_c),\qquad a_c = \dfrac{S_c^{\,p}}{\sum_{c'} S_{c'}^{\,p}}$"],
    "f_err": [r"$e_n = \sqrt{(\hat x_n - x_n)^2 + (\hat y_n - y_n)^2}\cdot g,\qquad \bar e = \dfrac{1}{N}\sum_{n=1}^{N} e_n$"],
}


def render(lines: list[str], out: Path, size: float = 22) -> None:
    """Mỗi dòng một ảnh, xếp chồng canh trái với khoảng cách đều."""
    parts = []
    for s in lines:
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, s, fontsize=size, color=INK)
        buf = io.BytesIO()
        fig.savefig(buf, dpi=200, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)
        parts.append(Image.open(io.BytesIO(buf.getvalue())).convert("RGBA"))
    gap = int(size * 200 / 72 * 0.55)
    W = max(p.size[0] for p in parts)
    H = sum(p.size[1] for p in parts) + gap * (len(parts) - 1)
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    y = 0
    for p in parts:
        img.paste(p, (0, y), p)
        y += p.size[1] + gap
    img.save(out)


def main(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name, lines in F.items():
        render(lines, dst / f"{name}.png")
    print("formulas:", len(F))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
