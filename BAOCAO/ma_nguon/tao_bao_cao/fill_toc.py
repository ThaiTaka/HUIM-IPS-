"""Điền sẵn Mục lục, Danh mục hình, Danh mục bảng (kèm số trang) vào báo cáo .docx.

docx-js chỉ ghi trường TOC rỗng; Word điền khi cập nhật trường, nhưng trình xem khác
(và bản PDF) sẽ thấy trang trống. Script này dựng PDF bằng LibreOffice, tìm trang của
từng đề mục / chú thích, rồi ghi các dòng đó vào phần kết quả của trường TOC
(Word vẫn có thể cập nhật lại bằng F9). Lặp tới khi số trang không đổi.

Chạy: python src/baocao/fill_toc.py BAOCAO/Bao_cao_HUIM_IPS_UJIIndoorLoc.docx
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from html import escape
from pathlib import Path

W = 9071                                     # bề rộng vùng chữ (DXA)
FONT = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
SOFFICE_PY = Path("/root/.claude/skills/synced/b3a8680d-0654-4773-b5d2-44a0ece69c6e_ed22ee13-d275-4aa5-ab26-52b7fc33cef8/pptx/scripts/office/soffice.py")


def para_items(xml: str):
    """(kiểu, cấp, chữ) của mọi đề mục Heading1-3 và chú thích hình/bảng, theo thứ tự."""
    out = []
    for p in re.findall(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", xml, flags=re.S):
        m = re.search(r'<w:pStyle w:val="(Heading[123]|CaptionHinh|CaptionBang)"/>', p)
        if not m:
            continue
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        st = m.group(1)
        kind = "toc" if st.startswith("Heading") else ("hinh" if st == "CaptionHinh" else "bang")
        out.append((kind, int(st[-1]) if kind == "toc" else 1, text.strip()))
    return out


def render_pages(docx: Path) -> list[str]:
    tmp = Path(tempfile.mkdtemp())
    cmd = ([sys.executable, str(SOFFICE_PY)] if SOFFICE_PY.exists() else ["soffice"]) + \
        ["--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(docx)]
    subprocess.run(cmd, check=True, capture_output=True)
    pdf = tmp / (docx.stem + ".pdf")
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                         capture_output=True, text=True).stdout
    shutil.rmtree(tmp)
    pages, labels = [], []
    for pg in txt.split("\f"):
        lines = [ln for ln in pg.splitlines() if not re.search(r"\.{4,}|…{2,}", ln)]
        pages.append(re.sub(r"\s+", "", "\n".join(lines)))
        tail = [ln.strip() for ln in pg.splitlines() if ln.strip()]
        lab = tail[-1] if tail else ""
        labels.append(lab if re.fullmatch(r"[ivxlcdm]+|\d+", lab) else "")
    return pages, labels


def find_pages(items, pages, labels):
    res, cur = [], 0
    for kind, lvl, text in items:
        key = re.sub(r"\s+", "", text)[:60]
        pg = next((i for i in range(cur, len(pages)) if key in pages[i]), None)
        if pg is None:
            raise SystemExit(f"không tìm thấy trang cho: {text}")
        res.append(labels[pg] or str(pg + 1))
        if kind == "toc":
            cur = pg
    return res


def entry(text: str, page: int, lvl: int, bold: bool) -> str:
    ind = {1: 0, 2: 283, 3: 567}[lvl]
    b = "<w:b/>" if bold else ""
    rpr = f"<w:rPr>{FONT}{b}</w:rPr>"
    return (f'<w:p><w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{W}"/></w:tabs>'
            f'<w:spacing w:before="0" w:after="60" w:line="300" w:lineRule="auto"/><w:ind w:left="{ind}"/></w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text, quote=False)}</w:t></w:r>'
            f'<w:r>{rpr}<w:tab/></w:r><w:r>{rpr}<w:t>{page}</w:t></w:r></w:p>')


def fill(xml: str, items, pages_of) -> str:
    groups = {"toc": [], "hinh": [], "bang": []}
    for (kind, lvl, text), pg in zip(items, pages_of):
        groups[kind].append(entry(text, pg, lvl, kind == "toc" and lvl == 1))
    instr = {"toc": "TOC \\h \\o", "hinh": "CaptionHinh", "bang": "CaptionBang"}
    for kind, body in groups.items():
        pat = re.compile(r'(<w:instrText xml:space="preserve">[^<]*' + re.escape(instr[kind]) +
                         r'[^<]*</w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>)'
                         r'.*?(<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>)', re.S)
        xml, n = pat.subn(lambda m: m.group(1) + "".join(body) + m.group(2), xml, count=1)
        assert n == 1, kind
    return xml


def rewrite(docx: Path, xml: str) -> None:
    """Ghi document.xml; bỏ cờ dirty để mọi trình xem hiển thị ngay mục lục đã điền
    (Word vẫn cập nhật được bằng chuột phải > Update Field hoặc F9)."""
    xml = xml.replace(' w:dirty="true"', "")
    tmp = docx.with_suffix(".tmp")
    with zipfile.ZipFile(docx) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            if it.filename == "word/document.xml":
                b = xml.encode("utf-8")
            elif it.filename == "word/settings.xml":
                b = zi.read(it.filename).decode("utf-8").replace('<w:updateFields w:val="true"/>', "").encode("utf-8")
            else:
                b = zi.read(it.filename)
            zo.writestr(it, b)
    shutil.move(tmp, docx)


def main(docx: Path) -> None:
    with zipfile.ZipFile(docx) as z:
        base = z.read("word/document.xml").decode("utf-8")
    items = para_items(base)
    prev = None
    for _ in range(4):
        pages_of = find_pages(items, *render_pages(docx))
        if pages_of == prev:
            break
        rewrite(docx, fill(base, items, pages_of))
        prev = pages_of
    print(f"mục lục: {sum(k == 'toc' for k, _, _ in items)} đề mục, "
          f"{sum(k == 'hinh' for k, _, _ in items)} hình, {sum(k == 'bang' for k, _, _ in items)} bảng")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
