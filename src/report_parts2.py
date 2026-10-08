"""Chapters 4-8 of the Word report. Imported by make_report.py.

No experimental number is written here; everything comes from the Ctx object.
"""
from __future__ import annotations

import pandas as pd

from report_builder import Doc
from utils import FIGURES


def nf(x, d=0):
    import numpy as np
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
def ch4(D: Doc, C) -> None:
    D.h(1, "4. Frequent Itemset Mining")
    D.p("Phải hiểu bài toán này trước, vì HUIM sinh ra từ việc chỉ ra nó "
        "không đủ.", align="justify")

    D.h(2, "4.1. Bốn khái niệm cơ sở")
    D.bullets([
        "Item: một đối tượng đơn lẻ. Trong siêu thị: một mặt hàng. Trong bài tìm hiểu "
        "này: một Access Point.",
        "Itemset: một tập hợp item, ví dụ {bánh mì, sữa}. Là TẬP HỢP — không "
        "có thứ tự, không lặp.",
        "Transaction (giao dịch): một tập item xuất hiện cùng nhau trong một "
        "lần ghi nhận. Siêu thị: một hoá đơn. Bài tìm hiểu: một fingerprint Wi-Fi.",
        "Database D: danh sách các transaction.",
    ])

    D.h(2, "4.2. Ví dụ nhỏ — 5 giao dịch")
    D.table(pd.DataFrame([
        {"Giao dịch": "T1", "Các item": "bánh mì, sữa"},
        {"Giao dịch": "T2", "Các item": "bánh mì, sữa, bơ"},
        {"Giao dịch": "T3", "Các item": "bánh mì, cá hồi"},
        {"Giao dịch": "T4", "Các item": "sữa, bơ"},
        {"Giao dịch": "T5", "Các item": "bánh mì, sữa, cá hồi"},
    ]), "Cơ sở dữ liệu giao dịch ví dụ", font_pt=10, widths=[1.3, 4.0])

    D.h(2, "4.3. Support")
    D.formula("support(X) = số giao dịch chứa X",
              "X là một itemset. Giao dịch T 'chứa' X khi X ⊆ T.")
    D.p("Tính trên ví dụ: support({bánh mì}) = 4 (T1, T2, T3, T5); "
        "support({sữa}) = 4 (T1, T2, T4, T5); support({bánh mì, sữa}) = 3 "
        "(T1, T2, T5); support({cá hồi}) = 2 (T3, T5); support({bơ}) = 2 "
        "(T2, T4).", align="justify")
    D.p("Một itemset là FREQUENT nếu support(X) ≥ minSup. Với minSup = 3: "
        "{bánh mì}, {sữa} và {bánh mì, sữa} đạt; {bơ} và {cá hồi} không đạt.",
        align="justify")

    D.h(2, "4.4. Tính chất làm bài toán giải được: downward closure")
    D.rich([("Đây là điểm quan trọng nhất của chương, vì chương 5 sẽ chỉ ra "
             "HUIM KHÔNG có tính chất này. ", "b"),
            ("Support có tính anti-monotone (downward closure):", "")])
    D.formula("X ⊆ Y  ⟹  support(X) ≥ support(Y)")
    D.p("Trực giác: nếu một giao dịch chứa Y thì nó cũng chứa mọi tập con của "
        "Y; nên tập lớn hơn không thể xuất hiện nhiều hơn tập con của nó.",
        align="justify")
    D.rich([("Hệ quả cho thuật toán: ", "b"),
            ("nếu X không frequent thì MỌI tập chứa X cũng không frequent. Vì "
             "vậy ngay khi phát hiện X không đạt ngưỡng, có thể bỏ toàn bộ "
             "nhánh chứa X — cắt tỉa an toàn. Đây chính là nguyên lý Apriori "
             "(Agrawal, Imieliński, Swami — ACM SIGMOD 1993), và là lý do một "
             "bài toán hàng tỷ tổ hợp trở nên khả thi.", "")])
    D.p("Han, Pei và Yin (ACM SIGMOD 2000) sau đó thay việc sinh ứng viên bằng "
        "tăng trưởng mẫu (pattern growth) trên cây FP-tree — tổ tiên trực tiếp "
        "của UP-Growth ở chương 6.", align="justify")

    D.h(2, "4.5. Tại sao Frequent Itemset Mining chưa đủ?")
    D.p("Support chỉ ĐẾM. Nó không biết GIÁ TRỊ.", align="justify")
    D.table(pd.DataFrame([
        {"Tình huống": "Xuất hiện rất nhiều, giá trị thấp",
         "Ví dụ siêu thị": "Túi nilon: có trong gần như mọi hoá đơn, lợi nhuận "
                           "gần 0",
         "Tương ứng trong Wi-Fi":
             "AP nhìn thấy khắp campus → support cao nhưng không giúp phân "
             "biệt vị trí nào cả"},
        {"Tình huống": "Xuất hiện ít, giá trị rất cao",
         "Ví dụ siêu thị": "Máy ảnh: hiếm khi xuất hiện, mỗi lần bán lãi bằng "
                           "hàng nghìn túi nilon",
         "Tương ứng trong Wi-Fi":
             "AP chỉ thấy được ở một tầng duy nhất → support thấp nhưng gần "
             "như là một 'máy phát hiện tầng'"},
    ]), "Frequent ≠ Useful: hai tình huống support không nắm bắt được",
        font_pt=9, widths=[1.5, 2.1, 2.4])
    D.rich([("Kết luận của chương: ", "b"),
            ("với minSup đủ thấp để bắt được mặt hàng giá trị cao mà hiếm, ta "
             "nhận về hàng triệu mẫu rác. Với minSup đủ cao để loại rác, ta "
             "mất mặt hàng giá trị. Support không thể làm cả hai, vì nó đo sai "
             "đại lượng. Đó là lý do cần Utility Mining.", "")])
    D.rich([("Lưu ý đọc trước cho chương 15: ", "b"),
            ("cột bên phải của bảng trên là một KỲ VỌNG, không phải một kết "
             "quả. Mục 15.6 kiểm chứng kỳ vọng đó trên UJIIndoorLoc và BÁC BỎ "
             "phần lớn của nó ở mức từng Access Point — số lần một AP được "
             "phát hiện và lượng thông tin nó mang về vị trí hoá ra gần như "
             "trùng khít về thứ hạng trên bộ dữ liệu này.", "i")])
    D.page_break()


