// BAOCAO/Slide_HUIM_IPS_UJIIndoorLoc.pptx — bài thuyết trình bảo vệ luận văn.
// Times New Roman cho mọi chữ; mọi sơ đồ (d01–d10) và biểu đồ (b01–b16) trong BAOCAO/diagram;
// số liệu đọc từ BAOCAO/so_lieu/du_lieu_bao_cao.json; công thức là ảnh mathtext (make_slide_formulas.py);
// ảnh nền vẽ từ dữ liệu UJIIndoorLoc (make_slide_art.py). Không dùng biểu tượng.
// Chạy: node src/baocao/build_slides.js   (cần npm "pptxgenjs", Python có matplotlib)
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const B = path.join(ROOT, "BAOCAO");
const D = JSON.parse(fs.readFileSync(path.join(B, "so_lieu", "du_lieu_bao_cao.json"), "utf8"));
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "slide_"));
execFileSync("python3", [path.join(__dirname, "make_slide_formulas.py"), TMP]);
execFileSync("python3", [path.join(__dirname, "make_slide_art.py"), TMP]);
const impF = path.join(ROOT, "results", "huim_only", "uji", "research", "importance.json");
const IMP = fs.existsSync(impF) ? JSON.parse(fs.readFileSync(impF, "utf8")) : null;

// ------------------------------------------------------------------ theme
const THEME = {
  name: "HUIM IPS", headFontFace: "Times New Roman", bodyFontFace: "Times New Roman",
  colors: { dk1: "1B2A3D", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F6F4EF", accent1: "2A7F8F", accent2: "B5532A",
            accent3: "8A8A85", accent4: "C9A227", accent5: "4C6A88", accent6: "9BB7C4", hlink: "2A7F8F", folHlink: "4C6A88" },
};
const K = THEME.colors;
const INK = K.dk1, NAVY = K.dk2, PAPER = K.lt2, TEAL = K.accent1, RUST = K.accent2, GREY = K.accent3, GOLD = K.accent4;
const LINE = "D8D3C8", SOFT = "E6F0F2", SOFT2 = "F7EAE3", CARD = "FBFAF7";
const F = "Times New Roman";

