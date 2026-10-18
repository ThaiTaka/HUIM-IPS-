"""BAOCAO1 / bước 1 - chạy toàn bộ thí nghiệm HUIM trên 4 bộ dữ liệu của thư mục
dataset-20261013T020803Z-1-001/dataset (UJI_LIB tầng 3, DLULIB, HCXY, HUS).
Huấn luyện trên tập train, chọn cấu hình trên 6 fold dev tách từ tập train, đánh giá
trên tập test (các file test của từng bộ dữ liệu).

    python BAOCAO1/ma_nguon/01_chay_thi_nghiem.py

Thứ tự (mỗi bước đọc kết quả của bước trước; kết quả đã có thì được dùng lại):
  1. src/huim_multi.py unions   union HUI chính xác ở mọi minUtil θ, 3 model x
                                {chung, từng vùng / tầng}, chạy song song
  2. src/huim_multi.py check    đối chiếu union với mọi lần chạy EFIM đã hoàn tất
  3. src/huim_multi.py steps    cho từng bộ dữ liệu:
        3  HUIM chung ở mọi θ, bộ định vị của bộ dữ liệu
        4  HUIM theo vùng / tầng (đoán vùng trước, rồi dùng AP của vùng)
        5  chọn lại bộ định vị trên dev, chỉ dùng AP HUIM
        6  quy tắc chọn AP từ HUI: union / top-n / frequent / weighted
        7  ensemble các cấu hình HUIM
  4. src/huim_multi.py step8    thời gian định vị, bộ nhớ radio map (chạy khi máy rảnh)
Cần có trước: results/multi_dataset/<bộ dữ liệu>/ (EFIM và bộ định vị của lần chạy
đa dữ liệu trước, src/run_multi_dataset.py). Mã nguồn thật nằm ở src/ (bản sao để
đọc: BAOCAO1/ma_nguon/ban_sao_src/). Toàn bộ mất khoảng 1 giờ trên máy 12 nhân.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
KEYS = ["uji_lib3", "dlulib", "hcxy", "hus_dedup"]


def chay(*args: str) -> None:
    print("==>", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, env=ENV, check=True)


if __name__ == "__main__":
    chay("src/huim_multi.py", "unions", "--workers", "10")
    chay("src/huim_multi.py", "check")
    for k in KEYS:
        chay("src/huim_multi.py", "steps", "--key", k, "--steps", "3", "4", "5", "6", "7")
    chay("src/huim_multi.py", "step8")
