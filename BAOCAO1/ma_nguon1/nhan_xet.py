"""Nhận xét và kết luận của BAOCAO1, rút ra từ so_lieu/ lúc dựng (dùng chung cho Word và PowerPoint).

Mỗi câu so sánh được tính từ số liệu: một nhận xét kiểu "tốt hơn" chỉ xuất hiện khi số liệu
cho thấy như vậy. Định dạng gạch đầu dòng: Word nhận (chữ, "b"), PowerPoint nhận (chữ, True).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from hinh_chung import KEYS, SO_LIEU, TAP_TEST, TEN_DS, VUNG, cau_hinh, theta_txt, vn
from nhan import lbl, theta_cua

J = cau_hinh()
B = J["bo_du_lieu"]
UJI = J["uji_tham_chieu_BAOCAO"]
DU = pd.read_csv(SO_LIEU / "01_du_lieu.csv").set_index("bo_du_lieu")
EF = pd.read_csv(SO_LIEU / "04_EFIM_so_HUI_thoi_gian_bo_nho.csv")
G = pd.read_csv(SO_LIEU / "05_buoc3_HUIM_chung.csv")
Z = pd.read_csv(SO_LIEU / "06_buoc4_HUIM_theo_vung.csv")
R6 = pd.read_csv(SO_LIEU / "08_buoc6_quy_tac_chon_AP.csv", dtype={"tham_so": str})
E7 = pd.read_csv(SO_LIEU / "09_buoc7_ensemble.csv")
KQ = pd.read_csv(SO_LIEU / "12_ket_qua_theo_tap_test.csv")
RANK = pd.read_csv(SO_LIEU / "11_xep_hang_tat_ca_cau_hinh.csv", dtype={"tham_so": str})


def m(x, nd=2):
    return vn(x, nd) + " m"


def kq(k, vai, tn):
    return KQ[(KQ.bo_du_lieu == k) & (KQ.vai_tro == vai) & (KQ.tap_test == tn)].iloc[0]


def doi(a, b):
    """Thay đổi tương đối (%), âm = giảm sai số."""
    return 100 * (b - a) / a


def best(T, k):
    t = T[T.bo_du_lieu == k].dropna(subset=["dev_sai_so_tb_m"])
    if not len(t):
        return None
    t = t.assign(_d=(t.minUtil_pct - B[k]["start"]["theta_pct"]).abs())
    return t.sort_values(["dev_sai_so_tb_m", "so_AP", "_d"]).iloc[0]


def efim_dung(k):
    """(θ cao nhất mà EFIM dừng giữa chừng, các model dừng ở θ đó); None nếu EFIM luôn xong."""
    e = EF[(EF.bo_du_lieu == k) & (EF.trang_thai != "COMPLETED")]
    if not len(e):
        return None
    th = float(e.minUtil_pct.max())
    return th, sorted(e[e.minUtil_pct == th].model)


def doi_txt(a, c):
    d = doi(a, c)
    return "không đổi" if abs(d) < 0.05 else f"{'+' if d > 0 else ''}{vn(d, 1)} %"


def _fmt(items, kieu):
    """items: list các list phần [(chữ, đậm?)]."""
    out = []
    for it in items:
        if kieu == "docx":
            out.append([(t, "b") if b else t for t, b in it])
        else:
            out.append([(t, True) if b else t for t, b in it])
    return out


def theo_bo(k) -> list:
    tn = TAP_TEST[k]["test"]
    s, b = kq(k, "ban_dau", tn), kq(k, "tot_nhat", tn)
    n_all = int(DU.loc[k, "so_AP_thay_o_train"])
    nb, ns = int(B[k]["best"]["n_ap"]), int(B[k]["start"]["n_ap"])
    th_b = " / ".join(theta_txt(t) for t in sorted(set(theta_cua(B[k]["best"]["config"]))))
    tt = []
    for _, t in TAP_TEST[k].items():
        a, c = kq(k, "ban_dau", t).sai_so_tb_m, kq(k, "tot_nhat", t).sai_so_tb_m
        tt.append(f"{t} {m(a)} → {m(c)} ({doi_txt(a, c)})")
    it = [(f"{TEN_DS[k]} ({n_all} AP): ", True), ("; ".join(tt), True),
          (f"; {ns} → {nb} AP, θ {theta_txt(B[k]['start']['theta_pct'])} → {th_b}. ", False)]
    if B[k]["best"]["config"] == B[k]["start"]["config"]:
        it.append(("Mọi θ cho cùng 5 AP và không quy tắc / ensemble nào tốt hơn trên dev, nên cấu hình "
                   "tốt nhất chính là cấu hình ban đầu.", False))
    elif nb >= n_all:
        it.append(("Cấu hình tốt nhất giữ đủ mọi AP thấy ở train: bộ dữ liệu có ít AP, bớt AP nào "
                   "cũng làm sai số dev tăng, nên HUIM gần như không cải thiện được.", False))
    else:
        ed = efim_dung(k)
        e = ed[0] if ed else None
        sau = [kq(k, "tot_nhat", t).sai_so_tb_m > kq(k, "ban_dau", t).sai_so_tb_m
               for _, t in TAP_TEST[k].items()]
        it.append((f"Hạ θ để union có thêm AP giảm sai số dev"
                   + (f"; EFIM liệt kê đầy đủ đã bắt đầu dừng ở θ = {theta_txt(e)} (Model "
                      + ", ".join(ed[1]) + "), nên cần thuật toán tìm union chính xác"
                      if e and min(theta_cua(B[k]['best']['config'])) < e else "")
                   + (". Trên tập test có vị trí mới (" + ", ".join(t for (_, t), w in zip(TAP_TEST[k].items(), sau) if w)
                      + ") sai số lại tăng nhẹ: lợi trên dev không chuyển hết sang vị trí chưa đo"
                      if any(sau) else "") + ".", False))
    return it


def vung_items() -> list:
    out = []
    for k in KEYS:
        z, g = best(Z, k), best(G, k)
        if z is None:
            continue
        dd, dt = z.dev_sai_so_tb_m - g.dev_sai_so_tb_m, z.test_sai_so_tb_m - g.test_sai_so_tb_m
        if dd < -0.005:
            s = (f"theo {VUNG[k]} tốt hơn chung {m(-dd, 3)} trên dev, "
                 + (f"{m(-dt, 3)} trên tập test" if dt < 0 else f"nhưng kém {m(dt, 3)} trên tập test"))
        elif dd > 0.005:
            s = f"theo {VUNG[k]} kém chung {m(dd, 3)} trên dev ({m(dt, 3)} trên tập test)"
        else:
            s = f"theo {VUNG[k]} và chung gần như bằng nhau (chênh {m(abs(dd), 3)} trên dev)"
        out.append([(f"{TEN_DS[k]}: ", True), (s + f" (tốt nhất: {lbl(z.cau_hinh, k)} so với "
                                                   f"{lbl(g.cau_hinh, k)}).", False)])
    return out


def quy_tac_items() -> list:
    out = []
    for k in KEYS:
        r = R6[R6.bo_du_lieu == k]
        if not len(r):
            continue
        u = r[r.quy_tac == "union"].iloc[0]
        o = r[r.quy_tac != "union"].sort_values("dev_sai_so_tb_m").iloc[0]
        if o.dev_sai_so_tb_m < u.dev_sai_so_tb_m - 0.005:
            s = (f"quy tắc {o.quy_tac}{'' if pd.isna(o.tham_so) else ' ' + str(o.tham_so)} ({int(o.so_AP)} AP) "
                 f"tốt hơn union trên dev ({m(o.dev_sai_so_tb_m)} so với {m(u.dev_sai_so_tb_m)})")
        else:
            s = f"không quy tắc nào tốt hơn union trên dev ({m(u.dev_sai_so_tb_m)})"
        out.append([(f"{TEN_DS[k]} (Model {u.model}, θ = {theta_txt(u.minUtil_pct)}): ", True), (s + ".", False)])
    return out


def ensemble_items() -> list:
    out = []
    for k in KEYS:
        e = E7[E7.bo_du_lieu == k].sort_values("dev_sai_so_tb_m")
        s = B[k]["best_single"]
        if not len(e):
            out.append([(f"{TEN_DS[k]}: ", True), ("không có ensemble có nghĩa (các cấu hình tốt cho cùng dự đoán).", False)])
            continue
        r = e.iloc[0]
        dd, dt = r.dev_sai_so_tb_m - s["dev_mean_m"], r.test_sai_so_tb_m - s["test_mean_m"]
        out.append([(f"{TEN_DS[k]}: ", True),
                    (f"ensemble tốt nhất so với cấu hình đơn tốt nhất: {'+' if dd >= 0 else '−'}{m(abs(dd), 3)} "
                     f"trên dev, {'+' if dt >= 0 else '−'}{m(abs(dt), 3)} trên tập test"
                     + (" - được chọn" if B[k]["best"]["config"].startswith("E_") else " - không được chọn")
                     + ".", False)])
    return out


def nhan_xet(kieu: str = "docx") -> list:
    items = [theo_bo(k) for k in KEYS]
    items.append([("UJIIndoorLoc (BAOCAO/): ", True),
                  (f"{m(UJI['ban_dau']['test_mean_m'])} → {m(UJI['tot_nhat']['test_mean_m'])}. Ở đó θ ban đầu "
                   "tính trên cả 3 tòa quá cao làm một tòa thiếu AP, nên hạ θ cho lợi rất lớn; ở 4 bộ dữ "
                   "liệu này θ ban đầu đã gần mức tốt hoặc bộ dữ liệu có quá ít AP, nên lợi nhỏ hơn.", False)])
    items.append([("HUIM theo vùng / tầng - ", True), (" ".join(
        "".join(t for t, _ in it) for it in vung_items()), False)])
    items.append([("Quy tắc chọn AP (bước 6) - ", True), (" ".join(
        "".join(t for t, _ in it) for it in quy_tac_items()), False)])
    items.append([("Ensemble (bước 7) - ", True), (" ".join(
        "".join(t for t, _ in it) for it in ensemble_items()), False)])
    return _fmt(items, kieu)


def y_chinh(kieu: str = "pptx") -> list:
    items = []
    for k in KEYS:
        tt = []
        for _, t in TAP_TEST[k].items():
            a, c = kq(k, "ban_dau", t).sai_so_tb_m, kq(k, "tot_nhat", t).sai_so_tb_m
            tt.append(f"{t} {doi_txt(a, c)}")
        items.append([(f"{TEN_DS[k]}: ", True),
                      (", ".join(tt) + f"; {int(B[k]['start']['n_ap'])} → {int(B[k]['best']['n_ap'])} AP",
                       False)])
    items.append([("Ít AP (DLULIB 17, HUS 5): cấu hình tốt nhất giữ đủ mọi AP", False)])
    return _fmt(items, kieu)


def ket_luan(kieu: str = "pptx", ok: int = 0, n: int = 0) -> list:
    U = pd.read_csv(SO_LIEU / "03_so_AP_theo_minUtil.csv")
    tmax = U.groupby(["bo_du_lieu", "pham_vi", "model"]).thoi_gian_tim_union_s.sum().max()
    items = [[("Tìm union chính xác khớp EFIM ở ", False), (f"{ok}/{n}", True),
              (f" mức θ EFIM chạy xong; cả lưới θ tới 0,05 % mất tối đa {vn(tmax / 60, 1)} phút "
               "cho một (bộ dữ liệu, model, phạm vi)", False)]]
    for k in KEYS:
        it = [(f"{TEN_DS[k]}: ", False)]
        for i, (_, tn) in enumerate(TAP_TEST[k].items()):
            s, b = kq(k, "ban_dau", tn), kq(k, "tot_nhat", tn)
            it += [("; " if i else "", False), (f"{m(s.sai_so_tb_m)} → {m(b.sai_so_tb_m)}", True),
                   (f" trên {tn}", False)]
        it.append((f" ({int(B[k]['best']['n_ap'])} AP)", False))
        items.append(it)
    items.append([("Bộ có ít AP: cấu hình HUIM tốt nhất là giữ mọi AP - HUIM không bớt được AP mà không mất "
                   "độ chính xác", False)])
    return _fmt(items, kieu)


def ensemble_txt(kieu: str = "pptx") -> list:
    return _fmt(ensemble_items(), kieu)
