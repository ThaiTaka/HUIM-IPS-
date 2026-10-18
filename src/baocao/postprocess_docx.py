"""Hậu xử lý word/document.xml của báo cáo do docx-js sinh ra.

- <m:nary> phải có <m:sup> (kể cả khi ẩn) theo lược đồ OMML; docx-js bỏ qua phần tử này.
- Các dấu ngoặc đánh dấu bằng ký tự ẩn: ⁢ABS -> |…|, ⁢FLO -> ⌊…⌋.
- Chữ đứng (tên hàm) đánh dấu bằng ⁠ -> <m:sty m:val="p"/>.
- Chữ trong công thức đặt phông Times New Roman.

Chạy: python src/baocao/postprocess_docx.py <file.docx>
"""
import re
import shutil
import sys
import zipfile

TNR = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/></w:rPr>'


def fix(x: str) -> str:
    x = x.replace("</m:sub><m:e>", "</m:sub><m:sup/><m:e>")
    x = x.replace("<m:d><m:dPr/><m:e><m:r><m:t>⁢ABS</m:t></m:r>",
                  '<m:d><m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr><m:e>')
    x = x.replace("<m:d><m:dPr/><m:e><m:r><m:t>⁢FLO</m:t></m:r>",
                  '<m:d><m:dPr><m:begChr m:val="⌊"/><m:endChr m:val="⌋"/></m:dPr><m:e>')
    x = x.replace("<m:r><m:t>⁠", '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>')
    assert "⁠" not in x and "⁢" not in x
    x = re.sub(r"<m:r>(<m:t[ >])", r"<m:r>" + TNR + r"\1", x)
    x = re.sub(r"</m:rPr>(<m:t[ >])", r"</m:rPr>" + TNR + r"\1", x)
    return x


def main(p: str) -> None:
    t = p + ".tmp"
    with zipfile.ZipFile(p) as zi, zipfile.ZipFile(t, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == "word/document.xml":
                b = fix(b.decode("utf-8")).encode("utf-8")
            zo.writestr(it, b)
    shutil.move(t, p)


if __name__ == "__main__":
    main(sys.argv[1])
