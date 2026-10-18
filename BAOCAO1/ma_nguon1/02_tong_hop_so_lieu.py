"""BAOCAO1 / bước 2 - gom kết quả thí nghiệm (results/huim_multi) thành các bảng trong so_lieu/.

    python BAOCAO1/ma_nguon/02_tong_hop_so_lieu.py

Không có số nào gõ tay: mọi bảng được đọc từ file kết quả của các lần chạy thật.
Cấu hình "tốt nhất" của mỗi bộ dữ liệu được chọn theo sai số trung bình trên 6 fold dev
tách từ tập train; tập test (các file test của bộ dữ liệu) chỉ dùng để báo cáo.
Cột test_* = tập test thứ nhất, test2_* = tập test thứ hai (tên file: cột tap_test /
tap_test2 và khóa "tap_test" trong 00_cau_hinh_cuoi_cung.json).
"""
from __future__ import annotations

import json
import re
import sys

import numpy as np
import pandas as pd

from hinh_chung import KEYS, RES, ROOT, SO_LIEU, TAP_TEST, TEN_DS

sys.path.insert(0, str(ROOT / "src"))
import huim_multi as HM                                # noqa: E402

MD = ROOT / "results" / "multi_dataset"

HAU_TO = [("_mean_m", "_sai_so_tb_m"), ("_median_m", "_trung_vi_m"),
          ("_max_m", "_lon_nhat_m"), ("_floor_acc", "_dung_tang"),
          ("_zone_acc", "_dung_vung"), ("_no_ap_seen_pct", "_mau_khong_thay_AP_nao_pct")]
TEN = {"config": "cau_hinh", "scope": "pham_vi", "theta_pct": "minUtil_pct",
       "n_ap": "so_AP", "positioner_label": "bo_dinh_vi", "status": "trang_thai",
       "rule": "quy_tac", "par": "tham_so", "seconds": "thoi_gian_danh_gia_s",
       "same_as": "giong_ket_qua_cua", "theta_best_on_dev": "minUtil_tot_nhat_dev",
       "from_config": "tu_cau_hinh", "efim_n_huis": "so_HUI_EFIM",
       "efim_seconds": "thoi_gian_EFIM_s", "members": "thanh_vien", "how": "cach_gop"}


def doi_ten(c: str) -> str:
    if c in TEN:
        return TEN[c]
    m = re.fullmatch(r"n_ap_z(\d)", c)
    if m:
        return f"so_AP_vung{m.group(1)}"
    m = re.fullmatch(r"aps_z(\d)", c)
    if m:
        return f"AP_vung{m.group(1)}"
    if c == "aps":
        return "AP"
    for a, b in HAU_TO:
        if c.endswith(a) and c.startswith(("dev", "test")):
            return c[: -len(a)] + b
    return c


def ghi(df: pd.DataFrame, ten: str) -> pd.DataFrame:
    df = df.drop(columns=[c for c in df.columns if c in ("positioner", "_r", "fam",
                                                         "same_key")], errors="ignore")
    df = df.rename(columns=doi_ten)
    df.to_csv(SO_LIEU / ten, index=False, float_format="%.4f")
    print(f"{ten}: {len(df)} dòng")
    return df


def doc(key: str, f: str) -> pd.DataFrame:
    p = RES / key / f
    if not p.exists() or p.stat().st_size < 5:
        return pd.DataFrame()
    return pd.read_csv(p, dtype={"par": str})


def gan_ds(df: pd.DataFrame, key: str) -> pd.DataFrame:
    df = df.copy()
    df.insert(0, "bo_du_lieu", key)
    df.insert(1, "tap_test", TAP_TEST[key]["test"])
    df.insert(2, "tap_test2", TAP_TEST[key].get("test2", ""))
    return df


def gop(f: str) -> pd.DataFrame:
    parts = [gan_ds(doc(k, f), k) for k in KEYS if len(doc(k, f))]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


# 01 - mô tả dữ liệu -------------------------------------------------------------
rows = []
for k in KEYS:
    d = json.loads((MD / k / "dataset_summary.json").read_text(encoding="utf-8"))
    D = HM.data(k)
    r = {"bo_du_lieu": k, "ten": TEN_DS[k], "so_cot_AP": d["n_wap_columns"],
         "so_AP_thay_o_train": d["train"]["aps_ever_detected"],
         "so_dong_train": d["train"]["rows"], "so_vi_tri_train": d["train"]["positions"],
         "so_AP_thay_moi_dong_TB": d["train"]["detections_per_row_mean"],
         "so_tang": d["n_building_floor_classes"], "nhan_vi_tri_model_BC": d["location_label"],
         "nhom_fold_dev": d["cv_group"], "so_fold_dev": len(D.folds),
         "he_so_ra_met": d["ground_factor"], "toa_do": d["coordinates"],
         "vung_HUIM": (f"{D.n_zones} {D.zone_kind}" if D.n_zones else "không"),
         "bo_dinh_vi_goc": D.cfg.label()}
    for i, (tn, t) in enumerate(d["tests"].items(), 1):
        s = "" if i == 1 else str(i)
        r[f"tap_test{s}"] = tn
        r[f"tap_test{s}_so_dong"] = t["rows"]
        r[f"tap_test{s}_so_vi_tri"] = t["positions"]
        r[f"tap_test{s}_vi_tri_co_trong_train"] = t["positions_also_in_training"]
    r["lam_sach"] = " | ".join(d.get("cleaning", []))
    rows.append(r)
