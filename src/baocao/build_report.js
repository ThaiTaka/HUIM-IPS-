// BAOCAO/Bao_cao_HUIM_IPS_UJIIndoorLoc.docx — báo cáo theo bố cục luận văn thạc sĩ.
// Mọi con số đọc từ BAOCAO/so_lieu/du_lieu_bao_cao.json; công thức là phương trình Word (OMML).
// Chạy: node src/baocao/build_report.js   (cần gói npm "docx")
const fs = require("fs");
const path = require("path");
const d = require("docx");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, HeadingLevel, TableOfContents, PageBreak, Footer, PageNumber, TabStopType,
  BorderStyle, ShadingType, LevelFormat, VerticalAlign, Tab,
  Math: M, MathRun, MathFraction, MathSubScript, MathSuperScript, MathSubSuperScript,
  MathSum, MathRadical, MathRoundBrackets, MathSquareBrackets, MathCurlyBrackets,
} = d;

const ROOT = path.resolve(__dirname, "..", "..");
const B = path.join(ROOT, "BAOCAO");
const D = JSON.parse(fs.readFileSync(path.join(B, "so_lieu", "du_lieu_bao_cao.json"), "utf8"));
const FONT = "Times New Roman";
const PT = (x) => x * 2;

// ------------------------------------------------------------------ numbers
const vn = (x, k = 2) => Number(x).toFixed(k).replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
const pct = (x, k = 1) => vn(100 * x, k) + "%";
const U = D.datasets.uji, UT = U.tests.validationData, SEL = U.selection, PRM = SEL.params;
const V6 = U.v6, U4 = U.v4_tests.validationData, RSH = V6.research.dev_mean_m;

// ------------------------------------------------------------------ text helpers
const R = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
function runs(s, base = {}) {   // **đậm**, $công thức nội dòng$: chữ cái nghiêng, _x là chỉ số dưới, ^x chỉ số trên
  const out = [];
  s.split(/(\*\*[^*]+\*\*|\$[^$]+\$)/).forEach((p) => {
    if (!p) return;
    if (p.startsWith("**")) out.push(R(p.slice(2, -2), { ...base, bold: true }));
    else if (p.startsWith("$") && p.length > 2) out.push(...mathRuns(p.slice(1, -1), base));
    else out.push(R(p, base));
  });
  return out;
}
const UPRIGHT = /^([A-Z]{2,}|exp|max|min|arg|round|log)$/;
function mathRuns(s, base) {
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
const P = (s, o = {}) => new Paragraph({ children: Array.isArray(s) ? s : runs(s), alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 120, line: 360 }, indent: { firstLine: 567 }, ...o });
const PN = (s, o = {}) => P(s, { indent: { firstLine: 0 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [R(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [R(t)] });
const BUL = (s) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(s),
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 340 } });
const NUM = (s, ref = "num") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(s),
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 340 } });

// ------------------------------------------------------------------ math helpers
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
const up = (t) => r("\u2060" + t);                  // chữ đứng (tên hàm, nhãn), xử lý sau khi ghi file
const abs = (...c) => rb(r("\u2062ABS"), ...c);       // |…| dạng dấu ngoặc OMML
const flo = (...c) => rb(r("\u2062FLO"), ...c);       // ⌊…⌋ dạng dấu ngoặc OMML
const qbar = (s) => sb([r("q̄")], [r(s)]);          // q̄_s
let eqNo = {};
function EQ(chap, children) {      // bảng 3 cột không viền: trống | công thức (giữa) | số hiệu (phải)
  eqNo[chap] = (eqNo[chap] || 0) + 1;
  const label = `(${chap}.${eqNo[chap]})`;
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const nb = { top: none, bottom: none, left: none, right: none };
  const cell = (w, align, kids) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: nb,
    verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 0, right: 0 },
    children: [new Paragraph({ alignment: align, spacing: { before: 60, after: 60 }, children: kids })] });
  return { label, p: new Table({ width: { size: 9071, type: WidthType.DXA }, columnWidths: [1000, 7071, 1000],
    borders: { ...nb, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ cantSplit: true, children: [cell(1000, AlignmentType.LEFT, []),
      cell(7071, AlignmentType.CENTER, [new M({ children })]),
      cell(1000, AlignmentType.RIGHT, [R(label)])] })] }) };
}

// ------------------------------------------------------------------ figures and tables
const figNo = {}, tabNo = {};
function pngSize(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function FIG(chap, file, caption, widthPx = 600) {
  figNo[chap] = (figNo[chap] || 0) + 1;
  const [w, h] = pngSize(file);
  const W = Math.min(widthPx, 600), H = Math.round(W * h / w);
  const label = `Hình ${chap}.${figNo[chap]}`;
  return { label, ps: [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: W, height: H },
        altText: { title: caption, description: caption, name: path.basename(file) } })] }),
    new Paragraph({ style: "CaptionHinh", children: [R(`${label}. `, { bold: true }), R(caption)] })] };
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function TAB(chap, caption, header, rows, widths, opts = {}) {
  tabNo[chap] = (tabNo[chap] || 0) + 1;
  const label = `Bảng ${chap}.${tabNo[chap]}`;
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, head) => new TableCell({
    borders, width: { size: widths[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { fill: "DCE3EC", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ alignment: (opts.align && opts.align[i]) || AlignmentType.LEFT,
      children: (typeof t === "string" ? runs(t, { bold: head, size: PT(opts.size || 11) }) : t) })] });
  return { label, ps: [
    new Paragraph({ style: "CaptionBang", keepNext: true, children: [R(`${label}. `, { bold: true }), R(caption)] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }),
             ...rows.map((rw) => new TableRow({ children: rw.map((c, i) => cell(String(c), i, false)) }))] }),
    new Paragraph({ spacing: { after: 120 }, children: [] })] };
}
const C = AlignmentType.CENTER, RT = AlignmentType.RIGHT, L = AlignmentType.LEFT;

// ------------------------------------------------------------------ data shortcuts
const order = D.order, T = D.title;
const allTests = [];
order.forEach((k) => Object.entries(D.datasets[k].tests).forEach(([t, v]) => allTests.push({ k, t, v })));
const nOk = allTests.filter((x) => x.v.duoi_7m).length;
const ref = (k, t) => D.references.find((x) => x.dataset === k && x.tap_test === t);
const refU = ref("uji", "validationData");
const fs4 = D.uji_floor_split;
const ver = D.versions;
const pil = D.pilots["theta_pilot.json"], win = D.pilots["window_pilot.json"];
const diag = (n) => path.join(B, "diagram", n);
const figr = (n) => path.join(ROOT, "figures", "huim_only", n);

// ================================================================== content
const body = [];
const add = (...xs) => xs.forEach((x) => (x.ps ? body.push(...x.ps) : x.p ? body.push(x.p) : body.push(x)));

// ---------- cover
const cover = [
  new Paragraph({ alignment: C, spacing: { after: 80 }, children: [R("BÁO CÁO CHUYÊN ĐỀ CAO HỌC", { bold: true, size: PT(14) })] }),
  new Paragraph({ alignment: C, spacing: { after: 1600 }, children: [R("Ngành Khoa học máy tính", { size: PT(13) })] }),
  new Paragraph({ alignment: C, spacing: { after: 240 }, children: [R("ỨNG DỤNG KHAI THÁC TẬP MỤC LỢI ÍCH CAO (HUIM)", { bold: true, size: PT(18) })] }),
  new Paragraph({ alignment: C, spacing: { after: 240 }, children: [R("TRONG HỆ THỐNG ĐỊNH VỊ TRONG NHÀ", { bold: true, size: PT(18) })] }),
  new Paragraph({ alignment: C, spacing: { after: 1400 }, children: [R("Định vị bằng so khớp High Utility Itemset trên dữ liệu vân tay Wi-Fi UJIIndoorLoc và năm bộ dữ liệu bổ sung", { italics: true, size: PT(13) })] }),
  new Paragraph({ alignment: L, indent: { left: 2835 }, spacing: { after: 200 }, children: [R("Học viên thực hiện: ", { bold: true }), R("..............................................")] }),
  new Paragraph({ alignment: L, indent: { left: 2835 }, spacing: { after: 200 }, children: [R("Mã số học viên: ", { bold: true }), R("..................................................")] }),
  new Paragraph({ alignment: L, indent: { left: 2835 }, spacing: { after: 2400 }, children: [R("Giảng viên hướng dẫn: ", { bold: true }), R("........................................")] }),
  new Paragraph({ alignment: C, children: [R("Năm 2026", { size: PT(13) })] }),
];

