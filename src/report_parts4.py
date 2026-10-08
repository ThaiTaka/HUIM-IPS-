"""Chapters 12-18, references and appendix of the Word report.

Every figure in these chapters is read from results/metrics/*.csv at build time.
"""
from __future__ import annotations

import json

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
def ch12(D: Doc, C) -> None:
    H = C.H.sort_values(["utility_model", "rel_minutil_pct"],
                        ascending=[True, False])
    D.h(1, "12. Kết quả HUIM")
    D.p("Toàn bộ số liệu trong chương này đọc từ "
        "results/metrics/huim_runs.csv. Không có giá trị nào được nhập tay.",
        align="justify")
    D.p(f"Cơ sở dữ liệu utility: {nf(C.huim['database']['n_rows'])} dòng "
        f"trainingData → {nf(C.huim['database']['n_non_empty_transactions'])} "
        f"giao dịch khác rỗng "
        f"({C.huim['database']['n_empty_fingerprints_dropped']} fingerprint "
        f"rỗng bị thuật toán tự bỏ), "
        f"{C.huim['database']['n_wap_columns']} item khả dĩ, độ dài giao dịch "
        f"trung bình {C.huim['database']['detections_per_transaction_mean']}.",
        align="justify")

    D.h(2, "12.1. Bảng kết quả đầy đủ")
    tbl = pd.DataFrame({
        "Utility model": [MODEL_VN.get(m, m).replace(" — ", " / ")
                          for m in H["utility_model"]],
        "minUtil (%)": [f"{v:g}" for v in H["rel_minutil_pct"]],
        "minUtil tuyệt đối": [nf(v, 0) for v in H["abs_minutil"]],
        "Trạng thái": ["COMPLETED" if s == "COMPLETED" else "ABORTED"
                       for s in H["status"]],
        "Số HUI": [nf(v) for v in H["n_huis"]],
        "Runtime (s)": [f"{v:,.2f}" for v in H["runtime_s"]],
        "Peak mem (MB)": [f"{v:,.1f}" for v in H["peak_memory_delta_mb"]],
        "Số WAP trong HUI": [int(v) for v in H["unique_waps_in_huis"]],
        "Giảm chiều (%)": [f"{v:.2f}" if v == v else "N/A"
                           for v in H["feature_reduction_pct_union"]],
        "Dài HUI TB": [f"{v:.2f}" for v in H["mean_hui_len"]],
        "Dài HUI max": [int(v) for v in H["max_hui_len"]],
        "Item sau TWU": [f"{int(a)}/{int(b)}" for a, b in
                         zip(H["items_after_twu_pruning"], H["items_initial"])],
        "Nút cây đã duyệt": [nf(v) for v in H["search_nodes_visited"]],
    })
    D.table(tbl, "Kết quả khai thác HUIM đầy đủ trên trainingData "
                 f"({len(H)} lần chạy). Giảm chiều tính theo tập hợp các WAP "
                 f"xuất hiện trong HUI", font_pt=7)

    D.h(2, "12.2. Ngưỡng minUtil và số lượng HUI")
    D.figure(FIGURES / "fig01_minutil_vs_hui_count.png",
             "Ngưỡng minUtil (theo % tổng utility, trục log, giảm dần sang "
             "phải) và số lượng High Utility Itemset tìm được. Vòng tròn đỏ = "
             "lần chạy dừng do hết ngân sách tài nguyên")
    for m, g in H.groupby("utility_model"):
        g = g.sort_values("rel_minutil_pct", ascending=False)
        nz = g[g["n_huis"] > 0]
        D.rich([(f"{MODEL_VN.get(m, m)}: ", "b"),
                (f"ở các ngưỡng từ {g['rel_minutil_pct'].max():g}% xuống "
                 f"{(nz['rel_minutil_pct'].max() if len(nz) else 0):g}% thuật "
                 f"toán trả về {int((g['n_huis'] == 0).sum())} lần chạy với 0 "
                 f"HUI; số HUI lớn nhất ghi nhận được là "
                 f"{nf(g['n_huis'].max())} tại "
                 f"{g.loc[g['n_huis'].idxmax(), 'rel_minutil_pct']:g}% "
                 f"(trạng thái {g.loc[g['n_huis'].idxmax(), 'status']}).", "")])

    D.h(2, "12.3. Chi phí: runtime và bộ nhớ")
    D.figure(FIGURES / "fig02_minutil_vs_runtime.png",
             "Ngưỡng minUtil và thời gian chạy (giây)")
    D.figure(FIGURES / "fig03_minutil_vs_peak_memory.png",
             "Ngưỡng minUtil và bộ nhớ đỉnh vượt trên mức nền (MB). Bộ nhớ "
             "được đo bằng cách lấy mẫu RSS của tiến trình mỗi 20 ms, để không "
             "làm sai lệch chính phép đo runtime")
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Runtime nhỏ nhất (s)": f"{g['runtime_s'].min():.2f}",
         "Runtime lớn nhất (s)": f"{g['runtime_s'].max():.2f}",
         "Peak mem nhỏ nhất (MB)": f"{g['peak_memory_delta_mb'].min():.2f}",
         "Peak mem lớn nhất (MB)": f"{g['peak_memory_delta_mb'].max():.1f}",
         "Số lần ABORTED": int((g["status"] != "COMPLETED").sum())}
        for m, g in H.groupby("utility_model")]),
        "Dải chi phí tính toán theo từng utility model", font_pt=9)
    ab = H[H["status"] != "COMPLETED"]
    if len(ab):
        D.p("Các lần chạy dừng có kiểm soát (được GIỮ LẠI trong log, không bị "
            "xoá):", align="justify")
        D.bullets([f"{MODEL_VN.get(r['utility_model'], r['utility_model'])} tại "
                   f"{r['rel_minutil_pct']:g}%: {r['abort_reason']}"
                   for _, r in ab.iterrows()])

    D.h(2, "12.4. Cấu trúc của các HUI tìm được")
    D.figure(FIGURES / "fig05_hui_length_distribution.png",
             "Phân bố độ dài HUI ở lần chạy COMPLETED có nhiều HUI nhất của "
             "mỗi utility model")
    comp = H[(H["status"] == "COMPLETED") & (H["n_huis"] > 0)]
    rows = []
    for m, g in comp.groupby("utility_model"):
        r = g.loc[g["n_huis"].idxmax()]
        rows.append({
            "Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
            "minUtil (%)": f"{r['rel_minutil_pct']:g}",
            "Số HUI": nf(r["n_huis"]),
            "Độ dài min / TB / max":
                f"{int(r['min_hui_len'])} / {r['mean_hui_len']:.2f} / "
                f"{int(r['max_hui_len'])}",
            "u(X) min / TB / max":
                f"{nf(r['hui_utility_min'], 0)} / "
                f"{nf(r['hui_utility_mean'], 0)} / "
                f"{nf(r['hui_utility_max'], 0)}",
            "Support TB": nf(r["hui_support_mean"], 1),
            "Số WAP riêng biệt": int(r["unique_waps_in_huis"]),
        })
    D.table(pd.DataFrame(rows),
            "Đặc tính của tập HUI phong phú nhất (và không bị cắt ngang) của "
            "mỗi model", font_pt=9)
    D.rich([("Một tỷ lệ cần chú ý: ", "b"),
            ("số HUI lớn hơn rất nhiều so với số WAP riêng biệt tham gia vào "
             "chúng. Đây là dấu hiệu nhận dạng của cơ chế được phân tích ở "
             "chương 15, Quan sát 1: các HUI phần lớn là TẬP CON CỦA NHAU, "
             "không phải những phát hiện độc lập. Một triệu HUI ở đây không "
             "phải một triệu phát hiện.", "")])

    D.h(2, "12.5. Cắt tỉa và không gian tìm kiếm")
    D.figure(FIGURES / "fig08_minutil_vs_items_surviving_twu.png",
             "Số item còn sống sau chặn TWU ở gốc cây, theo ngưỡng minUtil")
    D.figure(FIGURES / "fig07_minutil_vs_search_nodes.png",
             "Số nút cây tìm kiếm đã duyệt, theo ngưỡng minUtil")
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Item ban đầu": int(g["items_initial"].iloc[0]),
         "Item sau TWU (min–max)":
             f"{int(g['items_after_twu_pruning'].min())}–"
             f"{int(g['items_after_twu_pruning'].max())}",
         "Item bị loại bởi local utility (max)":
             nf(g["items_pruned_by_local_utility"].max()),
         "Ứng viên bị loại bởi subtree utility (max)":
             nf(g["candidates_pruned_by_subtree_utility"].max()),
         "Giao dịch được hợp nhờ merging (max)":
             nf(g["transactions_saved_by_merging"].max())}
        for m, g in H.groupby("utility_model")]),
        "Hiệu lực thực đo của từng cơ chế cắt tỉa và của transaction merging",
        font_pt=8)
    D.rich([("Transaction merging thực sự hoạt động trên dữ liệu này, ", "b"),
            ("với số giao dịch được hợp lên tới hàng chục triệu lượt trong các "
             "lần chạy sâu. Lý do mang tính đặc thù của Wi-Fi: phép chiếu liên "
             "tục bóc các AP đứng đầu khỏi mỗi giao dịch, phần còn lại là các "
             "'đuôi'; các fingerprint thu ở những điểm gần nhau có đuôi rất "
             "giống nhau, nên sau vài lần chiếu nhiều giao dịch trở nên GIỐNG "
             "NHAU HOÀN TOÀN và co lại thành một. Một cơ sở dữ liệu giỏ hàng, "
             "nơi mỗi hoá đơn mang tính cá biệt, hưởng lợi ít hơn nhiều.",
             "")])

    D.h(2, "12.6. Số WAP được giữ lại")
    D.figure(FIGURES / "fig04_minutil_vs_selected_waps.png",
             "Ngưỡng minUtil và số WAP trong tập hợp các AP xuất hiện ở HUI")
    D.rich([("Đây là kết quả quan trọng nhất của chương, và là điều kiện để "
             "phương pháp có thể dùng được cho IPS: ", "b"),
            ("ngay cả khi số HUI lên tới hàng trăm nghìn, số WAP riêng biệt "
             "tham gia vào chúng vẫn nhỏ. Nếu tập hợp này phình ra bằng toàn "
             f"bộ {C.cs['waps_detected_in_train']} AP thì 'HUIM-assisted "
             "feature selection' sẽ không chọn gì cả, và toàn bộ hướng nghiên "
             "cứu sẽ sụp. Số liệu cho thấy không phải như vậy.", "")])

    D.h(2, "12.7. Vì sao minUtil phải là tỷ lệ, không phải số tuyệt đối")
    o7 = C.o["observation_7_scale"]
    D.table(pd.DataFrame([
        {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
         "Tổng utility database": nf(d["total_database_utility"], 0),
         "TU(T) trung bình": nf(d["transaction_utility_mean"], 2),
         "TU(T) lớn nhất": nf(d["transaction_utility_max"], 2),
         "Khoảng p(i)": ("1 (hằng số)" if d.get("p_min") is None
                         else f"{d['p_min']:.3g} – {d['p_max']:.3g}")}
        for m, d in o7.items()]),
        "Cùng một cơ sở dữ liệu, cùng internal utility — chỉ p thay đổi",
        font_pt=9)
    vals = [d["total_database_utility"] for d in o7.values()]
    if vals and min(vals) > 0:
        D.p(f"[EXPERIMENT RESULT] Tổng utility toàn database chênh nhau "
            f"{max(vals)/min(vals):.2f} lần giữa các model, dù cơ sở dữ liệu, "
            f"các giao dịch và internal utility hoàn toàn giống nhau. Chỉ có "
            f"p thay đổi. Vì vậy một minUtil tuyệt đối (ví dụ 200.000) là vô "
            f"nghĩa khi so sánh giữa các model: cùng con số đó nằm ở những vị "
            f"trí hoàn toàn khác nhau trên ba phân bố utility.",
            align="justify")
    D.page_break()


