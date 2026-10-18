"""BAOCAO1 / bước 5 - tạo slide PowerPoint (16:9) từ so_lieu/ và diagram/.

    python BAOCAO1/ma_nguon/05_tao_slide_pptx.py

Biểu đồ cột là biểu đồ gốc của PowerPoint (sửa được số liệu trong PowerPoint); hình nhiều
ô (đường theo θ, CDF, bản đồ, sơ đồ) lấy từ diagram/. Mọi số đọc từ so_lieu/.
"""
from __future__ import annotations

import pandas as pd
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE

from hinh_chung import BAOCAO, KEYS, SO_LIEU, TAP_TEST, TEN_DS, VUNG, cau_hinh, theta_txt, vn
from nhan import lbl, theta_cua
from slide_chung import (BLANK, DEV, GREY, ICE, INK2, NAVY, SOFT, VAL, WHITE, Hh, W, bar_chart,
                         bullets, card, footer, m, picture, prs, text, title)

from nhan_xet import ensemble_txt, ket_luan, y_chinh   # noqa: E402

J = cau_hinh()
B = J["bo_du_lieu"]
UJI = J["uji_tham_chieu_BAOCAO"]
DU = pd.read_csv(SO_LIEU / "01_du_lieu.csv").set_index("bo_du_lieu")
CHK = pd.read_csv(SO_LIEU / "02_kiem_chung_union_vs_EFIM.csv")
KQ = pd.read_csv(SO_LIEU / "12_ket_qua_theo_tap_test.csv")
ok = int(CHK.identical.astype(str).str.lower().eq("true").sum())


def kq(k, vai, tn):
    return KQ[(KQ.bo_du_lieu == k) & (KQ.vai_tro == vai) & (KQ.tap_test == tn)].iloc[0]


def th_best(k):
    return " / ".join(theta_txt(t) for t in sorted(set(theta_cua(B[k]["best"]["config"]))))


def nen_toi(s):
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY


# ------------------------------------------------------------ 1. bìa
s = prs.slides.add_slide(BLANK)
nen_toi(s)
text(s, 0.7, 0.55, 11.5, 0.5, "BÁO CÁO BÀI TÌM HIỂU · 4 bộ dữ liệu Wi-Fi", size=16, color=ICE)
text(s, 0.7, 1.05, 11.9, 1.2, "HUIM cho định vị trong nhà bằng vân tay Wi-Fi", size=38, bold=True,
     color=WHITE, font="Cambria")
text(s, 0.7, 2.2, 11.9, 0.8, "UJI_LIB tầng 3 · DLULIB · HCXY · HUS - chọn Access Point bằng HUIM, "
     "tối ưu sai số theo mét, chỉ dùng cấu hình có HUIM", size=17, color=ICE)
for i, k in enumerate(KEYS):
    tn = TAP_TEST[k]["test"]
    b, s0 = kq(k, "tot_nhat", tn), kq(k, "ban_dau", tn)
    card(s, 0.7 + i * 3.05, 3.45, 2.85, 2.55, m(b.sai_so_tb_m),
         f"{TEN_DS[k]} · tập test {tn}\nban đầu {m(s0.sai_so_tb_m)}\nθ = {th_best(k)}, "
         f"{int(B[k]['best']['n_ap'])} AP", fill=RGBColor(0x18, 0x4F, 0x95), big_color=WHITE,
         small_color=ICE)
text(s, 0.7, 6.35, 11.9, 0.7, "16/10/2026 · chọn cấu hình trên 6 fold dev tách từ tập train; tập test "
     "(các file test của bộ dữ liệu) chỉ dùng để báo cáo · UJIIndoorLoc: xem BAOCAO/", size=12, color=ICE)

# ------------------------------------------------------------ 2. dữ liệu và tập test
s = prs.slides.add_slide(BLANK)
title(s, "Dữ liệu và tập test", "Mọi con số \"trên tập test\" là sai số trên các file test đi kèm bộ dữ liệu")
for i, k in enumerate(KEYS):
    r = DU.loc[k]
    tt = " + ".join(f"{tn} ({vn(r[f'tap_test{s_}_so_dong'], 0)} mẫu)" for s_, tn in
                    zip(("", "2"), TAP_TEST[k].values()))
    card(s, 0.6 + i * 3.1, 1.7, 2.95, 2.7, f"{int(r.so_AP_thay_o_train)} AP",
         f"{TEN_DS[k]}\ntrain {vn(r.so_dong_train, 0)} dòng, {int(r.so_vi_tri_train)} vị trí"
         + f"\ntest: {tt}")