ghi(pd.DataFrame(rows), "01_du_lieu.csv")

# 02 - kiểm chứng tìm union với EFIM ------------------------------------------------
ghi(pd.read_csv(RES / "union_check.csv"), "02_kiem_chung_union_vs_EFIM.csv")

# 03 - số AP trong union theo minUtil, chi phí tìm kiếm -------------------------------
rows = []
for k in KEYS:
    D = HM.data(k)
    for scope in D.scopes():
        for m in HM.MODELS:
            T = HM.union_table(k, m, scope, compute=False)
            for j, th in enumerate(T["theta_pct"]):
                st = str(T["level_status"][j])
                rows.append({"bo_du_lieu": k, "pham_vi": scope, "model": m,
                             "minUtil_pct": float(th), "trang_thai": st,
                             "so_AP": int(T["member"][:, j].sum()) if st == "COMPLETED" else np.nan,
                             "so_AP_co_trong_pham_vi": int(T["n_items_present"]),
                             "da_du_moi_AP": bool(T["saturated"][j]),
                             "thoi_gian_tim_union_s": float(T["level_seconds"][j]),
                             "bo_nho_dinh_MB": float(T["level_peak_mb"][j]),
                             "so_nut_tim_kiem": int(T["level_nodes"][j]),
                             "tong_utility": float(T["total_utility"]),
                             "so_giao_dich": int(T["n_transactions"])})
ghi(pd.DataFrame(rows), "03_so_AP_theo_minUtil.csv")

# 04 - EFIM liệt kê đầy đủ (lần chạy đa dữ liệu trước) ----------------------------------
rows = []
for k in KEYS:
    for m in HM.MODELS:
        E = HM.efim_runs(k, m)
        for r in E.itertuples():
            rows.append({"bo_du_lieu": k, "model": m, "minUtil_pct": float(r.rel_minutil_pct),
                         "trang_thai": r.status, "so_HUI": int(r.n_huis),
                         "thoi_gian_s": float(r.runtime_s),
                         "bo_nho_dinh_MB": float(r.peak_memory_delta_mb),
                         "so_AP_union_EFIM": int(r.unique_waps_in_huis)})
ghi(pd.DataFrame(rows).sort_values(["bo_du_lieu", "model", "minUtil_pct"],
                                   ascending=[True, True, False]),
    "04_EFIM_so_HUI_thoi_gian_bo_nho.csv")

# 05-09 - các bước tối ưu -------------------------------------------------------------
ghi(gop("step3_G_global.csv"), "05_buoc3_HUIM_chung.csv")
ghi(gop("step4_Z_zones.csv"), "06_buoc4_HUIM_theo_vung.csv")
ghi(pd.concat([gop("step5_T_global.csv"), gop("step4_TZ_zones.csv")], ignore_index=True),
    "07_buoc5_bo_dinh_vi_chon_lai.csv")
rows = []
for k in KEYS:
    p = RES / k / "step5_positioner.json"
    if not p.exists():
        continue
    j = json.loads(p.read_text(encoding="utf-8"))
    for s in j["stages"]:
        rows.append({"bo_du_lieu": k, "chon_tren_cau_hinh": j["selected_on"],
                     "so_AP": j["n_ap"], "giai_doan": s["stage"], "noi_dung": s["what"],
                     "bo_dinh_vi": s["label"], "dev_sai_so_tb_m": s["dev"]["mean_ground_m"],
                     "dev_trung_vi_m": s["dev"]["median_ground_m"],
                     "bo_dinh_vi_goc": j["base_positioner"],
                     "giong_bo_dinh_vi_goc": j["same_as_base"],
                     "thoi_gian_chon_s": j["seconds"]})
ghi(pd.DataFrame(rows), "07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv")
ghi(gop("step6_rules.csv"), "08_buoc6_quy_tac_chon_AP.csv")
ghi(gop("step7_ensembles.csv"), "09_buoc7_ensemble.csv")
ghi(gop("step8_time_memory.csv"), "10_buoc8_thoi_gian_bo_nho.csv")

