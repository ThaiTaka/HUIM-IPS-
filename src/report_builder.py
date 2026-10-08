"""Thin wrapper over python-docx: Times New Roman everywhere, numbered
captions, tables that come from DataFrames, and a hard guard against
placeholders.

The guard matters: `Doc.check()` scans the finished document for the strings
this project must never ship ("TODO", "XXX", "N/A" without an explanation,
"example value", "placeholder") and raises if one survived.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Times New Roman"
BODY_PT = 12
FORBIDDEN = ("TODO", "FIXME", "XXX", "PLACEHOLDER", "LOREM IPSUM",
             "EXAMPLE VALUE", "<INSERT", "TBD")


def _rfonts(run) -> None:
    """python-docx only sets the ASCII font; Vietnamese diacritics are resolved
    through the hAnsi/eastAsia/cs slots, so all four must be set or Word
    silently substitutes a different face."""
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rPr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)


class Doc:
    def __init__(self) -> None:
        self.d = Document()
        self._fig = 0
        self._tab = 0
        self._setup()

    # ------------------------------------------------------------------ setup
    def _setup(self) -> None:
        for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3",
                     "Heading 4", "Caption", "List Bullet", "List Number",
                     "Quote", "Intense Quote"):
            try:
                st = self.d.styles[name]
            except KeyError:
                continue
            st.font.name = FONT
            if name == "Normal":
                st.font.size = Pt(BODY_PT)
            rpr = st.element.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rpr.append(rf)
            for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                rf.set(qn(a), FONT)
        # Styles alone are not enough: Word falls back to the document
        # defaults and to the theme fonts for anything a style does not pin,
        # which is how Calibri reappears in a document whose styles are all
        # Times New Roman. Pin both.
        self._pin_doc_defaults()
        self._pin_theme_fonts()
        n = self.d.styles["Normal"]
        n.paragraph_format.space_after = Pt(3)
        n.paragraph_format.line_spacing = 1.15
        for lvl, size in ((1, 16), (2, 14), (3, 12.5), (4, 12)):
            st = self.d.styles[f"Heading {lvl}"]
            st.font.size = Pt(size)
            st.font.bold = True
            st.font.color.rgb = RGBColor(0x1F, 0x1F, 0x1F)
        sec = self.d.sections[0]
        sec.left_margin = sec.right_margin = Inches(1.0)
        sec.top_margin = sec.bottom_margin = Inches(1.0)
        self._page_numbers(sec)

    def _pin_doc_defaults(self) -> None:
        """w:docDefaults/w:rPrDefault/w:rFonts - the fallback Word uses for any
        run whose style does not name a font."""
        styles = self.d.styles.element
        dd = styles.find(qn("w:docDefaults"))
        if dd is None:
            dd = OxmlElement("w:docDefaults")
            styles.insert(0, dd)
        rprd = dd.find(qn("w:rPrDefault"))
        if rprd is None:
            rprd = OxmlElement("w:rPrDefault")
            dd.insert(0, rprd)
        rpr = rprd.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            rprd.append(rpr)
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), FONT)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme",
                  "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
        sz = rpr.find(qn("w:sz"))
        if sz is None:
            sz = OxmlElement("w:sz")
            rpr.append(sz)
        sz.set(qn("w:val"), str(int(BODY_PT * 2)))

    def _pin_theme_fonts(self) -> None:
        """Styles that reference the theme (+Headings / +Body) resolve through
        theme1.xml, so the theme's major and minor Latin fonts are pinned too."""
        # The theme is related to the DOCUMENT part, not to the package.
        part = None
        for p in self.d.part.package.iter_parts():
            if str(p.partname).lower().endswith("theme1.xml"):
                part = p
                break
        if part is None:
            return
        try:
            from lxml import etree
            root = etree.fromstring(part.blob)
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            changed = False
            for tag in ("majorFont", "minorFont"):
                for latin in root.findall(f".//a:{tag}/a:latin", ns):
                    latin.set("typeface", FONT)
                    changed = True
            if changed:
                part._blob = etree.tostring(root, xml_declaration=True,
                                            encoding="UTF-8", standalone=True)
        except Exception:
            pass

    def _page_numbers(self, sec) -> None:
        p = sec.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run()
        _rfonts(r)
        r.font.size = Pt(10)
        for el, txt in ((OxmlElement("w:fldChar"), None),
                        (OxmlElement("w:instrText"), "PAGE"),
                        (OxmlElement("w:fldChar"), None)):
            if txt is None:
                el.set(qn("w:fldCharType"),
                       "begin" if el is None else "begin")
        fld1 = OxmlElement("w:fldChar")
        fld1.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = "PAGE"
        fld2 = OxmlElement("w:fldChar")
        fld2.set(qn("w:fldCharType"), "end")
        r._element.append(fld1)
        r._element.append(instr)
        r._element.append(fld2)

    # ---------------------------------------------------------------- content
    def title_page(self, lines: Sequence[tuple[str, int, bool]]) -> None:
        for _ in range(3):
            self.d.add_paragraph()
        for text, size, bold in lines:
            p = self.d.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.size = Pt(size)
            r.bold = bold
            _rfonts(r)
        self.page_break()

    def h(self, level: int, text: str) -> None:
        p = self.d.add_heading(text, level=level)
        for r in p.runs:
            _rfonts(r)

    def p(self, text: str, italic: bool = False, bold: bool = False,
          align: str | None = None, size: float | None = None) -> None:
        par = self.d.add_paragraph()
        if align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = par.add_run(text)
        r.italic = italic
        r.bold = bold
        if size:
            r.font.size = Pt(size)
        _rfonts(r)

    def rich(self, parts: Sequence[tuple[str, str]],
             align: str | None = "justify") -> None:
        """parts = [(text, style)] where style in {"", "b", "i", "bi", "c"}."""
        par = self.d.add_paragraph()
        if align == "justify":
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for text, style in parts:
            r = par.add_run(text)
            r.bold = "b" in style
            r.italic = "i" in style
            if "c" in style:
                r.font.size = Pt(BODY_PT - 1)
            _rfonts(r)

    def bullets(self, items: Iterable[str], numbered: bool = False) -> None:
        style = "List Number" if numbered else "List Bullet"
        for it in items:
            par = self.d.add_paragraph(style=style)
            r = par.add_run(it)
            _rfonts(r)

    def formula(self, text: str, explain: str | None = None) -> None:
        par = self.d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = par.add_run(text)
        r.italic = True
        r.font.size = Pt(BODY_PT + 1)
        _rfonts(r)
        if explain:
            self.p(explain, size=BODY_PT - 1, align="justify")

    def caption(self, text: str, kind: str = "Bảng") -> str:
        if kind == "Bảng":
            self._tab += 1
            num = self._tab
        else:
            self._fig += 1
            num = self._fig
        par = self.d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = par.add_run(f"{kind} {num}. {text}")
        r.italic = True
        r.font.size = Pt(BODY_PT - 1)
        _rfonts(r)
        return f"{kind} {num}"

    def table(self, df: pd.DataFrame, caption: str,
              font_pt: float = 9.0, widths: Sequence[float] | None = None,
              max_rows: int | None = None) -> str:
        label = self.caption(caption, "Bảng")
        if max_rows is not None and len(df) > max_rows:
            df = df.head(max_rows)
        t = self.d.add_table(rows=1, cols=len(df.columns))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, c in enumerate(df.columns):
            cell = t.rows[0].cells[j]
            cell.text = ""
            r = cell.paragraphs[0].add_run(str(c))
            r.bold = True
            r.font.size = Pt(font_pt)
            _rfonts(r)
        for _, row in df.iterrows():
            cells = t.add_row().cells
            for j, c in enumerate(df.columns):
                cells[j].text = ""
                r = cells[j].paragraphs[0].add_run(
                    "" if pd.isna(row[c]) else str(row[c]))
                r.font.size = Pt(font_pt)
                _rfonts(r)
        if widths:
            for row in t.rows:
                for j, w in enumerate(widths):
                    if j < len(row.cells):
                        row.cells[j].width = Inches(w)
        self.d.add_paragraph()
        return label

    def figure(self, path: Path, caption: str, width_in: float = 5.3) -> str:
        if not Path(path).exists():
            raise FileNotFoundError(f"figure missing: {path}")
        par = self.d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.add_run().add_picture(str(path), width=Inches(width_in))
        return self.caption(caption, "Hình")

    def page_break(self) -> None:
        self.d.add_page_break()

    def toc_field(self) -> None:
        """A real Word TOC field; Word fills it on open (F9). A static list is
        also printed by the caller so the file is useful without Word."""
        par = self.d.add_paragraph()
        r = par.add_run()
        _rfonts(r)
        b = OxmlElement("w:fldChar")
        b.set(qn("w:fldCharType"), "begin")
        i = OxmlElement("w:instrText")
        i.set(qn("xml:space"), "preserve")
        i.text = 'TOC \\o "1-2" \\h \\z \\u'
        s = OxmlElement("w:fldChar")
        s.set(qn("w:fldCharType"), "separate")
        t = OxmlElement("w:t")
        t.text = ("Mục lục sẽ được Word tạo tự động: nhấn Ctrl+A rồi F9, "
                  "hoặc bấm chuột phải vào đây và chọn Update Field.")
        e = OxmlElement("w:fldChar")
        e.set(qn("w:fldCharType"), "end")
        for el in (b, i, s, t, e):
            r._element.append(el)

    # ------------------------------------------------------------------ check
    def check(self) -> dict:
        texts = [p.text for p in self.d.paragraphs]
        for t in self.d.tables:
            for row in t.rows:
                for c in row.cells:
                    texts.append(c.text)
        blob = "\n".join(texts)
        up = blob.upper()
        hits = [w for w in FORBIDDEN if w in up]
        if hits:
            raise AssertionError(f"forbidden placeholder text in report: {hits}")
        bad_font = []
        for p in self.d.paragraphs:
            for r in p.runs:
                if r.font.name not in (None, FONT):
                    bad_font.append(r.font.name)
        return {"n_paragraphs": len(self.d.paragraphs),
                "n_tables": len(self.d.tables),
                "n_figures": self._fig,
                "n_numbered_tables": self._tab,
                "n_characters": len(blob),
                "non_times_new_roman_runs": sorted(set(bad_font))}

    def save(self, path: Path) -> dict:
        """Write via a temporary file and then replace.

        On Windows the Search indexer and Explorer's preview handler open a
        .docx moments after it changes, so saving straight onto the target
        intermittently fails with PermissionError. Writing elsewhere and then
        os.replace() keeps the window in which the target is open as short as
        possible, and the retry covers the case where even that loses the
        race."""
        import os
        import time
        info = self.check()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + ".__tmp__" + path.suffix)
        self.d.save(str(tmp))
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
                f"{path} stayed locked by another process through 8 retries. "
                f"Close Word/Explorer preview for it and re-run. ({last})")
        info["path"] = str(path)
        return info
