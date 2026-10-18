"""BAOCAO / bước 5 - tạo slide PowerPoint (16:9) từ so_lieu/ và diagram/.

    python BAOCAO/ma_nguon/05_tao_slide_pptx.py

Biểu đồ cột/đường là biểu đồ gốc của PowerPoint (sửa được số liệu trong PowerPoint);
hình phức tạp (heatmap, bản đồ, CDF, sơ đồ) lấy từ diagram/. Mọi số đọc từ so_lieu/.
"""
from __future__ import annotations

import json

import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from hinh_chung import BAOCAO, DIAGRAM, SO_LIEU, theta_txt, vn
from nhan import lbl, lbl_ngan

J = json.loads((SO_LIEU / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))
B, S = J["tot_nhat"], J["ban_dau"]
CHK = pd.read_csv(SO_LIEU / "01_kiem_chung_union_vs_EFIM.csv")
S2 = pd.read_csv(SO_LIEU / "04_buoc2_model_ABC.csv")
S3 = pd.read_csv(SO_LIEU / "05_buoc3_minUtil_HUIM_chung.csv")
S4 = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_toa.csv")
S6 = pd.read_csv(SO_LIEU / "07_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
S7 = pd.read_csv(SO_LIEU / "08_buoc7_ensemble.csv")
S8 = pd.read_csv(SO_LIEU / "09_buoc8_thoi_gian_bo_nho.csv")
RANK = pd.read_csv(SO_LIEU / "10_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})
TOA = pd.read_csv(SO_LIEU / "11_sai_so_theo_toa.csv", dtype={"toa": str})

NAVY = RGBColor(0x0D, 0x36, 0x6B)
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
GRID = RGBColor(0xE1, 0xE0, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xF2, 0xF4, 0xF8)
ICE = RGBColor(0xCD, 0xE2, 0xFB)
MODEL = {"A": RGBColor(0x2A, 0x78, 0xD6), "B": RGBColor(0xEB, 0x68, 0x34),
         "C": RGBColor(0x1B, 0xAF, 0x7A)}
DEV, VAL = RGBColor(0x86, 0xB6, 0xEF), RGBColor(0x1C, 0x5C, 0xAB)
GREY = RGBColor(0x9A, 0x9A, 0x9A)
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, Hh = 13.333, 7.5


def m(x, nd=2):
    return vn(x, nd) + " m"


def text(slide, x, y, w, h, runs, size=16, color=INK, bold=False, font=BODY,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        parts = para if isinstance(para, tuple) and isinstance(para[0], tuple) else (
            (para,) if not isinstance(para, tuple) else (para,))
        for part in parts:
            if isinstance(part, tuple):
                t, fmt = part
            else:
                t, fmt = part, {}
            r = p.add_run()
            r.text = t
            r.font.name = fmt.get("font", font)
            r.font.size = Pt(fmt.get("size", size))
            r.font.bold = fmt.get("bold", bold)
            r.font.italic = fmt.get("italic", False)
            r.font.color.rgb = fmt.get("color", color)
        p.space_after = Pt(6)
    return tb


def bullets(slide, x, y, w, h, items, size=15, color=INK):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Emu(Inches(0.28))))
        pPr.set("indent", str(-Emu(Inches(0.22))))
        bu = pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar", {"char": "•"})
        pPr.append(bu)
        parts = it if isinstance(it, list) else [it]
        for part in parts:
            t, b = (part, False) if isinstance(part, str) else part
            r = p.add_run()
            r.text = t
            r.font.name, r.font.size, r.font.bold = BODY, Pt(size), b
            r.font.color.rgb = color
        p.space_after = Pt(8)
    return tb


def title(slide, t, sub=None):
    text(slide, 0.6, 0.35, W - 1.2, 0.8, t, size=30, bold=True, font=HEAD, color=NAVY)
    if sub:
        text(slide, 0.6, 1.08, W - 1.2, 0.5, sub, size=15, color=INK2)


def footer(slide, src):
    text(slide, 0.6, Hh - 0.45, W - 1.2, 0.3, src, size=10, color=MUTED)


def card(slide, x, y, w, h, big, small, fill=SOFT, big_color=NAVY, small_color=INK2):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    text(slide, x + 0.2, y + 0.15, w - 0.4, h * 0.5, big, size=36, bold=True, color=big_color,
         font=HEAD, anchor=MSO_ANCHOR.BOTTOM)
    text(slide, x + 0.2, y + h * 0.55, w - 0.4, h * 0.42, small, size=13, color=small_color)


def picture(slide, name, x, y, w=None, h=None):
    p = DIAGRAM / f"{name}.png"
    return slide.shapes.add_picture(str(p), Inches(x), Inches(y),
                                    Inches(w) if w else None, Inches(h) if h else None)


def style_chart(ch, title_txt=None, legend=True, y_title=None, x_title=None, labels=True, fmt='0.0'):
    ch.font.name, ch.font.size = BODY, Pt(12)
    ch.font.color.rgb = INK2
    if title_txt:
        ch.has_title = True
        ch.chart_title.text_frame.text = title_txt
        tp = ch.chart_title.text_frame.paragraphs[0]
        tp.runs[0].font.size, tp.runs[0].font.bold = Pt(14), True
        tp.runs[0].font.color.rgb = INK
    else:
        ch.has_title = False
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(11)
    va = ch.value_axis
    va.minimum_scale = 0                 # cột / đường luôn bắt đầu từ 0, không phóng đại chênh lệch
    va.major_gridlines.format.line.color.rgb = GRID
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(11)
    ch.category_axis.tick_labels.font.size = Pt(11)
    ch.category_axis.format.line.color.rgb = GRID
    if y_title:
        va.has_title = True
        va.axis_title.text_frame.text = y_title
        va.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
    if x_title:
        ca = ch.category_axis
        ca.has_title = True
        ca.axis_title.text_frame.text = x_title
        ca.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
    if labels:
        pl = ch.plots[0]
        pl.has_data_labels = True
        pl.data_labels.number_format = fmt
        pl.data_labels.number_format_is_linked = False
        pl.data_labels.font.size = Pt(10)
        pl.data_labels.font.color.rgb = INK


def bar_chart(slide, x, y, w, h, cats, series, colors, **kw):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, [round(float(v), 3) for v in vals])
    gf = slide.shapes.add_chart(kw.pop("kind", XL_CHART_TYPE.COLUMN_CLUSTERED), Inches(x), Inches(y),
                                Inches(w), Inches(h), cd)
    ch = gf.chart
    for s, c in zip(ch.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = c
    ch.plots[0].gap_width = 60
    ch.plots[0].overlap = -10
    style_chart(ch, **kw)
    return ch


def line_chart(slide, x, y, w, h, cats, series, colors, dashes=None, **kw):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, [None if pd.isna(v) else round(float(v), 3) for v in vals])
    ch = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    for i, (s, c) in enumerate(zip(ch.series, colors)):
        s.format.line.color.rgb = c
        s.format.line.width = Pt(2.25)
        s.smooth = False
        s.marker.style = XL_MARKER_STYLE.CIRCLE
        s.marker.size = 7
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = c
        s.marker.format.line.color.rgb = c
        if dashes and dashes[i]:
            from pptx.enum.dml import MSO_LINE_DASH_STYLE
            s.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    style_chart(ch, **kw)
    return ch


