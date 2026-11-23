"""Ảnh bổ sung cho Slide_HUIM_IPS_V7_day_du.pptx (cùng phong cách make_slide_v7_assets.py).

    fm_gf, fm_level, fm_adam     công thức còn thiếu trong bộ fm_* của make_slide_v7_assets.py
    cells_map.png                bản đồ 933 ô tham chiếu (huấn luyện) và 1 111 vị trí thật của tập kiểm tra, theo mét

Chạy: python src/baocao/make_main_assets_v7.py <thư mục ra>      (build_slides_v7_day_du.js tự gọi, sau make_slide_v7_assets.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slide_v7_assets as base  # noqa: E402

ROOT, GF = base.ROOT, base.GF
NAVY, TEAL, RUST, GOLD, GREY, INK = base.NAVY, base.TEAL, base.RUST, base.GOLD, base.GREY, base.INK

F = {
    "fm_gf": [r"$g=\cos\varphi=\cos\left(39{,}992698^{\circ}\right)=0{,}766126$",
              r"$\text{mét thực địa}\;=\;g\times\text{đơn vị tọa độ}$"],
    "fm_level": [r"$\ell(i,T)=\left\lfloor\dfrac{q(i,T)-1}{100}\cdot 3\right\rfloor\in\{0,1,2\}\quad$ (thấp, vừa, cao)",
                 r"$\text{mục của góc nhìn abs-L3}=\left(i,\ \ell(i,T)\right)$"],
    "fm_adam": [r"$\nabla_t=\dfrac{\partial L}{\partial\theta}+\lambda_{w}\,\theta,\qquad\lambda_{w}=10^{-3}$",
                r"$m_t=\beta_1 m_{t-1}+(1-\beta_1)\,\nabla_t,\qquad v_t=\beta_2 v_{t-1}+(1-\beta_2)\,\nabla_t^{2}$",
                r"$\theta_t=\theta_{t-1}-\eta\,\dfrac{m_t/(1-\beta_1^{\,t})}{\sqrt{v_t/(1-\beta_2^{\,t})}+10^{-8}},\quad\eta=5\cdot10^{-4}$"],
}


def cells_map(dst: Path) -> None:
    tr = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv", usecols=["LONGITUDE", "LATITUDE", "FLOOR", "BUILDINGID"])
    te = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "validationData.csv", usecols=["LONGITUDE", "LATITUDE"])
    cells = tr.drop_duplicates(["LONGITUDE", "LATITUDE", "FLOOR", "BUILDINGID"])
    x0, y0 = tr.LONGITUDE.min(), tr.LATITUDE.min()
    fig, ax = plt.subplots(figsize=(7.6, 5.3), dpi=200)
    cols = {0: TEAL, 1: GOLD, 2: NAVY}
    for b in (0, 1, 2):
        c = cells[cells.BUILDINGID == b]
        ax.scatter((c.LONGITUDE - x0) * GF, (c.LATITUDE - y0) * GF, s=7, color=cols[b], alpha=0.55, lw=0, label=f"Tòa {b}: {len(c)} ô (mọi tầng chồng lên nhau)")
    ax.scatter((te.LONGITUDE - x0) * GF, (te.LATITUDE - y0) * GF, s=5, color=RUST, alpha=0.55, lw=0, label="1 111 vị trí thật của tập kiểm tra")
    ax.set_aspect("equal")
    ax.set_xlabel("mét (Đông)", fontsize=11, color=INK)
    ax.set_ylabel("mét (Bắc)", fontsize=11, color=INK)
    ax.tick_params(labelsize=10, colors=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=9.5, frameon=False, markerscale=2.2)
    ax.grid(color="#E3E0D8", lw=0.5)
    fig.savefig(dst / "cells_map.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name, lines in F.items():
        base.render(lines, dst / f"{name}.png")
    cells_map(dst)
    print("assets bổ sung:", [p.name for p in dst.glob("fm_g*.png")] + ["cells_map.png"])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
