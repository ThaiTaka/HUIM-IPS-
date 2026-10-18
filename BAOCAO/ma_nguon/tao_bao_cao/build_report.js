// BAOCAO/Bao_cao_HUIM_IPS_UJIIndoorLoc.docx — báo cáo theo thể thức luận văn thạc sĩ.
// Mọi con số đọc từ BAOCAO/so_lieu (du_lieu_bao_cao.json, bieu_do/*.csv) và results/;
// mọi sơ đồ và biểu đồ lấy từ BAOCAO/diagram. Công thức là phương trình Word (OMML).
// Chạy: node src/baocao/build_report.js   (cần npm "docx"; LibreOffice để điền mục lục)
const fs = require("fs");
const path = require("path");
const L_ = require("./report_lib");
const { vn, pct, R, runs, P, PN, H1, H2, H3, BUL, NUMS, GAP, r, fr, sb, sp, sbsp, sum, sqrt, rb, sq, cb, up, abs, flo,
  EQ, FIG, TAB, ALGO, BOX, build, C, RT, L, J, PT, TableOfContents, Paragraph, TextRun, Tab, TabStopType, d } = L_;

const ROOT = path.resolve(__dirname, "..", "..");
const B = path.join(ROOT, "BAOCAO");
const D = JSON.parse(fs.readFileSync(path.join(B, "so_lieu", "du_lieu_bao_cao.json"), "utf8"));
const csv = (n) => {                         // CSV đơn giản (không có dấu phẩy trong ô)
  const [h, ...rows] = fs.readFileSync(path.join(B, "so_lieu", "bieu_do", n), "utf8").trim().split(/\r?\n/);
  const k = h.split(",");
  return rows.map((l) => Object.fromEntries(l.split(",").map((v, i) => [k[i], isNaN(+v) ? v : +v])));
};
const dg = (n) => path.join(B, "diagram", n);
const impF = path.join(ROOT, "results", "huim_only", "uji", "research", "importance.json");
const IMP = fs.existsSync(impF) ? JSON.parse(fs.readFileSync(impF, "utf8")) : null;

// ------------------------------------------------------------------ dữ liệu
const order = D.order, T = D.title;
const U = D.datasets.uji, UT = U.tests.validationData, SEL = U.selection, PRM = SEL.params;
const V6 = U.v6, U4 = U.v4_tests.validationData, RSH = V6.research.dev_mean_m;
const allTests = [];
order.forEach((k) => Object.entries(D.datasets[k].tests).forEach(([t, v]) => allTests.push({ k, t, v })));
const nOk = allTests.filter((x) => x.v.duoi_7m).length;
const others = allTests.filter((x) => x.k !== "uji");
const ref = (k, t) => D.references.find((x) => x.dataset === k && x.tap_test === t);
const refU = ref("uji", "validationData");
const fs4 = D.uji_floor_split;
const pil = D.pilots["theta_pilot.json"], win = D.pilots["window_pilot.json"];
const EX = D.worked_example, GF = 0.766126;
const nHUI3 = U.model.n_huis + V6.n_huis_L3 + V6.n_huis_abs;
const phones = csv("b14_dien_thoai.csv");
const floors = csv("b04_sai_so_theo_toa_tang.csv");

// ------------------------------------------------------------------ nội dung
const body = [];
const add = (...xs) => xs.forEach((x) => (Array.isArray(x) ? body.push(...x) : x.ps ? body.push(...x.ps) : x.p ? body.push(x.p) : body.push(x)));
const fig = (chap, f, cap, w) => FIG(chap, dg(f), cap, w);

// ================================================================== BÌA
const blank = (n) => Array.from({ length: n }, () => new Paragraph({ children: [] }));
const center = (t, o = {}, sp_ = {}) => new Paragraph({ alignment: C, spacing: { after: 60, ...sp_ }, children: [R(t, o)] });
const cover = [
  center("BỘ GIÁO DỤC VÀ ĐÀO TẠO", { bold: true, size: PT(13) }),
  center("TRƯỜNG ĐẠI HỌC …………………………………", { bold: true, size: PT(13) }, { after: 600 }),
  center("…………………………………", { bold: true, size: PT(14) }, { after: 100 }),
  center("(Họ và tên học viên)", { italics: true, size: PT(12) }, { after: 1500 }),
  center("ỨNG DỤNG THUẬT TOÁN KHAI THÁC", { bold: true, size: PT(18) }, { after: 120 }),
  center("TẬP MỤC LỢI ÍCH CAO (HUIM)", { bold: true, size: PT(18) }, { after: 120 }),
  center("TRONG HỆ THỐNG ĐỊNH VỊ TRONG NHÀ", { bold: true, size: PT(18) }, { after: 1500 }),
  center("LUẬN VĂN THẠC SĨ KHOA HỌC MÁY TÍNH", { bold: true, size: PT(15) }, { after: 3200 }),
  center("…………, NĂM 2026", { bold: true, size: PT(13) }),
];
const titlePage = [
  center("BỘ GIÁO DỤC VÀ ĐÀO TẠO", { bold: true, size: PT(13) }),
  center("TRƯỜNG ĐẠI HỌC …………………………………", { bold: true, size: PT(13) }, { after: 600 }),
  center("…………………………………", { bold: true, size: PT(14) }, { after: 100 }),
  center("(Họ và tên học viên)", { italics: true, size: PT(12) }, { after: 1300 }),
  center("ỨNG DỤNG THUẬT TOÁN KHAI THÁC", { bold: true, size: PT(17) }, { after: 120 }),
  center("TẬP MỤC LỢI ÍCH CAO (HUIM)", { bold: true, size: PT(17) }, { after: 120 }),
  center("TRONG HỆ THỐNG ĐỊNH VỊ TRONG NHÀ", { bold: true, size: PT(17) }, { after: 900 }),
  center("Chuyên ngành: Khoa học máy tính", { size: PT(13) }),
  center("Mã số: …………………", { size: PT(13) }, { after: 700 }),
  center("LUẬN VĂN THẠC SĨ KHOA HỌC MÁY TÍNH", { bold: true, size: PT(15) }, { after: 900 }),
  center("NGƯỜI HƯỚNG DẪN KHOA HỌC:", { bold: true, size: PT(13) }),
  center("…………………………………………", { size: PT(13) }, { after: 2300 }),
  center("…………, NĂM 2026", { bold: true, size: PT(13) }),
];