# ===========================================================================
def ch13(D: Doc, C) -> None:
    I, b = C.I, C.base
    D.h(1, "13. Kết quả IPS")
    D.p("Toàn bộ số liệu đọc từ results/metrics/ips_results.csv. Mỗi điều kiện "
        "được đánh giá ĐÚNG MỘT LẦN trên validationData "
        f"({nf(C.va['n_rows'])} fingerprint), với cùng một cấu hình k-NN đã "
        "đóng băng.", align="justify")

    D.h(2, "13.1. Baseline")
    _gf = ((C.coord or {}).get("conclusion", {})
           .get("ground_distance_correction_factor"))
    D.table(pd.DataFrame([
        {"Độ đo": "Số đặc trưng (WAP)", "All 520 WAP": int(b["n_waps_selected"]),
         "465 WAP phát hiện trong training":
             int(C.base465["n_waps_selected"]) if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Giảm chiều so với 520",
         "All 520 WAP": "0.00%",
         "465 WAP phát hiện trong training":
             f"{C.base465['feature_reduction_pct']:.2f}%"
             if C.base465 is not None else "N/A"},
        {"Độ đo": "Building Accuracy", "All 520 WAP": pc(b["building_accuracy"]),
         "465 WAP phát hiện trong training":
             pc(C.base465["building_accuracy"]) if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Floor Accuracy", "All 520 WAP": pc(b["floor_accuracy"]),
         "465 WAP phát hiện trong training":
             pc(C.base465["floor_accuracy"]) if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Joint Building-Floor Accuracy",
         "All 520 WAP": pc(b["joint_building_floor_accuracy"]),
         "465 WAP phát hiện trong training":
             pc(C.base465["joint_building_floor_accuracy"])
             if C.base465 is not None else "N/A"},
        {"Độ đo": "Joint Macro F1", "All 520 WAP": f"{b['joint_macro_f1']:.4f}",
         "465 WAP phát hiện trong training":
             f"{C.base465['joint_macro_f1']:.4f}" if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Floor-within-1 Accuracy",
         "All 520 WAP": pc(b["floor_within_1_accuracy"]),
         "465 WAP phát hiện trong training":
             pc(C.base465["floor_within_1_accuracy"]) if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Sai số trung vị — toạ độ chiếu (m)",
         "All 520 WAP": f"{b['pos_median_error']:.2f}",
         "465 WAP phát hiện trong training":
             f"{C.base465['pos_median_error']:.2f}" if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Sai số trung vị — THỰC ĐỊA (m)",
         "All 520 WAP": f"{b['pos_median_error_ground_m']:.2f}",
         "465 WAP phát hiện trong training":
             f"{C.base465['pos_median_error_ground_m']:.2f}"
             if C.base465 is not None else "N/A"},
        {"Độ đo": "Sai số trung bình — toạ độ chiếu (m)",
         "All 520 WAP": f"{b['pos_mean_error']:.2f}",
         "465 WAP phát hiện trong training":
             f"{C.base465['pos_mean_error']:.2f}" if C.base465 is not None
             else "N/A"},
        {"Độ đo": "Sai số trung bình — THỰC ĐỊA (m)",
         "All 520 WAP": f"{b['pos_mean_error_ground_m']:.2f}",
         "465 WAP phát hiện trong training":
             f"{C.base465['pos_mean_error_ground_m']:.2f}"
             if C.base465 is not None else "N/A"},
        {"Độ đo": "p75 / p90 / p95 — THỰC ĐỊA (m)",
         "All 520 WAP": f"{b['pos_p75_error_ground_m']:.1f} / "
                        f"{b['pos_p90_error_ground_m']:.1f} / "
                        f"{b['pos_p95_error_ground_m']:.1f}",
         "465 WAP phát hiện trong training":
             (f"{C.base465['pos_p75_error_ground_m']:.1f} / "
              f"{C.base465['pos_p90_error_ground_m']:.1f} / "
              f"{C.base465['pos_p95_error_ground_m']:.1f}")
             if C.base465 is not None else "N/A"},
    ]), "Hai baseline. 'Toạ độ chiếu' là quy ước mà literature UJIIndoorLoc "
        "dùng khi trích sai số theo mét; 'thực địa' đã hiệu chỉnh biến dạng "
        "Web Mercator" + (f" (nhân {_gf:.4f})" if _gf else "")
        + " — xem mục 11.6", font_pt=9, widths=[2.4, 1.5, 2.0])
    D.rich([("Đối chiếu với mục tiêu nhóm đặt ra (7–8 m): ", "b"),
            (f"sai số TRUNG VỊ thực địa của baseline là "
             f"{b['pos_median_error_ground_m']:.2f} m — nằm DƯỚI dải mục tiêu. "
             f"Sai số TRUNG BÌNH thực địa là "
             f"{b['pos_mean_error_ground_m']:.2f} m — nằm TRÊN dải mục tiêu. "
             f"Hai con số chênh nhau vì phân bố sai số có đuôi dài: p95 lên "
             f"tới {b['pos_p95_error_ground_m']:.1f} m, do một số fingerprint "
             f"bị gán sai tầng hoặc sai toà nhà. Phải nêu rõ đang dùng thống "
             f"kê nào, nếu không con số sẽ gây hiểu nhầm.", "")])
    D.figure(FIGURES / "fig17_positioning_error_metres.png",
             "Sai số định vị (mét thực địa) so với dải mục tiêu 7–8 m, cho "
             "baseline và các cấu hình chính", width_in=6.2)
    D.rich([("Dự đoán từ chương 3 được kiểm chứng. ", "b"),
            (f"Audit đã dự đoán trước (mục 3.7) rằng phân loại toà nhà sẽ gần "
             f"như được giải quyết, còn tầng mới là phần khó, dựa trên việc "
             f"{C.tr['anomaly_probes']['ap_building_spread']['n_waps_in_exactly_1_building']}"
             f" AP chỉ nằm trong một toà nhà. Số liệu: Building Accuracy "
             f"{pc(b['building_accuracy'])} so với Floor Accuracy "
             f"{pc(b['floor_accuracy'])}. Vì Joint Accuracy bị chặn bởi thành "
             f"phần tầng, NHẦM TẦNG là toàn bộ vấn đề, và mọi phương pháp chọn "
             f"đặc trưng phải được đánh giá ở chỗ nó có bảo toàn khả năng phân "
             f"biệt TRONG CÙNG một toà nhà hay không.", "")])
    if C.base465 is not None:
        D.rich([("Phần giảm chiều MIỄN PHÍ. ", "b"),
                (f"Bỏ {C.tr['n_wap_columns_detected'] - int(C.base465['n_waps_selected'])} "
                 f"cột luôn bằng sentinel trong training cho ngay "
                 f"{C.base465['feature_reduction_pct']:.2f}% giảm chiều với "
                 f"joint accuracy {pc(C.base465['joint_building_floor_accuracy'])}"
                 f" (baseline: {pc(b['joint_building_floor_accuracy'])}). "
                 "Phần này KHÔNG được ghi công cho HUIM.", "")])

    D.h(2, "13.2. Chọn AP bằng union của HUI (minUtil là núm duy nhất)")
    U = I[I["family"] == "huim_union"]
    if len(U):
        D.table(pd.DataFrame([
            {"Utility model": MODEL_VN.get(r["utility_model"],
                                           r["utility_model"]).replace(" — ", " / "),
             "minUtil (%)": f"{float(r['rel_minutil_pct']):g}",
             "Mining": str(r.get("huim_status", "")),
             "Số HUI": nf(r.get("n_huis")),
             "Số WAP": int(r["n_waps_selected"]),
             "Giảm chiều": f"{r['feature_reduction_pct']:.2f}%",
             "Building": pc(r["building_accuracy"]),
             "Floor": pc(r["floor_accuracy"]),
             "Joint": pc(r["joint_building_floor_accuracy"]),
             "Macro F1": f"{r['joint_macro_f1']:.4f}",
             "Sai số trung vị": f"{r['pos_median_error']:.2f}",
             "FP không có AP nào":
                 int(r["val_rows_with_no_selected_wap_detected"])}
            for _, r in U.sort_values(
                ["utility_model", "rel_minutil_pct"],
                ascending=[True, False]).iterrows()]),
            "Chọn AP bằng hợp các WAP xuất hiện trong HUI. Cột cuối là số "
            "fingerprint kiểm định không phát hiện được AP nào trong tập đã "
            "chọn", font_pt=8)

    D.h(2, "13.3. Quét ngân sách đặc trưng: HUIM so với các đối chứng")
    D.figure(FIGURES / "fig06_selected_waps_vs_accuracy.png",
             "Số WAP được chọn (trục log) và Joint Building-Floor Accuracy. "
             "Đường nét gãy đen là baseline toàn bộ 520 WAP. Thanh lỗi của "
             "đường ngẫu nhiên là khoảng min–max trên 3 seed")
    o5 = C.o["observation_5_huim_vs_controls"]
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
            d["Random (TB)"] = (pc(r["control_random_mean"])
                                if "control_random_mean" in r else "—")
            data.append(d)
        D.table(pd.DataFrame(data),
                "Joint Building-Floor Accuracy ở các ngân sách đặc trưng khớp "
                "nhau. Đây là bảng quyết định bài tìm hiểu có kết quả dương hay "
                "không", font_pt=8)
        w = o5["verdict_inputs"]
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"Trên {w['n_comparisons']} ngân sách khớp nhau, lựa chọn "
                 f"HUIM tốt nhất vượt chọn ngẫu nhiên ở "
                 f"{w['huim_beats_random']}/{w['n_comparisons']} trường hợp, "
                 f"vượt top-n theo mutual information ở "
                 f"{w['huim_beats_top_mi']}/{w['n_comparisons']}, và vượt "
                 f"top-n theo số lần được phát hiện ở "
                 f"{w['huim_beats_top_support']}/{w['n_comparisons']}.", "")])

    D.h(2, "13.4. Giảm chiều và độ chính xác")
    D.figure(FIGURES / "fig09_feature_reduction_vs_accuracy.png",
             "Mức giảm chiều (%) và Joint Building-Floor Accuracy, gồm cả các "
             "điểm union (hình thoi) nơi minUtil là núm điều khiển duy nhất")
    o4 = C.o["observation_4_feature_reduction_vs_accuracy"]
    best = o4["per_model_best_topn"]
    if best:
        D.table(pd.DataFrame([
            {"Utility model": MODEL_VN.get(m, m).replace(" — ", " / "),
             "Số WAP": d["n_waps"],
             "Giảm chiều": f"{d['feature_reduction_pct']:.2f}%",
             "Building": pc(d["building_accuracy"]),
             "Floor": pc(d["floor_accuracy"]),
             "Joint": pc(d["joint_accuracy"]),
             "Δ Joint so với baseline":
                 f"{d['delta_joint_vs_baseline']*100:+.2f} pp",
             "Macro F1": f"{d['joint_macro_f1']:.4f}",
             "Sai số trung vị": f"{d['median_pos_error']:.2f}"}
            for m, d in best.items()]),
            "Cấu hình top-n tốt nhất của từng utility model (theo Joint "
            "Accuracy)", font_pt=9)
    sm = o4.get("smallest_subset_matching_baseline")
    if sm:
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                (f"Tập con nhỏ nhất do HUIM chọn mà ĐẠT HOẶC VƯỢT baseline "
                 f"toàn bộ {int(C.base['n_waps_selected'])} WAP về Joint "
                 f"Accuracy dùng {sm['n_waps']} WAP "
                 f"({sm['feature_reduction_pct']:.2f}% giảm chiều) và đạt "
                 f"{pc(sm['joint_accuracy'])} (điều kiện "
                 f"{sm['condition']}).", "")])
    else:
        D.rich([("[EXPERIMENT RESULT] ", "b"),
                ("KHÔNG có tập con nào do HUIM chọn đạt được mức Joint "
                 "Accuracy của baseline toàn bộ WAP. Kết quả này được báo cáo "
                 "đúng như nó là; phân tích nguyên nhân ở chương 15.", "")])
    D.figure(FIGURES / "fig11_selected_waps_vs_positioning_error.png",
             "Số WAP được chọn và sai số định vị trung vị (đơn vị toạ độ của "
             "bộ dữ liệu)")

    D.h(2, "13.5. Baseline so với HUIM — ba độ đo accuracy")
    D.figure(FIGURES / "fig10_baseline_vs_huim_accuracies.png",
             "Building / Floor / Joint Accuracy của baseline và của cấu hình "
             "HUIM tốt nhất mỗi utility model", width_in=6.4)

    if C.COST is not None and len(C.COST):
        D.h(2, "13.6. Đánh giá THỜI GIAN và BỘ NHỚ của hệ thống định vị")
        D.p("Chi phí khai thác HUIM đã đo ở chương 12. Mục này đo nửa còn lại — "
            "và đây mới là chỗ việc giảm chiều thực sự trả công: thời gian "
            "định vị một fingerprint, và bộ nhớ mà cơ sở dữ liệu vân tay "
            "chiếm.", align="justify")
        D.bullets([
            "Thời gian đo với n_jobs = 1 để con số là chi phí MỘT LÕI, khả "
            "chuyển giữa các máy, thay vì phụ thuộc lúc đó máy rảnh mấy lõi. "
            "Việc này không đổi kết quả dự đoán, chỉ đổi tốc độ.",
            "Mỗi phép đo lặp lại nhiều lần và lấy TRUNG VỊ; ở số chiều nhỏ, "
            "một lần dự đoán chỉ mất vài chục mili-giây nên bị nhiễu lịch "
            "biểu của hệ điều hành chi phối — vì vậy mỗi mẫu được lặp đủ để "
            "tích luỹ tối thiểu 0,5 giây công việc.",
            "Bộ nhớ cơ sở dữ liệu được tính CHÍNH XÁC (số dòng × số cột × kích "
            "thước phần tử), không ước lượng, và báo cáo cho float64 (bản cài "
            "đặt này), float32 và int8 (một hệ thống triển khai có thể dùng).",
        ])
        CO = C.COST.sort_values("n_features", ascending=False)
        D.table(pd.DataFrame([
            {"Điều kiện": r["condition"],
             "Số WAP": int(r["n_features"]),
             "Index sklearn": r["sklearn_algorithm"],
             "Thời gian build (s)": f"{r['fit_seconds']:.4f}",
             "Dự đoán 1111 FP (s)": f"{r['predict_total_seconds']:.3f}",
             "ms / fingerprint": f"{r['predict_ms_per_fingerprint']:.4f}",
             "CSDL float64 (MB)": f"{r['db_memory_float64_mb']:.2f}",
             "CSDL int8 (MB)": f"{r['db_memory_int8_mb']:.2f}",
             "Joint Acc": pc(r["joint_building_floor_accuracy"])}
            for _, r in CO.iterrows()]),
            "Thời gian và bộ nhớ của hệ thống định vị theo số đặc trưng "
            "(k-NN đã đóng băng, một lõi)", font_pt=7.5)
        D.figure(FIGURES / "fig16_ips_time_and_memory.png",
                 "Thời gian định vị một fingerprint (trái), bộ nhớ cơ sở dữ "
                 "liệu vân tay (giữa), và đánh đổi chi phí ↔ độ chính xác "
                 "(phải)", width_in=6.5)
        base_c = CO[CO["condition"] == "baseline_all_520"]
        if len(base_c):
            bc = base_c.iloc[0]
            best = CO.loc[CO["joint_building_floor_accuracy"].idxmax()]
            rows = []
            for _, r in CO.iterrows():
                if r["condition"] == "baseline_all_520":
                    continue
                rows.append({
                    "Điều kiện": r["condition"], "Số WAP": int(r["n_features"]),
                    "Nhanh hơn baseline":
                        f"{bc['predict_ms_per_fingerprint'] / r['predict_ms_per_fingerprint']:.2f}×",
                    "Bộ nhớ so với baseline":
                        f"{100*r['db_memory_float64_mb'] / bc['db_memory_float64_mb']:.1f}%",
                    "Δ Joint Acc":
                        f"{(r['joint_building_floor_accuracy'] - bc['joint_building_floor_accuracy'])*100:+.2f} pp"})
            D.table(pd.DataFrame(rows).head(12),
                    "Chi phí tương đối so với baseline toàn bộ WAP", font_pt=8)
            D.rich([("Kết quả quan trọng nhất của mục này: ", "b"),
                    (f"điều kiện có độ chính xác CAO NHẤT trong toàn bộ nghiên "
                     f"cứu là {best['condition']} với "
                     f"{int(best['n_features'])} WAP — đạt "
                     f"{pc(best['joint_building_floor_accuracy'])} joint "
                     f"accuracy, tức "
                     f"{(best['joint_building_floor_accuracy'] - bc['joint_building_floor_accuracy'])*100:+.2f} "
                     f"điểm so với baseline, trong khi nhanh hơn "
                     f"{bc['predict_ms_per_fingerprint'] / best['predict_ms_per_fingerprint']:.2f} lần "
                     f"và chỉ chiếm "
                     f"{100*best['db_memory_float64_mb'] / bc['db_memory_float64_mb']:.1f}% "
                     f"bộ nhớ. Giảm chiều VỪA rẻ hơn VỪA chính xác hơn — "
                     f"nhưng tập đặc trưng đó đến từ một tiêu chí đối chứng "
                     f"đơn giản, KHÔNG phải từ HUIM.", "")])
            D.rich([("Một chi tiết kỹ thuật đáng ghi: ", "b"),
                    ("đường cong thời gian không đơn điệu ở số chiều nhỏ nhất. "
                     "Lý do đã được ghi nhận trong log: với algorithm='auto', "
                     "scikit-learn chuyển sang chỉ mục dạng CÂY (kd_tree) khi "
                     "số chiều đủ nhỏ, và trên dữ liệu thưa như thế này một "
                     "cây lại chậm hơn duyệt vét cạn. Đây là hiệu ứng thuật "
                     "toán có thể giải thích được, không phải nhiễu đo.", "")])

    D.h(2, "13.7. Confusion matrix")
    D.figure(FIGURES / "fig12_confusion_matrices.png",
             "Confusion matrix nhãn BUILDINGID_FLOOR: baseline (trái) và cấu "
             "hình HUIM tốt nhất (phải). Màu theo tỷ lệ chuẩn hoá theo dòng",
             width_in=6.6)
    D.p("Cách đọc: các ô ngoài đường chéo nằm TRONG CÙNG một toà nhà là nhầm "
        "tầng; các ô nằm giữa hai toà nhà khác nhau là nhầm toà nhà và nghiêm "
        "trọng hơn nhiều. Hình cho thấy phần lớn lỗi thuộc loại thứ nhất, phù "
        "hợp với phân tích ở mục 13.1.", align="justify")

    rf = I[I["rf_joint_building_floor_accuracy"].notna()] \
        if "rf_joint_building_floor_accuracy" in I else pd.DataFrame()
    if len(rf):
        D.h(2, "13.8. Bộ phân loại phụ: Random Forest")
        D.table(pd.DataFrame([
            {"Điều kiện": r["condition"], "Số WAP": int(r["n_waps_selected"]),
             "k-NN Joint": pc(r["joint_building_floor_accuracy"]),
             "RF Joint": pc(r["rf_joint_building_floor_accuracy"]),
             "RF Building": pc(r["rf_building_accuracy"]),
             "RF Floor": pc(r["rf_floor_accuracy"])}
            for _, r in rf.iterrows()]),
            "Random Forest như kiểm tra phụ (KHÔNG thay thế so sánh chính). "
            "k-NN vẫn là bộ phân loại dùng cho mọi so sánh trong báo cáo",
            font_pt=9)
        D.p("Random Forest chỉ được chạy trên một số điều kiện chính để tiết "
            "kiệm tài nguyên. Nó có mặt để kiểm tra rằng các kết luận không "
            "phải là hiện tượng riêng của k-NN, chứ không phải để thay thế so "
            "sánh chính — đổi đồng thời cả bộ phân loại lẫn tập đặc trưng sẽ "
            "làm mất khả năng quy nguyên nhân.", align="justify")
    D.page_break()


