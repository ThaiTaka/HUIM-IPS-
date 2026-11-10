// Các slide "BỔ SUNG · Vì sao chọn vậy / con số này từ đâu" xen vào bộ slide V7 (build_slides_v7.js, chạy với SUPP=1).
// Mọi con số đọc từ BAOCAO/so_lieu_V7/nguon_goc_hang_so.json (tính lại bởi src/baocao/export_why_v7.py) hoặc du_lieu_bao_cao_V7.json.
// Nguyên tắc: mỗi hằng số được xếp vào MỘT loại — đếm / định nghĩa / đo / quy ước / chọn trên dev / ngân sách —
// và nói thẳng điều chưa được dò (lưới thô, giá trị nằm ở biên lưới, chưa cắt riêng thành phần).
module.exports = function why(c) {
  const { pres, slide, text, bullets, table, card, callout, para, vn, vnd, pct, MX, SW, F, INK, NAVY, TEAL, RUST, GREY, GOLD, SOFT, SOFT2, CARD, LINE, D, tr, dI, T7, T6r, E } = c;
  const W = SW - 2 * MX;
  const G = E.grid;
  const by = (arr, key, v) => arr.find((r) => Math.abs(r[key] - v) < 1e-9);

  function sup(kicker, title, notes) {
    const s = slide("Bổ sung · " + kicker, title, notes);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: SW - MX - 1.55, y: 0.22, w: 1.55, h: 0.32, rectRadius: 0.05, fill: { color: GOLD }, line: { color: GOLD } });
    s.addText("BỔ SUNG", { x: SW - MX - 1.55, y: 0.22, w: 1.55, h: 0.32, fontFace: F, fontSize: 12, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    return s;
  }
  const CW = 0.0059;                                   // inch / (pt · ký tự), Times New Roman, chữ có dấu
  const plain = (t) => String(t).replace(/\*\*|_\{|\^\{|\}/g, "");
  function tb(s, header, rows, x, y, w, colW, o = {}) {   // bảng có chiều cao dòng ước lượng theo độ dài chữ; trả về đáy dự kiến
    const size = o.size || 13, lh = size * 1.22 / 72, minH = o.minH || 0.4;
    const hs = rows.map((r) => Math.max(minH, 0.14 + lh * Math.max(...r.map((c, j) => Math.ceil(plain(c).length * CW * size / Math.max(0.5, colW[j] - 0.2))))));
    table(s, header, rows, x, y, w, colW, { ...o, rowH: [0.42, ...hs] });
    return y + 0.42 + hs.reduce((a, b) => a + b, 0);
  }
  const head = (s, t, x, y, w) => s.addText(t, { x, y, w, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: NAVY, margin: 0, isTextBox: true });
  const note = (s, t, x, y, w, h, color = GREY, size = 13) => text(s, t, x, y, w, h, { fontSize: size, color });

  // ------------------------------------------------------------------ 1. 0,766126
  function coord() {
    const k = E.coord, r = E.rssi;
    const s = sup("Vì sao đo bằng mét", "Vì sao 0,766126: đó là cos của vĩ độ nơi thu dữ liệu",
      "Nếu hỏi: tại sao nhân 0,766126? Tọa độ UJIIndoorLoc ở Web-Mercator (EPSG:3857), hệ bảo giác nên độ dài bị kéo giãn 1/cos(vĩ độ) lần; ở vĩ độ 39,9927° độ co là cos = 0,766126. Đã thử 4 hệ tọa độ giả định; chỉ Web-Mercator đặt tâm dữ liệu cách khuôn viên UJI 139,7 m, các hệ khác lệch hàng trăm km (results/coordinate_system_verification.json). Hệ số này chỉ đổi đơn vị; sai số của mọi mô hình nhân cùng một hằng số nên không đổi thứ tự các mô hình.");
    const rows = [
      ["0,766126", "định nghĩa", `Web-Mercator kéo giãn độ dài 1/cos φ lần ⇒ mét = đơn vị × cos φ; cos(${vn(k.lat_deg, 6)}°) = **${vn(k.cos_lat, 6)}**`],
      [`φ = ${vn(k.lat_deg, 6)}°`, "đo", `đổi ngược tâm vùng dữ liệu (EPSG:3857) về vĩ độ; cách khuôn viên UJI **${vn(k.dist_to_campus_m, 1)} m**. Thử UTM-31N: lệch ${vn(k.dist_utm31_km, 0)} km ⇒ loại`],
      [`${vn(k.x_extent, 2)} × ${vn(k.y_extent, 2)} đơn vị`, "đo", `bề rộng × bề cao vùng dữ liệu = ${vn(k.x_extent_m, 1)} × ${vn(k.y_extent_m, 1)} m sau khi nhân 0,766126`],
      [`${vn(r.n_rows, 0)} / ${vn(r.n_rows_with_ap, 0)} / ${vn(r.n_rows - r.n_rows_with_ap, 0)}`, "đếm", `vân tay huấn luyện / có ít nhất 1 AP / không AP nào (${vn(r.n_rows, 0)} − ${vn(r.n_rows_with_ap, 0)} = ${vn(r.n_rows - r.n_rows_with_ap, 0)})`],
      [`933 ô; ${vn(E.cells.mean_transactions, 2)} vân tay/ô`, "đếm", `933 vị trí tham chiếu khác nhau; ${vn(r.n_rows_with_ap, 0)} / 933 = ${vn(r.n_rows_with_ap / 933, 2)}`]];
    head(s, "Con số — loại — từ đâu", MX, 1.45, 7.4);
    tb(s, ["Con số", "Loại", "Từ đâu, cách tự kiểm"], rows, MX, 1.85, 7.6, [1.95, 1.15, 4.5], { size: 12.5 });
    card(s, MX + 7.9, 1.45, W - 7.9, 4.45, SOFT, "Tự tính cos(39,992698°) bằng tay", NAVY, TEAL);
    bullets(s, ["cos 40° = 0,766044; sin 40° = 0,642788",
      "40° − 39,992698° = 0,007302° = 1,2745·10⁻⁴ rad",
      "cos(40° − δ) ≈ cos 40° + sin 40°·δ = 0,766044 + 0,642788 × 1,2745·10⁻⁴",
      "= 0,766044 + 0,0000819 = **0,766126**",
      "Độ co ngược lại: 1 / 0,766126 = 1,305268 (khớp tệp kiểm tra)"], MX + 8.15, 2.05, W - 8.4, 3.8, 14);
    callout(s, "Hệ số chỉ **đổi đơn vị** (đơn vị tọa độ → mét): sai số mọi mô hình nhân cùng một hằng số, nên thứ tự các mô hình không phụ thuộc vào nó.", 6.1, 0.8, NAVY, "FFFFFF", 15);
  }

  // ------------------------------------------------------------------ 2. ba lợi ích
  function utility() {
    const tp = E.theta_pilot.phone_folds_theta20_all6_dev_mean_m, r = E.rssi, sw = r.share_within_db;
    const s = sup("Vì sao ba lợi ích", "Vì sao rank, abs, rel; từ đâu −104 dBm, 0 dBm, 40 dB, 3 mức",
      "Nếu hỏi: tại sao cửa sổ rel là 40 dB? Thành thật: 40 dB chọn trước theo quy ước, chưa dò lưới; kiểm lại sau thì 89,9% lần đọc nằm trong 40 dB so với AP mạnh nhất cùng vân tay (30 dB: 71,1%; 50 dB: 96,7%), nên cửa sổ này bao phần lớn dữ liệu. −104 và 0 dBm là giá trị nhỏ nhất và lớn nhất thật sự có trong trainingData (358 763 lần đọc). Thang q từ 1 đến 100 là quy ước để lợi ích là số nguyên; minUtil là tỷ lệ phần trăm nên không phụ thuộc thang (ngoài sai số làm tròn). Nếu hỏi vì sao rel kém nhất khi đứng một mình mà thêm vào lại giúp nhiều nhất: đó là giả thuyết bổ sung thông tin (rel bất biến với lệch thu thiết bị), chưa kiểm riêng.");
    const rows = [
      ["q ∈ [1, 100]; 0 = không nghe", "quy ước", "AP nghe được có q ≥ 1 (số nguyên); AP không nghe (RSSI = 100) có q = 0. Thang 100 là quy ước; minUtil = θ% × tổng nên không phụ thuộc thang"],
      [`−104 và 0 dBm (abs)`, "đếm", `RSSI nhỏ nhất / lớn nhất thật sự có trong ${vn(r.n_readings, 0)} lần đọc của trainingData: −${Math.abs(r.min_detected)} và ${r.max_detected}`],
      ["W = 40 dB (rel)", "quy ước", `chọn trước, **chưa dò lưới**; kiểm sau: ${pct(sw["40"], 1)} lần đọc nằm trong 40 dB so với AP mạnh nhất (30 dB: ${pct(sw["30"], 1)}; 50 dB: ${pct(sw["50"], 1)})`],
      ["3 mức (L3)", "quy ước", "mức = ⌊(q − 1)/100 × 3⌋: q = 1–34 thấp, 35–67 vừa, 68–100 cao; **chưa quét** L khác"]];
    tb(s, ["Con số", "Loại", "Từ đâu"], rows, MX, 1.5, 7.6, [1.9, 0.95, 4.75], { size: 12.5 });
    head(s, "Chọn lợi ích nền (dev, θ = 20%)", MX + 7.9, 1.45, W - 7.9);
    const yu = tb(s, ["Lợi ích", "Sai số dev (m)"], [["rank", vn(tp.rank, 3)], ["abs", vn(tp.abs, 3)], ["rel", vn(tp.rel, 3)]], MX + 7.9, 1.85, W - 7.9, [2.2, 2.0], { size: 13.5, align: ["left", "right"], hl: (i) => i === 0 });
    note(s, `6 fold theo điện thoại, ước lượng V4. rank thắng abs chỉ ${vn(tp.abs - tp.rank, 3)} m; rel yếu nhất khi đứng riêng. Nhưng khi **thêm** rel làm bằng chứng bổ sung: −0,195 m (6/6 fold), mức giảm lớn nhất trong các HUI mới.`, MX + 7.9, yu + 0.15, W - 7.9, 1.8, INK, 13);
    callout(s, "Lý do thiết kế: các điện thoại đọc RSSI lệch nhau. **rank** bất biến với mọi biến đổi đơn điệu; **rel** bất biến với lệch hằng số; **abs** thì không. Mỗi cách mắc lỗi khác nhau nên bổ sung cho nhau (giả thuyết, chưa kiểm riêng).", 5.55, 1.2, SOFT2, INK, 14.5);
  }

  // ------------------------------------------------------------------ 3. theta
  function theta() {
    const tp = E.theta_pilot.results_dev_mean_m, cl = E.cells, v = Object.fromEntries(E.versions.map((x) => [x.version, x]));
    const s = sup("Vì sao ngưỡng khai thác", "Vì sao θ = 20% và ngân sách 10 s, 10 000 HUI, hệ số 1,25",
      "Nếu hỏi: tại sao không θ = 10%, tốt hơn? Thành thật: trong thí nghiệm thăm dò trên 2 fold dev, 10% tốt hơn 20% khoảng 0,6 m (7,138 so với 7,742 ở σ tốt nhất), nhưng tốn khoảng 25 phút khai thác mỗi fold. V2 dùng 10% với fold theo người dùng: dev 7,699 nhưng test 8,175; V3 chuyển sang fold theo điện thoại và θ = 20%: dev 7,669, test 7,997. Vậy 20% là thỏa hiệp chất lượng–chi phí, không phải điểm tối ưu trên dev. Cũng phải nói: θ thực dùng trung bình là 34,55% vì 72,5% số ô vượt ngân sách ở 20% và bị nâng ngưỡng (nhân 1,25). Ví dụ ô 1: 20 → 25 → 31,25 → 39,0625% sau 3 lần nâng (4 lần chạy).");
    head(s, "Thăm dò θ (dev, fold 1–2, ước lượng V4, mét)", MX, 1.45, 7);
    const rows = [["θ = 30%, không làm mượt", vn(tp["theta 30%, no smoothing"], 3)], ["θ = 20%, σ = 0", vn(tp["theta 20%, sigma 0"], 3)], ["θ = 20%, σ tốt nhất (6 m)", vn(tp["theta 20%, best sigma (6 m)"], 3)],
      ["θ = 10%, σ = 0", vn(tp["theta 10%, sigma 0"], 3)], ["θ = 10%, σ tốt nhất (6 m)", vn(tp["theta 10%, best sigma (6 m)"], 3)]];
    const yt = tb(s, ["Cấu hình", "Sai số dev (m)"], rows, MX, 1.85, 5.6, [3.6, 2.0], { size: 13, align: ["left", "right"], hl: (i) => i === 2 });
    bullets(s, [`θ nhỏ → nhiều HUI → tốt hơn trên dev: 10% hơn 20% **${vn(tp["theta 20%, best sigma (6 m)"] - tp["theta 10%, best sigma (6 m)"], 3)} m**, nhưng ~25 phút/fold khai thác`,
      `V2 (10%, fold theo người dùng): dev ${vn(v.v2.dev_mean_m, 3)} → test ${vn(v.v2.test_mean_m, 3)}; V3 (20%, fold theo điện thoại): ${vn(v.v3.dev_mean_m, 3)} → ${vn(v.v3.test_mean_m, 3)}`,
      "**Kết luận trung thực:** 20% là thỏa hiệp chất lượng–chi phí, không phải cực tiểu của dev"], MX, yt + 0.12, 6.0, 6.85 - yt - 0.12, 13, INK, 5);
    card(s, MX + 6.3, 1.45, W - 6.3, 5.4, SOFT2, "Ngân sách và tự nâng ngưỡng", RUST, RUST);
    bullets(s, [`**10 s, 10 000 HUI:** ngân sách tính toán (không dò). Lần chạy cuối của mọi ô ≤ ${vn(cl.max_runtime_s, 2)} s nên giới hạn thời gian không kích hoạt; giới hạn 10 000 HUI mới chặn`,
      `**× 1,25:** hệ số nâng ngưỡng khi vượt ngân sách. Ô 1: ${cl.cell1.n_attempts} lần chạy, θ = 20 × 1,25³ = **${vn(cl.cell1.theta_used_pct, 4)}%** (20 → 25 → 31,25 → 39,0625)`,
      `**${pct(cl.share_escalated, 1)}** số ô phải nâng ít nhất một lần; θ thực dùng trung bình **${vn(cl.mean_theta_used_pct, 2)}%**, nhiều nhất ${cl.max_attempts} lần chạy`,
      `Tổng **${vn(cl.total_huis, 0)}** HUI = 933 ô × ${vn(cl.mean_huis, 0)} HUI trung bình (mô hình rank)`,
      "Không bao giờ giữ tập HUI bị cắt cụt: nâng ngưỡng rồi chạy lại"], MX + 6.55, 2.0, W - 6.8, 4.8, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ 4. P, V, gamma, tau, beta
  function match() {
    const gt = G.gamma_tau, be = G.beta;
    const s = sup("Vì sao P·V³", "Vì sao điểm khớp P·V³ và γ = 2, τ = 20, β = 3",
      "Nếu hỏi: tại sao γ = 2, τ = 20, β = 3? Chúng được chọn bằng lưới trên dev ở giai đoạn V4 (2 880 cấu hình: 2 lợi ích × 3 cặp (γ,τ) × 2 giá trị β × 4 giá trị σ × 3 giá trị kf × 5 giá trị m × 4 giá trị p), cấu hình sai số dev thấp nhất là 7,6532 m. Bảng bên phải là 'đổi một tham số, giữ các tham số còn lại ở giá trị đã chọn'. Phải nói thẳng: lưới thô, chỉ 3 cặp (γ,τ) nên chưa thử (γ=2, τ=40); β chỉ thử 1 và 3. V6 và V7 giữ nguyên các giá trị này và chưa dò lại theo sai số của V7. Hằng số nào cũng có trực giác: γ = 2 phạt mẫu khớp dở (khớp một nửa chỉ còn 0,25), τ = 20 dB định mức lệch cường độ chấp nhận được, β = 3 làm độ phủ V chi phối.");
    head(s, "Mỗi thành phần cư xử thế nào (tự tính bằng tay)", MX, 1.45, 7.2);
    const rows = [["frac^{γ}, γ = 2", "khớp nửa mẫu (frac = 0,5): γ = 1 → 0,50; **γ = 2 → 0,25**; khớp trọn → 1: phạt khớp dở"],
      ["exp(−Δq/τ), τ = 20", "Δq = 10: τ = 20 → **0,607**, τ = 40 → 0,779; Δq = 20: 0,368 / 0,607 (e^{−0,5} và e^{−1})"],
      ["V^{β}, β = 3", "độ phủ V = 0,8: β = 1 → 0,800; **β = 3 → 0,512**; V = 0,5: 0,500 / 0,125 ⇒ ô giải thích ít AP bị phạt nặng"],
      ["Vì sao nhân P và V", "P: ô chứa bao nhiêu mẫu mạnh của mình; V: ô giải thích bao nhiêu phần vân tay. Cả hai phải cao"]];
    const ym = tb(s, ["Thành phần", "Ví dụ số"], rows, MX, 1.85, 7.2, [1.9, 5.3], { size: 12.5 });
    head(s, "Dev: đổi một tham số, giữ phần còn lại (m)", MX + 7.5, 1.45, W - 7.5);
    const r2 = [...gt.map((x) => [`(γ, τ) = (${x.gamma}, ${x.tau})`, vn(x.dev_mean_m, 3)]), ...be.map((x) => [`β = ${x.beta}`, vn(x.dev_mean_m, 3)])];
    const yg = tb(s, ["Cấu hình", "Sai số dev"], r2, MX + 7.5, 1.85, W - 7.5, [2.7, 1.9], { size: 13, align: ["left", "right"], hl: (i) => i === 2 || i === 4 });
    note(s, `${vn(G.n_configurations, 0)} cấu hình = 2 lợi ích × 3 (γ,τ) × 2 β × 4 σ × 3 kf × 5 m × 4 p; cực tiểu dev = ${vn(G.selected_dev_mean_m, 4)} m.`, MX + 7.5, yg + 0.12, W - 7.5, 0.8, INK, 12.5);
    callout(s, "**Thừa nhận:** lưới thô (chưa thử γ = 2 với τ = 40; β chỉ 1 và 3). Đây là sai số của ước lượng V4 (7,65 m); V6/V7 giữ nguyên P, V làm đặc trưng và **chưa dò lại** các hằng số theo sai số V7.", Math.max(ym, yg + 0.95) + 0.15, 1.15, SOFT2, INK, 14);
  }

  // ------------------------------------------------------------------ 5. sigma, kf, K
  function smooth() {
    const sg = G.sigma, kf = G.kf, nn = E.nn_cells, bk = E.best_of_k;
    const g3 = (d) => Math.exp(-(d * d) / (2 * 9));
    const s = sup("Vì sao các hằng số làm mượt", "Vì sao σ = 3 m, kf = 20 và 30 ô ứng viên",
      "Nếu hỏi: tại sao σ = 3 m? Khoảng cách từ một ô tới ô gần nhất cùng tầng có trung vị 2,22 m, P75 = 3,82 m (933 ô), nên σ = 3 m làm mượt trong phạm vi một–hai ô lân cận. Trong lưới {0, 3, 6, 10} thì σ = 3 cho sai số dev thấp nhất (7,653 m), chưa thử các giá trị xen kẽ. Nếu hỏi kf = 20: đó là biên trên của lưới {3, 10, 20}; cải thiện so với kf = 10 chỉ 0,016 m nên coi là bão hòa, không phải tối ưu chính xác; độ chính xác tầng của V4 còn giảm nhẹ khi kf tăng (84,18% → 83,84%). K = 30: ô tiên tri (dùng nhãn thật, chỉ để đo) cho thấy lợi ích giảm dần: K = 20 → 0,732 m, K = 30 → 0,588 m; K = 30 chọn từ V5, chưa quét K theo sai số cuối cùng.");
    head(s, "σ và kf (dev, các tham số khác giữ nguyên, m)", MX, 1.45, 6.2);
    const rows = [...sg.map((x) => [`σ = ${x.sigma} m`, vn(x.dev_mean_m, 3), "—"]), ...kf.map((x) => [`kf = ${x.kf}`, vn(x.dev_mean_m, 3), pct(x.joint_accuracy, 2)])];
    const ys = tb(s, ["Cấu hình", "Sai số dev", "Đúng tầng (V4)"], rows, MX, 1.85, 6.2, [2.2, 1.9, 2.1], { size: 12.5, minH: 0.36, align: ["left", "right", "right"], hl: (i) => i === 1 || i === 6 });
    bullets(s, [`Khoảng cách ô gần nhất cùng tầng: trung vị **${vn(nn.median, 2)} m**, P75 ${vn(nn.p75, 2)} m ⇒ σ = 3 m ≈ một–hai ô. Trọng số Gauss: d = ${vn(nn.median, 2)} m → **${vn(g3(Number(nn.median.toFixed(2))), 3)}**, d = 6 m → ${vn(g3(6), 3)}`,
      "**kf = 20 nằm ở biên trên của lưới**; hơn kf = 10 chỉ 0,016 m: bão hòa, không phải tối ưu chính xác"], MX, ys + 0.1, 6.2, 6.9 - ys - 0.1, 12.5, INK, 4);
    head(s, "K: ô tiên tri trong K ứng viên đầu (dev)", MX + 6.5, 1.45, W - 6.5);
    const r2 = bk.filter((x) => [1, 5, 10, 20, 30].includes(x.K)).map((x) => [x.K, vn(x.mean_m, 3), pct(x.under3, 1)]);
    const yk = tb(s, ["K", "Ô gần nhất cách (m)", "Dưới 3 m"], r2, MX + 6.5, 1.85, W - 6.5, [0.9, 2.6, 2.1], { size: 13, align: ["center", "right", "right"], hl: (i) => i === 4 });
    note(s, `Từ K = 20 lên 30 chỉ giảm thêm ${vn(bk.find((x) => x.K === 20).mean_m - bk.find((x) => x.K === 30).mean_m, 3)} m: lợi ích giảm dần trong khi bộ chấm điểm phải xử lý thêm ô. **K = 30 chọn từ V5, chưa quét K theo sai số cuối cùng.** "Tiên tri" dùng vị trí thật nên chỉ để đo trần.`, MX + 6.5, yk + 0.15, W - 6.5, 6.9 - yk - 0.15, INK, 13);
  }

  // ------------------------------------------------------------------ 6. V6
  function v6() {
    const R = E.v6_rerank_grid.gbm_floor;
    const s = sup("Vì sao V6 như vậy", "Vì sao V6 dùng GBM 300 cây, m = 20, λ = 2 (đường cơ sở)",
      "V6 chỉ là đường cơ sở để so sánh; V7 bỏ cả m và λ vì học trọng số trực tiếp. Nếu hỏi: tại sao m = 20, λ = 2? Bề mặt sai số phẳng quanh cực tiểu: m từ 5 đến 12 và λ từ 1 đến 2 cho sai số dev 7,190–7,212 m, chênh vài centimet; λ = 4 tệ hơn rõ (7,28–7,33). m = 20, λ = 2 không phải cực tiểu duy nhất. Siêu tham số của GBM (300 cây, lr 0,06, 31 lá, tối thiểu 40 mẫu/lá, L2 = 1) là cấu hình cố định, không có lưới riêng trong kho; GBM được chọn thay Ridge vì dev tốt hơn (7,190 so với 7,327).");
    head(s, "Lưới m × λ của bộ xếp hạng GBM (dev, m)", MX, 1.45, 7);
    const ms = [3, 5, 8, 12], ls = ["0.5", "1.0", "2.0", "4.0"];
    const rows = ms.map((m) => [`m = ${m}`, ...ls.map((l) => vn(R[`${m}|${l}`], 3))]);
    const yv = tb(s, ["", "λ = 0,5", "λ = 1", "λ = 2", "λ = 4"], rows, MX, 1.85, 7.2, [1.4, 1.45, 1.45, 1.45, 1.45], { size: 13, align: ["left", "right", "right", "right", "right"] });
    const vals = ms.flatMap((m) => ls.map((l) => R[`${m}|${l}`])), K40 = E.v6_rerank_grid.gbm_building_k40;
    bullets(s, [`Cực tiểu của lưới này: m = 12, λ = 2 → **${vn(E.v6_rerank_grid.gbm_best, 3)} m**; GBM thắng Ridge (${vn(E.v6_rerank_grid.ridge_best, 3)} m)`,
      `Quanh cực tiểu (m = 5–12, λ = 1–2) sai số chỉ **${vn(Math.min(...[5, 8, 12].flatMap((m) => ["1.0", "2.0"].map((l) => R[`${m}|${l}`]))), 3)}–${vn(Math.max(...[5, 8, 12].flatMap((m) => ["1.0", "2.0"].map((l) => R[`${m}|${l}`]))), 3)} m**; cả bảng ${vn(Math.min(...vals), 3)}–${vn(Math.max(...vals), 3)} m`,
      `V6 dùng m = 20 (K = 30). Lưới tòa nhà K = 40 có m = 20: λ = 2 → ${vn(K40["20|2.0"], 3)} m so với m = 12: ${vn(K40["12|2.0"], 3)} m (chênh ${vn(Math.abs(K40["12|2.0"] - K40["20|2.0"]), 3)} m)`], MX, yv + 0.15, 7.2, 6.9 - yv - 0.15, 13.5, INK, 6);
    card(s, MX + 7.5, 1.45, W - 7.5, 5.4, SOFT2, "Điều cần thừa nhận", RUST, RUST);
    bullets(s, ["m = 20, λ = 2 **không** là cực tiểu duy nhất của lưới; quanh cực tiểu các lựa chọn khác nhau chỉ vài centimet (bên trái)",
      "Siêu tham số GBM là cấu hình cố định, **không có lưới riêng**",
      "**V7 không còn m, λ:** trọng số do bộ chấm điểm học, huấn luyện bằng sai số mét",
      "Vì vậy ngay cả khi bị hỏi về hai số này, kết quả V7 không phụ thuộc vào chúng; chỉ đường cơ sở V6 phụ thuộc"], MX + 7.75, 2.0, W - 8.0, 4.7, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ 7. năm góc nhìn
  function views() {
    const c1 = dI("C_rel"), c2 = dI("C_rel_absL3"), cl = E.cells;
    const s = sup("Vì sao 5 góc nhìn", "Vì sao 5 góc nhìn HUI và vì sao giữ abs mức-3 dù lợi ích nhỏ",
      "Nếu hỏi: abs-L3 giảm chỉ 0,034 m và khoảng tin cậy chứa 0, sao vẫn giữ? Quy tắc chọn được khai báo trước khi chấm test: chọn biến thể có sai số dev thấp hơn VÀ tốt hơn ở ít nhất 4/6 fold. V7-C2 đạt (4/6, thấp hơn 0,034 m); do đó giữ, nhưng nói rõ lợi ích nhỏ và không có ý nghĩa thống kê riêng. Số HUI là kết quả của EFIM, kiểm bằng cách cộng cột n_huis của 933 ô (cell_runs.csv): 3 238 416 cho mô hình rank.");
    const rows = [["rank", "V4", "nền: thứ hạng cường độ", vn(D.config.hui.final_hui_counts.rank, 0)], ["rank-L3", "V5", "mục (AP, mức 1–3)", vn(D.config.hui.final_hui_counts.rank_L3, 0)], ["abs", "V6", "cường độ tuyệt đối", vn(D.config.hui.final_hui_counts.abs, 0)],
      ["**rel**", "V7-C1", "so với AP mạnh nhất", vn(D.config.hui.final_hui_counts.rel, 0)], ["**abs-L3**", "V7-C2", "(AP, mức) tuyệt đối", vn(D.config.hui.final_hui_counts.abs_L3, 0)]];
    head(s, "Mỗi góc nhìn được thêm ở đâu, có nhiều HUI cỡ nào", MX, 1.45, 7.5);
    const yw = tb(s, ["Góc nhìn", "Thêm ở", "Ý nghĩa", "Số HUI"], rows.map((r) => r.map((x) => x.replace(/\*\*/g, ""))), MX, 1.85, 7.6, [1.5, 1.2, 2.9, 2.0], { size: 13, align: ["left", "center", "left", "right"], hl: (i) => i >= 3 });
    bullets(s, [`Mức giảm dev khi thêm góc nhìn (có thông tin): V4 **${vn(dI("V4").mean, 3)}** → V5 **${vn(dI("V5").mean, 3)}** → V6* **${vn(dI("V6*").mean, 3)}** m`,
      `Thêm **rel**: ${vnd(c1.mean - dI("B_base").mean, 3)} m, tốt hơn 6/6 fold, KTC cặp [−0,283; −0,106] (không chứa 0)`,
      `Thêm **abs-L3**: ${vnd(c2.mean - c1.mean, 3)} m, tốt hơn 4/6 fold, KTC [−0,087; +0,054] (chứa 0)`], MX, yw + 0.15, 7.6, 6.9 - yw - 0.15, 13.5, INK, 6);
    card(s, MX + 7.9, 1.45, W - 7.9, 5.4, SOFT, "Vì sao giữ abs-L3", TEAL, TEAL);
    bullets(s, ["Quy tắc chọn khai báo trước test: dev thấp hơn **và** tốt hơn ≥ 4/6 fold; abs-L3 đạt (4/6)",
      "Nhưng **không có ý nghĩa thống kê riêng**: lợi ích nhỏ, nói thẳng như vậy",
      `Tổng số HUI mô hình rank = Σ cột n_huis của 933 ô = **${vn(cl.total_huis, 0)}** (tự cộng được từ cell_runs.csv)`,
      "(AP, mức) coi AP mạnh và AP yếu là hai mục khác nhau ⇒ mẫu chi tiết hơn"], MX + 8.15, 2.0, W - 8.4, 4.7, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ 8. đặc trưng
  function features() {
    const s = sup("Vì sao 49 cột, ×4", "Vì sao 33 + 8 + 8 = 49 cột và 4 phép biến đổi (196 đầu vào)",
      "Nếu hỏi: tại sao 4 phép biến đổi? Vì quyết định là SO SÁNH 30 ô cùng một truy vấn: x − max, min-max trong truy vấn và hạng chỉ giữ thông tin tương đối giữa các ô, bất biến với thang của điểm. Dạng này đã dùng cho GBM từ V5 (hàm relative). Log có dấu nén đuôi dài rồi z-score cho Adam ổn định. Thành thật: chưa có thí nghiệm cắt riêng log có dấu; số 5,9588 → 5,9300 là khi đổi ĐỒNG THỜI sang tập hợp 5 thành viên và log có dấu. Khối 'bù lệch thiết bị' (13 cột) bị loại vì làm tệ đi 0,063 m.");
    const rows = [["33 cột V6", "quy ước", "kế thừa từ V5/V6, giữ nguyên để so sánh công bằng với V6"],
      ["+ 8 cột / mô hình mới", "định nghĩa", "P, V, R, điểm tương đối, hạng, MAE, corr, cos: bản rút gọn của các nhóm bằng chứng V6 (điểm khớp, độ phủ, hồ sơ cường độ)"],
      ["33 + 8 + 8 = **49**", "đếm", "V6 33 cột; + rel 8; + abs-L3 8"],
      ["× 4 phép biến đổi = **196**", "định nghĩa", "giá trị gốc, x − max, min-max, hạng (trong truy vấn); V7-B: 33 × 4 = 132"],
      ["log có dấu, z-score", "quy ước", "nén đuôi dài rồi chuẩn hóa để Adam ổn định; **chưa cắt riêng**"]];
    const yf = tb(s, ["Con số", "Loại", "Vì sao"], rows.map((r) => r.map((x) => x.replace(/\*\*/g, ""))), MX, 1.5, 7.9, [2.2, 1.1, 4.6], { size: 12.5 });
    card(s, MX + 8.2, 1.5, W - 8.2, 3.2, SOFT, "Vì sao dạng tương đối", NAVY, TEAL);
    bullets(s, ["Quyết định là **so sánh 30 ô cùng một truy vấn**; điểm tuyệt đối đổi theo từng vân tay",
      "x − max, min-max, hạng: giữ phần tương đối, bất biến với thang của điểm"], MX + 8.45, 2.05, W - 8.7, 2.6, 13.5, INK, 6);
    card(s, MX + 8.2, 4.85, W - 8.2, 2.0, SOFT2, "Đã thử và loại", RUST, RUST);
    bullets(s, ["Bù lệch thiết bị (13 cột): +0,063 m (tệ hơn)", "Đồng thuận không gian (15 cột): −0,006 m (không đáng kể)"], MX + 8.45, 5.4, W - 8.7, 1.4, 13, INK, 4);
    note(s, `Chưa tách: 5,9588 → ${vn(E.scorer.ens5_slog_base, 4)} m (dev) khi đồng thời đổi sang tập hợp 5 thành viên và log có dấu.`, MX, yf + 0.15, 7.9, 0.8, GREY, 12.5);
  }

  // ------------------------------------------------------------------ 9. scorer
  function scorer() {
    const sc = E.scorer;
    const s = sup("Vì sao MLP 32/16", "Vì sao MLP 32/16 có nhánh gộp, và 7 360 tham số từ đâu",
      "Số tham số tự cộng được: lớp 1 là 196×32 trọng số + 32 độ lệch = 6 304; lớp 2 nhận 64 đầu vào (h và trung bình h) nên 64×16 + 16 = 1 040; lớp cuối 16 trọng số; tổng 7 360. V7-B (132 đầu vào): 132×32+32 = 4 256, cộng 1 040 và 16 là 5 312. Nếu hỏi: tại sao 32/16 chứ không 64/32? Chỉ thử hai cấu hình (1 thành viên, dev 6 fold): 64/32 với weight decay 1e-4 cho 5,9797; 32/16 với 1e-3 cho 5,9588; chênh 0,021 m, chọn mạng nhỏ vì không kém mà ít tham số. Chưa có lưới sâu hơn; lr và batch chưa dò. Nhánh gộp (trung bình h trên 30 ô) để điểm ô i phụ thuộc các ô còn lại; chưa có thí nghiệm cắt riêng nhánh này.");
    head(s, "Tự cộng số tham số", MX, 1.45, 7);
    const rows = [["Lớp 1: 196 → 32", "196 × 32 + 32", "6 304"], ["Lớp 2: 64 → 16 (h ghép h̄)", "64 × 16 + 16", "1 040"], ["Đầu ra: 16 → 1", "16", "16"], ["**Tổng V7-C2**", "6 304 + 1 040 + 16", "**7 360**"], ["Tổng V7-B (132 đầu vào)", "(132 × 32 + 32) + 1 040 + 16", "5 312"]];
    const yc = tb(s, ["Thành phần", "Phép tính", "Tham số"], rows.map((r) => r.map((x) => x.replace(/\*\*/g, ""))), MX, 1.85, 7.2, [2.9, 2.7, 1.6], { size: 13, align: ["left", "left", "right"], hl: (i) => i === 3 });
    bullets(s, ["Lớp gộp: h̄ = trung bình h của 30 ô ⇒ điểm của ô i **phụ thuộc các ô còn lại** (quyết định là so sánh tương đối)", "ReLU: hàm kích hoạt chuẩn; **chưa thử** mạng sâu hơn hay rộng hơn ngoài hai cấu hình bên phải"], MX, yc + 0.15, 7.2, 6.9 - yc - 0.15, 13.5, INK, 6);
    card(s, MX + 7.5, 1.45, W - 7.5, 5.4, SOFT2, "Bằng chứng chọn 32/16 — và giới hạn", RUST, RUST);
    bullets(s, [`Chỉ so **hai** cấu hình (1 thành viên, dev 6 fold): MLP 64/32, wd 10⁻⁴ → **${vn(sc["mlp64_32_wd1e-4"], 4)}**; MLP 32/16, wd 10⁻³ → **${vn(sc["mlp32_16_wd1e-3"], 4)}** m`,
      `Chênh ${vn(sc["mlp64_32_wd1e-4"] - sc["mlp32_16_wd1e-3"], 3)} m: nhỏ; chọn mạng nhỏ hơn vì **không kém mà ít tham số hơn**`,
      "Hai thay đổi (kích thước mạng và weight decay) đổi **cùng lúc**, chưa tách riêng",
      "Chưa có lưới sâu hơn; chưa cắt riêng nhánh gộp; lr và batch chưa dò"], MX + 7.75, 2.0, W - 8.0, 4.7, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ 10. softmax
  function softmax() {
    const e = (x) => Math.exp(x), z = e(2) + e(1) + e(0), w = [e(2) / z, e(1) / z, e(0) / z];
    const s = sup("Vì sao softmax", "Vì sao softmax: tọa độ là tổng có trọng số các tâm ô",
      "Softmax làm trọng số không âm, tổng bằng 1, nên tọa độ dự đoán luôn nằm trong bao lồi của 30 tâm ô và học được bằng gradient. Hạn chế thừa nhận: bao lồi nghĩa là ở biên/đầu hành lang tọa độ bị kéo vào trong; nhóm biên cũng là nhóm sai số cao nhất. Chưa so sánh thực nghiệm với hồi quy tọa độ trực tiếp. V6 dùng w ∝ exp(−d̂/λ) trên 20 ô với m, λ cố định; V7 học s_i.");
    head(s, "Ví dụ tính tay: 3 ô với s = (2, 1, 0), tâm ô tại x = 0, 10, 20 m", MX, 1.45, 11);
    const rows = [["exp(s)", vn(e(2), 3), vn(e(1), 3), vn(e(0), 3), `tổng = ${vn(z, 3)}`], ["w = exp(s) / tổng", vn(w[0], 4), vn(w[1], 4), vn(w[2], 4), "tổng = 1,0000"], ["tâm ô x (m)", "0", "10", "20", ""], ["w · x", vn(w[0] * 0, 3), vn(w[1] * 10, 3), vn(w[2] * 20, 3), `x̂ = **${vn(w[1] * 10 + w[2] * 20, 3)} m**`]];
    const yx = tb(s, ["", "ô 1", "ô 2", "ô 3", "cộng"], rows, MX, 1.85, 8.2, [2.3, 1.3, 1.3, 1.3, 2.0], { size: 13.5, align: ["left", "right", "right", "right", "right"] });
    bullets(s, ["Trọng số ≥ 0, tổng = 1 ⇒ (x̂, ŷ) nằm trong **bao lồi** của 30 tâm ô: không thể dự đoán ra ngoài vùng ứng viên",
      "Khả vi ⇒ học được bằng gradient từ sai số mét (bước 8)", "Khác V6: w ∝ exp(−d̂/λ) trên 20 ô, m và λ cố định; V7 học s_{i}"], MX, yx + 0.2, 8.2, 6.9 - yx - 0.2, 13.5, INK, 6);
    card(s, MX + 8.5, 1.85, W - 8.5, 4.95, SOFT2, "Hạn chế thừa nhận", RUST, RUST);
    bullets(s, ["Bao lồi kéo tọa độ **vào trong** khi vị trí thật ở biên hoặc đầu hành lang; nhóm biên cũng là nhóm sai số cao nhất", "**Chưa so sánh** với hồi quy tọa độ trực tiếp bằng thực nghiệm", `Trần: ô gần nhất trong 30 cách ${vn(E.best_of_k.find((x) => x.K === 30).mean_m, 2)} m (dev), V7 đạt 5,70 m: còn dư địa ở khâu chọn trọng số`], MX + 8.75, 2.4, W - 9.0, 4.3, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ 11. loss & huấn luyện
  function loss() {
    const ep = E.epochs;
    const s = sup("Vì sao các siêu tham số huấn luyện", "Vì sao mất mát là sai số mét; lr, epoch, ε từ đâu",
      "Quy tắc trung thực: 'chưa dò' nghĩa là không có thí nghiệm nào trong kho. Mất mát bằng đúng chỉ số báo cáo (sai số mét trung bình). ε = 10⁻⁶ chỉ để đạo hàm xác định khi dự đoán trùng vị trí thật: √10⁻⁶ = 0,001 đơn vị = 0,00077 m, không ảnh hưởng kết quả. lr 5·10⁻⁴, batch 256, β của Adam là giá trị phổ biến, chưa dò lưới. Trần 30 epoch hầu như không chạm: V7-C2 không mô hình nào (epoch tốt nhất 5–29, trung vị 15). Dừng sớm: 8 epoch liền không cải thiện quá 10⁻⁴ m. Gradient viết tay đã kiểm bằng sai phân hữu hạn (lệch tương đối 5·10⁻⁸). Nếu bị hỏi có dò thêm không: có thể, nhưng phải chọn trên dev, không phải trên test.");
    const rows = [["L = TB(0,766126·‖ĉ − c‖)", "định nghĩa", "đúng chỉ số báo cáo; V6 tối ưu log(1 + d) từng ô (đại lượng thay thế)"],
      ["ε = 10⁻⁶", "định nghĩa", "tránh √0 khi ĉ = c; ảnh hưởng √10⁻⁶ × 0,766126 = 0,00077 m"],
      ["Adam, lr 5·10⁻⁴, batch 256", "quy ước", "mặc định phổ biến; **chưa dò lưới** lr và batch"],
      ["weight decay 10⁻³", "dev (2 cấu hình)", "thử 10⁻⁴ (mạng 64/32) và 10⁻³ (mạng 32/16); đổi cùng lúc với kích thước mạng"],
      ["tối đa 30 epoch", "ngân sách", `epoch tốt nhất V7-C2: ${ep.C2.min}–${ep.C2.max} (trung vị ${vn(ep.C2.median, 0)}); **${ep.C2.n_at_cap}/${ep.C2.n_members}** chạm trần 30`],
      ["dừng sớm, kiên nhẫn 8", "quy ước", "dừng khi 8 epoch liền không giảm quá 10⁻⁴ m trên fold dừng sớm"],
      ["5 thành viên", "định nghĩa", "6 fold − 1 fold đánh giá = 5 fold huấn luyện; mỗi thành viên dừng sớm trên một fold khác"],
      ["gradient viết tay", "kiểm", "sai phân hữu hạn: lệch tương đối 5·10⁻⁸ (tests/test_v7.py)"]];
    tb(s, ["Con số", "Loại", "Vì sao / bằng chứng"], rows, MX, 1.5, W, [3.1, 1.6, W - 4.7], { size: 12.5, minH: 0.5 });
  }

  // ------------------------------------------------------------------ 12. folds
  function folds() {
    const f = E.folds, v = Object.fromEntries(E.versions.map((x) => [x.version, x]));
    const s = sup("Vì sao 6 fold theo điện thoại", "Vì sao 6 fold theo điện thoại và tập hợp 5 thành viên",
      "Nếu hỏi: tại sao fold theo điện thoại? validationData có 11 điện thoại trong đó 9 chưa từng thấy ở huấn luyện, nên dev phải giữ lại cả điện thoại để mô phỏng. Bằng chứng: V2 chọn theo fold người dùng cho dev 7,699 nhưng test 8,175 (không chuyển); V3 chuyển sang fold theo điện thoại: dev 7,669, test 7,997. Tại sao 6? 16 điện thoại chia bằng GroupKFold thành 6 nhóm; 6 là số đã dùng từ V3 và V7 giữ nguyên để so sánh công bằng với V6, chưa quét số fold. Hạn chế thừa nhận: các fold không cân bằng; fold 0 và 1 mỗi fold chỉ một điện thoại (14 và 13) và chiếm 47% số vân tay.");
    head(s, "6 fold của GroupKFold theo PHONEID (16 điện thoại)", MX, 1.45, 7);
    const rows = f.map((x) => [`fold ${x.fold + 1}`, x.phones.join(", "), vn(x.rows, 0), pct(x.rows / 19937, 1)]);
    const yd = tb(s, ["Fold", "Điện thoại", "Vân tay", "Tỷ lệ"], rows, MX, 1.85, 6.8, [1.2, 2.6, 1.5, 1.5], { size: 13, align: ["center", "left", "right", "right"] });
    note(s, `Tổng ${vn(f.reduce((a, x) => a + x.rows, 0), 0)} vân tay (khớp 19 937). Fold 1 và 2 mỗi fold chỉ một điện thoại (14 và 13) và chiếm ${pct((f[0].rows + f[1].rows) / 19937, 1)}: **các fold không cân bằng**.`, MX, yd + 0.15, 6.8, 1.1, INK, 13);
    card(s, MX + 7.1, 1.45, W - 7.1, 5.4, SOFT, "Vì sao điện thoại, vì sao 6, vì sao 5", NAVY, TEAL);
    bullets(s, [`Test có 11 điện thoại, **9 chưa từng thấy**; dev phải giữ lại cả điện thoại`,
      `V2 (fold theo người dùng): dev ${vn(v.v2.dev_mean_m, 3)} → test ${vn(v.v2.test_mean_m, 3)} (không chuyển); V3 (theo điện thoại): ${vn(v.v3.dev_mean_m, 3)} → ${vn(v.v3.test_mean_m, 3)}`,
      "**6 fold:** số đã dùng từ V3, V7 giữ để so sánh công bằng với V6; chưa quét số fold",
      "**5 thành viên:** 6 − 1 fold đánh giá = 5 fold huấn luyện; thành viên i dừng sớm trên fold i, huấn luyện trên 4 fold còn lại"], MX + 7.35, 2.0, W - 7.6, 4.7, 13.5, INK, 6);
  }

  // ------------------------------------------------------------------ phụ lục
  function qa() {
    const b = D.nested, v7 = T7, v6 = T6r;
    const gB = tr("B_base").mean - v6.mean, gRel = tr("C_rel").mean - tr("B_base").mean, gAbs = v7.mean - tr("C_rel").mean;
    const mk = (kicker, title, rows, notes) => {
      const s = sup(kicker, title, notes);
      tb(s, ["Câu hỏi dự kiến", "Trả lời ngắn, kèm số có thể kiểm"], rows, MX, 1.45, W, [3.6, W - 3.6], { size: 12.5, minH: 0.8 });
    };
    mk("Hỏi–đáp (1/2)", "Câu hỏi hóc búa dự kiến (1/2): kết quả và kiểm định", [
      ["Mục tiêu dưới 6 m chưa đạt, sao vẫn kết luận V7 tốt hơn V6?", `Không nói đạt mục tiêu. Giảm ${vn(-v7.diff_vs_V6, 3)} m (${vn(-v7.pct_vs_ref, 1)}%) trên test, KTC 95% cặp [${vnd(v7.diff_lo, 2)}; ${vnd(v7.diff_hi, 2)}] không chứa 0; dev ${vnd(dI("C_rel_absL3")["diff_vs_V6*"], 3)} m.`],
      ["validationData đã dùng từ V1 đến V6: có overfit vào test?", "Có nguy cơ, nên chọn mô hình chỉ bằng dev; mỗi biến thể chấm đúng một lần và báo cả biến thể không chọn (V7-A tệ hơn 0,020 m; V7-D tệ hơn 0,014 m). Test là chỉ báo, không phải ước lượng độc lập."],
      [`Dev ${vn(dI("C_rel_absL3").mean, 2)} m mà test ${vn(v7.mean, 2)} m: vì sao test cao hơn?`, `V6 cũng vậy: ${vn(dI("V6*").mean, 3)} → ${vn(v6.mean, 3)} (${vnd(v6.mean - dI("V6*").mean, 2)}); V7: ${vn(dI("C_rel_absL3").mean, 3)} → ${vn(v7.mean, 3)} (${vnd(v7.mean - dI("C_rel_absL3").mean, 2)}). Test có 9/11 điện thoại chưa từng thấy và thu muộn hơn; chênh gần bằng nhau ở mọi phiên bản nên không phải lỗi riêng của V7.`],
      ["Siêu tham số chọn trên dev: có overfit dev?", `Lưới thô (${vn(G.n_configurations, 0)} cấu hình), kf = 20 ở biên lưới. Đã đo rò rỉ bậc hai bằng giao thức lồng nhau: ${vnd(b.diff, 4)} m (fold ngoài 2) — không đo được rò rỉ đáng kể.`],
      ["Ý nghĩa thống kê thế nào?", "Bootstrap 4 000 lần lấy lại CẢ điện thoại (cụm). Test chỉ 11 cụm (điện thoại 13 chiếm 33% vân tay) nên KTC của trung bình rộng [5,65; 7,21]; phải đọc KTC của chênh lệch cặp."]],
      "Phần hỏi–đáp: mỗi trả lời có số kiểm được trong báo cáo V7 (§6) hoặc trong so_lieu_V7. Nếu bị hỏi điều chưa dò (lr, batch, số fold, K): nói thẳng 'chưa dò', và nói sẽ chọn trên dev, không phải trên test.");
    mk("Hỏi–đáp (2/2)", "Câu hỏi hóc búa dự kiến (2/2): thiết kế và vai trò của HUIM", [
      ["HUIM là lõi hay chỉ tiền xử lý cho MLP?", `Ứng viên, tầng và mọi đặc trưng đều sinh từ HUI. Nhưng mức giảm lớn nhất đến từ bộ chấm điểm học trực tiếp (${vnd(gB, 3)} m test), HUI mới rel ${vnd(gRel, 3)} m và abs-L3 ${vnd(gAbs, 3)} m. Nói thẳng: HUI cho bằng chứng, bộ chấm điểm quyết định trọng số.`],
      ["Vì sao không k-NN / so khớp vân tay thô?", "Ràng buộc đề bài. Mô hình chỉ gồm HUI (tập mục, lợi ích, support) và vị trí ô; kiểm bằng quét cú pháp 9 mô-đun suy luận (T12) và test tĩnh; vân tay huấn luyện không được lưu."],
      ["Vì sao không θ = 10% (tốt hơn trong thăm dò)?", "Tốt hơn 0,6 m ở fold 1–2 nhưng ~25 phút khai thác mỗi fold; V2 (10%, fold theo người dùng) dev 7,699 → test 8,175. 20% là thỏa hiệp chất lượng–chi phí, và θ thực dùng sau tự nâng ngưỡng là 34,55%."],
      ["rel kém nhất khi đứng riêng, sao thêm vào lại giúp nhất?", "Dev khi đứng riêng: rank 7,669; abs 7,685; rel 8,362. Thêm làm bằng chứng bổ sung: −0,195 m, 6/6 fold. Giả thuyết: rel bất biến với lệch thu của thiết bị nên bổ sung cho abs/rank; chưa kiểm riêng."],
      ["Vì sao softmax trên 30 ô, không hồi quy tọa độ trực tiếp?", "Softmax giữ kết quả trong bao lồi các ô ứng viên và học được từ sai số mét; hồi quy trực tiếp có thể trả điểm ngoài vùng khả dĩ. **Chưa so sánh thực nghiệm** hai cách; bao lồi kéo tọa độ vào trong ở biên."]],
      "Câu đầu tiên là câu dễ bị hỏi nhất: trả lời thẳng rằng phần lớn mức giảm đến từ bộ chấm điểm học trực tiếp; HUI cung cấp ứng viên và mọi đặc trưng; không có k-NN.");
  }

  function index() {
    const mk = (n, rows) => {
      const s = sup(`Bản đồ nguồn gốc con số (${n}/2)`, `Bản đồ nguồn gốc con số (${n}/2): mỗi số thuộc loại nào`,
        "Bảng tra nhanh. Loại: ĐẾM = tự đếm lại từ dữ liệu; ĐỊNH NGHĨA = theo công thức/thiết kế; ĐO = đo trên dữ liệu; QUY ƯỚC = giá trị phổ biến chưa dò; DEV = chọn bằng lưới/so sánh trên dev; NGÂN SÁCH = giới hạn tính toán. Khi bị hỏi một con số, trả lời đúng loại của nó và nêu điều chưa dò.");
      tb(s, ["Con số", "Loại", "Từ đâu (một dòng)"], rows, MX, 1.45, W, [3.5, 1.7, W - 5.2], { size: 12.5, minH: 0.55 });
    };
    mk(1, [["0,766126", "định nghĩa", "cos(vĩ độ 39,992698°) của Web-Mercator"],
      ["19 937 / 19 861 / 76 vân tay; 933 ô; 21,29/ô", "đếm", "dòng CSV; 19 861 / 933 = 21,29"],
      ["q ∈ [1, 100]; −104…0 dBm", "quy ước / đếm", "thang số nguyên; RSSI nhỏ nhất và lớn nhất thật có trong dữ liệu"],
      ["W = 40 dB; 3 mức", "quy ước", "chưa dò; 89,9% lần đọc trong 40 dB"],
      ["θ = 20% (thực dùng 34,55%)", "dev + ngân sách", "thăm dò dev: 10% tốt hơn 0,6 m nhưng ~25 phút/fold; 72,5% ô bị nâng ngưỡng"],
      ["10 s / 10 000 HUI / × 1,25", "ngân sách", "giới hạn tính toán; ô 1: 20 × 1,25³ = 39,0625%"],
      ["γ = 2, τ = 20, β = 3", "dev (lưới thô)", "2 880 cấu hình; (γ,τ) 3 cặp, β ∈ {1,3}"],
      ["σ = 3 m, kf = 20", "dev", "σ ∈ {0,3,6,10}; kf ∈ {3,10,20} (20 ở biên)"]]);
    mk(2, [["K = 30 ô ứng viên", "quy ước + đo", "ô tiên tri: K = 20 → 0,732 m; K = 30 → 0,588 m; chưa quét K"],
      ["m = 20, λ = 2, GBM 300 cây (V6)", "dev / quy ước", "bề mặt phẳng (7,19–7,21 m quanh cực tiểu); GBM không có lưới riêng; V7 không dùng"],
      ["33 + 8 + 8 = 49; × 4 = 196", "định nghĩa", "33 cột V6 + 8 mỗi mô hình mới; 4 phép biến đổi tương đối"],
      ["MLP 32/16, 7 360 tham số", "dev (2 cấu hình)", "196×32+32 + 64×16+16 + 16; 64/32: 5,9797 vs 32/16: 5,9588"],
      ["lr 5·10⁻⁴, batch 256, ε = 10⁻⁶", "quy ước", "chưa dò lưới; ε chỉ tránh √0"],
      ["30 epoch, kiên nhẫn 8", "ngân sách / quy ước", "epoch tốt nhất 5–29, trung vị 15"],
      ["6 fold, 5 thành viên", "quy ước / định nghĩa", "16 điện thoại → 6 nhóm; 6 − 1 = 5"],
      ["12,90 triệu HUI; 6,309 m; 5,702 m", "đếm / đo", "EFIM (khớp vét cạn); chấm lại độc lập bằng Excel, Python, verify_v7"]]);
  }

  return { coord, utility, theta, match, smooth, v6, views, features, scorer, softmax, loss, folds, appendix: () => { qa(); index(); } };
};
