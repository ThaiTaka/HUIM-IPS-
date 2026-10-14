"""Build verification/kiem_chung_da_dataset.xlsx - the cross-dataset results
recomputed by Excel formulas from the per-row prediction files, so every
accuracy and every metre figure of TONG_HOP_DA_DATASET.md can be checked by
hand.

Inputs (written by src/run_multi_dataset.py; nothing is computed here except
by Excel formulas)
  results/multi_dataset/<ds>/predictions/<test>__{study_knn,optimised}.csv
  results/multi_dataset/<ds>/positioning_ablation.csv     (reported values)
  results/multi_dataset/<ds>/huim_runs__*.csv
  results/multi_dataset/<ds>/timing.csv
  the training files of each dataset (neighbour coordinates)

Colour convention (as in verification/kiem_chung_thu_cong.xlsx)
  blue text   = a value copied from a data or result file
  black text  = an Excel formula
  green cell  = a check: KHỚP means the recomputation agrees

Sheets
  0_HuongDan      how to read the workbook
  1_TongHop       every dataset x test set x model: Excel vs reported
  2_minUtil       absolute minUtil = minUtil% x total utility, every run
  3_ThoiGian      ms per fingerprint = median of the timed runs / rows
  <ds>_<test>_S0 / _TU   one row per test fingerprint: correct building /
                  floor, error in metres; (x, y) rebuilt from the neighbours
                  and their weights for every row (first REBUILD_ROWS rows on
                  the large test sets)

Run: python src/make_multi_dataset_kit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter as L

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_multi_dataset_summary import ORDER, SHORT
from make_verification_kit import (BAD, BLACK, BOLD, NOTE, OK, TITLE, check,
                                   excel_recalculate, header, put)
from multi_datasets import load
from utils import PROJECT_ROOT, RESULTS, get_logger, load_json

LOG = get_logger("kit_multi")
ROOT = RESULTS / "multi_dataset"
OUT = PROJECT_ROOT / "verification" / "kiem_chung_da_dataset.xlsx"
REBUILD_ROWS = 1500          # rebuild (x, y) for every row up to this size


def pred_sheet(wb, name: str, P: pd.DataFrame, train: pd.DataFrame,
               factor: float, rep: pd.Series, title: str) -> dict:
    ws = wb.create_sheet(name)
    top = 14
    members = sorted({c.split("nbr")[0] for c in P.columns
                      if "nbr" in c and c.endswith("_weight")})
    k = max(int(c.split("nbr")[1].split("_")[0]) for c in P.columns
            if c.endswith("_weight"))
    n_reb = len(P) if len(P) <= REBUILD_ROWS else min(len(P), 300)
    xy = {(f, r): (x, y) for f, r, x, y in zip(
        train["SRC_FILE"], train["SRC_ROW"], train["X"], train["Y"])}
    one_file = train["SRC_FILE"].nunique() == 1
    tfile = train["SRC_FILE"].iloc[0]

    cols = ["File nguồn", "Dòng", "Tòa thật", "Tầng thật", "Tòa dự đoán",
            "Tầng dự đoán", "Đúng tòa? (1/0)", "Đúng tầng? (1/0)",
            "Đúng cả hai? (1/0)", "x thật", "y thật", "x dự đoán (file)",
            "y dự đoán (file)", "Sai số (đơn vị toạ độ)", "Sai số (m)",
            "x dựng lại = TB member Σw·x", "y dựng lại", "(x,y) khớp? (1/0)"]
    blocks = {}
    for m, pre in enumerate(members, start=1):
        blocks[pre] = len(cols) + 1
        for j in range(1, k + 1):
            cols += [f"M{m} láng giềng {j}: dòng train", f"M{m} x{j}",
                     f"M{m} y{j}", f"M{m} w{j}"]
    header(ws, top, cols)
    for j in range(1, len(cols) + 1):
        ws.column_dimensions[L(j)].width = 10.5
    ws.column_dimensions["A"].width = 30
    r0 = top + 1
    for i, r in enumerate(P.itertuples(index=False), start=r0):
        r = r._asdict()
        put(ws, i, 1, r["src_file"])
        put(ws, i, 2, int(r["src_row"]))
        for c, key in ((3, "true_building"), (4, "true_floor"),
                       (5, "pred_building"), (6, "pred_floor")):
            put(ws, i, c, int(r[key]))
        put(ws, i, 7, f"=IF(C{i}=E{i},1,0)", BLACK)
        put(ws, i, 8, f"=IF(D{i}=F{i},1,0)", BLACK)
        put(ws, i, 9, f"=G{i}*H{i}", BLACK)
        for c, key in ((10, "true_x"), (11, "true_y"), (12, "pred_x"),
                       (13, "pred_y")):
            put(ws, i, c, float(r[key]), fmt="0.0000")
        put(ws, i, 14, f"=SQRT((J{i}-L{i})^2+(K{i}-M{i})^2)", BLACK, "0.0000")
        put(ws, i, 15, f"=N{i}*$B$12", BLACK, "0.0000")
        if i - r0 >= n_reb:
            continue
        px, py = [], []
        for pre in members:
            b0 = blocks[pre]
            wx, wy, ww = [], [], []
            for j in range(1, k + 1):
                wcol = f"{pre}nbr{j}_weight"
                if wcol not in r or pd.isna(r[wcol]):
                    continue
                c = b0 + 4 * (j - 1)
                tr_row = int(r[f"{pre}nbr{j}_train_row"])
                f = r.get(f"{pre}nbr{j}_train_file", tfile)
                x, y = xy[(f, tr_row)]
                put(ws, i, c, tr_row if one_file else f"{f}:{tr_row}")
                put(ws, i, c + 1, float(x), fmt="0.0000")
                put(ws, i, c + 2, float(y), fmt="0.0000")
                put(ws, i, c + 3, float(r[wcol]), fmt="0.000000")
                ww.append(f"{L(c + 3)}{i}")
                wx.append(f"{L(c + 3)}{i}*{L(c + 1)}{i}")
                wy.append(f"{L(c + 3)}{i}*{L(c + 2)}{i}")
            px.append(f"({'+'.join(wx)})/({'+'.join(ww)})")
            py.append(f"({'+'.join(wy)})/({'+'.join(ww)})")
        put(ws, i, 16, f"=({'+'.join(px)})/{len(members)}", BLACK, "0.0000")
        put(ws, i, 17, f"=({'+'.join(py)})/{len(members)}", BLACK, "0.0000")
        put(ws, i, 18, f"=IF(AND(ABS(P{i}-L{i})<1E-6,ABS(Q{i}-M{i})<1E-6),1,0)",
            BLACK)
    r1 = r0 + len(P) - 1
    ws["A1"] = title
    ws["A1"].font = TITLE
    put(ws, 2, 1, "Chỉ số", BOLD)
    put(ws, 2, 2, "Excel tính", BOLD)
    put(ws, 2, 3, "Báo cáo (positioning_ablation.csv)", BOLD)
    put(ws, 2, 4, "Kiểm tra", BOLD)
    summary = [
        ("Số fingerprint", f"=COUNT(B{r0}:B{r1})", rep["test_n_test"], "0"),
        ("Độ chính xác tòa", f"=AVERAGE(G{r0}:G{r1})",
         rep["test_building_accuracy"], "0.0000%"),
        ("Độ chính xác tầng", f"=AVERAGE(H{r0}:H{r1})",
         rep["test_floor_accuracy"], "0.0000%"),
        ("Độ chính xác tòa + tầng", f"=AVERAGE(I{r0}:I{r1})",
         rep["test_joint_accuracy"], "0.0000%"),
        ("Sai số TB (m)", f"=AVERAGE(O{r0}:O{r1})", rep["test_mean_err_m"],
         "0.0000"),
        ("Trung vị (m)", f"=MEDIAN(O{r0}:O{r1})", rep["test_median_err_m"],
         "0.0000"),
        ("Phân vị 90 (m)", f"=PERCENTILE(O{r0}:O{r1},0.9)",
         rep["test_p90_err_m"], "0.0000"),
        ("Số dòng (x,y) dựng lại khớp file",
         f"=SUM(R{r0}:R{r0 + n_reb - 1})", n_reb, "0"),
    ]
    cells = {}
    for t, (text, f, v, fmt) in enumerate(summary, start=3):
        put(ws, t, 1, text, BOLD)
        put(ws, t, 2, f, BLACK, fmt)
        put(ws, t, 3, float(v), fmt=fmt)
        tol = 0.5 if fmt == "0" else 1e-4
        check(ws, t, 4, f'=IF(ABS(B{t}-C{t})<={tol},"{OK}","{BAD}")')
        cells[text] = f"'{name}'!B{t}"
    put(ws, 12, 1, "Hệ số ra mét thực địa", BOLD)
    put(ws, 12, 2, float(factor), fmt="0.000000")
    put(ws, 13, 1, f"(x,y) dựng lại cho {n_reb} / {len(P)} dòng đầu; đủ "
                   "láng giềng của mọi dòng nằm trong file CSV dự đoán.", NOTE)
    ws.freeze_panes = ws.cell(row=r0, column=3)
    return cells


def sheet_guide(wb, n_sheets: int) -> None:
    ws = wb.active
    ws.title = "0_HuongDan"
    lines = [
        ("Kiểm chứng kết quả HUIM-IPS trên nhiều bộ dữ liệu", TITLE),
        ("", None),
        ("Màu chữ xanh dương = số chép từ file dữ liệu / file kết quả "
         "(đầu vào). Màu đen = công thức Excel. Ô xanh lá = phép kiểm tra; "
         f"'{OK}' nghĩa là Excel tính lại ra đúng số đã báo cáo.", None),
        ("", None),
        ("1_TongHop: mỗi dòng là một bộ dữ liệu x tập test x mô hình (S0 = k-NN "
         "của nghiên cứu, TU = mô hình tối ưu PHASE I3). Cột 'Excel tính' lấy "
         "từ sheet chi tiết tương ứng.", None),
        ("Sheet <bộ>_<test>_S0 / _TU: mỗi dòng là một fingerprint test. Đúng "
         "tòa = (tòa dự đoán = tòa thật); đúng tầng tương tự; sai số = căn "
         "bậc hai ((x thật - x dự đoán)^2 + (y thật - y dự đoán)^2) x hệ số "
         "ra mét (ô B12).", None),
        ("(x, y) dự đoán = trung bình các member của Σ w_j · (x_j, y_j) / Σ w_j "
         "trên các láng giềng được liệt kê (dòng của file train, toạ độ, "
         "trọng số). Cột R = 1 khi Excel dựng lại đúng (x, y) trong file.",
         None),
        ("2_minUtil: minUtil tuyệt đối = minUtil% x tổng utility của CSDL, cho "
         "mọi lần chạy EFIM.", None),
        ("3_ThoiGian: thời gian không tính tay được; sheet cho các lần đo gốc "
         "và công thức trung vị -> ms / fingerprint.", None),
        ("", None),
        (f"Tổng số sheet chi tiết: {n_sheets}.", None),
    ]
    for i, (t, font) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=1, value=t)
        if font is not None:
            c.font = font
    ws.column_dimensions["A"].width = 150


def sheet_minutil(wb, runs: pd.DataFrame) -> None:
    ws = wb.create_sheet("2_minUtil")
    header(ws, 1, ["Bộ dữ liệu", "run_tag", "Trạng thái", "Tổng utility CSDL",
                   "minUtil %", "minUtil tuyệt đối (Excel)",
                   "minUtil tuyệt đối (file)", "Kiểm tra", "Số HUI",
                   "Số WAP trong HUI", "Thời gian EFIM (s)"],
           [16, 34, 22, 18, 10, 18, 18, 10, 10, 10, 12])
    for i, r in enumerate(runs.itertuples(index=False), start=2):
        put(ws, i, 1, r.dataset)
        put(ws, i, 2, r.run_tag)
        put(ws, i, 3, r.status)
        put(ws, i, 4, float(r.total_db_utility), fmt="0.000")
        put(ws, i, 5, float(r.rel_minutil_pct), fmt="0.0000")
        put(ws, i, 6, f"=D{i}*E{i}/100", BLACK, "0.000")
        put(ws, i, 7, float(r.abs_minutil), fmt="0.000")
        check(ws, i, 8, f'=IF(ABS(F{i}-G{i})<=0.001*MAX(1,ABS(G{i})),'
                        f'"{OK}","{BAD}")')
        put(ws, i, 9, int(r.n_huis))
        put(ws, i, 10, int(r.unique_waps_in_huis))
        put(ws, i, 11, float(r.runtime_s), fmt="0.000")
    ws.freeze_panes = "C2"


def sheet_timing(wb, T: pd.DataFrame) -> None:
    import json
    ws = wb.create_sheet("3_ThoiGian")
    header(ws, 1, ["Bộ dữ liệu", "Tập test", "Tập WAP", "Số WAP", "Số dòng test",
                   "k-NN: lần 1 (s)", "lần 2", "lần 3", "k-NN ms/fp (Excel)",
                   "k-NN ms/fp (file)", "KT", "Tối ưu: lần 1 (s)", "lần 2",
                   "lần 3", "Tối ưu ms/fp (Excel)", "Tối ưu ms/fp (file)", "KT"],
           [16, 12, 44, 8, 10, 10, 10, 10, 12, 12, 8, 10, 10, 10, 12, 12, 8])
    for i, r in enumerate(T.itertuples(index=False), start=2):
        put(ws, i, 1, r.dataset)
        put(ws, i, 2, r.test_set)
        put(ws, i, 3, r.condition)
        put(ws, i, 4, int(r.n_waps))
        put(ws, i, 5, int(r.n_test))
        for base, samples, rep in ((6, r.study_samples_s, r.study_ms_per_fp),
                                   (12, r.opt_samples_s, r.opt_ms_per_fp)):
            for j, v in enumerate(json.loads(samples)):
                put(ws, i, base + j, float(v), fmt="0.0000")
            put(ws, i, base + 3, f"=MEDIAN({L(base)}{i}:{L(base + 2)}{i})"
                                 f"/E{i}*1000", BLACK, "0.0000")
            put(ws, i, base + 4, float(rep), fmt="0.0000")
            check(ws, i, base + 5, f'=IF(ABS({L(base + 3)}{i}-{L(base + 4)}{i})'
                                   f'<=0.001,"{OK}","{BAD}")')
    ws.freeze_panes = "D2"


def main() -> None:
    wb = Workbook()
    runs, timing, sheets = [], [], []
    for key in ORDER:
        d = ROOT / key
        if not (d / "positioning_ablation.csv").exists():
            continue
        b = load(key)
        A = pd.read_csv(d / "positioning_ablation.csv")
        final = load_json(d / "positioning.json")["stages"][-1]["stage"]
        for f in sorted(d.glob("huim_runs__*.csv")):
            runs.append(pd.read_csv(f).assign(dataset=SHORT[key]))
        if (d / "timing.csv").exists():
            timing.append(pd.read_csv(d / "timing.csv").assign(
                dataset=SHORT[key]))
        for ti, tname in enumerate(b.tests):
            for tag, file, stage in (("S0", "study_knn", "S0"),
                                     ("TU", "optimised", final)):
                P = pd.read_csv(d / "predictions" / f"{tname}__{file}.csv")
                rep = A[(A["test_set"] == tname) & (A["stage"] == stage)].iloc[0]
                name = f"{key}_{ti + 1}_{tag}"[:31]
                title = (f"{SHORT[key]} · {tname} · "
                         f"{'k-NN nghiên cứu (S0)' if tag == 'S0' else 'mô hình tối ưu (' + stage + ')'}"
                         f" · {rep['config']}")
                cells = pred_sheet(wb, name, P, b.train, b.ground_factor, rep,
                                   title)
                sheets.append((SHORT[key], tname, tag, cells, rep))
                LOG.info("sheet %s: %d rows", name, len(P))
    sheet_guide(wb, len(sheets))
    ws = wb.create_sheet("1_TongHop", 1)
    header(ws, 1, ["Bộ dữ liệu", "Tập test", "Mô hình", "Chỉ số", "Excel tính",
                   "Báo cáo", "Kiểm tra"], [18, 12, 8, 30, 14, 14, 10])
    i = 2
    for ds, tname, tag, cells, rep in sheets:
        for text, key, fmt in (("Độ chính xác tòa", "test_building_accuracy",
                                "0.0000%"),
                               ("Độ chính xác tầng", "test_floor_accuracy",
                                "0.0000%"),
                               ("Sai số TB (m)", "test_mean_err_m", "0.0000"),
                               ("Trung vị (m)", "test_median_err_m", "0.0000"),
                               ("Phân vị 90 (m)", "test_p90_err_m", "0.0000")):
            put(ws, i, 1, ds)
            put(ws, i, 2, tname)
            put(ws, i, 3, tag)
            put(ws, i, 4, text, BOLD)
            put(ws, i, 5, "=" + cells[text], BLACK, fmt)
            put(ws, i, 6, float(rep[key]), fmt=fmt)
            check(ws, i, 7, f'=IF(ABS(E{i}-F{i})<=0.0001,"{OK}","{BAD}")')
            i += 1
    ws.freeze_panes = "E2"
    if runs:
        sheet_minutil(wb, pd.concat(runs, ignore_index=True))
    if timing:
        sheet_timing(wb, pd.concat(timing, ignore_index=True))
    wb.calculation.fullCalcOnLoad = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_name(OUT.stem + ".__tmp__.xlsx")
    wb.save(tmp)
    tmp.replace(OUT)
    LOG.info("wrote %s (%d detail sheets)", OUT, len(sheets))
    excel_recalculate(OUT)


if __name__ == "__main__":
    main()
