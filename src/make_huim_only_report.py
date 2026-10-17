"""PHASE QL - Word report: indoor positioning by HUIM alone (no k-NN).

Every number is read from results/huim_only/ (and, for reference rows only,
results/multi_dataset/) at build time.

Output: report/Bao_Cao_HUIM_IPS_Dinh_Vi_Chi_Bang_HUIM.docx
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_positioning import CELL_MAX_HUIS, CELL_TIME_S, ESCALATE
from report_builder import Doc
from run_huim_only import (BETA_GRID, GT_GRID, M_GRID, ORDER, OUT_ROOT,
                           P_GRID, TARGET_M, THETA_GRID)
from utils import FIGURES, PROJECT_ROOT, RESULTS

FIG = FIGURES / "huim_only"
OUT = PROJECT_ROOT / "report" / "Bao_Cao_HUIM_IPS_Dinh_Vi_Chi_Bang_HUIM.docx"
TITLES = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB",
          "hcxy": "HCXY", "hus": "HUS", "hus_dedup": "HUS (khử trùng lặp)"}


def J(p):
    return json.load(open(p, encoding="utf-8"))


def f2(v, d=2):
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v, d=2):
    return f2(v * 100, d) + "%"


def build() -> Doc:
    keys = [k for k in ORDER if (OUT_ROOT / k / "summary.json").exists()]
    if "uji" not in keys:
        raise SystemExit("results/huim_only/uji/summary.json missing")
    S = {k: J(OUT_ROOT / k / "summary.json") for k in keys}
    ver = J(OUT_ROOT / "verification.json")
    ref = pd.read_csv(FIG / "fig60_huim_only_all_datasets.csv")
    for f in ("fig60_huim_only_all_datasets", "fig61_huim_only_cdf_uji",
              "fig62_huim_only_dev", "fig63_huim_only_example"):
        if not (FIG / f"{f}.png").exists():
            raise SystemExit(f"{f} missing; run src/plots_huim_only.py")
    U = S["uji"]
    T = next(iter(U["tests"].values()))
    sel = U["selection"]
    prm = sel["params"]
    mdl = U["model"]
    G = pd.read_csv(OUT_ROOT / "uji" / "dev_grid.csv")
    runs = pd.read_csv(OUT_ROOT / "uji" / "cell_runs.csv")

    d = Doc()
    d.title_page([
        ("BÁO CÁO BÀI TÌM HIỂU", 16, True),
        ("ỨNG DỤNG THUẬT TOÁN HIGH UTILITY ITEMSET MINING (EFIM)", 14, True),
        ("VÀO HỆ THỐNG ĐỊNH VỊ TRONG NHÀ", 14, True),
        ("Phiên bản 4: định vị CHỈ bằng HUIM — khớp mẫu High Utility Itemset, không k-NN", 12.5, False),
        ("Dữ liệu: UJIIndoorLoc và các dataset trong dataset-20261013T020803Z-1-001", 12, False),
        (f"Sinh tự động lúc {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC từ results/huim_only/", 10, False),
    ])
    d.h(1, "Mục lục")
    d.toc_field()
    d.page_break()

    d.h(1, "1. Tóm tắt")
    d.rich([("Yêu cầu của giảng viên: ", "b"),
            ("HUIM phải là thuật toán định vị, không phải một nhánh lọc AP đứng trước k-NN. "
             "Phiên bản này đáp ứng đúng yêu cầu đó: mô hình định vị chính là các tập High Utility "
             "Itemset do EFIM khai thác; khi định vị, fingerprint cần định vị được coi là một giao "
             "dịch và được so khớp với các HUI. Không có k-NN, không có phép so khoảng cách giữa "
             "fingerprint truy vấn và fingerprint huấn luyện ở bất kỳ bước nào.", "")])
    d.rich([(f"Kết quả trên UJIIndoorLoc (validationData = tập test, {f2(T['n_test'], 0)} fingerprint): ", "b"),
            (f"sai số trung bình {f2(T['mean_err_m'])} m, trung vị {f2(T['median_err_m'])} m, "
             f"đúng tòa {pct(T['building_accuracy'])}, đúng tòa+tầng {pct(T['joint_accuracy'])}. "
             f"Trên tập dev (6 fold theo người dùng của trainingData): {f2(sel['dev_mean_m'])} m. ", ""),
            (f"Yêu cầu < {f2(TARGET_M, 0)} m: {'ĐẠT' if T['below_target'] else 'CHƯA ĐẠT'}.", "b")])
    rows = []
    for k in keys:
        for t, X in S[k]["tests"].items():
            r = ref[(ref.dataset == k) & (ref.test_set == t)]
            rows.append({"Dataset": TITLES[k], "Tập test": t, "Số mẫu": X["n_test"],
                         "Ô (cell)": S[k]["model"]["n_cells"],
                         "Số HUI": f2(S[k]["model"]["n_huis"], 0),
                         "Sai số TB (m)": f2(X["mean_err_m"]),
                         "Trung vị (m)": f2(X["median_err_m"]),
                         "Tòa+tầng": pct(X["joint_accuracy"]),
                         f"< {TARGET_M:g} m": "đạt" if X["below_target"] else "không"})
    d.table(pd.DataFrame(rows), "Định vị chỉ bằng HUIM trên mọi dataset (tham số chọn trên dev, test chấm một lần)", font_pt=8.5)
    d.figure(FIG / "fig60_huim_only_all_datasets.png", "Sai số trung bình của bộ định vị chỉ dùng HUIM; đường đỏ = 7 m", 6.3)

    d.h(1, "2. Vì sao phải bỏ k-NN")
    d.p("Ở các phiên bản trước, HUIM chọn một tập AP rồi k-NN làm toàn bộ việc định vị. Phân tích "
        "Shapley trên UJIIndoorLoc cho thấy HUIM khi đó chỉ đóng góp khoảng 6% mức giảm sai số, và "
        "thay HUIM bằng một tiêu chí xếp hạng đơn giản (mutual information) cho kết quả gần như "
        "y hệt. Như vậy HUIM chỉ là một nhánh tiền xử lý, không phải phương pháp định vị. Phiên "
        "bản này loại bỏ k-NN hoàn toàn.", align="justify")
    d.table(pd.DataFrame([
        {"Khía cạnh": "Mô hình lưu gì", "k-NN (bản trước)": "mọi fingerprint huấn luyện (vector RSSI)",
         "Khớp HUI (bản này)": "các HUI của từng ô: tập AP, utility, support"},
        {"Khía cạnh": "So sánh truy vấn với", "k-NN (bản trước)": "từng fingerprint huấn luyện (khoảng cách)",
         "Khớp HUI (bản này)": "từng HUI (mẫu đã khai thác)"},
        {"Khía cạnh": "Điểm của một vị trí", "k-NN (bản trước)": "1/khoảng cách tới một fingerprint",
         "Khớp HUI (bản này)": "lượng utility HUI của ô có trong giao dịch truy vấn"},
        {"Khía cạnh": "Bỏ HUIM đi thì", "k-NN (bản trước)": "vẫn định vị được (dùng mọi AP)",
         "Khớp HUI (bản này)": "không còn mô hình, không định vị được"},
    ]), "So sánh vai trò của HUIM giữa hai thiết kế")

    d.h(1, "3. HUIM và EFIM")
    d.formula("u(i,T) = q(i,T)·p(i)    u(X,T) = Σ_{i∈X} u(i,T)    u(X) = Σ_{T⊇X} u(X,T)")
    d.p("X là High Utility Itemset khi u(X) ≥ minUtil. EFIM (Zida et al., Knowledge and Information "
        "Systems 51(2):595–625, 2017, DOI 10.1007/s10115-016-0986-0) liệt kê đầy đủ các HUI bằng "
        "duyệt chiều sâu với hai chặn trên local utility và subtree utility, chiếu và gộp giao dịch. "
        "Bản cài đặt src/huim/efim.py được kiểm chứng với oracle vét cạn (tests/test_efim.py).", align="justify")

    d.h(1, "4. Mô hình hoá: mỗi vị trí tham chiếu là một cơ sở dữ liệu giao dịch")
    d.bullets([
        "Giao dịch T = một fingerprint; item = một AP được phát hiện; q(i,T) = round(1 + (RSSI − RSSI_min)/(RSSI_max − RSSI_min) × 99) ∈ [1,100]; p(i) = 1.",
        f"Ô (cell) c = một điểm tham chiếu của tập huấn luyện (UJIIndoorLoc: {mdl['n_cells']} ô). D_c = giao dịch của các fingerprint huấn luyện đo tại c.",
        "minUtil_c = θ% × u(D_c) — tương đối theo từng ô. HUI_c = EFIM(D_c, minUtil_c): các nhóm AP cùng xuất hiện với tín hiệu mạnh, là “chữ ký” Wi-Fi của vị trí c.",
        f"Ngân sách mỗi ô: {f2(CELL_TIME_S, 0)} s hoặc {f2(CELL_MAX_HUIS, 0)} HUI; vượt ngân sách thì khai thác lại ở θ × {f2(ESCALATE)} tới khi hoàn chỉnh (không dùng tập HUI bị cắt ngang).",
        "Mô hình định vị = {(HUI_c, toạ độ tâm của c, tòa_tầng của c)} cho mọi ô. Không lưu fingerprint nào.",
    ])

    d.h(1, "5. Thuật toán định vị bằng khớp HUI")
    d.p("Fingerprint cần định vị cũng được biến thành một giao dịch T. Với mỗi HUI X của ô c:", align="justify")
    d.formula("frac(X,T) = |X ∩ T| / |X|",
              "Tỷ lệ AP của mẫu X được nhìn thấy trong truy vấn (khớp mềm: thiết bị khác có thể bỏ sót một AP).")
    d.formula("agree(X,T) = exp(−|q̄_T(X) − q̄_c(X)| / τ),   q̄_c(X) = u(X) / (s(X)·|X|)",
              "Mức khớp cường độ: utility trung bình mỗi item của X trong truy vấn so với trong D_c.")
    d.formula("P_c(T) = Σ_{X∈HUI_c} [u(X)/Σ_{Y∈HUI_c} u(Y)] · frac(X,T)^γ · agree(X,T)",
              "Điểm mẫu: phần khối lượng utility HUI của ô c mà truy vấn chứa, đúng cường độ.")
    d.formula("V_c(T) = Σ_{i∈T∩I_c} q(i,T) / Σ_{i∈T} q(i,T),   I_c = ∪ HUI_c",
              "Độ phủ: phần utility của truy vấn được các mẫu của ô c giải thích.")
    d.formula("score_c(T) = P_c(T) · V_c(T)^β")
    d.formula("(x̂, ŷ) = Σ_{c∈top-m} a_c (x_c, y_c),   a_c = score_c^p / Σ score^p;   tòa_tầng = bỏ phiếu theo a_c",
              "m ô điểm cao nhất cho toạ độ; tòa và tầng do chính các ô đó bỏ phiếu.")
    d.p("Ghi chú trung thực: bước cuối là trung bình có trọng số của tâm các ô — giống về hình thức "
        "với bước cuối của weighted k-NN. Khác biệt cốt lõi là ở chỗ ô nào được chọn và với trọng số "
        "nào: ở đây hoàn toàn do điểm khớp HUI quyết định; không có khoảng cách fingerprint nào được tính.",
        align="justify")

    d.h(2, "5.1. Giao thức")
    d.table(pd.DataFrame([
        {"Bước": "Chuẩn hoá RSSI, khai thác EFIM theo ô", "Dữ liệu": "huấn luyện"},
        {"Bước": f"Chọn θ ∈ {THETA_GRID}, (γ,τ) ∈ {GT_GRID}, β ∈ {BETA_GRID}, m ∈ {M_GRID}, p ∈ {P_GRID}",
         "Dữ liệu": "dev: " + sel["dev_folds"]},
        {"Bước": "Khai thác lại toàn bộ tập huấn luyện ở θ đã chọn", "Dữ liệu": "huấn luyện"},
        {"Bước": "Đánh giá", "Dữ liệu": "tập test, một lần"},
    ]), f"Dữ liệu dùng ở từng bước ({sel['n_configurations']} cấu hình trên dev)", font_pt=8.5)

    d.h(1, "6. Kết quả trên UJIIndoorLoc")
    d.p(f"Cấu hình chọn trên dev: θ = {f2(sel['theta_pct'], 0)}%, {prm and sel['label']}. Mô hình cuối: "
        f"{mdl['n_cells']} ô, {f2(mdl['n_huis'], 0)} HUI, khai thác trong {f2(mdl['mining_seconds'], 1)} s; "
        f"{mdl['cells_escalated']} ô phải nâng θ (θ trung vị {f2(mdl['theta_used_median_pct'])}%); "
        f"{mdl['aps_in_some_hui']}/{mdl['n_aps']} AP xuất hiện trong ít nhất một HUI.", align="justify")
    d.figure(FIG / "fig62_huim_only_dev.png", "Sai số trên dev theo θ và m (mỗi điểm là cấu hình tốt nhất của các tham số còn lại)", 5.4)
    abl = []
    for name, col in (("β (độ phủ)", "beta"), ("τ (khớp cường độ)", "tau"), ("γ (khớp mềm)", "gamma"), ("p (độ sắc trọng số)", "p")):
        for v, g in G[G.theta_pct == sel["theta_pct"]].groupby(col):
            abl.append({"Thành phần": name, "Giá trị": f2(v, 0), "Dev TB tốt nhất (m)": f2(g.dev_mean_m.min()),
                        "Tòa+tầng dev": pct(g.loc[g.dev_mean_m.idxmin(), "dev_joint_accuracy"])})
    d.table(pd.DataFrame(abl), f"Ảnh hưởng của từng thành phần điểm khớp trên dev (θ = {f2(sel['theta_pct'], 0)}%)", font_pt=8.5)
    d.table(pd.DataFrame([{"Chỉ số": k, "Giá trị": v} for k, v in [
        ("Sai số trung bình", f2(T["mean_err_m"]) + " m"), ("Trung vị", f2(T["median_err_m"]) + " m"),
        ("p75 / p90 / p95", f"{f2(T['p75_err_m'])} / {f2(T['p90_err_m'])} / {f2(T['p95_err_m'])} m"),
        ("Tỷ lệ ≤ 5 m", pct(T["share_within_5m"])),
        ("Đúng tòa", pct(T["building_accuracy"])), ("Đúng tầng", pct(T["floor_accuracy"])),
        ("Đúng tòa+tầng", pct(T["joint_accuracy"])),
        ("Thời gian định vị", f2(T["ms_per_fp"]) + " ms / fingerprint")]]),
        "UJIIndoorLoc validationData (tập test): định vị chỉ bằng HUIM")
    d.figure(FIG / "fig61_huim_only_cdf_uji.png", "Phân bố sai số; hai đường k-NN chỉ để tham chiếu", 5.6)
    d.figure(FIG / "fig63_huim_only_example.png", "Ví dụ một truy vấn: các ô có điểm khớp HUI cao nhất, vị trí thật và vị trí ước lượng", 6.0)

    d.h(1, "7. Các dataset khác")
    d.p("Cùng mã nguồn, chỉ đổi dữ liệu; θ và tham số điểm khớp được chọn lại trên dev của từng dataset.", align="justify")
    rows = []
    for k in keys:
        s = S[k]["selection"]
        for t, X in S[k]["tests"].items():
            rows.append({"Dataset": TITLES[k], "Tập test": t, "θ (%)": f2(s["theta_pct"], 0),
                         "Tham số": s["label"], "Dev TB (m)": f2(s["dev_mean_m"]),
                         "Test TB (m)": f2(X["mean_err_m"]), "Tòa+tầng": pct(X["joint_accuracy"]),
                         "ms/fp": f2(X["ms_per_fp"])})
    d.table(pd.DataFrame(rows), "Tham số được chọn và kết quả trên từng dataset", font_pt=7.5)
    rr = ref.dropna(subset=["knn_opt_m"])
    d.table(pd.DataFrame([{"Dataset": TITLES[r.dataset], "Tập test": r.test_set,
                           "Chỉ HUIM (m)": f2(r.huim_only_mean_m),
                           "k-NN gốc, mọi AP (m)": f2(r.knn_study_m),
                           "k-NN tối ưu, mọi AP (m)": f2(r.knn_opt_m)} for r in rr.itertuples()]),
            "Tham chiếu: sai số của các bộ định vị k-NN ở phiên bản trước (không dùng trong hệ thống này)", font_pt=8)

    d.h(1, "8. Đóng góp của HUIM")
    d.p("Trong hệ thống này HUIM là toàn bộ mô hình định vị: bỏ HUIM thì không còn gì để định vị. "
        "Câu hỏi “HUIM chiếm bao nhiêu % công việc” vì vậy có câu trả lời trực tiếp: mọi quyết định "
        "(ô nào, tầng nào, toạ độ nào) đều xuất phát từ điểm khớp HUI. Các tham số γ, τ, β, m, p chỉ "
        "điều chỉnh cách đọc các HUI, và được chọn trên dev.", align="justify")

    d.h(1, "9. Kiểm chứng độc lập")
    d.p("src/verify_huim_only.py không gọi EFIM hay bộ định vị. Nó tính lại minUtil của mọi ô (M1), "
        "utility và support của mọi HUI ở các ô lấy mẫu từ dBm gốc (M2), kiểm tra mọi itemset 1–2 AP "
        "vượt minUtil đều có trong mô hình ở mọi ô (M3), tính lại điểm khớp, các ô được chọn và toạ "
        "độ của các truy vấn ngẫu nhiên bằng vòng lặp Python thuần (M4), đếm lại các metric từ file "
        "dự đoán (M5) và kiểm tra cấu hình chọn là cực tiểu của lưới dev (M6).", align="justify")
    d.table(pd.DataFrame([{"Dataset": TITLES[r["dataset"]], "Số phép kiểm": r["n_checks"],
                           "Thất bại": r["n_failed"]} for r in ver["datasets"]]),
            f"Kiểm chứng: {ver['n_checks']} phép kiểm, {ver['n_failed']} thất bại (results/huim_only/verification.json)")

    d.h(1, "10. Hạn chế")
    d.bullets([
        "Ô = điểm tham chiếu của tập huấn luyện; vị trí ước lượng là tổ hợp lồi của tâm các ô, nên không thể nằm ngoài vùng đã khảo sát.",
        "Bước cuối (trung bình có trọng số của m ô) giống về hình thức với weighted k-NN; điểm khác là trọng số do khớp HUI quyết định.",
        "Các tham số γ, τ, β, m, p, θ được chọn trên dev; tập test chấm một lần, không chọn lại sau khi xem test.",
        f"Ngân sách {f2(CELL_TIME_S, 0)} s/ô làm một số ô dày đặc phải chạy ở θ cao hơn θ chọn; số ô bị ảnh hưởng ghi trong cell_runs.csv.",
        "EFIM viết bằng Python; thời gian khai thác và định vị là của cài đặt này.",
    ])
    d.h(1, "11. Chạy lại")
    for c in ("python -m pytest tests -q",
              "python src/run_huim_only.py --dataset all",
              "python src/verify_huim_only.py",
              "python src/plots_huim_only.py",
              "python src/make_huim_only_report.py"):
        d.p(c, italic=True)
    return d


def main():
    info = build().save(OUT)
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