# ===========================================================================
def ch5(D: Doc, C) -> None:
    D.h(1, "5. High Utility Itemset Mining")
    D.p("Chương này trình bày toàn bộ công thức; mọi ký hiệu đều được giải "
        "nghĩa. Cơ sở dữ liệu ví dụ là ví dụ chạy chuẩn của literature HUIM "
        "(xuất hiện trong Liu & Qu 2012, Fournier-Viger et al. 2014, Zida et "
        "al. 2017), nên có thể đối chiếu trực tiếp với các bài báo.",
        align="justify")

    D.h(2, "5.1. Cơ sở dữ liệu utility ví dụ")
    D.table(pd.DataFrame([
        {"Giao dịch": "T1", "Nội dung (item, q)": "(a,1) (c,1) (d,1)",
         "TU(T)": "1×5 + 1×1 + 1×2 = 8"},
        {"Giao dịch": "T2", "Nội dung (item, q)": "(a,2) (c,6) (e,2) (g,5)",
         "TU(T)": "10 + 6 + 6 + 5 = 27"},
        {"Giao dịch": "T3", "Nội dung (item, q)":
            "(a,1) (b,2) (c,1) (d,6) (e,1) (f,5)",
         "TU(T)": "5 + 4 + 1 + 12 + 3 + 5 = 30"},
        {"Giao dịch": "T4", "Nội dung (item, q)": "(b,4) (c,3) (d,3) (e,1)",
         "TU(T)": "8 + 3 + 6 + 3 = 20"},
        {"Giao dịch": "T5", "Nội dung (item, q)": "(b,2) (c,2) (e,1) (g,2)",
         "TU(T)": "4 + 2 + 3 + 2 = 11"},
    ]), "Cơ sở dữ liệu utility ví dụ. External utility: p(a)=5, p(b)=2, "
        "p(c)=1, p(d)=2, p(e)=3, p(f)=1, p(g)=1. Tổng utility toàn database "
        "= 96", font_pt=9, widths=[0.9, 2.8, 2.3])
    D.p("Các giá trị TU trong bảng được kiểm chứng bằng unit test "
        "(tests/test_efim.py::test_transaction_and_total_utility), không phải "
        "tính nhẩm.", size=10, italic=True)

    D.h(2, "5.2. Internal utility — q(i, T)")
    D.formula("q(i, T)")
    D.p("Là 'lượng' của item i trong giao dịch T. Trong bài toán giỏ hàng đây "
        "là SỐ LƯỢNG mua. Đặc điểm: phụ thuộc CẢ item VÀ giao dịch — cùng một "
        "item có q khác nhau ở các giao dịch khác nhau. Ví dụ: q(a,T1) = 1 "
        "nhưng q(a,T2) = 2.", align="justify")

    D.h(2, "5.3. External utility — p(i)")
    D.formula("p(i)")
    D.p("Là 'giá trị đơn vị' của item i. Trong bài toán giỏ hàng đây là LỢI "
        "NHUẬN trên một đơn vị. Đặc điểm quan trọng: p(i) KHÔNG phụ thuộc giao "
        "dịch — nó là thuộc tính của item, lưu trong một bảng riêng. Ví dụ: "
        "p(a) = 5 ở mọi giao dịch.", align="justify")
    D.rich([("Hãy ghi nhớ sự khác biệt này, vì chương 8 phụ thuộc hoàn toàn "
             "vào nó: ", "b"),
            ("q thay đổi theo từng lần ghi nhận, p là hằng số của item. Khi "
             "ánh xạ sang Wi-Fi, RSSI thay đổi theo từng fingerprint nên đóng "
             "vai q; còn 'mức độ quan trọng' của một AP là thuộc tính của AP "
             "nên đóng vai p.", "")])

    D.h(2, "5.4. Utility của một item trong một giao dịch")
    D.formula("u(i, T) = q(i, T) × p(i)")
    D.p("Ví dụ: u(a,T2) = q(a,T2) × p(a) = 2 × 5 = 10.", align="justify")

    D.h(2, "5.5. Utility của một itemset trong một giao dịch")
    D.formula("u(X, T) = Σ ( i ∈ X )  u(i, T) ,    định nghĩa khi X ⊆ T")
    D.p("Nếu X không là tập con của T thì X không xuất hiện trong T và không "
        "đóng góp gì. Ví dụ: u({b,d}, T3) = 2×2 + 6×2 = 4 + 12 = 16.",
        align="justify")

    D.h(2, "5.6. Utility của một itemset trên toàn cơ sở dữ liệu")
    D.formula("u(X) = Σ ( T ∈ g(X) )  u(X, T) ,    g(X) = { T ∈ D : X ⊆ T }")
    D.p("g(X) là tập giao dịch chứa X. Ví dụ: {b,d} chỉ có trong T3 và T4, nên "
        "u({b,d}) = 16 + (4×2 + 3×2) = 16 + 14 = 30. Giá trị 30 khớp với giá "
        "trị công bố trong literature cho ví dụ chuẩn và được kiểm chứng bằng "
        "unit test.", align="justify")

    D.h(2, "5.7. Transaction Utility — TU(T)")
    D.formula("TU(T) = u(T, T) = Σ ( i ∈ T )  u(i, T)")
    D.p("Tổng utility của mọi item trong T. Đây là utility LỚN NHẤT mà bất kỳ "
        "itemset nào trong T có thể đóng góp từ giao dịch đó — nhận xét này "
        "chính là hạt giống của TWU ở mục 5.11.", align="justify")

    D.h(2, "5.8. minUtil và định nghĩa High Utility Itemset")
    D.formula("X là High Utility Itemset  ⟺  u(X) ≥ minUtil")
    D.p("minUtil là ngưỡng do người dùng đặt. Trực giác: 'tôi chỉ quan tâm các "
        "nhóm mặt hàng mang về ít nhất minUtil'. Với ví dụ trên và "
        "minUtil = 30, thuật toán trả về 7 itemset, trong đó {b,d} có u = 30 "
        "và {b,c,d,e} có u = 40.", align="justify")
    D.rich([("Một lưu ý thực tế rất quan trọng (chương 12 chứng minh bằng số "
             "liệu): ", "b"),
            ("utility tuyệt đối phụ thuộc thang đo của q và p. Một minUtil = "
             "200.000 là vô nghĩa nếu không biết tổng utility của cơ sở dữ "
             "liệu. Vì vậy bài tìm hiểu luôn biểu diễn minUtil dưới dạng TỶ LỆ PHẦN "
             "TRĂM của tổng utility toàn database.", "")])

    D.h(2, "5.9. Vì sao HUIM khó hơn Frequent Itemset Mining?")
    D.rich([("Câu trả lời chính xác: ", "b"),
            ("utility KHÔNG có tính anti-monotone như support, và cũng không "
             "có tính monotone.", "")])
    D.p("Nghĩa là từ u(X) < minUtil ta KHÔNG suy ra được u(Y) < minUtil cho "
        "mọi Y ⊇ X. Hai chiều đều có phản ví dụ, lấy từ chính ví dụ trên:",
        align="justify")
    D.bullets([
        "Tập con utility thấp hơn tập cha: u({b}) = 2×2 + 4×2 + 2×2 = 16 "
        "(b có trong T3, T4, T5), nhưng u({b,d}) = 30. Thêm item làm utility "
        "TĂNG, vì utility của item mới được cộng vào.",
        "Thêm item làm utility GIẢM: u({b,d,f}) < u({b,d}), vì {b,d,f} chỉ còn "
        "trong T3 (f chỉ có ở T3), nên mất hẳn phần đóng góp của T4.",
    ])
    D.p("Hai lực đối nghịch: thêm item thì cộng thêm utility (đẩy lên), nhưng "
        "đồng thời thu hẹp tập giao dịch chứa itemset (đẩy xuống). Kết quả là "
        "utility không đơn điệu theo bất kỳ chiều nào.", align="justify")
    D.rich([("Hệ quả: ", "b"),
            ("không thể cắt tỉa trực tiếp bằng utility. Nếu cứ cắt nhánh khi "
             "u(X) < minUtil, thuật toán sẽ BỎ SÓT kết quả đúng. Đây là lý do "
             "toàn bộ literature HUIM xoay quanh việc tìm các HÀM CHẶN TRÊN có "
             "tính anti-monotone để cắt tỉa thay cho utility. Tính chất này "
             "được chứng minh hình thức bởi Yao, Hamilton và Butz (SIAM SDM "
             "2004), và được kiểm chứng bằng unit test "
             "test_utility_is_not_anti_monotonic trong bài tìm hiểu.", "")])

    D.h(2, "5.10. Candidate explosion và cây tìm kiếm")
    D.p(f"Một itemset trên n item có 2^n − 1 tập con khác rỗng. Với "
        f"{C.cs['waps_detected_in_train']} AP được phát hiện trong "
        f"trainingData, không gian tìm kiếm có cỡ 2^"
        f"{C.cs['waps_detected_in_train']} — không thể liệt kê.",
        align="justify")
    D.p("Cây tìm kiếm (set-enumeration tree) có dạng: gốc là ∅; mỗi nút là "
        "một itemset; con của nút X là các X ∪ {z} với z lớn hơn mọi phần tử "
        "của X theo một thứ tự toàn phần đã chọn. Nhờ thứ tự này mỗi itemset "
        "xuất hiện đúng một lần. Toàn bộ nghệ thuật của thuật toán HUIM là: "
        "cắt được bao nhiêu nhánh mà vẫn không bỏ sót kết quả.",
        align="justify")

    D.h(2, "5.11. TWU — Transaction Weighted Utilization")
    D.formula("TWU(X) = Σ ( T ∈ g(X) )  TU(T)")
    D.p("Tổng Transaction Utility của mọi giao dịch chứa X.", align="justify")
    D.rich([("Chứng minh trực giác vì sao TWU là chặn trên: ", "b"),
            ("với mọi itemset Y ⊇ X ta có g(Y) ⊆ g(X) (giao dịch chứa Y thì "
             "chứa X). Với mỗi T ∈ g(Y): u(Y,T) ≤ TU(T), vì u(Y,T) là tổng "
             "utility của một TẬP CON các item của T còn TU(T) là tổng của "
             "TOÀN BỘ. Cộng lại:", "")])
    D.formula("u(Y) = Σ(T∈g(Y)) u(Y,T) ≤ Σ(T∈g(Y)) TU(T) ≤ Σ(T∈g(X)) TU(T) "
              "= TWU(X)")
    D.rich([("Và TWU CÓ tính anti-monotone: ", "b"),
            ("X ⊆ Y ⟹ g(Y) ⊆ g(X) ⟹ TWU(Y) ≤ TWU(X). Vậy nếu TWU(X) < minUtil "
             "thì u(Y) < minUtil với mọi Y ⊇ X, nên cắt được cả nhánh một cách "
             "an toàn. Đây là đóng góp của Liu, Liao và Choudhary (PAKDD 2005) "
             "và là nền tảng của mọi thuật toán HUIM sau đó. Tính chất này "
             "được kiểm chứng VÉT CẠN trong "
             "test_twu_is_an_upper_bound_on_utility_of_supersets.", "")])
    D.p("Điểm yếu của TWU: đây là chặn trên RẤT LỎNG, vì TU(T) tính cả những "
        "item không nằm trong itemset ta quan tâm. Toàn bộ tiến bộ từ 2005 đến "
        "EFIM là làm cho chặn trên này chặt hơn.", align="justify")
    D.page_break()


