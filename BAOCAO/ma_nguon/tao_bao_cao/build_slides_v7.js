// BAOCAO/Slide_HUIM_IPS_V7.pptx — bài thuyết trình HUIM-IPS V7 (từ 6,87 m xuống 6,309 m trên UJIIndoorLoc).
// Giữ thiết kế của Slide_HUIM_IPS_UJIIndoorLoc.pptx: Times New Roman, nền navy cho bìa/chương, thanh chương ở chân slide,
// thẻ teal/rust, công thức là ảnh mathtext (make_slide_v7_assets.py). Mọi số liệu đọc từ BAOCAO/so_lieu_V7/du_lieu_bao_cao_V7.json.
// Chạy: node src/baocao/build_slides_v7.js   (cần npm "pptxgenjs"; Python có matplotlib, pandas)
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const B = path.join(ROOT, "BAOCAO");
const D = JSON.parse(fs.readFileSync(path.join(B, "so_lieu_V7", "du_lieu_bao_cao_V7.json"), "utf8"));
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "slide_v7_"));
execFileSync("python", [path.join(__dirname, "make_slide_v7_assets.py"), TMP], { env: { ...process.env, PYTHONIOENCODING: "utf-8" } });

// ------------------------------------------------------------------ theme (như slide cũ)
const THEME = {
  name: "HUIM IPS V7", headFontFace: "Times New Roman", bodyFontFace: "Times New Roman",
  colors: { dk1: "1B2A3D", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F6F4EF", accent1: "2A7F8F", accent2: "B5532A",
            accent3: "8A8A85", accent4: "C9A227", accent5: "4C6A88", accent6: "9BB7C4", hlink: "2A7F8F", folHlink: "4C6A88" },
};
const K = THEME.colors;
const INK = K.dk1, NAVY = K.dk2, TEAL = K.accent1, RUST = K.accent2, GREY = K.accent3, GOLD = K.accent4;
const LINE = "D8D3C8", SOFT = "E6F0F2", SOFT2 = "F7EAE3", CARD = "FBFAF7";
const F = "Times New Roman";

const vn = (x, k = 2) => {                            // dấu phẩy thập phân; khoảng trắng chỉ nhóm phần nguyên
  const [i, f] = Number(x).toFixed(k).split(".");
  return i.replace(/\B(?=(\d{3})+(?!\d))/g, " ") + (f ? "," + f : "");
};
const vnd = (x, k = 2) => (x > 0 ? "+" : x < 0 ? "−" : "") + vn(Math.abs(x), k);
const pct = (x, k = 1) => vn(100 * x, k) + "%";
const tr = (m) => D.test.find((r) => r.model === m);
const dI = (m) => D.dev_inf.find((r) => r.model === m);
const dA = (m) => D.dev_all.find((r) => r.model === m);
const TJ = D.test_json, EX = D.example, C1 = EX.cell1, HX = C1.hui_example, VF = D.verif, TOY = D.toy;
const T7 = tr("C_rel_absL3"), T6 = tr("V6"), T6r = tr("V6r");
const FIN = TJ.C_rel_absL3;
const HC = D.config.hui.final_hui_counts;
const nHUI6 = HC.rank + HC.rank_L3 + HC.abs, nHUI7 = nHUI6 + HC.rel + HC.abs_L3;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13,33 × 7,5 in
pres.theme = { headFontFace: F, bodyFontFace: F };
pres.title = "HUIM-IPS V7: tối ưu sai số định vị bằng bằng chứng HUI";
pres.subject = "Thuật toán, thực nghiệm và kiểm chứng của HUIM-IPS V7 trên UJIIndoorLoc";
const SW = 13.333, SH = 7.5, MX = 0.6;
const CHAPTERS = ["Mở đầu", "Lý thuyết", "Thuật toán V7", "Kết quả", "Kiểm chứng", "Kết luận"];

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

// ------------------------------------------------------------------ helpers
let curChap = -1, curSection = "Giới thiệu";
function tracker(s) {
  const w = 1.75;
  CHAPTERS.forEach((c, i) => {
    const x = MX + i * (w + 0.08), on = i === curChap;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 7.1, w, h: 0.05, fill: { color: on ? TEAL : "E3E0D8" }, line: { color: on ? TEAL : "E3E0D8" } });
    s.addText(`${i + 1}. ${c}`, { x, y: 7.15, w, h: 0.25, fontFace: F, fontSize: 9.5, color: on ? NAVY : GREY, bold: on, margin: 0, isTextBox: true });
  });
}
function slide(kicker, title, notes) {
  if (title.length > 62) console.warn("TIÊU ĐỀ DÀI:", title.length, title);
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
  s.addText(title, { x: MX, y: 3.0, w: 9.5, h: 1.0, fontFace: F, fontSize: 38, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.15, w: 2.6, h: 0, line: { color: GOLD, width: 2 } });
  s.addText(items.map((t, k) => ({ text: t, options: { breakLine: k < items.length - 1 } })),
    { x: MX, y: 4.35, w: 9, h: 2.4, fontFace: F, fontSize: 18, color: "DCE6EE", valign: "top", paraSpaceAfter: 6, margin: 0, isTextBox: true });
  if (notes) s.addNotes(notes);
  return s;
}
function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function img(s, file, x, y, w, h, align = "center", name) {
  const [pw, ph] = pngSize(file);
  let W = w, H = w * ph / pw;
  if (H > h) { H = h; W = h * pw / ph; }
  const X = align === "left" ? x : align === "right" ? x + w - W : x + (w - W) / 2;
  s.addImage({ path: file, x: X, y, w: W, h: H, altText: name || path.basename(file) });
  return { x: X, y, w: W, h: H };
}
const as = (f) => path.join(TMP, f + ".png");
function para(text) {
  return text.split(/(\*\*[^*]+\*\*|_\{[^}]*\}|\^\{[^}]*\})/).filter(Boolean).map((p) =>
    p.startsWith("**") ? { text: p.slice(2, -2), options: { bold: true } }
      : p.startsWith("_{") ? { text: p.slice(2, -1), options: { subscript: true } }
      : p.startsWith("^{") ? { text: p.slice(2, -1), options: { superscript: true } }
      : { text: p, options: {} });
}
function bullets(s, items, x, y, w, h, size = 16, color = INK, gap = 8) {
  const runs = [];
  items.forEach((t, i) => {
    const r = para(t).map((q) => ({ text: q.text, options: { ...q.options, bullet: { indent: 18 }, align: "left", paraSpaceAfter: gap } }));
    if (i < items.length - 1) r[r.length - 1].options.breakLine = true;
    runs.push(...r);
  });
  s.addText(runs, { x, y, w, h, fontFace: F, fontSize: size, color, valign: "top", margin: 2, isTextBox: true });
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(para(t), { x, y, w, h, fontFace: F, fontSize: 16, color: INK, valign: "top", margin: 0, isTextBox: true, ...o });
}
function ann(s, items, x, y, w, h, size = 14) {            // chú thích ký hiệu: **ký hiệu** — ý nghĩa
  const runs = [];
  items.forEach(([sym, mean], i) => {
    para(sym).forEach((q) => runs.push({ text: q.text, options: { ...q.options, bold: true, color: NAVY } }));
    para(" — " + mean).forEach((q, j, arr) => runs.push({ text: q.text, options: { ...q.options, breakLine: i < items.length - 1 && j === arr.length - 1 } }));
  });
  s.addText(runs, { x, y, w, h, fontFace: F, fontSize: size, color: INK, valign: "top", paraSpaceAfter: 5, margin: 0, isTextBox: true });
}
function stat(s, x, y, w, value, label, color = NAVY, size = 40) {
  s.addText(value, { x, y, w, h: 0.8, fontFace: F, fontSize: size, bold: true, color, margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.82, w, h: 0.6, fontFace: F, fontSize: 13.5, color: GREY, margin: 0, valign: "top", isTextBox: true });
}
function card(s, x, y, w, h, fill = CARD, title, tcolor = NAVY, edge = null) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: LINE, width: 0.75 },
    shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 4, offset: 1.5, angle: 90 } });
  if (edge) s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h, fill: { color: edge }, line: { color: edge } });
  if (title) s.addText(title, { x: x + 0.25, y: y + 0.12, w: w - 0.5, h: 0.42, fontFace: F, fontSize: 17, bold: true, color: tcolor, margin: 0, isTextBox: true });
}
function badge(s, x, y, n, color = TEAL, d = 0.5) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color } });
  s.addText(String(n), { x, y, w: d, h: d, fontFace: F, fontSize: d > 0.45 ? 16 : 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function table(s, header, rows, x, y, w, colW, o = {}) {
  const hd = header.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center", valign: "middle" } }));
  const cellText = (c) => { const t = String(c); return /\*\*|_\{|\^\{/.test(t) ? para(t) : t; };    // **đậm**, _{dưới}, ^{trên} trong ô bảng
  const body = rows.map((r, i) => r.map((c, j) => ({ text: cellText(c), options: {
    fill: { color: (o.hl && o.hl(i)) ? SOFT2 : (i % 2 ? "F7F6F2" : "FFFFFF") },
    align: (o.align && o.align[j]) || "left", valign: "middle", bold: !!(o.hl && o.hl(i)) } })));
  s.addTable([hd, ...body], { x, y, w, colW, fontFace: F, fontSize: o.size || 13, color: INK,
    border: { type: "solid", pt: 0.5, color: LINE }, rowH: o.rowH || 0.36, margin: [2, 6, 2, 6] });
}
function callout(s, t, y = 6.0, h = 0.82, fill = NAVY, color = "FFFFFF", size = 16) {
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y, w: SW - 2 * MX, h, fill: { color: fill }, line: { color: fill } });
  s.addText(para(t), { x: MX + 0.3, y, w: SW - 2 * MX - 0.6, h, fontFace: F, fontSize: size, color, valign: "middle", margin: 0, isTextBox: true });
}
function fcard(s, file, x, y, w, h) {                       // thẻ công thức: ảnh công thức trong khung kem
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: CARD }, line: { color: LINE, width: 0.75 },
    shadow: { type: "outer", color: "000000", opacity: 0.1, blur: 4, offset: 1.5, angle: 90 } });
  return img(s, as(file), x + 0.25, y + 0.2, w - 0.5, h - 0.4, "left", file);
}
function formulaSlide(kicker, title, file, syms, o = {}) {
  const s = slide(kicker, title, o.notes);
  const fw = o.fw || 7.4, fh = o.fh || 4.2, fy = o.fy || 1.5;
  fcard(s, file, MX, fy, fw, fh);
  const ax = MX + fw + 0.3;
  s.addText("Chú thích ký hiệu", { x: ax, y: fy, w: SW - MX - ax, h: 0.35, fontFace: F, fontSize: 16, bold: true, color: TEAL, margin: 0, isTextBox: true });
  ann(s, syms, ax, fy + 0.4, SW - MX - ax, fh - 0.4, o.size || 14);
  if (o.callout) callout(s, o.callout, o.cy || 5.95, o.ch || 0.9, o.cfill || NAVY, o.ccolor || "FFFFFF", o.csize || 15);
  return s;
}
function chartBase() {
  return { catAxisLabelFontSize: 13, catAxisLabelColor: INK, catAxisLabelFontFace: F, valAxisLabelFontSize: 12, valAxisLabelColor: GREY, valAxisLabelFontFace: F,
    valGridLine: { color: "E3E0D8", size: 0.5 }, catGridLine: { style: "none" }, dataLabelFontFace: F, dataLabelFontSize: 12, dataLabelColor: INK,
    legendFontFace: F, legendFontSize: 12, legendColor: INK, titleFontFace: F, titleColor: NAVY, titleFontSize: 14 };
}

