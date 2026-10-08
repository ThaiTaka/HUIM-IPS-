"""Chapter 15 (reverse-thinking), 17, 18 and the appendix cheat sheet.

Chapter 15 mirrors research/reverse_thinking_analysis.md: both read the same
results/reverse_thinking_observations.json, so the Word chapter and the
Markdown analysis cannot disagree.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from report_builder import Doc
from utils import FIGURES

MODEL_VN = {"A_signal": "Model A — Signal utility",
            "B_discriminative": "Model B — Discriminative utility",
            "C_rare_discriminative": "Model C — Rare-discriminative"}


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


def pc(x, d=2):
    try:
        return f"{float(x)*100:.{d}f}%"
    except (TypeError, ValueError):
        return "N/A"


# ===========================================================================
def ch15(D: Doc, C) -> None:
    o = C.o
    o1 = o["observation_1_threshold_vs_hui_count"]
    o2 = o["observation_2_cost_of_lowering_threshold"]
    o3 = o["observation_3_models_select_different_aps"]
    o4 = o["observation_4_feature_reduction_vs_accuracy"]
    o5 = o["observation_5_huim_vs_controls"]
    o6 = o["observation_6_strong_vs_discriminative"]
    o8 = o["observation_8_more_huis_vs_accuracy"]
    b = o4["baseline_all_520"]

    D.h(1, "15. Phân tích theo tư duy ngược")
    D.p("Mỗi mục dưới đây bắt đầu từ một con số ĐỌC TỪ LOG, rồi mới đi tìm lý "
        "do. Cấu trúc cố định: KẾT QUẢ → QUAN SÁT → TẠI SAO → CƠ CHẾ THUẬT "
        "TOÁN → LÝ THUYẾT HUIM → Ý NGHĨA CHO IPS. Các phát biểu được gắn thẻ "
        "[FACT FROM DATA], [EXPERIMENT RESULT], [FACT FROM PAPER] hoặc "
        "[OUR INTERPRETATION].", align="justify")

    # ------------------------------------------------------------- OBS 1
    D.h(2, "15.1. Quan sát 1 — Giảm minUtil không làm kết quả LỚN DẦN, nó làm "
           "kết quả BÙNG NỔ")
    D.h(3, "KẾT QUẢ")
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Số lần chạy": r["n_runs"],
         "Dải ngưỡng đã thử":
             f"{r['lowest_threshold_tested_pct']:g}% – "
             f"{r['highest_threshold_tested_pct']:g}%",
         "Số lần chạy 0 HUI": r["n_runs_zero_huis"],
         "Ngưỡng cao nhất còn có HUI":
             (f"{r['highest_threshold_with_any_hui_pct']:g}%"
              if r["highest_threshold_with_any_hui_pct"] else "N/A"),
         "Số HUI lớn nhất ghi nhận": nf(r["max_n_huis_observed"])}
        for m, r in o1.items()]),
        "Hành vi của số lượng HUI theo ngưỡng", font_pt=9)
    steps = [(m, r["sharpest_step"]) for m, r in o1.items()
             if r.get("sharpest_step")]
    if steps:
        D.table(pd.DataFrame([
            {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
             "minUtil từ → đến": f"{s['from_pct']:g}% → {s['to_pct']:g}%",
             "Tỷ lệ ngưỡng": f"{s['threshold_ratio']:g}×",
             "Số HUI từ → đến":
                 f"{nf(s['from_n_huis'])} → {nf(s['to_n_huis'])}",
             "Item sau TWU từ → đến":
                 f"{s['from_items_after_twu']} → {s['to_items_after_twu']}",
             "Nút cây từ → đến":
                 f"{nf(s['from_nodes'])} → {nf(s['to_nodes'])}",
             "Runtime từ → đến (s)":
                 f"{s['from_runtime_s']:.2f} → {s['to_runtime_s']:.2f}",
             "Trạng thái sau": s["to_status"]}
            for m, s in steps]),
            "Bước nhảy mạnh nhất đo được của mỗi utility model", font_pt=8)
    D.p("Xem lại Hình ở mục 12.2 (minUtil và số lượng HUI) — đó chính là hình dạng của hiện tượng chuyển pha đang bàn ở đây.", size=11,
        italic=True)

    D.h(3, "QUAN SÁT")
    for m, s in steps:
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"{MODEL_VN.get(m, m)}: chia ngưỡng cho "
                 f"{s['threshold_ratio']:g} đã đưa kết quả từ "
                 f"{nf(s['from_n_huis'])} lên {nf(s['to_n_huis'])} itemset. "
                 f"Trong khi đó số item sống sót sau chặn TWU ở gốc chỉ nhích "
                 f"từ {s['from_items_after_twu']} lên "
                 f"{s['to_items_after_twu']}, và số nút cây đã duyệt từ "
                 f"{nf(s['from_nodes'])} lên {nf(s['to_nodes'])}.", "")])

    D.h(3, "TẠI SAO?")
    D.p("Ngưỡng chỉ thay đổi theo một hệ số nhân nhỏ; kết quả thay đổi theo "
        "nhiều bậc độ lớn. Lời giải thích không nằm ở ngưỡng, nó nằm ở HÌNH "
        "DẠNG của không gian tìm kiếm.", align="justify")
    D.rich([("[FACT FROM DATA] ", "b"),
            (f"Một fingerprint phát hiện trung bình "
             f"{C.o['context']['mean_detections_per_fingerprint']} AP. Các AP "
             "đó không độc lập với nhau: chúng là những AP được lắp gần một vị "
             "trí vật lý, nên chúng được nhìn thấy cùng nhau hết lần này đến "
             "lần khác.", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Giả sử một nhóm k AP cùng xuất hiện trong nhiều fingerprint với "
             "tín hiệu mạnh. Thì MỌI tập con khác rỗng trong 2^k − 1 tập con "
             "của nó cũng cùng xuất hiện ít nhất bằng số lần đó, và utility "
             "của mỗi tập con là một tổng riêng của cùng những utility theo "
             "giao dịch ấy. Ngay khi ngưỡng tụt xuống dưới mức mà tập con NGẮN "
             "NHẤT còn vượt qua, toàn bộ lưới tập con vượt ngưỡng CÙNG MỘT "
             "LÚC. Kết quả không lớn lên từng item một; nó lớn lên theo từng "
             "tập lũy.", "")])
    pairs = []
    for m, d in o3["primary_hui_set_per_model"].items():
        pairs.append(f"{MODEL_VN.get(m, m)} tại {d['rel_minutil_pct']:g}% cho "
                     f"{nf(d['n_huis'])} HUI nhưng chỉ từ {d['n_waps']} WAP "
                     f"riêng biệt")
    D.p("Điều này hiện ra rất rõ trong số liệu: " + "; ".join(pairs) + ".",
        align="justify")
    D.rich([("[OUR INTERPRETATION] Tỷ lệ đó chính là dấu hiệu nhận dạng của cơ "
             "chế: ", "b"),
            ("một lượng khổng lồ itemset trên một bảng chữ cái nhỏ có nghĩa là "
             "các itemset là TẬP CON CỦA NHAU, không phải những phát hiện độc "
             "lập. Một triệu HUI ở đây không phải một triệu phát hiện; đó là "
             "một nhúm nhóm AP được đếm lại một lần cho mỗi tập con.", "")])

    D.h(3, "CƠ CHẾ THUẬT TOÁN")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("EFIM cắt tỉa bằng hai chặn trên (Zida et al. 2017): local "
             "utility loại một item khỏi cả cây con, subtree utility ngăn "
             "không bước vào một nhánh. Cả hai đều là chặn trên cho điều TỐT "
             "NHẤT mà một hậu duệ có thể đạt được.", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Một chặn trên chỉ có thể cắt một nhánh KHÔNG THỂ chứa đáp án. "
             "Khi ngưỡng hạ xuống, những nhánh THỰC SỰ có chứa đáp án thôi "
             "không còn cắt được nữa — và đó là hành vi ĐÚNG. EFIM không hề "
             "thất bại ở minUtil thấp; nó đang bị yêu cầu liệt kê một tập kết "
             "quả mà bản thân nó đã là cỡ lũy thừa. Không có luật cắt tỉa nào "
             "làm nhỏ được một tập đáp án đúng.", "")])
    D.p("Bằng chứng số liệu rằng bản thân các ITEM không phải vấn đề: chặn TWU "
        "ở gốc chỉ giữ lại " +
        ", ".join(f"{o2[m]['items_after_twu_min']}–"
                  f"{o2[m]['items_after_twu_max']} trên "
                  f"{o2[m]['items_initial']} item "
                  f"({MODEL_VN.get(m, m).split(' — ')[0]})" for m in o2) +
        ". Một thay đổi khiêm tốn ở bảng chữ cái đi kèm một thay đổi khổng lồ "
        "ở kết quả, nên bùng nổ là theo ĐỘ SÂU của cây tìm kiếm, không phải "
        "theo ĐỘ RỘNG.", align="justify")

    D.h(3, "LÝ THUYẾT HUIM")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("Utility không có tính anti-monotone và cũng không monotone (Yao "
             "et al. 2004). Support thì có downward closure — một tập cha "
             "không bao giờ xuất hiện nhiều hơn tập con của nó — và chỉ riêng "
             "tính chất đó đã giữ cho frequent-itemset mining khả thi. Utility "
             "không có: thêm một item thì cộng thêm utility của nó (đẩy lên) "
             "nhưng đồng thời có thể thu hẹp tập giao dịch chứa itemset (đẩy "
             "xuống).", "")])
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("Vì vậy việc cắt tỉa buộc phải dùng một ĐẠI DIỆN (surrogate) có "
             "tính chất đó. TWU là anti-monotone (Liu et al. 2005); local và "
             "subtree utility là các phiên bản chặt hơn của cùng ý tưởng. Tất "
             "cả đều là ƯỚC LƯỢNG VƯỢT, nên an toàn, nhưng chúng cũng là "
             "NGƯỠNG ÁP LÊN MỘT CHẶN TRÊN, không phải lên đáp án — và đó là lý "
             "do hiệu lực của chúng sụp đổ đúng vào lúc ngưỡng không còn tách "
             "được nhánh hứa hẹn khỏi nhánh không hứa hẹn.", "")])

    D.h(3, "Ý NGHĨA CHO IPS")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Với bài toán định vị, điều này quyết định cách ĐỌC minUtil. "
             "minUtil KHÔNG phải núm điều chỉnh độ chính xác và KHÔNG phải núm "
             "điều chỉnh chất lượng — nó là núm quyết định MỘT NHÓM AP ĐỒNG "
             "XUẤT HIỆN LỚN ĐẾN ĐÂU THÌ ĐƯỢC COI LÀ MỘT MẪU. Ngưỡng cao chỉ mô "
             "tả những cụm AP dày đặc nhất trên campus. Ngưỡng thấp mô tả cùng "
             "những cụm đó CỘNG THÊM mọi tổ hợp con của chúng — tức là nhiều "
             "kết quả hơn nhưng gần như không thêm thông tin. Với ứng dụng "
             "chọn AP, điểm làm việc hữu dụng vì thế nằm gần ĐẦU TRÊN của dải "
             "ngưỡng, chứ không phải đầu dưới — ngược hẳn với trực giác 'càng "
             "nhiều mẫu càng tốt'.", "")])

    # ------------------------------------------------------------- OBS 2
    D.h(2, "15.2. Quan sát 2 — Runtime theo cây tìm kiếm, bộ nhớ theo kích "
           "thước kết quả")
    D.h(3, "KẾT QUẢ")
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Runtime (s)": f"{r['runtime_s_min']:.2f} – {r['runtime_s_max']:.2f}",
         "Peak mem (MB)":
             f"{r['peak_mem_delta_mb_min']:.1f} – {r['peak_mem_delta_mb_max']:.1f}",
         "Nút cây đã duyệt": f"{nf(r['nodes_min'])} – {nf(r['nodes_max'])}",
         "Spearman ρ(nút, runtime)":
             nf(r.get("spearman_nodes_vs_runtime"), 3),
         "Spearman ρ(số HUI, runtime)":
             nf(r.get("spearman_nhuis_vs_runtime"), 3),
         "Số lần ABORTED": r["n_aborted"]}
        for m, r in o2.items()]),
        "Chi phí tính toán và mức tương quan hạng với kích thước cây tìm kiếm",
        font_pt=8)
    D.p("Xem lại các hình ở mục 12.3 (minUtil với runtime và bộ nhớ).",
        size=11, italic=True)

    D.h(3, "TẠI SAO?")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Tương quan hạng gần như hoàn hảo giữa số nút đã duyệt và runtime "
             "nghĩa là mô hình chi phí đơn giản là CHI PHÍ TRÊN MỖI NÚT: mỗi "
             "nút tốn một phép chiếu cơ sở dữ liệu hiện hành cộng một lượt "
             "Fast Utility Counting. Hạ ngưỡng không làm một nút đắt hơn; nó "
             "làm CÓ NHIỀU NÚT HƠN. Vậy runtime là một thước đo cho việc EFIM "
             "bị buộc phải đi bộ qua bao nhiêu phần của lưới itemset.", "")])
    D.p("Bộ nhớ hành xử khác runtime, và cần tách bạch lý do: TẬP LÀM VIỆC của "
        "EFIM là nhỏ (mỗi mức đệ quy một cơ sở dữ liệu đã chiếu, và "
        "transaction merging giữ cho chúng nhỏ), nhưng DANH SÁCH KẾT QUẢ lớn "
        "lên theo số HUI tìm được. Vì vậy bộ nhớ đỉnh theo KÍCH THƯỚC KẾT QUẢ "
        "chứ không theo kích thước tìm kiếm.", align="justify")

    D.h(3, "CƠ CHẾ THUẬT TOÁN")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("Thiết kế bộ nhớ của EFIM là có chủ đích: high-utility database "
             "projection tái dùng mảng của nút cha thay vì tạo utility-list "
             "cho từng itemset (chi phí vốn chi phối HUI-Miner), và "
             "transaction merging hợp các giao dịch đã chiếu trở nên giống "
             "nhau.", "")])
    D.rich([("[FACT FROM DATA] ", "b"),
            ("Số giao dịch được hợp nhờ merging trên bộ dữ liệu này lên tới " +
             ", ".join(f"{nf(C.H[C.H['utility_model'] == m]['transactions_saved_by_merging'].max())} "
                       f"lượt ({MODEL_VN.get(m, m).split(' — ')[0]})"
                       for m in o2) + ".", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Merging hiệu quả ở đây vì một lý do đặc thù của dữ liệu Wi-Fi. "
             "Phép chiếu liên tục bóc các AP đứng đầu khỏi mỗi giao dịch; phần "
             "còn lại là các 'đuôi'. Fingerprint thu ở những điểm gần nhau có "
             "đuôi rất giống nhau, nên sau vài lần chiếu nhiều giao dịch trở "
             "nên GIỐNG NHAU HOÀN TOÀN và co lại thành một. Một cơ sở dữ liệu "
             "giỏ hàng, nơi mỗi hoá đơn mang tính cá biệt, hưởng lợi ít hơn "
             "nhiều.", "")])

    D.h(3, "Ý NGHĨA CHO IPS")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Với một hệ thống định vị triển khai thật, hệ quả thực tế là HUIM "
             "thuộc PHA OFFLINE, và chi phí của nó phải được dự toán theo "
             "NGƯỠNG, không theo kích thước cơ sở dữ liệu. Khai thác là một "
             "phép tính một lần trong khảo sát hiện trường; pha online chỉ bao "
             "giờ nhìn thấy danh sách AP kết quả, và danh sách đó không tốn gì. "
             "Người thiết kế hệ thống cần chính đường cong ngưỡng–runtime đo "
             "được ở đây, không phải một con số runtime trung bình.", "")])

    # ------------------------------------------------------------- OBS 3
    D.h(2, "15.3. Quan sát 3 — Hai định nghĩa utility KHÔNG chọn cùng một tập "
           "Access Point")
    D.h(3, "KẾT QUẢ")
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Lần chạy": d["run_tag"], "minUtil": f"{d['rel_minutil_pct']:g}%",
         "Số HUI": nf(d["n_huis"]), "Số WAP trong union": d["n_waps"]}
        for m, d in o3["primary_hui_set_per_model"].items()]),
        "Tập HUI phong phú nhất và KHÔNG bị cắt ngang của mỗi model (tập bị "
        "cắt ngang bị thiên lệch theo thứ tự duyệt nên không dùng để xếp hạng "
        "AP)", font_pt=9)
    if o3["pairwise_overlap"]:
        D.table(pd.DataFrame([
            {"Cặp so sánh": k, "|A|": v["n_a"], "|B|": v["n_b"],
             "|A ∩ B|": v["n_intersection"], "Jaccard": f"{v['jaccard']:.3f}",
             "Trùng trong top-10": f"{v['top10_overlap']}/10"}
            for k, v in o3["pairwise_overlap"].items()]),
            "Mức chồng lấp giữa các tập AP được chọn", font_pt=8)

    D.h(3, "TẠI SAO?")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Các model dùng CHUNG internal utility và chỉ khác nhau ở p(i), "
             "nên mọi khác biệt đều quy về external utility. Với Model A, "
             "p ≡ 1 làm utility thành hàm của 'cường độ tín hiệu × số lần các "
             "AP cùng xuất hiện': nó thưởng cho AP mạnh và phổ biến. Model B "
             "nhân thêm mutual information của AP với nhãn tầng, tức là DÌM "
             "CHÍNH những AP phổ biến đó xuống, bởi một AP nhìn thấy ở mọi nơi "
             "không nói gì về việc bạn đang ở đâu.", "")])

    D.h(3, "CƠ CHẾ THUẬT TOÁN")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Tác động chạy qua các CHẶN TRÊN, không chỉ qua utility cuối "
             "cùng. TWU(i) = Σ(T ∋ i) TU(T) được tính từ CÙNG các giá trị p, "
             "nên thay đổi p làm thay đổi item nào sống sót qua chặn ở gốc, "
             "điều này làm thay đổi thứ tự item (EFIM sắp theo TWU tăng), điều "
             "này làm thay đổi HÌNH DẠNG của toàn bộ cây tìm kiếm. Vậy hai "
             "định nghĩa utility không chỉ cho điểm lại cùng những mẫu cũ; "
             "chúng duyệt những cái cây khác nhau và có thể trả về những mẫu "
             "khác nhau về cấu trúc.", "")])

    D.h(3, "LÝ THUYẾT HUIM")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("Đây chính là tính chất làm utility mining khác với weighted "
             "frequent-itemset mining (Gan et al., IEEE TKDE 2021): hàm utility "
             "là MỘT PHẦN CỦA PHÁT BIỂU BÀI TOÁN, không phải một bước xếp hạng "
             "hậu kỳ.", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Với một nghiên cứu ứng dụng, hệ luận này khó nghe nhưng quan "
             "trọng: 'các High Utility Itemset của bộ dữ liệu này' KHÔNG phải "
             "một đối tượng xác định. Nó chỉ xác định tương đối với một lựa "
             "chọn (q, p) mà người phân tích đưa ra.", "")])

    D.h(3, "Ý NGHĨA CHO IPS")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Nếu mục tiêu là định vị thì utility phải mã hoá một điều gì đó "
             "về định vị. Khái niệm 'hữu ích' của Model A — mạnh và ở khắp nơi "
             "— gần như là ĐỐI LẬP với điều một fingerprint cần, vốn là một AP "
             "mà mẫu hiện diện của nó THAY ĐỔI giữa các vị trí. Model B được "
             "thiết kế để mã hoá điều đó, và các con số chồng lấp ở trên cho "
             "thấy thiết kế này thực sự làm thay đổi câu trả lời, chứ không "
             "chỉ dán lại nhãn.", "")])

    # ------------------------------------------------------------- OBS 4
    D.h(2, "15.4. Quan sát 4 — Giảm được bao nhiêu đặc trưng, và vì sao TẦNG "
           "là ràng buộc")
    D.h(3, "KẾT QUẢ")
    D.p(f"Baseline toàn bộ {b['n_waps']} cột WAP: Building "
        f"{pc(b['building_accuracy'])}, Floor {pc(b['floor_accuracy'])}, Joint "
        f"{pc(b['joint_accuracy'])}, Macro F1 {b['joint_macro_f1']:.4f}, sai "
        f"số định vị trung vị {b['median_pos_error']:.2f} đơn vị toạ độ.",
        align="justify")
    if o4["per_model_best_topn"]:
        D.table(pd.DataFrame([
            {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
             "Số WAP": d["n_waps"],
             "Giảm chiều": f"{d['feature_reduction_pct']:.2f}%",
             "Building": pc(d["building_accuracy"]),
             "Floor": pc(d["floor_accuracy"]),
             "Joint": pc(d["joint_accuracy"]),
             "Δ Joint": f"{d['delta_joint_vs_baseline']*100:+.2f} pp"}
            for m, d in o4["per_model_best_topn"].items()]),
            "Cấu hình top-n tốt nhất của mỗi model so với baseline", font_pt=9)
    D.p("Xem lại hình ở mục 13.4 (giảm chiều và độ chính xác joint).",
        size=11, italic=True)

    D.h(3, "TẠI SAO?")
    D.rich([("[FACT FROM DATA] ", "b"),
            (f"Audit đã dự đoán sự chia tách độ khó này TRƯỚC khi fit bất kỳ "
             f"mô hình nào: trong "
             f"{C.o['context']['n_waps_detected_in_training']} AP được phát "
             f"hiện ở training, "
             f"{o6['ap_building_spread']['n_waps_in_exactly_1_building']} AP "
             f"chỉ nằm trong một toà nhà và chỉ "
             f"{o6['ap_building_spread']['n_waps_in_all_3_buildings']} AP thấy "
             f"được ở cả ba. Vậy xác định TOÀ NHÀ gần như là một phép tra "
             f"bảng; xác định TẦNG đòi hỏi phân giải khác biệt tín hiệu TRONG "
             f"CÙNG một toà nhà, nơi cùng những AP đó nhìn thấy được ở mọi "
             f"tầng.", "")])
    D.rich([("[EXPERIMENT RESULT] ", "b"),
            (f"Và số liệu đúng như vậy: Building {pc(b['building_accuracy'])} "
             f"so với Floor {pc(b['floor_accuracy'])} tại baseline. Joint bị "
             f"chặn bởi thành phần tầng, nên NHẦM TẦNG là toàn bộ vấn đề, và "
             f"mọi phương pháp chọn đặc trưng phải được đánh giá ở chỗ nó có "
             f"bảo toàn khả năng phân biệt trong cùng toà nhà hay không.", "")])

    D.h(3, "CƠ CHẾ")
    D.rich([("[OUR INTERPRETATION] Hai lực đối nghịch khi bỏ cột. ", "b"),
            ("Bỏ một cột thuần nhiễu thì GIÚP k-NN, vì mỗi chiều được giữ lại "
             "đều góp vào khoảng cách và các chiều nhiễu làm loãng các chiều "
             "mang thông tin — chính là curse of dimensionality. Bỏ một cột có "
             "khả năng phân biệt hai tầng thì GÂY HẠI, và không thể bù lại. "
             "Chỗ đường cong quay đầu chính là chỗ lực thứ hai bắt đầu thắng.",
             "")])
    D.p("Một cơ chế thứ hai, cụ thể hơn, quan trọng ở các ngân sách nhỏ: một "
        "fingerprint kiểm định mà KHÔNG phát hiện được AP nào trong tập đã "
        "chọn sẽ trở thành một vector toàn 0, và láng giềng gần nhất của nó "
        "lúc đó gần như tuỳ ý. Số lượng này được ghi log cho từng điều kiện "
        "(cột val_rows_with_no_selected_wap_detected trong "
        "results/metrics/ips_results.csv) đúng để một sự sụt giảm ở n nhỏ có "
        "thể quy về MẤT ĐỘ PHỦ chứ không bị quy sai thành MẤT KHẢ NĂNG PHÂN "
        "BIỆT.", align="justify")

    D.h(3, "Ý NGHĨA CHO IPS")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Câu trả lời cho 'giảm được bao nhiêu WAP' KHÔNG phải một con số "
             "duy nhất — nó phụ thuộc vào độ chính xác nào đang được bảo vệ. "
             "Building accuracy chịu được giảm chiều rất mạnh vì một nhúm AP "
             "độc quyền theo toà nhà gánh nó. Floor accuracy là ràng buộc "
             "chặt. Một báo cáo chỉ nêu building accuracy sẽ làm phương pháp "
             "trông tốt hơn thực tế rất nhiều.", "")])

    # ------------------------------------------------------------- OBS 5
    D.h(2, "15.5. Quan sát 5 — HUIM giúp, hay chỉ là 'ít đặc trưng hơn' giúp?")
    D.h(3, "KẾT QUẢ")
    D.p("Đây là so sánh quyết định bài tìm hiểu có kết quả dương hay không. Ở mỗi "
        "ngân sách đặc trưng khớp nhau, lựa chọn của HUIM được đặt cạnh "
        "(i) chọn ngẫu nhiên từ các AP được phát hiện trong training, (ii) n "
        "AP được phát hiện nhiều nhất, (iii) n AP có mutual information cao "
        "nhất — chính tiêu chí mà Model B nhúng vào, dùng một mình, KHÔNG có "
        "khai thác itemset.", align="justify")
    rows = o5["matched_budget_comparison"]
    if rows:
        huim_cols = sorted({k for r in rows for k in r if k.startswith("huim_")})
        data = []
        for r in rows:
            d = {"n": r["budget_n"]}
            for c in huim_cols:
                d["HUIM " + c[5:].split("_")[0].upper()] = (
                    pc(r[c]) if c in r else "—")
            d["Top-n MI"] = pc(r["control_top_mi"]) if "control_top_mi" in r else "—"
            d["Top-n support"] = (pc(r["control_top_support"])
                                  if "control_top_support" in r else "—")
            d["Random TB"] = (pc(r["control_random_mean"])
                              if "control_random_mean" in r else "—")
            d["Random min–max"] = (
                f"{r['control_random_min']*100:.2f}–"
                f"{r['control_random_max']*100:.2f}%"
                if "control_random_min" in r else "—")
            data.append(d)
        D.table(pd.DataFrame(data),
                "Joint Building-Floor Accuracy ở các ngân sách khớp nhau",
                font_pt=8)
    w = o5["verdict_inputs"]
    D.rich([("[EXPERIMENT RESULT] ", "b"),
            (f"Trên {w['n_comparisons']} ngân sách khớp nhau: HUIM tốt nhất "
             f"vượt chọn ngẫu nhiên ở {w['huim_beats_random']}/"
             f"{w['n_comparisons']} trường hợp, vượt top-n theo mutual "
             f"information ở {w['huim_beats_top_mi']}/{w['n_comparisons']}, "
             f"vượt top-n theo số lần phát hiện ở "
             f"{w['huim_beats_top_support']}/{w['n_comparisons']}.", "")])
    D.p("Xem lại hình ở mục 13.3 (HUIM so với ba đối chứng).", size=11,
        italic=True)

    D.h(3, "TẠI SAO BA ĐỐI CHỨNG, VÀ MỖI CÁI TRẢ LỜI GÌ")
    D.bullets([
        "So với NGẪU NHIÊN: tập được chọn có chứa thông tin nào không? Nếu "
        "HUIM không vượt ngẫu nhiên thì việc 'giảm chiều' chỉ là XOÁ chiều.",
        "So với TOP-N THEO SUPPORT: có hơn 'chọn các AP nhìn thấy nhiều nhất' "
        "không? Support là thứ mà một frequent-itemset miner sẽ ưu tiên, nên "
        "đây là câu hỏi frequent-vs-useful ở dạng thực nghiệm.",
        "So với TOP-N THEO MUTUAL INFORMATION: đây là đối chứng khó nhất. "
        "External utility của Model B CHÍNH LÀ mutual information. Nếu xếp "
        "hạng AP bằng MI trực tiếp cũng tốt bằng việc khai thác những itemset "
        "có utility dựng từ MI, thì phần khai thác itemset KHÔNG đóng góp gì "
        "ngoài chính trọng số nó được cho sẵn — và sự trung thực đòi hỏi phải "
        "nói ra điều đó.",
    ])

    D.h(3, "LÝ THUYẾT HUIM")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("HUIM được định nghĩa là một bài toán phát hiện mẫu KHÔNG GIÁM "
             "SÁT: tìm các itemset có utility vượt ngưỡng. Không có gì trong "
             "định nghĩa tối ưu một mục tiêu phân loại.", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Nên ở đây không có định lý nào để viện dẫn — việc một High "
             "Utility Itemset có phải một tập đặc trưng tốt hay không là một "
             "câu hỏi THUẦN THỰC NGHIỆM, và câu trả lời chính đáng duy nhất là "
             "bảng số liệu ở trên. Đặc biệt: KHÔNG được đồng nhất HUI với "
             "'nhóm đặc trưng định vị tốt' nếu các con số này không chứng minh "
             "điều đó.", "")])

    # ------------------------------------------------------------- OBS 6
    D.h(2, "15.6. Quan sát 6 — 'Được phát hiện nhiều' và 'mang thông tin' tách "
           "rời đến đâu?")
    D.p("Mục này ban đầu được thiết kế để xác nhận khẩu hiệu 'frequent ≠ "
        "useful'. Số liệu đã BÁC BỎ phần lớn kỳ vọng đó trên bộ dữ liệu này, "
        "và kết quả được báo cáo đúng như đo được.", align="justify",
        italic=True)
    D.h(3, "KẾT QUẢ")
    sup = o6.get("top10_by_support", [])
    mis = o6.get("top10_by_mutual_information") or []
    D.table(pd.DataFrame([
        {"Hạng": k + 1,
         "AP được phát hiện nhiều nhất": sup[k]["wap"] if k < len(sup) else "—",
         "Số lần phát hiện": nf(sup[k]["support"]) if k < len(sup) else "—",
         "AP có MI cao nhất": mis[k]["wap"] if k < len(mis) else "—",
         "MI (bit)": mis[k]["mi_bits"] if k < len(mis) else "—",
         "Số lần phát hiện ": nf(mis[k]["support"]) if k < len(mis) else "—"}
        for k in range(max(len(sup), len(mis)))]),
        "Hai bảng xếp hạng AP: theo tần suất và theo lượng thông tin",
        font_pt=9)
    D.rich([("[EXPERIMENT RESULT] ", "b"),
            (f"Mức trùng giữa hai top-10: "
             f"{o6['overlap_top10_support_vs_top10_mi']}/10"
             + (f" ({', '.join(o6['overlap_members'])})"
                if o6["overlap_members"] else "") + ".", "")])
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"Trên toàn bộ {o6['n_detected_waps_compared']} AP được phát "
                 f"hiện, tương quan hạng giữa số lần được phát hiện và mutual "
                 f"information là ", ""),
                (f"Spearman ρ = "
                 f"{o6['spearman_support_vs_mi_over_all_detected_waps']}", "b"),
                (f" (Pearson r = "
                 f"{o6['pearson_support_vs_mi_over_all_detected_waps']}). Mức "
                 f"trùng xếp hạng theo độ sâu: "
                 + ", ".join(f"top-{k}: {v}/{k}"
                             for k, v in o6["rank_overlap_at_depth"].items())
                 + ".", "")])
        D.rich([("Đây là một kết quả ĐI NGƯỢC kỳ vọng ban đầu, và nó phải được "
                 "nói thẳng. ", "b"),
                ("Hai tiêu chí KHÔNG tách rời nhau trên bộ dữ liệu này — chúng "
                 "gần như trùng khít về thứ hạng. Nguyên nhân nằm ở chính cách "
                 "rời rạc hoá dùng cho mutual information: trạng thái 0 ('không "
                 "phát hiện') chiếm phần áp đảo trong phân bố, nên I(A_i;Y) "
                 "chủ yếu phản ánh việc AP i CÓ ĐƯỢC NHÌN THẤY HAY KHÔNG ở "
                 "từng tầng, tức gần như là một hàm đơn điệu của support.",
                 "")])
        D.rich([("[OUR INTERPRETATION] Hệ quả nghiêm túc cho Model B: ", "b"),
                ("external utility mà bài tìm hiểu gọi là 'discriminative' trên thực "
                 "tế gần như là một cách tham số hoá lại tần suất phát hiện. "
                 "Điều này giải thích ba quan sát khác một cách nhất quán: "
                 "(1) hai đối chứng top-n theo MI và top-n theo support cho kết "
                 "quả rất gần nhau; (2) Model B và Model C chọn ra những tập "
                 "AP rất giống nhau; (3) ablation giữa B và C ít thông tin hơn "
                 "mong đợi. Đây là một HẠN CHẾ THIẾT KẾ của bài tìm hiểu, không phải "
                 "một tính chất của HUIM.", "")])
    if o6.get("label_entropy_bits") is not None:
        D.rich([("[FACT FROM DATA] ", "b"),
                (f"Entropy nhãn H(Y) của "
                 f"{C.tr['joint_building_floor_n_classes']} lớp "
                 f"BUILDINGID_FLOOR là {o6['label_entropy_bits']} bit. AP mang "
                 f"thông tin nhất cung cấp {o6['max_mi_bits']} bit, tức "
                 f"{o6['max_mi_as_fraction_of_H_Y']*100:.1f}% của H(Y).",
                 "")])
    D.p("Xem lại hình ở mục 8.4 (quan hệ giữa số lần được phát hiện và lượng thông tin của mỗi AP).", size=11, italic=True)

    D.h(3, "TẠI SAO?")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Độ phủ và lượng thông tin kéo cùng chiều nhau tới một điểm — một "
             "AP không ai nhìn thấy thì không phân biệt được gì, nên có độ phủ "
             "là ĐIỀU KIỆN CẦN để mang thông tin. Chúng chỉ tách nhau khi đi "
             "sâu xuống bảng xếp hạng, và trên bộ dữ liệu này mức tách rời đó "
             "rất nhỏ.", "")])
    D.rich([("[FACT FROM DATA] ", "b"),
            (f"Lý do cấu trúc nằm trong audit: "
             f"{o6['ap_building_spread']['n_waps_in_exactly_1_building']} AP "
             f"được phát hiện chỉ nằm trong một toà nhà, "
             f"{o6['ap_building_spread']['n_waps_in_exactly_2_buildings']} AP "
             f"ở hai toà và "
             f"{o6['ap_building_spread']['n_waps_in_all_3_buildings']} AP ở cả "
             f"ba. SỰ GIỚI HẠN KHÔNG GIAN chính là thứ tạo ra thông tin.", "")])

    D.h(3, "LÝ THUYẾT HUIM")
    D.rich([("[FACT FROM PAPER] ", "b"),
            ("Đây đúng là động lực của utility mining so với frequent-itemset "
             "mining (Yao et al. 2004; Gan et al. 2021): tần suất và giá trị "
             "là hai trục khác nhau, một item có thể hiếm-mà-quý hoặc "
             "phổ biến-mà-vô dụng.", "")])
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Trên bộ dữ liệu này sự tách rời đó là CÓ THẬT NHƯNG NHỎ, như số "
             "liệu ở trên cho thấy. Chỗ mà sự phân biệt thực sự có hiệu lực "
             "không nằm ở tần suất của từng item, mà nằm ở UTILITY CỦA MODEL A "
             "— vốn nhân cường độ tín hiệu với mức độ đồng xuất hiện, và có "
             "xếp hạng TỆ HƠN CẢ NGẪU NHIÊN (xem mục 15.8). Đó mới là minh hoạ "
             "sạch sẽ cho 'thứ trông có vẻ giá trị không phải thứ hữu ích', và "
             "nó là điều làm Model A trở thành một đối chứng CÓ NGHĨA chứ "
             "không phải một nhánh ablation lãng phí.", "")])

    D.h(3, "Ý NGHĨA CHO IPS")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Bài học thực tiễn hẹp hơn khẩu hiệu nhiều: đừng giữ một AP vì "
             "TÍN HIỆU CỦA NÓ MẠNH. Nhưng giữ AP vì NÓ ĐƯỢC PHÁT HIỆN RỘNG "
             "RÃI, trên bộ dữ liệu này, lại KHÔNG phải một heuristic tồi chút "
             "nào — đối chứng top-n theo số lần phát hiện bám sát ở mọi ngân "
             "sách, và ở 200 AP nó là điều kiện có độ chính xác cao nhất trong "
             "toàn bộ nghiên cứu. Thứ một cơ sở dữ liệu fingerprint cần trước "
             "hết là ĐỘ PHỦ, rồi mới đến các biên vùng phủ cắt qua toà nhà.",
             "")])

    # ------------------------------------------------------------- OBS 8
    D.h(2, "15.7. Quan sát 7 — Nhiều HUI hơn có chắc định vị tốt hơn không?")
    _ = None
    D.h(3, "KẾT QUẢ")
    items = [f"Số điều kiện union được đánh giá: {o8['n_points']}"]
    if "spearman_n_huis_vs_joint_accuracy" in o8:
        items.append(f"Spearman ρ(số HUI, joint accuracy) = "
                     f"{o8['spearman_n_huis_vs_joint_accuracy']}")
        items.append(f"Spearman ρ(số WAP được chọn, joint accuracy) = "
                     f"{o8['spearman_n_waps_vs_joint_accuracy']}")
    if "spearman_n_waps_vs_joint_accuracy_topn" in o8:
        items.append(f"Spearman ρ(số WAP, joint accuracy) trên quét top-n = "
                     f"{o8['spearman_n_waps_vs_joint_accuracy_topn']}")
    D.bullets(items)
    D.h(3, "TRẢ LỜI")
    D.rich([("[OUR INTERPRETATION] ", "b"),
            ("Tương quan tính trên các điểm union KHÔNG tách được 'nhiều "
             "itemset hơn' khỏi 'nhiều đặc trưng hơn', vì hạ minUtil làm tăng "
             "cả hai cùng lúc. Quét top-n giữ CỐ ĐỊNH tập HUI và chỉ thay đổi "
             "ngân sách, nên đó mới là so sánh cô lập được số lượng đặc "
             "trưng.", "")])
    D.rich([("Và câu hỏi 'tập HUI lớn hơn có cho độ chính xác tốt hơn' là một "
             "CÂU HỎI SAI, ", "b"),
            ("vì Quan sát 1 đã giải thích tại sao: một tập HUI lớn hơn ở "
             "minUtil thấp hơn phần lớn là THÊM CÁC TẬP CON của cùng những "
             "nhóm AP, nên nó thêm itemset mà không thêm AP. Thứ làm thay đổi "
             "độ chính xác là NHỮNG AP NÀO rơi vào union, không phải BAO NHIÊU "
             "itemset nhắc đến chúng. Vì vậy mọi phát biểu kiểu 'khai thác "
             "nhiều mẫu hơn thì định vị tốt hơn' đều KHÔNG được thực nghiệm "
             "này ủng hộ.", "")])

    # ------------------------------------------------------------- wrap
    # ------------------------------------------------------------- OBS 9
    o9 = C.o.get("observation_9_ranking_vs_size", {})
    if o9.get("largest_huim_selected_set"):
        D.h(2, "15.8. Quan sát 8 — Thiếu hụt là do XẾP HẠNG kém hay do QUÁ ÍT "
               "đặc trưng?")
        D.h(3, "KẾT QUẢ")
        bb = o9.get("best_joint_at_or_below_that_budget_any_method") or {}
        sc = o9.get("smallest_control_subset_reaching_baseline")
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"Tập AP lớn nhất mà bất kỳ điều kiện HUIM nào tạo ra là "
                 f"{o9['largest_huim_selected_set']} WAP "
                 f"({o9['largest_huim_set_condition']}). Trong giới hạn ngân "
                 f"sách đó, độ chính xác joint cao nhất mà MỌI phương pháp "
                 f"trong nghiên cứu này đạt được là "
                 f"{pc(bb.get('joint'))} ({bb.get('condition','N/A')}, "
                 f"{bb.get('n_waps','N/A')} WAP), so với baseline "
                 f"{pc(b['joint_accuracy'])} trên {b['n_waps']} WAP.", "")])
        if sc:
            D.rich([("[EXPERIMENT RESULT] ", "b"),
                    (f"Tập con nhỏ nhất thuộc BẤT KỲ loại nào chạm được "
                     f"baseline dùng {sc['n_waps']} WAP "
                     f"({sc['reduction_pct']:.2f}% giảm chiều, "
                     f"{pc(sc['joint'])}, {sc['condition']}) — cao hơn hẳn "
                     f"trần {o9['largest_huim_selected_set']} WAP mà HUIM có "
                     f"thể cung cấp.", "")])
        rows9 = o9.get("like_for_like_at_huim_budgets", [])
        if rows9:
            cols9 = sorted({k for r in rows9 for k in r if k != "n"})
            hdr = {"huim_A_signal": "HUIM A", "huim_B_discriminative": "HUIM B",
                   "huim_C_rare_discriminative": "HUIM C",
                   "control_top_mi": "Top-n MI",
                   "control_top_support": "Top-n support",
                   "control_random_mean": "Random (TB)"}
            data = []
            for r in rows9:
                d = {"n": r["n"]}
                for c in cols9:
                    d[hdr.get(c, c)] = pc(r[c]) if c in r else "—"
                data.append(d)
            D.table(pd.DataFrame(data),
                    "So sánh ĐÚNG ngân sách mà HUIM sử dụng (Joint Accuracy)",
                    font_pt=8)
        bm = o9.get("beats_random_by_model", {})
        if bm:
            D.table(pd.DataFrame([
                {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
                 "Số ngân sách so sánh": d["n"],
                 "Số lần xếp hạng HUIM vượt ngẫu nhiên": d["beats"]}
                for m, d in bm.items()]),
                "Xếp hạng của từng utility model có hơn NGẪU NHIÊN ở cùng ngân "
                "sách không?", font_pt=9)
        D.h(3, "TẠI SAO? — hai cách giải thích phải tách bạch")
        D.rich([("Cách giải thích 1 — xếp hạng sai. ", "b"),
                ("Nếu thứ tự AP mà HUIM đưa ra không hơn gì ngẫu nhiên thì nó "
                 "sẽ thua chọn ngẫu nhiên ở cùng ngân sách. Bảng trên trả lời "
                 "câu này RIÊNG cho từng model — và câu trả lời khác nhau giữa "
                 "các model, đó chính là mục đích của ablation.", "")])
        D.rich([("Cách giải thích 2 — tập quá nhỏ. ", "b"),
                (f"HUIM chỉ có thể cung cấp những AP xuất hiện trong một tập "
                 f"HUI KHÔNG bị cắt ngang, và số lượng đó bị chặn bởi ngưỡng "
                 f"minUtil thấp nhất còn hoàn thành trong ngân sách tài "
                 f"nguyên. Ở đây trần là {o9['largest_huim_selected_set']} "
                 f"WAP, trong khi đối chứng đơn giản nhất cần "
                 + (f"{sc['n_waps']} WAP" if sc else "nhiều hơn mọi ngân sách "
                                                    "đã thử")
                 + " để chạm baseline. ", ""),
                ("Ngay cả một xếp hạng HOÀN HẢO cũng không thể lấp khoảng "
                 "cách từ bên trong cái trần đó.", "b")])
        D.rich([("[OUR INTERPRETATION] ", "b"),
                ("Đây là phát hiện cơ chế hữu ích nhất của nghiên cứu, và nó "
                 "chỉ thẳng về Quan sát 1. Muốn mở rộng tập AP thì minUtil "
                 "phải giảm; nhưng giảm minUtil làm số ITEMSET tăng nhanh hơn "
                 "rất nhiều so với số AP, và chi phí khai thác bùng nổ trước "
                 "khi tập AP kịp lớn lên một cách hữu ích. Kích thước tập đặc "
                 "trưng mà người dùng cần, và vùng ngưỡng mà HUIM thực sự chạy "
                 "được — trên bộ dữ liệu này và với các định nghĩa utility này "
                 "— đang kéo về hai hướng ngược nhau.", "")])
        D.rich([("Lưu ý điều này KHÔNG nói. ", "b"),
                ("Nó không nói xếp hạng của HUIM là kém — đó là câu hỏi riêng "
                 "mà bảng ở trên trả lời. Nó nói rằng điểm làm việc nơi đặc "
                 "trưng do HUIM chọn có thể cạnh tranh được đã KHÔNG nằm trong "
                 "tầm với của ngân sách tính toán dùng ở đây, và đó là một "
                 "phát biểu về thiết kế thực nghiệm này cũng nhiều như về bản "
                 "thân phương pháp.", "")])

    D.h(2, "15.9. Đọc ngược chuỗi suy luận: từ kết quả về lý thuyết")
    D.bullets([
        "[EXPERIMENT RESULT] Kích thước kết quả cực kỳ nhạy với minUtil, nhưng "
        "số AP riêng biệt tham gia thì không. → [LÝ THUYẾT] Vì utility thiếu "
        "downward closure, tập đáp án là một HỢP CỦA CÁC LƯỚI TẬP CON, và kích "
        "thước của nó bị chi phối bởi độ sâu của itemset đạt ngưỡng sâu nhất.",
        "[EXPERIMENT RESULT] Runtime tỷ lệ với số nút đã duyệt; bộ nhớ tỷ lệ "
        "với kích thước kết quả. → [LÝ THUYẾT] Các chặn trên của EFIM điều "
        "khiển TÌM KIẾM, không điều khiển KẾT QUẢ. Không thuật toán đúng nào "
        "làm tốt hơn được ở phần kết quả.",
        "[EXPERIMENT RESULT] Chỉ thay đổi p đã làm thay đổi tập AP được chọn. "
        "→ [LÝ THUYẾT] Hàm utility là một phần của phát biểu bài toán, nên "
        "'các HUI của một bộ dữ liệu' không phải khái niệm xác định nếu không "
        "kèm (q, p).",
        "[EXPERIMENT RESULT] Số lần được phát hiện và mutual information hoá "
        "ra gần như trùng khít về thứ hạng, nên 'frequent ≠ useful' KHÔNG được "
        "chứng minh ở mức từng AP — ngược với điều bài tìm hiểu kỳ vọng. → [LÝ "
        "THUYẾT] Sự phân biệt vẫn đúng, nhưng nó phát huy ở mức HÀM UTILITY "
        "chứ không ở mức item: Model A, với p ≡ 1 biến utility thành tích của "
        "cường độ tín hiệu và mức đồng xuất hiện, xếp hạng AP tệ hơn cả ngẫu "
        "nhiên.",
        "[LÝ THUYẾT → THỰC TIỄN] HUIM KHÔNG phải một bộ chọn đặc trưng có giám "
        "sát. Mọi ích lợi của nó cho định vị đến từ định nghĩa utility do "
        "người phân tích cung cấp, và phải được chứng minh bằng đối chứng chứ "
        "không được giả định.",
    ])
    D.h(3, "Những điều KHÔNG được khẳng định")
    D.bullets([
        "Rằng một High Utility Itemset, một cách tổng quát, là một nhóm đặc "
        "trưng tốt cho phân loại.",
        "Rằng HUIM là một phương pháp chọn AP tốt hơn các phương pháp "
        "information-theoretic đã có; bảng ngân sách khớp nhau là bằng chứng "
        "duy nhất được đưa ra, và nó được đọc đúng như nó là.",
        "Rằng các kết quả này tổng quát hoá được ra ngoài UJIIndoorLoc, một "
        "cấu hình k-NN, và các định nghĩa (q, p) dùng ở đây.",
        "Bất kỳ quyền ưu tiên novelty nào. Xem research/literature_review.md "
        "mục 7.",
    ])
    D.page_break()


# ===========================================================================
def ch17_18(D: Doc, C) -> None:
    o4 = C.o["observation_4_feature_reduction_vs_accuracy"]
    o5 = C.o["observation_5_huim_vs_controls"]
    b = o4["baseline_all_520"]
    D.h(1, "17. Kết luận")
    D.p("Trả lời trực tiếp bảy câu hỏi nghiên cứu, mọi con số lấy từ log thực "
        "nghiệm.", align="justify")

    D.h(2, "RQ1 — Có thể mô hình hoá fingerprint Wi-Fi thành utility "
           "transaction cho HUIM một cách hợp lý hay không?")
    D.rich([("Có, về mặt kỹ thuật, và đây là kết quả KHẲNG ĐỊNH ĐƯỢC. ", "b"),
            (f"{nf(C.huim['database']['n_rows'])} fingerprint được chuyển "
             f"thành {nf(C.huim['database']['n_non_empty_transactions'])} "
             f"utility transaction; EFIM chạy được trên chúng và trả về kết "
             f"quả. Nhưng 'hợp lý' có một điều kiện: q và p KHÔNG tồn tại "
             "trong dữ liệu Wi-Fi, chúng phải được định nghĩa, nên tính hợp lý "
             "là tính hợp lý CỦA ĐỊNH NGHĨA, không phải một tính chất của bộ "
             "dữ liệu. Đây là mô hình đề xuất của bài tìm hiểu, không phải một phương "
             "pháp chuẩn hoá đã được công nhận.", "")])

    D.h(2, "RQ2 — minUtil ảnh hưởng thế nào đến số HUI, runtime và bộ nhớ?")
    o1 = C.o["observation_1_threshold_vs_hui_count"]
    o2 = C.o["observation_2_cost_of_lowering_threshold"]
    D.p("Ảnh hưởng là PHI TUYẾN và rất gắt. " +
        "; ".join(
            f"{MODEL_VN.get(m, m).split(' — ')[0]}: "
            f"{r['n_runs_zero_huis']} lần chạy cho 0 HUI ở ngưỡng cao, số HUI "
            f"lớn nhất {nf(r['max_n_huis_observed'])}"
            for m, r in o1.items()) +
        ". Runtime trải " +
        "; ".join(f"{r['runtime_s_min']:.2f}–{r['runtime_s_max']:.2f} s"
                  for r in o2.values()) +
        ", bộ nhớ đỉnh trải " +
        "; ".join(f"{r['peak_mem_delta_mb_min']:.1f}–"
                  f"{r['peak_mem_delta_mb_max']:.1f} MB"
                  for r in o2.values()) +
        ". Runtime theo số nút cây đã duyệt; bộ nhớ theo kích thước kết quả.",
        align="justify")

    D.h(2, "RQ3 — Signal utility và discriminative utility tạo ra các HUI khác "
           "nhau thế nào?")
    ov = C.o["observation_3_models_select_different_aps"]["pairwise_overlap"]
    if ov:
        D.p("Khác nhau thật, cả về tập AP được chọn lẫn về hình dạng đường "
            "cong ngưỡng. Mức chồng lấp: " +
            "; ".join(f"{k} → Jaccard {v['jaccard']:.3f}, trùng top-10 "
                      f"{v['top10_overlap']}/10" for k, v in ov.items()) +
            ".", align="justify")
    D.p("Một khác biệt định tính cũng đáng ghi: Model B cho đường cong số HUI "
        "theo ngưỡng MƯỢT hơn hẳn Model A, vốn nhảy gần như trực tiếp từ 'không "
        "có gì' sang 'vượt ngân sách'. [OUR INTERPRETATION] Điều này phù hợp "
        "với việc p biến thiên theo AP làm phân bố utility giãn ra, nên ngưỡng "
        "có nhiều chỗ để tách các itemset hơn.", align="justify")

    D.h(2, "RQ4 — HUIM có dùng được như một phương pháp chọn WAP để giảm số "
           "chiều của IPS không?")
    D.rich([("Về mặt cơ học thì được, và điều kiện cần đã thoả: ", "b"),
            ("tập hợp các AP xuất hiện trong HUI vẫn NHỎ ngay cả khi số HUI "
             "lên tới hàng trăm nghìn. Nếu tập hợp này phình ra bằng toàn bộ "
             f"{C.cs['waps_detected_in_train']} AP thì phương pháp sẽ không "
             "chọn gì cả. Việc nó không phình ra là kết quả cho phép hướng "
             "nghiên cứu này tồn tại.", "")])
    w = o5["verdict_inputs"]
    D.rich([("Nhưng 'dùng được' khác với 'đáng dùng'. ", "b"),
            (f"Trên {w['n_comparisons']} ngân sách khớp nhau, HUIM vượt chọn "
             f"ngẫu nhiên ở {w['huim_beats_random']}/{w['n_comparisons']}, "
             f"vượt top-n theo mutual information ở {w['huim_beats_top_mi']}/"
             f"{w['n_comparisons']}, vượt top-n theo support ở "
             f"{w['huim_beats_top_support']}/{w['n_comparisons']}. Đối chứng "
             "top-n-theo-MI là đối chứng quan trọng nhất, vì nó dùng chính "
             "thước đo mà Model B được cho sẵn nhưng KHÔNG khai thác itemset.",
             "")])

    D.h(2, "RQ5 — Giảm số WAP bằng HUIM ảnh hưởng thế nào đến độ chính xác "
           "Building/Floor?")
    D.p(f"Baseline toàn bộ {b['n_waps']} WAP: Building "
        f"{pc(b['building_accuracy'])}, Floor {pc(b['floor_accuracy'])}, Joint "
        f"{pc(b['joint_accuracy'])}.", align="justify")
    if o4["per_model_best_topn"]:
        D.p("Cấu hình HUIM tốt nhất mỗi model: " +
            "; ".join(f"{MODEL_VN.get(m, m).split(' — ')[0]} với "
                      f"{d['n_waps']} WAP ({d['feature_reduction_pct']:.2f}% "
                      f"giảm chiều) → Joint {pc(d['joint_accuracy'])} "
                      f"({d['delta_joint_vs_baseline']*100:+.2f} pp)"
                      for m, d in o4["per_model_best_topn"].items()) + ".",
            align="justify")
    D.rich([("Điểm phải nói rõ: ", "b"),
            ("Building accuracy chịu được giảm chiều rất mạnh, Floor accuracy "
             "thì không. Vì Joint bị chặn bởi Floor, mọi kết luận lạc quan dựa "
             "trên Building accuracy sẽ là gây hiểu nhầm.", "")])

    D.h(2, "RQ6 — Có trade-off hợp lý giữa giảm chiều, chi phí khai thác và "
           "chất lượng định vị không?")
    sm = o4.get("smallest_subset_matching_baseline")
    if sm:
        D.p(f"Có một điểm làm việc đáng chú ý: {sm['n_waps']} WAP "
            f"({sm['feature_reduction_pct']:.2f}% giảm chiều) đạt "
            f"{pc(sm['joint_accuracy'])} joint accuracy, bằng hoặc hơn "
            f"baseline. Chi phí khai thác để có được tập đó được ghi trong "
            f"bảng ablation chương 14.", align="justify")
    else:
        D.p("Trong các cấu hình đã thử, KHÔNG có tập con nào do HUIM chọn đạt "
            "được mức joint accuracy của baseline toàn bộ WAP. Trade-off vì "
            "vậy là có thật nhưng không thuận lợi: giảm chiều phải trả giá "
            "bằng độ chính xác.", align="justify")
    D.p("Về chi phí khai thác, trade-off rõ ràng và nằm ở phía ngược với trực "
        "giác: ngưỡng CAO vừa rẻ hơn vừa cho tập AP gọn hơn và đủ dùng, trong "
        "khi ngưỡng thấp đắt theo cấp số mà hầu như chỉ thêm các tập con.",
        align="justify")

    D.h(2, "RQ7 — Kết quả thực nghiệm cho ta hiểu NGƯỢC LẠI điều gì về bản "
           "chất HUIM?")
    D.bullets([
        "HUIM đếm itemset, không đếm phát hiện. Số HUI khổng lồ trên một bảng "
        "chữ cái nhỏ là dấu hiệu của các tập con lồng nhau, không phải của "
        "nhiều tri thức hơn.",
        "Chặn trên điều khiển TÌM KIẾM, không điều khiển KẾT QUẢ. EFIM không "
        "'kém đi' ở ngưỡng thấp; nó đang bị yêu cầu viết ra một đáp án đúng có "
        "kích thước lũy thừa.",
        "Hàm utility là PHÁT BIỂU BÀI TOÁN, không phải một bước xếp hạng hậu "
        "kỳ. Đổi p là đổi cả cây tìm kiếm.",
        "minUtil không phải núm chất lượng. Nó là núm 'nhóm lớn đến đâu mới "
        "được coi là một mẫu'.",
        "HUIM không có mục tiêu giám sát. Vì thế không có định lý nào bảo đảm "
        "một HUI là đặc trưng tốt; chỉ có số liệu.",
    ])

    D.h(2, "Đóng góp thực sự của bài tìm hiểu")
    D.rich([("Phát biểu thận trọng và đúng mức: ", "b"),
            ("Bài tìm hiểu khảo sát khả năng thích nghi mô hình High Utility Itemset "
             "Mining cho bài toán lựa chọn nhóm Access Point trong Wi-Fi "
             "fingerprint indoor positioning.", "i")])
    D.bullets([
        "Một ánh xạ HUIM ↔ IPS được phát biểu tường minh, với ba định nghĩa "
        "utility khác nhau và một ablation cô lập đúng một biến.",
        "Một bản cài đặt EFIM được kiểm chứng đối chiếu oracle brute-force, "
        "kèm bộ kiểm thử tái lập được.",
        "Một mô tả thực nghiệm về hành vi ngưỡng của HUIM trên dữ liệu Wi-Fi "
        "thưa và rộng — khác biệt rõ rệt so với dữ liệu giỏ hàng.",
        "Một đánh giá có ĐỐI CHỨNG, tức là có thể cho kết quả âm, và kết quả "
        "được báo cáo đúng như đo được.",
        "Một audit dữ liệu phát hiện các bất thường không có trong tài liệu bộ "
        "dữ liệu (fingerprint rỗng, giá trị 0 dBm theo thiết bị, SPACEID rỗng "
        "trong validation, đơn vị toạ độ không được tài liệu hoá).",
    ])
    D.p("KHÔNG phải đóng góp: việc chọn Access Point (đã có từ Chen et al., "
        "IEEE TKDE 2006), việc dùng mutual information làm tiêu chí phân biệt "
        "(Song et al., ISPRS IJGI 2016), thuật toán EFIM, hay bất kỳ quyền ưu "
        "tiên novelty nào.", align="justify")
    D.page_break()

    D.h(1, "18. Hướng phát triển")
    D.bullets([
        "Khai thác HUI theo từng lớp vị trí (HUI Signature Matching): thay vì "
        "dùng HUIM để chọn đặc trưng rồi giao cho k-NN, hãy khai thác signature "
        "HUI riêng cho mỗi BUILDINGID_FLOOR rồi so khớp fingerprint kiểm định "
        "với các signature bằng điểm utility có trọng số. Đây là một ứng dụng "
        "KHÁC HẲN của HUIM và phải được tách riêng khỏi pipeline chính.",
        "Dùng các biến thể HUIM phù hợp hơn với cấu trúc đã quan sát: vì tập "
        "đáp án phần lớn là các tập con lồng nhau, các bài toán 'closed high "
        "utility itemset' hoặc 'top-k high utility itemset' sẽ cho cùng thông "
        "tin với kết quả nhỏ hơn nhiều bậc — và tránh được hẳn vấn đề bùng nổ "
        "đã mô tả ở Quan sát 1. Đây là hướng phát triển tự nhiên nhất rút ra "
        "trực tiếp từ kết quả.",
        "Đưa mối quan hệ không gian vào utility: hiện tại p(i) chỉ phụ thuộc "
        "mutual information với nhãn. Một định nghĩa utility có tính đến vị "
        "trí hình học của AP, hoặc tính đến mức dư thừa giữa các AP, có thể "
        "tránh việc chọn nhiều AP mang cùng một thông tin.",
        "So sánh với các phương pháp giảm chiều đã được công nhận (PCA, "
        "mutual-information feature selection có xử lý dư thừa như mRMR, "
        "Random Forest feature importance) ở cùng ngân sách đặc trưng, để đặt "
        "HUIM vào đúng vị trí của nó trong bức tranh rộng hơn.",
        "Kiểm chứng trên bộ dữ liệu fingerprint khác và mới hơn, vì mọi kết "
        "luận hiện tại chỉ thuộc về UJIIndoorLoc 2013.",
        "Dùng SPMF (hoặc một cài đặt tham chiếu khác) khi có JVM, để đối chiếu "
        "cả tính đúng và hiệu năng với một triển khai đã được cộng đồng kiểm "
        "chứng.",
        "Nghiên cứu quy trình chọn ngưỡng: vùng chuyển pha rất hẹp, nên một "
        "phương pháp tự động xác định điểm làm việc là điều kiện để phương "
        "pháp có thể dùng trong thực tế.",
    ])
    D.page_break()


# ===========================================================================
def appendix_cheatsheet(D: Doc, C) -> None:
    o4 = C.o["observation_4_feature_reduction_vs_accuracy"]
    o5 = C.o["observation_5_huim_vs_controls"]
    o1 = C.o["observation_1_threshold_vs_hui_count"]
    b = o4["baseline_all_520"]
    cfg = C.cfg
    pr = C.huim["preprocessor"]
    hm = C.huim["utility_models"]
    w = o5["verdict_inputs"]
    best_line = "; ".join(
        f"{MODEL_VN.get(m, m).split(' — ')[0]}: {d['n_waps']} WAP → Joint "
        f"{pc(d['joint_accuracy'])}"
        for m, d in o4["per_model_best_topn"].items()) or "N/A"

    D.h(1, "Phụ lục A — Những câu tôi phải trả lời được khi cô hỏi")
    D.p("Mỗi câu 2–5 câu trả lời. Mọi con số đọc từ log thực nghiệm.",
        align="justify")

    qa = [
        ("1. HUIM là gì?",
         "High Utility Itemset Mining: tìm các tập item có TỔNG ĐỘ HỮU ÍCH "
         "(utility) vượt một ngưỡng minUtil do người dùng đặt. Utility của một "
         "itemset là tổng, trên các giao dịch chứa nó, của tổng theo item của "
         "q(i,T) × p(i). Nó là bài toán phát hiện mẫu KHÔNG giám sát."),
        ("2. Khác Frequent Itemset Mining thế nào?",
         "Frequent Itemset Mining đo TẦN SUẤT (support — chỉ đếm số giao dịch). "
         "HUIM đo GIÁ TRỊ. Một mặt hàng có thể xuất hiện khắp nơi mà giá trị "
         "gần 0 (túi nilon), hoặc hiếm mà rất giá trị (máy ảnh); support không "
         "phân biệt được hai trường hợp đó. Quan trọng hơn về mặt thuật toán: "
         "support có downward closure nên cắt tỉa được trực tiếp, utility thì "
         "không. LƯU Ý TRUNG THỰC — trên UJIIndoorLoc, thực nghiệm của em cho "
         "thấy ở mức TỪNG AP thì tần suất và lượng thông tin gần như trùng "
         "nhau (xem mục 15.6), nên khác biệt giữa hai bài toán KHÔNG thể hiện "
         "ra ở đó; nó thể hiện ở cách ĐỊNH NGHĨA hàm utility."),
        ("3. Utility là gì?",
         "Utility của một itemset X là u(X) = Σ(T ∈ g(X)) u(X,T), với "
         "u(X,T) = Σ(i ∈ X) q(i,T) × p(i) và g(X) là tập giao dịch chứa X. Nói "
         "gọn: cộng giá trị của mọi item của X trong mọi giao dịch có chứa đủ "
         "X."),
        ("4. Internal utility là gì?",
         "q(i,T): 'lượng' của item i trong giao dịch T. Trong bài toán giỏ "
         "hàng là SỐ LƯỢNG mua. Đặc điểm nhận dạng: phụ thuộc CẢ item VÀ giao "
         "dịch. Trong bài tìm hiểu này q(i,T) là cường độ RSSI của AP i trong "
         f"fingerprint T, đã chuẩn hoá về số nguyên dương từ 1 đến "
         f"{pr['q_max']}."),
        ("5. External utility là gì?",
         "p(i): 'giá trị đơn vị' của item i. Trong giỏ hàng là LỢI NHUẬN mỗi "
         "đơn vị. Đặc điểm nhận dạng: KHÔNG phụ thuộc giao dịch — là thuộc "
         "tính của riêng item. Trong bài tìm hiểu này p(i) là mức độ phân biệt vị trí "
         "của AP, đo bằng mutual information (Model A đặt p ≡ 1 làm đối "
         "chứng)."),
        ("6. minUtil là gì?",
         "Ngưỡng tối thiểu: X là High Utility Itemset khi u(X) ≥ minUtil. Vì "
         "utility tuyệt đối phụ thuộc thang đo của q và p, bài tìm hiểu luôn biểu "
         "diễn minUtil theo % tổng utility toàn database — đây là điểm phải "
         "nhấn, vì tổng utility của ba model chênh nhau nhiều lần dù cùng một "
         "cơ sở dữ liệu."),
        ("7. TWU là gì?",
         "Transaction Weighted Utilization: TWU(X) = Σ(T ∈ g(X)) TU(T), với "
         "TU(T) là tổng utility của mọi item trong T. Nó là CHẶN TRÊN cho "
         "utility của X và của mọi tập cha của X, vì u(Y,T) ≤ TU(T) và "
         "g(Y) ⊆ g(X). Quan trọng: TWU CÓ tính anti-monotone, nên cắt tỉa bằng "
         "TWU là an toàn."),
        ("8. Vì sao utility không anti-monotone?",
         "Vì thêm một item gây ra hai tác động trái chiều: cộng thêm utility "
         "của item mới (đẩy utility LÊN), nhưng đồng thời thu hẹp tập giao "
         "dịch chứa itemset (đẩy utility XUỐNG). Phản ví dụ cụ thể trong ví dụ "
         "chuẩn: u({b}) = 16 < u({b,d}) = 30, nhưng u({b,d,f}) < u({b,d}). Hệ "
         "quả: không thể cắt nhánh khi u(X) < minUtil, phải cắt bằng chặn "
         "trên."),
        ("9. EFIM prune như thế nào?",
         "Hai chặn trên. LOCAL UTILITY lu(α,z): nếu < minUtil thì loại item z "
         "khỏi TOÀN BỘ cây con của α (tập còn lại gọi là Secondary). SUBTREE "
         "UTILITY su(α,z): nếu < minUtil thì KHÔNG BƯỚC VÀO nhánh α∪{z} (tập "
         "vượt ngưỡng gọi là Primary). su chặt hơn lu vì nó chỉ cộng utility "
         "của các item đứng SAU z. Cả hai tính được trong một lượt quét nhờ "
         "Fast Utility Counting. Lưu ý đẹp: lu(∅,z) chính bằng TWU(z)."),
        ("10. Vì sao chọn EFIM?",
         "Căn cứ chính là một đánh giá thực nghiệm ĐỘC LẬP: Zhang và cộng sự, "
         "Expert Systems with Applications, vol. 101, pp. 91–115, 2018, "
         "DOI 10.1016/j.eswa.2018.02.008 — không do tác giả EFIM viết. Thêm "
         "hai lý do riêng cho bộ dữ liệu này: transaction merging có đất dùng "
         f"({nf(C.tr['duplicate_rows_wap_only'])} dòng có vector WAP trùng "
         "nhau, và dữ liệu thưa nên các giao dịch sau chiếu va nhau nhiều), và "
         "cơ sở dữ liệu RỘNG chứ không SÂU nên chi phí bộ nhớ của hướng "
         "utility-list đáng lo hơn."),
        ("11. Một fingerprint được biến thành transaction thế nào?",
         "Một dòng CSV = một transaction. Transaction đó chứa đúng những AP "
         f"được PHÁT HIỆN trong lần quét đó, tức những cột có giá trị khác "
         f"100. Trung bình mỗi transaction có "
         f"{C.o['context']['mean_detections_per_fingerprint']} item trên "
         f"{C.tr['n_wap_columns_detected']} item khả dĩ. "
         f"{C.tr['anomaly_probes']['n_empty_fingerprints']} dòng không phát "
         "hiện AP nào nên tạo transaction rỗng và bị thuật toán tự bỏ."),
        ("12. WAP được biến thành item thế nào?",
         "Mỗi cột WAP001…WAP520 là một item. Item thuộc transaction KHI VÀ CHỈ "
         "KHI AP đó được phát hiện. Đây là điểm mấu chốt: 'không phát hiện' "
         "ánh xạ thành ITEM VẮNG MẶT, tuyệt đối không phải thành một utility "
         "lớn — dù giá trị thô của nó (100) là số LỚN NHẤT trong ma trận."),
        ("13. RSSI được biến thành internal utility thế nào?",
         f"q(i,T) = round(1 + (RSSI − RSSI_min)/(RSSI_max − RSSI_min) × "
         f"({pr['q_max']} − 1)), với RSSI_min = {pr['rssi_min_train']:g} dBm và "
         f"RSSI_max = {pr['rssi_max_train']:g} dBm lấy TRÊN trainingData. Tín "
         f"hiệu yếu nhất → q = 1, mạnh nhất → q = {pr['q_max']}. Lý do phải "
         "làm vậy: RSSI là số ÂM, còn EFIM và mọi chặn trên TWU/lu/su yêu cầu "
         "utility DƯƠNG."),
        ("14. External utility của WAP lấy từ đâu?",
         "Từ mutual information I(A_i ; Y) giữa trạng thái của AP và nhãn "
         f"BUILDINGID_FLOOR, tính trên trainingData, rồi chuẩn hoá: "
         f"p(i) = max(MI_i, 10⁻⁶) / max_j MI_j. Entropy nhãn H(Y) = "
         f"{hm['B_discriminative']['label_entropy_H_Y_bits']} bit; AP thông "
         f"tin nhất cho {hm['B_discriminative']['mi_bits_max']} bit, tức "
         f"{hm['B_discriminative']['mi_bits_max_as_fraction_of_H_Y']*100:.1f}% "
         "H(Y). Đây là tiêu chí mà literature chọn AP gọi là information gain "
         "(Chen et al., IEEE TKDE 2006)."),
        ("15. Vì sao không được tính MI trên validation?",
         "Vì đó là DATA LEAKAGE. Nếu p được tính từ validationData thì tập AP "
         "được chọn đã 'biết trước' câu trả lời của bài kiểm tra; độ chính xác "
         "sẽ cao giả tạo và không nói gì về dữ liệu chưa từng thấy. Bài tìm hiểu "
         "CƯỠNG CHẾ điều này bằng mã: hàm build_external_utility nhận tham số "
         "split_name và RAISE lỗi nếu khác 'training' — có unit test riêng cho "
         "cơ chế đó."),
        ("16. HUIM giúp IPS ở bước nào?",
         "Ở PHA OFFLINE, bước chọn đặc trưng. Luồng: trainingData → utility "
         "transaction → EFIM → tập HUI → xếp hạng ra tập AP được chọn → k-NN "
         "chỉ dùng các cột AP đó → đánh giá trên validationData. Pha ONLINE "
         "không chạy HUIM, nó chỉ nhận danh sách AP đã chọn, nên chi phí khai "
         "thác là chi phí một lần."),
        ("17. Baseline là gì?",
         f"Hai baseline. (1) ALL-WAP: toàn bộ {b['n_waps']} cột, Joint "
         f"accuracy {pc(b['joint_accuracy'])} — baseline chính. (2) "
         f"{C.cs['waps_detected_in_train']} AP từng được phát hiện trong "
         "training — để tách phần giảm chiều MIỄN PHÍ ra khỏi phần công của "
         "HUIM. Ngoài ra còn ba ĐỐI CHỨNG ở ngân sách khớp nhau: random-n, "
         "top-n theo support, top-n theo MI."),
        ("18. Accuracy nào đang sử dụng?",
         f"Building Accuracy, Floor Accuracy và Joint Building-Floor Accuracy "
         f"(độ đo chính), cả ba suy ra từ CÙNG một dự đoán nhãn joint nên nhất "
         f"quán với nhau. Thêm macro F1 vì các lớp mất cân bằng, confusion "
         f"matrix, và sai số định vị theo đơn vị toạ độ. Baseline: Building "
         f"{pc(b['building_accuracy'])}, Floor {pc(b['floor_accuracy'])}, Joint "
         f"{pc(b['joint_accuracy'])}."),
        ("19. Feature reduction là gì?",
         f"Feature Reduction % = (1 − số_WAP_được_chọn / "
         f"{C.tr['n_wap_columns_detected']}) × 100%. Kết quả tốt nhất mỗi "
         f"model: {best_line}. Lưu ý trung thực: bỏ "
         f"{C.tr['n_wap_columns_detected'] - C.cs['waps_detected_in_train']} "
         f"cột không bao giờ được phát hiện đã cho "
         f"{(1 - C.cs['waps_detected_in_train']/C.tr['n_wap_columns_detected'])*100:.2f}% "
         "giảm chiều MIỄN PHÍ, không nhờ HUIM."),
        ("20. Nếu minUtil giảm thì chuyện gì xảy ra?",
         "Số HUI không lớn dần mà BÙNG NỔ. " +
         "; ".join(f"{MODEL_VN.get(m, r).split(' — ')[0] if False else MODEL_VN.get(m, m).split(' — ')[0]}: "
                   f"{r['n_runs_zero_huis']} lần chạy 0 HUI ở ngưỡng cao, số "
                   f"HUI lớn nhất {nf(r['max_n_huis_observed'])}"
                   for m, r in o1.items()) +
         ". Lý do: nếu một nhóm k AP đạt ngưỡng thì toàn bộ 2^k − 1 tập con "
         "của nó cũng đạt gần như đồng thời. Runtime và bộ nhớ tăng theo, và "
         "các lần chạy vượt ngân sách bị dừng CÓ KIỂM SOÁT với trạng thái "
         "ABORTED_RESOURCE_LIMIT."),
        ("21. HUI nhiều hơn có chắc Accuracy cao hơn không?",
         "KHÔNG, và đây là câu hỏi sai. Tập HUI lớn hơn ở minUtil thấp hơn "
         "phần lớn chỉ là THÊM CÁC TẬP CON của cùng những nhóm AP: số HUI tăng "
         "mà số AP riêng biệt gần như không tăng. Số liệu cho thấy hàng trăm "
         "nghìn HUI vẫn chỉ đến từ vài chục WAP. Thứ làm thay đổi accuracy là "
         "NHỮNG AP NÀO được chọn, không phải bao nhiêu itemset nhắc đến "
         "chúng."),
        ("22. Điểm yếu lớn nhất của phương pháp là gì?",
         "Ánh xạ utility mang tính THIẾT KẾ. q và p không tồn tại trong dữ "
         "liệu Wi-Fi nên phải tự định nghĩa; một định nghĩa khác cho tập HUI "
         "khác và tập AP khác. Nói cách khác, 'các High Utility Itemset của "
         "UJIIndoorLoc' không phải một đối tượng xác định. Thứ hai: HUIM không "
         "phải bộ chọn đặc trưng CÓ GIÁM SÁT, nên không có gì bảo đảm một HUI "
         "là đặc trưng tốt — phải chứng minh bằng đối chứng. Thứ ba: vùng "
         "ngưỡng dùng được rất hẹp."),
        ("23. Điều gì là đóng góp thực sự của bài tìm hiểu?",
         "Phát biểu đúng mức: bài tìm hiểu KHẢO SÁT khả năng thích nghi mô hình HUIM "
         "cho bài toán chọn nhóm Access Point trong Wi-Fi fingerprint indoor "
         "positioning. Cụ thể: một ánh xạ HUIM ↔ IPS tường minh với ba định "
         "nghĩa utility và ablation cô lập một biến; một bản cài đặt EFIM được "
         "kiểm chứng bằng oracle brute-force; một mô tả thực nghiệm hành vi "
         "ngưỡng trên dữ liệu Wi-Fi thưa-rộng; và một đánh giá CÓ ĐỐI CHỨNG, "
         "tức là có thể cho kết quả âm."),
        ("24. Phần nào dựa trên literature?",
         "Toàn bộ định nghĩa HUIM (item, itemset, transaction, q, p, u, TU, "
         "TWU, minUtil, HUI) — Yao et al. 2004, Liu et al. 2005, Gan et al. "
         "IEEE TKDE 2021. Thuật toán EFIM và các chặn trên của nó — Zida et "
         "al. 2017. Mutual information làm thước đo phân biệt AP — Chen et al. "
         "IEEE TKDE 2006, Song et al. ISPRS IJGI 2016. k-NN làm baseline "
         "fingerprint — Bahl & Padmanabhan 2000, Torres-Sospedra et al. ESWA "
         "2015. Bộ dữ liệu — Torres-Sospedra et al. IPIN 2014."),
        ("25. Phần nào là đề xuất của nhóm?",
         "Ánh xạ fingerprint → transaction; định nghĩa RSSI → internal "
         "utility; định nghĩa mức phân biệt của AP → external utility (ba "
         "biến thể A/B/C); và quy tắc xếp hạng HUI → tập AP được chọn "
         "(utility_contribution). Kèm phát biểu bắt buộc: trong phạm vi "
         "literature review đã kiểm chứng, chưa tìm thấy bằng chứng đủ mạnh để "
         "coi ánh xạ HUIM → UJIIndoorLoc này là phương pháp chuẩn hoá đã được "
         "công nhận."),
    ]
    for q, a in qa:
        D.h(3, q)
        D.p(a, align="justify")

    D.h(2, "Ba câu hỏi khó mà cô có thể hỏi thêm")
    for q, a in [
        ("Nếu top-n theo mutual information cũng tốt bằng HUIM thì bài tìm hiểu còn "
         "giá trị gì?",
         f"Đó là một kết quả âm có giá trị khoa học, và bài tìm hiểu báo cáo nó đúng "
         f"như đo được: trên {w['n_comparisons']} ngân sách khớp nhau, HUIM "
         f"vượt top-n theo MI ở {w['huim_beats_top_mi']} trường hợp. Giá trị "
         f"nằm ở chỗ đã THIẾT LẬP được so sánh đó: nếu không có đối chứng này, "
         f"một báo cáo có thể trình bày cùng những con số accuracy như một "
         f"thành công mà không ai kiểm tra được. Biết rằng khai thác itemset "
         f"KHÔNG thêm gì so với thước đo nó được cho sẵn là một tri thức hữu "
         f"ích về bản chất HUIM."),
        ("Sao không báo cáo sai số định vị theo mét như các bài báo khác?",
         "Vì không xác minh được. Mô tả thuộc tính chính thức của bộ dữ liệu "
         "(UCI) và trang web của chính nhóm tác giả đều KHÔNG nêu hệ toạ độ "
         "hay đơn vị của LONGITUDE/LATITUDE — cả hai chỉ cho khoảng giá trị. "
         "Toàn văn bài báo IPIN 2014 nằm sau tường phí không truy cập được. "
         "Hộp giới hạn dữ liệu có kích thước hợp lý cho một campus ba toà nhà "
         "nếu đơn vị là mét, nhưng đó là SUY LUẬN, không phải bằng chứng. Đồ "
         "án báo cáo sai số theo đơn vị toạ độ và ghi rõ hạn chế này."),
        ("Số liệu trong báo cáo có đáng tin không?",
         "Báo cáo được SINH TỰ ĐỘNG từ các file kết quả: results/*.json, "
         "results/metrics/*.csv, results/tables/*.csv, figures/*.png. Script "
         "sinh báo cáo không chứa bất kỳ con số thực nghiệm nào — nếu thiếu "
         "file kết quả thì nó báo lỗi và dừng, chứ không in ra văn bản có lỗ. "
         "Mỗi biểu đồ còn lưu kèm một file CSV chứa đúng những dòng đã vẽ. Và "
         "mọi lần chạy vượt ngân sách tài nguyên đều được GIỮ trong log với "
         "trạng thái ABORTED_RESOURCE_LIMIT, không bị xoá để làm kết quả đẹp "
         "hơn."),
    ]:
        D.h(3, q)
        D.p(a, align="justify")