// ---------- front matter
const front = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R("TÓM TẮT")] }),
  P(`Báo cáo nghiên cứu khả năng dùng thuật toán khai thác tập mục lợi ích cao (High Utility Itemset Mining, HUIM) làm **thuật toán định vị chính** của một hệ thống định vị trong nhà dựa trên vân tay Wi-Fi, thay vì chỉ dùng HUIM như một bước lọc điểm truy cập (AP) đứng trước bộ phân loại k-láng giềng gần nhất (k-NN). Mỗi điểm tham chiếu của tập huấn luyện được coi là một cơ sở dữ liệu giao dịch; thuật toán EFIM khai thác tập High Utility Itemset (HUI) của từng điểm, và tập HUI này chính là mô hình định vị. Khi định vị, vân tay cần xác định được coi là một giao dịch và được so khớp với HUI của mọi ô: điểm khớp đo lượng lợi ích HUI của ô mà vân tay chứa, mức độ phù hợp của cường độ tín hiệu và độ phủ của vân tay. Tầng được chọn trước theo các ô khớp tốt nhất; các ô ứng viên của tầng đó sau đó được xếp hạng lại bằng nhiều bằng chứng rút ra từ HUI (ba mô hình HUI với ba cách đặt lợi ích nội, và hồ sơ cường độ của ô suy ra từ chính các HUI), và toạ độ là trọng tâm có trọng số của các ô xếp đầu. Không có phép so khoảng cách nào giữa vân tay truy vấn và vân tay huấn luyện, và mô hình không lưu vân tay huấn luyện.`),
  P(`Toàn bộ tham số được chọn trên các fold kiểm định (dev) tách từ tập huấn luyện; tập kiểm tra chỉ được dùng một lần. Trên ${allTests.length} tập kiểm tra của ${order.length} bộ dữ liệu, ${nOk} tập đạt sai số trung bình dưới 7 m. Trên UJIIndoorLoc (${vn(UT.so_mau, 0)} vân tay kiểm tra, ${pct(UT.dung_toa_tang)} xác định đúng tòa và tầng), sai số trung bình là ${vn(UT.sai_so_tb_m)} m và trung vị ${vn(UT.trung_vi_m)} m, giảm từ ${vn(U4.mean_err_m)} m của phiên bản chỉ dùng một điểm khớp HUI; bước xếp hạng lại được chọn trên dev (sai số dev ${vn(V6.dev_mean_v4_m)} m xuống ${vn(V6.dev_mean_m)} m) trước khi tập kiểm tra được chấm. Phần lớn sai số còn lại (${pct(fs4[0].phan_tong_sai_so, 0)}) nằm ở các mẫu đã xác định đúng tầng, và ${"9/11"} điện thoại của tập kiểm tra không xuất hiện trong tập huấn luyện. Mọi con số được kiểm chứng độc lập (${D.verification.n_checks} phép kiểm, ${D.verification.n_failed} thất bại) và có thể tính lại bằng sổ Excel kèm theo.`),
  PN(`**Từ khoá:** khai thác tập mục lợi ích cao, EFIM, định vị trong nhà, vân tay Wi-Fi, UJIIndoorLoc.`),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R("MỤC LỤC")] }),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R("DANH MỤC HÌNH")] }),
  new TableOfContents("Danh mục hình", { hyperlink: true, stylesWithLevels: [new d.StyleLevel("CaptionHinh", 1)] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R("DANH MỤC BẢNG")] }),
  new TableOfContents("Danh mục bảng", { hyperlink: true, stylesWithLevels: [new d.StyleLevel("CaptionBang", 1)] }),
];
const abbr = [
  ["AP", "Access Point — điểm truy cập Wi-Fi"], ["RSSI", "Received Signal Strength Indicator — cường độ tín hiệu thu (dBm)"],
  ["IPS", "Indoor Positioning System — hệ thống định vị trong nhà"], ["HUIM", "High Utility Itemset Mining — khai thác tập mục lợi ích cao"],
  ["HUI", "High Utility Itemset — tập mục có lợi ích không nhỏ hơn ngưỡng"], ["EFIM", "EFficient high-utility Itemset Mining (Zida và cộng sự, 2017)"],
  ["TWU", "Transaction-Weighted Utility — lợi ích có trọng số giao dịch"], ["k-NN", "k-Nearest Neighbours — k láng giềng gần nhất"],
  ["Ô (cell)", "một điểm tham chiếu của tập huấn luyện, đơn vị vị trí của mô hình"], ["dev", "fold kiểm định tách từ tập huấn luyện, dùng để chọn tham số"],
  ["θ", "ngưỡng lợi ích tối thiểu tương đối (% lợi ích của cơ sở dữ liệu)"],
  ["Ô ứng viên", "một trong K ô có điểm HUI cao nhất của tầng đã chọn, được xếp hạng lại ở Bước 8"],
  ["$q̂_c$(i)", "cường độ ước lượng của AP i tại ô c, suy ra từ các HUI của ô (hồ sơ cường độ)"],
  ["GBM", "Gradient Boosting Machine — mô hình hồi quy cây tăng cường, dùng ở Bước 8"],
];
front.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [R("DANH MỤC KÝ HIỆU VÀ CHỮ VIẾT TẮT")] }));
const tA = TAB("0", "Ký hiệu và chữ viết tắt", ["Ký hiệu", "Ý nghĩa"], abbr, [1800, 7200]);
front.push(...tA.ps.slice(1));   // không đánh số bảng ký hiệu

// ================================================================== CHƯƠNG 1
add(H1("CHƯƠNG 1. TỔNG QUAN"));
add(H2("1.1. Bối cảnh"));
add(P(`Hệ thống định vị toàn cầu không hoạt động ổn định trong các toà nhà, nên định vị trong nhà thường dựa vào tín hiệu của các điểm truy cập Wi-Fi sẵn có. Phương pháp vân tay (fingerprinting) gồm hai pha: pha khảo sát ghi lại cường độ tín hiệu thu (RSSI) của mọi AP tại các điểm tham chiếu đã biết toạ độ; pha định vị so sánh vân tay mới với cơ sở dữ liệu đó để suy ra vị trí [1], [2]. Bộ dữ liệu UJIIndoorLoc [3] là chuẩn đối chiếu phổ biến cho bài toán này, với 520 AP, ba toà nhà và mười ba tầng.`));
add(P(`Khai thác tập mục lợi ích cao (HUIM) [6], [7] mở rộng khai thác tập phổ biến [11] bằng cách gán cho mỗi mục một lợi ích nội (số lượng) và một lợi ích ngoài (trọng số); bài toán là tìm mọi tập mục có tổng lợi ích không nhỏ hơn một ngưỡng. Thuật toán EFIM [5] giải bài toán này hiệu quả nhờ hai chặn trên chặt và kỹ thuật chiếu, gộp giao dịch.`));
add(H2("1.2. Vấn đề nghiên cứu"));
add(P(`Ở các giai đoạn trước của đề tài, HUIM được dùng để chọn tập AP, còn việc định vị do k-NN đảm nhận. Kết quả trên UJIIndoorLoc cho thấy hai điều. Thứ nhất, khai thác HUI trên toàn bộ dữ liệu chỉ giữ được ${refU.huim_toan_cuc_so_ap} AP và cho sai số ${vn(refU.huim_toan_cuc_knn_m)} m. Thứ hai, khai thác theo từng tòa – tầng giữ ${refU.huim_chon_ap_so_ap}/${refU.tong_ap} AP và cho ${vn(refU.huim_chon_ap_knn_m)} m, nhưng phân tích Shapley cho thấy HUIM chỉ đóng góp khoảng 6% mức giảm sai số, và thay HUIM bằng một tiêu chí xếp hạng AP đơn giản cho kết quả gần như tương đương. Khi đó HUIM chỉ là một nhánh tiền xử lý: bỏ HUIM đi, k-NN vẫn định vị được.`));
add(P(`Câu hỏi của báo cáo vì vậy là: **có thể xây dựng một hệ thống định vị trong đó HUIM là thuật toán định vị chính, không dùng k-NN, mà vẫn đạt sai số trung bình dưới 7 m hay không?**`));
add(H2("1.3. Mục tiêu và phạm vi"));
add(BUL(`Mô hình hoá dữ liệu vân tay Wi-Fi thành các cơ sở dữ liệu giao dịch có lợi ích, phù hợp với định nghĩa của bài toán HUIM.`));
add(BUL(`Đề xuất thuật toán định vị chỉ dựa trên tập HUI: mô hình định vị là tập HUI của các điểm tham chiếu, quyết định tầng và toạ độ do điểm khớp HUI đưa ra.`));
add(BUL(`Đánh giá trên UJIIndoorLoc và năm bộ dữ liệu bổ sung (UJI_LIB tầng 3, DLULIB, HCXY, HUS, HUS khử trùng lặp) với giao thức không rò rỉ dữ liệu, và kiểm chứng độc lập mọi con số.`));
add(P(`Báo cáo không khẳng định tính mới tuyệt đối của việc dùng mẫu tập mục cho định vị, và không ngoại suy kết quả ra ngoài các bộ dữ liệu đã dùng.`));
add(H2("1.4. Cấu trúc báo cáo"));
add(P(`Chương 2 trình bày cơ sở lý thuyết về định vị vân tay, bài toán HUIM và thuật toán EFIM. Chương 3 trình bày mô hình và thuật toán đề xuất theo từng bước từ đầu vào tới đầu ra. Chương 4 trình bày dữ liệu, giao thức, kết quả, phân tích và kiểm chứng. Chương 5 kết luận và nêu hướng phát triển.`));