def toa(k, b):
    return TOA[(TOA.cau_hinh == k) & (TOA.toa == str(b))].iloc[0]


def sec(slide_title):
    s = prs.slides.add_slide(BLANK)
    return s


best3 = S3.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
best4 = S4.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
red = 100 * (1 - B["test_mean_m"] / S["test_mean_m"])

# ------------------------------------------------------------ 1. bìa
s = prs.slides.add_slide(BLANK)
bg = s.background.fill
bg.solid()
bg.fore_color.rgb = NAVY
text(s, 0.7, 0.7, 11.5, 0.5, "BÁO CÁO BÀI TÌM HIỂU · UJIIndoorLoc", size=16, color=ICE)
text(s, 0.7, 1.2, 11.9, 1.6, "HUIM cho định vị trong nhà bằng vân tay Wi-Fi", size=40, bold=True,
     color=WHITE, font=HEAD)
text(s, 0.7, 2.55, 11.9, 0.9, "Tối ưu việc chọn Access Point bằng khai thác tập mục tiện ích cao - "
     "chỉ dùng các cấu hình có HUIM", size=18, color=ICE)
for i, (big, small) in enumerate([
        (m(B["test_mean_m"]), "sai số trung bình trên tập test\n" + lbl_ngan(B["config"])),
        ("−" + vn(red, 1) + " %", f"so với cấu hình ban đầu\n({m(S['test_mean_m'])}, HUIM chung A, θ = 1,9294 %)"),
        (vn(toa("ban_dau", 1).sai_so_tb_m, 1) + " → " + m(toa("tot_nhat", 1).sai_so_tb_m, 1),
         "sai số tòa 1 - tòa hỏng nhất ban đầu")]):
    card(s, 0.7 + i * 4.05, 4.1, 3.8, 2.2, big, small, fill=RGBColor(0x18, 0x4F, 0x95),
         big_color=WHITE, small_color=ICE)
