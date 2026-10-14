"""Build report/HUIM_IPS_Mo_ta_cac_file_Python.docx - a Vietnamese guide to
every Python file of the project: what it is for, how it works, what it reads
and what it writes, plus the manual-verification procedure.

The descriptions are prose written here. Every NUMBER in the document is read
or recomputed at build time (line counts, test counts, EFIM's running example,
minUtil thresholds, positioning results, verification results), so the guide
cannot drift away from the code and the result files.

Run: python src/make_code_guide.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_builder import Doc, _rfonts
from utils import (FIGURES, METRICS, PROJECT_ROOT, REPORT, RESULTS, get_logger,
                   load_json)

LOG = get_logger("codeguide", "code_guide.log")
OUT = REPORT / "HUIM_IPS_Mo_ta_cac_file_Python.docx"
MONO = "Consolas"


# ------------------------------------------------------------------ helpers
def shade(cell, hex_fill: str) -> None:
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def cell_text(cell, text: str, bold: bool = False, size: float = 10.5,
              mono: bool = False) -> None:
    """Write text into a cell; '\n' starts a new paragraph inside the cell."""
    cell.text = ""
    for k, line in enumerate(str(text).split("\n")):
        par = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
        par.paragraph_format.space_after = Pt(1)
        r = par.add_run(line)
        r.bold = bold
        r.font.size = Pt(size)
        if mono:
            r.font.name = MONO
            r._element.get_or_add_rPr()
        else:
            _rfonts(r)


def kv_table(D: Doc, rows: list[tuple[str, str]], widths=(1.45, 5.05)) -> None:
    """Two-column 'label | content' table for one file."""
    t = D.d.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, content in rows:
        c0, c1 = t.add_row().cells
        cell_text(c0, label, bold=True)
        shade(c0, "E8EDF3")
        cell_text(c1, content, mono=label.startswith("Cách chạy"))
        c0.width, c1.width = Inches(widths[0]), Inches(widths[1])
    D.d.add_paragraph()


def grid(D: Doc, df: pd.DataFrame, widths: list[float], size: float = 9.5,
         caption: str | None = None) -> None:
    """A plain table with a shaded header row (optionally numbered)."""
    if caption:
        D.caption(caption, "Bảng")
    t = D.d.add_table(rows=1, cols=len(df.columns))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, c in enumerate(df.columns):
        cell_text(t.rows[0].cells[j], str(c), bold=True, size=size)
        shade(t.rows[0].cells[j], "DDE3EA")
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for j, c in enumerate(df.columns):
            cell_text(cells[j], "" if pd.isna(row[c]) else str(row[c]),
                      size=size)
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Inches(w)
    D.d.add_paragraph()


def code(D: Doc, text: str) -> None:
    for line in text.strip("\n").split("\n"):
        par = D.d.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.left_indent = Inches(0.3)
        r = par.add_run(line)
        r.font.name = MONO
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x73)
    D.d.add_paragraph()


def n_lines(rel: str) -> int:
    with open(PROJECT_ROOT / rel, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def vn(x: float, d: int = 2) -> str:
    """Vietnamese number format: 1.234,56"""
    return f"{x:,.{d}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")


def vn_int(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def count_tests() -> str:
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only",
                            "-q", "tests"], cwd=PROJECT_ROOT,
                           capture_output=True, text=True, timeout=300)
        m = re.search(r"(\d+) tests? collected", r.stdout)
        return m.group(1) if m else "?"
    except Exception:
        return "?"


# ---------------------------------------------------------- file catalogue
# group, path, purpose (one line), then the detailed rows
FILES: list[dict] = [
    # ---------------------------------------------------- infrastructure
    dict(group="Hạ tầng dùng chung", path="src/utils.py",
         short="Đường dẫn, tìm dữ liệu, log, JSON, thông tin máy, đo bộ nhớ",
         purpose="Các hàm và hằng số mà gần như mọi script khác import: vị trí "
                 "các thư mục, tìm hai file CSV, ghi log, ghi/đọc JSON, ghi lại "
                 "cấu hình máy, đo bộ nhớ đỉnh.",
         how="PROJECT_ROOT là thư mục cha của src/. Các hằng RESULTS, METRICS, "
             "FIGURES, REPORT, SLIDES… được tạo sẵn khi import.\n"
             "find_dataset(): tìm trainingData.csv / validationData.csv trong "
             "vài thư mục ứng viên; KHÔNG bao giờ ghi vào hai file đó.\n"
             "get_logger(): ghi đồng thời ra màn hình và results/logs/<tên>.log.\n"
             "JSONSafe/dump_json(): chuyển kiểu numpy sang JSON để không mất "
             "trường nào.\n"
             "environment_info(): OS, CPU, RAM, phiên bản Python và thư viện — "
             "được ghi vào mọi file kết quả.\n"
             "MemoryMonitor: một luồng nền lấy mẫu bộ nhớ RSS mỗi 20 ms (không "
             "dùng tracemalloc vì nó làm chậm chính phép đo thời gian).\n"
             "relocate(): neo lại đường dẫn tuyệt đối đã ghi trong file kết quả "
             "(ví dụ D:\\ips\\results\\…) về thư mục project hiện tại.",
         inputs="Không có — được import.",
         outputs="Hàm/hằng cho các module khác; tạo các thư mục kết quả nếu "
                 "chưa có.",
         run="(không chạy trực tiếp)",
         rel="Được import bởi hầu hết các script trong src/ và research/."),
    # ---------------------------------------------------------- data
    dict(group="Dữ liệu", path="src/inspect_data.py",
         short="PHASE A — audit chỉ-đọc hai file CSV",
         purpose="Hiểu dữ liệu TRƯỚC khi mô hình hoá: kiểm tra cấu trúc, tính "
                 "toàn vẹn và ý nghĩa của giá trị 100.",
         how="Đếm cột WAP thực tế (không giả định 520); đếm ô thiếu, dòng trùng; "
             "kiểm chứng '100 = không phát hiện' bằng phân bố giá trị (không có "
             "ô nào trong khoảng 1…99); thống kê RSSI, số AP phát hiện mỗi "
             "fingerprint; tìm bất thường (fingerprint rỗng, ô 0 dBm, SPACEID của "
             "validation bằng 0…); so USERID/PHONEID giữa hai split; tính SHA-256 "
             "của file để chứng minh không bị sửa.",
         inputs="ujiindoorloc/UJIndoorLoc/trainingData.csv, validationData.csv",
         outputs="results/data_summary.json",
         run="python src/inspect_data.py",
         rel="Kết quả được make_audit_report.py, verify_coordinates.py, báo cáo "
             "và slide đọc lại."),
    dict(group="Dữ liệu", path="src/verify_coordinates.py",
         short="Xác định hệ toạ độ LONGITUDE/LATITUDE (Web Mercator)",
         purpose="Bộ dữ liệu không ghi đơn vị toạ độ; script này xác định bằng "
                 "thực nghiệm để biết sai số đo theo mét có đúng không.",
         how="Lấy tâm hộp bao toạ độ; nghịch đảo từng phép chiếu ứng viên (Web "
             "Mercator EPSG:3857, UTM 30N/31N, độ WGS84); đo khoảng cách "
             "haversine tới campus Đại học Jaume I. Chỉ Web Mercator rơi đúng "
             "campus. Vì Web Mercator phóng đại khoảng cách 1/cos(vĩ độ) lần, "
             "sai số thực địa = sai số toạ độ × cos(vĩ độ).",
         inputs="results/data_summary.json",
         outputs="results/coordinate_system_verification.json (hệ số mặt đất)",
         run="python src/verify_coordinates.py",
         rel="Hệ số dùng trong ips_model.py (WEB_MERCATOR_GROUND_FACTOR)."),
    dict(group="Dữ liệu", path="src/make_audit_report.py",
         short="Viết results/data_audit.md từ JSON của audit",
         purpose="Biến số liệu audit thành văn bản đọc được.",
         how="Chỉ đọc JSON rồi chèn số vào văn bản; không tính gì mới, nên văn "
             "bản không thể lệch số liệu. Báo lỗi nếu chưa có kết quả hệ toạ độ.",
         inputs="results/data_summary.json, "
                "results/coordinate_system_verification.json",
         outputs="results/data_audit.md",
         run="python src/make_audit_report.py", rel="Sau inspect_data.py."),
    dict(group="Dữ liệu", path="src/preprocess_uji.py",
         short="Fingerprint → đặc trưng k-NN và giao dịch utility cho HUIM",
         purpose="Bước tiền xử lý dùng chung cho cả HUIM và định vị.",
         how="NOT_DETECTED = 100. fit_preprocessor() (CHỈ gọi trên trainingData) "
             "học RSSI min/max (−104 và 0 dBm).\n"
             "positive_representation(): 100 → 0; RSSI → 1 + (RSSI + 104)/104 × 99 "
             "(thang 1…100). 0 nghĩa là 'không có thông tin', không phải 'sóng "
             "yếu'.\n"
             "internal_utility_matrix(): làm tròn thành số nguyên q(i,T) ≥ 1.\n"
             "transactions(): mỗi dòng → một giao dịch {WAP: q} chỉ gồm các WAP "
             "được phát hiện.\n"
             "joint_label(): nhãn lớp 'BUILDINGID_FLOOR' (13 lớp).",
         inputs="DataFrame của hai CSV (load_splits() đọc chúng).",
         outputs="Ma trận đặc trưng, danh sách giao dịch, nhãn.",
         run="(module, được import)",
         rel="Dùng bởi utility_models, run_huim, run_ips, plots, …"),
    # ------------------------------------------------- HUIM model
    dict(group="Mô hình utility và HUIM", path="src/utility_models.py",
         short="Định nghĩa p(i) cho ba model A, B, C; cổng chống rò rỉ",
         purpose="Phần 'mô hình hoá HUIM cho IPS': dữ liệu Wi-Fi không có sẵn "
                 "số lượng q và đơn giá p, nên phải tự định nghĩa.",
         how="q(i,T) dùng chung = RSSI chuẩn hoá. Chỉ p(i) khác nhau:\n"
             "Model A: p(i) = 1 (đối chứng: chỉ cường độ và đồng xuất hiện).\n"
             "Model B: p(i) = I(A_i;Y) / max_j I(A_j;Y) — mutual information "
             "giữa trạng thái WAP (6 trạng thái: không phát hiện + 5 khoảng "
             "dBm) và nhãn tòa-tầng, tính từ histogram đồng thời.\n"
             "Model C: p(i) tỉ lệ với I(A_i;Y) × log(N/(1+support_i)) — phạt WAP "
             "xuất hiện khắp nơi.\n"
             "p luôn ≥ 1e-6 vì EFIM cần utility dương. "
             "build_external_utility(…, split_name) BÁO LỖI nếu split_name khác "
             "'training' — không thể vô tình ước lượng p từ validationData.",
         inputs="trainingData, Preprocessor, nhãn",
         outputs="UtilityModel: bảng p(i) + thông tin chẩn đoán",
         run="(module)", rel="Dùng bởi pilot, run_huim, run_huim_refine, plots."),
    dict(group="Mô hình utility và HUIM", path="src/huim/__init__.py",
         short="Gom API của gói huim",
         purpose="Cho phép 'from huim import EFIM, brute_force_hui, …'.",
         how="Chỉ import lại các hàm từ efim.py và brute_force.py.",
         inputs="—", outputs="—", run="(module)", rel="Gói src/huim/."),
    dict(group="Mô hình utility và HUIM", path="src/huim/brute_force.py",
         short="'Oracle' tính HUI đúng định nghĩa, không cắt tỉa",
         purpose="Chuẩn so sánh để chứng minh EFIM cài đặt đúng.",
         how="u(i,T) = q(i,T) × p(i); TU(T) = tổng u(i,T); u(X) = tổng u(X,T) "
             "trên các giao dịch chứa X; TWU(i) = tổng TU(T) trên các giao dịch "
             "chứa i. brute_force_hui() duyệt MỌI tổ hợp item (2^|I|), nên chỉ "
             "dùng cho CSDL nhỏ trong unit test.",
         inputs="Danh sách giao dịch (dict), bảng p, minUtil",
         outputs="Danh sách (itemset, utility, support)",
         run="(module)", rel="Dùng bởi tests/test_efim.py."),
    dict(group="Mô hình utility và HUIM", path="src/huim/efim.py",
         short="Thuật toán EFIM (Zida et al., 2017)",
         purpose="Khai phá MỌI tập mục hữu ích cao (u(X) ≥ minUtil) một cách "
                 "hiệu quả. Nguyên lý chi tiết và ví dụ ở Chương 3.",
         how="1. Tính TU và TWU; bỏ item có TWU < minUtil.\n"
             "2. Sắp item theo TWU tăng dần (thứ tự duyệt).\n"
             "3. Gộp các giao dịch giống hệt nhau (transaction merging).\n"
             "4. Fast Utility Counting: một lượt quét tính local utility (lu) và "
             "subtree utility (su) cho mọi item.\n"
             "5. Duyệt sâu (DFS): với mỗi item thuộc Primary (su ≥ minUtil), "
             "chiếu CSDL theo tiền tố mới (database projection), cộng utility — "
             "nếu ≥ minUtil thì xuất HUI; Secondary = item có lu ≥ minUtil.\n"
             "6. Dừng có kiểm soát khi quá 600 s hoặc 1.000.000 HUI "
             "(ABORTED_RESOURCE_LIMIT), giữ lại kết quả một phần.",
         inputs="Danh sách giao dịch {item: q}, bảng p, minUtil TUYỆT ĐỐI",
         outputs="Danh sách HUI (itemset, utility, support) + EFIMStats (số nút "
                 "đã duyệt, item còn lại sau TWU, số giao dịch được gộp…)",
         run="(module)", rel="Dùng bởi pilot, run_huim, run_huim_refine, "
                             "verify_huim."),
    dict(group="Mô hình utility và HUIM", path="src/feature_selection.py",
         short="Tập HUI → tập WAP được chọn (union / top-n)",
         purpose="Bước HUIM 'giúp' hệ định vị: chọn WAP từ các HUI.",
         how="union: mọi WAP xuất hiện trong ít nhất một HUI (minUtil là núm "
             "duy nhất).\n"
             "top-n: n WAP có utility_contribution(i) = tổng u(X)/|X| trên các "
             "HUI X chứa i (chia đều utility của mỗi HUI cho các thành viên).\n"
             "Kèm các thống kê thay thế và tương quan hạng Spearman giữa chúng; "
             "feature_reduction_pct = (1 − số chọn/520) × 100.",
         inputs="Danh sách HUI", outputs="WAP đã xếp hạng, thống kê từng WAP",
         run="(module)", rel="Dùng bởi run_huim, run_huim_refine."),
    # ----------------------------------------------------- mining
    dict(group="Thực nghiệm khai phá", path="src/pilot.py",
         short="PHASE G — chạy thử trên mẫu con để hiệu chỉnh lưới minUtil",
         purpose="Tìm vùng ngưỡng đáng quan tâm trước khi chạy toàn bộ dữ liệu.",
         how="Lấy mẫu phân tầng ~2.500 dòng; chạy EFIM ở lưới 5% → 0,01% tổng "
             "utility, giới hạn 120 s / 300.000 HUI; dừng hạ ngưỡng khi bị cắt.",
         inputs="trainingData.csv",
         outputs="results/metrics/pilot_runs.csv, results/pilot_summary.json",
         run="python src/pilot.py", rel="Kết quả định hướng lưới của run_huim."),
    dict(group="Thực nghiệm khai phá", path="src/run_huim.py",
         short="PHASE H — khai phá đầy đủ: 3 model × lưới minUtil",
         purpose="Chạy EFIM trên toàn bộ giao dịch của trainingData.",
         how="Với mỗi model: tổng utility CSDL; với mỗi ngưỡng %: minUtil tuyệt "
             "đối = tổng × % / 100; chạy EFIM trong MemoryMonitor; lưu HUI (đầy "
             "đủ nếu ≤ 50.000, luôn lưu top-1000) và thống kê từng WAP; ghi một "
             "dòng vào huim_runs.csv. Gặp lần chạy bị cắt thì dừng hạ ngưỡng.",
         inputs="trainingData.csv",
         outputs="results/metrics/huim_runs.csv, results/hui/*, "
                 "results/huim_summary.json",
         run="python src/run_huim.py", rel="Sau tests và pilot."),
    dict(group="Thực nghiệm khai phá", path="src/run_huim_refine.py",
         short="PHASE H2 — tinh chỉnh lưới quanh điểm chuyển pha",
         purpose="Tìm tập HUI phong phú nhất mà KHÔNG bị cắt ngang.",
         how="Lấy khoảng giữa ngưỡng chạy xong thấp nhất và ngưỡng bị cắt cao "
             "nhất, thử điểm giữa theo cấp số nhân (tối đa 3 lần); đủ 20.000 HUI "
             "thì dừng.",
         inputs="results/metrics/huim_runs.csv, trainingData.csv",
         outputs="Thêm dòng vào huim_runs.csv; results/huim_refinement.json",
         run="python src/run_huim_refine.py", rel="Sau run_huim."),
    # -------------------------------------------------- positioning
    dict(group="Định vị (IPS)", path="src/ips_model.py",
         short="Mô hình k-NN, giao thức đánh giá, độ đo, sai số mét",
         purpose="Định nghĩa CÙNG MỘT bộ phân loại cho mọi điều kiện.",
         how="select_knn_config(): chọn k, metric, weights MỘT lần trên phép chia "
             "75/25 của trainingData với đủ 520 WAP, rồi đóng băng.\n"
             "evaluate_once(): fit trên toàn bộ trainingData, dự đoán "
             "validationData đúng một lần; tòa/tầng/joint, macro F1, confusion "
             "matrix; toạ độ = trung bình có trọng số của chính các láng giềng.\n"
             "positioning_error(): khoảng cách Euclid theo toạ độ chiếu, và × "
             "hệ số Web Mercator (cos vĩ độ) ra mét thực địa.",
         inputs="Ma trận đặc trưng, nhãn, toạ độ", outputs="dict các độ đo",
         run="(module)", rel="Dùng bởi run_ips, run_ips_cost."),
    dict(group="Định vị (IPS)", path="src/run_ips.py",
         short="PHASE I — đánh giá mọi điều kiện chọn WAP (HUIM và đối chứng)",
         purpose="So sánh HUIM với baseline và các đối chứng ở CÙNG số WAP.",
         how="Điều kiện: baseline 520 WAP, 465 WAP từng phát hiện; HUIM union "
             "và top-n; đối chứng ngẫu nhiên (3 seed), top-n theo số lần phát "
             "hiện, top-n theo mutual information. Mọi điều kiện dùng cùng k-NN "
             "đã đóng băng; validation đánh giá đúng một lần mỗi điều kiện.",
         inputs="2 CSV, results/metrics/huim_runs.csv, results/hui/*__waps.json",
         outputs="results/metrics/ips_results.csv, results/ips_summary.json",
         run="python src/run_ips.py", rel="Sau run_huim_refine."),
    dict(group="Định vị (IPS)", path="src/run_ips_cost.py",
         short="Thời gian định vị và bộ nhớ theo số WAP",
         purpose="Tiêu chí 'thời gian, bộ nhớ' phía hệ định vị.",
         how="Một lõi (n_jobs=1), khởi động một lần rồi lặp 5 lần lấy trung vị; "
             "bộ nhớ CSDL vân tay tính chính xác = dòng × cột × số byte.",
         inputs="2 CSV, ips_results.csv, ips_summary.json",
         outputs="results/metrics/ips_cost.csv, results/ips_cost_summary.json",
         run="python src/run_ips_cost.py", rel="Hình fig16 vẽ từ đây."),
    dict(group="Định vị (IPS)", path="src/optimize_positioning.py",
         short="PHASE I3 (mới) — tối ưu sai số định vị theo mét",
         purpose="Giảm sai số mét mà không dùng validationData để chọn mô hình. "
                 "Nguyên lý chi tiết ở Chương 4.",
         how="Chia trainingData thành 6 fold 'giữ lại người đo' (GroupKFold theo "
             "USERID). Năm bước S0–S4: k-NN gốc → khoảng cách tốt nhất ở k=1 → "
             "thêm k láng giềng có trọng số 1/d^p → dò độ lệch thiết bị → "
             "ensemble hai biểu diễn. Mỗi bước giữ cấu hình tốt nhất TRÊN DEV và "
             "chỉ được nhận nếu giảm ít nhất 0,05 m. validationData chỉ chấm "
             "điểm mỗi bước một lần. Sau đó áp mô hình đã chọn lên các tập WAP "
             "của PHASE I (kể cả HUIM, ghi kèm minUtil).",
         inputs="2 CSV, results/metrics/ips_results.csv, "
                "results/ips_summary.json",
         outputs="results/positioning_optimisation.json, "
                 "results/metrics/positioning_dev_grid.csv, "
                 "positioning_ablation.csv, positioning_conditions.csv, "
                 "results/predictions/val_predictions_*.csv, "
                 "figures/fig18_positioning_optimisation.png",
         run="python src/optimize_positioning.py\n"
             "python src/optimize_positioning.py --figure-only",
         rel="Dự đoán từng dòng được verify_positioning.py và "
             "make_verification_kit.py kiểm tra."),
    # ------------------------------------------------ analysis / figures
    dict(group="Phân tích và biểu đồ", path="src/plots.py",
         short="PHASE J — vẽ fig01–fig17, fig19 (mỗi hình kèm CSV)",
         purpose="Biểu đồ khai phá, định vị, chi phí, EDA.",
         how="Đọc CSV kết quả; mỗi hình ghi kèm figures/<tên>.csv chứa đúng các "
             "dòng đã vẽ. Mọi điều kiện HUIM ghi kèm ngưỡng minUtil (%), chú "
             "thích chân hình ghi minUtil tuyệt đối = % × tổng utility; fig19 "
             "là bảng tra cứu minUtil → số HUI → số WAP → độ chính xác. fig17 "
             "(sai số mét so với dải 7–8 m) có thêm nhóm 'Mô hình tối ưu' đọc "
             "từ results/predictions/val_predictions_optimised.csv.",
         inputs="results/metrics/*.csv, ips_summary.json, 2 CSV (EDA)",
         outputs="figures/fig01…fig17, fig19 (.png + .csv)",
         run="python src/plots.py", rel="Hình được báo cáo và slide nhúng."),
    dict(group="Phân tích và biểu đồ", path="src/make_diagrams.py",
         short="Sơ đồ minh hoạ fig20–fig26",
         purpose="Hình minh hoạ khái niệm (pipeline, cây EFIM, ánh xạ dữ liệu…).",
         how="Vẽ bằng hình khối matplotlib, không dùng ảnh có bản quyền; hộp "
             "được co giãn theo lượng chữ; tránh ký tự Times New Roman không có.",
         inputs="results/data_summary.json (một vài nhãn)",
         outputs="figures/fig20_…fig26_*.png",
         run="python src/make_diagrams.py", rel="Slide và báo cáo."),
    dict(group="Phân tích và biểu đồ", path="src/make_ablation.py",
         short="Bảng ablation (ALL WAP so với HUIM A/B/C và đối chứng)",
         purpose="Bảng so sánh bắt buộc của đề bài.",
         how="Ghép ips_results.csv với huim_runs.csv theo run tag để chi phí "
             "khai phá đứng cạnh độ chính xác nó tạo ra.",
         inputs="results/metrics/ips_results.csv, huim_runs.csv",
         outputs="results/tables/ablation_study.csv, ablation_study.md",
         run="python src/make_ablation.py", rel="Báo cáo chương 14."),
    dict(group="Phân tích và biểu đồ", path="src/make_reverse_analysis.py",
         short="PHASE K — phân tích 'tư duy ngược' từ số liệu",
         purpose="Mỗi nhận định bắt đầu từ một con số đo được rồi mới giải thích.",
         how="Đọc kết quả, tính các quan sát (ngưỡng ↔ số HUI, chi phí hạ ngưỡng, "
             "tập AP khác nhau giữa model, HUIM ↔ đối chứng, tương quan support ↔ "
             "MI…) và viết văn bản.",
         inputs="huim_runs.csv, ips_results.csv, data_summary.json, "
                "huim_summary.json, results/hui/*",
         outputs="results/reverse_thinking_observations.json, "
                 "research/reverse_thinking_analysis.md",
         run="python src/make_reverse_analysis.py", rel="Báo cáo chương 15."),
    # ------------------------------------------------ documents
    dict(group="Tài liệu: báo cáo và slide", path="src/report_builder.py",
         short="Lớp Doc bọc python-docx (Times New Roman, chú thích, kiểm tra)",
         purpose="Công cụ viết file Word dùng chung.",
         how="Đặt font cho mọi slot (để dấu tiếng Việt không bị đổi font), "
             "chú thích Bảng/Hình tự đánh số, bảng từ DataFrame, trường mục lục; "
             "check() từ chối lưu nếu còn chữ giữ chỗ (danh sách FORBIDDEN trong file); lưu qua file "
             "tạm để tránh lỗi file đang bị khoá.",
         inputs="—", outputs="Lớp Doc", run="(module)",
         rel="Dùng bởi build_report.py và make_code_guide.py."),
    dict(group="Tài liệu: báo cáo và slide", path="src/make_report.py",
         short="Báo cáo Word: bìa, mục lục, chương 1–3 + lớp Ctx nạp kết quả",
         purpose="Phần đầu báo cáo và bộ nạp mọi file kết quả.",
         how="Ctx đọc mọi JSON/CSV cần thiết một lần (báo lỗi nếu thiếu); các "
             "chương chỉ chèn số đọc từ Ctx, không gõ tay số liệu.",
         inputs="results/*.json, results/metrics/*.csv, research/papers_table.csv",
         outputs="(nội dung, qua build_report.py)", run="(module)",
         rel="Cùng report_parts2–5."),
    dict(group="Tài liệu: báo cáo và slide", path="src/report_parts2.py",
         short="Chương 4–8 (FIM, HUIM, thuật toán, vì sao EFIM, mô hình hoá)",
         purpose="Phần lý thuyết của báo cáo.", how="Như make_report.py.",
         inputs="Ctx", outputs="(nội dung)", run="(module)", rel="build_report.py"),
    dict(group="Tài liệu: báo cáo và slide", path="src/report_parts3.py",
         short="Chương 9–11 (Model A, Model B/C, thiết kế thực nghiệm)",
         purpose="Phần mô hình utility và giao thức.", how="Như trên.",
         inputs="Ctx", outputs="(nội dung)", run="(module)", rel="build_report.py"),
    dict(group="Tài liệu: báo cáo và slide", path="src/report_parts4.py",
         short="Chương 12–14, 16 (kết quả HUIM, IPS, ablation, hạn chế), "
               "tài liệu tham khảo",
         purpose="Phần kết quả; có thêm mục 13.1.1 về tối ưu sai số mét.",
         how="Như trên; mục 13.1.1 đọc results/positioning_optimisation.json.",
         inputs="Ctx", outputs="(nội dung)", run="(module)", rel="build_report.py"),
    dict(group="Tài liệu: báo cáo và slide", path="src/report_parts5.py",
         short="Chương 15, 17–18 và phụ lục cheat sheet",
         purpose="Tư duy ngược, kết luận, hướng phát triển.", how="Như trên.",
         inputs="Ctx", outputs="(nội dung)", run="(module)", rel="build_report.py"),
    dict(group="Tài liệu: báo cáo và slide", path="src/build_report.py",
         short="PHASE L — lắp ráp báo cáo Word",
         purpose="Gọi lần lượt các chương rồi lưu file.",
         how="Tạo Ctx và Doc, gọi cover/ch1…ch18/appendix theo thứ tự đề bài.",
         inputs="Như make_report.py",
         outputs="report/HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx, "
                 "report/report_build_info.json",
         run="python src/build_report.py", rel="Sau figures, ablation, reverse."),
    dict(group="Tài liệu: báo cáo và slide", path="src/make_slides.py",
         short="PHASE M — deck PowerPoint chính + speaker notes",
         purpose="Bài trình bày, mọi số đọc từ results/.",
         how="Lớp Deck: font Times New Roman, cỡ chữ cố định, ≤ 5 gạch đầu dòng; "
             "số slide trong speaker notes tự đánh. Có slide 'Tối ưu sai số định "
             "vị theo mét' khi PHASE I3 đã chạy.",
         inputs="results/, figures/",
         outputs="slides/HUIM_IPS_UJIIndoorLoc_Presentation.pptx, "
                 "slides/speaker_notes.md",
         run="python src/make_slides.py", rel="Sau figures."),
    dict(group="Tài liệu: báo cáo và slide", path="src/make_prep_slides.py",
         short="Deck 8 slide về tiền xử lý dữ liệu",
         purpose="Trình bày riêng các bước tiền xử lý thực tế của dự án.",
         how="Vẽ slide bằng python-pptx. Lưu ý: khác các script tài liệu khác, "
             "số liệu trong deck này được GÕ trong script (lấy từ "
             "results/data_audit.md, huim_summary.json, fig08 CSV), nên phải tự "
             "cập nhật nếu kết quả thay đổi.",
         inputs="figures/fig13_eda_rssi_and_sparsity.png",
         outputs="slides/HUIM_Preprocessing_slides.pptx",
         run="python src/make_prep_slides.py", rel="Độc lập với pipeline."),
    dict(group="Tài liệu: báo cáo và slide", path="src/update_modelabc_slides.py",
         short="(mới) Cập nhật 2 biểu đồ trong deck 4 slide Model A/B/C, ghi "
               "minUtil",
         purpose="Biểu đồ 'HUIM có hơn các đối chứng không?' và biểu đồ thời "
                 "gian khai phá phải ghi rõ ngưỡng minUtil để kiểm chứng.",
         how="Mở deck có sẵn, thay dữ liệu sau hai biểu đồ gốc của PowerPoint "
             "(replace_data) — giữ nguyên màu, font, bố cục. Nhãn mỗi nhóm ghi "
             "'minUtil x% = giá trị tuyệt đối'; số liệu đọc từ huim_runs.csv và "
             "ips_results.csv; speaker notes được bổ sung phép tính "
             "% × tổng utility.",
         inputs="slides/HUIM_ModelABC_4slides.pptx, huim_runs.csv, "
                "ips_results.csv",
         outputs="slides/HUIM_ModelABC_4slides.pptx (ghi đè an toàn qua file tạm)",
         run="python src/update_modelabc_slides.py", rel="—"),
    dict(group="Tài liệu: báo cáo và slide", path="src/make_final_summary.py",
         short="PHASE N — FINAL_SUMMARY.md + kiểm tra sản phẩm bàn giao",
         purpose="Tóm tắt cuối và kiểm tra docx/pptx thực sự đúng yêu cầu.",
         how="Mở lại docx/pptx: đếm slide, kiểm font, chữ giữ chỗ, hình; quét "
             "các script tài liệu để bắt số gõ tay; liệt kê deliverables.",
         inputs="results/, report/, slides/, figures/",
         outputs="FINAL_SUMMARY.md, results/deliverables.csv, "
                 "results/verification.json",
         run="python src/make_final_summary.py", rel="Chạy cuối pipeline."),
    dict(group="Tài liệu: báo cáo và slide", path="src/check_glyphs.py",
         short="Tìm ký tự mà font Times New Roman không vẽ được",
         purpose="Tránh ô vuông (tofu) trong hình và slide.",
         how="Đọc bảng mã của file font, quét chuỗi trong code, đề xuất ký tự "
             "thay thế giữ nghĩa.",
         inputs="C:/Windows/Fonts/times.ttf, các file .py",
         outputs="results/glyph_check.json", run="python src/check_glyphs.py",
         rel="Công cụ phụ."),
    # ------------------------------------------------ verification
    dict(group="Kiểm chứng", path="src/verify_huim.py",
         short="(mới) Tính lại MỌI HUI từ CSV gốc, không dùng code EFIM",
         purpose="Chứng minh kết quả HUIM đúng mà không phải tin EFIM.",
         how="Tự cài lại q(i,T), p(i), u(X) từ định nghĩa. Với ba lần khai phá "
             "dùng trong biểu đồ: (1) minUtil% × tổng = minUtil tuyệt đối; (2) "
             "q, p khớp code dự án; (3) mọi HUI có u(X) ≥ minUtil; (4) utility và "
             "(5) support khớp EFIM; (6) vét cạn MỌI tổ hợp 1–3 WAP (hàng chục triệu "
             "itemset) — đúng các itemset có u ≥ minUtil phải nằm trong danh "
             "sách HUI; (7) hợp các HUI = tập WAP mà thí nghiệm định vị dùng. "
             "Run model C chỉ lưu top-1000 nên được khai phá lại (~30–50 s).",
         inputs="trainingData.csv, huim_runs.csv, ips_results.csv, results/hui/*",
         outputs="results/verification/huim_checks.json, hui_samples.csv, "
                 "hui_breakdown_*.csv/json, p_values.csv",
         run="python src/verify_huim.py",
         rel="Sheet 2, 3, 9 của workbook kiểm chứng đọc các file này."),
    dict(group="Kiểm chứng", path="src/verify_positioning.py",
         short="(mới) Tính lại độ chính xác và sai số mét chỉ bằng csv + math",
         purpose="Kiểm chứng độc lập với numpy/sklearn mà thí nghiệm dùng.",
         how="Đọc file dự đoán từng dòng; đếm số dòng đúng tòa/tầng/cả hai; "
             "tính sai số căn((x1−x2)² + (y1−y2)²) × cos(vĩ độ) (hệ số tự tính "
             "lại); trung bình/trung vị/phân vị; dựng lại toạ độ từ láng giềng "
             "(Σw·x/Σw, trung bình các member). --brute N: tìm lại láng giềng "
             "gần nhất trên toàn bộ trainingData bằng vòng lặp Python thuần. "
             "--row L: in mọi bước tính cho dòng L của validationData.csv.",
         inputs="2 CSV, results/predictions/*.csv, ips_summary.json, "
                "positioning_optimisation.json",
         outputs="results/verification/positioning_checks.json",
         run="python src/verify_positioning.py\n"
             "python src/verify_positioning.py --brute 25\n"
             "python src/verify_positioning.py --row 17",
         rel="Chạy sau optimize_positioning.py."),
    dict(group="Kiểm chứng", path="src/make_verification_kit.py",
         short="(mới) Workbook Excel kiểm chứng thủ công bằng công thức",
         purpose="Để kiểm tra tay mọi con số chính bằng Excel.",
         how="Ghi dữ liệu đầu vào (chữ xanh) và CÔNG THỨC Excel (chữ đen) tính "
             "lại: minUtil tuyệt đối, utility HUI cộng tay theo từng giao dịch, "
             "định vị tay một fingerprint, mọi dự đoán trên validation của hai mô hình với "
             "công thức đúng/sai và sai số, so với số báo cáo (ô KHỚP/LỆCH), hệ "
             "số Web Mercator. Nếu máy có Excel thì cho Excel tính lại và kiểm "
             "tra không còn ô lỗi hay ô LỆCH.",
         inputs="2 CSV, huim_runs.csv, ips_summary.json, "
                "positioning_optimisation.json, results/predictions/*, "
                "results/verification/*",
         outputs="verification/kiem_chung_thu_cong.xlsx",
         run="python src/make_verification_kit.py", rel="Chương 5."),
    dict(group="Kiểm chứng", path="tests/conftest.py",
         short="Cấu hình pytest (thêm src/ vào đường dẫn import)",
         purpose="Để các test import được module trong src/.",
         how="Một dòng sys.path.insert.", inputs="—", outputs="—",
         run="(pytest tự nạp)", rel="tests/"),
    dict(group="Kiểm chứng", path="tests/test_efim.py",
         short="Unit test: EFIM so với oracle brute-force",
         purpose="Không chạy gì trên UJIIndoorLoc trước khi EFIM được chứng minh "
                 "đúng.",
         how="Ví dụ chuẩn của literature ở 16 ngưỡng; 40 CSDL ngẫu nhiên × 5 "
             "ngưỡng; 15 CSDL thưa-rộng giống Wi-Fi; p là số thực; hai utility "
             "tính tay (u({b,d}) = 30, u({b,c,d,e}) = 40); TWU là cận trên (vét "
             "cạn); utility không anti-monotone; support đúng sau transaction "
             "merging; cắt tỉa thực sự xảy ra; dừng có kiểm soát hoạt động.",
         inputs="—", outputs="Kết quả pass/fail",
         run="python -m pytest tests -q", rel="huim/efim.py, huim/brute_force.py"),
    dict(group="Kiểm chứng", path="tests/test_utility.py",
         short="Unit test: tiền xử lý, mutual information, cổng chống rò rỉ",
         purpose="Bảo đảm ngữ nghĩa tiền xử lý và p(i) đúng.",
         how="Kiểm tra xử lý sentinel 100, tính dương và đơn điệu của q; MI so "
             "với sklearn.metrics.mutual_info_score trên 25 bộ ngẫu nhiên; "
             "build_external_utility phải báo lỗi với split khác 'training'.",
         inputs="—", outputs="Kết quả pass/fail",
         run="python -m pytest tests -q",
         rel="preprocess_uji.py, utility_models.py"),
    # ------------------------------------------------ literature
    dict(group="Tài liệu tham khảo (research/)", path="research/verify_dois.py",
         short="PHASE B — kiểm tra DOI qua Crossref (cần mạng)",
         purpose="Không trích dẫn DOI chưa xác minh.",
         how="Gọi API Crossref cho từng DOI đề xuất; ghi tiêu đề/tác giả/năm/nơi "
             "đăng; DOI không tồn tại hoặc trỏ sai bài bị loại.",
         inputs="Danh sách DOI trong script",
         outputs="research/doi_verification.json",
         run="python research/verify_dois.py", rel="build_literature.py"),
    dict(group="Tài liệu tham khảo (research/)",
         path="research/build_literature.py",
         short="Bảng bài báo + BibTeX từ bản ghi Crossref đã xác minh",
         purpose="Danh mục tài liệu chỉ gồm nguồn đã kiểm chứng.",
         how="Khẳng định tiêu đề khớp (sai thì dừng); kiểm DBLP; ghi rõ những gì "
             "không truy cập được (Scopus, SJR).",
         inputs="research/doi_verification*.json (+ mạng)",
         outputs="research/papers_table.csv, references.bib, "
                 "literature_build_log.json",
         run="python research/build_literature.py", rel="Báo cáo chương tài liệu."),
    dict(group="Tài liệu tham khảo (research/)",
         path="research/make_literature_review.py",
         short="Viết research/literature_review.md",
         purpose="Tổng quan tài liệu, gắn nhãn FACT / INTERPRETATION.",
         how="Chèn bảng từ papers_table.csv; số thống kê kiểm DOI tính từ file.",
         inputs="research/papers_table.csv, doi_verification*.json, "
                "results/data_summary.json",
         outputs="research/literature_review.md",
         run="python research/make_literature_review.py", rel="—"),
    # ------------------------------------------------ orchestration
    dict(group="Điều phối", path="run_experiments.py",
         short="Chạy toàn bộ pipeline theo đúng thứ tự",
         purpose="Tái lập toàn bộ nghiên cứu bằng một lệnh.",
         how="Danh sách PHASES (tên, nhãn, lệnh); chạy từng script bằng "
             "subprocess với PYTHONIOENCODING=utf-8; phase lỗi thì dừng (trừ "
             "phase cần mạng).",
         inputs="—", outputs="Mọi thứ ở trên",
         run="python run_experiments.py\npython run_experiments.py --list\n"
             "python run_experiments.py --only positioning\n"
             "python run_experiments.py --from figures --offline",
         rel="Gọi mọi script."),
    dict(group="Điều phối", path="src/make_code_guide.py",
         short="(mới) Tạo chính tài liệu Word này",
         purpose="Mô tả mọi file .py; số liệu đọc lúc dựng.",
         how="Mô tả là văn bản viết trong script; số dòng code, số test, ví dụ "
             "EFIM, ngưỡng minUtil, kết quả định vị và kiểm chứng được đọc/tính "
             "lại khi chạy.",
         inputs="Mã nguồn, results/, figures/",
         outputs="report/HUIM_IPS_Mo_ta_cac_file_Python.docx",
         run="python src/make_code_guide.py", rel="Chạy cuối."),
]


# ------------------------------------------------------------------ chapters
def chapter_overview(D: Doc) -> None:
    D.h(1, "1. Bức tranh tổng thể")
    D.rich([("Dự án làm gì. ", "b"),
            ("Dùng High Utility Itemset Mining (thuật toán EFIM) để chọn nhóm "
             "Access Point (WAP) cho bài toán định vị trong nhà bằng vân tay "
             "Wi-Fi trên bộ dữ liệu UJIIndoorLoc, rồi đánh giá có đối chứng: "
             "độ chính xác tòa nhà/tầng, sai số theo mét, thời gian và bộ nhớ.",
             "")])
    D.rich([("Ba quy tắc xuyên suốt mã nguồn. ", "b"),
            ("(1) validationData chỉ dùng để đánh giá, mỗi điều kiện đúng một "
             "lần; mọi thứ được 'học' (chuẩn hoá RSSI, p(i), siêu tham số) chỉ "
             "lấy từ trainingData — có cổng báo lỗi trong code. (2) Không gõ tay "
             "số liệu vào báo cáo/slide/hình: mọi số đọc từ results/. (3) Mỗi "
             "hình có file CSV chứa đúng dữ liệu đã vẽ.", "")])
    D.h(2, "1.1. Thứ tự chạy (pipeline)")
    sys.path.insert(0, str(PROJECT_ROOT))
    import run_experiments as rx
    by_path = {f["path"]: f for f in FILES}
    rows = []
    for name, label, cmd in rx.PHASES:
        script = cmd[-1] if cmd[-1].endswith(".py") else " ".join(cmd[2:])
        f = by_path.get(script)
        rows.append({"Phase": name,
                     "Nhãn": re.match(r"PHASE \S+", label).group(0),
                     "Script": script,
                     "Ghi ra": f["outputs"] if f else "kết quả pass/fail"})
    grid(D, pd.DataFrame(rows), [1.05, 0.75, 1.95, 2.75], size=8.5,
         caption="Các phase theo thứ tự run_experiments.py chạy")
    fig = FIGURES / "fig25_pipeline.png"
    if fig.exists():
        D.figure(fig, "Luồng dữ liệu của nghiên cứu: không có mũi tên nào đi "
                      "từ validationData ngược về bước học", width_in=6.2)
    D.h(2, "1.2. Thư mục")
    grid(D, pd.DataFrame([
        {"Thư mục": "ujiindoorloc/UJIndoorLoc/", "Chứa": "Hai file CSV gốc "
         "(chỉ đọc; SHA-256 ghi trong results/data_summary.json)"},
        {"Thư mục": "src/", "Chứa": "Mã nguồn chính (mô tả ở Chương 2)"},
        {"Thư mục": "src/huim/", "Chứa": "EFIM và oracle brute-force"},
        {"Thư mục": "tests/", "Chứa": "Unit test (pytest)"},
        {"Thư mục": "research/", "Chứa": "Script tài liệu tham khảo + kết quả"},
        {"Thư mục": "results/", "Chứa": "JSON kết quả; metrics/ (CSV); hui/ (tập "
         "HUI); predictions/ (dự đoán từng dòng); verification/ (kết quả kiểm "
         "chứng); logs/"},
        {"Thư mục": "figures/", "Chứa": "Hình .png + .csv dữ liệu của hình"},
        {"Thư mục": "report/, slides/", "Chứa": "Báo cáo Word, slide, tài liệu này"},
        {"Thư mục": "verification/", "Chứa": "Workbook Excel kiểm chứng thủ công"},
    ]), [1.8, 4.7])


def chapter_catalogue(D: Doc) -> None:
    D.h(1, "2. Từng file .py: tác dụng, nguyên lý, đầu vào, đầu ra")
    rows = []
    for i, f in enumerate(FILES, start=1):
        rows.append({"#": i, "File": f["path"], "Dòng": n_lines(f["path"]),
                     "Tác dụng": f["short"]})
    grid(D, pd.DataFrame(rows), [0.35, 2.15, 0.5, 3.5], size=8.5,
         caption=f"Tổng hợp {len(FILES)} file Python của dự án (số dòng đếm "
                 "lúc tạo tài liệu)")
    group = None
    k = 0
    for f in FILES:
        if f["group"] != group:
            group = f["group"]
            k += 1
            D.h(2, f"2.{k}. {group}")
        D.h(3, f["path"])
        kv_table(D, [("Tác dụng", f["purpose"]),
                     ("Nguyên lý hoạt động", f["how"]),
                     ("Đầu vào", f["inputs"]),
                     ("Đầu ra", f["outputs"]),
                     ("Cách chạy", f["run"]),
                     ("Liên quan", f["rel"])])


def chapter_efim(D: Doc) -> None:
    """EFIM on the running example of the literature (the one in the EFIM
    paper and in the video the student referenced), computed here."""
    sys.path.insert(0, str(PROJECT_ROOT / "tests"))
    from huim.brute_force import itemset_utility, transaction_utility, twu
    from huim.efim import mine_efim
    from test_efim import RUNNING_DB as DB, RUNNING_P as P
    mu = 30
    D.h(1, "3. Nguyên lý EFIM trên ví dụ chuẩn")
    D.p("Ví dụ dưới đây là cơ sở dữ liệu 5 giao dịch, 7 item (a–g) dùng trong "
        "bài báo EFIM và trong video giới thiệu thuật toán; cũng chính là dữ "
        "liệu mà tests/test_efim.py dùng. Mọi con số trong chương này được "
        "src/make_code_guide.py tính lại bằng chính mã nguồn của dự án lúc tạo "
        "tài liệu.", align="justify")
    rows = []
    for k, t in enumerate(DB, start=1):
        rows.append({"Giao dịch": f"T{k}",
                     "Item (số lượng q)": ", ".join(f"{i}({q})" for i, q in t.items()),
                     "TU(T) = Σ q·p": f"{transaction_utility(t, P):g}"})
    grid(D, pd.DataFrame(rows), [1.0, 3.5, 2.0], caption="Cơ sở dữ liệu ví dụ; "
         "đơn giá p: " + ", ".join(f"p({i})={v}" for i, v in P.items()))
    D.h(2, "3.1. Các khái niệm")
    D.bullets([
        "u(i,T) = q(i,T) × p(i): utility của item i trong giao dịch T. Trong dự "
        "án: q = RSSI chuẩn hoá (1…100), p = trọng số của WAP (Model A/B/C).",
        "u(X) = tổng u(X,T) trên các giao dịch chứa TOÀN BỘ X. X là HUI nếu "
        "u(X) ≥ minUtil.",
        f"Ví dụ tính tay: {{b,d}} chỉ nằm trong T3, T4: (2×2 + 6×2) + (4×2 + 3×2) "
        f"= {itemset_utility(('b', 'd'), DB, P):g}.",
        "Utility KHÔNG đơn điệu: thêm item có thể làm tăng hoặc giảm u(X), nên "
        "không cắt tỉa được bằng chính u(X) như Apriori. Phải dùng cận trên.",
        "TWU(i) = tổng TU(T) trên các giao dịch chứa i — cận trên của u(X) với "
        "mọi X chứa i. Nếu TWU(i) < minUtil thì bỏ i hẳn.",
    ])
    tw = {i: twu(i, DB, P) for i in sorted(P)}
    order = sorted((i for i in tw if tw[i] >= mu), key=lambda i: (tw[i], i))
    # root-level subtree utility: transactions sorted in the processing order
    su = {}
    for z, item in enumerate(order):
        tot = 0.0
        for t in DB:
            if item in t:
                tot += sum(q * P[i] for i, q in t.items()
                           if i in order and order.index(i) >= z)
        su[item] = tot
    D.h(2, f"3.2. Bước tiền xử lý của EFIM với minUtil = {mu}")
    grid(D, pd.DataFrame([{"Item": i, "TWU(i)": f"{tw[i]:g}",
                           "Thứ tự duyệt": order.index(i) + 1 if i in order else "bị loại",
                           "lu(gốc, i) = TWU": f"{tw[i]:g}",
                           "su(gốc, i)": f"{su[i]:g}" if i in su else "—",
                           "Vai trò ở gốc": ("Primary (được mở nhánh)"
                                             if i in su and su[i] >= mu else
                                             "chỉ là Secondary (mở rộng)")}
                          for i in order]),
         [0.6, 0.8, 1.0, 1.1, 0.8, 2.2],
         caption="TWU, thứ tự duyệt (TWU tăng dần), local utility và subtree "
                 "utility tại gốc")
    D.bullets([
        f"Thứ tự duyệt: {' < '.join(order)} (TWU tăng dần, như bài báo EFIM).",
        "Local utility lu(α,z): cận trên cho MỌI itemset mở rộng α có chứa z. "
        "lu < minUtil → bỏ z khỏi toàn bộ cây con của α (tập Secondary).",
        "Subtree utility su(α,z): chỉ cộng utility của các item đứng SAU z, nên "
        "chặt hơn. su < minUtil → không mở nhánh α + {z} (tập Primary).",
        "Database projection: khi đi xuống nút α + {z}, mỗi giao dịch chỉ giữ "
        "phần đứng sau z và một con số 'utility tiền tố' — CSDL nhỏ dần theo độ "
        "sâu.",
        "Transaction merging: các giao dịch chiếu ra giống hệt nhau được gộp "
        "(cộng utility), rất hiệu quả với dữ liệu Wi-Fi thưa và lặp lại.",
        "Fast Utility Counting: lu và su của mọi item được tính trong MỘT lượt "
        "quét bằng hai mảng 'utility bin'.",
    ])
    huis, st = mine_efim(DB, P, mu)
    D.h(2, f"3.3. Kết quả: {len(huis)} HUI")
    grid(D, pd.DataFrame([{"HUI": "{" + ", ".join(sorted(x)) + "}",
                           "u(X)": f"{u:g}", "Support": s}
                          for x, u, s in sorted(huis, key=lambda r: (len(r[0]), sorted(r[0])))]),
         [3.0, 1.5, 1.5], caption=f"Các HUI với minUtil = {mu} (EFIM, khớp "
                                   "oracle brute-force trong unit test)")
    D.p(f"EFIM chỉ duyệt {st.n_nodes_visited} nút của cây tìm kiếm (2^7 − 1 = 127 "
        f"itemset khả dĩ), loại {st.n_candidates_pruned_by_su} nhánh nhờ subtree "
        f"utility và tiết kiệm {st.n_transactions_saved_by_merging} giao dịch nhờ "
        f"gộp — đó là lý do nó nhanh.", align="justify")
    D.h(2, "3.4. minUtil trong dự án: % và giá trị tuyệt đối")
    H = pd.read_csv(METRICS / "huim_runs.csv")
    prim = (H[(H["status"] == "COMPLETED") & (H["n_huis"] > 0)]
            .sort_values("rel_minutil_pct").groupby("utility_model").head(1)
            .sort_values("utility_model"))
    D.p("Dự án đặt minUtil theo % tổng utility của cơ sở dữ liệu, vì tổng "
        "utility khác nhau giữa ba model (cùng dữ liệu, chỉ khác p). Giá trị "
        "tuyệt đối mà EFIM thực sự dùng = % × tổng / 100. Đây là các ngưỡng nằm "
        "trên mọi biểu đồ HUIM:", align="justify")
    grid(D, pd.DataFrame([{
        "Model": r["utility_model"],
        "minUtil (%)": f"{r['rel_minutil_pct']:g}".replace(".", ","),
        "Tổng utility CSDL": vn(r["total_db_utility"], 0),
        "minUtil tuyệt đối": vn(r["abs_minutil"], 2),
        "Số HUI": vn_int(r["n_huis"]),
        "Số WAP (union)": int(r["unique_waps_in_huis"])} for _, r in prim.iterrows()]),
        [1.55, 0.8, 1.2, 1.15, 0.8, 0.9],
        caption="Ngưỡng thấp nhất CHẠY XONG của mỗi model (đọc từ "
                "results/metrics/huim_runs.csv)")


def chapter_positioning(D: Doc) -> None:
    PO = load_json(RESULTS / "positioning_optimisation.json")
    A = pd.read_csv(METRICS / "positioning_ablation.csv")
    s0, sel = A[A["stage"] == "S0"].iloc[0], A.iloc[-1]
    cfg = PO["selected_config"]
    D.h(1, "4. Nguyên lý tối ưu sai số định vị (optimize_positioning.py)")
    D.h(2, "4.1. Định vị bằng k-NN")
    D.bullets([
        "Mỗi fingerprint là một vector 520 số. Định vị = tìm các fingerprint "
        "huấn luyện 'giống' nhất (láng giềng gần nhất) rồi lấy vị trí của chúng.",
        "Khoảng cách Manhattan (mô hình cũ): d(a,b) = Σ |a_j − b_j|.",
        "Khoảng cách Bray-Curtis (mô hình tối ưu): d(a,b) = Σ |a_j − b_j| / "
        "Σ (a_j + b_j). Chia cho tổng cường độ nên ít bị ảnh hưởng khi một điện "
        "thoại đọc yếu hơn đồng loạt vài dB.",
        "Biểu diễn 'exponential': exp((RSSI + 105)/24) / exp(105/24) — nén vùng "
        "sóng yếu (nhiễu nhiều) và giãn vùng sóng mạnh.",
        "Toạ độ dự đoán = Σ w_i · x_i / Σ w_i với w_i = 1/d_i^p trên k láng giềng.",
        "Dò độ lệch thiết bị: thử cộng δ = −6, −3, 0, +3, +6 dB vào mọi RSSI "
        "được phát hiện của truy vấn; giữ δ cho láng giềng gần nhất GẦN nhất. "
        "Chỉ dùng tín hiệu của chính truy vấn, không dùng vị trí hay nhãn.",
        "Ensemble: trung bình toạ độ của hai mô hình dùng hai biểu diễn khác "
        "nhau (exponential và positive).",
    ])
    D.h(2, "4.2. Vì sao chọn trên fold 'giữ lại người đo'")
    D.p("k = 1 của mô hình cũ được chọn trên phép chia NGẪU NHIÊN, nơi truy vấn "
        "dev thường có 'anh em sinh đôi' đo cùng chỗ trong tập huấn luyện. "
        "validationData do người khác đo, bằng điện thoại khác, bốn tháng sau. "
        "Vì vậy optimize_positioning.py chia trainingData theo USERID (6 fold): "
        "mỗi lần đánh giá dev chỉ gồm người đo mà mô hình chưa thấy. Mọi lựa chọn "
        "(biểu diễn, khoảng cách, k, p, δ, ensemble) được làm trên các fold này; "
        "validationData chỉ chấm điểm mỗi bước một lần.", align="justify")
    grid(D, pd.DataFrame([{
        "Bước": r["stage"], "Cấu hình": r["config"],
        "Dev TB (m)": vn(r["dev_mean_ground_m"]),
        "Validation TB (m)": vn(r["val_mean_ground_m"]),
        "Trung vị (m)": vn(r["val_median_ground_m"]),
        "Joint acc": vn(r["val_joint_building_floor_accuracy"] * 100) + "%"}
        for _, r in A.iterrows()]), [0.45, 2.75, 0.7, 0.9, 0.75, 0.75], size=8.5,
        caption="Từng bước: dev dùng để CHỌN, validation chỉ để BÁO CÁO (mét "
                "thực địa)")
    D.rich([("Kết quả. ", "b"),
            (f"Mô hình được chọn ({PO['selected_label']}) giảm sai số trung bình "
             f"từ {vn(s0['val_mean_ground_m'])} m xuống "
             f"{vn(sel['val_mean_ground_m'])} m thực địa, trung vị từ "
             f"{vn(s0['val_median_ground_m'])} m xuống "
             f"{vn(sel['val_median_ground_m'])} m, độ chính xác joint từ "
             f"{vn(s0['val_joint_building_floor_accuracy'] * 100)}% lên "
             f"{vn(sel['val_joint_building_floor_accuracy'] * 100)}%. Trên dev "
             f"bước dò độ lệch và ensemble đều có lợi, nhưng trên validation "
             f"sai số mét không giảm thêm sau bước S2 — được báo cáo đúng như "
             f"đo, và mô hình vẫn là mô hình do giao thức chọn.", "")])
    fig = FIGURES / "fig18_positioning_optimisation.png"
    if fig.exists():
        D.figure(fig, "Phân bố sai số từng bước (trái) và sai số trung bình của "
                      "từng tập WAP trước/sau tối ưu (phải; HUIM ghi kèm minUtil)",
                 width_in=6.4)


def chapter_verification(D: Doc) -> None:
    va_n = int(load_json(RESULTS / "data_summary.json")["validation"]["n_rows"])
    isum = load_json(RESULTS / "ips_summary.json")
    b = isum["conditions"]["baseline_all_520"]["result"]["knn"]
    po = load_json(RESULTS / "positioning_optimisation.json")["validation"]["selected"]
    D.h(1, "5. Hướng dẫn kiểm chứng thủ công")
    D.p(f"Câu hỏi 'làm sao biết {vn(b['joint_building_floor_accuracy'] * 100)}% "
        f"hay {vn(po['positioning_error']['mean_error_ground_m'])} m là đúng?' có "
        "ba lớp trả lời, từ dễ đến kỹ. Lớp nào cũng KHÔNG cần tin vào code thí "
        "nghiệm.", align="justify")
    D.h(2, "5.1. Hiểu con số trước khi kiểm")
    cc = load_json(RESULTS / "coordinate_system_verification.json")["conclusion"]
    gf = vn(cc["ground_distance_correction_factor"], 6)
    lat = vn(cc["inverted_centroid_lat_deg"], 2)
    scale = vn(cc["web_mercator_scale_factor_at_this_latitude"], 3)
    D.bullets([
        f"Độ chính xác joint = (số fingerprint kiểm định đoán đúng CẢ tòa nhà LẪN "
        f"tầng) / {vn_int(va_n)}. Mô hình cũ: {round(b['joint_building_floor_accuracy'] * va_n)}"
        f" / {vn_int(va_n)} = {vn(b['joint_building_floor_accuracy'] * 100)}%. Mô hình tối "
        f"ưu: {round(po['joint_building_floor_accuracy'] * va_n)} / {vn_int(va_n)} = "
        f"{vn(po['joint_building_floor_accuracy'] * 100)}%.",
        "Sai số mét của MỘT fingerprint = căn((x_thật − x_dự đoán)² + (y_thật − "
        f"y_dự đoán)²) × {gf}. 'Sai số trung bình' là trung bình cộng của "
        f"{vn_int(va_n)} con số đó; 'trung vị' là con số đứng giữa khi sắp xếp.",
        f"{gf} = cos(vĩ độ ≈ {lat}°): toạ độ của bộ dữ liệu là Web Mercator, "
        f"phóng đại khoảng cách {scale} lần ở vĩ độ này.",
        "minUtil (%) chỉ là cách viết gọn; EFIM dùng minUtil TUYỆT ĐỐI = % × tổng "
        "utility / 100 (xem Bảng ở mục 3.4).",
    ])
    D.h(2, "5.2. Lớp 1 — Excel: verification/kiem_chung_thu_cong.xlsx")
    D.p("Mở file bằng Excel. Chữ xanh dương là số chép từ file dữ liệu; chữ đen "
        "là công thức; ô nền xanh lá là ô kiểm tra (KHỚP/ĐẠT là đúng). Bấm vào ô "
        "bất kỳ để xem công thức. Thứ tự đề nghị:", align="justify")
    D.bullets([
        "Sheet 1_minUtil: cột 'minUtil tuyệt đối = C/100*D' phải bằng cột lấy từ "
        "huim_runs.csv ở cả 37 lần khai phá.",
        "Sheet 2_HUI_mau: HUI mẫu — utility EFIM = utility tính lại, và ≥ minUtil.",
        "Sheet 3_HUI_tinh_tay: một HUI 2 WAP cộng tay qua từng giao dịch: q từ "
        "RSSI bằng công thức, u(X,T) = q·p + q·p, u(X) = SUM.",
        "Sheet 4_kNN_tinh_tay: một fingerprint được định vị từng bước bằng công "
        "thức (biểu diễn → khoảng cách → hạng → trọng số → toạ độ → sai số).",
        f"Sheet 5 và 6: {vn_int(va_n)} dự đoán; ô tổng hợp đầu sheet là AVERAGE / MEDIAN / "
        "PERCENTILE của các cột; sheet 6 dựng lại toạ độ từ 2 × 12 láng giềng.",
        "Sheet 7_TongHop: số Excel tính được đặt cạnh số báo cáo — phải KHỚP.",
        f"Sheet 8_HeSo_Mercator: {gf} tính lại từ vĩ độ.",
        "Sheet 9_KiemTra_Python: kết quả hai script kiểm chứng (lớp 2).",
    ])
    # the worked row: the validation fingerprint whose optimised error is the
    # median one (a typical case, and the row sheet 4 of the workbook uses)
    O = pd.read_csv(RESULTS / "predictions" / "val_predictions_optimised.csv")
    typical = O.sort_values("err_ground_m").reset_index(drop=True)
    typical = typical.iloc[len(typical) // 2]
    line = int(typical["csv_line"])
    D.h(2, "5.3. Lớp 2 — Python độc lập")
    code(D, "python src/verify_huim.py                # mọi HUI tính lại từ CSV\n"
            "python src/verify_positioning.py         # csv + math, không numpy\n"
            "python src/verify_positioning.py --brute 25\n"
            f"python src/verify_positioning.py --row {line}")
    rows = []
    for name, label in (("huim_checks.json", "verify_huim.py"),
                        ("positioning_checks.json", "verify_positioning.py")):
        p = RESULTS / "verification" / name
        if p.exists():
            v = load_json(p)
            rows.append({"Script": label, "Số phép kiểm tra": v["n_checks"],
                         "Thất bại": v["n_failed"],
                         "Kết quả": "TẤT CẢ PASS" if v["n_failed"] == 0 else "CÓ LỖI"})
    if rows:
        grid(D, pd.DataFrame(rows), [2.0, 1.4, 1.0, 2.1],
             caption="Kết quả lần chạy kiểm chứng gần nhất "
                     "(results/verification/*.json)")
    D.h(2, "5.4. Lớp 3 — tự tính bằng tay một dòng")
    P = pd.read_csv(RESULTS / "predictions" / "val_predictions_study_knn.csv")
    r = P[P["csv_line"] == line].iloc[0]

    def c(v):                       # coordinates as written in the CSV files
        return f"{v:.4f}"

    D.p(f"Lấy dòng {line} của validationData.csv (dòng có sai số của mô hình "
        f"tối ưu đúng bằng trung vị — một ca điển hình, cũng là dòng mà sheet "
        f"4_kNN_tinh_tay dùng). Toạ độ thật: x = {c(r['true_x'])}, y = "
        f"{c(r['true_y'])}; tòa nhà/tầng thật {int(r['true_building'])}/"
        f"{int(r['true_floor'])}.", align="justify")
    D.bullets([
        f"Mô hình cũ (k = 1): láng giềng gần nhất là dòng "
        f"{int(r['nbr1_train_line'])} của trainingData.csv, nên toạ độ dự đoán "
        f"chính là toạ độ dòng đó: ({c(r['pred_x'])}; {c(r['pred_y'])}). Sai số = "
        f"căn(({c(r['true_x'])} − ({c(r['pred_x'])}))² + ({c(r['true_y'])} − "
        f"{c(r['pred_y'])})²) = {vn(r['err_projected_m'], 4)} m toạ độ × {gf} "
        f"= {vn(r['err_ground_m'], 4)} m thực địa; dự đoán tòa nhà/tầng "
        f"{int(r['pred_building'])}/{int(r['pred_floor'])}.",
        f"Mô hình tối ưu: toạ độ dự đoán ({c(typical['pred_x'])}; "
        f"{c(typical['pred_y'])}) là trung bình của hai member, mỗi member là "
        f"trung bình có trọng số 1/d^p của 12 láng giềng (danh sách láng giềng, "
        f"khoảng cách và trọng số nằm trong file "
        f"results/predictions/val_predictions_optimised.csv). Sai số "
        f"{vn(typical['err_ground_m'], 4)} m thực địa; dự đoán tòa nhà/tầng "
        f"{int(typical['pred_building'])}/{int(typical['pred_floor'])}.",
    ])
    better = ("mô hình cũ" if r["err_ground_m"] < typical["err_ground_m"]
              else "mô hình tối ưu")
    D.p(f"Ở riêng dòng này {better} sai ít hơn. Một dòng đơn lẻ không quyết định "
        f"mô hình nào tốt hơn: chỉ trung bình (và trung vị) trên cả "
        f"{vn_int(va_n)} dòng mới nói được điều đó — đó là lý do sheet 5 và 6 "
        f"tính lại cả {vn_int(va_n)} dòng.", align="justify")
    D.p("Mở trainingData.csv, nhảy tới đúng dòng láng giềng và đọc cột "
        "LONGITUDE/LATITUDE để so. Lệnh 'python src/verify_positioning.py --row "
        "<dòng>' in toàn bộ phép tính này cho bất kỳ dòng nào, cho cả hai mô hình.",
        align="justify")
    D.rich([("Lưu ý khi mở file CSV bằng Excel. ", "b"),
            ("Các file CSV của bộ dữ liệu dùng dấu phẩy để ngăn cột và dấu chấm "
             "thập phân. Nếu Excel đang dùng định dạng số kiểu Việt Nam (thập phân "
             "là dấu phẩy) thì mở trực tiếp có thể dồn cả dòng vào một ô hoặc đọc "
             "sai số. Khi đó dùng Data → From Text/CSV, chọn Delimiter = Comma, "
             "và trong Transform/Locale chọn English (United States) để dấu chấm "
             "được hiểu là thập phân. Workbook kiểm chứng không gặp vấn đề này vì "
             "số đã nằm sẵn trong ô.", "")])


def main() -> None:
    D = Doc()
    D.title_page([
        ("DỰ ÁN HUIM-IPS — UJIIndoorLoc", 14, False),
        ("", 12, False),
        ("MÔ TẢ CÁC FILE PYTHON", 24, True),
        ("Tác dụng, nguyên lý hoạt động, đầu vào, đầu ra", 15, False),
        ("và hướng dẫn kiểm chứng kết quả", 15, False),
        ("", 12, False), ("", 12, False),
        (f"{len(FILES)} file .py, "
         f"{vn_int(sum(n_lines(f['path']) for f in FILES))} dòng mã; "
         f"{count_tests()} unit test", 12, False),
        ("", 12, False),
        ("Tài liệu được sinh bởi src/make_code_guide.py; mọi con số đọc từ mã "
         "nguồn và results/ lúc tạo.", 10, False),
    ])
    D.h(1, "Mục lục")
    D.toc_field()
    chapter_overview(D)
    chapter_catalogue(D)
    chapter_efim(D)
    chapter_positioning(D)
    chapter_verification(D)
    info = D.save(OUT)
    LOG.info("saved %s (%s paragraphs, %s tables)", info["path"],
             info["n_paragraphs"], info["n_tables"])
    print("OK ", info["path"])


if __name__ == "__main__":
    main()
