// Thư viện dựng báo cáo .docx theo thể thức luận văn thạc sĩ (dùng bởi build_report.js).
// Times New Roman 13 pt, giãn dòng 1,5; lề trên/dưới 2 cm, trái 3 cm, phải 2 cm; công thức OMML
// (chữ trong công thức cũng đặt Times New Roman); hình, bảng, công thức đánh số theo chương.
const fs = require("fs");
const path = require("path");
const d = require("docx");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, HeadingLevel, TableOfContents, Footer, PageNumber, TabStopType, NumberFormat,
  BorderStyle, ShadingType, LevelFormat, VerticalAlign, Tab,
  Math: M, MathRun, MathFraction, MathSubScript, MathSuperScript, MathSubSuperScript,
  MathSum, MathRadical, MathRoundBrackets, MathSquareBrackets, MathCurlyBrackets,
} = d;

const FONT = "Times New Roman";
const PT = (x) => x * 2;
const C = AlignmentType.CENTER, RT = AlignmentType.RIGHT, L = AlignmentType.LEFT, J = AlignmentType.JUSTIFIED;
const TEXT_W = 9071;                         // A4 trừ lề trái 3 cm và phải 2 cm (DXA)
const INK = "000000", HEAD_FILL = "D9D9D9";

// ------------------------------------------------------------------ số
const vn = (x, k = 2) => Number(x).toFixed(k).replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
const pct = (x, k = 1) => vn(100 * x, k) + "%";

// ------------------------------------------------------------------ chữ
const R = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
const UPRIGHT = /^([A-Z]{2,}|exp|max|min|arg|round|log|floor)$/;
function mathRuns(s, base) {       // $…$ nội dòng: chữ cái nghiêng, _x chỉ số dưới, ^x chỉ số trên
  const out = [];
  s.split(/(_\{[^}]*\}|_[^\s,.;:()\]{}=<>]+|\^\{[^}]*\}|\^[^\s,.;:()\]{}=<>]+|[A-Za-zα-ωΑ-Ω]+)/).forEach((t) => {
    if (!t) return;
    const brace = (x) => x.replace(/^[_^]\{?/, "").replace(/\}$/, "");
    const it = (x) => /[A-Za-zα-ωΑ-Ω]/.test(x) && !UPRIGHT.test(x);
    if (t[0] === "_") { const x = brace(t); out.push(R(x, { ...base, subScript: true, italics: it(x) })); }
    else if (t[0] === "^") { const x = brace(t); out.push(R(x, { ...base, superScript: true, italics: it(x) })); }
    else if (/^[A-Za-zα-ωΑ-Ω]+$/.test(t)) out.push(R(t, { ...base, italics: !UPRIGHT.test(t) }));
    else out.push(R(t, base));
  });
  return out;
}
function runs(s, base = {}) {      // **đậm**, *nghiêng*, $công thức$
  const out = [];
  s.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|\$[^$]+\$)/).forEach((p) => {
    if (!p) return;
    if (p.startsWith("**")) out.push(R(p.slice(2, -2), { ...base, bold: true }));
    else if (p.startsWith("*") && p.length > 2) out.push(R(p.slice(1, -1), { ...base, italics: true }));
    else if (p.startsWith("$") && p.length > 2) out.push(...mathRuns(p.slice(1, -1), base));
    else out.push(R(p, base));
  });
  return out;
}
const P = (s, o = {}) => new Paragraph({ children: Array.isArray(s) ? s : runs(s), alignment: J,
  spacing: { before: 0, after: 120, line: 360 }, indent: { firstLine: 567 }, ...o });
const PN = (s, o = {}) => P(s, { indent: { firstLine: 0 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [R(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [R(t)] });
const BUL = (s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(s), alignment: J,
  spacing: { after: 80, line: 360 } });
let numRef = 0;
function NUMS(items) {             // danh sách đánh số 1), 2)… bắt đầu lại từ 1 mỗi lần gọi
  const ref = `num${numRef++}`;
  numbering.push({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1)", alignment: L,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] });
  return items.map((s) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(s), alignment: J,
    spacing: { after: 80, line: 360 } }));
}
const numbering = [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: L,
  style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }];

