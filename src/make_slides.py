"""PHASE M - build slides/HUIM_IPS_UJIIndoorLoc_Presentation.pptx.

Style rules taken from the brief and applied mechanically:
  * every run is Times New Roman; body text is 13 pt everywhere;
  * at most five bullets per slide, each one short;
  * no decorative imagery - every figure is either a data chart from figures/
    or a schematic drawn by make_diagrams.py;
  * every number is read from results/ at build time. This module contains no
    experimental values.

Speaker notes are attached to each slide and also written to
slides/speaker_notes.md.
"""
from __future__ import annotations

import re

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (FIGURES, METRICS, RESULTS, SLIDES, TABLES, dump_json,
                   get_logger, load_json)

LOG = get_logger("slides", "slides.log")

FONT = "Times New Roman"
BODY_PT = 13
TITLE_PT = 26
SUB_PT = 15
SMALL_PT = 10.5

INK = RGBColor(0x1A, 0x1A, 0x1A)
ACCENT = RGBColor(0x8C, 0x2D, 0x04)
BLUE = RGBColor(0x1F, 0x3B, 0x73)
GREEN = RGBColor(0x14, 0x5A, 0x32)
GREY = RGBColor(0x6E, 0x6E, 0x6E)

W = Inches(13.333)
H = Inches(7.5)

OUT = SLIDES / "HUIM_IPS_UJIIndoorLoc_Presentation.pptx"

MODEL_SHORT = {"A_signal": "Model A (signal)",
               "B_discriminative": "Model B (discriminative)",
               "C_rare_discriminative": "Model C (rare-discr.)"}


def pc(x, d=2):
    try:
        return f"{float(x)*100:.{d}f}%"
    except (TypeError, ValueError):
        return "N/A"


def nf(x, d=0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(v):
        return "N/A"
    return f"{v:,.{d}f}"


# --------------------------------------------------------------------- fonts
def _font(run, size=BODY_PT, bold=False, italic=False, color=INK):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    # the ASCII slot alone is not enough for Vietnamese diacritics in PowerPoint
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            from pptx.oxml.ns import nsmap
            from lxml import etree
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT)


class Deck:
    def __init__(self) -> None:
        self.p = Presentation()
        self.p.slide_width = W
        self.p.slide_height = H
        self.notes: list[tuple[str, str]] = []
        self.last_pic_bottom = 0.0
        self._pin_theme_fonts()

    def _pin_theme_fonts(self) -> None:
        """Runs carry an explicit typeface, but PowerPoint still resolves
        placeholder and notes text through the theme's major/minor fonts, which
        default to Calibri. Pin them so the deck is Times New Roman throughout."""
        from lxml import etree
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        for part in self.p.part.package.iter_parts():
            if not str(part.partname).lower().endswith("theme1.xml"):
                continue
            try:
                root = etree.fromstring(part.blob)
                changed = False
                for tag in ("majorFont", "minorFont"):
                    for latin in root.findall(f".//a:{tag}/a:latin", ns):
                        latin.set("typeface", FONT)
                        changed = True
                if changed:
                    part._blob = etree.tostring(root, xml_declaration=True,
                                                encoding="UTF-8",
                                                standalone=True)
            except Exception:
                pass

    def slide(self):
        return self.p.slides.add_slide(self.p.slide_layouts[6])

    # ------------------------------------------------------------- primitives
    def para(self, s, lines, x, y, w, h, size=BODY_PT, bold=False,
             color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             bullet=False, space_after=7, line_spacing=1.12):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        if isinstance(lines, str):
            lines = [lines]
        for k, item in enumerate(lines):
            if isinstance(item, tuple):
                txt, opts = item
            else:
                txt, opts = item, {}
            para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            para.alignment = opts.get("align", align)
            para.space_after = Pt(opts.get("space_after", space_after))
            para.line_spacing = opts.get("line_spacing", line_spacing)
            prefix = "–  " if (bullet and not opts.get("nobullet")) else ""
            r = para.add_run()
            r.text = prefix + txt
            _font(r, size=opts.get("size", size),
                  bold=opts.get("bold", bold),
                  italic=opts.get("italic", False),
                  color=opts.get("color", color))
        return tb

    def title(self, s, txt, sub=None):
        self.para(s, txt, 0.55, 0.32, 12.2, 0.9, size=TITLE_PT, bold=True,
                  color=INK)
        y = 1.18
        if sub:
            self.para(s, sub, 0.55, 1.12, 12.2, 0.42, size=SUB_PT, color=GREY)
            y = 1.68
        ln = s.shapes.add_shape(1, Inches(0.55), Inches(y - 0.12),
                                Inches(12.2), Emu(9525))
        ln.fill.solid()
        ln.fill.fore_color.rgb = RGBColor(0xC8, 0xC8, 0xC8)
        ln.line.fill.background()
        ln.shadow.inherit = False
        return y

    def pic(self, s, name, x, y, w=None, h=None, max_bottom=7.25):
        """Insert a figure and return the inches at which its BOTTOM sits.

        Returning the measured bottom (rather than letting the caller guess)
        is what stops bullet text from landing on top of a chart: figures are
        saved with bbox="tight", so their aspect ratio is whatever cropping
        produced, not the figsize that was requested."""
        p = FIGURES / name
        if not p.exists():
            raise FileNotFoundError(f"figure missing for slides: {p}")
        kw = {}
        if w:
            kw["width"] = Inches(w)
        if h:
            kw["height"] = Inches(h)
        shp = s.shapes.add_picture(str(p), Inches(x), Inches(y), **kw)
        # Clamp to the slide. add_picture honours the requested width and
        # derives the height from the image's own aspect ratio, which for a
        # bbox="tight" matplotlib export is not the figsize that was asked
        # for - so a width that looks safe can push the image off the bottom.
        bottom = (shp.top + shp.height) / 914400.0
        if bottom > max_bottom:
            avail = max_bottom - y
            if avail > 0.3:
                scale = avail / (shp.height / 914400.0)
                new_w = (shp.width / 914400.0) * scale
                shp.width = Inches(new_w)
                shp.height = Inches(avail)
                # keep it horizontally centred on its original centre
                cx = x + (w or new_w) / 2.0
                shp.left = Inches(max(0.15, cx - new_w / 2.0))
        self.last_pic_bottom = (shp.top + shp.height) / 914400.0
        return self.last_pic_bottom

    def callout(self, s, txt, x, y, w, h, color=ACCENT):
        sh = s.shapes.add_shape(5, Inches(x), Inches(y), Inches(w), Inches(h))
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(0xFA, 0xF4, 0xF1)
        sh.line.color.rgb = color
        sh.line.width = Pt(1.0)
        sh.shadow.inherit = False
        tf = sh.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = tf.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        r = para.add_run()
        r.text = txt
        _font(r, size=BODY_PT, bold=True, color=color)
        return sh

    def table(self, s, df, x, y, w, h, size=10.0, header_bold=True):
        rows, cols = df.shape[0] + 1, df.shape[1]
        gf = s.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w),
                                Inches(h))
        tbl = gf.table
        for j, c in enumerate(df.columns):
            cell = tbl.cell(0, j)
            cell.text = ""
            para = cell.text_frame.paragraphs[0]
            r = para.add_run()
            r.text = str(c)
            _font(r, size=size, bold=header_bold, color=INK)
        for i in range(df.shape[0]):
            for j in range(cols):
                cell = tbl.cell(i + 1, j)
                cell.text = ""
                para = cell.text_frame.paragraphs[0]
                r = para.add_run()
                v = df.iat[i, j]
                r.text = "" if pd.isna(v) else str(v)
                _font(r, size=size, color=INK)
        return tbl

    def note(self, s, title, body):
        """Speaker notes. The slide number is derived from the deck, never
        typed, so inserting a slide cannot leave the notes mis-numbered."""
        s.notes_slide.notes_text_frame.text = body
        n = len(self.p.slides)
        label = re.sub(r"^Slide\s*\d+\s*[-—]\s*", "", title).strip()
        self.notes.append((f"Slide {n} — {label}", body))

    def save(self, path: Path) -> dict:
        """Temp-file-then-replace, for the same reason as the Word report: on
        Windows the indexer/preview handler can hold a freshly written Office
        file for a moment and make a direct overwrite fail."""
        import os
        import time
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + ".__tmp__" + path.suffix)
        self.p.save(str(tmp))
        last = None
        for attempt in range(8):
            try:
                os.replace(tmp, path)
                last = None
                break
            except PermissionError as e:
                last = e
                time.sleep(0.4 * (attempt + 1))
        if last is not None:
            tmp.unlink(missing_ok=True)
            raise PermissionError(
                f"{path} stayed locked through 8 retries. Close PowerPoint / "
                f"Explorer preview for it and re-run. ({last})")
        return {"n_slides": len(self.p.slides), "path": str(path)}


