"""Build slides/HUIM_Preprocessing_slides.pptx - the preprocessing actually used
in this project (src/preprocess_uji.py, src/utility_models.py, src/huim/efim.py).

Every number below was read from results/data_audit.md, results/huim_summary.json,
figures/fig08_*.csv or computed from the real CSVs (worked example, row 3248).
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "HUIM_Preprocessing_slides.pptx"
FONT = "Times New Roman"
INK = RGBColor(0x1A, 0x1A, 0x1A)
ACCENT = RGBColor(0x8C, 0x2D, 0x04)
BLUE = RGBColor(0x1F, 0x3B, 0x73)
GREEN = RGBColor(0x14, 0x5A, 0x32)
GREY = RGBColor(0x6E, 0x6E, 0x6E)
LIGHT = RGBColor(0xF3, 0xF1, 0xEC)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)


def text(s, x, y, w, h, lines, size=16, bold=False, color=INK,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, after=8):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [lines]
    for k, ln in enumerate(lines):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(after)
        r = p.add_run()
        r.text = ln
        f = r.font
        f.name, f.size, f.bold, f.color.rgb = FONT, Pt(size), bold, color
    return tb


def box(s, x, y, w, h, lines, color=BLUE, size=14, fill=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    sh.line.color.rgb = color
    sh.line.width = Pt(2)
    if fill:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    else:
        sh.fill.background()
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for k, ln in enumerate(lines):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = ln
        r.font.name, r.font.size = FONT, Pt(size)
        r.font.bold = (k == 0)
        r.font.color.rgb = INK
    return sh


def arrow(s, x, y, w=0.4):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                           Inches(w), Inches(0.3))
    a.fill.solid()
    a.fill.fore_color.rgb = GREY
    a.line.fill.background()


def table(s, x, y, w, rows, col_w, size=13, row_h=0.42):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y),
                           Inches(w), Inches(row_h * len(rows))).table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            r = c.text_frame.paragraphs[0].add_run()
            r.text = str(val)
            r.font.name, r.font.size = FONT, Pt(size)
            r.font.bold = (i == 0)
            r.font.color.rgb = RGBColor(255, 255, 255) if i == 0 else INK
            c.fill.solid()
            c.fill.fore_color.rgb = BLUE if i == 0 else (LIGHT if i % 2 else RGBColor(255, 255, 255))
    return t


def slide(title, sub=None, notes=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.6, 0.35, 12.1, 0.8, title, 28, True, ACCENT)
    if sub:
        text(s, 0.6, 1.1, 12.1, 0.5, sub, 16, False, GREY)
    s.notes_slide.notes_text_frame.text = notes
    return s


def src(s, t):
    text(s, 0.6, 7.0, 12.1, 0.35, "Nguồn: " + t, 11, False, GREY)


# 1 ------------------------------------------------------------- title
s = prs.slides.add_slide(prs.slide_layouts[6])
text(s, 0.8, 2.2, 11.7, 1.2, "Tiền xử lý dữ liệu cho HUIM", 40, True, ACCENT)
text(s, 0.8, 3.4, 11.7, 1.4,
     ["Wi-Fi fingerprint UJIIndoorLoc → utility transaction → EFIM",
      "Những bước đã được áp dụng trong dự án HUIM-IPS"], 20, False, INK)
text(s, 0.8, 6.3, 11.7, 0.5,
     "Nội dung đọc từ src/preprocess_uji.py, src/utility_models.py, src/huim/efim.py, results/", 12, False, GREY)

# 2 ------------------------------------------------------------- overview
s = slide("Tổng quan: 5 bước tiền xử lý",
          "Từ một dòng CSV đến đầu vào của thuật toán EFIM",
          "Bước 1-3 nằm ở preprocess_uji.py và utility_models.py. Bước 4 là phần tiền xử lý nội bộ của EFIM.")
labels = [("1. Làm sạch", "100 = không phát hiện\nkiểm tra khoảng RSSI"),
          ("2. Chuẩn hoá RSSI", "q(i,T) ∈ [1, 100]\nfit trên train"),
          ("3. Tạo transaction", "item = WAP\nô ≠ 100 → có mặt"),
          ("4. Trọng số p(i)", "Model A / B / C\nchỉ ước lượng từ train"),
          ("5. Bên trong EFIM", "TWU, sắp thứ tự,\nTWU-pruning, merging")]
cols = [BLUE, BLUE, ACCENT, ACCENT, GREEN]
for k, ((h, b), c) in enumerate(zip(labels, cols)):
    x = 0.5 + k * 2.55
    box(s, x, 2.3, 2.2, 1.9, [h] + b.split("\n"), c, 14)
    if k < 4:
        arrow(s, x + 2.22, 3.1, 0.3)
text(s, 0.6, 4.8, 12.1, 1.8,
     ["• Đầu vào: trainingData.csv (19.937 dòng) và validationData.csv (1.111 dòng), mỗi file 520 cột WAP.",
      "• Đầu ra: danh sách transaction {WAP: q} và vector p(i) cho từng WAP.",
      "• Mọi tham số học từ dữ liệu (RSSI min/max, p(i)) chỉ lấy từ trainingData."],
     16)
src(s, "src/preprocess_uji.py, configs/experiment.yaml")

# 3 ------------------------------------------------------------- raw data
s = slide("Dữ liệu thô: giá trị 100 là “không phát hiện”",
          "Kiểm tra bằng 3 bằng chứng trong results/data_audit.md",
          "Giá trị 100 không phải RSSI. Nó là sentinel, nên không được đưa thẳng vào hàm khoảng cách hay chuẩn hoá.")
text(s, 0.6, 1.7, 5.4, 4.8,
     ["• Tài liệu UCI: “Positive value 100 is used to denote when a WAP was not detected”.",
      "• Phân bố: mọi giá trị nằm trong [-104, 0] hoặc đúng bằng 100; không có ô nào trong 1…99.",
      "• 96,54% số ô của train bằng 100 (10.008.477 / 10.367.240).",
      "• Trung bình mỗi fingerprint phát hiện 18,0 / 520 AP.",
      "• Nếu không loại 100, “RSSI trung bình” tính ra +93,8 — vô nghĩa."], 15)
s.shapes.add_picture(str(ROOT / "figures" / "fig13_eda_rssi_and_sparsity.png"),
                     Inches(6.2), Inches(1.9), width=Inches(6.8))
text(s, 6.2, 5.2, 6.8, 1.0,
     "Trái: RSSI của các AP được phát hiện (358.763 giá trị). Phải: số AP phát hiện trên mỗi fingerprint.",
     12, False, GREY)
src(s, "results/data_audit.md §2-3; figures/fig13_eda_rssi_and_sparsity.png")

# 4 ------------------------------------------------------------- normalisation
s = slide("Bước 1-2: chuẩn hoá RSSI sang “positive representation”",
          "Preprocessor.positive_representation / internal_utility_matrix",
          "Ví dụ lấy từ dòng 3248 của trainingData: -77 → 27, -89 → 15, -78 → 26.")
text(s, 0.6, 1.7, 6.2, 4.9,
     ["• Không phát hiện (100) → 0 (“không có thông tin”).",
      "• Đã phát hiện: đưa RSSI về [0,1] theo min/max của train, rồi ánh xạ sang [1, 100].",
      "• Làm tròn thành số nguyên dương; không bao giờ để ô đã phát hiện làm tròn về 0.",
      "• Kết quả q(i,T) là số nguyên dương → EFIM cần utility dương cho các cận trên.",
      "• Q_MAX = 100 là lựa chọn để dễ đọc, không phải siêu tham số được tinh chỉnh."],
     15)
box(s, 7.1, 1.8, 5.7, 1.2,
    ["Công thức",
     "q = round( 1 + (RSSI − RSSI_min) / (RSSI_max − RSSI_min) × 99 )"], BLUE, 14)
text(s, 7.1, 3.2, 5.7, 0.4,
     "Tham số fit trên train: RSSI_min = −104, RSSI_max = 0 (n = 19.937 dòng)", 13, False, GREY)
table(s, 7.1, 3.8, 5.7,
      [["WAP", "RSSI thô", "q(i,T)"],
       ["WAP255", "−77", "27"], ["WAP284", "−89", "15"],
       ["WAP310", "−78", "26"], ["WAP366", "−78", "26"]],
      [1.9, 1.9, 1.9], 14)
text(s, 7.1, 6.0, 5.7, 0.6,
     "fit_preprocessor kiểm tra khoảng RSSI phát hiện nằm trong [−104, 0], nếu không sẽ báo lỗi.",
     12, False, GREY)
src(s, "src/preprocess_uji.py; configs/experiment.yaml (preprocessing)")

# 5 ------------------------------------------------------------- transactions
s = slide("Bước 3: mỗi fingerprint thành một utility transaction",
          "Item = WAP; một WAP có mặt trong transaction nếu giá trị ≠ 100",
          "Dòng rỗng giữ nguyên trong dataframe để chỉ số khớp nhau, nhưng bộ khai phá bỏ chúng.")
box(s, 0.6, 1.8, 3.6, 1.7, ["Dòng CSV (dòng 3248)", "520 cột WAP", "4 cột ≠ 100, 516 cột = 100"], BLUE, 14)
arrow(s, 4.3, 2.5)
box(s, 4.8, 1.8, 3.6, 1.7, ["Transaction", "{WAP255: 27, WAP284: 15,", "WAP310: 26, WAP366: 26}"], ACCENT, 14)
arrow(s, 8.5, 2.5)
box(s, 9.0, 1.8, 3.7, 1.7, ["Sau khi có p(i)", "Model A: tổng utility = 94", "Model B: tổng utility ≈ 15,5"], GREEN, 14)
table(s, 0.6, 3.9, 7.4,
      [["Thống kê (trainingData)", "Giá trị"],
       ["Số dòng / transaction", "19.937"],
       ["Transaction không rỗng", "19.861"],
       ["Transaction rỗng (76 dòng không phát hiện AP nào)", "76"],
       ["Độ dài trung bình (không rỗng)", "18,06"],
       ["Số item khác nhau thực sự xuất hiện", "465 / 520"]],
      [5.4, 2.0], 13, 0.45)
text(s, 8.3, 3.9, 4.5, 2.8,
     ["• 76 dòng rỗng tập trung ở vài thiết bị (PHONEID 22: 14, PHONEID 1: 59…) — nghi lỗi thu thập; vẫn giữ cho bộ phân lớp để mọi điều kiện thấy cùng dữ liệu.",
      "• Không có AP nào xuất hiện trong hơn 23,8% fingerprint."], 13)
src(s, "Preprocessor.transactions; results/huim_summary.json (database); results/data_audit.md §3-4")

# 6 ------------------------------------------------------------- p(i)
s = slide("Bước 4: external utility p(i) — 3 mô hình",
          "Internal utility q dùng chung; chỉ p(i) khác nhau để ablation cô lập đúng một biến",
          "Đây là phần do dự án tự định nghĩa, không phải chuẩn trong tài liệu: dữ liệu fingerprint không có sẵn đơn giá hay số lượng.")
table(s, 0.6, 1.8, 12.1,
      [["Mô hình", "p(i)", "Vai trò"],
       ["A – Signal", "p(i) = 1 với mọi WAP", "Điều kiện đối chứng"],
       ["B – Discriminative", "max(I(A_i;Y), 1e-6) / max_j I(A_j;Y)", "Mutual information với nhãn BUILDINGID_FLOOR"],
       ["C – Rare-discriminative", "I(A_i;Y) × log(N / (1 + support_i)), chuẩn hoá về (0,1]", "Giảm trọng số AP xuất hiện khắp nơi"]],
      [2.8, 5.6, 3.7], 13, 0.6)
text(s, 0.6, 4.4, 12.1, 2.5,
     ["• Y = BUILDINGID_FLOOR (13 lớp, H(Y) = 3,639 bit). SPACEID bị loại vì bằng 0 toàn bộ trong validationData.",
      "• I(A;Y) tính từ histogram đồng thời với 6 trạng thái: 1 “không phát hiện” + 5 khoảng dBm, biên [−104, −90, −80, −70, −60, 0].",
      "• Model B: p_mean = 0,175; AP tốt nhất WAP087 (0,438 bit). Model A: tổng utility của DB = 9.058.242.",
      "• Sàn 1e-6 giữ p > 0 vì EFIM yêu cầu utility dương."], 14)
src(s, "src/utility_models.py; results/huim_summary.json (utility_models)")

# 7 ------------------------------------------------------------- leakage
s = slide("Quy tắc chống rò rỉ và những gì cố ý không làm",
          "Các quyết định tiền xử lý được ghi lại để không bị hiểu là bước ẩn",
          "Các cổng chặn rò rỉ được cài đặt trong code, không chỉ là quy ước.")
text(s, 0.6, 1.7, 5.9, 0.5, "Chống rò rỉ dữ liệu", 18, True, BLUE)
text(s, 0.6, 2.25, 5.9, 4.5,
     ["• fit_preprocessor chỉ gọi trên trainingData (RSSI min/max).",
      "• build_external_utility ném lỗi nếu split_name khác “training”.",
      "• p(i) (mutual information) chỉ ước lượng từ trainingData.",
      "• validationData chỉ được transform, không bao giờ dùng để fit."], 14)
text(s, 6.9, 1.7, 5.9, 0.5, "Không làm (và lý do)", 18, True, ACCENT)
text(s, 6.9, 2.25, 5.9, 4.5,
     ["• Không xoá 637 dòng trùng hệt trong train: sẽ là bước không được ghi nhận; mọi điều kiện thấy cùng dữ liệu.",
      "• Không vá 137 ô 0 dBm (đều từ một thiết bị PHONEID 19): chỉ ghi lại, và neo chuẩn hoá vào khoảng RSSI đã được tài liệu hoá.",
      "• Không dùng SPACEID / RELATIVEPOSITION làm nhãn (validation toàn 0).",
      "• Không sửa file CSV gốc (SHA-256 được ghi trong results/data_summary.json)."], 14)
src(s, "src/preprocess_uji.py, src/utility_models.py; results/data_audit.md §1, §4, §8")

# 8 ------------------------------------------------------------- EFIM internal
s = slide("Bước 5: tiền xử lý bên trong EFIM",
          "Chạy ở đầu mỗi lần khai phá, trước khi tìm kiếm theo chiều sâu",
          "Số liệu item sau TWU-pruning lấy từ figures/fig08_minutil_vs_items_surviving_twu.csv. Tổng cộng 465 item xuất hiện trong dữ liệu.")
text(s, 0.6, 1.7, 6.3, 5.1,
     ["1. Kiểm tra mọi p(i) > 0 và q > 0; thiếu thì báo lỗi.",
      "2. Tính TU(T) = Σ q·p cho mỗi transaction, TWU(i) = tổng TU của các transaction chứa i.",
      "3. TWU-pruning: bỏ item có TWU < minUtil.",
      "4. Sắp item theo TWU tăng dần (bằng nhau thì theo nhãn).",
      "5. Dựng DB đã cắt tỉa, bỏ transaction rỗng, gộp transaction giống hệt nhau (transaction merging, có cộng dồn count).",
      "6. Tính local utility / subtree utility cho gốc bằng Fast Utility Counting."], 14)
table(s, 7.2, 1.8, 5.6,
      [["minUtil", "A: item còn lại", "B: item còn lại"],
       ["20%", "17", "41"], ["10%", "56", "60"], ["5%", "151", "93"],
       ["2,5%", "231", "175"], ["2%", "250", "204"]],
      [1.4, 2.1, 2.1], 14, 0.5)
text(s, 7.2, 5.0, 5.6, 1.6,
     "minUtil tính theo % tổng utility của DB. Ngưỡng càng cao thì TWU-pruning càng loại nhiều item; trong 465 item ban đầu, ở minUtil 20% chỉ còn 17 (A) và 41 (B).",
     13, False, GREY)
src(s, "src/huim/efim.py (mine); figures/fig08_minutil_vs_items_surviving_twu.csv")

prs.save(OUT)
print("saved", OUT)