# ===========================================================================
def ch14(D: Doc, C) -> None:
    D.h(1, "14. Ablation study")
    D.p("Bảng dưới đây sinh từ results/tables/ablation_study.csv, vốn được "
        "join từ results/metrics/ips_results.csv và "
        "results/metrics/huim_runs.csv. Chi phí khai thác (runtime, số HUI) "
        "luôn đặt cạnh độ chính xác mà nó tạo ra.", align="justify")
    cols = ["Method", "Utility Model", "WAP count", "Reduction %",
            "Building Acc %", "Floor Acc %", "Joint Acc %",
            "HUIM Runtime (s)", "HUI Count"]
    AB = C.AB
    show = AB[[c for c in cols if c in AB.columns]].copy()
    show.columns = ["Phương pháp", "Utility Model", "Số WAP", "Giảm chiều %",
                    "Building %", "Floor %", "Joint %", "HUIM Runtime (s)",
                    "Số HUI"][:len(show.columns)]
    D.table(show, "Ablation study đầy đủ: ALL WAP so với HUIM Signal utility, "
                  "HUIM Discriminative utility, HUIM Rare-discriminative, và "
                  "các đối chứng ở ngân sách khớp nhau", font_pt=7)
    D.p("Các điều kiện đối chứng được đưa vào bảng ablation một cách có chủ "
        "đích: một ablation chỉ so phương pháp với 'dùng tất cả' thì không "
        "phân biệt được CHỌN đặc trưng với XOÁ đặc trưng.", align="justify")
    D.p("Dạng đồ thị của bảng trên đã được trình bày ở mục 13.4.",
        size=11, italic=True)
    D.page_break()