text(s, 0.7, 6.75, 11.9, 0.4, "16/10/2026 · chọn cấu hình trên 6 fold dev của trainingData; "
     "tập test = validationData (1.111 mẫu), chỉ dùng để báo cáo", size=12, color=ICE)

# ------------------------------------------------------------ 1b. dữ liệu và tập test
s = prs.slides.add_slide(BLANK)
title(s, "Dữ liệu và tập test",
      "Mọi con số \"trên tập test\" trong bài là sai số trên validationData của UJIIndoorLoc")
card(s, 0.6, 1.7, 3.9, 2.4, "19.937", "trainingData: radio map, khai phá HUIM và 6 fold dev "
     "(GroupKFold theo USERID) để chọn cấu hình")
card(s, 4.72, 1.7, 3.9, 2.4, "1.111", "validationData = TẬP TEST: chỉ để báo cáo, "
     "không tham gia chọn", fill=NAVY, big_color=WHITE, small_color=ICE)
card(s, 8.84, 1.7, 3.9, 2.4, m(B["test_mean_m"]), "sai số trung bình trên tập test của cấu hình "
     "chọn theo dev")
bullets(s, 0.6, 4.5, 12.2, 2.2, [
    ["Kho UCI chỉ công bố 2 file có nhãn; trang mô tả gọi validationData.csv là ",
     ("\"1111 validation/test records\"", True)],
    ["Vai trò \"validation\" (chọn tham số) do ", ("6 fold dev tách từ trainingData", True), " đảm nhận"],
    "Tập test khác người đo, điện thoại và thời điểm (khoảng 4 tháng sau) → đo đúng khả năng gặp người dùng mới",
], size=16)
footer(s, "Nguồn: archive.ics.uci.edu/dataset/310/ujiindoorloc; giao thức: báo cáo Word, mục 1.1-1.2")

# ------------------------------------------------------------ 2. vấn đề
s = prs.slides.add_slide(BLANK)
title(s, "Vì sao HUIM ban đầu sai 19 m", "86 AP, θ = 1,9294 %, khai phá chung 3 tòa")
bullets(s, 0.6, 1.7, 5.0, 4.8, [
    ["minUtil tính theo tổng utility của ", ("cả 3 tòa", True)],
    ["Tòa 2 nhiều dòng, AP cùng xuất hiện dày → ", ("chiếm gần hết HUI", True)],
    ["Tòa 1: ", ("68,4 %", True), " mẫu test không thấy AP nào trong 86 AP"],
    ["Model B/C chọn ", ("0 AP", True), " ở tòa 1 → đổi hàm utility không cứu được"],
    ["Hướng sửa: khai phá ", ("riêng từng tòa", True), ", hạ θ bằng thuật toán tìm union chính xác"],
], size=16)
picture(s, "H05_so_AP_moi_toa", 5.9, 1.75, w=6.9)
footer(s, "Nguồn: so_lieu/05_buoc3_minUtil_HUIM_chung.csv, 06_buoc4_HUIM_theo_toa.csv")