bullets(s, 0.6, 4.7, 12.2, 2.3, [
    ["Chọn mọi thứ trên ", ("6 fold dev tách từ tập train", True),
     " (nhóm theo tháng / lần lấy mẫu / vị trí / ngẫu nhiên, giống cách tập test khác train)"],
    ["HUS: 409 dòng test là ", ("bản chép y hệt dòng train", True), " → bỏ một bản chép khỏi train cho mỗi dòng test"],
    ["syl, tuji, UJI_LIB_DB_Floor_5 rỗng; UJIIndoorLoc đã làm ở BAOCAO/ ("
     + m(UJI["tot_nhat"]["test_mean_m"]) + " trên tập test)"],
], size=15)
footer(s, "Nguồn: so_lieu/01_du_lieu.csv; giao thức: báo cáo Word mục 1")

# ------------------------------------------------------------ 3. luồng
s = prs.slides.add_slide(BLANK)
title(s, "Luồng HUIM-IPS", "vân tay → giao dịch utility → HUIM (θ) → tập AP → k-NN → sai số trên tập test")
picture(s, "H01_so_do_luong_HUIM_IPS", 1.0, 1.5, w=11.3)

# ------------------------------------------------------------ 4. union chính xác
s = prs.slides.add_slide(BLANK)
title(s, "Union HUI chính xác ở mọi θ", "Chỉ cần MỘT HUI cho mỗi AP - hạ θ tới 0,05 % mà không liệt kê hết HUI")
picture(s, "H02_so_AP_theo_minUtil", 0.4, 1.6, w=9.3)
card(s, 9.95, 1.7, 2.9, 1.9, f"{ok}/{len(CHK)}", "mức θ EFIM chạy xong: union trùng khớp từng AP")
bullets(s, 9.95, 3.85, 3.0, 3.0, [
    "HUS: mọi vân tay thấy cả 5 AP → tập 5 AP có utility = 100 % → union luôn 5 AP",
    "DLULIB: 17 AP, union đủ 17 AP từ θ ≈ 1 %",
], size=13)
footer(s, "Nguồn: so_lieu/02_kiem_chung_union_vs_EFIM.csv, 03_so_AP_theo_minUtil.csv; src/huim/union_search.py")

# ------------------------------------------------------------ 5. chi phí khai phá
s = prs.slides.add_slide(BLANK)
title(s, "Chi phí khai phá theo θ", "Tìm union chính xác so với EFIM liệt kê đầy đủ (X: EFIM dừng ở 600 s / 10⁶ HUI)")
picture(s, "H03_thoi_gian_union_vs_EFIM", 0.5, 1.6, w=12.3)
footer(s, "Nguồn: so_lieu/03_so_AP_theo_minUtil.csv, 04_EFIM_so_HUI_thoi_gian_bo_nho.csv")

# ------------------------------------------------------------ 6. bước 3
s = prs.slides.add_slide(BLANK)
title(s, "Bước 3 · HUIM chung, quét minUtil θ", "Nét liền: tập test · nét chấm: dev (dùng để chọn) · đỏ: θ được chọn")
picture(s, "H04_sai_so_theo_minUtil", 0.5, 1.6, w=12.3)
footer(s, "Nguồn: so_lieu/05_buoc3_HUIM_chung.csv")

# ------------------------------------------------------------ 7. đánh đổi
s = prs.slides.add_slide(BLANK)
title(s, "Đánh đổi số AP và sai số", "Mỗi điểm là một (phạm vi, model, θ); vòng đỏ: cấu hình đơn tốt nhất theo dev")
picture(s, "H05_danh_doi_AP_sai_so", 0.5, 1.6, w=12.3)
footer(s, "Nguồn: so_lieu/05_..., 06_buoc4_HUIM_theo_vung.csv")

# ------------------------------------------------------------ 8. bước 4
s = prs.slides.add_slide(BLANK)
title(s, "Bước 4 · HUIM theo vùng / tầng", "Đoán vùng trước, rồi định vị bằng AP và vân tay của vùng đó")
picture(s, "H06_theo_vung_vs_chung", 0.6, 1.6, w=12.1)
footer(s, "Nguồn: so_lieu/06_buoc4_HUIM_theo_vung.csv · vùng: 3 tầng (DLULIB), 3 cụm k-means (UJI_LIB, HCXY)")