// ================================================================== PHẦN ĐẦU
const front = [];
const fadd = (...xs) => xs.forEach((x) => (Array.isArray(x) ? front.push(...x) : x.ps ? front.push(...x.ps) : front.push(x)));
fadd(new Paragraph({ heading: d.HeadingLevel.HEADING_1, children: [R("LỜI CAM ĐOAN")] }));
fadd(P(`Tôi xin cam đoan luận văn “Ứng dụng thuật toán khai thác tập mục lợi ích cao (HUIM) trong hệ thống định vị trong nhà” là công trình nghiên cứu của bản thân, được thực hiện dưới sự hướng dẫn khoa học của người hướng dẫn. Các số liệu và kết quả trình bày trong luận văn được tạo ra từ mã nguồn và dữ liệu đi kèm, có thể tính lại và kiểm chứng độc lập; các nội dung tham khảo đều được trích dẫn nguồn đầy đủ.`));
fadd(P(`Tôi xin chịu hoàn toàn trách nhiệm về tính trung thực của các kết quả trong luận văn.`));
fadd(new Paragraph({ alignment: RT, spacing: { before: 600, after: 60 }, children: [R("…………, ngày …… tháng …… năm 2026", { italics: true })] }));
fadd(new Paragraph({ alignment: RT, spacing: { after: 1200 }, children: [R("Học viên thực hiện", { bold: true })] }));
fadd(new Paragraph({ alignment: RT, children: [R("…………………………………")] }));

fadd(H1("LỜI CẢM ƠN"));
fadd(P(`Trước hết, tôi xin bày tỏ lòng biết ơn sâu sắc tới người hướng dẫn khoa học đã định hướng đề tài, góp ý về phương pháp và yêu cầu khắt khe về tính trung thực của số liệu trong suốt quá trình thực hiện luận văn.`));
fadd(P(`Tôi xin cảm ơn quý thầy cô của chương trình đào tạo thạc sĩ Khoa học máy tính đã truyền đạt kiến thức nền tảng về khai phá dữ liệu, học máy và các hệ thống định vị. Tôi cũng xin cảm ơn nhóm tác giả bộ dữ liệu UJIIndoorLoc và các bộ dữ liệu vân tay Wi-Fi đã công bố dữ liệu, giúp các kết quả của luận văn có thể được đối chiếu.`));
fadd(P(`Cuối cùng, tôi xin cảm ơn gia đình và bạn bè đã luôn động viên trong thời gian học tập và nghiên cứu.`));

fadd(H1("TÓM TẮT"));
fadd(P(`Luận văn nghiên cứu việc dùng thuật toán khai thác tập mục lợi ích cao (High Utility Itemset Mining, HUIM) làm **thuật toán định vị chính** của một hệ thống định vị trong nhà dựa trên vân tay Wi-Fi. Ở các nghiên cứu trước của đề tài, HUIM chỉ chọn tập điểm truy cập (AP) cho bộ phân loại k-láng giềng gần nhất (k-NN); phân tích cho thấy khi đó HUIM chỉ đóng góp khoảng 6% mức giảm sai số và có thể bị thay thế. Luận văn đề xuất một mô hình trong đó mỗi điểm tham chiếu của tập huấn luyện được coi là một cơ sở dữ liệu giao dịch, thuật toán EFIM khai thác tập High Utility Itemset (HUI) của từng điểm, và tập HUI này chính là mô hình định vị. Vân tay cần định vị được so khớp với HUI của mọi ô để chọn tòa nhà, tầng và các ô ứng viên; các ô ứng viên sau đó được xếp hạng lại bằng bằng chứng rút ra từ ba mô hình HUI và hồ sơ cường độ suy ra từ HUI, kết hợp bởi một bộ hồi quy Gradient Boosting học trên các fold kiểm định. Mô hình không lưu và không so sánh vân tay huấn luyện, và không dùng k-NN.`));
fadd(P(`Mọi tham số được chọn trên các fold kiểm định tách từ tập huấn luyện; mỗi tập kiểm tra chỉ được chấm một lần. Trên ${allTests.length} tập kiểm tra của ${order.length} bộ dữ liệu, cả ${nOk} tập đạt sai số trung bình dưới 7 m. Trên UJIIndoorLoc (${vn(UT.so_mau, 0)} vân tay kiểm tra, 9/11 điện thoại không có trong tập huấn luyện), sai số trung bình là **${vn(UT.sai_so_tb_m)} m**, trung vị ${vn(UT.trung_vi_m)} m, đúng tòa nhà ${pct(UT.dung_toa)} và đúng tòa–tầng ${pct(UT.dung_toa_tang)}; phiên bản chỉ dùng một điểm khớp HUI đạt ${vn(U4.mean_err_m)} m. Mọi con số được kiểm chứng độc lập (${D.verification.n_checks} phép kiểm, ${D.verification.n_failed} thất bại) và có thể tính lại bằng sổ Excel kèm theo.`));
fadd(PN(`**Từ khoá:** khai thác tập mục lợi ích cao, EFIM, định vị trong nhà, vân tay Wi-Fi, UJIIndoorLoc, Gradient Boosting.`));

