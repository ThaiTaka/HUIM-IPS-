// Phần 1 của Slide_HUIM_IPS_V7_day_du.pptx: bìa, bản đồ tổng quát, chương 1 "Dữ liệu UJIIndoorLoc".
// Mỗi slide: nội dung + kịch bản thuyết trình (ghi chú) có ví dụ đời thường và lý do chọn.
module.exports = function part1(c) {
  const { pres, slide, divider, img, as, bullets, text, ann, stat, card, badge, table, tb, callout, fcard, head, chartBase, vn, vnd, pct, tr, dI,
    MX, SW, W, F, INK, NAVY, TEAL, RUST, GREY, GOLD, SOFT, SOFT2, CARD, LINE, D, E, DS, path } = c;
  const T7 = tr("C_rel_absL3"), T6 = tr("V6"), T6r = tr("V6r");
  const FIN = D.test_json.C_rel_absL3;
  const EX = D.example;

  // ------------------------------------------------------------------ 1. bìa
  pres.addSection({ title: "Mở đầu" });
  {
    const s = pres.addSlide({ masterName: "TOI", sectionTitle: "Mở đầu" });
    s.background = { path: as("art_title") };
    s.addText("HUIM-IPS · PHIÊN BẢN V7", { x: MX, y: 0.7, w: 8, h: 0.4, fontFace: F, fontSize: 15, bold: true, color: "9BC4CD", charSpacing: 2, margin: 0, isTextBox: true });
    s.addText("Từ vân tay Wi-Fi đến sai số 6,3 m", { x: MX, y: 1.3, w: 7.5, h: 1.9, fontFace: F, fontSize: 44, bold: true, color: "FFFFFF", valign: "top", margin: 0, isTextBox: true });
    s.addText(`Định vị trong nhà trên UJIIndoorLoc: ${vn(T7.mean, 3)} m trên tập kiểm tra (V6: ${vn(T6.mean, 3)} m)`, { x: MX, y: 3.3, w: 7.5, h: 0.9, fontFace: F, fontSize: 21, color: "FFFFFF", margin: 0, valign: "top", isTextBox: true });
    s.addShape(pres.shapes.LINE, { x: MX, y: 4.35, w: 2.6, h: 0, line: { color: GOLD, width: 2.5 } });
    s.addText("Khai thác tập mục lợi ích cao (EFIM) làm lõi, học trọng số của 30 ô ứng viên bằng chính sai số mét — không k-NN, không lưu vân tay huấn luyện", { x: MX, y: 4.5, w: 7.5, h: 1.0, fontFace: F, fontSize: 18, italic: true, color: "DCE6EE", margin: 0, valign: "top", isTextBox: true });
    s.addText([
      { text: "Học viên: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
      { text: "Người hướng dẫn khoa học: ", options: { bold: true } }, { text: "……………………………", options: { breakLine: true } },
      { text: "Năm 2026", options: {} },
    ], { x: MX, y: 5.7, w: 7, h: 1.2, fontFace: F, fontSize: 16, color: "FFFFFF", paraSpaceAfter: 4, margin: 0, isTextBox: true });
    s.addText("Nền: bản đồ điểm khảo sát UJIIndoorLoc; chấm màu là vân tay kiểm tra theo sai số V7", { x: 7.5, y: 7.0, w: 5.5, h: 0.3, fontFace: F, fontSize: 10, italic: true, color: "9BB7C4", align: "right", margin: 0, isTextBox: true });
    s.addNotes(`KỊCH BẢN (khoảng 1 phút)
NÓI: Em xin chào quý thầy cô. Hôm nay em trình bày một hệ thống định vị trong nhà bằng Wi-Fi.
VÍ DỤ ĐỜI THƯỜNG: Khi mình vào một trung tâm thương mại hay thư viện lớn, GPS gần như mất tín hiệu, nhưng điện thoại vẫn "nghe" được rất nhiều bộ phát Wi-Fi xung quanh. Đứng ở chỗ này thì nghe được bộ phát A rất to, bộ phát B nhỏ; đi sang chỗ khác thì khác hẳn. Tổ hợp "nghe được những Wi-Fi nào, to nhỏ ra sao" giống như dấu vân tay của từng vị trí. Hệ thống của em dùng dấu vân tay đó để đoán người dùng đang đứng ở đâu.
KẾT QUẢ: Trên tập kiểm tra của bộ dữ liệu UJIIndoorLoc, sai số trung bình của phiên bản V7 là ${vn(T7.mean, 3)} mét, tức là khoảng 6,3 mét. Phiên bản trước đó (V6) là ${vn(T6.mean, 3)} mét. Em nói thẳng ngay từ đầu: mục tiêu ban đầu là dưới 6 mét thì em CHƯA đạt.
LỘ TRÌNH: Em sẽ đi theo đúng đường đi của dữ liệu: bắt đầu từ dữ liệu UJIIndoorLoc, rồi rút các mẫu Wi-Fi đặc trưng của từng ô, chọn ra 30 ô ứng viên, học cách chia trọng số cho 30 ô đó, rồi một ví dụ trọn vẹn, kết quả và cuối cùng là cách em kiểm chứng. Ở mỗi bước, em sẽ giải thích công thức, từng ký hiệu và vì sao chọn các con số.
CHUYỂN Ý: Trước hết, em xin cho thầy cô xem bản đồ tổng quát của cả hệ thống.`);
  }

  // ------------------------------------------------------------------ 2. bản đồ tổng quát
  {
    const s = slide("Tổng quan", `Con đường từ dữ liệu đến ${vn(T7.mean, 3)} m: tám bước`,
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Đây là bản đồ của cả bài. Dữ liệu đi từ trái sang phải, từ hàng trên xuống hàng dưới. Em đọc nhanh từng ô; chi tiết của từng ô sẽ có slide riêng.
VÍ DỤ ĐỜI THƯỜNG: Hãy hình dung em là một người dẫn đường trong tòa nhà. Bước 1: em có sổ ghi chép 19 937 lần đo Wi-Fi ở 933 điểm đã đánh dấu. Bước 2 và 3: với mỗi điểm đánh dấu, em rút ra "bộ mẫu Wi-Fi đặc trưng" của điểm đó, giống như một quán ăn có "combo món gọi nhiều nhất". Bước 4 và 5: khi có một lần đo mới, em đối chiếu với combo của từng điểm để chọn ra tầng và 30 điểm nghi vấn. Bước 6 và 7: thay vì chọn đại một điểm, em để một "trọng tài" nhỏ chia phiếu bầu cho 30 điểm đó, rồi lấy vị trí trung bình có trọng số. Bước 8: đo xem vị trí đoán lệch bao nhiêu mét so với vị trí thật.
VÌ SAO THIẾT KẾ NHƯ VẬY: Hai bước đầu cho ra một danh sách ứng viên rất tốt: trong 30 ứng viên luôn có ô cách vị trí thật trung bình chỉ 0,59 mét (trên tập dev). Vấn đề không phải là tìm đúng vùng, mà là chia trọng số cho khéo. Đó là lý do V7 tập trung học bước 6 và 7.
CHUYỂN Ý: Bây giờ em đi từng bước, bắt đầu từ dữ liệu.`);
    const box = (x, y, w, h, n, t, sub, col) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: col === TEAL ? "E6F0F2" : col === RUST ? "F7EAE3" : "EDF0F5" }, line: { color: col, width: 1.25 } });
      badge(s, x + 0.12, y + 0.12, n, col, 0.42);
      s.addText(t, { x: x + 0.62, y: y + 0.1, w: w - 0.72, h: 0.46, fontFace: F, fontSize: 14.5, bold: true, color: INK, margin: 0, valign: "middle", isTextBox: true });
      s.addText(sub, { x: x + 0.15, y: y + 0.66, w: w - 0.3, h: h - 0.72, fontFace: F, fontSize: 12.5, color: INK, margin: 0, valign: "top", isTextBox: true });
    };
    const w = 2.75, g = 0.37, xs = [0, 1, 2, 3].map((i) => MX + i * (w + g));
    const nHUI = Object.values(D.config.hui.final_hui_counts).reduce((a, b) => a + b, 0);
    const r1 = [["1", "Dữ liệu UJIIndoorLoc", `${vn(DS.train.rows, 0)} vân tay huấn luyện, ${vn(DS.test.rows, 0)} kiểm tra; 520 AP; 3 tòa, 13 tầng`, NAVY],
      ["2", "Ô tham chiếu và lợi ích q", `${vn(DS.cells.n, 0)} ô; RSSI đổi thành q ∈ [1, 100] theo 3 cách: rank, abs, rel`, TEAL],
      ["3", "Khai thác HUI bằng EFIM", `Mỗi ô một tập mẫu AP đặc trưng; 5 góc nhìn, ${vn(nHUI / 1e6, 2)} triệu HUI`, TEAL],
      ["4", "Điểm khớp và chọn tầng", `Điểm P·V³, làm mượt σ = 3 m; đúng tầng ${pct(FIN.floor_accuracy, 2)}`, TEAL]];
    const r2 = [["5", "30 ô ứng viên", "Ô gần nhất trong 30 cách vị trí thật 0,59 m (dev): ứng viên đã tốt", TEAL],
      ["6", "49 đặc trưng bằng chứng", "Mỗi ô có 49 số suy ra từ HUI; dạng tương đối → 196 đầu vào", RUST],
      ["7", "MLP chấm điểm + softmax", "Điểm s → trọng số w (tổng 1); tọa độ = Σ w · tâm ô", RUST],
      ["8", "Học bằng sai số mét", `Mất mát = sai số mét; kết quả test ${vn(T7.mean, 3)} m`, RUST]];
    r1.forEach((b, i) => box(xs[i], 1.45, w, 1.95, ...b));
    r2.forEach((b, i) => box(xs[i], 4.0, w, 1.95, ...b));
    for (let i = 0; i < 3; i++) {
      s.addShape(pres.shapes.LINE, { x: xs[i] + w + 0.03, y: 2.4, w: g - 0.06, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
      s.addShape(pres.shapes.LINE, { x: xs[i] + w + 0.03, y: 4.95, w: g - 0.06, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
    }
    s.addShape(pres.shapes.LINE, { x: xs[3] + w / 2, y: 3.4, w: 0, h: 0.3, line: { color: GREY, width: 1.75 } });
    s.addShape(pres.shapes.LINE, { x: xs[0] + w / 2, y: 3.7, w: xs[3] - xs[0], h: 0, line: { color: GREY, width: 1.75 } });
    s.addShape(pres.shapes.LINE, { x: xs[0] + w / 2, y: 3.7, w: 0, h: 0.28, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 6.2, w: 0.4, h: 0.25, rectRadius: 0.05, fill: { color: "E6F0F2" }, line: { color: TEAL, width: 1.25 } });
    s.addText("bước HUIM (mẫu, điểm khớp, ứng viên)", { x: MX + 0.5, y: 6.17, w: 3.6, h: 0.3, fontFace: F, fontSize: 13, color: INK, margin: 0, isTextBox: true });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX + 4.4, y: 6.2, w: 0.4, h: 0.25, rectRadius: 0.05, fill: { color: "F7EAE3" }, line: { color: RUST, width: 1.25 } });
    s.addText("bước học trọng số (phần mới của V7)", { x: MX + 4.9, y: 6.17, w: 3.6, h: 0.3, fontFace: F, fontSize: 13, color: INK, margin: 0, isTextBox: true });
    s.addText("Mọi đặc trưng đều sinh từ HUI; tọa độ thật chỉ là nhãn huấn luyện và để đo.", { x: 8.2, y: 6.17, w: SW - MX - 8.2, h: 0.3, fontFace: F, fontSize: 12.5, italic: true, color: NAVY, margin: 0, isTextBox: true, align: "right" });
  }

  // ================================================================== CHƯƠNG 1
  divider(0, "Dữ liệu UJIIndoorLoc", ["Bài toán và các cột dữ liệu", "Một vân tay Wi-Fi trông thế nào", "Train và test khác nhau có chủ đích", "Đơn vị đo, ô tham chiếu và cách đánh giá"],
`KỊCH BẢN (20 giây)
NÓI: Chương đầu tiên là dữ liệu. Em sẽ nói ba điều: dữ liệu gồm những gì và cột nào được dùng làm gì; vì sao tập huấn luyện và tập kiểm tra khác nhau có chủ đích; và hệ thống đo sai số theo đơn vị nào. Lý do em dành thời gian cho dữ liệu: mọi con số quyết định về sau, từ cách chia fold đến cách tính mét, đều bắt nguồn từ đặc điểm của dữ liệu này.
CHUYỂN Ý: Trước hết là bài toán và các cột dữ liệu.`);

  // ---- bài toán và các cột
  {
    const s = slide("Dữ liệu · Bài toán", "Bài toán và các cột dữ liệu: cột nào dùng làm gì",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Bài toán rất đơn giản khi phát biểu: cho một vân tay Wi-Fi, trả về tòa nhà, tầng và tọa độ (x, y). Dữ liệu em dùng là UJIIndoorLoc, thu bằng điện thoại trong ba tòa nhà của Đại học Jaume I (Tây Ban Nha): ${vn(DS.train.rows, 0)} vân tay dùng để huấn luyện và ${vn(DS.test.rows, 0)} vân tay để kiểm tra, tổng cộng ${vn(DS.train.rows + DS.test.rows, 0)} dòng.
VÍ DỤ ĐỜI THƯỜNG: Hãy tưởng tượng mỗi dòng của bảng là một lần ai đó đứng yên ở một điểm, mở điện thoại và ghi lại: "ở đây nghe được 18 bộ phát Wi-Fi, bộ số 98 và 99 rất mạnh, bộ số 486 yếu...", kèm theo nhãn: "điểm này ở tòa 2, tầng 1, kinh độ ..., vĩ độ ...". Đó là một vân tay có nhãn.
CÁC CỘT: Có 520 cột WAP001 đến WAP520 là cường độ tín hiệu của 520 bộ phát; đây là đầu vào duy nhất của hệ thống. Bốn cột LONGITUDE, LATITUDE, FLOOR, BUILDINGID là nhãn vị trí, chỉ dùng để huấn luyện và để đo sai số. Cột PHONEID em dùng để chia fold. Ba cột SPACEID, RELATIVEPOSITION và USERID em không dùng: SPACEID và RELATIVEPOSITION bằng 0 hết trong tập kiểm tra nên không thể đánh giá được.
VÌ SAO CHỌN: Em chỉ dùng đầu vào Wi-Fi thuần túy, đúng chuẩn của bài toán, để so sánh công bằng với các phiên bản trước.
CHUYỂN Ý: Tiếp theo em cho thầy cô thấy một vân tay cụ thể trông như thế nào.`);
    const rows = [["WAP001 … WAP520", "RSSI (dBm) của 520 bộ phát; 100 = không nghe thấy", "đầu vào duy nhất"],
      ["LONGITUDE, LATITUDE", "tọa độ Web-Mercator của vị trí đo", "nhãn huấn luyện; đo sai số"],
      ["BUILDINGID, FLOOR", "tòa (0–2) và tầng (0–4): 13 cặp tòa–tầng", "nhãn huấn luyện; đo độ đúng tầng"],
      ["PHONEID", "mã điện thoại thu (16 máy huấn luyện, 11 máy kiểm tra)", "chia fold theo điện thoại"],
      ["USERID, TIMESTAMP", "người thu và thời điểm thu", "không dùng làm đầu vào"],
      ["SPACEID, RELATIVEPOSITION", "phòng và vị trí tương đối; bằng 0 hết ở tập kiểm tra", "không dùng"]];
    head(s, "Các cột của UJIIndoorLoc và vai trò trong V7", MX, 1.4, 8);
    tb(s, ["Cột", "Ý nghĩa", "Vai trò trong V7"], rows, MX, 1.8, 8.2, [2.5, 3.7, 2.0], { size: 12.5 });
    const x = MX + 8.5, w = SW - MX - x;
    stat(s, x, 1.4, w, vn(DS.train.rows + DS.test.rows, 0), `vân tay: ${vn(DS.train.rows, 0)} huấn luyện + ${vn(DS.test.rows, 0)} kiểm tra`, TEAL, 34);
    stat(s, x, 2.85, w, "520 AP", "bộ phát Wi-Fi (WAP001–WAP520), đầu vào của hệ thống", NAVY, 34);
    stat(s, x, 4.3, w, "3 tòa · 13 tầng", `tòa 0: ${DS.floor_per_building["0"]} tầng; tòa 1: ${DS.floor_per_building["1"]}; tòa 2: ${DS.floor_per_building["2"]}`, NAVY, 28);
    card(s, MX, 5.75, W, 1.1, SOFT2, null, RUST, RUST);
    text(s, "**Chú thích:** vân tay = một lần đo, tức một dòng gồm 520 giá trị RSSI. **RSSI** (Received Signal Strength Indicator) là cường độ tín hiệu tính bằng dBm: càng gần 0 càng mạnh, −104 là rất yếu. **WAP** = Wireless Access Point (bộ phát Wi-Fi). Nguồn dữ liệu: Torres-Sospedra và cộng sự, IPIN 2014.", MX + 0.3, 5.85, W - 0.6, 0.95, { fontSize: 13.5, valign: "middle" });
  }

  // ---- một vân tay
  {
    const s = slide("Dữ liệu · Một vân tay", "Một vân tay Wi-Fi: 520 số, nhưng đa số bằng 100",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Đây là một vân tay thật, hàng 335 của tập kiểm tra. Có 520 số nhưng chỉ ${EX.n_ap} số là tín hiệu thật. Bảng bên trái liệt kê ${EX.n_ap} bộ phát điện thoại nghe thấy, ví dụ WAP098 và WAP099 đều ở −54 dBm là rất mạnh; WAP486 ở −79 dBm thì yếu hơn nhiều.
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ đến chiếc radio. Cả dải sóng có 520 đài, nhưng ở chỗ bạn ngồi chỉ bắt được khoảng 18 đài; 502 đài còn lại là "rè, không bắt được". Dữ liệu ghi những đài không bắt được bằng số 100. Số 100 không phải là tín hiệu mạnh, mà chỉ có nghĩa là "không nghe thấy".
VÌ SAO TIN RẰNG 100 LÀ "KHÔNG NGHE THẤY": Em kiểm chứng bằng ba bằng chứng. Một, tài liệu chính thức ghi đúng như vậy. Hai, trong cả ma trận 10,4 triệu ô, không có giá trị nào từ 1 đến 99: tín hiệu thật nằm trong khoảng −104 đến 0, còn lại chỉ có đúng số 100 — một khoảng trống rộng 100 đơn vị thì không phải là thang đo thật. Ba, nếu 100 là tín hiệu thì điện thoại nào cũng nghe thấy gần như mọi đài ở mức mạnh nhất, điều này phi lý. Với cách hiểu đúng, trung bình mỗi vân tay nghe được ${vn(DS.train.ap_per_fp.mean, 2)} bộ phát, tức khoảng 3,5% trong số 520.
HỆ QUẢ: Dữ liệu cực kỳ thưa: ${vn(100 * DS.train.share_not_detected, 2)}% là "không nghe thấy". Vì vậy cách tự nhiên nhất là coi mỗi vân tay như một "giỏ hàng" chỉ chứa các bộ phát nghe được; em sẽ quay lại ý này ở chương hai.
NẾU BỊ HỎI: "76 vân tay không nghe được gì thì sao?" — Em giữ nguyên, báo cáo riêng, vì chúng tập trung ở vài điện thoại (lỗi thu), và tập kiểm tra không có vân tay nào như vậy.
CHUYỂN Ý: Tiếp theo, tập huấn luyện và tập kiểm tra khác nhau như thế nào.`);
    head(s, `Hàng ${EX.src_row} của tập kiểm tra: ${EX.n_ap} AP nghe được (còn lại ${520 - EX.n_ap} giá trị = 100)`, MX, 1.4, 6.4, 14.5);
    const rows = EX.aps.slice(0, 6).map((a) => [`WAP${String(a.ap).padStart(3, "0")}`, `${vn(a.rssi, 0)}`, a.rssi >= -60 ? "rất mạnh" : a.rssi >= -75 ? "mạnh" : a.rssi >= -85 ? "yếu" : "rất yếu"]);
    rows.push(["… còn " + (EX.n_ap - 6) + " AP", "yếu hơn", ""]);
    const yb = tb(s, ["AP", "RSSI (dBm)", "Mức"], rows, MX, 1.8, 4.1, [1.6, 1.4, 1.1], { size: 12, minH: 0.32, align: ["left", "right", "left"] });
    const hist = DS.train.ap_hist.map((b, i) => (b.lo === b.hi ? `${b.lo}` : b.hi >= 99 ? `${b.lo}+` : `${b.lo}–${b.hi}`));
    s.addChart(pres.charts.BAR, [{ name: "Huấn luyện", labels: hist, values: DS.train.ap_hist.map((b) => Math.round(1000 * b.share) / 10) }, { name: "Kiểm tra", labels: hist, values: DS.test.ap_hist.map((b) => Math.round(1000 * b.share) / 10) }],
      { ...chartBase(), x: MX + 4.4, y: 1.35, w: SW - MX - (MX + 4.4), h: 3.55, barDir: "col", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 10.5,
        valAxisMinVal: 0, valAxisMaxVal: 60, valAxisMajorUnit: 10, showLegend: true, legendPos: "b", showTitle: true, title: "% vân tay theo số AP nghe được", barGapWidthPct: 40, catAxisLabelFontSize: 11.5 });
    card(s, MX, 5.3, W, 1.55, SOFT, null, TEAL, TEAL);
    bullets(s, [`**${vn(100 * DS.train.share_not_detected, 2)}%** giá trị là 100 (không nghe thấy); trung bình **${vn(DS.train.ap_per_fp.mean, 2)}** AP/vân tay (trung vị ${DS.train.ap_per_fp.median}, tối đa ${DS.train.ap_per_fp.max}); tập kiểm tra: ${vn(DS.test.ap_per_fp.mean, 2)} AP/vân tay`,
      `**Vì sao 100 là "không nghe thấy":** tài liệu ghi vậy; không có giá trị nào trong 1…99 (khoảng trống 100 đơn vị); nếu 100 là tín hiệu thì mọi máy đều nghe gần hết 520 đài ở mức mạnh nhất, vô lý`,
      `RSSI thật nằm trong [−104, 0] dBm; ${DS.train.ap_per_fp.n_empty} vân tay huấn luyện không nghe được AP nào (tập kiểm tra: ${DS.test.ap_per_fp.n_empty})`], MX + 0.25, 5.36, W - 0.5, 1.45, 13, INK, 3);
  }

  // ---- train vs test
  {
    const s = slide("Dữ liệu · Train và test", "Tập huấn luyện và tập kiểm tra khác nhau có chủ đích",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Điều quan trọng nhất của bộ dữ liệu này là hai tập không giống nhau. Tập huấn luyện thu từ ngày 30 tháng 5 đến 20 tháng 6 năm 2013, bởi 18 người dùng với 16 điện thoại. Tập kiểm tra thu từ 19 tháng 9 đến 8 tháng 10, tức là sau ${DS.days_gap} ngày, và không có người dùng nào trùng. Chỉ có 2 trong 11 điện thoại của tập kiểm tra (máy 13 và 14) từng xuất hiện ở tập huấn luyện; ${DS.phones_unseen_in_test.length} máy còn lại hoàn toàn mới.
VÍ DỤ ĐỜI THƯỜNG: Giống như em ôn thi bằng đề của trường A rồi đi thi bằng đề của trường B vào ba tháng sau, với cây bút khác, bàn khác. Điện thoại khác nhau thu cùng một bài hát qua các micro khác nhau thì nghe to nhỏ khác nhau: máy này đọc −60 dBm, máy kia có thể đọc −70 dBm cho cùng một bộ phát. Ba tháng sau cũng có thể thay đổi cả bộ phát. Đó là lý do tập kiểm tra khó hơn.
HỆ QUẢ: Có ba hệ quả em sẽ dùng xuyên suốt. Một, tập kiểm tra khó hơn, nên con số 6,3 mét trên test không thể so trực tiếp với số trên một tập chia ngẫu nhiên. Hai, khi em tự đánh giá thử (dev), em phải giữ lại CẢ điện thoại, chứ không giữ lại vài dòng ngẫu nhiên; nếu không em sẽ báo kết quả đẹp giả tạo. Ba, có ${DS.aps.test_only} bộ phát chỉ xuất hiện ở tập kiểm tra, mô hình nào cũng không thể học được, nên đó là một trần chất lượng không ai vượt được.
NẾU BỊ HỎI: "Vì sao không chia ngẫu nhiên?" — Vì thực tế người dùng mang điện thoại mới vào tòa nhà sau vài tháng; chia ngẫu nhiên sẽ cho kết quả quá lạc quan.
CHUYỂN Ý: Bây giờ là đơn vị đo: sai số tính bằng mét thế nào.`);
    const A = DS.train, B = DS.test;
    const rows = [["Số vân tay", vn(A.rows, 0), vn(B.rows, 0), "tập kiểm tra nhỏ hơn 18 lần"],
      ["Thời gian thu", `${A.dates[0]} → ${A.dates[1]}`, `${B.dates[0]} → ${B.dates[1]}`, `cách nhau ${DS.days_gap} ngày`],
      ["Người dùng (USERID)", `${A.users.length} người`, "1 giá trị (0)", "không trùng người nào"],
      ["Điện thoại (PHONEID)", `${A.phones.length} máy`, `${B.phones.length} máy`, `trùng ${DS.phones_overlap.length} (máy ${DS.phones_overlap.join(", ")}); ${DS.phones_unseen_in_test.length} máy chưa từng thấy`],
      ["AP nghe được / vân tay", vn(A.ap_per_fp.mean, 2), vn(B.ap_per_fp.mean, 2), "tập kiểm tra thưa hơn"],
      ["AP từng nghe được", `${A.aps_ever_detected} / 520`, `${B.aps_ever_detected} / 520`, `${DS.aps.test_only} AP chỉ có ở tập kiểm tra`]];
    const yb = tb(s, ["Đặc điểm", "Tập huấn luyện", "Tập kiểm tra", "Nhận xét"], rows, MX, 1.45, W, [2.4, 2.6, 2.6, W - 7.6], { size: 12.5, minH: 0.42 });
    const cw = (W - 0.5) / 3;
    [["1. Test khó hơn dev", "Khác máy, khác người, khác thời điểm ⇒ sai số test cao hơn sai số tự đánh giá: V6 +0,65 m, V7 +0,61 m."],
      ["2. Dev phải giữ lại cả điện thoại", "Chia fold theo PHONEID để mô phỏng việc gặp máy lạ; chia ngẫu nhiên sẽ cho số đẹp giả."],
      [`3. Có trần chất lượng`, `${DS.aps.test_only} AP chỉ có ở tập kiểm tra: mọi mô hình huấn luyện trên train đều không thể khai thác được.`]].forEach((q, i) => {
      card(s, MX + i * (cw + 0.25), yb + 0.25, cw, 6.85 - yb - 0.25, i === 1 ? SOFT : i === 0 ? SOFT2 : CARD, q[0], i === 0 ? RUST : TEAL, i === 0 ? RUST : TEAL);
      text(s, q[1], MX + i * (cw + 0.25) + 0.22, yb + 0.75, cw - 0.4, 6.85 - yb - 0.85, { fontSize: 13.5 });
    });
  }

  // ---- đơn vị đo
  {
    const g = 0.766126, ex = EX.v7, dx = ex.sum_dx, dy = ex.sum_dy;
    const s = slide("Dữ liệu · Đơn vị đo", "Sai số tính bằng mét: hệ số g = 0,766126 là cos của vĩ độ",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Cột tọa độ của dữ liệu không ghi đơn vị. Em đã thử bốn hệ tọa độ giả định và chỉ có Web-Mercator, hệ dùng trong Google Maps, đặt tâm vùng dữ liệu cách khuôn viên Đại học Jaume I khoảng 139,7 mét; các hệ khác lệch hàng trăm cây số. Web-Mercator có một đặc điểm: nó kéo giãn khoảng cách theo hệ số 1 chia cos của vĩ độ. Ở vĩ độ 39,99 độ Bắc, một đơn vị tọa độ thực ra chỉ dài 0,766126 mét. Em gọi hệ số này là g.
VÍ DỤ ĐỜI THƯỜNG: Trên bản đồ thế giới kiểu Google, đảo Greenland trông to ngang châu Phi, nhưng thực tế nhỏ hơn rất nhiều. Cũng như vậy, khoảng cách đo thẳng trên tọa độ ở vĩ độ 40 độ bị phóng to lên 1,3 lần. Muốn ra mét thực thì phải nhân với 0,766.
CÔNG THỨC: Sai số của vân tay thứ n là e_n bằng g nhân căn của tổng bình phương độ lệch x và độ lệch y. Sai số trung bình là trung bình của e_n trên N bằng 1 111 vân tay kiểm tra; đây chính là con số 6,309 mét.
CÁCH TỰ KIỂM: cos 40 độ bằng 0,766044; vĩ độ thực là 39,992698 độ, nhỏ hơn 40 độ một chút (0,0073 độ) nên cos lớn hơn một chút: 0,766126. Ví dụ hàng 335: độ lệch x là ${vn(dx, 5)}, độ lệch y là ${vn(dy, 5)} đơn vị tọa độ, khoảng cách ${vn(Math.hypot(dx, dy), 5)}, nhân 0,766126 ra ${vn(ex.err_m, 4)} mét.
VÌ SAO CHỌN: Báo cáo sai số theo mét thực để con số có nghĩa vật lý và so sánh được; hệ số chỉ đổi đơn vị, không đổi thứ tự các mô hình.
CHUYỂN Ý: Tiếp theo là "ô tham chiếu" — đơn vị mà mô hình thực sự học.`);
    fcard(s, "fm_gf", MX, 1.4, 6.6, 1.35);
    fcard(s, "fm_err", MX, 2.9, 6.6, 1.15);
    const ax = MX + 6.9, aw = SW - MX - ax;
    s.addText("Chú thích ký hiệu", { x: ax, y: 1.38, w: aw, h: 0.33, fontFace: F, fontSize: 15, bold: true, color: TEAL, margin: 0, isTextBox: true });
    ann(s, [["φ", `vĩ độ nơi thu dữ liệu: ${vn(E.coord.lat_deg, 6)}° Bắc (đổi ngược từ tâm vùng dữ liệu)`], ["g", "mét thực địa trên một đơn vị tọa độ = cos φ"],
      ["(x̂_{n}, ŷ_{n})", "tọa độ dự đoán của vân tay n"], ["(x_{n}, y_{n})", "tọa độ thật (chỉ dùng để đo)"], ["e_{n}", "sai số (mét) của vân tay n"], ["N", `số vân tay kiểm tra = ${vn(DS.test.rows, 0)}`], ["ē", "sai số trung bình; đây là số 6,309 m"]], ax, 1.75, aw, 2.5, 13);
    card(s, MX, 4.25, 6.6, 2.6, SOFT, "Vì sao chọn cách này", TEAL, TEAL);
    bullets(s, ["Web-Mercator **kéo giãn độ dài 1/cos φ lần**: không nhân g thì mọi sai số bị phóng to 1,31 lần", "Thử 4 hệ tọa độ: chỉ EPSG:3857 cho tâm dữ liệu **cách khuôn viên UJI 139,7 m**; UTM-31N lệch 497 km", "Báo cáo mét thực để con số có nghĩa vật lý; g chỉ đổi đơn vị, **không đổi thứ tự** giữa các mô hình"], MX + 0.22, 4.75, 6.2, 2.05, 13.5, INK, 4);
    card(s, MX + 6.9, 4.25, aw, 2.6, SOFT2, "Tự kiểm bằng tay", RUST, RUST);
    bullets(s, ["cos 40° = 0,766044; sin 40° = 0,642788", "40° − 39,992698° = 0,0073° = 1,27·10⁻⁴ rad", "cos ≈ 0,766044 + 0,642788 × 1,27·10⁻⁴ = **0,766126**", `Hàng 335: √(${vn(dx, 4)}² + ${vn(dy, 4)}²) × g = ${vn(Math.hypot(dx, dy), 4)} × 0,766126 = **${vn(ex.err_m, 4)} m**`], MX + 7.12, 4.75, aw - 0.4, 2.05, 13, INK, 4);
  }

  // ---- ô tham chiếu
  {
    const cl = DS.cells;
    const s = slide("Dữ liệu · Ô tham chiếu", `Ô tham chiếu: ${vn(cl.n, 0)} điểm đánh dấu; mô hình không lưu vân tay`,
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Trong tập huấn luyện, những lần đo được thực hiện ở một số vị trí cố định, mỗi vị trí đo nhiều lần. Em gọi mỗi vị trí khác nhau, tính theo bộ bốn: kinh độ, vĩ độ, tầng, tòa, là một Ô. Có đúng ${vn(cl.n, 0)} ô: tòa 0 có 259 ô, tòa 1 có 265 ô, tòa 2 có 409 ô. Mỗi ô có trung bình ${vn(cl.mean_informative_fp, 2)} vân tay hữu ích (trung vị ${cl.median}, ít nhất ${cl.min}, nhiều nhất ${cl.max}). Số 21,29 tính bằng ${vn(cl.n_informative_fp, 0)} vân tay có ít nhất một AP chia cho ${cl.n} ô; bạn có thể tự kiểm.
VÍ DỤ ĐỜI THƯỜNG: Ô giống như các chiếc ghế được đánh số trong một rạp hát. Người ta không hỏi "bạn đang ở tọa độ nào" mà hỏi "bạn ngồi ghế số mấy". Mỗi ghế có hồ sơ riêng: những lần có người ngồi ở ghế đó thì nghe thấy Wi-Fi nào. Khi có một lần đo mới, em hỏi: hồ sơ của ghế nào giống lần đo này nhất?
BẢN ĐỒ: Các chấm xanh, vàng, xanh đậm là các ô trong ba tòa nhà (các tầng chồng lên nhau); các chấm cam là 1 111 vị trí thật của tập kiểm tra. Có thể thấy tập kiểm tra nằm đúng trong vùng đã khảo sát, nhưng không trùng đúng từng ô, vì vậy mô hình phải suy ra vị trí nằm giữa các ô.
QUAN TRỌNG: V7 không lưu vân tay huấn luyện. Với mỗi ô, em chỉ giữ lại các "mẫu Wi-Fi đặc trưng" (sẽ nói ở chương sau) và vị trí của ô. Không có phép so sánh vân tay với vân tay như k-NN.
KÝ HIỆU: c là một ô; D_c là tập các vân tay thuộc ô c; (x_c, y_c) là tâm ô.
CHUYỂN Ý: Còn một câu hỏi: em đánh giá hệ thống thế nào để con số 6,3 mét đáng tin?`);
    img(s, as("cells_map"), MX, 1.4, 7.3, 5.45, "left", "bản đồ 933 ô và vị trí kiểm tra");
    const x = MX + 7.6, w = SW - MX - x;
    stat(s, x, 1.4, w, `${vn(cl.n, 0)} ô`, "vị trí huấn luyện khác nhau: tòa 0: 259; tòa 1: 265; tòa 2: 409", TEAL, 32);
    stat(s, x, 2.8, w, `${vn(cl.mean_informative_fp, 2)}`, `vân tay có ≥ 1 AP trên mỗi ô (= ${vn(cl.n_informative_fp, 0)} / ${cl.n}); trung vị ${cl.median}, từ ${cl.min} đến ${cl.max}`, NAVY, 32);
    card(s, x, 4.3, w, 2.55, SOFT, "Ký hiệu và quy ước", TEAL, TEAL);
    ann(s, [["c", "một ô (một vị trí đo)"], ["D_{c}", "các vân tay huấn luyện của ô c"], ["(x_{c}, y_{c})", "tâm ô c"]], x + 0.22, 4.8, w - 0.4, 0.9, 13);
    text(s, "Mô hình chỉ giữ **mẫu AP đặc trưng của từng ô** và vị trí ô; **không lưu vân tay** và không so khớp vân tay với vân tay (không k-NN).", x + 0.22, 5.7, w - 0.4, 1.1, { fontSize: 13.5 });
  }

  // ---- đánh giá
  {
    const s = slide("Dữ liệu · Cách đánh giá", "Cách đánh giá: tự thi thử theo điện thoại, chấm test một lần",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Để biết một thiết kế tốt hay không mà không "nhìn trộm" đáp án, em chia dữ liệu huấn luyện thành 6 nhóm theo điện thoại. Mỗi lần lấy một nhóm làm "thi thử" (gọi là dev) và huấn luyện trên 5 nhóm còn lại; làm 6 lần để mỗi nhóm đều được thi thử đúng một lần. Mọi quyết định thiết kế (chọn mô hình, chọn tham số) em chỉ dựa trên điểm thi thử này. Tập kiểm tra 1 111 vân tay chỉ để chấm một lần cho mỗi biến thể đã khai báo trước.
VÍ DỤ ĐỜI THƯỜNG: Đây giống kỳ thi: có đề thi thử của các trường khác (dev theo điện thoại) và có kỳ thi chính thức (test). Học sinh chỉ được sửa cách học dựa trên điểm thi thử. Nếu cứ thấy điểm chính thức thấp lại sửa cách học thì điểm chính thức không còn khách quan nữa.
VÌ SAO THEO ĐIỆN THOẠI: Tập kiểm tra có 9 trong 11 máy chưa từng gặp. Em đã thử chia theo người dùng ở các phiên bản trước: dev ra 7,699 mét nhưng test 8,175 mét, không chuyển sang được. Sau khi chuyển sang chia theo điện thoại, dev 7,669 mét và test 7,997 mét, sát nhau hơn (ở bước đó em đổi cùng lúc cả ngưỡng θ và cách chọn lợi ích nên không tách riêng được tác dụng của riêng cách chia fold). Vì vậy em giữ cách chia theo điện thoại.
SỐ 6 FOLD: 16 điện thoại chia được thành 6 nhóm; con số 6 là quy ước đã dùng từ V3 và em giữ nguyên ở V7 để so sánh công bằng với V6; em chưa thử số fold khác. Các fold không cân bằng: hai fold đầu mỗi fold chỉ có một điện thoại (máy 14 và 13) và chiếm 46,9% số vân tay.
THÀNH THẬT: Tập kiểm tra đã được dùng từ phiên bản V1 đến V6, nên con số trên test là chỉ báo, không phải ước lượng hoàn toàn độc lập. Em xin nói rõ điều này trước khi thầy cô hỏi.
CHUYỂN Ý: Giờ em bắt đầu vào các bước thuật toán, từ vân tay đến các mẫu Wi-Fi đặc trưng.`);
    head(s, "6 fold của GroupKFold theo PHONEID (16 điện thoại huấn luyện)", MX, 1.4, 7.5);
    const f = E.folds;
    const rows = f.map((x) => [`fold ${x.fold + 1}`, x.phones.join(", "), vn(x.rows, 0), pct(x.rows / DS.train.rows, 1)]);
    const yb = tb(s, ["Fold", "Điện thoại", "Vân tay", "Tỷ lệ"], rows, MX, 1.8, 6.6, [1.1, 2.6, 1.4, 1.5], { size: 12.5, minH: 0.34, align: ["center", "left", "right", "right"] });
    const x = MX + 6.9, w = SW - MX - x;
    card(s, x, 1.4, w, 2.65, SOFT, "Quy tắc đánh giá", TEAL, TEAL);
    bullets(s, ["Mỗi fold làm **dev** một lần; mô hình HUI của fold đó **chỉ đào trên các điện thoại khác**", "Mọi quyết định chọn mô hình dựa trên **dev**", "Test chấm **một lần** cho mỗi biến thể khai báo trước, báo cả biến thể không chọn"], x + 0.22, 1.9, w - 0.4, 2.1, 13.5, INK, 4);
    card(s, x, 4.2, w, 2.65, SOFT2, "Vì sao theo điện thoại", RUST, RUST);
    bullets(s, [`Test có 11 máy, **9 chưa từng thấy**; dev phải giữ lại cả máy`, `Chia theo người dùng: dev 7,699 → test 8,175 (không chuyển); theo điện thoại: 7,669 → 7,997`, "**Trung thực:** test đã dùng từ V1–V6 nên là chỉ báo, không phải ước lượng độc lập"], x + 0.22, 4.7, w - 0.4, 2.1, 13.5, INK, 4);
    text(s, `Tổng ${vn(f.reduce((a, q) => a + q.rows, 0), 0)} vân tay. Hai fold đầu mỗi fold chỉ một điện thoại (14 và 13), chiếm ${pct((f[0].rows + f[1].rows) / DS.train.rows, 1)}: các fold **không cân bằng**. 6 là quy ước từ V3, giữ nguyên để so sánh công bằng với V6; chưa thử số fold khác.`, MX, yb + 0.15, 6.6, 6.85 - yb - 0.15, { fontSize: 13, color: INK });
  }
};
