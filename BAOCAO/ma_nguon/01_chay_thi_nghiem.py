"""BAOCAO / bước 1 - chạy toàn bộ thí nghiệm HUIM trên UJIIndoorLoc (huấn luyện trên
trainingData, chọn cấu hình trên dev, đánh giá trên tập test = validationData).

    python BAOCAO/ma_nguon/01_chay_thi_nghiem.py

Thứ tự (mỗi bước đọc kết quả của bước trước; kết quả đã có thì được dùng lại):
  1. src/run_union_levels.py   union HUI chính xác ở mọi minUtil θ, cho 3 model x
                               {chung 3 tòa, tòa 0, tòa 1, tòa 2}, chạy song song
  2. src/check_union_search.py đối chiếu union với mọi lần chạy EFIM đã hoàn tất
  3. src/run_huim_opt.py --step 2 3 4 6 7 8
        2  Model A / B / C tại các θ mà EFIM liệt kê đủ
        3  lưới θ, HUIM chung 3 tòa
        4  lưới θ, HUIM riêng từng tòa (đoán tòa trước, rồi dùng AP của tòa đó)
        6  quy tắc chọn AP từ HUI: union / top-n / frequent / weighted
        7  ensemble các cấu hình HUIM
        8  thời gian định vị, bộ nhớ radio map, thời gian dựng mô hình
Mã nguồn thật nằm ở src/ (bản sao để đọc: BAOCAO/ma_nguon/ban_sao_src/).
Toàn bộ mất khoảng 2-3 giờ trên máy 12 nhân.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def chay(*args: str) -> None:
    print("==>", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, env=ENV, check=True)


if __name__ == "__main__":
    chay("src/run_union_levels.py", "global", "b0", "b1", "b2")
    chay("src/check_union_search.py")
    chay("src/run_huim_opt.py", "--step", "2", "3", "4", "6", "7", "8")