fadd(H1("ABSTRACT"));
fadd(P(`This thesis studies High Utility Itemset Mining (HUIM) as the **primary positioning algorithm** of a Wi-Fi fingerprint indoor positioning system, rather than as an access-point selection step in front of a k-nearest-neighbour (k-NN) classifier. Every reference point of the training data is treated as a transaction database; the EFIM algorithm mines the High Utility Itemsets (HUIs) of each point, and these HUI sets form the positioning model. A query fingerprint is matched against the HUIs of every cell to decide the building, the floor and a set of candidate cells; the candidates are then re-ranked with evidence derived from three HUI models and from cell strength profiles computed from the HUIs, combined by a gradient boosting regressor trained on validation folds only. No training fingerprint is stored or compared and no k-NN is used.`));
fadd(P(`All parameters are selected on validation folds split from the training data, and each test set is scored once. All ${allTests.length} test sets of the ${order.length} datasets reach a mean error below 7 m. On UJIIndoorLoc (${vn(UT.so_mau, 0)} test fingerprints, 9 of 11 phones unseen in training) the mean error is **${UT.sai_so_tb_m.toFixed(2)} m** (median ${UT.trung_vi_m.toFixed(2)} m, building accuracy ${(100 * UT.dung_toa).toFixed(1)}%, building-floor accuracy ${(100 * UT.dung_toa_tang).toFixed(1)}%), compared with ${U4.mean_err_m.toFixed(2)} m for the single HUI-score version. Every number is verified independently (${D.verification.n_checks} checks, ${D.verification.n_failed} failed).`));
fadd(PN(`**Keywords:** high utility itemset mining, EFIM, indoor positioning, Wi-Fi fingerprinting, UJIIndoorLoc, gradient boosting.`));

fadd(H1("MỤC LỤC"));
fadd(new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }));
const abbr = [
  ["AP", "Access Point — điểm truy cập Wi-Fi"], ["RSSI", "Received Signal Strength Indicator — cường độ tín hiệu thu (dBm)"],
  ["IPS", "Indoor Positioning System — hệ thống định vị trong nhà"], ["HUIM", "High Utility Itemset Mining — khai thác tập mục lợi ích cao"],
  ["HUI", "High Utility Itemset — tập mục có lợi ích không nhỏ hơn ngưỡng minUtil"], ["EFIM", "EFficient high-utility Itemset Mining (Zida và cộng sự, 2017)"],
  ["TU, TWU", "Transaction Utility, Transaction-Weighted Utility — lợi ích giao dịch, lợi ích có trọng số giao dịch"],
  ["k-NN, WKNN", "k-Nearest Neighbours, Weighted k-NN — k láng giềng gần nhất (có trọng số)"],
  ["GBM", "Gradient Boosting Machine — mô hình hồi quy cây tăng cường theo gradient"],
  ["Ô (cell)", "một điểm tham chiếu của tập huấn luyện, đơn vị vị trí của mô hình"],
  ["Ô ứng viên", "một trong K ô có điểm HUI cao nhất của tầng đã chọn, được xếp hạng lại ở Bước 8"],
  ["dev", "fold kiểm định tách từ tập huấn luyện, chỉ dùng để chọn tham số và huấn luyện bộ hồi quy"],
  ["θ", "ngưỡng lợi ích tối thiểu tương đối (% lợi ích của cơ sở dữ liệu giao dịch của ô)"],
  ["q(i,T), p(i)", "lợi ích nội của AP i trong vân tay T; lợi ích ngoài của AP i"],
  ["$P_c$, $V_c$, $R_c$", "điểm khớp mẫu HUI, độ phủ truy vấn, độ phủ ngược của ô c"],
  ["$q̂_c$(i)", "cường độ ước lượng của AP i tại ô c, suy ra từ các HUI của ô"],
  ["g", "hệ số đổi toạ độ Web Mercator ra mét thực địa (UJIIndoorLoc: 0,766126)"],
];
fadd(H1("DANH MỤC KÝ HIỆU VÀ CHỮ VIẾT TẮT"));
const tA = TAB("0", "", ["Ký hiệu", "Ý nghĩa"], abbr, [2000, 7071]);
fadd(...tA.ps.slice(1));
fadd(H1("DANH MỤC BẢNG"));
fadd(new TableOfContents("Danh mục bảng", { hyperlink: true, stylesWithLevels: [new d.StyleLevel("CaptionBang", 1)] }));
fadd(H1("DANH MỤC HÌNH"));
fadd(new TableOfContents("Danh mục hình", { hyperlink: true, stylesWithLevels: [new d.StyleLevel("CaptionHinh", 1)] }));

// ================================================================== MỞ ĐẦU
add(new Paragraph({ heading: d.HeadingLevel.HEADING_1, children: [R("MỞ ĐẦU")] }));
add(H2("1. Lý do chọn đề tài"));
add(P(`Con người dành phần lớn thời gian ở trong các toà nhà, nơi tín hiệu vệ tinh định vị toàn cầu bị suy giảm mạnh, trong khi nhu cầu xác định vị trí trong nhà ngày càng lớn: dẫn đường trong bệnh viện, sân bay, trường đại học; quản lý tài sản; hỗ trợ cứu hộ. Định vị bằng vân tay Wi-Fi là hướng tiếp cận phổ biến vì tận dụng hạ tầng điểm truy cập sẵn có và chỉ cần điện thoại thông thường [15], [16].`));
add(P(`Khai thác tập mục lợi ích cao (HUIM) là một bài toán khai phá dữ liệu mở rộng khai thác tập phổ biến: mỗi mục trong giao dịch mang một lợi ích định lượng, và cần tìm mọi tập mục có tổng lợi ích lớn [6], [10]. Một vân tay Wi-Fi có cấu trúc rất gần với một giao dịch có lợi ích: tập các AP được phát hiện, mỗi AP kèm cường độ tín hiệu. Điều đó gợi ý rằng các tập AP mạnh cùng xuất hiện tại một vị trí, tức các HUI, có thể mô tả vị trí đó.`));
add(P(`Ở các giai đoạn trước của đề tài, HUIM được dùng để chọn tập AP, còn việc định vị do k-NN đảm nhận. Kết quả cho thấy HUIM chỉ đóng góp khoảng 6% mức giảm sai số và có thể được thay bằng một tiêu chí xếp hạng AP đơn giản; nói cách khác, bỏ HUIM đi hệ thống vẫn định vị được. Với một đề tài mang tên “Ứng dụng HUIM vào hệ thống định vị trong nhà”, vai trò như vậy là chưa đủ. Luận văn vì vậy đặt mục tiêu xây dựng một hệ thống trong đó **HUIM là thuật toán định vị chính**, không dùng k-NN, và vẫn đạt sai số trung bình dưới 7 m.`));
add(H2("2. Mục tiêu nghiên cứu"));
add(...NUMS([
  `Mô hình hoá dữ liệu vân tay Wi-Fi thành các cơ sở dữ liệu giao dịch có lợi ích phù hợp với định nghĩa của bài toán HUIM.`,
  `Đề xuất mô hình định vị mà mô hình là tập HUI của các điểm tham chiếu; mọi quyết định về tòa nhà, tầng và toạ độ đều dựa trên bằng chứng rút ra từ HUI.`,
  `Đạt sai số định vị trung bình dưới 7 m trên tập kiểm tra của UJIIndoorLoc và các bộ dữ liệu bổ sung, với giao thức đánh giá không rò rỉ dữ liệu.`,
  `Kiểm chứng độc lập mọi con số và cung cấp mã nguồn, số liệu để có thể tái lập.`]));