# ------------------------------------------------------------ 3. luồng
s = prs.slides.add_slide(BLANK)
title(s, "Luồng HUIM-IPS", "fingerprint → giao dịch utility → HUIM (θ) → tập AP → S4 → sai số")
picture(s, "H01_so_do_luong_HUIM_IPS", 1.2, 1.55, w=10.9)
text(s, 0.6, 6.55, 12.1, 0.5, [(("q(i,T) = RSSI chuẩn hoá 1-100  ·  p(i): A = 1, B = MI(AP; vị trí), "
     "C = MI × IDF  ·  u(X) = Σ_{T⊇X} Σ_{i∈X} q(i,T)·p(i)  ·  HUI nếu u(X) ≥ θ·Σ TU(T)", {"size": 14}),)],
     color=INK2)

# ------------------------------------------------------------ 4. thuật toán
s = prs.slides.add_slide(BLANK)
title(s, "Hạ θ mà không bị EFIM bùng nổ", "Chỉ cần MỘT HUI cho mỗi AP để biết AP đó thuộc union")
picture(s, "H02_EFIM_bung_no_va_thoi_gian_tim_union", 0.5, 1.7, w=8.3)
ok = int(CHK["identical"].astype(str).str.lower().eq("true").sum())
card(s, 9.1, 1.75, 3.7, 1.9, f"{ok}/{len(CHK)}", "mức θ mà EFIM chạy xong: union trùng khớp từng AP")
bullets(s, 9.1, 3.9, 3.8, 3.0, [
    "Giữ duyệt DFS + cận TWU, lu, su của EFIM",
    ["Thêm ", ("luật phủ", True), ": cắt cây con không thể thêm AP mới vào union"],
    "Chính xác, không xấp xỉ; mỗi θ tính độc lập",
], size=14)
footer(s, "Nguồn: so_lieu/01_kiem_chung_union_vs_EFIM.csv, 03_EFIM_so_HUI_thoi_gian_bo_nho.csv; src/huim/union_search.py")

# ------------------------------------------------------------ 5. bước 2
s = prs.slides.add_slide(BLANK)
title(s, "Bước 2 · Model A / B / C", "HUIM chung, θ mà EFIM liệt kê xong; tốt nhất theo dev của mỗi model")
b2 = S2.sort_values("dev_sai_so_tb_m").groupby("model").first().reset_index()
cats = [f"Model {r.model}\nθ = {theta_txt(r.minUtil_pct)}, {int(r.so_AP)} AP" for _, r in b2.iterrows()]
bar_chart(s, 0.6, 1.6, 7.4, 5.2, cats, [("dev (chọn)", b2.dev_sai_so_tb_m), ("tập test", b2.test_sai_so_tb_m)],
          [DEV, VAL], y_title="Sai số trung bình (m)")
bar_chart(s, 8.2, 1.6, 4.6, 5.2, [f"Model {x}" for x in b2.model],
          [("Tòa 0", b2.test_toa0_m), ("Tòa 1", b2.test_toa1_m), ("Tòa 2", b2.test_toa2_m)],
          [RGBColor(0x62, 0x50, 0xD6), RGBColor(0xED, 0xA1, 0x00), RGBColor(0x00, 0x83, 0x00)],
          title_txt="Tập test theo tòa (m)", fmt='0')
footer(s, "Nguồn: so_lieu/04_buoc2_model_ABC.csv")

