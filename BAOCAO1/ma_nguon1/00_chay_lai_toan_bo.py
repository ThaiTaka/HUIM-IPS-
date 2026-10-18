"""Chạy lại toàn bộ BAOCAO1 theo thứ tự.

    python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py            # thí nghiệm + báo cáo
    python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py --bao-cao  # chỉ dựng lại số liệu, hình, docx, pptx

Cần Python 3.12+ với numpy, pandas, scikit-learn, matplotlib, psutil, openpyxl,
python-docx, python-pptx (requirements.txt ở thư mục gốc dự án).
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
env = dict(os.environ, PYTHONIOENCODING="utf-8")
buoc = ["02_tong_hop_so_lieu.py", "03_ve_bieu_do.py", "04_tao_bao_cao_word.py",
        "05_tao_slide_pptx.py", "06_tao_huong_dan_doc.py"]
if "--bao-cao" not in sys.argv:
    buoc.insert(0, "01_chay_thi_nghiem.py")
for name in buoc:
    print("==>", name, flush=True)
    subprocess.run([sys.executable, str(HERE / name)], check=True, env=env, cwd=HERE)