add(H2("3. Đối tượng và phạm vi nghiên cứu"));
add(P(`**Đối tượng:** thuật toán khai thác tập mục lợi ích cao EFIM [5], dữ liệu vân tay Wi-Fi dạng RSSI và bài toán ước lượng toạ độ hai chiều, tòa nhà, tầng của một vân tay.`));
add(P(`**Phạm vi:** sáu bộ dữ liệu công khai hoặc được cung cấp sẵn: UJIIndoorLoc [3] (ba toà nhà, 13 tòa–tầng), UJI_LIB tầng 3, DLULIB, HCXY, HUS và HUS sau khi khử trùng lặp. Luận văn chỉ xét định vị tĩnh từ một lần quét; không xét theo dõi quỹ đạo, cảm biến quán tính hay các công nghệ khác ngoài Wi-Fi RSSI.`));
add(H2("4. Phương pháp nghiên cứu"));
add(BUL(`**Nghiên cứu lý thuyết:** tổng hợp các phương pháp định vị vân tay và các thuật toán HUIM, phân tích tính chất của lợi ích và các chặn trên dùng để cắt tỉa.`));
add(BUL(`**Thực nghiệm có kiểm soát:** mọi lựa chọn mô hình dựa trên các fold kiểm định tách từ tập huấn luyện (với UJIIndoorLoc, fold được giữ lại theo điện thoại để mô phỏng thiết bị lạ); tập kiểm tra chỉ dùng một lần cho mỗi phiên bản và mọi phiên bản đều được ghi lại.`));
add(BUL(`**Kiểm chứng độc lập:** một chương trình riêng không gọi EFIM hay bộ định vị tính lại các đại lượng từ dữ liệu gốc; sổ Excel và script dùng thư viện chuẩn tính lại sai số trung bình.`));
add(H2("5. Đóng góp của luận văn"));
add(BUL(`Một cách mô hình hoá vân tay Wi-Fi thành bài toán HUIM theo từng điểm tham chiếu, với ba định nghĩa lợi ích nội (abs, rel, rank) và ngưỡng tương đối theo ô có cơ chế tự nâng ngưỡng bảo đảm tập HUI luôn đầy đủ.`));
add(BUL(`Một thuật toán định vị chỉ dựa trên HUI gồm tám bước, trong đó tầng, ô ứng viên và toạ độ đều được suy ra từ điểm khớp HUI và các đại lượng rút ra từ HUI (hồ sơ cường độ, độ phủ ngược), không lưu và không so sánh vân tay huấn luyện.`));
add(BUL(`Kết quả dưới 7 m trên cả ${allTests.length} tập kiểm tra của ${order.length} bộ dữ liệu, kèm phân tích định lượng nguồn sai số (thiết bị thu, độ phân giải trong tầng) và kiểm chứng độc lập.`));
add(H2("6. Bố cục luận văn"));
add(P(`Ngoài phần mở đầu, kết luận, tài liệu tham khảo và phụ lục, luận văn gồm bốn chương. Chương 1 tổng quan về định vị trong nhà và khai thác tập mục lợi ích cao. Chương 2 trình bày cơ sở lý thuyết: mô hình tín hiệu, bài toán định vị vân tay, bài toán HUIM, thuật toán EFIM, Gradient Boosting và các độ đo đánh giá. Chương 3 trình bày mô hình định vị đề xuất theo tám bước từ đầu vào tới đầu ra. Chương 4 trình bày thực nghiệm, kết quả, phân tích và kiểm chứng.`));

// ================================================================== CHƯƠNG 1
add(H1("CHƯƠNG 1. TỔNG QUAN VỀ ĐỊNH VỊ TRONG NHÀ VÀ KHAI THÁC TẬP MỤC LỢI ÍCH CAO"));
add(H2("1.1. Bài toán định vị trong nhà"));
add(P(`Hệ thống định vị trong nhà (IPS) xác định vị trí của một thiết bị hoặc người dùng bên trong toà nhà, thường gồm toạ độ trên mặt sàn, tầng và toà nhà. Khác với môi trường ngoài trời, tín hiệu vô tuyến trong nhà bị phản xạ, nhiễu xạ và suy hao qua tường, sàn, đồ vật và chính cơ thể người, nên các mô hình hình học đơn giản dựa trên khoảng cách thường kém chính xác [15], [16]. Hai đặc thù quan trọng của bài toán là tính đa tầng (cần xác định đúng tầng trước khi xét toạ độ) và tính không đồng nhất của thiết bị thu: cùng một vị trí, các điện thoại khác nhau đọc cường độ tín hiệu khác nhau [8].`));
add(H2("1.2. Các công nghệ định vị trong nhà"));
const t11 = TAB(1, "So sánh định tính một số công nghệ định vị trong nhà (tổng hợp từ [15], [16])",
  ["Công nghệ", "Đại lượng đo", "Hạ tầng", "Ưu điểm", "Hạn chế"], [
    ["Wi-Fi RSSI (vân tay)", "Cường độ tín hiệu", "AP sẵn có", "Chi phí thấp, điện thoại phổ biến", "Cần khảo sát; nhạy với thiết bị và môi trường"],
    ["Bluetooth Low Energy", "Cường độ tín hiệu", "Lắp đặt beacon", "Tiêu thụ năng lượng thấp", "Cần lắp đặt, bảo trì beacon"],
    ["Ultra-wideband (UWB)", "Thời gian truyền", "Lắp đặt anchor", "Độ chính xác cao", "Chi phí phần cứng cao"],
    ["RFID", "Phát hiện thẻ", "Đầu đọc, thẻ", "Phù hợp quản lý tài sản", "Tầm hoạt động ngắn"],
    ["Cảm biến quán tính (PDR)", "Gia tốc, con quay", "Không cần", "Không phụ thuộc hạ tầng", "Sai số tích luỹ theo thời gian"],
  ], [1900, 1500, 1400, 2100, 2171], { size: 11 });