# ------------------------------------------------------------ 9. bước 5
s = prs.slides.add_slide(BLANK)
title(s, "Bước 5 · Chọn lại bộ định vị trên AP HUIM", "Biểu diễn × khoảng cách × k × trọng số × lệch thiết bị × ensemble, trên dev")
picture(s, "H07_bo_dinh_vi_chon_lai", 0.5, 1.6, w=12.3)
footer(s, "Nguồn: so_lieu/07_..., 07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv")

# ------------------------------------------------------------ 10. bước 6
s = prs.slides.add_slide(BLANK)
title(s, "Bước 6 · Quy tắc chọn AP từ HUI", "union / top-n / frequent / weighted trên tập HUI đầy đủ của EFIM")
picture(s, "H08_quy_tac_chon_AP", 0.5, 1.6, w=12.3)
footer(s, "Nguồn: so_lieu/08_buoc6_quy_tac_chon_AP.csv")

# ------------------------------------------------------------ 11. bước 7
s = prs.slides.add_slide(BLANK)
title(s, "Bước 7 · Ensemble nhiều cấu hình HUIM", "toạ độ = trung bình / trung vị của các thành viên; tầng = đa số")
E7 = pd.read_csv(SO_LIEU / "09_buoc7_ensemble.csv")
cats, a, b = [], [], []
for k in KEYS:
    e = E7[E7.bo_du_lieu == k].sort_values("dev_sai_so_tb_m")
    if not len(e):
        continue
    sg = B[k]["best_single"]
    th_s = theta_txt(sg["theta_pct"])
    th_e = " / ".join(theta_txt(x) for x in sorted(set(theta_cua(e.iloc[0].cau_hinh))))
    cats.append(f"{TEN_DS[k]} · θ đơn {th_s} · ensemble {th_e}")
    a.append(sg["test_mean_m"])
    b.append(e.iloc[0].test_sai_so_tb_m)
ch = bar_chart(s, 0.6, 1.55, 8.3, 5.3, cats, [("đơn tốt nhất theo dev", a), ("ensemble tốt nhất theo dev", b)],
               [DEV, VAL], kind=XL_CHART_TYPE.BAR_CLUSTERED, y_title="Sai số trên tập test thứ nhất (m)",
               fmt='0.000')
ch.category_axis.reverse_order = True
bullets(s, 9.2, 1.8, 3.7, 5.0, ensemble_txt("pptx"), size=13)
footer(s, "Nguồn: so_lieu/09_buoc7_ensemble.csv; chi tiết 5 ensemble tốt nhất mỗi bộ: diagram/H09_ensemble.png")

# ------------------------------------------------------------ 12. kết quả trên tập test
s = prs.slides.add_slide(BLANK)
title(s, "Kết quả trên tập test", "Cấu hình HUIM ban đầu và cấu hình tốt nhất theo dev")
cats, a, b = [], [], []
for k in KEYS:
    for _, tn in TAP_TEST[k].items():
        cats.append(f"{TEN_DS[k]} · {tn} · θ {theta_txt(B[k]['start']['theta_pct'])} → {th_best(k)}")
        a.append(kq(k, "ban_dau", tn).sai_so_tb_m)
        b.append(kq(k, "tot_nhat", tn).sai_so_tb_m)
ch = bar_chart(s, 0.6, 1.55, 12.1, 5.4, cats, [("ban đầu", a), ("tốt nhất theo dev", b)], [GREY, VAL],
               kind=XL_CHART_TYPE.BAR_CLUSTERED, y_title="Sai số trung bình trên tập test (m)", fmt='0.00')
ch.category_axis.reverse_order = True
footer(s, "Nguồn: so_lieu/12_ket_qua_theo_tap_test.csv")

# ------------------------------------------------------------ 13. CDF
s = prs.slides.add_slide(BLANK)
title(s, "Phân phối sai số trên tập test", "ban đầu (xám) và tốt nhất (xanh); θ trong tiêu đề mỗi ô")
picture(s, "H11_CDF_sai_so", 0.5, 1.7, w=12.3)
footer(s, "Nguồn: so_lieu/13_du_doan_tung_mau_tap_test.csv")

# ------------------------------------------------------------ 14. theo vùng / tầng + bản đồ
s = prs.slides.add_slide(BLANK)
title(s, "Sai số theo vùng / tầng", "tập test thứ nhất: ban đầu và tốt nhất; θ trong tiêu đề mỗi ô")
picture(s, "H15_sai_so_theo_vung_tang", 0.9, 1.6, w=11.5)
footer(s, "Nguồn: so_lieu/13_du_doan_tung_mau_tap_test.csv")