# ===========================================================================
def ch16(D: Doc, C) -> None:
    D.h(1, "16. Hạn chế")
    D.p("Phần này được viết để một người phản biện nghiêm khắc không tìm ra "
        "điều gì mà báo cáo chưa tự nói ra.", align="justify")

    D.h(2, "16.1. Hạn chế về phương pháp")
    o6 = C.o.get("observation_6_strong_vs_discriminative", {})
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        D.rich([("Hạn chế lớn nhất, phát hiện SAU khi chạy thực nghiệm: ", "b"),
                (f"external utility của Model B gần như là một cách tham số "
                 f"hoá lại tần suất phát hiện. Tương quan hạng giữa số lần "
                 f"được phát hiện và mutual information trên "
                 f"{o6['n_detected_waps_compared']} AP là Spearman ρ = "
                 f"{o6['spearman_support_vs_mi_over_all_detected_waps']}. "
                 "Nguyên nhân: trạng thái 'không phát hiện' chiếm phần áp đảo "
                 "trong phân bố của mỗi AP, nên MI chủ yếu đo việc AP có được "
                 "nhìn thấy hay không ở từng tầng. Hệ quả là Model B KHÔNG "
                 "thực sự mang thông tin độc lập với Model 'tần suất' như "
                 "thiết kế ban đầu giả định, và ablation B–C vì vậy ít thông "
                 "tin hơn mong đợi. Chi tiết ở mục 10.5.", "")])
    D.bullets([
        "Ánh xạ utility mang tính THIẾT KẾ. q và p không tồn tại trong dữ "
        "liệu Wi-Fi; chúng được bài tìm hiểu định nghĩa. Một định nghĩa khác sẽ cho "
        "tập HUI khác và tập AP khác. Vì vậy 'các High Utility Itemset của "
        "UJIIndoorLoc' KHÔNG phải một đối tượng xác định — nó chỉ xác định "
        "tương đối với một cặp (q, p) do người phân tích chọn.",
        "HUIM không phải một bộ chọn đặc trưng có giám sát. Định nghĩa của "
        "HUIM không tối ưu bất kỳ mục tiêu phân loại nào. Mọi ích lợi của nó "
        "cho bài toán định vị đều đến từ định nghĩa utility được cung cấp, và "
        "phải được chứng minh bằng đối chứng chứ không được giả định.",
        "Độ nhạy theo ngưỡng là rất lớn. Khoảng giữa 'không có HUI nào' và "
        "'vượt ngân sách tài nguyên' rất hẹp. Một hệ thống thực tế sẽ cần quy "
        "trình chọn ngưỡng, và bài tìm hiểu không đề xuất quy trình đó.",
        "Quy tắc xếp hạng HUI → AP là một thiết kế trong nhiều thiết kế khả "
        "dĩ. Bài tìm hiểu chọn utility_contribution (mỗi HUI chia đều utility cho các "
        "thành viên) vì nó là phân rã chính xác và không cần tham số, và quyết "
        "định này được ghi lại TRƯỚC khi có số liệu accuracy. Các thống kê "
        "thay thế được tính và lưu kèm, nhưng không thể loại trừ rằng một quy "
        "tắc khác cho kết quả khác.",
        "Siêu tham số k-NN được chọn trên một phép chia ngẫu nhiên phân tầng "
        "của trainingData. Phép chia này LẠC QUAN so với validationData, vì "
        "validationData đến từ người dùng khác, thiết bị phần lớn khác và thời "
        "điểm cách đó khoảng bốn tháng.",
    ])

    D.h(2, "16.2. Hạn chế về cài đặt")
    D.bullets([
        "Không dùng được SPMF (không có JVM trong môi trường thực nghiệm), nên "
        "EFIM được cài lại bằng Python. Tính đúng được bảo đảm bằng đối chiếu "
        "với oracle brute-force trên hàng chục cơ sở dữ liệu ngẫu nhiên, nhưng "
        "đó không giống với việc dùng một cài đặt tham chiếu đã được cộng đồng "
        "kiểm chứng nhiều năm.",
        "Hiệu năng tuyệt đối (giây, MB) là của một cài đặt Python, không nên "
        "so sánh trực tiếp với các con số trong các bài báo dùng Java. Điều có "
        "ý nghĩa là HÌNH DẠNG của các đường cong theo ngưỡng, không phải giá "
        "trị tuyệt đối.",
        f"Các lần chạy vượt ngân sách ({nf(C.huim['time_limit_s'])} giây hoặc "
        f"{nf(C.huim['max_huis'])} itemset) bị dừng có kiểm soát. Tập HUI của "
        "chúng bị cắt ngang theo thứ tự duyệt DFS, nên BỊ THIÊN LỆCH; vì vậy "
        "chúng không được dùng để xếp hạng AP, chỉ dùng cho phân tích hiệu "
        "năng khai thác, và được đánh dấu rõ trong mọi bảng.",
    ])

    D.h(2, "16.3. Hạn chế về dữ liệu")
    cs, tr = C.cs, C.tr
    D.bullets([
        f"Bộ dữ liệu được thu từ 2013 (training: "
        f"{tr['TIMESTAMP_stats']['min_utc'][:10]} đến "
        f"{tr['TIMESTAMP_stats']['max_utc'][:10]}). Hạ tầng Wi-Fi, chuẩn và "
        f"phần cứng điện thoại đã thay đổi đáng kể từ đó.",
        f"Không đồng nhất thiết bị: hai split chỉ chung "
        f"{len(cs['PHONEID_overlap'])} mã thiết bị và KHÔNG chung người dùng "
        f"nào. Đây đồng thời là điểm mạnh (đánh giá trung thực) và là hạn chế "
        f"(không tách được ảnh hưởng của thiết bị khỏi ảnh hưởng của phương "
        f"pháp).",
        f"{cs['waps_only_in_validation']} AP chỉ xuất hiện trong "
        f"validationData. Thông tin của chúng không thể tiếp cận với MỌI "
        f"phương pháp — một trần chặn độ chính xác không sơ đồ chọn đặc trưng "
        f"nào nâng lên được.",
        f"{tr['anomaly_probes']['n_empty_fingerprints']} fingerprint huấn "
        f"luyện không phát hiện AP nào, và "
        f"{tr['anomaly_probes']['n_cells_equal_0_dbm']} phép đo bằng đúng "
        f"0 dBm đều đến từ một thiết bị duy nhất. Những dòng này được GIỮ "
        f"NGUYÊN (ghi nhận, không sửa ngầm), nên chúng là nhiễu — tuy là nhiễu "
        f"giống nhau ở mọi điều kiện so sánh.",
        f"{nf(tr['duplicate_rows_full'])} dòng huấn luyện trùng lặp hoàn toàn, "
        f"cũng được giữ nguyên với cùng lý do.",
        "Đơn vị của LONGITUDE/LATITUDE KHÔNG được tài liệu hoá ở bất kỳ nguồn "
        "sơ cấp nào truy cập được. Vì vậy sai số định vị được báo cáo theo đơn "
        "vị toạ độ của bộ dữ liệu, KHÔNG gọi là mét.",
        "SPACEID trong validationData đồng nhất bằng 0, nên không thể đánh giá "
        "ở cấp phòng. Mọi kết luận của bài tìm hiểu chỉ ở cấp toà nhà và tầng.",
    ])

    D.h(2, "16.4. Hạn chế về tính tổng quát")
    D.bullets([
        "Kết quả thuộc về MỘT bộ dữ liệu, MỘT cấu hình k-NN, và các định nghĩa "
        "(q, p) cụ thể của bài tìm hiểu. Không có cơ sở để ngoại suy sang bộ dữ liệu "
        "fingerprint khác.",
        "Literature review không phải một systematic review. Nó không truy "
        "cập được IEEE Xplore và ACM DL full-text search; scimagojr.com trả về "
        "HTTP 403 nên KHÔNG có quartile nào được khẳng định. Phát biểu 'không "
        "tìm thấy nghiên cứu HUIM + UJIIndoorLoc' là phát biểu về PHẠM VI RÀ "
        "SOÁT NÀY, không phải về sự tồn tại.",
        "Bài tìm hiểu KHÔNG khẳng định bất kỳ quyền ưu tiên novelty nào.",
    ])
    D.page_break()