const vn = (x, k = 2) => Number(x).toFixed(k).replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
const pct = (x, k = 1) => vn(100 * x, k) + "%";
const U = D.datasets.uji, UT = U.tests.validationData, SEL = U.selection, PRM = SEL.params;
const V6 = U.v6, U4 = U.v4_tests.validationData, RSH = V6.research.dev_mean_m;
const allTests = [];
D.order.forEach((k) => Object.entries(D.datasets[k].tests).forEach(([t, v]) => allTests.push({ k, t, v })));
const nOk = allTests.filter((x) => x.v.duoi_7m).length;
const split = D.uji_floor_split;
const refU = D.references.find((x) => x.dataset === "uji");
const others = allTests.filter((x) => x.k !== "uji");
const nHUI3 = U.model.n_huis + V6.n_huis_L3 + V6.n_huis_abs;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13,33 × 7,5 in
pres.theme = { headFontFace: F, bodyFontFace: F };
pres.title = "Ứng dụng HUIM trong hệ thống định vị trong nhà";
pres.subject = "Bảo vệ luận văn thạc sĩ Khoa học máy tính";
const SW = 13.333, SH = 7.5, MX = 0.6;
const CHAPTERS = ["Mở đầu", "Cơ sở lý thuyết", "Mô hình đề xuất", "Thực nghiệm", "Kết luận"];

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
function tracker(s) {                       // dải tiến độ theo chương ở chân slide
  const w = 1.75;
  CHAPTERS.forEach((c, i) => {
    const x = MX + i * (w + 0.08), on = i === curChap;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 7.1, w, h: 0.05, fill: { color: on ? TEAL : "E3E0D8" }, line: { color: on ? TEAL : "E3E0D8" } });
    s.addText(`${i + 1}. ${c}`, { x, y: 7.15, w, h: 0.25, fontFace: F, fontSize: 9.5, color: on ? NAVY : GREY,
      bold: on, margin: 0, isTextBox: true });
  });
}
function slide(kicker, title, notes) {
  const s = pres.addSlide({ masterName: "NOI_DUNG", sectionTitle: curSection });
  s.addText(kicker.toUpperCase(), { x: MX, y: 0.24, w: 9, h: 0.3, fontFace: F, fontSize: 12, bold: true,
    color: TEAL, charSpacing: 1.5, margin: 0, isTextBox: true });
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
  s.addText(String(i + 1).padStart(2, "0"), { x: MX, y: 1.3, w: 3, h: 1.6, fontFace: F, fontSize: 110, bold: true,
    color: "7FB3BF", margin: 0, isTextBox: true });
  s.addText(title, { x: MX, y: 3.0, w: 8.5, h: 1.0, fontFace: F, fontSize: 38, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.15, w: 2.6, h: 0, line: { color: GOLD, width: 2 } });
  s.addText(items.map((t, k) => ({ text: t, options: { breakLine: k < items.length - 1 } })),
    { x: MX, y: 4.35, w: 8, h: 2.4, fontFace: F, fontSize: 18, color: "DCE6EE", valign: "top", paraSpaceAfter: 6, margin: 0, isTextBox: true });
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
const dg = (f) => path.join(B, "diagram", f);
const fx = (f) => path.join(TMP, f + ".png");
function para(text) {                 // **đậm**, _{dưới}, ^{trên}
  return text.split(/(\*\*[^*]+\*\*|_\{[^}]*\}|\^\{[^}]*\})/).filter(Boolean).map((p) =>
    p.startsWith("**") ? { text: p.slice(2, -2), options: { bold: true } }
      : p.startsWith("_{") ? { text: p.slice(2, -1), options: { subscript: true } }
      : p.startsWith("^{") ? { text: p.slice(2, -1), options: { superscript: true } }
      : { text: p, options: {} });
}
function bullets(s, items, x, y, w, h, size = 17, color = INK) {
  // pptxgenjs ghi pPr cho từng run; đặt bullet + align cho mọi run để đoạn nhiều run vẫn một gạch đầu dòng
  const runs = [];
  items.forEach((t, i) => {
    const r = para(t).map((q) => ({ text: q.text, options: { ...q.options, bullet: { indent: 20 }, align: "left", paraSpaceAfter: 9 } }));
    if (i < items.length - 1) r[r.length - 1].options.breakLine = true;
    runs.push(...r);
  });
  s.addText(runs, { x, y, w, h, fontFace: F, fontSize: size, color, valign: "top", margin: 2, isTextBox: true });
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(para(t), { x, y, w, h, fontFace: F, fontSize: 17, color: INK, valign: "top", margin: 0, isTextBox: true, ...o });
}
function stat(s, x, y, w, value, label, color = NAVY, size = 40) {
  s.addText(value, { x, y, w, h: 0.8, fontFace: F, fontSize: size, bold: true, color, margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.82, w, h: 0.6, fontFace: F, fontSize: 13.5, color: GREY, margin: 0, valign: "top", isTextBox: true });
}
function card(s, x, y, w, h, fill = CARD, title, tcolor = NAVY, edge = null) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: LINE, width: 0.75 },
    shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 4, offset: 1.5, angle: 90 } });
  if (edge) s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h, fill: { color: edge }, line: { color: edge } });
  if (title) s.addText(title, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: 0.45, fontFace: F, fontSize: 18, bold: true,
    color: tcolor, margin: 0, isTextBox: true });
}
function badge(s, x, y, n, color = TEAL) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color }, line: { color } });
  s.addText(String(n), { x, y, w: 0.5, h: 0.5, fontFace: F, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function table(s, header, rows, x, y, w, colW, o = {}) {
  const hd = header.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center", valign: "middle" } }));
  const body = rows.map((r, i) => r.map((c, j) => ({ text: String(c), options: {
    fill: { color: (o.hl && o.hl(i)) ? SOFT2 : (i % 2 ? "F7F6F2" : "FFFFFF") },
    align: (o.align && o.align[j]) || "left", valign: "middle", bold: !!(o.hl && o.hl(i)) } })));
  s.addTable([hd, ...body], { x, y, w, colW, fontFace: F, fontSize: o.size || 14, color: INK,
    border: { type: "solid", pt: 0.5, color: LINE }, rowH: o.rowH || 0.38, margin: [2, 6, 2, 6] });
}
function figSlide(kicker, title, file, bulletsList, notes, imgW = 8.4) {
  const s = slide(kicker, title, notes);
  const r = img(s, dg(file), MX, 1.5, imgW, 5.3, "left", title);
  if (bulletsList) bullets(s, bulletsList, r.x + r.w + 0.35, 1.6, SW - MX - (r.x + r.w + 0.35), 5.2, 16);
  return s;
}

// ================================================================== 1. tiêu đề
pres.addSection({ title: "Giới thiệu" });
{
  const s = pres.addSlide({ masterName: "TOI", sectionTitle: "Giới thiệu" });
  s.background = { path: path.join(TMP, "art_title.png") };
  s.addText("LUẬN VĂN THẠC SĨ KHOA HỌC MÁY TÍNH", { x: MX, y: 0.7, w: 8, h: 0.4, fontFace: F, fontSize: 15, bold: true,
    color: "9BC4CD", charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Ứng dụng thuật toán khai thác tập mục lợi ích cao (HUIM) trong hệ thống định vị trong nhà",
    { x: MX, y: 1.35, w: 7.4, h: 2.6, fontFace: F, fontSize: 38, bold: true, color: "FFFFFF", valign: "top", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.2, w: 2.6, h: 0, line: { color: GOLD, width: 2.5 } });
  s.addText("Định vị bằng so khớp High Utility Itemset trên vân tay Wi-Fi — không dùng k-NN",
    { x: MX, y: 4.35, w: 7.4, h: 0.6, fontFace: F, fontSize: 19, italic: true, color: "DCE6EE", margin: 0, isTextBox: true });
  s.addText([
    { text: "Học viên: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Người hướng dẫn khoa học: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Năm 2026", options: {} },
  ], { x: MX, y: 5.25, w: 7, h: 1.5, fontFace: F, fontSize: 17, color: "FFFFFF", paraSpaceAfter: 6, margin: 0, isTextBox: true });
  s.addText("Nền: bản đồ điểm khảo sát UJIIndoorLoc; chấm màu là vân tay kiểm tra theo sai số", { x: 8.0, y: 7.0, w: 5.0, h: 0.3,
    fontFace: F, fontSize: 10, italic: true, color: "9BB7C4", align: "right", margin: 0, isTextBox: true });
  s.addNotes("Kính thưa hội đồng. Luận văn trình bày cách dùng thuật toán khai thác tập mục lợi ích cao làm thuật toán định vị chính của một hệ thống định vị trong nhà dựa trên vân tay Wi-Fi, không dùng k-NN.");
}

// ================================================================== 2. nội dung
{
  const s = slide("Nội dung", "Nội dung trình bày");
  const d = [["Mở đầu", "Bối cảnh, vấn đề của các giai đoạn trước, câu hỏi và mục tiêu nghiên cứu"],
    ["Cơ sở lý thuyết", "Định vị vân tay, bài toán HUIM, thuật toán EFIM, Gradient Boosting, độ đo"],
    ["Mô hình đề xuất", "Tám bước từ vân tay Wi-Fi tới toạ độ, mọi quyết định dựa trên HUI"],
    ["Thực nghiệm", "Sáu bộ dữ liệu, giao thức không rò rỉ, kết quả, phân tích và kiểm chứng"],
    ["Kết luận", "Kết quả đạt được, hạn chế và hướng phát triển"]];
  const w = (SW - 2 * MX - 4 * 0.25) / 5;
  d.forEach(([t, s2], i) => {
    const x = MX + i * (w + 0.25);
    card(s, x, 1.75, w, 4.6, i % 2 ? CARD : SOFT, null, NAVY, TEAL);
    s.addText(String(i + 1).padStart(2, "0"), { x: x + 0.3, y: 2.0, w: w - 0.5, h: 1.0, fontFace: F, fontSize: 48, bold: true, color: TEAL, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.3, y: 3.15, w: w - 0.5, h: 0.9, fontFace: F, fontSize: 21, bold: true, color: NAVY, margin: 0, valign: "top", isTextBox: true });
    s.addText(s2, { x: x + 0.3, y: 4.1, w: w - 0.5, h: 2.1, fontFace: F, fontSize: 15, color: INK, margin: 0, valign: "top", isTextBox: true });
  });
}

// ================================================================== CHƯƠNG 1
divider(0, "Mở đầu", ["Bối cảnh định vị trong nhà", "HUIM ở các giai đoạn trước: chỉ là bước lọc AP", "Câu hỏi, mục tiêu và đóng góp"]);
{
  const s = slide("Mở đầu · Bối cảnh", "Định vị trong nhà bằng vân tay Wi-Fi",
    "Trong nhà tín hiệu vệ tinh suy giảm; vân tay Wi-Fi dùng hạ tầng AP sẵn có. Hai pha: khảo sát ghi RSSI tại các điểm tham chiếu; định vị so vân tay mới với dữ liệu khảo sát.");
  card(s, MX, 1.6, 5.9, 2.4, SOFT, "Pha khảo sát (offline)", TEAL, TEAL);
  text(s, "Ghi vectơ RSSI của mọi AP tại các **điểm tham chiếu** đã biết toạ độ, tầng, toà nhà.", MX + 0.3, 2.2, 5.4, 1.6, { fontSize: 16 });
  card(s, MX + 6.3, 1.6, 5.9, 2.4, SOFT2, "Pha định vị (online)", RUST, RUST);
  text(s, "So **vân tay mới** với mô hình học từ dữ liệu khảo sát để suy ra toạ độ, tầng, toà nhà.", MX + 6.6, 2.2, 5.4, 1.6, { fontSize: 16 });
  text(s, "**Khó khăn chính**", MX, 4.3, 6, 0.4, { fontSize: 18, color: NAVY });
  bullets(s, ["Tín hiệu dao động theo thời gian và người dùng", "Điện thoại khác nhau đọc RSSI khác nhau",
    "Tín hiệu chồng lấn giữa các tầng liền kề", "Vectơ thưa: mỗi vân tay chỉ thấy vài chục trong hàng trăm AP"], MX, 4.8, 6.5, 2.1, 16);
  const d0 = D.datasets.uji.description;
  stat(s, MX + 7.0, 4.3, 2.6, `${d0.so_ap}`, "AP trong UJIIndoorLoc", NAVY);
  stat(s, MX + 9.6, 4.3, 2.6, `${d0.so_lop_toa_tang}`, "tòa – tầng (3 toà nhà)", TEAL);
  stat(s, MX + 7.0, 5.65, 2.6, vn(d0.mau_huan_luyen, 0), "vân tay huấn luyện", NAVY, 34);
  stat(s, MX + 9.6, 5.65, 2.6, vn(d0.ap_tb_moi_fp, 1), "AP phát hiện mỗi vân tay", TEAL, 34);
}
{
  const s = slide("Mở đầu · Vấn đề", "HUIM phải là thuật toán định vị, không chỉ là bước lọc AP",
    `Ở các phiên bản trước, HUIM chỉ chọn tập AP rồi k-NN định vị; HUIM chỉ đóng góp khoảng 6% mức giảm sai số. Bỏ HUIM, k-NN vẫn định vị được.`);
  const y = 1.6, h = 3.75, w = 5.85;
  card(s, MX, y, w, h, SOFT2, "Trước: HUIM là nhánh tiền xử lý", RUST, RUST);
  bullets(s, ["HUIM chọn tập AP; **k-NN** so khoảng cách vân tay và quyết định vị trí",
    `HUI toàn cục: còn ${refU.huim_toan_cuc_so_ap}/${refU.tong_ap} AP, sai số ${vn(refU.huim_toan_cuc_knn_m)} m`,
    `HUI theo tòa–tầng: ${refU.huim_chon_ap_so_ap}/${refU.tong_ap} AP, sai số ${vn(refU.huim_chon_ap_knn_m)} m`,
    "Phân tích Shapley: HUIM đóng góp khoảng **6%** mức giảm sai số"], MX + 0.3, y + 0.75, w - 0.5, h - 0.9, 16);
  const x2 = MX + w + 0.43;
  card(s, x2, y, w, h, SOFT, "Đề xuất: HUIM là mô hình định vị", TEAL, TEAL);
  bullets(s, ["Mỗi điểm tham chiếu là một **ô**; vân tay của ô là một cơ sở dữ liệu giao dịch",
    "EFIM khai thác tập HUI của từng ô; **tập HUI chính là mô hình**",
    "Tầng, ô ứng viên và toạ độ suy ra từ **bằng chứng HUI**; không k-NN, không lưu vân tay",
    "Bỏ HUIM thì hệ thống không còn mô hình để định vị"], x2 + 0.3, y + 0.75, w - 0.5, h - 0.9, 16);
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 5.6, w: SW - 2 * MX, h: 1.15, fill: { color: NAVY }, line: { color: NAVY } });
  text(s, "**Câu hỏi nghiên cứu:** có thể xây dựng hệ thống định vị trong đó HUIM là thuật toán định vị chính, không dùng k-NN, mà vẫn đạt sai số trung bình **dưới 7 m** hay không?",
    MX + 0.3, 5.75, SW - 2 * MX - 0.6, 0.9, { fontSize: 17, color: "FFFFFF", valign: "middle" });
}
{
  const s = slide("Mở đầu · Mục tiêu", "Mục tiêu và đóng góp của luận văn");
  const goals = ["Mô hình hoá vân tay Wi-Fi thành các cơ sở dữ liệu giao dịch có lợi ích theo từng điểm tham chiếu",
    "Mô hình định vị mà mô hình là tập HUI; mọi quyết định dựa trên bằng chứng HUI",
    "Sai số trung bình dưới 7 m trên tập kiểm tra, giao thức không rò rỉ dữ liệu",
    "Kiểm chứng độc lập mọi con số; mã nguồn và số liệu để tái lập"];
  goals.forEach((g, i) => { badge(s, MX, 1.7 + i * 0.95, i + 1); text(s, g, MX + 0.7, 1.75 + i * 0.95, 5.6, 0.85, { fontSize: 16 }); });
  card(s, MX + 6.6, 1.6, SW - 2 * MX - 6.6, 5.15, CARD, "Đóng góp", NAVY, GOLD);
  bullets(s, ["Ba định nghĩa lợi ích nội (abs, rel, rank) và ngưỡng tương đối theo ô có **tự nâng ngưỡng**, bảo đảm tập HUI đầy đủ",
    "Thuật toán định vị **tám bước** chỉ dựa trên HUI, kể cả hồ sơ cường độ và độ phủ ngược suy ra từ HUI",
    `**${nOk}/${allTests.length}** tập kiểm tra của ${D.order.length} bộ dữ liệu dưới 7 m; phân tích định lượng nguồn sai số`,
    `**${D.verification.n_checks}** phép kiểm chứng độc lập, 0 thất bại`], MX + 6.9, 2.25, SW - 2 * MX - 7.2, 4.4, 16);
}

// ================================================================== CHƯƠNG 2
divider(1, "Cơ sở lý thuyết", ["Bài toán khai thác tập mục lợi ích cao", "Thuật toán EFIM và các chặn trên", "Gradient Boosting và độ đo đánh giá"]);
{
  const s = slide("Cơ sở lý thuyết · HUIM", "Bài toán khai thác tập mục lợi ích cao",
    "Mỗi mục có lợi ích nội trong từng giao dịch và lợi ích ngoài. Lợi ích của tập mục là tổng trên mọi giao dịch chứa nó; lợi ích không đơn điệu giảm nên cần chặn trên TWU.");
  card(s, MX, 1.55, 5.9, 3.9, CARD);
  img(s, fx("f_util"), MX + 0.35, 1.8, 5.2, 3.4, "left", "Định nghĩa lợi ích");
  text(s, "**Ánh xạ sang định vị Wi-Fi**", MX + 6.4, 1.6, 5.9, 0.4, { fontSize: 18, color: NAVY });
  table(s, ["HUIM", "Định vị vân tay"], [["mục i", "một AP"], ["giao dịch T", "một vân tay (một lần quét)"],
    ["lợi ích nội q(i,T)", "cường độ RSSI đã chuẩn hoá"], ["lợi ích ngoài p(i)", "đặt bằng 1"],
    ["cơ sở dữ liệu D", "các vân tay của một điểm tham chiếu"]], MX + 6.4, 2.1, 5.9, [2.4, 3.5], { size: 15, rowH: 0.45 });
  card(s, MX, 5.65, SW - 2 * MX, 1.1, SOFT, null, NAVY, TEAL);
  text(s, "**Không đơn điệu:** thêm một mục có thể làm u(X) tăng hoặc giảm → cắt tỉa bằng chặn trên **TWU** (đóng xuống: X ⊆ Y ⇒ TWU(Y) ≤ TWU(X)).",
    MX + 0.35, 5.8, SW - 2 * MX - 0.7, 0.85, { fontSize: 16, valign: "middle" });
}
{
  const s = slide("Cơ sở lý thuyết · EFIM", "Thuật toán EFIM (Zida và cộng sự, 2017)",
    "EFIM duyệt cây liệt kê tập theo chiều sâu, mục sắp theo TWU tăng dần. Hai chặn trên lu và su tính trong một lần quét cơ sở dữ liệu đã chiếu.");
  card(s, MX, 1.55, 7.3, 3.35, CARD);
  img(s, fx("f_efim"), MX + 0.3, 1.8, 6.7, 2.9, "left", "Chặn trên của EFIM");
  const steps = ["Tính TWU, loại mục TWU < minUtil, sắp mục", "Chiếu và gộp giao dịch giống nhau",
    "Duyệt sâu: lu < minUtil → loại mục khỏi cây con", "su < minUtil → không duyệt nhánh", "Xuất mọi X có u(X) ≥ minUtil"];
  steps.forEach((t, i) => { badge(s, MX + 7.7, 1.6 + i * 0.68, i + 1, i < 2 ? TEAL : NAVY); text(s, t, MX + 8.35, 1.66 + i * 0.68, 4.3, 0.6, { fontSize: 15.5 }); });
  card(s, MX, 5.15, SW - 2 * MX, 1.6, SOFT, null, NAVY, TEAL);
  text(s, "**Trong luận văn:** EFIM cài đặt lại trong ma_nguon/src/huim/efim.py, kiểm thử khớp hoàn toàn với thuật toán vét cạn; thêm ngân sách thời gian và số HUI để dùng cho cơ chế **tự nâng ngưỡng** theo từng ô.",
    MX + 0.35, 5.3, SW - 2 * MX - 0.7, 1.3, { fontSize: 16, valign: "middle" });
}
{
  const s = slide("Cơ sở lý thuyết · Độ đo", "Độ đo đánh giá và Gradient Boosting",
    "Sai số định vị là khoảng cách Euclid theo mét thực địa; UJIIndoorLoc dùng Web Mercator nên nhân 0,766126. Gradient Boosting cộng dồn các cây hồi quy nhỏ, mỗi cây học phần dư.");
  card(s, MX, 1.55, 6.1, 2.4, CARD, "Sai số định vị", NAVY, TEAL);
  img(s, fx("f_err"), MX + 0.3, 2.25, 5.5, 1.0, "left", "Sai số");
  text(s, "g = 0,766126 (UJIIndoorLoc, Web Mercator); g = 1 cho các bộ khác. Báo cáo thêm trung vị, p75, p90 và độ chính xác tòa–tầng.", MX + 0.3, 3.3, 5.5, 0.6, { fontSize: 13.5, color: GREY });
  card(s, MX + 6.4, 1.55, SW - 2 * MX - 6.4, 2.4, CARD, "Gradient Boosting [Friedman 2001]", NAVY, RUST);
  bullets(s, ["Mô hình là tổng của nhiều cây hồi quy nhỏ, mỗi cây học phần dư của các cây trước",
    "Biến thể histogram (LightGBM, scikit-learn) học nhanh trên hàng trăm nghìn mẫu",
    "Chỉ dùng ở **Bước 8** để cân các bằng chứng rút ra từ HUI"], MX + 6.7, 2.2, SW - 2 * MX - 7.0, 1.7, 15);
  card(s, MX, 4.2, SW - 2 * MX, 2.55, SOFT, "Giao thức chọn mô hình", TEAL, TEAL);
  bullets(s, ["Mọi tham số chọn trên **6 fold kiểm định (dev)** tách từ tập huấn luyện; UJIIndoorLoc giữ lại theo **điện thoại** (9/11 điện thoại kiểm tra là thiết bị lạ)",
    "Tập kiểm tra chỉ chấm **một lần** cho mỗi phiên bản; mọi phiên bản đều được ghi lại",
    "Kiểm chứng độc lập bằng chương trình không gọi EFIM hay bộ định vị, sổ Excel và script thư viện chuẩn"], MX + 0.3, 4.8, SW - 2 * MX - 0.6, 1.9, 15.5);
}

// ================================================================== CHƯƠNG 3
divider(2, "Mô hình đề xuất", ["Tám bước từ vân tay Wi-Fi tới toạ độ", "Mô hình chỉ gồm tập HUI của các ô", "Bước 8: xếp hạng lại bằng bằng chứng HUI"]);
{
  const s = slide("Mô hình đề xuất · Tổng quan", "Hệ thống định vị dựa trên HUIM: hai pha, tám bước",
    "Huấn luyện: lợi ích nội, cơ sở dữ liệu theo ô, EFIM, mô hình. Định vị: chấm điểm, làm mượt và chọn tầng, ô ứng viên, xếp hạng lại.");
  img(s, dg("d01_tong_quan.png"), MX, 1.45, SW - 2 * MX, 5.4, "center", "Sơ đồ tổng quát");
}
{
  const s = slide("Mô hình đề xuất · Bước 1", "Từ cường độ tín hiệu tới lợi ích nội",
    "Ba dạng lợi ích nội abs, rel, rank. Rank bất biến với mọi biến đổi đơn điệu của thang RSSI, phù hợp với điện thoại lạ, và được chọn trên dev.");
  const r = img(s, dg("d02_buoc1_utility.png"), MX, 1.45, 7.7, 5.4, "left", "Bước 1");
  const x = r.x + r.w + 0.35, w = SW - MX - x;
  card(s, x, 1.55, w, 1.35, CARD);
  img(s, fx("f_rank"), x + 0.15, 1.7, w - 0.3, 1.05, "left", "Lợi ích rank");
  const p = D.pilots["theta_pilot.json"].phone_folds_theta20_all6_dev_mean_m;
  bullets(s, ["n_{T}: số AP thấy được; r_{T}(i): thứ hạng cường độ của AP i",
    `Dev: **rank ${vn(p.rank)} m**, abs ${vn(p.abs)} m, rel ${vn(p.rel)} m`,
    "Bền với khác biệt giữa các điện thoại"], x, 3.15, w, 3.6, 15.5);
}
{
  const s = slide("Mô hình đề xuất · Bước 2 và 3", "Mỗi ô là một cơ sở dữ liệu giao dịch; EFIM khai thác HUI của ô",
    `Ngưỡng minUtil tương đối theo ô; vượt ngân sách thì θ nhân 1,25 và khai thác lại tới khi hoàn tất. UJIIndoorLoc: ${U.mining.o_phai_nang_theta}/${U.model.n_cells} ô phải nâng θ.`);
  card(s, MX, 1.45, SW - 2 * MX, 0.75, CARD);
  img(s, fx("f_cell"), MX + 0.3, 1.55, 9, 0.55, "left", "Ngưỡng theo ô");
  const w = (SW - 2 * MX - 0.3) / 2;
  img(s, dg("d03_buoc2_o_giao_dich.png"), MX, 2.35, w, 3.65, "center", "Bước 2");
  img(s, dg("d04_buoc3_efim.png"), MX + w + 0.3, 2.35, w, 3.65, "center", "Bước 3");
  text(s, `**${U.model.n_cells} ô**, trung bình ${vn(U.mining.giao_dich_tb_moi_o, 1)} giao dịch/ô · θ = ${vn(SEL.theta_pct, 0)}% · ngân sách 10 s hoặc 10 000 HUI · θ trung vị thực dùng ${vn(U.mining.theta_trung_vi_dung)}%`,
    MX, 6.25, SW - 2 * MX, 0.6, { fontSize: 15.5, align: "center" });
}
{
  const s = slide("Mô hình đề xuất · Bước 4", "Mô hình định vị là tập HUI của mọi ô — không lưu vân tay",
    "Mô hình chỉ gồm HUI cùng toạ độ trọng tâm và nhãn tòa-tầng của từng ô. Không lưu vân tay huấn luyện nên không thể so khoảng cách vân tay như k-NN.");
  const r = img(s, dg("d05_buoc4_mo_hinh.png"), MX, 1.45, 8.2, 5.4, "left", "Bước 4");
  const x = r.x + r.w + 0.45, w = SW - MX - x;
  stat(s, x, 1.65, w, vn(U.model.n_huis, 0), "HUI trong mô hình chính", NAVY, 36);
  stat(s, x, 3.15, w, vn(nHUI3, 0), "HUI của cả ba mô hình (Bước 8)", TEAL, 36);
  stat(s, x, 4.65, w, "0", "vân tay huấn luyện được lưu", RUST, 44);
}
{
  const s = slide("Mô hình đề xuất · Bước 5", "Chấm điểm khớp giữa vân tay và HUI của ô",
    "ρ: tỷ lệ mục của HUI có trong vân tay; agree: mức phù hợp cường độ; P_c: khối lượng HUI của ô mà vân tay chứa; V_c: phần vân tay được HUI của ô giải thích.");
  card(s, MX, 1.45, 6.4, 3.45, CARD);
  img(s, fx("f_score"), MX + 0.25, 1.65, 5.9, 3.05, "left", "Điểm khớp");
  bullets(s, ["ρ: khớp mềm, chịu được AP bị bỏ sót", "agree: phạt chênh lệch cường độ, thang τ",
    "P_{c}: khối lượng HUI của ô có trong vân tay", "V_{c}: phần vân tay được HUI của ô giải thích"], MX, 5.1, 6.4, 1.8, 15);
  img(s, dg("d06_buoc5_cham_diem.png"), MX + 6.7, 1.45, SW - 2 * MX - 6.7, 5.4, "right", "Bước 5");
}
{
  const s = slide("Mô hình đề xuất · Bước 6", "Làm mượt không gian và chọn tầng",
    `Điểm mỗi ô được cộng điểm các ô cùng tầng bằng nhân Gauss σ = ${PRM.sigma} m; tầng là tầng có trung bình k_f = ${PRM.kf} điểm lớn nhất cao nhất.`);
  card(s, MX, 1.45, SW - 2 * MX, 1.75, CARD);
  img(s, fx("f_smooth"), MX + 0.3, 1.58, 8.6, 1.5, "left", "Làm mượt");
  text(s, `σ = ${PRM.sigma} m,  k_{f} = ${PRM.kf}`, MX + 9.3, 1.75, 2.9, 0.5, { fontSize: 19, color: TEAL, bold: true });
  text(s, "chọn trên dev", MX + 9.3, 2.3, 2.9, 0.4, { fontSize: 15, color: GREY });
  img(s, dg("d07_buoc6_lam_muot_tang.png"), MX, 3.35, SW - 2 * MX, 3.5, "center", "Bước 6");
}
{
  const s = slide("Mô hình đề xuất · Bước 7", "Ô ứng viên và ước lượng ban đầu",
    `${V6.k_candidates} ô điểm cao nhất của tầng là ô ứng viên. Ước lượng ban đầu (v4) là trọng tâm của ${PRM.m} ô tốt nhất. Trong 12 ô đó có ô cách vị trí thật 2,4 m nhưng ô điểm cao nhất cách 8,8 m: cần xếp hạng lại.`);
  const r = img(s, dg("d08_buoc7_toa_do.png"), MX, 1.45, 7.2, 5.4, "left", "Bước 7");
  const x = r.x + r.w + 0.4, w = SW - MX - x;
  card(s, x, 1.55, w, 1.4, CARD);
  img(s, fx("f_coord"), x + 0.15, 1.7, w - 0.3, 1.1, "left", "Trọng tâm");
  stat(s, x, 3.25, w / 2 - 0.1, "2,4 m", "ô gần nhất trong 12 ô", TEAL, 34);
  stat(s, x + w / 2, 3.25, w / 2, "8,8 m", "ô điểm cao nhất", RUST, 34);
  text(s, "Tập ứng viên **đúng vùng**, nhưng một điểm khớp duy nhất **không sắp đúng thứ tự** các ô lân cận → Bước 8.", x, 4.75, w, 1.8, { fontSize: 16 });
}
{
  const s = slide("Mô hình đề xuất · Bước 8", "Xếp hạng lại ô ứng viên bằng bằng chứng HUI",
    `Mỗi ô ứng viên có ${V6.n_features} đặc trưng tính từ HUI: ba mô hình HUI (rank, mục theo mức cường độ, abs), hồ sơ cường độ suy ra từ HUI, độ đồng thuận không gian. Bộ hồi quy Gradient Boosting học trên dev dự đoán khoảng cách ô tới vị trí thật.`);
  const r = img(s, dg("d09_buoc8_xep_hang_lai.png"), MX, 1.4, 8.3, 3.3, "left", "Bước 8");
  card(s, MX, r.y + r.h + 0.1, 8.3, 6.85 - (r.y + r.h + 0.1), CARD);
  img(s, fx("f_rerank"), MX + 0.2, r.y + r.h + 0.2, 7.9, 6.75 - (r.y + r.h + 0.25), "left", "Công thức Bước 8");
  const x = MX + 8.65, w = SW - MX - x;
  bullets(s, [`Ba mô hình HUI: rank, mức cường độ (L = 3), abs — tổng **${vn(nHUI3 / 1e6, 2)} triệu HUI**`,
    "Hồ sơ cường độ q̂_{c}(i) suy ra **từ HUI của ô**",
    "Bộ hồi quy học **chỉ trên fold dev**, nhãn = khoảng cách ô – vị trí thật",
    `Toạ độ: trọng tâm ${V6.m} ô dự đoán gần nhất, λ = ${vn(V6.lam, 0)} m`,
    `Dev: **${vn(V6.dev_mean_v4_m)} → ${vn(V6.dev_mean_m)} m**`], x, 1.5, w, 5.3, 15);
}
{
  const s = slide("Mô hình đề xuất · Bước 8", "Năm nhóm bằng chứng HUI và vai trò của bộ hồi quy",
    "Bộ hồi quy không thấy vân tay huấn luyện nào; chỉ cân các bằng chứng do HUI tạo ra. Ô được xét vẫn là ô điểm HUI cao nhất; toạ độ là tổ hợp lồi của tâm các ô đó.");
  table(s, ["Nhóm bằng chứng", "Đặc trưng", "Số"], [
    ["Điểm khớp HUI (rank)", "S, P (γ = 1, 2), V, R, P với IDF của HUI, thứ hạng", "10"],
    ["Đồng thuận không gian", "khoảng cách tới ước lượng ban đầu, tới ô đầu, mật độ ứng viên", "4"],
    ["Mô hình mức cường độ", "P, V, điểm, thứ hạng, MAE và cosin hồ sơ", "6"],
    ["Hồ sơ cường độ (rank)", "MAE, tương quan, cosin, khối lượng AP mạnh nhất, số AP chung", "5"],
    ["Mô hình lợi ích abs", "P, V, R, điểm, thứ hạng, MAE, tương quan, cosin", "8"],
  ], MX, 1.55, IMP ? 6.6 : SW - 2 * MX, IMP ? [2.0, 4.0, 0.6] : [3.0, 7.5, 1.6], { size: 13, rowH: 0.5, align: ["left", "left", "center"] });
  if (IMP) img(s, dg("b10_dong_gop_bang_chung.png"), MX + 6.9, 1.5, SW - 2 * MX - 6.9, 3.4, "right", "Đóng góp nhóm bằng chứng");
  card(s, MX, 4.95, SW - 2 * MX, 1.8, SOFT2, null, NAVY, RUST);
  text(s, `**Nói rõ với hội đồng:** bộ hồi quy chỉ nhận bằng chứng do HUI tạo ra và chỉ chọn giữa các ô có điểm HUI cao nhất; bỏ HUIM thì không còn ứng viên lẫn đặc trưng. Nhưng việc **cân** các bằng chứng là do học máy; phiên bản không dùng bộ hồi quy (Bước 1–7) đạt **${vn(U4.mean_err_m)} m** trên UJIIndoorLoc.`,
    MX + 0.35, 5.1, SW - 2 * MX - 0.7, 1.55, { fontSize: 16, valign: "middle" });
}

// ================================================================== CHƯƠNG 4
divider(3, "Thực nghiệm và đánh giá", ["Sáu bộ dữ liệu, giao thức không rò rỉ", `${nOk}/${allTests.length} tập kiểm tra dưới 7 m`, "Phân tích, so sánh và kiểm chứng"]);
figSlide("Thực nghiệm · Dữ liệu", "Sáu bộ dữ liệu thực nghiệm", "b13_mo_ta_du_lieu.png", null,
  "UJIIndoorLoc lớn và khó nhất: ba toà nhà, 13 tòa-tầng, 520 AP. HUS có bản khử trùng lặp.", SW - 2 * MX);
{
  const s = slide("Thực nghiệm · Dữ liệu", "UJIIndoorLoc: tập kiểm tra dùng điện thoại lạ",
    "Chỉ 2 trong 11 điện thoại của tập kiểm tra có trong tập huấn luyện; vân tay kiểm tra thấy ít AP hơn. Đây là lý do giữ lại fold theo điện thoại.");
  img(s, dg("b14_dien_thoai.png"), MX, 1.45, SW - 2 * MX, 3.6, "center", "Điện thoại");
  img(s, dg("b16_so_ap_moi_van_tay.png"), MX, 5.1, 5.6, 1.8, "left", "Số AP");
  text(s, "**9/11 điện thoại** của tập kiểm tra không có trong tập huấn luyện → fold dev **giữ lại theo điện thoại** (GroupKFold trên PHONEID) để mô phỏng đúng tình huống gặp thiết bị lạ.",
    MX + 6.0, 5.3, SW - 2 * MX - 6.0, 1.5, { fontSize: 16 });
}
{
  const s = slide("Thực nghiệm · Giao thức", "Chọn trên dev, chấm tập kiểm tra đúng một lần",
    "Mọi tham số chọn trên 6 fold dev. Sau khi chọn, EFIM chạy lại trên toàn bộ tập huấn luyện, bộ hồi quy học trên đặc trưng ngoài fold, mô hình cuối chấm tập kiểm tra một lần.");
  const r = img(s, dg("d10_giao_thuc.png"), MX, 1.45, 8.3, 4.4, "left", "Giao thức");
  img(s, fx("f_err"), MX + 0.2, r.y + r.h + 0.2, 7.5, 0.85, "left", "Sai số");
  bullets(s, ["6 fold dev, **GroupKFold theo PHONEID**", `${vn(SEL.n_configurations, 0)} cấu hình Bước 1–7 so trên dev`,
    "Bước 8: đặc trưng ngoài fold, chọn K, m, λ trên dev", "Tập kiểm tra không tham gia lựa chọn nào",
    `${D.verification.n_checks} phép kiểm chứng độc lập`], MX + 8.7, 1.6, SW - 2 * MX - 8.7, 5.2, 15.5);
}
figSlide("Thực nghiệm · Chọn tham số", "Lựa chọn tham số Bước 1–7 trên dev", "b11_luoi_tham_so_dev.png", [
  `UJIIndoorLoc: lợi ích **rank**, θ = ${vn(SEL.theta_pct, 0)}%`,
  `γ = ${PRM.gamma}, τ = ${PRM.tau}, β = ${PRM.beta}`, `σ = ${PRM.sigma} m, k_{f} = ${PRM.kf}, m = ${PRM.m}, p = ${PRM.p}`,
  "σ = 3 m có lợi; σ = 10 m làm mờ chữ ký ô", `Dev Bước 1–7: **${vn(SEL.dev_mean_m)} m**`],
  "Lưới tham số đánh giá trên 6 fold dev; mỗi điểm là cấu hình tốt nhất của các tham số còn lại.", 7.6);
{
  const s = slide("Thực nghiệm · Kết quả", `${nOk}/${allTests.length} tập kiểm tra đạt sai số trung bình dưới 7 m`,
    `Mọi tập kiểm tra đều dưới 7 m. UJIIndoorLoc ${vn(UT.sai_so_tb_m)} m sau Bước 8 (v4: ${vn(U4.mean_err_m)} m). Các bộ khác chỉ dùng Bước 1-7.`);
  const short = { uji: "UJIIndoorLoc", uji_lib3: "UJI_LIB", dlulib: "DLULIB", hcxy: "HCXY", hus: "HUS", hus_dedup: "HUS khử trùng" };
  const labels = allTests.map(({ k, t }) => `${short[k]} · ${t.replace("validationData", "validation").replace("testcase", "case ").replace("test_HCXY", "test")}`);
  s.addChart(pres.charts.BAR, [{ name: "Sai số trung bình (m)", labels, values: allTests.map(({ v }) => Math.round(v.sai_so_tb_m * 100) / 100) }], {
    x: MX, y: 1.45, w: 8.4, h: 5.4, barDir: "bar", catAxisOrientation: "maxMin",
    chartColors: allTests.map(({ k }) => (k === "uji" ? NAVY : TEAL)),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 13, dataLabelColor: INK, dataLabelFontFace: F,
    catAxisLabelFontSize: 13, catAxisLabelColor: INK, catAxisLabelFontFace: F,
    valAxisLabelFontSize: 12, valAxisLabelColor: GREY, valAxisLabelFontFace: F, valAxisMinVal: 0, valAxisMaxVal: 8, valAxisMajorUnit: 1,
    valGridLine: { color: "E3E0D8", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: false, showTitle: true, title: "Sai số trung bình trên tập kiểm tra (m) — mục tiêu < 7 m", titleFontSize: 14, titleColor: NAVY, titleFontFace: F, barGapWidthPct: 45,
  });
  const x = MX + 8.8, w = SW - MX - x;
  stat(s, x, 1.6, w, `${nOk}/${allTests.length}`, "tập kiểm tra dưới 7 m", TEAL, 44);
  stat(s, x, 3.15, w, `${vn(UT.sai_so_tb_m)} m`, `UJIIndoorLoc, trung vị ${vn(UT.trung_vi_m)} m`, NAVY, 44);
  stat(s, x, 4.7, w, `${vn(Math.min(...others.map((a) => a.v.sai_so_tb_m)))}–${vn(Math.max(...others.map((a) => a.v.sai_so_tb_m)))} m`, "năm bộ dữ liệu còn lại (Bước 1–7)", NAVY, 34);
}
{
  const s = slide("Thực nghiệm · Kết quả", "Phân bố sai số trên tập kiểm tra",
    "Đường CDF của mô hình cuối nằm trên đường v4 ở mọi mức sai số; k-NN tối ưu chỉ để tham chiếu.");
  img(s, dg("b02_cdf_uji.png"), MX, 1.45, 6.2, 5.4, "left", "CDF UJIIndoorLoc");
  img(s, dg("b03_cdf_cac_bo_khac.png"), MX + 6.35, 1.45, SW - 2 * MX - 6.35, 5.4, "right", "CDF các bộ khác");
}
figSlide("Thực nghiệm · Kết quả", "Sai số trung bình và trung vị của mọi tập kiểm tra", "b01_ket_qua_tap_test.png", null,
  "Cột là sai số trung bình, phần gạch chéo là trung vị; đường đứt là mức 7 m.", SW - 2 * MX);
{
  const s = slide("Thực nghiệm · Phân tích UJIIndoorLoc", "Sai số còn lại nằm chủ yếu trong tầng",
    `${pct(split[0].phan_tong_sai_so)} tổng sai số thuộc các mẫu đã đoán đúng tầng; Bước 8 giảm sai số các mẫu này từ 7,78 m xuống ${vn(split[0].sai_so_tb_m)} m.`);
  const cw = 2.95;
  [[`${vn(UT.sai_so_tb_m)} m`, "sai số trung bình", NAVY], [`${vn(UT.trung_vi_m)} m`, "trung vị", TEAL],
   [pct(UT.dung_toa), "đúng tòa nhà", NAVY], [pct(UT.dung_toa_tang), "đúng tòa và tầng", TEAL]]
    .forEach(([v, l, c], i) => stat(s, MX + i * (cw + 0.1), 1.5, cw, v, l, c, 38));
  img(s, dg("b04_sai_so_theo_toa_tang.png"), MX, 3.05, 7.6, 3.85, "left", "Theo tòa tầng");
  table(s, ["Nhóm mẫu", "Số mẫu", "TB (m)", "Phần sai số"], split.map((x) => [x.nhom, vn(x.so_mau, 0), vn(x.sai_so_tb_m), pct(x.phan_tong_sai_so)]),
    MX + 7.9, 3.15, SW - 2 * MX - 7.9, [1.9, 0.85, 0.85, 1.1], { align: ["left", "right", "right", "right"], size: 13, rowH: 0.48 });
  text(s, "Lỗi tầng hầu như chỉ giữa hai **tầng liền kề**; nhầm toà nhà gần như không có.", MX + 7.9, 4.85, SW - 2 * MX - 7.9, 1.6, { fontSize: 15.5 });
}
{
  const s = slide("Thực nghiệm · Phân tích UJIIndoorLoc", "Nhầm lẫn tầng và phân bố không gian của sai số",
    "Ma trận nhầm lẫn: lỗi gần đường chéo, giữa các tầng liền kề. Bản đồ: sai số lớn ở đầu hành lang và vùng thưa điểm tham chiếu.");
  img(s, dg("b05_ma_tran_nham_lan_tang.png"), MX, 1.45, 5.3, 5.4, "left", "Ma trận nhầm lẫn");
  img(s, dg("b06_ban_do_sai_so.png"), MX + 5.45, 1.45, SW - 2 * MX - 5.45, 5.4, "right", "Bản đồ sai số");
}
figSlide("Thực nghiệm · Phân tích Bước 8", "Tác động của Bước 8 trên từng vân tay", "b07_cai_thien_tung_van_tay.png", [
  `Sai số trung bình: **${vn(U4.mean_err_m)} → ${vn(UT.sai_so_tb_m)} m**`, `Trung vị: ${vn(U4.median_err_m)} → ${vn(UT.trung_vi_m)} m`,
  "Phần lớn vân tay được cải thiện (dưới đường chéo)", "Vân tay sai số rất lớn ở v4 được kéo về gần hơn"],
  "Mỗi điểm là một vân tay kiểm tra; dưới đường chéo là được cải thiện.", 8.6);
{
  const s = slide("Thực nghiệm · Phân tích Bước 8", "Những gì đã thử trên dev cho Bước 8",
    "Mọi biến thể so bằng sai số dev ngoài fold; tập kiểm tra không được đọc. IDF và mô hình mức cường độ dùng riêng không cải thiện.");
  img(s, dg("b09_bien_the_buoc8.png"), MX, 1.45, 7.6, 5.4, "left", "Biến thể");
  const x = MX + 7.9, w = SW - MX - x;
  stat(s, x, 1.6, w, `${vn(RSH["v4 (baseline)"])} m`, "dev, Bước 1–7 (v4)", GREY, 38);
  stat(s, x, 3.05, w, `${vn(V6.dev_mean_m)} m`, "dev, mô hình cuối (v6)", TEAL, 38);
  stat(s, x, 4.5, w, `${vn(UT.sai_so_tb_m)} m`, "tập kiểm tra, chấm một lần", NAVY, 38);
}
{
  const s = slide("Thực nghiệm · Phiên bản", "Lịch sử phiên bản và nguyên tắc chọn mô hình",
    "v1 có kiểm tra thấp nhất trong Bước 1-7 nhưng dev kém nhất nên không được chọn. v6 có dev thấp nhất nên là mô hình cuối.");
  img(s, dg("b08_lich_su_phien_ban.png"), MX, 1.45, 7.2, 4.2, "left", "Phiên bản");
  const V = D.versions;
  table(s, ["Bản", "Dev", "Test"], V.map((v) => [v.version.replace(" (final)", " (cuối)"), vn(v.dev_mean_m), vn(v.test_mean_m)]),
    MX + 7.5, 1.55, SW - 2 * MX - 7.5, [1.7, 1.2, 1.25], { align: ["left", "right", "right"], size: 14, rowH: 0.48, hl: (i) => i === V.length - 1 });
  card(s, MX, 5.85, SW - 2 * MX, 0.95, SOFT, null, NAVY, TEAL);
  text(s, `**Nguyên tắc:** mọi lựa chọn dựa trên dev; mỗi phiên bản chấm tập kiểm tra đúng một lần. Mô hình cuối **v6**: dev ${vn(V6.dev_mean_m)} m, kiểm tra **${vn(UT.sai_so_tb_m)} m**.`,
    MX + 0.35, 5.95, SW - 2 * MX - 0.7, 0.75, { fontSize: 16, valign: "middle" });
}
{
  const s = slide("Thực nghiệm · Chi phí", "Thống kê khai thác HUI và chi phí tính toán",
    "Số HUI mỗi ô biến thiên nhiều bậc; ô nhiều AP mạnh phải nâng ngưỡng. Thời gian định vị UJIIndoorLoc lớn nhất do ba mô hình HUI.");
  img(s, dg("b12_thong_ke_khai_thac.png"), MX, 1.45, 8.4, 3.6, "left", "Thống kê khai thác");
  table(s, ["Bộ dữ liệu", "ms / vân tay"], allTests.filter((x, i, a) => a.findIndex((y) => y.k === x.k) === i).map(({ k, v }) => [D.title[k], vn(v.ms_moi_fp, 2)]),
    MX + 8.7, 1.55, SW - 2 * MX - 8.7, [2.6, 1.3], { align: ["left", "right"], size: 13, rowH: 0.42 });
  bullets(s, [`Mô hình chính UJIIndoorLoc: **${vn(U.model.n_huis, 0)} HUI**, ${U.mining.o_phai_nang_theta}/${U.model.n_cells} ô nâng θ`,
    `Ba mô hình của Bước 8: **${vn(nHUI3, 0)} HUI**`, "Chi phí định vị không phụ thuộc số vân tay huấn luyện"], MX, 5.25, 8.4, 1.6, 15);
}
figSlide("Thực nghiệm · So sánh", "Đặt cạnh các hệ thống dùng k-NN (chỉ để tham chiếu)", "b15_so_sanh_tham_chieu.png", [
  `UJIIndoorLoc: đề xuất **${vn(refU.chi_huim_m)} m**, k-NN gốc ${vn(refU.knn_goc_m)} m, k-NN tối ưu ${vn(refU.knn_toi_uu_m)} m`,
  "Bộ một tầng: vị trí kiểm tra trùng điểm tham chiếu, lợi thế cho k-NN",
  "Ưu điểm của đề xuất: mọi quyết định đến từ HUI, mô hình không chứa vân tay"],
  "Hệ thống đề xuất tốt hơn k-NN gốc nhưng kém k-NN tối ưu trên UJIIndoorLoc.", 8.6);
{
  const s = slide("Thực nghiệm · Kiểm chứng", "Mọi con số đều tính lại được độc lập",
    "Ba cách kiểm tra: chương trình kiểm chứng không gọi EFIM hay bộ định vị; sổ Excel bằng công thức; script thư viện chuẩn.");
  const w = (SW - 2 * MX - 0.6) / 3;
  [[`${D.verification.n_checks} phép kiểm`, `${D.verification.n_failed} thất bại`, "Tính lại ngưỡng, lợi ích, HUI vượt ngưỡng, điểm khớp, tầng, toạ độ; với mô hình cuối: toạ độ = tổng có trọng số các ô, ô nằm đúng tầng, v4 tái lập khít."],
   ["Sổ Excel", "so_lieu/kiem_chung_mean.xlsx", "Mỗi tập kiểm tra một sheet: sai số từng mẫu bằng SQRT, trung bình bằng AVERAGE, so với số báo cáo; ví dụ dựng lại toạ độ bằng SUMPRODUCT."],
   ["Script Python", "so_lieu/kiem_tra_mean.py", "Chỉ dùng thư viện chuẩn: tính lại sai số trung bình, trung vị, đúng tòa–tầng; in KHỚP hoặc LỆCH cho từng tập."]]
    .forEach(([a, b, c], i) => {
      const x = MX + i * (w + 0.3);
      card(s, x, 1.6, w, 3.95, i === 0 ? SOFT : CARD, null, NAVY, i === 0 ? TEAL : NAVY);
      s.addText(a, { x: x + 0.3, y: 1.8, w: w - 0.6, h: 0.65, fontFace: F, fontSize: 26, bold: true, color: i === 0 ? TEAL : NAVY, margin: 0, isTextBox: true });
      s.addText(b, { x: x + 0.3, y: 2.45, w: w - 0.6, h: 0.45, fontFace: F, fontSize: 14, bold: true, color: GREY, margin: 0, isTextBox: true });
      text(s, c, x + 0.3, 3.0, w - 0.6, 2.4, { fontSize: 15 });
    });
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 5.8, w: SW - 2 * MX, h: 0.95, fill: { color: NAVY }, line: { color: NAVY } });
  text(s, `**Kết quả:** cả ${allTests.length}/${allTests.length} tập kiểm tra KHỚP; chênh lệch giữa sai số tính lại và sai số báo cáo dưới 0,00005 m.`,
    MX + 0.35, 5.95, SW - 2 * MX - 0.7, 0.65, { fontSize: 17, color: "FFFFFF", valign: "middle" });
}