add(P(`${t11.label} tóm tắt các công nghệ thường gặp. Luận văn tập trung vào Wi-Fi RSSI vì không cần lắp đặt thêm thiết bị và có các bộ dữ liệu chuẩn để đối chiếu.`));
add(t11);
add(H2("1.3. Định vị bằng vân tay Wi-Fi"));
add(P(`Phương pháp vân tay gồm hai pha. Ở **pha khảo sát** (offline), người khảo sát ghi lại vectơ RSSI của mọi AP tại nhiều điểm tham chiếu đã biết toạ độ; tập các cặp (vân tay, vị trí) tạo thành cơ sở dữ liệu huấn luyện. Ở **pha định vị** (online), vân tay mới được so với cơ sở dữ liệu để suy ra vị trí [1], [2]. Bộ dữ liệu UJIIndoorLoc [3] là chuẩn đối chiếu phổ biến cho bài toán này với 520 AP, ba toà nhà và mười ba tòa–tầng.`));
add(P(`Các khó khăn chính của định vị vân tay gồm: (i) dao động của tín hiệu theo thời gian và theo người dùng; (ii) khác biệt giữa các thiết bị thu, khiến cùng một vị trí cho các vectơ RSSI lệch nhau; (iii) tín hiệu chồng lấn giữa các tầng liền kề; (iv) số chiều lớn và thưa (mỗi vân tay chỉ thấy một phần nhỏ trong hàng trăm AP) [8], [12].`));
add(H2("1.4. Các phương pháp định vị vân tay"));
const t12 = TAB(1, "Một số nhóm phương pháp định vị vân tay Wi-Fi",
  ["Nhóm", "Nguyên lý", "Ví dụ"], [
    ["Tất định (k-NN, WKNN)", "Tìm k vân tay huấn luyện gần nhất theo một độ đo khoảng cách, lấy trung bình vị trí", "RADAR [1]; so sánh độ đo [4]"],
    ["Xác suất", "Ước lượng phân bố RSSI tại mỗi vị trí, chọn vị trí có hậu nghiệm lớn nhất", "Horus [2]"],
    ["Học máy", "Học trực tiếp ánh xạ từ vân tay sang vị trí hoặc tầng", "Tổng quan [8], [16]"],
    ["Chọn AP", "Giảm số chiều bằng cách giữ các AP có ích cho định vị", "Chọn AP tiết kiệm năng lượng [12]"],
  ], [2100, 4571, 2400], { size: 11.5 });
add(P(`${t12.label} tóm tắt các nhóm phương pháp. Trong các hệ thống tất định, k-NN với độ đo khoảng cách phù hợp là lời giải mạnh và phổ biến [4]. Điểm chung của các phương pháp này là mô hình chứa (hoặc ước lượng trực tiếp từ) các vân tay huấn luyện. Hướng đi của luận văn khác ở chỗ mô hình chỉ gồm các mẫu tập mục khai thác được, không chứa vân tay.`));
add(t12);
add(H2("1.5. Khai thác mẫu phổ biến và tập mục lợi ích cao"));
add(P(`Khai thác tập phổ biến tìm các tập mục xuất hiện cùng nhau trong nhiều giao dịch; Apriori [11] và FP-growth [17] là hai thuật toán nền tảng. Tập phổ biến chỉ xét sự có mặt của mục, bỏ qua số lượng và giá trị. Khai thác tập mục lợi ích cao [6] gán cho mỗi mục một lợi ích nội (ví dụ số lượng) và một lợi ích ngoài (ví dụ đơn giá), và tìm các tập mục có tổng lợi ích không nhỏ hơn ngưỡng. Vì lợi ích không có tính đơn điệu như độ hỗ trợ, các thuật toán phải dùng chặn trên để cắt tỉa không gian tìm kiếm.`));
const t13 = TAB(1, "Một số thuật toán khai thác tập mục lợi ích cao tiêu biểu",
  ["Thuật toán", "Năm", "Ý tưởng chính"], [
    ["Two-Phase [7]", "2005", "Chặn trên TWU đơn điệu giảm; sinh ứng viên rồi tính lợi ích thật ở pha hai"],
    ["HUI-Miner [18]", "2012", "Danh sách lợi ích (utility-list), khai thác không sinh ứng viên"],
    ["FHM [19]", "2014", "Cắt tỉa theo đồng xuất hiện của cặp mục (EUCP) trên nền HUI-Miner"],
    ["EFIM [5]", "2017", "Chặn trên lợi ích cục bộ và lợi ích cây con; chiếu và gộp giao dịch; một lần quét mỗi nút"],
  ], [1800, 900, 6371], { size: 11.5 });