# ===========================================================================
def ch6(D: Doc, C) -> None:
    D.h(1, "6. Các thuật toán HUIM")

    D.h(2, "6.1. Two-Phase (Liu, Liao & Choudhary — PAKDD 2005)")
    D.bullets([
        "Pha 1: tìm mọi itemset có TWU ≥ minUtil. Vì TWU anti-monotone nên "
        "dùng được chiến lược kiểu Apriori. Kết quả là tập ỨNG VIÊN.",
        "Pha 2: quét lại cơ sở dữ liệu, tính u(X) chính xác cho từng ứng viên, "
        "loại những cái không đạt.",
        "Điểm yếu: tập ứng viên pha 1 có thể lớn gấp nhiều lần tập kết quả "
        "thật, vì TWU quá lỏng; và pha 2 phải quét lại toàn bộ database.",
    ])

    D.h(2, "6.2. UP-Growth (Tseng, Wu, Shie & Yu — ACM SIGKDD 2010; bản "
           "journal UP-Growth+ trên IEEE TKDE 2013)")
    D.p("Hướng tiếp cận: GIẢM SỐ ỨNG VIÊN. Dùng cấu trúc UP-Tree theo tinh "
        "thần FP-Growth, kèm bốn chiến lược loại item không hứa hẹn ngay trong "
        "lúc xây cây:", align="justify")
    D.bullets([
        "DGU — Discarding Global Unpromising items: loại item có TWU < minUtil "
        "khi xây cây toàn cục.",
        "DGN — Discarding Global Node utilities: bỏ utility của các node tổ "
        "tiên khỏi ước lượng.",
        "DLU — Discarding Local Unpromising items: tương tự DGU ở mức cây con.",
        "DLN — Discarding Local Node utilities: tương tự DGN ở mức cây con.",
    ])
    D.p("Vẫn là thuật toán hai pha: vẫn phải xác minh lại ứng viên.",
        align="justify")

    D.h(2, "6.3. HUI-Miner (Liu & Qu — ACM CIKM 2012)")
    D.p("Hướng tiếp cận: BỎ HẲN PHA SINH ỨNG VIÊN. Đây là bước ngoặt.",
        align="justify")
    D.rich([("Cấu trúc utility-list. ", "b"),
            ("Mỗi itemset X được gắn một danh sách các bộ ba:", "")])
    D.formula("(tid, iutil, rutil)")
    D.bullets([
        "tid: mã giao dịch chứa X.",
        "iutil = u(X, T): utility của chính X trong giao dịch đó.",
        "rutil = remaining utility: tổng utility của các item trong T đứng SAU "
        "mọi item của X theo thứ tự đã chọn — những item còn có thể được thêm "
        "vào để mở rộng X.",
    ])
    D.rich([("Chặn trên: ", "b"),
            ("Σ iutil + Σ rutil trên toàn danh sách. Lý do đây là chặn trên: "
             "bất kỳ mở rộng nào của X cũng chỉ có thể thêm các item nằm trong "
             "phần 'remaining', nên utility của mở rộng không thể vượt quá "
             "(utility hiện có) + (toàn bộ utility còn lại). Nếu chặn trên này "
             "< minUtil, cắt nhánh ngay — KHÔNG cần quét lại database.", "")])
    D.p("Utility-list của X ∪ {z} được tạo bằng cách giao hai utility-list của "
        "X và của {z}, nên không cần sinh ứng viên rồi xác minh. Đây gọi là "
        "thuật toán MỘT PHA.", align="justify")
    D.p("Fournier-Viger và cộng sự (2014) bổ sung cho hướng này cơ chế EUCP "
        "(Estimated Utility Co-occurrence Pruning) trong thuật toán FHM: dùng "
        "một bảng tra cứu theo cặp item để loại sớm những cặp không thể cùng "
        "tạo nên HUI.", align="justify")
    D.p("Điểm yếu của hướng utility-list: phải tạo và lưu một utility-list cho "
        "MỖI itemset được xét. Với cây tìm kiếm lớn, chi phí bộ nhớ và chi phí "
        "giao danh sách trở thành nút cổ chai — và đó chính là chỗ EFIM cải "
        "tiến.", align="justify")
    D.page_break()


