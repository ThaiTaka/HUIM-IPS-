// Phần 2 của Slide_HUIM_IPS_V7_day_du.pptx: chương 2 "Từ vân tay đến mẫu HUI" và chương 3 "Điểm khớp, tầng, 30 ô ứng viên".
module.exports = function part2(c) {
  const { pres, slide, divider, img, as, bullets, text, ann, stat, card, table, tb, callout, fcard, head, chartBase, algoSlide, vn, vnd, pct, tr, dI,
    MX, SW, W, F, INK, NAVY, TEAL, RUST, GREY, GOLD, SOFT, SOFT2, CARD, D, E, DS } = c;
  const T7 = tr("C_rel_absL3"), T6 = tr("V6"), T6r = tr("V6r");
  const FIN = D.test_json.C_rel_absL3;
  const EX = D.example, C1 = EX.cell1, HX = C1.hui_example, G = E.grid, CL = E.cells;
  const HC = D.config.hui.final_hui_counts;
  const nHUI6 = HC.rank + HC.rank_L3 + HC.abs, nHUI7 = nHUI6 + HC.rel + HC.abs_L3;
  const wap = (n) => "WAP" + String(n).padStart(3, "0");
  const W3 = EX.cells.filter((z) => [351, 348, 352].includes(z.cell)).reduce((a, z) => a + z.w6, 0);   // tổng trọng số V6 của 3 ô xa (hàng 335)

  // ================================================================== CHƯƠNG 2
  divider(1, "Từ vân tay đến mẫu HUI", ["Bước 1: quy đổi cường độ thành lợi ích q", "Bước 2: mỗi ô có tập mẫu AP đặc trưng (HUI)", "Vì sao EFIM, θ = 20% và 5 góc nhìn"],
`KỊCH BẢN (30 giây)
NÓI: Chương này trả lời câu hỏi: làm sao biến 19 937 lần đo thành một "hồ sơ" gọn cho từng ô? Em làm ba việc. Một, quy đổi độ mạnh tín hiệu thành một con số gọi là lợi ích q. Hai, với mỗi ô, khai thác các tổ hợp bộ phát hay cùng mạnh với nhau, gọi là HUI, bằng thuật toán EFIM. Ba, làm việc đó từ năm góc nhìn khác nhau.
LƯU Ý: Em không giảng lại lý thuyết HUIM. Em chỉ nói những gì cần để hiểu công thức đang dùng và vì sao chọn.
CHUYỂN Ý: Bước đầu tiên: đổi RSSI thành lợi ích q.`);

  // ---- Bước 1: q
  algoSlide("Bước 1 · Lợi ích q", "Bước 1: quy đổi cường độ RSSI thành lợi ích q ∈ [1, 100]", {
    formula: "fm_util3", fh: 2.2, fw: 7.2,
    syms: [["q(i,T)", "lợi ích của AP i trong vân tay T: số nguyên 1…100; bằng 0 nếu không nghe thấy"], ["RSSI_{T}(i)", "cường độ của AP i trong T (dBm)"],
      ["n_{T}, r_{T}(i)", "số AP nghe được trong T; hạng của AP i (1 = mạnh nhất)"], ["L, H", "RSSI yếu nhất và mạnh nhất: −104 và 0 dBm"], ["W", "cửa sổ 40 dB của rel"],
      ["clip(·,0,1)", "cắt về đoạn [0, 1]"]], symSize: 12.5,
    ex: "**Tự kiểm hàng 335, WAP098 (−54 dBm, mạnh nhất trong 10 AP):** abs = 1 + 99 × (−54 + 104)/104 = 48,6 → **49**; rel = 1 + 99 × clip((0 + 40)/40) = **100**; rank (r = 1, n = 10) = 1 + 99 × (10 − 1)/(10 − 1) = **100**",
    why: ["EFIM cần lợi ích là **số nguyên dương**; AP không nghe (0) phải khác AP nghe yếu (≥ 1), nên không dùng RSSI âm trực tiếp",
      "**Ba cách quy đổi** vì điện thoại đọc RSSI lệch nhau: rank bất biến mọi biến đổi đơn điệu; rel bất biến lệch hằng số; abs giữ độ mạnh tuyệt đối",
      "Dùng cả ba vì mỗi cách mắc lỗi khác nhau, bổ sung cho nhau"], whySize: 12,
    nums: [["1…100; 0 = không nghe", "quy ước", "thang số nguyên"], ["−104; 0 dBm", "đếm", "RSSI nhỏ/lớn nhất có thật"], ["W = 40 dB", "quy ước", "chưa dò; 89,9% lần đọc trong 40 dB"], ["rank / abs / rel", "dev", "7,669 / 7,685 / 8,362 (đứng riêng)"]],
    numCols: [1.75, 0.8, 3.42],
  },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Bước đầu tiên là đổi cường độ tín hiệu RSSI thành một con số dương gọi là lợi ích q, từ 1 đến 100. Em có ba cách đổi: rank, abs và rel. Công thức ở bên trái; các ký hiệu được chú thích ở bên phải.
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ đến một cuộc thi chạy 100 mét với 10 vận động viên. Rank là "thứ hạng": người nhanh nhất được 100 điểm, người chậm nhất được 1 điểm. Abs là "thời gian tuyệt đối": ai chạy nhanh bao nhiêu giây thì được điểm tương ứng. Rel là "chậm hơn người nhất bao nhiêu giây": người nhất được 100, ai chậm hơn 40 giây trở lên chỉ còn 1 điểm. Giờ giả sử hôm đó đồng hồ của sân bị chậm đều 2 giây cho mọi người: thời gian tuyệt đối (abs) bị sai, nhưng thứ hạng (rank) và khoảng cách so với người nhất (rel) vẫn nguyên. Đó chính xác là chuyện điện thoại đọc lệch RSSI.
TỰ KIỂM: Hàng 335 có WAP098 ở −54 dBm. Theo abs: 1 cộng 99 nhân (−54 + 104) chia 104 bằng 48,6, làm tròn là 49. Theo rel: AP mạnh nhất trong vân tay nên điểm là 100. Theo rank: hạng 1 trong 10 AP nên cũng 100.
VÌ SAO CHỌN: Thứ nhất, thuật toán khai thác mẫu cần lợi ích là số nguyên dương, và "không nghe thấy" phải là 0, khác "nghe yếu" là 1; nếu dùng thẳng RSSI âm thì không được. Thứ hai, vì sao ba cách: máy khác nhau đọc lệch nhau, nên em dùng cả ba để các cách bù lỗi cho nhau. Khi đứng riêng, rank cho sai số dev thấp nhất 7,669 mét, abs 7,685, rel 8,362; vì vậy rank là "nền".
CÁC CON SỐ: −104 và 0 dBm là giá trị nhỏ nhất và lớn nhất thật sự có trong dữ liệu. Thang 1 đến 100 là quy ước. Cửa sổ 40 dB em chọn trước và CHƯA dò lưới; kiểm lại thì 89,9% lần đọc nằm trong 40 dB so với bộ phát mạnh nhất cùng vân tay.
CHUYỂN Ý: Em cho thầy cô xem ví dụ số cụ thể.`);

  // ---- ví dụ q của hàng 335 + mức
  {
    const s = slide("Bước 1 · Ví dụ", "Ví dụ: hàng 335 thành giao dịch, và độ bền khi máy đọc lệch",
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Đây là vân tay hàng 335 sau khi quy đổi. Cột đầu là RSSI, ba cột tiếp theo là lợi ích theo rank, abs, rel. Hai cột cuối mô phỏng trường hợp điện thoại đọc thấp hơn 10 dB cho mọi bộ phát.
VÍ DỤ ĐỜI THƯỜNG: Một vân tay giống như một hóa đơn ở quán: mỗi bộ phát là một món, q là "số tiền" của món đó. Hóa đơn này có 10 món: WAP098 và WAP099 là hai món "đắt tiền" (q = 100 và 89 theo rank), WAP486 và WAP489 là món tầm trung.
ĐỌC BẢNG: Nhìn hai cột cuối. Khi máy đọc thấp hơn 10 dB, giá trị abs của WAP098 tụt từ 49 xuống 39 — máy lệch thì abs bị sai theo. Trong khi đó rank vẫn là 100 và rel vẫn là 100. Nghĩa là rank và rel "miễn nhiễm" với kiểu lệch này. Vì thế em không bỏ cách nào: abs mang thông tin độ mạnh tuyệt đối, rank và rel bền với máy lạ.
BA MỨC: Em còn chia lợi ích q thành 3 mức: thấp (1 đến 34), vừa (35 đến 67), cao (68 đến 100) bằng công thức ℓ ở khung bên trái. Khi đó mỗi bộ phát ở mức khác nhau được coi là hai "món" khác nhau: bộ phát WAP098 ở mức cao khác với WAP098 ở mức thấp. Cách này cho một góc nhìn chi tiết hơn mà em gọi là abs-L3.
TỰ KIỂM MỨC: q = 34 thì (34−1)/100×3 = 0,99, lấy phần nguyên 0 là thấp; q = 35 thì 1,02, mức vừa; q = 68 thì 2,01, mức cao.
VÌ SAO 3 MỨC: Em chỉ thử mức 3 và mức 1 (không chia), chưa quét số mức khác; đây là điểm em ghi nhận là chưa dò.
CHUYỂN Ý: Có giao dịch rồi, em khai thác các mẫu đặc trưng của từng ô.`);
    const sel = EX.aps.slice(0, 6);
    const rows = sel.map((a) => [wap(a.ap), vn(a.rssi, 0), a.q_rank, a.q_abs, a.q_rel, a.q_abs_shift, a.q_rank_shift === a.q_rank && a.q_rel_shift === a.q_rel ? "không đổi" : "đổi"]);
    head(s, `Hàng ${EX.src_row}: 6 trong ${EX.n_ap} AP mạnh nhất`, MX, 1.4, 7.6);
    const yb = tb(s, ["AP", "RSSI", "q rank", "q abs", "q rel", "abs (máy −10 dB)", "rank, rel"], rows, MX, 1.8, 8.0, [1.2, 0.9, 0.95, 0.95, 0.95, 1.85, 1.2], { size: 12.5, minH: 0.34, align: ["left", "right", "right", "right", "right", "right", "center"] });
    text(s, `**Giao dịch T** = { ${EX.aps.slice(0, 5).map((a) => `${wap(a.ap)}: ${a.q_rank}`).join(";  ")} … } (q theo rank); phần còn lại của 520 giá trị là 0 (không nghe thấy).`, MX, yb + 0.12, 8.0, 0.7, { fontSize: 13.5 });
    fcard(s, "fm_level", MX + 8.3, 1.4, SW - MX - (MX + 8.3), 1.75);
    ann(s, [["ℓ(i,T)", "mức cường độ: 0 thấp, 1 vừa, 2 cao"], ["⌊·⌋", "lấy phần nguyên"], ["(i, ℓ)", "mục của góc nhìn abs-L3"]], MX + 8.3, 3.3, SW - MX - (MX + 8.3), 1.2, 13);
    card(s, MX + 8.3, 4.6, SW - MX - (MX + 8.3), 2.25, SOFT2, "Tự kiểm mức", RUST, RUST);
    bullets(s, ["q = 34: (34 − 1)/100 × 3 = 0,99 → mức 0 (thấp)", "q = 35: 1,02 → mức 1 (vừa)", "q = 68: 2,01 → mức 2 (cao)", "Chỉ thử 1 và 3 mức; **chưa quét** số mức khác"], MX + 8.52, 5.1, SW - MX - (MX + 8.3) - 0.4, 1.7, 12.5, INK, 3);
    card(s, MX, yb + 0.9, 8.0, 6.85 - (yb + 0.9), SOFT, null, TEAL, TEAL);
    text(s, "**Đọc hai cột cuối:** máy đọc thấp hơn 10 dB thì **abs đổi** (WAP098: 49 → 39) nhưng **rank và rel giữ nguyên**: hai cách này bền với máy lạ, abs mang thêm độ mạnh tuyệt đối.", MX + 0.25, yb + 1.0, 7.5, 6.85 - (yb + 1.1), { fontSize: 13.5, valign: "middle" });
  }

  // ---- Bước 2: HUI của ô
  algoSlide("Bước 2 · HUI của từng ô", "Bước 2: mỗi ô có một tập mẫu AP đặc trưng (HUI)", {
    formula: "fm_cell", fh: 2.2, fw: 6.3,
    syms: [["u(X)", "lợi ích của tổ hợp AP X = tổng q(i,T) của các AP trong X, cộng trên mọi vân tay T của ô chứa đủ X"], ["D_{c}, u(D_{c})", "các vân tay của ô c; tổng lợi ích của chúng"],
      ["θ, minUtil_{c}", "tỷ lệ 20% và ngưỡng tối thiểu của ô c"], ["HUI_{c}", "các tổ hợp X đạt u(X) ≥ minUtil_{c}: mẫu AP cùng mạnh của ô"],
      ["s(X), |X|", "số vân tay của ô chứa X; số AP trong X"], ["q̄_{c}(X)", "cường độ trung bình mỗi AP của X"], ["w(X)", "tỷ trọng của X trong tổng lợi ích HUI của ô"]], symSize: 11.5,
    ex: `**Ví dụ ô ${C1.cell} (tầng ${EX.pred_bf}):** ${vn(C1.n_huis, 0)} HUI. Một HUI = {${HX.items_ap.map(wap).join(", ")}}: u = ${vn(HX.u, 0)}, support = ${HX.support}, |X| = ${HX.n} ⇒ q̄ = ${vn(HX.u, 0)} / (${HX.support} × ${HX.n}) = **${vn(HX.q_bar, 2)}**`,
    why: ["Một AP riêng lẻ **không đặc trưng** (nghe được ở nhiều nơi); **tổ hợp AP cùng mạnh** thì đặc trưng hơn nhiều",
      "Dùng **lợi ích** (độ mạnh), không chỉ đếm tần suất: AP mạnh có trọng lượng lớn hơn",
      "Mô hình chỉ gồm mẫu và vị trí ô: **không lưu vân tay**, đúng ràng buộc không k-NN"],
    nums: [["θ = 20%", "dev+ngân sách", "xem slide EFIM tiếp theo"], [`933 ô; ${vn(CL.mean_transactions, 2)} vân tay/ô`, "đếm", "19 861 / 933"], [`${vn(CL.mean_huis, 0)} HUI/ô`, "đếm", `${vn(CL.total_huis, 0)} / 933 (mô hình rank)`]],
    numCols: [1.75, 1.0, 3.2],
  },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Bây giờ em có 933 ô, mỗi ô có khoảng 21 vân tay, mỗi vân tay là một "hóa đơn" các bộ phát với lợi ích q. Với mỗi ô, em tìm những tổ hợp bộ phát hay cùng mạnh với nhau; những tổ hợp đủ lớn gọi là HUI — tập mục có lợi ích cao.
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ đến một quán trà sữa. Mỗi hóa đơn là một vân tay; mỗi món là một bộ phát; tiền của món là lợi ích q. Quán này có "combo" trà sữa, trân châu, bánh flan hay được gọi cùng nhau và chi nhiều tiền; quán bên cạnh lại có combo khác. Nhìn một hóa đơn lạ, ta đoán được "hóa đơn này của quán nào" nhờ combo, chứ không phải nhờ một món lẻ như trà sữa, vì quán nào cũng bán trà sữa. Bộ phát Wi-Fi cũng vậy: một bộ phát nghe được ở nhiều nơi, nhưng tổ hợp sáu bộ phát cùng mạnh thì rất riêng cho một vị trí.
CÔNG THỨC: Ngưỡng minUtil của ô c bằng θ nhân tổng lợi ích của ô, với θ bằng 20 phần trăm. Một tổ hợp X là HUI nếu lợi ích u(X) đạt ngưỡng. Với mỗi HUI em giữ lại: cường độ trung bình mỗi bộ phát q-gạch và tỷ trọng w(X).
VÍ DỤ SỐ: Ô 351 ở tòa 2 tầng 1 có ${vn(C1.n_huis, 0)} HUI. Lấy một HUI gồm sáu bộ phát: WAP070, 098, 099, 117, 118, 489. Tổ hợp này xuất hiện trong 16 vân tay của ô, tổng lợi ích 7 032. Cường độ trung bình mỗi bộ phát là 7 032 chia (16 nhân 6) bằng 73,25. Thầy cô có thể bấm máy tính để kiểm.
VÌ SAO CHỌN HUI: Ba lý do. Một, tổ hợp đặc trưng hơn bộ phát lẻ. Hai, dùng lợi ích để quan tâm đến độ mạnh, không chỉ đếm xuất hiện. Ba, mô hình chỉ lưu các mẫu, không lưu vân tay, nên đúng ràng buộc không dùng k-NN.
CHUYỂN Ý: Làm sao khai thác nhanh và chính xác? Em dùng EFIM.`);

  // ---- EFIM + theta
  algoSlide("Bước 2 · EFIM", "Vì sao dùng EFIM, θ = 20% và ngân sách 10 s / 10 000 HUI", {
    formula: "fm_efim", fh: 2.2, fw: 6.6,
    syms: [["TWU(X)", "tổng lợi ích các vân tay chứa X; nếu < minUtil thì loại X và mọi tập chứa X"], ["TU(T)", "tổng lợi ích của vân tay T"],
      ["α, z", "tiền tố đang mở rộng và AP z định thêm vào"], ["re(α,T)", "lợi ích còn lại của T sau α"], ["lu(α,z), su(α,z)", "hai chặn trên: nếu < minUtil thì cắt z hoặc cắt cả nhánh"]], symSize: 12,
    ex: `**Ví dụ tự nâng ngưỡng (ô 1):** ${CL.cell1.n_attempts} lần chạy, θ = 20 → 25 → 31,25 → **${vn(CL.cell1.theta_used_pct, 4)}%** (nhân 1,25 mỗi lần vượt ngân sách). ${pct(CL.share_escalated, 1)} số ô phải nâng ít nhất một lần; θ thực dùng trung bình **${vn(CL.mean_theta_used_pct, 2)}%**`,
    why: ["Cần khai thác **chính xác** (không bỏ sót HUI) cho 933 ô × 5 góc nhìn: EFIM là thuật toán chính xác, nhanh và tiết kiệm bộ nhớ (Zida và cộng sự, 2015)",
      "Tự cài bằng Python và **kiểm chứng**: 85 test so EFIM với duyệt vét cạn cho cùng HUI, lợi ích, support",
      "Không sinh–kiểm mọi tổ hợp: số tổ hợp tăng theo cấp số mũ (2^{520})"], whySize: 12,
    nums: [["θ = 20%", "dev+ngân sách", "10% hơn 0,6 m nhưng ~25 phút/fold"], ["10 s / 10 000 HUI", "ngân sách", `lần chạy cuối ≤ ${vn(CL.max_runtime_s, 2)} s`], ["× 1,25", "ngân sách", "nâng ngưỡng khi vượt ngân sách"]],
    numCols: [1.7, 1.0, 3.2],
  },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Để khai thác các mẫu HUI em dùng thuật toán EFIM. EFIM là thuật toán khai thác chính xác, nghĩa là không bỏ sót HUI nào, và nhanh nhờ cắt tỉa. Em tự cài đặt bằng Python và kiểm chứng bằng 85 bài test so sánh với duyệt vét cạn trên dữ liệu nhỏ: cùng tập HUI, cùng lợi ích, cùng support.
VÍ DỤ ĐỜI THƯỜNG: Giả sử cần tìm combo trong thực đơn 520 món. Nếu thử mọi tổ hợp thì có hai mũ 520 khả năng, nhiều hơn số nguyên tử trong vũ trụ. EFIM giống một người tính nhẩm giỏi: trước khi thử một nhánh, họ cộng thử "kể cả lấy hết những món còn lại thì tối đa cũng chỉ ra ngần này doanh thu"; nếu con số tối đa đó vẫn chưa tới 20 phần trăm tổng doanh thu thì bỏ cả nhánh, khỏi thử nữa. TWU, lu và su trong công thức chính là ba cách tính "con số tối đa" đó, từ thô đến tinh.
VÌ SAO CHỌN EFIM: Em cần khai thác 933 ô nhân 5 góc nhìn mà không được bỏ sót mẫu nào; bài báo EFIM báo cáo nhanh hơn các thuật toán trước nhiều bậc độ lớn và tiết kiệm bộ nhớ.
VÌ SAO θ BẰNG 20 PHẦN TRĂM: Em nói thật: trong thí nghiệm thăm dò, θ bằng 10 phần trăm tốt hơn 20 phần trăm khoảng 0,6 mét (7,138 so với 7,742 mét ở cấu hình tốt nhất), nhưng mất khoảng 25 phút khai thác cho mỗi fold. Em chọn 20 phần trăm như một thỏa hiệp giữa chất lượng và chi phí, không phải điểm tối ưu trên dev.
NGÂN SÁCH: Mỗi ô tối đa 10 giây hoặc 10 000 HUI. Nếu vượt thì nhân θ lên 1,25 lần và chạy lại, không bao giờ giữ một tập bị cắt cụt. Ví dụ ô số 1 phải chạy 4 lần: 20, 25, 31,25 rồi 39,0625 phần trăm. Có ${pct(CL.share_escalated, 1)} số ô phải nâng ngưỡng, nên θ thực dùng trung bình là ${vn(CL.mean_theta_used_pct, 2)} phần trăm, cao hơn 20 phần trăm danh nghĩa. Em xin ghi nhận điều này.
CHUYỂN Ý: Em còn làm việc này từ năm góc nhìn khác nhau.`);

  // ---- 5 góc nhìn
  {
    const s = slide("Bước 2 · Năm góc nhìn", `Năm góc nhìn HUI: ${vn(nHUI7 / 1e6, 2)} triệu mẫu từ 5 lần khai thác`,
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: Mỗi "góc nhìn" là một lần khai thác EFIM riêng với cách quy đổi lợi ích khác nhau. V6 có ba góc nhìn: rank, rank mức 3 và abs, tổng khoảng 7,33 triệu mẫu. V7 thêm hai góc nhìn mới: rel và abs mức 3, nâng tổng lên ${vn(nHUI7 / 1e6, 2)} triệu mẫu.
VÍ DỤ ĐỜI THƯỜNG: Giống như năm giám khảo cùng chấm một thí sinh nhưng mỗi người chú ý một khía cạnh: người nhìn thứ hạng, người nhìn điểm tuyệt đối, người nhìn khoảng cách so với người giỏi nhất, người nhìn từng mức giỏi–trung bình–yếu. Một người có thể nhìn sót, năm người cùng nhìn thì chắc hơn.
VÌ SAO THÊM REL VÀ ABS-L3: Em thêm rel vì nó bất biến khi điện thoại đọc lệch hằng số, là điểm yếu của abs. Kết quả thật: thêm rel làm sai số dev giảm 0,195 mét, tốt hơn ở cả 6 trên 6 fold; khoảng tin cậy không chứa 0. Thêm abs-L3 chỉ giảm thêm 0,034 mét, tốt hơn ở 4 trên 6 fold, khoảng tin cậy có chứa 0. Em giữ abs-L3 vì quy tắc chọn đã khai báo trước (thấp hơn ở dev và tốt hơn ở ít nhất 4 trên 6 fold), nhưng nói rõ lợi ích này nhỏ và không có ý nghĩa thống kê riêng.
VÌ SAO RANK-L3 CÓ ÍT HUI HƠN RANK (nếu được hỏi): Ở rank, mỗi mục chỉ là bộ phát. Ở rank-L3 mỗi mục là cặp (bộ phát, mức), nên bộ phát 98 ở mức cao khác bộ phát 98 ở mức thấp. Lợi ích của mục vẫn là q và tổng lợi ích của ô không đổi, nên ngưỡng minUtil giữ nguyên; nhưng một tổ hợp (bộ phát, mức) chỉ xuất hiện trong những vân tay mà bộ phát đó đúng ở mức ấy, nên gom được ít lợi ích hơn và ít tổ hợp vượt ngưỡng. Đây không phải mất thông tin: mẫu ít hơn nhưng cụ thể hơn, ví dụ "bộ phát 98 mạnh cùng bộ phát 486 yếu". Số HUI còn chịu ảnh hưởng của cơ chế nâng ngưỡng khi vượt ngân sách, phần này em chưa tách riêng. Ba mức là quy ước, em chỉ thử mức 1 và mức 3, chưa quét số mức khác.
CON SỐ: Số mẫu là kết quả của EFIM, không phải tham số em chọn. Có thể tự kiểm: cộng cột số HUI của 933 ô trong tệp cell_runs.csv cho mô hình rank ra ${vn(HC.rank, 0)}.
CHUYỂN Ý: Có 5 bộ hồ sơ rồi, giờ đến việc chấm điểm: vân tay mới giống hồ sơ nào?`);
    const rows = [["rank", "V4", "thứ hạng cường độ", vn(HC.rank, 0)], ["rank-L3", "V5", "rank, mục = (AP, mức 1–3)", vn(HC.rank_L3, 0)], ["abs", "V6", "cường độ tuyệt đối", vn(HC.abs, 0)],
      ["rel", "V7-C1", "so với AP mạnh nhất (W = 40 dB)", vn(HC.rel, 0)], ["abs-L3", "V7-C2", "abs, mục = (AP, mức 1–3)", vn(HC.abs_L3, 0)], ["Tổng V6 → V7", "", "", `${vn(nHUI6, 0)} → ${vn(nHUI7, 0)}`]];
    head(s, "Mỗi góc nhìn là một lần EFIM với cách quy đổi lợi ích khác nhau", MX, 1.4, W);
    const yb = tb(s, ["Góc nhìn", "Thêm ở", "Lợi ích nội q", "Số HUI (mô hình cuối)"], rows, MX, 1.8, W, [1.9, 1.5, 5.0, W - 8.4], { size: 13.5, minH: 0.4, align: ["left", "center", "left", "right"], hl: (i) => i === 3 || i === 4 });
    const cw = (W - 0.4) / 2;
    card(s, MX, yb + 0.25, cw, 6.85 - yb - 0.25, SOFT, "Vì sao thêm rel và abs-L3", TEAL, TEAL);
    bullets(s, ["**rel** bất biến khi máy đọc lệch hằng số (điểm yếu của abs)", `Thêm rel: ${vnd(dI("C_rel").mean - dI("B_base").mean, 3)} m (dev), **6/6 fold**, KTC [−0,283; −0,106] không chứa 0`, `Thêm abs-L3: ${vnd(dI("C_rel_absL3").mean - dI("C_rel").mean, 3)} m, 4/6 fold, KTC [−0,087; +0,054] **chứa 0**`], MX + 0.22, yb + 0.75, cw - 0.4, 6.85 - yb - 0.85, 13, INK, 4);
    card(s, MX + cw + 0.4, yb + 0.25, cw, 6.85 - yb - 0.25, SOFT2, "Vì sao các con số", RUST, RUST);
    bullets(s, [`Số HUI là **kết quả của EFIM**, không phải tham số chọn (tự kiểm: Σ cột n_huis của 933 ô = ${vn(HC.rank, 0)} cho rank)`, "**Vì sao rank-L3 có ít HUI hơn rank:** mục là (AP, mức) nên mỗi tổ hợp chỉ gom được vân tay ở đúng mức, còn minUtil giữ nguyên ⇒ ít tổ hợp vượt ngưỡng; mẫu ít nhưng **cụ thể hơn**", "3 mức là quy ước (chỉ thử 1 và 3); giữ abs-L3 theo quy tắc khai báo trước"], MX + cw + 0.62, yb + 0.7, cw - 0.4, 6.85 - yb - 0.8, 12, INK, 3);
  }

  // ================================================================== CHƯƠNG 3
  divider(2, "Điểm khớp, tầng và 30 ô ứng viên", ["Bước 3: điểm khớp P·V³ giữa vân tay mới và từng ô", "Bước 4: làm mượt không gian và chọn tầng", "Bước 5: 30 ô ứng viên; vì sao V6 chưa đủ"],
`KỊCH BẢN (30 giây)
NÓI: Có hồ sơ HUI của 933 ô rồi, giờ đến lúc định vị. Khi có một vân tay mới, em chấm điểm xem nó giống hồ sơ của từng ô đến mức nào, làm mượt điểm theo không gian, chọn tầng và giữ lại 30 ô tốt nhất làm ứng viên. Phần này giữ nguyên từ V6; phần mới của V7 nằm ở chương sau.
CHUYỂN Ý: Công thức chấm điểm khớp.`);

  // ---- P, V
  algoSlide("Bước 3 · Điểm khớp", "Bước 3: điểm khớp P·V³ giữa vân tay mới T và hồ sơ HUI của ô c", {
    formula: "fm_match", fh: 2.7, fw: 7.2,
    syms: [["T", "vân tay mới cần định vị"], ["X", "một mẫu AP (HUI) của ô c"], ["ρ(X,T)", "tỷ lệ AP của X có mặt trong T (0…1)"], ["q_{T}(X), q̄_{c}(X)", "cường độ của T và cường độ trung bình của ô, trên X"],
      ["agree", "độ khớp cường độ (0,1]; τ = 20"], ["P_{c}(T)", "điểm mẫu; γ = 2"], ["I_{c}", "mọi AP xuất hiện trong ít nhất một HUI của ô c"], ["V_{c}(T)", "độ phủ: phần cường độ của T mà ô c giải thích"], ["score", "P·V³ (β = 3)"]], symSize: 11.5,
    ex: `**Ví dụ ô ${C1.cell}, hàng ${EX.src_row}:** P = ${vn(C1.P, 4)} (tổng 8 535 số hạng); V = ${vn(Math.round(C1.V * C1.q_sum), 0)} / ${C1.q_sum} = ${vn(C1.V, 4)}; P·V³ = ${vn(C1.P, 4)} × ${vn(C1.V, 4)}³ = **${vn(C1.S_raw, 4)}**`,
    exH: 0.55,
    why: ["**P** hỏi: vân tay chứa bao nhiêu mẫu đặc trưng của ô, đúng cường độ? **V** hỏi: ô giải thích được bao nhiêu phần vân tay?", "Nhân P và V: hai điều kiện phải cùng cao; V³ để độ phủ chi phối"],
    nums: [["γ = 2", "dev", "(1,20): 7,838; (2,20): 7,653"], ["τ = 20", "dev", "(1,40): 7,748; (2,20): 7,653"], ["β = 3", "dev", "β = 1: 7,993; β = 3: 7,653"]],
    numCols: [1.2, 0.75, 2.45], numSize: 11, leftW: 6.0,
  },
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Khi có vân tay mới T, em đối chiếu với từng ô c bằng hai đại lượng. Đại lượng P cho biết vân tay chứa bao nhiêu mẫu đặc trưng của ô, và cường độ có khớp không. Đại lượng V cho biết ô giải thích được bao nhiêu phần của vân tay. Điểm cuối cùng của ô là P nhân V mũ ba.
VÍ DỤ ĐỜI THƯỜNG: Hãy quay lại quán trà sữa. Đưa cho bạn một hóa đơn lạ, hỏi hóa đơn này của quán A hay quán B. Điểm P là: "hóa đơn này chứa bao nhiêu combo đặc trưng của quán A, và số lượng có đúng thói quen quán A không?". Điểm V là: "quán A giải thích được bao nhiêu phần trăm số tiền trên hóa đơn này?". Nếu hóa đơn có nhiều món mà quán A không bán, thì V thấp dù P cao; ngược lại nếu hóa đơn chỉ có một món phổ biến thì P thấp. Cần cả hai cùng cao thì mới chắc là quán A.
CÁC KÝ HIỆU: Với mỗi mẫu X của ô, rho là tỷ lệ bộ phát của X có mặt trong vân tay; agree đo cường độ của vân tay có gần cường độ trung bình của ô không, đo bằng hàm mũ giảm dần theo độ lệch, chia cho tau bằng 20. Mỗi mẫu được cân bằng tỷ trọng w(X). P là tổng của w nhân rho mũ gamma nhân agree trên tất cả các mẫu của ô, với gamma bằng 2. V là tổng cường độ của các bộ phát trong vân tay mà ô có biết đến, chia cho tổng cường độ của cả vân tay.
VÍ DỤ SỐ: Ô 351 với vân tay hàng 335: P bằng 0,1817 là tổng của 8 535 số hạng rất nhỏ, mỗi số hạng cỡ 10 mũ trừ 5. Tổng cường độ vân tay là 505; các bộ phát WAP082, 418 và 486 không thuộc mẫu nào của ô 351 nên V bằng 414 chia 505 bằng 0,8198. Điểm P·V³ bằng 0,1817 nhân 0,8198 mũ ba, ra 0,1001.
VÌ SAO CHỌN: P và V bổ sung nhau; em nhân vì hai điều kiện phải cùng đúng. Các hằng số gamma, tau, beta chọn bằng lưới trên dev (slide tiếp theo có số liệu).
CHUYỂN Ý: Vì sao lại là 2, 20 và 3? Em giải thích ở slide tiếp.`);

  // ---- vì sao gamma tau beta
  {
    const gt = G.gamma_tau, be = G.beta;
    const s = slide("Bước 3 · Các hằng số", "Vì sao γ = 2, τ = 20, β = 3: bằng chứng từ lưới trên dev",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Ba hằng số này em chọn bằng lưới trên dev ở giai đoạn V4: ${vn(G.n_configurations, 0)} cấu hình, nghĩa là hai cách quy đổi lợi ích, ba cặp (gamma, tau), hai giá trị beta, bốn giá trị sigma, ba giá trị kf, năm giá trị m, bốn giá trị p; cấu hình có sai số dev thấp nhất là 7,6532 mét. Bảng bên phải là "đổi một tham số, giữ các tham số khác ở giá trị đã chọn".
VÍ DỤ ĐỜI THƯỜNG VÀ TRỰC GIÁC: Gamma bằng 2: nếu hóa đơn chỉ chứa một nửa combo của quán thì chỉ được một phần tư điểm (0,5 bình phương), không phải một nửa — phạt nặng việc khớp dở. Tau bằng 20: nếu độ mạnh lệch 10 đơn vị so với thói quen của quán thì điểm còn 0,607; lệch 20 đơn vị thì còn 0,368; với tau 40 thì chấp nhận lệch rộng hơn (0,779 và 0,607). Beta bằng 3: nếu quán giải thích được 80 phần trăm hóa đơn thì điểm là 0,8 mũ 3 bằng 0,512; chỉ 50 phần trăm thì 0,125; tức là ô nào không giải thích được vân tay bị phạt rất nặng.
BẰNG CHỨNG: Với gamma, tau: ba cặp thử cho 7,838; 7,748 và 7,653 mét. Với beta: beta bằng 1 cho 7,993, beta bằng 3 cho 7,653 mét, tức là làm độ phủ chi phối giúp tốt hơn 0,34 mét.
THÀNH THẬT: Lưới này thô. Em chỉ thử ba cặp (gamma, tau) nên chưa thử gamma bằng 2 với tau bằng 40; beta chỉ thử 1 và 3. Đây là sai số của ước lượng V4 chứ không phải của V7; V6 và V7 giữ nguyên các giá trị này mà chưa dò lại theo sai số V7.
CHUYỂN Ý: Tiếp theo là làm mượt theo không gian và chọn tầng.`);
    head(s, "Mỗi thành phần cư xử thế nào (tự tính bằng tay)", MX, 1.4, 7.2);
    const rows = [["ρ^{γ}, γ = 2", "khớp nửa mẫu (ρ = 0,5): γ = 1 → 0,50; **γ = 2 → 0,25**; khớp trọn → 1: phạt khớp dở"],
      ["exp(−Δq/τ), τ = 20", "Δq = 10: τ = 20 → **0,607**, τ = 40 → 0,779; Δq = 20: 0,368 / 0,607"],
      ["V^{β}, β = 3", "V = 0,8: β = 1 → 0,800; **β = 3 → 0,512**; V = 0,5: 0,500 / 0,125 ⇒ ô giải thích ít bị phạt nặng"],
      ["Vì sao nhân P và V", "P: ô chứa bao nhiêu mẫu mạnh của mình; V: ô giải thích bao nhiêu phần vân tay. Cả hai phải cao"]];
    const ym = tb(s, ["Thành phần", "Ví dụ số"], rows, MX, 1.8, 7.2, [1.9, 5.3], { size: 12.5 });
    head(s, "Dev: đổi một tham số, giữ phần còn lại (m)", MX + 7.5, 1.4, W - 7.5);
    const r2 = [...gt.map((x) => [`(γ, τ) = (${x.gamma}, ${x.tau})`, vn(x.dev_mean_m, 3)]), ...be.map((x) => [`β = ${x.beta}`, vn(x.dev_mean_m, 3)])];
    const yg = tb(s, ["Cấu hình", "Sai số dev"], r2, MX + 7.5, 1.8, W - 7.5, [2.7, 1.9], { size: 13, align: ["left", "right"], hl: (i) => i === 2 || i === 4 });
    text(s, `${vn(G.n_configurations, 0)} cấu hình = 2 lợi ích × 3 (γ,τ) × 2 β × 4 σ × 3 kf × 5 m × 4 p; cực tiểu dev = ${vn(G.selected_dev_mean_m, 4)} m.`, MX + 7.5, yg + 0.12, W - 7.5, 0.7, { fontSize: 12.5 });
    callout(s, "**Thừa nhận:** lưới thô (chưa thử γ = 2 với τ = 40; β chỉ 1 và 3). Đây là sai số của ước lượng V4 (7,65 m); V6/V7 giữ nguyên P, V làm đặc trưng và **chưa dò lại** các hằng số theo sai số V7.", Math.max(ym, yg + 0.85) + 0.2, 1.15, SOFT2, INK, 14);
  }

  // ---- làm mượt và tầng
  algoSlide("Bước 4 · Làm mượt và chọn tầng", "Bước 4: làm mượt không gian (σ = 3 m) và chọn tầng", {
    formula: "fm_smooth", fh: 2.1, fw: 7.4,
    syms: [["S_{c}(T)", "điểm của ô c sau làm mượt"], ["K(c′,c)", "nhân Gauss theo khoảng cách ô; chỉ cùng tầng; chuẩn hóa theo hàng"], ["d(c′,c)", "khoảng cách (m) giữa tâm hai ô"], ["σ = 3 m", "độ rộng của nhân Gauss"], ["f(T)", "tầng được chọn"], ["top_{20}(f)", "20 ô điểm cao nhất của tầng f"]], symSize: 12,
    ex: `**Tự kiểm trọng số Gauss (σ = 3 m):** ô cách ${vn(E.nn_cells.median, 2)} m (trung vị khoảng cách tới ô gần nhất cùng tầng) → exp(−${vn(E.nn_cells.median, 2)}² / 18) = **0,760**; ô cách 6 m → exp(−36/18) = **0,135**. Chọn tầng đúng ${pct(FIN.floor_accuracy, 2)} (test), đúng tòa ${pct(FIN.building_accuracy, 2)}`,
    exH: 0.62,
    why: ["**Hàng xóm bỏ phiếu:** nếu nhiều ô sát nhau cùng khớp thì đáng tin hơn một ô lẻ", "Chọn tầng bằng **trung bình 20 ô tốt nhất**, để một ô nhiễu không quyết định cả tầng", "Chỉ làm mượt trong **cùng tầng**: sàn nhà là rào chắn tín hiệu"],
    nums: [["σ = 3 m", "dev", "σ = 0: 7,787; **3: 7,653**; 6: 7,773; 10: 8,094"], ["kf = 20", "dev", "kf = 3: 7,720; 10: 7,669; **20: 7,653** (biên lưới)"], ["trung vị 2,22 m", "đo", "khoảng cách ô gần nhất cùng tầng (933 ô)"]],
    numCols: [1.15, 0.7, 3.3], numSize: 11, leftW: 6.0,
  },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Sau khi chấm điểm từng ô, em làm hai việc. Việc thứ nhất là làm mượt điểm theo không gian: mỗi ô nhận thêm điểm từ các ô lân cận cùng tầng, với trọng số Gauss, nghĩa là ô càng gần thì càng ảnh hưởng nhiều. Việc thứ hai là chọn tầng: lấy 20 ô có điểm cao nhất của mỗi tầng, tính trung bình, tầng nào cao nhất thì được chọn.
VÍ DỤ ĐỜI THƯỜNG: Giống như bỏ phiếu ở một khu phố: nếu một căn nhà báo "nghi phạm ở đây" nhưng nhà hàng xóm bên cạnh đều im lặng thì ít đáng tin; nếu ba nhà liền kề cùng báo thì tin hơn nhiều. Làm mượt chính là cho hàng xóm bỏ phiếu giúp nhau. Còn chọn tầng giống như hỏi "tòa nhà nào có nhiều phòng nghi vấn nhất" và đếm top 20 để không bị một căn nhiễu đánh lừa. Chỉ làm mượt trong cùng tầng vì sàn nhà chắn sóng; hai ô sát nhau nhưng khác tầng không phải hàng xóm.
TỰ KIỂM: Khoảng cách từ một ô tới ô gần nhất cùng tầng có trung vị 2,22 mét. Với sigma bằng 3 mét, một ô cách 2,22 mét có trọng số exp trừ 2,22 bình phương chia 18, bằng 0,760; một ô cách 6 mét còn 0,135. Vậy sigma bằng 3 mét tương đương phạm vi một đến hai ô lân cận.
VÌ SAO CHỌN: Trong lưới sigma 0, 3, 6, 10 thì sigma bằng 3 cho sai số dev thấp nhất là 7,653 mét; sigma bằng 0 (không làm mượt) cho 7,787; sigma bằng 10 tệ hơn nhiều, 8,094. Với kf: 3, 10, 20 cho 7,720; 7,669; 7,653.
THÀNH THẬT: kf bằng 20 nằm ở biên trên của lưới, hơn kf bằng 10 chỉ 0,016 mét, nên coi là bão hòa chứ không phải tối ưu chính xác; em chưa thử các giá trị xen kẽ cho sigma.
KẾT QUẢ: Cách chọn tầng này cho độ chính xác tòa 99,91% và tầng 80,38% trên test. Em giữ nguyên quy tắc chọn tầng ở V7, nên V7 không cải thiện độ chính xác tầng; phần cải thiện đến từ việc chọn vị trí trong tầng.
CHUYỂN Ý: Còn lại 30 ô ứng viên của tầng đó.`);

  // ---- 30 ứng viên
  {
    const cd = D.cand_dev, bk = E.best_of_k.filter((x) => [1, 3, 5, 10, 20, 30].includes(x.K));
    const s = slide("Bước 5 · 30 ô ứng viên", "Bước 5: 30 ô ứng viên — HUI đã tìm đúng vùng",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Sau khi chọn tầng, em giữ lại 30 ô có điểm cao nhất của tầng đó làm ứng viên. Biểu đồ cột cho thấy: nếu em có một "tiên tri" biết vị trí thật và chọn ô gần nhất trong K ô ứng viên đầu tiên, thì khoảng cách trung bình là 7,52 mét khi K bằng 1, giảm xuống 1,53 mét khi K bằng 10, và chỉ còn 0,59 mét khi K bằng 30. Có 92,4 phần trăm vân tay mà trong 30 ứng viên có ô cách vị trí thật dưới 3 mét.
VÍ DỤ ĐỜI THƯỜNG: Giống như cảnh sát có danh sách 30 điểm nghi vấn trên bản đồ. Trong 30 điểm đó, hầu như luôn có điểm nằm sát hiện trường — gần như chỉ cách 0,6 mét. Nhưng cảnh sát không biết điểm nào là điểm đúng, nên phải đoán. Nếu cứ chọn điểm đứng đầu danh sách thì sai trung bình 7,5 mét; nếu lấy trung bình có trọng số như V6 thì sai 6,2 mét. Bài toán còn lại không phải là tìm vùng, mà là chia trọng số cho khéo.
VÌ SAO K BẰNG 30: Tiên tri cho thấy lợi ích giảm dần: từ K bằng 20 lên 30 chỉ tốt thêm 0,144 mét, trong khi bộ chấm điểm phải xử lý thêm ô. K bằng 30 em chọn từ V5; em chưa quét K theo sai số cuối cùng. Chú ý "tiên tri" dùng vị trí thật nên chỉ để đo trần, không phải kết quả thật.
Ý NGHĨA CHO V7: Vì trần chất lượng của 30 ứng viên rất cao (0,59 mét), còn kết quả thực chỉ 5,70 mét (dev), nên chỗ cải thiện lớn nhất là khâu chọn trọng số. Đó là lý do V7 thiết kế một bộ chấm điểm học trực tiếp.
CHUYỂN Ý: Trước khi giới thiệu V7, em nói ngắn gọn V6 đã làm gì.`);
    s.addChart(pres.charts.BAR, [{ name: "Ô gần nhất trong K ứng viên đầu (m)", labels: bk.map((x) => `K = ${x.K}`), values: bk.map((x) => Math.round(x.mean_m * 1000) / 1000) }],
      { ...chartBase(), x: MX, y: 1.4, w: 6.8, h: 4.35, barDir: "col", chartColors: [TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 12.5,
        valAxisMinVal: 0, valAxisMaxVal: 9, valAxisMajorUnit: 1, showLegend: false, showTitle: true, title: "Ô gần nhất trong K ứng viên đầu: khoảng cách tới vị trí thật (m, dev; dùng nhãn thật để đo trần)", barGapWidthPct: 45, titleFontSize: 12 });
    const x = MX + 7.1, w = SW - MX - x;
    stat(s, x, 1.4, w, `${vn(cd[1].mean_m)} m`, `ô gần nhất trong 30 ứng viên (dev); ${pct(cd[1].duoi_3m, 1)} vân tay có ô cách dưới 3 m`, TEAL, 34);
    stat(s, x, 2.85, w, `${vn(cd[0].mean_m)} m`, "nếu chỉ lấy ô điểm HUI cao nhất (dev)", NAVY, 34);
    stat(s, x, 4.3, w, `${vn(cd[2].mean_m)} m`, "tọa độ hợp nhất của V6* (dev)", RUST, 34);
    card(s, MX, 5.9, W, 0.95, SOFT2, null, RUST, RUST);
    text(s, `**Vì sao K = 30:** lợi ích giảm dần (K = 20 → 30 chỉ tốt thêm ${vn(bk.find((q) => q.K === 20).mean_m - bk.find((q) => q.K === 30).mean_m, 3)} m); chọn từ V5, **chưa quét K** theo sai số cuối. Trần 0,59 m so với 5,70 m thật ⇒ chỗ cải thiện là **chia trọng số**, nên V7 học trọng số.`, MX + 0.3, 5.95, W - 0.6, 0.85, { fontSize: 13.5, valign: "middle" });
  }

  // ---- V6
  algoSlide("Bước 5 · Đường cơ sở V6", "Đường cơ sở V6: dự đoán khoảng cách từng ô, đổi thành trọng số", {
    formula: "fm_v6", fh: 2.2, fw: 6.8,
    syms: [["φ_{c}", "33 đặc trưng HUI của ô ứng viên c"], ["g", "Gradient Boosting học trên log(1 + d), d = khoảng cách ô → vị trí thật"], ["d̂_{c}", "khoảng cách dự đoán của ô c"], ["λ = 2", "nhiệt độ cố định của trọng số"], ["top-20", "20 ô có d̂ nhỏ nhất"], ["a_{c}", "trọng số của ô c; tổng bằng 1"]], symSize: 12.5,
    ex: `**Hàng ${EX.src_row}:** V6 dồn trọng số vào các ô xa (351, 348, 352: tổng ${pct(W3, 0)}) nên sai **${vn(EX.v6.err_m, 2)} m**; V7 chuyển trọng số tới ô gần hơn và sai **${vn(EX.v7.err_m, 2)} m**. Test: V6 ${vn(T6.mean, 3)} m → V7 ${vn(T7.mean, 3)} m`, exH: 0.62,
    why: ["V6 là **đường cơ sở** để so sánh công bằng; V7 giữ ứng viên, tầng và đặc trưng HUI của V6", "**Hạn chế:** mục tiêu huấn luyện (log khoảng cách từng ô) **không phải** sai số tọa độ cuối; trọng số theo công thức cố định (m = 20, λ = 2)"],
    nums: [["300 cây, lr 0,06", "quy ước", "cấu hình GBM cố định, không có lưới"], ["m = 20, λ = 2", "dev", "bề mặt phẳng: chênh vài centimet"], ["33 cột", "đếm", "đặc trưng từ V5/V6"]],
    numCols: [1.6, 0.8, 3.0], leftW: 6.0,
  },
`KỊCH BẢN (khoảng 1,5 phút)
NÓI: V6 là phiên bản trước và cũng là đường cơ sở để so sánh. Với mỗi ô ứng viên, V6 dùng bộ hồi quy Gradient Boosting để dự đoán "ô này cách vị trí thật bao xa", dựa trên 33 đặc trưng HUI. Rồi V6 lấy 20 ô được dự đoán gần nhất và chia trọng số theo công thức cố định: trọng số tỷ lệ với e mũ trừ khoảng cách chia lambda, với lambda bằng 2.
VÍ DỤ ĐỜI THƯỜNG: Giống như 30 người làm chứng, mỗi người nói "tôi nghĩ hiện trường cách tôi X mét". V6 tin những người nói "tôi ở gần" nhiều hơn, theo một công thức cố định. Vấn đề: mỗi người được huấn luyện để đoán KHOẢNG CÁCH của mình cho chuẩn, chứ không phải để cho ra VỊ TRÍ HỢP NHẤT chuẩn. Một người đoán khoảng cách rất tốt vẫn có thể kéo vị trí chung về phía sai nếu trọng số chia không khéo.
VÍ DỤ SỐ: Với vân tay hàng 335, V6 dồn trọng số vào các ô 351, 348 và 352, là những ô cách xa vị trí thật, tổng ${vn(100 * W3, 0)} phần trăm, nên sai 7,99 mét. V7 chuyển trọng số tới các ô gần hơn nên sai 4,64 mét.
VỀ CÁC CON SỐ CỦA V6: Cấu hình GBM là cấu hình cố định, em không có lưới riêng cho nó. Với m và lambda: bề mặt sai số rất phẳng quanh cực tiểu, chỉ chênh vài centimet giữa các lựa chọn lân cận; V7 không còn dùng hai tham số này vì học trọng số trực tiếp.
KẾT QUẢ V6: sai số test là ${vn(T6.mean, 3)} mét (tái tạo ${vn(T6r.mean, 3)}).
CHUYỂN Ý: Từ đây em sang phần mới của V7: học trực tiếp trọng số.`);
};