# ===========================================================================
def refs(D: Doc, C) -> None:
    D.h(1, "Tài liệu tham khảo")
    D.p("Định dạng theo kiểu IEEE. Toàn bộ metadata (tác giả, năm, venue, nhà "
        "xuất bản, volume, trang, DOI) được lấy từ Crossref API và lưu tại "
        "research/doi_verification.json. Tên bài báo trả về từ Crossref được "
        "ĐỐI CHIẾU với bài báo dự định trích dẫn; các mục không khớp đã bị "
        "loại bỏ.", align="justify")
    P = C.PAP.copy()
    P["_y"] = pd.to_numeric(P["year"], errors="coerce").fillna(0)
    P = P.sort_values(["_y", "paper"])
    for k, (_, r) in enumerate(P.iterrows(), 1):
        au = str(r["authors"]).split("; ")
        if len(au) > 3:
            astr = ", ".join(au[:3]) + " et al."
        else:
            astr = ", ".join(au)
        venue = str(r["venue"])
        bits = [f"[{k}]", astr + ",", f'"{r["paper"]},"']
        if str(r["venue_type"]) == "Journal":
            bits.append(f"{venue},")
            if str(r["volume"]) and str(r["volume"]) != "nan":
                bits.append(f"vol. {r['volume']},")
            if str(r["issue"]) and str(r["issue"]) != "nan":
                bits.append(f"no. {r['issue']},")
        else:
            bits.append(f"in {venue},")
        if str(r["pages"]) and str(r["pages"]) != "nan":
            bits.append(f"pp. {r['pages']},")
        bits.append(f"{int(r['_y'])}.")
        bits.append(f"DOI: {r['doi']}")
        D.p(" ".join(bits), size=10.5, align="justify")
    D.p("")
    D.rich([("Về xếp hạng tạp chí: ", "b"),
            ("không mục nào trong danh sách trên được gắn Q1/Q2. Lý do: "
             "(1) các bài hội nghị (CIKM, SIGKDD, IPIN, SIGMOD, INFOCOM, "
             "MobiSys, SDM) KHÔNG có quartile SJR/JCR — quartile xếp hạng TẠP "
             "CHÍ, không xếp hạng kỷ yếu hội nghị; (2) với các bài tạp chí, "
             "nguồn xếp hạng scimagojr.com trả về HTTP 403 Forbidden từ môi "
             "trường thực nghiệm (đã thử trang tạp chí, endpoint tìm theo ISSN "
             "và cả bản xuất CSV), và không có quyền truy cập Scopus hay Web "
             "of Science. Vì vậy ô quartile ghi 'Not verified' kèm lý do. Câu "
             "'IEEE = Q1' là một lỗi phạm trù: IEEE là nhà xuất bản, không "
             "phải một tạp chí.", "")])
    D.p("Chi tiết literature review, bảng metadata đầy đủ và bằng chứng "
        "indexing: research/literature_review.md, research/papers_table.csv, "
        "research/references.bib.", size=10.5)
    D.page_break()
