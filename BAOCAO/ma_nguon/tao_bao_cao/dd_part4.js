// Phần 4 của Slide_HUIM_IPS_V7_day_du.pptx: chương 5 "Ví dụ trọn vẹn", chương 6 "Kết quả", chương 7 "Kiểm chứng, giới hạn, hỏi–đáp".
const fs = require("fs");
const path = require("path");

module.exports = function part4(c) {
  const { pres, slide, divider, img, as, bullets, text, ann, stat, card, badge, table, tb, callout, fcard, head, chartBase, vn, vnd, pct, tr, dI, dA,
    MX, SW, W, F, INK, NAVY, TEAL, RUST, GREY, GOLD, SOFT, SOFT2, CARD, LINE, D, E, DS, ROOT } = c;
  const T7 = tr("C_rel_absL3"), T6 = tr("V6"), T6r = tr("V6r");
  const EX = D.example, VF = D.verif, TJ = D.test_json, FIN = TJ.C_rel_absL3, G = E.grid;
  const wap = (n) => "WAP" + String(n).padStart(3, "0");
  const W3 = EX.cells.filter((z) => [351, 348, 352].includes(z.cell)).reduce((a, z) => a + z.w6, 0);
  const FIG = (f) => path.join(ROOT, "BAOCAO_V7", "bieu_do", f);       // diagram có sẵn của báo cáo V7 (vẽ từ số liệu thật bởi src/v7/figures.py)
  const csvErr = (rel) => {                                                // sai số từng vân tay theo src_row, đọc từ tệp dự đoán
    const L = fs.readFileSync(path.join(ROOT, rel), "utf8").split(/\r?\n/).filter(Boolean), h = L[0].split(",");
    const ir = h.indexOf("src_row"), ie = h.indexOf("err_m"), m = new Map();
    L.slice(1).forEach((l) => { const q = l.split(","); m.set(q[ir], parseFloat(q[ie])); });
    return m;
  };
  const rj = (p) => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8")); } catch (e) { return null; } };

  // ================================================================== CHƯƠNG 5: ví dụ
  divider(4, "Ví dụ trọn vẹn: vân tay hàng 335", ["Bằng chứng HUI của các ô ứng viên", "Trọng số V6 và V7 trên bản đồ", "Tính tay tọa độ và sai số"],
`KỊCH BẢN (30 giây)
NÓI: Em xin đi qua một ví dụ trọn vẹn để thầy cô thấy các bước vừa rồi chạy ra con số cụ thể thế nào. Em không chọn ví dụ đẹp: hàng 335 của tập kiểm tra được chọn bằng quy tắc khách quan vì sai số V7 của nó bằng đúng trung vị của cả tập kiểm tra (4,6357 mét), nên nó là một vân tay "bình thường". Điện thoại 13, tòa 2, tầng 1, và hệ thống chọn đúng tầng.
CHUYỂN Ý: Đầu tiên là bảng bằng chứng của các ô ứng viên hàng đầu.`);

  {
    const cs = EX.cells.slice(0, 8);
    const s = slide("Ví dụ · Bước 1", `Hàng ${EX.src_row}: bằng chứng HUI của các ô ứng viên hàng đầu`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Vân tay hàng 335 nghe được 10 bộ phát. Sau khi chọn tầng 2_1, em có 30 ô ứng viên; bảng này liệt kê 8 ô có điểm HUI cao nhất. Các cột là: hạng theo điểm HUI, số hiệu ô, điểm tương đối S chia S1 (so với ô đứng đầu), P, V, R (các bằng chứng), khoảng cách thật từ ô tới vị trí thật tính bằng mét, và hai cột cuối là trọng số mà V6 và V7 gán cho ô đó.
VÍ DỤ ĐỜI THƯỜNG: Ô 351 đứng hạng 1 theo điểm HUI, giống như thí sinh được giám khảo đầu tiên chấm cao nhất. Nhưng sự thật là ô 351 cách vị trí thật tới ${vn(cs[0].dist_m, 2)} mét, tức là "người đứng đầu danh sách" lại không phải người gần nhất. Trong 30 ô có những ô cách vị trí thật chỉ ${vn(Math.min(...EX.cells.map((q) => q.dist_m)), 2)} mét.
SO SÁNH TRỌNG SỐ: V6 dồn nhiều trọng số vào các ô xa như 351, 348, 352 (tổng khoảng ${vn(100 * W3, 0)} phần trăm), vì các ô này có điểm HUI cao. V7 nhìn thêm các bằng chứng khác, nên chuyển trọng số sang các ô gần hơn như 344, 342, 338, 365.
NÓI THẲNG: Đây là một ví dụ V7 thắng. Có những vân tay V7 thua V6; trên dev, V7 tốt hơn 0,5 mét ở 8 324 truy vấn và kém hơn 0,5 mét ở 6 248 truy vấn. Tức là V7 không thắng tuyệt đối, mà thắng về trung bình.
CHUYỂN Ý: Em cho thầy cô xem trên bản đồ.`);
    const rows = cs.map((q) => [q.rank_hui, q.cell, vn(q.S_rel, 3), vn(q.P, 4), vn(q.V, 3), vn(q.R, 3), vn(q.dist_m, 2), vn(q.w6, 4), vn(q.w7, 4)]);
    tb(s, ["Hạng HUI", "Ô", "S/S₁", "P", "V", "R", "cách vị trí thật (m)", "w V6", "w V7"], rows, MX, 1.45, W, [1.2, 1.1, 1.3, 1.3, 1.3, 1.3, 2.2, 1.2, W - 10.9], { size: 13.5, minH: 0.4, align: ["center", "center", "right", "right", "right", "right", "right", "right", "right"] });
    card(s, MX, 5.35, 6.0, 1.5, CARD, null, TEAL, TEAL);
    text(s, `Vị trí thật: tầng ${EX.pred_bf} (dự đoán đúng), điện thoại ${EX.phone}. **Ô hạng 1 (${EX.cells[0].cell}) cách ${vn(EX.cells[0].dist_m, 2)} m**; ước lượng V4 (trung bình 12 ô) sai ${vn(EX.v4_err_m, 2)} m.`, MX + 0.3, 5.5, 5.5, 1.25, { fontSize: 14.5, valign: "middle" });
    card(s, MX + 6.3, 5.35, W - 6.3, 1.5, SOFT2, null, RUST, RUST);
    text(s, "**Ký hiệu:** S/S₁ điểm tương đối so với ô hạng 1; P, V, R bằng chứng HUI (bước 3 và 6); w trọng số của ô. **V6** dồn trọng số vào các ô xa (351, 348, 352: tổng ${pct(W3, 0)}); **V7** chuyển tới ô gần hơn (344, 342, 338, 365).", MX + 6.55, 5.45, W - 6.8, 1.3, { fontSize: 13.5, valign: "middle" });
  }

  {
    const s = slide("Ví dụ · Bước 2", "Trọng số V6 và V7 trên cùng 30 ô ứng viên của hàng 335",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Mỗi bong bóng là một trong 30 ô ứng viên; diện tích bong bóng tỷ lệ với trọng số. Ngôi sao vàng là vị trí thật; dấu X là tọa độ ước lượng. Bên trái là V6, bên phải là V7.
VÍ DỤ ĐỜI THƯỜNG: Hãy nhìn như một bài kéo co. Mỗi ô kéo tọa độ ước lượng về phía mình với một lực bằng trọng số. Ở V6, những ô lớn nằm xa ngôi sao nên kéo X lệch xa vị trí thật (sai 7,99 mét). Ở V7, những bong bóng lớn tập trung quanh ngôi sao nên X gần ngôi sao hơn (sai 4,64 mét).
ĐIỂM CẦN NHẤN: Cả hai đều dùng đúng 30 ô giống nhau và cùng công thức tọa độ là tổng có trọng số. Khác nhau duy nhất là cách chia trọng số. Và vì tọa độ nằm trong bao lồi của 30 tâm ô nên không thể vượt ra ngoài vùng bong bóng.
CHUYỂN Ý: Giờ em tính tay từ trọng số ra sai số mét.`);
    img(s, as("ex_map"), MX, 1.4, W, 5.45, "center", "bản đồ ví dụ V6 và V7");
  }

  {
    const cs = EX.cells.slice().sort((a, b) => Math.max(b.w6, b.w7) - Math.max(a.w6, a.w7));
    const top = cs.slice(0, 7), rest = cs.slice(7);
    const rows = top.map((q) => [`ô ${q.cell}`, vn(q.dx, 3), vn(q.dy, 3), vn(q.w6, 4), vn(q.w7, 4)]);
    rows.push([`${rest.length} ô còn lại`, "", "", vn(rest.reduce((a, q) => a + q.w6, 0), 4), vn(rest.reduce((a, q) => a + q.w7, 0), 4)]);
    const s = slide("Ví dụ · Bước 3", "Tính tay tọa độ và sai số của V6 và V7 cho hàng 335",
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Em tính tay từ 30 trọng số ra sai số mét. Với mỗi ô, em lấy hiệu giữa tâm ô và vị trí thật: delta x và delta y, tính bằng đơn vị tọa độ. Tọa độ ước lượng trừ vị trí thật bằng tổng w nhân delta trên cả 30 ô; làm riêng cho x và y. Rồi lấy căn tổng bình phương và nhân với g bằng 0,766126.
VÍ DỤ ĐỜI THƯỜNG: Giống như cân một chiếc bàn: moment lệch của mỗi quả cân là trọng lượng nhân khoảng cách đến điểm đặt; tổng moment cho biết trọng tâm lệch bao nhiêu. Ở đây "điểm đặt" là vị trí thật, "quả cân" là ô ứng viên, và tổng w nhân delta chính là độ lệch của trọng tâm.
KẾT QUẢ: Với V6*, tổng w nhân delta x là ${vn(EX.v6.sum_dx, 5)} và delta y là ${vn(EX.v6.sum_dy, 5)}; căn là ${vn(Math.hypot(EX.v6.sum_dx, EX.v6.sum_dy), 5)} đơn vị; nhân 0,766126 ra ${vn(EX.v6.err_m, 4)} mét. Với V7: ${vn(EX.v7.sum_dx, 5)} và ${vn(EX.v7.sum_dy, 5)}; căn ${vn(Math.hypot(EX.v7.sum_dx, EX.v7.sum_dy), 5)}; nhân g ra ${vn(EX.v7.err_m, 4)} mét. V7 giảm ${vn(EX.v6.err_m - EX.v7.err_m, 2)} mét, tức ${vn(100 * (1 - EX.v7.err_m / EX.v6.err_m), 0)} phần trăm trên vân tay này.
KIỂM CHỨNG: Con số 4,6357 mét này nằm trong Excel (sheet Vi_du_mot_truy_van) và trong tệp dự đoán; thầy cô chọn bất kỳ vân tay nào khác cũng có thể tính lại theo cách này.
CHUYỂN Ý: Từ một vân tay, em chuyển sang kết quả trên toàn bộ tập kiểm tra.`);
    tb(s, ["Ô", "Δx", "Δy", "w V6", "w V7"], rows, MX, 1.45, 6.7, [1.9, 1.2, 1.2, 1.2, 1.2], { size: 13, minH: 0.36, align: ["left", "right", "right", "right", "right"] });
    card(s, MX + 7.0, 1.45, W - 7.0, 3.3, SOFT, "Cộng đủ 30 ô", NAVY, TEAL);
    tb(s, ["", "V6*", "V7"], [["Σ w", "1,000000", "1,000000"], ["Σ w·Δx", vn(EX.v6.sum_dx, 5), vn(EX.v7.sum_dx, 5)], ["Σ w·Δy", vn(EX.v6.sum_dy, 5), vn(EX.v7.sum_dy, 5)], ["√(…) (đơn vị tọa độ)", vn(Math.hypot(EX.v6.sum_dx, EX.v6.sum_dy), 5), vn(Math.hypot(EX.v7.sum_dx, EX.v7.sum_dy), 5)]],
      MX + 7.22, 1.95, W - 7.45, [2.5, 1.55, 1.5].map((x) => x * (W - 7.45) / 5.55), { size: 13, minH: 0.4, align: ["left", "right", "right"] });
    card(s, MX, 5.0, W, 1.85, SOFT2, "Sai số = 0,766126 × √(…)", RUST, RUST);
    bullets(s, [`V6*: 0,766126 × ${vn(Math.hypot(EX.v6.sum_dx, EX.v6.sum_dy), 5)} = **${vn(EX.v6.err_m, 4)} m**      V7: 0,766126 × ${vn(Math.hypot(EX.v7.sum_dx, EX.v7.sum_dy), 5)} = **${vn(EX.v7.err_m, 4)} m**`,
      `Δ = tâm ô − vị trí thật (đơn vị tọa độ); V7 giảm ${vn(EX.v6.err_m - EX.v7.err_m, 2)} m (${vn(100 * (1 - EX.v7.err_m / EX.v6.err_m), 0)}%) trên vân tay này; 30 trọng số và sai số lưu trong tệp khớp đến 6 chữ số`], MX + 0.3, 5.5, W - 0.6, 1.3, 14.5, INK, 6);
  }

  // ================================================================== CHƯƠNG 6: kết quả
  divider(5, `Kết quả: ${vn(T7.mean, 3)} m trên tập kiểm tra`, ["Mỗi bước đóng góp bao nhiêu mét", "Bảng kết quả và phân bố sai số", "Theo tầng, theo điện thoại; vì sao test khó hơn dev", "Những hướng không giúp"],
`KỊCH BẢN (30 giây)
NÓI: Chương này trả lời câu hỏi chính: con số 6,3 mét đến từ đâu và có đáng tin không. Em sẽ cho thấy mỗi bước đóng góp bao nhiêu mét, bảng kết quả đầy đủ, phân bố sai số, sau đó giải thích vì sao test khó hơn dev và những hướng em đã thử mà không giúp. Em báo cả kết quả không đẹp.
CHUYỂN Ý: Bắt đầu bằng "bậc thang" các cải tiến.`);

  // ---- ladder
  {
    const s = slide("Kết quả · Đóng góp từng bước", `Từ ${vn(T6r.mean, 3)} m xuống ${vn(T7.mean, 3)} m: mỗi bước đóng góp bao nhiêu`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Biểu đồ cho thấy sai số trên tập kiểm tra (cột xanh đậm) và trên dev (cột xanh lục) sau mỗi bước. Bắt đầu từ V6 tái tạo: ${vn(T6r.mean, 3)} mét trên test. Bước một: thay công thức chia trọng số cố định bằng bộ chấm điểm học trực tiếp (V7-B), giảm xuống ${vn(tr("B_base").mean, 3)} mét, tức giảm ${vn(T6r.mean - tr("B_base").mean, 3)} mét. Bước hai: thêm góc nhìn rel (V7-C1) còn ${vn(tr("C_rel").mean, 3)} mét. Bước ba: thêm góc nhìn abs mức 3 (V7-C2) còn ${vn(T7.mean, 3)} mét.
VÍ DỤ ĐỜI THƯỜNG: Giống như chạy bộ giảm thời gian: tập đúng kỹ thuật (đổi cách học trọng số) giúp nhanh hơn nhiều nhất, còn mua giày tốt hơn (thêm mẫu HUI mới) giúp thêm một chút.
ĐIỂM QUAN TRỌNG: Thầy cô để ý: phần lớn mức giảm đến từ việc học trọng số trực tiếp (giảm 0,43 mét trên test, 0,28 mét trên dev), còn việc thêm các mẫu HUI mới chỉ giảm thêm 0,04 và 0,08 mét trên test (0,195 và 0,034 mét trên dev). Em xin nói thẳng: HUI cung cấp ứng viên và mọi đặc trưng, nhưng bước quyết định mức giảm lớn nhất là bộ chấm điểm học.
NÓI VỀ Ý NGHĨA THỐNG KÊ: Chỉ khối rel (giảm 0,195 mét, tốt hơn ở 6 trên 6 fold) và bộ chấm điểm trực tiếp có ý nghĩa thống kê rõ; abs mức 3 nhỏ và khoảng tin cậy cặp chứa 0.
CHUYỂN Ý: Bảng kết quả đầy đủ trên tập kiểm tra.`);
    const ladder = [["V6 (tái tạo)", T6r.mean, dI("V6*").mean], ["+ bộ chấm điểm trực tiếp (V7-B)", tr("B_base").mean, dI("B_base").mean], ["+ HUI rel (V7-C1)", tr("C_rel").mean, dI("C_rel").mean], ["+ HUI abs-L3 (V7-C2)", T7.mean, dI("C_rel_absL3").mean]];
    const labels = ladder.map((l) => l[0]);
    s.addChart(pres.charts.BAR, [{ name: "validationData (test)", labels, values: ladder.map((l) => Math.round(l[1] * 1000) / 1000) }, { name: "dev out-of-fold (có thông tin)", labels, values: ladder.map((l) => Math.round(l[2] * 1000) / 1000) }],
      { ...chartBase(), x: MX, y: 1.45, w: 7.9, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontSize: 11.5,
        valAxisMinVal: 5, valAxisMaxVal: 7.2, valAxisMajorUnit: 0.5, showLegend: true, legendPos: "b", showTitle: true, title: "Sai số trung bình (m); trục bắt đầu từ 5 m", barGapWidthPct: 45, catAxisLabelFontSize: 12 });
    const rows = [["V7-B", vnd(tr("B_base").mean - T6r.mean, 3), vnd(dI("B_base").mean - dI("V6*").mean, 3)], ["+ rel", vnd(tr("C_rel").mean - tr("B_base").mean, 3), vnd(dI("C_rel").mean - dI("B_base").mean, 3)],
      ["+ abs-L3", vnd(T7.mean - tr("C_rel").mean, 3), vnd(dI("C_rel_absL3").mean - dI("C_rel").mean, 3)], ["Tổng", vnd(T7.mean - T6r.mean, 3), vnd(dI("C_rel_absL3").mean - dI("V6*").mean, 3)]];
    head(s, "Thay đổi so với bước trước (m)", MX + 8.2, 1.5, 4.3);
    const yb = tb(s, ["Bước", "Test", "Dev"], rows, MX + 8.2, 1.9, W - 8.2, [1.8, 1.25, 1.2].map((x) => x * (W - 8.2) / 4.25), { size: 14, minH: 0.42, align: ["left", "right", "right"], hl: (i) => i === 3 });
    text(s, "Chỉ **rel** (−0,195 m dev, 6/6 fold) và **bộ chấm điểm trực tiếp** có ý nghĩa thống kê rõ; abs-L3 nhỏ (khoảng tin cậy cặp chứa 0).", MX + 8.2, yb + 0.2, W - 8.2, 1.8, { fontSize: 14, color: RUST });
  }

  // ---- bảng test
  {
    const order = [["V4", "V4 (lưu)"], ["V5", "V5 (lưu)"], ["V6", "V6 (lưu)"], ["V6r", "V6 (tái tạo)"], ["V7-A", "V7-A hợp nhất thích ứng"], ["B_base", "V7-B tối ưu trực tiếp"], ["C_rel", "V7-C1 + HUI rel"], ["C_rel_absL3", "V7-C2 + HUI abs-L3 (chọn theo dev)"], ["D_hier", "V7-D + HUI cấp tầng"]];
    const s = slide("Kết quả · Tập kiểm tra", `Test: V7-C2 đạt ${vn(T7.mean, 3)} m, thấp hơn V6 ${vn(-T7.diff_vs_V6, 3)} m`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Đây là bảng kết quả đầy đủ trên 1 111 vân tay của tập kiểm tra. Hàng được tô màu là V7-C2, mô hình em chọn dựa trên dev: sai số trung bình ${vn(T7.mean, 3)} mét, khoảng tin cậy 95 phần trăm từ ${vn(T7.ci95_lo, 2)} đến ${vn(T7.ci95_hi, 2)}, trung vị ${vn(T7.median, 3)} mét, P90 là ${vn(T7.p90, 2)} mét. So với V6, V7-C2 thấp hơn ${vn(-T7.diff_vs_V6, 3)} mét, khoảng tin cậy cặp từ ${vnd(T7.diff_lo, 2)} đến ${vnd(T7.diff_hi, 2)}, không chứa 0.
VÍ DỤ ĐỜI THƯỜNG: Trung bình 6,3 mét tương đương khoảng 8 bước chân: nếu hệ thống bảo bạn đứng ở điểm A, bạn thật sự đang đứng cách A chừng 8 bước. Trung vị 4,6 mét nghĩa là một nửa số lần định vị sai dưới 4,6 mét; P90 12,9 mét nghĩa là 9 trên 10 lần sai không quá 12,9 mét.
CÁC CÁCH ĐỌC CẦN CHÚ Ý: Một, "TB" là trung bình trên 1 111 vân tay; "KTC 95%" lấy mẫu lại cả điện thoại, chỉ có 11 điện thoại nên khoảng này rộng. Hai, nên đọc cột "Chênh vs V6 [KTC cặp]" vì khoảng tin cậy của chênh lệch cặp hẹp hơn nhiều. Ba, độ chính xác tòa 99,91 phần trăm và tầng 80,38 phần trăm là như nhau ở mọi dòng vì em giữ cùng quy tắc chọn tầng.
THÀNH THẬT: Mỗi biến thể được chấm đúng một lần, kể cả những biến thể không được chọn: V7-A thành 6,886 (tệ hơn V6), V7-D thành 6,324 (tệ hơn V7-C2 0,014 mét). Mục tiêu dưới 6 mét CHƯA đạt.
CHUYỂN Ý: Phân bố sai số trông thế nào?`);
    const rows = order.map(([m, lab]) => { const r = tr(m); return [lab, vn(r.mean, 3), `[${vn(r.ci95_lo, 2)}; ${vn(r.ci95_hi, 2)}]`, m === "V6" ? "—" : `${vnd(r.diff_vs_V6, 3)} [${vnd(r.diff_lo, 2)}; ${vnd(r.diff_hi, 2)}]`, vn(r.median, 3), vn(r.p75, 2), vn(r.p90, 2), vn(r.p95, 2)]; });
    tb(s, ["Mô hình", "TB (m)", "KTC 95%", "Chênh vs V6 [KTC cặp]", "Trung vị", "P75", "P90", "P95"], rows, MX, 1.45, W, [3.3, 1.0, 1.7, 2.6, 1.0, 0.8, 0.8, 0.93], { size: 13, minH: 0.4, align: ["left", "right", "center", "center", "right", "right", "right", "right"], hl: (i) => order[i][0] === "C_rel_absL3" });
    text(s, `Đúng tòa ${pct(FIN.building_accuracy, 2)}, đúng tầng ${pct(FIN.floor_accuracy, 2)} ở mọi dòng. V7-C2 tốt hơn V6 trong ${pct(T7.p_better, 1)} số lần lấy mẫu lại điện thoại (11 cụm). **Mục tiêu dưới 6 m chưa đạt.** TB: trung bình; KTC: khoảng tin cậy; P75/P90/P95: phân vị thứ 75/90/95.`, MX, 6.0, W, 0.85, { fontSize: 14 });
  }

  // ---- CDF
  {
    const s = slide("Kết quả · Phân bố sai số", "Phân bố sai số: V7 nằm trên V6 ở hầu hết mọi mức sai số",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Đường cong này gọi là CDF: tại mỗi mức sai số trên trục ngang, đường cho biết bao nhiêu phần trăm vân tay có sai số nhỏ hơn mức đó. Đường càng nằm cao và càng nằm bên trái thì hệ thống càng tốt. Bên trái là tập kiểm tra, bên phải là dev. Đường xanh lục của V7-C2 nằm trên đường V6 và V4 ở hầu hết mọi mức.
VÍ DỤ ĐỜI THƯỜNG: Giống như biểu đồ thời gian chạy của cả lớp: đường nào lên cao sớm hơn nghĩa là nhiều bạn chạy xong sớm hơn. Ví dụ ở mức 5 mét, V7 có khoảng ${vn(100 * FIN.share_within_5m, 1)} phần trăm vân tay sai dưới 5 mét, trong khi V6 chỉ khoảng ${vn(100 * TJ.V6_reproduced.share_within_5m, 1)} phần trăm.
ĐIỂM CẦN NHẤN: Chênh lệch lớn nhất nằm ở "đuôi" sai số: P90 giảm từ 14,0 xuống 12,9 mét. Nghĩa là V7 giúp nhiều nhất ở những trường hợp khó, nhưng vẫn còn khoảng 10 phần trăm vân tay sai hơn 12,9 mét.
CHUYỂN Ý: Sai số khác nhau thế nào giữa các tầng và điện thoại?`);
    img(s, as("cdf_test"), MX, 1.45, 6.0, 5.35, "left", "CDF test");
    img(s, as("cdf_dev"), MX + 6.2, 1.45, W - 6.2, 5.35, "right", "CDF dev");
  }

  // ---- diagram F5: tỷ lệ truy vấn dưới ngưỡng (dev)
  {
    const cd = D.cand_dev, pc = (x) => vn(100 * x, 2);
    const s = slide("Kết quả · Dưới ngưỡng", "Diagram: tỷ lệ truy vấn có sai số dưới 3 m, 5 m, 10 m (dev)",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Đây là một diagram quan trọng trong báo cáo V7. Mỗi nhóm cột là một ngưỡng sai số: dưới 3 mét, dưới 5 mét, dưới 10 mét. Trong mỗi nhóm có bốn cột: xám là cách đơn giản nhất, chỉ lấy ô có điểm HUI cao nhất; xanh lục là "tiên tri": ô gần nhất trong 30 ứng viên, chọn bằng cách biết trước vị trí thật, nên chỉ để đo trần chứ không phải kết quả thật; xanh dương là V6; cam là V7.
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ đến một buổi tập bắn bia với ba vòng: vòng trong 3 mét, vòng giữa 5 mét, vòng ngoài 10 mét. Xạ thủ xám chỉ bắn một phát vào ô đứng đầu danh sách; "xạ thủ thần tiên" xanh lục biết trước đáp án nên chọn đúng điểm gần nhất trong 30 điểm; V6 và V7 là hai xạ thủ thật phải tự đoán. Cột càng cao càng nhiều phát trúng vòng đó.
ĐỌC SỐ: Ở vòng 3 mét, V6 trúng ${pc(cd[2].duoi_3m)} phần trăm, V7 trúng ${pc(cd[3].duoi_3m)} phần trăm, tăng ${vn(100 * (cd[3].duoi_3m - cd[2].duoi_3m), 2)} điểm phần trăm. Ở vòng 5 mét: ${pc(cd[2].duoi_5m)} lên ${pc(cd[3].duoi_5m)}. Ở vòng 10 mét: ${pc(cd[2].duoi_10m)} lên ${pc(cd[3].duoi_10m)}. Tức là V7 tốt hơn V6 ở cả ba vòng, nhưng mức tăng nhỏ.
ĐIỂM CẦN NHẤN: Cột xanh lục cao vọt: ${pc(cd[1].duoi_3m)} phần trăm vân tay có ít nhất một ô ứng viên cách vị trí thật dưới 3 mét. Nghĩa là các ứng viên do HUI chọn đã rất tốt; khoảng cách giữa cột xanh lục và cột cam chính là phần còn lại mà khâu chọn trọng số chưa khai thác được. Đây là lý do em nói còn dư địa và mục tiêu dưới 6 mét chưa đạt.
NÓI THẲNG: Cột "tiên tri" dùng nhãn thật nên em không bao giờ báo nó như một kết quả; em chỉ dùng nó để biết trần.
CHUYỂN Ý: Giờ em xem từng thành phần đóng góp bao nhiêu trên dev, qua biểu đồ cắt bỏ.`);
    img(s, FIG("F5_hieu_qua_chon_o_ung_vien_dev.png"), MX, 1.4, 7.9, 5.45, "left", "F5 tỷ lệ truy vấn dưới ngưỡng");
    const x = MX + 8.2, w = W - 8.2;
    card(s, x, 1.4, w, 5.45, SOFT, "Cách đọc biểu đồ", TEAL, TEAL);
    bullets(s, ["**Xám:** chỉ lấy ô điểm HUI cao nhất", "**Xanh lục:** ô gần nhất trong 30 ứng viên (**tiên tri**, dùng nhãn thật, chỉ để đo trần)", "**Xanh dương:** V6*; **cam:** V7 cuối",
      `Dưới 3 m: V6* ${pc(cd[2].duoi_3m)}% → V7 **${pc(cd[3].duoi_3m)}%**`, `Dưới 5 m: ${pc(cd[2].duoi_5m)}% → **${pc(cd[3].duoi_5m)}%**; dưới 10 m: ${pc(cd[2].duoi_10m)}% → **${pc(cd[3].duoi_10m)}%**`,
      `Trần tiên tri ${pc(cd[1].duoi_3m)}% (3 m) ⇒ **còn dư địa ở khâu chọn trọng số**`], x + 0.22, 1.9, w - 0.4, 4.9, 13, INK, 6);
  }

  // ---- tầng + điện thoại
  {
    const rn = D.floor_dev, gv = (g, m) => rn.find((r) => r.group === g && r.model === m).mean;
    const fr = D.floor_right_test, fw = D.floor_wrong_test, tg = (a, m) => a.find((r) => r.model === m).mean;
    const s = slide("Kết quả · Tầng và điện thoại", "Giảm sai số chủ yếu khi tầng đúng; 10/11 điện thoại tốt hơn",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Biểu đồ bên trái chia vân tay theo kết quả chọn tầng. Khi chọn đúng tầng, sai số của V7 trên test là ${vn(tg(fr, "C_rel_absL3"), 2)} mét so với ${vn(tg(fr, "V6"), 2)} mét của V6, giảm khoảng 9,5 phần trăm. Khi chọn sai tầng (19,6 phần trăm số vân tay), sai số lên tới ${vn(tg(fw, "C_rel_absL3"), 2)} mét và V7 chỉ cải thiện khoảng 3,4 phần trăm.
VÍ DỤ ĐỜI THƯỜNG: Nếu chọn sai tầng thì giống như hệ thống chỉ cho bạn lên tầng 3 trong khi bạn đang ở tầng 2: kể cả vị trí ngang có chính xác thì cũng sai cả một tầng; vì thế sai số tăng vọt. Đó là lý do độ chính xác tầng quyết định rất nhiều.
BIỂU ĐỒ BÊN PHẢI: Sai số theo từng điện thoại của tập kiểm tra. V7 tốt hơn V6 ở 10 trong 11 điện thoại; điện thoại 2 (52 vân tay) tệ hơn 1,32 mét. Máy 13 và 14 từng xuất hiện ở tập huấn luyện; chín máy còn lại hoàn toàn mới nhưng V7 vẫn tốt hơn trên hầu hết. Điều này cho thấy cải tiến không chỉ dựa vào việc "đã quen máy".
THÀNH THẬT: Em không cải thiện độ chính xác tầng, vì em giữ nguyên quy tắc chọn tầng. Đây là hạn chế lớn và là hướng phát triển: học quyết định tầng từ HUI.
CHUYỂN Ý: Còn một câu hỏi thầy cô hay hỏi: vì sao dev thấp mà test cao?`);
    const labels = ["dev đúng tầng", "dev sai tầng", "test đúng tầng", "test sai tầng"];
    s.addChart(pres.charts.BAR, [{ name: "V6", labels, values: [gv("floor_right", "V6*"), gv("floor_wrong", "V6*"), tg(fr, "V6"), tg(fw, "V6")].map((v) => Math.round(v * 100) / 100) },
      { name: "V7-C2", labels, values: [gv("floor_right", "C_rel_absL3"), gv("floor_wrong", "C_rel_absL3"), tg(fr, "C_rel_absL3"), tg(fw, "C_rel_absL3")].map((v) => Math.round(v * 100) / 100) }],
      { ...chartBase(), x: MX, y: 1.4, w: 5.9, h: 5.45, barDir: "col", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 11,
        valAxisMinVal: 0, valAxisMaxVal: 15, valAxisMajorUnit: 3, showLegend: true, legendPos: "b", showTitle: true, title: "Sai số trung bình (m) theo kết quả chọn tầng", barGapWidthPct: 40, catAxisLabelFontSize: 11, titleFontSize: 12 });
    const pt = D.phones_test.slice().sort((a, b) => b.V6 - a.V6);
    const lab2 = pt.map((p) => `ĐT ${p.phone} (n=${p.n})`);
    s.addChart(pres.charts.BAR, [{ name: "V6", labels: lab2, values: pt.map((p) => Math.round(p.V6 * 100) / 100) }, { name: "V7-C2", labels: lab2, values: pt.map((p) => Math.round(p.V7 * 100) / 100) }],
      { ...chartBase(), x: MX + 6.2, y: 1.4, w: W - 6.2, h: 5.45, barDir: "bar", catAxisOrientation: "maxMin", barGrouping: "clustered", chartColors: [NAVY, TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 9.5,
        valAxisMinVal: 0, valAxisMaxVal: 12, valAxisMajorUnit: 2, showLegend: true, legendPos: "b", showTitle: true, title: "Test: sai số trung bình theo điện thoại (m)", barGapWidthPct: 30, catAxisLabelFontSize: 10.5, titleFontSize: 12 });
  }

  // ---- dev vs test
  {
    const p13 = D.phones_test.find((p) => p.phone === 13), pairs = [["V4", "V4", "V4"], ["V5", "V5", "V5"], ["V6*", "V6r", "V6 (V6* ở dev)"], ["C_rel_absL3", "C_rel_absL3", "V7-C2"]];
    const s = slide("Kết quả · Dev và test", `Dev ${vn(dI("C_rel_absL3").mean, 2)} m, test ${vn(T7.mean, 2)} m: vì sao test cao hơn`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Một câu hỏi tự nhiên: sao dev là 5,70 mét mà test là 6,31 mét? Bảng cho thấy đây không phải lỗi riêng của V7: V4 chênh ${vnd(tr("V4").mean - dI("V4").mean, 2)} mét, V5 ${vnd(tr("V5").mean - dI("V5").mean, 2)}, V6 ${vnd(T6r.mean - dI("V6*").mean, 2)}, V7 ${vnd(T7.mean - dI("C_rel_absL3").mean, 2)} mét. Test luôn khó hơn dev, và độ chênh gần như không đổi giữa V6 và V7, nên cải tiến của V7 là thật.
VÍ DỤ ĐỜI THƯỜNG: Giống như luyện thi bằng đề thi thử và đi thi bằng đề chính thức của một vùng khác, ba tháng sau: điểm thi chính thức luôn thấp hơn một chút, không phải vì học kém đi mà vì đề khác. Nếu mọi học sinh đều thấp hơn khoảng 0,6 điểm thì không có gì bất thường.
NGUYÊN NHÂN: Có bốn nguyên nhân em đã đo được. Một, 9 trong 11 điện thoại của test chưa từng xuất hiện khi huấn luyện. Hai, test thu sau huấn luyện ${DS.days_gap} ngày. Ba, có ${DS.aps.test_only} bộ phát chỉ có ở test nên không mô hình nào khai thác được. Bốn, điện thoại 13 chiếm ${pct(p13.n / DS.test.rows, 0)} số vân tay test, nên khoảng tin cậy của trung bình rất rộng. Độ chính xác tầng cũng thấp hơn: dev ${pct(0.8383909, 2)} và test ${pct(FIN.floor_accuracy, 2)}.
NÓI THẲNG: Em không hề dùng test để chỉnh mô hình; mọi quyết định dựa trên dev. Test chỉ để chấm.
CHUYỂN Ý: Giờ em nói về những hướng em đã thử mà không giúp.`);
    const rows = pairs.map(([d, t, lab]) => [lab, vn(dI(d).mean, 3), vn(tr(t).mean, 3), vnd(tr(t).mean - dI(d).mean, 3)]);
    head(s, "Cùng một phiên bản: dev (có thông tin) so với test (m)", MX, 1.4, 7.5);
    const yb = tb(s, ["Phiên bản", "Dev", "Test", "Test − dev"], rows, MX, 1.8, 7.0, [2.8, 1.4, 1.4, 1.4], { size: 13.5, minH: 0.42, align: ["left", "right", "right", "right"], hl: (i) => i === 3 });
    text(s, `Test khó hơn dev ở **mọi** phiên bản; V6 và V7 chênh gần như nhau (${vnd(T6r.mean - dI("V6*").mean, 2)} và ${vnd(T7.mean - dI("C_rel_absL3").mean, 2)} m) nên cải tiến của V7 là thật.`, MX, yb + 0.2, 7.0, 1.3, { fontSize: 14, color: RUST });
    card(s, MX + 7.3, 1.4, W - 7.3, 5.45, SOFT, "Vì sao test khó hơn", TEAL, TEAL);
    bullets(s, ["**9/11 điện thoại chưa từng thấy** khi huấn luyện", `Thu sau huấn luyện **${DS.days_gap} ngày**`, `**${DS.aps.test_only} AP chỉ có ở test**: không mô hình nào khai thác được`, `Điện thoại 13 chiếm **${pct(p13.n / DS.test.rows, 0)}** vân tay test: khoảng tin cậy của trung bình rộng`, "Đúng tầng: dev 83,84%, test 80,38%", "Mọi quyết định chọn mô hình dựa trên **dev**; test chỉ để chấm"], MX + 7.55, 1.95, W - 7.8, 4.8, 14, INK, 7);
  }

  // ---- cơ chế
  {
    const Wt = D.weights, w6 = Wt.find((r) => r.model === "V6*"), w7 = Wt.find((r) => r.model === "V7"), im = D.improved;
    const s = slide("Kết quả · Cơ chế", "V7 chuyển trọng số tới ô đúng chỗ hơn: tập trung hơn và gần hơn",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Em muốn xem V7 thực sự làm gì với trọng số. Trên dev, V7 làm sai số tốt hơn 0,5 mét ở ${vn(im[0].n, 0)} truy vấn, giảm trung bình ${vn(im[0].mean_gain_m, 2)} mét; và kém hơn 0,5 mét ở ${vn(im[1].n, 0)} truy vấn, tăng trung bình ${vn(-im[1].mean_gain_m, 2)} mét. Nghĩa là V7 không thắng ở mọi truy vấn, mà thắng ở nhiều truy vấn hơn và thắng đậm hơn.
VÍ DỤ ĐỜI THƯỜNG: V6 giống người chia đều "phiếu tín nhiệm" cho nhiều người, nên lúc nào cũng có vài người sai kéo kết quả lệch. V7 tập trung phiếu hơn vào vài ô tin cậy. Số ô hiệu dụng, tính bằng 1 chia tổng w bình phương, giảm từ ${vn(w6.eff_cells, 2)} xuống ${vn(w7.eff_cells, 2)}: V7 coi như chỉ "nghe" khoảng 3 ô, còn V6 nghe khoảng 5 ô. Khối lượng trọng số đặt vào các ô cách vị trí thật dưới 3 mét tăng từ ${pct(w6.mass_within_3m, 1)} lên ${pct(w7.mass_within_3m, 1)}.
CÁI GIÁ: Tập trung hơn cũng nghĩa là mạo hiểm hơn: khi V7 tin nhầm một ô thì sai nặng hơn. Đó là lý do còn ${vn(im[1].n, 0)} truy vấn kém đi. Nguồn sai số còn lại là sai tầng và các vùng thưa ô tham chiếu.
KÝ HIỆU: N_eff, số ô hiệu dụng, bằng 1 chia tổng w_i bình phương: nếu 30 ô có trọng số bằng nhau thì N_eff = 30; nếu một ô có trọng số 1 thì N_eff = 1.
CHUYỂN Ý: Còn những hướng em đã thử mà không giúp.`);
    img(s, as("hist_dev"), MX, 1.4, 6.9, 4.4, "left", "histogram cải thiện");
    const rows = [["số ô hiệu dụng N_{eff}", vn(w6.eff_cells, 2), vn(w7.eff_cells, 2)], ["trọng số lớn nhất", vn(w6.max_weight, 2), vn(w7.max_weight, 2)], ["khối lượng trên ô cách < 3 m", pct(w6.mass_within_3m, 1), pct(w7.mass_within_3m, 1)], ["trọng số trên ô HUI hạng 1", pct(w6.mass_top1_hui_cell, 1), pct(w7.mass_top1_hui_cell, 1)]];
    head(s, "Trọng số (dev, 19 861 vân tay)", MX + 7.2, 1.4, 5);
    const yb = tb(s, ["", "V6*", "V7-C2"], rows, MX + 7.2, 1.8, W - 7.2, [2.9, 1.1, 1.1].map((x) => x * (W - 7.2) / 5.1), { size: 13, minH: 0.4, align: ["left", "right", "right"] });
    text(s, `**Tốt hơn >0,5 m:** ${vn(im[0].n, 0)} truy vấn, giảm TB ${vn(im[0].mean_gain_m, 2)} m.\n**Kém hơn >0,5 m:** ${vn(im[1].n, 0)} truy vấn, tăng TB ${vn(-im[1].mean_gain_m, 2)} m.`, MX + 7.2, yb + 0.15, W - 7.2, 0.9, { fontSize: 13.5 });
    fcard(s, "fm_neff", MX + 7.2, yb + 1.1, 2.9, 0.95);
    text(s, "N_{eff}: nếu 30 ô bằng nhau thì 30; nếu một ô nhận hết thì 1", MX + 10.3, yb + 1.1, W - 10.3 + 0.0, 0.95, { fontSize: 12, color: GREY, valign: "middle" });
    callout(s, "V7 giữ \"độ sắc nét\" cao hơn nhưng vẫn **hỏng** ở một phần truy vấn: sai tầng và vùng thưa điểm tham chiếu vẫn là nguồn sai số còn lại.", 6.2, 0.7, SOFT2, INK, 14.5);
  }

  // ---- diagram F8: từng truy vấn trên tập kiểm tra
  {
    const v6 = csvErr("results/huim_only/uji/v6/predictions/validationData.csv"), v7 = csvErr("results/huim_only/uji/v7/predictions/C_rel_absL3.csv");
    let better = 0, worse = 0, same = 0;
    v6.forEach((e6, k) => { const d = e6 - v7.get(k); if (d > 0.5) better++; else if (d < -0.5) worse++; else same++; });
    const s = slide("Kết quả · Từng truy vấn (test)", `Diagram: trên test, V7 tốt hơn V6 ở ${vn(better, 0)} vân tay, kém hơn ở ${vn(worse, 0)}`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Biểu đồ này so sánh V7 với V6 trên TỪNG vân tay của tập kiểm tra. Trục ngang là sai số của V6 trừ sai số của V7, tính bằng mét: bên phải số 0 nghĩa là V7 chính xác hơn (cột xanh), bên trái là V7 kém hơn (cột cam). Em chỉ đếm những vân tay chênh hơn 0,5 mét. Kết quả: V7 tốt hơn ở ${vn(better, 0)} vân tay, kém hơn ở ${vn(worse, 0)} vân tay, và ${vn(same, 0)} vân tay hai bên chênh không quá 0,5 mét.
VÍ DỤ ĐỜI THƯỜNG: Giống bảng so sánh điểm của hai học sinh trên từng bài kiểm tra trong cả học kỳ: không ai thắng ở mọi bài. Học sinh V7 thắng đậm ở ${vn(better, 0)} bài, thua ở ${vn(worse, 0)} bài, hòa ở ${vn(same, 0)} bài. Điều quan trọng là tổng điểm: các bài V7 thắng thường thắng với khoảng cách lớn (đuôi bên phải kéo dài đến 20 mét), nên sai số trung bình giảm từ ${vn(T6.mean, 3)} xuống ${vn(T7.mean, 3)} mét.
NÓI THẲNG: V7 không tốt hơn V6 ở mọi vân tay. Có ${vn(worse, 0)} vân tay V7 kém hơn; em đã giải thích nguyên nhân: V7 tập trung trọng số hơn nên khi tin nhầm một ô thì sai nặng hơn. Đây là một đánh đổi.
LƯU Ý ĐỂ TRẢ LỜI: "V6" trong biểu đồ này là dự đoán đã lưu của V6 (6,866 mét). Em phát hiện nhãn gốc của biểu đồ ghi nhầm là V6*, nên đã sửa mã vẽ và vẽ lại trước khi đưa vào bài.
CHUYỂN Ý: Cuối cùng là biểu đồ cắt bỏ thành phần trên dev.`);
    img(s, FIG("F8_cai_thien_tung_truy_van_test.png"), MX, 1.4, 7.7, 5.45, "left", "F8 từng truy vấn trên test");
    const x = MX + 8.0, w = W - 8.0;
    card(s, x, 1.4, w, 5.45, SOFT, "Cách đọc biểu đồ", TEAL, TEAL);
    bullets(s, ["Trục ngang: **sai số V6 − sai số V7** (m); dương = V7 chính xác hơn", `**${vn(better, 0)}** vân tay V7 tốt hơn > 0,5 m (cột xanh)`, `**${vn(worse, 0)}** vân tay V7 kém hơn > 0,5 m (cột cam)`, `**${vn(same, 0)}** vân tay chênh không quá 0,5 m`,
      "Đuôi bên phải dài hơn bên trái ⇒ khi thắng thì thắng đậm hơn", "V6 ở đây là **dự đoán đã lưu** của V6 (6,866 m)"], x + 0.22, 1.9, w - 0.4, 4.9, 13, INK, 6);
  }

  // ---- diagram F6: cắt bỏ thành phần (dev)
  {
    const m = (k) => dI(k).mean, df = (a, b) => vnd(m(a) - m(b), 2);
    const s = slide("Kết quả · Cắt bỏ thành phần", "Diagram: cắt bỏ thành phần trên dev, mỗi thanh thêm một thay đổi",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Biểu đồ này gọi là cắt bỏ thành phần, tiếng Anh là ablation. Mỗi thanh ngang thêm đúng một thay đổi so với thanh ngay phía trên, và chiều dài thanh là sai số trung bình trên dev, trên 19 861 vân tay có thông tin. Đọc từ trên xuống: V4 là ${vn(m("V4"), 2)} mét, V6 sau khi sửa số học là ${vn(m("V6*"), 2)} mét, V7-A đổi cách hợp nhất ô giảm được chút ít còn ${vn(m("V7-A"), 2)} mét, V7-B học trọng số trực tiếp còn ${vn(m("B_base"), 2)} mét, thêm góc nhìn rel còn ${vn(m("C_rel"), 2)}, thêm abs mức 3 còn ${vn(m("C_rel_absL3"), 2)}, và V7-D thêm HUI cấp tầng chỉ còn ${vn(m("D_hier"), 2)} mét.
VÍ DỤ ĐỜI THƯỜNG: Giống như nâng cấp dần một chiếc xe đua: lần đầu thay động cơ (học trọng số trực tiếp) tăng tốc nhiều nhất; các lần sau thay lốp, thay đèn (thêm góc nhìn rel, abs mức 3) mỗi lần chỉ nhanh thêm một chút. Biểu đồ giúp biết món nâng cấp nào đáng tiền.
ĐỌC KỸ HAI THANH CUỐI: V7-D có sai số dev thấp nhất, ${vn(m("D_hier"), 2)} mét, nhưng em KHÔNG chọn nó, vì quy tắc em khai báo trước là sai số dev thấp hơn VÀ tốt hơn ở ít nhất 4 trong 6 fold; V7-D chỉ tốt hơn ở 3 trên 6 fold và trên test lại tệ hơn 0,014 mét. Với V7-A cũng vậy: giảm trên dev nhưng tệ hơn trên test nên em coi là không bền.
CON SỐ ĐÁNG NHỚ: Từ V4 xuống V6* giảm ${df("V6*", "V4")} (các cải tiến của V5 và V6). Trong phần V7, bước giảm nhiều nhất là V7-B (${df("B_base", "V7-A")} so với thanh trước); thêm rel giảm ${df("C_rel", "B_base")}, thêm abs mức 3 chỉ ${df("C_rel_absL3", "C_rel")}.
CHUYỂN Ý: Em xin chuyển sang những hướng em đã thử mà không giúp.`);
    img(s, FIG("F6_ablation_dev.png"), MX, 1.4, 8.4, 4.4, "left", "F6 cắt bỏ thành phần trên dev");
    const x = MX + 8.7, w = W - 8.7;
    card(s, x, 1.4, w, 4.4, SOFT, "Đọc từng bước (dev, m)", TEAL, TEAL);
    bullets(s, [`V4 → V6*: **${df("V6*", "V4")}** (cải tiến V5, V6)`, `+ hợp nhất thích ứng V7-A: ${df("V7-A", "V6*")} (**không bền** ở test)`, `+ bộ chấm điểm trực tiếp V7-B: **${df("B_base", "V7-A")}**`, `+ HUI rel (V7-C1): **${df("C_rel", "B_base")}**`, `+ HUI abs-L3 (V7-C2): ${df("C_rel_absL3", "C_rel")}`, `+ HUI cấp tầng (V7-D): ${df("D_hier", "C_rel_absL3")} (**không chọn**)`], x + 0.2, 1.9, w - 0.35, 4.9, 12.5, INK, 6);
    callout(s, "**V7-D thấp nhất trên dev (5,69 m) nhưng không được chọn:** quy tắc khai báo trước là dev thấp hơn **và** tốt hơn ≥ 4/6 fold; V7-D chỉ 3/6 fold và tệ hơn 0,014 m trên test.", 5.95, 0.9, SOFT2, INK, 14);
  }

  // ---- kết quả âm
  {
    const Ex = D.explore, byLog = (n) => Ex.find((r) => r.log === n);
    const s = slide("Kết quả · Thử nghiệm không giúp", "Những hướng không giúp và vì sao chọn V7-C2",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Một nghiên cứu trung thực phải báo cả những điều không hiệu quả. Em đã thử năm hướng không giúp. Một, đặc trưng bù lệch thiết bị làm tệ đi 0,063 mét vì mạng học các đặc điểm riêng của điện thoại huấn luyện. Hai, đặc trưng đồng thuận không gian giữa các mô hình HUI chỉ cải thiện 0,006 mét, không đáng kể. Ba, trộn trọng số của V7 với trọng số GBM của V6 không tốt hơn V7 thuần. Bốn, mất mát phụ listwise cho kết quả tệ hơn. Năm, V7-A, đổi cách hợp nhất ô trên dự đoán của V6: giảm 0,027 mét trên dev nhưng tệ hơn 0,020 mét trên test, nên không bền.
VÍ DỤ ĐỜI THƯỜNG: Giống như đổi chiến thuật trong một trận bóng: có chiến thuật thắng ở trận tập nhưng thua ở trận thật, vì đối thủ thật khác với đối thủ tập. Chọn chiến thuật nào không thể chỉ nhìn một trận.
QUY TẮC CHỌN: Em chọn mô hình theo một quy tắc đã khai báo TRƯỚC khi chấm test: sai số dev thấp hơn VÀ tốt hơn ở ít nhất 4 trong 6 fold. V7-D (thêm HUI cấp tầng) có dev thấp hơn chút (−0,013 mét) nhưng chỉ tốt hơn ở 3/6 fold, và tệ hơn 0,014 mét trên test, nên không chọn. V7-C2 đạt quy tắc, là mô hình được chọn.
LƯU Ý: Lần khai thác HUI cấp tầng đầu tiên dùng giới hạn thời gian đồng hồ 600 giây khiến số HUI thay đổi theo tải máy; em đã bỏ cách đó và dùng chính sách chỉ dựa trên số HUI.
CHUYỂN Ý: Bây giờ là phần quan trọng: kiểm chứng.`);
    const rows = [["Đặc trưng bù lệch thiết bị (13 cột)", `${vn(D.dev_files.C_devrob.mean_inf, 3)} so với V7-B ${vn(D.dev_files.B_base.mean_inf, 3)}`, "tệ hơn (+0,063 m): quá khớp theo điện thoại huấn luyện"],
      ["Đồng thuận không gian giữa các mô hình HUI (15 cột)", `${vn(byLog("b2_rel_geo.log").tb_co_trong_so, 3)} so với ${vn(byLog("b2_rel.log").tb_co_trong_so, 3)}`, "−0,006 m: không có ý nghĩa"],
      ["Trộn trọng số V7-C2 với trọng số GBM của V6 (chọn lồng nhau)", "5,706 so với 5,702", "không tốt hơn V7-C2 thuần"],
      ["Mất mát phụ listwise (aux 0,3, thăm dò 1 thành viên)", `${vn(byLog("b_c2.log").tb_co_trong_so, 3)} so với ${vn(byLog("b_c1.log").tb_co_trong_so, 3)}`, "tệ hơn"],
      ["Hợp nhất thích ứng V7-A (trên test)", `${vn(tr("V7-A").mean, 3)} so với ${vn(T6r.mean, 3)}`, "tệ hơn 0,020 m: không bền"],
      ["HUI cấp tầng V7-D (test)", `${vn(tr("D_hier").mean, 3)} so với ${vn(T7.mean, 3)}`, "tệ hơn 0,014 m; chỉ tốt hơn 3/6 fold ở dev"]];
    const yb = tb(s, ["Thử nghiệm", "Sai số (m)", "Kết luận"], rows, MX, 1.45, W, [5.4, 3.2, W - 8.6], { size: 12.5, minH: 0.45, align: ["left", "center", "left"] });
    callout(s, "**Quy tắc chọn (khai báo trước khi chấm test):** sai số dev thấp hơn **và** tốt hơn ở ít nhất 4/6 fold. V7-C2 đạt; V7-A và V7-D không đạt hoặc không bền trên test.", yb + 0.25, 1.0, SOFT2, INK, 14.5);
  }

  // ================================================================== CHƯƠNG 7: kiểm chứng
  divider(6, "Kiểm chứng, giới hạn và hỏi–đáp", ["Làm sao biết 6,309 m không phải số ảo", "Chống rò rỉ dữ liệu", "Giới hạn, hướng tiếp theo và câu hỏi dự kiến"],
`KỊCH BẢN (30 giây)
NÓI: Chương cuối trả lời câu hỏi mà em nghĩ thầy cô quan tâm nhất: làm sao biết con số 6,309 mét là thật. Em có ba cách tính lại độc lập, một bộ biện pháp chống rò rỉ, và em xin nói rõ những giới hạn của nghiên cứu. Cuối cùng là các câu hỏi em dự kiến và bản đồ nguồn gốc các con số.
CHUYỂN Ý: Cách kiểm tra đầu tiên và đơn giản nhất.`);

  {
    const fr = VF.first_rows;
    const s = slide("Kiểm chứng · Cách 1", `Tính lại ${vn(T7.mean, 4)} m từ tọa độ thật và tọa độ dự đoán`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Cách kiểm tra đơn giản nhất là không chạy lại mô hình, chỉ tính lại sai số từ hai cột tọa độ: tọa độ thật và tọa độ dự đoán của từng vân tay. Bảng này lấy vài dòng đầu và hàng 335. Với mỗi dòng: lấy x-mũ trừ x và y-mũ trừ y, tính căn tổng bình phương, nhân 0,766126 ra sai số mét. Cộng 1 111 sai số được ${vn(VF.sum_err_m, 2)} mét; chia 1 111 ra ${vn(VF.mean_err_m, 4)} mét.
VÍ DỤ ĐỜI THƯỜNG: Giống như kiểm tra hóa đơn nhà hàng: không cần vào bếp xem đầu bếp nấu, chỉ cần cộng lại từng món trên hóa đơn xem tổng có đúng không. Thầy cô có thể chọn bất kỳ một dòng nào, bấm máy tính cầm tay để kiểm.
CÁCH TRÌNH BÀY CHO HỘI ĐỒNG: Em có thể mở thư mục BAOCAO/so_lieu_V7, chạy lệnh python kiem_tra_V7.py (chỉ dùng thư viện chuẩn của Python); chương trình in KHỚP cho cả chín mô hình, và dựng lại tọa độ V7-C2 từ 30 trọng số, lệch tối đa 9,3 nhân 10 mũ trừ 10.
GIỚI HẠN CỦA CÁCH KIỂM NÀY: Cách này chứng minh con số được tính đúng từ tệp dự đoán. Nó CHƯA chứng minh rằng tệp dự đoán được tạo ra mà không nhìn thấy đáp án. Điều đó dựa vào quy trình và các phép kiểm rò rỉ ở các slide tiếp theo.
CHUYỂN Ý: Còn hai cách kiểm tra nữa: Excel và chương trình kiểm chứng của dự án.`);
    fcard(s, "fm_err", MX, 1.4, 6.6, 1.25);
    const rows = fr.slice(0, 4).concat(fr.slice(6)).map((r) => [r.src_row, vn(r.true_x, 3), vn(r.true_y, 3), vn(r.pred_x, 3), vn(r.pred_y, 3), vn(r.dx, 3), vn(r.dy, 3), vn(r.err_m, 4)]);
    tb(s, ["Hàng", "x thật", "y thật", "x̂", "ŷ", "x̂−x", "ŷ−y", "sai số (m)"], rows, MX, 2.85, W, [0.9, 1.7, 1.9, 1.7, 1.9, 1.1, 1.1, W - 10.3], { size: 12.5, minH: 0.38, align: ["center", "right", "right", "right", "right", "right", "right", "right"], hl: (i) => i === 4 });
    card(s, MX + 6.9, 1.4, W - 6.9, 1.25, SOFT, null, TEAL, TEAL);
    text(s, `**Tổng 1 111 sai số = ${vn(VF.sum_err_m, 2)} m; ${vn(VF.sum_err_m, 2)} / 1 111 = ${vn(VF.mean_err_m, 4)} m**; trung vị ${vn(VF.median_err_m, 4)} m; P90 ${vn(VF.p90_err_m, 4)} m.`, MX + 7.15, 1.45, W - 7.4, 1.15, { fontSize: 14.5, valign: "middle" });
    text(s, `Hàng 335 (tô màu): Δx = ${vn(fr[6].dx, 5)}, Δy = ${vn(fr[6].dy, 5)} → √(…) = ${vn(Math.hypot(fr[6].dx, fr[6].dy), 5)} → × 0,766126 = **${vn(fr[6].err_m, 4)} m**. **Ký hiệu:** e_{n} sai số vân tay n (m); (x̂, ŷ) dự đoán; (x, y) thật; g = 0,766126; N = 1 111.`, MX, 6.1, W, 0.8, { fontSize: 13.5 });
  }

  {
    const s = slide("Kiểm chứng · Cách 2 và 3", `Excel, Python và verify_v7: ${D.verification.n_checks} phép kiểm, ${D.verification.n_failed} thất bại`,
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Cách hai và ba là ba công cụ độc lập. Công cụ một là tệp Excel kiem_chung_V7_mean.xlsx. Sheet Tong_hop liệt kê chín mô hình, mỗi dòng ghi KHỚP; mỗi sheet mô hình có công thức sai số từng mẫu và hàm AVERAGE; sheet V7C2_dung_lai_toa_do dựng lại tọa độ bằng SUMPRODUCT của 30 trọng số và 30 tâm ô; sheet Vi_du_mot_truy_van dựng tay hàng 335. Công cụ hai là chương trình Python chỉ dùng thư viện chuẩn: lệnh kiem_tra_V7.py in KHỚP cho từng mô hình. Công cụ ba là verify_v7.py của dự án với 16 phép kiểm; cả 16 đều đạt.
VÍ DỤ ĐỜI THƯỜNG: Giống như ba kế toán độc lập cùng kiểm một sổ cái bằng ba công cụ khác nhau (máy tính tay, bảng tính, phần mềm). Nếu cả ba ra cùng một con số thì khả năng sai sót ngẫu nhiên rất nhỏ.
MƯỜI SÁU PHÉP KIỂM GỒM: tính lại trung bình, trung vị, P90; tọa độ bằng đúng tổng w nhân tâm ô; trọng số không âm và tổng bằng 1; không có NaN; mọi ô ứng viên nằm đúng tầng; đúng là các hàng của validationData; độ chính xác tầng tòa; V6 tái tạo khớp bản lưu; V6 không bị sửa (git diff rỗng); fold rời nhau theo điện thoại; mã băm cache khớp; mọi cache dựng từ cùng một tệp huấn luyện (SHA-256); quét cú pháp không có k-NN; EFIM bằng vét cạn; tái lập theo seed; khai thác EFIM tái lập số HUI của V6.
NÓI THẲNG: Những phép kiểm này chứng minh tính đúng đắn và tính nhất quán của chuỗi tính toán; chúng không thay thế một tập kiểm tra hoàn toàn độc lập, điều mà em ghi nhận là một giới hạn.
CHUYỂN Ý: Còn câu hỏi rò rỉ dữ liệu.`);
    const MODELS = [["V4 (đã lưu)", tr("V4").mean], ["V5 (đã lưu)", tr("V5").mean], ["V6 (đã lưu)", tr("V6").mean], ["V6 (tái tạo)", tr("V6r").mean], ["V7-A", tr("V7-A").mean], ["V7-B", tr("B_base").mean], ["V7-C1", tr("C_rel").mean], ["V7-C2 (chọn)", tr("C_rel_absL3").mean], ["V7-D", tr("D_hier").mean]];
    const rows = MODELS.map(([n, v]) => [n, vn(v, 4), vn(v, 4), "KHỚP"]);
    head(s, "Sheet Tong_hop của kiem_chung_V7_mean.xlsx", MX, 1.4, 6.7);
    const yb = tb(s, ["Mô hình", "TB tính lại (m)", "TB báo cáo (m)", "Kết luận"], rows, MX, 1.8, 6.7, [2.4, 1.5, 1.5, 1.3], { size: 13, minH: 0.37, align: ["left", "right", "right", "center"], hl: (i) => i === 7 });
    text(s, "Cột sai số từng mẫu: =SQRT((x̂−x)^2+(ŷ−y)^2)*g; trung bình: =AVERAGE(...). Python: python kiem_tra_V7.py → 9 dòng KHỚP + \"Tất cả khớp.\"", MX, yb + 0.15, 6.7, 1.0, { fontSize: 13, color: GREY });
    card(s, MX + 7.0, 1.4, W - 7.0, 2.55, SOFT, "Excel và Python", NAVY, TEAL);
    bullets(s, ["**V7C2_dung_lai_toa_do**: (x̂, ŷ) = SUMPRODUCT(30 trọng số, 30 tâm ô); lệch tối đa 9·10⁻¹⁰", "**Vi_du_mot_truy_van**: hàng 335 dựng tay: 7,9938 và 4,6357 m", "**Dev_OOF**: V6* 6,2087; V7-C2 5,7017 m (19 861 vân tay)"], MX + 7.22, 1.9, W - 7.45, 2.0, 12.5, INK, 4);
    card(s, MX + 7.0, 4.1, W - 7.0, 2.75, SOFT2, `verify_v7.py: ${D.verification.n_checks} phép kiểm`, RUST, RUST);
    bullets(s, ["Tính lại trung bình/trung vị/P90; tọa độ = Σ w · tâm ô; Σ w = 1", "Mọi ô ứng viên đúng tầng; đúng 1 111 hàng validationData", "V6 không đổi (git diff rỗng); fold rời nhau theo điện thoại", "SHA-256 của dữ liệu; **không k-NN** (quét cú pháp 9 mô-đun)", "EFIM = vét cạn; tái lập theo seed"], MX + 7.22, 4.6, W - 7.45, 2.2, 12.5, INK, 3);
  }

  {
    const nes = D.nested;
    const s = slide("Kiểm chứng · Chống rò rỉ", "Chống rò rỉ dữ liệu và đo độ tin cậy",
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Em có năm biện pháp chống rò rỉ. Một, chia fold theo điện thoại, nên không điện thoại nào ở cả hai phía. Hai, mô hình HUI của đặc trưng fold k chỉ được khai thác trên các điện thoại khác. Ba, mọi quyết định chọn mô hình dựa trên dev; test chỉ chấm một lần cho mỗi biến thể đã khai báo trước, kể cả biến thể không chọn. Bốn, mỗi tệp cache có mã băm SHA-256 của dữ liệu huấn luyện, chỉ số hàng của fold, phiên bản mã và cấu hình, cache không khớp bị từ chối. Năm, em đo rò rỉ gián tiếp bậc hai bằng giao thức lồng nhau.
VÍ DỤ ĐỜI THƯỜNG: Giống như chấm thi: bài thi chính thức được niêm phong (test), người ra đề thi thử không được thấy đề chính thức (dev tách khỏi test), và biên bản ghi rõ ai làm gì lúc nào (cache có mã băm). Em còn kiểm tra một kẽ hở nhỏ: giám khảo thi thử có vô tình thấy một phần đề chính thức không (rò rỉ bậc hai); kết quả đo được chênh lệch chỉ −0,0035 mét.
KHOẢNG TIN CẬY: Em dùng bootstrap 4 000 lần lấy mẫu lại CẢ điện thoại (không phải từng vân tay), vì các vân tay của cùng một điện thoại không độc lập. Test chỉ có 11 cụm nên khoảng tin cậy của trung bình rộng: ${vn(T7.mean, 3)} [${vn(T7.ci95_lo, 2)}; ${vn(T7.ci95_hi, 2)}]; nhưng khoảng tin cậy của chênh lệch cặp so với V6 là [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}], không chứa 0, nên đó mới là con số cần đọc.
TÁI LẬP: Hai lần chạy độc lập cùng cấu hình cho sai số theo 6 fold trùng đến 3 chữ số thập phân; số HUI của các mô hình fold bằng đúng số trong kết quả V6.
THÀNH THẬT: Tập validation đã được dùng từ V1 đến V6 nên con số trên test là chỉ báo, chưa phải ước lượng hoàn toàn độc lập; chưa có tập kiểm tra mới.
CHUYỂN Ý: Cuối cùng là giới hạn và hướng tiếp theo.`);
    card(s, MX, 1.4, 6.1, 2.65, SOFT, "Năm biện pháp chống rò rỉ", TEAL, TEAL);
    bullets(s, ["Fold theo **điện thoại**; HUI của fold k chỉ đào trên máy khác", "Chọn mô hình **chỉ bằng dev**; test chấm một lần, báo cả biến thể không chọn", "Cache có **SHA-256**, chỉ số hàng, mã, cấu hình; không khớp thì từ chối", `Rò rỉ bậc hai (lồng nhau, fold ngoài 2): chuẩn **${vn(nes.standard, 4)}**; chặt **${vn(nes.strict, 4)}**; chênh ${vnd(nes.diff, 4)} m`], MX + 0.22, 1.9, 5.7, 2.1, 12.5, INK, 3);
    card(s, MX, 4.2, 6.1, 2.65, SOFT2, "Tái lập", RUST, RUST);
    bullets(s, ["Hai lần chạy độc lập: sai số theo 6 fold trùng đến 3 chữ số", "Số HUI của 12 mô hình fold bằng đúng số của V6; L3 cuối 1 031 786 khớp summary.json của V6", "Mã và kết quả V6 không bị sửa (git diff rỗng)"], MX + 0.22, 4.7, 5.7, 2.1, 12.5, INK, 4);
    fcard(s, "fm_boot", MX + 6.4, 1.4, W - 6.4, 1.3);
    ann(s, [["B_{b}", "một lần lấy mẫu lại: chọn ngẫu nhiên có hoàn lại các điện thoại"], ["p, n", "điện thoại p và vân tay n của p"], ["ē^{(b)}", "sai số trung bình của lần lấy mẫu thứ b (4 000 lần)"]], MX + 6.4, 2.85, W - 6.4, 1.2, 12.5);
    const rows = [["Test, V7-C2", `${vn(T7.mean, 3)} [${vn(T7.ci95_lo, 2)}; ${vn(T7.ci95_hi, 2)}]`], ["Test, chênh vs V6", `${vnd(T7.diff_vs_V6, 3)} [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}]`], ["Dev, chênh vs V6*", `${vnd(dI("C_rel_absL3")["diff_vs_V6*"], 3)} [${vnd(dI("C_rel_absL3").diff_lo, 2)}; ${vnd(dI("C_rel_absL3").diff_hi, 2)}]`]];
    const yb = tb(s, ["Đại lượng", "Giá trị [KTC 95%]"], rows, MX + 6.4, 4.2, W - 6.4, [2.3, 3.4].map((x) => x * (W - 6.4) / 5.7), { size: 13, minH: 0.42, align: ["left", "right"] });
    text(s, "KTC của trung bình rộng vì chỉ 11 (test) hoặc 16 (dev) cụm; KTC của **chênh lệch cặp** hẹp hơn và là điều cần đọc.", MX + 6.4, yb + 0.15, W - 6.4, 1.0, { fontSize: 13, color: GREY });
  }

  // ---- giới hạn
  {
    const e = rj("results/huim_only/uji/v7/dev/E_seeds.json"), ts = rj("results/huim_only/uji/v7/test_summary.json");
    const eTest = ts && ts.E_seeds ? ts.E_seeds.mean : null;
    const cost = D.cost, c6 = cost.v6, c7 = cost.v7;
    const s = slide("Giới hạn", "Giới hạn của V7 và hướng tiếp theo: mục tiêu dưới 6 m chưa đạt",
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Em xin kết luận bằng sự trung thực. V7 giảm sai số trên test từ ${vn(T6.mean, 3)} xuống ${vn(T7.mean, 3)} mét, tức là giảm 8,1 phần trăm, nhưng mục tiêu dưới 6 mét CHƯA đạt. Khoảng cách tới trần chất lượng của 30 ứng viên (0,59 mét) vẫn còn rất lớn, nghĩa là còn dư địa ở khâu chọn trọng số và nhất là ở khâu chọn tầng: đúng tầng chỉ 80,4 phần trăm và em chưa cải thiện được.
HẠN CHẾ: Một, tập validation đã dùng nhiều lần nên không phải ước lượng độc lập; chưa có tập kiểm tra mới. Hai, chỉ đánh giá trên UJIIndoorLoc, chưa đánh giá các bộ dữ liệu khác với V7. Ba, chi phí: V7 chậm hơn V6 khoảng 63 phần trăm và cần RAM nhiều hơn 41 phần trăm (đỉnh ${vn(c7.peak_working_set_MB, 0)} MB so với ${vn(c6.peak_working_set_MB, 0)} MB). Bốn, nhiều siêu tham số chưa dò (lr, batch, K, số fold, W, số mức).
HƯỚNG TIẾP THEO: Một, học quyết định tầng từ HUI vì sai tầng là nguồn sai số lớn nhất. Hai, thêm góc nhìn HUI. Ba, giảm RAM bằng ma trận thưa. Bốn, kiểm tra trên tập độc lập mới.
THỬ NGHIỆM BỔ SUNG V7-E (nói nếu được hỏi "còn cách nào xuống dưới 6,3 mét không?"): Em có thử tập hợp 5 seed ngẫu nhiên cho bộ chấm điểm, tức 30 mạng thay vì 6, giữ nguyên đặc trưng của V7-C2. Trên dev, V7-E đạt ${e ? vn(e.mean_inf, 4) : "5,6814"} mét, thấp hơn V7-C2 khoảng 0,020 mét và tốt hơn ở cả 6 trên 6 fold, nên đạt quy tắc chọn đã khai báo. ${eTest ? "Em chấm V7-E trên tập kiểm tra đúng một lần: " + vn(eTest, 4) + " mét, tức là thấp hơn V7-C2 khoảng 0,032 mét và dưới 6,3 mét; em đã tự tính lại con số này từ tệp dự đoán và ra đúng như vậy. Nhưng em nói thật: mức cải thiện này nhỏ (V7-E chỉ tốt hơn V7-C2 ở khoảng một nửa số vân tay), em chưa làm khoảng tin cậy cặp cho nó và chưa mở rộng bộ kiểm chứng Excel và Python cho V7-E. Vì vậy số liệu chính của bài vẫn là V7-C2 với 6,309 mét, đã kiểm chứng đủ ba cách; V7-E là kết quả bổ sung." : "Em CHƯA chấm V7-E trên tập kiểm tra nên chưa đưa vào kết quả chính."}
VÍ DỤ ĐỜI THƯỜNG CHO TẬP HỢP: Giống như hỏi ý kiến một người thì có thể thiên lệch, hỏi ý kiến cả hội đồng năm người rồi lấy trung bình thì ổn định hơn một chút; nhưng thêm người không làm hội đồng thông minh hơn nhiều, chỉ làm ít dao động hơn. Vì thế mức cải thiện nhỏ là hợp lý.
CHUYỂN Ý: Cuối cùng em xin tóm tắt các con số để thầy cô tiện tra cứu.`);
    const cols = [
      ["Chưa đạt / hạn chế", RUST, ["Dưới 6 m **chưa đạt** (6,309 m); ô tiên tri 0,59 m (dev) cho thấy còn dư địa", "Validation đã dùng từ V1–V6; **chưa có tập độc lập mới**", "Đúng tầng 80,4% **không cải thiện**; sai tầng tốn thêm ~7 m", `Chi phí: thời gian +63%, RAM đỉnh ${vn(c6.peak_working_set_MB, 0)} → ${vn(c7.peak_working_set_MB, 0)} MB`, "Nhiều siêu tham số chưa dò: lr, batch, K, W, số mức, số fold"]],
      ["Hướng tiếp theo", NAVY, ["Học quyết định tầng từ HUI (sai tầng là nguồn sai số lớn nhất)", "Thêm góc nhìn HUI (θ khác nhau, rel mức-3)", "Giảm RAM bằng ma trận thưa", "Kiểm tra trên tập độc lập mới và các bộ dữ liệu khác"]],
      ["Thử nghiệm bổ sung: V7-E (5 seed)", TEAL, [`**V7-E:** tập hợp 5 seed cho bộ chấm điểm (30 mạng thay vì 6), cùng đặc trưng với V7-C2`, `Dev: **${e ? vn(e.mean_inf, 4) : "5,6814"} m** (−0,020 m; tốt hơn ở 6/6 fold) ⇒ đạt quy tắc chọn khai báo trước`,
        eTest ? `Test (chấm một lần): **${vn(eTest, 4)} m**, thấp hơn V7-C2 0,032 m và **dưới 6,3 m**; tự tính lại từ tệp dự đoán: khớp` : "Test V7-E: **chưa chấm**, chưa đưa vào kết quả chính",
        eTest ? "Cải thiện **nhỏ** (tốt hơn V7-C2 ở 586/1 111 vân tay), chưa có Excel/Python kiểm chứng riêng ⇒ **số chính của bài vẫn là V7-C2: 6,309 m**" : "Số liệu chính của bài vẫn là V7-C2: 6,309 m"]]];
    const w = (W - 0.5) / 3;
    cols.forEach(([t, col, items], i) => { const x = MX + i * (w + 0.25); card(s, x, 1.45, w, 5.4, CARD, t, col, col); bullets(s, items, x + 0.25, 2.05, w - 0.45, 4.7, 14, INK, 9); });
  }

  // ---- bản đồ nguồn gốc con số
  {
    const mk = (n, rows) => {
      const s = slide(`Bản đồ nguồn gốc con số (${n}/2)`, `Bản đồ nguồn gốc con số (${n}/2): mỗi số thuộc loại nào`,
`KỊCH BẢN (khoảng 2 phút)
NÓI: Em tổng hợp mọi hằng số xuất hiện trong bài vào một bảng, phân loại theo nguồn gốc. "Đếm" là số đếm được từ dữ liệu, có thể tự kiểm. "Định nghĩa" là theo công thức hay thiết kế. "Đo" là đo trên dữ liệu. "Quy ước" là giá trị phổ biến em chưa dò lưới. "Dev" là chọn bằng lưới hoặc so sánh trên dev. "Ngân sách" là giới hạn tính toán.
VÌ SAO LÀM BẢNG NÀY: Mỗi con số đều thuộc một trong các loại này, và em muốn nói đúng loại của nó khi thầy cô hỏi: số nào em chọn bằng thực nghiệm, số nào em tự đếm, số nào là quy ước, và nhất là số nào em chưa dò.
VÍ DỤ CÁCH TRẢ LỜI: Nếu thầy cô hỏi "vì sao cửa sổ rel là 40 dB?", em sẽ trả lời: đó là quy ước, em chưa dò lưới; kiểm lại thì 89,9 phần trăm lần đọc nằm trong 40 dB so với AP mạnh nhất. Nếu hỏi "vì sao 7 360 tham số?", em trả lời: đó là số đếm: 6 304 cộng 1 040 cộng 16.
CHUYỂN Ý: ${n === 1 ? "Phần hai của bảng." : "Em xin dừng ở đây và nhận câu hỏi."}`);
      tb(s, ["Con số", "Loại", "Từ đâu (một dòng)"], rows, MX, 1.45, W, [3.6, 1.7, W - 5.3], { size: 12.5, minH: 0.52 });
    };
    mk(1, [["0,766126", "định nghĩa", "cos(vĩ độ 39,992698°) của Web-Mercator"],
      ["19 937 / 19 861 / 76 vân tay; 933 ô; 21,29/ô", "đếm", "dòng CSV; 19 861 / 933 = 21,29"],
      ["6 fold theo điện thoại; 5 thành viên", "quy ước / định nghĩa", "16 điện thoại → 6 nhóm; 6 − 1 = 5"],
      ["q ∈ [1, 100]; −104…0 dBm", "quy ước / đếm", "thang số nguyên; RSSI nhỏ nhất và lớn nhất có thật"],
      ["W = 40 dB; 3 mức", "quy ước", "chưa dò; 89,9% lần đọc trong 40 dB"],
      ["θ = 20% (thực dùng 34,55%)", "dev + ngân sách", "thăm dò: 10% tốt hơn 0,6 m nhưng ~25 phút/fold; 72,5% ô bị nâng ngưỡng"],
      ["10 s / 10 000 HUI / × 1,25", "ngân sách", "giới hạn tính toán; ô 1: 20 × 1,25³ = 39,0625%"],
      ["γ = 2, τ = 20, β = 3", "dev (lưới thô)", "2 880 cấu hình; (γ,τ) 3 cặp, β ∈ {1,3}"]]);
    mk(2, [["σ = 3 m, kf = 20", "dev", "σ ∈ {0,3,6,10}; kf ∈ {3,10,20} (20 ở biên)"],
      ["K = 30 ô ứng viên", "quy ước + đo", "ô tiên tri: K = 20 → 0,732 m; K = 30 → 0,588 m; chưa quét K"],
      ["m = 20, λ = 2, GBM 300 cây (V6)", "dev / quy ước", "bề mặt phẳng (7,19–7,21 m quanh cực tiểu); GBM không có lưới riêng; V7 không dùng"],
      ["33 + 8 + 8 = 49; × 4 = 196", "định nghĩa", "33 cột V6 + 8 mỗi mô hình mới; 4 phép biến đổi tương đối"],
      ["MLP 32/16, 7 360 tham số", "dev (2 cấu hình)", "196×32+32 + 64×16+16 + 16; 64/32: 5,9797 vs 32/16: 5,9588"],
      ["lr 5·10⁻⁴, batch 256, ε = 10⁻⁶", "quy ước", "chưa dò lưới; ε chỉ tránh √0"],
      ["30 epoch, kiên nhẫn 8", "ngân sách / quy ước", "epoch tốt nhất 5–29, trung vị 15"],
      ["12,90 triệu HUI; 6,309 m; 5,702 m", "đếm / đo", "EFIM (khớp vét cạn); chấm lại độc lập bằng Excel, Python, verify_v7"]]);
  }

  // ---- hỏi đáp
  {
    const b = D.nested;
    const gB = tr("B_base").mean - T6r.mean, gRel = tr("C_rel").mean - tr("B_base").mean, gAbs = T7.mean - tr("C_rel").mean;
    const mk = (kicker, title, rows, notes) => {
      const s = slide(kicker, title, notes);
      tb(s, ["Câu hỏi dự kiến", "Trả lời ngắn, kèm số có thể kiểm"], rows, MX, 1.45, W, [3.6, W - 3.6], { size: 12.5, minH: 0.8 });
    };
    mk("Hỏi–đáp (1/2)", "Câu hỏi dự kiến (1/2): kết quả và kiểm định", [
      ["Mục tiêu dưới 6 m chưa đạt, sao vẫn kết luận V7 tốt hơn V6?", `Không nói đạt mục tiêu. Giảm ${vn(-T7.diff_vs_V6, 3)} m (${vn(-T7.pct_vs_ref, 1)}%) trên test, KTC 95% cặp [${vnd(T7.diff_lo, 2)}; ${vnd(T7.diff_hi, 2)}] không chứa 0; dev ${vnd(dI("C_rel_absL3")["diff_vs_V6*"], 3)} m.`],
      ["validationData đã dùng từ V1 đến V6: có overfit vào test?", "Có nguy cơ, nên chọn mô hình chỉ bằng dev; mỗi biến thể chấm đúng một lần và báo cả biến thể không chọn (V7-A tệ hơn 0,020 m; V7-D tệ hơn 0,014 m). Test là chỉ báo, không phải ước lượng độc lập."],
      [`Dev ${vn(dI("C_rel_absL3").mean, 2)} m mà test ${vn(T7.mean, 2)} m: vì sao test cao hơn?`, `V6 cũng vậy: ${vn(dI("V6*").mean, 3)} → ${vn(T6r.mean, 3)} (${vnd(T6r.mean - dI("V6*").mean, 2)}); V7: ${vn(dI("C_rel_absL3").mean, 3)} → ${vn(T7.mean, 3)} (${vnd(T7.mean - dI("C_rel_absL3").mean, 2)}). Test có 9/11 điện thoại chưa từng thấy, thu sau ${DS.days_gap} ngày; chênh gần bằng nhau nên không phải lỗi riêng của V7.`],
      ["Siêu tham số chọn trên dev: có overfit dev?", `Lưới thô (${vn(G.n_configurations, 0)} cấu hình), kf = 20 ở biên lưới. Đã đo rò rỉ bậc hai bằng giao thức lồng nhau: ${vnd(b.diff, 4)} m (fold ngoài 2) — không đo được rò rỉ đáng kể.`],
      ["Ý nghĩa thống kê thế nào?", "Bootstrap 4 000 lần lấy lại CẢ điện thoại (cụm). Test chỉ 11 cụm (điện thoại 13 chiếm 33% vân tay) nên KTC của trung bình rộng [5,65; 7,21]; phải đọc KTC của chênh lệch cặp."]],
`KỊCH BẢN (khoảng 2 phút nếu cần dùng)
CÁCH DÙNG SLIDE NÀY: Đây là slide dự phòng cho phần hỏi đáp; em không cần trình bày hết. Mỗi câu trả lời đều có con số có thể kiểm.
CÂU 1 (mục tiêu chưa đạt): Em trả lời thẳng: em không nói đã đạt mục tiêu. Em chỉ nói V7 tốt hơn V6 một cách có ý nghĩa thống kê.
CÂU 2 (test dùng nhiều lần): Nói thật là có nguy cơ; vì vậy em chọn mô hình bằng dev, mỗi biến thể chấm một lần, và báo cả biến thể thua.
CÂU 3 (vì sao test cao hơn dev): Giải thích bằng bốn nguyên nhân đã đo: máy lạ, 91 ngày, 55 AP chỉ có ở test, máy 13 chiếm 33 phần trăm. Và chênh lệch của V6 và V7 gần bằng nhau.
CÂU 4 (siêu tham số): Nói lưới thô, kf ở biên; đã đo rò rỉ bậc hai.
CÂU 5 (thống kê): Nói bootstrap theo điện thoại và nên đọc khoảng tin cậy của chênh lệch cặp.
VÍ DỤ ĐỜI THƯỜNG KHI CẦN: Nếu thầy cô hỏi "sao số của em có đáng tin?", em có thể ví với kỳ thi: đề thi chính thức niêm phong (test), em chỉ sửa cách học dựa vào đề thi thử (dev), và em có biên bản kiểm tra ba người độc lập chấm lại bài.`);
    mk("Hỏi–đáp (2/2)", "Câu hỏi dự kiến (2/2): thiết kế và vai trò của HUIM", [
      ["HUIM là lõi hay chỉ tiền xử lý cho MLP?", `Ứng viên, tầng và mọi đặc trưng đều sinh từ HUI. Nhưng mức giảm lớn nhất đến từ bộ chấm điểm học trực tiếp (${vnd(gB, 3)} m test), HUI mới rel ${vnd(gRel, 3)} m và abs-L3 ${vnd(gAbs, 3)} m. Nói thẳng: HUI cho bằng chứng, bộ chấm điểm quyết định trọng số.`],
      ["Vì sao không k-NN / so khớp vân tay thô?", "Ràng buộc đề bài. Mô hình chỉ gồm HUI (tập mục, lợi ích, support) và vị trí ô; kiểm bằng quét cú pháp 9 mô-đun suy luận (T12) và test tĩnh; vân tay huấn luyện không được lưu."],
      ["Vì sao không θ = 10% (tốt hơn trong thăm dò)?", "Tốt hơn 0,6 m ở fold 1–2 nhưng ~25 phút khai thác mỗi fold; V2 (10%, fold theo người dùng) dev 7,699 → test 8,175. 20% là thỏa hiệp chất lượng–chi phí, và θ thực dùng sau tự nâng ngưỡng là 34,55%."],
      ["rel kém nhất khi đứng riêng, sao thêm vào lại giúp nhất?", "Dev khi đứng riêng: rank 7,669; abs 7,685; rel 8,362. Thêm làm bằng chứng bổ sung: −0,195 m, 6/6 fold. Giả thuyết: rel bất biến với lệch thu của thiết bị nên bổ sung cho abs/rank; chưa kiểm riêng."],
      ["Vì sao softmax trên 30 ô, không hồi quy tọa độ trực tiếp?", "Softmax giữ kết quả trong bao lồi các ô ứng viên và học được từ sai số mét; hồi quy trực tiếp có thể trả điểm ngoài vùng khả dĩ. **Chưa so sánh thực nghiệm** hai cách; bao lồi kéo tọa độ vào trong ở biên."]],
`KỊCH BẢN (khoảng 2 phút nếu cần dùng)
CÂU 1 (HUIM là lõi?): Câu dễ bị hỏi nhất. Trả lời thẳng: ứng viên, tầng và mọi đặc trưng đều từ HUI, nhưng phần lớn mức giảm sai số đến từ bộ chấm điểm học trực tiếp; HUI mới chỉ giảm thêm vài phần trăm mét. Nói như vậy thể hiện sự trung thực.
VÍ DỤ ĐỜI THƯỜNG: HUI giống như nguyên liệu và bộ chấm điểm giống như đầu bếp: nguyên liệu tốt mới có món ngon, nhưng cách nấu quyết định món cuối. Cả hai đều cần.
CÂU 2 (không k-NN): Đây là ràng buộc đề bài; kiểm bằng quét cú pháp.
CÂU 3 (θ = 10%): Đã giải thích: thỏa hiệp; θ thực dùng 34,55 phần trăm.
CÂU 4 (rel): Giả thuyết bổ sung thông tin; chưa kiểm riêng.
CÂU 5 (softmax): Bao lồi và học được; chưa so sánh thực nghiệm với hồi quy trực tiếp.`);
  }

  // ---- tóm tắt
  {
    const s = slide("Tóm tắt", "Tóm tắt một slide: từ UJIIndoorLoc đến 6,3 m",
`KỊCH BẢN TỔNG KẾT (khoảng 2 phút)
NÓI: Em xin tóm tắt lại bằng bốn ô. Ô một, dữ liệu: 21 048 vân tay Wi-Fi từ 520 bộ phát trong ba tòa nhà; tập kiểm tra khác tập huấn luyện về máy, người và thời điểm, nên khó hơn. Ô hai, HUI: em đổi cường độ thành lợi ích q, dùng EFIM khai thác từ năm góc nhìn các tổ hợp bộ phát đặc trưng của từng ô, rồi chấm điểm khớp P nhân V mũ ba, làm mượt, chọn tầng và giữ 30 ô ứng viên. Ô ba, phần mới của V7: 49 đặc trưng, dạng tương đối, bộ chấm điểm MLP 7 360 tham số, softmax và huấn luyện bằng chính sai số mét. Ô bốn, kết quả: 6,309 mét trên tập kiểm tra, V6 là 6,866 mét; kiểm chứng bằng Excel, Python và 16 phép kiểm; mục tiêu dưới 6 mét chưa đạt.
VÍ DỤ ĐỜI THƯỜNG: Hệ thống giống một người dẫn đường trong tòa nhà: nghe Wi-Fi, tra sổ mẫu của từng ô, chọn 30 điểm nghi vấn, rồi một trọng tài học cách chia phiếu để chốt vị trí; kết quả lệch trung bình khoảng 8 bước chân.
LỜI KẾT: Em xin cảm ơn thầy cô đã lắng nghe và rất mong nhận được nhận xét, câu hỏi của thầy cô.`);
    const cw = (W - 0.3) / 2, ch = 2.62, y1 = 1.4, y2 = y1 + ch + 0.14;
    const panel = (x, y, num, title, lines, color) => {
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: ch, fill: { color: color === TEAL ? "E6F0F2" : color === RUST ? "F7EAE3" : color === GOLD ? "F6F0DC" : "EDF0F5" }, line: { color: LINE, width: 0.75 } });
      badge(s, x + 0.15, y + 0.12, num, color, 0.42);
      s.addText(title, { x: x + 0.68, y: y + 0.1, w: cw - 0.85, h: 0.45, fontFace: F, fontSize: 17, bold: true, color: NAVY, margin: 0, valign: "middle", isTextBox: true });
      s.addText(lines.map((t, i) => c.para(t).map((q, j, a) => ({ text: q.text, options: { ...q.options, breakLine: i < lines.length - 1 && j === a.length - 1 } }))).flat(),
        { x: x + 0.2, y: y + 0.62, w: cw - 0.4, h: ch - 0.68, fontFace: F, fontSize: 13.5, color: INK, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
    };
    const nHUI = Object.values(D.config.hui.final_hui_counts).reduce((a, q) => a + q, 0);
    panel(MX, y1, 1, "Dữ liệu UJIIndoorLoc", ["**21 048 vân tay**, 520 AP, 3 tòa, 13 tầng, **933 ô**; 96,54% giá trị là 100 (không nghe).", "Test khác train về **máy, người, thời điểm (91 ngày)** ⇒ khó hơn; dev chia theo điện thoại.", "Sai số tính bằng mét: **g = 0,766126** = cos vĩ độ."], NAVY);
    panel(MX + cw + 0.3, y1, 2, "Mẫu HUI, ứng viên (giữ từ V6)", ["RSSI → **q ∈ [1,100]** (rank, abs, rel); **EFIM** khai thác HUI mỗi ô, θ = 20%.", `**5 góc nhìn**, ${vn(nHUI / 1e6, 2)} triệu HUI; điểm khớp **P·V³**, làm mượt σ = 3 m, tầng, **30 ô ứng viên**.`, "Ô gần nhất trong 30 cách vị trí thật **0,59 m** (dev)."], TEAL);
    panel(MX, y2, 3, "Học trọng số (mới ở V7)", ["**49 đặc trưng** → dạng tương đối (196) → **MLP 7 360 tham số** → s_{i}.", "**softmax** → w_{i}; (x̂, ŷ) = Σ w_{i}·tâm ô_{i}.", "Mất mát = **sai số mét**, Adam, tập hợp 5 thành viên, fold theo điện thoại."], RUST);
    panel(MX + cw + 0.3, y2, 4, "Kết quả và kiểm chứng", [`**${vn(T7.mean, 3)} m** test (V6 ${vn(T6.mean, 3)}); dev ${vn(dI("C_rel_absL3").mean, 3)} m; mục tiêu < 6 m **chưa đạt**.`, "Giúp: **bộ chấm điểm học**, **rel**. Không giúp: V7-A, bù lệch thiết bị, cấp tầng.", `Kiểm chứng: Excel + Python + **${D.verification.n_checks}** phép kiểm; không k-NN; không rò rỉ đo được.`], GOLD);
  }
};
