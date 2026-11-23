// Bộ công cụ dựng slide cho Slide_HUIM_IPS_V7_day_du.pptx (cùng thiết kế với Slide_HUIM_IPS_V7.pptx:
// Times New Roman, nền navy cho bìa/chương, thẻ teal/rust, công thức là ảnh mathtext).
// createKit() trả về mọi hàm/hằng số mà các phần nội dung (dd_*.js) dùng.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

module.exports = function createKit({ TMP, ROOT }) {
  const B = path.join(ROOT, "BAOCAO");
  const rd = (f) => JSON.parse(fs.readFileSync(path.join(B, "so_lieu_V7", f), "utf8"));
  const D = rd("du_lieu_bao_cao_V7.json"), E = rd("nguon_goc_hang_so.json"), DS = rd("du_lieu_dataset_uji.json");

  const THEME = {
    name: "HUIM IPS V7 đầy đủ", headFontFace: "Times New Roman", bodyFontFace: "Times New Roman",
    colors: { dk1: "1B2A3D", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F6F4EF", accent1: "2A7F8F", accent2: "B5532A",
              accent3: "8A8A85", accent4: "C9A227", accent5: "4C6A88", accent6: "9BB7C4", hlink: "2A7F8F", folHlink: "4C6A88" },
  };
  const K = THEME.colors;
  const INK = K.dk1, NAVY = K.dk2, TEAL = K.accent1, RUST = K.accent2, GREY = K.accent3, GOLD = K.accent4;
  const LINE = "D8D3C8", SOFT = "E6F0F2", SOFT2 = "F7EAE3", CARD = "FBFAF7";
  const F = "Times New Roman";
  const SW = 13.333, SH = 7.5, MX = 0.6, W = SW - 2 * MX;

  // số kiểu Việt Nam: dấu phẩy thập phân, khoảng trắng nhóm phần nguyên
  const vn = (x, k = 2) => {
    const [i, f] = Number(x).toFixed(k).split(".");
    return (i.startsWith("-") ? "−" + i.slice(1) : i).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + (f ? "," + f : "");
  };
  const vnd = (x, k = 2) => (x > 0 ? "+" : x < 0 ? "−" : "") + vn(Math.abs(x), k);
  const pct = (x, k = 1) => vn(100 * x, k) + "%";
  const tr = (m) => D.test.find((r) => r.model === m);
  const dI = (m) => D.dev_inf.find((r) => r.model === m);
  const dA = (m) => D.dev_all.find((r) => r.model === m);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: F, bodyFontFace: F };
  pres.title = "HUIM-IPS V7: từ dữ liệu UJIIndoorLoc đến sai số 6,3 m";
  pres.subject = "Thuật toán V7 đầy đủ: dữ liệu, HUI, chọn ứng viên, học trọng số, kết quả, kiểm chứng";
  const CHAPTERS = ["Dữ liệu", "Mẫu HUI", "Ứng viên", "Học trọng số", "Ví dụ", "Kết quả", "Kiểm chứng"];
  pres.defineSlideMaster({ title: "TOI", background: { color: NAVY }, objects: [] });
  pres.defineSlideMaster({
    title: "NOI_DUNG", background: { color: "FFFFFF" },
    objects: [
      { rect: { x: 0, y: 0, w: SW, h: 0.12, fill: { color: NAVY }, line: { color: NAVY } } },
      { line: { x: MX, y: 6.98, w: SW - 2 * MX, h: 0, line: { color: LINE, width: 0.75 } } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.55, w: SW - 2 * MX, h: 0.75,
        fontFace: F, fontSize: 27, bold: true, color: NAVY, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: SW - MX - 0.8, y: 7.06, w: 0.8, h: 0.3, fontFace: F, fontSize: 11, color: GREY, align: "right" },
  });

  let curChap = -1, curSection = "Mở đầu";
  const warnings = [];
  function tracker(s) {
    const w = 1.6;
    CHAPTERS.forEach((c, i) => {
      const x = MX + i * (w + 0.08), on = i === curChap;
      s.addShape(pres.shapes.RECTANGLE, { x, y: 7.1, w, h: 0.05, fill: { color: on ? TEAL : "E3E0D8" }, line: { color: on ? TEAL : "E3E0D8" } });
      s.addText(`${i + 1}. ${c}`, { x, y: 7.15, w, h: 0.25, fontFace: F, fontSize: 9.5, color: on ? NAVY : GREY, bold: on, margin: 0, isTextBox: true });
    });
  }
  function slide(kicker, title, notes) {
    if (title.length > 64) warnings.push(`TIÊU ĐỀ DÀI (${title.length}): ${title}`);
    if (!notes || notes.length < 400) warnings.push(`GHI CHÚ NGẮN (${(notes || "").length}): ${title}`);
    const s = pres.addSlide({ masterName: "NOI_DUNG", sectionTitle: curSection });
    s.addText(kicker.toUpperCase(), { x: MX, y: 0.24, w: 10, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5, margin: 0, isTextBox: true });
    s.addText(title, { placeholder: "title" });
    tracker(s);
    if (notes) s.addNotes(notes);
    return s;
  }
  function divider(i, title, items, notes) {
    curChap = i; curSection = CHAPTERS[i];
    pres.addSection({ title: CHAPTERS[i] });
    const s = pres.addSlide({ masterName: "TOI", sectionTitle: CHAPTERS[i] });
    s.background = { path: path.join(TMP, "art_section.png") };
    s.addText(String(i + 1).padStart(2, "0"), { x: MX, y: 1.3, w: 3, h: 1.6, fontFace: F, fontSize: 110, bold: true, color: "7FB3BF", margin: 0, isTextBox: true });
    s.addText(title, { x: MX, y: 3.0, w: 11, h: 1.0, fontFace: F, fontSize: 38, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
    s.addShape(pres.shapes.LINE, { x: MX, y: 4.15, w: 2.6, h: 0, line: { color: GOLD, width: 2 } });
    s.addText(items.map((t, k) => ({ text: t, options: { breakLine: k < items.length - 1 } })),
      { x: MX, y: 4.35, w: 10, h: 2.4, fontFace: F, fontSize: 18, color: "DCE6EE", valign: "top", paraSpaceAfter: 6, margin: 0, isTextBox: true });
    if (notes) s.addNotes(notes);
    return s;
  }
  function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
  function img(s, file, x, y, w, h, align = "center", name) {
    const [pw, ph] = pngSize(file);
    let Wd = w, H = w * ph / pw;
    if (H > h) { H = h; Wd = h * pw / ph; }
    const X = align === "left" ? x : align === "right" ? x + w - Wd : x + (w - Wd) / 2;
    s.addImage({ path: file, x: X, y, w: Wd, h: H, altText: name || path.basename(file) });
    return { x: X, y, w: Wd, h: H };
  }
  const as = (f) => path.join(TMP, f + ".png");
  function para(text) {
    return text.split(/(\*\*[^*]+\*\*|_\{[^}]*\}|\^\{[^}]*\})/).filter(Boolean).map((p) =>
      p.startsWith("**") ? { text: p.slice(2, -2), options: { bold: true } }
        : p.startsWith("_{") ? { text: p.slice(2, -1), options: { subscript: true } }
        : p.startsWith("^{") ? { text: p.slice(2, -1), options: { superscript: true } }
        : { text: p, options: {} });
  }
  function bullets(s, items, x, y, w, h, size = 15, color = INK, gap = 6) {
    const runs = [];
    items.forEach((t, i) => {
      const r = para(t).map((q) => ({ text: q.text, options: { ...q.options, bullet: { indent: 16 }, align: "left", paraSpaceAfter: gap } }));
      if (i < items.length - 1) r[r.length - 1].options.breakLine = true;
      runs.push(...r);
    });
    s.addText(runs, { x, y, w, h, fontFace: F, fontSize: size, color, valign: "top", margin: 2, isTextBox: true });
  }
  function text(s, t, x, y, w, h, o = {}) {
    s.addText(para(t), { x, y, w, h, fontFace: F, fontSize: 15, color: INK, valign: "top", margin: 0, isTextBox: true, ...o });
  }
  function ann(s, items, x, y, w, h, size = 13.5) {      // chú thích ký hiệu: **ký hiệu** — ý nghĩa
    const runs = [];
    items.forEach(([sym, mean], i) => {
      para(sym).forEach((q) => runs.push({ text: q.text, options: { ...q.options, bold: true, color: NAVY } }));
      para(" — " + mean).forEach((q, j, arr) => runs.push({ text: q.text, options: { ...q.options, breakLine: i < items.length - 1 && j === arr.length - 1 } }));
    });
    s.addText(runs, { x, y, w, h, fontFace: F, fontSize: size, color: INK, valign: "top", paraSpaceAfter: 4, margin: 0, isTextBox: true });
  }
  function stat(s, x, y, w, value, label, color = NAVY, size = 36) {
    s.addText(value, { x, y, w, h: 0.7, fontFace: F, fontSize: size, bold: true, color, margin: 0, isTextBox: true });
    s.addText(label, { x, y: y + 0.72, w, h: 0.6, fontFace: F, fontSize: 13, color: GREY, margin: 0, valign: "top", isTextBox: true });
  }
  function card(s, x, y, w, h, fill = CARD, title, tcolor = NAVY, edge = null) {
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: LINE, width: 0.75 },
      shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 4, offset: 1.5, angle: 90 } });
    if (edge) s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h, fill: { color: edge }, line: { color: edge } });
    if (title) s.addText(title, { x: x + 0.22, y: y + 0.1, w: w - 0.45, h: 0.38, fontFace: F, fontSize: 16, bold: true, color: tcolor, margin: 0, isTextBox: true });
  }
  function badge(s, x, y, n, color = TEAL, d = 0.5) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color } });
    s.addText(String(n), { x, y, w: d, h: d, fontFace: F, fontSize: d > 0.45 ? 16 : 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  }
  function table(s, header, rows, x, y, w, colW, o = {}) {
    const hd = header.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center", valign: "middle" } }));
    const cellText = (c) => { const t = String(c); return /\*\*|_\{|\^\{/.test(t) ? para(t) : t; };
    const body = rows.map((r, i) => r.map((c, j) => ({ text: cellText(c), options: {
      fill: { color: (o.hl && o.hl(i)) ? SOFT2 : (i % 2 ? "F7F6F2" : "FFFFFF") },
      align: (o.align && o.align[j]) || "left", valign: "middle", bold: !!(o.hl && o.hl(i)) } })));
    s.addTable([hd, ...body], { x, y, w, colW, fontFace: F, fontSize: o.size || 13, color: INK,
      border: { type: "solid", pt: 0.5, color: LINE }, rowH: o.rowH || 0.36, margin: [2, 6, 2, 6] });
  }
  const CW = 0.0059;                                         // inch / (pt · ký tự), Times New Roman, chữ có dấu
  const plain = (t) => String(t).replace(/\*\*|_\{|\^\{|\}/g, "");
  function tb(s, header, rows, x, y, w, colW, o = {}) {      // bảng có chiều cao dòng ước lượng theo độ dài chữ; trả về đáy dự kiến
    const size = o.size || 13, lh = size * 1.22 / 72, minH = o.minH || 0.38;
    const hs = rows.map((r) => Math.max(minH, 0.14 + lh * Math.max(...r.map((c, j) => Math.ceil(plain(c).length * CW * size / Math.max(0.5, colW[j] - 0.2))))));
    const hh = o.hdrH || 0.4;
    table(s, header, rows, x, y, w, colW, { ...o, rowH: [hh, ...hs] });
    return y + hh + hs.reduce((a, b) => a + b, 0);
  }
  function callout(s, t, y = 6.0, h = 0.82, fill = NAVY, color = "FFFFFF", size = 15) {
    s.addShape(pres.shapes.RECTANGLE, { x: MX, y, w: W, h, fill: { color: fill }, line: { color: fill } });
    s.addText(para(t), { x: MX + 0.3, y, w: W - 0.6, h, fontFace: F, fontSize: size, color, valign: "middle", margin: 0, isTextBox: true });
  }
  function fcard(s, file, x, y, w, h) {                      // thẻ công thức: ảnh công thức trong khung kem
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: CARD }, line: { color: LINE, width: 0.75 },
      shadow: { type: "outer", color: "000000", opacity: 0.1, blur: 4, offset: 1.5, angle: 90 } });
    return img(s, as(file), x + 0.25, y + 0.18, w - 0.5, h - 0.36, "left", file);
  }
  const head = (s, t, x, y, w, size = 15) => s.addText(t, { x, y, w, h: 0.35, fontFace: F, fontSize: size, bold: true, color: NAVY, margin: 0, isTextBox: true });
  function chartBase() {
    return { catAxisLabelFontSize: 13, catAxisLabelColor: INK, catAxisLabelFontFace: F, valAxisLabelFontSize: 12, valAxisLabelColor: GREY, valAxisLabelFontFace: F,
      valGridLine: { color: "E3E0D8", size: 0.5 }, catGridLine: { style: "none" }, dataLabelFontFace: F, dataLabelFontSize: 12, dataLabelColor: INK,
      legendFontFace: F, legendFontSize: 12, legendColor: INK, titleFontFace: F, titleColor: NAVY, titleFontSize: 14 };
  }

  // Slide thuật toán: công thức + chú thích ký hiệu (trên); "vì sao chọn" và "vì sao các con số" (dưới).
  //   o.formula: tên ảnh fm_*; o.fh: cao thẻ công thức; o.syms: [[ký hiệu, nghĩa]]; o.why: [mục]; o.nums: [[số, loại, vì sao]];
  //   o.symSize / o.whySize / o.numSize: cỡ chữ; o.extra(s, y): vẽ thêm ở dải dưới
  function algoSlide(kicker, title, o, notes) {
    const s = slide(kicker, title, notes);
    const fy = 1.4, fh = o.fh || 2.55, fw = o.fw || 6.9;
    fcard(s, o.formula, MX, fy, fw, fh);
    const ax = MX + fw + 0.3, aw = SW - MX - ax;
    s.addText("Chú thích ký hiệu", { x: ax, y: fy - 0.02, w: aw, h: 0.33, fontFace: F, fontSize: 15, bold: true, color: TEAL, margin: 0, isTextBox: true });
    ann(s, o.syms, ax, fy + 0.34, aw, fh - 0.3, o.symSize || 13);
    let by = fy + fh + 0.15;
    if (o.ex || o.exDraw) {                                 // dải ví dụ số (một dòng chữ) hoặc hình tự vẽ
      const eh = o.exH || 0.62;
      s.addShape(pres.shapes.RECTANGLE, { x: MX, y: by, w: W, h: eh, fill: { color: "FFF8E1" }, line: { color: GOLD, width: 1 } });
      if (o.exDraw) o.exDraw(s, by, eh);
      else s.addText(para(o.ex), { x: MX + 0.2, y: by, w: W - 0.4, h: eh, fontFace: F, fontSize: o.exSize || 13.5, color: INK, valign: "middle", margin: 0, isTextBox: true });
      by += eh + 0.15;
    }
    const bh = 6.9 - by;
    const lw = o.leftW || 5.55;
    card(s, MX, by, lw, bh, SOFT, o.whyTitle || "Vì sao chọn cách này", TEAL, TEAL);
    const wsz = o.whySize || 12.5;
    bullets(s, o.why, MX + 0.22, by + 0.5, lw - 0.4, bh - 0.55, wsz, INK, 4);
    const rx = MX + lw + 0.25, rw = W - lw - 0.25;
    card(s, rx, by, rw, bh, SOFT2, o.numTitle || "Vì sao các con số này", RUST, RUST);
    const bot = tb(s, ["Con số", "Loại", "Nguồn gốc"], o.nums, rx + 0.18, by + 0.5, rw - 0.36, o.numCols || [1.7, 0.8, rw - 0.36 - 2.5], { size: o.numSize || 10.5, minH: 0.27, hdrH: 0.3 });
    if (bot > 6.88) warnings.push(`BẢNG SỐ TRÀN (${bot.toFixed(2)}): ${title}`);
    let hw = 0;                                                  // ước lượng chiều cao các gạch đầu dòng
    o.why.forEach((t) => { hw += Math.ceil(plain(t).length * CW * wsz / (lw - 0.4 - 0.3)) * wsz * 1.22 / 72 + 4 / 72; });
    if (by + 0.5 + hw > 6.88) warnings.push(`LÝ DO TRÀN (${(by + 0.5 + hw).toFixed(2)}): ${title}`);
    return s;
  }

  return { pres, THEME, ROOT, B, D, E, DS, TMP, SW, SH, MX, W, F, INK, NAVY, TEAL, RUST, GREY, GOLD, LINE, SOFT, SOFT2, CARD, CHAPTERS,
    vn, vnd, pct, tr, dI, dA, slide, divider, img, as, para, bullets, text, ann, stat, card, badge, table, tb, callout, fcard, head, chartBase, algoSlide,
    warnings, setChapter: (i) => { curChap = i; curSection = CHAPTERS[i]; pres.addSection({ title: CHAPTERS[i] }); } };
};
