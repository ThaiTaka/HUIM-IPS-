// Chương 3 (mô hình đề xuất) và Chương 4 (thực nghiệm) của báo cáo; gọi từ build_report.js.
module.exports = function (ctx) {
  const { add, fig, D, U, UT, SEL, PRM, V6, U4, RSH, allTests, nOk, others, refU, fs4, pil, win, EX, GF, nHUI3,
    phones, floors, IMP, order, T, L_ } = ctx;
  const { vn, pct, P, PN, H1, H2, H3, BUL, NUMS, GAP, r, fr, sb, sp, sbsp, sum, rb, sq, cb, up, abs, flo,
    EQ, TAB, ALGO, BOX, C, RT, L } = L_;
  const mn = Math.min(...others.map((x) => x.v.sai_so_tb_m)), mx = Math.max(...others.map((x) => x.v.sai_so_tb_m));

  // ================================================================ CHƯƠNG 3
  add(H1("CHƯƠNG 3. MÔ HÌNH ĐỊNH VỊ ĐỀ XUẤT DỰA TRÊN KHAI THÁC TẬP MỤC LỢI ÍCH CAO"));
  add(H2("3.1. Ý tưởng và tổng quan hệ thống"));
  add(P(`Ý tưởng cốt lõi là coi mỗi điểm tham chiếu của tập huấn luyện như một “cửa hàng” và mỗi vân tay đo tại đó như một “hoá đơn”: các AP được phát hiện là các mặt hàng, cường độ tín hiệu là lợi ích của mặt hàng. Các tập AP mạnh thường cùng xuất hiện tại một điểm — chính là các HUI của cơ sở dữ liệu giao dịch của điểm đó — tạo thành “chữ ký” của vị trí. Một vân tay mới được định vị bằng cách đo nó khớp với chữ ký HUI của điểm nào nhất.`));
  const f31 = fig(3, "d01_tong_quan.png", "Sơ đồ tổng quát của hệ thống định vị dựa trên HUIM (không k-NN)");
  add(P(`Hệ thống gồm hai pha (${f31.label}). **Pha huấn luyện** thực hiện một lần: chuyển RSSI thành lợi ích nội (Bước 1), nhóm vân tay theo điểm tham chiếu thành các cơ sở dữ liệu giao dịch (Bước 2), khai thác HUI của từng cơ sở dữ liệu bằng EFIM (Bước 3) và lưu mô hình là tập HUI cùng toạ độ, tầng của từng ô (Bước 4). **Pha định vị** xử lý từng vân tay: chấm điểm khớp với HUI của mọi ô (Bước 5), làm mượt điểm theo không gian và chọn tầng (Bước 6), chọn các ô ứng viên và ước lượng ban đầu (Bước 7), rồi xếp hạng lại các ô ứng viên bằng bằng chứng rút ra từ HUI để ra toạ độ cuối (Bước 8). Các hình minh hoạ của chương dùng một vân tay thật: dòng ${EX.src_row} của validationData (UJIIndoorLoc), truy vấn có sai số đúng bằng trung vị của mô hình cuối.`));
  add(f31);
  const t31 = TAB(3, "Đầu vào, đầu ra của từng bước", ["Bước", "Đầu vào", "Đầu ra"], [
    ["1. Lợi ích nội", "Vân tay RSSI (dBm)", "Giao dịch {(AP, q(i,T))}"],
    ["2. Cơ sở dữ liệu theo ô", "Giao dịch huấn luyện, nhãn điểm tham chiếu", "$D_c$ cho mỗi ô c"],
    ["3. Khai thác EFIM", "$D_c$, θ", "$HUI_c$ đầy đủ (tự nâng θ nếu vượt ngân sách)"],
    ["4. Mô hình", "$HUI_c$, vị trí huấn luyện", "{($HUI_c$, $x_c$, $y_c$, tòa–tầng$_c$)}"],
    ["5. Chấm điểm", "Giao dịch truy vấn T, mô hình", "$score_c$(T) cho mọi ô"],
    ["6. Làm mượt, chọn tầng", "$score_c$(T), vị trí các ô", "$S_c$(T), tòa–tầng f"],
    ["7. Ô ứng viên", "$S_c$(T), f", "K ô ứng viên, ước lượng ban đầu"],
    ["8. Xếp hạng lại", "Ứng viên, ba mô hình HUI, bộ hồi quy g", "Toạ độ cuối ($x̂$, $ŷ$)"],
  ], [2200, 3400, 3471], { size: 11.5 });
  add(t31);

  add(H2("3.2. Bước 1 — Lợi ích nội từ cường độ tín hiệu"));
  add(P(`Mỗi vân tay T là một giao dịch; mục là một AP được phát hiện. Lợi ích ngoài được đặt p(i) = 1 cho mọi AP, nên lợi ích chỉ phản ánh cường độ tín hiệu. Ba định nghĩa lợi ích nội được so sánh, với $n_T$ là số AP thấy được trong T và $r_T$(i) là thứ hạng cường độ của AP i (mạnh nhất có hạng 1):`));
  add(EQ(3, [sb([r("q")], [up("a​bs")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([up("RSSI"), rb(r("i,T")), r("−"), sb([up("RSSI")], [up("min")])], [sb([up("RSSI")], [up("max")]), r("−"), sb([up("RSSI")], [up("min")])]))]));
  add(EQ(3, [sb([r("q")], [up("rel")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([up("RSSI"), rb(r("i,T")), r("−"), sb([up("max")], [r("j∈T")]), up("RSSI"), rb(r("j,T")), r("+40")], [r("40")]))]));
  add(EQ(3, [sb([r("q")], [up("rank")]), rb(r("i,T")), r("="), up("round"), rb(r("1+99·"), fr([sb([r("n")], [r("T")]), r("−"), sb([r("r")], [r("T")]), rb(r("i"))], [sb([r("n")], [r("T")]), r("−1")]))]));
  add(P(`Dạng abs giữ cường độ tuyệt đối. Dạng rel không đổi khi một điện thoại đọc mọi AP lệch cùng một lượng dB. Dạng rank còn bất biến với mọi biến đổi đơn điệu của thang RSSI, nên phù hợp nhất khi tập kiểm tra dùng điện thoại lạ. Trên dev của UJIIndoorLoc, dạng rank cho ${vn(pil.phone_folds_theta20_all6_dev_mean_m.rank)} m, so với ${vn(pil.phone_folds_theta20_all6_dev_mean_m.abs)} m của abs và ${vn(pil.phone_folds_theta20_all6_dev_mean_m.rel)} m của rel, và được chọn làm mô hình chính.`));
  add(fig(3, "d02_buoc1_utility.png", `Bước 1 trên vân tay ví dụ (dòng ${EX.src_row} của validationData)`));

  add(H2("3.3. Bước 2 và 3 — Cơ sở dữ liệu giao dịch theo ô và khai thác EFIM"));
  add(P(`Một ô c là một điểm tham chiếu của tập huấn luyện; $D_c$ là tập giao dịch của các vân tay đo tại c (UJIIndoorLoc: ${U.model.n_cells} ô, trung bình ${vn(U.mining.giao_dich_tb_moi_o, 1)} giao dịch mỗi ô). Ngưỡng được đặt tương đối theo lợi ích của chính ô đó, để các ô ít mẫu không bị lấn át bởi các ô nhiều mẫu:`));
  add(EQ(3, [sb([r("minUtil")], [r("c")]), r("=θ·u"), rb(sb([r("D")], [r("c")])), r(",   "), sb([up("HUI")], [r("c")]), r("="), cb(r("X : u"), rb(r("X")), r("≥"), sb([r("minUtil")], [r("c")]))]));
  add(P(`EFIM được chạy độc lập trên từng $D_c$ với ngân sách 10 giây hoặc 10 000 HUI. Nếu vượt ngân sách, ô đó được khai thác lại với θ nhân 1,25 cho tới khi hoàn tất. Nhờ vậy tập HUI dùng cho mô hình luôn đầy đủ ở ngưỡng thực dùng; một danh sách HUI bị cắt ngang giữa chừng sẽ thiên lệch theo thứ tự duyệt và không bao giờ được dùng. Trên UJIIndoorLoc với θ = ${vn(SEL.theta_pct, 0)}%, ${U.mining.o_phai_nang_theta}/${U.model.n_cells} ô phải nâng θ (θ trung vị thực dùng ${vn(U.mining.theta_trung_vi_dung)}%), do các ô có nhiều AP mạnh cùng xuất hiện sinh ra số HUI rất lớn.`));
  add(ALGO(3, "Khai thác HUI của một ô với cơ chế tự nâng ngưỡng", [
    "Đầu vào: cơ sở dữ liệu $D_c$, ngưỡng tương đối θ, ngân sách (10 s, 10 000 HUI), hệ số nâng 1,25",
    "  1. U ← u($D_c$) = tổng lợi ích mọi giao dịch của ô",
    "  2. lặp:",
    "  3.     (H, trạng thái) ← EFIM($D_c$, θ·U, ngân sách)",
    "  4.     nếu trạng thái = HOÀN TẤT thì trả về H và θ",
    "  5.     θ ← 1,25·θ",
    "Đầu ra: $HUI_c$ đầy đủ ở ngưỡng θ thực dùng",
  ]));
  add(fig(3, "d03_buoc2_o_giao_dich.png", "Một ô là một cơ sở dữ liệu giao dịch (ô có điểm khớp cao nhất cho vân tay ví dụ)"));
  add(fig(3, "d04_buoc3_efim.png", "Khai thác HUI của một ô bằng EFIM với hai chặn trên lu và su"));

  add(H2("3.4. Bước 4 — Mô hình định vị"));
  add(P(`Mô hình định vị là tập {($HUI_c$, $x_c$, $y_c$, tòa–tầng$_c$)} của mọi ô, trong đó ($x_c$, $y_c$) là trọng tâm các vị trí huấn luyện của ô và tòa–tầng$_c$ là nhãn chiếm đa số. Với mỗi HUI X, mô hình lưu u(X) và độ hỗ trợ s(X); lợi ích trung bình mỗi mục của X trong ô và trọng số của X trong ô được suy ra trực tiếp:`));
  add(EQ(3, [sb([r("q̄")], [r("c")]), rb(r("X")), r("="), fr([r("u"), rb(r("X"))], [r("s"), rb(r("X")), r("·"), abs(r("X"))]), r(",   "), r("w"), rb(r("X")), r("="), fr([r("u"), rb(r("X"))], [sum([r("Y∈"), sb([up("HUI")], [r("c")])], [r("u"), rb(r("Y"))])])]));
  add(P(`Mô hình chính của UJIIndoorLoc gồm ${vn(U.model.n_huis, 0)} HUI; ${U.model.aps_in_some_hui}/${U.model.n_aps} AP xuất hiện trong ít nhất một HUI. Mô hình không lưu bất kỳ vân tay huấn luyện nào: mọi thông tin về một vị trí được đọc từ các HUI của ô.`));
  add(fig(3, "d05_buoc4_mo_hinh.png", "Các HUI có lợi ích lớn nhất của một ô trong mô hình"));

  add(H2("3.5. Bước 5 — Chấm điểm khớp giữa vân tay và HUI của ô"));
  add(P(`Vân tay cần định vị được chuyển thành giao dịch T theo Bước 1. Với mỗi HUI X của ô c, ba đại lượng được tính: tỷ lệ $ρ$(X,T) các mục của X có mặt trong T (khớp mềm, vì thiết bị khác có thể bỏ sót một AP), lợi ích trung bình mỗi mục của X trong T, và mức phù hợp cường độ agree(X,T) với τ là thang cường độ:`));
  add(EQ(3, [r("ρ"), rb(r("X,T")), r("="), fr([abs(r("X∩T"))], [abs(r("X"))]), r(",   "), sb([r("q̄")], [r("T")]), rb(r("X")), r("="), fr([r("1")], [abs(r("X∩T"))]), sum([r("i∈X∩T")], [r("q"), rb(r("i,T"))])]));
  add(EQ(3, [up("agree"), rb(r("X,T")), r("="), up("exp"), rb(r("−"), fr([abs(sb([r("q̄")], [r("T")]), rb(r("X")), r("−"), sb([r("q̄")], [r("c")]), rb(r("X")))], [r("τ")]))]));
  add(P(`Điểm mẫu $P_c$ đo khối lượng lợi ích HUI của ô mà vân tay chứa, đúng cường độ; độ phủ $V_c$ đo phần lợi ích của vân tay được các HUI của ô giải thích, với $I_c$ là hợp các mục của $HUI_c$:`));
  add(EQ(3, [sb([r("P")], [r("c")]), rb(r("T")), r("="), sum([r("X∈"), sb([up("HUI")], [r("c")])], [r("w"), rb(r("X")), r("·"), sp([r("ρ"), rb(r("X,T"))], [r("γ")]), r("·"), up("agree"), rb(r("X,T"))])]));
  add(EQ(3, [sb([r("V")], [r("c")]), rb(r("T")), r("="), fr([sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T"))])], [sum([r("i∈T")], [r("q"), rb(r("i,T"))])]), r(",   "), sb([up("score")], [r("c")]), rb(r("T")), r("="), sb([r("P")], [r("c")]), rb(r("T")), r("·"), sbsp([r("V")], [r("c")], [r("β")]), rb(r("T"))]));
  add(P(`$P_c$ trả lời câu hỏi “vân tay chứa bao nhiêu phần chữ ký HUI của ô, với cường độ đúng không”, còn $V_c$ trả lời “chữ ký của ô giải thích được bao nhiêu phần của vân tay”. Tích của hai đại lượng phạt cả trường hợp ô có chữ ký nhỏ khớp một phần nhỏ của vân tay lẫn trường hợp vân tay chỉ khớp phần yếu của chữ ký.`));
  add(fig(3, "d06_buoc5_cham_diem.png", "Chấm điểm vân tay ví dụ với các HUI của ô có điểm cao nhất (số liệu thật)"));

  add(H2("3.6. Bước 6 — Làm mượt không gian và chọn tầng"));
  add(P(`Các ô lân cận trên cùng tầng thường có chữ ký HUI gần nhau. Điểm của mỗi ô được cộng thêm điểm của các ô cùng tầng trong bán kính cỡ σ mét bằng nhân Gauss chuẩn hoá theo hàng, với d(c′,c) là khoảng cách thực địa giữa tâm hai ô; sau đó tầng được chọn là tầng có trung bình $k_f$ điểm lớn nhất cao nhất:`));
  add(EQ(3, [sb([r("S")], [r("c")]), rb(r("T")), r("="), sum([r("c′")], [sb([up("score")], [r("c′")]), rb(r("T")), r("·K"), rb(r("c′,c"))]), r(",   K"), rb(r("c′,c")), r("∝"), sp([r("e")], [r("−d"), sp([rb(r("c′,c"))], [r("2")]), r("/2"), sp([r("σ")], [r("2")])])]));
  add(EQ(3, [r("f"), rb(r("T")), r("="), sb([up("arg max")], [r("f")]), fr([r("1")], [sb([r("k")], [r("f")])]), sum([r("c∈"), sb([up("top")], [sb([r("k")], [r("f")])]), rb(r("f"))], [sb([r("S")], [r("c")]), rb(r("T"))])]));
  add(P(`Việc chọn tầng theo trung bình nhiều ô tốt nhất (thay vì một ô duy nhất) làm quyết định bền hơn trước nhiễu. Với UJIIndoorLoc, cấu hình được chọn trên dev là σ = ${PRM.sigma} m và $k_f$ = ${PRM.kf}.`));
  add(fig(3, "d07_buoc6_lam_muot_tang.png", "Điểm trước và sau làm mượt; điểm theo từng tòa–tầng của vân tay ví dụ"));

  add(H2("3.7. Bước 7 — Ô ứng viên và ước lượng ban đầu"));
  add(P(`K = ${V6.k_candidates} ô có điểm $S_c$ cao nhất trong tầng đã chọn được giữ làm ô ứng viên cho Bước 8. Ước lượng ban đầu là trọng tâm có trọng số của m = ${PRM.m} ô tốt nhất; số mũ p = ${PRM.p} điều chỉnh độ tập trung của trọng số:`));
  add(EQ(3, [rb(r("x̂,ŷ")), r("="), sum([r("c∈top-m"), rb(r("f"))], [sb([r("a")], [r("c")]), rb(sb([r("x")], [r("c")]), r(","), sb([r("y")], [r("c")]))]), r(",   "), sb([r("a")], [r("c")]), r("="), fr([sbsp([r("S")], [r("c")], [r("p")])], [sum([r("c′∈top-m"), rb(r("f"))], [sbsp([r("S")], [r("c′")], [r("p")])])])]));
  add(P(`Ước lượng ban đầu chính là đầu ra của phiên bản v4 (Bước 1–7). Phân tích v4 trên tập kiểm tra UJIIndoorLoc cho thấy trong 12 ô được chọn, ô gần vị trí thật nhất cách trung bình 2,40 m, trong khi ô có điểm cao nhất cách 8,82 m: tập ứng viên đúng vùng nhưng một điểm khớp duy nhất không sắp được các ô lân cận theo đúng thứ tự. Bước 8 giải quyết đúng vấn đề này.`));
  add(fig(3, "d08_buoc7_toa_do.png", "Ô ứng viên của tầng đã chọn và ước lượng ban đầu của vân tay ví dụ"));

  add(H2("3.8. Bước 8 — Xếp hạng lại ô ứng viên bằng bằng chứng HUI"));
  add(H3("3.8.1. Hai mô hình HUI phụ"));
  add(P(`Ngoài mô hình chính (lợi ích rank), hai mô hình HUI phụ được khai thác bằng chính quy trình Bước 2–4. Mô hình **mục theo mức cường độ** tách mỗi AP thành L = 3 mục theo mức của lợi ích nội (${vn(V6.n_huis_L3, 0)} HUI), để HUI ghi nhận cả AP nào mạnh, AP nào yếu:`));
  add(EQ(3, [r("i"), r(" ↦ "), rb(r("i,ℓ")), r(",   "), r("ℓ"), r("="), up("min"), rb(r("L−1, "), flo(fr([rb(r("q"), rb(r("i,T")), r("−1")), r("·L")], [r("100")])))]));
  add(P(`Mô hình **lợi ích abs** dùng cường độ tuyệt đối (${vn(V6.n_huis_abs, 0)} HUI), bổ sung thông tin mà dạng rank bỏ đi. Tổng cộng ba mô hình có ${vn(nHUI3, 0)} HUI.`));
  add(H3("3.8.2. Hồ sơ cường độ suy ra từ HUI"));
  add(P(`Từ HUI của mỗi ô có thể suy ra một hồ sơ cường độ: khối lượng HUI đặt trên AP i và cường độ ước lượng của AP i tại ô, với w(X) và $q̄_c$(X) như ở (3.5):`));
  add(EQ(3, [sb([r("m")], [r("c")]), rb(r("i")), r("∝"), sum([r("X∈"), sb([up("HUI")], [r("c")]), r(", i∈X")], [fr([r("w"), rb(r("X"))], [abs(r("X"))])]), r(",   "), sb([r("q̂")], [r("c")]), rb(r("i")), r("="), fr([sum([r("X∋i")], [r("w"), rb(r("X")), sb([r("q̄")], [r("c")]), rb(r("X"))])], [sum([r("X∋i")], [r("w"), rb(r("X"))])])]));
  add(EQ(3, [sb([r("R")], [r("c")]), rb(r("T")), r("="), sum([r("i∈T")], [sb([r("m")], [r("c")]), rb(r("i"))]), r(",   "), sb([up("MAE")], [r("c")]), rb(r("T")), r("="), fr([sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T")), abs(r("q"), rb(r("i,T")), r("−"), sb([r("q̂")], [r("c")]), rb(r("i")))])], [sum([r("i∈T∩"), sb([r("I")], [r("c")])], [r("q"), rb(r("i,T"))])])]));
  add(P(`$R_c$ là độ phủ ngược (phần khối lượng HUI của ô có mặt trong vân tay); MAE$_c$ đo độ lệch giữa cường độ của vân tay và hồ sơ cường độ của ô. Hai ô lân cận có cùng tập AP nhưng khác mức cường độ sẽ có hồ sơ khác nhau, nên các đại lượng này phân biệt được ô mà điểm $P_c$ không phân biệt được.`));
  add(H3("3.8.3. Véc-tơ bằng chứng"));
  add(P(`Mỗi cặp (vân tay T, ô ứng viên c) được mô tả bằng véc-tơ φ(T, c) gồm ${V6.n_features} đặc trưng, chia thành năm nhóm (${"Bảng 3.2"}). Mỗi đặc trưng được dùng thêm ở dạng so với các ứng viên khác của cùng truy vấn (hiệu với giá trị lớn nhất, chuẩn hoá min–max và thứ hạng), vì điều cần học là ô nào tốt hơn các ô còn lại của cùng truy vấn.`));
  const t32 = TAB(3, "Các nhóm đặc trưng của véc-tơ bằng chứng φ(T, c) (mọi đặc trưng đều tính từ HUI)", ["Nhóm", "Đặc trưng", "Số lượng"], [
    ["Điểm khớp HUI, mô hình rank", "$S_c$, log $S_c$, $S_c$/max S, thứ hạng, $P_c$ (γ = 2 và γ = 1), $V_c$, $R_c$, $P_c$ với trọng số IDF của HUI giữa các ô lân cận, điểm trước làm mượt", "10"],
    ["Đồng thuận không gian, ngữ cảnh", "khoảng cách tới ước lượng ban đầu, tới ô xếp đầu, số ứng viên trong bán kính 5 m, số AP của vân tay", "4"],
    ["Mô hình mục theo mức cường độ", "$P_c$, $V_c$, điểm sau làm mượt, thứ hạng, MAE và cosin hồ sơ cường độ", "6"],
    ["Hồ sơ cường độ (rank)", "MAE$_c$, hệ số tương quan, cosin, khối lượng HUI trên AP mạnh nhất, số AP chung", "5"],
    ["Mô hình lợi ích abs", "$P_c$, $V_c$, $R_c$, điểm sau làm mượt, thứ hạng, MAE, tương quan, cosin", "8"],
  ], [2500, 5571, 1000], { align: [L, L, C], size: 11 });
  add(t32);
  add(H3("3.8.4. Bộ hồi quy và toạ độ cuối"));
  add(P(`Một bộ hồi quy Gradient Boosting [13], [14] học hàm g dự đoán log(1 + khoảng cách) từ tâm ô ứng viên tới vị trí thật. Dữ liệu huấn luyện chỉ lấy từ các fold dev: với mỗi fold, đặc trưng của các truy vấn dev được tính từ ba mô hình HUI khai thác trên phần còn lại của tập huấn luyện, nên bộ hồi quy chỉ học từ dữ liệu ngoài fold. Toạ độ cuối là trọng tâm của m = ${V6.m} ô có khoảng cách dự đoán nhỏ nhất, với λ = ${vn(V6.lam, 0)} m:`));
  add(EQ(3, [sb([r("d̂")], [r("c")]), r("="), up("exp"), rb(r("g"), rb(r("φ"), rb(r("T,c")))), r("−1"), r(",   "), sb([r("a")], [r("c")]), r("∝"), up("exp"), rb(r("−"), fr([sb([r("d̂")], [r("c")]), r("−"), sb([r("d̂")], [up("min")])], [r("λ")])), r(",   "), rb(r("x̂,ŷ")), r("="), sum([r("c")], [sb([r("a")], [r("c")]), rb(sb([r("x")], [r("c")]), r(","), sb([r("y")], [r("c")]))])]));
  add(BOX("Nhận xét 3.1 (Vai trò của HUIM và của bộ hồi quy)", [
    `Bộ hồi quy không nhìn thấy vân tay huấn luyện nào; nó chỉ học cách cân các bằng chứng do HUI tạo ra. Các ô được xét vẫn là các ô có điểm HUI cao nhất, và toạ độ vẫn là tổ hợp lồi của tâm các ô đó. Nếu bỏ HUIM, không còn ô ứng viên lẫn đặc trưng nào để xếp hạng. Ngược lại, phần cân các bằng chứng là do học máy đảm nhận; phiên bản không dùng bộ hồi quy (Bước 1–7) đạt ${vn(U4.mean_err_m)} m trên UJIIndoorLoc.`]));
  add(GAP());
  add(fig(3, "d09_buoc8_xep_hang_lai.png", "Bước 8: bằng chứng HUI, bộ hồi quy và toạ độ cuối của vân tay ví dụ"));

  add(H2("3.9. Thuật toán tổng hợp và độ phức tạp"));
  add(ALGO(3, "Định vị bằng so khớp High Utility Itemset", [
    "Đầu vào: tập huấn luyện {(T, toạ độ, tòa–tầng)}; vân tay truy vấn T*; tham số θ, γ, τ, β, σ, $k_f$, m, p, K, λ",
    "Huấn luyện:",
    "  1. Với mỗi vân tay huấn luyện T: tính q(i,T) theo (3.1)–(3.3)",
    "  2. Với mỗi ô c: $D_c$ ← giao dịch đo tại c; $minUtil_c$ ← θ·u($D_c$)",
    "  3.   $HUI_c$ ← EFIM($D_c$, $minUtil_c$) với tự nâng ngưỡng (Thuật toán 3.1)",
    "  4. Mô hình ← {($HUI_c$, $x_c$, $y_c$, tòa–tầng$_c$)}; lặp lại 1–4 cho mô hình mức cường độ và mô hình abs",
    "  4b. Trên 6 fold dev: tính φ(T, c) cho các ô ứng viên của mỗi truy vấn dev; học g bằng Gradient Boosting",
    "Định vị T*:",
    "  5. Với mỗi ô c: $P_c$(T*), $V_c$(T*), $score_c$(T*) theo (3.6)–(3.9)",
    "  6. S ← làm mượt theo (3.10); f ← tầng theo (3.11)",
    "  7. K ô ứng viên ← K ô có S cao nhất của tầng f; ước lượng ban đầu theo (3.12)",
    "  8. Với mỗi ứng viên: φ(T*, c) theo (3.13)–(3.15), $d̂_c$ ← g(φ); (x̂, ŷ) theo (3.16)",
    "Đầu ra: (x̂, ŷ), tòa–tầng f",
  ]));
  const t33 = TAB(3, "Độ phức tạp của pha định vị (H: số HUI, A: số AP, C: số ô, K: số ô ứng viên)", ["Bước", "Phép tính chính", "Độ phức tạp"], [
    ["5", "Giao của từng HUI với vân tay; tổng theo ô", "O(H) mỗi mô hình"],
    ["6", "Nhân điểm với ma trận nhân Gauss; trung bình theo tầng", "O(C²)"],
    ["7", "Chọn K ô lớn nhất", "O(C log C)"],
    ["8", "Hồ sơ cường độ và dự đoán của bộ hồi quy", "O(K·A + K·số cây)"],
  ], [900, 5571, 2600], { align: [C, L, L] });
  add(P(`${t33.label} cho thấy chi phí định vị không phụ thuộc số vân tay huấn luyện, chỉ phụ thuộc số HUI và số ô. Trên UJIIndoorLoc, thời gian đo được là ${vn(UT.ms_moi_fp)} ms mỗi vân tay với cài đặt Python (${vn(U4.ms_per_fp)} ms khi chỉ dùng mô hình chính).`));
  add(t33);

  add(H2("3.10. Ví dụ tính toán trên một vân tay"));
  const top = EX.cells.slice(0, 10).map((c, i) => {
    const dd = Math.hypot(c.x - EX.true_x, c.y - EX.true_y) * GF;
    return [String(i + 1), String(c.index), vn(c.weight, 4), vn(dd, 2)];
  });
  const t34 = TAB(3, `Mười ô đầu tiên sau Bước 8 của vân tay ví dụ (dòng ${EX.src_row} của validationData)`,
    ["Thứ tự", "Chỉ số ô", "Trọng số $a_c$", "Khoảng cách tới vị trí thật (m)"], top, [1300, 1600, 2300, 3871], { align: [C, RT, RT, RT] });
  add(P(`Vân tay ví dụ được dự đoán đúng tòa–tầng ${EX.pred_building_floor.replace("_", "–")}. Ước lượng ban đầu của Bước 7 có sai số ${vn(EX.v4_err_m)} m; sau Bước 8, toạ độ cuối là tổng có trọng số của ${V6.m} ô với trọng số trong ${t34.label} và có sai số **${vn(EX.err_m)} m**. Sổ Excel kèm theo (sheet Vi_du_UJI_mot_truy_van) tính lại toạ độ này bằng hàm SUMPRODUCT.`));
  add(t34);
  add(H2("3.11. Kết luận chương 3"));
  add(P(`Chương 3 đã trình bày mô hình định vị đề xuất gồm tám bước. Bước 1–4 biến dữ liệu khảo sát thành ba mô hình HUI; Bước 5–7 dùng điểm khớp HUI để chọn tòa nhà, tầng và các ô ứng viên; Bước 8 xếp hạng lại các ô ứng viên bằng bằng chứng rút ra từ HUI. Chương 4 đánh giá mô hình trên sáu bộ dữ liệu.`));

  // ================================================================ CHƯƠNG 4
  add(H1("CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ"));
  add(H2("4.1. Môi trường thực nghiệm"));
  const t41 = TAB(4, "Môi trường thực nghiệm", ["Thành phần", "Cấu hình"], [
    ["Bộ xử lý", "4 lõi x86_64"], ["Bộ nhớ", "15,7 GB RAM"], ["Hệ điều hành", "Linux 64 bit"],
    ["Ngôn ngữ", "Python 3.13 (CPython)"],
    ["Thư viện", "numpy 2.5, scipy 1.18, pandas 3.0, scikit-learn 1.9, matplotlib 3.11"],
    ["Thuật toán HUIM", "EFIM cài đặt trong mã nguồn (ma_nguon/src/huim/efim.py), kiểm thử với thuật toán vét cạn"],
    ["Báo cáo", "docx (Node.js), LibreOffice để dựng mục lục; mọi số liệu đọc tự động từ kết quả"],
  ], [2400, 6671], { size: 11.5 });
  add(t41);
  add(H2("4.2. Dữ liệu thực nghiệm"));
  const t42 = TAB(4, "Mô tả các bộ dữ liệu sử dụng", ["Bộ dữ liệu", "Số AP", "Tòa–tầng", "Mẫu huấn luyện", "Điểm tham chiếu", "AP / vân tay", "Tập kiểm tra (số mẫu)"],
    order.map((k) => { const x = D.datasets[k].description; return [x.ten, x.so_ap, x.so_lop_toa_tang, vn(x.mau_huan_luyen, 0), vn(x.diem_tham_chieu, 0), vn(x.ap_tb_moi_fp, 1), x.tap_test]; }),
    [1700, 700, 900, 1250, 1200, 1000, 2321], { align: [L, RT, RT, RT, RT, RT, L], size: 10.5 });
  const fB13 = fig(4, "b13_mo_ta_du_lieu.png", "Quy mô của sáu bộ dữ liệu");
  const fB14 = fig(4, "b14_dien_thoai.png", "UJIIndoorLoc: điện thoại trong tập huấn luyện và tập kiểm tra; sai số của mô hình cuối theo điện thoại");
  const fB16 = fig(4, "b16_so_ap_moi_van_tay.png", "UJIIndoorLoc: phân bố số AP được phát hiện trong một vân tay", 520);
  add(P(`${t42.label} và ${fB13.label} mô tả sáu bộ dữ liệu. UJIIndoorLoc [3] là bộ lớn và khó nhất: ba toà nhà, 13 tòa–tầng, 520 AP, ${vn(D.datasets.uji.description.mau_huan_luyen, 0)} vân tay huấn luyện từ 16 điện thoại của 18 người dùng. Toạ độ của UJIIndoorLoc dùng phép chiếu Web Mercator (EPSG:3857), nên khoảng cách được đổi ra mét thực địa bằng hệ số 0,766126. Các bộ còn lại dùng lưới toạ độ tính bằng mét. HUS chứa nhiều mẫu kiểm tra trùng hệt mẫu huấn luyện; bộ “HUS (khử trùng lặp)” loại các bản trùng này và là con số khách quan hơn.`));
  add(t42);
  add(fB13);
  const seen = phones.filter((x) => x.co_trong_huan_luyen === "True" || x.co_trong_huan_luyen === true).length;
  add(P(`Một đặc điểm quan trọng của UJIIndoorLoc là tập kiểm tra (validationData) được thu bằng các điện thoại khác: chỉ ${seen} trong ${phones.length} điện thoại của tập kiểm tra có mặt trong tập huấn luyện (${fB14.label}). Vân tay kiểm tra cũng thấy ít AP hơn (${fB16.label}). Đây là tình huống thực tế — người dùng mang thiết bị bất kỳ — và là lý do giao thức đánh giá giữ lại theo điện thoại (mục 4.3).`));
  add(fB14, fB16);

  add(H2("4.3. Giao thức đánh giá"));
  add(P(`Tập kiểm tra chỉ được dùng một lần cho mỗi phiên bản mô hình; mọi lựa chọn (dạng lợi ích nội, θ, γ, τ, β, σ, $k_f$, m, p, và mọi lựa chọn của Bước 8) được thực hiện trên 6 fold kiểm định tách từ tập huấn luyện. Với UJIIndoorLoc, 9 trong 11 điện thoại của validationData không có trong trainingData, nên các fold được giữ lại theo điện thoại (GroupKFold trên PHONEID) để mô phỏng đúng tình huống gặp thiết bị lạ. Sau khi chọn, EFIM được chạy lại trên toàn bộ tập huấn luyện, bộ hồi quy của Bước 8 được học trên đặc trưng ngoài fold của cả 6 fold, và mô hình cuối được chấm một lần trên tập kiểm tra. Sai số tính theo (2.10).`));
  add(fig(4, "d10_giao_thuc.png", "Giao thức đánh giá và kiểm chứng"));

  add(H2("4.4. Lựa chọn tham số trên tập kiểm định"));
  const t43 = TAB(4, "Cấu hình Bước 1–7 được chọn trên các fold dev của từng bộ dữ liệu", ["Bộ dữ liệu", "Lợi ích", "θ (%)", "γ", "τ", "β", "σ (m)", "$k_f$", "m", "p", "Dev (m)"],
    order.map((k) => { const s = D.datasets[k].selection, p = s.params;
      return [T[k], s.utility || "abs", vn(s.theta_pct, 0), p.gamma, p.tau, p.beta, p.sigma, p.kf, p.m, p.p, vn(s.dev_mean_m)]; }),
    [1900, 800, 700, 500, 600, 500, 700, 600, 500, 500, 871], { align: [L, C, RT, RT, RT, RT, RT, RT, RT, RT, RT], size: 10.5 });
  const fB11 = fig(4, "b11_luoi_tham_so_dev.png", "UJIIndoorLoc, Bước 1–7: sai số dev theo σ và m (mỗi điểm là cấu hình tốt nhất của các tham số còn lại)", 540);
  add(P(`${t43.label} liệt kê cấu hình được chọn. Với UJIIndoorLoc, ${vn(SEL.n_configurations, 0)} cấu hình được so trên dev. θ được cố định ở ${vn(SEL.theta_pct, 0)}% bằng thí nghiệm trên dev (θ = 10% sinh khoảng 4 triệu HUI mỗi fold); dạng rank được chọn vì cho sai số dev thấp nhất. ${fB11.label} cho thấy làm mượt với σ = 3 m có lợi, trong khi σ = 10 m làm mờ chữ ký các ô và tăng sai số.`));
  add(t43);
  add(fB11);
  add(P(`Với Bước 8, các tham số của bộ hồi quy (300 cây, tốc độ học 0,06, tối đa 31 lá, tối thiểu 40 mẫu mỗi lá) và của bước định vị cuối (K = ${V6.k_candidates}, m = ${V6.m}, λ = ${vn(V6.lam, 0)}) được chọn trên sai số dev ngoài fold.`));

  add(H2("4.5. Kết quả trên tập kiểm tra"));
  const t44 = TAB(4, "Kết quả của mô hình đề xuất trên tập kiểm tra", ["Bộ dữ liệu", "Tập kiểm tra", "Số mẫu", "TB (m)", "Trung vị (m)", "p75 (m)", "p90 (m)", "Đúng tòa–tầng", "< 7 m"],
    allTests.map(({ k, t, v }) => [T[k], t, vn(v.so_mau, 0), vn(v.sai_so_tb_m), vn(v.trung_vi_m), vn(v.p75_m), vn(v.p90_m), pct(v.dung_toa_tang), v.duoi_7m ? "đạt" : "không"]),
    [1700, 1500, 750, 750, 900, 800, 800, 1071, 800], { align: [L, L, RT, RT, RT, RT, RT, RT, C], size: 10.5 });
  const fB01 = fig(4, "b01_ket_qua_tap_test.png", "Sai số trung bình (cột) và trung vị (phần gạch chéo) trên tập kiểm tra của mọi bộ dữ liệu");
  add(P(`${t44.label} và ${fB01.label} trình bày kết quả. **${nOk}/${allTests.length} tập kiểm tra đạt sai số trung bình dưới 7 m.** Trên UJIIndoorLoc, sai số trung bình là ${vn(UT.sai_so_tb_m)} m, trung vị ${vn(UT.trung_vi_m)} m, đúng tòa nhà ${pct(UT.dung_toa)} và đúng tòa–tầng ${pct(UT.dung_toa_tang)}; so với ước lượng ban đầu của Bước 7 (${vn(U4.mean_err_m)} m, trung vị ${vn(U4.median_err_m)} m), Bước 8 giảm sai số trung bình ${vn(U4.mean_err_m - UT.sai_so_tb_m)} m. Trên năm bộ dữ liệu còn lại, Bước 1–7 đã đạt sai số ${vn(mn)}–${vn(mx)} m nên không cần Bước 8.`));
  add(t44);
  add(fB01);
  add(fig(4, "b02_cdf_uji.png", "UJIIndoorLoc: hàm phân bố tích luỹ của sai số; hai đường k-NN chỉ để tham chiếu", 560));
  add(fig(4, "b03_cdf_cac_bo_khac.png", "Hàm phân bố tích luỹ của sai số trên các bộ dữ liệu bổ sung"));

  add(H2("4.6. Phân tích kết quả trên UJIIndoorLoc"));
  add(H3("4.6.1. Sai số theo tầng và nhầm lẫn tầng"));
  const t45 = TAB(4, "Tách sai số theo việc xác định đúng hay sai tầng (UJIIndoorLoc, mô hình cuối)", ["Nhóm mẫu", "Số mẫu", "Sai số TB (m)", "Phần trong tổng sai số"],
    fs4.map((x) => [x.nhom, vn(x.so_mau, 0), vn(x.sai_so_tb_m), pct(x.phan_tong_sai_so)]), [3600, 1400, 1800, 2271], { align: [L, RT, RT, RT] });
  add(P(`${t45.label} cho thấy phần lớn sai số nằm ở các mẫu đã xác định đúng tầng (${pct(fs4[0].phan_tong_sai_so)} tổng sai số, sai số trung bình ${vn(fs4[0].sai_so_tb_m)} m, so với 7,78 m ở v4). Bước 8 giảm chủ yếu sai số trong tầng, nhưng đây vẫn là điểm nghẽn: mỗi ô của UJIIndoorLoc chỉ có khoảng ${vn(U.mining.giao_dich_tb_moi_o, 0)} vân tay của một đến bốn người dùng, và gần như không vị trí kiểm tra nào trùng điểm tham chiếu, nên toạ độ phải được nội suy giữa các ô.`));
  add(t45);
  const worst = [...floors].sort((a, b) => b.cuoi_m - a.cuoi_m)[0], best = [...floors].sort((a, b) => a.cuoi_m - b.cuoi_m)[0];
  const fB04 = fig(4, "b04_sai_so_theo_toa_tang.png", "UJIIndoorLoc: sai số trung bình theo tòa nhà – tầng, trước và sau Bước 8");
  const fB05 = fig(4, "b05_ma_tran_nham_lan_tang.png", "UJIIndoorLoc: ma trận nhầm lẫn tòa–tầng của mô hình cuối", 500);
  add(P(`${fB04.label} và ${fB05.label} chi tiết hoá theo tòa–tầng. Sai số thấp nhất ở ${best.toa_tang.replace("_", "–")} (tòa–tầng, ${vn(best.cuoi_m)} m) và cao nhất ở ${worst.toa_tang.replace("_", "–")} (${vn(worst.cuoi_m)} m, ${worst.so_mau} mẫu). Bước 8 cải thiện ở hầu hết tòa–tầng. Ma trận nhầm lẫn cho thấy các lỗi tầng hầu như chỉ xảy ra giữa hai tầng liền kề của cùng toà nhà, đúng với hiện tượng tín hiệu chồng lấn giữa các tầng; lỗi nhầm toà nhà gần như không có (đúng tòa nhà ${pct(UT.dung_toa)}).`));
  add(fB04, fB05);
  add(H3("4.6.2. Phân bố không gian và theo thiết bị"));
  const phSorted = [...phones].sort((a, b) => b.sai_so_tb_m - a.sai_so_tb_m);
  const fB06 = fig(4, "b06_ban_do_sai_so.png", "UJIIndoorLoc: phân bố không gian của sai số trên tập kiểm tra (mô hình cuối)");
  add(P(`${fB06.label} vẽ vị trí các vân tay kiểm tra, tô màu theo sai số. Sai số lớn tập trung ở các đầu hành lang và các vùng thưa điểm tham chiếu, nơi tâm các ô gần nhất cũng đã cách xa vị trí thật. Theo thiết bị (${fB14.label}), điện thoại có sai số lớn nhất là PHONEID ${phSorted[0].PHONEID} (${vn(phSorted[0].sai_so_tb_m)} m, ${phSorted[0].so_mau} mẫu) và thấp nhất là PHONEID ${phSorted[phSorted.length - 1].PHONEID} (${vn(phSorted[phSorted.length - 1].sai_so_tb_m)} m); chênh lệch giữa các thiết bị lớn hơn chênh lệch giữa các toà nhà, xác nhận thiết bị thu là một nguồn sai số chính.`));
  add(fB06);
  add(H3("4.6.3. Tác động của Bước 8 trên từng vân tay"));
  const fB07 = fig(4, "b07_cai_thien_tung_van_tay.png", "Thay đổi sai số của từng vân tay từ ước lượng ban đầu (v4) tới mô hình cuối");
  add(P(`${fB07.label} so sánh sai số của từng vân tay trước và sau Bước 8. Phần lớn vân tay được cải thiện (điểm nằm dưới đường chéo); các vân tay có sai số rất lớn ở v4 — thường do chọn sai cụm ô — được kéo về gần hơn. Một phần nhỏ vân tay bị xấu đi, chủ yếu khi các ô ứng viên tốt nhất đều nằm cùng một phía của vị trí thật.`));
  add(fB07);

  add(H2("4.7. Phân tích Bước 8"));
  add(H3("4.7.1. Các biến thể đã thử"));
  const t46 = TAB(4, "Các biến thể của Bước 8 thử trên dev UJIIndoorLoc (sai số trung bình ngoài fold, 19 937 truy vấn)", ["Biến thể", "Dev TB (m)", "Kết luận"], [
    ["Bước 1–7, một điểm khớp HUI (v4)", vn(RSH["v4 (baseline)"]), "mốc so sánh"],
    ["Trọng số IDF của HUI giữa các ô lân cận", vn(RSH["IDF weight of HUIs (best)"]), "gần như không đổi"],
    ["Chỉ dùng mô hình mục theo mức cường độ (fold 0)", `${vn(RSH["level items (AP, strength level) alone, fold 0"].L3)} so với ${vn(RSH["level items (AP, strength level) alone, fold 0"].v4)}`, "kém hơn khi dùng riêng"],
    ["Xếp hạng lại bằng các điểm HUI", vn(RSH["re-rank, HUI scores"]), "cải thiện"],
    ["+ hồ sơ cường độ suy ra từ HUI", vn(RSH["re-rank + HUI strength profile"]), "cải thiện"],
    ["Ứng viên trên cả toà nhà (không theo tầng)", vn(RSH["re-rank, candidates over the whole building"]), "không dùng"],
    ["+ đặc trưng so với các ứng viên khác (v5)", vn(RSH["re-rank + features relative to the query's candidates (v5)"]), "cải thiện"],
    ["v5 học khi bỏ ô của chính truy vấn", vn(RSH["v5 trained leave-own-cell-out"]), "không dùng"],
    ["v5 + mô hình HUI lợi ích abs (v6)", vn(RSH["v5 + abs HUI model (v6)"]), "chọn"],
  ], [5200, 1700, 2171], { align: [L, RT, L], size: 11 });
  const fB09 = fig(4, "b09_bien_the_buoc8.png", "Bước 8: sai số dev của các biến thể (xám: không dùng)", 560);
  add(P(`${t46.label} và ${fB09.label} ghi lại các biến thể đã thử; mọi con số là sai số dev ngoài fold và tập kiểm tra không được đọc. Trọng số IDF và mô hình mục theo mức cường độ dùng riêng không cải thiện; chúng chỉ có ích khi là bằng chứng bổ sung cho bộ hồi quy. Quyết định tầng bằng một bộ phân loại học trên dev nâng độ chính xác tầng trên dev từ ${pct(V6.research["learned floor decision dev floor accuracy"].baseline)} lên ${pct(V6.research["learned floor decision dev floor accuracy"].learned)} nhưng không giảm sai số vị trí, nên không được dùng.`));
  add(t46);
  add(fB09);
  if (IMP) {
    const imp = Object.entries(IMP.increase_m).sort((a, b) => b[1] - a[1]);
    add(H3("4.7.2. Mức đóng góp của từng nhóm bằng chứng"));
    const fB10 = fig(4, "b10_dong_gop_bang_chung.png", "Bước 8: sai số dev tăng thêm khi xáo trộn từng nhóm bằng chứng HUI", 560);
    add(P(`Để biết nhóm bằng chứng nào quan trọng, mỗi nhóm đặc trưng của ${"Bảng 3.2"} lần lượt được xáo trộn giữa các truy vấn của fold dev đang giữ lại (bộ hồi quy học trên năm fold còn lại), và mức tăng sai số dev được ghi nhận (${fB10.label}). Xáo trộn nhóm **${imp[0][0].toLowerCase()}** làm sai số tăng nhiều nhất (+${vn(imp[0][1])} m); mọi nhóm đều làm sai số tăng khi bị xáo trộn, tức mỗi nhóm bằng chứng HUI đều mang thông tin riêng.`));
    add(fB10);
  }
  add(H3(IMP ? "4.7.3. Lịch sử phiên bản" : "4.7.2. Lịch sử phiên bản"));
  const ver = D.versions;
  const t47 = TAB(4, "Các phiên bản đã thử trên UJIIndoorLoc (mỗi phiên bản chọn trên dev rồi chấm tập kiểm tra một lần)", ["Phiên bản", "Thay đổi", "Fold dev", "Dev TB (m)", "Kiểm tra TB (m)", "Đúng tầng"],
    ver.map((v) => [v.version.replace(" (final)", " (cuối)"), v.change_vi, v.dev_folds === "leave-phones-out" ? "theo điện thoại" : "theo người dùng", vn(v.dev_mean_m), vn(v.test_mean_m), pct(v.test_floor_accuracy)]),
    [900, 3700, 1300, 1000, 1171, 1000], { align: [L, L, L, RT, RT, RT], size: 10.5 });
  const fB08 = fig(4, "b08_lich_su_phien_ban.png", "UJIIndoorLoc: sai số dev và sai số kiểm tra qua các phiên bản", 560);
  add(P(`${t47.label} và ${fB08.label} ghi lại mọi phiên bản. Trong các phiên bản Bước 1–7, v1 có sai số kiểm tra thấp nhất nhưng sai số dev kém nhất; giao thức chọn v4, vì chọn theo con số kiểm tra là chọn mô hình trên tập kiểm tra. Sự chênh giữa dev và kiểm tra ở v2 là lý do chuyển sang fold giữ lại theo điện thoại. v5 và v6 thêm Bước 8; v6 có sai số dev thấp nhất (${vn(V6.dev_mean_m)} m) nên là mô hình cuối, và sai số kiểm tra của nó (${vn(UT.sai_so_tb_m)} m) được tính đúng một lần sau khi đã chọn. Hai thí nghiệm phụ khác cho kết quả âm: đặt lợi ích ngoài p(i) theo IDF hoặc theo thông tin tương hỗ không cải thiện, và khai thác HUI trên cửa sổ chồng lấn gồm các ô lân cận làm sai số dev tăng từ ${vn(win.best_dev_mean_m["cells only (window 0)"])} m lên ${vn(win.best_dev_mean_m["window 4 m"])} m (bán kính 4 m) và ${vn(win.best_dev_mean_m["window 8 m"])} m (8 m).`));
  add(t47);
  add(fB08);

  add(H2("4.8. Thống kê khai thác và chi phí tính toán"));
  const t48 = TAB(4, "Thống kê khai thác HUI của mô hình chính trên toàn bộ tập huấn luyện", ["Bộ dữ liệu", "Số ô", "Giao dịch / ô", "Số HUI", "θ trung vị thực dùng (%)", "Ô phải nâng θ", "AP trong HUI", "Thời gian (s)"],
    order.map((k) => { const m = D.datasets[k].mining; return [m.ten, vn(m.so_o, 0), vn(m.giao_dich_tb_moi_o, 1), vn(m.so_hui, 0), vn(m.theta_trung_vi_dung, 1), vn(m.o_phai_nang_theta, 0), `${m.ap_trong_hui}/${m.tong_ap}`, vn(m.thoi_gian_khai_thac_s, 0)]; }),
    [1700, 800, 1000, 1300, 1200, 1000, 1071, 1000], { align: [L, RT, RT, RT, RT, RT, RT, RT], size: 10.5 });
  const fB12 = fig(4, "b12_thong_ke_khai_thac.png", "Số HUI trên mỗi ô và ngưỡng θ thực dùng của sáu bộ dữ liệu");
  add(P(`${t48.label} và ${fB12.label} thống kê quá trình khai thác. Số HUI mỗi ô biến thiên nhiều bậc độ lớn: ô có nhiều AP mạnh cùng xuất hiện sinh ra hàng nghìn HUI và phải nâng ngưỡng. Cơ chế tự nâng ngưỡng bảo đảm mọi ô đều có tập HUI đầy đủ trong ngân sách thời gian. Với UJIIndoorLoc, ba mô hình HUI của mô hình cuối có tổng cộng ${vn(nHUI3, 0)} HUI.`));
  add(t48);
  add(fB12);
  const t49 = TAB(4, "Thời gian định vị trung bình mỗi vân tay", ["Bộ dữ liệu", "Tập kiểm tra", "ms / vân tay"],
    allTests.map(({ k, t, v }) => [T[k], t, vn(v.ms_moi_fp, 2)]), [3000, 3000, 3071], { align: [L, L, RT] });
  add(P(`${t49.label} cho thấy thời gian định vị. Chi phí lớn nhất thuộc về UJIIndoorLoc vì số HUI lớn và Bước 8 dùng ba mô hình; một cài đặt bằng ngôn ngữ biên dịch hoặc khai thác HUI đóng, HUI cực đại để giảm dư thừa có thể giảm đáng kể thời gian này.`));
  add(t49);

  add(H2("4.9. So sánh với các hệ thống tham chiếu"));
  const t410 = TAB(4, "Sai số trung bình (m) của hệ thống đề xuất và các hệ thống tham chiếu dùng k-NN", ["Bộ dữ liệu", "Tập kiểm tra", "Đề xuất (chỉ HUIM)", "k-NN gốc", "k-NN tối ưu", "HUIM chọn AP + k-NN"],
    D.references.map((x) => [x.ten, x.tap_test, vn(x.chi_huim_m), x.knn_goc_m != null ? vn(x.knn_goc_m) : "–", x.knn_toi_uu_m != null ? vn(x.knn_toi_uu_m) : "–", x.huim_chon_ap_knn_m != null ? `${vn(x.huim_chon_ap_knn_m)} (${x.huim_chon_ap_so_ap}/${x.tong_ap} AP)` : "–"]),
    [1700, 1500, 1300, 1000, 1100, 2471], { align: [L, L, RT, RT, RT, RT], size: 10.5 });
  const fB15 = fig(4, "b15_so_sanh_tham_chieu.png", "So sánh với các hệ thống tham chiếu dùng k-NN");
  add(P(`${t410.label} và ${fB15.label} đặt kết quả cạnh các hệ thống dùng k-NN của các giai đoạn trước, chỉ để tham chiếu. Trên UJIIndoorLoc, hệ thống đề xuất tốt hơn k-NN gốc (k = 1) nhưng kém k-NN đã tối ưu; trên các bộ dữ liệu một tầng, k-NN cho sai số thấp hơn vì vị trí kiểm tra trùng hoặc rất gần điểm tham chiếu. Ưu điểm của thiết kế đề xuất không nằm ở sai số tuyệt đối mà ở chỗ toàn bộ quyết định định vị đến từ các mẫu HUI và mô hình không chứa vân tay huấn luyện.`));
  add(t410);
  add(fB15);

  add(H2("4.10. Kiểm chứng độc lập"));
  const t411 = TAB(4, "Kết quả kiểm chứng độc lập", ["Phạm vi", "Số phép kiểm", "Thất bại"],
    [...D.verification.per_dataset.map((x) => [`${T[x.dataset]}, Bước 1–7`, x.n_checks, x.n_failed]),
     ["UJIIndoorLoc, mô hình cuối (Bước 8)", V6.verification.n_checks, V6.verification.n_failed]], [5000, 2000, 2071], { align: [L, RT, RT] });
  add(P(`Chương trình kiểm chứng không gọi EFIM hay bộ định vị. Từ dữ liệu gốc và các tệp kết quả, nó tính lại ngưỡng của mọi ô, lợi ích và độ hỗ trợ của các HUI bằng cách quét lại dữ liệu, kiểm tra mọi tập 1–2 AP vượt ngưỡng đều có trong mô hình, tính lại điểm khớp, các ô được chọn và toạ độ của các truy vấn ngẫu nhiên bằng vòng lặp thuần, và đếm lại sai số, độ chính xác. Với mô hình cuối của UJIIndoorLoc, ${V6.verification.n_checks} phép kiểm riêng xác nhận: sai số tính lại từ toạ độ khớp với báo cáo; mỗi toạ độ dự đoán đúng bằng tổng có trọng số của tâm các ô được chọn, trọng số dương và có tổng bằng 1; mọi ô được chọn nằm trên tầng dự đoán; ước lượng ban đầu bên trong mô hình cuối trùng khít với dự đoán của v4; và các dòng kiểm tra đúng là 1 111 dòng của validationData (${t411.label}). Ngoài ra, sổ Excel so_lieu/kiem_chung_mean.xlsx tính lại sai số trung bình của mọi tập kiểm tra bằng công thức (2.10) và khớp với kết quả báo cáo tới 10⁻⁴ m.`));
  add(t411);

  add(H2("4.11. Thảo luận"));
  add(P(`Kết quả cho thấy HUIM có thể đảm nhận toàn bộ việc định vị: trên năm bộ dữ liệu ngoài UJIIndoorLoc, sai số trung bình nằm trong khoảng ${vn(mn)}–${vn(mx)} m chỉ với Bước 1–7, và trên UJIIndoorLoc đạt ${vn(UT.sai_so_tb_m)} m khi thêm Bước 8. Mức giảm trên tập kiểm tra (${vn(U4.mean_err_m - UT.sai_so_tb_m)} m) không nhỏ hơn mức giảm trên dev (${vn(V6.dev_mean_v4_m - V6.dev_mean_m)} m), nên không có dấu hiệu Bước 8 quá khớp với các fold dev.`));
  add(P(`Cần nêu rõ ba giới hạn. **Thứ nhất**, kết quả UJIIndoorLoc chỉ thấp hơn mức 7 m ${vn(7 - UT.sai_so_tb_m)} m; với ${vn(UT.so_mau, 0)} mẫu, sai số chuẩn của giá trị trung bình là ${vn(UT.sai_so_chuan_tb_m)} m, nên khoảng tin cậy 95% xấp xỉ ${vn(UT.sai_so_tb_m - 1.96 * UT.sai_so_chuan_tb_m)}–${vn(UT.sai_so_tb_m + 1.96 * UT.sai_so_chuan_tb_m)} m và khoảng cách tới mức 7 m nằm trong biên dao động thống kê. **Thứ hai**, Bước 8 dùng một bộ hồi quy học có giám sát; bộ hồi quy chỉ nhận bằng chứng do HUI tạo ra và chỉ chọn giữa các ô có điểm HUI cao nhất, nhưng phần cân các bằng chứng là do học máy đảm nhận. **Thứ ba**, thiết bị thu: tập kiểm tra dùng chủ yếu điện thoại lạ, và mẫu HUI của một ô mô tả nhóm AP mạnh cùng xuất hiện tại ô đó, phân biệt tốt giữa các vùng nhưng ít thông tin về vị trí chính xác giữa các điểm tham chiếu.`));
  add(P(`Về chi phí, với θ thấp số HUI tăng rất nhanh (${vn(U.model.n_huis, 0)} HUI cho mô hình chính của UJIIndoorLoc ở θ = 20%, tổng cộng ${vn(nHUI3, 0)} HUI cho ba mô hình), làm thời gian định vị lớn hơn k-NN trên cài đặt Python. Đây là cái giá của việc thay vân tay bằng mẫu: mô hình không chứa dữ liệu thô nhưng phải lưu và duyệt nhiều mẫu.`));
  add(H2("4.12. Kết luận chương 4"));
  add(P(`Chương 4 đã đánh giá mô hình đề xuất trên sáu bộ dữ liệu với giao thức không rò rỉ dữ liệu. Mô hình đạt sai số trung bình dưới 7 m trên cả ${allTests.length} tập kiểm tra; trên UJIIndoorLoc, Bước 8 giảm sai số từ ${vn(U4.mean_err_m)} m xuống ${vn(UT.sai_so_tb_m)} m. Các phân tích theo tầng, theo thiết bị, theo không gian và theo nhóm bằng chứng cho thấy nguồn sai số chính còn lại là độ phân giải trong tầng và sự khác biệt thiết bị; mọi con số đều được kiểm chứng độc lập.`));

  // ================================================================ KẾT LUẬN
  add(H1("KẾT LUẬN VÀ KIẾN NGHỊ"));
  add(H2("1. Kết quả đạt được"));
  add(BUL(`Luận văn đã xây dựng một hệ thống định vị trong nhà trong đó HUIM là thuật toán định vị chính: mô hình là tập HUI do EFIM khai thác cho từng điểm tham chiếu, và mọi quyết định về tòa nhà, tầng và toạ độ đến từ bằng chứng rút ra từ HUI; không dùng k-NN và không lưu vân tay huấn luyện.`));
  add(BUL(`Trên ${allTests.length} tập kiểm tra của ${order.length} bộ dữ liệu, cả ${nOk} tập đạt sai số trung bình dưới 7 m (UJIIndoorLoc ${vn(UT.sai_so_tb_m)} m, UJI_LIB ${vn(D.datasets.uji_lib3.tests["Test-01"].sai_so_tb_m)}/${vn(D.datasets.uji_lib3.tests["Test-02"].sai_so_tb_m)} m, DLULIB ${vn(D.datasets.dlulib.tests.Testing.sai_so_tb_m)} m, HCXY ${vn(D.datasets.hcxy.tests.test_HCXY.sai_so_tb_m)} m, HUS khoảng ${vn(D.datasets.hus_dedup.tests.testcase1.sai_so_tb_m)}–${vn(D.datasets.hus_dedup.tests.testcase2.sai_so_tb_m)} m).`));
  add(BUL(`Trên UJIIndoorLoc, Bước 8 (xếp hạng lại ô ứng viên bằng bằng chứng HUI từ ba mô hình HUI) giảm sai số trung bình từ ${vn(U4.mean_err_m)} m xuống ${vn(UT.sai_so_tb_m)} m, dưới mức 7 m với biên nhỏ.`));
  add(BUL(`Mọi lựa chọn mô hình được thực hiện trên dev; mọi con số được kiểm chứng độc lập (${D.verification.n_checks} phép kiểm, ${D.verification.n_failed} thất bại) và có thể tính lại bằng sổ Excel và script kèm theo.`));
  add(H2("2. Hạn chế"));
  add(BUL(`Biên dưới mức 7 m trên UJIIndoorLoc nhỏ so với sai số chuẩn ${vn(UT.sai_so_chuan_tb_m)} m.`));
  add(BUL(`Bước 8 dựa vào một bộ hồi quy học máy để cân các bằng chứng HUI; phiên bản chỉ dùng điểm khớp HUI đạt ${vn(U4.mean_err_m)} m trên UJIIndoorLoc.`));
  add(BUL(`Chi phí khai thác và định vị lớn khi θ thấp; cài đặt hiện tại bằng Python.`));
  add(H2("3. Hướng phát triển và kiến nghị"));
  add(BUL(`Thiết kế lợi ích nội bất biến hơn với thiết bị, ví dụ hiệu chỉnh độ lệch theo từng điện thoại ngay trong lợi ích nội.`));
  add(BUL(`Tăng độ phân giải trong tầng bằng các ô nhỏ hơn hoặc kết hợp HUI ở nhiều mức không gian (tầng, vùng, ô); thay bộ hồi quy của Bước 8 bằng một quy tắc kết hợp tường minh, dễ diễn giải hơn.`));
  add(BUL(`Dùng HUI đóng hoặc HUI cực đại và một cài đặt EFIM biên dịch để giảm số mẫu và thời gian định vị; đánh giá trên các bộ dữ liệu có nhiều thiết bị và nhiều thời điểm thu hơn.`));
};