add(P(`${t13.label} tóm tắt các thuật toán tiêu biểu; các khảo sát [9], [10] cho thấy EFIM thuộc nhóm nhanh và tiết kiệm bộ nhớ nhất. Luận văn dùng EFIM làm thuật toán khai thác.`));
add(t13);
add(H2("1.6. Các giai đoạn trước của đề tài và vấn đề đặt ra"));
add(P(`Trước luận văn này, HUIM được dùng để chọn tập AP cho k-NN. Khai thác HUI trên toàn bộ dữ liệu UJIIndoorLoc chỉ giữ được ${refU.huim_toan_cuc_so_ap} AP và cho sai số ${vn(refU.huim_toan_cuc_knn_m)} m; khai thác theo từng tòa–tầng giữ ${refU.huim_chon_ap_so_ap}/${refU.tong_ap} AP và cho ${vn(refU.huim_chon_ap_knn_m)} m. Tuy nhiên, phân tích Shapley cho thấy HUIM chỉ đóng góp khoảng 6% mức giảm sai số, phần còn lại đến từ k-NN và các bước khác; thay HUIM bằng một tiêu chí xếp hạng AP đơn giản cho kết quả gần như tương đương. Khi đó HUIM là một nhánh tiền xử lý có thể bỏ đi.`));
add(BOX("Câu hỏi nghiên cứu", [`Có thể xây dựng một hệ thống định vị trong nhà trong đó HUIM là thuật toán định vị chính — mô hình là tập HUI, mọi quyết định đến từ bằng chứng HUI, không dùng k-NN — mà vẫn đạt sai số trung bình dưới 7 m trên tập kiểm tra hay không?`]));
add(GAP());
add(H2("1.7. Kết luận chương 1"));
add(P(`Chương 1 đã trình bày bài toán định vị trong nhà, các công nghệ và phương pháp định vị vân tay, cùng bài toán và các thuật toán khai thác tập mục lợi ích cao. Từ hạn chế của cách dùng HUIM như bước chọn AP, chương này đặt ra câu hỏi nghiên cứu của luận văn. Chương 2 trình bày các cơ sở lý thuyết cần thiết để trả lời câu hỏi đó.`));