# 11 - xếp hạng mọi cấu hình theo dev -------------------------------------------------
parts = []
for k in KEYS:
    A = HM.single_rows(k)
    A["loai"] = "don"
    E = doc(k, "step7_ensembles.csv")
    if len(E):
        E = E.assign(loai="ensemble", scope="ensemble")
    X = pd.concat([A, E], ignore_index=True)
    X["_r"] = X.dev_mean_m.round(6)
    X = X.sort_values(["_r", "n_ap"]).reset_index(drop=True)
    X["hang_theo_dev"] = np.arange(1, len(X) + 1)
    keep = ["hang_theo_dev", "loai", "config", "scope", "model", "theta_pct", "rule",
            "par", "n_ap", "positioner_label"] + [c for c in X.columns if c.startswith(
                ("dev_", "test")) and not c.endswith("no_ap_seen_pct")]
    parts.append(gan_ds(X[[c for c in keep if c in X.columns]], k))
ghi(pd.concat(parts, ignore_index=True), "11_xep_hang_tat_ca_cau_hinh.csv")

# 12-13 - kết quả cuối cùng theo tập test, dự đoán từng mẫu ---------------------------
TONG, rows, frames = {}, [], []
for k in KEYS:
    S = HM.summary(k)
    D = HM.data(k)
    tm = doc(k, "step8_time_memory.csv")
    pj = json.loads((RES / k / "step5_positioner.json").read_text(encoding="utf-8"))
    TONG[k] = {"ten": TEN_DS[k], "tap_test": S["tests"], **S,
               "buoc5_bo_dinh_vi": {x: pj[x] for x in ("selected_on", "base_positioner",
                                                        "new_positioner", "same_as_base")},
               "thoi_gian_bo_nho": tm.to_dict(orient="records")}
    for vai, cfg in (("ban_dau", S["start"]["config"]), ("don_tot_nhat", S["best_single"]["config"]),
                     ("tot_nhat", S["best"]["config"])):
        P = HM.load_preds(k, cfg)
        for name, T in D.tests.items():
            p = D.prefix[name]
            e = P[f"{p}_err"]
            r = {"bo_du_lieu": k, "vai_tro": vai, "cau_hinh": cfg, "tap_test": name,
                 "so_mau": len(e), "sai_so_tb_m": e.mean(), "trung_vi_m": np.median(e),
                 "p75_m": np.percentile(e, 75), "p90_m": np.percentile(e, 90),
                 "lon_nhat_m": e.max(), "trong_1m_pct": 100 * (e <= 1).mean(),
                 "trong_2m_pct": 100 * (e <= 2).mean(), "trong_5m_pct": 100 * (e <= 5).mean()}
            if D.multi_floor:
                r["dung_tang_pct"] = 100 * (P[f"{p}_label"].astype(str) == T["y"]).mean()
            rows.append(r)
            if vai != "don_tot_nhat":
                df = T["df"]
                frames.append(pd.DataFrame({
                    "bo_du_lieu": k, "vai_tro": vai, "cau_hinh": cfg, "tap_test": name,
                    "file_goc": df["SRC_FILE"].to_numpy(), "dong_goc": df["SRC_ROW"].to_numpy(),
                    "tang_that": df["FLOOR"].to_numpy(),
                    "x_that": T["C"][:, 0], "y_that": T["C"][:, 1],
                    "x_du_doan": P[f"{p}_xy"][:, 0], "y_du_doan": P[f"{p}_xy"][:, 1],
                    "nhan_du_doan": P[f"{p}_label"].astype(str), "sai_so_m": e}))
ghi(pd.DataFrame(rows), "12_ket_qua_theo_tap_test.csv")
ghi(pd.concat(frames, ignore_index=True), "13_du_doan_tung_mau_tap_test.csv")

# tham chiếu: UJIIndoorLoc (đã làm ở BAOCAO/)
uji = json.loads((ROOT / "BAOCAO" / "so_lieu" / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))
(SO_LIEU / "00_cau_hinh_cuoi_cung.json").write_text(json.dumps({
    "tieu_chi_chon": "sai số trung bình (m) trên 6 fold dev tách từ tập train của từng bộ dữ "
                     "liệu; tập test (các file test của bộ dữ liệu) chỉ dùng để báo cáo",
    "can_bang_quy_tac": "ít AP nhất trong các cấu hình có sai số dev <= 105 % dev tốt nhất "
                        "của cùng phạm vi",
    "bo_du_lieu": TONG,
    "uji_tham_chieu_BAOCAO": {"tot_nhat": uji["tot_nhat"], "ban_dau": uji["ban_dau"]},
}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("00_cau_hinh_cuoi_cung.json:", {k: v["best"]["config"] for k, v in TONG.items()})
