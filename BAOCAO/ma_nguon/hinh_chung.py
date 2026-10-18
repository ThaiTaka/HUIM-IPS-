"""Kiểu dáng dùng chung cho mọi hình trong BAOCAO/diagram (matplotlib, tiếng Việt).

Màu gán cố định theo THỰC THỂ, không theo thứ hạng:
  * Model A / B / C        -> 3 ô đầu của bảng màu phân loại (đã kiểm tra an toàn
                              cho người mù màu với mọi cặp)
  * Tòa 0 / 1 / 2          -> bộ màu thứ hai (tím / vàng / xanh lá), không trùng model
  * phạm vi HUIM           -> nét: chung 3 tòa = nét liền, theo từng tòa = nét đứt
Nhãn số ghi trực tiếp lên cột/điểm quan trọng, nên màu không bao giờ là kênh duy nhất.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BAOCAO = ROOT / "BAOCAO"
DIAGRAM = BAOCAO / "diagram"
SO_LIEU = BAOCAO / "so_lieu"
RES = ROOT / "results" / "huim_opt"
DIAGRAM.mkdir(parents=True, exist_ok=True)
SO_LIEU.mkdir(parents=True, exist_ok=True)

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, PAPER = "#e1e0d9", "#c3c2b7", "#ffffff"
MODEL_COLOR = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
MODEL_NAME = {"A": "Model A (p = 1)", "B": "Model B (p = MI)",
              "C": "Model C (p = MI×IDF)"}
BUILDING_COLOR = {0: "#6250d6", 1: "#eda100", 2: "#008300"}
SCOPE_STYLE = {"global": "-", "per_building": "--"}
SCOPE_NAME = {"global": "HUIM chung 3 tòa", "per_building": "HUIM theo từng tòa"}
HIGHLIGHT = "#d03b3b"          # chỉ dùng để khoanh cấu hình được chọn
FILL_SOFT = "#f2f4f8"

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.labelsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "legend.fontsize": 8.5,
    "lines.linewidth": 2.0, "lines.markersize": 6,
    "figure.facecolor": PAPER, "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER, "svg.fonttype": "none",
})


def vn(x: float, nd: int = 2) -> str:
    """Số kiểu Việt Nam: dấu phẩy thập phân, dấu chấm phân nghìn."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def theta_txt(th: float) -> str:
    """minUtil θ dạng chữ, giữ đủ chữ số của các mốc PHASE H (1,9294 %, 1,7321 %)."""
    s = f"{th:g}".replace(".", ",")
    return f"{s} %"


def luu(fig, ten: str, nguon: str | None = None, dpi: int = 200) -> Path:
    """Lưu PNG (dùng trong Word/PowerPoint) và SVG; `nguon` = dòng chú thích nguồn
    số liệu đặt dưới hình."""
    if nguon:
        fig.text(0.0, -0.02, nguon, fontsize=7.2, color=MUTED, ha="left",
                 va="top", transform=fig.transFigure, wrap=True)
    p = DIAGRAM / f"{ten}.png"
    fig.savefig(p, dpi=dpi, bbox_inches="tight", pad_inches=0.12)
    fig.savefig(DIAGRAM / f"{ten}.svg", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return p
