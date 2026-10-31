"""Tính lại sai số V7 từ các tệp du_doan/*.csv, chỉ dùng thư viện chuẩn.

    python kiem_tra_V7.py

Với mỗi mô hình: sai số từng mẫu = sqrt((x_dự đoán - x_thật)^2 + (y_dự đoán - y_thật)^2) × g (g = 0,766126, đổi toạ độ
Web-Mercator ra mét thực địa); trung bình, trung vị, P90 và độ chính xác tòa+tầng được so với 00_ket_qua_tong_hop_V7.csv.
Với V7-C2 còn dựng lại toạ độ từ 30 trọng số và tâm 30 ô (mo_hinh_uji_cells.csv), và tính lại dev out-of-fold.
"""
import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = 0.766126


def percentile(sorted_values, q):
    k = (len(sorted_values) - 1) * q            # nội suy tuyến tính, giống numpy.percentile và PERCENTILE của Excel
    f, c = math.floor(k), math.ceil(k)
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def main():
    loi = 0
    for r in csv.DictReader(open(HERE / "00_ket_qua_tong_hop_V7.csv", encoding="utf-8")):
        sai_so, dung = [], 0
        for d in csv.DictReader(open(HERE / r["file"], encoding="utf-8")):
            e = math.hypot(float(d["pred_x"]) - float(d["true_x"]), float(d["pred_y"]) - float(d["true_y"])) * G
            sai_so.append(e)
            dung += f"{d['true_building']}_{d['true_floor']}" == d["pred_building_floor"]
        n = len(sai_so)
        s = sorted(sai_so)
        tb = sum(sai_so) / n
        tv = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        p90 = percentile(s, 0.9)
        khop = (abs(round(tb, 4) - float(r["sai_so_tb_m"])) < 1e-4 and abs(round(tv, 4) - float(r["trung_vi_m"])) < 1e-4
                and abs(round(p90, 4) - float(r["p90_m"])) < 1e-4 and abs(round(dung / n, 6) - float(r["dung_toa_tang"])) < 1e-5)
        loi += not khop
        print(f"{r['mo_hinh']:<44} n={n:<5} TB {tb:8.4f} m | báo cáo {float(r['sai_so_tb_m']):8.4f} m | trung vị {tv:7.4f} | P90 {p90:8.4f} "
              f"| đúng tòa+tầng {dung / n:.4f} | {'KHỚP' if khop else 'LỆCH'}")
    # V7-C2: dựng lại toạ độ từ trọng số và tâm ô
    cells = [(float(c["x"]), float(c["y"])) for c in csv.DictReader(open(HERE / "mo_hinh_uji_cells.csv", encoding="utf-8"))]
    lech, tong_w_min, tong_w_max, e_tb, n = 0.0, 9.0, 0.0, 0.0, 0
    for d in csv.DictReader(open(HERE / "du_doan" / "V7C2.csv", encoding="utf-8")):
        w = [float(d[f"cell{j}_weight"]) for j in range(1, 31)]
        idx = [int(d[f"cell{j}_index"]) for j in range(1, 31)]
        ox, oy = cells[idx[0]]                                      # gốc cục bộ để tránh mất chữ số trên toạ độ 4,9e6
        x = ox + sum(wj * (cells[i][0] - ox) for wj, i in zip(w, idx))
        y = oy + sum(wj * (cells[i][1] - oy) for wj, i in zip(w, idx))
        lech = max(lech, abs(x - float(d["pred_x"])), abs(y - float(d["pred_y"])))
        tong_w_min, tong_w_max = min(tong_w_min, sum(w)), max(tong_w_max, sum(w))
        e_tb += math.hypot(x - float(d["true_x"]), y - float(d["true_y"])) * G
        n += 1
    ok2 = lech < 1e-6 and abs(1 - tong_w_min) < 1e-9 and abs(1 - tong_w_max) < 1e-9
    loi += not ok2
    print(f"V7-C2: dựng lại (x̂, ŷ) = Σ w·(x, y): lệch toạ độ lớn nhất {lech:.2e}; tổng trọng số {tong_w_min:.12f}…{tong_w_max:.12f}; "
          f"sai số TB từ toạ độ dựng lại {e_tb / n:.4f} m | {'KHỚP' if ok2 else 'LỆCH'}")
    # dev out-of-fold
    s6 = s7 = 0.0
    k = 0
    a6 = a7 = 0.0
    m = 0
    for d in csv.DictReader(open(HERE / "du_doan_dev" / "dev_oof_V6star_V7C2.csv", encoding="utf-8")):
        e6 = math.hypot(float(d["v6star_x"]) - float(d["true_x"]), float(d["v6star_y"]) - float(d["true_y"])) * G
        e7 = math.hypot(float(d["v7c2_x"]) - float(d["true_x"]), float(d["v7c2_y"]) - float(d["true_y"])) * G
        a6, a7, m = a6 + e6, a7 + e7, m + 1
        if int(d["n_ap"]) >= 1:
            s6, s7, k = s6 + e6, s7 + e7, k + 1
    print(f"Dev out-of-fold, vân tay có thông tin (n={k}): V6* {s6 / k:.4f} m, V7-C2 {s7 / k:.4f} m | tất cả (n={m}): V6* {a6 / m:.4f} m, V7-C2 {a7 / m:.4f} m")
    ref = {"v6": 6.2087, "v7": 5.7017}
    ok3 = abs(round(s6 / k, 4) - ref["v6"]) < 1e-4 and abs(round(s7 / k, 4) - ref["v7"]) < 1e-4
    loi += not ok3
    print("Dev khớp báo cáo." if ok3 else "Dev LỆCH báo cáo.")
    print("Tất cả khớp." if not loi else f"{loi} phép kiểm lệch.")


if __name__ == "__main__":
    main()