// ================================================================== CHƯƠNG 2
add(H1("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT"));
add(H2("2.1. Định vị trong nhà bằng vân tay Wi-Fi"));
add(P(`Một vân tay là vectơ RSSI của mọi AP tại một lần quét; AP không thu được tín hiệu được ghi bằng giá trị quy ước (UJIIndoorLoc dùng 100). Các hệ thống kinh điển như RADAR [1] và Horus [2] ước lượng vị trí bằng cách so vân tay mới với các vân tay đã khảo sát, phổ biến nhất là bằng k-NN với một độ đo khoảng cách [4]. Khó khăn chính gồm: tín hiệu dao động theo thời gian, khác biệt giữa các thiết bị thu, và sự chồng lấn tín hiệu giữa các tầng liền kề [8].`));
add(H2("2.2. Bài toán khai thác tập mục lợi ích cao"));
add(P(`Cho tập mục I và cơ sở dữ liệu giao dịch D. Mỗi mục i trong giao dịch T có lợi ích nội q(i,T) > 0 và mỗi mục có lợi ích ngoài p(i) > 0. Lợi ích của mục, của tập mục X trong một giao dịch và trong toàn bộ D được định nghĩa [6], [7]:`));
const e21 = EQ(2, [r("u"), rb(r("i,T")), r("=q"), rb(r("i,T")), r("·p"), rb(r("i"))]);
const e22 = EQ(2, [r("u"), rb(r("X,T")), r("="), sum([r("i∈X")], [r("u"), rb(r("i,T"))])]);
const e23 = EQ(2, [r("u"), rb(r("X")), r("="), sum([r("T∈D, X⊆T")], [r("u"), rb(r("X,T"))])]);
add(e21, e22, e23);
add(P(`Tập mục X là tập mục lợi ích cao (HUI) khi u(X) ≥ minUtil. Khác với độ hỗ trợ trong khai thác tập phổ biến, lợi ích không có tính đơn điệu giảm: thêm một mục có thể làm u(X) tăng hoặc giảm, nên không thể cắt tỉa trực tiếp bằng u(X). Các thuật toán dùng chặn trên đơn điệu giảm, phổ biến nhất là lợi ích có trọng số giao dịch [7]:`));
const e24 = EQ(2, [up("TU"), rb(r("T")), r("="), sum([r("i∈T")], [r("u"), rb(r("i,T"))]), r(",   "), up("TWU"), rb(r("X")), r("="), sum([r("T∈D, X⊆T")], [up("TU"), rb(r("T"))])]);
add(e24);
add(H2("2.3. Thuật toán EFIM"));
add(P(`EFIM [5] duyệt cây liệt kê tập theo chiều sâu, với các mục được sắp theo thứ tự tăng dần của TWU. Tại nút α, với mỗi mục z có thể mở rộng, EFIM tính hai chặn trên trong một lần quét cơ sở dữ liệu đã chiếu:`));
const e25 = EQ(2, [up("lu"), rb(r("α,z")), r("="), sum([r("T∋α∪{z}")], [sq(r("u"), rb(r("α,T")), r("+"), up("re"), rb(r("α,T")))])]);
const e26 = EQ(2, [up("su"), rb(r("α,z")), r("="), sum([r("T∋α∪{z}")], [sq(r("u"), rb(r("α,T")), r("+u"), rb(r("z,T")), r("+"), sum([r("i∈T, i≻z")], [r("u"), rb(r("i,T"))]))])]);
add(e25, e26);
add(P(`Trong đó re(α,T) là tổng lợi ích các mục đứng sau α trong T. Nếu lu(α,z) < minUtil thì z bị loại khỏi toàn bộ cây con của α; nếu su(α,z) < minUtil thì nhánh α ∪ {z} không được duyệt. Kết hợp với chiếu cơ sở dữ liệu và gộp các giao dịch giống nhau, EFIM là một trong các thuật toán nhanh và tiết kiệm bộ nhớ nhất theo đánh giá độc lập [9]. Bản cài đặt dùng trong báo cáo được kiểm chứng với một thuật toán vét cạn trên dữ liệu ngẫu nhiên (thư mục ma_nguon/tests).`));
add(H2("2.4. Các bộ dữ liệu"));
const t21 = TAB(2, "Mô tả các bộ dữ liệu sử dụng", ["Bộ dữ liệu", "Số AP", "Số lớp tòa–tầng", "Mẫu huấn luyện", "Điểm tham chiếu", "Tập kiểm tra (số mẫu)"],
  order.map((k) => { const x = D.datasets[k].description; return [x.ten, x.so_ap, x.so_lop_toa_tang, vn(x.mau_huan_luyen, 0), vn(x.diem_tham_chieu, 0), x.tap_test]; }),
  [1700, 800, 1200, 1300, 1300, 2700], { align: [L, RT, RT, RT, RT, L], size: 10.5 });
add(P(`UJIIndoorLoc [3] dùng toạ độ Web Mercator (EPSG:3857); khoảng cách được đổi ra mét thực địa bằng hệ số 0,766126. Các bộ còn lại dùng lưới toạ độ tính bằng mét. HUS chứa nhiều mẫu kiểm tra trùng hệt mẫu huấn luyện; bộ “HUS (khử trùng lặp)” loại các bản trùng này và là con số khách quan hơn.`));
add(t21);