# ------------------------------------------------------------ 6-7. bước 3, 4
for S_, scope, ttl in ((S3, "global", "Bước 3 · Quét minUtil θ, HUIM chung 3 tòa"),
                       (S4, "per_building", "Bước 4 · Quét minUtil θ, HUIM riêng từng tòa")):
    s = prs.slides.add_slide(BLANK)
    bst = S_.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
    title(s, ttl, f"Tốt nhất theo dev: Model {bst.model}, θ = {theta_txt(bst.minUtil_pct)}, "
          f"{int(bst.so_AP)} AP · dev {m(bst.dev_sai_so_tb_m)} · tập test {m(bst.test_sai_so_tb_m)}")
    ths = sorted(S_.minUtil_pct.unique())
    cats = [theta_txt(t) for t in ths]
    ser = []
    for mm in "ABC":
        g = S_[S_.model == mm].set_index("minUtil_pct").reindex(ths)
        ser.append((f"Model {mm}", g.test_sai_so_tb_m))
    line_chart(s, 0.6, 1.6, 7.6, 5.3, cats, ser, [MODEL[x] for x in "ABC"], labels=False,
               y_title="Sai số tập test (m)", x_title="minUtil θ (% tổng utility của phạm vi)",
               title_txt="Sai số trung bình theo θ")
    ser = []
    for mm in "ABC":
        g = S_[S_.model == mm].set_index("minUtil_pct").reindex(ths)
        ser.append((f"Model {mm}", g.so_AP))
    ch = line_chart(s, 8.4, 1.6, 4.4, 5.3, [theta_txt(t).replace(" %", "") for t in ths], ser,
                    [MODEL[x] for x in "ABC"], labels=False,
                    y_title="Số AP", title_txt="Số AP theo θ", x_title="minUtil θ (%)")
    ch.category_axis.tick_labels.font.size = Pt(9)
    footer(s, f"Nguồn: so_lieu/{'05_buoc3_minUtil_HUIM_chung' if scope == 'global' else '06_buoc4_HUIM_theo_toa'}.csv "
           "(ô trống: θ không có AP / chưa tính được)")

# ------------------------------------------------------------ 8. đánh đổi
s = prs.slides.add_slide(BLANK)
title(s, "Đánh đổi số AP và sai số", "Mỗi điểm là một (phạm vi, model, θ); nhãn cạnh điểm là θ")
picture(s, "H06_danh_doi_so_AP_sai_so", 0.6, 1.5, w=12.1)
bullets(s, 0.6, 6.35, 12.1, 0.8, [
    ["Ở 150-200 AP, ", ("HUIM theo tòa", True), " sai số thấp hơn HUIM chung; ở ~5,3 m, HUIM chung C θ = 0,5 % "
     "cần ít AP hơn (229 so với 303-311)"],
], size=13)
footer(s, "Nguồn: so_lieu/05_..., 06_...")

# ------------------------------------------------------------ 9. bước 6
if len(S6):
    s = prs.slides.add_slide(BLANK)
    title(s, "Bước 6 · Quy tắc chuyển HUI thành tập AP", "union / top-n / frequent / weighted, cùng θ và cùng S4")
    for i, (scope, g) in enumerate(S6.groupby("pham_vi", sort=False)):
        cats = [r.quy_tac + ("" if pd.isna(r.tham_so) or r.tham_so == "" else f" {r.tham_so}") + f"\n{int(r.so_AP)} AP"
                for _, r in g.iterrows()]
        ww = (W - 1.4) / max(1, S6.pham_vi.nunique())
        bar_chart(s, 0.6 + i * ww, 1.6, ww - 0.2, 5.3, cats,
                  [("dev (chọn)", g.dev_sai_so_tb_m), ("tập test", g.test_sai_so_tb_m)], [DEV, VAL],
                  title_txt=("HUIM chung" if scope == "global" else "HUIM theo tòa") +
                  f", Model {g.model.iloc[0]}, θ = {theta_txt(g.minUtil_pct.iloc[0])}",
                  y_title="Sai số trung bình (m)")
    footer(s, "Nguồn: so_lieu/07_buoc6_quy_tac_chon_AP.csv")

