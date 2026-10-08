"""Chapters 9-11 of the Word report (utility models, experimental setup).

Imported by make_report.py. All numbers come from the Ctx object.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from report_builder import Doc
from utils import FIGURES


def nf(x, d=0):
    if x is None:
        return "N/A"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(v):
        return "N/A"
    return f"{v:,.{d}f}"


# ===========================================================================
def ch9(D: Doc, C) -> None:
    hm = C.huim["utility_models"]
    a = hm["A_signal"]
    D.h(1, "9. Utility Model A — Signal utility")
    D.p("Model A là ĐIỀU KIỆN ĐỐI CHỨNG (control condition) của ablation, "
        "không phải mô hình được kỳ vọng tốt nhất. Mục đích của nó là trả lời "
        "câu hỏi: nếu utility chỉ phản ánh cường độ tín hiệu thì HUIM tìm ra "
        "cái gì?", align="justify")

    D.h(2, "9.1. Định nghĩa")
    D.formula("q(i,T) = cường độ RSSI đã chuẩn hoá  (mục 8.4)")
    D.formula("p(i) = 1  với mọi AP i")
    D.formula("⟹  u(i,T) = q(i,T)")
    D.p(a["p_rationale"], align="justify")

    D.h(2, "9.2. Hệ quả của việc đặt p ≡ 1")
    D.p("Khi p ≡ 1, utility của một itemset chỉ còn phụ thuộc hai thứ: cường "
        "độ tín hiệu của các AP, và SỐ LƯỢNG fingerprint mà chúng cùng xuất "
        "hiện. Nói cách khác, một High Utility Itemset dưới Model A gần như "
        "chính là 'một nhóm AP mạnh và đồng xuất hiện thường xuyên'.",
        align="justify")
    D.rich([("Đây chính là lý do Model A là đối chứng tốt: ", "b"),
            ("nó tái tạo lại đúng chế độ thất bại của Frequent Itemset Mining "
             "đã phân tích ở mục 4.5 — nhưng ở mức HÀM UTILITY chứ không ở mức "
             "từng item. Kết quả thực nghiệm (chương 13 và mục 15.8) cho thấy "
             "xếp hạng AP của Model A tệ hơn cả chọn ngẫu nhiên ở mọi ngân "
             "sách đã thử, trong khi bản thân tần suất phát hiện của từng AP "
             "lại là một tiêu chí chọn RẤT tốt. Nói cách khác: thứ gây hại "
             "không phải 'tần suất', mà là việc nhân cường độ tín hiệu với mức "
             "đồng xuất hiện.", "")])

    D.h(2, "9.3. Số liệu thực đo của Model A")
    D.table(pd.DataFrame([
        {"Đại lượng": "Tổng utility toàn database",
         "Giá trị": nf(a["total_database_utility"], 0)},
        {"Đại lượng": "Số giao dịch (khác rỗng)",
         "Giá trị": nf(a["n_transactions"])},
        {"Đại lượng": "Số item thực sự xuất hiện",
         "Giá trị": nf(a["n_distinct_items_present"])},
        {"Đại lượng": "TU(T) nhỏ nhất",
         "Giá trị": nf(a["transaction_utility_min"], 0)},
        {"Đại lượng": "TU(T) lớn nhất",
         "Giá trị": nf(a["transaction_utility_max"], 0)},
        {"Đại lượng": "TU(T) trung bình",
         "Giá trị": nf(a["transaction_utility_mean"], 2)},
        {"Đại lượng": "TU(T) trung vị",
         "Giá trị": nf(a["transaction_utility_median"], 1)},
        {"Đại lượng": "Khoảng giá trị p(i)", "Giá trị": "1 (hằng số)"},
    ]), "Model A — thống kê cơ sở dữ liệu utility (trainingData)",
        font_pt=10, widths=[3.2, 2.4])
    D.rich([("Ghi nhận rõ: ", "b"),
            ("đây là một adaptation được thử nghiệm, không phải một định nghĩa "
             "chuẩn có trong literature.", "i")])
    D.page_break()


# ===========================================================================
def ch10(D: Doc, C) -> None:
    hm = C.huim["utility_models"]
    b = hm["B_discriminative"]
    cm = hm.get("C_rare_discriminative")
    D.h(1, "10. Utility Model B — Discriminative utility (và Model C)")
    D.p("Đây là mô hình chính của bài tìm hiểu, nếu kết quả hợp lý.", align="justify")

    D.h(2, "10.1. Ý tưởng")
    D.p("Model A coi 'hữu ích' = 'mạnh và phổ biến'. Nhưng với bài toán định "
        "vị, một AP nhìn thấy được ở mọi nơi thì KHÔNG giúp gì cả — nó không "
        "phân biệt được vị trí nào với vị trí nào. Thứ một cơ sở dữ liệu "
        "fingerprint cần là AP mà TRẠNG THÁI của nó THAY ĐỔI theo vị trí.",
        align="justify")
    D.p("Vì vậy external utility của Model B được định nghĩa là mức độ phân "
        "biệt vị trí của AP, đo bằng mutual information (lượng tin tương hỗ) "
        "giữa trạng thái của AP và nhãn vị trí.", align="justify")

    D.h(2, "10.2. Mutual information — công thức và cách tính")
    D.formula("I(A ; Y) = Σ(a) Σ(y)  P(a,y) · log₂ [ P(a,y) / ( P(a)·P(y) ) ]")
    D.p("Trong đó: A là trạng thái của AP đang xét (biến ngẫu nhiên rời rạc), "
        "Y là nhãn vị trí, P(a,y) là xác suất đồng thời, P(a) và P(y) là xác "
        "suất lề. Đơn vị là bit. Ý nghĩa: biết trạng thái của AP thì giảm được "
        "bao nhiêu bit bất định về vị trí.", align="justify")
    D.rich([("Rời rạc hoá trạng thái AP. ", "b"),
            (f"AP được quy về {b['n_signal_states']} trạng thái: trạng thái 0 "
             "dành riêng cho 'không phát hiện' (bản thân việc KHÔNG nhìn thấy "
             "một AP cũng định vị được bạn, chẳng kém gì việc nhìn thấy nó "
             f"mạnh), và {b['n_signal_states'] - 1} trạng thái cường độ chia "
             f"theo các mốc dBm {b['rssi_bin_edges_dbm']}.", "")])
    D.p("Mutual information được tính TRỰC TIẾP từ histogram đồng thời, nên "
        "hoàn toàn tiền định (deterministic) và tái lập được — không dùng bộ "
        "ước lượng có yếu tố ngẫu nhiên. Bản cài đặt được kiểm chứng đối chiếu "
        "với sklearn.metrics.mutual_info_score trên 25 bộ dữ liệu ngẫu nhiên "
        "(tests/test_utility.py::test_mutual_information_matches_sklearn_oracle).",
        align="justify")
    D.rich([("Căn cứ literature: ", "b"),
            ("đại lượng này chính là tiêu chí mà literature về chọn Access "
             "Point gọi là information gain — xem Chen và cộng sự (IEEE TKDE, "
             "vol. 18, pp. 877–888, 2006) và Song và cộng sự (ISPRS IJGI, "
             "vol. 5, 189, 2016). Phần LẤY TỪ literature là thước đo; phần ĐỀ "
             "XUẤT của bài tìm hiểu là việc đặt thước đo đó vào đúng khe external "
             "utility của HUIM.", "")])

    D.h(2, "10.3. Nhãn mục tiêu")
    D.rich([("Y = BUILDINGID_FLOOR. ", "b"),
            (f"Lý do chọn nhãn này thay vì nhãn chi tiết hơn: audit đã xác "
             f"nhận cả hai split đều có đúng "
             f"{C.tr['joint_building_floor_n_classes']} lớp này, trong khi "
             f"SPACEID trong validationData đồng nhất bằng 0 "
             f"({C.cs['validation_SPACEID_n_unique']} giá trị duy nhất) nên "
             "không thể dùng để đánh giá. Đây là lớp định vị thô (coarse "
             "localisation) nhưng có ý nghĩa rõ ràng và đánh giá được một cách "
             "trung thực.", "")])
    D.table(pd.DataFrame([
        {"Đại lượng": "Entropy của nhãn H(Y)",
         "Giá trị": f"{b['label_entropy_H_Y_bits']} bit",
         "Ý nghĩa": f"Mức bất định ban đầu về vị trí giữa "
                    f"{C.tr['joint_building_floor_n_classes']} lớp"},
        {"Đại lượng": "MI lớn nhất trong các AP",
         "Giá trị": f"{b['mi_bits_max']} bit",
         "Ý nghĩa": f"AP thông tin nhất giải thích được "
                    f"{b['mi_bits_max_as_fraction_of_H_Y']*100:.1f}% H(Y)"},
        {"Đại lượng": "MI trung bình (trên các AP được phát hiện)",
         "Giá trị": f"{b['mi_bits_mean_over_detected']} bit",
         "Ý nghĩa": "Phần lớn AP đóng góp rất ít thông tin"},
    ]), "Thông tin mà một AP đơn lẻ mang về vị trí", font_pt=9,
        widths=[2.3, 1.3, 2.4])
    D.p("Không AP nào một mình giải thích được toàn bộ H(Y) — đó chính là lý "
        "do bài toán cần một NHÓM AP, và cũng là lý do một thuật toán khai "
        "thác ITEMSET (nhóm) thay vì xếp hạng từng item riêng lẻ là một ý "
        "tưởng đáng thử.", align="justify")

    D.h(2, "10.4. Công thức external utility của Model B")
    D.formula("p(i) = max( I(A_i ; Y) , 10⁻⁶ )  /  max_j I(A_j ; Y)")
    D.p("Chuẩn hoá về khoảng (0, 1], với AP thông tin nhất có p = 1. Sàn "
        "10⁻⁶ là bắt buộc về mặt thuật toán: EFIM yêu cầu utility dương "
        "nghiêm ngặt, nên một AP có MI đúng bằng 0 vẫn phải có p > 0.",
        align="justify")
    D.rich([("Vì sao chọn dạng TỶ LỆ chứ không phải dạng 1 + k·MI: ", "b"),
            ("dạng tỷ lệ cho phép utility của một AP không mang thông tin suy "
             "giảm về gần 0, trong khi dạng 1 + k·MI luôn giữ cho mọi AP một "
             "mức utility tối thiểu. Hành vi cần KIỂM TRA ở đây chính là liệu "
             "việc dìm các AP vô ích xuống gần 0 có thay đổi tập AP được chọn "
             "hay không, nên dạng tỷ lệ là lựa chọn đúng. Đây là quyết định "
             "thiết kế, được ghi lại trước khi có bất kỳ số liệu accuracy "
             "nào.", "")])
    D.table(pd.DataFrame([
        {"Đại lượng": "p nhỏ nhất", "Giá trị": f"{b['p_min']:.3g}"},
        {"Đại lượng": "p lớn nhất", "Giá trị": f"{b['p_max']:.3g}"},
        {"Đại lượng": "p trung bình", "Giá trị": f"{b['p_mean']:.4g}"},
        {"Đại lượng": "Tổng utility toàn database",
         "Giá trị": nf(b["total_database_utility"], 0)},
        {"Đại lượng": "TU(T) trung bình",
         "Giá trị": nf(b["transaction_utility_mean"], 2)},
        {"Đại lượng": "TU(T) lớn nhất",
         "Giá trị": nf(b["transaction_utility_max"], 2)},
        {"Đại lượng": "Nguồn dữ liệu ước lượng p",
         "Giá trị": b["estimated_from"]},
    ]), "Model B — thống kê external utility và cơ sở dữ liệu utility",
        font_pt=10, widths=[3.2, 2.4])
    top = b.get("top10_waps_by_mi") or []
    if top:
        D.table(pd.DataFrame([
            {"Hạng": k + 1, "WAP": r["wap"], "MI (bit)": r["mi_bits"],
             "Số lần được phát hiện": nf(r["support"])}
            for k, r in enumerate(top)]),
            "Model B — 10 AP có mutual information cao nhất với "
            "BUILDINGID_FLOOR", font_pt=10, widths=[0.7, 1.3, 1.3, 2.0])

    o6 = C.o.get("observation_6_strong_vs_discriminative", {})
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        D.h(2, "10.5. Một hạn chế thiết kế phát hiện được SAU khi chạy thực "
               "nghiệm")
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"Trên toàn bộ {o6['n_detected_waps_compared']} AP được phát "
                 f"hiện, tương quan hạng giữa SỐ LẦN ĐƯỢC PHÁT HIỆN và MUTUAL "
                 f"INFORMATION là Spearman ρ = ", ""),
                (f"{o6['spearman_support_vs_mi_over_all_detected_waps']}", "b"),
                (f" (Pearson r = "
                 f"{o6['pearson_support_vs_mi_over_all_detected_waps']}).",
                 "")])
        D.rich([("Hệ quả phải nói thẳng: ", "b"),
                ("external utility mà bài tìm hiểu đặt tên là 'discriminative' trên "
                 "bộ dữ liệu này gần như là một cách THAM SỐ HOÁ LẠI tần suất "
                 "phát hiện, chứ không phải một đại lượng độc lập với nó.",
                 "")])
        D.p("Nguyên nhân nằm ở chính cách rời rạc hoá: trạng thái 0 ('không "
            "phát hiện') chiếm phần áp đảo trong phân bố của mỗi AP, nên "
            "I(A_i;Y) chủ yếu phản ánh việc AP i CÓ ĐƯỢC NHÌN THẤY HAY KHÔNG "
            "ở từng tầng — tức gần như chính là support tính theo từng lớp.",
            align="justify")
        D.p("Điều này giải thích một cách nhất quán ba hiện tượng khác trong "
            "kết quả: (1) hai đối chứng top-n theo MI và top-n theo support "
            "cho kết quả rất gần nhau; (2) Model B và Model C chọn ra những "
            "tập AP rất giống nhau; (3) ablation giữa B và C vì vậy ít thông "
            "tin hơn thiết kế ban đầu kỳ vọng.", align="justify")
        D.rich([("Đây là HẠN CHẾ CỦA THIẾT KẾ BÀI TÌM HIỂU, không phải tính chất của "
                 "HUIM. ", "b"),
                ("Một phiên bản sau nên dùng MI có điều kiện trên việc AP đã "
                 "được phát hiện, hoặc một thước đo trực tiếp đo sự biến thiên "
                 "CƯỜNG ĐỘ theo vị trí, để external utility thực sự mang thông "
                 "tin khác với support.", "")])

    D.h(2, "10.6. Chống data leakage — điểm bắt buộc")
    D.rich([("Nguyên tắc tuyệt đối: ", "b"),
            ("mutual information và mọi trọng số p CHỈ được tính trên "
             "trainingData. Nếu dùng validationData để thiết kế đặc trưng thì "
             "đó là data leakage, và mọi con số độ chính xác sau đó đều vô "
             "giá trị.", "")])
    D.p("Vì sao điều này nghiêm trọng: nếu p được tính từ validationData, thì "
        "tập AP được chọn đã 'biết trước' câu trả lời của bài kiểm tra. Mô "
        "hình sẽ cho độ chính xác cao một cách giả tạo, và con số đó không nói "
        "gì về hiệu năng thực tế trên dữ liệu chưa từng thấy.", align="justify")
    D.rich([("Cách bài tìm hiểu CƯỠNG CHẾ nguyên tắc này thay vì chỉ hứa: ", "b"),
            ("hàm build_external_utility nhận một tham số bắt buộc "
             "split_name, và sẽ RAISE lỗi nếu giá trị khác 'training'. Một lời "
             "gọi vô tình trên validationData không thể âm thầm sinh ra một "
             "vector trọng số bị rò rỉ — nó làm chương trình dừng. Có unit "
             "test riêng cho cơ chế này "
             "(test_leakage_gate_refuses_non_training_split).", "")])

    if cm:
        D.h(2, "10.7. Model C — Rare-discriminative utility (tuỳ chọn)")
        D.p("Model C kiểm tra một giả thuyết hẹp hơn: nếu dìm thêm các AP phổ "
            "biến — những AP được phát hiện ở khắp nơi nên không phân tách "
            "được gì — thì tập AP được chọn có thay đổi không?",
            align="justify")
        D.formula("p(i) ∝ I(A_i ; Y) × log( N / (1 + support_i) )")
        D.p("Thừa số thứ hai là inverse document frequency (IDF) quen thuộc "
            "trong truy hồi thông tin, với N là số fingerprint huấn luyện và "
            "support_i là số fingerprint phát hiện được AP i. Nhân MI với IDF "
            "chỉ giữ lại AP vừa mang thông tin vừa không phổ biến. Giá trị "
            "được chuẩn hoá về (0, 1].", align="justify")
        D.table(pd.DataFrame([
            {"Đại lượng": "p nhỏ nhất", "Giá trị": f"{cm['p_min']:.3g}"},
            {"Đại lượng": "p lớn nhất", "Giá trị": f"{cm['p_max']:.3g}"},
            {"Đại lượng": "p trung bình", "Giá trị": f"{cm['p_mean']:.4g}"},
            {"Đại lượng": "Tổng utility toàn database",
             "Giá trị": nf(cm["total_database_utility"], 0)},
        ]), "Model C — thống kê external utility", font_pt=10,
            widths=[3.2, 2.4])
    D.page_break()


# ===========================================================================
def ch11(D: Doc, C) -> None:
    env, pro = C.env, C.ips["protocol"]
    D.h(1, "11. Thiết kế thực nghiệm")

    D.h(2, "11.1. Giao thức chống data leakage")
    D.table(pd.DataFrame([
        {"Bước": "Chuẩn hoá RSSI (RSSI_min, RSSI_max)",
         "Dùng dữ liệu nào": "trainingData"},
        {"Bước": "Thiết kế utility, tính trọng số p (mutual information)",
         "Dùng dữ liệu nào": "trainingData"},
        {"Bước": "Khai thác HUIM (EFIM)",
         "Dùng dữ liệu nào": "trainingData"},
        {"Bước": "Chọn tập AP từ các HUI",
         "Dùng dữ liệu nào": "trainingData"},
        {"Bước": "Chọn siêu tham số k-NN",
         "Dùng dữ liệu nào": "train_sub / dev_sub — đều tách từ trainingData"},
        {"Bước": "Huấn luyện bộ phân loại cuối",
         "Dùng dữ liệu nào": "toàn bộ trainingData"},
        {"Bước": "ĐÁNH GIÁ",
         "Dùng dữ liệu nào": "validationData — một lần duy nhất cho mỗi "
                             "điều kiện"},
    ]), "validationData chỉ xuất hiện ở đúng một dòng cuối cùng", font_pt=10,
        widths=[3.4, 2.5])
    D.p(pro["validation_used_for"], align="justify")

    D.h(2, "11.2. Kiểm chứng tính đúng của bản cài đặt EFIM")
    D.p("Vì không dùng được SPMF (mục 7.4), bản cài đặt Python phải tự chứng "
        "minh tính đúng. Chiến lược: không bao giờ tin vào đầu ra của chính "
        "nó.", align="justify")
    D.bullets([
        "Một module ORACLE brute-force (src/huim/brute_force.py) liệt kê mọi "
        "tập con khác rỗng và tính u(X) thẳng từ định nghĩa. Nó cố tình KHÔNG "
        "có cắt tỉa và KHÔNG có cấu trúc dữ liệu thông minh, nên mọi bất đồng "
        "với EFIM là lỗi của EFIM chứ không phải hai bản cài đặt cùng sai một "
        "kiểu.",
        "EFIM được đối chiếu với oracle trên: ví dụ chuẩn của literature tại "
        "16 ngưỡng khác nhau; 40 cơ sở dữ liệu ngẫu nhiên độc lập, mỗi cái ở 5 "
        "ngưỡng; 15 cơ sở dữ liệu có hình dạng thưa-và-rộng giống Wi-Fi; và "
        "một trường hợp external utility là số thực (vì Model B dùng p không "
        "nguyên).",
        "Hai giá trị utility được TÍNH TAY trong file test (u({b,d}) = 30 và "
        "u({b,c,d,e}) = 40 trên ví dụ chuẩn), để phủ cả tình huống 'cả hai bản "
        "cài đặt đều sai giống nhau'.",
        "Kiểm chứng các tính chất lý thuyết: TWU là chặn trên (vét cạn mọi "
        "itemset của ví dụ), utility KHÔNG anti-monotone (phản ví dụ cụ thể), "
        "support vẫn chính xác sau transaction merging, cắt tỉa thực sự xảy ra "
        "(nếu không, thuật toán chỉ là brute force khoác áo).",
        "Kiểm chứng cơ chế dừng có kiểm soát: giới hạn thời gian và giới hạn "
        "số HUI đều phải làm thuật toán dừng và báo trạng thái "
        "ABORTED_RESOURCE_LIMIT, không phải treo máy hay mất kết quả.",
        "Kiểm chứng tiền xử lý và utility model: ngữ nghĩa của sentinel 100, "
        "tính dương của utility, cổng chặn data leakage, và mutual information "
        "đối chiếu với sklearn.",
    ])
    D.rich([("Nguyên tắc thi hành: ", "b"),
            ("KHÔNG dòng nào của UJIIndoorLoc được chạy trước khi toàn bộ "
             "kiểm thử trên đạt. Lệnh kiểm thử và kết quả được ghi trong "
             "README.md và results/logs/.", "")])

    D.h(2, "11.3. Thí nghiệm thăm dò (pilot) và việc hiệu chỉnh lưới minUtil")
    D.rich([("Lưới minUtil ban đầu — 5%, 2%, 1%, 0.5%, 0.2%, 0.1% — được coi "
             "là MỘT GIẢ THUYẾT, không phải một thiết kế đã đúng. ", "b"),
            ("Pilot trên một mẫu con phân tầng cho thấy giả thuyết này sai về "
             "độ phân giải: khoảng giữa 5% và 2% chứa toàn bộ vùng chuyển pha, "
             "còn các ngưỡng từ 1% xuống thấp hơn đều vượt ngân sách tài "
             "nguyên. Lưới thực tế vì vậy được dày lên trong dải đó và mở rộng "
             "lên phía trên.", "")])
    D.p(f"Lưới cuối cùng dùng cho thực nghiệm đầy đủ: "
        f"{', '.join(str(v) + '%' for v in C.huim['grid_pct'])}. Sau đó một "
        f"pha hiệu chỉnh thích nghi dùng chia đôi hình học để mô tả vùng "
        f"chuyển pha giữa ngưỡng thấp nhất COMPLETED và ngưỡng cao nhất "
        f"ABORTED.", align="justify")
    D.p(f"Ngân sách tài nguyên cho mỗi lần chạy: "
        f"{nf(C.huim['time_limit_s'])} giây và {nf(C.huim['max_huis'])} "
        f"itemset. Vượt một trong hai thì lần chạy đó dừng CÓ KIỂM SOÁT và "
        f"được ghi với trạng thái ABORTED_RESOURCE_LIMIT — kết quả một phần "
        f"vẫn được giữ, không bị xoá.", align="justify")

    D.h(2, "11.4. Bộ phân loại và giao thức đánh giá")
    cfg = pro["frozen_knn_config"]
    D.table(pd.DataFrame([
        {"Hạng mục": "Bộ phân loại chính", "Cấu hình": "k-Nearest Neighbours"},
        {"Hạng mục": "Số láng giềng k",
         "Cấu hình": str(cfg["n_neighbors"])},
        {"Hạng mục": "Hàm khoảng cách", "Cấu hình": cfg["metric"]},
        {"Hạng mục": "Trọng số láng giềng", "Cấu hình": cfg["weights"]},
        {"Hạng mục": "Chọn trên", "Cấu hình": cfg["selected_on"]},
        {"Hạng mục": "Độ chính xác joint trên dev_sub khi chọn",
         "Cấu hình": f"{cfg['dev_joint_accuracy']*100:.2f}%"},
        {"Hạng mục": "Biểu diễn đặc trưng",
         "Cấu hình": "positive representation (mục 8.4): không phát hiện → 0"},
        {"Hạng mục": "Nhãn mục tiêu",
         "Cấu hình": "BUILDINGID_FLOOR (13 lớp)"},
        {"Hạng mục": "Random seed", "Cấu hình": str(pro["random_seed"])},
        {"Hạng mục": "Bộ phân loại phụ",
         "Cấu hình": "Random Forest (chỉ trên một số điều kiện chính)"},
    ]), "Cấu hình bộ phân loại — ĐÓNG BĂNG và dùng chung cho mọi điều kiện",
        font_pt=10, widths=[2.6, 3.2])
    D.rich([("Điểm phương pháp quan trọng nhất của chương: ", "b"),
            ("siêu tham số được chọn MỘT LẦN, trên tập đặc trưng ALL-WAP, rồi "
             "ĐÓNG BĂNG và dùng y nguyên cho mọi điều kiện HUIM. Nhờ vậy khác "
             "biệt duy nhất giữa 'All-WAP' và 'HUIM-selected' là CỘT NÀO CÓ "
             "MẶT. Nếu độ chính xác thay đổi thì chính việc chọn đặc trưng gây "
             "ra. Ngoài ra, việc tinh chỉnh trên baseline khiến mọi lợi thế "
             "của tinh chỉnh thuộc về BASELINE, không thuộc về phương pháp của "
             "bài tìm hiểu — đây là lựa chọn bảo thủ, có lợi cho bên đối chứng.", "")])
    D.p("Phản đề cần tránh: nếu đổi cả bộ phân loại lẫn tập đặc trưng rồi báo "
        "'HUIM cải thiện độ chính xác' thì kết luận đó vô giá trị, vì không "
        "biết cải thiện đến từ đâu.", align="justify")

    D.h(2, "11.5. Các điều kiện được đánh giá, và vì sao cần đối chứng")
    D.table(pd.DataFrame([
        {"Điều kiện": "baseline_all_520",
         "Tập đặc trưng": f"toàn bộ {C.tr['n_wap_columns_detected']} cột WAP",
         "Mục đích": "Baseline chính theo yêu cầu"},
        {"Điều kiện": "baseline_detected_465",
         "Tập đặc trưng": f"{C.cs['waps_detected_in_train']} AP từng được "
                          f"phát hiện trong training",
         "Mục đích": "Tách phần giảm chiều MIỄN PHÍ ra khỏi phần công của HUIM"},
        {"Điều kiện": "huim_union__*",
         "Tập đặc trưng": "hợp các AP xuất hiện trong tập HUI",
         "Mục đích": "minUtil là núm điều khiển duy nhất — cách đọc trung thực "
                     "nhất của 'HUIM chọn các AP này'"},
        {"Điều kiện": "huim_topn__*",
         "Tập đặc trưng": "n AP xếp hạng cao nhất theo utility contribution",
         "Mục đích": "Cho phép quét ngân sách đặc trưng tuỳ ý để vẽ đường cong "
                     "giảm chiều ↔ độ chính xác"},
        {"Điều kiện": "control_random__n",
         "Tập đặc trưng": "n AP chọn ngẫu nhiên (3 seed)",
         "Mục đích": "Tập được chọn có chứa thông tin gì không? Nếu không hơn "
                     "ngẫu nhiên thì đây chỉ là xoá chiều"},
        {"Điều kiện": "control_top_support__n",
         "Tập đặc trưng": "n AP được phát hiện nhiều nhất",
         "Mục đích": "Có hơn 'chọn AP nhìn thấy nhiều nhất' không? Đây là câu "
                     "hỏi frequent-vs-useful dạng thực nghiệm"},
        {"Điều kiện": "control_top_mi__n",
         "Tập đặc trưng": "n AP có mutual information cao nhất",
         "Mục đích": "ĐỐI CHỨNG KHÓ NHẤT: nếu xếp hạng AP bằng MI trực tiếp "
                     "cũng tốt bằng khai thác itemset có utility dựng từ MI, "
                     "thì phần khai thác itemset không đóng góp gì"},
    ]), "Các điều kiện thực nghiệm và mục đích của từng điều kiện",
        font_pt=9, widths=[1.5, 1.9, 2.6])
    D.rich([("Ba điều kiện đối chứng là phần không thể bỏ. ", "b"),
            ("Một câu như 'đặc trưng do HUIM chọn đạt độ chính xác X' tự nó "
             "không phải một kết quả. Nếu một tập ngẫu nhiên cùng kích thước "
             "cũng đạt X thì việc chọn không làm gì cả. Và nếu xếp hạng AP "
             "bằng mutual information đơn thuần cũng đạt X thì HUIM không thêm "
             "gì so với chính thước đo mà nó được cho sẵn — và sự trung thực "
             "đòi hỏi phải nói ra điều đó.", "")])

    D.h(2, "11.6. Các độ đo")
    D.bullets([
        "Building Accuracy — tỷ lệ dự đoán đúng toà nhà.",
        "Floor Accuracy — tỷ lệ dự đoán đúng tầng.",
        "Joint Building-Floor Accuracy — tỷ lệ đúng ĐỒNG THỜI cả hai. Đây là "
        "độ đo chính. Cả ba được suy ra từ CÙNG một dự đoán nhãn joint, nên "
        "chúng nhất quán với nhau theo cấu trúc: một mô hình không thể được "
        "ghi công 'đúng tầng' khi nó dự đoán sai toà nhà.",
        "Macro F1 (joint, building, floor) — vì các lớp mất cân bằng "
        f"(kích thước lớp huấn luyện từ "
        f"{nf(min(C.tr['joint_building_floor_distribution'].values()))} đến "
        f"{nf(max(C.tr['joint_building_floor_distribution'].values()))}), "
        "accuracy một mình có thể gây hiểu nhầm.",
        "Confusion matrix của nhãn joint.",
        "Sai số định vị theo toạ độ: trung bình, trung vị, phân vị 75/90/95.",
        "Số fingerprint kiểm định mà KHÔNG có AP nào trong tập được chọn được "
        "phát hiện — chỉ số chẩn đoán cốt yếu, vì nó cho biết một sự sụt giảm "
        "ở ngân sách nhỏ là do mất ĐỘ PHỦ hay do mất KHẢ NĂNG PHÂN BIỆT.",
    ])
    co = C.coord
    if co and co.get("conclusion", {}).get("identified_as"):
        cc = co["conclusion"]
        D.h(3, "Về sai số định vị: hệ toạ độ đã được xác định bằng thực nghiệm")
        D.p("Mô tả thuộc tính chính thức của bộ dữ liệu (UCI) và trang web của "
            "chính nhóm tác giả đều KHÔNG nêu hệ toạ độ hay đơn vị của "
            "LONGITUDE/LATITUDE. Thay vì đoán, bài này xác định bằng cách "
            "nghịch đảo từng phép chiếu ứng viên tại tâm hộp giới hạn của bộ "
            "dữ liệu, rồi đo xem kết quả rơi cách Universitat Jaume I — campus "
            "nơi dữ liệu được thu — bao xa.", align="justify")
        D.table(pd.DataFrame([
            {"Phép chiếu ứng viên": c["candidate"],
             "Vĩ độ nghịch đảo": (f"{c['lat_deg']:.5f}"
                                  if isinstance(c.get("lat_deg"), float)
                                  else "—"),
             "Kinh độ nghịch đảo": (f"{c['lon_deg']:.5f}"
                                    if isinstance(c.get("lon_deg"), float)
                                    else "—"),
             "Cách campus UJI":
                 (f"{c['distance_to_uji_campus_m']:,.1f} m"
                  if isinstance(c.get("distance_to_uji_campus_m"), (int, float))
                  else "—")}
            for c in co["candidates_tested"]]),
            "Nhận dạng hệ toạ độ bằng cách nghịch đảo phép chiếu (nguồn tham "
            "chiếu độc lập: vị trí campus UJI)", font_pt=9)
        D.rich([("Kết quả không mơ hồ: ", "b"),
                (f"{cc['identified_as']} đặt tâm dữ liệu cách campus đúng "
                 f"{cc['distance_to_uji_campus_m']} m, trong khi các ứng viên "
                 f"UTM lệch hàng trăm km.", "")])
        if "web_mercator_scale_factor_at_this_latitude" in cc:
            D.rich([("Nhưng câu trả lời KHÔNG đơn giản là 'vậy là mét'. ", "b"),
                    (f"Web Mercator là phép chiếu BẢO GIÁC chứ không BẢO "
                     f"KHOẢNG CÁCH: hệ số tỷ lệ của nó là 1/cos(vĩ độ), tại "
                     f"campus này bằng "
                     f"{cc['web_mercator_scale_factor_at_this_latitude']}. Một "
                     f"khoảng cách đọc thẳng từ hai cột toạ độ vì vậy LỚN HƠN "
                     f"khoảng cách thực trên mặt đất khoảng 30%.", "")])
            D.table(pd.DataFrame([
                {"Đại lượng": "Chiều ngang hộp giới hạn",
                 "Toạ độ chiếu": f"{cc['projected_extent_m']['x']} m",
                 "Thực địa": f"{cc['true_extent_m']['x']} m"},
                {"Đại lượng": "Chiều dọc hộp giới hạn",
                 "Toạ độ chiếu": f"{cc['projected_extent_m']['y']} m",
                 "Thực địa": f"{cc['true_extent_m']['y']} m"},
                {"Đại lượng": "Diện tích hộp giới hạn",
                 "Toạ độ chiếu": f"{cc['projected_bbox_area_m2']:,.0f} m²",
                 "Thực địa": f"{cc['true_bbox_area_m2']:,.0f} m²"},
            ]), "Hệ quả của biến dạng Web Mercator", font_pt=10,
                widths=[2.4, 1.8, 1.8])
            D.rich([("[OUR INTERPRETATION] ", "b"),
                    (f"Literature thứ cấp thường trích con số ≈108.703 m² cho "
                     f"khu vực này. Con số đó khớp với hộp giới hạn TOẠ ĐỘ "
                     f"CHIẾU ({cc['projected_bbox_area_m2']:,.0f} m²), không "
                     f"khớp với diện tích đã hiệu chỉnh "
                     f"({cc['true_bbox_area_m2']:,.0f} m²). Đây là bằng chứng "
                     f"thêm rằng chính con số công bố cũng được tính trong hệ "
                     f"toạ độ chiếu, và rằng quy ước của literature này là coi "
                     f"hai cột đó là mét một cách trực tiếp.", "")])
        D.rich([("Quyết định: ", "b"),
                ("sai số định vị được báo cáo THEO CẢ HAI CÁCH — mét toạ độ "
                 "chiếu (để so sánh được với các kết quả đã công bố trên "
                 "UJIIndoorLoc) và mét thực địa (đúng về mặt vật lý). Mọi bảng "
                 "đều ghi rõ đang hiển thị loại nào.", "")])

    D.h(2, "11.7. Môi trường thực nghiệm và tính tái lập")
    pk = env["packages"]
    D.table(pd.DataFrame([
        {"Hạng mục": "Hệ điều hành", "Giá trị": env["platform"]},
        {"Hạng mục": "CPU", "Giá trị": str(env.get("cpu_model", "N/A"))},
        {"Hạng mục": "Số lõi (vật lý / logic)",
         "Giá trị": f"{env.get('cpu_count_physical')} / "
                    f"{env.get('cpu_count_logical')}"},
        {"Hạng mục": "RAM", "Giá trị": f"{env.get('ram_total_gb')} GB"},
        {"Hạng mục": "Python", "Giá trị": env["python_version"]},
        {"Hạng mục": "numpy / pandas",
         "Giá trị": f"{pk['numpy']} / {pk['pandas']}"},
        {"Hạng mục": "scikit-learn / scipy",
         "Giá trị": f"{pk['sklearn']} / {pk['scipy']}"},
        {"Hạng mục": "matplotlib", "Giá trị": pk["matplotlib"]},
        {"Hạng mục": "python-docx / python-pptx",
         "Giá trị": f"{pk['docx']} / {pk['pptx']}"},
        {"Hạng mục": "Random seed", "Giá trị": str(pro["random_seed"])},
        {"Hạng mục": "Lệnh chạy lại toàn bộ",
         "Giá trị": "python run_experiments.py"},
    ]), "Môi trường thực nghiệm (ghi tự động, không nhập tay)", font_pt=10,
        widths=[2.4, 3.4])
    D.page_break()