# ===========================================================================
def ch6b(D: Doc, C) -> None:
    D.h(1, "6.4. EFIM — thuật toán chính của bài tìm hiểu")
    D.p("Zida, Fournier-Viger, Lin, Wu & Tseng, Knowledge and Information "
        "Systems, vol. 51, no. 2, pp. 595–625, DOI 10.1007/s10115-016-0986-0. "
        "EFIM thay utility-list bằng phép chiếu cơ sở dữ liệu, và đưa ra hai "
        "chặn trên chặt hơn TWU.", align="justify")

    D.h(2, "6.4.1. Search space và item ordering")
    D.p("EFIM duyệt cây set-enumeration theo chiều sâu (depth-first). Thứ tự "
        "toàn phần ≺ giữa các item là THỨ TỰ TWU TĂNG DẦN. Lý do: item có TWU "
        "nhỏ được xét trước nên các nhánh ít hứa hẹn nằm ở phần nông của cây "
        "và bị cắt sớm, còn item TWU lớn bị đẩy xuống sâu nơi phép chiếu đã "
        "làm cơ sở dữ liệu nhỏ lại. Với một nút α (prefix), tập mở rộng E(α) "
        "gồm các item lớn hơn mọi phần tử của α theo ≺.", align="justify")

    D.h(2, "6.4.2. Remaining utility")
    D.formula("re(α, T) = Σ ( i ∈ T,  i ≻ max(α) )  u(i, T)",
              "Tổng utility của các item trong T đứng sau α theo thứ tự ≺ — "
              "tức phần còn có thể thêm vào.")

    D.h(2, "6.4.3. Local utility — chặn trên thứ nhất")
    D.formula("lu(α, z) = Σ ( T ∈ g(α ∪ {z}) ) [ u(α, T) + re(α, T) ]")
    D.rich([("Ý nghĩa và cách dùng: ", "b"),
            ("lu(α,z) là chặn trên cho utility của MỌI itemset vừa chứa "
             "α ∪ {z} vừa là mở rộng của α. Nếu lu(α,z) < minUtil thì item z "
             "bị LOẠI KHỎI TOÀN BỘ CÂY CON của α. Tập item còn lại gọi là "
             "Secondary(α).", "")])
    D.rich([("Liên kết với lý thuyết chương 5: ", "b"),
            ("tại nút gốc α = ∅ ta có u(∅,T) = 0 và re(∅,T) = TU(T), nên "
             "lu(∅,z) = Σ(T ∋ z) TU(T) = TWU(z). Vậy local utility chính là "
             "TWU được tổng quát hoá cho một prefix bất kỳ, và cắt tỉa bằng "
             "TWU chỉ là trường hợp riêng tại gốc. Mã nguồn của bài tìm hiểu ghi rõ "
             "nhận xét này (src/huim/efim.py).", "")])

    D.h(2, "6.4.4. Subtree utility — chặn trên thứ hai")
    D.formula("su(α, z) = Σ ( T ∈ g(α ∪ {z}) ) [ u(α,T) + u(z,T) "
              "+ Σ ( i ∈ T, i ≻ z )  u(i,T) ]")
    D.rich([("Ý nghĩa và cách dùng: ", "b"),
            ("su(α,z) là chặn trên cho utility của mọi itemset trong CÂY CON "
             "gốc tại α ∪ {z}. Nếu su(α,z) < minUtil thì không cần BƯỚC VÀO "
             "nhánh đó. Tập item vượt ngưỡng gọi là Primary(α).", "")])
    D.p("So sánh hai chặn: su chặt hơn lu, vì su chỉ cộng utility của các item "
        "đứng SAU z, còn lu cộng utility của tất cả item còn lại kể cả những "
        "item đứng trước z. Hai chặn phục vụ hai việc khác nhau: su quyết định "
        "'có vào nhánh này không', lu quyết định 'item nào còn được phép xuất "
        "hiện ở bất kỳ đâu trong cây con này'.", align="justify")
    D.table(pd.DataFrame([
        {"Chặn trên": "TWU", "Phạm vi cắt tỉa": "Toàn bộ nhánh chứa item",
         "Độ chặt": "Lỏng nhất",
         "Dùng ở": "Gốc cây (= local utility tại ∅)"},
        {"Chặn trên": "Local utility lu(α,z)",
         "Phạm vi cắt tỉa": "Loại item z khỏi cả cây con của α",
         "Độ chặt": "Chặt hơn TWU", "Dùng ở": "Mọi nút → Secondary(α)"},
        {"Chặn trên": "Subtree utility su(α,z)",
         "Phạm vi cắt tỉa": "Không bước vào cây con α ∪ {z}",
         "Độ chặt": "Chặt nhất", "Dùng ở": "Mọi nút → Primary(α)"},
    ]), "Ba chặn trên và vai trò khác nhau của chúng", font_pt=9,
        widths=[1.5, 2.0, 1.1, 1.8])

    D.h(2, "6.4.5. High-utility database projection")
    D.p("Khi đi xuống nhánh α ∪ {i}, EFIM không tạo cấu trúc mới cho itemset "
        "mà CHIẾU cơ sở dữ liệu: mỗi giao dịch chỉ giữ lại các item đứng sau i "
        "theo ≺, cộng thêm một số vô hướng prefix_utility = u(α ∪ {i}, T). Nhờ "
        "vậy thông tin về phần prefix được nén thành MỘT CON SỐ thay vì một "
        "danh sách — đó là khác biệt cốt lõi so với HUI-Miner.",
        align="justify")

    D.h(2, "6.4.6. Transaction merging")
    D.p("Sau vài lần chiếu, nhiều giao dịch trở nên GIỐNG NHAU HOÀN TOÀN (cùng "
        "tập item còn lại). EFIM hợp chúng thành một giao dịch duy nhất, cộng "
        "utility theo từng vị trí. Phép hợp này chính xác với utility vì "
        "u(X, giao dịch hợp) = Σ u(X, từng giao dịch gốc).", align="justify")
    D.p("Bản cài đặt của bài tìm hiểu cộng thêm một trường đếm số giao dịch gốc đã "
        "được hợp, nhờ đó support cũng được bảo toàn chính xác — điều cần "
        "thiết vì chương 8 dùng support khi xếp hạng AP. Có unit test riêng "
        "cho tính chất này (test_support_is_exact_despite_transaction_merging).",
        align="justify")

    D.h(2, "6.4.7. Fast Utility Counting")
    D.p("Để tính lu và su cho TẤT CẢ item mở rộng, EFIM dùng hai mảng "
        "utility-bin đánh chỉ số theo item và MỘT lần quét duy nhất cho mỗi "
        "giao dịch. Với giao dịch có prefix utility pu và các item "
        "e₁ ≺ … ≺ eₘ mang utility u₁ … uₘ:", align="justify")
    D.formula("lu_bin[e_k]  +=  pu + Σ(j = 1..m) u_j      (giống nhau mọi k)")
    D.formula("su_bin[e_k]  +=  pu + Σ(j = k..m) u_j")
    D.p("Một lần quét NGƯỢC từ cuối giao dịch về đầu, cộng dồn biến 'rest', là "
        "đủ để điền cả hai mảng. Chi phí tuyến tính theo kích thước cơ sở dữ "
        "liệu đã chiếu — đó là lý do cái tên 'Fast'.", align="justify")

    D.h(2, "6.4.8. Ví dụ tính tay — để giải thích lại được với giảng viên")
    D.p("Dùng cơ sở dữ liệu ví dụ ở mục 5.1 với minUtil = 30.",
        align="justify")
    D.table(pd.DataFrame([
        {"Bước": "1. Tính TU từng giao dịch",
         "Kết quả": "TU(T1..T5) = 8, 27, 30, 20, 11. Tổng = 96."},
        {"Bước": "2. Tính TWU từng item",
         "Kết quả": "TWU(a) = T1+T2+T3 = 65;  TWU(b) = T3+T4+T5 = 61;  "
                    "TWU(c) = cả 5 = 96;  TWU(d) = T1+T3+T4 = 58;  "
                    "TWU(e) = T2+T3+T4+T5 = 88;  TWU(f) = T3 = 30;  "
                    "TWU(g) = T2+T5 = 38."},
        {"Bước": "3. Cắt tỉa ở gốc, dùng lu(∅,·) = TWU",
         "Kết quả": "Với minUtil = 30, MỌI item đều có TWU ≥ 30 (kể cả f với "
                    "TWU = 30), nên KHÔNG item nào bị loại. Thực nghiệm xác "
                    "nhận điều này: unit test test_pruning_actually_happens "
                    "kiểm tra 7/7 item còn lại ở minUtil = 30, và chỉ khi tăng "
                    "lên minUtil = 40 thì f mới bị loại."},
        {"Bước": "4. Thứ tự ≺ = TWU tăng dần",
         "Kết quả": "f (30) ≺ g (38) ≺ d (58) ≺ b (61) ≺ a (65) ≺ e (88) "
                    "≺ c (96)."},
        {"Bước": "5. Chọn Primary(∅) bằng su",
         "Kết quả": "Chỉ các item có su(∅,z) ≥ 30 được mở nhánh; các nhánh "
                    "còn lại không bị bước vào."},
        {"Bước": "6. Đi sâu: chiếu và hợp giao dịch",
         "Kết quả": "Ví dụ nhánh b: chiếu lên b cho T3, T4, T5 với "
                    "prefix_utility lần lượt 4, 8, 4. Tiếp tục xuống d: chỉ "
                    "T3 và T4 còn chứa d → u({b,d}) = (4+12) + (8+6) = 30 "
                    "≥ 30 → XUẤT KẾT QUẢ."},
        {"Bước": "7. Kết quả cuối",
         "Kết quả": "7 HUI, trong đó {b,d} với u = 30 và {b,c,d,e} với u = 40. "
                    "Đối chiếu với brute-force: trùng khớp hoàn toàn."},
    ]), "Vết chạy EFIM trên ví dụ chuẩn với minUtil = 30", font_pt=9,
        widths=[1.7, 4.3])
    D.page_break()


