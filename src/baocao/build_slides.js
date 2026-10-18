// BAOCAO/Slide_HUIM_IPS_UJIIndoorLoc.pptx — bài thuyết trình bảo vệ chuyên đề.
// Mọi con số đọc từ BAOCAO/so_lieu/du_lieu_bao_cao.json; công thức là ảnh mathtext
// (make_slide_formulas.py) để hiển thị giống nhau trên mọi máy.
// Chạy: node src/baocao/build_slides.js   (cần gói npm "pptxgenjs", Python có matplotlib)
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const B = path.join(ROOT, "BAOCAO");
const D = JSON.parse(fs.readFileSync(path.join(B, "so_lieu", "du_lieu_bao_cao.json"), "utf8"));
const FX = fs.mkdtempSync(path.join(os.tmpdir(), "cong_thuc_"));
execFileSync("python3", [path.join(__dirname, "make_slide_formulas.py"), FX]);

// ------------------------------------------------------------------ theme
const THEME = {
  name: "HUIM IPS", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B2A3D", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F4F1EA", accent1: "2E7D8C", accent2: "B5532A",
            accent3: "7A8C99", accent4: "D9A441", accent5: "4C6A88", accent6: "9BB7C4",
            hlink: "2E7D8C", folHlink: "4C6A88" },
};
const K = THEME.colors;
const INK = K.dk1, NAVY = K.dk2, PAPER = K.lt2, TEAL = K.accent1, RUST = K.accent2, GREY = K.accent3;
const LINE = "D5D0C4", SOFT = "E8F1F2", SOFT2 = "F6E9E2";
const HF = THEME.headFontFace, BF = THEME.bodyFontFace;

const vn = (x, k = 2) => Number(x).toFixed(k).replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
const pct = (x, k = 1) => vn(100 * x, k) + "%";
const U = D.datasets.uji, UT = U.tests.validationData, SEL = U.selection, PRM = SEL.params;
const V6 = U.v6, U4 = U.v4_tests.validationData, RSH = V6.research.dev_mean_m;
const allTests = [];
D.order.forEach((k) => Object.entries(D.datasets[k].tests).forEach(([t, v]) => allTests.push({ k, t, v })));
const nOk = allTests.filter((x) => x.v.duoi_7m).length;
const split = D.uji_floor_split;
const refU = D.references.find((x) => x.dataset === "uji");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13,33 × 7,5 in
pres.theme = { headFontFace: HF, bodyFontFace: BF };
pres.title = "Ứng dụng HUIM trong hệ thống định vị trong nhà";
pres.subject = "Định vị bằng so khớp High Utility Itemset trên UJIIndoorLoc";

const SW = 13.333, SH = 7.5, MX = 0.6;
const FOOT = "Ứng dụng HUIM trong định vị trong nhà";

pres.defineSlideMaster({
  title: "TIEU_DE", background: { color: NAVY },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: MX, y: 2.0, w: 11.6, h: 1.9,
    fontFace: HF, fontSize: 36, bold: true, color: "FFFFFF", valign: "top", align: "left", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "NOI_DUNG", background: { color: "FFFFFF" },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { line: { x: MX, y: 7.0, w: SW - 2 * MX, h: 0, line: { color: LINE, width: 0.75 } } },
    { text: { text: FOOT, options: { x: MX, y: 7.05, w: 7, h: 0.3, fontFace: BF, fontSize: 10, color: GREY, margin: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.62, w: SW - 2 * MX, h: 0.75,
      fontFace: HF, fontSize: 26, bold: true, color: NAVY, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: SW - MX - 1.0, y: 7.05, w: 1.0, h: 0.3, fontFace: BF, fontSize: 10, color: GREY, align: "right" },
});

// ------------------------------------------------------------------ helpers
const sections = [];
function section(title) { pres.addSection({ title }); sections.push(title); }
function slide(kicker, title, notes) {
  const s = pres.addSlide({ masterName: "NOI_DUNG", sectionTitle: sections[sections.length - 1] });
  s.addText(kicker.toUpperCase(), { x: MX, y: 0.3, w: 9, h: 0.3, fontFace: BF, fontSize: 11, bold: true,
    color: TEAL, charSpacing: 1.5, margin: 0, isTextBox: true });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
// ảnh vừa khung (x, y, w, h), giữ tỉ lệ, canh theo `align`
function img(s, file, x, y, w, h, align = "center", name) {
  const [pw, ph] = pngSize(file);
  let W = w, H = w * ph / pw;
  if (H > h) { H = h; W = h * pw / ph; }
  const X = align === "left" ? x : align === "right" ? x + w - W : x + (w - W) / 2;
  s.addImage({ path: file, x: X, y, w: W, h: H, altText: name || path.basename(file) });
  return { x: X, y, w: W, h: H };
}
const diag = (f) => path.join(B, "diagram", f);
const fx = (f) => path.join(FX, f + ".png");
// đoạn văn có gạch đầu dòng; phần **đậm** in đậm
function para(text) {           // **đậm**, _{dưới}, ^{trên}
  return text.split(/(\*\*[^*]+\*\*|_\{[^}]*\}|\^\{[^}]*\})/).filter(Boolean).map((p) =>
    p.startsWith("**") ? { text: p.slice(2, -2), options: { bold: true } }
      : p.startsWith("_{") ? { text: p.slice(2, -1), options: { subscript: true } }
      : p.startsWith("^{") ? { text: p.slice(2, -1), options: { superscript: true } }
      : { text: p, options: {} });
}
function bullets(s, items, x, y, w, h, size = 16, color = INK) {
  // pptxgenjs ghi pPr cho từng run; đặt bullet + align cho mọi run để đoạn nhiều run vẫn
  // một dòng đầu dòng (align giống nhau thì chỉ breakLine mới tách đoạn)
  const runs = [];
  items.forEach((t, i) => {
    const r = para(t).map((x) => ({ text: x.text,
      options: { ...x.options, bullet: { indent: 18 }, align: "left", paraSpaceAfter: 8 } }));
    if (i < items.length - 1) r[r.length - 1].options.breakLine = true;
    runs.push(...r);
  });
  s.addText(runs, { x, y, w, h, fontFace: BF, fontSize: size, color, valign: "top", margin: 2, isTextBox: true });
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(para(t), { x, y, w, h, fontFace: BF, fontSize: 16, color: INK, valign: "top", margin: 0, isTextBox: true, ...o });
}
// khối số liệu: số lớn + nhãn nhỏ
function stat(s, x, y, w, value, label, color = NAVY) {
  s.addText(value, { x, y, w, h: 0.8, fontFace: HF, fontSize: 40, bold: true, color, margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.82, w, h: 0.6, fontFace: BF, fontSize: 13, color: GREY, margin: 0, valign: "top", isTextBox: true });
}
function panel(s, x, y, w, h, fill, title, titleColor) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill } });
  if (title) s.addText(title, { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: 0.4, fontFace: HF, fontSize: 17, bold: true,
    color: titleColor || NAVY, margin: 0, isTextBox: true });
}
function table(s, header, rows, x, y, w, colW, o = {}) {
  const hd = header.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center", valign: "middle" } }));
  const body = rows.map((r, i) => r.map((c, j) => ({ text: String(c), options: {
    fill: { color: (o.hl && o.hl(i)) ? SOFT2 : (i % 2 ? "F7F6F2" : "FFFFFF") },
    align: (o.align && o.align[j]) || "left", valign: "middle", bold: !!(o.hl && o.hl(i)) } })));
  s.addTable([hd, ...body], { x, y, w, colW, fontFace: BF, fontSize: o.size || 13, color: INK,
    border: { type: "solid", pt: 0.5, color: LINE }, rowH: o.rowH || 0.36, margin: [2, 6, 2, 6] });
}

