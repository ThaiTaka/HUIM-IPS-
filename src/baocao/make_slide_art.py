"""Ảnh nền cho slide (vẽ từ dữ liệu thật của UJIIndoorLoc), không dùng biểu tượng.

  art_title.png    bản đồ các điểm huấn luyện (xanh nhạt) và vân tay kiểm tra (theo sai số) trên nền sẫm
  art_section.png  bản đồ các điểm tham chiếu, mờ, cho slide mở chương

Chạy: python src/baocao/make_slide_art.py <thư mục ra>   (build_slides.js tự gọi)
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NAVY = "#1F3A5F"


def main(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    tr = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv", usecols=["LONGITUDE", "LATITUDE"])
    P = pd.read_csv(ROOT / "results" / "huim_only" / "uji" / "v6" / "predictions" / "validationData.csv")
    x0, y0 = tr.LONGITUDE.min(), tr.LATITUDE.min()
    for name, alpha_t, show_test in (("art_title.png", 0.55, True), ("art_section.png", 0.28, False)):
        fig = plt.figure(figsize=(13.333, 7.5), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        fig.patch.set_facecolor(NAVY); ax.set_facecolor(NAVY)
        ax.scatter(tr.LONGITUDE - x0, tr.LATITUDE - y0, s=2.5, color="#7FB3BF", alpha=alpha_t, lw=0)
        if show_test:
            ax.scatter(P.true_x - x0, P.true_y - y0, s=7, c=P.err_m.clip(0, 15), cmap="YlOrBr", alpha=0.85, lw=0)
        ax.set_xlim(-400, 330); ax.set_ylim(-70, 330)
        ax.set_aspect("equal"); ax.axis("off")
        fig.savefig(dst / name, facecolor=NAVY)
        plt.close(fig)
    print("art:", sorted(p.name for p in dst.glob("art_*.png")))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