// ================================================================== CHƯƠNG 2
add(H1("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT"));
add(H2("2.1. Mô hình tín hiệu Wi-Fi và cường độ RSSI"));
add(P(`Cường độ tín hiệu thu được từ một AP giảm theo khoảng cách và chịu ảnh hưởng của vật cản. Mô hình suy hao log-khoảng cách thường dùng để mô tả hiện tượng này [15]:`));
add(EQ(2, [up("RSSI"), rb(r("d")), r("="), up("RSSI"), rb(sb([r("d")], [r("0")])), r("−10"), r("n"), sb([up("log")], [r("10")]), fr([r("d")], [sb([r("d")], [r("0")])]), r("+"), sb([r("X")], [r("σ")])]));
add(P(`trong đó d là khoảng cách tới AP, $d_0$ là khoảng cách tham chiếu, n là hệ số suy hao phụ thuộc môi trường và $X_σ$ là nhiễu ngẫu nhiên. Vì n và $X_σ$ thay đổi mạnh theo vị trí, việc suy khoảng cách từ RSSI rồi tam giác đạc kém chính xác trong nhà; phương pháp vân tay tránh mô hình hoá trực tiếp bằng cách học quan hệ giữa vectơ RSSI và vị trí từ dữ liệu khảo sát. Trong UJIIndoorLoc, RSSI nằm trong khoảng −104 dBm tới 0 dBm, và AP không được phát hiện được ghi giá trị quy ước 100 [3].`));
add(H2("2.2. Bài toán định vị vân tay"));
add(P(`Gọi $A$ là tập AP. Một vân tay là vectơ f gồm |A| thành phần, thành phần thứ i là RSSI của AP i hoặc giá trị rỗng nếu AP i không được phát hiện. Tập huấn luyện gồm các cặp ($f_j$, $ℓ_j$) với $ℓ_j$ = ($x_j$, $y_j$, tòa nhà, tầng). Bài toán định vị là xây dựng ánh xạ h sao cho với vân tay mới f, h(f) gần vị trí thật. Phương pháp tham chiếu k-NN có trọng số (WKNN) ước lượng:`));
add(EQ(2, [rb(r("x̂,ŷ")), r("="), fr([sum([r("j∈"), sb([r("N")], [r("k")]), rb(r("f"))], [sb([r("w")], [r("j")]), rb(sb([r("x")], [r("j")]), r(","), sb([r("y")], [r("j")]))])], [sum([r("j∈"), sb([r("N")], [r("k")]), rb(r("f"))], [sb([r("w")], [r("j")])])]), r(",   "), sb([r("w")], [r("j")]), r("="), fr([r("1")], [r("δ"), rb(r("f,"), sb([r("f")], [r("j")]))])]));
add(P(`với $N_k$(f) là k vân tay huấn luyện gần f nhất theo độ đo δ [4]. Luận văn chỉ dùng k-NN làm **hệ tham chiếu** để đối chiếu kết quả (mục 4.9); hệ thống đề xuất không dùng công thức này.`));
add(H2("2.3. Bài toán khai thác tập mục lợi ích cao"));
add(P(`Cho tập mục I và cơ sở dữ liệu giao dịch D. Mỗi mục i trong giao dịch T có lợi ích nội q(i,T) > 0 và mỗi mục có lợi ích ngoài p(i) > 0. Lợi ích của mục, của tập mục X trong một giao dịch và trong toàn bộ D được định nghĩa [6], [7]:`));
add(EQ(2, [r("u"), rb(r("i,T")), r("=q"), rb(r("i,T")), r("·p"), rb(r("i"))]));
add(EQ(2, [r("u"), rb(r("X,T")), r("="), sum([r("i∈X")], [r("u"), rb(r("i,T"))])]));
add(EQ(2, [r("u"), rb(r("X")), r("="), sum([r("T∈D, X⊆T")], [r("u"), rb(r("X,T"))])]));
add(BOX("Định nghĩa 2.1 (Tập mục lợi ích cao)", [`Cho ngưỡng minUtil > 0, tập mục X là một High Utility Itemset (HUI) nếu u(X) ≥ minUtil. Bài toán HUIM là tìm tập tất cả các HUI của D.`]));
add(GAP());
// ví dụ minh hoạ: CSDL 4 giao dịch, lợi ích tính bằng mã để bảo đảm đúng
{
  const DB = [{ A: 5, B: 3, C: 1 }, { A: 4, C: 2, D: 6 }, { B: 2, C: 3, D: 1 }, { A: 3, B: 4, D: 2 }];
  const items = ["A", "B", "C", "D"], MINU = 15;
  const util = (X) => DB.reduce((s, t) => (X.every((i) => i in t) ? s + X.reduce((a, i) => a + t[i], 0) : s), 0);
  const tu = DB.map((t) => Object.values(t).reduce((a, b) => a + b, 0));
  const twu = (X) => DB.reduce((s, t, k) => (X.every((i) => i in t) ? s + tu[k] : s), 0);
  const subsets = [];
  for (let m = 1; m < 16; m++) subsets.push(items.filter((_, i) => m & (1 << i)));
  subsets.sort((a, b) => a.length - b.length || a.join().localeCompare(b.join()));
  const tE1 = TAB(2, "Ví dụ: bốn vân tay (giao dịch) với lợi ích nội của các AP (p(i) = 1)", ["Giao dịch", "A", "B", "C", "D", "TU(T)"],
    DB.map((t, k) => [`$T_${k + 1}$`, ...items.map((i) => (i in t ? String(t[i]) : "–")), String(tu[k])]), [1800, 1300, 1300, 1300, 1300, 2071], { align: [C, RT, RT, RT, RT, RT] });
  const rows = subsets.filter((X) => util(X) > 0).map((X) => [`{${X.join(", ")}}`, String(util(X)), String(twu(X)), util(X) >= MINU ? "HUI" : "–"]);
  const tE2 = TAB(2, `Lợi ích và TWU của mọi tập mục trong ví dụ; minUtil = ${MINU}`, ["Tập mục X", "u(X)", "TWU(X)", "Kết luận"], rows, [3000, 1800, 1800, 2471], { align: [L, RT, RT, C], size: 11 });
  const hu = subsets.filter((X) => util(X) >= MINU).map((X) => `{${X.join(", ")}}`);
  add(P(`Ví dụ, xét cơ sở dữ liệu gồm bốn vân tay ở ${tE1.label}, trong đó mỗi AP là một mục và lợi ích nội là cường độ đã chuẩn hoá. Với minUtil = ${MINU}, ${tE2.label} liệt kê lợi ích của mọi tập mục; các HUI là ${hu.join(", ")}. Có thể thấy u({A}) = ${util(["A"])} nhỏ hơn u({A, D}) = ${util(["A", "D"])}: thêm mục làm lợi ích tăng, nên lợi ích không đơn điệu giảm. Ngược lại TWU luôn không tăng khi thêm mục, và mọi HUI đều có TWU ≥ minUtil.`));
  add(tE1, tE2);
}
add(P(`Khác với độ hỗ trợ trong khai thác tập phổ biến, lợi ích không có tính đơn điệu giảm: thêm một mục có thể làm u(X) tăng hoặc giảm, nên không thể cắt tỉa trực tiếp bằng u(X). Các thuật toán dùng chặn trên đơn điệu giảm, phổ biến nhất là lợi ích có trọng số giao dịch [7]:`));
add(EQ(2, [up("TU"), rb(r("T")), r("="), sum([r("i∈T")], [r("u"), rb(r("i,T"))]), r(",   "), up("TWU"), rb(r("X")), r("="), sum([r("T∈D, X⊆T")], [up("TU"), rb(r("T"))])]));
add(BOX("Tính chất 2.1 (Đóng xuống của TWU)", [`Với mọi X ⊆ Y: u(Y) ≤ TWU(Y) ≤ TWU(X). Do đó nếu TWU(X) < minUtil thì không tập cha nào của X là HUI, và X cùng mọi mở rộng của nó có thể bị loại.`]));
add(GAP());
add(H2("2.4. Thuật toán EFIM"));
add(P(`EFIM [5] duyệt cây liệt kê tập theo chiều sâu, với các mục được sắp theo thứ tự tăng dần của TWU. Tại nút α, với mỗi mục z có thể mở rộng, EFIM tính hai chặn trên trong một lần quét cơ sở dữ liệu đã chiếu theo α:`));
add(EQ(2, [up("lu"), rb(r("α,z")), r("="), sum([r("T∋α∪{z}")], [sq(r("u"), rb(r("α,T")), r("+"), up("re"), rb(r("α,T")))])]));
add(EQ(2, [up("su"), rb(r("α,z")), r("="), sum([r("T∋α∪{z}")], [sq(r("u"), rb(r("α,T")), r("+u"), rb(r("z,T")), r("+"), sum([r("i∈T, i≻z")], [r("u"), rb(r("i,T"))]))])]));
add(P(`Trong đó re(α,T) là tổng lợi ích các mục đứng sau α trong T. Nếu lu(α,z) < minUtil thì z bị loại khỏi toàn bộ cây con của α; nếu su(α,z) < minUtil thì nhánh α ∪ {z} không được duyệt. Hai kỹ thuật **chiếu cơ sở dữ liệu** (chỉ giữ phần giao dịch đứng sau α) và **gộp giao dịch** (cộng lợi ích các giao dịch giống hệt nhau sau khi chiếu) giúp mỗi nút chỉ cần một lần quét tuyến tính.`));
add(ALGO(2, "EFIM (tóm tắt theo [5])", [
  "Đầu vào: cơ sở dữ liệu D, ngưỡng minUtil",
  "  1. Tính TWU của mọi mục; loại các mục có TWU < minUtil; sắp mục theo TWU tăng dần",
  "  2. Sắp và gộp các giao dịch giống nhau; tính lu(∅, z) và su(∅, z) cho mọi mục z",
  "  3. Search(α = ∅, D, mục mở rộng = {z : su(∅,z) ≥ minUtil}, mục chính = {z : lu(∅,z) ≥ minUtil})",
  "Search(α, D_α, Primary, Secondary):",
  "  4. Với mỗi z ∈ Primary: β ← α ∪ {z}; quét D_α tính u(β) và chiếu, gộp được D_β",
  "  5.   nếu u(β) ≥ minUtil thì xuất β",
  "  6.   tính lu(β, w), su(β, w) cho mọi w ∈ Secondary sau z trong một lần quét D_β",
  "  7.   Search(β, D_β, {w : su(β,w) ≥ minUtil}, {w : lu(β,w) ≥ minUtil})",
  "Đầu ra: tập mọi HUI của D",
]));
add(P(`Bản cài đặt EFIM của luận văn (ma_nguon/src/huim/efim.py) được kiểm thử bằng cách so với một thuật toán vét cạn trên dữ liệu ngẫu nhiên: tập HUI và lợi ích của từng HUI trùng khớp hoàn toàn. Bản cài đặt thêm ngân sách thời gian và số HUI cho mỗi lần chạy để dùng trong cơ chế tự nâng ngưỡng (mục 3.3).`));
add(H2("2.5. Học tăng cường theo gradient"));
add(P(`Gradient Boosting [13] xây dựng một mô hình hồi quy dạng tổng của M cây quyết định nhỏ, mỗi cây được học để giảm hàm mất mát của tổng các cây trước nó:`));
add(EQ(2, [sb([r("F")], [r("M")]), rb(r("φ")), r("="), sb([r("F")], [r("0")]), r("+"), sum([r("m=1")], [r("η"), sb([r("h")], [r("m")]), rb(r("φ"))], [r("M")]), r(",   "), sb([r("h")], [r("m")]), r("="), sb([up("arg min")], [r("h")]), sum([r("j")], [sp([rb(sb([r("g")], [r("jm")]), r("−h"), rb(sb([r("φ")], [r("j")])))], [r("2")])])]));
add(P(`với η là tốc độ học và $g_{jm}$ là gradient âm của hàm mất mát tại mẫu j sau m − 1 cây (với mất mát bình phương, chính là phần dư). Biến thể dựa trên histogram [14], được cài đặt trong scikit-learn [20] (HistGradientBoostingRegressor), rời rạc hoá đặc trưng thành các ngăn để học nhanh trên hàng trăm nghìn mẫu. Trong luận văn, Gradient Boosting chỉ được dùng ở Bước 8 để kết hợp các bằng chứng rút ra từ HUI (mục 3.8).`));
add(H2("2.6. Độ đo đánh giá"));
add(P(`Sai số định vị của vân tay n là khoảng cách Euclid giữa vị trí ước lượng và vị trí thật, đổi ra mét thực địa bằng hệ số g (g = 0,766126 cho UJIIndoorLoc do dùng toạ độ Web Mercator, g = 1 cho các bộ còn lại). Độ đo chính là sai số trung bình trên N vân tay kiểm tra; ngoài ra luận văn báo cáo trung vị, các phân vị 75%, 90%, 95% và độ chính xác tòa nhà, tòa–tầng:`));
add(EQ(2, [sb([r("e")], [r("n")]), r("="), sqrt([sp([rb(sb([r("x̂")], [r("n")]), r("−"), sb([r("x")], [r("n")]))], [r("2")]), r("+"), sp([rb(sb([r("ŷ")], [r("n")]), r("−"), sb([r("y")], [r("n")]))], [r("2")])]), r("·g,   "), r("ē"), r("="), fr([r("1")], [r("N")]), sum([r("n=1")], [sb([r("e")], [r("n")])], [r("N")])]));
add(EQ(2, [up("Acc"), r("="), fr([r("1")], [r("N")]), sum([r("n=1")], [r("𝟙"), sq(sb([r("f̂")], [r("n")]), r("="), sb([r("f")], [r("n")]))], [r("N")]), r(",   "), up("SE"), rb(r("ē")), r("="), fr([r("s")], [sqrt([r("N")])])]));
add(P(`trong đó $f_n$ là nhãn tòa–tầng, 𝟙[·] là hàm chỉ thị và s là độ lệch chuẩn mẫu của các sai số; sai số chuẩn SE dùng để đánh giá độ tin cậy của sai số trung bình.`));
add(H2("2.7. Kết luận chương 2"));
add(P(`Chương 2 đã trình bày mô hình tín hiệu, bài toán định vị vân tay, bài toán HUIM với tính chất đóng xuống của TWU, thuật toán EFIM, kỹ thuật Gradient Boosting và các độ đo đánh giá. Đây là nền tảng cho mô hình định vị đề xuất ở Chương 3.`));

