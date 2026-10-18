"""Tính lại sai số trung bình từ các file du_doan/*.csv, chỉ dùng thư viện chuẩn.

    python kiem_tra_mean.py

Với mỗi tập test: sai số từng mẫu = sqrt((x_dự đoán - x_thật)^2 + (y_dự đoán - y_thật)^2)
nhân hệ số đổi ra mét thực địa; trung bình cộng được so với 01_ket_qua_tong_hop.csv.
"""
import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
tong_hop = {(r["dataset"], r["tap_test"]): r
            for r in csv.DictReader(open(HERE / "01_ket_qua_tong_hop.csv", encoding="utf-8"))}
loi = 0
for (ds, tap), r in tong_hop.items():
    he_so = float(r["he_so_met"])
    sai_so, dung = [], 0
    for d in csv.DictReader(open(HERE / "du_doan" / f"{ds}__{tap}.csv", encoding="utf-8")):
        e = math.hypot(float(d["pred_x"]) - float(d["true_x"]),
                       float(d["pred_y"]) - float(d["true_y"])) * he_so
        sai_so.append(e)
        dung += f"{d['true_building']}_{d['true_floor']}" == d["pred_building_floor"]
    tb = sum(sai_so) / len(sai_so)
    s = sorted(sai_so)
    n = len(s)
    tv = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    khop = (abs(round(tb, 4) - float(r["sai_so_tb_m"])) < 1e-4
            and abs(round(tv, 4) - float(r["trung_vi_m"])) < 1e-4
            and abs(round(dung / n, 6) - float(r["dung_toa_tang"])) < 1e-5)
    loi += not khop
    print(f"{r['ten']:<22} {tap:<15} n={n:<5} TB tính lại {tb:8.4f} m | báo cáo {float(r['sai_so_tb_m']):8.4f} m"
          f" | trung vị {tv:7.4f} m | đúng tòa+tầng {dung / n:.4f} | {'KHỚP' if khop else 'LỆCH'}")
print("Tất cả khớp." if not loi else f"{loi} tập test lệch.")
