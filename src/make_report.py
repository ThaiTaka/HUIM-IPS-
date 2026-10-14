"""PHASE L - build report/HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx.

Hard rule enforced by construction: this script contains no experimental
numbers. Everything quantitative is read at build time from

    results/data_summary.json                 (PHASE A)
    results/huim_summary.json                 (PHASE H)
    results/metrics/huim_runs.csv             (PHASE H)
    results/metrics/ips_results.csv           (PHASE I)
    results/ips_summary.json                  (PHASE I)
    results/reverse_thinking_observations.json(PHASE K)
    results/tables/ablation_study.csv         (PHASE J)
    research/papers_table.csv                 (PHASE B)
    figures/*.png                             (PHASE J)

If a file is missing the build fails loudly rather than emitting prose with
holes in it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_builder import Doc
from utils import (FIGURES, METRICS, REPORT, RESEARCH, RESULTS, TABLES,
                   dump_json, get_logger, load_json)

LOG = get_logger("report", "report.log")

MODEL_VN = {"A_signal": "Model A — Signal utility",
            "B_discriminative": "Model B — Discriminative utility",
            "C_rare_discriminative": "Model C — Rare-discriminative utility"}


def pc(x, d=2):
    return f"{float(x)*100:.{d}f}%"


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


class Ctx:
    """All experiment outputs, loaded once."""

    def __init__(self) -> None:
        need = {
            "audit": RESULTS / "data_summary.json",
            "huim": RESULTS / "huim_summary.json",
            "ips": RESULTS / "ips_summary.json",
            "obs": RESULTS / "reverse_thinking_observations.json",
        }
        for k, p in need.items():
            if not p.exists():
                raise FileNotFoundError(f"{p} missing - run the pipeline first")
            setattr(self, k, load_json(p))
        cp = RESULTS / "coordinate_system_verification.json"
        self.coord = load_json(cp) if cp.exists() else None
        cc = METRICS / "ips_cost.csv"
        self.COST = pd.read_csv(cc) if cc.exists() else None
        self.H = pd.read_csv(METRICS / "huim_runs.csv")
        self.I = pd.read_csv(METRICS / "ips_results.csv")
        self.AB = pd.read_csv(TABLES / "ablation_study.csv")
        self.PAP = pd.read_csv(RESEARCH / "papers_table.csv")
        self.tr = self.audit["training"]
        self.va = self.audit["validation"]
        self.cs = self.audit["cross_split"]
        self.env = self.audit["environment"]
        self.base = self.I[self.I["condition"] == "baseline_all_520"].iloc[0]
        b = self.I[self.I["condition"] == "baseline_detected_465"]
        self.base465 = b.iloc[0] if len(b) else None
        self.cfg = self.ips["protocol"]["frozen_knn_config"]
        self.o = self.obs
        # PHASE I3 (positioning optimisation) is optional: its section is
        # written only when its result files exist
        po = RESULTS / "positioning_optimisation.json"
        self.PO = load_json(po) if po.exists() else None
        self.PAB = (pd.read_csv(METRICS / "positioning_ablation.csv")
                    if self.PO else None)
        self.PCN = (pd.read_csv(METRICS / "positioning_conditions.csv")
                    if self.PO else None)


# ===========================================================================
def cover(D: Doc, C: Ctx) -> None:
    D.title_page([
        ("BÁO CÁO TÌM HIỂU THUẬT TOÁN", 13, False),
        ("HỌC PHẦN CAO HỌC — KHOA CÔNG NGHỆ THÔNG TIN", 12, False),
        ("", 12, False), ("", 12, False),
        ("HIGH UTILITY ITEMSET MINING", 22, True),
        ("TRONG INDOOR POSITIONING SYSTEM", 22, True),
        ("", 12, False),
        ("Thực nghiệm trên UJIIndoorLoc", 15, False),
        ("", 12, False), ("", 12, False),
        ("Khai thác tập mục hữu ích cao (HUIM) như một phương pháp",
         12, False),
        ("lựa chọn nhóm Access Point cho định vị trong nhà dựa trên",
         12, False),
        ("vân tay Wi-Fi", 12, False),
        ("", 12, False),
        ("Mức độ: BÀI TÌM HIỂU — tìm hiểu thuật toán, mô hình hoá áp dụng",
         11, True),
        ("cho IPS, cài đặt và đánh giá trên UJIIndoorLoc.", 11, True),
        ("Đây không phải đồ án tốt nghiệp hay luận văn.", 11, True),
        ("", 12, False), ("", 12, False),
        (f"Thuật toán chính: EFIM (Zida et al., 2017)", 12, False),
        (f"Dữ liệu: UJIIndoorLoc — {nf(C.tr['n_rows'])} bản ghi huấn luyện, "
         f"{nf(C.va['n_rows'])} bản ghi kiểm định", 11, False),
        (f"{C.tr['n_wap_columns_detected']} cột WAP", 11, False),
        ("", 12, False), ("", 12, False),
        ("Toàn bộ số liệu trong báo cáo này được sinh tự động từ log thực "
         "nghiệm", 10, False),
        ("(results/, figures/); không có số liệu nào được nhập tay.", 10, False),
    ])

    D.h(1, "Mục lục")
    D.toc_field()
    D.p("Nếu mở bằng công cụ không hỗ trợ field TOC, danh sách chương như sau:",
        size=11)
    D.bullets([
        "1. Tôi cần biết gì trước khi bắt đầu?",
        "2. Indoor Positioning System (IPS)",
        "3. Bộ dữ liệu UJIIndoorLoc",
        "4. Frequent Itemset Mining",
        "5. High Utility Itemset Mining",
        "6. Các thuật toán HUIM",
        "7. Tại sao chọn EFIM?",
        "8. Mô hình hóa HUIM trong IPS",
        "9. Utility Model A — Signal utility",
        "10. Utility Model B — Discriminative utility (và Model C)",
        "11. Thiết kế thực nghiệm",
        "12. Kết quả HUIM",
        "13. Kết quả IPS",
        "14. Ablation study",
        "15. Phân tích theo tư duy ngược",
        "16. Hạn chế",
        "17. Kết luận",
        "18. Hướng phát triển",
        "Tài liệu tham khảo",
        "Phụ lục A — Những câu tôi phải trả lời được khi cô hỏi",
    ])
    D.page_break()


# ===========================================================================
def ch1(D: Doc, C: Ctx) -> None:
    D.h(1, "1. Tôi cần biết gì trước khi bắt đầu?")
    D.p("Chương này viết cho người chưa từng tiếp xúc với cả HUIM lẫn IPS. "
        "Mục tiêu là sau khi đọc xong, bạn hiểu chính xác bài tìm hiểu đang làm gì, "
        "và quan trọng hơn: đang KHÔNG làm gì.", align="justify")

    D.h(2, "1.1. Bài tìm hiểu này giải quyết việc gì?")
    D.p("Có hai thế giới tách biệt:", align="justify")
    D.bullets([
        "Thế giới thứ nhất — Data mining: HUIM (High Utility Itemset Mining) "
        "là bài toán tìm các nhóm mặt hàng mang lại tổng giá trị cao trong một "
        "cơ sở dữ liệu giao dịch. Nó sinh ra từ bài toán giỏ hàng siêu thị.",
        "Thế giới thứ hai — Định vị trong nhà: IPS (Indoor Positioning System) "
        "cần xác định bạn đang ở toà nhà nào, tầng nào, dựa trên cường độ tín "
        "hiệu Wi-Fi mà điện thoại nhìn thấy.",
    ])
    D.rich([("Câu hỏi của bài tìm hiểu: ", "b"),
            ("liệu có thể dùng công cụ của thế giới thứ nhất để giúp thế giới "
             "thứ hai bớt đi một vấn đề cụ thể — số lượng đặc trưng quá "
             "lớn? Bộ dữ liệu UJIIndoorLoc có ", ""),
            (f"{C.tr['n_wap_columns_detected']} cột WAP", "b"),
            (". Mỗi cột là một Access Point. Nếu HUIM có thể chỉ ra rằng chỉ "
             "một nhóm nhỏ trong số đó là thực sự cần thiết, hệ thống định vị "
             "sẽ nhẹ hơn rất nhiều.", "")])

    D.h(2, "1.2. Ba từ phải hiểu ngay")
    D.table(pd.DataFrame([
        {"Thuật ngữ": "Fingerprint (vân tay Wi-Fi)",
         "Nghĩa": "Một lần quét Wi-Fi tại một vị trí: danh sách các AP nhìn "
                  "thấy kèm cường độ tín hiệu của từng AP. Trong UJIIndoorLoc, "
                  "mỗi dòng CSV là một fingerprint."},
        {"Thuật ngữ": "RSSI",
         "Nghĩa": "Received Signal Strength Indicator — cường độ tín hiệu, đo "
                  "bằng dBm. Giá trị âm; càng gần 0 càng mạnh. Trong bộ dữ "
                  "liệu này phạm vi là −104 dBm (rất yếu) đến 0 dBm."},
        {"Thuật ngữ": "Utility (độ hữu ích)",
         "Nghĩa": "Trong HUIM, utility là một con số đo 'giá trị' của một "
                  "item. Với giỏ hàng siêu thị đó thường là lợi nhuận. Với "
                  "Wi-Fi thì KHÔNG có sẵn — bài tìm hiểu phải tự định nghĩa, và đó "
                  "chính là phần đóng góp (và cũng là điểm yếu) của bài tìm hiểu."},
    ]), "Ba thuật ngữ cốt lõi", font_pt=10, widths=[1.6, 4.4])

    D.h(2, "1.3. Phạm vi và mức độ của tài liệu này")
    D.rich([("Đây là một BÀI TÌM HIỂU, không phải đồ án tốt nghiệp hay luận "
             "văn. ", "b"),
            ("Phân biệt này quan trọng vì nó quyết định mức độ của các kết "
             "luận: một bài tìm hiểu có nhiệm vụ HIỂU và KIỂM CHỨNG một "
             "phương pháp trên dữ liệu thật, chứ không có nhiệm vụ đề xuất "
             "phương pháp mới hay chứng minh tính vượt trội.", "")])
    D.p("Nhiệm vụ được giao gồm đúng ba phần:", align="justify")
    D.bullets([
        "Tìm hiểu thuật toán — chương 4 đến chương 7 trình bày từ Frequent "
        "Itemset Mining lên tới EFIM, kèm ví dụ tính tay.",
        "Mô hình hoá áp dụng cho IPS — chương 8 đến chương 10 xây dựng ánh xạ "
        "HUIM ↔ IPS và ba định nghĩa utility.",
        "Cài đặt và đánh giá trên bộ dữ liệu UJIIndoorLoc — chương 11 đến "
        "chương 15.",
    ], numbered=True)
    D.p("Hai tiêu chí đánh giá được đặt ra kèm theo:", align="justify")
    D.bullets([
        "Độ chính xác định vị, với mức tham chiếu 7–8 mét (chương 13, mục "
        "13.1).",
        "Thời gian và bộ nhớ — cả phía khai thác HUIM (chương 12) lẫn phía hệ "
        "thống định vị (mục 13.6).",
    ])
    D.rich([("Hệ quả cho cách đọc tài liệu: ", "b"),
            ("mọi phát biểu ở đây là kết quả của một bài tìm hiểu có kiểm "
             "chứng trên MỘT bộ dữ liệu, với MỘT cấu hình bộ phân loại và các "
             "định nghĩa utility do người làm tự đặt. Không có tuyên bố nào về "
             "tính tổng quát hay tính mới.", "")])

    D.h(2, "1.4. Bài tìm hiểu này KHÔNG khẳng định điều gì")
    D.p("Phần này đặt ngay đầu báo cáo, không đặt ở cuối, vì nó quyết định "
        "cách đọc toàn bộ phần còn lại.", align="justify")
    D.bullets([
        "KHÔNG khẳng định HUIM là phương pháp chuẩn cho IPS. Literature review "
        "(mục 7 của research/literature_review.md) không tìm thấy nghiên cứu "
        "nào áp dụng HUIM trực tiếp cho UJIIndoorLoc hay Wi-Fi fingerprinting. "
        "Vì vậy ánh xạ HUIM → IPS trong bài tìm hiểu là MÔ HÌNH ĐỀ XUẤT, không phải "
        "phương pháp đã được công nhận.",
        "KHÔNG khẳng định đây là nghiên cứu đầu tiên trên thế giới. Không tìm "
        "thấy bằng chứng không đồng nghĩa với không tồn tại; IEEE Xplore và "
        "ACM DL full-text search không truy cập được từ môi trường thực nghiệm.",
        "KHÔNG khẳng định việc chọn Access Point là đóng góp mới. Chọn AP bằng "
        "tiêu chí information-theoretic đã có từ Chen và cộng sự (IEEE TKDE, "
        "2006). Điểm chưa thấy trong literature là dùng một thuật toán HUIM "
        "làm cơ chế chọn.",
        "KHÔNG khẳng định một High Utility Itemset đương nhiên là một nhóm "
        "đặc trưng tốt cho phân loại. Đây là câu hỏi thực nghiệm; chương 13 "
        "và 15 trả lời bằng số liệu, kể cả khi câu trả lời là bất lợi.",
    ])

    D.h(2, "1.5. Phương pháp trình bày: tư duy ngược")
    D.p("Báo cáo không trình bày theo thứ tự Lý thuyết → Định nghĩa → Thuật "
        "toán → Hết. Thứ tự được dùng là:", align="justify")
    D.formula("KẾT QUẢ → QUAN SÁT → TẠI SAO? → CƠ CHẾ THUẬT TOÁN → LÝ THUYẾT "
              "→ KẾT LUẬN")
    D.p("Lý do: các hiện tượng quan sát được trong thực nghiệm (ví dụ: giảm "
        "ngưỡng một chút làm số lượng kết quả tăng vọt) là thứ buộc ta phải "
        "hiểu lý thuyết, chứ không phải ngược lại. Chương 15 là chương áp dụng "
        "triệt để cấu trúc này.", align="justify")
    D.page_break()


# ===========================================================================
def ch2(D: Doc, C: Ctx) -> None:
    D.h(1, "2. Indoor Positioning System (IPS)")

    D.h(2, "2.1. Vì sao GPS không dùng được trong nhà")
    D.p("GPS hoạt động bằng cách đo thời gian truyền tín hiệu từ các vệ tinh "
        "cách Trái Đất khoảng 20.000 km. Tín hiệu đến mặt đất đã rất yếu, và "
        "nó cần đường truyền thẳng (line-of-sight) tới ít nhất 4 vệ tinh. "
        "Trong nhà, bê tông và kim loại hấp thụ cùng phản xạ tín hiệu, nên "
        "GPS hoặc không bắt được, hoặc cho sai số hàng chục mét — vô nghĩa khi "
        "ta cần biết đang ở tầng 2 hay tầng 3.", align="justify")
    D.p("Điểm then chốt: GPS không phân biệt được ĐỘ CAO trong nhà. Mà trong "
        "một toà nhà, biết tầng còn quan trọng hơn biết toạ độ ngang.",
        align="justify")

    D.h(2, "2.2. Wi-Fi fingerprinting")
    D.p("Ý tưởng, do Bahl và Padmanabhan đề xuất trong hệ thống RADAR "
        "(IEEE INFOCOM 2000): thay vì tính toán hình học, hãy coi đây là bài "
        "toán so khớp mẫu.", align="justify")
    D.p("Mỗi vị trí trong toà nhà có một 'vân tay' tín hiệu riêng: tập hợp các "
        "AP nhìn thấy được và cường độ của từng AP. Vân tay này là đặc trưng "
        "của vị trí đó, vì nó phụ thuộc vào khoảng cách tới từng AP và vào các "
        "vật cản ở giữa.", align="justify")

    D.h(3, "Offline phase (pha khảo sát)")
    D.bullets([
        "Đi khắp toà nhà, dừng ở các điểm tham chiếu đã biết vị trí.",
        "Tại mỗi điểm, quét Wi-Fi và ghi lại RSSI của tất cả AP nhìn thấy.",
        "Lưu thành một cơ sở dữ liệu: (vân tay → vị trí).",
        "Đây chính là cách UJIIndoorLoc được tạo ra, và chính là nơi HUIM "
        "được dùng trong bài tìm hiểu này.",
    ])
    D.h(3, "Online phase (pha định vị)")
    D.bullets([
        "Điện thoại người dùng quét Wi-Fi, thu được một vân tay mới.",
        "Hệ thống tìm trong cơ sở dữ liệu những vân tay giống nhất.",
        "Vị trí của các vân tay giống nhất chính là vị trí dự đoán.",
        "Thuật toán tự nhiên nhất ở bước này là k-Nearest Neighbours (k-NN) — "
        "và đó là lý do baseline của bài tìm hiểu dùng k-NN, chứ không phải vì k-NN "
        "cho kết quả đẹp.",
    ])

    D.h(2, "2.3. Vấn đề số chiều — chính là vấn đề bài tìm hiểu nhắm vào")
    D.rich([("Một vân tay trong UJIIndoorLoc là một vector ",
             ""),
            (f"{C.tr['n_wap_columns_detected']} chiều", "b"),
            (", nhưng trung bình chỉ có ", ""),
            (f"{C.tr['not_detected_probe']['detections_per_fingerprint']['mean']}",
             "b"),
            (" AP thực sự được phát hiện. Nghĩa là ", ""),
            (f"{C.tr['not_detected_probe']['share_eq_100_pct']:.2f}%", "b"),
            (" ma trận dữ liệu là giá trị 'không phát hiện'. Giữ cả "
             f"{C.tr['n_wap_columns_detected']} chiều khiến mỗi phép so khớp "
             "k-NN phải tính trên hàng trăm chiều hầu hết là rỗng — vừa tốn "
             "tài nguyên, vừa làm loãng các chiều thực sự mang thông tin "
             "(curse of dimensionality).", "")])
    D.p("Khalajmehrabadi, Gatsis và Akopian (IEEE Communications Surveys & "
        "Tutorials, 2017) coi đây là một vấn đề triển khai độc lập, không chỉ "
        "là chuyện tối ưu nhỏ.", align="justify")
    D.page_break()


# ===========================================================================
def ch3(D: Doc, C: Ctx) -> None:
    tr, va, cs = C.tr, C.va, C.cs
    ptr = tr["not_detected_probe"]
    atr = tr["anomaly_probes"]
    D.h(1, "3. Bộ dữ liệu UJIIndoorLoc")
    D.p("Công bố bởi Torres-Sospedra và cộng sự tại IPIN 2014 "
        "(DOI: 10.1109/IPIN.2014.7275492). Abstract của bài báo mô tả nó là "
        "'the biggest database in the literature' và 'the first publicly "
        "available database' cho bài toán này.", align="justify")

    D.h(2, "3.1. Schema — kiểm tra thực tế, không giả định")
    D.table(pd.DataFrame([
        {"Thuộc tính": "Số dòng", "trainingData": nf(tr["n_rows"]),
         "validationData": nf(va["n_rows"])},
        {"Thuộc tính": "Số cột", "trainingData": tr["n_cols"],
         "validationData": va["n_cols"]},
        {"Thuộc tính": "Số cột WAP (đếm thực tế)",
         "trainingData": tr["n_wap_columns_detected"],
         "validationData": va["n_wap_columns_detected"]},
        {"Thuộc tính": "Đánh số WAP liên tục từ 1",
         "trainingData": str(tr["wap_numbering_dense_1_based"]),
         "validationData": str(va["wap_numbering_dense_1_based"])},
        {"Thuộc tính": "Giá trị thiếu (NaN)",
         "trainingData": tr["missing_values_total"],
         "validationData": va["missing_values_total"]},
        {"Thuộc tính": "Dòng trùng lặp hoàn toàn",
         "trainingData": nf(tr["duplicate_rows_full"]),
         "validationData": va["duplicate_rows_full"]},
        {"Thuộc tính": "Số lớp BUILDINGID_FLOOR",
         "trainingData": tr["joint_building_floor_n_classes"],
         "validationData": va["joint_building_floor_n_classes"]},
    ]), "Schema UJIIndoorLoc đo trực tiếp từ hai file CSV (không hard-code)",
        font_pt=10)
    D.p(f"Chín cột không phải WAP: {', '.join(tr['non_wap_columns'])}. "
        f"Khớp đúng schema tài liệu chính thức mô tả.", size=11)

    D.h(2, "3.2. Giá trị 100 nghĩa là gì? — một giả thuyết đã được kiểm chứng")
    D.p("Rất nhiều tài liệu nói 'giá trị 100 nghĩa là AP không được phát "
        "hiện'. Bài tìm hiểu không chấp nhận điều đó như kiến thức nền; nó được kiểm "
        "chứng bằng ba nguồn độc lập.", align="justify")
    D.rich([("Bằng chứng 1 — tài liệu chính thức. ", "b"),
            ("Mô tả thuộc tính của bộ dữ liệu tại UCI Machine Learning "
             "Repository ghi nguyên văn: ", ""),
            ('"Positive value 100 is used to denote when a WAP was not '
             'detected."', "i"),
            (" và về phạm vi tín hiệu: ", ""),
            ('"Negative integer values ranging -104dBm (extremely poor '
             'signal) to 0dbM."', "i")])
    D.rich([("Bằng chứng 2 — phân bố dữ liệu. ", "b"),
            (f"Trong {nf(ptr['total_wap_cells'])} ô dữ liệu WAP của "
             f"trainingData, số ô có giá trị thuộc khoảng 1…99 là ", ""),
            (f"{ptr['count_in_1_to_99']}", "b"),
            (f", số ô lớn hơn 100 là {ptr['count_gt_100']}, số ô nhỏ hơn −104 "
             f"là {ptr['count_lt_minus_104']}. Giá trị lớn nhất không phải 100 "
             f"là {ptr['max_value_excluding_100']:g}. Nghĩa là toàn bộ dữ liệu "
             f"nằm trong [−104, 0] HOẶC bằng đúng 100, với một khoảng trống "
             f"rộng ", ""),
            (f"{ptr['gap_between_100_and_next_lower_value']:g}", "b"),
            (" đơn vị ở giữa mà không có bất kỳ giá trị nào. Một thang đo vật "
             "lý không có lỗ hổng như vậy — 100 là giá trị sentinel.", "")])
    D.rich([("Bằng chứng 3 — tính nhất quán. ", "b"),
            (f"Nếu đọc 100 là 'không phát hiện' thì mỗi fingerprint phát hiện "
             f"trung bình {ptr['detections_per_fingerprint']['mean']} AP trên "
             f"tổng {tr['n_wap_columns_detected']} AP — hợp lý với một lần "
             "quét Wi-Fi. Nếu đọc 100 là một mức cường độ thì gần như mọi AP "
             "đều được phát hiện ở mức mạnh nhất trong gần như mọi lần quét, "
             "điều vô lý về mặt vật lý.", "")])
    D.rich([("Kết luận: ", "b"), ("giả thuyết được chấp nhận. Toàn bộ mã nguồn "
             "dùng hằng số có tên ", ""), ("NOT_DETECTED = 100", "i"),
            (".", "")])

    D.h(2, "3.3. Độ thưa — tính chất quan trọng nhất của bộ dữ liệu")
    D.table(pd.DataFrame([
        {"Chỉ số": "Tỷ lệ ô là sentinel 100",
         "trainingData": f"{ptr['share_eq_100_pct']:.2f}%",
         "validationData": f"{va['not_detected_probe']['share_eq_100_pct']:.2f}%"},
        {"Chỉ số": "Số AP phát hiện / fingerprint (trung bình)",
         "trainingData": ptr["detections_per_fingerprint"]["mean"],
         "validationData": va["not_detected_probe"][
             "detections_per_fingerprint"]["mean"]},
        {"Chỉ số": "… trung vị",
         "trainingData": f"{ptr['detections_per_fingerprint']['median']:g}",
         "validationData": f"{va['not_detected_probe']['detections_per_fingerprint']['median']:g}"},
        {"Chỉ số": "… min / max",
         "trainingData": f"{ptr['detections_per_fingerprint']['min']} / "
                         f"{ptr['detections_per_fingerprint']['max']}",
         "validationData": f"{va['not_detected_probe']['detections_per_fingerprint']['min']} / "
                           f"{va['not_detected_probe']['detections_per_fingerprint']['max']}"},
        {"Chỉ số": "Fingerprint không phát hiện AP nào",
         "trainingData": ptr["detections_per_fingerprint"][
             "n_rows_with_zero_detections"],
         "validationData": va["not_detected_probe"][
             "detections_per_fingerprint"]["n_rows_with_zero_detections"]},
        {"Chỉ số": "Cột WAP luôn bằng 100 ở mọi dòng",
         "trainingData": ptr["n_wap_columns_always_100"],
         "validationData": va["not_detected_probe"]["n_wap_columns_always_100"]},
    ]), "Độ thưa của UJIIndoorLoc", font_pt=10)
    D.p("Phát biểu lại bằng ngôn ngữ itemset mining: cơ sở dữ liệu có "
        f"{tr['n_wap_columns_detected']} item khả dĩ nhưng độ dài giao dịch "
        f"trung bình chỉ {ptr['detections_per_fingerprint']['mean']}. Chính "
        "tính chất này vừa làm cho việc ánh xạ fingerprint → transaction trở "
        "nên tự nhiên, vừa là nguyên nhân của hiện tượng bùng nổ số lượng HUI "
        "sẽ thấy ở chương 12.", align="justify")
    D.figure(FIGURES / "fig13_eda_rssi_and_sparsity.png",
             "Phân bố RSSI của các AP được phát hiện (trái) và số AP phát hiện "
             "trên mỗi fingerprint (phải), trainingData")

    D.h(2, "3.4. Những bất thường phát hiện được (không có trong tài liệu "
           "bộ dữ liệu)")
    D.rich([(f"Fingerprint rỗng. ", "b"),
            (f"{atr['n_empty_fingerprints']} dòng trainingData có toàn bộ "
             f"{tr['n_wap_columns_detected']} cột WAP bằng 100 — một vị trí có "
             f"nhãn nhưng không có phép đo nào. Phân bố theo PHONEID: "
             f"{atr['empty_fingerprints_by_phoneid']}. Tập trung vào một vài "
             "thiết bị cụ thể, nên đây là lỗi thu thập dữ liệu chứ không phải "
             "tính chất của các vị trí đó.", "")])
    D.rich([(f"Giá trị đúng 0 dBm. ", "b"),
            (f"Có {atr['n_cells_equal_0_dbm']} ô bằng đúng 0 dBm trong "
             f"trainingData, nằm trong {atr['n_rows_containing_a_0_dbm_reading']} "
             f"dòng. Toàn bộ đến từ MỘT thiết bị "
             f"(PHONEID {list(atr.get('rows_with_0_dbm_by_phoneid', {}).keys())}) "
             f"trong MỘT toà nhà "
             f"({list(atr.get('rows_with_0_dbm_by_building', {}).keys())}). "
             "0 dBm là giá trị tối đa theo tài liệu nhưng bất khả thi về vật "
             "lý ở khoảng cách thực; đây là artefact hiệu chuẩn thiết bị. Dữ "
             "liệu được giữ nguyên (ghi nhận, không sửa ngầm), nhưng đây là lý "
             "do phép chuẩn hoá RSSI được neo vào phạm vi TÀI LIỆU thay vì vào "
             "giá trị cực trị mà một thiết bị tình cờ tạo ra.", "")])

    D.h(2, "3.5. Nhãn và hai split khác nhau có chủ đích")
    bxf = tr["building_x_floor"]
    floors = sorted({f for b in bxf for f in bxf[b]}, key=int)
    rows = []
    for b in sorted(bxf, key=int):
        r = {"BUILDINGID": b}
        for f in floors:
            r[f"Tầng {f}"] = nf(bxf[b].get(f, 0))
        r["Tổng"] = nf(sum(bxf[b].get(f, 0) for f in floors))
        rows.append(r)
    D.table(pd.DataFrame(rows),
            "Phân bố fingerprint huấn luyện theo toà nhà × tầng", font_pt=10)
    D.figure(FIGURES / "fig15_building_floor_distribution.png",
             "trainingData: số fingerprint theo toà nhà và tầng", width_in=5.2)

    D.rich([("SPACEID và RELATIVEPOSITION không dùng được làm nhãn. ", "b"),
            (f"Trong validationData, SPACEID có "
             f"{cs['validation_SPACEID_n_unique']} giá trị duy nhất (toàn bộ "
             f"bằng 0: {cs['validation_SPACEID_all_zero']}) và "
             f"RELATIVEPOSITION cũng vậy. Nghĩa là split kiểm định KHÔNG có "
             "nhãn cấp phòng. Mọi con số 'độ chính xác cấp phòng' báo cáo trên "
             "split này sẽ là vô nghĩa. Bài tìm hiểu vì vậy chỉ đánh giá ở cấp toà "
             "nhà và tầng.", "")])
    D.table(pd.DataFrame([
        {"Chỉ số": "USERID", "trainingData": str(cs["USERID_train_values"]),
         "validationData": str(cs["USERID_validation_values"]),
         "Giao nhau": str(cs["USERID_overlap"] or "KHÔNG CÓ")},
        {"Chỉ số": "PHONEID", "trainingData": str(cs["PHONEID_train_values"]),
         "validationData": str(cs["PHONEID_validation_values"]),
         "Giao nhau": str(cs["PHONEID_overlap"])},
        {"Chỉ số": "Thời gian thu thập (UTC)",
         "trainingData": f"{tr['TIMESTAMP_stats']['min_utc'][:10]} → "
                         f"{tr['TIMESTAMP_stats']['max_utc'][:10]}",
         "validationData": f"{va['TIMESTAMP_stats']['min_utc'][:10]} → "
                           f"{va['TIMESTAMP_stats']['max_utc'][:10]}",
         "Giao nhau": "—"},
    ]), "Hai split khác nhau về người dùng, thiết bị và thời gian", font_pt=9,
        widths=[1.5, 2.1, 1.7, 1.0])
    gap_days = int((int(va["TIMESTAMP_stats"]["min"]) -
                    int(tr["TIMESTAMP_stats"]["max"])) / 86400)
    D.rich([("Đây là điểm rất dễ bỏ qua và nó thay đổi cách đọc mọi con số độ "
             "chính xác. ", "b"),
            (f"Hai split KHÔNG chia sẻ bất kỳ USERID nào, chỉ chung "
             f"{len(cs['PHONEID_overlap'])} mã thiết bị "
             f"({cs['PHONEID_overlap']}), và validationData được thu khoảng "
             f"{gap_days} ngày sau khi trainingData kết thúc. Vì vậy mọi độ "
             "chính xác trong báo cáo này là con số CROSS-DEVICE, CROSS-TIME, "
             "không phải con số của một phép chia ngẫu nhiên, và không được so "
             "sánh với các bài báo tự chia lại file huấn luyện. Ngoài ra, có ",
             ""),
            (f"{cs['validation_rows_with_wap_vector_identical_to_a_train_row']}",
             "b"),
            (" dòng kiểm định có vector WAP trùng khít một dòng huấn luyện, "
             "nên không có đường ghi nhớ (memorisation) tầm thường nào.", "")])

    D.h(2, "3.6. Độ phủ AP giữa hai split — một trần chặn sẵn có")
    D.table(pd.DataFrame([
        {"Chỉ số": "AP từng được phát hiện trong trainingData",
         "Số lượng": f"{cs['waps_detected_in_train']} / "
                     f"{tr['n_wap_columns_detected']}"},
        {"Chỉ số": "AP từng được phát hiện trong validationData",
         "Số lượng": cs["waps_detected_in_validation"]},
        {"Chỉ số": "Phát hiện ở cả hai", "Số lượng": cs["waps_detected_in_both"]},
        {"Chỉ số": "Chỉ có trong training",
         "Số lượng": cs["waps_only_in_train"]},
        {"Chỉ số": "CHỈ có trong validation",
         "Số lượng": cs["waps_only_in_validation"]},
    ]), "Độ phủ Access Point giữa hai split", font_pt=10, widths=[4.0, 1.6])
    D.bullets([
        f"{tr['n_wap_columns_detected'] - cs['waps_detected_in_train']} cột là "
        f"sentinel 100 ở MỌI dòng huấn luyện. Chúng không mang thông tin nào "
        f"cho bất kỳ mô hình huấn luyện trên training, nên loại bỏ chúng là "
        f"giảm chiều MIỄN PHÍ, không nhờ HUIM. Vì vậy thực nghiệm báo cáo thêm "
        f"một baseline 'tất cả AP từng được phát hiện' để HUIM không được ghi "
        f"công phần giảm chiều này.",
        f"{cs['waps_only_in_validation']} AP chỉ xuất hiện trong validation. "
        f"Thông tin của chúng là không thể tiếp cận, với MỌI phương pháp. Đây "
        f"là một trần chặn độ chính xác mà không sơ đồ chọn đặc trưng nào nâng "
        f"lên được.",
    ])

    D.h(2, "3.7. AP đi xa đến đâu? — một dự đoán đưa ra TRƯỚC khi chạy mô hình")
    sp = atr["ap_building_spread"]
    D.table(pd.DataFrame([
        {"Số toà nhà mà AP từng được phát hiện": "0 (không bao giờ)",
         "Số AP": sp["n_waps_in_0_buildings"]},
        {"Số toà nhà mà AP từng được phát hiện": "đúng 1",
         "Số AP": sp["n_waps_in_exactly_1_building"]},
        {"Số toà nhà mà AP từng được phát hiện": "đúng 2",
         "Số AP": sp["n_waps_in_exactly_2_buildings"]},
        {"Số toà nhà mà AP từng được phát hiện": "cả 3",
         "Số AP": sp["n_waps_in_all_3_buildings"]},
    ]), "Mức độ lan toả không gian của các Access Point", font_pt=10,
        widths=[4.0, 1.6])
    D.rich([("Dự đoán: ", "b"),
            (f"{sp['n_waps_in_exactly_1_building']} trong "
             f"{cs['waps_detected_in_train']} AP được phát hiện chỉ nằm trong "
             f"một toà nhà, và chỉ {sp['n_waps_in_all_3_buildings']} AP thấy "
             "được ở cả ba. Điều này dự đoán trước rằng phân loại TOÀ NHÀ gần "
             "như là một phép tra bảng, còn phân loại TẦNG mới là phần khó. "
             "Chương 13 sẽ kiểm chứng dự đoán này — và đây là cách đúng để làm "
             "khoa học: dự đoán trước, kiểm chứng sau.", "")])
    D.page_break()
