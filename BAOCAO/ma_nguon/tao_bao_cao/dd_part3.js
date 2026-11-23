// Phần 3 của Slide_HUIM_IPS_V7_day_du.pptx: chương 4 "Học trọng số 30 ô ứng viên" (phần mới của V7).
const fs = require("fs");
const path = require("path");

module.exports = function part3(c) {
  const { pres, slide, divider, img, as, bullets, text, ann, stat, card, badge, table, tb, callout, fcard, head, chartBase, algoSlide, vn, vnd, pct, tr, dI,
    MX, SW, W, F, INK, NAVY, TEAL, RUST, GREY, GOLD, SOFT, SOFT2, CARD, LINE, D, E, DS } = c;
  const T7 = tr("C_rel_absL3"), T6 = tr("V6"), T6r = tr("V6r");
  const EX = D.example, SC = E.scorer, EP = E.epochs;
  const rj = (f) => { try { return JSON.parse(fs.readFileSync(path.join(c.ROOT, f), "utf8")); } catch (e) { return null; } };
  const CMP = rj("results/huim_only/uji/v7/scorer_compare/summary.json"), TS = rj("results/huim_only/uji/v7/test_summary.json");
  const CR = CMP ? CMP.rows : null, FT = TS && TS.F_nopool ? TS.F_nopool : null;

  divider(3, "Học trọng số 30 ô ứng viên (phần mới của V7)", ["Ý tưởng: học trọng số bằng chính sai số mét", "49 đặc trưng → 196 đầu vào → MLP → softmax → tọa độ", "Mất mát, Adam, và huấn luyện không rò rỉ"],
`KỊCH BẢN (30 giây)
NÓI: Đây là phần mới của V7 và là nơi sai số giảm nhiều nhất. Em sẽ đi qua năm việc: mô tả mỗi ô ứng viên bằng 49 con số, đưa về dạng tương đối, cho một mạng nhỏ chấm điểm, đổi điểm thành trọng số bằng softmax, và huấn luyện mạng bằng chính sai số tính bằng mét. Cuối cùng là cách em huấn luyện để không rò rỉ dữ liệu.
CHUYỂN Ý: Trước hết là ý tưởng chung.`);

  // ---- ý tưởng
  {
    const s = slide("V7 · Ý tưởng", "Ý tưởng V7: học trực tiếp trọng số của 30 ô bằng sai số mét",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Hình bên trái là cách V6 làm: mỗi ô dự đoán khoảng cách của mình tới vị trí thật rồi đổi thành trọng số bằng công thức cố định. Hình bên phải là cách V7: một bộ chấm điểm cho điểm mỗi ô, softmax đổi điểm thành trọng số, tọa độ cuối là tổng có trọng số của tâm 30 ô; và toàn bộ được huấn luyện để làm cho tọa độ cuối sai ít nhất.
VÍ DỤ ĐỜI THƯỜNG: Hãy tưởng tượng một chiếc bàn phẳng, đặt 30 quả cân tại 30 vị trí ứng viên. Trọng tâm của chiếc bàn chính là tọa độ dự đoán. Quả cân nào nặng bao nhiêu do một "trọng tài" quyết định. V6 dùng một công thức cố định để cân; V7 cho trọng tài tự học cách cân sao cho trọng tâm rơi gần vị trí thật nhất. Giống như một đầu bếp: thay vì làm theo công thức cố định "2 muỗng đường", đầu bếp nếm thử rồi tự chỉnh để món ăn hợp khẩu vị người ăn, tức là học từ kết quả cuối.
VÌ SAO LÀM VẬY: Chương trước đã cho thấy: trong 30 ứng viên luôn có ô cách vị trí thật khoảng 0,59 mét, còn kết quả hợp nhất của V6 sai 6,2 mét. Chỗ cần cải thiện là cách chia trọng số. Đại lượng cần tối ưu chính là sai số tọa độ cuối, nên em dùng nó làm mục tiêu huấn luyện thay vì một đại lượng thay thế.
KẾT QUẢ SƠ BỘ: Chỉ riêng việc thay công thức cố định bằng bộ chấm điểm học trực tiếp (V7-B, vẫn dùng các đặc trưng cũ của V6) đã đưa sai số test từ ${vn(T6r.mean, 3)} xuống ${vn(tr("B_base").mean, 3)} mét. Thêm hai góc nhìn HUI mới đưa xuống ${vn(T7.mean, 3)} mét.
CHUYỂN Ý: Bộ chấm điểm nhận vào cái gì? Em mô tả 49 đặc trưng của mỗi ô.`);
    const half = (W - 0.4) / 2;
    card(s, MX, 1.4, half, 2.0, SOFT2, "V6: dự đoán khoảng cách từng ô", RUST, RUST);
    bullets(s, ["GBM học log(1 + d) cho **từng ô** (d: khoảng cách tới vị trí thật)", "Trọng số: a ∝ exp(−d̂/λ), **m = 20, λ = 2 cố định**", "Mục tiêu huấn luyện **khác** mục tiêu đo (sai số tọa độ)"], MX + 0.22, 1.9, half - 0.4, 1.45, 14, INK, 5);
    card(s, MX + half + 0.4, 1.4, half, 2.0, SOFT, "V7: học trọng số bằng sai số mét", TEAL, TEAL);
    bullets(s, ["Bộ chấm điểm cho điểm s_{i} mỗi ô; **w = softmax(s)**", "Tọa độ = Σ w_{i} · tâm ô_{i}", "Huấn luyện bằng **chính sai số mét** của tọa độ cuối"], MX + half + 0.62, 1.9, half - 0.4, 1.45, 14, INK, 5);
    // chuỗi V7
    const names = [["30 ô ứng viên", "từ chương 3"], ["49 đặc trưng", "bước 6"], ["dạng tương đối", "196 đầu vào, bước 7"], ["MLP chấm điểm", "s_{i}, bước 8"], ["softmax", "w_{i}, bước 9"], ["tọa độ + sai số", "bước 10"]];
    const bw = 1.78, g = 0.29, y0 = 3.7;
    names.forEach(([t, sub], i) => {
      const x = MX + i * (bw + g), col = i === 0 ? TEAL : RUST;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y0, w: bw, h: 1.15, rectRadius: 0.07, fill: { color: i === 0 ? "E6F0F2" : "F7EAE3" }, line: { color: col, width: 1.25 } });
      s.addText(t, { x: x + 0.05, y: y0 + 0.1, w: bw - 0.1, h: 0.5, fontFace: F, fontSize: 14, bold: true, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
      s.addText(c.para(sub), { x: x + 0.05, y: y0 + 0.62, w: bw - 0.1, h: 0.45, fontFace: F, fontSize: 12, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
      if (i < 5) s.addShape(pres.shapes.LINE, { x: x + bw + 0.02, y: y0 + 0.575, w: g - 0.04, h: 0, line: { color: GREY, width: 1.75, endArrowType: "triangle" } });
    });
    s.addShape(pres.shapes.LINE, { x: MX + 5 * (bw + g) + bw / 2, y: y0 + 1.15, w: 0, h: 0.35, line: { color: GREY, width: 1.5 } });
    s.addShape(pres.shapes.LINE, { x: MX + 3 * (bw + g) + bw / 2, y: y0 + 1.5, w: 2 * (bw + g), h: 0, line: { color: GREY, width: 1.5 } });
    s.addShape(pres.shapes.LINE, { x: MX + 3 * (bw + g) + bw / 2, y: y0 + 1.15, w: 0, h: 0.35, line: { color: GREY, width: 1.5, endArrowType: "triangle" } });
    s.addText("sai số mét truyền ngược để cập nhật bộ chấm điểm (gradient)", { x: MX + 3 * (bw + g) - 0.2, y: y0 + 1.55, w: 4.8, h: 0.3, fontFace: F, fontSize: 12, italic: true, color: GREY, margin: 0, isTextBox: true });
    callout(s, `Kết quả: chỉ thay công thức cố định bằng bộ chấm điểm học trực tiếp: **${vn(T6r.mean, 3)} → ${vn(tr("B_base").mean, 3)} m** (test); thêm hai góc nhìn HUI mới: **${vn(T7.mean, 3)} m**.`, 6.0, 0.8, NAVY, "FFFFFF", 15);
  }

  // ---- V6 khác V7 trong 8 bước
  {
    const s = slide("V7 · So với V6", "V6 khác V7 ở bước nào trong 8 bước (và bằng chứng ở slide nào)",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Em tóm tắt sự khác nhau giữa V6 và V7 theo đúng tám bước của sơ đồ tổng quan. Bốn bước đầu, từ dữ liệu, lợi ích q, điểm khớp, làm mượt đến 30 ô ứng viên, V7 giữ nguyên từ V6, trừ việc ở bước 2 V7 khai thác thêm hai góc nhìn HUI. Phần khác biệt thật sự nằm ở bốn bước sau: đặc trưng, dạng tương đối, bộ chấm điểm và mục tiêu huấn luyện.
VÍ DỤ ĐỜI THƯỜNG: Giống hai đầu bếp dùng chung nguyên liệu và sơ chế: V6 nêm nếm theo công thức cố định, V7 nếm thử và tự chỉnh theo khẩu vị người ăn. Nguyên liệu thêm hai loại mới (hai góc nhìn HUI), nhưng điểm khác lớn nhất là cách nêm.
CÁCH CHỨNG MINH TỪNG BƯỚC: Cột bên phải ghi tên slide có bằng chứng. Bước 2: slide "Năm góc nhìn HUI" có bảng số HUI từng góc nhìn. Bước 5: slide "49 đặc trưng" có phép cộng 33 + 8 + 8. Bước 6: slide "dạng tương đối" có ví dụ số 196 đầu vào. Bước 7: slide "bộ chấm điểm MLP" có phép cộng 7 360 tham số, và slide "Đường cơ sở V6" có công thức GBM với trọng số cố định. Bước 8: slide "mất mát" và slide "đóng góp từng bước", trong đó V7-B giảm 0,43 mét chỉ nhờ cách học mà không thêm đặc trưng nào.
NÓI THẲNG: Mức giảm 0,43 mét của V7-B gộp hai thay đổi: đổi sang học bằng sai số mét và đổi sang MLP. Em đã so thêm các bộ chấm điểm khác ở slide sau để tách bớt hai yếu tố này.
CHUYỂN Ý: Em đi vào bước 5, mô tả 49 đặc trưng.`);
    const rows = [["1. Dữ liệu, lợi ích q", "như V7", "giữ nguyên", "Bước 1 (q) và ví dụ hàng 335"],
      ["2. EFIM, HUI theo ô", "3 góc nhìn (rank, rank-L3, abs): 7,33 triệu HUI", "**5 góc nhìn**, thêm rel và abs-L3: 12,90 triệu HUI", "Năm góc nhìn HUI"],
      ["3. Điểm khớp P·V³, tầng", "σ = 3 m, 20 ô chọn tầng", "giữ nguyên", "Điểm khớp; làm mượt và chọn tầng"],
      ["4. 30 ô ứng viên", "30 ô", "giữ nguyên", "30 ô ứng viên"],
      ["5. Đặc trưng", "33 cột", "**49 cột** (+ 8 cột mỗi góc nhìn mới)", "49 đặc trưng"],
      ["6. Dạng tương đối", "x, x−max, min-max, hạng (GBM)", "4 phép + slog + z-score: **196 đầu vào**", "Dạng tương đối"],
      ["7. Chấm điểm, trọng số", "GBM dự đoán log(1+d); a ∝ exp(−d̂/λ), m = 20, λ = 2 cố định", "**MLP 7 360 tham số**, softmax trên 30 ô: trọng số được học", "Bộ chấm điểm MLP; Đường cơ sở V6"],
      ["8. Mục tiêu huấn luyện", "log khoảng cách từng ô (gián tiếp)", "**sai số tọa độ cuối bằng mét**, Adam, 5 thành viên", "Mất mát; Đóng góp từng bước"]];
    tb(s, ["Bước", "V6", "V7", "Bằng chứng ở slide"], rows, MX, 1.45, W, [2.5, 3.6, 3.8, W - 9.9], { size: 12.5, minH: 0.5, hl: (i) => i >= 4 });
    callout(s, "Bước 1–4 giữ nguyên từ V6 (trừ 2 góc nhìn mới ở bước 2). **Phần mới thật sự của V7 là bước 5–8**; V7 cũng tính bằng float64 thay vì float32.", 6.2, 0.65, NAVY, "FFFFFF", 14.5);
  }

  // ---- 49 đặc trưng
  algoSlide("Bước 6 · Đặc trưng", "Bước 6: 49 đặc trưng bằng chứng cho mỗi ô ứng viên", {
    formula: "fm_feat", fh: 2.5, fw: 7.1,
    syms: [["q̂_{c}(i)", "cường độ ước lượng của AP i trong ô c, suy ra từ HUI (trung bình có trọng số w)"], ["m_{c}(i)", "khối lượng HUI của ô c mà AP i mang (tổng bằng 1)"], ["R_{c}(T)", "độ phủ ngược: phần khối lượng HUI của ô có mặt trong T"],
      ["MAE_{c}(T)", "sai lệch trung bình (có trọng số q) giữa cường độ của T và hồ sơ q̂ của ô"], ["cos_{c}(T)", "góc giữa vector cường độ của T và hồ sơ m ⊙ q̂"], ["⊙, ⟨·,·⟩, ‖·‖", "nhân từng phần tử; tích vô hướng; độ dài vector"]], symSize: 11.5,
    ex: "**49 = 33 + 8 + 8:** 33 cột của V6; 8 cột cho mỗi góc nhìn mới (rel, abs-L3): **P, V, R, điểm tương đối S/S₁, hạng, MAE, corr, cos**", exH: 0.55,
    why: ["Mỗi ô ứng viên cần nhiều **bằng chứng**: mức khớp mẫu (P), độ phủ (V, R) và **hình dạng hồ sơ cường độ** (MAE, corr, cos)", "Mọi cột đều tính từ **HUI và vân tay truy vấn**: không dùng RSSI thô độc lập, không dùng vân tay huấn luyện"],
    nums: [["33 cột", "quy ước", "kế thừa từ V5/V6"], ["8 cột / góc nhìn", "định nghĩa", "rút gọn các nhóm bằng chứng V6"], ["49 = 33 + 8 + 8", "đếm", "V7-B chỉ 33 cột"]],
    numCols: [1.6, 0.95, 3.0], leftW: 5.9,
  },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Để chấm điểm một ô ứng viên, bộ chấm điểm cần "hồ sơ" của ô đó đối với vân tay đang xét. Em mô tả mỗi ô bằng 49 con số, tất cả suy ra từ HUI và từ chính vân tay truy vấn. Có ba nhóm: nhóm điểm khớp (P, V, điểm tương đối, hạng), nhóm độ phủ (R) và nhóm hình dạng hồ sơ cường độ (MAE, corr, cos).
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ 30 ô như 30 ứng viên xin việc và 49 con số là hồ sơ năng lực của từng người: điểm chuyên môn (P), mức độ phù hợp vị trí (V), độ phủ kỹ năng (R)... và cả "hình dạng" năng lực: người này giỏi những kỹ năng nào so với yêu cầu. Hai chỉ số MAE và cosine chính là so "hình dạng": bộ phát nào lẽ ra mạnh ở ô này thì trong vân tay có mạnh không.
CÔNG THỨC: Từ các HUI của ô, em suy ra cường độ q-mũ của từng bộ phát (trung bình có trọng số w trên các HUI chứa bộ phát đó) và khối lượng m của bộ phát (nó chiếm bao nhiêu phần trong các HUI). R là phần khối lượng HUI của ô mà vân tay có mặt. MAE là độ lệch trung bình giữa cường độ vân tay và hồ sơ của ô. Cosine là góc giữa hai vector: vector cường độ của vân tay và vector hồ sơ.
CÁC CON SỐ: 33 cột đầu là kế thừa từ V5 và V6 để so sánh công bằng. Mỗi góc nhìn mới thêm 8 cột: P, V, R, điểm tương đối, hạng, MAE, corr và cos. Vậy 33 cộng 8 cộng 8 bằng 49. Chính V7-B chỉ dùng 33 cột và đã giảm được sai số, cho thấy phần lớn cải thiện đến từ cách học trọng số.
RÀNG BUỘC: Không có đặc trưng nào dùng RSSI thô độc lập hay so sánh với vân tay huấn luyện; đầu vào duy nhất ngoài HUI là chính vân tay truy vấn, và nó chỉ được dùng để khớp với HUI.
CHUYỂN Ý: 49 số này chưa dùng được ngay; em cần đưa chúng về dạng tương đối giữa 30 ô.`);

  // ---- tương đối
  {
    const cs = EX.cells, mx = Math.max(...cs.map((q) => q.S)), mn = Math.min(...cs.map((q) => q.S));
    const c1 = cs[0], c4 = cs[3];
    algoSlide("Bước 7 · Dạng tương đối", "Bước 7: đưa đặc trưng về dạng tương đối giữa 30 ô (196 đầu vào)", {
      formula: "fm_rel", fh: 1.95, fw: 7.3,
      syms: [["x_{i}", "một đặc trưng của ứng viên i (ví dụ điểm S)"], ["x̃_{i}", "hiệu với giá trị lớn nhất của 30 ứng viên"], ["x̄_{i}", "min-max trong truy vấn, nằm trong [0, 1]"], ["r_{i}", "hạng của x_{i} (0 = lớn nhất)"], ["slog", "log có dấu: nén đuôi dài"], ["μ, σ", "trung bình và độ lệch chuẩn trên tập huấn luyện"]], symSize: 12,
      ex: `**Ví dụ hàng ${EX.src_row}, đặc trưng S** (max = ${vn(mx, 4)}, min = ${vn(mn, 4)} trong 30 ô): ô ${c1.cell}: x = ${vn(c1.S, 4)} → x − max = ${vn(c1.S - mx, 4)}, min-max = ${vn((c1.S - mn) / (mx - mn), 3)}, hạng 0; ô ${c4.cell}: x = ${vn(c4.S, 4)} → x − max = ${vn(c4.S - mx, 4)}, min-max = ${vn((c4.S - mn) / (mx - mn), 3)}, hạng 3`, exH: 0.75, exSize: 13,
      why: ["Quyết định là **so sánh 30 ô cùng một truy vấn**; điểm tuyệt đối đổi theo từng vân tay", "x − max, min-max, hạng: giữ phần tương đối, **bất biến với thang** của điểm", "slog + z-score: nén đuôi dài rồi chuẩn hóa để Adam ổn định"],
      nums: [["× 4 phép = 196", "định nghĩa", "gốc, x−max, min-max, hạng (V7-B: 132)"], ["slog, z-score", "quy ước", "chưa cắt riêng"], ["bù lệch thiết bị", "dev", "+0,063 m: tệ hơn, đã loại"]],
      numCols: [1.6, 0.95, 3.0], leftW: 5.9,
    },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Điểm của một ô, ví dụ P hay V, tự nó không có nhiều ý nghĩa: vân tay này có thể cho điểm tối đa 0,06, vân tay kia cho điểm tối đa 0,6. Điều quan trọng là ô này TỐT HƠN các ô khác trong cùng một truy vấn bao nhiêu. Vì vậy em tạo thêm ba dạng tương đối cho mỗi đặc trưng: hiệu với giá trị lớn nhất (x trừ max), giá trị chuẩn hóa min-max trong truy vấn, và thứ hạng. Với bốn dạng cho mỗi đặc trưng, 49 cột thành 49 nhân 4 bằng 196 đầu vào.
VÍ DỤ ĐỜI THƯỜNG: Điểm 7 trong lớp giỏi và điểm 7 trong lớp yếu có ý nghĩa rất khác nhau. Muốn biết em học sinh giỏi đến đâu thì phải xem em đó đứng thứ mấy trong lớp và cách người đứng đầu bao nhiêu điểm. Ba dạng tương đối chính là: cách người đứng đầu bao nhiêu điểm, vị trí trong khoảng từ thấp nhất đến cao nhất, và thứ hạng.
VÍ DỤ SỐ: Với hàng 335, đặc trưng S của 30 ô có lớn nhất là 0,0614 (ô 351) và nhỏ nhất là ${vn(mn, 4)}. Ô 351: x trừ max bằng 0, min-max bằng 1, hạng 0. Ô thứ tư có S bằng ${vn(c4.S, 4)}: x trừ max bằng ${vn(c4.S - mx, 4)}, min-max bằng ${vn((c4.S - mn) / (mx - mn), 3)}, hạng 3.
SLOG VÀ Z-SCORE: Hàm slog bằng dấu nhân logarit của một cộng giá trị tuyệt đối: nén những giá trị rất lớn để mạng không bị chi phối bởi vài giá trị lệch. Sau đó trừ trung bình và chia độ lệch chuẩn (tính trên tập huấn luyện) để các cột có thang giống nhau; điều này giúp thuật toán tối ưu Adam ổn định.
THÀNH THẬT: Em chưa có thí nghiệm cắt riêng slog. Số 5,9588 xuống 5,9300 mét (dev) xảy ra khi em đổi đồng thời sang tập hợp năm thành viên và dùng slog. Em cũng đã thử thêm một khối 13 cột "bù lệch thiết bị" nhưng nó làm tệ đi 0,063 mét nên em loại.
CHUYỂN Ý: Đã có 196 con số cho mỗi ô; đến bộ chấm điểm.`);
  }

  // ---- MLP
  {
    const drawNet = (s, y, h) => {
      const names = [["z_{i}", "196 số"], ["ReLU(W_{1}z_{i} + b_{1})", "h_{i}: 32 số"], ["[h_{i} ; h̄]", "ghép với trung bình: 64 số"], ["ReLU(W_{2}[·] + b_{2})", "g_{i}: 16 số"], ["s_{i} = w_{3}ᵀ g_{i}", "điểm: 1 số"]];
      const bw = 2.1, g = 0.4, x0 = MX + (W - (5 * bw + 4 * g)) / 2;
      names.forEach(([t, sub], i) => {
        const x = x0 + i * (bw + g), col = i % 2 ? TEAL : NAVY;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y + 0.06, w: bw, h: h - 0.12, rectRadius: 0.06, fill: { color: i % 2 ? "E6F0F2" : "E8EDF4" }, line: { color: col, width: 1.25 } });
        s.addText(c.para(t), { x: x + 0.04, y: y + 0.08, w: bw - 0.08, h: (h - 0.16) * 0.55, fontFace: F, fontSize: 12.5, bold: true, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
        s.addText(c.para(sub), { x: x + 0.04, y: y + 0.08 + (h - 0.16) * 0.55, w: bw - 0.08, h: (h - 0.16) * 0.42, fontFace: F, fontSize: 11.5, color: INK, align: "center", valign: "middle", margin: 0, isTextBox: true });
        if (i < 4) s.addShape(pres.shapes.LINE, { x: x + bw + 0.02, y: y + h / 2, w: g - 0.04, h: 0, line: { color: GREY, width: 1.5, endArrowType: "triangle" } });
      });
    };
    algoSlide("Bước 8 · Bộ chấm điểm", "Bước 8: bộ chấm điểm MLP dùng chung cho 30 ô (7 360 tham số)", {
      formula: "fm_scorer", fh: 1.9, fw: 6.0,
      syms: [["z_{i}", "196 đặc trưng đã chuẩn hóa của ô ứng viên i"], ["W_{1}, b_{1}", "lớp ẩn 1: 196 → 32 (6 304 tham số)"], ["h̄", "trung bình h của 30 ứng viên: cho ô i biết các ô còn lại"], ["W_{2}, b_{2}", "lớp ẩn 2: 64 → 16 (1 040 tham số)"], ["w_{3}", "16 trọng số cuối → điểm s_{i} (16 tham số)"], ["ReLU", "max(0, ·); K = 30"]], symSize: 12,
      exDraw: drawNet, exH: 0.9,
      why: ["**Dùng chung** một bộ tham số cho mọi ô: ít tham số, không phụ thuộc thứ tự", "**Nhánh gộp** (h̄): điểm của một ô phụ thuộc các ô còn lại (đã cắt riêng ở slide sau: không cần thiết)", "MLP nhỏ vì dữ liệu chỉ vài chục nghìn truy vấn; gradient viết tay, kiểm bằng sai phân hữu hạn"],
      nums: [["32 và 16 nơ-ron", "dev (2 cấu hình)", `64/32: ${vn(SC["mlp64_32_wd1e-4"], 4)}; **32/16: ${vn(SC["mlp32_16_wd1e-3"], 4)}**`], ["7 360 tham số", "đếm", "6 304 + 1 040 + 16"], ["V7-B: 5 312", "đếm", "(132×32+32) + 1 040 + 16"]],
      numCols: [1.55, 1.15, 2.75], leftW: 5.9,
    },
`KỊCH BẢN (khoảng 2,5 phút)
NÓI: Bộ chấm điểm là một mạng nơ-ron nhỏ. Nó nhận 196 con số của một ô, cho qua lớp ẩn thứ nhất 32 nơ-ron, ghép kết quả với trung bình của cả 30 ô, rồi cho qua lớp thứ hai 16 nơ-ron, cuối cùng ra một con số s là điểm của ô đó. Cùng một bộ tham số được dùng cho cả 30 ô, giống như một giám khảo chấm cho mọi thí sinh.
VÍ DỤ ĐỜI THƯỜNG: Hãy nghĩ đến một giám khảo cuộc thi hát chấm 30 thí sinh. Nếu giám khảo chỉ nhìn từng thí sinh riêng lẻ thì có thể cho ai cũng 9 điểm; nhưng giám khảo giỏi còn xem điểm trung bình của cả buổi thi để cho điểm có phân biệt. Nhánh h-gạch chính là phần "xem trung bình của cả 30 người": điểm của ô i phụ thuộc cả các ô khác của cùng truy vấn.
TỰ KIỂM SỐ THAM SỐ: Lớp 1 có 196 nhân 32 trọng số cộng 32 độ lệch là 6 304. Lớp 2 nhận 64 đầu vào (h và trung bình h) và ra 16: 64 nhân 16 cộng 16 là 1 040. Lớp cuối có 16 trọng số. Tổng là 6 304 cộng 1 040 cộng 16 bằng 7 360. Với V7-B (chỉ 132 đầu vào) là 5 312.
VÌ SAO CHỌN: Một, dùng chung tham số để mô hình gọn và không phụ thuộc vào thứ tự ô. Hai, nhánh gộp để so sánh tương đối giữa các ô. Ba, mạng nhỏ vì dữ liệu chỉ vài chục nghìn truy vấn.
VÌ SAO 32 VÀ 16: Em chỉ so hai cấu hình trên dev: mạng 64/32 với weight decay 10 mũ trừ 4 cho 5,9797 mét, mạng 32/16 với weight decay 10 mũ trừ 3 cho 5,9588 mét. Chênh 0,021 mét, nhỏ; em chọn mạng nhỏ hơn vì không kém mà ít tham số hơn. Hai thay đổi này đổi cùng lúc nên em chưa tách riêng được; em cũng chưa dò lưới sâu hơn và chưa cắt riêng nhánh gộp.
CẬP NHẬT: Sau đó em đã chạy so sánh MLP với các bộ chấm điểm khác (hai slide ngay sau slide này): nhánh gộp hóa ra không cần thiết và các bộ chấm điểm cho kết quả sát nhau.
CHUYỂN Ý: Em trình bày kết quả so sánh, rồi đến softmax.`);
  }

  // ---- so sánh các bộ chấm điểm (đã chạy thật)
  if (CR) {
    const g = (k) => CR[k], r3 = (x) => vn(x, 4), tms = (k) => vn(g(k).infer_ms_per_query, 3), fold = (k) => `${g(k).folds_better_than_ref}/6`;
    const C2m1 = g("mlp_c2_m1"), C2saved = CMP.c2_saved_5members.inf_mean;
    const s = slide("Bước 8 · So sánh bộ chấm điểm", "Bước 8: đã chạy thử các bộ chấm điểm khác, đo sai số mét và thời gian",
`KỊCH BẢN (khoảng 3 phút)
NÓI: Ở phần trước em nói chưa so MLP với bộ chấm điểm nào khác. Em đã chạy thật. Tất cả dùng cùng đặc trưng 49 cột (196 đầu vào), cùng 6 fold dev theo điện thoại, cùng hàm mất mát sai số mét, chỉ khác bộ chấm điểm. Em đo hai thứ: sai số trung bình trên dev bằng mét và thời gian: thời gian huấn luyện mỗi thành viên và thời gian suy luận cho mỗi vân tay, chỉ tính riêng bộ chấm điểm. Phần khai thác HUI cho mỗi vân tay mất khoảng 336 mili giây (V7), lớn hơn bộ chấm điểm hàng nghìn lần, nên thời gian của bộ chấm điểm không phải nút cổ chai.
VÍ DỤ ĐỜI THƯỜNG: Giống như tuyển giám khảo cho một cuộc thi: em cho các ứng viên cùng chấm một bộ hồ sơ như nhau, rồi so điểm số của họ so với đáp án và xem ai chấm nhanh. Vòng một mỗi ứng viên chấm một lượt (1 thành viên); ứng viên nào đủ điều kiện thì vào vòng hai, nơi lập hội đồng 5 người cùng chấm như V7-C2.
ĐỌC KẾT QUẢ: Một, các mô hình đơn giản không thua MLP: tuyến tính chỉ 196 tham số đạt ${r3(g("linear_lr5e-3_m1").inf_mean)} mét ở vòng một, thấp hơn MLP chuẩn ${r3(C2m1.inf_mean)} mét, và huấn luyện nhanh gấp khoảng 6 lần. Hai, MLP không có nhánh gộp, tức bỏ phần trung bình của 30 ô, tốt hơn MLP có nhánh gộp: ${r3(g("mlp_nopool_m1").inf_mean)} so với ${r3(C2m1.inf_mean)}; ở vòng hai với 5 thành viên là ${r3(g("mlp_nopool_m5").inf_mean)} so với ${r3(C2saved)} mét của V7-C2. Điều này cho thấy nhánh gộp không cần thiết, vì dạng tương đối ở bước 7 đã chứa thông tin so sánh giữa các ô. Ba, MLP rộng hơn (64/32) không tốt hơn. Bốn, attention không thắng. Năm, GBM kiểu V6 và k-NN kém hơn rõ; k-NN còn chậm hơn khoảng 40 lần ở khâu suy luận.
NÓI THẲNG: Mức chênh giữa tuyến tính, MLP và MLP không nhánh gộp chỉ cỡ 0,01 đến 0,05 mét, cùng cỡ dao động giữa các lần huấn luyện. Em chọn theo quy tắc khai báo trước chứ không khẳng định đã tìm ra bộ tốt nhất tuyệt đối. Em thử hai tốc độ học (5·10⁻⁴ và 5·10⁻³) cho tuyến tính, MLP, MLP không nhánh gộp và attention; MLP rộng và GBM chỉ một cấu hình; chưa dò thêm.
CÁCH ĐỌC THỜI GIAN: Thời gian huấn luyện là giây cho mỗi thành viên trên một fold. Suy luận là mili giây cho mỗi vân tay, một thành viên. Hội đồng 5 thành viên nhân lên khoảng 5 lần. Thời gian của GBM 49 cột đo lại sạch trên một fold vì lần chạy đầu bị đo sai do máy ngủ.
CHUYỂN Ý: Em kết luận chọn bộ nào ở slide sau.`);
    const rows = [["Tuyến tính (lr 5·10⁻³)", "196", r3(g("linear_lr5e-3_m1").inf_mean), r3(g("linear_lr5e-3_m5").inf_mean), vn(g("linear_lr5e-3_m1").train_s_per_fold, 0), tms("linear_lr5e-3_m1")],
      ["**MLP không nhánh gộp 32/16**", "6 848", r3(g("mlp_nopool_m1").inf_mean), "**" + r3(g("mlp_nopool_m5").inf_mean) + "**", vn(g("mlp_nopool_m1").train_s_per_fold, 0), tms("mlp_nopool_m1")],
      ["MLP có nhánh gộp 32/16 (V7-C2)", "7 360", r3(C2m1.inf_mean), r3(C2saved) + " (đã lưu)", vn(C2m1.train_s_per_fold, 0), tms("mlp_c2_m1")],
      ["MLP rộng 64/32", "16 768", r3(g("mlp_wide_m1").inf_mean), "—", vn(g("mlp_wide_m1").train_s_per_fold, 0), tms("mlp_wide_m1")],
      ["Attention 1 đầu (lr 5·10⁻³)", "8 640", r3(g("attn_lr5e-3_m1").inf_mean), r3(g("attn_lr5e-3_m5").inf_mean), vn(g("attn_lr5e-3_m1").train_s_per_fold, 0), tms("attn_lr5e-3_m1")],
      ["GBM 49 cột + công thức V6", "—", r3(g("gbm49").inf_mean), "—", vn(g("gbm49_f0").train_s_per_fold, 0), tms("gbm49_f0")],
      ["GBM 33 cột (V6*)", "—", r3(g("gbm33").inf_mean), "—", vn(g("gbm33").train_s_per_fold, 0), tms("gbm33")],
      ["k-NN trên đặc trưng HUI (k = 15, tham khảo)", "—", r3(g("knn49").inf_mean), "—", "0 (không huấn luyện)", tms("knn49")]];
    tb(s, ["Bộ chấm điểm", "Tham số", "Dev, 1 thành viên (m)", "Dev, 5 thành viên (m)", "Huấn luyện (s/thành viên)", "Suy luận (ms/vân tay)"], rows, MX, 1.4, W, [3.9, 1.0, 1.7, 1.9, 1.9, W - 10.4], { size: 12, minH: 0.42, align: ["left", "right", "right", "right", "right", "right"], hl: (i) => i === 1 });
    text(s, "Cùng 49 cột, 6 fold dev theo điện thoại, mất mát sai số mét; vân tay có thông tin (19 861). Thời gian chỉ tính riêng bộ chấm điểm; khai thác HUI cho mỗi vân tay mất ~336 ms. GBM/k-NN dùng cách V6: dự đoán log(1 + d), trọng số exp(−d/λ), m = 20, λ = 2. validationData không được đọc ở bước này.", MX, 5.95, W, 0.9, { fontSize: 12.5, color: GREY });
  }

  // ---- chọn bộ chấm điểm + GBM 3 vs 5 góc nhìn
  if (CR) {
    const g = (k) => CR[k], r3 = (x) => vn(x, 4), C2saved = CMP.c2_saved_5members.inf_mean, V7B = dI("B_base").mean;
    const nop = g("mlp_nopool_m5");
    const testTxt = FT ? `Em chấm test đúng một lần cho bộ này: ${vn(FT.mean, 4)} mét (trung vị ${vn(FT.median, 3)}, P90 ${vn(FT.p90, 2)}), so với V7-C2 là ${vn(T7.mean, 4)} mét.` : "Em chưa chấm test cho bộ này.";
    const s = slide("Bước 8 · Chọn bộ chấm điểm", "Bước 8: các bộ chấm điểm sát nhau, không bộ nào vượt rõ V7-C2",
`KỊCH BẢN (khoảng 3 phút)
NÓI: Em áp quy tắc đã khai báo trước: sai số dev thấp hơn bộ chuẩn VÀ tốt hơn ở ít nhất 4 trên 6 fold, so với V7-C2 (5 thành viên, ${r3(C2saved)} mét). Trên dev chỉ MLP không nhánh gộp đạt quy tắc: ${r3(nop.inf_mean)} mét, tốt hơn ở ${nop.folds_better_than_ref} trên 6 fold. Tuyến tính (${r3(g("linear_lr5e-3_m5").inf_mean)}, ${g("linear_lr5e-3_m5").folds_better_than_ref}/6 fold) và attention (${r3(g("attn_lr5e-3_m5").inf_mean)}) không đạt. ${testTxt} ${FT ? (FT.mean >= T7.mean ? "Nghĩa là bộ thắng trên dev KHÔNG cải thiện trên test; chênh " + vn(FT.mean - T7.mean, 3) + " mét nằm trong nhiễu. Kết luận trung thực: em giữ V7-C2 làm mô hình chính, vì nó đã được kiểm chứng đủ ba cách, và nói rằng việc chọn bộ chấm điểm không phải yếu tố quyết định." : "Bộ này tốt hơn V7-C2 trên test.") : ""}
VÍ DỤ ĐỜI THƯỜNG: Giống tuyển chọn trên điểm thi thử và quy tắc công bố trước: ai vừa có điểm trung bình cao hơn vừa hơn ở ít nhất bốn trong sáu bài thi thử thì được vào, và chỉ người vào mới được thi chính thức. Một mô hình chỉ hơn ở điểm trung bình nhưng thua nhiều bài thi thử thì không được chọn.
CÂU HỎI CỦA THẦY CÔ: "Nếu V6 dùng bộ hồi quy GBM nhưng có 5 góc nhìn thì sao?" Em đã chạy: GBM với 49 cột đạt ${r3(g("gbm49").inf_mean)} mét trên dev, so với ${r3(g("gbm33").inf_mean)} mét của GBM 33 cột (V6*): thêm hai góc nhìn giảm ${vn(g("gbm33").inf_mean - g("gbm49").inf_mean, 3)} mét. Với bộ chấm điểm học trực tiếp: 33 cột (V7-B) là ${r3(V7B)}, 49 cột (V7-C2) là ${r3(dI("C_rel_absL3").mean)} mét, giảm ${vn(V7B - dI("C_rel_absL3").mean, 3)} mét. Tức là thêm góc nhìn giúp khoảng 0,23 mét ở cả hai cách. Còn đổi cách chấm điểm từ GBM sang học trực tiếp giúp thêm khoảng 0,27 mét ở cả hai mức đặc trưng. Hai đóng góp này gần như cộng dồn: đặc trưng mới và cách học mới độc lập với nhau.
NÓI THẲNG: Số GBM 49 cột là trên dev, em chưa chấm test; dev của V6 6,209 mét tương ứng 6,861 mét trên test, nên GBM 49 cột nhiều khả năng cho khoảng 6,6 mét trên test, đó là ước đoán chứ không phải số đo. Với MLP không nhánh gộp, mức hơn V7-C2 trên dev chỉ khoảng ${vn(C2saved - nop.inf_mean, 3)} mét và mức đó không tái hiện trên test; em thừa nhận nhánh gộp không cần thiết nhưng bỏ nó cũng không cải thiện kết quả cuối.
CHUYỂN Ý: Quay lại các bước còn lại của V7: softmax và huấn luyện.`);
    const rows = [["GBM, 33 cột (V6*)", r3(g("gbm33").inf_mean), "—"], ["GBM, 49 cột (5 góc nhìn)", r3(g("gbm49").inf_mean), vnd(g("gbm49").inf_mean - g("gbm33").inf_mean, 3)],
      ["Học trực tiếp, 33 cột (V7-B)", r3(V7B), vnd(V7B - g("gbm33").inf_mean, 3) + " so với GBM 33"], ["Học trực tiếp, 49 cột (V7-C2)", r3(dI("C_rel_absL3").mean), vnd(dI("C_rel_absL3").mean - V7B, 3)]];
    head(s, "GBM với 3 hay 5 góc nhìn so với học trực tiếp (dev, m)", MX, 1.4, 7.2);
    const yb = tb(s, ["Cách chấm điểm và đặc trưng", "Sai số dev", "Thay đổi"], rows, MX, 1.8, 7.2, [3.9, 1.5, 1.8], { size: 12.5, minH: 0.42, align: ["left", "right", "right"] });
    text(s, "Thêm 2 góc nhìn: **−0,24 m** (GBM) và **−0,23 m** (học trực tiếp). Đổi GBM → học trực tiếp: **−0,28 m** (33 cột) và **−0,27 m** (49 cột). Hai đóng góp gần như cộng dồn. Số GBM 49 cột là dev; chưa chấm test.", MX, yb + 0.15, 7.2, 1.5, { fontSize: 13.5 });
    card(s, MX + 7.5, 1.4, W - 7.5, 5.45, SOFT, "Quy tắc chọn và kết quả", TEAL, TEAL);
    bullets(s, ["Quy tắc khai báo trước: dev thấp hơn **và** tốt hơn ≥ 4/6 fold so với V7-C2 (5 thành viên, " + r3(C2saved) + " m)",
      `**MLP không nhánh gộp:** ${r3(nop.inf_mean)} m, **${nop.folds_better_than_ref}/6 fold: đạt**`, `Tuyến tính ${r3(g("linear_lr5e-3_m5").inf_mean)} m (${g("linear_lr5e-3_m5").folds_better_than_ref}/6) và attention ${r3(g("attn_lr5e-3_m5").inf_mean)} m (${g("attn_lr5e-3_m5").folds_better_than_ref}/6): không đạt`,
      FT ? `**Test, chấm một lần:** ${vn(FT.mean, 4)} m (V7-C2: ${vn(T7.mean, 4)} m)` : "Test: chưa chấm", "**Kết luận:** dev chọn MLP không nhánh gộp nhưng test không cải thiện ⇒ **giữ V7-C2** làm mô hình chính", "**Thừa nhận:** nhánh gộp không cần thiết; chênh giữa các bộ cỡ 0,01–0,05 m, cùng cỡ dao động giữa các lần huấn luyện"], MX + 7.75, 1.9, W - 8.0, 4.9, 13, INK, 6);
  }

  // ---- softmax
  {
    const e = (x) => Math.exp(x), z = e(2) + e(1) + e(0), w = [e(2) / z, e(1) / z, e(0) / z];
    algoSlide("Bước 9 · Softmax", "Bước 9: softmax đổi điểm thành trọng số, rồi thành tọa độ", {
      formula: "fm_softmax", fh: 1.7, fw: 6.6,
      syms: [["s_{i}", "điểm của ô ứng viên i (đầu ra bộ chấm điểm)"], ["w_{i}", "trọng số của ô i: không âm, tổng bằng 1"], ["K = 30", "số ô ứng viên"], ["(x_{i}, y_{i})", "tâm của ô ứng viên i"], ["(x̂, ŷ)", "tọa độ dự đoán"]], symSize: 13,
      ex: `**Ví dụ tay (3 ô, tâm tại x = 0, 10, 20 m; điểm s = 2, 1, 0):** e^{s} = ${vn(e(2), 3)}; ${vn(e(1), 3)}; 1,000 (tổng ${vn(z, 3)}) ⇒ w = ${vn(w[0], 4)}; ${vn(w[1], 4)}; ${vn(w[2], 4)} ⇒ x̂ = 0,2447 × 10 + 0,0900 × 20 = **${vn(w[1] * 10 + w[2] * 20, 3)} m**`, exH: 0.62, exSize: 13,
      why: ["w ≥ 0, tổng = 1 ⇒ (x̂, ŷ) luôn nằm trong **bao lồi** của 30 tâm ô: không thể dự đoán ra ngoài vùng ứng viên", "**Khả vi** ⇒ học được bằng gradient từ sai số mét", "V6 dùng w ∝ exp(−d̂/λ) trên 20 ô cố định; V7 **học** s_{i}"],
      nums: [["K = 30", "quy ước + đo", "K = 20: 0,732 m; K = 30: 0,588 m"], ["exp", "định nghĩa", "softmax chuẩn, không nhiệt độ riêng"], ["hạn chế", "—", "bao lồi kéo vào trong ở biên"]],
      numCols: [1.2, 1.2, 3.0], leftW: 5.9,
    },
`KỊCH BẢN (khoảng 2 phút)
NÓI: Bộ chấm điểm cho ra 30 điểm s. Em đổi điểm thành trọng số bằng softmax: trọng số của ô i bằng e mũ s-i chia tổng e mũ s của cả 30 ô. Nhờ vậy trọng số luôn không âm và cộng lại bằng 1. Tọa độ dự đoán là tổng có trọng số của tâm 30 ô.
VÍ DỤ ĐỜI THƯỜNG: Giống như chia 100 phần trăm tiền thưởng cho 30 người: người điểm cao nhận nhiều, người điểm thấp nhận ít, nhưng không ai nhận số âm và tổng luôn đủ 100 phần trăm. Và tọa độ cuối là "trọng tâm" của chiếc bàn có 30 quả cân đặt ở 30 ô.
VÍ DỤ SỐ: Thầy cô cho em một thí dụ nhỏ: ba ô nằm trên một đường thẳng tại 0, 10 và 20 mét, với điểm s bằng 2, 1, 0. Tính e mũ s được 7,389; 2,718 và 1; tổng là 11,107. Trọng số là 0,6652; 0,2447 và 0,0900. Tọa độ dự đoán bằng 0,2447 nhân 10 cộng 0,09 nhân 20, ra 4,248 mét; nghĩa là gần ô thứ nhất, vì ô này nhận nhiều phiếu nhất. Với 30 ô thật thì cũng làm y như vậy nhưng trên hai trục x và y.
VÌ SAO CHỌN SOFTMAX: Ba lý do. Một, trọng số không âm, tổng bằng 1 nên kết quả luôn nằm trong bao lồi của các ô ứng viên, không bay ra ngoài vùng khả dĩ. Hai, softmax khả vi nên học được từ sai số mét. Ba, so với V6 thì không cần cố định số ô m và nhiệt độ lambda.
HẠN CHẾ: Vì nằm trong bao lồi, khi vị trí thật ở biên hoặc đầu hành lang thì tọa độ bị kéo vào trong; đúng là nhóm biên có sai số cao nhất. Em cũng chưa so sánh thực nghiệm với việc hồi quy tọa độ trực tiếp.
CHUYỂN Ý: Giờ là cách huấn luyện: mất mát tính bằng mét.`);
  }

  // ---- mất mát
  {
    const s = slide("Bước 10 · Mất mát", "Bước 10: học bằng chính sai số mét — hàm mất mát và gradient",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Để huấn luyện, em cần một hàm mất mát: một con số cho biết mô hình đang sai bao nhiêu. Em chọn chính sai số trung bình tính bằng mét, đúng cái mà hội đồng chấm. Công thức: mất mát L bằng trung bình, trên N vân tay huấn luyện, của g nhân căn bậc hai của (độ lệch x bình phương cộng độ lệch y bình phương cộng epsilon).
VÍ DỤ ĐỜI THƯỜNG: Giống như luyện thi bằng chính đề thi và chính thang điểm của kỳ thi. V6 giống học sinh luyện kỹ năng "ước lượng khoảng cách" rồi hy vọng điểm thi tốt, còn V7 luyện thẳng trên thang điểm của bài thi. Luyện đúng thứ được chấm thì không bị lệch mục tiêu.
CÁC KÝ HIỆU: g là 0,766126, hệ số đổi sang mét; epsilon bằng 10 mũ trừ 6 chỉ để căn bậc hai có đạo hàm khi dự đoán trùng đúng vị trí thật; ảnh hưởng của nó là căn của 10 mũ trừ 6 nhân 0,766 bằng 0,00077 mét, không đáng kể.
GRADIENT: Để cập nhật mạng cần biết "tăng điểm s của ô nào thì sai số giảm". Theo quy tắc chuỗi: đạo hàm của L theo tọa độ ước lượng là vector đơn vị chỉ từ vị trí thật đến ước lượng, nhân g chia N. Đạo hàm của tọa độ theo điểm s-i bằng w-i nhân (tâm ô i trừ tọa độ ước lượng). Ghép lại: ô nằm ở phía "đúng" của tọa độ ước lượng được tăng điểm, ô ở phía "sai" bị giảm. Em viết tay bằng NumPy và kiểm chứng bằng sai phân hữu hạn, sai lệch tương đối chỉ 5 nhân 10 mũ trừ 8.
VÌ SAO CHỌN: Tối ưu đúng đại lượng được đo. Đây là điểm khác biệt cốt lõi so với V6.
CHUYỂN Ý: Còn một phần nữa: thuật toán cập nhật tham số và các con số huấn luyện.`);
    fcard(s, "fm_loss", MX, 1.4, 6.9, 1.35);
    fcard(s, "fm_grad", MX, 2.9, 6.9, 1.55);
    const ax = MX + 7.2, aw = SW - MX - ax;
    s.addText("Chú thích ký hiệu", { x: ax, y: 1.38, w: aw, h: 0.33, fontFace: F, fontSize: 15, bold: true, color: TEAL, margin: 0, isTextBox: true });
    ann(s, [["L", "mất mát: sai số tọa độ hợp nhất trung bình (mét)"], ["N", "số vân tay huấn luyện của mỗi lô"], ["ĉ_{n}, c_{n}", "tọa độ dự đoán và tọa độ thật của vân tay n"], ["g", "0,766126 mét trên một đơn vị tọa độ"], ["ε = 10⁻⁶", "hằng nhỏ để căn có đạo hàm tại 0"],
      ["∂L/∂ĉ_{n}", "hướng và độ lớn L thay đổi khi dịch ước lượng"], ["c_{i}", "tâm ô ứng viên i; w_{i} trọng số softmax"], ["∂L/∂s_{i}", "ô ở phía \"đúng\" của ĉ được tăng điểm"]], ax, 1.75, aw, 3.0, 12.5);
    card(s, MX, 4.65, 6.9, 2.2, SOFT, "Vì sao mất mát là sai số mét", TEAL, TEAL);
    bullets(s, ["Tối ưu **đúng đại lượng được đo**; V6 tối ưu log(1 + d) từng ô (đại lượng thay thế)", "Hàm mất mát khả vi (nhờ softmax và căn có ε) ⇒ gradient chạy được", "Gradient viết tay bằng NumPy, kiểm bằng sai phân hữu hạn: lệch tương đối **5·10⁻⁸**"], MX + 0.22, 5.15, 6.5, 1.65, 13, INK, 4);
    card(s, ax, 4.9, aw, 1.95, SOFT2, "Con số", RUST, RUST);
    bullets(s, ["g = 0,766126: **định nghĩa** (cos vĩ độ)", "ε = 10⁻⁶: **định nghĩa**; ảnh hưởng √10⁻⁶ × g = 0,00077 m", "Gradient kiểm bằng sai phân hữu hạn (tests/test_v7.py)"], ax + 0.22, 5.4, aw - 0.4, 1.4, 12.5, INK, 3);
  }

  // ---- Adam + số huấn luyện
  {
    const s = slide("Bước 10 · Tối ưu", "Cập nhật tham số bằng Adam và các con số huấn luyện",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Để cập nhật 7 360 tham số của mạng em dùng thuật toán Adam. Adam nhìn vào gradient hiện tại cộng một chút phạt weight decay, rồi giữ hai "bộ nhớ": m là trung bình trượt của gradient (hướng đi gần đây) và v là trung bình trượt của bình phương gradient (độ dốc gần đây). Mỗi bước cập nhật tỷ lệ m chia căn của v, nên những tham số có gradient lớn thì bước nhỏ lại, những tham số có gradient nhỏ thì bước lớn lên.
VÍ DỤ ĐỜI THƯỜNG: Giống người đi xuống núi trong sương mù. Người đó nhớ hướng mình vừa đi (m: động lượng) nên không đổi hướng liên tục theo từng viên đá nhỏ; và biết đoạn nào dốc đứng thì bước ngắn lại (v), đoạn nào thoải thì bước dài hơn. Learning rate eta bằng 0,0005 là độ dài bước cơ bản.
CÁC CON SỐ, NÓI THẲNG: Learning rate 0,0005, beta một bằng 0,9, beta hai bằng 0,999 và kích thước lô 256 là các giá trị phổ biến; em chưa dò lưới các giá trị này. Weight decay 10 mũ trừ 3 được chọn cùng lúc với kích thước mạng khi so hai cấu hình. Tối đa 30 epoch: số epoch tốt nhất thật sự của 30 mô hình V7-C2 nằm trong khoảng ${EP.C2.min} đến ${EP.C2.max}, trung vị ${vn(EP.C2.median, 0)}, không có mô hình nào chạm trần 30. Dừng sớm với kiên nhẫn 8: nếu 8 epoch liền sai số trên fold dừng sớm không giảm quá 10 mũ trừ 4 mét thì dừng và lấy mô hình tốt nhất.
VÌ SAO CHỌN ADAM: Adam là thuật toán tối ưu phổ biến, ổn định với mạng nhỏ và không cần chỉnh tay tốc độ học cho từng tham số. Em không thử các thuật toán tối ưu khác, đây là một điểm em ghi nhận.
CHUYỂN Ý: Cuối cùng là cách huấn luyện để không rò rỉ dữ liệu.`);
    fcard(s, "fm_adam", MX, 1.4, 6.6, 2.4);
    const ax = MX + 6.9, aw = SW - MX - ax;
    s.addText("Chú thích ký hiệu", { x: ax, y: 1.38, w: aw, h: 0.33, fontFace: F, fontSize: 15, bold: true, color: TEAL, margin: 0, isTextBox: true });
    ann(s, [["θ", "một tham số của mạng"], ["∇_{t}", "gradient ở bước t, cộng phạt weight decay λ_{w}θ"], ["m_{t}, v_{t}", "trung bình trượt của gradient và của bình phương gradient"], ["β_{1}, β_{2}", "hệ số nhớ: 0,9 và 0,999"], ["η", "bước học (learning rate) = 5·10⁻⁴"], ["1 − β^{t}", "hiệu chỉnh độ lệch ở các bước đầu"]], ax, 1.75, aw, 2.2, 12.5);
    const rows = [["Adam: η = 5·10⁻⁴, β = (0,9; 0,999), batch 256", "quy ước", "giá trị phổ biến; **chưa dò lưới** lr và batch"],
      ["weight decay λ_{w} = 10⁻³", "dev (2 cấu hình)", "thử 10⁻⁴ (mạng 64/32) và 10⁻³ (mạng 32/16); đổi cùng lúc với kích thước mạng"],
      ["tối đa 30 epoch", "ngân sách", `epoch tốt nhất V7-C2: ${EP.C2.min}–${EP.C2.max} (trung vị ${vn(EP.C2.median, 0)}); **${EP.C2.n_at_cap}/${EP.C2.n_members}** chạm trần`],
      ["dừng sớm, kiên nhẫn 8", "quy ước", "dừng khi 8 epoch liền không giảm quá 10⁻⁴ m trên fold dừng sớm"]];
    tb(s, ["Con số", "Loại", "Vì sao / bằng chứng"], rows, MX, 4.0, W, [4.2, 1.7, W - 5.9], { size: 12.5, minH: 0.5 });
  }

  // ---- huấn luyện không rò rỉ
  {
    const s = slide("Bước 10 · Huấn luyện", "Huấn luyện không rò rỉ: 6 fold, tập hợp 5 thành viên",
`KỊCH BẢN (khoảng 2 phút)
NÓI: Với mỗi fold đánh giá, em huấn luyện năm mạng, gọi là năm thành viên. Thành viên thứ i dùng một fold huấn luyện khác làm fold "dừng sớm" và huấn luyện trên bốn fold còn lại. Điểm s của năm thành viên được lấy trung bình rồi mới softmax. Hình bên trái là ví dụ khi đánh giá fold 3 (ô vàng): ô đỏ là fold dừng sớm của từng thành viên, ô xanh là fold huấn luyện. Fold đánh giá không bao giờ bị mạng nhìn thấy.
VÍ DỤ ĐỜI THƯỜNG: Giống năm học sinh cùng ôn thi. Mỗi người có một bộ đề thi thử riêng (fold dừng sớm) để biết khi nào nên dừng ôn: nếu điểm thi thử không tăng nữa thì ngừng, vì ôn thêm chỉ là học vẹt. Cuối cùng em lấy ý kiến trung bình của cả năm người; ý kiến của nhiều người thường ổn định hơn ý kiến của một người. Còn đề thi chính thức (fold đánh giá) thì không ai được xem trước.
VÌ SAO CHỌN: Số thành viên là sáu fold trừ một fold đánh giá bằng năm. Cách chia theo điện thoại đảm bảo không điện thoại nào có mặt ở cả hai phía. Mô hình HUI của đặc trưng fold k cũng chỉ được khai thác trên các điện thoại khác, nên bản thân đặc trưng cũng không rò rỉ.
RÒ RỈ GIÁN TIẾP: Còn một kẽ hở tinh vi hơn: mô hình HUI của một fold huấn luyện đã "đọc" các vân tay của fold đánh giá khi khai thác. Em đã đo riêng bằng giao thức lồng nhau chặt hơn trên fold ngoài số 2: chênh lệch chỉ là −0,0035 mét, tức là không đo được rò rỉ bậc hai đáng kể.
GHI NHẬN: Mỗi tệp cache đều ghi mã băm SHA-256 của dữ liệu huấn luyện, chỉ số hàng của fold, phiên bản mã và cấu hình; cache không khớp bị từ chối.
CHUYỂN Ý: Bây giờ em đi qua một ví dụ trọn vẹn với một vân tay thật.`);
    const k = 2, cx = MX, cy = 1.7, cw = 0.92, ch = 0.55;
    head(s, "Ví dụ: fold đánh giá = fold 3", MX, 1.4, 6);
    for (let m = 0; m < 5; m++) {
      s.addText(`thành viên ${m + 1}`, { x: cx, y: cy + 0.45 + m * 0.6, w: 1.5, h: 0.45, fontFace: F, fontSize: 13, color: INK, margin: 0, valign: "middle", isTextBox: true });
      const train = [0, 1, 3, 4, 5];
      for (let f = 0; f < 6; f++) {
        let col, lab;
        if (f === k) { col = GOLD; lab = "đánh giá"; } else if (train[m] === f) { col = RUST; lab = "dừng sớm"; } else { col = TEAL; lab = "huấn luyện"; }
        s.addShape(pres.shapes.RECTANGLE, { x: cx + 1.6 + f * (cw + 0.06), y: cy + 0.45 + m * 0.6, w: cw, h: 0.46, fill: { color: col }, line: { color: "FFFFFF", width: 1 } });
        s.addText(lab, { x: cx + 1.6 + f * (cw + 0.06), y: cy + 0.45 + m * 0.6, w: cw, h: 0.46, fontFace: F, fontSize: 11, color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true });
      }
    }
    for (let f = 0; f < 6; f++) s.addText(`fold ${f + 1}`, { x: cx + 1.6 + f * (cw + 0.06), y: cy, w: cw, h: 0.4, fontFace: F, fontSize: 12.5, color: GREY, align: "center", margin: 0, isTextBox: true });
    const x = MX + 8.55, w = SW - MX - x;
    card(s, x, 1.4, w, 3.55, SOFT, "Vì sao thiết kế thế này", TEAL, TEAL);
    bullets(s, ["**5 thành viên** = 6 fold − 1 fold đánh giá", "Mỗi thành viên **dừng sớm trên một fold huấn luyện khác**; điểm s trung bình rồi mới softmax", "Fold đánh giá **không bao giờ** bị mạng nhìn thấy"], x + 0.2, 1.9, w - 0.35, 3.0, 13, INK, 5);
    card(s, MX, 5.15, W, 1.7, SOFT2, null, RUST, RUST);
    bullets(s, ["Mô hình HUI của đặc trưng fold k **chỉ đào trên các điện thoại khác**; cache có SHA-256 của dữ liệu, chỉ số hàng, mã, cấu hình; cache không khớp bị từ chối",
      `**Rò rỉ gián tiếp** (mô hình HUI của fold huấn luyện đã đọc fold đánh giá): đo bằng giao thức lồng nhau chặt trên fold ngoài số 2: chênh lệch **${vnd(D.nested.diff, 4)} m**`], MX + 0.3, 5.3, W - 0.6, 1.5, 13.5, INK, 6);
  }
};