# ------------------------------------------------------------ 10. bước 7
s = prs.slides.add_slide(BLANK)
title(s, "Bước 7 · Ensemble nhiều cấu hình HUIM", "toạ độ = trung bình / trung vị của các thành viên; tầng = đa số")
single = RANK[RANK.loai == "don"].iloc[0]
picture(s, "H09_ensemble", 0.6, 1.55, w=9.0)
gain = single.test_sai_so_tb_m - B["test_mean_m"]
card(s, 9.9, 1.7, 2.9, 1.9, "−" + m(gain), "tập test so với cấu hình đơn lẻ tốt nhất")
t_s = S8[S8.cau_hinh == single.cau_hinh]
t_b = S8[S8.cau_hinh == B["config"]]
if len(t_s) and len(t_b):
    card(s, 9.9, 3.8, 2.9, 1.9, vn(t_b.iloc[0].ms_per_fp / t_s.iloc[0].ms_per_fp, 1) + "×",
         "thời gian định vị so với cấu hình đơn lẻ")
bullets(s, 0.6, 5.35, 12.1, 1.5, [
    ["Ensemble tốt nhất theo dev: trung vị toạ độ của ", ("3 cấu hình θ = 0,5 %", True),
     " (2 HUIM chung + 1 HUIM theo tòa)"],
    ["Lợi ích nhỏ so với chi phí: nếu cần nhanh, dùng cấu hình đơn lẻ ", (lbl_ngan(single.cau_hinh), True)],
], size=14)
footer(s, "Nguồn: so_lieu/08_buoc7_ensemble.csv, 09_buoc8_thoi_gian_bo_nho.csv; trục ngang của hình đã phóng to")

# ------------------------------------------------------------ 11. kết quả theo tòa
s = prs.slides.add_slide(BLANK)
title(s, "Cấu hình cuối cùng · sai số theo tòa", lbl(B["config"]))
cats = ["Tòa 0", "Tòa 1", "Tòa 2", "Toàn bộ"]
bar_chart(s, 0.6, 1.6, 8.0, 5.3, cats,
          [("Ban đầu (chung A, θ = 1,9294 %)", [toa("ban_dau", b).sai_so_tb_m for b in ("0", "1", "2", "Tong")]),
           ("Tốt nhất", [toa("tot_nhat", b).sai_so_tb_m for b in ("0", "1", "2", "Tong")])],
          [GREY, VAL], y_title="Sai số trung bình trên tập test (m)")
r = toa("tot_nhat", "Tong")
card(s, 8.9, 1.7, 3.9, 1.6, m(r.trung_vi_m), "trung vị sai số")
card(s, 8.9, 3.5, 3.9, 1.6, vn(r.toa_tang_dung_pct, 1) + " %", "đúng cả tòa và tầng")
card(s, 8.9, 5.3, 3.9, 1.6, vn(r.trong_5m_pct, 1) + " %", "mẫu có sai số ≤ 5 m")
footer(s, "Nguồn: so_lieu/11_sai_so_theo_toa.csv")

# ------------------------------------------------------------ 12. heatmap + CDF
s = prs.slides.add_slide(BLANK)
title(s, "Theo tòa × tầng và phân phối sai số", "tập test (validationData), 1.111 mẫu")
picture(s, "H13_heatmap_sai_so_toa_tang", 0.5, 1.6, w=6.6)
picture(s, "H14_CDF_sai_so", 7.3, 1.6, w=5.6)
footer(s, "Nguồn: so_lieu/12_sai_so_theo_toa_tang.csv, 13_du_doan_tung_mau_tap_test.csv")

# ------------------------------------------------------------ 13. bản đồ
s = prs.slides.add_slide(BLANK)
title(s, "Sai số trên bản đồ", "vị trí thật của mẫu test, tô màu theo sai số")
picture(s, "H15_ban_do_sai_so", 0.6, 1.6, w=12.1)
footer(s, "Nguồn: so_lieu/13_du_doan_tung_mau_tap_test.csv")