# ===========================================================================
def ch7(D: Doc, C) -> None:
    D.h(1, "7. Tại sao chọn EFIM?")
    D.p("Lựa chọn phải dựa trên literature, không dựa trên cảm tính, và quan "
        "trọng hơn: không chỉ dựa trên bài báo của chính tác giả EFIM.",
        align="justify")

    D.h(2, "7.1. Căn cứ chính: một đánh giá thực nghiệm độc lập")
    D.rich([("Zhang, Almpanidis, Wang và Liu, ", ""),
            ('"An empirical evaluation of high utility itemset mining '
             'algorithms"', "i"),
            (", Expert Systems with Applications, vol. 101, pp. 91–115, 2018, "
             "DOI 10.1016/j.eswa.2018.02.008.", "")])
    D.rich([("Đây là đánh giá của BÊN THỨ BA — không do nhóm tác giả EFIM "
             "viết. ", "b"),
            ("Việc dựa vào một benchmark độc lập thay vì dựa vào phần thực "
             "nghiệm trong bài báo đề xuất thuật toán chính là lý do EFIM được "
             "chọn, chứ không phải HUI-Miner hay UP-Growth. Một bài báo đề "
             "xuất thuật toán luôn có động lực trình bày thuật toán của mình "
             "trong điều kiện thuận lợi nhất.", "")])

    D.h(2, "7.2. Căn cứ kỹ thuật từ chính bài báo EFIM")
    D.bullets([
        "Hai chặn trên chặt hơn TWU (local utility, subtree utility) → cắt tỉa "
        "mạnh hơn các thế hệ trước.",
        "Không tạo cấu trúc dữ liệu riêng cho từng itemset (khác "
        "HUI-Miner/FHM) → chi phí bộ nhớ không tỷ lệ với số itemset được xét.",
        "Transaction merging → khai thác sự trùng lặp sau khi chiếu.",
        "Fast Utility Counting → tính cả hai chặn trong thời gian tuyến tính.",
        "Bài báo báo cáo EFIM nhanh hơn tới nhiều bậc độ lớn và tốn ít bộ nhớ "
        "hơn UP-Growth+, HUI-Miner, FHM và các thuật toán khác.",
    ])

    D.h(2, "7.3. Hai lý do riêng cho bộ dữ liệu này")
    D.rich([("Lý do 1 — transaction merging có đất dùng. ", "b"),
            (f"Audit tìm thấy {nf(C.tr['duplicate_rows_wap_only'])} dòng huấn "
             f"luyện có vector WAP {C.tr['n_wap_columns_detected']} chiều "
             "trùng khít một dòng khác. Hơn nữa, vì dữ liệu rất thưa, các giao "
             "dịch sau khi chiếu va vào nhau rất thường xuyên. Số liệu thực đo "
             "được báo cáo ở chương 12.", "")])
    D.rich([("Lý do 2 — cơ sở dữ liệu RỘNG chứ không SÂU. ", "b"),
            (f"{C.cs['waps_detected_in_train']} item nhưng độ dài giao dịch "
             f"trung bình chỉ "
             f"{C.tr['not_detected_probe']['detections_per_fingerprint']['mean']}"
             ". Với hình dạng này, chi phí bộ nhớ của hướng utility-list (một "
             "danh sách cho mỗi itemset được xét) đáng lo hơn chi phí quét "
             "database. EFIM được thiết kế đúng cho tình huống đó.", "")])
    D.p("[OUR INTERPRETATION] Hai lý do này là suy luận của bài tìm hiểu dựa trên "
        "tính chất dữ liệu, không phải phát biểu từ bài báo.", size=10,
        italic=True)

    D.h(2, "7.4. Cài đặt: vì sao không dùng SPMF?")
    D.p("SPMF (Fournier-Viger và cộng sự, 2016) là thư viện tham chiếu và lẽ "
        "ra nên được ưu tiên. SPMF là thư viện Java và môi trường thực nghiệm "
        "không có JVM; vì vậy EFIM được cài đặt lại bằng Python.",
        align="justify")
    D.rich([("Hệ quả về phương pháp, và cách xử lý: ", "b"),
            ("khi không thể dựa vào một binary đã được cộng đồng kiểm chứng, "
             "bản cài đặt phải TỰ CHỨNG MINH tính đúng. Bài tìm hiểu làm điều đó bằng "
             "cách đối chiếu với một ORACLE brute-force độc lập "
             "(src/huim/brute_force.py) — module này cố tình không có bất kỳ "
             "cắt tỉa nào, nó tính thẳng từ định nghĩa. Chi tiết ở mục 11.2. "
             "Không có dòng nào của UJIIndoorLoc được chạy trước khi toàn bộ "
             "kiểm thử này đạt.", "")])
    D.page_break()