s = prs.slides.add_slide(BLANK)
title(s, "Sai số trên bản đồ", "sai số trung bình tại mỗi vị trí test, cấu hình tốt nhất; θ trong tiêu đề mỗi ô")
picture(s, "H12_ban_do_sai_so", 0.5, 1.7, w=12.3)
footer(s, "Nguồn: so_lieu/13_du_doan_tung_mau_tap_test.csv")

# ------------------------------------------------------------ 15. thời gian & bộ nhớ
s = prs.slides.add_slide(BLANK)
title(s, "Thời gian và bộ nhớ", "định vị ≤ 1.111 vân tay test một lô, trung vị 3 lần, máy rảnh")
picture(s, "H13_thoi_gian_bo_nho_dinh_vi", 1.25, 1.45, h=5.45)
footer(s, "Nguồn: so_lieu/10_buoc8_thoi_gian_bo_nho.csv; khai phá: so_lieu/03_..., 04_... (Hình 3, 14)")

# ------------------------------------------------------------ 16. năm bộ dữ liệu
s = prs.slides.add_slide(BLANK)
title(s, "Năm bộ dữ liệu", "HUIM ban đầu và tốt nhất trên tập test (UJIIndoorLoc: BAOCAO/)")
cats = [f"UJIIndoorLoc · θ {theta_txt(UJI['ban_dau']['theta_pct'])} → 0,5 %"]
a, b = [UJI["ban_dau"]["test_mean_m"]], [UJI["tot_nhat"]["test_mean_m"]]
for k in KEYS:
    tn = TAP_TEST[k]["test"]
    cats.append(f"{TEN_DS[k]} · {tn} · θ {theta_txt(B[k]['start']['theta_pct'])} → {th_best(k)}")
    a.append(kq(k, "ban_dau", tn).sai_so_tb_m)
    b.append(kq(k, "tot_nhat", tn).sai_so_tb_m)
ch = bar_chart(s, 0.6, 1.55, 7.8, 5.4, cats, [("ban đầu", a), ("tốt nhất", b)], [GREY, VAL],
               kind=XL_CHART_TYPE.BAR_CLUSTERED, y_title="Sai số trung bình trên tập test (m)", fmt='0.00')
ch.category_axis.reverse_order = True

bullets(s, 8.5, 1.7, 4.4, 5.2, y_chinh("pptx"), size=14)
footer(s, "Nguồn: so_lieu/12_ket_qua_theo_tap_test.csv, BAOCAO/so_lieu/00_cau_hinh_cuoi_cung.json")

# ------------------------------------------------------------ 17. hạn chế
s = prs.slides.add_slide(BLANK)
title(s, "Hạn chế cần nói rõ")
bullets(s, 0.6, 1.5, 12.1, 5.4, [
    "Chỉ so sánh các biến thể HUIM với nhau - không kết luận HUIM tốt hơn cách chọn AP khác",
    "HUI khai phá trên toàn tập train nên dev hơi lạc quan (như nhau cho mọi cấu hình); tập test sạch",
    "Vùng của UJI_LIB / HCXY là 3 cụm k-means - số vùng không được tối ưu",
    "Quy tắc bước 6 cần tập HUI đầy đủ → chỉ làm được ở θ EFIM liệt kê xong",
    "HCXY không ghi đơn vị toạ độ (đọc là mét); DLULIB, HUS không có tài liệu mô tả",
    "Thời gian đo bằng Python thuần trên một máy; chỉ dùng để so sánh trong báo cáo này",
], size=17)

# ------------------------------------------------------------ 18. kết luận
s = prs.slides.add_slide(BLANK)
nen_toi(s)
text(s, 0.7, 0.6, 11.9, 0.9, "Kết luận", size=36, bold=True, color=WHITE, font="Cambria")
bullets(s, 0.7, 1.7, 11.9, 4.5, ket_luan("pptx", ok, len(CHK)), size=17, color=WHITE)
text(s, 0.7, 6.4, 11.9, 0.6, "Chạy lại: python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py  ·  "
     "đọc BAOCAO1/00_HUONG_DAN_DOC.md trước", size=13, color=ICE)

out = BAOCAO / "Slide_HUIM_IPS_4_bo_du_lieu.pptx"
prs.save(str(out))
print("đã lưu", out, len(prs.slides), "slide")
