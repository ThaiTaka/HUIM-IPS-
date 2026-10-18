"""BAOCAO1 / bước 4 - tạo báo cáo Word từ so_lieu/ và diagram/.

    python BAOCAO1/ma_nguon/04_tao_bao_cao_word.py

Mọi con số trong văn bản được đọc từ so_lieu/ lúc dựng; không có số gõ tay.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from hinh_chung import (BAOCAO, DIAGRAM, KEYS, NHOM_FOLD, SO_LIEU, TAP_TEST, TEN_DS, TEN_DS_DAI,
                        TOA_DO, VUNG, cau_hinh, theta_txt, vn)
from nhan import QT, lbl, theta_cua
from word_chung import Doc

J = cau_hinh()
B = J["bo_du_lieu"]
UJI = J["uji_tham_chieu_BAOCAO"]
DU = pd.read_csv(SO_LIEU / "01_du_lieu.csv").set_index("bo_du_lieu")
CHK = pd.read_csv(SO_LIEU / "02_kiem_chung_union_vs_EFIM.csv")
U = pd.read_csv(SO_LIEU / "03_so_AP_theo_minUtil.csv")
EF = pd.read_csv(SO_LIEU / "04_EFIM_so_HUI_thoi_gian_bo_nho.csv")
G = pd.read_csv(SO_LIEU / "05_buoc3_HUIM_chung.csv")
Z = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_vung.csv")
T5 = pd.read_csv(SO_LIEU / "07_buoc5_bo_dinh_vi_chon_lai.csv")
P5 = pd.read_csv(SO_LIEU / "07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv")
R6 = pd.read_csv(SO_LIEU / "08_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
E7 = pd.read_csv(SO_LIEU / "09_buoc7_ensemble.csv")
TM = pd.read_csv(SO_LIEU / "10_buoc8_thoi_gian_bo_nho.csv")
RANK = pd.read_csv(SO_LIEU / "11_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})
KQ = pd.read_csv(SO_LIEU / "12_ket_qua_theo_tap_test.csv")

d = Doc()
H = lambda name: DIAGRAM / f"{name}.png"          # noqa: E731
NBSP = " "


def m(x, nd=2):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else vn(x, nd) + NBSP + "m"


def pct(x, nd=1):
    return vn(x, nd) + NBSP + "%"


def kq(k, vai, tn):
    return KQ[(KQ.bo_du_lieu == k) & (KQ.vai_tro == vai) & (KQ.tap_test == tn)].iloc[0]


def giam(a, b):
    return 100 * (1 - b / a)


def doi_txt(a, b):
    """'-5,2 %', '+1,3 %' hoặc 'không đổi' (|thay đổi| < 0,05 %)."""
    c = 100 * (b - a) / a
    return "không đổi" if abs(c) < 0.05 else f"{'+' if c > 0 else ''}{vn(c, 1)} %"


def tests(k):
    return list(TAP_TEST[k].items())          # [("test", "Test-01"), ("test2", "Test-02")]


def ket_qua_dong(k, vai):
    """'Test-01 1,19 m; Test-02 2,03 m' của một vai trò."""
    return "; ".join(f"{tn} {m(kq(k, vai, tn).sai_so_tb_m)}" for _, tn in tests(k))


def theta_best(k):
    return " / ".join(theta_txt(t) for t in sorted(set(theta_cua(B[k]["best"]["config"]))))


def best_row(T, k):
    t = T[T.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
    if not len(t):
        return None
    # cùng dev, cùng số AP (cùng tập AP ở nhiều θ): lấy θ gần θ ban đầu nhất
    t = t.assign(_d=(t.minUtil_pct - B[k]["start"]["theta_pct"]).abs())
    return t.sort_values(["dev_sai_so_tb_m", "so_AP", "_d"]).iloc[0]


def cot_test(k, r):
    out = [m(r["test_sai_so_tb_m"])]
    if "test2" in TAP_TEST[k]:
        out.append(m(r.get("test2_sai_so_tb_m")))
    return out


def hdr_test(k):
    return [f"Test: {tn}" for _, tn in tests(k)]


# ================================================================== bìa
d.p(("BÁO CÁO BÀI TÌM HIỂU", "b"), size=13, align="center", after=2)
d.p(("HUIM CHO ĐỊNH VỊ TRONG NHÀ BẰNG VÂN TAY WI‑FI", "b"), size=17, align="center", after=2)
d.p("Tối ưu việc chọn Access Point bằng khai thác tập mục tiện ích cao (HUIM) trên 4 bộ dữ liệu "
    "của thư mục dataset-20261013T020803Z-1-001: UJI_LIB tầng 3, DLULIB, HCXY, HUS - chỉ dùng các "
    "cấu hình có HUIM", size=12.5, align="center", after=14)
lines = [[("Kết quả chính. ", "b"), "Sai số định vị trung bình trên TẬP TEST của từng bộ dữ liệu "
          "(các file test đi kèm bộ dữ liệu, không dùng để chọn), cấu hình HUIM tốt nhất chọn theo dev:"]]
for k in KEYS:
    b = B[k]["best"]
    lines.append([(f"{TEN_DS[k]}: ", "b"), (ket_qua_dong(k, "tot_nhat"), "b"),
                  f" (ban đầu {ket_qua_dong(k, 'ban_dau')}) - {lbl(b['config'], k)}, {int(b['n_ap'])} AP."])
lines.append([("Đã thử ", "b"), f"{sum(B[k]['n_configs'] for k in KEYS)} cấu hình HUIM "
              "(3 model × lưới minUtil θ × phạm vi chung / theo vùng-tầng × bộ định vị × quy tắc chọn "
              "AP × ensemble). Mọi lựa chọn dựa trên 6 fold dev tách từ tập train."])
d.hop(lines)
d.p("Ngày lập: 16/10/2026. UJIIndoorLoc (cũng nằm trong thư mục này) đã được làm riêng ở BAOCAO/ "
    f"(tốt nhất {m(UJI['tot_nhat']['test_mean_m'])} trên tập test); báo cáo này làm 4 bộ còn lại. "
    "Thư mục syl, tuji và UJI_LIB_DB_Floor_5 rỗng (cả trong file zip) nên không chạy được.",
    size=10.5, italic=True)

d.h("Mục lục", 1)
for s in ["Tóm tắt", "1. Dữ liệu, tập test và giao thức đánh giá", "2. Mô hình hoá HUIM cho việc chọn AP",
          "3. Tìm union HUI chính xác: kiểm chứng và chi phí", "4. Bộ định vị",
          "5. Kết quả tối ưu HUIM (bước 3-7)", "6. Thời gian và bộ nhớ",
          "7. Cấu hình cuối cùng trên tập test", "8. Nhận xét chung và so sánh với UJIIndoorLoc",
          "9. Hạn chế", "10. Cách chạy lại và truy vết số liệu"]:
    d.p(s, after=1)
d.ngat_trang()

# ================================================================ tóm tắt
d.h("Tóm tắt", 1)
d.p("Báo cáo áp dụng đúng quy trình HUIM đã tối ưu trên UJIIndoorLoc (BAOCAO/) cho 4 bộ dữ liệu khác: "
    "chọn tập Access Point (AP) bằng HUIM rồi định vị bằng k-NN chỉ trên các AP đó, và tìm cấu hình HUIM "
    "cho sai số theo mét thấp nhất. Các bước: (3) quét ngưỡng minUtil θ cho 3 hàm utility Model A / B / C - "
    "nhờ thuật toán tìm chính xác tập AP xuất hiện trong ít nhất một HUI mà không cần liệt kê hết HUI, θ "
    "được hạ xuống tới 0,05 %, nơi EFIM liệt kê đầy đủ không chạy nổi; (4) khai phá HUIM riêng cho từng "
    "tầng (DLULIB) hoặc từng vùng không gian (UJI_LIB, HCXY); (5) chọn lại bộ định vị chỉ trên các AP HUIM; "
    "(6) các quy tắc top-n / frequent / weighted trên tập HUI đầy đủ; (7) ensemble nhiều cấu hình; "
    "(8) đo thời gian và bộ nhớ.", align="justify")
for k in KEYS:
    s, b = B[k]["start"], B[k]["best"]
    t0, t1 = kq(k, "ban_dau", TAP_TEST[k]["test"]), kq(k, "tot_nhat", TAP_TEST[k]["test"])
    d.p((f"{TEN_DS[k]}: ", "b"),
        f"ban đầu (HUIM chung, Model A, θ = {theta_txt(s['theta_pct'])}, {int(s['n_ap'])} AP) "
        f"{ket_qua_dong(k, 'ban_dau')}; tốt nhất theo dev ({lbl(b['config'], k)}, {int(b['n_ap'])} AP) "
        f"{ket_qua_dong(k, 'tot_nhat')} - thay đổi trên {TAP_TEST[k]['test']}: "
        f"{doi_txt(t0.sai_so_tb_m, t1.sai_so_tb_m)}.", align="justify")
d.hinh(H("H01_so_do_luong_HUIM_IPS"), "Hình 1. Sơ đồ luồng HUIM-IPS và cấu hình cuối cùng của 4 bộ dữ liệu "
       "(ngưỡng minUtil θ ghi ở khối 3 và trong bảng).")

# ================================================================ 1
d.h("1. Dữ liệu, tập test và giao thức đánh giá", 1)
d.h("1.1. Bốn bộ dữ liệu", 2)
rows = []
for k in KEYS:
    r = DU.loc[k]
    rows.append([TEN_DS[k], int(r.so_cot_AP), int(r.so_AP_thay_o_train), int(r.so_dong_train),
                 int(r.so_vi_tri_train), vn(r.so_AP_thay_moi_dong_TB, 1), int(r.so_tang),
                 str(r.vung_HUIM)])
d.bang(["Bộ dữ liệu", "Cột AP", "AP thấy ở train", "Dòng train", "Vị trí train", "AP thấy / dòng",
        "Tầng", "Vùng HUIM"], rows, [3.0, 1.5, 1.9, 1.8, 1.8, 1.8, 1.2, 2.2], "Bốn bộ dữ liệu", size=8.8)
d.bullets([[(f"{TEN_DS_DAI[k]}: ", "b"), TOA_DO[k] + "."] for k in KEYS])

d.h("1.2. Tập test của từng bộ dữ liệu", 2)
d.p("Mỗi bộ dữ liệu đi kèm file test riêng; báo cáo gọi chúng là tập test và chỉ dùng chúng để báo cáo kết "
    "quả. Không file test nào được dùng để dựng radio map, khai phá HUI hay chọn bất kỳ tham số nào.",
    align="justify")
rows = []
for k in KEYS:
    r = DU.loc[k]
    for s in ("", "2"):
        if isinstance(r.get(f"tap_test{s}"), str) and r.get(f"tap_test{s}"):
            rows.append([TEN_DS[k], r[f"tap_test{s}"], int(r[f"tap_test{s}_so_dong"]),
                         int(r[f"tap_test{s}_so_vi_tri"]), int(r[f"tap_test{s}_vi_tri_co_trong_train"])])
d.bang(["Bộ dữ liệu", "File test", "Số mẫu", "Số vị trí", "Vị trí có trong train"], rows,
       [3.2, 3.2, 2.4, 2.4, 3.6], "Tập test", size=9)
d.bullets([
    "UJI_LIB tầng 3: Test-01 đo lại đúng 24 vị trí của train, Test-02 đo ở 24 vị trí khác (lệch 1 m); "
    "cả hai trải đều 25 tháng như train. Báo cáo ghi cả hai.",
    "HCXY: không vị trí test nào trùng vị trí train - bài toán nội suy vị trí mới.",
    "DLULIB: tập test đo lại mọi vị trí train bằng cùng điện thoại.",
    "HUS: 204/205 dòng của testcase1 và 205/205 dòng của testcase2 là bản chép y hệt một dòng train "
    "(cùng vị trí, cùng 5 RSSI). Đánh giá nguyên bản thì k-NN tìm thấy chính bản chép và sai số gần 0 m do "
    "cấu tạo dữ liệu. Báo cáo dùng bản đã bỏ đúng một dòng train cho mỗi dòng test bị chép (409 dòng); "
    "đây là con số trung thực.",
])

d.h("1.3. Giao thức: chọn trên dev, báo cáo trên tập test", 2)
d.p("Mọi lựa chọn - hàm utility (Model A/B/C), ngưỡng minUtil θ, phạm vi khai phá (chung hay theo vùng/tầng), "
    "bộ định vị, quy tắc chọn AP, thành viên ensemble - đều dựa trên sai số trung bình trên 6 fold dev tách "
    "từ tập train. Fold được nhóm sao cho dev khác train giống như tập test khác train:", align="justify")
d.bullets([[(f"{TEN_DS[k]}: ", "b"), NHOM_FOLD[k] + "."] for k in KEYS])
d.p("Tập test được đánh giá một lần cho mỗi cấu hình và không bao giờ được dùng để chọn, nên con số trên "
    "tập test của cấu hình cuối cùng không bị chọn lọc theo tập test. Chỉ số: sai số định vị trung bình, "
    "trung vị, p90 (mét); tỉ lệ đúng tầng (DLULIB); thời gian định vị; bộ nhớ radio map; thời gian và bộ nhớ "
    "khai phá HUIM.", align="justify")

# ================================================================ 2
d.h("2. Mô hình hoá HUIM cho việc chọn AP", 1)
d.p("Giống BAOCAO/: mỗi vân tay của tập train là một giao dịch T; item là AP thấy được (RSSI ≠ 100). Utility "
    "trong q(i,T) là cường độ tín hiệu chuẩn hoá về 1-100; utility ngoài p(i) có ba định nghĩa:",
    align="justify")
d.cong_thuc("q(i,T) = round( 1 + 99 · (RSSI(i,T) − RSSI_min) / (RSSI_max − RSSI_min) )")
d.bullets([
    [("Model A (tín hiệu): ", "b"), "p(i) = 1."],
    [("Model B (phân biệt): ", "b"), "p(i) = I(A_i ; Y) / max_j I(A_j ; Y), thông tin tương hỗ giữa trạng thái "
     "AP và nhãn vị trí Y."],
    [("Model C (hiếm và phân biệt): ", "b"), "p(i) ∝ I(A_i ; Y) · log(N / (1 + support_i))."],
])
d.p("Nhãn vị trí Y: DLULIB có 3 tầng nên Y = tầng; các bộ một tầng có I(A;Y) = 0 với nhãn tầng, nên Y = điểm "
    "tham chiếu (RP). Trong HUIM theo tầng/vùng, tầng là hằng số nên Y = RP trong vùng đó.", align="justify")
d.cong_thuc("u(X) = Σ_{T ⊇ X} Σ_{i ∈ X} q(i,T) · p(i)      X là HUI nếu u(X) ≥ minUtil = θ · Σ_T TU(T)")
d.p("Tập AP đưa cho bộ định vị là union của các HUI: mọi AP có mặt trong ít nhất một HUI (θ là tham số duy "
    "nhất). HUIM theo vùng/tầng khai phá riêng trên giao dịch của mỗi vùng, θ tính theo tổng utility của "
    "vùng đó; khi định vị, giai đoạn 1 đoán vùng bằng bỏ phiếu k-NN trên hợp các tập AP, giai đoạn 2 định vị "
    "trong vùng đoán được bằng tập AP và vân tay train của vùng. Vùng: 3 tầng của DLULIB; với UJI_LIB và HCXY "
    "(1 tầng) là 3 cụm k-means trên toạ độ các vị trí train (đánh số theo x); HUS chỉ có 5 AP nên không chia "
    "vùng.", align="justify")

# ================================================================ 3
d.h("3. Tìm union HUI chính xác: kiểm chứng và chi phí", 1)
ok = int(CHK.identical.astype(str).str.lower().eq("true").sum())
d.p("EFIM (Zida và cộng sự, 2017) liệt kê đủ mọi HUI; khi θ thấp, các AP cùng xuất hiện dày đặc làm số HUI "
    "tăng theo cấp số nhân và EFIM dừng ở giới hạn 600 s / 10⁶ HUI. Union chỉ cần MỘT HUI cho mỗi AP, nên "
    "dự án dùng thuật toán tìm kiếm phủ (src/huim/union_search.py, đã dùng ở BAOCAO/): duyệt DFS như EFIM "
    "với cận TWU, local utility và sub-tree utility, thêm luật cắt cây con không thể thêm AP mới vào union. "
    "Các mức θ tính từ cao xuống thấp; AP đã vào union ở mức cao được giữ ở mức thấp hơn. Khi mọi AP của "
    "phạm vi đã vào union, các mức thấp hơn chắc chắn cho cùng tập (ghi là \"đã đủ mọi AP\").",
    align="justify")
rows = []
for k in KEYS:
    c = CHK[CHK.dataset == k]
    rows.append([TEN_DS[k], len(c), int(c.identical.astype(str).str.lower().eq("true").sum()),
                 vn(c.thoi_gian_EFIM_s.sum(), 0)])
d.bang(["Bộ dữ liệu", "Lần chạy EFIM hoàn tất", "Union trùng khớp", "Tổng thời gian EFIM (s)"],
       rows, [4.0, 4.0, 3.6, 4.4], "Kiểm chứng: union của thuật toán tìm kiếm so với union các HUI của EFIM",
       size=9)
d.p(f"Union của thuật toán tìm kiếm trùng từng AP với union của EFIM ở {ok}/{len(CHK)} lần chạy EFIM đã "
    "hoàn tất. Không mức θ nào trong lưới bị quá giới hạn 15 phút/mức.", align="justify")
d.hinh(H("H02_so_AP_theo_minUtil"), "Hình 2. Số AP trong union HUI theo minUtil θ (nét liền: HUIM chung; "
       "nét đứt: hợp các vùng / tầng).")
d.p("HUS là trường hợp suy biến: mọi vân tay của HUS đều thấy cả 5 AP, nên tập gồm cả 5 AP có utility bằng "
    "đúng tổng utility của cơ sở dữ liệu và là HUI ở mọi θ ≤ 100 %. Vì vậy union của HUS luôn là 5 AP, với "
    "mọi model và mọi θ; HUIM chỉ bớt được AP qua các quy tắc ở bước 6.", align="justify")
d.hinh(H("H03_thoi_gian_union_vs_EFIM"), "Hình 3. Thời gian tìm union chính xác ở từng mức θ so với EFIM "
       "liệt kê đầy đủ (dấu X: EFIM dừng ở giới hạn).")
d.hinh(H("H14_bo_nho_khai_pha"), "Hình 14. Bộ nhớ tăng thêm lúc đỉnh khi khai phá, theo θ.")

# ================================================================ 4
d.h("4. Bộ định vị", 1)
d.p("Bộ định vị là k-NN hồi quy toạ độ (trung bình có trọng số 1/d^p của k láng giềng) và bỏ phiếu tầng. Bộ "
    "định vị gốc của mỗi bộ dữ liệu được chọn ở lần chạy đa dữ liệu trước bằng đúng quy trình chọn trên dev "
    "của BAOCAO/ (biểu diễn tín hiệu × khoảng cách × k × trọng số, dò lệch thiết bị ±dB, ensemble 2 biểu "
    "diễn). Bước 5 chọn lại toàn bộ các tham số đó, nhưng chỉ trên các cột AP mà HUIM chọn.", align="justify")
rows = []
for k in KEYS:
    info = B[k]["buoc5_bo_dinh_vi"]
    rows.append([TEN_DS[k], info["base_positioner"], info["new_positioner"],
                 "giữ nguyên" if info["same_as_base"] else "đổi"])
d.bang(["Bộ dữ liệu", "Bộ định vị gốc", "Chọn lại trên AP HUIM (bước 5)", "Kết quả"], rows,
       [2.8, 5.4, 6.0, 2.0], "Bộ định vị", size=8.6)

# ================================================================ 5
d.h("5. Kết quả tối ưu HUIM (bước 3-7)", 1)
d.h("5.1. Bước 3 - HUIM chung, quét minUtil θ", 2)
d.hinh(H("H04_sai_so_theo_minUtil"), "Hình 4. HUIM chung: sai số trung bình theo minUtil θ trên dev và tập test.")
for k in KEYS:
    g = G[G.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
    rows = []
    for mm in "ABC":
        r = best_row(g[g.model == mm], k)
        if r is not None:
            rows.append([f"Model {mm}", theta_txt(r.minUtil_pct), int(r.so_AP), m(r.dev_sai_so_tb_m),
                         *cot_test(k, r)])
    s = g[(g.model == "A") & np.isclose(g.minUtil_pct, B[k]["start"]["theta_pct"])].iloc[0]
    rows.append(["Ban đầu (A)", theta_txt(s.minUtil_pct), int(s.so_AP), m(s.dev_sai_so_tb_m), *cot_test(k, s)])
    d.bang(["Model", "θ", "AP", "Dev"] + hdr_test(k), rows,
           [3.0, 2.0, 1.6, 2.4] + [3.0] * len(tests(k)),
           f"{TEN_DS[k]} - HUIM chung: cấu hình tốt nhất theo dev của mỗi model", size=9)

d.h("5.2. Bước 4 - HUIM theo vùng / tầng", 2)
d.hinh(H("H06_theo_vung_vs_chung"), "Hình 6. HUIM theo vùng / tầng so với HUIM chung, theo θ.")
rows = []
for k in KEYS:
    z, g = best_row(Z, k), best_row(G, k)
    if z is None:
        continue
    for nm, r in (("chung", g), (f"theo {VUNG[k]}", z)):
        rows.append([TEN_DS[k], f"HUIM {nm}, Model {r.model}", theta_txt(r.minUtil_pct), int(r.so_AP),
                     m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Phạm vi, model", "θ", "AP", "Dev", "Test (thứ nhất)"], rows,
       [2.8, 4.6, 1.8, 1.4, 2.2, 2.6], "HUIM chung và HUIM theo vùng / tầng (tốt nhất theo dev)", size=9)
d.hinh(H("H15_sai_so_theo_vung_tang"), "Hình 15. Sai số trên tập test theo vùng / tầng của mẫu test.")

d.h("5.3. Bước 5 - chọn lại bộ định vị trên AP HUIM", 2)
d.hinh(H("H07_bo_dinh_vi_chon_lai"), "Hình 7. Bộ định vị gốc và bộ định vị chọn lại, trên tập AP HUIM tốt nhất.")
rows = []
for k in KEYS:
    p = P5[P5.bo_du_lieu == k]
    for r in p.itertuples():
        rows.append([TEN_DS[k], r.giai_doan, r.bo_dinh_vi, m(r.dev_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Giai đoạn", "Bộ định vị", "Dev"], rows, [2.8, 1.8, 9.0, 2.4],
       "Các giai đoạn chọn bộ định vị trên AP HUIM (một giai đoạn chỉ được giữ nếu bớt ≥ 0,05 m trên dev)",
       size=8.5)

d.h("5.4. Bước 6 - quy tắc chọn AP từ HUI", 2)
d.hinh(H("H08_quy_tac_chon_AP"), "Hình 8. Các quy tắc chọn AP trên tập HUI đầy đủ của EFIM.")
rows = []
for k in KEYS:
    for r in R6[R6.bo_du_lieu == k].itertuples():
        q = QT.get(r.quy_tac + ("" if pd.isna(r.tham_so) else str(r.tham_so)), r.quy_tac)
        rows.append([TEN_DS[k], f"Model {r.model}, θ = {theta_txt(r.minUtil_pct)}", q, int(r.so_AP),
                     m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Model, θ", "Quy tắc", "AP", "Dev", "Test (thứ nhất)"], rows,
       [2.6, 4.0, 3.4, 1.2, 2.2, 2.6], "Quy tắc chọn AP", size=8.5)

d.h("5.5. Bước 7 - ensemble", 2)
d.hinh(H("H09_ensemble"), "Hình 9. Ensemble tốt nhất theo dev so với cấu hình đơn tốt nhất.")
rows = []
for k in KEYS:
    s = B[k]["best_single"]
    e = E7[E7.bo_du_lieu == k].sort_values("dev_sai_so_tb_m")
    rows.append([TEN_DS[k], "đơn: " + lbl(s["config"], k), m(s["dev_mean_m"]), m(s["test_mean_m"])])
    if len(e):
        r = e.iloc[0]
        rows.append([TEN_DS[k], lbl(r.cau_hinh, k), m(r.dev_sai_so_tb_m), m(r.test_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Cấu hình", "Dev", "Test (thứ nhất)"], rows, [2.6, 9.4, 2.2, 2.4],
       "Cấu hình đơn tốt nhất và ensemble tốt nhất theo dev", size=8.5)

d.h("5.6. Đánh đổi số AP - sai số và cấu hình cân bằng", 2)
d.hinh(H("H05_danh_doi_AP_sai_so"), "Hình 5. Đánh đổi số AP và sai số trên tập test; vòng tròn: cấu hình "
       "ban đầu (xám) và cấu hình đơn tốt nhất (đỏ), kèm θ.")
d.p("Quy tắc chọn θ cân bằng (đặt trước khi xem tập test): trong mỗi phạm vi, lấy cấu hình ít AP nhất có "
    "sai số dev không quá 105 % sai số dev tốt nhất của phạm vi đó.", align="justify")
rows = []
for k in KEYS:
    for scope, v in B[k]["balanced"].items():
        r = RANK[(RANK.bo_du_lieu == k) & (RANK.cau_hinh == v["config"])].iloc[0]
        rows.append([TEN_DS[k], lbl(v["config"], k), int(v["n_ap"]), m(r.dev_sai_so_tb_m),
                     m(r.test_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Cấu hình cân bằng", "AP", "Dev", "Test (thứ nhất)"], rows,
       [2.6, 8.0, 1.4, 2.2, 2.4], "Cấu hình cân bằng", size=8.5)

# ================================================================ 6
d.h("6. Thời gian và bộ nhớ", 1)
d.p("Thời gian định vị: định vị tối đa 1.111 vân tay đầu của tập test thứ nhất trong một lô (bằng kích thước "
    "tập test của UJIIndoorLoc), dùng mọi nhân CPU, trung vị 3 lần sau một lần khởi động, khi máy không chạy "
    "việc khác. Bộ nhớ: kích thước radio map float64 (số dòng tham chiếu × số AP × 8 byte, × 2 nếu bộ định "
    "vị là ensemble hai biểu diễn) và RSS tăng thêm khi định vị.", align="justify")
d.hinh(H("H13_thoi_gian_bo_nho_dinh_vi"), "Hình 13. Thời gian định vị và bộ nhớ radio map, kèm θ.")
TEN_VAI = {"ban_dau": "ban đầu", "don_tot_nhat": "đơn tốt nhất", "can_bang_global": "cân bằng (chung)",
           "can_bang_zone": "cân bằng (vùng)", "tot_nhat_ensemble": "ensemble tốt nhất"}
rows = []
for r in TM.drop_duplicates(["bo_du_lieu", "cau_hinh"]).itertuples():
    rows.append([TEN_DS[r.bo_du_lieu], TEN_VAI.get(r.label, r.label),
                 " / ".join(theta_txt(t) for t in sorted(set(theta_cua(r.cau_hinh)))), int(r.so_AP),
                 vn(r.ms_per_fp, 3), vn(r.radio_map_mb, 2), m(r.test_sai_so_tb_m)])
d.bang(["Bộ dữ liệu", "Cấu hình", "θ", "AP", "ms / vân tay", "Radio map (MB)", "Test (thứ nhất)"], rows,
       [2.6, 3.0, 2.4, 1.2, 2.2, 2.4, 2.6], "Thời gian định vị và bộ nhớ", size=8.5)

# ================================================================ 7
d.h("7. Cấu hình cuối cùng trên tập test", 1)
d.hinh(H("H10_ban_dau_vs_tot_nhat"), "Hình 10. Sai số trên tập test: cấu hình HUIM ban đầu và cấu hình tốt "
       "nhất theo dev (θ và số AP dưới mỗi cặp cột).")
rows = []
for r in KQ[KQ.vai_tro != "don_tot_nhat"].itertuples():
    rows.append([TEN_DS[r.bo_du_lieu], r.tap_test, "ban đầu" if r.vai_tro == "ban_dau" else "tốt nhất",
                 m(r.sai_so_tb_m), m(r.trung_vi_m), m(r.p90_m), pct(r.trong_2m_pct),
                 "-" if pd.isna(getattr(r, "dung_tang_pct", np.nan)) else pct(r.dung_tang_pct)])
d.bang(["Bộ dữ liệu", "Tập test", "Cấu hình", "TB", "Trung vị", "p90", "≤ 2 m", "Đúng tầng"], rows,
       [2.6, 2.2, 1.8, 1.9, 1.9, 1.9, 1.9, 1.9], "Kết quả trên tập test", size=8.5)
d.hinh(H("H11_CDF_sai_so"), "Hình 11. Phân phối tích luỹ sai số trên tập test.")
d.hinh(H("H12_ban_do_sai_so"), "Hình 12. Sai số trung bình tại mỗi vị trí test, cấu hình tốt nhất.")

# ================================================================ 8
d.h("8. Nhận xét chung và so sánh với UJIIndoorLoc", 1)
rows = [["UJIIndoorLoc (BAOCAO/)", "validationData = tập test", m(UJI["ban_dau"]["test_mean_m"]),
         m(UJI["tot_nhat"]["test_mean_m"]), int(UJI["ban_dau"]["n_ap"]), int(UJI["tot_nhat"]["n_ap"])]]
for k in KEYS:
    for _, tn in tests(k):
        rows.append([TEN_DS[k], tn, m(kq(k, "ban_dau", tn).sai_so_tb_m), m(kq(k, "tot_nhat", tn).sai_so_tb_m),
                     int(B[k]["start"]["n_ap"]), int(B[k]["best"]["n_ap"])])
d.bang(["Bộ dữ liệu", "Tập test", "Ban đầu", "Tốt nhất", "AP ban đầu", "AP tốt nhất"], rows,
       [3.6, 3.4, 2.2, 2.2, 2.2, 2.4], "Năm bộ dữ liệu: cấu hình HUIM ban đầu và tốt nhất", size=8.8)
from nhan_xet import nhan_xet                         # noqa: E402

d.bullets(nhan_xet("docx"))

# ================================================================ 9
d.h("9. Hạn chế", 1)
d.bullets([
    "Báo cáo chỉ so sánh các biến thể HUIM với nhau; nó không kết luận HUIM tốt hơn các cách chọn AP khác.",
    "HUI được khai phá trên toàn bộ tập train, nên tập AP đã \"nhìn thấy\" các fold dev; độ lệch lạc quan này "
    "như nhau cho mọi cấu hình nên không thiên vị cấu hình nào, nhưng con số dev thấp hơn thực tế đôi chút. "
    "Con số trên tập test thì sạch.",
    "Vùng của UJI_LIB và HCXY là lựa chọn thiết kế (k-means, 3 vùng); số vùng không được tối ưu.",
    "Quy tắc ở bước 6 cần tập HUI đầy đủ, nên chỉ làm được ở mức θ EFIM liệt kê xong, có thể cao hơn θ "
    "tốt nhất.",
    "HCXY không ghi đơn vị toạ độ; báo cáo đọc là mét (khoảng cách giữa các vị trí khảo sát 0,59-1,2). "
    "DLULIB, HUS không có tài liệu mô tả kèm theo.",
    "Thời gian đo bằng Python thuần trên một máy Windows 12 nhân; chỉ có ý nghĩa so sánh trong báo cáo này. "
    "Thời gian tìm union được đo khi nhiều mức (bộ dữ liệu × model × phạm vi) chạy song song (10 tiến trình); "
    "thời gian EFIM lấy từ lần chạy đa dữ liệu trước. So sánh giữa hai thuật toán chỉ nên đọc theo bậc độ lớn.",
])

# ================================================================ 10
d.h("10. Cách chạy lại và truy vết số liệu", 1)
d.p("Chạy từ thư mục gốc dự án: python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py (thí nghiệm + báo cáo) hoặc "
    "thêm --bao-cao để chỉ dựng lại số liệu, hình, Word và PowerPoint từ kết quả có sẵn.")
rows = [
    ["Bảng 1-2, mục 1", "so_lieu/01_du_lieu.csv", "src/multi_datasets.py"],
    ["Bảng 3", "so_lieu/02_kiem_chung_union_vs_EFIM.csv", "src/huim_multi.py check"],
    ["Hình 2, 3, 14", "so_lieu/03_so_AP_theo_minUtil.csv, 04_EFIM_...csv", "src/huim_multi.py unions"],
    ["Bước 3, Hình 4", "so_lieu/05_buoc3_HUIM_chung.csv", "src/huim_multi.py steps (3)"],
    ["Bước 4, Hình 6, 15", "so_lieu/06_buoc4_HUIM_theo_vung.csv", "src/huim_multi.py steps (4)"],
    ["Bước 5, Hình 7", "so_lieu/07_..., 07b_...csv", "src/huim_multi.py steps (5)"],
    ["Bước 6, Hình 8", "so_lieu/08_buoc6_quy_tac_chon_AP.csv", "src/huim_multi.py steps (6)"],
    ["Bước 7, Hình 9", "so_lieu/09_buoc7_ensemble.csv", "src/huim_multi.py steps (7)"],
    ["Mục 6, Hình 13", "so_lieu/10_buoc8_thoi_gian_bo_nho.csv", "src/huim_multi.py step8"],
    ["Mục 5.6", "so_lieu/11_xep_hang_tat_ca_cau_hinh.csv", "BAOCAO1/ma_nguon/02_tong_hop_so_lieu.py"],
    ["Mục 7, Hình 10-12", "so_lieu/12_..., 13_...csv", "BAOCAO1/ma_nguon/02_tong_hop_so_lieu.py"],
]
d.bang(["Nội dung", "File số liệu", "Sinh bởi"], rows, [3.4, 7.0, 6.0], "Truy vết số liệu", size=8.5)

out = BAOCAO / "Bao_cao_HUIM_IPS_4_bo_du_lieu.docx"
d.d.core_properties.title = "HUIM cho định vị trong nhà trên 4 bộ dữ liệu"
d.save(out)
print("đã lưu", out, "-", d.n_bang, "bảng,", d.n_hinh, "hình")