// ------------------------------------------------------------------ công thức (OMML)
const r = (t) => new MathRun(t);
const fr = (n, dd) => new MathFraction({ numerator: n, denominator: dd });
const sb = (b, s) => new MathSubScript({ children: b, subScript: s });
const sp = (b, s) => new MathSuperScript({ children: b, superScript: s });
const sbsp = (b, s, u) => new MathSubSuperScript({ children: b, subScript: s, superScript: u });
const sum = (lo, body, hi) => new MathSum({ children: body, subScript: lo, ...(hi ? { superScript: hi } : {}) });
const sqrt = (b) => new MathRadical({ children: b });
const rb = (...c) => new MathRoundBrackets({ children: c });
const sq = (...c) => new MathSquareBrackets({ children: c });
const cb = (...c) => new MathCurlyBrackets({ children: c });
const up = (t) => r("⁠" + t);                  // chữ đứng (tên hàm, nhãn)
const abs = (...c) => rb(r("⁢ABS"), ...c);       // |…|
const flo = (...c) => rb(r("⁢FLO"), ...c);       // ⌊…⌋
const eqNo = {};
function EQ(chap, children) {      // bảng 3 cột không viền: trống | công thức | (số hiệu)
  eqNo[chap] = (eqNo[chap] || 0) + 1;
  const label = `(${chap}.${eqNo[chap]})`;
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const nb = { top: none, bottom: none, left: none, right: none };
  const cell = (w, align, kids) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: nb,
    verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 0, right: 0 },
    children: [new Paragraph({ alignment: align, spacing: { before: 60, after: 60 }, children: kids })] });
  return { label, p: new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [900, 7271, 900],
    borders: { ...nb, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ cantSplit: true, children: [cell(900, L, []),
      cell(7271, C, [new M({ children })]), cell(900, RT, [R(label)])] })] }) };
}

// ------------------------------------------------------------------ hình, bảng, khung
const figNo = {}, tabNo = {}, algNo = {};
function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function FIG(chap, file, caption, widthPx = 600) {
  figNo[chap] = (figNo[chap] || 0) + 1;
  const [w, h] = pngSize(file);
  let W = Math.min(widthPx, 605), H = Math.round(W * h / w);
  if (H > 760) { H = 760; W = Math.round(H * w / h); }
  const label = `Hình ${chap}.${figNo[chap]}`;
  return { label, ps: [
    new Paragraph({ alignment: C, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: W, height: H },
        altText: { title: caption, description: caption, name: path.basename(file) } })] }),
    new Paragraph({ style: "CaptionHinh", children: [R(`${label}. `, { bold: true, italics: false }), R(caption)] })] };
}
const line = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: line, bottom: line, left: line, right: line };
function TAB(chap, caption, header, rows, widths, opts = {}) {
  tabNo[chap] = (tabNo[chap] || 0) + 1;
  const label = `Bảng ${chap}.${tabNo[chap]}`;
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, head) => new TableCell({
    borders, width: { size: widths[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { fill: HEAD_FILL, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: head ? C : ((opts.align && opts.align[i]) || L), spacing: { line: 260 },
      children: (typeof t === "string" ? runs(t, { bold: head || (opts.boldRow && opts.boldRow(rIdx)), size: PT(opts.size || 11.5) }) : t) })] });
  let rIdx = -1;
  return { label, ps: [
    new Paragraph({ style: "CaptionBang", keepNext: true, children: [R(`${label}. `, { bold: true, italics: false }), R(caption)] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: C,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }),
             ...rows.map((rw, k) => { rIdx = k; return new TableRow({ cantSplit: true, children: rw.map((c, i) => cell(String(c), i, false)) }); })] }),
    new Paragraph({ spacing: { after: 160 }, children: [] })] };
}
function ALGO(chap, title, lines) {          // khung thuật toán: dòng không thụt lề in đậm
  algNo[chap] = (algNo[chap] || 0) + 1;
  const label = `Thuật toán ${chap}.${algNo[chap]}`;
  return { label, ps: [
    new Paragraph({ style: "CaptionThuatToan", keepNext: true, children: [R(`${label}. `, { bold: true, italics: false }), R(title)] }),
    new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], alignment: C,
      rows: [new TableRow({ cantSplit: true, children: [new TableCell({ borders, width: { size: TEXT_W, type: WidthType.DXA },
        margins: { top: 100, bottom: 100, left: 160, right: 160 },
        children: lines.map((t) => new Paragraph({ spacing: { after: 20, line: 276 },
          children: runs(t, { size: PT(12), bold: !t.startsWith(" ") }) })) })] })] }),
    new Paragraph({ spacing: { after: 160 }, children: [] })] };
}
function BOX(title, lines) {                  // khung ghi chú (định nghĩa, nhận xét)
  return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], alignment: C,
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({ borders, width: { size: TEXT_W, type: WidthType.DXA },
      shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" }, margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [new Paragraph({ spacing: { after: 60 }, children: [R(title, { bold: true })] }),
        ...lines.map((t) => new Paragraph({ alignment: J, spacing: { after: 40, line: 300 }, children: runs(t) }))] })] })] });
}
const GAP = () => new Paragraph({ spacing: { after: 120 }, children: [] });