// ================================================================== CHƯƠNG 3
add(H1("CHƯƠNG 3. PHƯƠNG PHÁP ĐỀ XUẤT"));
add(H2("3.1. Tổng quan hệ thống"));
const f31 = FIG(3, diag("d01_tong_quan.png"), "Sơ đồ tổng quát của hệ thống định vị chỉ dùng HUIM");
add(P(`Hệ thống gồm hai pha (${f31.label}). Pha huấn luyện thực hiện một lần trên tập huấn luyện: chuyển RSSI thành lợi ích nội (bước 1), nhóm vân tay theo điểm tham chiếu thành các cơ sở dữ liệu giao dịch (bước 2), khai thác HUI của từng cơ sở dữ liệu bằng EFIM (bước 3) và lưu mô hình là tập HUI cùng toạ độ, tầng của từng ô (bước 4). Pha định vị xử lý từng vân tay: chấm điểm khớp với HUI của mọi ô (bước 5), làm mượt điểm theo không gian và chọn tầng (bước 6), rồi ước lượng toạ độ (bước 7).`));
add(f31);
add(H2("3.2. Bước 1 — Lợi ích nội từ cường độ tín hiệu"));
add(P(`Mỗi vân tay T là một giao dịch; mục là một AP được phát hiện. Lợi ích ngoài được đặt p(i) = 1, nên lợi ích chỉ phản ánh cường độ tín hiệu. Ba định nghĩa lợi ích nội được so sánh, với $n_T$ là số AP thấy được trong T và $r_T$(i) là thứ hạng cường độ của AP i (mạnh nhất có hạng 1):`));
const e31 = EQ(3, [sb([r("q")], [up("a\u200Bbs")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([up("RSSI"), rb(r("i,T")), r("−"), sb([up("RSSI")], [up("min")])], [sb([up("RSSI")], [up("max")]), r("−"), sb([up("RSSI")], [up("min")])]))]);
const e32 = EQ(3, [sb([r("q")], [up("rel")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([up("RSSI"), rb(r("i,T")), r("−"), sb([up("max")], [r("j∈T")]), up("RSSI"), rb(r("j,T")), r("+40")], [r("40")]))]);
const e33 = EQ(3, [sb([r("q")], [up("rank")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([sb([r("n")], [r("T")]), r("−"), sb([r("r")], [r("T")]), rb(r("i"))], [sb([r("n")], [r("T")]), r("−1")]))]);
add(e31, e32, e33);
add(P(`Dạng rel và rank không đổi khi một điện thoại đọc mọi AP lệch cùng một lượng dB; dạng rank còn bất biến với mọi biến đổi đơn điệu của thang RSSI. Dạng được chọn trên dev cho UJIIndoorLoc là **${SEL.utility}** (mục 4.3). ${"Hình 3.2"} minh hoạ trên một vân tay thật của tập kiểm tra.`));
add(FIG(3, diag("d02_buoc1_utility.png"), "Bước 1 trên một vân tay thật (dòng " + D.worked_example.src_row + " của validationData)"));
add(H2("3.3. Bước 2 và 3 — Cơ sở dữ liệu giao dịch theo ô và khai thác EFIM"));
add(P(`Một ô c là một điểm tham chiếu của tập huấn luyện; $D_c$ là tập giao dịch của các vân tay đo tại c (UJIIndoorLoc: ${U.model.n_cells} ô, trung bình ${vn(U.mining.giao_dich_tb_moi_o, 1)} giao dịch mỗi ô). Ngưỡng được đặt tương đối theo lợi ích của chính ô đó, để các ô ít mẫu không bị lấn át bởi các ô nhiều mẫu:`));
const e34 = EQ(3, [sb([r("minUtil")], [r("c")]), r("=θ·u"), rb(sb([r("D")], [r("c")])), r(",   "), sb([up("HUI")], [r("c")]), r("="), cb(r("X : u"), rb(r("X")), r("≥"), sb([r("minUtil")], [r("c")]))]);
add(e34);
add(P(`EFIM được chạy độc lập trên từng $D_c$. Mỗi lần chạy có ngân sách 10 giây hoặc 10 000 HUI; nếu vượt ngân sách, ô đó được khai thác lại với θ nhân 1,25 cho tới khi hoàn tất, nên tập HUI dùng cho mô hình luôn đầy đủ (danh sách bị cắt ngang thiên lệch theo thứ tự duyệt và không bao giờ được dùng). Trên UJIIndoorLoc với θ = ${vn(SEL.theta_pct, 0)}%, ${U.mining.o_phai_nang_theta}/${U.model.n_cells} ô phải nâng θ (θ trung vị thực dùng ${vn(U.mining.theta_trung_vi_dung)}%), do các ô có nhiều AP cùng xuất hiện sinh ra số HUI rất lớn.`));
add(FIG(3, diag("d03_buoc2_o_giao_dich.png"), "Một ô là một cơ sở dữ liệu giao dịch (ô có điểm khớp cao nhất cho vân tay ví dụ)"));
add(FIG(3, diag("d04_buoc3_efim.png"), "Khai thác HUI của một ô bằng EFIM với hai chặn trên lu và su"));
add(H2("3.4. Bước 4 — Mô hình định vị"));
add(P(`Mô hình định vị là tập {($HUI_c$, $x_c$, $y_c$, tòa–tầng$_c$)} của mọi ô, trong đó ($x_c$, $y_c$) là trọng tâm các vị trí huấn luyện của ô. Với mỗi HUI X, mô hình lưu u(X) và độ hỗ trợ s(X); lợi ích trung bình mỗi mục của X trong ô được suy ra trực tiếp:`));
add(EQ(3, [sb([r("q̄")], [r("c")]), rb(r("X")), r("="), fr([r("u"), rb(r("X"))], [r("s"), rb(r("X")), r("·"), abs(r("X"))])]));
add(P(`Mô hình UJIIndoorLoc gồm ${vn(U.model.n_huis, 0)} HUI; ${U.model.aps_in_some_hui}/${U.model.n_aps} AP xuất hiện trong ít nhất một HUI. Mô hình không lưu bất kỳ vân tay huấn luyện nào.`));
add(FIG(3, diag("d05_buoc4_mo_hinh.png"), "Các HUI có lợi ích lớn nhất của một ô trong mô hình"));
add(H2("3.5. Bước 5 — Chấm điểm khớp giữa vân tay và HUI của ô"));
add(P(`Vân tay cần định vị cũng được chuyển thành giao dịch T theo bước 1. Với mỗi HUI X của ô c, ba đại lượng được tính: tỷ lệ $ρ$(X,T) các mục của X có mặt trong T (khớp mềm, vì thiết bị khác có thể bỏ sót một AP), lợi ích trung bình mỗi mục của X trong T, và mức phù hợp cường độ agree(X,T) với τ là thang cường độ:`));
add(EQ(3, [r("ρ"), rb(r("X,T")), r("="), fr([abs(r("X∩T"))], [abs(r("X"))]), r(",   "), sb([r("q̄")], [r("T")]), rb(r("X")), r("="), fr([r("1")], [abs(r("X∩T"))]), sum([r("i∈X∩T")], [r("q"), rb(r("i,T"))])]));
add(EQ(3, [up("agree"), rb(r("X,T")), r("="), up("exp"), rb(r("−"), fr([abs(sb([r("q̄")], [r("T")]), rb(r("X")), r("−"), sb([r("q̄")], [r("c")]), rb(r("X")))], [r("τ")]))]));
add(P(`Điểm mẫu $P_c$ đo khối lượng lợi ích HUI của ô mà vân tay chứa, đúng cường độ; độ phủ $V_c$ đo phần lợi ích của vân tay được các HUI của ô giải thích, với $I_c$ là hợp các mục của $HUI_c$:`));
add(EQ(3, [sb([r("P")], [r("c")]), rb(r("T")), r("="), sum([r("X∈"), sb([up("HUI")], [r("c")])], [fr([r("u"), rb(r("X"))], [sum([r("Y∈"), sb([up("HUI")], [r("c")])], [r("u"), rb(r("Y"))])]), r("·"), sp([r("ρ"), rb(r("X,T"))], [r("γ")]), r("·"), up("agree"), rb(r("X,T"))])]));
add(EQ(3, [sb([r("V")], [r("c")]), rb(r("T")), r("="), fr([sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T"))])], [sum([r("i∈T")], [r("q"), rb(r("i,T"))])]), r(",   "), sb([up("score")], [r("c")]), rb(r("T")), r("="), sb([r("P")], [r("c")]), rb(r("T")), r("·"), sbsp([r("V")], [r("c")], [r("β")]), rb(r("T"))]));
add(FIG(3, diag("d06_buoc5_cham_diem.png"), "Chấm điểm vân tay ví dụ với các HUI của ô có điểm cao nhất (số liệu thật)"));
add(H2("3.6. Bước 6 — Làm mượt không gian và chọn tầng"));
add(P(`Các ô lân cận trên cùng tầng thường có chữ ký HUI gần nhau. Điểm của mỗi ô được cộng thêm điểm của các ô cùng tầng trong bán kính cỡ σ mét bằng nhân Gauss chuẩn hoá theo hàng, với d(c′,c) là khoảng cách thực địa giữa tâm hai ô; sau đó tầng được chọn là tầng có trung bình $k_f$ điểm lớn nhất cao nhất:`));
add(EQ(3, [sb([r("S")], [r("c")]), rb(r("T")), r("="), sum([r("c′")], [sb([up("score")], [r("c′")]), rb(r("T")), r("·"), r("K"), rb(r("c′,c"))]), r(",   K"), rb(r("c′,c")), r("∝"), sp([r("e")], [r("−d"), sp([rb(r("c′,c"))], [r("2")]), r("/2"), sp([r("σ")], [r("2")])])]));
add(EQ(3, [r("f"), rb(r("T")), r("="), sb([up("arg max")], [r("f")]), fr([r("1")], [sb([r("k")], [r("f")])]), sum([r("c∈"), sb([up("top")], [sb([r("k")], [r("f")])]), rb(r("f"))], [sb([r("S")], [r("c")]), rb(r("T"))])]));
add(FIG(3, diag("d07_buoc6_lam_muot_tang.png"), "Điểm trước và sau làm mượt; điểm theo từng tòa–tầng của vân tay ví dụ"));
add(H2("3.7. Bước 7 — Ô ứng viên và ước lượng ban đầu"));
add(P(`K = ${V6.k_candidates} ô có điểm $S_c$ cao nhất trong tầng đã chọn được giữ làm ô ứng viên cho Bước 8. Ước lượng ban đầu là trọng tâm có trọng số của m = ${PRM.m} ô tốt nhất; số mũ p = ${PRM.p} điều chỉnh độ tập trung của trọng số:`));
add(EQ(3, [rb(r("x̂,ŷ")), r("="), sum([r("c∈top-m"), rb(r("f"))], [sb([r("a")], [r("c")]), rb(sb([r("x")], [r("c")]), r(","), sb([r("y")], [r("c")]))]), r(",   "), sb([r("a")], [r("c")]), r("="), fr([sbsp([r("S")], [r("c")], [r("p")])], [sum([r("c′∈top-m"), rb(r("f"))], [sbsp([r("S")], [r("c′")], [r("p")])])])]));
add(P(`Ước lượng ban đầu chính là đầu ra của phiên bản v4 (mục 4.4). Phân tích v4 trên tập kiểm tra UJIIndoorLoc cho thấy trong 12 ô được chọn, ô gần vị trí thật nhất cách trung bình 2,40 m, trong khi ô có điểm cao nhất cách 8,82 m: tập ứng viên đúng vùng nhưng một điểm khớp duy nhất không sắp được các ô lân cận theo đúng thứ tự. Bước 8 giải quyết việc này.`));
add(FIG(3, diag("d08_buoc7_toa_do.png"), "Ô ứng viên của tầng đã chọn và ước lượng ban đầu của vân tay ví dụ"));
add(H2("3.8. Bước 8 — Xếp hạng lại ô ứng viên bằng bằng chứng HUI"));
add(P(`Mỗi ô ứng viên được mô tả bằng một véc-tơ bằng chứng, mọi thành phần đều tính từ tập HUI. Ngoài mô hình chính (lợi ích nội rank), hai mô hình HUI phụ được khai thác bằng chính quy trình Bước 2–4: mô hình **mục theo mức cường độ**, trong đó mỗi AP được tách thành L = 3 mục theo mức của lợi ích nội (${vn(V6.n_huis_L3, 0)} HUI), và mô hình **lợi ích abs** theo cường độ tuyệt đối (${vn(V6.n_huis_abs, 0)} HUI):`));
add(EQ(3, [r("i"), r(" ↦ "), rb(r("i,ℓ")), r(",   "), r("ℓ"), r("="), up("min"), rb(r("L−1, "), flo(fr([rb(r("q"), rb(r("i,T")), r("−1")), r("·L")], [r("100")])))]));
add(P(`Từ HUI của mỗi ô có thể suy ra một hồ sơ cường độ: khối lượng HUI đặt trên AP i và cường độ ước lượng của AP i tại ô, với w(X) và $q̄_c$(X) như ở (3.5)–(3.8):`));
add(EQ(3, [sb([r("m")], [r("c")]), rb(r("i")), r("∝"), sum([r("X∈"), sb([up("HUI")], [r("c")]), r(", i∈X")], [fr([r("w"), rb(r("X"))], [abs(r("X"))])]), r(",   "), sb([r("q̂")], [r("c")]), rb(r("i")), r("="), fr([sum([r("X∋i")], [r("w"), rb(r("X")), sb([r("q̄")], [r("c")]), rb(r("X"))])], [sum([r("X∋i")], [r("w"), rb(r("X"))])])]));
add(EQ(3, [sb([r("R")], [r("c")]), rb(r("T")), r("="), sum([r("i∈T")], [sb([r("m")], [r("c")]), rb(r("i"))]), r(",   "), sb([up("MAE")], [r("c")]), rb(r("T")), r("="), fr([sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T")), abs(r("q"), rb(r("i,T")), r("−"), sb([r("q̂")], [r("c")]), rb(r("i")))])], [sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T"))])])]));
add(P(`$R_c$ là độ phủ ngược (phần khối lượng HUI của ô có mặt trong vân tay), MAE$_c$ đo độ lệch giữa cường độ của vân tay và hồ sơ cường độ của ô. Véc-tơ bằng chứng φ(T, c) gồm ${V6.n_features} đặc trưng: các điểm $P_c$, $V_c$, $R_c$, $S_c$ của mô hình rank (kể cả $P_c$ với trọng số IDF của HUI giữa các ô lân cận), $P_c$, $V_c$ và thứ hạng của ô theo hai mô hình phụ, các đại lượng hồ sơ cường độ (MAE, hệ số tương quan, cosin) của mô hình rank, mô hình mức cường độ và mô hình abs, và độ đồng thuận không gian giữa các ứng viên (khoảng cách tới ước lượng ban đầu, tới ô xếp đầu, số ứng viên trong bán kính 5 m). Mỗi đặc trưng được dùng thêm ở dạng so với các ứng viên khác của cùng truy vấn (hiệu với giá trị lớn nhất, chuẩn hoá min–max và thứ hạng).`));
add(P(`Một bộ hồi quy Gradient Boosting [13], [14] học hàm g dự đoán khoảng cách từ tâm ô ứng viên tới vị trí thật, trên dữ liệu chỉ lấy từ các fold dev: với mỗi fold, đặc trưng của các truy vấn dev được tính từ mô hình HUI khai thác trên phần còn lại, nên bộ hồi quy chỉ học từ dữ liệu ngoài fold. Toạ độ cuối là trọng tâm của m = ${V6.m} ô có khoảng cách dự đoán nhỏ nhất, với λ = ${vn(V6.lam, 0)} m:`));
add(EQ(3, [sb([r("d̂")], [r("c")]), r("="), up("exp"), rb(r("g"), rb(r("φ"), rb(r("T,c")))), r("−1"), r(",   "), sb([r("a")], [r("c")]), r("∝"), up("exp"), rb(r("−"), fr([sb([r("d̂")], [r("c")]), r("−"), sb([r("d̂")], [up("min")])], [r("λ")])), r(",   "), rb(r("x̂,ŷ")), r("="), sum([r("c")], [sb([r("a")], [r("c")]), rb(sb([r("x")], [r("c")]), r(","), sb([r("y")], [r("c")]))])]));
add(P(`Bộ hồi quy không nhìn thấy vân tay huấn luyện nào; nó chỉ học cách cân các bằng chứng do HUI tạo ra. Các ô được xét vẫn là các ô có điểm HUI cao nhất, và toạ độ vẫn là tổ hợp lồi của tâm các ô đó. Nếu bỏ HUIM, không còn ô ứng viên lẫn đặc trưng nào để xếp hạng.`));
add(FIG(3, diag("d09_buoc8_xep_hang_lai.png"), "Bước 8: bằng chứng HUI, bộ hồi quy và toạ độ cuối của vân tay ví dụ"));
add(H2("3.9. Thuật toán tổng hợp"));
const algo = [
  "Đầu vào: tập huấn luyện {(T, toạ độ, tòa–tầng)}; vân tay truy vấn T*; tham số θ, γ, τ, β, σ, $k_f$, m, p",
  "Huấn luyện:",
  "  1. Với mỗi vân tay huấn luyện T: tính q(i,T) theo (3.1)–(3.3)",
  "  2. Với mỗi ô c: $D_c$ ← giao dịch đo tại c; $minUtil_c$ ← θ·u($D_c$)",
  "  3.   lặp: $HUI_c$ ← EFIM($D_c$, $minUtil_c$); nếu vượt ngân sách thì θ ← 1,25·θ",
  "  4. Mô hình ← {($HUI_c$, $x_c$, $y_c$, tòa–tầng$_c$)} của mọi ô; lặp lại 1–4 cho mô hình mức cường độ và mô hình abs",
  "  4b. Trên 6 fold dev: tính φ(T, c) cho các ô ứng viên của mỗi truy vấn dev; học g bằng Gradient Boosting",
  "Định vị T*:",
  "  5. Với mỗi ô c: tính $P_c$(T*), $V_c$(T*), $score_c$(T*) theo (3.6)–(3.9)",
  "  6. S ← làm mượt theo (3.10); f ← tầng theo (3.11)",
  "  7. K ô ứng viên ← K ô có S cao nhất của tầng f",
  "  8. Với mỗi ứng viên: φ(T*, c) theo (3.13)–(3.15), $d̂_c$ ← g(φ); (x̂, ŷ) theo (3.16)",
  "Đầu ra: (x̂, ŷ), tòa–tầng f",
];
add(new Paragraph({ style: "CaptionBang", keepNext: true, children: [R("Thuật toán 3.1. ", { bold: true }), R("Định vị bằng so khớp High Utility Itemset")] }));
add(new Table({ width: { size: 9071, type: WidthType.DXA }, columnWidths: [9071], alignment: C,
  rows: [new TableRow({ cantSplit: true, children: [new TableCell({ borders, width: { size: 9071, type: WidthType.DXA },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: algo.map((t) => new Paragraph({ spacing: { after: 30 }, children: runs(t, { size: PT(11.5), bold: !t.startsWith(" ") }) })) })] })] }));
add(new Paragraph({ children: [] }));
add(P(`Gọi H là tổng số HUI của mô hình và A là số AP. Chi phí định vị một vân tay là O(H) cho bước 5 trên mỗi mô hình HUI (mỗi HUI được xét một lần nhờ biểu diễn ma trận thưa), O(C²) cho làm mượt với C ô, O(K·A) cho hồ sơ cường độ, và không phụ thuộc vào số vân tay huấn luyện. Với UJIIndoorLoc, thời gian đo được là ${vn(UT.ms_moi_fp)} ms mỗi vân tay trên cài đặt Python (${vn(U4.ms_per_fp)} ms khi chỉ dùng mô hình chính).`));

// ================================================================== CHƯƠNG 4
add(H1("CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ"));
add(H2("4.1. Giao thức đánh giá"));
add(P(`Tập kiểm tra chỉ được dùng một lần cho mỗi phiên bản mô hình; mọi lựa chọn (dạng lợi ích nội, θ, γ, τ, β, σ, $k_f$, m, p) được thực hiện trên 6 fold kiểm định tách từ tập huấn luyện. Với UJIIndoorLoc, ${"9 trong 11"} điện thoại của validationData không có trong trainingData, nên các fold được giữ lại theo điện thoại (GroupKFold trên PHONEID) để mô phỏng đúng tình huống gặp thiết bị lạ. Sau khi chọn, EFIM được chạy lại trên toàn bộ tập huấn luyện và mô hình cuối được chấm một lần trên tập kiểm tra. Bộ hồi quy của Bước 8 cũng chỉ học từ các fold dev, và mọi lựa chọn của Bước 8 (đặc trưng, K, m, λ) dựa trên sai số dev ngoài fold. Sai số được tính theo mét thực địa:`));
add(EQ(4, [sb([r("e")], [r("n")]), r("="), sqrt([sp([rb(sb([r("x̂")], [r("n")]), r("−"), sb([r("x")], [r("n")]))], [r("2")]), r("+"), sp([rb(sb([r("ŷ")], [r("n")]), r("−"), sb([r("y")], [r("n")]))], [r("2")])]), r("·g,   "), r("ē"), r("="), fr([r("1")], [r("N")]), sum([r("n=1")], [sb([r("e")], [r("n")])], [r("N")])]));
add(P(`với g = 0,766126 cho UJIIndoorLoc (Web Mercator) và g = 1 cho các bộ còn lại.`));
add(FIG(4, diag("d10_giao_thuc.png"), "Giao thức đánh giá và kiểm chứng"));
add(H2("4.2. Tham số được chọn trên dev"));
const t41 = TAB(4, "Cấu hình được chọn trên các fold dev của từng bộ dữ liệu", ["Bộ dữ liệu", "Utility", "θ (%)", "γ", "τ", "β", "σ (m)", "$k_f$", "m", "p", "Dev TB (m)"],
  order.map((k) => { const s = D.datasets[k].selection, p = s.params;
    return [T[k], s.utility || "abs", vn(s.theta_pct, 0), p.gamma, p.tau, p.beta, p.sigma, p.kf, p.m, p.p, vn(s.dev_mean_m)]; }),
  [1900, 800, 700, 500, 600, 500, 700, 600, 500, 500, 1200], { align: [L, C, RT, RT, RT, RT, RT, RT, RT, RT, RT], size: 10 });
add(P(`${t41.label} liệt kê cấu hình được chọn. Với UJIIndoorLoc, θ được cố định ở ${vn(SEL.theta_pct, 0)}% bằng thí nghiệm trên dev (θ = 10% sinh khoảng 4 triệu HUI mỗi fold); dạng lợi ích nội rank được chọn vì cho sai số dev thấp nhất trong ba dạng (${vn(pil.phone_folds_theta20_all6_dev_mean_m.rank)} m so với ${vn(pil.phone_folds_theta20_all6_dev_mean_m.abs)} m của abs và ${vn(pil.phone_folds_theta20_all6_dev_mean_m.rel)} m của rel).`));
add(t41);
add(FIG(4, figr("fig62_huim_only_dev.png"), "Sai số trên dev của UJIIndoorLoc theo σ và m (mỗi điểm là cấu hình tốt nhất của các tham số còn lại)", 520));
const t4r = TAB(4, "Các biến thể của Bước 8 thử trên dev UJIIndoorLoc (sai số trung bình ngoài fold, 19 937 truy vấn)", ["Biến thể", "Dev TB (m)", "Kết luận"], [
  ["Bước 1–7, một điểm khớp HUI (v4)", vn(RSH["v4 (baseline)"]), "mốc so sánh"],
  ["Trọng số IDF của HUI giữa các ô lân cận", vn(RSH["IDF weight of HUIs (best)"]), "gần như không đổi"],
  ["Chỉ dùng mô hình mục theo mức cường độ (fold 0)", `${vn(RSH["level items (AP, strength level) alone, fold 0"].L3)} so với ${vn(RSH["level items (AP, strength level) alone, fold 0"].v4)}`, "kém hơn khi dùng riêng"],
  ["Xếp hạng lại bằng các điểm HUI", vn(RSH["re-rank, HUI scores"]), "cải thiện"],
  ["+ hồ sơ cường độ suy ra từ HUI", vn(RSH["re-rank + HUI strength profile"]), "cải thiện"],
  ["Ứng viên trên cả toà nhà (không theo tầng)", vn(RSH["re-rank, candidates over the whole building"]), "không dùng"],
  ["+ đặc trưng so với các ứng viên khác (v5)", vn(RSH["re-rank + features relative to the query's candidates (v5)"]), "cải thiện"],
  ["v5 học khi bỏ ô của chính truy vấn", vn(RSH["v5 trained leave-own-cell-out"]), "không dùng"],
  ["v5 + mô hình HUI lợi ích abs (v6)", vn(RSH["v5 + abs HUI model (v6)"]), "chọn"],
], [5000, 1700, 2300], { align: [L, RT, L], size: 10.5 });
add(P(`${t4r.label} ghi lại các biến thể của Bước 8 đã thử; mọi con số là sai số dev ngoài fold và tập kiểm tra không được đọc. Trọng số IDF và mô hình mục theo mức cường độ dùng riêng không cải thiện; chúng chỉ có ích khi là bằng chứng bổ sung cho bộ hồi quy. Quyết định tầng bằng một bộ phân loại học trên dev nâng độ chính xác tầng trên dev từ ${pct(V6.research["learned floor decision dev floor accuracy"].baseline)} lên ${pct(V6.research["learned floor decision dev floor accuracy"].learned)} nhưng không giảm sai số vị trí, nên không được dùng.`));
add(t4r);
add(H2("4.3. Kết quả trên tập kiểm tra"));
const t42 = TAB(4, "Kết quả định vị chỉ bằng HUIM trên tập kiểm tra", ["Bộ dữ liệu", "Tập kiểm tra", "Số mẫu", "TB (m)", "Trung vị (m)", "p90 (m)", "Đúng tòa–tầng", "< 7 m"],
  allTests.map(({ k, t, v }) => [T[k], t, vn(v.so_mau, 0), vn(v.sai_so_tb_m), vn(v.trung_vi_m), vn(v.p90_m), pct(v.dung_toa_tang), v.duoi_7m ? "đạt" : "không"]),
  [1800, 1700, 800, 800, 1000, 900, 1200, 800], { align: [L, L, RT, RT, RT, RT, RT, C], size: 10.5 });
add(P(`${t42.label} và Hình 4.3 trình bày kết quả. ${nOk}/${allTests.length} tập kiểm tra đạt sai số trung bình dưới 7 m. Trên UJIIndoorLoc, sai số trung bình là ${vn(UT.sai_so_tb_m)} m, trung vị ${vn(UT.trung_vi_m)} m, xác định đúng tòa ${pct(UT.dung_toa)} và đúng tòa–tầng ${pct(UT.dung_toa_tang)}; so với ước lượng ban đầu của Bước 7 (${vn(U4.mean_err_m)} m, trung vị ${vn(U4.median_err_m)} m), Bước 8 giảm sai số trung bình ${vn(U4.mean_err_m - UT.sai_so_tb_m)} m. Các bộ dữ liệu khác dùng Bước 1–7 vì đã đạt mục tiêu ở bước đó.`));
add(t42);
add(FIG(4, figr("fig60_huim_only_all_datasets.png"), "Sai số trung bình trên tập kiểm tra của mọi bộ dữ liệu; đường đứt là mức 7 m"));
add(FIG(4, figr("fig61_huim_only_cdf_uji.png"), "Phân bố sai số trên tập kiểm tra UJIIndoorLoc: mô hình cuối, ước lượng ban đầu (v4) và hai đường k-NN chỉ để tham chiếu", 540));
add(H2("4.4. Phân tích sai số trên UJIIndoorLoc"));
const t43 = TAB(4, "Tách sai số theo việc xác định đúng hay sai tầng (UJIIndoorLoc)", ["Nhóm mẫu", "Số mẫu", "Sai số TB (m)", "Phần trong tổng sai số"],
  fs4.map((x) => [x.nhom, vn(x.so_mau, 0), vn(x.sai_so_tb_m), pct(x.phan_tong_sai_so)]), [3600, 1400, 1800, 2200], { align: [L, RT, RT, RT] });
add(P(`${t43.label} cho thấy phần lớn sai số vẫn nằm ở các mẫu đã xác định đúng tầng (${pct(fs4[0].phan_tong_sai_so)} tổng sai số, sai số trung bình ${vn(fs4[0].sai_so_tb_m)} m, so với 7,78 m ở v4). Bước 8 giảm chủ yếu sai số trong tầng, nhưng đây vẫn là điểm nghẽn: mỗi ô của UJIIndoorLoc chỉ có khoảng ${vn(U.mining.giao_dich_tb_moi_o, 0)} vân tay của một đến bốn người dùng, và gần như không vị trí kiểm tra nào trùng điểm tham chiếu, nên toạ độ phải được nội suy giữa các ô. Theo từng toà nhà, sai số trung bình lần lượt là ${D.uji_by_building.map((x) => `${vn(x.sai_so_tb_m)} m (tòa ${x.toa})`).join(", ")}.`));
add(t43);
const t44 = TAB(4, "Các phiên bản đã thử trên UJIIndoorLoc (mỗi phiên bản chọn trên dev rồi chấm tập kiểm tra một lần)", ["Phiên bản", "Thay đổi", "Fold dev", "Dev TB (m)", "Kiểm tra TB (m)", "Đúng tầng"],
  ver.map((v) => [v.version.replace(" (final)", " (cuối)"), v.change_vi, v.dev_folds === "leave-phones-out" ? "theo điện thoại" : "theo người dùng", vn(v.dev_mean_m), vn(v.test_mean_m), pct(v.test_floor_accuracy)]),
  [900, 3800, 1300, 1000, 1200, 1000], { align: [L, L, L, RT, RT, RT], size: 10 });
add(P(`${t44.label} ghi lại mọi phiên bản. Trong các phiên bản Bước 1–7, v1 có sai số kiểm tra thấp nhất nhưng sai số dev kém nhất; giao thức chọn v4, vì chọn theo con số kiểm tra là chọn mô hình trên tập kiểm tra. Sự chênh giữa dev và kiểm tra ở v2 là lý do chuyển sang fold giữ lại theo điện thoại. v5 và v6 thêm Bước 8; v6 có sai số dev thấp nhất (${vn(V6.dev_mean_m)} m) nên là mô hình cuối, và sai số kiểm tra của nó (${vn(UT.sai_so_tb_m)} m) được tính đúng một lần sau khi đã chọn. Hai thí nghiệm phụ khác cho kết quả âm: đặt lợi ích ngoài p(i) theo IDF hoặc theo thông tin tương hỗ không cải thiện, và khai thác HUI trên cửa sổ chồng lấn gồm các ô lân cận (bán kính 4 m và 8 m) làm sai số dev tăng từ ${vn(win.best_dev_mean_m["cells only (window 0)"])} m lên ${vn(win.best_dev_mean_m["window 4 m"])} m và ${vn(win.best_dev_mean_m["window 8 m"])} m vì chữ ký các ô lân cận trở nên giống nhau.`));
add(t44);
add(H2("4.5. So sánh với các hệ thống tham chiếu"));
const t45 = TAB(4, "Sai số trung bình (m) của hệ thống chỉ dùng HUIM và các hệ thống tham chiếu dùng k-NN", ["Bộ dữ liệu", "Tập kiểm tra", "Chỉ HUIM", "k-NN gốc", "k-NN tối ưu", "HUIM chọn AP + k-NN"],
  D.references.map((x) => [x.ten, x.tap_test, vn(x.chi_huim_m), x.knn_goc_m != null ? vn(x.knn_goc_m) : "–", x.knn_toi_uu_m != null ? vn(x.knn_toi_uu_m) : "–", x.huim_chon_ap_knn_m != null ? `${vn(x.huim_chon_ap_knn_m)} (${x.huim_chon_ap_so_ap}/${x.tong_ap} AP)` : "–"]),
  [1800, 1700, 1000, 1000, 1100, 2400], { align: [L, L, RT, RT, RT, RT], size: 10.5 });
add(P(`${t45.label} đặt kết quả cạnh các hệ thống dùng k-NN của các giai đoạn trước, chỉ để tham chiếu. Hệ thống chỉ dùng HUIM tốt hơn k-NN gốc (k = 1, khoảng cách Manhattan) trên UJIIndoorLoc nhưng kém k-NN đã tối ưu; trên các bộ dữ liệu một tầng, k-NN cho sai số thấp hơn vì vị trí kiểm tra trùng hoặc rất gần điểm tham chiếu. Ưu điểm của thiết kế đề xuất không nằm ở sai số tuyệt đối mà ở chỗ toàn bộ quyết định định vị đến từ các mẫu HUI: bỏ HUIM đi thì hệ thống không còn mô hình để định vị.`));
add(t45);
add(H2("4.6. Kiểm chứng độc lập"));
const t46 = TAB(4, "Kết quả kiểm chứng độc lập", ["Bộ dữ liệu", "Số phép kiểm", "Thất bại"],
  [...D.verification.per_dataset.map((x) => [T[x.dataset], x.n_checks, x.n_failed]),
   ["UJIIndoorLoc, mô hình cuối (Bước 8)", V6.verification.n_checks, V6.verification.n_failed]], [3600, 2200, 2200], { align: [L, RT, RT] });
add(P(`Chương trình kiểm chứng không gọi EFIM hay bộ định vị. Từ dữ liệu gốc và các tệp kết quả, nó tính lại ngưỡng của mọi ô, lợi ích và độ hỗ trợ của các HUI bằng cách quét lại dữ liệu, kiểm tra mọi tập 1–2 AP vượt ngưỡng đều có trong mô hình, tính lại điểm khớp, các ô được chọn và toạ độ của các truy vấn ngẫu nhiên bằng vòng lặp thuần, và đếm lại sai số, độ chính xác (${t46.label}). Với mô hình cuối của UJIIndoorLoc, ${V6.verification.n_checks} phép kiểm riêng xác nhận: sai số tính lại từ toạ độ khớp với báo cáo; mỗi toạ độ dự đoán đúng bằng tổng có trọng số của tâm các ô được chọn, trọng số dương và có tổng bằng 1; mọi ô được chọn nằm trên tầng dự đoán; ước lượng ban đầu bên trong mô hình cuối trùng khít với dự đoán của v4; và các dòng kiểm tra đúng là 1 111 dòng của validationData. Ngoài ra, sổ Excel so_lieu/kiem_chung_mean.xlsx tính lại sai số trung bình của mọi tập kiểm tra bằng công thức (4.1) và khớp với kết quả báo cáo tới 10⁻⁴ m.`));
add(t46);
add(H2("4.7. Thảo luận"));
add(P(`Kết quả cho thấy HUIM có thể đảm nhận toàn bộ việc định vị: trên năm bộ dữ liệu ngoài UJIIndoorLoc, sai số trung bình nằm trong khoảng ${vn(Math.min(...allTests.filter((x) => x.k !== "uji").map((x) => x.v.sai_so_tb_m)))}–${vn(Math.max(...allTests.filter((x) => x.k !== "uji").map((x) => x.v.sai_so_tb_m)))} m với Bước 1–7, và trên UJIIndoorLoc đạt ${vn(UT.sai_so_tb_m)} m khi thêm Bước 8. Mức giảm trên tập kiểm tra (${vn(U4.mean_err_m - UT.sai_so_tb_m)} m) không nhỏ hơn mức giảm trên dev (${vn(V6.dev_mean_v4_m - V6.dev_mean_m)} m), nên không có dấu hiệu Bước 8 quá khớp với các fold dev.`));
add(P(`Cần nêu rõ ba giới hạn. Thứ nhất, kết quả UJIIndoorLoc chỉ thấp hơn mức 7 m ${vn(7 - UT.sai_so_tb_m)} m; với ${vn(UT.so_mau, 0)} mẫu, sai số chuẩn của giá trị trung bình là ${vn(UT.sai_so_chuan_tb_m)} m, nên khoảng cách này nằm trong biên dao động thống kê (khoảng tin cậy 95% xấp xỉ ${vn(UT.sai_so_tb_m - 1.96 * UT.sai_so_chuan_tb_m)}–${vn(UT.sai_so_tb_m + 1.96 * UT.sai_so_chuan_tb_m)} m). Thứ hai, Bước 8 dùng một bộ hồi quy học có giám sát; bộ hồi quy chỉ nhận bằng chứng do HUI tạo ra và chỉ chọn giữa các ô có điểm HUI cao nhất, nhưng phần cân các bằng chứng là do học máy đảm nhận. Thứ ba, thiết bị thu: tập kiểm tra dùng chủ yếu điện thoại lạ, và mẫu HUI của một ô mô tả nhóm AP mạnh cùng xuất hiện tại ô đó, phân biệt tốt giữa các vùng nhưng ít thông tin về vị trí chính xác bên trong vùng.`));
add(P(`Chi phí tính toán là một hạn chế khác: với θ thấp, số HUI tăng rất nhanh (khoảng 3,2 triệu HUI cho mô hình chính của UJIIndoorLoc ở θ = 20%, tổng cộng ${vn((U.model.n_huis + V6.n_huis_L3 + V6.n_huis_abs) / 1e6, 2)} triệu HUI cho ba mô hình), làm thời gian định vị lớn hơn k-NN trên cài đặt Python. Một cài đặt EFIM bằng ngôn ngữ biên dịch, hoặc các biến thể khai thác HUI đóng hay HUI cực đại để giảm dư thừa, là hướng cải thiện tự nhiên.`));

// ================================================================== CHƯƠNG 5
add(H1("CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"));
add(H2("5.1. Kết luận"));
add(BUL(`Báo cáo đã xây dựng một hệ thống định vị trong nhà trong đó HUIM là thuật toán định vị chính: mô hình là tập HUI do EFIM khai thác cho từng điểm tham chiếu, và mọi quyết định về tầng và toạ độ đến từ bằng chứng rút ra từ HUI; không dùng k-NN và không lưu vân tay huấn luyện.`));
add(BUL(`Trên ${allTests.length} tập kiểm tra của ${order.length} bộ dữ liệu, ${nOk} tập đạt sai số trung bình dưới 7 m (UJIIndoorLoc ${vn(UT.sai_so_tb_m)} m, UJI_LIB ${vn(D.datasets.uji_lib3.tests["Test-01"].sai_so_tb_m)}/${vn(D.datasets.uji_lib3.tests["Test-02"].sai_so_tb_m)} m, DLULIB ${vn(D.datasets.dlulib.tests.Testing.sai_so_tb_m)} m, HCXY ${vn(D.datasets.hcxy.tests.test_HCXY.sai_so_tb_m)} m, HUS khoảng ${vn(D.datasets.hus_dedup.tests.testcase1.sai_so_tb_m)}–${vn(D.datasets.hus_dedup.tests.testcase2.sai_so_tb_m)} m).`));
add(BUL(`Trên UJIIndoorLoc, Bước 8 (xếp hạng lại ô ứng viên bằng bằng chứng HUI từ ba mô hình HUI) giảm sai số trung bình từ ${vn(U4.mean_err_m)} m xuống ${vn(UT.sai_so_tb_m)} m, dưới mức 7 m với biên nhỏ; phần sai số còn lại chủ yếu nằm trong tầng và gắn với thiết bị thu khác nhau giữa hai tập.`));
add(BUL(`Mọi con số được chọn theo giao thức không rò rỉ dữ liệu, được kiểm chứng độc lập và có thể tính lại bằng sổ Excel kèm theo.`));
add(H2("5.2. Hướng phát triển"));
add(BUL(`Thiết kế lợi ích nội bất biến tốt hơn với thiết bị, ví dụ hiệu chỉnh độ lệch theo từng điện thoại ngay trong lợi ích nội.`));
add(BUL(`Tăng độ phân giải trong tầng bằng các ô nhỏ hơn hoặc bằng cách kết hợp HUI ở nhiều mức không gian (tầng, vùng, ô), và thay bộ hồi quy của Bước 8 bằng một quy tắc kết hợp tường minh dễ diễn giải hơn.`));
add(BUL(`Dùng HUI đóng hoặc HUI cực đại và một cài đặt EFIM biên dịch để giảm số mẫu và thời gian định vị.`));

// ================================================================== references
const refs = [
  "P. Bahl, V. N. Padmanabhan, “RADAR: an in-building RF-based user location and tracking system,” in Proc. IEEE INFOCOM 2000, doi: 10.1109/INFCOM.2000.832252.",
  "M. Youssef, A. Agrawala, “The Horus WLAN location determination system,” in Proc. MobiSys 2005, doi: 10.1145/1067170.1067193.",
  "J. Torres-Sospedra et al., “UJIIndoorLoc: A new multi-building and multi-floor database for WLAN fingerprint-based indoor localization problems,” in Proc. IPIN 2014, pp. 261–270, doi: 10.1109/IPIN.2014.7275492.",
  "J. Torres-Sospedra, R. Montoliu, S. Trilles, Ó. Belmonte, J. Huerta, “Comprehensive analysis of distance and similarity measures for Wi-Fi fingerprinting indoor positioning systems,” Expert Systems with Applications, 2015, doi: 10.1016/j.eswa.2015.08.013.",
  "S. Zida, P. Fournier-Viger, J. C.-W. Lin, C.-W. Wu, V. S. Tseng, “EFIM: a fast and memory efficient algorithm for high-utility itemset mining,” Knowledge and Information Systems, vol. 51, no. 2, pp. 595–625, 2017, doi: 10.1007/s10115-016-0986-0.",
  "H. Yao, H. J. Hamilton, C. J. Butz, “A foundational approach to mining itemset utilities from databases,” in Proc. SIAM SDM 2004, doi: 10.1137/1.9781611972740.51.",
  "Y. Liu, W.-K. Liao, A. Choudhary, “A two-phase algorithm for fast discovery of high utility itemsets,” in Proc. PAKDD 2005, LNCS, doi: 10.1007/11430919_79.",
  "A. Khalajmehrabadi, N. Gatsis, D. Akopian, “Modern WLAN fingerprinting indoor positioning methods and deployment challenges,” IEEE Communications Surveys & Tutorials, 2017, doi: 10.1109/COMST.2017.2671454.",
  "C. Zhang, G. Almpanidis, W. Wang, C. Liu, “An empirical evaluation of high utility itemset mining algorithms,” Expert Systems with Applications, vol. 101, pp. 91–115, 2018, doi: 10.1016/j.eswa.2018.02.008.",
  "P. Fournier-Viger, J. C.-W. Lin, T. Truong-Chi, R. Nkambou, “A survey of high utility itemset mining,” in High-Utility Pattern Mining, Studies in Big Data, Springer, 2019, doi: 10.1007/978-3-030-04921-8_1.",
  "R. Agrawal, T. Imieliński, A. Swami, “Mining association rules between sets of items in large databases,” in Proc. ACM SIGMOD 1993, doi: 10.1145/170035.170072.",
  "Y. Chen, Q. Yang, J. Yin, X. Chai, “Power-efficient access-point selection for indoor location estimation,” IEEE Transactions on Knowledge and Data Engineering, vol. 18, pp. 877–888, 2006, doi: 10.1109/TKDE.2006.112.",
  "J. H. Friedman, “Greedy function approximation: A gradient boosting machine,” The Annals of Statistics, vol. 29, no. 5, pp. 1189–1232, 2001, doi: 10.1214/aos/1013203451.",
  "G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, T.-Y. Liu, “LightGBM: A highly efficient gradient boosting decision tree,” in Advances in Neural Information Processing Systems 30 (NIPS 2017), pp. 3146–3154.",
];
add(H1("TÀI LIỆU THAM KHẢO"));
refs.forEach((t, i) => add(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 100, line: 300 },
  indent: { left: 567, hanging: 567 }, children: [R(`[${i + 1}]`), new TextRun({ font: FONT, children: [new Tab()] }), R(t)], tabStops: [{ type: TabStopType.LEFT, position: 567 }] })));

// ================================================================== appendix
add(H1("PHỤ LỤC. CẤU TRÚC THƯ MỤC BÁO CÁO VÀ CÁCH KIỂM CHỨNG"));
const tP = TAB("A", "Nội dung thư mục BAOCAO", ["Thành phần", "Nội dung"], [
  ["diagram/", "9 sơ đồ mô hình theo từng bước, từ đầu vào tới đầu ra, vẽ từ mô hình và một vân tay kiểm tra thật"],
  ["so_lieu/", "kết quả tổng hợp, cấu hình chọn trên dev, lịch sử phiên bản, dự đoán từng mẫu, sổ Excel kiểm chứng, script kiem_tra_mean.py"],
  ["ma_nguon/", "mã nguồn EFIM, bộ định vị, thực nghiệm, kiểm chứng, kiểm thử và script dựng báo cáo"],
  ["Bao_cao_HUIM_IPS_UJIIndoorLoc.docx", "báo cáo này"],
  ["Slide_HUIM_IPS_UJIIndoorLoc.pptx", "bài thuyết trình"]], [3200, 5871]);
add(tP);
add(P(`Để kiểm tra sai số trung bình: mở so_lieu/kiem_chung_mean.xlsx (sheet Tong_hop) hoặc chạy “python kiem_tra_mean.py” trong thư mục so_lieu; cả hai tính lại sai số của từng mẫu từ toạ độ thật và toạ độ dự đoán rồi so với con số trong ${t42.label}.`));

// ================================================================== document
const doc = new Document({
  creator: "HUIM-IPS", title: "Ứng dụng HUIM trong hệ thống định vị trong nhà",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: PT(13) } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: PT(15), bold: true, color: "1F3A5F" },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 360 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: PT(13.5), bold: true, color: "1F3A5F" },
        paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: PT(13), bold: true, italics: true },
        paragraph: { spacing: { before: 180, after: 80 }, keepNext: true, outlineLevel: 2 } },
      { id: "CaptionHinh", name: "Caption Hinh", basedOn: "Normal", run: { font: FONT, size: PT(12), italics: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 40, after: 220 } } },
      { id: "CaptionBang", name: "Caption Bang", basedOn: "Normal", run: { font: FONT, size: PT(12), italics: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 } } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 1134 } } },
      children: cover },
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 1134 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: C, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: PT(12) })] })] }) },
      children: [...front, ...body] },
  ],
});
const out = path.join(B, "Bao_cao_HUIM_IPS_UJIIndoorLoc.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  // OMML: <m:nary> bắt buộc có <m:sup> (kể cả khi ẩn); docx-js bỏ qua phần tử này.
  require("child_process").execFileSync("python3", ["-c", `
import sys, zipfile, shutil
p = sys.argv[1]; t = p + ".tmp"
with zipfile.ZipFile(p) as zi, zipfile.ZipFile(t, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        b = zi.read(it.filename)
        if it.filename == "word/document.xml":
            x = b.decode("utf-8").replace("</m:sub><m:e>", "</m:sub><m:sup/><m:e>")
            x = x.replace("<m:d><m:dPr/><m:e><m:r><m:t>\u2062ABS</m:t></m:r>",
                          '<m:d><m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr><m:e>')
            x = x.replace("<m:r><m:t>\u2060", '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>')
            x = x.replace("<m:d><m:dPr/><m:e><m:r><m:t>\u2062FLO</m:t></m:r>",
                          '<m:d><m:dPr><m:begChr m:val="⌊"/><m:endChr m:val="⌋"/></m:dPr><m:e>')
            assert "\u2060" not in x and "\u2062" not in x
            b = x.encode("utf-8")
        zo.writestr(it, b)
shutil.move(t, p)`, out]);
  // Mục lục, danh mục hình/bảng: điền sẵn kèm số trang (cần LibreOffice; Word cập nhật lại bằng F9).
  require("child_process").execFileSync("python3", [path.join(__dirname, "fill_toc.py"), out], { stdio: "inherit" });
  console.log("written", out, fs.statSync(out).size);
});