# ------------------------------------------------------------ 14. thời gian & bộ nhớ
s = prs.slides.add_slide(BLANK)
title(s, "Thời gian và bộ nhớ", "định vị 1.111 mẫu một lô, trung vị 3 lần, máy 12 nhân")
d8 = S8.copy()
cats = [("Ensemble tốt nhất" if c.startswith("E_") else lbl_ngan(c)) + f"\n{int(n)} AP"
        for c, n in zip(d8.cau_hinh, d8.so_AP)]
bar_chart(s, 0.6, 1.6, 6.2, 5.3, cats, [("ms / fingerprint", d8.ms_per_fp)], [VAL], legend=False,
          kind=XL_CHART_TYPE.BAR_CLUSTERED, title_txt="Thời gian định vị (ms / fingerprint)", fmt='0.00')
bar_chart(s, 6.9, 1.6, 5.9, 5.3, cats, [("MB", d8.radio_map_mb)], [DEV], legend=False,
          kind=XL_CHART_TYPE.BAR_CLUSTERED, title_txt="Radio map (MB, float64)", fmt='0.0')
footer(s, "Nguồn: so_lieu/09_buoc8_thoi_gian_bo_nho.csv; khai phá HUIM: so_lieu/02_..., 03_...")

# ------------------------------------------------------------ 15. hạn chế
s = prs.slides.add_slide(BLANK)
title(s, "Hạn chế cần nói rõ")
bullets(s, 0.6, 1.5, 12.1, 5.4, [
    "Chỉ so sánh các biến thể HUIM với nhau - không kết luận HUIM tốt hơn cách chọn AP khác",
    "HUI khai phá trên toàn trainingData nên dev hơi lạc quan (như nhau cho mọi cấu hình); tập test sạch",
    "HUIM theo tòa phải đoán tòa trước; mẫu đoán sai tòa được định vị trong tòa sai (đã tính vào sai số)",
    "q(i,T), p(i) là lựa chọn mô hình hoá; HUIM không tối ưu trực tiếp sai số → mọi lợi ích phải đo",
    "Thời gian đo bằng Python thuần trên một máy; chỉ dùng để so sánh trong báo cáo này",
], size=17)

# ------------------------------------------------------------ 16. kết luận
s = prs.slides.add_slide(BLANK)
bg = s.background.fill
bg.solid()
bg.fore_color.rgb = NAVY
text(s, 0.7, 0.6, 11.9, 0.9, "Kết luận", size=36, bold=True, color=WHITE, font=HEAD)
bullets(s, 0.7, 1.7, 11.9, 4.0, [
    ["Lỗi của HUIM ban đầu: θ tính trên cả 3 tòa quá cao, ", ("tòa 1 thiếu AP", True),
     "; đổi hàm utility không sửa được"],
    ["Hạ θ (nhờ tìm union chính xác) hoặc ", ("khai phá riêng từng tòa", True), " đều cứu tòa 1: ",
     (m(toa('ban_dau', 1).sai_so_tb_m, 1) + " → " + m(toa('tot_nhat', 1).sai_so_tb_m, 1), True)],
    ["Tìm union chính xác khớp EFIM ở ", (f"{ok}/{len(CHK)}", True), " mức θ mà EFIM chạy xong"],
    ["Chọn theo dev: ", (lbl_ngan(B["config"]), True), " → ", (m(B["test_mean_m"]), True),
     " trên tập test"],
    ["Đơn lẻ, nhanh hơn: ", (lbl_ngan(RANK[RANK.loai == "don"].iloc[0].cau_hinh), True), " → ",
     (m(RANK[RANK.loai == "don"].iloc[0].test_sai_so_tb_m), True)],
], size=18, color=WHITE)
text(s, 0.7, 6.3, 11.9, 0.6, "Chạy lại: python BAOCAO/ma_nguon/00_chay_lai_toan_bo.py  ·  "
     "đọc BAOCAO/00_HUONG_DAN_DOC.md trước", size=13, color=ICE)

out = BAOCAO / "Slide_HUIM_IPS_UJIIndoorLoc.pptx"
prs.save(str(out))
print("đã lưu", out, len(prs.slides), "slide")
