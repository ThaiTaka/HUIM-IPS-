// Phụ lục của báo cáo; gọi từ build_report.js.
module.exports = function ({ add, D, U, UT, V6, EX, GF, L_ }) {
  const { vn, P, PN, H1, H2, BUL, TAB, C, RT, L } = L_;
  add(H1("PHỤ LỤC"));
  add(H2("Phụ lục A. Cấu trúc thư mục báo cáo"));
  const tA = TAB("A", "Nội dung thư mục BAOCAO", ["Thành phần", "Nội dung"], [
    ["diagram/d01–d10", "10 sơ đồ mô hình theo từng bước, từ đầu vào tới đầu ra, vẽ từ mô hình và một vân tay kiểm tra thật"],
    ["diagram/b01–b16", "16 biểu đồ kết quả và phân tích (số liệu vẽ nằm trong so_lieu/bieu_do)"],
    ["so_lieu/", "kết quả tổng hợp, cấu hình chọn trên dev, lịch sử phiên bản, dự đoán từng mẫu, sổ Excel kiểm chứng, script kiem_tra_mean.py"],
    ["ma_nguon/", "mã nguồn EFIM, bộ định vị, Bước 8, thực nghiệm, kiểm chứng, kiểm thử và script dựng báo cáo"],
    ["Bao_cao_…docx, Slide_…pptx", "luận văn này và bài thuyết trình"]], [3000, 6071]);
  add(tA);
  add(H2("Phụ lục B. Tham số của mô hình cuối (UJIIndoorLoc)"));
  const s = U.selection, p = s.params;
  const tB = TAB("B", "Toàn bộ tham số của mô hình cuối trên UJIIndoorLoc", ["Tham số", "Giá trị", "Ý nghĩa"], [
    ["Lợi ích nội", s.utility, "dạng rank (3.3) cho mô hình chính"],
    ["θ", `${vn(s.theta_pct, 0)}%`, "ngưỡng tương đối theo ô; tự nâng ×1,25 khi vượt ngân sách"],
    ["Ngân sách EFIM", "10 s, 10 000 HUI", "mỗi lần chạy trên một ô"],
    ["γ, τ, β", `${p.gamma}, ${p.tau}, ${p.beta}`, "số mũ của ρ, thang cường độ, số mũ của độ phủ"],
    ["σ, $k_f$", `${p.sigma} m, ${p.kf}`, "bán kính làm mượt; số ô dùng chọn tầng"],
    ["m, p (Bước 7)", `${p.m}, ${p.p}`, "ước lượng ban đầu"],
    ["L", "3", "số mức cường độ của mô hình mục theo mức"],
    ["K, m, λ (Bước 8)", `${V6.k_candidates}, ${V6.m}, ${vn(V6.lam, 0)}`, "số ô ứng viên, số ô dùng cho toạ độ cuối, thang khoảng cách"],
    ["Bộ hồi quy", "300 cây, η = 0,06, 31 lá, ≥ 40 mẫu/lá", "HistGradientBoostingRegressor, mục tiêu log(1 + khoảng cách)"],
    ["Fold dev", "6, theo điện thoại", "GroupKFold trên PHONEID"],
  ], [2300, 2600, 4171], { align: [L, L, L] });
  add(tB);
  add(H2("Phụ lục C. Các phép kiểm chứng của mô hình cuối"));
  const tC = TAB("C", "Kiểm chứng độc lập mô hình cuối của UJIIndoorLoc (ma_nguon/src/verify_v6.py)", ["Phép kiểm", "Kết quả", "Chi tiết"],
    V6.verification.checks.map((c) => [c.check, c.ok ? "đạt" : "không đạt", c.detail]), [3300, 1100, 4671], { align: [L, C, L], size: 11 });
  add(tC);
  add(H2("Phụ lục D. Hướng dẫn tái lập kết quả"));
  add(P(`Mã nguồn nằm trong thư mục ma_nguon (bản sao của src/ và tests/ của dự án). Cần Python 3.12 trở lên và các gói trong requirements.txt. Các lệnh chính, chạy từ thư mục gốc dự án:`));
  [
    "python -m pytest tests -q  —  kiểm thử EFIM với thuật toán vét cạn và bộ định vị",
    "python src/run_huim_only.py --dataset uji  —  Bước 1–7: chọn trên dev, chấm tập kiểm tra",
    "python src/huim_research.py --stage mine --fold k [--levels 3 | --kind abs]  —  ba mô hình HUI theo fold dev",
    "python src/huim_rerank_final.py --stage dev --fold k --with-abs  —  đặc trưng Bước 8 trên dev",
    "python src/huim_rerank_final.py --stage final --with-abs  —  học trên dev, chấm tập kiểm tra một lần",
    "python src/verify_huim_only.py; python src/verify_v6.py  —  kiểm chứng độc lập",
    "python so_lieu/kiem_tra_mean.py  —  tính lại sai số trung bình chỉ bằng thư viện chuẩn",
  ].forEach((t) => add(BUL(t)));
};
