"""Kiểu dáng và hằng số dùng chung cho BAOCAO1 (4 bộ dữ liệu, matplotlib, tiếng Việt).

Màu gán cố định theo THỰC THỂ, không theo thứ hạng:
  * Model A / B / C          -> 3 ô đầu của bảng màu phân loại (giống BAOCAO)
  * ban đầu / tốt nhất       -> xám / xanh đậm
  * phạm vi HUIM             -> nét: chung = nét liền, theo vùng / tầng = nét đứt
Nhãn số ghi trực tiếp lên cột/điểm quan trọng, nên màu không bao giờ là kênh duy nhất.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BAOCAO = ROOT / "BAOCAO1"
DIAGRAM = BAOCAO / "diagram"
SO_LIEU = BAOCAO / "so_lieu"
RES = ROOT / "results" / "huim_multi"
DIAGRAM.mkdir(parents=True, exist_ok=True)
SO_LIEU.mkdir(parents=True, exist_ok=True)

KEYS = ["uji_lib3", "dlulib", "hcxy", "hus_dedup"]
TEN_DS = {"uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB", "hcxy": "HCXY",
          "hus_dedup": "HUS"}
TEN_DS_DAI = {"uji_lib3": "UJI_LIB tầng 3 (thư viện UJI, 25 tháng)",
              "dlulib": "DLULIB (1 tòa, 3 tầng)", "hcxy": "HCXY (1 tầng)",
              "hus_dedup": "HUS (1 phòng, 5 AP, đã bỏ dòng test bị chép từ train)"}
VUNG = {"uji_lib3": "vùng", "dlulib": "tầng", "hcxy": "vùng", "hus_dedup": None}
TAP_TEST = {"uji_lib3": {"test": "Test-01", "test2": "Test-02"},
            "dlulib": {"test": "Testing"}, "hcxy": {"test": "test_HCXY"},
            "hus_dedup": {"test": "testcase1", "test2": "testcase2"}}

TOA_DO = {
    "uji_lib3": "lưới toạ độ cục bộ, đơn vị mét",
    "dlulib": "lưới toạ độ cục bộ, đơn vị mét, điểm tham chiếu cách nhau 1,2 m; 3 tầng dùng chung lưới x, y",
    "hcxy": "toạ độ trong mapxy_HCXY.txt, không ghi đơn vị; đọc là mét (các điểm khảo sát gần nhau "
            "cách 0,59-1,2)",
    "hus_dedup": "lưới toạ độ trong hus_mapXY.txt, bước 0,5; đọc là mét",
}
NHOM_FOLD = {
    "uji_lib3": "theo tháng (mỗi fold bỏ ra trọn các tháng): hai tập test trải cùng 25 tháng như train và "
                "khác train ở lần thu thập; dữ liệu không có cột người dùng / thiết bị (một điện thoại)",
    "dlulib": "theo lần lấy mẫu (SampleTimes): tập test đo lại mọi vị trí train bằng cùng điện thoại, nên "
              "fold dev giữ mọi vị trí trong train và để ra các lần đo khác của chính vị trí đó",
    "hcxy": "theo vị trí (mỗi fold bỏ ra trọn các vị trí): không vị trí test nào là vị trí train",
    "hus_dedup": "dữ liệu không có cột người dùng / thiết bị / lần đo và tập test đo lại các vị trí train, "
                 "nên dùng 6 fold ngẫu nhiên theo dòng",
}

INK, INK2, MUTED ="#0b0b0b", "#52514e", "#898781"
GRID, AXIS, PAPER = "#e1e0d9", "#c3c2b7", "#ffffff"
MODEL_COLOR = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
MODEL_NAME = {"A": "Model A (p = 1)", "B": "Model B (p = MI)",
              "C": "Model C (p = MI×IDF)"}
START_COLOR, BEST_COLOR = "#9a9a9a", "#1c5cab"
DEV_COLOR, TEST_COLOR = "#86b6ef", "#1c5cab"
HIGHLIGHT = "#d03b3b"          # chỉ dùng để khoanh / kẻ θ của cấu hình được chọn
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
    s = f"{float(th):g}".replace(".", ",")
    return f"{s} %"


def cau_hinh() -> dict:
    return json.loads((SO_LIEU / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))


def luu(fig, ten: str, nguon: str | None = None, dpi: int = 200, nguon_y: float = -0.02) -> Path:
    """Lưu PNG (dùng trong Word/PowerPoint) và SVG; `nguon` = dòng nguồn số liệu dưới hình."""
    if nguon:
        fig.text(0.0, nguon_y, nguon, fontsize=7.2, color=MUTED, ha="left",
                 va="top", transform=fig.transFigure, wrap=True)
    p = DIAGRAM / f"{ten}.png"
    fig.savefig(p, dpi=dpi, bbox_inches="tight", pad_inches=0.12)
    fig.savefig(DIAGRAM / f"{ten}.svg", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return p