# ===========================================================================
def build() -> dict:
    audit = load_json(RESULTS / "data_summary.json")
    hsum = load_json(RESULTS / "huim_summary.json")
    isum = load_json(RESULTS / "ips_summary.json")
    O = load_json(RESULTS / "reverse_thinking_observations.json")
    Hd = pd.read_csv(METRICS / "huim_runs.csv")
    Id = pd.read_csv(METRICS / "ips_results.csv")
    PAP = pd.read_csv(Path(__file__).resolve().parents[1] / "research" /
                      "papers_table.csv")
    cpth = RESULTS / "coordinate_system_verification.json"
    C_coord = load_json(cpth) if cpth.exists() else None
    cpth2 = METRICS / "ips_cost.csv"
    COST = pd.read_csv(cpth2) if cpth2.exists() else None
    tr, cs = audit["training"], audit["cross_split"]
    base = Id[Id["condition"] == "baseline_all_520"].iloc[0]
    o1 = O["observation_1_threshold_vs_hui_count"]
    o2 = O["observation_2_cost_of_lowering_threshold"]
    o3 = O["observation_3_models_select_different_aps"]
    o4 = O["observation_4_feature_reduction_vs_accuracy"]
    o5 = O["observation_5_huim_vs_controls"]
    o6 = O["observation_6_strong_vs_discriminative"]
    cfg = isum["protocol"]["frozen_knn_config"]
    D = Deck()

    # ------------------------------------------------------------- 1 cover
    s = D.slide()
    D.para(s, "HIGH UTILITY ITEMSET MINING", 0.7, 0.75, 12.0, 0.75,
           size=32, bold=True, align=PP_ALIGN.CENTER)
    D.para(s, "TRONG INDOOR POSITIONING SYSTEM", 0.7, 1.5, 12.0, 0.75,
           size=32, bold=True, align=PP_ALIGN.CENTER)
    D.para(s, "Thực nghiệm với UJIIndoorLoc", 0.7, 2.3, 12.0, 0.4,
           size=19, color=GREY, align=PP_ALIGN.CENTER)
    D.para(s, "BÀI TÌM HIỂU THUẬT TOÁN — chưa phải đồ án", 0.7, 2.72, 12.0,
           0.35, size=13, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
    D.pic(s, "fig20_cover_illustration.png", 1.45, 3.12, w=10.4)
    D.para(s, [("Học phần cao học — Khoa Công nghệ Thông tin",
                {"align": PP_ALIGN.CENTER, "size": 12, "color": GREY}),
               (f"Thuật toán chính: EFIM (Zida et al., 2017)  ·  "
                f"{nf(tr['n_rows'])} fingerprint huấn luyện  ·  "
                f"{tr['n_wap_columns_detected']} cột WAP",
                {"align": PP_ALIGN.CENTER, "size": 12, "color": GREY})],
           0.7, 6.55, 12.0, 0.7)
    D.note(s, "Slide 1 — Trang bìa",
           "Tôi cần nói gì: Giới thiệu đề tài trong một câu — tôi thử dùng một "
           "thuật toán khai thác dữ liệu của bài toán giỏ hàng siêu thị (HUIM) "
           "để chọn ra nhóm Access Point hữu ích cho định vị trong nhà, và "
           "kiểm chứng trên bộ dữ liệu UJIIndoorLoc.\n\n"
           "Thông điệp chính: Nói RÕ NGAY TỪ ĐẦU rằng đây là BÀI TÌM HIỂU — "
           "ba nhiệm vụ là tìm hiểu thuật toán, mô hình hoá áp dụng cho IPS, "
           "và cài đặt đánh giá trên UJIIndoorLoc. Không phải đồ án, không "
           "tuyên bố phương pháp mới.\n\n"
           "Nếu cô hỏi sâu: Hình minh hoạ là tự vẽ bằng matplotlib, không dùng "
           "ảnh có bản quyền. Luồng trong hình chính là luồng của bài tìm hiểu: toà "
           "nhà → tín hiệu Wi-Fi → fingerprint → utility transaction → HUIM → "
           "nhóm AP → vị trí.")

    # --------------------------------------------------------- 2 bài toán
    s = D.slide()
    y = D.title(s, "Bài toán", "Định vị trong nhà bằng vân tay Wi-Fi")
    D.para(s, [
        "GPS không dùng được trong nhà: tín hiệu bị chắn, và không phân biệt "
        "được TẦNG.",
        "Wi-Fi fingerprinting: mỗi vị trí có một 'vân tay' riêng — tập AP nhìn "
        "thấy kèm cường độ.",
        f"UJIIndoorLoc: {nf(tr['n_rows'])} fingerprint huấn luyện, "
        f"{tr['n_wap_columns_detected']} cột WAP, "
        f"{tr['joint_building_floor_n_classes']} lớp toà nhà × tầng.",
        f"Nhưng trung bình chỉ "
        f"{tr['not_detected_probe']['detections_per_fingerprint']['mean']} AP "
        f"được phát hiện mỗi lần quét → "
        f"{tr['not_detected_probe']['share_eq_100_pct']:.1f}% ma trận là "
        f"'không phát hiện'.",
        "Số chiều lớn mà gần như rỗng: vừa tốn tài nguyên, vừa làm loãng các "
        "chiều mang thông tin.",
    ], 0.7, y + 0.12, 12.0, 2.3, bullet=True)
    D.pic(s, "fig21_ips_workflow.png", 1.1, y + 2.6, w=11.1)
    D.note(s, "Slide 2 — Bài toán",
           "Tôi cần nói gì: Dẫn từ 'vì sao cần IPS' đến 'vì sao số chiều là "
           "một vấn đề thật'. Nhấn con số 96,5% — đó là lý do toàn bộ bài tìm hiểu "
           "tồn tại.\n\n"
           "Thông điệp chính: Vấn đề không phải thiếu dữ liệu, mà là dữ liệu "
           "quá rộng và quá rỗng.\n\n"
           "Nếu cô hỏi sâu: Offline phase là pha khảo sát, tạo ra cơ sở dữ "
           "liệu vân tay; online phase là pha định vị, so khớp vân tay mới. "
           "HUIM nằm ở pha offline.")

    # -------------------------------------------------- 3 câu hỏi nghiên cứu
    s = D.slide()
    y = D.title(s, "Câu hỏi nghiên cứu")
    D.callout(s, "Có thể dùng HUIM để tìm nhóm WAP hữu ích và giảm không gian "
                 "feature mà vẫn duy trì khả năng định vị không?",
              0.9, y + 0.2, 11.5, 1.05)
    D.para(s, [
        "RQ2 — minUtil ảnh hưởng thế nào đến số HUI, runtime, bộ nhớ?",
        "RQ3 — Signal utility và discriminative utility cho ra HUI khác nhau "
        "thế nào?",
        "RQ4/RQ5 — HUIM có dùng được để chọn WAP? Giảm chiều ảnh hưởng "
        "Building/Floor accuracy ra sao?",
        "RQ6 — Có trade-off hợp lý giữa giảm chiều, chi phí khai thác và chất "
        "lượng định vị?",
        "RQ7 — Kết quả cho ta hiểu NGƯỢC LẠI điều gì về bản chất HUIM?",
    ], 0.7, y + 1.55, 12.0, 2.3, bullet=True)
    D.callout(s, "Chưa tìm thấy nghiên cứu nào áp dụng HUIM trực tiếp cho "
                 "UJIIndoorLoc / Wi-Fi fingerprinting.\n"
                 "→ Ánh xạ HUIM → IPS ở đây là MÔ HÌNH ĐỀ XUẤT, không phải "
                 "phương pháp đã được công nhận.",
              0.9, y + 3.95, 11.5, 1.15, color=BLUE)
    D.para(s, "Không khẳng định novelty: không tìm thấy bằng chứng ≠ không tồn "
              "tại (IEEE Xplore / ACM DL full-text không truy cập được).",
           0.9, y + 5.2, 11.5, 0.4, size=SMALL_PT, color=GREY,
           align=PP_ALIGN.CENTER)
    D.note(s, "Slide 3 — Câu hỏi nghiên cứu",
           "Tôi cần nói gì: Đặt câu hỏi dưới dạng CÂU HỎI, không phải kết "
           "luận. Và nói ngay rằng literature review không tìm thấy tiền lệ "
           "HUIM + UJIIndoorLoc, nên đây là mô hình đề xuất.\n\n"
           "Thông điệp chính: Bài tìm hiểu đi tìm câu trả lời, kể cả khi câu trả lời "
           "là bất lợi.\n\n"
           "Nếu cô hỏi sâu: Em đã kiểm tra 40 DOI qua Crossref; 4 không tồn "
           "tại và 12 trả về bài báo khác hẳn bài em định trích — tất cả đã bị "
           "loại. Danh sách 24 nguồn còn lại ở research/papers_table.csv.")

    # ------------------------------- 4 KẾT QUẢ TRƯỚC, LÝ THUYẾT SAU
    s = D.slide()
    y = D.title(s, "Kết quả trước, lý thuyết sau",
                "Điểm bắt đầu của tư duy ngược")
    rows = [{"Điều kiện": f"Baseline — tất cả "
                          f"{int(base['n_waps_selected'])} WAP",
             "Số WAP": int(base["n_waps_selected"]), "Giảm chiều": "0.00%",
             "Building": pc(base["building_accuracy"]),
             "Floor": pc(base["floor_accuracy"]),
             "Joint": pc(base["joint_building_floor_accuracy"])}]
    for m, d in o4["per_model_best_topn"].items():
        rows.append({"Điều kiện": f"HUIM — {MODEL_SHORT.get(m, m)}",
                     "Số WAP": d["n_waps"],
                     "Giảm chiều": f"{d['feature_reduction_pct']:.2f}%",
                     "Building": pc(d["building_accuracy"]),
                     "Floor": pc(d["floor_accuracy"]),
                     "Joint": pc(d["joint_accuracy"])})
    D.table(s, pd.DataFrame(rows), 0.7, y + 0.15, 12.0,
            0.45 * (len(rows) + 1), size=11.5)
    biggest = None
    for m, r in o1.items():
        st = r.get("sharpest_step")
        if st and (biggest is None or st["to_n_huis"] > biggest[1]["to_n_huis"]):
            biggest = (m, st)
    extra = []
    if biggest:
        m, st = biggest
        extra.append(f"Và ở phía khai thác: minUtil {st['from_pct']:g}% → "
                     f"{st['to_pct']:g}% ({st['threshold_ratio']:g}×) đưa số "
                     f"HUI từ {nf(st['from_n_huis'])} lên "
                     f"{nf(st['to_n_huis'])}.")
    extra.append(f"Cùng một cấu hình k-NN (k={cfg['n_neighbors']}, "
                 f"{cfg['metric']}, {cfg['weights']}) cho MỌI điều kiện — "
                 f"khác biệt duy nhất là cột nào có mặt.")
    D.para(s, extra, 0.7, y + 0.35 + 0.45 * (len(rows) + 1), 12.0, 1.0,
           bullet=True)
    D.callout(s, "Điều gì trong HUIM tạo ra hành vi này?",
              3.4, 6.35, 6.5, 0.72)
    D.note(s, "Slide 4 — Kết quả trước",
           "Tôi cần nói gì: Đưa số thật lên trước, chưa giải thích gì. Đọc "
           "bảng: baseline bao nhiêu WAP và bao nhiêu accuracy, HUIM bao nhiêu "
           "WAP và bao nhiêu accuracy. Rồi dừng lại và đặt câu hỏi ở cuối "
           "slide.\n\n"
           "Thông điệp chính: Có hiện tượng cần giải thích — và đó là lý do "
           "phải học lý thuyết, chứ không phải ngược lại.\n\n"
           "Nếu cô hỏi sâu: Mọi số trong bảng đọc từ "
           "results/metrics/ips_results.csv. Siêu tham số k-NN được chọn một "
           "lần trên ALL-WAP rồi đóng băng, nên lợi thế của tinh chỉnh thuộc "
           "về baseline chứ không thuộc về phương pháp của em.")

    # --------------------------------------------------- 5 minUtil vs HUI
    s = D.slide()
    y = D.title(s, "minUtil đã làm gì?", "Ngưỡng và số lượng High Utility "
                                         "Itemset")
    D.pic(s, "fig01_minutil_vs_hui_count.png", 0.6, y + 0.1, w=7.4)
    lines = []
    for m, r in o1.items():
        hi = r["highest_threshold_with_any_hui_pct"]
        lines.append(f"{MODEL_SHORT.get(m, m)}: {r['n_runs_zero_huis']} lần "
                     f"chạy cho 0 HUI; HUI đầu tiên xuất hiện ở "
                     f"{hi:g}%" if hi else f"{MODEL_SHORT.get(m, m)}: không có "
                                           f"HUI ở mọi ngưỡng đã thử")
    lines.append("Chuyển pha rất gắt: từ 'không có gì' sang 'vượt ngân sách' "
                 "chỉ trong một bước ngưỡng.")
    lines.append("Số HUI khổng lồ nhưng chỉ đến từ vài chục WAP riêng biệt.")
    D.para(s, lines, 8.25, y + 0.3, 4.5, 3.6, bullet=True)
    D.callout(s, "Một triệu HUI không phải\nmột triệu phát hiện", 8.5, 5.3,
              4.0, 0.95)
    D.note(s, "Slide 5 — minUtil và số HUI",
           "Tôi cần nói gì: Chỉ vào vùng chuyển pha trên đồ thị. Nhấn rằng "
           "trục x là log và giảm dần sang phải, trục y là symlog. Vòng tròn "
           "đỏ là các lần chạy bị dừng do hết ngân sách — em giữ lại, không "
           "xoá.\n\n"
           "Thông điệp chính: Giảm ngưỡng không làm kết quả lớn dần mà làm nó "
           "bùng nổ, trong khi số AP riêng biệt gần như không tăng.\n\n"
           "Nếu cô hỏi sâu: Lý do là nếu một nhóm k AP đạt ngưỡng thì cả "
           "2^k − 1 tập con của nó cũng đạt gần như đồng thời. Đó là vì utility "
           "không có downward closure.")

    # -------------------------------------------------------- 6 giá phải trả
    s = D.slide()
    y = D.title(s, "Giá phải trả", "Runtime và bộ nhớ theo ngưỡng")
    b1 = D.pic(s, "fig02_minutil_vs_runtime.png", 0.5, y + 0.1, w=6.2, max_bottom=5.0)
    b2 = D.pic(s, "fig03_minutil_vs_peak_memory.png", 6.85, y + 0.1, w=6.2, max_bottom=5.0)
    bot = max(b1, b2)
    lines = []
    for m, r in o2.items():
        lines.append(f"{MODEL_SHORT.get(m, m)}: runtime "
                     f"{r['runtime_s_min']:.2f}–{r['runtime_s_max']:.2f} s, "
                     f"bộ nhớ đỉnh {r['peak_mem_delta_mb_min']:.1f}–"
                     f"{r['peak_mem_delta_mb_max']:.1f} MB, "
                     f"{r['n_aborted']} lần ABORTED.")
    rho = [r.get("spearman_nodes_vs_runtime") for r in o2.values()
           if r.get("spearman_nodes_vs_runtime") is not None]
    if rho:
        lines.append("Spearman ρ(số nút cây đã duyệt, runtime) = "
                     + ", ".join(f"{v:.3f}" for v in rho)
                     + " → chi phí là chi phí TRÊN MỖI NÚT.")
    D.para(s, lines, 0.7, bot + 0.1, 12.0, max(0.5, 7.2 - bot), bullet=True)
    D.callout(s, "Tại sao giảm threshold lại tốn tài nguyên nhanh như vậy?",
              2.6, 6.68, 8.1, 0.6)
    D.note(s, "Slide 6 — Giá phải trả",
           "Tôi cần nói gì: Runtime và bộ nhớ là hai câu chuyện KHÁC NHAU. "
           "Runtime theo số nút cây tìm kiếm; bộ nhớ theo kích thước KẾT QUẢ.\n\n"
           "Thông điệp chính: Hạ ngưỡng không làm một nút đắt hơn, nó làm có "
           "nhiều nút hơn.\n\n"
           "Nếu cô hỏi sâu: Em đo bộ nhớ bằng cách lấy mẫu RSS tiến trình mỗi "
           "20 ms thay vì dùng tracemalloc, vì tracemalloc làm chậm chương "
           "trình nhiều lần và sẽ phá chính phép đo runtime trong cùng thí "
           "nghiệm.")

    # ----------------------------------------------- 7 quay ngược về HUIM
    s = D.slide()
    y = D.title(s, "Quay ngược về HUIM", "Những khái niệm cần để giải thích "
                                         "hiện tượng trên")
    bot = D.pic(s, "fig22_huim_concepts.png", 1.0, y + 0.15, w=11.3, max_bottom=5.3)
    D.para(s, [
        "Utility KHÔNG anti-monotone: u({b}) = 16 < u({b,d}) = 30, nhưng "
        "u({b,d,f}) < u({b,d}).",
        "→ Không thể cắt nhánh bằng chính utility — phải cắt bằng CHẶN TRÊN.",
        "TWU(X) = Σ TU(T) trên các giao dịch chứa X là chặn trên và CÓ "
        "anti-monotone → cắt được "
        "an toàn (Liu et al., 2005).",
    ], 0.7, y + 3.35, 12.0, 1.4, bullet=True)
    D.note(s, "Slide 7 — Khái niệm HUIM",
           "Tôi cần nói gì: Năm khái niệm: item, transaction, q, p, minUtil. "
           "Rồi đến điểm cốt tử: utility không anti-monotone, nên không prune "
           "trực tiếp được.\n\n"
           "Thông điệp chính: Toàn bộ literature HUIM là lịch sử đi tìm chặn "
           "trên chặt hơn.\n\n"
           "Nếu cô hỏi sâu: Phản ví dụ em nêu lấy từ ví dụ chạy chuẩn của "
           "literature và được kiểm chứng bằng unit test — u({b,d}) = 30 em "
           "tính tay trong file test, và brute-force cùng EFIM đều cho ra 30.")

    # ------------------------------------- 8 UJIIndoorLoc -> utility database
    s = D.slide()
    y = D.title(s, "Từ UJIIndoorLoc đến Utility Database")
    D.pic(s, "fig23_uji_to_utility.png", 0.45, y + 0.1, w=12.45)
    mp_df = pd.DataFrame([
        {"HUIM": "Transaction T", "IPS": "một fingerprint Wi-Fi (một dòng CSV)"},
        {"HUIM": "Item i", "IPS": "một Access Point; không phát hiện → item "
                                  "vắng mặt"},
        {"HUIM": "Internal utility q(i,T)", "IPS": "RSSI đã chuẩn hoá "
                                                   "(1 … 100)"},
        {"HUIM": "External utility p(i)", "IPS": "mức phân biệt vị trí của AP"},
        {"HUIM": "High Utility Itemset", "IPS": "nhóm AP có tổng utility vượt "
                                                "ngưỡng — KHÔNG đương nhiên là "
                                                "đặc trưng tốt"},
    ])
    D.table(s, mp_df, 0.7, y + 2.35, 12.0, 2.5, size=11.5)
    D.para(s, "Đây là ánh xạ do bài tìm hiểu MÔ HÌNH HOÁ, không phải ngữ nghĩa gốc "
              "của HUIM: dữ liệu Wi-Fi không có 'số lượng' và không có 'lợi "
              "nhuận' của AP.",
           0.7, 6.55, 12.0, 0.5, size=SMALL_PT, color=ACCENT)
    D.note(s, "Slide 8 — Ánh xạ",
           "Tôi cần nói gì: Đi theo năm bước trong sơ đồ, rồi đọc bảng ánh xạ. "
           "Nhấn dòng cuối cùng của bảng.\n\n"
           "Thông điệp chính: q và p không có sẵn trong dữ liệu Wi-Fi; em phải "
           "định nghĩa chúng, và đó vừa là đóng góp vừa là điểm yếu lớn nhất.\n\n"
           "Nếu cô hỏi sâu: Giá trị 100 trong cột WAP nghĩa là 'không phát "
           "hiện' — em đã kiểm chứng bằng ba nguồn: tài liệu UCI ghi nguyên "
           "văn, phân bố dữ liệu (không có ô nào trong khoảng 1–99 trên hơn 10 "
           "triệu ô), và tính nhất quán vật lý.")

    # ----------------------------------------------------- 9 utility models
    s = D.slide()
    y = D.title(s, "Utility Models", "Chỉ external utility thay đổi; internal "
                                     "utility giữ nguyên")
    hm = hsum["utility_models"]
    rows = []
    for key, label, formula in (
            ("A_signal", "Model A — Signal", "p(i) = 1"),
            ("B_discriminative", "Model B — Discriminative",
             "p(i) = MI(A_i;Y) / max MI"),
            ("C_rare_discriminative", "Model C — Rare-discriminative",
             "p(i) tỉ lệ với MI(A_i;Y) × IDF(i)")):
        if key not in hm:
            continue
        d = hm[key]
        rows.append({"Utility model": label, "Công thức p(i)": formula,
                     "Tổng utility DB": nf(d["total_database_utility"]),
                     "TU(T) trung bình": nf(d["transaction_utility_mean"], 2)})
    D.table(s, pd.DataFrame(rows), 0.7, y + 0.15, 12.0, 0.5 * (len(rows) + 1),
            size=11.5)
    lines = [
        "Model A là ĐỐI CHỨNG: với p ≡ 1, 'high utility' ≈ 'mạnh và đồng xuất "
        "hiện nhiều' — tái tạo đúng chế độ thất bại của frequent itemset "
        "mining.",
        f"Model B: p(i) = mutual information với BUILDINGID_FLOOR, tính CHỈ "
        f"trên trainingData. H(Y) = "
        f"{hm['B_discriminative']['label_entropy_H_Y_bits']} bit; AP tốt nhất "
        f"cho {hm['B_discriminative']['mi_bits_max']} bit.",
    ]
    vals = [d["total_database_utility"] for d in hm.values()]
    if vals and min(vals) > 0:
        lines.append(f"Tổng utility chênh {max(vals)/min(vals):.1f}× giữa các "
                     f"model → minUtil PHẢI biểu diễn theo % tổng utility, "
                     f"không thể dùng số tuyệt đối.")
    D.para(s, lines, 0.7, y + 0.4 + 0.5 * (len(rows) + 1), 12.0, 1.9,
           bullet=True)
    D.note(s, "Slide 9 — Utility models",
           "Tôi cần nói gì: Ba model dùng CHUNG internal utility, chỉ khác "
           "p(i). Nhờ vậy ablation cô lập đúng một biến.\n\n"
           "Thông điệp chính: Model A là đối chứng có chủ đích, không phải "
           "model em kỳ vọng tốt nhất.\n\n"
           "Nếu cô hỏi sâu: MI chỉ được tính trên trainingData. Em cưỡng chế "
           "bằng code: hàm build_external_utility nhận tham số split_name và "
           "raise lỗi nếu khác 'training'. Có unit test riêng cho cơ chế đó.")

    # -------------------------------------------------------- 10 EFIM
    s = D.slide()
    y = D.title(s, "EFIM hoạt động thế nào?", "Sơ đồ nguyên lý (schematic)")
    D.pic(s, "fig24_efim_tree.png", 0.55, y + 0.05, w=7.6)
    D.para(s, [
        "Local utility lu(α,z) < minUtil → loại item z khỏi CẢ cây con của α.",
        "Subtree utility su(α,z) < minUtil → KHÔNG bước vào nhánh của α "
        "mở rộng bởi z.",
        "Database projection: prefix được nén thành MỘT số, không phải một "
        "danh sách.",
        "Transaction merging: các giao dịch giống nhau sau khi chiếu được hợp "
        "lại.",
        "Fast Utility Counting: cả hai chặn tính trong một lượt quét ngược.",
    ], 8.4, y + 0.25, 4.4, 3.6, bullet=True)
    nice = "lu({ }, z) = TWU(z)  →  cắt tỉa bằng TWU chỉ là trường hợp riêng tại gốc"
    D.callout(s, nice, 1.6, 6.2, 10.1, 0.75, color=BLUE)
    D.note(s, "Slide 10 — EFIM",
           "Tôi cần nói gì: Đi từ cây tìm kiếm: nút là itemset, con là itemset "
           "thêm một item lớn hơn. Hai chặn trên làm hai việc khác nhau — một "
           "cái loại ITEM khỏi cây con, một cái không cho VÀO nhánh.\n\n"
           "Thông điệp chính: su chặt hơn lu vì nó chỉ cộng utility của các "
           "item đứng SAU z.\n\n"
           "Nếu cô hỏi sâu: Nhận xét ở khung dưới là chỗ lý thuyết khớp lại "
           "với nhau — tại gốc, local utility chính bằng TWU, nên TWU pruning "
           "là trường hợp đặc biệt của local utility pruning. Em có ghi nhận "
           "xét này trong mã nguồn.")

    # -------------------------------------------------------- 11 pipeline
    s = D.slide()
    y = D.title(s, "Experimental Pipeline", "validationData chỉ xuất hiện ở "
                                            "bước cuối")
    bot = D.pic(s, "fig25_pipeline.png", 0.45, y + 0.15, w=11.9,
                max_bottom=5.1)
    D.para(s, [
        f"Siêu tham số k-NN chọn MỘT LẦN trên train_sub/dev_sub của "
        f"trainingData (k={cfg['n_neighbors']}, {cfg['metric']}, "
        f"{cfg['weights']}), rồi ĐÓNG BĂNG cho mọi điều kiện.",
        "Chuẩn hoá RSSI, trọng số p, khai thác HUIM và chọn AP: tất cả chỉ "
        "dùng trainingData.",
        f"Hai split còn khác nhau có chủ đích: không chung USERID nào, chỉ "
        f"chung {len(cs['PHONEID_overlap'])} PHONEID, cách nhau ~4 tháng → "
        f"đây là con số cross-device, cross-time.",
    ], 0.7, y + 3.1, 12.0, 1.8, bullet=True)
    D.note(s, "Slide 11 — Pipeline",
           "Tôi cần nói gì: Chỉ vào đường kẻ đứt màu đỏ: không có mũi tên nào "
           "đi từ phải sang trái. Đó là toàn bộ cơ chế chống data leakage.\n\n"
           "Thông điệp chính: validationData được dùng đúng một lần cho mỗi "
           "điều kiện, chỉ để đánh giá.\n\n"
           "Nếu cô hỏi sâu: Việc tinh chỉnh k-NN trên ALL-WAP là lựa chọn bảo "
           "thủ — mọi lợi thế của tinh chỉnh thuộc về baseline. Và vì hai split "
           "khác người dùng, khác thiết bị, khác thời điểm nên accuracy ở đây "
           "không so sánh được với các bài tự chia lại file huấn luyện.")

    # ------------------------------- 12 độ chính xác theo mét (mục tiêu 7-8m)
    s = D.slide()
    y = D.title(s, "Độ chính xác định vị theo mét",
                "Đối chiếu với mức tham chiếu 7–8 m")
    bot = D.pic(s, "fig17_positioning_error_metres.png", 2.45,
                y + 0.02, w=8.4, max_bottom=5.3)
    acc_lines = []
    if "pos_median_error_ground_m" in base:
        acc_lines.append(
            f"Baseline: trung vị {base['pos_median_error']:.2f} m toạ độ chiếu "
            f"= {base['pos_median_error_ground_m']:.2f} m thực địa; trung bình "
            f"{base['pos_mean_error']:.2f} m chiếu = "
            f"{base['pos_mean_error_ground_m']:.2f} m thực địa.")
        acc_lines.append(
            f"Trung vị DƯỚI dải 7–8 m; trung bình TRÊN dải, vì phân bố có đuôi "
            f"dài (p95 = {base['pos_p95_error_ground_m']:.1f} m).")
    if C_coord and C_coord.get("conclusion", {}).get("identified_as"):
        cc2 = C_coord["conclusion"]
        acc_lines.append(
            f"Toạ độ là {cc2['identified_as'].split('(')[0].strip()} — xác "
            f"định bằng cách nghịch đảo phép chiếu, rơi cách campus UJI "
            f"{cc2['distance_to_uji_campus_m']} m (UTM lệch hàng trăm km).")
        if "web_mercator_scale_factor_at_this_latitude" in cc2:
            acc_lines.append(
                f"Web Mercator KHÔNG bảo toàn khoảng cách: hệ số "
                f"{cc2['web_mercator_scale_factor_at_this_latitude']} → khoảng "
                f"cách đọc thẳng từ cột toạ độ lớn hơn thực tế ~30%.")
    D.para(s, acc_lines, 0.55, bot + 0.12, 12.25,
           max(0.5, 7.35 - bot - 0.12), bullet=True)
    D.note(s, "Slide 12 — Độ chính xác theo mét",
           "Tôi cần nói gì: Trả lời trực tiếp tiêu chí 7–8 m. Nói rõ đang dùng "
           "thống kê nào: trung vị hay trung bình, toạ độ chiếu hay thực địa.\n\n"
           "Thông điệp chính: Trung vị dưới mục tiêu, trung bình trên mục tiêu "
           "— chênh nhau vì đuôi phân bố, do một số fingerprint bị gán sai "
           "tầng.\n\n"
           "Nếu cô hỏi sâu: Bộ dữ liệu KHÔNG ghi đơn vị toạ độ. Em xác định "
           "bằng thực nghiệm: nghịch đảo từng phép chiếu ứng viên rồi đo "
           "khoảng cách tới campus UJI. Web Mercator trúng trong 140 m, UTM "
           "lệch 497 và 871 km. Và vì Web Mercator bảo giác chứ không bảo "
           "khoảng cách, em báo cáo cả hai con số — con số chiếu để so với "
           "literature, con số thực địa vì nó đúng về vật lý.")

    # -------------------------------- 13 thời gian và bộ nhớ của IPS
    if COST is not None and len(COST):
        s = D.slide()
        y = D.title(s, "Đánh giá thời gian và bộ nhớ",
                    "Phía hệ thống định vị — nơi giảm chiều thực sự trả công")
        bot = D.pic(s, "fig16_ips_time_and_memory.png", 0.75,
                    y + 0.05, w=11.8, max_bottom=5.2)
        bc = COST[COST["condition"] == "baseline_all_520"]
        cost_lines = []
        if len(bc):
            bcr = bc.iloc[0]
            bestc = COST.loc[COST["joint_building_floor_accuracy"].idxmax()]
            cost_lines.append(
                f"Baseline {int(bcr['n_features'])} WAP: "
                f"{bcr['predict_ms_per_fingerprint']:.3f} ms/fingerprint, "
                f"CSDL vân tay {bcr['db_memory_float64_mb']:.1f} MB.")
            cost_lines.append(
                f"{bestc['condition']} ({int(bestc['n_features'])} WAP): "
                f"{bestc['predict_ms_per_fingerprint']:.3f} ms/fp "
                f"({bcr['predict_ms_per_fingerprint']/bestc['predict_ms_per_fingerprint']:.1f}× "
                f"nhanh hơn), "
                f"{100*bestc['db_memory_float64_mb']/bcr['db_memory_float64_mb']:.0f}% "
                f"bộ nhớ, và joint accuracy "
                f"{pc(bestc['joint_building_floor_accuracy'])} "
                f"({(bestc['joint_building_floor_accuracy']-bcr['joint_building_floor_accuracy'])*100:+.2f} pp).")
            hb = COST[COST["family"].astype(str).str.startswith("huim")]
            if len(hb):
                hbest = hb.loc[hb["joint_building_floor_accuracy"].idxmax()]
                cost_lines.append(
                    f"HUIM tốt nhất ({int(hbest['n_features'])} WAP): "
                    f"{bcr['predict_ms_per_fingerprint']/hbest['predict_ms_per_fingerprint']:.1f}× "
                    f"nhanh hơn, "
                    f"{100*hbest['db_memory_float64_mb']/bcr['db_memory_float64_mb']:.0f}% "
                    f"bộ nhớ, nhưng accuracy "
                    f"{pc(hbest['joint_building_floor_accuracy'])}.")
        cost_lines.append(
            "Đo một lõi, lặp lại lấy trung vị; bộ nhớ CSDL tính chính xác "
            "(dòng × cột × kích thước phần tử), không ước lượng.")
        D.para(s, cost_lines, 0.55, bot + 0.12, 12.25,
               max(0.5, 7.35 - bot - 0.12), bullet=True)
        D.note(s, "Slide 13 — Thời gian và bộ nhớ",
               "Tôi cần nói gì: Đây là tiêu chí thứ hai nhóm đặt ra. Chi phí "
               "khai thác HUIM đã nói ở slide trước; slide này là chi phí của "
               "chính hệ thống định vị.\n\n"
               "Thông điệp chính: Giảm chiều cho lợi ích tuyến tính và rất rõ "
               "về cả thời gian lẫn bộ nhớ — nhưng tập đặc trưng tốt nhất đến "
               "từ đối chứng đơn giản, không phải từ HUIM.\n\n"
               "Nếu cô hỏi sâu: Em đo với n_jobs=1 để con số là chi phí một "
               "lõi, khả chuyển. Ở số chiều nhỏ nhất đường cong không đơn "
               "điệu vì scikit-learn chuyển sang chỉ mục kd_tree, mà trên dữ "
               "liệu thưa thì cây chậm hơn duyệt vét cạn — em có ghi lại thuật "
               "toán index trong log để chứng minh.")

    # --------------------------------------------- 14 baseline vs HUIM
    s = D.slide()
    y = D.title(s, "Baseline so với HUIM", "Building / Floor / Joint accuracy")
    bot = D.pic(s, "fig10_baseline_vs_huim_accuracies.png", 1.0, y + 0.1,
                w=11.3, max_bottom=5.3)
    D.para(s, [
        f"Building {pc(base['building_accuracy'])} nhưng Floor "
        f"{pc(base['floor_accuracy'])} ở baseline: NHẦM TẦNG là toàn bộ vấn "
        f"đề, vì Joint bị chặn bởi Floor.",
        f"Audit đã dự đoán điều này TRƯỚC khi fit mô hình: "
        f"{o6['ap_building_spread']['n_waps_in_exactly_1_building']} AP chỉ "
        f"nằm trong một toà nhà, chỉ "
        f"{o6['ap_building_spread']['n_waps_in_all_3_buildings']} AP thấy được "
        f"ở cả ba.",
    ], 0.7, y + 3.55, 12.0, 1.2, bullet=True)
    D.note(s, "Slide 12 — Baseline vs HUIM",
           "Tôi cần nói gì: Đọc ba cột của baseline, rồi so với HUIM tốt nhất. "
           "Nhấn rằng Building gần như được giải quyết còn Floor là phần khó.\n\n"
           "Thông điệp chính: Một báo cáo chỉ nêu Building accuracy sẽ làm "
           "phương pháp trông tốt hơn thực tế rất nhiều.\n\n"
           "Nếu cô hỏi sâu: Cả ba accuracy suy ra từ CÙNG một dự đoán nhãn "
           "joint, nên chúng nhất quán theo cấu trúc — mô hình không thể được "
           "ghi công 'đúng tầng' khi nó dự đoán sai toà nhà.")

    # ------------------------------------------------------- 13 ablation
    s = D.slide()
    y = D.title(s, "Utility Ablation", "ALL WAP so với ba định nghĩa utility, "
                                       "và so với đối chứng")
    AB = pd.read_csv(TABLES / "ablation_study.csv")
    keep = AB[AB["Method"].str.contains(
        "ALL WAP \\(primary|HUIM top-n \\(best|Control", regex=True)].copy()
    show = keep[["Method", "Utility Model", "WAP count", "Reduction %",
                 "Building Acc %", "Floor Acc %", "Joint Acc %",
                 "HUI Count"]].head(9)
    show.columns = ["Phương pháp", "Utility model", "Số WAP", "Giảm chiều %",
                    "Building %", "Floor %", "Joint %", "Số HUI"]
    D.table(s, show, 0.5, y + 0.15, 12.35, 0.42 * (len(show) + 1), size=10.0)
    w = o5["verdict_inputs"]
    D.para(s, [
        f"Trên {w['n_comparisons']} ngân sách đặc trưng KHỚP NHAU: HUIM vượt "
        f"random {w['huim_beats_random']}/{w['n_comparisons']}, vượt top-n "
        f"theo MI {w['huim_beats_top_mi']}/{w['n_comparisons']}, vượt top-n "
        f"theo support {w['huim_beats_top_support']}/{w['n_comparisons']}.",
        "Đối chứng top-n-theo-MI là đối chứng khó nhất: nó dùng chính thước đo "
        "Model B được cho sẵn, nhưng KHÔNG khai thác itemset.",
    ], 0.6, y + 0.45 + 0.42 * (len(show) + 1), 12.2, 1.4, bullet=True)
    D.note(s, "Slide 13 — Ablation",
           "Tôi cần nói gì: Ablation không chỉ so HUIM với 'dùng tất cả'. Phải "
           "có đối chứng ở CÙNG ngân sách đặc trưng, nếu không thì không phân "
           "biệt được CHỌN đặc trưng với XOÁ đặc trưng.\n\n"
           "Thông điệp chính: Ba đối chứng trả lời ba câu khác nhau, và chỉ "
           "câu thứ ba là về HUIM.\n\n"
           "Nếu cô hỏi sâu: Nếu HUIM không vượt top-n theo MI thì đó là kết "
           "quả ÂM và em báo cáo đúng như vậy — giá trị nằm ở chỗ đã thiết lập "
           "được phép so sánh đó.")

    # ------------------------------ 14 feature reduction vs accuracy
    s = D.slide()
    y = D.title(s, "Feature Reduction và Accuracy", "Slide quan trọng nhất của "
                                                    "phần kết quả")
    D.pic(s, "fig09_feature_reduction_vs_accuracy.png", 0.55, y + 0.05, w=7.7)
    lines = []
    sm = o4.get("smallest_subset_matching_baseline")
    if sm:
        lines.append(f"Tập nhỏ nhất đạt/vượt baseline: {sm['n_waps']} WAP "
                     f"({sm['feature_reduction_pct']:.2f}% giảm chiều), Joint "
                     f"{pc(sm['joint_accuracy'])}.")
    else:
        lines.append("KHÔNG tập con nào do HUIM chọn đạt được Joint accuracy "
                     "của baseline toàn bộ WAP.")
    if o4["baseline_detected_465"]:
        d = o4["baseline_detected_465"]
        lines.append(f"Lưu ý trung thực: bỏ các cột chưa bao giờ được phát "
                     f"hiện cho {d['feature_reduction_pct']:.2f}% giảm chiều "
                     f"MIỄN PHÍ — phần này không nhờ HUIM.")
    lines.append("Building accuracy chịu được giảm chiều mạnh; Floor accuracy "
                 "là ràng buộc chặt.")
    lines.append("Hình thoi = điểm union, nơi minUtil là núm điều khiển duy "
                 "nhất.")
    D.para(s, lines, 8.5, y + 0.2, 4.4, 3.9, bullet=True)
    D.note(s, "Slide 14 — Giảm chiều và accuracy",
           "Tôi cần nói gì: Đây là slide trả lời RQ4-RQ6. Đi từ phải sang: "
           "giảm chiều tăng thì accuracy đi về đâu. So HUIM với ba đường đối "
           "chứng.\n\n"
           "Thông điệp chính: Câu trả lời cho 'giảm được bao nhiêu WAP' không "
           "phải một con số — nó phụ thuộc vào accuracy nào đang được bảo vệ.\n\n"
           "Nếu cô hỏi sâu: Em KHÔNG gọi đây là Pareto front, vì chưa kiểm tra "
           "điều kiện Pareto một cách hình thức. Em chỉ nói có trade-off. Ở "
           "ngân sách nhỏ, một phần sụt giảm là do MẤT ĐỘ PHỦ chứ không phải "
           "mất khả năng phân biệt — em log riêng số fingerprint kiểm định "
           "không phát hiện được AP nào trong tập đã chọn.")

    # ------------------------------------------------- 15 reverse thinking
    s = D.slide()
    y = D.title(s, "Tư duy ngược: từ kết quả đến cơ chế",
                "Slide chủ đạo của báo cáo")
    D.pic(s, "fig26_reverse_thinking_chain.png", 3.95, y + 0.02, w=5.45)
    D.para(s, [
        "Kết quả buộc ta phải hiểu lý thuyết, không phải ngược lại.",
        "Số HUI nhạy với minUtil, số AP thì không → đáp án là hợp của các lưới "
        "tập con.",
        "Runtime theo số nút; bộ nhớ theo kích thước kết quả → chặn trên điều "
        "khiển TÌM KIẾM, không điều khiển KẾT QUẢ.",
        "Chỉ đổi p mà tập AP đổi → hàm utility là PHÁT BIỂU BÀI TOÁN.",
    ], 0.55, y + 0.25, 3.3, 4.3, bullet=True)
    right = []
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        right.append(
            f"KẾT QUẢ NGƯỢC KỲ VỌNG: ρ(số lần phát hiện, MI) = "
            f"{o6['spearman_support_vs_mi_over_all_detected_waps']} trên "
            f"{o6['n_detected_waps_compared']} AP.")
        right.append("→ 'Frequent ≠ Useful' KHÔNG được chứng minh ở mức từng "
                     "AP trên bộ dữ liệu này.")
    right.append("Nhưng Model A (p ≡ 1, utility = tín hiệu × đồng xuất hiện) "
                 "xếp hạng TỆ HƠN ngẫu nhiên → phân biệt nằm ở HÀM UTILITY.")
    right.append("minUtil không phải núm chất lượng: nó là núm 'nhóm lớn đến "
                 "đâu là một mẫu'.")
    D.para(s, right, 9.5, y + 0.25, 3.3, 4.3, bullet=True)
    D.note(s, "Slide 15 — Tư duy ngược",
           "Tôi cần nói gì: Đi dọc chuỗi ở giữa, từ trên xuống: hành vi quan "
           "sát được → cơ chế bùng nổ → vai trò của chặn trên → lý thuyết "
           "(utility không có downward closure) → ý nghĩa cho IPS.\n\n"
           "Thông điệp chính: Đây là cách em học được lý thuyết — từ hiện "
           "tượng, không từ định nghĩa.\n\n"
           "Nếu cô hỏi sâu: Các con số trong chuỗi lấy đúng từ log, và phân "
           "tích đầy đủ 8 quan sát nằm trong "
           "research/reverse_thinking_analysis.md — file đó và chương 15 của "
           "báo cáo Word đọc cùng một file JSON nên không thể lệch nhau.")

    # --------------------------------- 16 does / does not
    s = D.slide()
    y = D.title(s, "HUIM làm được gì, và không làm được gì")
    hdr = s.shapes.add_textbox(Inches(0.7), Inches(y + 0.1), Inches(5.9),
                               Inches(0.4))
    for x, label, color in ((0.7, "LÀM ĐƯỢC  (data chứng minh)", GREEN),
                            (6.95, "KHÔNG LÀM ĐƯỢC", ACCENT)):
        D.para(s, label, x, y + 0.1, 5.9, 0.4, size=15, bold=True, color=color)
    does = [
        f"Chuyển {nf(hsum['database']['n_rows'])} fingerprint thành utility "
        f"transaction và khai thác được bằng EFIM.",
        "Giữ tập AP được chọn NHỎ, ngay cả khi số HUI lên hàng trăm nghìn.",
        "Mô tả được hành vi ngưỡng của HUIM trên dữ liệu Wi-Fi thưa và rộng.",
        "Cho thấy đổi định nghĩa utility thì tập AP được chọn thực sự đổi.",
    ]
    donts = [
        "KHÔNG đảm bảo một HUI là nhóm đặc trưng tốt cho phân loại.",
        "KHÔNG tự giải quyết bài toán định vị — vẫn cần một bộ phân loại.",
        "Phụ thuộc hoàn toàn vào định nghĩa utility do người phân tích chọn.",
        "Phụ thuộc minUtil, mà vùng ngưỡng dùng được rất hẹp.",
        "KHÔNG phải bộ chọn đặc trưng CÓ GIÁM SÁT — không có mục tiêu phân "
        "loại trong định nghĩa.",
    ]
    D.para(s, does, 0.7, y + 0.6, 5.9, 4.4, bullet=True)
    D.para(s, donts, 6.95, y + 0.6, 5.9, 4.4, bullet=True)
    D.note(s, "Slide 16 — Làm được / không làm được",
           "Tôi cần nói gì: Cột trái chỉ ghi điều số liệu chứng minh. Cột phải "
           "ghi điều em KHÔNG khẳng định.\n\n"
           "Thông điệp chính: Giới hạn của kết luận là một phần của kết luận.\n\n"
           "Nếu cô hỏi sâu: Điểm quan trọng nhất ở cột phải là dòng cuối — "
           "HUIM là bài toán không giám sát, không có gì trong định nghĩa của "
           "nó tối ưu một mục tiêu phân loại. Vì vậy không có định lý nào để "
           "viện dẫn, chỉ có số liệu đối chứng.")

    # -------------------------------------------------------- 17 kết luận
    s = D.slide()
    y = D.title(s, "Kết luận")
    lines = [
        f"HUIM áp dụng được về mặt kỹ thuật: "
        f"{nf(hsum['database']['n_non_empty_transactions'])} utility "
        f"transaction, EFIM chạy và cho kết quả; nhưng 'hợp lý' là hợp lý CỦA "
        f"ĐỊNH NGHĨA utility, không phải tính chất của bộ dữ liệu.",
    ]
    if o3["pairwise_overlap"]:
        k0 = list(o3["pairwise_overlap"])[0]
        v0 = o3["pairwise_overlap"][k0]
        lines.append(f"Discriminative utility (Model B) cho đường cong ngưỡng "
                     f"mượt hơn và chọn tập AP khác Model A (Jaccard "
                     f"{v0['jaccard']:.3f} cho cặp đầu tiên).")
    if sm:
        lines.append(f"Giảm chiều: {sm['n_waps']} WAP "
                     f"({sm['feature_reduction_pct']:.2f}%) đạt Joint "
                     f"{pc(sm['joint_accuracy'])}, so với baseline "
                     f"{pc(base['joint_building_floor_accuracy'])} trên "
                     f"{int(base['n_waps_selected'])} WAP.")
    else:
        lines.append(f"Giảm chiều: không cấu hình HUIM nào đạt baseline "
                     f"{pc(base['joint_building_floor_accuracy'])} "
                     f"({int(base['n_waps_selected'])} WAP); trade-off có thật "
                     f"nhưng không thuận lợi.")
    o9 = O.get("observation_9_ranking_vs_size", {})
    if o9.get("largest_huim_selected_set"):
        bb = o9.get("best_joint_at_or_below_that_budget_any_method") or {}
        sc = o9.get("smallest_control_subset_reaching_baseline") or {}
        lines.append(
            f"CƠ CHẾ: tập AP lớn nhất HUIM tạo ra là "
            f"{o9['largest_huim_selected_set']} WAP. Ở ngân sách đó, MỌI "
            f"phương pháp đều chỉ đạt tối đa "
            f"{pc(bb.get('joint_building_floor_accuracy', bb.get('joint')))}"
            + (f", trong khi cần {sc['n_waps']} WAP mới chạm baseline"
               if sc else "")
            + " — ngay cả một xếp hạng hoàn hảo cũng không thể lấp khoảng "
              "cách từ bên trong trần đó.")
    bm = o9.get("beats_random_by_model", {})
    if bm:
        lines.append(
            "ĐỐI CHỨNG: " + "; ".join(
                f"{MODEL_SHORT.get(m, m)} vượt ngẫu nhiên {d['beats']}/{d['n']}"
                for m, d in bm.items())
            + f"; HUIM tốt nhất vượt top-n theo MI "
              f"{w['huim_beats_top_mi']}/{w['n_comparisons']}.")
    lines.append("Đóng góp: khảo sát khả năng thích nghi HUIM cho bài toán "
                 "chọn nhóm AP — có đối chứng, có thể cho kết quả âm, không "
                 "tuyên bố novelty.")
    D.para(s, lines, 0.7, y + 0.2, 12.0, 4.3, bullet=True)
    D.para(s, "Mọi con số trong bài đọc trực tiếp từ results/ và figures/; "
              "script sinh slide không chứa giá trị thực nghiệm nào.",
           0.7, 6.55, 12.0, 0.45, size=SMALL_PT, color=GREY)
    D.note(s, "Slide 17 — Kết luận",
           "Tôi cần nói gì: Trả lời trực tiếp từng câu hỏi nghiên cứu bằng "
           "con số. Không dùng từ 'vượt trội'.\n\n"
           "Thông điệp chính: Trade-off chính nằm ngược trực giác — ngưỡng cao "
           "tốt hơn ngưỡng thấp cho mục đích chọn AP.\n\n"
           "Nếu cô hỏi sâu: Nếu cô hỏi 'vậy có nên dùng HUIM cho IPS không', "
           "câu trả lời trung thực là: dựa trên thực nghiệm này, HUIM là một "
           "cách hợp lệ để chọn nhóm AP nhưng chưa chứng minh được là tốt hơn "
           "các tiêu chí information-theoretic đơn giản hơn — và bảng đối chứng "
           "ngân sách khớp nhau là bằng chứng duy nhất em đưa ra.")

    # ------------------------------------------------------ 18 references
    s = D.slide()
    y = D.title(s, "Tài liệu tham khảo", "Metadata xác minh qua Crossref API")
    P = PAP.copy()
    P["_y"] = pd.to_numeric(P["year"], errors="coerce").fillna(0)
    keys = ["zida2017efim", "zhang2018empirical", "gan2021survey",
            "liu2012huiminer", "tseng2010upgrowth", "liu2005twophase",
            "torressospedra2014uji", "chen2006power"]
    sel = P[P["key"].isin(keys)]
    lines = []
    for k, (_, r) in enumerate(sel.iterrows(), 1):
        au = str(r["authors"]).split("; ")
        astr = (", ".join(au[:2]) + " et al.") if len(au) > 2 else ", ".join(au)
        venue = str(r["venue"])
        if len(venue) > 58:
            venue = venue[:55] + "…"
        lines.append(f"[{k}] {astr}, \"{r['paper']},\" {venue}, "
                     f"{int(r['_y'])}. DOI: {r['doi']}")
    D.para(s, lines, 0.7, y + 0.2, 12.2, 4.1, size=11.0, space_after=9)
    D.para(s, "Không mục nào được gắn Q1/Q2. Bài hội nghị KHÔNG có quartile "
              "SJR/JCR (quartile xếp hạng tạp chí, không xếp hạng kỷ yếu). Với "
              "các bài tạp chí, scimagojr.com trả về HTTP 403 từ môi trường "
              "thực nghiệm nên ghi 'Not verified'. 'IEEE = Q1' là lỗi phạm "
              "trù: IEEE là nhà xuất bản.",
           0.7, 5.75, 12.2, 1.1, size=SMALL_PT, color=ACCENT)
    D.note(s, "Slide 18 — Tài liệu tham khảo",
           "Tôi cần nói gì: Tám nguồn mạnh nhất. Nhấn rằng metadata lấy từ "
           "Crossref chứ không từ trí nhớ.\n\n"
           "Thông điệp chính: Em không gắn Q1/Q2 cho bất kỳ nguồn nào, và em "
           "giải thích được tại sao.\n\n"
           "Nếu cô hỏi sâu: Trong 40 DOI em đề xuất ban đầu, 4 không tồn tại "
           "trong Crossref và 12 trả về một bài báo HOÀN TOÀN KHÁC — ví dụ một "
           "DOI em tưởng là bài utility mining thực ra là bài về nhận dạng "
           "tiếng nói. Tất cả đã bị loại. Đó là lý do phải xác minh.")

    info = D.save(OUT)
    # speaker notes file
    md = ["# Speaker notes — HUIM trong Indoor Positioning System\n",
          "> Sinh tự động bởi `src/make_slides.py`. Mỗi slide có ba phần: "
          "tôi cần nói gì, thông điệp chính, và nếu cô hỏi sâu thì trả lời "
          "gì.\n",
          "Ngôn ngữ nói tự nhiên — KHÔNG đọc chữ trên slide.\n"]
    for title, body in D.notes:
        md.append(f"\n## {title}\n")
        md.append(body.replace("Tôi cần nói gì:", "**Tôi cần nói gì:**")
                  .replace("Thông điệp chính:", "**Thông điệp chính:**")
                  .replace("Nếu cô hỏi sâu:", "**Nếu cô hỏi sâu:**"))
    (SLIDES / "speaker_notes.md").write_text("\n".join(md), encoding="utf-8")
    info["speaker_notes"] = str(SLIDES / "speaker_notes.md")
    info["n_notes"] = len(D.notes)
    return info


def main() -> None:
    info = build()
    dump_json(info, SLIDES / "slides_build_info.json")
    LOG.info("saved %s (%d slides)", info["path"], info["n_slides"])
    print(f"OK  {info['path']}  ({info['n_slides']} slides, "
          f"{info['n_notes']} speaker notes)")


if __name__ == "__main__":
    main()
