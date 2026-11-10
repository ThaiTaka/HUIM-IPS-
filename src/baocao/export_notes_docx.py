"""Xuất tiêu đề và ghi chú (kịch bản thuyết trình) của từng slide trong Slide_HUIM_IPS_V7_day_du.pptx ra Word.

    python src/baocao/export_notes_docx.py
Ghi: BAOCAO/Kich_ban_thuyet_trinh_V7.docx
"""
import html
import re
import zipfile
from pathlib import Path

from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "BAOCAO" / "Slide_HUIM_IPS_V7_day_du.pptx"
OUT = ROOT / "BAOCAO" / "Kich_ban_thuyet_trinh_V7.docx"
LABELS = ("KỊCH BẢN", "NÓI", "VÍ DỤ ĐỜI THƯỜNG", "VÌ SAO CHỌN", "CHUYỂN Ý", "THÀNH THẬT", "NẾU BỊ HỎI", "TỰ KIỂM", "NÓI THẲNG")


def slide_order(z):
    pres = z.read("ppt/presentation.xml").decode("utf-8")
    rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
    rid = re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)
    tgt = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
    tgt.update({k: v for v, k in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)})
    return [Path(tgt[r]).name for r in rid]


def texts(xml):
    return [html.unescape(t) for t in re.findall(r"<a:t>([^<]*)</a:t>", xml)]


z = zipfile.ZipFile(SRC)
doc = Document()
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(12)
doc.add_heading("Kịch bản thuyết trình HUIM-IPS V7", 0)
doc.add_paragraph("Nội dung lấy từ phần ghi chú của Slide_HUIM_IPS_V7_day_du.pptx, theo thứ tự slide.")
for i, name in enumerate(slide_order(z), 1):
    sx = z.read(f"ppt/slides/{name}").decode("utf-8")
    title = next((t for t in texts(sx) if len(t) > 12), f"Slide {i}")
    rel = z.read(f"ppt/slides/_rels/{name}.rels").decode("utf-8")
    m = re.search(r"notesSlides/(notesSlide\d+\.xml)", rel)
    doc.add_heading(f"Slide {i}: {title}", 1)
    if not m:
        continue
    lines = texts(z.read(f"ppt/notesSlides/{m.group(1)}").decode("utf-8"))
    if lines and lines[-1].strip().isdigit():
        lines = lines[:-1]                                  # số slide
    for ln in lines:
        p = doc.add_paragraph()
        mm = re.match(r"^([A-ZÀ-Ỹ][A-ZÀ-Ỹ ,()'\"/\-–0-9]*?)(\s*\(|:)", ln)
        if mm and mm.group(1).strip() in LABELS or (mm and ln.split(":")[0].isupper()):
            head, _, rest = ln.partition(":")
            p.add_run(head + ":").bold = True
            p.add_run(rest)
        else:
            p.add_run(ln)
doc.save(OUT)
print("written", OUT, OUT.stat().st_size)
