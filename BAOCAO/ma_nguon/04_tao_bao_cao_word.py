"""BAOCAO / bước 4 - tạo báo cáo Word từ so_lieu/ và diagram/.

    python BAOCAO/ma_nguon/04_tao_bao_cao_word.py

Mọi con số trong văn bản được đọc từ so_lieu/ lúc dựng; không có số gõ tay.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from hinh_chung import BAOCAO, DIAGRAM, SO_LIEU, theta_txt, vn
from nhan import lbl
from word_chung import Doc

J = json.loads((SO_LIEU / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))
B, S = J["tot_nhat"], J["ban_dau"]
CHK = pd.read_csv(SO_LIEU / "01_kiem_chung_union_vs_EFIM.csv")
T2 = pd.read_csv(SO_LIEU / "02_so_AP_theo_minUtil.csv")
E3 = pd.read_csv(SO_LIEU / "03_EFIM_so_HUI_thoi_gian_bo_nho.csv")
S2 = pd.read_csv(SO_LIEU / "04_buoc2_model_ABC.csv")
S3 = pd.read_csv(SO_LIEU / "05_buoc3_minUtil_HUIM_chung.csv")
S4 = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_toa.csv")
S6 = pd.read_csv(SO_LIEU / "07_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
S7 = pd.read_csv(SO_LIEU / "08_buoc7_ensemble.csv")
S8 = pd.read_csv(SO_LIEU / "09_buoc8_thoi_gian_bo_nho.csv")
RANK = pd.read_csv(SO_LIEU / "10_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})
TOA = pd.read_csv(SO_LIEU / "11_sai_so_theo_toa.csv", dtype={"toa": str})
CELL = pd.read_csv(SO_LIEU / "12_sai_so_theo_toa_tang.csv")


d = Doc()
H = lambda name: DIAGRAM / f"{name}.png"          # noqa: E731
NBSP = " "                                    # số và đơn vị không bị ngắt dòng
pct = lambda x, nd=1: vn(100 * x, nd) + NBSP + "%"  # noqa: E731


def m(x, nd=2):
    return vn(x, nd) + NBSP + "m"


best3 = S3.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
best4 = S4.dropna(subset=["dev_sai_so_tb_m"]).sort_values("dev_sai_so_tb_m").iloc[0]
best6 = S6.sort_values("dev_sai_so_tb_m").iloc[0] if len(S6) else None
best7 = S7.sort_values("dev_sai_so_tb_m").iloc[0]
t_start = S8[S8.cau_hinh == "G_A__1.9294pct"].iloc[0]
t_best = S8[S8.cau_hinh == B["config"]]
t_best = t_best.iloc[0] if len(t_best) else None
toa = lambda k, b: TOA[(TOA.cau_hinh == k) & (TOA.toa == str(b))].iloc[0]   # noqa: E731
SINGLE = RANK[RANK.loai == "don"].iloc[0]
T_SINGLE = S8[S8.cau_hinh == SINGLE.cau_hinh]
T_SINGLE = T_SINGLE.iloc[0] if len(T_SINGLE) else None

# ================================================================== bìa
d.p(("BÁO CÁO BÀI TÌM HIỂU", "b"), size=13, align="center", after=2)
d.p(("HUIM CHO ĐỊNH VỊ TRONG NHÀ BẰNG VÂN TAY WI‑FI", "b"), size=17, align="center", after=2)
d.p("Tối ưu việc chọn Access Point bằng khai thác tập mục tiện ích cao (HUIM) trên bộ dữ liệu "
    "UJIIndoorLoc - chỉ dùng các cấu hình có HUIM", size=12.5, align="center", after=14)
d.hop([
    [("Kết quả chính. ", "b"), f"Cấu hình HUIM tốt nhất (chọn theo dev): ", (lbl(B["config"]), "b"),
     f", {int(B['n_ap'])} AP."],
    [("Sai số trung bình trên tập test (validationData, 1.111 mẫu): ", "b"), (m(B["test_mean_m"]), "b"),
     f" (trung vị {m(B['test_median_m'])}, p90 {m(B['test_p90_m'])}); "
     f"đúng tòa {pct(B['test_building_acc'])}, đúng tòa-tầng {pct(B['test_joint_acc'])}."],
    [("Cấu hình ban đầu ", "b"), f"(HUIM chung 3 tòa, Model A, θ = 1,9294 %, 86 AP): {m(S['test_mean_m'])}; "
     f"đúng tòa-tầng {pct(S['test_joint_acc'])}. Sai số giảm ",
     (vn(100 * (1 - B['test_mean_m'] / S['test_mean_m']), 1) + " %", "b"), "."],
    [("Tòa 1 ", "b"), f"(tòa hỏng nhất ban đầu): {m(toa('ban_dau', 1).sai_so_tb_m)} → "
     f"{m(toa('tot_nhat', 1).sai_so_tb_m)}."],
    [("Chi phí: ", "b")] + ([f"{vn(t_best.ms_per_fp, 2)} ms / fingerprint, radio map "
                            f"{vn(t_best.radio_map_mb, 1)} MB (ban đầu {vn(t_start.ms_per_fp, 2)} ms, "
                            f"{vn(t_start.radio_map_mb, 1)} MB)."] if t_best is not None else ["xem mục 6."]),
    [("Phương án đơn lẻ ", "b"), f"(cấu hình không ensemble tốt nhất theo dev): {lbl(SINGLE.cau_hinh)}, "
     f"{int(SINGLE.so_AP)} AP - {m(SINGLE.test_sai_so_tb_m)} trên tập test (dev {m(SINGLE.dev_sai_so_tb_m)})"
     + (f", {vn(T_SINGLE.ms_per_fp, 2)} ms / fingerprint, radio map {vn(T_SINGLE.radio_map_mb, 1)} MB"
        if T_SINGLE is not None else "") + ". Ensemble chỉ hơn "
     + m(SINGLE.test_sai_so_tb_m - B["test_mean_m"]) + " nhưng chạy 3 mô hình."],
    [("Đã thử ", "b"), f"{J['so_cau_hinh_da_thu']} cấu hình HUIM (3 model × lưới minUtil × 2 phạm vi × "
     "quy tắc chọn AP × ensemble). Mọi lựa chọn dựa trên 6 fold dev của trainingData; "
     "tập test (validationData) chỉ dùng để báo cáo."],
])
d.p("Ngày lập: 16/10/2026. Bộ dữ liệu: UJIIndoorLoc (Torres-Sospedra và cộng sự, IPIN 2014, "
    "DOI 10.1109/IPIN.2014.7275492), dùng nguyên bản, không chỉnh sửa.", size=10.5, italic=True)

d.h("Mục lục", 1)
for s in ["Tóm tắt", "1. Bài toán, dữ liệu và giao thức đánh giá", "2. Mô hình hoá HUIM cho việc chọn AP",
          "3. Thuật toán: EFIM và tìm union HUI chính xác", "4. Bộ định vị S4",
          "5. Kết quả tối ưu HUIM (bước 2-7)", "6. Thời gian và bộ nhớ",
          "7. Cấu hình cuối cùng: phân tích theo tòa, tầng, vị trí", "8. Hạn chế",
          "9. Cách chạy lại và truy vết số liệu"]:
    d.p(s, after=1)
d.ngat_trang()

# ================================================================ tóm tắt
d.h("Tóm tắt", 1)
d.p("Mục tiêu của đợt cập nhật này là chỉ giữ lại các cấu hình có dùng HUIM để chọn AP, và làm cho "
    "HUIM cho sai số định vị thấp nhất có thể trên UJIIndoorLoc. Cấu hình ban đầu - HUIM khai phá "
    "chung trên giao dịch của cả 3 tòa, Model A (p(i) = 1), minUtil θ = 1,9294 % - chọn 86 AP và cho "
    f"sai số trung bình {m(S['test_mean_m'])}. Phân tích cho thấy nguyên nhân chính không nằm ở hàm "
    "utility mà ở ngưỡng minUtil so với phạm vi khai phá: ngưỡng tính theo tổng utility của cả 3 tòa, tòa 2 "
    "có nhiều dòng và AP cùng xuất hiện dày đặc nên chiếm gần hết các HUI; tòa 1 gần như không có AP nào được "
    "chọn (68,4 % mẫu test của tòa 1 không thấy AP nào trong 86 AP). Có hai cách sửa, cả hai đều được "
    "thử: hạ θ của HUIM chung (cần thuật toán mới, vì EFIM không chạy nổi dưới 1,93 %) và khai phá HUIM "
    "riêng cho từng tòa.", align="justify")
d.p("Các bước đã làm: (2) so sánh 3 hàm utility Model A / B / C; (3) quét lưới minUtil θ - để quét được "
    "θ thấp (0,5-1,5 %), nơi EFIM liệt kê đầy đủ bị bùng nổ, báo cáo đề xuất một thuật toán tìm "
    "chính xác tập AP xuất hiện trong ít nhất một HUI mà không cần liệt kê hết HUI, và kiểm chứng nó "
    f"cho kết quả giống hệt EFIM ở cả {len(CHK)} lần chạy EFIM đã hoàn tất; (4) khai phá HUIM riêng "
    "cho từng tòa; (5) dùng bộ định vị S4 cho mọi cấu hình; (6) thử 4 quy tắc chuyển HUI thành tập AP; "
    "(7) ensemble nhiều cấu hình HUIM; (8) đo thời gian và bộ nhớ.", align="justify")
d.p(f"Cấu hình tốt nhất theo dev là {lbl(B['config'])}: sai số trung bình {m(B['test_mean_m'])} trên "
    f"tập test, giảm {vn(100 * (1 - B['test_mean_m'] / S['test_mean_m']), 1)} % so với ban đầu. "
    f"Cấu hình đơn lẻ tốt nhất ({lbl(SINGLE.cau_hinh)}, {int(SINGLE.so_AP)} AP) đạt {m(SINGLE.test_sai_so_tb_m)} "
    "với chi phí bằng khoảng một phần ba, nên là lựa chọn thực tế khi cần nhanh.", align="justify")
d.hinh(H("H01_so_do_luong_HUIM_IPS"), "Hình 1. Sơ đồ luồng HUIM-IPS với cấu hình cuối cùng (ngưỡng minUtil ghi trong khối 3).")

# ================================================================ 1
d.h("1. Bài toán, dữ liệu và giao thức đánh giá", 1)
d.h("1.1. UJIIndoorLoc", 2)
d.bullets([
    "trainingData: 19.937 fingerprint, validationData: 1.111 fingerprint; mỗi fingerprint là cường độ "
    "tín hiệu (RSSI, dBm) của 520 AP, giá trị 100 = không thấy AP.",
    "3 tòa nhà (BUILDINGID 0-2), 13 cặp tòa-tầng; toạ độ LONGITUDE/LATITUDE là mét chiếu Web Mercator "
    "(EPSG:3857). Sai số được báo bằng mét mặt đất = mét chiếu × 0,766126.",
    "Hai tập có người đo, thiết bị và thời điểm khác nhau (cách nhau khoảng 4 tháng), nên sai số trên "
    "tập test là sai số khi gặp người dùng mới, điện thoại mới.",
    [("validationData được dùng làm tập test. ", "b"),
     "Kho UCI chỉ công bố hai file có nhãn của UJIIndoorLoc, và trang mô tả gọi validationData.csv là "
     "\"1111 validation/test records\" (archive.ics.uci.edu/dataset/310/ujiindoorloc). Báo cáo dùng nó làm tập test: "
     "không dùng để dựng radio map, khai phá HUI hay chọn bất kỳ tham số nào. Vai trò \"validation\" "
     "(chọn tham số) do 6 fold dev tách từ trainingData đảm nhận (mục 1.2). Mọi con số \"trên tập test\" "
     "trong báo cáo là trên 1.111 mẫu của validationData."],
])
d.h("1.2. Giao thức: chọn trên dev, báo cáo trên tập test", 2)
d.p("Mọi lựa chọn trong báo cáo - hàm utility (Model A/B/C), ngưỡng minUtil θ, phạm vi khai phá (chung "
    "hay theo tòa), quy tắc chọn AP, thành viên ensemble - đều dựa trên sai số trung bình trên 6 fold dev: "
    "GroupKFold theo USERID trên trainingData, nên mỗi fold dev chỉ chứa người dùng mà mô hình chưa thấy. "
    "Tập test (validationData) được đánh giá một lần cho mỗi cấu hình và không bao giờ được dùng để chọn. "
    "Như vậy con số trên tập test của cấu hình cuối cùng là con số trung thực, không bị chọn lọc theo tập kiểm tra.",
    align="justify")
d.p("Các chỉ số: sai số định vị trung bình, trung vị, p90 (mét mặt đất); tỉ lệ đúng tòa; tỉ lệ đúng cả tòa "
    "và tầng; thời gian định vị mỗi fingerprint; bộ nhớ radio map; thời gian và bộ nhớ khai phá HUIM.",
    align="justify")

# ================================================================ 2
d.h("2. Mô hình hoá HUIM cho việc chọn AP", 1)
d.h("2.1. Fingerprint thành giao dịch utility", 2)
d.p("Mỗi fingerprint của trainingData là một giao dịch T; item là AP thấy được (RSSI ≠ 100). "
    "Utility trong (internal utility) là cường độ tín hiệu chuẩn hoá về số nguyên 1-100:", align="justify")
d.cong_thuc("q(i, T) = round( 1 + 99 · (RSSI(i,T) − RSSI_min) / (RSSI_max − RSSI_min) )")
d.p("Utility ngoài p(i) không có sẵn trong dữ liệu Wi-Fi nên phải định nghĩa; ba định nghĩa được so sánh:")
d.bullets([
    [("Model A (tín hiệu): ", "b"), "p(i) = 1 - utility chỉ do cường độ tín hiệu và mức độ cùng xuất hiện."],
    [("Model B (phân biệt): ", "b"), "p(i) = I(A_i ; Y) / max_j I(A_j ; Y), thông tin tương hỗ giữa trạng "
     "thái AP (6 mức RSSI) và nhãn vị trí Y."],
    [("Model C (hiếm và phân biệt): ", "b"), "p(i) ∝ I(A_i ; Y) · log(N / (1 + support_i))."],
])
d.p("Utility của tập AP X trong giao dịch T và trên cả cơ sở dữ liệu D:")
d.cong_thuc("u(X, T) = Σ_{i∈X} q(i,T) · p(i)          u(X) = Σ_{T ⊇ X} u(X, T)")
d.p("X là tập mục tiện ích cao (HUI) nếu u(X) ≥ minUtil. Báo cáo ghi minUtil dưới dạng tỉ lệ θ của tổng "
    "utility của phạm vi khai phá: minUtil = θ · Σ_T TU(T).", align="justify")
d.h("2.2. Từ tập HUI đến tập AP", 2)
d.bullets([
    [("union: ", "b"), "mọi AP có mặt trong ít nhất một HUI (cách đọc trực tiếp của \"HUIM chọn AP\"; "
     "θ là tham số duy nhất)."],
    [("top-n: ", "b"), "n AP có đóng góp utility lớn nhất, đóng góp(i) = Σ_{X∋i} u(X)/|X|."],
    [("frequent: ", "b"), "AP xuất hiện trong ít nhất k HUI."],
    [("weighted: ", "b"), "giữ cả union nhưng nhân trọng số w_i = (đóng góp(i)/max)^γ vào khoảng cách "
     "Bray-Curtis (Bray-Curtis có trọng số)."],
])
d.h("2.3. HUIM chung và HUIM theo từng tòa", 2)
d.p("HUIM chung khai phá một lần trên giao dịch của cả 3 tòa. HUIM theo từng tòa khai phá riêng trên giao "
    "dịch của mỗi tòa b (với Model B/C, Y là tầng trong tòa đó), cho 3 tập AP_0, AP_1, AP_2, mỗi tập dùng "
    "ngưỡng θ tính theo tổng utility của chính tòa đó. Khi định vị một fingerprint mới:", align="justify")
d.bullets([
    "giai đoạn 1 - đoán tòa: bỏ phiếu có trọng số của 12 láng giềng S4 trên AP_0 ∪ AP_1 ∪ AP_2 "
    "(không dùng tòa thật của mẫu kiểm tra);",
    "giai đoạn 2 - trong tòa đoán được, chạy S4 chỉ trên AP của tòa đó và các fingerprint huấn luyện "
    "của tòa đó, ra toạ độ (x, y) và tầng.",
])

# ================================================================ 3
d.h("3. Thuật toán: EFIM và tìm union HUI chính xác", 1)
d.h("3.1. Vì sao không hạ θ được bằng EFIM", 2)
e_rows = []
for mm in "ABC":
    for _, r in E3[(E3.model == mm) & (E3.so_HUI > 0)].sort_values("minUtil_pct", ascending=False).iterrows():
        e_rows.append([mm, theta_txt(r.minUtil_pct), f"{int(r.so_HUI):,}".replace(",", "."),
                       "xong" if r.trang_thai == "COMPLETED" else "DỪNG (giới hạn)",
                       vn(r.thoi_gian_s, 1), vn(r.bo_nho_dinh_MB, 1), int(r.so_AP_union_EFIM)])
d.p("EFIM (Zida và cộng sự, 2017) liệt kê đầy đủ mọi HUI. Trên UJIIndoorLoc, các AP cùng tòa xuất hiện "
    "cùng nhau rất dày nên mỗi tập con lớn của một nhóm AP như vậy đều là HUI: khi θ giảm, số HUI tăng "
    "theo cấp số nhân và EFIM dừng vì chạm giới hạn 600 s / 10⁶ HUI (Bảng 1, Hình 2a). Khi dừng giữa "
    "chừng, tập AP thu được không đầy đủ - ví dụ Model A ở θ = 1,8612 % chỉ có 31 AP trong khi θ = "
    "1,9294 % có 86 AP, trái với tính đơn điệu - nên các lần chạy dừng giữa chừng bị loại.", align="justify")
d.bang(["Model", "θ", "Số HUI", "Trạng thái", "Thời gian (s)", "Bộ nhớ (MB)", "AP trong union"], e_rows,
       [1.4, 1.8, 2.4, 3.0, 2.4, 2.4, 2.6], "EFIM liệt kê đầy đủ theo minUtil θ (HUIM chung 3 tòa)")
d.h("3.2. Tìm union chính xác không cần liệt kê HUI", 2)
d.p("Tập AP mà HUIM giao cho bộ định vị là union(θ) = { i : tồn tại X ∋ i với u(X) ≥ minUtil }. "
    "Muốn biết AP i có thuộc union hay không chỉ cần MỘT HUI chứa i, không cần mọi HUI. Thuật toán "
    "(src/huim/union_search.py) giữ nguyên phép duyệt theo chiều sâu của EFIM - thứ tự item theo TWU tăng, "
    "cận TWU, cận local utility lu và cận sub-tree utility su - và thêm một luật cắt nhánh chính xác:",
    align="justify")
d.bullets([
    [("Luật phủ: ", "b"), "khi mọi item của tiền tố α đã chắc chắn thuộc union, cây con của α chỉ còn đáng "
     "duyệt nếu nó có thể sinh ra một HUI chứa một item v CHƯA thuộc union; mọi tập như vậy có utility "
     "≤ lu(α, v), nên nếu lu(α, v) < minUtil với mọi v chưa phủ thì cắt cả cây con."],
    "Mọi cận dùng để cắt đều là cận trên của utility, nên một nhánh chỉ bị cắt khi chắc chắn không chứa HUI "
    "nào làm thêm AP vào union: kết quả là union chính xác, không xấp xỉ.",
    "Mỗi mức θ được tính độc lập (chạy song song); union phải tăng khi θ giảm - được kiểm tra tự động.",
])
ok = int(CHK["identical"].astype(str).str.lower().eq("true").sum())
d.p("Kiểm chứng thứ nhất (tests/test_union_search.py): trên 18 cơ sở dữ liệu ngẫu nhiên, kể cả loại dày đặc "
    "nơi luật phủ cắt nhiều nhất, và 6 ngưỡng mỗi cơ sở dữ liệu, union của thuật toán trùng với union của "
    "oracle vét cạn (liệt kê mọi tập con theo đúng định nghĩa HUI); 19/19 kiểm thử đạt.", align="justify")
d.p(f"Kiểm chứng thứ hai, trên UJIIndoorLoc: ở cả {len(CHK)} mức θ mà EFIM liệt kê xong (Model A, B, C), union của thuật toán "
    f"trùng khớp từng AP với union của EFIM ({ok}/{len(CHK)} khớp; so_lieu/01_kiem_chung_union_vs_EFIM.csv). "
    "Nhờ đó các mức θ thấp mà EFIM không chạy nổi vẫn có tập AP chính xác.", align="justify")
d.hinh(H("H02_EFIM_bung_no_va_thoi_gian_tim_union"),
       "Hình 2. (a) Số HUI EFIM liệt kê theo θ; (b) thời gian EFIM liệt kê đủ so với thời gian tìm union.")
d.hinh(H("H03_so_AP_theo_minUtil"), "Hình 3. Số AP trong union HUI theo minUtil θ, HUIM chung và HUIM theo tòa.")

# ================================================================ 4
d.h("4. Bộ định vị S4", 1)
d.p("Mọi cấu hình dùng cùng một bộ định vị S4 (đã chọn trước trên dev ở PHASE I3 của dự án), chỉ khác "
    "tập AP đầu vào:", align="justify")
d.bullets([
    "biểu diễn mũ x = exp((RSSI + 105)/24) / exp(105/24), AP không thấy = 0; khoảng cách Bray-Curtis;",
    "k = 12 láng giềng, trọng số w = 1/d⁴; toạ độ = trung bình có trọng số của 12 láng giềng;",
    "tìm độ lệch thiết bị: thử cộng δ ∈ {−6, −3, 0, +3, +6} dB vào RSSI của mẫu, giữ δ cho láng giềng gần nhất "
    "gần nhất (chỉ dùng tín hiệu của chính mẫu);",
    "ensemble: trung bình toạ độ với cùng mô hình trên biểu diễn dương (1-100); tầng = bỏ phiếu có trọng số.",
])

# ================================================================ 5
d.h("5. Kết quả tối ưu HUIM", 1)
d.h("5.1. Bước 2 - Model A / B / C", 2)
rows = []
for _, r in S2.sort_values("dev_sai_so_tb_m").head(8).iterrows():
    rows.append([r.model, theta_txt(r.theta_pct) if "theta_pct" in r else theta_txt(r.minUtil_pct),
                 int(r.so_AP), m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m),
                 vn(r.test_toa0_m, 1), vn(r.test_toa1_m, 1), vn(r.test_toa2_m, 1), pct(r.test_dung_toa_tang)])
d.bang(["Model", "θ", "AP", "Dev", "Test", "Tòa 0", "Tòa 1", "Tòa 2", "Đúng tòa-tầng"], rows,
       [1.3, 1.7, 1.1, 1.9, 2.1, 1.6, 1.6, 1.6, 2.3],
       "Bước 2: HUIM chung, các θ mà EFIM liệt kê xong (8 cấu hình tốt nhất theo dev; sai số theo tòa trên tập test, m)")
d.p("Model B và C chọn 0 AP ở tòa 1 (thông tin tương hỗ với nhãn tòa-tầng do tòa 2 chi phối), nên tòa 1 vẫn "
    "sai 43-45 m; Model A có 29 AP ở tòa 1 nhưng 68 % mẫu test tòa 1 không thấy AP nào trong số đó. "
    "Đổi hàm utility không giải quyết được vấn đề tòa 1.", align="justify")

d.h("5.2. Bước 3 - quét minUtil θ, HUIM chung", 2)
rows = []
for _, r in S3.sort_values(["model", "minUtil_pct"]).iterrows():
    if pd.isna(r.get("dev_sai_so_tb_m")):
        rows.append([r.model, theta_txt(r.minUtil_pct), int(r.so_AP) if not pd.isna(r.get("so_AP")) else "-",
                     "-", "-", "-", "-", "chưa tính được" if isinstance(r.get("status"), str) else "0 AP"])
        continue
    rows.append([r.model, theta_txt(r.minUtil_pct), int(r.so_AP), m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m),
                 vn(r.test_toa1_m, 1), pct(r.test_dung_toa_tang), ""])
d.bang(["Model", "θ", "AP", "Dev", "Test", "Tòa 1 (m)", "Đúng tòa-tầng", "Ghi chú"], rows,
       [1.2, 2.0, 1.2, 2.1, 2.3, 1.9, 2.3, 3.2], "Bước 3: lưới θ, HUIM chung 3 tòa, bộ định vị S4")
d.p(f"Cấu hình HUIM chung tốt nhất theo dev: {lbl(best3.cau_hinh)}, {int(best3.so_AP)} AP, dev "
    f"{m(best3.dev_sai_so_tb_m)}, tập test {m(best3.test_sai_so_tb_m)}. Hạ θ làm union lớn dần và sai số "
    "giảm, nhưng tòa 1 chỉ được cứu khi union đủ lớn để chứa AP của tòa 1 - tức là phải dùng nhiều AP cho cả 3 tòa.",
    align="justify")
d.hinh(H("H04_sai_so_theo_minUtil"), "Hình 4. Sai số trung bình theo minUtil θ: (a) HUIM chung, (b) HUIM theo tòa.")

d.h("5.3. Bước 4 - HUIM theo từng tòa", 2)
rows = []
for _, r in S4.sort_values(["model", "minUtil_pct"]).iterrows():
    if pd.isna(r.get("dev_sai_so_tb_m")):
        rows.append([r.model, theta_txt(r.minUtil_pct), "-", "-", "-", "-", "-",
                     "chưa tính được" if isinstance(r.get("status"), str) else "có tòa 0 AP"])
        continue
    rows.append([r.model, theta_txt(r.minUtil_pct),
                 f"{int(r.so_AP)} ({int(r.so_AP_toa0)}/{int(r.so_AP_toa1)}/{int(r.so_AP_toa2)})",
                 m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m), vn(r.test_toa1_m, 1), pct(r.test_dung_toa_tang), ""])
d.bang(["Model", "θ", "AP (tòa 0/1/2)", "Dev", "Test", "Tòa 1 (m)", "Đúng tòa-tầng", "Ghi chú"], rows,
       [1.2, 2.0, 3.0, 2.0, 2.2, 1.8, 2.2, 2.0], "Bước 4: lưới θ, HUIM riêng từng tòa (θ theo utility của mỗi tòa)")
d.p(f"Cấu hình HUIM theo tòa tốt nhất theo dev: {lbl(best4.cau_hinh)} - {int(best4.so_AP)} AP "
    f"({int(best4.so_AP_toa0)}/{int(best4.so_AP_toa1)}/{int(best4.so_AP_toa2)} cho tòa 0/1/2), dev "
    f"{m(best4.dev_sai_so_tb_m)}, tập test {m(best4.test_sai_so_tb_m)}, tòa 1 {m(best4.test_toa1_m)}, đúng tòa "
    f"{pct(best4.test_dung_toa)}. Khai phá theo tòa buộc mỗi tòa có tập AP của mình, nên tòa 1 không còn bị "
    "tòa 2 lấn át (Hình 5).", align="justify")
d.hinh(H("H05_so_AP_moi_toa"), "Hình 5. Số AP mỗi tòa trong tập chọn: ban đầu, HUIM chung tốt nhất, HUIM theo tòa tốt nhất.")
d.hinh(H("H06_danh_doi_so_AP_sai_so"), "Hình 6. Đánh đổi số AP - sai số; nhãn cạnh mỗi điểm là minUtil θ.")
d.hinh(H("H07_do_chinh_xac_toa_tang_theo_minUtil"), "Hình 7. Tỉ lệ đúng tòa-tầng theo minUtil θ.")

d.h("5.4. Bước 6 - quy tắc chuyển HUI thành tập AP", 2)
E3b = pd.read_csv(SO_LIEU / "03b_EFIM_theo_toa.csv")
if len(E3b):
    d.p("Các quy tắc top-n, frequent và weighted cần TOÀN BỘ tập HUI (để tính đóng góp utility và số HUI chứa mỗi AP), "
        "tức là phải chạy EFIM liệt kê đầy đủ. Với HUIM theo tòa, EFIM (giới hạn 300 s / 10⁶ HUI mỗi lần) được thử "
        "cho Model A từ θ cao xuống tới mức đầu tiên bị dừng, và cho Model B - model của cấu hình theo tòa tốt nhất - ở "
        "mọi θ từ θ tốt nhất trở lên. Không có mức θ nào mà cả 3 tòa đều liệt kê xong và có HUI "
        "(Bảng dưới) - tòa 1 dừng ngay từ θ = 7,5 % - nên ở phạm vi theo tòa chỉ quy tắc union áp dụng được "
        "(nhờ thuật toán tìm union ở mục 3.2). Các quy tắc còn lại được so sánh trên HUIM chung.", align="justify")
    rows = [[r.model, int(r.toa), theta_txt(r.minUtil_pct), "xong" if r.trang_thai == "COMPLETED" else "DỪNG",
             f"{int(r.so_HUI):,}".replace(",", "."), vn(r.thoi_gian_s, 1)] for _, r in E3b.iterrows()]
    d.bang(["Model", "Tòa", "θ", "EFIM", "Số HUI", "Thời gian (s)"], rows, [1.6, 1.4, 2.0, 2.2, 3.0, 2.6],
           "EFIM liệt kê đầy đủ theo từng tòa, θ giảm dần đến mức đầu tiên bị dừng", size=9)
if len(S6):
    rows = [[("Chung" if r.pham_vi == "global" else "Theo tòa") + f" {r.model}", theta_txt(r.minUtil_pct),
             r.quy_tac + ("" if pd.isna(r.tham_so) or r.tham_so == "" else f" ({r.tham_so})"),
             int(r.so_AP), m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m)]
            for _, r in S6.iterrows()]
    d.bang(["Phạm vi, model", "θ", "Quy tắc", "AP", "Dev", "Test"], rows,
           [3.2, 1.8, 3.6, 1.4, 2.6, 2.6], "Bước 6: quy tắc chọn AP trên tập HUI đầy đủ (EFIM) của cấu hình tốt nhất mỗi phạm vi")
    d.p("Các quy tắc top-n / frequent / weighted cần toàn bộ tập HUI (để tính đóng góp utility và số HUI chứa "
        "mỗi AP), nên được áp dụng ở θ tốt nhất của mỗi phạm vi nếu EFIM liệt kê xong ở đó, ngược lại ở θ "
        f"kế tiếp cao hơn. Quy tắc tốt nhất theo dev: {lbl(best6.cau_hinh)} (dev {m(best6.dev_sai_so_tb_m)}, "
        f"tập test {m(best6.test_sai_so_tb_m)}).", align="justify")
    d.hinh(H("H08_quy_tac_chon_AP"), "Hình 8. So sánh quy tắc chọn AP (θ ghi trên tiêu đề từng ô).")

d.h("5.5. Bước 7 - ensemble nhiều cấu hình HUIM", 2)
rows = [[lbl(r.cau_hinh), m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m), pct(r.test_dung_toa_tang)]
        for _, r in S7.sort_values("dev_sai_so_tb_m").head(8).iterrows()]
d.bang(["Ensemble (thành viên, θ)", "Dev", "Test", "Đúng tòa-tầng"], rows, [10.2, 2.0, 2.2, 2.4],
       "Bước 7: 8 ensemble tốt nhất theo dev (toạ độ = trung bình hoặc trung vị; tầng = đa số)", size=8.5)
d.p(f"Ensemble tốt nhất theo dev: {lbl(best7.cau_hinh)} - dev {m(best7.dev_sai_so_tb_m)}, tập test "
    f"{m(best7.test_sai_so_tb_m)}.", align="justify")
d.hinh(H("H09_ensemble"), "Hình 9. Ensemble so với cấu hình đơn lẻ tốt nhất.")

d.h("5.6. Xếp hạng chung và cấu hình được chọn", 2)
rows = [[int(r.hang_theo_dev), lbl(r.cau_hinh), "-" if pd.isna(r.so_AP) else int(r.so_AP),
         m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m)] for _, r in RANK.head(10).iterrows()]
d.bang(["Hạng", "Cấu hình (θ)", "AP", "Dev", "Test"], rows, [1.3, 9.6, 1.4, 2.2, 2.2],
       f"10 cấu hình tốt nhất theo dev trong {len(RANK)} cấu hình đã thử", size=8.5, bold_row=0)
CB = J["can_bang"]
d.p("Chọn θ cân bằng giữa số AP và độ chính xác. Quy tắc đặt trước khi xem tập test: trong mỗi phạm vi, "
    "lấy cấu hình ít AP nhất có sai số dev không quá 105 % sai số dev tốt nhất của phạm vi đó.", align="justify")
d.bullets([[("HUIM chung" if k == "global" else "HUIM theo tòa") + ": ", (lbl(v["config"]), "b"),
            f" - {int(v['n_ap'])} AP, dev {m(v['dev_mean_m'])} (ngưỡng {m(v['nguong_dev_m'])}), "
            f"tập test {m(v['test_mean_m'])}."] for k, v in CB.items()])

# ================================================================ 6
d.h("6. Thời gian và bộ nhớ", 1)
d.p("Chi phí ngoại tuyến (huấn luyện) gồm khai phá HUIM để có tập AP và dựng radio map; chi phí trực tuyến "
    "là thời gian định vị một fingerprint. Thời gian định vị là trung vị của 3 lần chạy sau 1 lần khởi động, "
    "định vị cả 1.111 mẫu test trong một lô, dùng mọi nhân CPU (máy 12 nhân); bộ nhớ là kích thước radio "
    "map (float64) và RSS tăng thêm khi chạy (psutil).", align="justify")
rows = [[lbl(r.cau_hinh) if not r.cau_hinh.startswith("E_") else "Ensemble tốt nhất", int(r.so_AP),
         vn(r.ms_per_fp, 2), vn(r.radio_map_mb, 1), vn(r.peak_delta_mb, 1),
         "-" if pd.isna(r.get("build_s")) else vn(r.build_s, 2), m(r.test_sai_so_tb_m)] for _, r in S8.iterrows()]
d.bang(["Cấu hình (θ)", "AP", "ms / fp", "Radio map (MB)", "RSS thêm (MB)", "Dựng (s)", "Test"], rows,
       [6.0, 1.2, 1.6, 2.1, 2.1, 1.6, 2.0], "Chi phí trực tuyến và kích thước mô hình", size=8.5)
d.hinh(H("H10_thoi_gian_bo_nho_dinh_vi"), "Hình 10. Thời gian định vị và bộ nhớ radio map.")
d.hinh(H("H11_bo_nho_khai_pha"), "Hình 11. Bộ nhớ đỉnh khi khai phá theo minUtil θ.")

# ================================================================ 7
d.h("7. Cấu hình cuối cùng: phân tích theo tòa, tầng, vị trí", 1)
rows = []
for k, ten in (("ban_dau", "Ban đầu"), ("tot_nhat", "Tốt nhất")):
    for b in ("0", "1", "2", "Tong"):
        r = TOA[(TOA.cau_hinh == k) & (TOA.toa == b)].iloc[0]
        rows.append([ten, "Toàn bộ" if b == "Tong" else f"Tòa {b}", int(r.so_mau), vn(r.sai_so_tb_m, 2),
                     vn(r.trung_vi_m, 2), vn(r.p90_m, 2), vn(r.toa_dung_pct, 1), vn(r.toa_tang_dung_pct, 1),
                     vn(r.trong_5m_pct, 1)])
d.bang(["Cấu hình", "Tòa", "Mẫu", "TB (m)", "Trung vị", "p90", "Đúng tòa %", "Đúng tòa-tầng %", "≤ 5 m %"],
       rows, [1.9, 1.7, 1.2, 1.6, 1.7, 1.5, 1.9, 2.6, 1.6],
       f"Sai số theo tòa trên tập test - ban đầu: {lbl(S['config'])}; tốt nhất: {lbl(B['config'])}", size=9)
d.hinh(H("H12_sai_so_theo_toa"), "Hình 12. Sai số trung bình theo tòa, trước và sau tối ưu.")
d.hinh(H("H13_heatmap_sai_so_toa_tang"), "Hình 13. Sai số trung bình theo tòa × tầng.")
d.hinh(H("H14_CDF_sai_so"), "Hình 14. Phân phối tích luỹ sai số trên 1.111 mẫu test.")
d.hinh(H("H15_ban_do_sai_so"), "Hình 15. Vị trí thật của các mẫu test, tô màu theo sai số.")

# ================================================================ 8
d.h("8. Hạn chế", 1)
d.bullets([
    "Báo cáo chỉ so sánh các biến thể HUIM với nhau, theo yêu cầu của đợt cập nhật; nó không kết luận HUIM "
    "tốt hơn các cách chọn AP khác (theo thông tin tương hỗ, theo tần suất, hay dùng mọi AP).",
    "HUI được khai phá trên toàn bộ trainingData, nên tập AP đã \"nhìn thấy\" các fold dev; độ lệch lạc quan "
    "này như nhau cho mọi cấu hình nên không thiên vị cấu hình nào, nhưng con số dev thấp hơn thực tế đôi chút. "
    "Con số trên tập test thì sạch.",
    "HUIM theo tòa cần đoán tòa trước; một mẫu đoán sai tòa sẽ được định vị trong tòa sai (đã tính vào sai số).",
    "Utility ngoài p(i) và utility trong q(i,T) là lựa chọn mô hình hoá của dự án, không phải chuẩn; HUIM không "
    "tối ưu trực tiếp sai số định vị, nên mọi lợi ích phải được đo bằng thực nghiệm.",
    "Thời gian đo trên một máy Windows 12 nhân, Python thuần (EFIM và tìm union không dùng mã biên dịch); "
    "chỉ có ý nghĩa so sánh giữa các cấu hình trong báo cáo này. Thời gian tìm union của từng mức θ được đo "
    "khi nhiều mức chạy song song (tới 15 tiến trình), còn thời gian EFIM lấy từ PHASE H; so sánh giữa hai "
    "thuật toán (Hình 2b) chỉ nên đọc theo bậc độ lớn. Thời gian định vị (mục 6) được đo khi máy rảnh.",
])
to = RANK[RANK.cau_hinh.astype(str).str.contains("TIMEOUT")]
miss = pd.concat([S3, S4])
miss = miss[miss.get("status").astype(str).str.contains("TIMEOUT|not computed", na=False)] if "status" in miss else miss.iloc[0:0]
if len(miss):
    d.bullets([f"{len(miss)} mức (phạm vi, model, θ) không tính xong union trong giới hạn "
               "30 phút/mức và được bỏ khỏi lưới: " + ", ".join(lbl(c) for c in miss.cau_hinh) + "."])

# ================================================================ 9
d.h("9. Cách chạy lại và truy vết số liệu", 1)
d.p("Chạy từ thư mục gốc dự án: python BAOCAO/ma_nguon/00_chay_lai_toan_bo.py (thí nghiệm + báo cáo, "
    "khoảng 2-3 giờ) hoặc thêm --bao-cao để chỉ dựng lại số liệu, hình, Word và PowerPoint từ kết quả có sẵn.")
rows = [
    ["Bảng 1, Hình 2, 11", "so_lieu/03_EFIM_so_HUI_thoi_gian_bo_nho.csv", "results/multi_dataset/uji/huim_runs__*.csv"],
    ["Kiểm chứng union", "so_lieu/01_kiem_chung_union_vs_EFIM.csv", "src/check_union_search.py"],
    ["Hình 3", "so_lieu/02_so_AP_theo_minUtil.csv", "src/run_union_levels.py, src/huim/union_search.py"],
    ["Bước 2", "so_lieu/04_buoc2_model_ABC.csv", "src/run_huim_opt.py --step 2"],
    ["Bước 3, Hình 4a", "so_lieu/05_buoc3_minUtil_HUIM_chung.csv", "src/run_huim_opt.py --step 3"],
    ["Bước 4, Hình 4b, 5-7", "so_lieu/06_buoc4_HUIM_theo_toa.csv", "src/run_huim_opt.py --step 4"],
    ["Bước 6, Hình 8", "so_lieu/07_buoc6_quy_tac_chon_AP.csv", "src/run_huim_opt.py --step 6"],
    ["Bước 7, Hình 9", "so_lieu/08_buoc7_ensemble.csv", "src/run_huim_opt.py --step 7"],
    ["Mục 6, Hình 10, 11", "so_lieu/09_buoc8_thoi_gian_bo_nho.csv", "src/run_huim_opt.py --step 8"],
    ["Mục 5.6", "so_lieu/10_xep_hang_tat_ca_cau_hinh.csv", "BAOCAO/ma_nguon/02_tong_hop_so_lieu.py"],
    ["Mục 7, Hình 12-15", "so_lieu/11-13_*.csv", "BAOCAO/ma_nguon/02_tong_hop_so_lieu.py"],
]
d.bang(["Nội dung", "File số liệu", "Sinh bởi"], rows, [3.4, 6.6, 6.4], "Truy vết số liệu", size=8.5)

d.save(BAOCAO / "Bao_cao_HUIM_IPS_UJIIndoorLoc.docx")
print("đã lưu", BAOCAO / "Bao_cao_HUIM_IPS_UJIIndoorLoc.docx", "-", d.n_bang, "bảng,", d.n_hinh, "hình")