// ================================================================== CHƯƠNG 5
divider(4, "Kết luận", ["Kết quả đạt được", "Hạn chế cần nói rõ", "Hướng phát triển"]);
{
  const s = slide("Kết luận", "Kết luận và hướng phát triển",
    "HUIM đã chuyển từ vai trò tiền xử lý sang vai trò thuật toán định vị. Kết quả dưới 7 m trên cả sáu bộ dữ liệu; trên UJIIndoorLoc nhờ Bước 8, với biên nhỏ cần nói rõ.");
  const w = (SW - 2 * MX - 0.5) / 3;
  const cols = [
    ["Kết quả đạt được", TEAL, ["HUIM là thuật toán định vị chính; **không k-NN**, không lưu vân tay",
      `**${nOk}/${allTests.length}** tập kiểm tra dưới 7 m`, `UJIIndoorLoc **${vn(UT.sai_so_tb_m)} m** (v4: ${vn(U4.mean_err_m)} m)`,
      `${D.verification.n_checks} phép kiểm chứng, 0 thất bại`]],
    ["Hạn chế", RUST, [`Biên dưới 7 m nhỏ: sai số chuẩn **${vn(UT.sai_so_chuan_tb_m)} m**`,
      "Bước 8 dùng bộ hồi quy để cân bằng chứng HUI", "Chi phí khai thác và định vị lớn khi θ thấp"]],
    ["Hướng phát triển", NAVY, ["Lợi ích nội bất biến hơn với thiết bị", "HUI nhiều mức không gian; quy tắc kết hợp tường minh",
      "HUI đóng, HUI cực đại; EFIM biên dịch"]]];
  cols.forEach(([t, c, items], i) => {
    const x = MX + i * (w + 0.25);
    card(s, x, 1.55, w, 5.2, CARD, t, c, c);
    bullets(s, items, x + 0.3, 2.3, w - 0.5, 4.3, 20);
  });
}
{
  const s = pres.addSlide({ masterName: "TOI", sectionTitle: "Kết luận" });
  s.background = { path: path.join(TMP, "art_title.png") };
  s.addText("Xin trân trọng cảm ơn hội đồng và quý thầy cô", { x: MX, y: 2.2, w: 7.6, h: 1.8, fontFace: F, fontSize: 38, bold: true, color: "FFFFFF", valign: "top", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.2, w: 2.6, h: 0, line: { color: GOLD, width: 2.5 } });
  s.addText("Rất mong nhận được ý kiến đóng góp", { x: MX, y: 4.4, w: 7.6, h: 0.6, fontFace: F, fontSize: 21, italic: true, color: "DCE6EE", margin: 0, isTextBox: true });
  s.addText("Mã nguồn, số liệu, sơ đồ và sổ kiểm chứng: thư mục BAOCAO", { x: MX, y: 5.3, w: 7.6, h: 0.4, fontFace: F, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true });
}

// ------------------------------------------------------------------ ghi file
const out = path.join(B, "Slide_HUIM_IPS_UJIIndoorLoc.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  const apply = process.env.PPTX_APPLY_THEME;           // scripts/apply_theme.js của skill pptx, nếu có
  if (apply && fs.existsSync(apply)) await require(apply).applyTheme(out, THEME);
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log("written", out, fs.statSync(out).size, "slides:", pres.slides.length);
});
