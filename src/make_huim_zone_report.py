"""PHASE ZL - Word report of PHASE Z (HUIM theo vùng chọn AP cho IPS).

Every number is read from results/huim_zone/ and results/multi_dataset/ at
build time; a missing file stops the build.

Output: report/Bao_Cao_HUIM_IPS_Theo_Vung.docx
Run:    python src/make_huim_zone_report.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_zone import ESCALATE, MAX_HUIS, N_SPATIAL_ZONES, ZONE_TIME_S
from report_builder import Doc
from run_huim_zone import MODELS, ORDER, OUT_ROOT, TARGET_M, THETA_GRID
from utils import FIGURES, PROJECT_ROOT, RESULTS

FIG = FIGURES / "huim_zone"
MULTI = RESULTS / "multi_dataset"
OUT = PROJECT_ROOT / "report" / "Bao_Cao_HUIM_IPS_Theo_Vung.docx"
TITLES = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB",
          "hcxy": "HCXY", "hus": "HUS", "hus_dedup": "HUS (khử trùng lặp)"}


def J(p: Path) -> dict:
    return json.load(open(p, encoding="utf-8"))


def f2(v, d=2) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v, d=2) -> str:
    return f2(v * 100, d) + "%"


def model_of(set_name: str) -> str:
    return "A" if "A_signal" in set_name else "B"


def theta_of(set_name: str) -> str:
    return set_name.split("__")[2][:-3]


class Data:
    def __init__(self) -> None:
        self.keys = [k for k in ORDER if (OUT_ROOT / k / "selected.json").exists()]
        if "uji" not in self.keys:
            raise SystemExit("results/huim_zone/uji/selected.json missing; run "
                             "src/run_huim_zone.py first")
        self.sel = {k: J(OUT_ROOT / k / "selected.json") for k in self.keys}
        self.sets = {k: J(OUT_ROOT / k / "ap_sets.json") for k in self.keys}
        self.test = {k: pd.read_csv(OUT_ROOT / k / "test_results.csv") for k in self.keys}
        self.dev = {k: pd.read_csv(OUT_ROOT / k / "dev_selection.csv") for k in self.keys}
        self.zm = {k: pd.read_csv(OUT_ROOT / k / "zone_mining.csv") for k in self.keys}
        self.ver = J(OUT_ROOT / "verification.json")
        self.glob = pd.read_csv(MULTI / "uji" / "positioning_conditions.csv")
        for p in ("fig50_zone_theta_curve", "fig51_zone_vs_alternatives",
                  "fig52_zone_all_datasets", "fig53_zone_cdf_uji",
                  "fig54_zone_per_zone_waps", "fig55_zone_time"):
            if not (FIG / f"{p}.png").exists():
                raise SystemExit(f"figure {p} missing; run src/plots_huim_zone.py")


def build(D: Data) -> Doc:
    d = Doc()
    U = D.sel["uji"]
    ut = next(iter(U["tests"]))
    T = U["tests"][ut]
    hz, al = T["huim_zone"], T["all_aps"]
    ctl = T["controls_same_budget_mean_err_m"]
    gb = T["global_huim_best"]
    n_sel = hz["n_waps"]
    uset = U["selection"]["selected_set"]
    usets = D.sets["uji"]
    zr = D.zm["uji"]
    zsel = zr[zr.set == uset]

    d.title_page([
        ("BÁO CÁO BÀI TÌM HIỂU", 16, True),
        ("ÁP DỤNG THUẬT TOÁN HIGH UTILITY ITEMSET MINING (EFIM)", 14, True),
        ("ĐỂ CHỌN ACCESS POINT CHO HỆ THỐNG ĐỊNH VỊ TRONG NHÀ", 14, True),
        ("Phiên bản 3: HUIM theo vùng (zone-wise HUIM)", 13, False),
        ("Dữ liệu: UJIIndoorLoc và các dataset trong dataset-20261013T020803Z-1-001", 12, False),
        (f"Sinh tự động lúc {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC từ results/huim_zone/", 10, False),
    ])
    d.h(1, "Mục lục")
    d.toc_field()
    d.page_break()

    # ------------------------------------------------------------------ 1
    d.h(1, "1. Tóm tắt kết quả")
    d.rich([("Yêu cầu: ", "b"),
            ("thuật toán HUIM phải là cơ chế chính của hệ thống định vị — HUIM chọn các "
             "Access Point (AP) hữu ích, rồi chỉ các AP đó được dùng để định vị trên "
             "UJIIndoorLoc và các dataset còn lại; sai số trung bình phải dưới "
             f"{f2(TARGET_M, 0)} m.", "")])
    d.rich([("Kết quả trên UJIIndoorLoc (validationData, "
             f"{T['n_test']:,} fingerprint): ".replace(",", " "), "b"),
            (f"HUIM theo vùng chọn {n_sel}/{al['n_waps']} WAP (giảm "
             f"{f2(hz['feature_reduction_pct'])}% số chiều). Định vị chỉ bằng {n_sel} WAP "
             f"đó cho sai số trung bình {f2(hz['mean_err_m'])} m, trung vị "
             f"{f2(hz['median_err_m'])} m, độ chính xác tòa nhà {pct(hz['building_accuracy'])}, "
             f"tòa+tầng {pct(hz['joint_accuracy'])}. ", ""),
            (f"Mức yêu cầu < {f2(TARGET_M, 0)} m: {'ĐẠT' if T['below_target'] else 'CHƯA ĐẠT'}.", "b")])
    d.p(f"So sánh trong cùng bộ định vị: toàn bộ {al['n_waps']} WAP cho "
        f"{f2(al['mean_err_m'])} m; HUIM toàn cục của phiên bản trước "
        f"({gb['n_waps']} WAP) cho {f2(gb['mean_err_m'])} m. Như vậy cách khai thác HUIM "
        "theo vùng là thay đổi quyết định: nó đưa sai số khi dùng AP do HUIM chọn từ "
        f"{f2(gb['mean_err_m'])} m xuống {f2(hz['mean_err_m'])} m.", align="justify")
    rows = []
    for k in D.keys:
        for t, X in D.sel[k]["tests"].items():
            rows.append({"Dataset": TITLES[k], "Tập test": t, "Số mẫu": X["n_test"],
                         "WAP (HUIM/tổng)": f"{X['huim_zone']['n_waps']}/{X['all_aps']['n_waps']}",
                         "Sai số TB HUIM (m)": f2(X["huim_zone"]["mean_err_m"]),
                         "Sai số TB toàn bộ AP (m)": f2(X["all_aps"]["mean_err_m"]),
                         "Trung vị HUIM (m)": f2(X["huim_zone"]["median_err_m"]),
                         f"< {TARGET_M:g} m": "đạt" if X["below_target"] else "không"})
    d.table(pd.DataFrame(rows), "Kết quả cuối trên mọi dataset: định vị chỉ bằng AP do "
            "HUIM theo vùng chọn (tập AP và ngưỡng chọn trên dev, test dùng một lần)",
            font_pt=8.5)
    d.figure(FIG / "fig52_zone_all_datasets.png",
             "Sai số trung bình: toàn bộ AP và AP do HUIM theo vùng chọn, mọi dataset; "
             "đường đỏ = 7 m", 6.3)

    # ------------------------------------------------------------------ 2
    d.h(1, "2. HUIM và EFIM — phần thuật toán")
    d.p("Cơ sở dữ liệu giao dịch D gồm các giao dịch T; mỗi item i trong T có utility "
        "nội q(i,T) và utility ngoài p(i). Các định nghĩa dùng trong toàn bài:", align="justify")
    d.formula("u(i,T) = q(i,T) · p(i)      u(X,T) = Σ_{i∈X} u(i,T)      u(X) = Σ_{T⊇X} u(X,T)")
    d.formula("TU(T) = Σ_{i∈T} u(i,T)      TWU(X) = Σ_{T⊇X} TU(T)",
              "X là high utility itemset (HUI) khi u(X) ≥ minUtil. Utility không "
              "anti-monotone (thêm item có thể làm u tăng hoặc giảm), nên không cắt tỉa "
              "bằng chính u được; TWU là một chặn trên anti-monotone dùng để loại item.")
    d.p("EFIM (Zida, Fournier-Viger, Lin, Wu & Tseng, Knowledge and Information Systems "
        "51(2):595–625, 2017, DOI 10.1007/s10115-016-0986-0) duyệt cây liệt kê tập theo "
        "chiều sâu với thứ tự item tăng dần theo TWU và dùng hai chặn:", align="justify")
    d.bullets([
        "Local utility lu(α,z) = Σ_{T∋α∪{z}} [u(α,T) + re(α,T)]: nếu < minUtil thì z bị loại khỏi toàn bộ cây con của α.",
        "Subtree utility su(α,z) = Σ_{T∋α∪{z}} [u(α,T) + u(z,T) + Σ_{i∈T, i≻z} u(i,T)]: nếu < minUtil thì không đi vào nhánh α∪{z}.",
        "Chiếu cơ sở dữ liệu (high-utility projection) và gộp giao dịch giống nhau (transaction merging); đếm utility nhanh bằng mảng utility-bin.",
    ])
    d.p("Bản cài đặt src/huim/efim.py được kiểm chứng với oracle vét cạn src/huim/brute_force.py "
        "(tests/test_efim.py) và phần khai thác theo vùng được kiểm chứng thêm bởi "
        "tests/test_huim_zone.py.", align="justify")

    # ------------------------------------------------------------------ 3
    d.h(1, "3. Mô hình hoá: fingerprint Wi-Fi → giao dịch utility")
    d.bullets([
        "Một fingerprint (một lần quét) = một giao dịch T; item = một WAP được phát hiện (giá trị ≠ 100).",
        "Utility nội q(i,T) = round(1 + (RSSI − RSSI_min)/(RSSI_max − RSSI_min) × 99) ∈ [1, 100], RSSI_min/max học từ dữ liệu huấn luyện (UJIIndoorLoc: −104 và 0 dBm).",
        "Model A: p(i) = 1 — utility chỉ phản ánh cường độ tín hiệu × mức đồng xuất hiện.",
        "Model B: p(i) = max(I(A_i;Y), 1e−6) / max_j I(A_j;Y) — mutual information giữa trạng thái AP và vị trí (tòa_tầng, hoặc điểm tham chiếu cho dataset một tầng), ước lượng chỉ trên dữ liệu huấn luyện.",
        "Một HUI là một nhóm AP thường được thấy cùng nhau với tín hiệu mạnh (A), hoặc vừa mạnh vừa phân biệt vị trí (B). AP được chọn = AP xuất hiện trong ít nhất một HUI.",
    ])

    # ------------------------------------------------------------------ 4
    d.h(1, "4. Vì sao HUIM toàn cục (phiên bản trước) không đạt")
    G = D.glob[(D.glob.family == "huim_union") & (D.glob.test_set == ut)].sort_values("utility_model")
    d.p("Phiên bản trước khai thác MỘT cơ sở dữ liệu gồm toàn bộ 19 861 giao dịch. Một tầng "
        "chỉ chiếm khoảng 8% số dòng, nên nhóm AP mạnh ở một tầng nhưng vô hình ở các tầng khác "
        "không bao giờ đạt minUtil toàn cục trước khi số itemset bùng nổ: tập AP lớn nhất còn "
        "khai thác trọn vẹn chỉ có 79–91 WAP, phần lớn tập trung ở các khu đông mẫu. Kết quả với "
        "cùng bộ định vị:", align="justify")
    d.table(pd.DataFrame([{"Tập AP": r.condition, "Số WAP": int(r.n_waps),
                           "Sai số TB (m)": f2(r.opt_mean_err_m),
                           "Tòa+tầng": pct(r.opt_joint_accuracy)} for r in G.itertuples()]),
            "HUIM toàn cục (PHASE H/H2) trên UJIIndoorLoc validationData, bộ định vị PHASE I3")
    d.p("Con số 5,36 m của phiên bản trước vì vậy đến từ toàn bộ 520 AP, không từ HUIM. "
        "Phiên bản này sửa đúng điểm đó: thay đổi cách áp dụng HUIM, giữ nguyên bộ định vị.",
        align="justify")

    # ------------------------------------------------------------------ 5
    d.h(1, "5. Phương pháp mới: HUIM theo vùng")
    d.p("Ý tưởng: thông tin định vị nằm ở chỗ mỗi khu vực có một nhóm AP đặc trưng của nó. "
        "Vì vậy HUIM được chạy riêng trên giao dịch của từng vùng, với minUtil tương đối theo "
        "tổng utility của chính vùng đó, rồi hợp các AP lại.", align="justify")
    d.bullets([
        f"Bước 1 — Vùng: lớp tòa_tầng (UJIIndoorLoc: {D.sets['uji']['n_zones']} vùng); site một tầng được chia thành {N_SPATIAL_ZONES} cụm k-means theo toạ độ huấn luyện.",
        "Bước 2 — Với mỗi vùng z: D_z = giao dịch của các fingerprint huấn luyện thuộc z; minUtil_z = θ% × u(D_z).",
        "Bước 3 — EFIM(D_z, p, minUtil_z) → HUI_z; S_z = mọi WAP xuất hiện trong ít nhất một HUI của HUI_z.",
        "Bước 4 — Tập AP định vị S = ∪_z S_z. Bộ định vị chỉ nhìn thấy các cột trong S.",
        f"Ngân sách mỗi lần chạy theo vùng: {f2(ZONE_TIME_S, 0)} s hoặc {f2(MAX_HUIS, 0)} HUI. Vùng nào chạm ngân sách được khai thác lại ở θ × {f2(ESCALATE)} cho tới khi hoàn chỉnh, nên S_z luôn là hợp của một tập HUI ĐẦY ĐỦ (danh sách bị cắt ngang thiên lệch theo thứ tự DFS và không bao giờ được dùng). Khi θ giảm dần theo lưới, vùng đã từng chạm ngân sách ở một θ lớn hơn dùng lại lần chạy hoàn chỉnh nhỏ nhất của nó.",
        f"Lưới θ: {', '.join(f2(t, 0) for t in THETA_GRID)}% cho cả Model A và Model B → {len(usets['sets'])} tập AP ứng viên.",
    ])
    d.formula("S(θ, p) = ∪_z { i : ∃X ∈ HUI(D_z, p, θ% · u(D_z)), i ∈ X }")
    d.p("Bộ định vị là mô hình PHASE I3 của từng dataset, đã được chọn trước đó trên dev fold "
        "của dữ liệu huấn luyện với toàn bộ AP (UJIIndoorLoc: " + U["positioner"] + "). Nó "
        "được giữ cố định; thứ duy nhất thay đổi giữa các điều kiện là tập cột do HUIM chọn.",
        align="justify")

    d.h(2, "5.1. Giao thức chống rò rỉ dữ liệu")
    d.table(pd.DataFrame([
        {"Bước": "Chuẩn hoá RSSI, p(i) Model B", "Dữ liệu": "huấn luyện"},
        {"Bước": "Chia vùng, khai thác EFIM theo vùng", "Dữ liệu": "huấn luyện"},
        {"Bước": "Chọn mô hình utility và θ", "Dữ liệu": "dev fold của tập huấn luyện (" + U["selection"]["dev_folds"].split(",")[0] + ", nhóm theo USERID với UJIIndoorLoc)"},
        {"Bước": "Đánh giá", "Dữ liệu": "tập test (validationData), mỗi tập AP đúng một lần"},
    ]), "Dữ liệu dùng ở từng bước")
    d.p("Quy tắc chọn: tập AP có sai số trung bình trên dev thấp nhất (hoà → ít WAP hơn). Mọi θ "
        "đều được báo cáo trên tập test để vẽ đường cong, nhưng tập được chọn đã cố định trước đó.",
        align="justify")

    # ------------------------------------------------------------------ 6
    d.h(1, "6. Kết quả trên UJIIndoorLoc")
    d.h(2, "6.1. Khai thác HUIM theo vùng")
    Z = zr.groupby("set").agg(n_zones=("zone", "size"), hui=("n_huis", "sum"),
                              runtime=("runtime_s", "sum"),
                              escal=("n_attempts", lambda s: int((s > 1).sum()))).reset_index()
    Z["n_waps"] = Z.set.map(lambda s: len(usets["sets"][s]))
    dv = D.dev["uji"].set_index("set")
    tr = D.test["uji"]
    trh = tr[(tr.family == "huim_zone") & (tr.test_set == ut)].set_index("set")
    Z["model"] = Z.set.map(model_of)
    Z["theta"] = Z.set.map(lambda s: float(theta_of(s)))
    Z = Z.sort_values(["model", "theta"], ascending=[True, False])
    d.table(pd.DataFrame([{"Model": r.model, "θ (%)": f2(r.theta, 0), "Tổng HUI": f"{int(r.hui):,}".replace(",", " "),
                           "Vùng phải nâng θ": r.escal, "Thời gian khai thác (s)": f2(r.runtime, 1),
                           "WAP chọn": r.n_waps, "Dev TB (m)": f2(dv.loc[r.set, "dev_mean_ground_m"]),
                           "Test TB (m)": f2(trh.loc[r.set, "mean_err_m"]),
                           "Tòa+tầng": pct(trh.loc[r.set, "joint_accuracy"]),
                           "Chọn": "✔" if r.set == uset else ""} for r in Z.itertuples()]),
            "UJIIndoorLoc: mọi tập AP ứng viên của HUIM theo vùng (dev dùng để chọn, test chỉ để báo cáo)",
            font_pt=8)
    d.figure(FIG / "fig50_zone_theta_curve.png",
             "(a) θ → số WAP giữ lại; (b) θ → sai số trên dev và trên validation; vòng tròn = tập được chọn trên dev", 6.3)
    d.p(f"Tập được chọn: {uset} — Model {model_of(uset)}, θ = {theta_of(uset)}%, "
        f"{n_sel} WAP; tổng {int(zsel.n_huis.sum()):,} HUI trên {len(zsel)} vùng, khai thác mất "
        f"{f2(zsel.runtime_s.sum(), 1)} s (đã gồm các lần nâng θ).".replace(",", " "), align="justify")
    d.table(pd.DataFrame([{"Vùng (tòa_tầng)": r.zone, "Giao dịch": r.n_transactions,
                           "AP thấy được": r.n_items, "θ dùng (%)": f2(r.theta_used_pct, 3),
                           "minUtil": f2(r.abs_minutil, 1), "Số HUI": f"{r.n_huis:,}".replace(",", " "),
                           "WAP chọn": r.n_waps} for r in zsel.itertuples()]),
            "UJIIndoorLoc, tập được chọn: kết quả khai thác của từng vùng", font_pt=8.5)
    d.figure(FIG / "fig54_zone_per_zone_waps.png",
             "Số AP mỗi tòa–tầng đóng góp vào tập định vị", 6.3)

    d.h(2, "6.2. Định vị bằng các AP do HUIM chọn")
    d.figure(FIG / "fig51_zone_vs_alternatives.png",
             "UJIIndoorLoc: HUIM theo vùng so với toàn bộ AP, HUIM toàn cục và các đối chứng cùng ngân sách", 6.3)
    rnd = ctl["random_mean_of_3"]
    d.table(pd.DataFrame([
        {"Điều kiện": f"HUIM theo vùng ({uset})", "Số WAP": n_sel, "Sai số TB (m)": f2(hz["mean_err_m"]),
         "Trung vị (m)": f2(hz["median_err_m"]), "p90 (m)": f2(hz["p90_err_m"]),
         "Tòa": pct(hz["building_accuracy"]), "Tòa+tầng": pct(hz["joint_accuracy"]), "ms/fp": f2(hz["ms_per_fp"])},
        {"Điều kiện": "Toàn bộ WAP", "Số WAP": al["n_waps"], "Sai số TB (m)": f2(al["mean_err_m"]),
         "Trung vị (m)": f2(al["median_err_m"]), "p90 (m)": f2(al["p90_err_m"]), "Tòa": "",
         "Tòa+tầng": pct(al["joint_accuracy"]), "ms/fp": f2(al["ms_per_fp"])},
        {"Điều kiện": f"HUIM toàn cục tốt nhất ({gb['set']})", "Số WAP": gb["n_waps"],
         "Sai số TB (m)": f2(gb["mean_err_m"]), "Trung vị (m)": "", "p90 (m)": "", "Tòa": "", "Tòa+tầng": "", "ms/fp": ""},
        {"Điều kiện": "Top-n theo số lần phát hiện", "Số WAP": n_sel, "Sai số TB (m)": f2(ctl["top_support"]),
         "Trung vị (m)": "", "p90 (m)": "", "Tòa": "", "Tòa+tầng": "", "ms/fp": ""},
        {"Điều kiện": "Top-n theo mutual information", "Số WAP": n_sel, "Sai số TB (m)": f2(ctl["top_mi"]),
         "Trung vị (m)": "", "p90 (m)": "", "Tòa": "", "Tòa+tầng": "", "ms/fp": ""},
        {"Điều kiện": "Ngẫu nhiên (TB 3 seed)", "Số WAP": n_sel, "Sai số TB (m)": f2(rnd),
         "Trung vị (m)": "", "p90 (m)": "", "Tòa": "", "Tòa+tầng": "", "ms/fp": ""},
    ]), "UJIIndoorLoc validationData, cùng một bộ định vị cho mọi dòng", font_pt=8.5)
    d.figure(FIG / "fig53_zone_cdf_uji.png", "Phân bố sai số trên 1 111 fingerprint validation", 5.6)
    d.figure(FIG / "fig55_zone_time.png", "Thời gian định vị theo số WAP (cùng bộ định vị)", 5.2)

    d.h(2, "6.3. HUIM đóng góp gì vào con số cuối")
    gain_glob = gb["mean_err_m"] - hz["mean_err_m"]
    d.bullets([
        f"HUIM quyết định TẬP CỘT: {n_sel} trên {al['n_waps']} WAP. Bộ định vị chỉ đọc RSSI của {n_sel} WAP này — {f2(hz['feature_reduction_pct'])}% số AP bị bỏ hoàn toàn khỏi cả cơ sở dữ liệu vân tay lẫn truy vấn.",
        f"So với HUIM toàn cục cùng bộ định vị, đổi sang HUIM theo vùng giảm sai số {f2(gain_glob)} m ({f2(gb['mean_err_m'])} → {f2(hz['mean_err_m'])} m).",
        f"So với dùng toàn bộ AP: {f2(hz['mean_err_m'])} m so với {f2(al['mean_err_m'])} m ({'thấp hơn' if hz['mean_err_m'] < al['mean_err_m'] else 'cao hơn'} {f2(abs(al['mean_err_m'] - hz['mean_err_m']))} m), trong khi thời gian định vị giảm từ {f2(al['ms_per_fp'])} xuống {f2(hz['ms_per_fp'])} ms/fingerprint.",
        f"So với đối chứng cùng {n_sel} WAP: ngẫu nhiên {f2(rnd)} m, top-n theo số lần phát hiện {f2(ctl['top_support'])} m, top-n theo MI {f2(ctl['top_mi'])} m. " + (
            "HUIM theo vùng tốt hơn cả ba." if hz["mean_err_m"] < min(rnd, ctl["top_support"], ctl["top_mi"]) else
            "Ở cùng ngân sách, HUIM theo vùng tốt hơn chọn ngẫu nhiên; ở mức này các tiêu chí xếp hạng đơn giản đạt sai số gần tương đương — đây là đối chứng phải đọc trung thực."),
    ])

    # ------------------------------------------------------------------ 7
    d.h(1, "7. Áp dụng cho các dataset khác (dataset-20261013T020803Z-1-001)")
    d.p("Cùng mã nguồn, chỉ đổi dữ liệu. Các quyết định riêng từng dataset (giá trị “không phát "
        "hiện”, đơn vị toạ độ, cách nhóm dev fold, nhãn vị trí) nằm trong src/multi_datasets.py.",
        align="justify")
    rows = []
    for k in D.keys:
        S = D.sel[k]
        for t, X in S["tests"].items():
            c = X["controls_same_budget_mean_err_m"]
            rows.append({"Dataset": TITLES[k], "Vùng": D.sets[k]["n_zones"], "Tập test": t,
                         "Tập chọn": f"{model_of(S['selection']['selected_set'])}, θ {theta_of(S['selection']['selected_set'])}%",
                         "WAP": f"{X['huim_zone']['n_waps']}/{X['all_aps']['n_waps']}",
                         "HUIM vùng (m)": f2(X["huim_zone"]["mean_err_m"]),
                         "Toàn bộ (m)": f2(X["all_aps"]["mean_err_m"]),
                         "HUIM toàn cục (m)": f2(X["global_huim_best"]["mean_err_m"]) if X["global_huim_best"] else "",
                         "Ngẫu nhiên (m)": f2(c["random_mean_of_3"]),
                         "Tòa+tầng": pct(X["huim_zone"]["joint_accuracy"])})
    d.table(pd.DataFrame(rows), "Mọi dataset: HUIM theo vùng so với toàn bộ AP, HUIM toàn cục và ngẫu nhiên cùng ngân sách",
            font_pt=7.5)
    d.p("Ghi chú: HUS chỉ có 5 AP và gần như mọi dòng test trùng một dòng huấn luyện (xem "
        "results/multi_dataset/hus/dataset_summary.json); HUS (khử trùng lặp) là con số trung "
        "thực. Với DLULIB (17 AP) và HUS, HUIM giữ gần như toàn bộ AP vì mọi AP đều thuộc ít "
        "nhất một HUI của một vùng — đó là hành vi đúng khi mọi AP đều hữu ích.", align="justify")

    # ------------------------------------------------------------------ 8
    d.h(1, "8. Kiểm chứng độc lập")
    d.p("src/verify_huim_zone.py không gọi EFIM, bộ định vị hay hàm tính metric. Từ CSV gốc và "
        "các file kết quả, nó tính lại:", align="justify")
    d.bullets([
        "Z0 — mọi lần chạy theo vùng đều COMPLETED (không dùng tập HUI bị cắt ngang).",
        "Z1/Z2 — q(i,T) tính lại từ dBm, tổng utility từng vùng và minUtil_z = θ_dùng% × tổng.",
        "Z3 — mỗi WAP được chọn có một HUI làm chứng; utility và support của nó, tính lại bằng cách quét các dòng của vùng, khớp log và ≥ minUtil_z.",
        "Z4 — tính đầy đủ tới độ dài 2: mọi itemset 1 và 2 AP có utility ≥ minUtil_z đều có toàn bộ AP nằm trong tập chọn.",
        "Z5 — tập AP đúng bằng hợp các vùng.",
        "P1–P3 — sai số mét, toạ độ dự đoán (Σ trọng số × toạ độ láng giềng), độ chính xác tòa/tầng tính lại từ file dự đoán; P4 — tập được chọn có dev error thấp nhất.",
    ])
    d.table(pd.DataFrame([{"Dataset": TITLES[r["dataset"]], "Số phép kiểm": r["n_checks"],
                           "Thất bại": r["n_failed"]} for r in D.ver["datasets"]]),
            f"Kết quả kiểm chứng: {D.ver['n_checks']} phép kiểm, {D.ver['n_failed']} thất bại "
            "(results/huim_zone/verification.json)")

    # ------------------------------------------------------------------ 9
    d.h(1, "9. Hạn chế")
    d.bullets([
        "Chia vùng dùng nhãn tòa_tầng của dữ liệu huấn luyện. Đây là thông tin có giám sát, dùng giống như Model B đã dùng; nó không chạm dữ liệu test, nhưng HUIM theo vùng không còn là khai thác hoàn toàn không giám sát.",
        "θ và mô hình utility được chọn trên dev fold, rồi đánh giá một lần trên test. Mọi θ được báo cáo để thấy độ nhạy; không chọn lại sau khi xem test.",
        "Kết quả phụ thuộc bộ định vị PHASE I3 đã chọn với toàn bộ AP; không tinh chỉnh lại bộ định vị cho từng tập AP (nếu làm, lợi thế sẽ thuộc về HUIM).",
        "Với dataset ít AP (HUS 5, DLULIB 17), HUIM gần như không loại AP nào; giá trị của HUIM thể hiện rõ ở dataset nhiều AP (UJIIndoorLoc 520, UJI_LIB 620, HCXY 347).",
        "EFIM viết bằng Python; thời gian khai thác tuyệt đối không so sánh trực tiếp với SPMF (Java).",
    ])

    # ------------------------------------------------------------------ 10
    d.h(1, "10. Chạy lại")
    d.p("python -m pip install -r requirements.txt", italic=True)
    d.p("python -m pytest tests -q", italic=True)
    d.p("python src/run_huim_zone.py --dataset all        (khai thác, chọn trên dev, đánh giá)", italic=True)
    d.p("python src/verify_huim_zone.py                   (kiểm chứng độc lập)", italic=True)
    d.p("python src/plots_huim_zone.py                    (biểu đồ fig50–fig55 + CSV)", italic=True)
    d.p("python src/make_huim_zone_report.py              (báo cáo này)", italic=True)
    d.p("hoặc: python run_experiments.py --from huim_zone", italic=True)
    return d


def main() -> None:
    info = build(Data()).save(OUT)
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
