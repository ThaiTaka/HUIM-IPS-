"""Dựng bộ kiểm chứng sai số V7 trong BAOCAO/so_lieu_V7 (giống BAOCAO/so_lieu):

    kiem_chung_V7_mean.xlsx   Excel có công thức tính lại sai số từng mẫu, trung bình, trung vị, P90, độ chính xác tầng
    kiem_tra_V7.py            Python chỉ dùng thư viện chuẩn: tính lại và so với 00_ket_qua_tong_hop_V7.csv
    du_doan/*.csv             dự đoán từng mẫu của validationData (V4, V5, V6, V6 tái tạo, V7-A, V7-B, V7-C1, V7-C2, V7-D)
    du_doan_dev/dev_oof_V6star_V7C2.csv   toạ độ dự đoán out-of-fold của dev (V6* và V7-C2)
    mo_hinh_uji_cells.csv     toạ độ 933 ô tham chiếu
    00_ket_qua_tong_hop_V7.csv, kiem_chung_V7.json, HUONG_DAN_KIEM_CHUNG.md

Chạy: python src/baocao/make_so_lieu_kit_v7.py        (sau đó recalc_xlsx.ps1 để Excel lưu giá trị đã tính)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from v7.common import GF, load_cache  # noqa: E402
from v7.experiments import load_oof  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import load_dev, oof_v6  # noqa: E402

UJI = ROOT / "results" / "huim_only" / "uji"
V7 = UJI / "v7"
OUT = ROOT / "BAOCAO" / "so_lieu_V7"
MODELS = [  # (tên sheet, nhãn, tệp nguồn)
    ("V4_luu", "V4 (dự đoán đã lưu)", UJI / "predictions" / "validationData.csv"),
    ("V5_luu", "V5 (dự đoán đã lưu)", UJI / "v5" / "predictions" / "validationData.csv"),
    ("V6_luu", "V6 (dự đoán đã lưu)", UJI / "v6" / "predictions" / "validationData.csv"),
    ("V6_tai_tao", "V6 (tái tạo ở V7)", V7 / "predictions" / "V6_reproduced.csv"),
    ("V7A", "V7-A hợp nhất thích ứng", V7 / "predictions" / "V7_A.csv"),
    ("V7B", "V7-B tối ưu trực tiếp", V7 / "predictions" / "B_base.csv"),
    ("V7C1", "V7-C1 (+ HUI rel)", V7 / "predictions" / "C_rel.csv"),
    ("V7C2", "V7-C2 (+ rel + abs mức-3) — mô hình chọn", V7 / "predictions" / "C_rel_absL3.csv"),
    ("V7D", "V7-D (+ HUI cấp tầng)", V7 / "predictions" / "D_hier.csv"),
]
HDR = PatternFill("solid", fgColor="1F3A5F")
SOFT = PatternFill("solid", fgColor="E6F0F2")
BOLD = Font(bold=True)
WHITE = Font(bold=True, color="FFFFFF")


def hdr(ws, row, labels):
    for j, t in enumerate(labels, 1):
        c = ws.cell(row, j, t)
        c.fill, c.font, c.alignment = HDR, WHITE, Alignment(horizontal="center", vertical="center", wrap_text=True)


def stats_from_csv(f: Path) -> dict:
    d = pd.read_csv(f)
    e = np.hypot(d.pred_x - d.true_x, d.pred_y - d.true_y).to_numpy() * GF
    ok = (d.true_building.astype(str) + "_" + d.true_floor.astype(str)) == d.pred_building_floor.astype(str)
    return {"n": int(len(d)), "mean": float(e.mean()), "median": float(np.median(e)), "p90": float(np.percentile(e, 90)),
            "floor": float(ok.mean())}


def build_summary_csv() -> dict:
    rep = {}
    rows = []
    for key, label, f in MODELS:
        s = stats_from_csv(f)
        rep[key] = s
        rows.append({"sheet": key, "mo_hinh": label, "file": f"du_doan/{key}.csv", "so_mau": s["n"], "sai_so_tb_m": round(s["mean"], 4),
                     "trung_vi_m": round(s["median"], 4), "p90_m": round(s["p90"], 4), "dung_toa_tang": round(s["floor"], 6), "he_so_met": GF})
    pd.DataFrame(rows).to_csv(OUT / "00_ket_qua_tong_hop_V7.csv", index=False, encoding="utf-8", lineterminator="\n")
    return rep


def copy_predictions() -> None:
    (OUT / "du_doan").mkdir(exist_ok=True)
    for key, _l, f in MODELS:
        shutil.copyfile(f, OUT / "du_doan" / f"{key}.csv")
    shutil.copyfile(UJI / "model" / "cells.csv", OUT / "mo_hinh_uji_cells.csv")
    shutil.copyfile(V7 / "verification.json", OUT / "kiem_chung_V7.json")


def dev_csv() -> pd.DataFrame:
    D = load_dev()
    P = oof_v6(D)
    O = load_oof("C_rel_absL3")
    rows = []
    for k, d in enumerate(D):
        x6, _w = fuse(P[k].astype(np.float64), d["cxy"], rule="v6", m=20, T=2.0)
        rows.append(pd.DataFrame({"fold": k, "dvi": d["dvi"], "phone": d["phone"], "n_ap": d["F"][:, 0, 13].astype(int),
                                  "true_x": d["true"][:, 0], "true_y": d["true"][:, 1], "v6star_x": x6[:, 0], "v6star_y": x6[:, 1],
                                  "v7c2_x": O[k][0][:, 0], "v7c2_y": O[k][0][:, 1]}))
    df = pd.concat(rows, ignore_index=True)
    (OUT / "du_doan_dev").mkdir(exist_ok=True)
    df.to_csv(OUT / "du_doan_dev" / "dev_oof_V6star_V7C2.csv", index=False, float_format="%.9f", lineterminator="\n")
    return df


def sheet_simple(wb, key, label, f: Path, row0=7):
    d = pd.read_csv(f)
    ws = wb.create_sheet(key)
    n = len(d)
    ws["A1"] = label
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"], ws["B2"] = "Hệ số mét g", GF
    last = row0 + n - 1
    ws["A3"], ws["B3"] = "Sai số trung bình (m)", f"=AVERAGE(F{row0}:F{last})"
    ws["A4"], ws["B4"] = "Trung vị (m)", f"=MEDIAN(F{row0}:F{last})"
    ws["A5"], ws["B5"] = "P90 (m)", f"=PERCENTILE(F{row0}:F{last},0.9)"
    ws["D3"], ws["E3"] = "Đúng tòa+tầng", f"=SUM(I{row0}:I{last})/COUNT(I{row0}:I{last})"
    ws["D4"], ws["E4"] = "Số mẫu", f"=COUNT(F{row0}:F{last})"
    ws["D5"], ws["E5"] = "Tổng sai số (m)", f"=SUM(F{row0}:F{last})"
    hdr(ws, row0 - 1, ["src_row", "true_x", "true_y", "pred_x", "pred_y", "sai số (m) = g·√((x̂−x)²+(ŷ−y)²)", "tòa_tầng thật", "tòa_tầng dự đoán", "đúng (1/0)"])
    for r, rec in enumerate(d.itertuples(index=False), row0):
        ws.cell(r, 1, int(rec.src_row))
        ws.cell(r, 2, float(rec.true_x)); ws.cell(r, 3, float(rec.true_y)); ws.cell(r, 4, float(rec.pred_x)); ws.cell(r, 5, float(rec.pred_y))
        ws.cell(r, 6, f"=SQRT((D{r}-B{r})^2+(E{r}-C{r})^2)*$B$2")
        ws.cell(r, 7, f"{rec.true_building}_{rec.true_floor}"); ws.cell(r, 8, str(rec.pred_building_floor))
        ws.cell(r, 9, f"=IF(G{r}=H{r},1,0)")
    for c, w in zip("ABCDEFGHI", (10, 14, 16, 14, 16, 30, 14, 16, 10)):
        ws.column_dimensions[c].width = w
    ws.column_dimensions["A"].width = 24
    ws.freeze_panes = f"A{row0}"
    return ws


def sheet_main(wb):
    """V7-C2: dựng lại toạ độ từ 30 trọng số và 30 tâm ô, rồi tính sai số."""
    d = pd.read_csv(V7 / "predictions" / "C_rel_absL3.csv")
    cells = pd.read_csv(UJI / "model" / "cells.csv")
    cx, cy = cells.x.to_numpy(), cells.y.to_numpy()
    ws = wb.create_sheet("V7C2_dung_lai_toa_do")
    row0 = 8
    n = len(d)
    last = row0 + n - 1
    ws["A1"] = "V7-C2 trên validationData: dựng lại (x̂, ŷ) = Σ wᵢ·(xᵢ, yᵢ) từ 30 trọng số và tâm 30 ô, rồi sai số"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"], ws["B2"] = "Hệ số mét g", GF
    ws["A3"], ws["B3"] = "Sai số TB (từ toạ độ dựng lại)", None
    ws["A4"], ws["B4"] = "Sai số TB (từ toạ độ lưu trong tệp)", None
    ws["A5"], ws["B5"] = "Lệch toạ độ lớn nhất giữa hai cách (đơn vị toạ độ)", None
    ws["A6"], ws["B6"] = "Min trọng số / tổng trọng số nhỏ nhất / lớn nhất", None
    wc0, xc0, yc0 = 5, 5 + 30, 5 + 60                  # cột bắt đầu của w, x, y (1-based: E=5)
    colx, coly = yc0 + 30, yc0 + 31                    # toạ độ dựng lại
    colfx, colfy, cole, colee, coldev, colsw = coly + 1, coly + 2, coly + 3, coly + 4, coly + 5, coly + 6
    heads = ["src_row", "phone", "true_x", "true_y"] + [f"w{j}" for j in range(1, 31)] + [f"x{j}" for j in range(1, 31)] + \
            [f"y{j}" for j in range(1, 31)] + ["x̂ dựng lại", "ŷ dựng lại", "x̂ trong tệp", "ŷ trong tệp", "sai số (m) từ toạ độ dựng lại",
                                                 "sai số (m) từ toạ độ trong tệp", "lệch toạ độ", "Σ w"]
    hdr(ws, row0 - 1, heads)
    # cột A..D: src_row, phone, true_x, true_y -> A,B,C,D ; w bắt đầu cột E (5)
    for r, rec in enumerate(d.itertuples(index=False), row0):
        ws.cell(r, 1, int(rec.src_row)); ws.cell(r, 2, int(d.phone.iloc[r - row0]))
        ws.cell(r, 3, float(rec.true_x)); ws.cell(r, 4, float(rec.true_y))
        idx = [int(d[f"cell{j}_index"].iloc[r - row0]) for j in range(1, 31)]
        for j in range(30):
            ws.cell(r, wc0 + j, float(d[f"cell{j + 1}_weight"].iloc[r - row0]))
            ws.cell(r, xc0 + j, float(cx[idx[j]]))
            ws.cell(r, yc0 + j, float(cy[idx[j]]))
        wr = f"{L(wc0)}{r}:{L(wc0 + 29)}{r}"
        ws.cell(r, colx, f"=SUMPRODUCT({wr},{L(xc0)}{r}:{L(xc0 + 29)}{r})")
        ws.cell(r, coly, f"=SUMPRODUCT({wr},{L(yc0)}{r}:{L(yc0 + 29)}{r})")
        ws.cell(r, colfx, float(rec.pred_x)); ws.cell(r, colfy, float(rec.pred_y))
        ws.cell(r, cole, f"=SQRT(({L(colx)}{r}-C{r})^2+({L(coly)}{r}-D{r})^2)*$B$2")
        ws.cell(r, colee, f"=SQRT(({L(colfx)}{r}-C{r})^2+({L(colfy)}{r}-D{r})^2)*$B$2")
        ws.cell(r, coldev, f"=MAX(ABS({L(colx)}{r}-{L(colfx)}{r}),ABS({L(coly)}{r}-{L(colfy)}{r}))")
        ws.cell(r, colsw, f"=SUM({wr})")
    ws["B3"] = f"=AVERAGE({L(cole)}{row0}:{L(cole)}{last})"
    ws["B4"] = f"=AVERAGE({L(colee)}{row0}:{L(colee)}{last})"
    ws["B5"] = f"=MAX({L(coldev)}{row0}:{L(coldev)}{last})"
    ws["B6"] = f"=MIN({L(wc0)}{row0}:{L(wc0 + 29)}{last})"
    ws["C6"] = f"=MIN({L(colsw)}{row0}:{L(colsw)}{last})"
    ws["D6"] = f"=MAX({L(colsw)}{row0}:{L(colsw)}{last})"
    ws.freeze_panes = f"E{row0}"
    ws.column_dimensions["A"].width = 44
    return ws


def sheet_example(wb):
    ex = json.load(open(OUT / "du_lieu_bao_cao_V7.json", encoding="utf-8"))["example"]
    ws = wb.create_sheet("Vi_du_mot_truy_van")
    ws["A1"] = f"Ví dụ: hàng {ex['src_row']} của validationData (truy vấn có sai số V7 đúng bằng trung vị). Δ = tâm ô − vị trí thật (đơn vị toạ độ)"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"], ws["B2"] = "Hệ số mét g", GF
    hdr(ws, 4, ["#", "ô", "Δx", "Δy", "khoảng cách tới vị trí thật (m)", "w V6*", "w V7", "w V6*·Δx", "w V6*·Δy", "w V7·Δx", "w V7·Δy"])
    r0 = 5
    for k, c in enumerate(ex["cells"]):
        r = r0 + k
        ws.cell(r, 1, c["rank_hui"]); ws.cell(r, 2, c["cell"]); ws.cell(r, 3, c["dx"]); ws.cell(r, 4, c["dy"])
        ws.cell(r, 5, f"=SQRT(C{r}^2+D{r}^2)*$B$2"); ws.cell(r, 6, c["w6"]); ws.cell(r, 7, c["w7"])
        ws.cell(r, 8, f"=F{r}*C{r}"); ws.cell(r, 9, f"=F{r}*D{r}"); ws.cell(r, 10, f"=G{r}*C{r}"); ws.cell(r, 11, f"=G{r}*D{r}")
    r1 = r0 + len(ex["cells"]) - 1
    s = r1 + 2
    rows = [("Σ w (phải bằng 1)", f"=SUM(F{r0}:F{r1})", f"=SUM(G{r0}:G{r1})"),
            ("x̂ − x = Σ w·Δx", f"=SUM(H{r0}:H{r1})", f"=SUM(J{r0}:J{r1})"),
            ("ŷ − y = Σ w·Δy", f"=SUM(I{r0}:I{r1})", f"=SUM(K{r0}:K{r1})")]
    ws.cell(s - 1, 5, "V6*").font = BOLD; ws.cell(s - 1, 6, "V6*").font = BOLD; ws.cell(s - 1, 7, "V7").font = BOLD
    for k, (lab, f6, f7) in enumerate(rows):
        ws.cell(s + k, 5, lab); ws.cell(s + k, 6, f6); ws.cell(s + k, 7, f7)
    ws.cell(s + 3, 5, "Sai số (m) = g·√((x̂−x)²+(ŷ−y)²)")
    ws.cell(s + 3, 6, f"=SQRT(F{s + 1}^2+F{s + 2}^2)*$B$2"); ws.cell(s + 3, 7, f"=SQRT(G{s + 1}^2+G{s + 2}^2)*$B$2")
    ws.cell(s + 4, 5, "Sai số lưu trong tệp dự đoán (m)"); ws.cell(s + 4, 6, ex["v6"]["err_m"]); ws.cell(s + 4, 7, ex["v7"]["err_m"])
    ws.cell(s + 5, 5, "Kết luận"); ws.cell(s + 5, 6, f'=IF(ABS(F{s + 3}-F{s + 4})<0.000001,"KHỚP","LỆCH")'); ws.cell(s + 5, 7, f'=IF(ABS(G{s + 3}-G{s + 4})<0.000001,"KHỚP","LỆCH")')
    for c, w in zip("ABCDEFGHIJK", (6, 8, 14, 14, 36, 12, 12, 14, 14, 14, 14)):
        ws.column_dimensions[c].width = w
    return s


def sheet_dev(wb, df: pd.DataFrame):
    ws = wb.create_sheet("Dev_OOF")
    row0 = 9
    n = len(df)
    last = row0 + n - 1
    ws["A1"] = "Dev out-of-fold (6 fold theo điện thoại): V6* (V6, trọng số float64) và V7-C2; 'có thông tin' = n_ap ≥ 1"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"], ws["B2"] = "Hệ số mét g", GF
    hdr(ws, row0 - 1, ["fold", "phone", "n_ap", "true_x", "true_y", "V6* x̂", "V6* ŷ", "V7-C2 x̂", "V7-C2 ŷ", "sai số V6* (m)", "sai số V7-C2 (m)", "có thông tin"])
    for r, rec in enumerate(df.itertuples(index=False), row0):
        ws.cell(r, 1, int(rec.fold)); ws.cell(r, 2, int(rec.phone)); ws.cell(r, 3, int(rec.n_ap))
        for j, v in enumerate((rec.true_x, rec.true_y, rec.v6star_x, rec.v6star_y, rec.v7c2_x, rec.v7c2_y), 4):
            ws.cell(r, j, float(v))
        ws.cell(r, 10, f"=SQRT((F{r}-D{r})^2+(G{r}-E{r})^2)*$B$2"); ws.cell(r, 11, f"=SQRT((H{r}-D{r})^2+(I{r}-E{r})^2)*$B$2")
        ws.cell(r, 12, f"=IF(C{r}>=1,1,0)")
    ws["A3"], ws["B3"], ws["C3"] = "Sai số TB, vân tay có thông tin (m)", f"=AVERAGEIFS(J{row0}:J{last},L{row0}:L{last},1)", f"=AVERAGEIFS(K{row0}:K{last},L{row0}:L{last},1)"
    ws["A4"], ws["B4"], ws["C4"] = "Sai số TB, tất cả vân tay (m)", f"=AVERAGE(J{row0}:J{last})", f"=AVERAGE(K{row0}:K{last})"
    ws["A5"], ws["B5"], ws["C5"] = "Số vân tay có thông tin / tất cả", f"=SUM(L{row0}:L{last})", f"=COUNT(J{row0}:J{last})"
    ws["B2"].number_format = "0.000000"
    ws["D3"], ws["D4"] = "← V6*  |  V7-C2 →", "← V6*  |  V7-C2 →"
    for c, w in zip("ABCDEFGHIJKL", (40, 14, 14, 14, 16, 14, 16, 14, 16, 16, 18, 14)):
        ws.column_dimensions[c].width = w
    ws.freeze_panes = f"A{row0}"
    return ws


def sheet_total(wb, rep, ex_row):
    ws = wb["Tong_hop"]
    ws["A1"] = "Kiểm chứng sai số V7 trên validationData (1.111 vân tay): tính lại từ toạ độ thật và toạ độ dự đoán của từng mẫu"
    ws["A1"].font = Font(bold=True, size=13)
    hdr(ws, 3, ["Sheet", "Mô hình", "Số mẫu", "Sai số TB tính lại (m)", "Sai số TB trong báo cáo (m)", "Chênh", "Kết luận",
                "Trung vị tính lại", "Trung vị báo cáo", "P90 tính lại", "P90 báo cáo", "Đúng tòa+tầng tính lại", "Đúng tòa+tầng báo cáo"])
    for k, (key, label, _f) in enumerate(MODELS):
        r = 4 + k
        s = rep[key]
        ws.cell(r, 1, key); ws.cell(r, 2, label)
        ws.cell(r, 3, f"='{key}'!E4"); ws.cell(r, 4, f"='{key}'!B3"); ws.cell(r, 5, round(s["mean"], 4))
        ws.cell(r, 6, f"=D{r}-E{r}"); ws.cell(r, 7, f'=IF(ABS(F{r})<0.00005,"KHỚP","LỆCH")')
        ws.cell(r, 8, f"='{key}'!B4"); ws.cell(r, 9, round(s["median"], 4)); ws.cell(r, 10, f"='{key}'!B5"); ws.cell(r, 11, round(s["p90"], 4))
        ws.cell(r, 12, f"='{key}'!E3"); ws.cell(r, 13, round(s["floor"], 6))
        if key == "V7C2":
            for c in range(1, 14):
                ws.cell(r, c).fill = SOFT
                ws.cell(r, c).font = BOLD
    r = 4 + len(MODELS) + 1
    ws.cell(r, 1, "Kiểm tra bổ sung của mô hình chọn (V7-C2)").font = BOLD
    ws.cell(r + 1, 1, "Sai số TB dựng lại từ 30 trọng số × tâm ô (m)"); ws.cell(r + 1, 4, "='V7C2_dung_lai_toa_do'!B3")
    ws.cell(r + 2, 1, "Lệch toạ độ lớn nhất so với toạ độ lưu (đơn vị toạ độ)"); ws.cell(r + 2, 4, "='V7C2_dung_lai_toa_do'!B5")
    ws.cell(r + 3, 1, "Tổng trọng số nhỏ nhất / lớn nhất"); ws.cell(r + 3, 4, "='V7C2_dung_lai_toa_do'!C6"); ws.cell(r + 3, 5, "='V7C2_dung_lai_toa_do'!D6")
    ws.cell(r + 4, 1, "Dev OOF, V7-C2, vân tay có thông tin (m)"); ws.cell(r + 4, 4, "='Dev_OOF'!C3")
    ws.cell(r + 5, 1, "Dev OOF, V6*, vân tay có thông tin (m)"); ws.cell(r + 5, 4, "='Dev_OOF'!B3")
    ws.cell(r + 6, 1, "Ví dụ một truy vấn (hàng 335): sai số V7 dựng bằng tay (m)"); ws.cell(r + 6, 4, f"='Vi_du_mot_truy_van'!G{ex_row + 3}")
    ws.cell(r + 7, 1, "Ví dụ một truy vấn (hàng 335): sai số V6* dựng bằng tay (m)"); ws.cell(r + 7, 4, f"='Vi_du_mot_truy_van'!F{ex_row + 3}")
    for c, w in zip("ABCDEFGHIJKLM", (58, 44, 10, 18, 20, 10, 12, 16, 16, 14, 14, 18, 20)):
        ws.column_dimensions[c].width = w


PY_CHECK = '''"""Tính lại sai số V7 từ các tệp du_doan/*.csv, chỉ dùng thư viện chuẩn.

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
'''

GUIDE = """# Kiểm chứng sai số V7 (6,309 m trên validationData)

Ba cách kiểm tra độc lập; cả ba tính lại sai số từ **toạ độ thật** và **toạ độ dự đoán** của từng vân tay, rồi so với con số trong báo cáo.

1. **Excel** — mở `kiem_chung_V7_mean.xlsx`:
   - `Tong_hop`: cột *Kết luận* ghi KHỚP cho từng mô hình (V4, V5, V6, V6 tái tạo, V7-A, V7-B, V7-C1, V7-C2, V7-D).
   - Mỗi sheet mô hình: cột F tính sai số từng mẫu bằng `=SQRT((x̂−x)^2+(ŷ−y)^2)*g`; B3 là `AVERAGE` (sai số trung bình), B4 trung vị, B5 P90.
   - `V7C2_dung_lai_toa_do`: dựng lại (x̂, ŷ) = Σ wᵢ·(xᵢ, yᵢ) từ **30 trọng số và tâm 30 ô** bằng `SUMPRODUCT`, rồi tính sai số.
   - `Vi_du_mot_truy_van`: một vân tay thật (hàng 335), V6\\* sai 7,9938 m, V7 sai 4,6357 m, dựng bằng tay.
   - `Dev_OOF`: dev out-of-fold của V6\\* và V7-C2 (19.937 vân tay; 19.861 có ít nhất một AP).
2. **Python, chỉ thư viện chuẩn** — trong thư mục này chạy `python kiem_tra_V7.py`; script in KHỚP hoặc LỆCH cho từng mô hình, dựng lại toạ độ V7-C2 từ trọng số và tính lại dev.
3. **Chương trình kiểm chứng độc lập của dự án** — `kiem_chung_V7.json` lưu kết quả của `src/v7/verify_v7.py`: 16 phép kiểm, 0 thất bại
   (tính lại sai số, trọng số ≥ 0 và tổng bằng 1, tọa độ = tổng có trọng số của tâm ô, ô nằm trên tầng dự đoán, fold rời nhau theo điện thoại,
   cache cùng nguồn dữ liệu, không k-NN, EFIM = vét cạn, tái lập theo seed, V6 không bị đổi).

Hệ số mét: UJIIndoorLoc dùng toạ độ Web Mercator nên mét thực địa = đơn vị toạ độ × **0,766126**.

| Tệp | Nội dung |
|---|---|
| `00_ket_qua_tong_hop_V7.csv` | số liệu báo cáo (trung bình, trung vị, P90, đúng tòa+tầng) của từng mô hình |
| `du_doan/*.csv` | dự đoán từng mẫu của validationData; các tệp V7 kèm 30 ô ứng viên và 30 trọng số |
| `du_doan_dev/dev_oof_V6star_V7C2.csv` | toạ độ dự đoán out-of-fold của dev |
| `mo_hinh_uji_cells.csv` | toạ độ 933 ô tham chiếu (chỉ số ô = số dòng, từ 0) |
| `du_lieu_bao_cao_V7.json` | nguồn số liệu duy nhất của slide V7 |
| `kiem_chung_V7.json` | kết quả `verify_v7.py` |

Tự kiểm bằng tay một vân tay: lấy `pred_x, pred_y, true_x, true_y` của một dòng, tính √((x̂−x)²+(ŷ−y)²)×0,766126. Ví dụ hàng 335 của validationData: Δx = −0,99923; Δy = 5,96774; √(…) = 6,05050; × 0,766126 = 4,6357 m.
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    copy_predictions()
    rep = build_summary_csv()
    df = dev_csv()
    wb = Workbook()
    wb.active.title = "Tong_hop"
    for key, label, f in MODELS:
        sheet_simple(wb, key, label, OUT / "du_doan" / f"{key}.csv")
    sheet_main(wb)
    ex_row = sheet_example(wb)
    sheet_dev(wb, df)
    sheet_total(wb, rep, ex_row)
    wb.save(OUT / "kiem_chung_V7_mean.xlsx")
    (OUT / "kiem_tra_V7.py").write_text(PY_CHECK, encoding="utf-8", newline="\n")
    (OUT / "HUONG_DAN_KIEM_CHUNG.md").write_text(GUIDE, encoding="utf-8", newline="\n")
    print("xong:", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