// ------------------------------------------------------------------ 1. tiêu đề
section("Mở đầu");
{
  const s = pres.addSlide({ masterName: "TIEU_DE", sectionTitle: "Mở đầu" });
  s.addText("BÁO CÁO CHUYÊN ĐỀ CAO HỌC  ·  NGÀNH KHOA HỌC MÁY TÍNH", { x: MX, y: 1.2, w: 11, h: 0.4,
    fontFace: BF, fontSize: 13, bold: true, color: "9BB7C4", charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Ứng dụng khai thác tập mục lợi ích cao (HUIM) trong hệ thống định vị trong nhà", { placeholder: "title" });
  s.addText("Định vị bằng so khớp High Utility Itemset trên vân tay Wi-Fi UJIIndoorLoc và năm bộ dữ liệu bổ sung",
    { x: MX, y: 3.95, w: 11, h: 0.5, fontFace: BF, fontSize: 18, italic: true, color: "DCE6EE", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.85, w: 3.0, h: 0, line: { color: "9BB7C4", width: 1 } });
  s.addText([
    { text: "Học viên thực hiện: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Giảng viên hướng dẫn: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
    { text: "Năm 2026", options: {} },
  ], { x: MX, y: 5.05, w: 8, h: 1.4, fontFace: BF, fontSize: 16, color: "FFFFFF", paraSpaceAfter: 6, margin: 0, isTextBox: true });
  s.addNotes("Kính thưa thầy cô. Đề tài trình bày cách dùng thuật toán khai thác tập mục lợi ích cao làm thuật toán định vị chính của một hệ thống định vị trong nhà dựa trên vân tay Wi-Fi, không dùng k-NN.");
}

// ------------------------------------------------------------------ 2. nội dung
{
  const s = slide("Mở đầu", "Nội dung trình bày");
  const items = [["01", "Đặt vấn đề", "Vai trò của HUIM trong các phiên bản trước và câu hỏi nghiên cứu"],
    ["02", "Cơ sở lý thuyết", "Bài toán khai thác tập mục lợi ích cao và thuật toán EFIM"],
    ["03", "Phương pháp đề xuất", "Bảy bước từ vân tay Wi-Fi tới toạ độ, chỉ dùng HUI"],
    ["04", "Thực nghiệm và đánh giá", "Giao thức, kết quả trên 9 tập kiểm tra, phân tích và kiểm chứng"],
    ["05", "Kết luận", "Đóng góp, hạn chế và hướng phát triển"]];
  items.forEach(([n, t, d], i) => {
    const y = 1.75 + i * 1.0;
    s.addText(n, { x: MX, y, w: 1.0, h: 0.8, fontFace: HF, fontSize: 34, bold: true, color: TEAL, margin: 0, valign: "top", isTextBox: true });
    s.addText(t, { x: MX + 1.15, y: y + 0.02, w: 6, h: 0.42, fontFace: HF, fontSize: 20, bold: true, color: NAVY, margin: 0, isTextBox: true });
    s.addText(d, { x: MX + 1.15, y: y + 0.44, w: 10, h: 0.35, fontFace: BF, fontSize: 14, color: GREY, margin: 0, isTextBox: true });
  });
  s.addNotes("Bài trình bày gồm năm phần, theo đúng bố cục của báo cáo.");
}

// ------------------------------------------------------------------ 3. đặt vấn đề
section("Đặt vấn đề");
{
  const s = slide("01 · Đặt vấn đề", "HUIM phải là thuật toán định vị, không chỉ là bước lọc AP",
    `Ở các phiên bản trước, HUIM chỉ chọn tập AP rồi k-NN định vị. Khai thác HUI toàn cục chỉ giữ ${refU.huim_toan_cuc_so_ap} AP và cho ${vn(refU.huim_toan_cuc_knn_m)} m; khai thác theo tòa-tầng giữ ${refU.huim_chon_ap_so_ap} trên ${refU.tong_ap} AP và cho ${vn(refU.huim_chon_ap_knn_m)} m, nhưng HUIM chỉ đóng góp khoảng 6% mức giảm sai số. Bỏ HUIM đi, k-NN vẫn định vị được, nên đề tài cần một thiết kế mà HUIM quyết định vị trí.`);
  const y = 1.7, h = 3.9, w = 5.85;
  panel(s, MX, y, w, h, SOFT2, "Trước: HUIM là nhánh tiền xử lý", RUST);
  bullets(s, [
    "HUIM chọn tập AP; **k-NN** so khoảng cách vân tay và quyết định vị trí",
    `HUI toàn cục: còn ${refU.huim_toan_cuc_so_ap}/${refU.tong_ap} AP, sai số ${vn(refU.huim_toan_cuc_knn_m)} m`,
    `HUI theo tòa–tầng: ${refU.huim_chon_ap_so_ap}/${refU.tong_ap} AP, sai số ${vn(refU.huim_chon_ap_knn_m)} m`,
    "Phân tích Shapley: HUIM đóng góp khoảng **6%** mức giảm sai số",
  ], MX + 0.25, y + 0.75, w - 0.5, h - 0.9, 17);
  const x2 = MX + w + 0.43;
  panel(s, x2, y, w, h, SOFT, "Đề xuất: HUIM là mô hình định vị", TEAL);
  bullets(s, [
    "Mỗi điểm tham chiếu là một **ô**; vân tay của ô là một cơ sở dữ liệu giao dịch",
    "EFIM khai thác tập HUI của từng ô; **tập HUI chính là mô hình**",
    "Tầng và toạ độ suy ra từ **điểm khớp HUI**; không có k-NN, không lưu vân tay",
    "Bỏ HUIM thì hệ thống không còn mô hình để định vị",
  ], x2 + 0.25, y + 0.75, w - 0.5, h - 0.9, 17);
  text(s, "**Câu hỏi nghiên cứu:** có thể xây dựng hệ thống định vị trong đó HUIM là thuật toán định vị chính, không dùng k-NN, mà vẫn đạt sai số trung bình dưới 7 m hay không?",
    MX, 5.85, SW - 2 * MX, 0.9, { fontSize: 16, color: NAVY });
}

// ------------------------------------------------------------------ 4. HUIM
section("Cơ sở lý thuyết");
{
  const s = slide("02 · Cơ sở lý thuyết", "Bài toán khai thác tập mục lợi ích cao",
    "Mỗi mục có lợi ích nội trong từng giao dịch và lợi ích ngoài. Lợi ích của tập mục là tổng lợi ích các mục trên mọi giao dịch chứa nó. Khác với tập phổ biến, lợi ích không đơn điệu giảm nên không cắt tỉa trực tiếp bằng u(X) được.");
  panel(s, MX, 1.7, 6.2, 4.9, "FBFAF7");
  img(s, fx("f_util"), MX + 0.4, 2.0, 5.4, 4.3, "left", "Định nghĩa lợi ích");
  const x = MX + 6.7;
  text(s, "**Ánh xạ sang định vị Wi-Fi**", x, 1.75, 5.4, 0.4, { fontSize: 18, color: NAVY });
  table(s, ["HUIM", "Định vị vân tay"], [["mục i", "một AP"], ["giao dịch T", "một vân tay (một lần quét)"],
    ["lợi ích nội q(i,T)", "cường độ RSSI đã chuẩn hoá"], ["lợi ích ngoài p(i)", "đặt bằng 1"],
    ["cơ sở dữ liệu D", "các vân tay của một ô"]], x, 2.25, 5.4, [2.2, 3.2], { size: 14, rowH: 0.42 });
  text(s, "Lợi ích **không đơn điệu**: thêm một mục có thể làm u(X) tăng hoặc giảm, nên cần các chặn trên để cắt tỉa không gian tìm kiếm.",
    x, 5.0, 5.4, 1.4, { fontSize: 15, color: INK });
}

// ------------------------------------------------------------------ 5. EFIM
{
  const s = slide("02 · Cơ sở lý thuyết", "Thuật toán EFIM (Zida và cộng sự, 2017)",
    "EFIM duyệt cây liệt kê tập theo chiều sâu, mục sắp theo TWU tăng dần. Tại mỗi nút, hai chặn trên lu và su được tính trong một lần quét cơ sở dữ liệu đã chiếu: lu dùng để loại mục khỏi cây con, su dùng để không duyệt nhánh. Bản cài đặt được kiểm thử với thuật toán vét cạn.");
  panel(s, MX, 1.7, 7.4, 3.3, "FBFAF7");
  img(s, fx("f_efim"), MX + 0.35, 1.95, 6.7, 2.8, "left", "Chặn trên của EFIM");
  const x = MX + 7.9;
  bullets(s, [
    "Duyệt cây liệt kê tập theo chiều sâu, mục sắp theo **TWU** tăng dần",
    "**lu** < minUtil: loại z khỏi toàn bộ cây con của α",
    "**su** < minUtil: không duyệt nhánh α ∪ {z}",
    "Chiếu cơ sở dữ liệu và gộp giao dịch trùng để tiết kiệm bộ nhớ",
  ], x, 1.75, SW - MX - x, 3.4, 15);
  panel(s, MX, 5.3, SW - 2 * MX, 1.35, SOFT);
  text(s, "**Kiểm chứng cài đặt:** EFIM trong mã nguồn được so với một thuật toán vét cạn trên dữ liệu ngẫu nhiên (thư mục ma_nguon/tests); tập HUI và lợi ích trùng khớp hoàn toàn.",
    MX + 0.3, 5.5, SW - 2 * MX - 0.6, 1.0, { fontSize: 15 });
}

// ------------------------------------------------------------------ 6. tổng quan
section("Phương pháp đề xuất");
{
  const s = slide("03 · Phương pháp đề xuất", "Tổng quan: hệ thống định vị chỉ dùng HUIM",
    "Hai pha. Huấn luyện chạy một lần: chuyển RSSI thành lợi ích nội, nhóm vân tay theo điểm tham chiếu, khai thác HUI bằng EFIM và lưu mô hình. Định vị cho từng vân tay: chấm điểm khớp với HUI của mọi ô, làm mượt, chọn tầng, rồi ước lượng toạ độ.");
  img(s, diag("d01_tong_quan.png"), MX, 1.55, SW - 2 * MX, 5.3, "center", "Sơ đồ tổng quát");
}

// ------------------------------------------------------------------ 7. bước 1
{
  const s = slide("03 · Bước 1", "Từ cường độ tín hiệu tới lợi ích nội",
    "Ba dạng lợi ích nội được thử: abs, rel và rank. Dạng rank không đổi khi một điện thoại đọc lệch mọi AP cùng một lượng dB, và bất biến với mọi biến đổi đơn điệu của thang RSSI. Rank được chọn trên dev.");
  const r = img(s, diag("d02_buoc1_utility.png"), MX, 1.55, 7.6, 5.2, "left", "Bước 1 trên một vân tay thật");
  const x = r.x + r.w + 0.35, w = SW - MX - x;
  img(s, fx("f_rank"), x, 1.75, w, 1.1, "left", "Lợi ích nội dạng rank");
  bullets(s, [
    "n_{T}: số AP thấy được trong T; r_{T}(i): thứ hạng cường độ của AP i",
    "AP không thấy không có trong giao dịch",
    `Dạng **rank** được chọn trên dev: ${vn(D.pilots["theta_pilot.json"].phone_folds_theta20_all6_dev_mean_m.rank)} m, so với ${vn(D.pilots["theta_pilot.json"].phone_folds_theta20_all6_dev_mean_m.abs)} m (abs) và ${vn(D.pilots["theta_pilot.json"].phone_folds_theta20_all6_dev_mean_m.rel)} m (rel)`,
    "Bền với khác biệt giữa các điện thoại",
  ], x, 3.1, w, 3.6, 14);
}

// ------------------------------------------------------------------ 8. bước 2–3
{
  const s = slide("03 · Bước 2 và 3", "Cơ sở dữ liệu giao dịch theo ô và khai thác EFIM",
    `Mỗi điểm tham chiếu là một ô, tập vân tay đo tại ô là một cơ sở dữ liệu giao dịch. Ngưỡng minUtil đặt tương đối theo lợi ích của chính ô. EFIM có ngân sách 10 giây hoặc 10 000 HUI; vượt ngân sách thì θ nhân 1,25 và khai thác lại cho tới khi hoàn tất, nên tập HUI luôn đầy đủ. Trên UJIIndoorLoc ${U.mining.o_phai_nang_theta} trên ${U.model.n_cells} ô phải nâng θ.`);
  img(s, fx("f_cell"), MX, 1.6, 8.5, 0.5, "left", "Ngưỡng theo ô");
  const w = (SW - 2 * MX - 0.3) / 2;
  img(s, diag("d03_buoc2_o_giao_dich.png"), MX, 2.35, w, 3.6, "center", "Một ô là cơ sở dữ liệu giao dịch");
  img(s, diag("d04_buoc3_efim.png"), MX + w + 0.3, 2.35, w, 3.6, "center", "EFIM liệt kê HUI của ô");
  text(s, `UJIIndoorLoc: **${U.model.n_cells} ô**, trung bình ${vn(U.mining.giao_dich_tb_moi_o, 1)} giao dịch mỗi ô; θ = ${vn(SEL.theta_pct, 0)}%; vượt ngân sách thì θ ← 1,25·θ và khai thác lại tới khi hoàn tất, nên tập HUI luôn đầy đủ.`,
    MX, 6.2, SW - 2 * MX, 0.7, { fontSize: 14 });
}

// ------------------------------------------------------------------ 9. bước 4
{
  const s = slide("03 · Bước 4", "Mô hình định vị là tập HUI của mọi ô",
    "Mô hình chỉ gồm các HUI cùng toạ độ trọng tâm và nhãn tòa-tầng của từng ô. Không có vân tay huấn luyện nào được lưu, vì vậy không thể so khoảng cách vân tay như k-NN.");
  const r = img(s, diag("d05_buoc4_mo_hinh.png"), MX, 1.55, 8.0, 5.3, "left", "HUI của một ô");
  const x = r.x + r.w + 0.4, w = SW - MX - x;
  stat(s, x, 1.75, w, vn(U.model.n_huis, 0), "HUI trong mô hình UJIIndoorLoc");
  stat(s, x, 3.25, w, `${U.model.aps_in_some_hui}/${U.model.n_aps}`, "AP xuất hiện trong ít nhất một HUI", TEAL);
  stat(s, x, 4.75, w, "0", "vân tay huấn luyện được lưu", RUST);
}

// ------------------------------------------------------------------ 10. bước 5
{
  const s = slide("03 · Bước 5", "Chấm điểm khớp giữa vân tay và HUI của ô",
    "Với mỗi HUI X của ô c: ρ là tỷ lệ mục của X có trong vân tay (khớp mềm vì thiết bị khác có thể bỏ sót AP), agree đo mức phù hợp cường độ. P_c là khối lượng lợi ích HUI của ô mà vân tay chứa, V_c là phần lợi ích của vân tay được các HUI của ô giải thích.");
  panel(s, MX, 1.55, 6.3, 3.4, "FBFAF7");
  img(s, fx("f_score"), MX + 0.25, 1.75, 5.8, 3.0, "left", "Công thức điểm khớp");
  bullets(s, [
    "ρ: khớp mềm, chịu được AP bị bỏ sót",
    "agree: phạt chênh lệch cường độ, thang τ",
    "P_{c}: khối lượng HUI của ô có trong vân tay",
    "V_{c}: phần vân tay được HUI của ô giải thích",
  ], MX, 5.15, 6.3, 1.7, 14);
  img(s, diag("d06_buoc5_cham_diem.png"), MX + 6.6, 1.55, SW - 2 * MX - 6.6, 5.3, "right", "Chấm điểm một vân tay thật");
}

// ------------------------------------------------------------------ 11. bước 6
{
  const s = slide("03 · Bước 6", "Làm mượt không gian và chọn tầng",
    `Ô lân cận trên cùng tầng có chữ ký HUI gần nhau, nên điểm mỗi ô được cộng điểm các ô cùng tầng bằng nhân Gauss bán kính σ = ${PRM.sigma} m. Tầng được chọn là tầng có trung bình k_f = ${PRM.kf} điểm lớn nhất cao nhất.`);
  panel(s, MX, 1.55, SW - 2 * MX, 1.75, "FBFAF7");
  img(s, fx("f_smooth"), MX + 0.3, 1.7, 8.5, 1.45, "left", "Làm mượt và chọn tầng");
  text(s, `σ = ${PRM.sigma} m,  k_{f} = ${PRM.kf}\n(chọn trên dev)`, MX + 9.2, 1.95, 2.8, 1.0, { fontSize: 16, color: TEAL, bold: true });
  img(s, diag("d07_buoc6_lam_muot_tang.png"), MX, 3.5, SW - 2 * MX, 3.4, "center", "Điểm trước và sau làm mượt");
}

// ------------------------------------------------------------------ 12. bước 7
{
  const s = slide("03 · Bước 7", "Ô ứng viên và ước lượng ban đầu",
    `${V6.k_candidates} ô có điểm cao nhất trên tầng đã chọn là ô ứng viên. Ước lượng ban đầu là trọng tâm có trọng số của m = ${PRM.m} ô tốt nhất; đây là đầu ra của phiên bản v4. Trong 12 ô đó luôn có ô gần đúng vị trí (trung bình 2,4 m), nhưng ô điểm cao nhất cách tới 8,8 m: tập ứng viên đúng vùng, chỉ thứ tự là chưa đúng.`);
  const r = img(s, diag("d08_buoc7_toa_do.png"), MX, 1.55, 7.0, 5.3, "left", "Ô ứng viên của vân tay ví dụ");
  const x = r.x + r.w + 0.4, w = SW - MX - x;
  img(s, fx("f_coord"), x, 1.8, w, 1.2, "left", "Trọng tâm có trọng số");
  bullets(s, [
    `**${V6.k_candidates} ô ứng viên** của tầng đã chọn được chuyển sang Bước 8`,
    `Ước lượng ban đầu (v4): trọng tâm của m = ${PRM.m} ô, trọng số theo S_{c}^{p}, p = ${PRM.p}`,
    "Trên tập test v4: ô gần nhất trong 12 ô cách **2,4 m**, ô điểm cao nhất cách **8,8 m**",
  ], x, 3.25, w, 3.5, 14);
}

// ------------------------------------------------------------------ 12b. bước 8
{
  const s = slide("03 · Bước 8", "Xếp hạng lại ô ứng viên bằng bằng chứng HUI",
    `Mỗi ô ứng viên có ${V6.n_features} đặc trưng, đều tính từ HUI: điểm khớp của ba mô hình HUI (rank, mục theo mức cường độ, lợi ích abs), độ phủ, hồ sơ cường độ của ô suy ra từ HUI và độ đồng thuận không gian. Bộ hồi quy Gradient Boosting học trên 6 fold dev dự đoán khoảng cách từ ô tới vị trí thật; toạ độ là trọng tâm của ${V6.m} ô dự đoán gần nhất. Bộ hồi quy không thấy vân tay huấn luyện nào, và không có k-NN.`);
  const r = img(s, diag("d09_buoc8_xep_hang_lai.png"), MX, 1.45, 8.3, 3.25, "left", "Bước 8 trên vân tay ví dụ");
  panel(s, MX, r.y + r.h + 0.1, 8.3, 6.85 - (r.y + r.h + 0.1), "FBFAF7");
  img(s, fx("f_rerank"), MX + 0.2, r.y + r.h + 0.2, 7.9, 6.75 - (r.y + r.h + 0.25), "left", "Công thức Bước 8");
  const x = MX + 8.6, w = SW - MX - x;
  bullets(s, [
    `Ba mô hình HUI: rank (${vn(U.model.n_huis / 1e6, 2)} tr.), mức cường độ (${vn(V6.n_huis_L3 / 1e6, 2)} tr.), abs (${vn(V6.n_huis_abs / 1e6, 2)} tr. HUI)`,
    "Hồ sơ cường độ q̂_{c}(i) suy ra **từ HUI của ô**, không từ vân tay",
    "Bộ hồi quy học **chỉ trên fold dev**, nhãn = khoảng cách ô – vị trí thật",
    `Dev: **${vn(V6.dev_mean_v4_m)} → ${vn(V6.dev_mean_m)} m**`,
  ], x, 1.6, w, 5.2, 14);
}

// ------------------------------------------------------------------ 13. giao thức
section("Thực nghiệm");
{
  const s = slide("04 · Thực nghiệm", "Giao thức đánh giá: chọn trên dev, chấm tập kiểm tra một lần",
    "Mọi tham số được chọn trên 6 fold dev tách từ tập huấn luyện. Với UJIIndoorLoc, 9 trên 11 điện thoại của tập kiểm tra không có trong tập huấn luyện, nên fold được giữ lại theo điện thoại. Sau khi chọn, mô hình được huấn luyện lại trên toàn bộ tập huấn luyện và chấm tập kiểm tra đúng một lần.");
  const r = img(s, diag("d10_giao_thuc.png"), MX, 1.55, 8.1, 4.3, "left", "Giao thức đánh giá");
  img(s, fx("f_err"), MX + 0.2, r.y + r.h + 0.25, 7.0, 0.85, "left", "Sai số theo mét");
  const x = MX + 8.5, w = SW - MX - x;
  bullets(s, [
    "g = 0,766126 cho UJIIndoorLoc (Web Mercator), g = 1 cho bộ còn lại",
    "6 fold dev, **GroupKFold theo PHONEID**",
    `${vn(SEL.n_configurations, 0)} cấu hình được so trên dev`,
    "Tập kiểm tra không tham gia bất kỳ lựa chọn nào",
  ], x, 1.75, w, 5.0, 15);
}

// ------------------------------------------------------------------ 14. kết quả tổng hợp
{
  const s = slide("04 · Kết quả", `${nOk}/${allTests.length} tập kiểm tra đạt sai số trung bình dưới 7 m`,
    `Mọi tập kiểm tra đều dưới 7 m. UJIIndoorLoc đạt ${vn(UT.sai_so_tb_m)} m sau Bước 8 (v4: ${vn(U4.mean_err_m)} m); biên dưới 7 m nhỏ, sai số chuẩn của trung bình là ${vn(UT.sai_so_chuan_tb_m)} m. Các bộ khác dùng Bước 1–7.`);
  const short = { uji: "UJIIndoorLoc", uji_lib3: "UJI_LIB", dlulib: "DLULIB", hcxy: "HCXY", hus: "HUS", hus_dedup: "HUS khử trùng" };
  const labels = allTests.map(({ k, t }) => `${short[k]} · ${t.replace("validationData", "validation").replace("testcase", "case ").replace("test_HCXY", "test")}`);
  const vals = allTests.map(({ v }) => Math.round(v.sai_so_tb_m * 100) / 100);
  s.addChart(pres.charts.BAR, [{ name: "Sai số trung bình (m)", labels, values: vals }], {
    x: MX, y: 1.5, w: 8.6, h: 5.35, barDir: "bar", catAxisOrientation: "maxMin",
    chartColors: allTests.map(({ k }) => (k === "uji" ? NAVY : TEAL)),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 12,
    dataLabelColor: INK, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelColor: INK, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelFontSize: 11, valAxisLabelColor: GREY, valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 10,
    valAxisMajorUnit: 1, valGridLine: { color: "E3E0D8", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: false, showTitle: true, title: "Sai số trung bình trên tập kiểm tra (m)", titleFontSize: 14,
    titleColor: NAVY, titleFontFace: "+mj-lt", barGapWidthPct: 45,
  });
  const x = MX + 9.0, w = SW - MX - x;
  stat(s, x, 1.7, w, `${nOk}/${allTests.length}`, "tập kiểm tra dưới 7 m", TEAL);
  stat(s, x, 3.2, w, `${vn(Math.min(...allTests.map((a) => a.v.sai_so_tb_m)))}–${vn(Math.max(...allTests.filter((a) => a.k !== "uji").map((a) => a.v.sai_so_tb_m)))} m`, "khoảng sai số trên 5 bộ ngoài UJIIndoorLoc", NAVY);
  stat(s, x, 4.7, w, `${vn(UT.sai_so_tb_m)} m`, `UJIIndoorLoc (${vn(UT.so_mau, 0)} vân tay), v4: ${vn(U4.mean_err_m)} m`, NAVY);
}

// ------------------------------------------------------------------ 15. UJIIndoorLoc
{
  const s = slide("04 · Phân tích", "UJIIndoorLoc: sai số còn lại nằm chủ yếu trong tầng",
    `Trung vị ${vn(UT.trung_vi_m)} m, đúng tòa ${pct(UT.dung_toa)}, đúng tòa-tầng ${pct(UT.dung_toa_tang)}. ${pct(split[0].phan_tong_sai_so)} tổng sai số nằm ở các mẫu đã đoán đúng tầng, nên điểm nghẽn là độ phân giải trong tầng: mỗi ô chỉ có khoảng ${vn(U.mining.giao_dich_tb_moi_o, 0)} vân tay của một tới bốn người dùng. Thêm vào đó, 9/11 điện thoại của tập kiểm tra không có trong tập huấn luyện.`);
  const cw = 2.85;
  [[`${vn(UT.sai_so_tb_m)} m`, "sai số trung bình", NAVY], [`${vn(UT.trung_vi_m)} m`, "trung vị", NAVY],
   [pct(UT.dung_toa_tang), "đúng tòa và tầng", TEAL], [pct(split[0].phan_tong_sai_so), "tổng sai số thuộc mẫu đúng tầng", NAVY]]
    .forEach(([v, l, c], i) => stat(s, MX + i * (cw + 0.13), 1.6, cw, v, l, c));
  table(s, ["Nhóm mẫu", "Số mẫu", "Sai số TB (m)", "Phần tổng sai số"],
    split.map((x) => [x.nhom, vn(x.so_mau, 0), vn(x.sai_so_tb_m), pct(x.phan_tong_sai_so)]),
    MX, 3.35, 6.2, [2.6, 1.0, 1.25, 1.35], { align: ["left", "right", "right", "right"], size: 13, rowH: 0.42 });
  bullets(s, [
    `Bước 8 giảm sai số mẫu đúng tầng từ 7,78 m xuống **${vn(split[0].sai_so_tb_m)} m**`,
    `Mỗi ô chỉ có khoảng ${vn(U.mining.giao_dich_tb_moi_o, 0)} vân tay của một tới bốn người dùng`,
    "**9/11 điện thoại** của tập kiểm tra không có trong tập huấn luyện",
  ], MX, 4.85, 6.3, 2.0, 14);
  img(s, path.join(ROOT, "figures", "huim_only", "fig61_huim_only_cdf_uji.png"), MX + 6.6, 3.2, SW - 2 * MX - 6.6, 3.7, "right", "Phân bố sai số UJIIndoorLoc");
}

// ------------------------------------------------------------------ 16. phiên bản
{
  const s = slide("04 · Phân tích", "Lịch sử phiên bản và lựa chọn mô hình cuối",
    "Mọi lựa chọn dựa trên sai số dev. Trong các phiên bản Bước 1–7, v1 có sai số kiểm tra thấp nhất nhưng dev kém nhất nên không được chọn. v5 và v6 thêm Bước 8; v6 có sai số dev thấp nhất nên là mô hình cuối, và tập kiểm tra chỉ được chấm sau khi đã chọn.");
  const V = D.versions;
  table(s, ["Phiên bản", "Thay đổi", "Fold dev", "Dev TB (m)", "Kiểm tra TB (m)", "Đúng tầng"],
    V.map((v) => [v.version.replace(" (final)", " (cuối)"), v.change_vi, v.dev_folds === "leave-phones-out" ? "theo điện thoại" : "theo người dùng",
      vn(v.dev_mean_m), vn(v.test_mean_m), pct(v.test_floor_accuracy)]),
    MX, 1.6, SW - 2 * MX, [1.2, 5.9, 1.55, 1.15, 1.35, 0.98],
    { align: ["left", "left", "left", "right", "right", "right"], size: 11, rowH: 0.5, hl: (i) => i === V.length - 1 });
  panel(s, MX, 5.85, SW - 2 * MX, 0.95, SOFT);
  text(s, `**Nguyên tắc:** mọi lựa chọn dựa trên dev; v1 có kiểm tra thấp nhất trong Bước 1–7 nhưng dev kém nhất nên không được chọn. Mô hình cuối là **v6** (dev ${vn(V6.dev_mean_m)} m), chấm tập kiểm tra đúng một lần: **${vn(UT.sai_so_tb_m)} m**.`,
    MX + 0.3, 6.0, SW - 2 * MX - 0.6, 0.7, { fontSize: 14 });
}

// ------------------------------------------------------------------ 16b. biến thể Bước 8
{
  const s = slide("04 · Phân tích", "Bước 8: những gì đã thử trên dev",
    "Mọi biến thể được so bằng sai số dev ngoài fold trên 19 937 truy vấn; tập kiểm tra không được đọc. Trọng số IDF của HUI và mô hình mục theo mức cường độ dùng riêng không cải thiện; chúng chỉ có ích khi làm bằng chứng bổ sung cho bộ hồi quy. Bộ phân loại tầng học trên dev tăng độ chính xác tầng nhưng không giảm sai số vị trí nên không dùng.");
  const L3 = RSH["level items (AP, strength level) alone, fold 0"];
  const rows = [["Bước 1–7, một điểm khớp HUI (v4)", vn(RSH["v4 (baseline)"]), "mốc"],
    ["Trọng số IDF của HUI giữa các ô lân cận", vn(RSH["IDF weight of HUIs (best)"]), "gần như không đổi"],
    ["Chỉ dùng mô hình mục theo mức cường độ (fold 0)", `${vn(L3.L3)} so với ${vn(L3.v4)}`, "kém hơn"],
    ["Xếp hạng lại bằng các điểm HUI", vn(RSH["re-rank, HUI scores"]), "cải thiện"],
    ["+ hồ sơ cường độ suy ra từ HUI", vn(RSH["re-rank + HUI strength profile"]), "cải thiện"],
    ["Ứng viên trên cả toà nhà", vn(RSH["re-rank, candidates over the whole building"]), "không dùng"],
    ["+ đặc trưng so với các ứng viên khác (v5)", vn(RSH["re-rank + features relative to the query's candidates (v5)"]), "cải thiện"],
    ["v5 học khi bỏ ô của chính truy vấn", vn(RSH["v5 trained leave-own-cell-out"]), "không dùng"],
    ["v5 + mô hình HUI lợi ích abs (v6)", vn(RSH["v5 + abs HUI model (v6)"]), "chọn"]];
  table(s, ["Biến thể", "Dev TB (m)", "Kết luận"], rows, MX, 1.6, 8.6, [5.4, 1.5, 1.7],
    { align: ["left", "right", "left"], size: 13, rowH: 0.48, hl: (i) => i === rows.length - 1 });
  const x = MX + 9.0, w = SW - MX - x;
  stat(s, x, 1.7, w, `${vn(RSH["v4 (baseline)"])} m`, "dev, Bước 1–7 (v4)", GREY);
  stat(s, x, 3.2, w, `${vn(V6.dev_mean_m)} m`, "dev, mô hình cuối (v6)", TEAL);
  stat(s, x, 4.7, w, `${vn(UT.sai_so_tb_m)} m`, "tập kiểm tra, chấm một lần", NAVY);
}

// ------------------------------------------------------------------ 17. tham chiếu
{
  const s = slide("04 · So sánh", "Đặt cạnh các hệ thống dùng k-NN",
    "Trên UJIIndoorLoc, hệ thống chỉ dùng HUIM tốt hơn k-NN gốc nhưng kém k-NN đã tối ưu. Trên các bộ dữ liệu một tầng, k-NN cho sai số thấp hơn vì vị trí kiểm tra trùng hoặc rất gần điểm tham chiếu. Ưu điểm của thiết kế là toàn bộ quyết định định vị đến từ mẫu HUI.");
  const R = D.references;
  table(s, ["Bộ dữ liệu", "Tập kiểm tra", "Chỉ HUIM", "k-NN gốc", "k-NN tối ưu", "HUIM chọn AP + k-NN"],
    R.map((x) => [D.title[x.dataset], x.tap_test, vn(x.chi_huim_m), x.knn_goc_m != null ? vn(x.knn_goc_m) : "–",
      x.knn_toi_uu_m != null ? vn(x.knn_toi_uu_m) : "–",
      x.huim_chon_ap_knn_m != null ? `${vn(x.huim_chon_ap_knn_m)} (${x.huim_chon_ap_so_ap}/${x.tong_ap} AP)` : "–"]),
    MX, 1.55, 8.3, [2.0, 1.45, 1.05, 1.05, 1.15, 1.6], { align: ["left", "left", "right", "right", "right", "right"], size: 12, rowH: 0.42, hl: (i) => i === 0 });
  const x = MX + 8.7, w = SW - MX - x;
  text(s, "**Đọc bảng**", x, 1.6, w, 0.4, { fontSize: 17, color: NAVY });
  bullets(s, [
    "Đơn vị: mét, sai số trung bình trên tập kiểm tra",
    "UJIIndoorLoc: chỉ HUIM tốt hơn **k-NN gốc**, kém k-NN đã tối ưu",
    "Bộ một tầng: vị trí kiểm tra trùng hoặc rất gần điểm tham chiếu, lợi thế cho k-NN",
    "Ở hệ thống đề xuất, bỏ HUIM thì không còn mô hình định vị",
  ], x, 2.1, w, 4.7, 14);
}

// ------------------------------------------------------------------ 18. kiểm chứng
{
  const s = slide("04 · Kiểm chứng", "Mọi con số đều tính lại được độc lập",
    "Có ba cách kiểm tra: chương trình kiểm chứng độc lập không gọi EFIM hay bộ định vị; sổ Excel tính lại sai số bằng công thức; script chỉ dùng thư viện chuẩn của Python. Cả ba đều khớp với con số báo cáo.");
  const w = (SW - 2 * MX - 0.6) / 3;
  const cols = [
    [`${D.verification.n_checks} phép kiểm`, `${D.verification.n_failed} thất bại`, "Chương trình kiểm chứng độc lập: đọc dữ liệu gốc, tính lại lợi ích, kiểm tra HUI vượt ngưỡng, điểm khớp, tầng và toạ độ của mẫu ngẫu nhiên; không gọi EFIM hay bộ định vị."],
    ["Sổ Excel", "so_lieu/kiem_chung_mean.xlsx", "Mỗi tập kiểm tra một sheet; sai số từng mẫu = SQRT((x̂ − x)² + (ŷ − y)²)·g; AVERAGE so với số báo cáo. Sheet ví dụ dựng lại toạ độ một truy vấn bằng SUMPRODUCT."],
    ["Script Python", "so_lieu/kiem_tra_mean.py", "Chỉ dùng thư viện chuẩn: đọc du_doan/*.csv, tính lại sai số trung bình, trung vị và tỷ lệ đúng tòa-tầng; in KHỚP hoặc LỆCH cho từng tập kiểm tra."],
  ];
  cols.forEach(([a, b, c], i) => {
    const x = MX + i * (w + 0.3);
    panel(s, x, 1.65, w, 3.85, i === 0 ? SOFT : "FBFAF7");
    s.addText(a, { x: x + 0.3, y: 1.9, w: w - 0.6, h: 0.7, fontFace: HF, fontSize: 26, bold: true, color: i === 0 ? TEAL : NAVY, margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.3, y: 2.6, w: w - 0.6, h: 0.45, fontFace: BF, fontSize: 14, bold: true, color: GREY, margin: 0, isTextBox: true });
    text(s, c, x + 0.3, 3.25, w - 0.6, 2.1, { fontSize: 15 });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 5.8, w: SW - 2 * MX, h: 0.85, fill: { color: NAVY }, line: { color: NAVY } });
  text(s, `**Kết quả:** cả ${allTests.length}/${allTests.length} tập kiểm tra KHỚP, chênh lệch giữa sai số tính lại và sai số báo cáo dưới 0,00005 m.`,
    MX + 0.3, 6.0, SW - 2 * MX - 0.6, 0.5, { fontSize: 16, color: "FFFFFF", valign: "middle" });
}

// ------------------------------------------------------------------ 19. kết luận
section("Kết luận");
{
  const s = pres.addSlide({ masterName: "TIEU_DE", sectionTitle: "Kết luận" });
  s.addText("05 · KẾT LUẬN", { x: MX, y: 0.55, w: 8, h: 0.4, fontFace: BF, fontSize: 13, bold: true, color: "9BB7C4", charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Kết luận và hướng phát triển", { x: MX, y: 0.95, w: 11, h: 0.8, fontFace: HF, fontSize: 32, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  const col = (x, title, items) => {
    s.addText(title, { x, y: 2.05, w: 5.7, h: 0.45, fontFace: HF, fontSize: 19, bold: true, color: "9BB7C4", margin: 0, isTextBox: true });
    bullets(s, items, x, 2.6, 5.7, 4.3, 15, "FFFFFF");
  };
  col(MX, "Kết quả đạt được", [
    "HUIM là thuật toán định vị chính: mô hình là tập HUI của từng ô, tầng và toạ độ đến từ bằng chứng HUI; **không dùng k-NN**",
    `**${nOk}/${allTests.length}** tập kiểm tra của 6 bộ dữ liệu đạt sai số trung bình dưới 7 m`,
    `UJIIndoorLoc: **${vn(UT.sai_so_tb_m)} m** (v4: ${vn(U4.mean_err_m)} m) nhờ xếp hạng lại bằng bằng chứng HUI; biên dưới 7 m còn nhỏ`,
    "Tham số chọn trên dev, mọi con số kiểm chứng được",
  ]);
  col(MX + 6.3, "Hướng phát triển", [
    "Lợi ích nội bất biến hơn với thiết bị, ví dụ hiệu chỉnh độ lệch theo từng điện thoại",
    "Tăng độ phân giải trong tầng bằng ô nhỏ hơn hoặc kết hợp HUI ở nhiều mức không gian",
    "Thay bộ hồi quy Bước 8 bằng quy tắc kết hợp tường minh, dễ diễn giải hơn",
    "Dùng HUI đóng hoặc HUI cực đại và cài đặt EFIM biên dịch để giảm số mẫu và thời gian định vị",
  ]);
  s.addNotes("Tóm lại, đề tài đã chuyển HUIM từ vai trò tiền xử lý sang vai trò thuật toán định vị. Kết quả đạt mục tiêu dưới 7 m trên cả sáu bộ dữ liệu; trên UJIIndoorLoc nhờ Bước 8, với biên nhỏ cần nói rõ.");
}

// ------------------------------------------------------------------ 20. cảm ơn
{
  const s = pres.addSlide({ masterName: "TIEU_DE", sectionTitle: "Kết luận" });
  s.addText("Xin cảm ơn quý thầy cô đã lắng nghe", { placeholder: "title" });
  s.addText("Rất mong nhận được ý kiến đóng góp", { x: MX, y: 3.95, w: 11, h: 0.5, fontFace: BF, fontSize: 20, italic: true, color: "DCE6EE", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: MX, y: 4.85, w: 3.0, h: 0, line: { color: "9BB7C4", width: 1 } });
  s.addText("Mã nguồn, số liệu và sổ kiểm chứng: thư mục BAOCAO", { x: MX, y: 5.05, w: 11, h: 0.4, fontFace: BF, fontSize: 15, color: "FFFFFF", margin: 0, isTextBox: true });
}

// ------------------------------------------------------------------ ghi file
const out = path.join(B, "Slide_HUIM_IPS_UJIIndoorLoc.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  const apply = process.env.PPTX_APPLY_THEME;           // scripts/apply_theme.js của skill pptx, nếu có
  if (apply && fs.existsSync(apply)) await require(apply).applyTheme(out, THEME);
  fs.rmSync(FX, { recursive: true, force: true });
  console.log("written", out, fs.statSync(out).size);
});