require("./build_report_ch3_4")({ add, fig, D, U, UT, SEL, PRM, V6, U4, RSH, allTests, nOk, others, ref, refU, fs4, pil, win, EX, GF, nHUI3,
  phones, floors, IMP, order, T, L_ });

// ================================================================== TÀI LIỆU THAM KHẢO
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
  "H. Liu, H. Darabi, P. Banerjee, J. Liu, “Survey of wireless indoor positioning techniques and systems,” IEEE Transactions on Systems, Man, and Cybernetics, Part C, vol. 37, no. 6, pp. 1067–1080, 2007, doi: 10.1109/TSMCC.2007.905750.",
  "F. Zafari, A. Gkelias, K. K. Leung, “A survey of indoor localization systems and technologies,” IEEE Communications Surveys & Tutorials, vol. 21, no. 3, pp. 2568–2599, 2019, doi: 10.1109/COMST.2019.2911558.",
  "J. Han, J. Pei, Y. Yin, “Mining frequent patterns without candidate generation,” in Proc. ACM SIGMOD 2000, pp. 1–12, doi: 10.1145/342009.335372.",
  "M. Liu, J. Qu, “Mining high utility itemsets without candidate generation,” in Proc. ACM CIKM 2012, pp. 55–64, doi: 10.1145/2396761.2396773.",
  "P. Fournier-Viger, C.-W. Wu, S. Zida, V. S. Tseng, “FHM: Faster high-utility itemset mining using estimated utility co-occurrence pruning,” in Proc. ISMIS 2014, LNAI, pp. 83–92, doi: 10.1007/978-3-319-08326-1_9.",
  "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
];
add(H1("TÀI LIỆU THAM KHẢO"));
refs.forEach((t, i) => add(new Paragraph({ alignment: J, spacing: { after: 100, line: 300 },
  indent: { left: 567, hanging: 567 }, tabStops: [{ type: TabStopType.LEFT, position: 567 }],
  children: [R(`[${i + 1}]`), new TextRun({ font: L_.FONT, children: [new Tab()] }), R(t)] })));

require("./build_report_appendix")({ add, D, U, UT, V6, EX, GF, L_ });

build({ cover, titlePage, front, body, out: path.join(B, "Bao_cao_HUIM_IPS_UJIIndoorLoc.docx") });