// ================================================================== 1. bìa
pres.addSection({ title: "Giới thiệu" });
{
  const s = pres.addSlide({ masterName: "TOI", sectionTitle: "Giới thiệu" });
  s.background = { path: as("art_title") };
  s.addText("HUIM-IPS · PHIÊN BẢN V7", { x: MX, y: 0.7, w: 8, h: 0.4, fontFace: F, fontSize: 15, bold: true, color: "9BC4CD", charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Tối ưu sai số định vị trong nhà bằng bằng chứng HUI", { x: MX, y: 1.3, w: 7.5, h: 2.3, fontFace: F, fontSize: 40, bold: true, color: "FFFFFF", valign: "top", margin: 0, isTextBox: true });
  s.addText(`Từ ${vn(T6.mean)} m (V6) xuống ${vn(T7.mean, 3)} m trên tập kiểm tra UJIIndoorLoc`, { x: MX, y: 3.65, w: 7.5, h: 0.5, fontFace: F, fontSize: 22, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.35, w: 2.6, h: 0, line: { color: GOLD, width: 2.5 } });
  s.addText("Khai thác tập mục lợi ích cao (EFIM) làm lõi định vị — không k-NN, không lưu vân tay huấn luyện", { x: MX, y: 4.5, w: 7.5, h: 0.9, fontFace: F, fontSize: 19, italic: true, color: "DCE6EE", margin: 0, valign: "top", isTextBox: true });
  s.addText([
    { text: "Học viên: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Người hướng dẫn khoa học: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Năm 2026", options: {} },
  ], { x: MX, y: 5.6, w: 7, h: 1.3, fontFace: F, fontSize: 16, color: "FFFFFF", paraSpaceAfter: 4, margin: 0, isTextBox: true });
  s.addText("Nền: bản đồ điểm khảo sát UJIIndoorLoc; chấm màu là vân tay kiểm tra theo sai số V7", { x: 7.5, y: 7.0, w: 5.5, h: 0.3,
    fontFace: F, fontSize: 10, italic: true, color: "9BB7C4", align: "right", margin: 0, isTextBox: true });
  s.addNotes("V7 giữ nguyên lõi HUIM của V6 (EFIM theo ô, tầng và 30 ô ứng viên từ bằng chứng HUI) và thay cách chấm điểm và kết hợp các ô bằng một bộ chấm điểm học trực tiếp từ sai số tọa độ. Kết quả trên tập kiểm tra là 6,309 m; mục tiêu dưới 6 m chưa đạt.");
}

// ================================================================== 2. nội dung
{
  const s = slide("Nội dung", "Nội dung trình bày");
  const d = [["Mở đầu", "Bài toán, dữ liệu, mục tiêu dưới 6 m và mười nguyên tắc không được vi phạm"],
    ["Lý thuyết", "Vân tay Wi-Fi, HUIM, EFIM, từ vân tay tới HUI, chấm điểm khớp, tầng, V6; mỗi khái niệm có ví dụ số"],
    ["Thuật toán V7", "Chẩn đoán V6, các bước tới 6,309 m, ví dụ một vân tay thật tính tay, V7-A đến V7-D"],
    ["Kết quả", "Dev và test, khoảng tin cậy, cắt bỏ thành phần, tầng, điện thoại, chi phí"],
    ["Kiểm chứng", "6,309 m có chính xác không: Excel, Python, 16 phép kiểm, rò rỉ và tái lập"],
    ["Kết luận", "Đạt gì, chưa đạt gì, hạn chế; slide ghi nhớ cho người mới học HUIM trong IPS"]];
  const w = (SW - 2 * MX - 2 * 0.25) / 3;
  d.forEach(([t, s2], i) => {
    const x = MX + (i % 3) * (w + 0.25), y = 1.55 + Math.floor(i / 3) * 2.7;
    card(s, x, y, w, 2.5, i % 2 ? CARD : SOFT, null, NAVY, TEAL);
    s.addText(String(i + 1).padStart(2, "0"), { x: x + 0.3, y: y + 0.12, w: 1.3, h: 0.8, fontFace: F, fontSize: 38, bold: true, color: TEAL, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 1.55, y: y + 0.25, w: w - 1.8, h: 0.6, fontFace: F, fontSize: 21, bold: true, color: NAVY, margin: 0, valign: "middle", isTextBox: true });
    s.addText(s2, { x: x + 0.3, y: y + 1.05, w: w - 0.55, h: 1.35, fontFace: F, fontSize: 15, color: INK, margin: 0, valign: "top", isTextBox: true });
  });
}

// ================================================================== CHƯƠNG 1
divider(0, "Mở đầu", ["Bài toán và dữ liệu", "Mục tiêu và mười nguyên tắc không được vi phạm"]);
{
  const s = slide("Mở đầu · V7 trong một trang", `V7 giảm sai số còn ${vn(T7.mean, 3)} m, chưa đạt mục tiêu dưới 6 m`,
    "Tóm tắt điều hành: V7 giữ lõi HUIM của V6 và đổi cách chấm điểm các ô ứng viên. Trên tập kiểm tra giảm 0,557 m (8,1%). Mục tiêu dưới 6 m chưa đạt; báo cáo nêu rõ.");
  stat(s, MX, 1.55, 3.7, `${vn(T7.mean, 3)} m`, `sai số trung bình trên validationData (1 111 vân tay); V6: ${vn(T6.mean, 3)} m`, TEAL, 46);
  stat(s, MX, 3.2, 3.7, `${vnd(T7.diff_vs_V6, 3)} m`, `so với V6 (${vnd(T7.pct_vs_ref, 1)}%); KTC 95% [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}]`, NAVY, 40);
  stat(s, MX, 4.75, 3.7, `${vn(dI("C_rel_absL3").mean, 3)} m`, `dev out-of-fold, vân tay có thông tin (V6*: ${vn(dI("V6*").mean, 3)} m)`, NAVY, 40);
  const x = MX + 4.2, w = SW - MX - x;
  card(s, x, 1.55, w, 3.55, CARD, "V7 làm gì khác V6", NAVY, TEAL);
  bullets(s, ["Giữ nguyên: EFIM theo ô, điểm khớp HUI, chọn tầng, 30 ô ứng viên",
    "Đổi: một bộ chấm điểm dùng chung học **trực tiếp** trọng số của 30 ô, huấn luyện bằng chính **sai số tọa độ** (mét)",
    "Thêm hai góc nhìn HUI: lợi ích **rel** và **(AP, mức) abs**: 12,90 triệu HUI (V6: 7,33 triệu)",
    "Tính tọa độ bằng float64; báo cáo cả vân tay không có AP"], x + 0.3, 2.15, w - 0.6, 2.9, 15.5);
  card(s, x, 5.3, w, 1.5, SOFT2, null, RUST, RUST);
  text(s, `**Trung thực:** mục tiêu dưới 6 m **chưa đạt** (${vn(T7.mean, 3)} m). Test khó hơn dev khoảng 0,6 m ở mọi phiên bản. V7-A không bền; V7-D trung tính. Kiểm chứng độc lập: **${D.verification.n_checks}/${D.verification.n_checks}** phép đạt.`, x + 0.3, 5.45, w - 0.6, 1.25, { fontSize: 15.5 });
}
{
  const s = slide("Mở đầu · Bài toán", "Định vị trong nhà bằng vân tay Wi-Fi trên UJIIndoorLoc",
    "Điện thoại đo cường độ tín hiệu (RSSI) của các điểm truy cập (AP) xung quanh, tạo thành vân tay. Biết vân tay thì suy ra vị trí. UJIIndoorLoc có 3 tòa, 13 tầng, 520 AP.");
  bullets(s, ["**Vân tay:** vector 520 giá trị RSSI (dBm); 100 nghĩa là không nghe thấy AP đó",
    "**UJIIndoorLoc:** 3 tòa, 13 tầng; 19 937 vân tay huấn luyện (16 điện thoại), 1 111 vân tay kiểm tra (11 điện thoại, 9 chưa từng thấy)",
    "**Điểm tham chiếu = ô:** 933 ô, mỗi ô là một vị trí huấn luyện",
    "**Đo lường:** sai số là khoảng cách Euclid theo mét thực địa; kiểm tra chỉ được chấm một lần mỗi biến thể",
    "**Mục tiêu V7:** sai số trung bình dưới 6,00 m (tốt hơn nếu 5,5–5,8 m); không k-NN"], MX, 1.55, 6.9, 5.2, 16);
  const vals = [["V4", tr("V4").mean], ["V5", tr("V5").mean], ["V6", T6.mean], ["V7", T7.mean]];
  s.addChart(pres.charts.BAR, [{ name: "Sai số trung bình (m)", labels: vals.map((v) => v[0]), values: vals.map((v) => Math.round(v[1] * 1000) / 1000) }], {
    ...chartBase(), x: 7.8, y: 1.5, w: 4.9, h: 4.6, barDir: "col", chartColors: [GREY, GREY, NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 14,
    valAxisMinVal: 0, valAxisMaxVal: 9, valAxisMajorUnit: 1, showLegend: false, showTitle: true, title: "Sai số trung bình trên validationData (m)", barGapWidthPct: 55,
    invertedColors: [GREY, GREY, NAVY, TEAL] });
  text(s, "Mục tiêu: dưới **6,00 m**", 7.8, 6.2, 4.9, 0.5, { fontSize: 16, color: RUST, align: "center" });
}
{
  const s = slide("Mở đầu · Ràng buộc", "Mười nguyên tắc không được vi phạm và cách kiểm chứng",
    "Mười nguyên tắc từ đề bài. Mỗi nguyên tắc có bằng chứng kiểm tra được trong mã hoặc kết quả.");
  const rows = [
    ["1. HUIM là thành phần cốt lõi", "EFIM tạo HUI; ô ứng viên, tầng và mọi đặc trưng từ HUI (hàm compute)"],
    ["2. EFIM khai thác chính xác", "85 test EFIM = vét cạn + 1 test trên giao dịch ô thật; số HUI 12 mô hình khớp V6"],
    ["3. Tòa, tầng, ô từ bằng chứng HUI", "tầng = floor_of(S); 30 ô = top-30 điểm HUI của tầng"],
    ["4. Không k-NN / WKNN", "quét cú pháp 9 mô-đun suy luận: không KNeighbors, KDTree, cdist (T12)"],
    ["5. Không mô hình độc lập trên RSSI thô", "bộ chấm điểm chỉ nhận cột đặc trưng sinh từ HUI"],
    ["6. Mô hình phụ chỉ nhận đặc trưng HUI", "49 cột: điểm khớp, độ phủ, hạng, hồ sơ cường độ suy ra từ HUI"],
    ["7. Không lưu vân tay huấn luyện", "mô hình chỉ gồm HUI (tập mục, u, support) và vị trí/tầng của ô"],
    ["8. Không rò rỉ train/dev/test", "fold theo PHONEID; cache có SHA-256; kiểm tra lồng nhau −0,0035 m"],
    ["9. Không chỉnh số liệu", "sai số tính lại độc lập bằng Excel, Python, verify_v7 (T1)"],
    ["10. Giữ V6 chạy lại được", "git diff so với điểm gốc rỗng trên mã/kết quả V6 (T9)"]];
  table(s, ["Nguyên tắc", "Bằng chứng trong V7"], rows, MX, 1.5, SW - 2 * MX, [4.3, SW - 2 * MX - 4.3], { size: 13.5, rowH: 0.49 });
}

// ================================================================== CHƯƠNG 2
divider(1, "Cơ sở lý thuyết", ["Vân tay Wi-Fi và đơn vị đo", "HUIM và EFIM, có ví dụ tính tay", "Từ vân tay tới HUI; chấm điểm khớp; tầng; V6"]);
{
  const s = slide("Lý thuyết · Vân tay Wi-Fi", "Vân tay Wi-Fi: mỗi vị trí có một mẫu cường độ tín hiệu",
    "Pha huấn luyện thu vân tay tại các điểm tham chiếu; pha định vị nhận một vân tay mới và suy ra vị trí. Ví dụ minh họa dùng hàng 335 của validationData: chỉ 10 trong 520 AP nghe thấy.");
  const bx = (x, y, w, h, t, sub, c) => {
    card(s, x, y, w, h, c === TEAL ? SOFT : SOFT2, null, c, c);
    s.addText(t, { x: x + 0.28, y: y + 0.1, w: w - 0.4, h: 0.4, fontFace: F, fontSize: 17, bold: true, color: c, margin: 0, isTextBox: true });
    s.addText(para(sub), { x: x + 0.28, y: y + 0.52, w: w - 0.45, h: h - 0.6, fontFace: F, fontSize: 14.5, color: INK, margin: 0, valign: "top", isTextBox: true });
  };
  bx(MX, 1.5, 5.95, 1.55, "Pha huấn luyện (offline)", "Đứng tại điểm tham chiếu, đo RSSI của mọi AP nghe được; lưu vân tay cùng vị trí. UJIIndoorLoc: 19 937 vân tay, 933 ô.", TEAL);
  bx(MX, 3.2, 5.95, 1.55, "Pha định vị (online)", "Điện thoại đo một vân tay mới T; hệ thống phải trả về (x̂, ŷ), tòa và tầng. **V7 không so khoảng cách với vân tay huấn luyện.**", RUST);
  text(s, "**Vân tay có thể thiếu AP:** 76 vân tay huấn luyện không nghe thấy AP nào; tập kiểm tra không có vân tay như vậy.", MX, 4.95, 5.95, 1.0, { fontSize: 15 });
  const hd = ["AP", "RSSI (dBm)"];
  const rows = EX.aps.map((a) => [`WAP${String(a.ap).padStart(3, "0")}`, a.rssi]);
  s.addText(`Ví dụ: hàng ${EX.src_row} của validationData, ${EX.n_ap} trong 520 AP`, { x: 7.0, y: 1.5, w: 5.7, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, hd, rows, 7.0, 1.95, 3.2, [1.7, 1.5], { size: 13, rowH: 0.36, align: ["left", "right"] });
  text(s, `Phần còn lại của 520 giá trị là 100 (không nghe thấy).\n\nAP mạnh nhất: WAP${String(EX.aps[0].ap).padStart(3, "0")}, WAP${String(EX.aps[1].ap).padStart(3, "0")} (${EX.aps[0].rssi} dBm).`, 10.45, 1.95, 2.3, 3.0, { fontSize: 14, color: GREY });
}
{
  const ex = D.example, ds = TJ;
  const s = slide("Lý thuyết · Dữ liệu và đơn vị", "Tọa độ Web-Mercator: mét thực địa = 0,766126 × đơn vị tọa độ",
    "UJIIndoorLoc lưu tọa độ trong hệ Web-Mercator; một đơn vị tọa độ ngắn hơn một mét thực địa ở vĩ độ này. Mọi sai số trong báo cáo đã nhân hệ số 0,766126.");
  fcard(s, "fm_err", MX, 1.5, 7.2, 1.7);
  ann(s, [["(x̂_{n}, ŷ_{n})", "tọa độ dự đoán của vân tay n"], ["(x_{n}, y_{n})", "tọa độ thật (chỉ dùng để đo lường)"], ["g = 0,766126", "mét thực địa trên một đơn vị tọa độ"], ["ē", "sai số trung bình; N = 1 111 vân tay kiểm tra"]],
    MX + 7.5, 1.5, SW - 2 * MX - 7.5, 1.9, 14);
  const dx = EX.v7.sum_dx, dy = EX.v7.sum_dy;
  card(s, MX, 3.45, SW - 2 * MX, 3.3, CARD, "Ví dụ số (hàng 335, V7)", NAVY, TEAL);
  bullets(s, [`x̂ − x = ${vn(dx, 5)} và ŷ − y = ${vn(dy, 5)} (đơn vị tọa độ)`,
    `khoảng cách = √(${vn(dx, 5)}² + ${vn(dy, 5)}²) = ${vn(Math.hypot(dx, dy), 5)} đơn vị tọa độ`,
    `sai số = ${vn(Math.hypot(dx, dy), 5)} × 0,766126 = **${vn(EX.v7.err_m, 4)} m**`,
    `Hệ số 0,766126 được kiểm bằng src/verify_coordinates.py; các tập dữ liệu khác dùng mét trực tiếp (hệ số 1)`], MX + 0.3, 4.05, SW - 2 * MX - 0.6, 2.6, 16);
}
{
  const s = formulaSlide("Lý thuyết · HUIM", "HUIM: khai thác tập mục có lợi ích tổng cao", "fm_hui", [
    ["D", "cơ sở dữ liệu giao dịch; T ∈ D là một giao dịch"],
    ["i, X", "mục (item); tập mục X ⊆ T"],
    ["q(i,T)", "lợi ích **nội**: số lượng của i trong T (ví dụ số lượng mua)"],
    ["p(i)", "lợi ích **ngoại**: giá trị một đơn vị của i (không đổi theo giao dịch)"],
    ["u(i,T)", "lợi ích của i trong T = q·p"],
    ["u(X)", "lợi ích của X: cộng trên mọi giao dịch chứa X"],
    ["minUtil", "ngưỡng lợi ích tối thiểu; X đạt ngưỡng là HUI"]],
    { fw: 6.9, fh: 3.9, callout: "**Khác khai thác tập phổ biến:** HUI quan tâm giá trị, không chỉ số lần xuất hiện. Vì u(X) **không đơn điệu** (thêm mục có thể tăng u), phải dùng chặn trên (TWU, lu, su) để cắt tỉa.",
      notes: "HUIM là mở rộng của khai thác tập phổ biến: mỗi mục có số lượng trong giao dịch và giá trị đơn vị. Một tập mục là HUI nếu tổng lợi ích của nó trên toàn bộ cơ sở dữ liệu không thấp hơn minUtil." });
}
{
  const s = slide("Lý thuyết · Ví dụ HUIM", "Ví dụ tính tay: tập xuất hiện nhiều chưa chắc là HUI",
    "Ví dụ chuẩn của tài liệu HUIM (5 giao dịch, 7 mục). u({a,c}) = 6+16+6 = 28 < 30: xuất hiện 3 lần nhưng không phải HUI. u({b,c,d,e}) = 20+20 = 40.");
  const names = "abcdefg".split("");
  const hdr = ["Giao dịch", ...names.map((n) => `${n} (p=${TOY.p[n]})`)];
  const rows = TOY.db.map((t, i) => [`T${i + 1}`, ...names.map((n) => (t[n] ? t[n] : "·"))]);
  table(s, hdr, rows, MX, 1.5, 6.3, [0.9, ...names.map(() => 0.77)], { size: 12.5, rowH: 0.4, align: ["center", ...names.map(() => "center")] });
  text(s, "Ô là số lượng q(i,T); p(i) là giá trị đơn vị ở tiêu đề cột. Lợi ích giao dịch TU = Σ q·p: " + TOY.tu.map((u, i) => `TU(T${i + 1}) = ${u}`).join(", ") + `; tổng = ${TOY.tu.reduce((a, b) => a + b, 0)}.`, MX, 4.05, 6.3, 1.2, { fontSize: 14, color: GREY });
  card(s, MX + 6.6, 1.5, SW - 2 * MX - 6.6, 2.2, CARD, "Tính tay u({a,c}) và u({b,c,d,e})", NAVY, TEAL);
  bullets(s, [`u({a,c}): T1 = 1·5+1·1 = ${TOY.u_ac_per_T[0]}; T2 = 2·5+6·1 = ${TOY.u_ac_per_T[1]}; T3 = 1·5+1·1 = ${TOY.u_ac_per_T[2]}; **tổng 28 < 30**`,
    `u({b,c,d,e}): T3 = ${TOY.u_bcde_per_T[2]}, T4 = ${TOY.u_bcde_per_T[3]}; **tổng 40**`], MX + 6.85, 2.05, SW - 2 * MX - 7.1, 1.6, 14);
  const hh = TOY.hui_30.map((h) => [`{${h.items.split("").join(",")}}`, vn(h.u, 0), h.support]);
  s.addText("Mọi HUI khi minUtil = 30 (EFIM = vét cạn)", { x: MX + 6.6, y: 3.85, w: 5.5, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Tập mục X", "u(X)", "Support"], hh, MX + 6.6, 4.25, 5.1, [2.6, 1.2, 1.3], { size: 13, rowH: 0.32, align: ["left", "right", "right"], hl: (i) => hh[i][0] === "{b,c,d,e}" });
  text(s, "Với minUtil = 40 chỉ còn {b,c,d,e} (u = 40).", MX, 5.5, 6.3, 0.5, { fontSize: 14.5, color: RUST });
}
{
  const s = slide("Lý thuyết · Từ vân tay tới giao dịch", "Một vân tay Wi-Fi là một giao dịch có lợi ích",
    "Ánh xạ: mỗi ô là một cơ sở dữ liệu giao dịch gồm các vân tay của ô đó; mỗi AP là một mục; cường độ tín hiệu quy về lợi ích nội q trong 1 đến 100; lợi ích ngoại bằng 1.");
  const rows = [["Cơ sở dữ liệu D", "các vân tay huấn luyện của **một ô** (trung bình 21,3 vân tay/ô)"],
    ["Giao dịch T", "một vân tay: các AP nghe được"],
    ["Mục i", "một AP (WAP001 … WAP520)"],
    ["Lợi ích nội q(i,T)", "cường độ của AP i trong vân tay T, quy về 1…100 (rank, abs hoặc rel)"],
    ["Lợi ích ngoại p(i)", "bằng 1 với mọi AP"],
    ["Tập mục X", "tổ hợp AP cùng mạnh trong một vân tay"],
    ["HUI của ô c", "mẫu AP cùng mạnh đặc trưng cho ô c (EFIM khai thác)"],
    ["minUtil_{c}", "θ × tổng lợi ích của ô, θ = 20%"]];
  table(s, ["Khái niệm HUIM", "Trong định vị Wi-Fi"], rows.map((r) => [r[0].replace("_{c}", "c"), r[1].replace(/\*\*/g, "")]), MX, 1.5, 7.3, [2.5, 4.8], { size: 13.5, rowH: 0.46 });
  card(s, MX + 7.6, 1.5, SW - 2 * MX - 7.6, 4.2, SOFT, "Ví dụ: vân tay hàng 335 thành giao dịch", NAVY, TEAL);
  const chips = EX.aps.map((a) => `WAP${String(a.ap).padStart(3, "0")}: ${a.q_rank}`).join("   ");
  text(s, "T = { " + chips + " }", MX + 7.85, 2.1, SW - 2 * MX - 8.1, 1.7, { fontSize: 15 });
  text(s, "Mỗi cặp là (AP : q theo thứ hạng). Giao dịch này được so với HUI của từng ô: **ô nào có các tổ hợp AP mạnh giống T thì điểm cao**.", MX + 7.85, 3.85, SW - 2 * MX - 8.1, 1.7, { fontSize: 15 });
  callout(s, "Mô hình định vị = tập HUI của mọi ô + vị trí ô. **Không còn vân tay huấn luyện nào trong mô hình.**", 6.0, 0.8, NAVY, "FFFFFF", 16);
}
{
  const s = slide("Lý thuyết · Lợi ích nội", "Ba cách quy RSSI về lợi ích nội q: rank, abs, rel",
    "rank dùng thứ hạng cường độ nên không đổi khi điện thoại lệch đều; rel đo so với AP mạnh nhất; abs dùng cường độ tuyệt đối nên chịu ảnh hưởng độ lệch của thiết bị. V6 dùng rank và abs; V7 thêm rel.");
  fcard(s, "fm_util3", MX, 1.5, 7.9, 2.55);
  ann(s, [["n_{T}, r_{T}(i)", "số AP nghe được và hạng của AP i (1 = mạnh nhất)"], ["L, H", "cận RSSI huấn luyện: −104 và 0 dBm"], ["W = 40", "cửa sổ 40 dB của lợi ích rel"], ["clip(·,0,1)", "cắt giá trị về [0, 1]"]],
    MX + 8.2, 1.5, SW - 2 * MX - 8.2, 2.55, 14);
  const sel = EX.aps.slice(0, 6);
  const rows = [["RSSI (dBm)", ...sel.map((a) => a.rssi)], ["q rank", ...sel.map((a) => a.q_rank)], ["q abs", ...sel.map((a) => a.q_abs)], ["q rel", ...sel.map((a) => a.q_rel)],
    ["abs nếu máy đọc thấp hơn 10 dB", ...sel.map((a) => a.q_abs_shift)], ["rank / rel nếu thấp hơn 10 dB", ...sel.map((a) => (a.q_rank_shift === a.q_rank && a.q_rel_shift === a.q_rel ? "không đổi" : "đổi"))]];
  s.addText("Ví dụ vân tay hàng 335 (6 AP mạnh nhất)", { x: MX, y: 4.2, w: 8, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["", ...sel.map((a) => `WAP${String(a.ap).padStart(3, "0")}`)], rows, MX, 4.6, SW - 2 * MX, [3.9, ...sel.map(() => (SW - 2 * MX - 3.9) / 6)], { size: 12.5, rowH: 0.3, align: ["left", ...sel.map(() => "center")] });
}
{
  const s = formulaSlide("Lý thuyết · EFIM", "EFIM: duyệt cây tập mục với hai chặn trên lu và su", "fm_efim", [
    ["TWU(X)", "tổng lợi ích các giao dịch chứa X; TWU < minUtil thì X và mọi tập chứa X không thể là HUI"],
    ["TU(T)", "tổng lợi ích của giao dịch T"],
    ["α, z", "tiền tố đang mở rộng và mục z định thêm vào"],
    ["re(α,T)", "lợi ích còn lại của T sau α (các mục xếp sau)"],
    ["lu(α,z)", "chặn trên cho mọi tập mở rộng từ α∪{z}: lu < minUtil thì loại z khỏi cây con"],
    ["su(α,z)", "chặn trên cho nhánh: su < minUtil thì không duyệt nhánh"]],
    { fw: 7.4, fh: 3.1, size: 13.5, callout: `**Ví dụ trên 5 giao dịch ở trước, minUtil = 40:** TWU(a)=${TOY.twu.a}, b=${TOY.twu.b}, c=${TOY.twu.c}, d=${TOY.twu.d}, e=${TOY.twu.e}, **f=${TOY.twu.f}, g=${TOY.twu.g}**. f và g có TWU < 40 nên bị loại ngay; còn {b,c,d,e} với u = 40 là HUI duy nhất.`,
      cy: 4.85, ch: 1.0, csize: 15,
      notes: "EFIM chiếu cơ sở dữ liệu và gộp giao dịch giống nhau, duyệt sâu và dùng hai chặn trên lu và su để cắt tỉa. Trong dự án EFIM được cài lại bằng Python và kiểm thử với thuật toán vét cạn." });
  const steps = ["Tính TWU, loại mục TWU < minUtil, sắp mục", "Chiếu CSDL và gộp giao dịch giống nhau", "Duyệt sâu; lu < minUtil → loại mục khỏi cây con", "su < minUtil → không duyệt nhánh", "Xuất mọi X có u(X) ≥ minUtil"];
  s.addText("Năm bước: " + steps.map((t, i) => `${i + 1}. ${t}`).join("   ·   "), { x: MX, y: 5.95, w: SW - 2 * MX, h: 0.9, fontFace: F, fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true });
}
{
  const s = formulaSlide("Lý thuyết · HUI theo ô", "Mỗi ô có một tập HUI riêng; tập HUI là mô hình", "fm_cell", [
    ["D_{c}", "các vân tay huấn luyện của ô c"],
    ["θ", "tỷ lệ ngưỡng: 20% tổng lợi ích của ô"],
    ["s(X)", "support: số vân tay của ô chứa X"],
    ["q̄_{c}(X)", "cường độ trung bình mỗi mục của X trong ô: u(X) / (s(X)·|X|)"],
    ["w(X)", "tỷ trọng của X trong lợi ích HUI của ô"]],
    { fw: 7.2, fh: 3.0, size: 14,
      callout: "**Tự nâng ngưỡng:** nếu một lần chạy vượt 10 s hoặc 10 000 HUI, nhân θ với 1,25 và chạy lại (θ thực dùng trung bình 34,5%); không bao giờ giữ tập HUI bị cắt cụt.", cy: 4.7, ch: 0.9, csize: 15,
      notes: "Mô hình định vị chỉ gồm HUI của từng ô (tập mục, lợi ích, support) và vị trí, tầng của ô." });
  card(s, MX, 5.75, SW - 2 * MX, 1.1, CARD, null, TEAL, TEAL);
  text(s, `**Ví dụ (ô 351, tầng 2_1):** ${vn(C1.n_huis, 0)} HUI, tổng lợi ích ${vn(C1.sum_u, 0)}, dùng ${C1.n_ap_in_Ic} trong 520 AP. Toàn mô hình rank: **${vn(HC.rank, 0)} HUI**; V6 (3 mô hình): ${vn(nHUI6, 0)}; V7 (5 mô hình): **${vn(nHUI7, 0)}**.`, MX + 0.3, 5.85, SW - 2 * MX - 0.6, 0.95, { fontSize: 15.5, valign: "middle" });
}
{
  const s = formulaSlide("Lý thuyết · Điểm khớp", "Chấm điểm khớp giữa truy vấn và HUI của từng ô", "fm_match", [
    ["ρ(X,T)", "tỷ lệ AP của X có mặt trong T (0…1)"],
    ["q_{T}(X)", "trung bình q(i,T) của các AP thuộc X ∩ T"],
    ["agree", "độ khớp cường độ: càng gần q̄ càng gần 1; τ = 20"],
    ["w(X)", "tỷ trọng của HUI X trong ô c"],
    ["P_{c}(T)", "điểm khớp mẫu (γ = 2)"],
    ["I_{c}", "mọi AP xuất hiện trong ít nhất một HUI của ô c"],
    ["V_{c}(T)", "độ phủ: phần cường độ của T được HUI của ô giải thích"],
    ["score", "P·V³ — hai điều kiện cùng phải đạt"]],
    { fw: 7.6, fh: 4.7, size: 13.5, fy: 1.5, callout: "P hỏi: \"vân tay chứa bao nhiêu mẫu mạnh của ô, đúng cường độ?\"  V hỏi: \"bao nhiêu phần của vân tay được ô giải thích?\"", cy: 6.3, ch: 0.6, csize: 14.5,
      notes: "Hai đại lượng bổ sung nhau: P đo mức chứa các mẫu đặc trưng của ô, V đo mức vân tay được ô giải thích. Điểm ô là tích P·V³." });
}
{
  const s = slide("Lý thuyết · Ví dụ tính điểm khớp", "Ví dụ tính tay P và V của ô 351 với vân tay hàng 335",
    "Một HUI đóng góp rất nhỏ (7,2·10⁻⁵); điểm P là tổng của 8 535 số hạng. Các con số được tính lại bằng mã và khớp với đặc trưng đã lưu.");
  const rows = [["X (WAP)", HX.items_ap.join(", ")], ["|X|, u(X), s(X)", `${HX.n}, ${vn(HX.u, 0)}, ${vn(HX.support, 0)}`], ["q̄ = u/(s·|X|)", `${vn(HX.u, 0)} / (${vn(HX.support, 0)}·${HX.n}) = ${vn(HX.q_bar, 2)}`],
    ["q của truy vấn trên X", HX.q_of_items.join(", ")], ["q_{T}(X) = trung bình", vn(HX.q_T, 4)], ["ρ = |X∩T|/|X|", `${HX.n_in_query}/${HX.n} = ${vn(HX.frac, 0)}`],
    ["agree = exp(−|q_{T} − q̄|/20)", `exp(−|${vn(HX.q_T, 2)} − ${vn(HX.q_bar, 2)}| / 20) = ${vn(HX.agree, 4)}`], ["w(X) = u(X)/Σu", `${vn(HX.u, 0)} / ${vn(C1.sum_u, 0)} = ${vn(HX.w * 1e4, 4)}·10^{-4}`.replace("^{-4}", "⁻⁴")],
    ["số hạng = w·ρ²·agree", `${vn(HX.term * 1e5, 2)}·10⁻⁵`]];
  s.addText("Một HUI của ô 351 (trong 8 535 HUI)", { x: MX, y: 1.45, w: 7.2, h: 0.35, fontFace: F, fontSize: 15.5, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Đại lượng", "Giá trị"], rows, MX, 1.85, 7.6, [3.2, 4.4], { size: 13, rowH: 0.4 });
  card(s, MX + 7.9, 1.5, SW - 2 * MX - 7.9, 4.95, SOFT, "Cộng lại cho cả ô", NAVY, TEAL);
  bullets(s, [`**P** = Σ trên 8 535 HUI = **${vn(C1.P, 4)}**`,
    `Σq của truy vấn = ${C1.q_sum}; AP ${C1.missing.map((a) => "WAP" + a).join(", ")} không thuộc I_{c}`.replace("_{c}", "c"),
    `**V** = (${C1.q_sum} − phần các AP vắng) / ${C1.q_sum} = **${vn(C1.V, 4)}**`,
    `P·V³ = ${vn(C1.P, 4)} × ${vn(C1.V, 4)}³ = **${vn(C1.S_raw, 4)}**`,
    `Sau làm mượt (σ = 3 m): S = **${vn(C1.S_smooth, 4)}**`], MX + 8.15, 2.1, SW - 2 * MX - 8.4, 4.3, 14.5);
}
{
  const s = slide("Lý thuyết · Làm mượt, tầng, ứng viên", "Làm mượt không gian, chọn tầng, 30 ô ứng viên và ước lượng V4",
    "Điểm của ô được trải sang các ô lân cận cùng tầng; tầng là tầng có 20 ô tốt nhất trung bình cao nhất; 30 ô tốt nhất của tầng là ứng viên; V4 lấy trung bình có trọng số S⁸ của 12 ô.");
  fcard(s, "fm_smooth", MX, 1.5, 7.6, 1.75);
  fcard(s, "fm_v4", MX, 3.4, 7.6, 1.1);
  ann(s, [["K(c′,c)", "nhân Gauss theo khoảng cách ô (σ = 3 m), chỉ cùng tầng, chuẩn hóa theo hàng"], ["f(T)", "tầng được chọn: trung bình S của 20 ô tốt nhất cao nhất"], ["a_{c}", "trọng số S⁸ của 12 ô tốt nhất (ước lượng V4)"]],
    MX + 7.9, 1.5, SW - 2 * MX - 7.9, 3.0, 14);
  const c = EX.cells[0];
  card(s, MX, 4.7, SW - 2 * MX, 2.15, CARD, "Ví dụ hàng 335", NAVY, TEAL);
  bullets(s, [`Tầng dự đoán **${EX.pred_bf}** = tầng thật (đúng). Ô có điểm cao nhất là ô **${c.cell}** (S = ${vn(c.S, 4)}) nhưng cách vị trí thật **${vn(c.dist_m, 2)} m**`,
    `30 ô ứng viên: có ô cách vị trí thật chỉ **${vn(Math.min(...EX.cells.map((q) => q.dist_m)), 2)} m** (ô ${EX.cells.reduce((a, b) => (a.dist_m < b.dist_m ? a : b)).cell}); ước lượng V4 sai **${vn(EX.v4_err_m, 2)} m**`], MX + 0.3, 5.3, SW - 2 * MX - 0.6, 1.5, 15);
}
{
  const s = formulaSlide("Lý thuyết · V6", "V6: bộ hồi quy dự đoán khoảng cách từng ô rồi đổi thành trọng số", "fm_v6", [
    ["φ_{c}", "33 đặc trưng HUI của ô ứng viên c (và dạng tương đối so với các ô khác)"],
    ["g", "Gradient Boosting (300 cây) dự đoán log(1+d), d = khoảng cách ô → vị trí thật"],
    ["d̂_{c}", "khoảng cách dự đoán của ô c"],
    ["λ = 2", "nhiệt độ cố định của trọng số"],
    ["top-20", "20 ô có d̂ nhỏ nhất"]],
    { fw: 7.2, fh: 3.4, size: 14, callout: `**Hạn chế của V6:** dự đoán khoảng cách từng ô tốt chưa bảo đảm tọa độ hợp nhất tốt; trọng số theo công thức cố định (m = 20, λ = 2). Với hàng 335, V6 sai **${vn(EX.v6.err_m, 2)} m**.`, cy: 5.2, ch: 0.95, csize: 15.5,
      notes: "Bước 8 của V6 chỉ nhận đặc trưng sinh ra từ HUI. Điểm yếu là mục tiêu huấn luyện (khoảng cách từng ô) không phải mục tiêu cuối (sai số tọa độ hợp nhất)." });
}

// ================================================================== CHƯƠNG 3
divider(2, "Thuật toán V7", ["Chẩn đoán V6: vì sao cần V7", "Các bước từ vân tay tới 6,309 m", "Ví dụ trọn vẹn một vân tay thật", "V7-A, V7-B, V7-C, V7-D và các thử nghiệm không giúp"]);
{
  const s = slide("V7 · Chẩn đoán", "Ứng viên đã đúng; sai số sinh ra khi xếp hạng và kết hợp",
    "Với 19 861 vân tay có thông tin, 30 ô ứng viên chứa ô cách vị trí thật dưới 3 m ở 92,4% truy vấn, nhưng tọa độ cuối của V6 chỉ dưới 3 m ở 37%. HUI không chọn sai vùng; khâu xếp hạng và kết hợp là điểm nghẽn.");
  const cd = D.cand_dev;
  const labels = ["dưới 3 m", "dưới 5 m", "dưới 10 m"];
  const nm = (r) => r.nguon.replace(" (điểm cao nhất)", "").replace(" (tiên tri)", " (tiên tri)").replace("(tọa độ hợp nhất)", "");
  const series = cd.map((r) => ({ name: nm(r).trim(), labels, values: [r.duoi_3m, r.duoi_5m, r.duoi_10m].map((v) => Math.round(v * 1000) / 10) }));
  s.addChart(pres.charts.BAR, series, { ...chartBase(), x: MX, y: 1.45, w: 8.0, h: 5.35, barDir: "col", barGrouping: "clustered", chartColors: [GREY, GOLD, NAVY, TEAL],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 11, valAxisMinVal: 0, valAxisMaxVal: 110, valAxisMajorUnit: 20, showLegend: true, legendPos: "b",
    showTitle: true, title: "% truy vấn có ô hoặc tọa độ cách vị trí thật dưới ngưỡng (dev)", barGapWidthPct: 40 });
  const x = MX + 8.3, w = SW - MX - x;
  stat(s, x, 1.55, w, `${vn(cd[1].mean_m)} m`, "ô gần nhất trong 30 ứng viên (tiên tri, dùng nhãn thật)", TEAL, 38);
  stat(s, x, 3.15, w, `${vn(cd[2].mean_m)} m`, "tọa độ hợp nhất của V6*", NAVY, 38);
  text(s, "→ V7 nhắm vào **cách chấm điểm và kết hợp ô**, không tìm thêm ứng viên.", x, 4.85, w, 1.5, { fontSize: 16, color: RUST });
}
{
  const dg = D.diag, em = dg.empty_fingerprints;
  const s = slide("V7 · Chẩn đoán", "Hai khiếm khuyết đo lường của V6 cần tách riêng",
    "76 vân tay huấn luyện không nghe thấy AP nào chiếm 10% tổng sai số dev; trọng số float32 nhân tọa độ cỡ 4,9 triệu tạo nhiễu 0,5–1 đơn vị tọa độ. V7 báo cáo hai cách tính và dùng float64.");
  card(s, MX, 1.55, 6.0, 4.1, SOFT2, "1. 76 vân tay không có AP nào", RUST, RUST);
  bullets(s, [`Mọi ô điểm 0, vị trí là kết quả **hòa điểm**; sai số trung bình **${vn(em.mean_err_v6, 1)} m**`,
    `Chiếm **${pct(em.share_of_dev_error_sum, 1)}** tổng sai số dev (điện thoại 1: 59, 22: 14, 13: 2, 6: 1)`,
    `Gộp vào: dev V6 = ${vn(dA("V6").mean, 3)} m; bỏ ra: **${vn(dI("V6").mean, 3)} m**`, "validationData có **0** vân tay như vậy → V7 báo cáo cả hai cách tính và chọn mô hình theo vân tay có thông tin"], MX + 0.3, 2.15, 5.5, 3.4, 14.5);
  card(s, MX + 6.3, 1.55, SW - 2 * MX - 6.3, 4.1, SOFT, "2. Nhiễu số học float32", TEAL, TEAL);
  bullets(s, ["Trọng số float32 có tổng lệch ~1e-7; nhân với tọa độ Web-Mercator ~4,9·10⁶", "→ tâm lệch **0,5–1 đơn vị tọa độ** (≈ 0,4–0,8 m) ở hầu hết truy vấn", `Ảnh hưởng lên trung bình nhỏ (${vn(dI("V6").mean, 4)} → ${vn(dI("V6*").mean, 4)} m) nhưng là sai sót thật`, "V7 tính **float64** và tọa độ **tương đối** so với ô số 1 (V6*: V6 sửa số học)"], MX + 6.6, 2.15, SW - 2 * MX - 6.9, 3.4, 14.5);
  callout(s, `Vì vậy mọi bảng dev có hai cột: **có thông tin (19 861)** dùng để chọn mô hình, và **tất cả (19 937)** để so với số tham chiếu của V6.`, 5.9, 0.9, NAVY, "FFFFFF", 15.5);
}
{
  const s = slide("V7 · Tổng quan", "Sơ đồ V7: tám bước từ vân tay tới tọa độ",
    "Teal là phần giữ nguyên từ V6, rust là phần mới của V7. Bước 1 đến 3 là HUIM như V6; bước 4 đến 8 là bằng chứng HUI và bộ chấm điểm học trực tiếp.");
  const box = (x, y, w, h, n, t, sub, c) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: c === TEAL ? "E6F0F2" : "F7EAE3" }, line: { color: c, width: 1.25 } });
    s.addText(`Bước ${n}`, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.3, fontFace: F, fontSize: 13, bold: true, color: c, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.15, y: y + 0.4, w: w - 0.3, h: 0.5, fontFace: F, fontSize: 14.5, bold: true, color: INK, margin: 0, valign: "top", isTextBox: true });
    s.addText(para(sub), { x: x + 0.15, y: y + 0.95, w: w - 0.3, h: h - 1.0, fontFace: F, fontSize: 13, color: INK, margin: 0, valign: "top", isTextBox: true });
  };
  const w = 2.75, g = 0.37, xs = [0, 1, 2, 3].map((i) => MX + i * (w + g));
  const r1 = [["1", "EFIM theo ô, 5 góc nhìn", "rank, rank-L3, abs (V6) + **rel, abs-L3 (V7)**: 12,9 triệu HUI", RUST], ["2", "Điểm khớp HUI → tầng", "P·V³, làm mượt σ = 3 m; tầng theo 20 ô tốt nhất", TEAL],
    ["3", "30 ô ứng viên", "30 ô điểm cao nhất của tầng đã chọn", TEAL], ["4", "Đặc trưng bằng chứng HUI", "33 cột V6 + 8 cột mỗi mô hình mới = **49 cột**", RUST]];
  const r2 = [["5", "Đặc trưng tương đối", "x−max, min-max, hạng; log có dấu; z-score", RUST], ["6", "Bộ chấm điểm dùng chung", "MLP 32/16 + nhánh gộp 30 ô → s_{i} (7 360 tham số)", RUST],
    ["7", "softmax → tọa độ", "w_{i} = softmax(s); (x̂, ŷ) = Σ w_{i}·tâm ô_{i}", RUST], ["8", "Học bằng sai số mét", "L = trung bình g·d(ĉ, c); Adam; tập hợp chéo 5 thành viên", RUST]];
  r1.forEach((b, i) => box(xs[i], 1.5, w, 2.0, ...b));
  r2.forEach((b, i) => box(xs[i], 4.15, w, 2.0, ...b));
  for (let i = 0; i < 3; i++) {
    s.addShape(pres.shapes.LINE, { x: xs[i] + w + 0.03, y: 2.5, w: g - 0.06, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
    s.addShape(pres.shapes.LINE, { x: xs[i] + w + 0.03, y: 5.15, w: g - 0.06, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
  }
  s.addShape(pres.shapes.LINE, { x: xs[3] + w / 2, y: 3.5, w: 0, h: 0.3, line: { color: GREY, width: 1.75 } });
  s.addShape(pres.shapes.LINE, { x: xs[0] + w / 2, y: 3.8, w: xs[3] - xs[0], h: 0, line: { color: GREY, width: 1.75 } });
  s.addShape(pres.shapes.LINE, { x: xs[0] + w / 2, y: 3.8, w: 0, h: 0.33, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 6.3, w: 0.4, h: 0.25, rectRadius: 0.05, fill: { color: "E6F0F2" }, line: { color: TEAL, width: 1.25 } });
  s.addText("giữ nguyên từ V6", { x: MX + 0.5, y: 6.28, w: 2.2, h: 0.3, fontFace: F, fontSize: 13, color: INK, margin: 0, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX + 2.9, y: 6.3, w: 0.4, h: 0.25, rectRadius: 0.05, fill: { color: "F7EAE3" }, line: { color: RUST, width: 1.25 } });
  s.addText("mới hoặc thay đổi ở V7", { x: MX + 3.4, y: 6.28, w: 3, h: 0.3, fontFace: F, fontSize: 13, color: INK, margin: 0, isTextBox: true });
  s.addText("HUIM vẫn là lõi: ứng viên, tầng và mọi đặc trưng đều sinh từ HUI do EFIM khai thác.", { x: 7.3, y: 6.28, w: SW - MX - 7.3, h: 0.3, fontFace: F, fontSize: 13, italic: true, color: NAVY, margin: 0, isTextBox: true, align: "right" });
}
{
  const s = slide("V7 · Bước 1", "Năm góc nhìn HUI: V6 dùng 3, V7 thêm 2",
    "Mỗi góc nhìn là một lần khai thác EFIM riêng trên lợi ích nội khác nhau. Góc nhìn rel bất biến với độ lệch thu của điện thoại; abs-L3 dùng cặp (AP, mức cường độ).");
  const sz = (n) => vn(n, 0);
  const rows = [["rank", "thứ hạng cường độ", "AP", sz(HC.rank), "V6"], ["rank-L3", "rank, mục = (AP, mức 1–3)", "AP × 3 mức", sz(HC.rank_L3), "V6"], ["abs", "cường độ tuyệt đối", "AP", sz(HC.abs), "V6"],
    ["rel", "cường độ so với AP mạnh nhất (W = 40 dB)", "AP", sz(HC.rel), "**V7 mới**"], ["abs-L3", "abs, mục = (AP, mức 1–3)", "AP × 3 mức", sz(HC.abs_L3), "**V7 mới**"],
    ["Tổng V6 / V7", "", "", `${sz(nHUI6)} / ${sz(nHUI7)}`, ""]];
  table(s, ["Góc nhìn", "Lợi ích nội", "Mục", "Số HUI (mô hình cuối)", "Dùng ở"], rows.map((r) => r.map((c) => c.replace(/\*\*/g, ""))), MX, 1.55, SW - 2 * MX, [1.7, 4.6, 1.8, 2.5, 1.53], { size: 14, rowH: 0.5, align: ["left", "left", "center", "right", "center"], hl: (i) => i >= 3 && i < 5 });
  card(s, MX, 5.15, 6.0, 1.7, SOFT, null, TEAL, TEAL);
  text(s, "**Khai thác:** θ = 20% tổng lợi ích của ô, cùng cơ chế tự nâng ngưỡng như V6; mỗi fold dev có 5 mô hình riêng chỉ đào trên các điện thoại khác.", MX + 0.3, 5.28, 5.5, 1.45, { fontSize: 14.5 });
  card(s, MX + 6.3, 5.15, SW - 2 * MX - 6.3, 1.7, CARD, null, RUST, RUST);
  text(s, `**Kích thước:** tệp mô hình ${vn(D.cost.v6.working_set_after_loading_MB / 1000, 2)} → ${vn(D.cost.v7.working_set_after_loading_MB / 1000, 2)} GB RAM sau khi nạp (V6 → V7); 74,3 MB so với 43,0 MB trên đĩa.`, MX + 6.6, 5.28, SW - 2 * MX - 6.9, 1.45, { fontSize: 14.5 });
}
{
  const s = slide("V7 · Bước 4", "Bước 4: đặc trưng bằng chứng HUI của từng ô ứng viên (49 cột)",
    "Mọi cột đều tính từ HUI của ô và từ chính vân tay truy vấn khớp với HUI. V6 có 33 cột; mỗi mô hình bổ sung thêm 8 cột.");
  fcard(s, "fm_feat", MX, 1.5, 7.6, 3.65);
  ann(s, [["q̂_{c}(i)", "cường độ ước lượng của AP i trong ô c, suy ra từ HUI"], ["m_{c}(i)", "khối lượng HUI mà AP i mang trong ô c (tổng = 1)"], ["R_{c}", "độ phủ ngược: phần khối lượng HUI của ô có mặt trong truy vấn"],
    ["MAE, cos", "độ sai lệch và góc giữa cường độ truy vấn và hồ sơ cường độ của ô"]], MX + 7.9, 1.5, SW - 2 * MX - 7.9, 3.65, 13.5);
  card(s, MX, 5.3, 6.0, 1.55, CARD, "33 cột của V6", NAVY, TEAL);
  text(s, "P (γ = 2, 1), V, R, điểm tương đối, hạng, log S, d_est, d_top1, mật độ ô, số AP; cùng bộ cho mô hình L3 và abs; hồ sơ cường độ: MAE, corr, cos, khối lượng AP mạnh nhất.", MX + 0.3, 5.82, 5.5, 1.0, { fontSize: 13 });
  card(s, MX + 6.3, 5.3, SW - 2 * MX - 6.3, 1.55, SOFT2, "+ 8 cột mỗi mô hình mới", RUST, RUST);
  text(s, "P, V, R, điểm tương đối, hạng, MAE, corr, cos cho **rel** và **abs-L3**: 33 + 8 + 8 = **49 cột**.", MX + 6.6, 5.82, SW - 2 * MX - 6.9, 1.0, { fontSize: 14 });
}
{
  const cs = EX.cells;
  const mx = Math.max(...cs.map((c) => c.S)), mn = Math.min(...cs.map((c) => c.S));
  const s = formulaSlide("V7 · Bước 5", "Bước 5: đặc trưng tương đối giữa các ô của cùng truy vấn", "fm_rel", [
    ["x_{i}", "một đặc trưng của ứng viên i (ví dụ điểm S)"],
    ["x̃_{i}", "hiệu với giá trị lớn nhất trong 30 ứng viên"],
    ["x̄_{i}", "min-max trong truy vấn, nằm trong [0, 1]"],
    ["r_{i}", "hạng của x_{i} trong truy vấn (0 = lớn nhất)"],
    ["slog", "log có dấu, nén đuôi dài"],
    ["μ, σ", "trung bình và độ lệch chuẩn trên tập huấn luyện"]],
    { fw: 7.6, fh: 2.2, size: 13.5, fy: 1.5 });
  const rows = cs.slice(0, 4).map((c, i) => [`ô ${c.cell}`, vn(c.S, 4), vn(c.S - mx, 4), vn((c.S - mn) / (mx - mn), 3), i]);
  s.addText(`Ví dụ hàng 335: đặc trưng S của 4 ô đầu (max = ${vn(mx, 4)}, min = ${vn(mn, 4)} trong 30 ô)`, { x: MX, y: 3.95, w: SW - 2 * MX, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Ô", "x = S", "x − max", "min-max", "hạng"], rows, MX, 4.35, 7.6, [1.6, 1.5, 1.6, 1.5, 1.4], { size: 13.5, rowH: 0.4, align: ["left", "right", "right", "right", "right"] });
  card(s, MX + 7.9, 3.95, SW - 2 * MX - 7.9, 2.9, SOFT, "Vì sao tương đối", NAVY, TEAL);
  bullets(s, ["Điểm tuyệt đối thay đổi theo vân tay; điều quan trọng là ô này **tốt hơn các ô khác bao nhiêu**", "4 phép biến đổi nhân số cột lên 4 lần: 49 × 4 = 196 đầu vào"], MX + 8.15, 4.5, SW - 2 * MX - 8.4, 2.3, 14.5);
}
{
  const s = formulaSlide("V7 · Bước 6", "Bước 6: bộ chấm điểm dùng chung cho 30 ô ứng viên", "fm_scorer", [
    ["z_{i}", "196 đặc trưng đã chuẩn hóa của ứng viên i"],
    ["W_{1}, b_{1}", "lớp ẩn 1: 196 → 32 (6 304 tham số)"],
    ["h̄", "trung bình h trên 30 ứng viên: cho ô i biết các ô còn lại"],
    ["W_{2}, b_{2}", "lớp ẩn 2: 64 → 16 (1 040 tham số)"],
    ["w_{3}", "16 trọng số cuối → điểm s_{i} (16 tham số)"]],
    { fw: 7.2, fh: 2.9, size: 14, fy: 1.5, notes: "Cùng một bộ tham số được dùng cho mọi ứng viên; nhánh gộp cho phép điểm của ô phụ thuộc các ô khác của cùng truy vấn. Tổng 7 360 tham số." });
  const bx = (x, y, w, h, lines, c) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: c === NAVY ? "E8EDF4" : c === TEAL ? "E6F0F2" : "F7EAE3" }, line: { color: c, width: 1.25 } });
    const runs = [];
    lines.forEach((ln, i) => para(ln).forEach((q, j, arr) => runs.push({ text: q.text, options: { ...q.options, breakLine: i < lines.length - 1 && j === arr.length - 1 } })));
    s.addText(runs, { x: x + 0.05, y, w: w - 0.1, h, fontFace: F, fontSize: 13, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
  };
  const y0 = 4.65, ww = 1.7, gg = 0.36, hh = 1.0;
  const seq = [[["z_{i}", "(196 số)"], NAVY], [["ReLU(W₁z+b₁)", "h_{i} (32)"], TEAL], [["[h_{i} ; h̄]", "(64)"], RUST], [["ReLU(W₂·+b₂)", "g_{i} (16)"], TEAL], [["s_{i} = w₃ᵀg_{i}", "(1 số)"], NAVY]];
  seq.forEach(([t, c], i) => { bx(MX + i * (ww + gg), y0, ww, hh, t, c);
    if (i < 4) s.addShape(pres.shapes.LINE, { x: MX + i * (ww + gg) + ww + 0.03, y: y0 + hh / 2, w: gg - 0.06, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } }); });
  s.addText("lặp cho cả 30 ứng viên; h̄ = trung bình các h_j", { x: MX, y: y0 + hh + 0.1, w: 7.5, h: 0.3, fontFace: F, fontSize: 12.5, italic: true, color: GREY, margin: 0, isTextBox: true });
  card(s, MX + 10.4 - 0.1, 4.45, SW - 2 * MX - 10.3, 1.9, SOFT, null, TEAL, TEAL);
  text(s, "Tổng **7 360** tham số (V7-B: 5 312)", MX + 10.4 + 0.1, 4.55, SW - 2 * MX - 10.5, 1.7, { fontSize: 14.5 });
}
{
  const cs = EX.cells.slice().sort((a, b) => b.w7 - a.w7);
  const s = formulaSlide("V7 · Bước 7", "Bước 7: softmax đổi điểm thành trọng số, rồi thành tọa độ", "fm_softmax", [
    ["s_{i}", "điểm của ô ứng viên i (đầu ra bộ chấm điểm)"],
    ["w_{i}", "trọng số: không âm, tổng bằng 1 (softmax)"],
    ["K = 30", "số ứng viên"],
    ["(x_{i}, y_{i})", "tâm của ô ứng viên i"],
    ["(x̂, ŷ)", "tọa độ dự đoán: nằm trong bao lồi của 30 tâm ô"]],
    { fw: 7.2, fh: 2.3, size: 14, fy: 1.5 });
  const rows = cs.slice(0, 6).map((c) => [`ô ${c.cell}`, vn(c.w7, 4), vn(c.dx, 2), vn(c.dy, 2), vn(c.w7 * c.dx, 3), vn(c.w7 * c.dy, 3)]);
  s.addText(`Ví dụ hàng 335, V7: 6 ô có trọng số lớn nhất (Δ = tâm ô − vị trí thật, đơn vị tọa độ)`, { x: MX, y: 3.95, w: SW - 2 * MX, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Ô", "w", "Δx", "Δy", "w·Δx", "w·Δy"], rows, MX, 4.35, 8.2, [1.4, 1.3, 1.4, 1.4, 1.35, 1.35], { size: 13, rowH: 0.36, align: ["left", "right", "right", "right", "right", "right"] });
  card(s, MX + 8.5, 3.95, SW - 2 * MX - 8.5, 2.9, SOFT, "Tính đủ 30 ô", NAVY, TEAL);
  bullets(s, [`Σ w = ${vn(cs.reduce((a, c) => a + c.w7, 0), 6)}`, `Σ w·Δx = **${vn(EX.v7.sum_dx, 5)}**`, `Σ w·Δy = **${vn(EX.v7.sum_dy, 5)}**`, "Slide ví dụ sau tính đủ 30 ô"], MX + 8.75, 4.5, SW - 2 * MX - 9.0, 2.3, 14.5);
}
{
  const s = formulaSlide("V7 · Bước 8", "Bước 8: học bằng chính sai số tọa độ tính bằng mét", "fm_loss", [
    ["L", "hàm mất mát: sai số tọa độ hợp nhất trung bình (m)"],
    ["ĉ_{n}, c_{n}", "tọa độ dự đoán và tọa độ thật của vân tay n"],
    ["g", "hệ số mét 0,766126"],
    ["ε = 10⁻⁶", "hằng nhỏ để đạo hàm xác định tại 0"]],
    { fw: 7.2, fh: 1.45, size: 14, fy: 1.5 });
  fcard(s, "fm_grad", MX, 3.1, 7.2, 1.55);
  ann(s, [["∂L/∂ĉ", "gradient theo tọa độ ước lượng: vector đơn vị hướng từ vị trí thật tới ước lượng, nhân g/N"], ["∂ĉ/∂s_{i}", "= w_{i}(c_{i} − ĉ) (đạo hàm của softmax)"], ["∂L/∂s_{i}", "ô nằm ở phía \"đúng\" của ĉ được tăng điểm"]], MX + 7.5, 3.1, SW - 2 * MX - 7.5, 1.9, 13.5);
  card(s, MX, 4.85, SW - 2 * MX, 2.0, CARD, "Huấn luyện", NAVY, TEAL);
  bullets(s, ["Adam (lr 5·10⁻⁴, weight decay 10⁻³), batch 256, tối đa 30 epoch, dừng sớm (kiên nhẫn 8); gradient viết tay bằng NumPy, kiểm bằng sai phân hữu hạn (sai lệch tương đối 5·10⁻⁸)",
    "Mất mát là **chính chỉ số cần giảm**; không có bước đổi khoảng cách thành trọng số bằng công thức cố định như V6"], MX + 0.3, 5.4, SW - 2 * MX - 0.6, 1.4, 14.5);
}
{
  const s = slide("V7 · Giao thức huấn luyện", "Tập hợp chéo theo điện thoại: fold đánh giá không bao giờ bị thấy",
    "Sáu fold theo điện thoại. Với fold đánh giá k, năm thành viên: thành viên i dừng sớm trên một fold huấn luyện i và huấn luyện trên bốn fold còn lại. Điểm s trung bình rồi softmax.");
  const k = 2, cx = MX, cy = 1.7, cw = 0.95, ch = 0.55;
  s.addText("Ví dụ: fold đánh giá k = 3", { x: MX, y: 1.4, w: 6, h: 0.3, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  for (let m = 0; m < 5; m++) {
    s.addText(`thành viên ${m + 1}`, { x: cx, y: cy + 0.45 + m * 0.6, w: 1.5, h: 0.45, fontFace: F, fontSize: 13, color: INK, margin: 0, valign: "middle", isTextBox: true });
    const train = [0, 1, 3, 4, 5];
    for (let f = 0; f < 6; f++) {
      let col = "E3E0D8", lab = "";
      if (f === k) { col = GOLD; lab = "đánh giá"; }
      else if (train[m] === f) { col = RUST; lab = "dừng sớm"; }
      else { col = TEAL; lab = "huấn luyện"; }
      s.addShape(pres.shapes.RECTANGLE, { x: cx + 1.6 + f * (cw + 0.06), y: cy + 0.45 + m * 0.6, w: cw, h: 0.46, fill: { color: col }, line: { color: "FFFFFF", width: 1 } });
      s.addText(lab, { x: cx + 1.6 + f * (cw + 0.06), y: cy + 0.45 + m * 0.6, w: cw, h: 0.46, fontFace: F, fontSize: 11, color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true });
    }
  }
  for (let f = 0; f < 6; f++) s.addText(`fold ${f + 1}`, { x: cx + 1.6 + f * (cw + 0.06), y: cy, w: cw, h: 0.4, fontFace: F, fontSize: 12.5, color: GREY, align: "center", margin: 0, isTextBox: true });
  bullets(s, ["Fold = **GroupKFold theo PHONEID** (16 điện thoại huấn luyện): không điện thoại nào có mặt ở hai phía của một fold",
    "Mô hình HUI của đặc trưng fold k **chỉ đào** trên các điện thoại khác; bộ chấm điểm cũng chỉ huấn luyện và dừng sớm trên các fold khác",
    "Điểm s của 5 thành viên được trung bình rồi mới softmax",
    `**Rò rỉ gián tiếp** (mô hình HUI M_{j} của fold huấn luyện đã đọc vân tay fold k): đo bằng giao thức chặt, chênh lệch **${vnd(D.nested.diff, 4)} m**`.replace("_{j}", "j")], MX, 5.2, SW - 2 * MX, 1.7, 14, INK, 3);
  card(s, MX + 9.2, 1.5, SW - 2 * MX - 9.2, 3.5, SOFT, "Cache có nguồn gốc", NAVY, TEAL);
  text(s, "Mỗi cache ghi SHA-256 của trainingData.csv, băm chỉ số hàng huấn luyện/đánh giá, mã, seed, cấu hình; từ chối cache không khớp.", MX + 9.45, 2.1, SW - 2 * MX - 9.7, 2.8, { fontSize: 14 });
}
{
  const s = slide("V7 · Ví dụ trọn vẹn (1)", `Vân tay hàng ${EX.src_row}: bằng chứng HUI của các ô ứng viên hàng đầu`,
    "Hàng 335 có sai số V7 đúng bằng trung vị của tập kiểm tra (4,6357 m) và đúng tầng; chọn theo quy tắc khách quan, không chọn ví dụ đẹp. Ô điểm HUI cao nhất cách vị trí thật 11,4 m.");
  const cs = EX.cells.slice(0, 8);
  const rows = cs.map((c) => [c.rank_hui, c.cell, vn(c.S_rel, 3), vn(c.P, 4), vn(c.V, 3), vn(c.R, 3), vn(c.dist_m, 2), vn(c.w6, 4), vn(c.w7, 4)]);
  table(s, ["Hạng HUI", "Ô", "S/S₁", "P", "V", "R", "cách vị trí thật (m)", "w V6", "w V7"], rows, MX, 1.5, SW - 2 * MX, [1.2, 1.1, 1.3, 1.3, 1.3, 1.3, 2.2, 1.2, 1.23], { size: 13.5, rowH: 0.4, align: ["center", "center", "right", "right", "right", "right", "right", "right", "right"] });
  card(s, MX, 5.35, 6.0, 1.5, CARD, null, TEAL, TEAL);
  text(s, `Vị trí thật: tầng ${EX.pred_bf} (dự đoán đúng), điện thoại ${EX.phone}. **Ô hạng 1 (${EX.cells[0].cell}) cách ${vn(EX.cells[0].dist_m, 2)} m**; V4 (trung bình 12 ô) sai ${vn(EX.v4_err_m, 2)} m.`, MX + 0.3, 5.5, 5.5, 1.25, { fontSize: 14.5, valign: "middle" });
  card(s, MX + 6.3, 5.35, SW - 2 * MX - 6.3, 1.5, SOFT2, null, RUST, RUST);
  text(s, "**V6** dồn trọng số vào các ô xa (351, 348, 352: tổng 45%); **V7** chuyển trọng số tới ô gần hơn (344, 342, 338, 365).", MX + 6.6, 5.5, SW - 2 * MX - 6.9, 1.25, { fontSize: 14.5, valign: "middle" });
}
{
  const s = slide("V7 · Ví dụ trọn vẹn (2)", "Trọng số V6 và V7 trên cùng 30 ô ứng viên của hàng 335",
    "Bong bóng là ô ứng viên, diện tích tỷ lệ với trọng số. Sao vàng là vị trí thật; dấu X là tọa độ ước lượng. V7 đặt trọng số lớn hơn vào các ô gần vị trí thật hơn.");
  img(s, as("ex_map"), MX, 1.45, SW - 2 * MX, 5.4, "center", "bản đồ ví dụ V6 và V7");
}
{
  const cs = EX.cells.slice().sort((a, b) => Math.max(b.w6, b.w7) - Math.max(a.w6, a.w7));
  const top = cs.slice(0, 7), rest = cs.slice(7);
  const sx = (k, key) => rest.reduce((a, c) => a + c[key] * c[k], 0);
  const rows = top.map((c) => [`ô ${c.cell}`, vn(c.dx, 3), vn(c.dy, 3), vn(c.w6, 4), vn(c.w7, 4)]);
  rows.push([`${rest.length} ô còn lại`, "", "", vn(rest.reduce((a, c) => a + c.w6, 0), 4), vn(rest.reduce((a, c) => a + c.w7, 0), 4)]);
  const s = slide("V7 · Ví dụ trọn vẹn (3)", "Tính tay (x̂ − x, ŷ − y) và sai số của V6 và V7 cho hàng 335",
    "Lấy Δ = tâm ô trừ vị trí thật rồi cộng w·Δ trên cả 30 ô: ra x̂−x, ŷ−y; nhân với g sau khi lấy căn tổng bình phương. Kết quả khớp tệp dự đoán và ô Excel Vi_du_mot_truy_van.");
  table(s, ["Ô", "Δx", "Δy", "w V6", "w V7"], rows, MX, 1.5, 6.7, [1.9, 1.2, 1.2, 1.2, 1.2], { size: 13, rowH: 0.38, align: ["left", "right", "right", "right", "right"] });
  const lines = [["Σ w·Δx", EX.v6.sum_dx, EX.v7.sum_dx], ["Σ w·Δy", EX.v6.sum_dy, EX.v7.sum_dy]];
  card(s, MX + 7.0, 1.5, SW - 2 * MX - 7.0, 3.35, SOFT, "Cộng đủ 30 ô", NAVY, TEAL);
  table(s, ["", "V6*", "V7"], [["Σ w", "1,000000", "1,000000"], ["Σ w·Δx", vn(EX.v6.sum_dx, 5), vn(EX.v7.sum_dx, 5)], ["Σ w·Δy", vn(EX.v6.sum_dy, 5), vn(EX.v7.sum_dy, 5)], ["√(…) (đơn vị toạ độ)", vn(Math.hypot(EX.v6.sum_dx, EX.v6.sum_dy), 5), vn(Math.hypot(EX.v7.sum_dx, EX.v7.sum_dy), 5)]],
    MX + 7.25, 2.1, SW - 2 * MX - 7.5, [2.6, 1.5, 1.4].map((x) => x * (SW - 2 * MX - 7.5) / 5.5), { size: 13, rowH: 0.42, align: ["left", "right", "right"] });
  card(s, MX, 5.0, SW - 2 * MX, 1.85, SOFT2, "Sai số = 0,766126 × √(…)", RUST, RUST);
  bullets(s, [`V6*: 0,766126 × ${vn(Math.hypot(EX.v6.sum_dx, EX.v6.sum_dy), 5)} = **${vn(EX.v6.err_m, 4)} m**      V7: 0,766126 × ${vn(Math.hypot(EX.v7.sum_dx, EX.v7.sum_dy), 5)} = **${vn(EX.v7.err_m, 4)} m**`,
    `V7 giảm ${vn(EX.v6.err_m - EX.v7.err_m, 2)} m (${vn(100 * (1 - EX.v7.err_m / EX.v6.err_m), 0)}%) trên vân tay này; 30 ô, 30 trọng số và sai số lưu trong tệp khớp đến 6 chữ số`], MX + 0.3, 5.6, SW - 2 * MX - 0.6, 1.2, 15);
}
{
  const s = slide("V7 · Từ bước nào ra bao nhiêu mét", `Từ ${vn(T6r.mean, 3)} m xuống ${vn(T7.mean, 3)} m: đóng góp của từng bước`,
    "Bộ chấm điểm trực tiếp giảm nhiều nhất (0,43 m trên test); mô hình HUI rel giảm thêm 0,04 m; abs-L3 thêm 0,08 m. Trên dev các mức giảm là 0,28; 0,19 và 0,03 m.");
  const ladder = [["V6 (tái tạo)", T6r.mean, dI("V6*").mean], ["+ bộ chấm điểm trực tiếp (V7-B)", tr("B_base").mean, dI("B_base").mean], ["+ HUI rel (V7-C1)", tr("C_rel").mean, dI("C_rel").mean], ["+ HUI abs-L3 (V7-C2)", T7.mean, dI("C_rel_absL3").mean]];
  const labels = ladder.map((l) => l[0]);
  s.addChart(pres.charts.BAR, [{ name: "validationData (test)", labels, values: ladder.map((l) => Math.round(l[1] * 1000) / 1000) }, { name: "dev out-of-fold (có thông tin)", labels, values: ladder.map((l) => Math.round(l[2] * 1000) / 1000) }],
    { ...chartBase(), x: MX, y: 1.45, w: 7.9, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontSize: 11.5,
      valAxisMinVal: 5, valAxisMaxVal: 7.2, valAxisMajorUnit: 0.5, showLegend: true, legendPos: "b", showTitle: true, title: "Sai số trung bình (m); trục bắt đầu từ 5 m", barGapWidthPct: 45, catAxisLabelFontSize: 12 });
  const rows = [["V7-B", vnd(tr("B_base").mean - T6r.mean, 3), vnd(dI("B_base").mean - dI("V6*").mean, 3)], ["+ rel", vnd(tr("C_rel").mean - tr("B_base").mean, 3), vnd(dI("C_rel").mean - dI("B_base").mean, 3)],
    ["+ abs-L3", vnd(T7.mean - tr("C_rel").mean, 3), vnd(dI("C_rel_absL3").mean - dI("C_rel").mean, 3)], ["Tổng", vnd(T7.mean - T6r.mean, 3), vnd(dI("C_rel_absL3").mean - dI("V6*").mean, 3)]];
  s.addText("Thay đổi so với bước trước (m)", { x: MX + 8.2, y: 1.5, w: 4.3, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Bước", "Test", "Dev"], rows, MX + 8.2, 1.95, SW - 2 * MX - 8.2, [1.8, 1.25, 1.2].map((x) => x * (SW - 2 * MX - 8.2) / 4.25), { size: 14, rowH: 0.45, align: ["left", "right", "right"], hl: (i) => i === 3 });
  text(s, "Chỉ khối **rel** (−0,195 m dev, tốt hơn ở 6/6 fold) và **bộ chấm điểm trực tiếp** có ý nghĩa thống kê rõ; abs-L3 nhỏ (KTC cặp chứa 0).", MX + 8.2, 4.4, SW - 2 * MX - 8.2, 1.8, { fontSize: 14.5, color: RUST });
}
{
  const v = D.v7a;
  const s = formulaSlide("V7-A · Hợp nhất thích ứng", "V7-A: đổi quy tắc hợp nhất ô; giảm rất ít và không bền", "fm_fusion", [
    ["d̂_{i}", "khoảng cách dự đoán của ô i (từ bộ xếp hạng V6)"],
    ["δ, s_{min}, r", "ngưỡng cắt, ngưỡng điểm tương đối, bán kính cụm (m)"],
    ["T₀, c", "nhiệt độ gốc và hệ số tăng theo d̂_{min}"],
    ["S_{i}/S_{1}", "điểm HUI tương đối của ô i"]],
    { fw: 7.6, fh: 3.1, size: 14, fy: 1.5 });
  const rows = [["V6* (m = 20, T = 2)", vn(v["V6*"].dev_informative_mean, 4), "—"], ["lưới (m, T)", vn(v.v6.nested_dev_informative_mean, 4), vnd(v.v6.nested_dev_informative_mean - v["V6*"].dev_informative_mean, 4)],
    ["cắt theo chênh lệch", vn(v.cut.nested_dev_informative_mean, 4), vnd(v.cut.nested_dev_informative_mean - v["V6*"].dev_informative_mean, 4)], ["**nhiệt độ thích ứng**", vn(v.adaptT.nested_dev_informative_mean, 4), vnd(v.adaptT.nested_dev_informative_mean - v["V6*"].dev_informative_mean, 4)],
    ["loại ô điểm thấp", vn(v.floorS.nested_dev_informative_mean, 4), vnd(v.floorS.nested_dev_informative_mean - v["V6*"].dev_informative_mean, 4)], ["chọn cụm", vn(v.cluster.nested_dev_informative_mean, 4), vnd(v.cluster.nested_dev_informative_mean - v["V6*"].dev_informative_mean, 4)]];
  table(s, ["Quy tắc (dev, chọn lồng nhau)", "TB (m)", "Chênh"], rows.map((r) => r.map((c) => c.replace(/\*\*/g, ""))), MX, 4.7, 7.6, [4.2, 1.7, 1.7], { size: 13, rowH: 0.31, align: ["left", "right", "right"], hl: (i) => i === 3 });
  card(s, MX + 7.9, 1.5, SW - 2 * MX - 7.9, 5.35, SOFT2, "Kết quả", RUST, RUST);
  bullets(s, [`Quy tắc tốt nhất (nhiệt độ thích ứng) giảm **${vn(v["V6*"].dev_informative_mean - v.adaptT.nested_dev_informative_mean, 3)} m** trên dev khi chọn tham số lồng nhau`,
    `Trên **test**: ${vn(tr("V7-A").mean, 4)} m so với V6 tái tạo ${vn(T6r.mean, 4)} m: **tệ hơn ${vn(tr("V7-A").mean - T6r.mean, 3)} m**`, "KTC cặp cả hai chiều chứa 0", "Kết luận: cách hợp nhất **không phải điểm nghẽn**; cần học lại cách chấm điểm (V7-B)"], MX + 8.15, 2.1, SW - 2 * MX - 8.4, 4.7, 14.5);
}
{
  const s = slide("V7-C · Bằng chứng HUI mới", "V7-C: thêm hai góc nhìn HUI, rel và abs mức-3",
    "Góc nhìn rel không đổi khi điện thoại đọc lệch đều; ví dụ trước cho thấy abs đổi khi lệch 10 dB còn rank và rel không đổi. Thêm rel giảm 0,195 m (6/6 fold); thêm abs-L3 giảm thêm 0,034 m.");
  card(s, MX, 1.5, 6.0, 2.55, SOFT, "Vì sao rel", TEAL, TEAL);
  bullets(s, ["Điện thoại khác nhau đọc RSSI lệch một hằng số", "rank và rel không đổi khi **mọi AP lệch đều**; abs đổi (ví dụ WAP" + String(EX.aps[0].ap).padStart(3, "0") + ": " + EX.aps[0].q_abs + " → " + EX.aps[0].q_abs_shift + " khi thấp hơn 10 dB)", "rel giữ **mức chênh lệch** giữa các AP, rank chỉ giữ thứ tự"], MX + 0.3, 2.05, 5.5, 2.0, 14.5);
  card(s, MX, 4.2, 6.0, 2.65, CARD, "Bằng chứng thêm vào mỗi ứng viên", NAVY, TEAL);
  bullets(s, ["P, V, R, điểm tương đối, hạng, MAE, corr, cos tính từ HUI của mô hình mới (8 cột)", "abs-L3 coi mỗi (AP, mức cường độ) là một mục: mẫu chi tiết hơn"], MX + 0.3, 4.75, 5.5, 2.0, 14.5);
  const rows = [["V7-B (chỉ đặc trưng V6)", vn(dI("B_base").mean, 4), "—", "—"], ["+ HUI rel (V7-C1)", vn(dI("C_rel").mean, 4), "−0,195 [−0,283; −0,106]", "6/6"], ["+ HUI abs-L3 (V7-C2)", vn(dI("C_rel_absL3").mean, 4), "−0,034 [−0,087; +0,054]", "4/6"]];
  table(s, ["Dev out-of-fold", "TB (m)", "Chênh [KTC 95% cặp]", "Fold tốt hơn"], rows, MX + 6.3, 1.55, SW - 2 * MX - 6.3, [2.2, 1.0, 2.3, 1.0].map((x) => x * (SW - 2 * MX - 6.3) / 6.5), { size: 13, rowH: 0.5, align: ["left", "right", "right", "center"] });
  const rows2 = [["V6 (tái tạo)", vn(T6r.mean, 4)], ["V7-B", vn(tr("B_base").mean, 4)], ["V7-C1 (+ rel)", vn(tr("C_rel").mean, 4)], ["V7-C2 (+ rel + abs-L3)", vn(T7.mean, 4)]];
  s.addText("Trên tập kiểm tra", { x: MX + 6.3, y: 4.0, w: 6, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Mô hình", "TB (m)"], rows2, MX + 6.3, 4.4, 5.0, [3.4, 1.6], { size: 13.5, rowH: 0.42, align: ["left", "right"], hl: (i) => i === 3 });
}
{
  const E = D.explore, byLog = (n) => E.find((r) => r.log === n);
  const s = slide("V7 · Các thử nghiệm không giúp", "Kết quả âm: bốn hướng không cải thiện (ghi trung thực)",
    "Bù lệch thiết bị làm tệ đi vì bộ chấm điểm học đặc trưng có dấu đặc thù của điện thoại huấn luyện; đồng thuận không gian không có lợi; trộn với GBM và mất mát phụ listwise không giúp.");
  const rows = [["Đặc trưng bù lệch thiết bị (13 cột)", `${vn(D.dev_files.C_devrob.mean_inf, 3)} so với V7-B ${vn(D.dev_files.B_base.mean_inf, 3)}`, "tệ hơn (+0,063 m): quá khớp theo điện thoại huấn luyện"],
    ["Đồng thuận không gian giữa các mô hình HUI (15 cột)", `${vn(byLog("b2_rel_geo.log").tb_co_trong_so, 3)} so với ${vn(byLog("b2_rel.log").tb_co_trong_so, 3)}`, "−0,006 m: không có ý nghĩa"],
    ["Trộn trọng số V7-C2 với trọng số GBM của V6 (chọn lồng nhau)", "5,706 so với 5,702", "không tốt hơn V7-C2 thuần"],
    ["Mất mát phụ listwise (aux 0,3, thăm dò 1 thành viên)", `${vn(byLog("b_c2.log").tb_co_trong_so, 3)} so với ${vn(byLog("b_c1.log").tb_co_trong_so, 3)}`, "tệ hơn"],
    ["Hợp nhất thích ứng V7-A (trên test)", `${vn(tr("V7-A").mean, 3)} so với ${vn(T6r.mean, 3)}`, "tệ hơn 0,020 m: không bền"]];
  table(s, ["Thử nghiệm", "Sai số dev (m)", "Kết luận"], rows, MX, 1.55, SW - 2 * MX, [5.6, 3.2, SW - 2 * MX - 8.8], { size: 13.5, rowH: 0.7, align: ["left", "center", "left"] });
  callout(s, "Các hướng IDF và thông tin tương hỗ đã thất bại ở V6 **không được lặp lại**. Mọi kết quả âm đều có nhật ký trong results/logs/v7_explore và BAOCAO_V7/so_lieu/logs.", 5.7, 1.0, SOFT2, INK, 15);
}
{
  const s = formulaSlide("V7-D · HUI phân cấp", "V7-D: HUI cấp tầng làm ngữ cảnh; kết quả trung tính", "fm_hier", [
    ["θ_{f}", "ngưỡng của mô hình cấp tầng: 12,5% tổng lợi ích của tầng"],
    ["P, V, R", "điểm khớp, độ phủ, độ phủ ngược tính trên HUI của tầng"],
    ["f*", "tầng được chọn của truy vấn"],
    ["11 số", "gắn vào mọi ứng viên của truy vấn"]],
    { fw: 7.6, fh: 1.9, size: 14, fy: 1.5 });
  const dd = D.dev_files.D_hier;
  const rows = [["Dev, có thông tin", vn(dI("C_rel_absL3").mean, 4), vn(dd.mean_inf, 4), "−0,013; tốt hơn 3/6 fold"], ["Dev, tất cả", vn(dA("C_rel_absL3").mean, 4), vn(dA("D_hier").mean, 4), ""], ["Test", vn(T7.mean, 4), vn(tr("D_hier").mean, 4), "+0,014"]];
  table(s, ["", "V7-C2", "V7-D", "Chênh"], rows, MX, 3.6, 7.6, [2.2, 1.6, 1.6, 2.2], { size: 13.5, rowH: 0.42, align: ["left", "right", "right", "left"] });
  text(s, "Mô hình cấp tầng thưa và không ổn định: số HUI 4 845 đến 67 839 giữa các mô hình, 1–3 tầng không có HUI nào ở 12,5%; HUI theo ô vẫn quyết định ứng viên.", MX, 5.45, 7.6, 1.4, { fontSize: 14, color: GREY });
  card(s, MX + 7.9, 1.5, SW - 2 * MX - 7.9, 5.35, SOFT2, "Vì sao giữ V7-C2", RUST, RUST);
  bullets(s, ["Tiêu chí chọn: sai số dev thấp hơn **và** tốt hơn ở ít nhất 4/6 fold (nêu **trước** khi chấm V7-D trên test)", "V7-D chỉ tốt hơn V7-C2 ở 3/6 fold, tệ hơn 0,014 m trên test", "Lần đào đầu dùng giới hạn đồng hồ 600 s cho mô hình khác nhau theo tải máy (22–124 nghìn HUI) → bỏ, dùng chính sách chỉ dựa trên số HUI"], MX + 8.15, 2.1, SW - 2 * MX - 8.4, 4.7, 14.5);
}

// ================================================================== CHƯƠNG 4
divider(3, "Kết quả", ["Dev out-of-fold và tập kiểm tra", "Phân bố sai số, tầng, điện thoại, hình học", "Cắt bỏ thành phần và chi phí"]);
{
  const s = slide("Kết quả · Dev out-of-fold", "Dev: V7-C2 giảm 0,507 m so với V6* (KTC chặn trên −0,26 m)",
    "Sai số trung bình (m) trên 19 861 vân tay có thông tin và trên cả 19 937 vân tay; khoảng tin cậy 95% của chênh lệch cặp theo cụm điện thoại.");
  const order = [["V4", "V4"], ["V5", "V5 (tái tạo)"], ["V6", "V6 (float32)"], ["V6*", "V6* (float64)"], ["V7-A", "V7-A hợp nhất thích ứng"], ["B_base", "V7-B tối ưu trực tiếp"], ["C_rel", "V7-C1 + HUI rel"], ["C_rel_absL3", "V7-C2 + HUI abs-L3 (chọn)"], ["D_hier", "V7-D + HUI cấp tầng"], ["C_devrob", "V7-C + bù lệch thiết bị"]];
  const rows = order.map(([m, lab]) => { const r = dI(m), a = dA(m); return [lab, vn(r.mean, 3), m === "V6*" ? "—" : `${vnd(r["diff_vs_V6*"], 3)} [${vnd(r.diff_lo, 2)}; ${vnd(r.diff_hi, 2)}]`, vn(a.mean, 3), vn(r.median, 3), vn(r.p75, 2), vn(r.p90, 2)]; });
  table(s, ["Mô hình", "Có thông tin", "Chênh vs V6* [KTC 95%]", "Tất cả", "Trung vị", "P75", "P90"], rows, MX, 1.5, SW - 2 * MX, [3.5, 1.4, 2.9, 1.2, 1.2, 0.9, 1.03], { size: 13, rowH: 0.43, align: ["left", "right", "center", "right", "right", "right", "right"], hl: (i) => order[i][0] === "C_rel_absL3" });
  text(s, "Độ chính xác tầng dev 84,15%, tòa 99,99% ở mọi dòng (cùng quy tắc chọn tầng). KTC: bootstrap 4 000 lần lấy mẫu lại **cả điện thoại** (16 cụm).", MX, 6.35, SW - 2 * MX, 0.5, { fontSize: 13.5, color: GREY });
}
{
  const s = slide("Kết quả · Tập kiểm tra", `Test: V7-C2 đạt ${vn(T7.mean, 3)} m, thấp hơn V6 ${vn(-T7.diff_vs_V6, 3)} m`,
    "Mỗi biến thể được chấm đúng một lần trên validationData, kể cả biến thể không được chọn. Tập này đã được dùng nhiều lần từ V1 đến V6 nên là chỉ báo, không phải ước lượng độc lập.");
  const order = [["V4", "V4 (lưu)"], ["V5", "V5 (lưu)"], ["V6", "V6 (lưu)"], ["V6r", "V6 (tái tạo)"], ["V7-A", "V7-A hợp nhất thích ứng"], ["B_base", "V7-B tối ưu trực tiếp"], ["C_rel", "V7-C1 + HUI rel"], ["C_rel_absL3", "V7-C2 + HUI abs-L3 (chọn theo dev)"], ["D_hier", "V7-D + HUI cấp tầng"]];
  const rows = order.map(([m, lab]) => { const r = tr(m); return [lab, vn(r.mean, 3), `[${vn(r.ci95_lo, 2)}; ${vn(r.ci95_hi, 2)}]`, m === "V6" ? "—" : `${vnd(r.diff_vs_V6, 3)} [${vnd(r.diff_lo, 2)}; ${vnd(r.diff_hi, 2)}]`, vn(r.median, 3), vn(r.p75, 2), vn(r.p90, 2), vn(r.p95, 2)]; });
  table(s, ["Mô hình", "TB (m)", "KTC 95%", "Chênh vs V6 [KTC cặp]", "Trung vị", "P75", "P90", "P95"], rows, MX, 1.5, SW - 2 * MX, [3.3, 1.0, 1.7, 2.6, 1.0, 0.8, 0.8, 0.93], { size: 13, rowH: 0.4, align: ["left", "right", "center", "center", "right", "right", "right", "right"], hl: (i) => order[i][0] === "C_rel_absL3" });
  text(s, `Đúng tòa ${pct(FIN.building_accuracy, 2)}, đúng tầng ${pct(FIN.floor_accuracy, 2)} ở mọi dòng. V7-C2 tốt hơn V6 trong ${pct(T7.p_better, 1)} số lần lấy mẫu lại điện thoại (11 cụm). Mục tiêu dưới 6 m: **chưa đạt**.`, MX, 6.15, SW - 2 * MX, 0.75, { fontSize: 14.5, color: INK });
}
{
  const s = slide("Kết quả · Phân bố sai số", "Phân bố sai số: V7 nằm trên V6 ở hầu hết mọi mức sai số",
    "Đường CDF của V7-C2 nằm trên V6 và V4; chênh lớn nhất ở đuôi sai số (P90 từ 14,0 m xuống 12,9 m).");
  img(s, as("cdf_test"), MX, 1.5, 6.0, 5.2, "left", "CDF test");
  img(s, as("cdf_dev"), MX + 6.2, 1.5, SW - 2 * MX - 6.2, 5.2, "right", "CDF dev");
}
{
  const rn = D.floor_dev, gv = (g, m) => rn.find((r) => r.group === g && r.model === m).mean;
  const fr = D.floor_right_test, fw = D.floor_wrong_test, tg = (a, m) => a.find((r) => r.model === m).mean;
  const s = slide("Kết quả · Tầng và hình học vị trí", "Giảm sai số chủ yếu khi tầng đúng; đầu hành lang khó nhất",
    "Quy tắc chọn tầng không đổi nên độ chính xác tầng không đổi. Sai số đúng tầng giảm khoảng 9,5%; vùng biên và vùng thưa điểm tham chiếu có sai số cao nhất ở mọi mô hình.");
  const labels = ["dev đúng tầng", "dev sai tầng", "test đúng tầng", "test sai tầng"];
  s.addChart(pres.charts.BAR, [{ name: "V6", labels, values: [gv("floor_right", "V6*"), gv("floor_wrong", "V6*"), tg(fr, "V6"), tg(fw, "V6")].map((v) => Math.round(v * 100) / 100) },
    { name: "V7-C2", labels, values: [gv("floor_right", "C_rel_absL3"), gv("floor_wrong", "C_rel_absL3"), tg(fr, "C_rel_absL3"), tg(fw, "C_rel_absL3")].map((v) => Math.round(v * 100) / 100) }],
    { ...chartBase(), x: MX, y: 1.45, w: 6.4, h: 5.35, barDir: "col", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 12,
      valAxisMinVal: 0, valAxisMaxVal: 11, valAxisMajorUnit: 2, showLegend: true, legendPos: "b", showTitle: true, title: "Sai số trung bình (m) theo kết quả chọn tầng", barGapWidthPct: 45 });
  const pt = D.ptype, nmv = { interior: "bên trong (ô ở mọi phía)", edge: "biên / đầu hành lang", isolated: "vùng thưa (không ô nào trong 8 m)" };
  const rows = [];
  ["interior", "edge", "isolated"].forEach((k) => { const a = pt.find((r) => r.set === "dev" && r.vi_tri === k), b = pt.find((r) => r.set === "test" && r.vi_tri === k);
    rows.push([nmv[k], `${pct(a.share, 0)} / ${pct(b.share, 0)}`, `${vn(a["V6*"], 2)} → ${vn(a.V7, 2)}`, `${vn(b.V6, 2)} → ${vn(b.V7, 2)}`]); });
  s.addText("Theo hình học các ô quanh vị trí thật", { x: MX + 6.7, y: 1.5, w: 5.6, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["Nhóm", "% (dev / test)", "Dev: V6* → V7", "Test: V6 → V7"], rows, MX + 6.7, 1.95, SW - 2 * MX - 6.7, [2.5, 1.1, 1.3, 1.3].map((x) => x * (SW - 2 * MX - 6.7) / 6.2), { size: 12.5, rowH: 0.62, align: ["left", "center", "center", "center"] });
  text(s, "Vị trí thật chỉ dùng để **phân nhóm khi phân tích**, không phải đầu vào mô hình. Đúng tầng giảm 9,5% (test); sai tầng giảm 3,4%.", MX + 6.7, 4.45, SW - 2 * MX - 6.7, 1.6, { fontSize: 14, color: GREY });
}
{
  const s = slide("Kết quả · Theo điện thoại", "Theo điện thoại: V7 tốt hơn ở 10/11 điện thoại của tập kiểm tra",
    "Điện thoại 13 và 14 cũng có trong tập huấn luyện; chín điện thoại còn lại chưa từng thấy. Điện thoại 2 (52 vân tay) tệ hơn 1,32 m; trên dev, điện thoại 17 và 19 không được cải thiện.");
  const pt = D.phones_test.slice().sort((a, b) => b.V6 - a.V6);
  const labels = pt.map((p) => `ĐT ${p.phone} (n=${p.n})`);
  s.addChart(pres.charts.BAR, [{ name: "V6", labels, values: pt.map((p) => Math.round(p.V6 * 100) / 100) }, { name: "V7-C2", labels, values: pt.map((p) => Math.round(p.V7 * 100) / 100) }],
    { ...chartBase(), x: MX, y: 1.45, w: 7.6, h: 5.4, barDir: "bar", catAxisOrientation: "maxMin", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 10.5,
      valAxisMinVal: 0, valAxisMaxVal: 12, valAxisMajorUnit: 2, showLegend: true, legendPos: "b", showTitle: true, title: "Test: sai số trung bình theo điện thoại (m)", barGapWidthPct: 35, catAxisLabelFontSize: 12 });
  const pdv = D.phones_dev.slice().sort((a, b) => a["gain_vs_V6*"] - b["gain_vs_V6*"]);
  const worst = pdv.slice(0, 4), best = pdv.slice(-3).reverse();
  card(s, MX + 7.9, 1.5, SW - 2 * MX - 7.9, 5.35, SOFT, "Dev (16 điện thoại)", NAVY, TEAL);
  bullets(s, [`V7 tốt hơn V6* ở **${pdv.filter((p) => p["gain_vs_V6*"] > 0).length}/16** điện thoại`, `Cải thiện nhiều nhất: ${best.map((p) => `ĐT ${p.phone} (−${vn(p["gain_vs_V6*"], 2)} m)`).join("; ")}`,
    `Không cải thiện: ${worst.filter((p) => p["gain_vs_V6*"] < 0).map((p) => `ĐT ${p.phone} (+${vn(-p["gain_vs_V6*"], 2)} m)`).join("; ")}`, "Điện thoại 17 là điện thoại khó nhất (12,5–13,1 m)"], MX + 8.15, 2.1, SW - 2 * MX - 8.4, 4.6, 14.5);
}
{
  const s = slide("Kết quả · Mẫu cải thiện và cơ chế", "V7 chuyển trọng số tới ô đúng chỗ hơn: tập trung hơn và gần hơn",
    "Trên dev, 8 324 truy vấn tốt hơn (giảm trung bình 2,89 m), 6 248 kém hơn (tăng 2,24 m). V7 tập trung trọng số hơn: số ô hiệu dụng giảm từ 5,24 xuống 3,08 và khối lượng đặt vào ô gần vị trí thật tăng.");
  img(s, as("hist_dev"), MX, 1.5, 6.9, 4.4, "left", "histogram cải thiện");
  const W = D.weights, w6 = W.find((r) => r.model === "V6*"), w7 = W.find((r) => r.model === "V7");
  const rows = [["số ô hiệu dụng 1/Σw²", vn(w6.eff_cells, 2), vn(w7.eff_cells, 2)], ["trọng số lớn nhất", vn(w6.max_weight, 2), vn(w7.max_weight, 2)], ["khối lượng trên ô cách < 3 m", pct(w6.mass_within_3m, 1), pct(w7.mass_within_3m, 1)], ["trọng số trên ô HUI hạng 1", pct(w6.mass_top1_hui_cell, 1), pct(w7.mass_top1_hui_cell, 1)]];
  s.addText("Trọng số (dev, 19 861 vân tay)", { x: MX + 7.2, y: 1.5, w: 5, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  table(s, ["", "V6*", "V7-C2"], rows, MX + 7.2, 1.95, SW - 2 * MX - 7.2, [2.9, 1.1, 1.1].map((x) => x * (SW - 2 * MX - 7.2) / 5.1), { size: 13, rowH: 0.4, align: ["left", "right", "right"] });
  const im = D.improved;
  text(s, `**Tốt hơn >0,5 m:** ${vn(im[0].n, 0)} truy vấn, giảm TB ${vn(im[0].mean_gain_m, 2)} m (V6* sai ${vn(im[0]["mean_err_V6*"], 2)} m ở đó).\n**Kém hơn >0,5 m:** ${vn(im[1].n, 0)} truy vấn, tăng TB ${vn(-im[1].mean_gain_m, 2)} m (V6* sai ${vn(im[1]["mean_err_V6*"], 2)} m).`, MX + 7.2, 4.15, SW - 2 * MX - 7.2, 1.3, { fontSize: 13.5 });
  fcardNeff(s);
  function fcardNeff(sl) { sl.addShape(pres.shapes.RECTANGLE, { x: MX + 7.2, y: 5.4, w: 3.2, h: 0.62, fill: { color: CARD }, line: { color: LINE, width: 0.75 } }); img(sl, as("fm_neff"), MX + 7.4, 5.43, 2.8, 0.56, "left", "N_eff"); }
  s.addText("số ô hiệu dụng", { x: MX + 10.55, y: 5.4, w: 1.9, h: 0.62, fontFace: F, fontSize: 13, color: GREY, margin: 0, valign: "middle", isTextBox: true });
  callout(s, "V7 giữ \"độ sắc nét\" cao hơn nhưng vẫn **hỏng** ở một phần truy vấn: sai tầng và vùng thưa điểm tham chiếu vẫn là nguồn sai số còn lại.", 6.2, 0.7, SOFT2, INK, 14.5);
}
{
  const s = slide("Kết quả · Cắt bỏ thành phần", "Cắt bỏ thành phần: bộ chấm điểm trực tiếp và HUI rel đóng góp rõ nhất",
    "Mỗi thanh thêm đúng một thay đổi. Các hướng không giúp (bù lệch thiết bị, V7-D) cũng được báo cáo; V7-C2 là mô hình chọn theo dev.");
  const rowsA = [["V4", dI("V4").mean], ["V6 (float32)", dI("V6").mean], ["V6* (float64)", dI("V6*").mean], ["V7-A hợp nhất thích ứng", dI("V7-A").mean], ["V7-B tối ưu trực tiếp", dI("B_base").mean], ["V7-C1 + HUI rel", dI("C_rel").mean],
    ["V7-C2 + HUI abs-L3 (chọn)", dI("C_rel_absL3").mean], ["V7-D + HUI cấp tầng", dI("D_hier").mean], ["V7-B + bù lệch thiết bị (không chọn)", dI("C_devrob").mean]];
  s.addChart(pres.charts.BAR, [{ name: "Sai số dev (m)", labels: rowsA.map((r) => r[0]), values: rowsA.map((r) => Math.round(r[1] * 1000) / 1000) }],
    { ...chartBase(), x: MX, y: 1.45, w: 8.3, h: 5.4, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [GREY, GREY, NAVY, TEAL, TEAL, TEAL, TEAL, GOLD, RUST], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontSize: 12,
      valAxisMinVal: 0, valAxisMaxVal: 8, valAxisMajorUnit: 1, showLegend: false, showTitle: true, title: "Sai số trung bình dev, vân tay có thông tin (m)", barGapWidthPct: 40, catAxisLabelFontSize: 12.5, invertedColors: [GREY] });
  const x = MX + 8.6, w = SW - MX - x;
  card(s, x, 1.5, w, 5.35, CARD, "Đọc biểu đồ", NAVY, TEAL);
  bullets(s, ["Sửa số học float64: −0,006 m", "V7-A: −0,027 m, **không bền**", "Bộ chấm điểm trực tiếp: **−0,251 m**", "+ HUI rel: **−0,195 m** (6/6 fold)", "+ HUI abs-L3: −0,034 m", "+ cấp tầng: −0,013 m (không chọn)", "+ bù lệch thiết bị: **+0,063 m** (tệ hơn)"], x + 0.25, 2.1, w - 0.45, 4.6, 14.5);
}
{
  const s = slide("Kết quả · Chi phí", "Chi phí: V7-C2 chậm hơn 63% và cần nhiều RAM hơn 41%",
    "Thời gian đo trên 1 111 vân tay của tập kiểm tra; RAM là đỉnh tập làm việc của tiến trình suy luận. V7-B (không thêm mô hình HUI) rẻ gần bằng V6 nhưng đã giảm 0,43 m.");
  const c6 = D.cost.v6, c7 = D.cost.v7, t6 = TJ.V6_reproduced.ms_per_query, t7 = FIN.ms_per_query;
  const rows = [["Số HUI của mô hình cuối", vn(nHUI6, 0), vn(nHUI7, 0)], ["Dung lượng tệp mô hình (.npz)", "43,0 MB", "74,3 MB"], ["Thời gian suy luận / vân tay (bằng chứng HUI + chấm điểm)", `${vn(t6, 1)} ms`, `${vn(t7, 1)} ms (${vnd(100 * (t7 / t6 - 1), 0)}%)`],
    ["Trong đó: mô hình rel / abs-L3 / bộ chấm điểm", "—", "72,5 / 56,8 / 0,9 ms"], ["RAM đỉnh của tiến trình suy luận", `${vn(c6.peak_working_set_MB, 0)} MB`, `${vn(c7.peak_working_set_MB, 0)} MB (${vnd(100 * (c7.peak_working_set_MB / c6.peak_working_set_MB - 1), 0)}%)`],
    ["RAM sau khi nạp mô hình", `${vn(c6.working_set_after_loading_MB, 0)} MB`, `${vn(c7.working_set_after_loading_MB, 0)} MB`]];
  table(s, ["", "V6", "V7-C2"], rows, MX, 1.55, SW - 2 * MX, [6.2, 2.9, SW - 2 * MX - 9.1], { size: 14, rowH: 0.5, align: ["left", "right", "right"] });
  card(s, MX, 5.55, SW - 2 * MX, 1.3, SOFT, null, TEAL, TEAL);
  text(s, "Chi phí định vị không phụ thuộc số vân tay huấn luyện (chỉ phụ thuộc số HUI). V7 chưa tối ưu bộ nhớ: HUI được giữ dưới dạng danh sách mảng và ma trận thưa. 266 ms của V6 trong summary.json đo ở thời điểm khác; bảng này so cùng máy, cùng phép đo.", MX + 0.3, 5.6, SW - 2 * MX - 0.6, 1.2, { fontSize: 14, valign: "middle" });
}

// ================================================================== CHƯƠNG 5
divider(4, "Kiểm chứng 6,309 m", ["Tính lại từ toạ độ thật và dự đoán", "Excel, Python và 16 phép kiểm độc lập", "Rò rỉ, tái lập và khoảng tin cậy"]);
{
  const s = slide("Kiểm chứng · Cách 1: tính lại từ toạ độ", `Kiểm chứng ${vn(T7.mean, 4)} m: sai số từng vân tay rồi lấy trung bình`,
    "Cách kiểm tra đơn giản nhất: lấy tọa độ thật và tọa độ dự đoán của từng vân tay, tính sai số rồi lấy trung bình. Không cần chạy lại mô hình.");
  fcard(s, "fm_err", MX, 1.5, 6.6, 1.35);
  const fr = VF.first_rows;
  const rows = fr.slice(0, 4).concat(fr.slice(6)).map((r) => [r.src_row, vn(r.true_x, 3), vn(r.true_y, 3), vn(r.pred_x, 3), vn(r.pred_y, 3), vn(r.dx, 3), vn(r.dy, 3), vn(r.err_m, 4)]);
  table(s, ["Hàng", "x thật", "y thật", "x̂", "ŷ", "x̂−x", "ŷ−y", "sai số (m)"], rows, MX, 3.05, SW - 2 * MX, [0.9, 1.7, 1.9, 1.7, 1.9, 1.1, 1.1, 1.83], { size: 13, rowH: 0.4, align: ["center", "right", "right", "right", "right", "right", "right", "right"], hl: (i) => i === 4 });
  card(s, MX + 6.9, 1.5, SW - 2 * MX - 6.9, 1.35, SOFT, null, TEAL, TEAL);
  text(s, `**Tổng 1 111 sai số = ${vn(VF.sum_err_m, 2)} m; ${vn(VF.sum_err_m, 2)} / 1 111 = ${vn(VF.mean_err_m, 4)} m**; trung vị ${vn(VF.median_err_m, 4)} m; P90 ${vn(VF.p90_err_m, 4)} m.`, MX + 7.15, 1.58, SW - 2 * MX - 7.4, 1.2, { fontSize: 15, valign: "middle" });
  text(s, `Hàng 335 (tô màu): Δx = ${vn(fr[6].dx, 5)}, Δy = ${vn(fr[6].dy, 5)} → √(…) = ${vn(Math.hypot(fr[6].dx, fr[6].dy), 5)} → × 0,766126 = **${vn(fr[6].err_m, 4)} m**. Mọi dòng của bảng có thể thử bằng máy tính cầm tay; bảng đủ 1 111 dòng nằm trong Excel và CSV của bộ kiểm chứng.`, MX, 5.55, SW - 2 * MX, 0.8, { fontSize: 14.5 });
  text(s, "**Ký hiệu:** e_{n} sai số vân tay n (m); (x̂_{n}, ŷ_{n}) tọa độ dự đoán; (x_{n}, y_{n}) tọa độ thật; g = 0,766126 (m trên đơn vị tọa độ); N = 1 111; ē sai số trung bình.", MX, 6.4, SW - 2 * MX, 0.5, { fontSize: 13.5, color: GREY });
}
{
  const s = slide("Kiểm chứng · Cách 2: Excel và Python", "Excel và Python tính lại độc lập: mọi mô hình ghi KHỚP",
    "Bộ kiểm chứng nằm ở BAOCAO/so_lieu_V7. Excel có công thức từng dòng; Python chỉ dùng thư viện chuẩn, in KHỚP hoặc LỆCH cho từng mô hình, dựng lại tọa độ V7-C2 từ 30 trọng số và tâm ô, và tính lại dev.");
  const MODELS = [["V4 (đã lưu)", tr("V4").mean], ["V5 (đã lưu)", tr("V5").mean], ["V6 (đã lưu)", tr("V6").mean], ["V6 (tái tạo)", tr("V6r").mean], ["V7-A", tr("V7-A").mean], ["V7-B", tr("B_base").mean], ["V7-C1", tr("C_rel").mean], ["V7-C2 (chọn)", tr("C_rel_absL3").mean], ["V7-D", tr("D_hier").mean]];
  const rows = MODELS.map(([n, v]) => [n, vn(v, 4), vn(v, 4), "KHỚP"]);
  table(s, ["Mô hình", "TB tính lại (m)", "TB báo cáo (m)", "Kết luận"], rows, MX, 1.5, 6.7, [2.4, 1.5, 1.5, 1.3], { size: 13, rowH: 0.38, align: ["left", "right", "right", "center"], hl: (i) => i === 7 });
  text(s, "Bảng trên là sheet **Tong_hop** của kiem_chung_V7_mean.xlsx (cột F: sai số từng mẫu =SQRT((x̂−x)^2+(ŷ−y)^2)*g; B3: =AVERAGE).", MX, 5.75, 6.7, 1.1, { fontSize: 13.5, color: GREY });
  card(s, MX + 7.0, 1.5, SW - 2 * MX - 7.0, 3.3, SOFT, "Excel: kiem_chung_V7_mean.xlsx", NAVY, TEAL);
  bullets(s, ["**Tong_hop**: 9 mô hình, cột Kết luận", "**V7C2_dung_lai_toa_do**: (x̂, ŷ) = SUMPRODUCT(30 trọng số, 30 tâm ô); lệch tối đa 9·10⁻¹⁰", "**Vi_du_mot_truy_van**: hàng 335 dựng bằng tay: 7,9938 và 4,6357 m", "**Dev_OOF**: V6* 6,2087; V7-C2 5,7017 m (19 861 vân tay)"], MX + 7.25, 2.1, SW - 2 * MX - 7.5, 2.6, 13.5);
  card(s, MX + 7.0, 5.0, SW - 2 * MX - 7.0, 1.85, SOFT2, "Python: kiem_tra_V7.py", RUST, RUST);
  text(s, "python kiem_tra_V7.py → 9 dòng KHỚP; V7-C2 dựng lại toạ độ: lệch 9,3·10⁻¹⁰, tổng trọng số = 1; dev khớp báo cáo; \"Tất cả khớp.\"", MX + 7.25, 5.55, SW - 2 * MX - 7.5, 1.25, { fontSize: 13.5 });
}
{
  const s = slide("Kiểm chứng · Cách 3: 16 phép kiểm độc lập", `verify_v7.py: ${D.verification.n_checks} phép kiểm, ${D.verification.n_failed} thất bại`,
    "Chương trình kiểm chứng không chạy mô hình: nó đọc tệp dự đoán, cells.csv, validationData.csv và siêu dữ liệu cache. Mười sáu phép đều đạt.");
  const nm = { "T1": "sai số TB/trung vị/P90 tính lại = báo cáo", "T2": "tọa độ = Σ w · tâm ô (lệch 9,3·10⁻¹⁰)", "T3": "w ≥ 0, hữu hạn, Σ w = 1 (|Σ−1| ≤ 2,1·10⁻¹⁵)", "T4": "không NaN / Inf trong tệp dự đoán", "T5": "mọi ô ứng viên nằm trên tầng được dự đoán", "T6": "các hàng test đúng là validationData (1 111 hàng)",
    "T7": "độ chính xác tầng/tòa tính lại từ nhãn", "T8": "V6 tái tạo khớp bản lưu (6,8658 vs 6,8614 m)", "T9": "V6 không đổi: git diff rỗng so với điểm gốc", "T10a": "fold rời nhau theo điện thoại; mỗi hàng đúng một fold", "T10b": "băm chỉ số cache khớp tính lại",
    "T11": "mọi cache dựng từ cùng trainingData.csv (SHA-256)", "T12": "không k-NN / so khớp vân tay thô (9 mô-đun)", "T13": "EFIM = vét cạn (86 test)", "T14": "tái lập theo seed: 3 biến thể × 6 fold trùng", "T15": "đào EFIM tái lập V6 (số HUI khớp)" };
  const checks = D.verification.checks;
  const rows = checks.map((c) => { const id = c.check.split(" ")[0]; return [id, nm[id] || c.check, c.ok ? "ĐẠT" : "LỆCH"]; });
  const half = Math.ceil(rows.length / 2), cw = (SW - 2 * MX - 0.3) / 2;
  table(s, ["#", "Phép kiểm", "KQ"], rows.slice(0, half), MX, 1.5, cw, [0.7, cw - 1.5, 0.8], { size: 12.5, rowH: 0.47, align: ["center", "left", "center"] });
  table(s, ["#", "Phép kiểm", "KQ"], rows.slice(half), MX + cw + 0.3, 1.5, cw, [0.7, cw - 1.5, 0.8], { size: 12.5, rowH: 0.47, align: ["center", "left", "center"] });
  text(s, "Test: pytest tests → 171 đạt, 1 bỏ qua (test rỗng có sẵn của V6); 15 test mới trong tests/test_v7.py (bất biến hợp nhất, gradient, tập hợp, cache, không k-NN, fold theo điện thoại, EFIM trên ô thật).", MX, 6.3, SW - 2 * MX, 0.6, { fontSize: 12.5, color: GREY });
}
{
  const nes = D.nested;
  const s = slide("Kiểm chứng · Rò rỉ, tái lập, độ tin cậy", "Không rò rỉ đo được, tái lập theo seed, khoảng tin cậy theo điện thoại",
    "Phép kiểm tra chặt cho fold ngoài số 2 đào lại 15 mô hình HUI không đọc vân tay fold 2; chênh lệch −0,0035 m. Hai lần chạy độc lập cho sai số theo fold trùng đến 3 chữ số. KTC lấy mẫu lại cả điện thoại.");
  card(s, MX, 1.5, 6.0, 2.55, SOFT, "Rò rỉ gián tiếp (lồng nhau)", NAVY, TEAL);
  bullets(s, [`Fold ngoài 2, 15 mô hình HUI đào lại, không vân tay fold 2 nào tới bộ chấm điểm`, `Giao thức chuẩn **${vn(nes.standard, 4)} m**; chặt **${vn(nes.strict, 4)} m**; chênh ${vnd(nes.diff, 4)} m`], MX + 0.3, 2.05, 5.5, 2.0, 14.5);
  card(s, MX, 4.2, 6.0, 2.65, SOFT, "Tái lập", NAVY, TEAL);
  bullets(s, ["Hai lần chạy độc lập (V7-B, C1, C2): sai số theo 6 fold trùng đến 3 chữ số", "Số HUI của 12 mô hình fold bằng đúng số của V6; L3 cuối 1 031 786 = số ghi trong summary.json của V6", "Đào EFIM và V6 không bị sửa (git diff rỗng)"], MX + 0.3, 4.75, 5.5, 2.0, 14);
  fcard(s, "fm_boot", MX + 6.3, 1.5, SW - 2 * MX - 6.3, 1.3);
  ann(s, [["B_{b}", "một lần lấy mẫu lại: chọn ngẫu nhiên có hoàn lại các điện thoại"], ["p, n", "điện thoại p và vân tay n của p"]], MX + 6.3, 2.95, SW - 2 * MX - 6.3, 0.95, 13.5);
  const rows = [["Test, V7-C2", `${vn(T7.mean, 3)} [${vn(T7.ci95_lo, 2)}; ${vn(T7.ci95_hi, 2)}]`], ["Test, chênh vs V6", `${vnd(T7.diff_vs_V6, 3)} [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}]`], ["Dev, chênh vs V6*", `${vnd(dI("C_rel_absL3")["diff_vs_V6*"], 3)} [${vnd(dI("C_rel_absL3").diff_lo, 2)}; ${vnd(dI("C_rel_absL3").diff_hi, 2)}]`]];
  table(s, ["Đại lượng", "Giá trị [KTC 95%]"], rows, MX + 6.3, 3.95, SW - 2 * MX - 6.3, [2.2, 3.5].map((x) => x * (SW - 2 * MX - 6.3) / 5.7), { size: 13, rowH: 0.42, align: ["left", "right"] });
  text(s, "KTC của trung bình rộng vì chỉ 11 (test) hoặc 16 (dev) cụm; KTC của **chênh lệch cặp** hẹp hơn và là điều cần đọc.", MX + 6.3, 5.85, SW - 2 * MX - 6.3, 1.0, { fontSize: 13.5, color: GREY });
}

// ================================================================== CHƯƠNG 6
divider(5, "Kết luận", ["Đạt gì, chưa đạt gì", "Hạn chế và hướng phát triển", "Ghi nhớ cho người mới học HUIM trong IPS"]);
{
  const s = slide("Kết luận", "Kết luận: V7 giảm sai số 8,1% nhưng chưa đạt mục tiêu dưới 6 m",
    "V7 đạt 6,309 m trên tập kiểm tra và 5,702 m trên dev. Mục tiêu dưới 6 m chưa đạt; phần còn lại nằm ở khâu chọn tầng và các ô lân cận khó phân biệt.");
  const cols = [
    ["Kết quả đạt được", TEAL, [`HUIM là lõi, **không k-NN**, không lưu vân tay`, `**${vn(T7.mean, 3)} m** trên test (V6 ${vn(T6.mean, 3)} m): ${vnd(T7.diff_vs_V6, 3)} m, KTC [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}]`, `dev ${vn(dI("C_rel_absL3").mean, 3)} m; trung vị ${vn(T7.median, 2)} m, P90 ${vn(T7.p90, 2)} m`, `**${D.verification.n_checks}/${D.verification.n_checks}** phép kiểm độc lập; Excel và Python khớp`]],
    ["Chưa đạt / hạn chế", RUST, ["Dưới 6 m **chưa đạt** (6,309 m); khoảng cách tới ô tiên tri còn lớn (0,59 m dev)", "Tập validation đã dùng nhiều lần; chưa có tập độc lập mới", "Đúng tầng 80,4% không cải thiện; sai tầng tốn thêm 2,3 m", "RAM +41%, thời gian +63%; chưa đánh giá bộ dữ liệu khác"]],
    ["Hướng phát triển", NAVY, ["Thêm góc nhìn HUI (θ khác nhau, rel mức-3)", "Ứng viên từ hai tầng tốt nhất; quyết định tầng học từ HUI", "HUI cấp vùng với θ thích ứng", "Tập kiểm tra độc lập; giảm RAM (ma trận thưa)"]]];
  const w = (SW - 2 * MX - 2 * 0.25) / 3;
  cols.forEach(([t, c, items], i) => { const x = MX + i * (w + 0.25); card(s, x, 1.55, w, 5.2, CARD, t, c, c); bullets(s, items, x + 0.3, 2.25, w - 0.5, 4.4, 15.5, INK, 10); });
}
{
  // slide tóm tắt cho người mới
  const s = slide("Ghi nhớ · Dành cho người mới học HUIM trong định vị trong nhà", "Tóm tắt một slide: lý thuyết và ví dụ để nhớ HUIM-IPS V7",
    "Slide ghi nhớ: bốn ô lý thuyết và ví dụ. Nguồn số liệu: BAOCAO/so_lieu_V7. Người mới chỉ cần nhớ: vân tay là giao dịch, AP là mục, cường độ là lợi ích, HUI là mẫu AP mạnh đặc trưng của ô; V7 học trọng số của 30 ô ứng viên bằng sai số mét.");
  const cw = (SW - 2 * MX - 0.3) / 2, ch = 2.62, y1 = 1.4, y2 = y1 + ch + 0.14;
  const panel = (x, y, num, title, lines, color) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: color === TEAL ? "E6F0F2" : color === RUST ? "F7EAE3" : color === GOLD ? "F6F0DC" : "EDF0F5" }, line: { color: LINE, width: 0.75 } });
    badge(s, x + 0.15, y + 0.12, num, color, 0.42);
    s.addText(title, { x: x + 0.68, y: y + 0.1, w: cw - 0.85, h: 0.45, fontFace: F, fontSize: 17, bold: true, color: NAVY, margin: 0, valign: "middle", isTextBox: true });
    s.addText(lines.map((t, i) => para(t).map((q, j, a) => ({ text: q.text, options: { ...q.options, breakLine: i < lines.length - 1 && j === a.length - 1 } }))).flat(),
      { x: x + 0.2, y: y + 0.62, w: cw - 0.4, h: ch - 0.68, fontFace: F, fontSize: 14, color: INK, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
  };
  const wap = (n) => "WAP" + String(n).padStart(3, "0");
  panel(MX, y1, 1, "Bài toán: vân tay Wi-Fi → vị trí", [
    "**Vân tay** = RSSI các AP nghe được (520 AP; 100 = không nghe). **Ô** = điểm tham chiếu (933 ô).",
    "Cần trả về (x̂, ŷ), tòa, tầng; sai số tính bằng **mét = 0,766126 × đơn vị tọa độ**.",
    `**Ví dụ:** hàng 335 nghe được ${EX.n_ap}/520 AP; ${wap(EX.aps[0].ap)}, ${wap(EX.aps[1].ap)} mạnh nhất (${EX.aps[0].rssi} dBm).`], TEAL);
  panel(MX + cw + 0.3, y1, 2, "HUIM: tập mục có lợi ích cao", [
    "**u(X)** = tổng q(i,T)·p(i) trên mọi giao dịch T ⊇ X và mọi i ∈ X; X là **HUI** khi u(X) ≥ minUtil; **EFIM** cắt tỉa bằng TWU, lu, su.",
    "Vân tay = giao dịch; AP = mục; cường độ → q ∈ [1,100]; p = 1. HUI = tổ hợp AP cùng mạnh đặc trưng của ô.",
    `**Ví dụ:** ô 351 có ${vn(C1.n_huis, 0)} HUI; HUI {${HX.items_ap.map(wap).join(", ")}}: u = ${vn(HX.u, 0)}, support ${vn(HX.support, 0)}.`], RUST);
  panel(MX, y2, 3, "Quy trình V7 (8 bước)", [
    "**1** EFIM mỗi ô, 5 góc nhìn → **2** điểm khớp P·V³ → tầng → **3** 30 ô ứng viên",
    "**4** 49 đặc trưng HUI → **5** tương đối + chuẩn hóa → **6** MLP chấm điểm s_{i}",
    "**7** w = softmax(s); (x̂, ŷ) = Σ w·tâm ô → **8** học bằng L = TB g·d(ĉ, c)",
    `**Ví dụ:** hàng 335: V6 sai ${vn(EX.v6.err_m, 2)} m; V7 sai **${vn(EX.v7.err_m, 2)} m**.`], NAVY);
  panel(MX + cw + 0.3, y2, 4, "Con số cần nhớ", [
    `**${vn(T7.mean, 3)} m** test (V6 ${vn(T6.mean, 3)}); dev ${vn(dI("C_rel_absL3").mean, 3)} m; mục tiêu < 6 m **chưa đạt**.`,
    `Đúng tòa ${pct(FIN.building_accuracy, 1)}, tầng ${pct(FIN.floor_accuracy, 1)}; ${vn(nHUI7 / 1e6, 2)} triệu HUI, 5 góc nhìn.`,
    "Giúp: **rel**, bộ chấm điểm trực tiếp. Không giúp: V7-A, bù lệch thiết bị, cấp tầng.",
    `Kiểm chứng: Excel + Python + ${D.verification.n_checks} phép kiểm; không k-NN.`], GOLD);
}

// ------------------------------------------------------------------ ghi file
const out = path.join(B, "Slide_HUIM_IPS_V7.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  const apply = process.env.PPTX_APPLY_THEME;
  if (apply && fs.existsSync(apply)) await require(apply).applyTheme(out, THEME);
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log("written", out, fs.statSync(out).size, "slides:", pres.slides.length);
});