# ===========================================================================
def ch8(D: Doc, C) -> None:
    D.h(1, "8. Mô hình hóa HUIM trong IPS")
    D.p("Đây là chương quan trọng nhất của báo cáo, và cũng là chương phải "
        "trung thực nhất, vì nó là phần KHÔNG lấy từ literature.",
        align="justify")

    D.h(2, "8.1. Phân biệt rành mạch hai loại nội dung")
    D.table(pd.DataFrame([
        {"Thành phần": "Định nghĩa HUIM (item, itemset, transaction, q, p, u, "
                       "TU, TWU, minUtil, HUI)",
         "Nguồn": "A. LITERATURE",
         "Tham chiếu": "Yao et al. 2004; Liu et al. 2005; Gan et al., IEEE "
                       "TKDE 2021"},
        {"Thành phần": "Thuật toán EFIM: local utility, subtree utility, "
                       "projection, merging, Fast Utility Counting",
         "Nguồn": "A. LITERATURE", "Tham chiếu": "Zida et al. 2017"},
        {"Thành phần": "Mutual information làm thước đo khả năng phân biệt của "
                       "một AP",
         "Nguồn": "A. LITERATURE",
         "Tham chiếu": "Chen et al., IEEE TKDE 2006; Song et al., ISPRS IJGI "
                       "2016"},
        {"Thành phần": "k-NN làm baseline định vị",
         "Nguồn": "A. LITERATURE",
         "Tham chiếu": "Bahl & Padmanabhan 2000; Torres-Sospedra et al., "
                       "ESWA 2015"},
        {"Thành phần": "Ánh xạ fingerprint → transaction; RSSI → internal "
                       "utility; mức phân biệt của AP → external utility",
         "Nguồn": "B. ĐỀ XUẤT CỦA BÀI TÌM HIỂU", "Tham chiếu": "—"},
        {"Thành phần": "Quy tắc xếp hạng HUI → tập AP được chọn",
         "Nguồn": "B. ĐỀ XUẤT CỦA BÀI TÌM HIỂU", "Tham chiếu": "—"},
    ]), "Phần nào của phương pháp lấy từ literature, phần nào là đề xuất của "
        "bài tìm hiểu", font_pt=9, widths=[2.5, 1.3, 2.2])
    D.rich([("Phát biểu bắt buộc. ", "b"),
            ("Trong phạm vi literature review đã kiểm chứng, chưa tìm thấy "
             "bằng chứng đủ mạnh để coi ánh xạ HUIM → UJIIndoorLoc dưới đây là "
             "phương pháp chuẩn hóa đã được công nhận; do đó phần này được xem "
             "là mô hình áp dụng/đề xuất thực nghiệm của bài tìm hiểu.", "i")])

    D.h(2, "8.2. Bảng ánh xạ khái niệm HUIM ↔ IPS")
    D.table(pd.DataFrame([
        {"Khái niệm HUIM": "Transaction T",
         "Khái niệm IPS": "Một fingerprint Wi-Fi (một dòng CSV)",
         "Ghi chú": "Ánh xạ tự nhiên nhất: một lần quét = một tập hợp những gì "
                    "nhìn thấy cùng lúc"},
        {"Khái niệm HUIM": "Item i",
         "Khái niệm IPS": f"Một Access Point (WAP001 … "
                          f"WAP{C.tr['n_wap_columns_detected']})",
         "Ghi chú": "AP không được phát hiện (giá trị 100) ⟹ item KHÔNG thuộc "
                    "transaction"},
        {"Khái niệm HUIM": "Internal utility q(i,T)",
         "Khái niệm IPS": "Cường độ RSSI đã chuẩn hoá",
         "Ghi chú": "Phụ thuộc cả AP và fingerprint — đúng vai của q"},
        {"Khái niệm HUIM": "External utility p(i)",
         "Khái niệm IPS": "Mức độ quan trọng / khả năng phân biệt vị trí của AP",
         "Ghi chú": "Thuộc tính của riêng AP, không đổi giữa các fingerprint — "
                    "đúng vai của p"},
        {"Khái niệm HUIM": "Itemset X", "Khái niệm IPS": "Một nhóm AP",
         "Ghi chú": "—"},
        {"Khái niệm HUIM": "u(X)",
         "Khái niệm IPS": "Tổng 'độ hữu ích' của nhóm AP trên toàn bộ khảo sát",
         "Ghi chú": "Theo ĐỊNH NGHĨA utility của bài tìm hiểu, không phải một đại "
                    "lượng vật lý"},
        {"Khái niệm HUIM": "High Utility Itemset",
         "Khái niệm IPS": "Nhóm AP có tổng utility vượt ngưỡng",
         "Ghi chú": "KHÔNG đồng nghĩa 'nhóm đặc trưng tốt cho phân loại' — xem "
                    "chương 13 và 15"},
        {"Khái niệm HUIM": "minUtil",
         "Khái niệm IPS": "Quyết định nhóm AP đồng xuất hiện lớn đến đâu mới "
                          "được coi là một mẫu",
         "Ghi chú": "KHÔNG phải núm điều chỉnh độ chính xác — chương 15, Quan "
                    "sát 1"},
    ]), "Ánh xạ HUIM ↔ IPS do bài tìm hiểu đề xuất", font_pt=9,
        widths=[1.5, 2.1, 2.4])

    D.h(2, "8.3. Vấn đề lớn phải giải quyết")
    D.p("Một cơ sở dữ liệu fingerprint Wi-Fi KHÔNG có hai thứ mà HUIM đòi:",
        align="justify")
    D.bullets([
        "Không có 'số lượng' theo nghĩa giỏ hàng. Một AP không được 'mua 3 "
        "cái'. Thứ có sẵn là RSSI — một đại lượng vật lý, ÂM, theo thang dBm.",
        "Không có 'lợi nhuận' của một AP. Không có bảng giá nào gắn với "
        "WAP001.",
    ])
    D.p("Vì vậy q và p phải được ĐỊNH NGHĨA. Đây là một quyết định mô hình hoá "
        "của bài tìm hiểu, và nó là nguồn gốc của cả đóng góp lẫn hạn chế lớn nhất "
        "của nghiên cứu.", align="justify")

    D.h(2, "8.4. Internal utility: từ RSSI âm sang số nguyên dương")
    D.p("Ba ràng buộc phải thoả đồng thời:", align="justify")
    D.bullets([
        "EFIM và mọi chặn trên TWU / lu / su yêu cầu utility DƯƠNG. RSSI thì "
        "âm. (Bản cài đặt kiểm tra điều kiện này và báo lỗi nếu bị vi phạm.)",
        "Giá trị 100 nghĩa là 'không phát hiện', phải ánh xạ thành 'item không "
        "thuộc transaction', KHÔNG phải thành một utility lớn. Đây là cái bẫy "
        "nguy hiểm nhất: 100 là giá trị LỚN NHẤT trong ma trận nhưng mang "
        "nghĩa KHÔNG CÓ TÍN HIỆU.",
        "Phép biến đổi phải được fit TRÊN trainingData, không được dùng "
        "validationData.",
    ])
    pr = C.huim["preprocessor"]
    D.formula("q(i,T) = round( 1 + (RSSI(i,T) − RSSI_min) / "
              "(RSSI_max − RSSI_min) × (Q_MAX − 1) )")
    D.p(f"với RSSI_min = {pr['rssi_min_train']:g} dBm và "
        f"RSSI_max = {pr['rssi_max_train']:g} dBm lấy từ các giá trị PHÁT HIỆN "
        f"ĐƯỢC trên trainingData ({nf(pr['fitted_on_n_rows'])} dòng), và "
        f"Q_MAX = {pr['q_max']}. Nếu AP không được phát hiện thì item không "
        f"thuộc transaction (q không được định nghĩa).", align="justify")
    D.p(f"Kết quả: tín hiệu yếu nhất có thể ({pr['rssi_min_train']:g} dBm) "
        f"→ q = 1; tín hiệu mạnh nhất ({pr['rssi_max_train']:g} dBm) "
        f"→ q = {pr['q_max']}; không phát hiện → item vắng mặt. Giá trị 0 được "
        f"giữ riêng cho 'không có thông tin', không bao giờ lẫn với 'tín hiệu "
        f"rất yếu'.", align="justify")
    D.p(f"[FACT FROM DATA] Phạm vi fit được xác nhận trùng khớp phạm vi tài "
        f"liệu [{pr['rssi_doc_min']}, {pr['rssi_doc_max']}] dBm, và hàm "
        f"fit_preprocessor báo lỗi nếu không trùng. Phạm vi RSSI của "
        f"validationData nằm hẳn bên trong phạm vi training, nên phép chuẩn "
        f"hoá không bao giờ phải ngoại suy.", size=10, italic=True)
    D.p("Cả ba Utility Model dùng CHUNG internal utility này. Nhờ vậy ablation "
        "cô lập đúng một biến: ý nghĩa của external utility.", align="justify")
    D.figure(FIGURES / "fig14_mutual_information_vs_support.png",
             "Khả năng phân biệt của từng AP (trái) và quan hệ giữa số lần "
             "được phát hiện và lượng thông tin mang lại (phải). Hình bên phải "
             "là cơ sở thực nghiệm cho khẳng định 'AP phổ biến ≠ AP hữu ích'")
    D.page_break()