// ------------------------------------------------------------------ bìa
function frameBorders() {
  const b = { style: BorderStyle.THICK_THIN_SMALL_GAP, size: 24, color: "000000", space: 24 };
  return { pageBorderTop: b, pageBorderBottom: b, pageBorderLeft: b, pageBorderRight: b };
}

// ------------------------------------------------------------------ tài liệu
function build({ cover, titlePage, front, body, out }) {
  const page = { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 1134, footer: 567 } };
  const foot = () => ({ default: new Footer({ children: [new Paragraph({ alignment: C,
    children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: PT(12) })] })] }) });
  const doc = new Document({
    creator: "Học viên", title: "Ứng dụng HUIM trong hệ thống định vị trong nhà",
    styles: {
      default: { document: { run: { font: FONT, size: PT(13), color: INK } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT, size: PT(14), bold: true, color: INK, allCaps: false },
          paragraph: { alignment: C, spacing: { before: 0, after: 360, line: 360 }, outlineLevel: 0, keepNext: true } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT, size: PT(13), bold: true, color: INK },
          paragraph: { spacing: { before: 240, after: 120, line: 360 }, keepNext: true, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: FONT, size: PT(13), bold: true, italics: true, color: INK },
          paragraph: { spacing: { before: 180, after: 100, line: 360 }, keepNext: true, outlineLevel: 2 } },
        { id: "CaptionHinh", name: "Caption Hinh", basedOn: "Normal", run: { font: FONT, size: PT(12), italics: true },
          paragraph: { alignment: C, spacing: { before: 40, after: 240, line: 276 } } },
        { id: "CaptionBang", name: "Caption Bang", basedOn: "Normal", run: { font: FONT, size: PT(12), italics: true },
          paragraph: { alignment: C, spacing: { before: 200, after: 80, line: 276 } } },
        { id: "CaptionThuatToan", name: "Caption Thuat Toan", basedOn: "Normal", run: { font: FONT, size: PT(12), italics: true },
          paragraph: { alignment: C, spacing: { before: 200, after: 80, line: 276 } } },
      ],
    },
    numbering: { config: numbering },
    sections: [
      { properties: { page: { ...page, borders: frameBorders() } }, children: cover },
      { properties: { page: { ...page, borders: frameBorders() } }, children: titlePage },
      { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } },
        footers: foot(), children: front },
      { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
        footers: foot(), children: body },
    ],
  });
  return Packer.toBuffer(doc).then((buf) => {
    fs.writeFileSync(out, buf);
    // Hậu xử lý OMML: <m:sup/> bắt buộc của <m:nary>; dấu |…|, ⌊…⌋; chữ đứng; phông Times New Roman
    // cho chữ trong công thức. Sau đó điền sẵn mục lục, danh mục hình/bảng kèm số trang.
    require("child_process").execFileSync("python3", [path.join(__dirname, "postprocess_docx.py"), out], { stdio: "inherit" });
    require("child_process").execFileSync("python3", [path.join(__dirname, "fill_toc.py"), out], { stdio: "inherit" });
    console.log("written", out, fs.statSync(out).size);
  });
}

module.exports = {
  d, FONT, PT, C, RT, L, J, TEXT_W, vn, pct, R, runs, P, PN, H1, H2, H3, BUL, NUMS, GAP,
  r, fr, sb, sp, sbsp, sum, sqrt, rb, sq, cb, up, abs, flo, EQ, FIG, TAB, ALGO, BOX, build,
  TableOfContents, Paragraph, TextRun, Tab, TabStopType, AlignmentType, HeadingLevel,
};
