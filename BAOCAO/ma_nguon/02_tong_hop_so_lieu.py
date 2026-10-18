"""BAOCAO / bước 2 - gom kết quả thí nghiệm (results/huim_opt) thành các bảng trong so_lieu/.

    python BAOCAO/ma_nguon/02_tong_hop_so_lieu.py

Không có số nào gõ tay: mọi bảng được đọc từ file kết quả của các lần chạy thật.
Cấu hình "tốt nhất" được chọn theo sai số trung bình trên 6 fold dev của trainingData
(GroupKFold theo USERID); tập test (validationData) chỉ dùng để báo cáo.
Cột/khóa val_* của kết quả thô được ghi ra so_lieu/ thành test_* (đo trên tập test).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from hinh_chung import RES, ROOT, SO_LIEU

sys.path.insert(0, str(ROOT / "src"))
import huim_opt as H                                   # noqa: E402
import optimize_positioning as op                      # noqa: E402

D = H.data()
VAL = ["dev_mean_m", "val_mean_m", "val_median_m", "val_p90_m",
       "val_building_acc", "val_joint_acc", "val_mean_b0_m", "val_mean_b1_m",
       "val_mean_b2_m"]
TEN = {"config": "cau_hinh", "scope": "pham_vi", "model": "model",
       "theta_pct": "minUtil_pct", "n_ap": "so_AP", "n_ap_b0": "so_AP_toa0",
       "n_ap_b1": "so_AP_toa1", "n_ap_b2": "so_AP_toa2",
       "dev_mean_m": "dev_sai_so_tb_m", "dev_median_m": "dev_trung_vi_m",
       "val_mean_m": "val_sai_so_tb_m", "val_median_m": "val_trung_vi_m",
       "val_p90_m": "val_p90_m", "val_building_acc": "val_dung_toa",
       "val_joint_acc": "val_dung_toa_tang", "val_mean_b0_m": "val_toa0_m",
       "val_mean_b1_m": "val_toa1_m", "val_mean_b2_m": "val_toa2_m",
       "rule": "quy_tac", "par": "tham_so", "seconds": "thoi_gian_danh_gia_s",
       "val_no_ap_seen_pct": "val_mau_khong_thay_AP_nao_pct"}


def sang_test(c):
    return "test_" + c[4:] if isinstance(c, str) and c.startswith("val_") else c


def doi_khoa_test(x):
    if isinstance(x, dict):
        return {sang_test(k): doi_khoa_test(v) for k, v in x.items()}
    if isinstance(x, list):
        return [doi_khoa_test(v) for v in x]
    return x


def ghi(df: pd.DataFrame, ten: str) -> pd.DataFrame:
    df = df.rename(columns=TEN).rename(columns=sang_test)
    df.to_csv(SO_LIEU / ten, index=False, float_format="%.4f")
    print(f"{ten}: {len(df)} dòng")
    return df


def bo_cot(df):
    return df[[c for c in df.columns if not c.startswith(("aps", "union_seconds", "union_peak"))]]


# 01 - kiểm chứng thuật toán tìm union với EFIM -----------------------------
ghi(pd.read_csv(RES / "union_check.csv"), "01_kiem_chung_union_vs_EFIM.csv")

# 02 - số AP trong union theo minUtil, chi phí tìm union ------------------------
home = np.array([np.bincount(D.b[(D.W[:, j] != 100)], minlength=3).argmax()
                 if (D.W[:, j] != 100).any() else -1 for j in range(520)])
rows = []
for m in "ABC":
    G = H.union_table(m, "global")
    P = [H.union_table(m, f"b{b}") for b in range(3)]
    for k, th in enumerate(G["theta_pct"]):
        c = np.flatnonzero(G["member"][:, k])
        rows.append({"pham_vi": "global", "model": m, "minUtil_pct": th,
                     "so_AP": len(c), **{f"so_AP_toa{b}": int((home[c] == b).sum())
                                         for b in range(3)},
                     "thoi_gian_tim_union_s": float(G["level_seconds"][k]),
                     "bo_nho_dinh_MB": float(G["level_peak_mb"][k]),
                     "trang_thai": str(G["level_status"][k]),
                     "so_nut_tim_kiem": int(G["level_nodes"][k])})
        kk = [int(np.argmin(np.abs(p["theta_pct"] - th))) for p in P]
        sets = [np.flatnonzero(p["member"][:, j]) for p, j in zip(P, kk)]
        rows.append({"pham_vi": "per_building", "model": m, "minUtil_pct": th,
                     "so_AP": len(set().union(*map(set, sets))),
                     **{f"so_AP_toa{b}": len(sets[b]) for b in range(3)},
                     "thoi_gian_tim_union_s": float(sum(
                         p["level_seconds"][j] for p, j in zip(P, kk))),
                     "bo_nho_dinh_MB": float(max(p["level_peak_mb"][j] for p, j in zip(P, kk))),
                     "trang_thai": ("COMPLETED" if all(str(p["level_status"][j]) == "COMPLETED"
                                                     for p, j in zip(P, kk)) else "TIMEOUT"),
                     "so_nut_tim_kiem": int(sum(p["level_nodes"][j]
                                               for p, j in zip(P, kk)))})
T2 = pd.DataFrame(rows)
T2.loc[T2.trang_thai != "COMPLETED", ["so_AP", "so_AP_toa0", "so_AP_toa1", "so_AP_toa2"]] = np.nan
ghi(T2, "02_so_AP_theo_minUtil.csv")

# 03 - EFIM liệt kê đầy đủ (PHASE H): số HUI, thời gian, bộ nhớ -----------------
E = pd.concat([H.huim_runs(m).assign(model=m) for m in "ABC"])
E = E[["model", "rel_minutil_pct", "status", "n_huis", "runtime_s",
       "peak_memory_delta_mb", "search_nodes_visited", "unique_waps_in_huis"]]
E.columns = ["model", "minUtil_pct", "trang_thai", "so_HUI", "thoi_gian_s",
             "bo_nho_dinh_MB", "so_nut_tim_kiem", "so_AP_union_EFIM"]
ghi(E, "03_EFIM_so_HUI_thoi_gian_bo_nho.csv")

# 03b - EFIM liệt kê đầy đủ theo từng tòa (giới hạn của các quy tắc bước 6) -------
rows = []
for f in sorted(RES.glob("huistats_b*_*_*pct.json")):
    _, scope, mm, th = f.stem.split("_")
    z = json.loads(f.read_text(encoding="utf-8"))
    rows.append({"model": mm, "toa": int(scope[1]), "minUtil_pct": float(th.replace("pct", "")),
                 "trang_thai": z["status"], "so_HUI": z["n_huis"],
                 "thoi_gian_s": z["runtime_s"], "bo_nho_dinh_MB": z["peak_delta_mb"]})
ghi(pd.DataFrame(rows).sort_values(["model", "toa", "minUtil_pct"], ascending=[True, True, False]),
    "03b_EFIM_theo_toa.csv")

# 04-08 - các bước tối ưu -----------------------------------------------------
ghi(bo_cot(pd.read_csv(RES / "step2_models_ABC.csv")), "04_buoc2_model_ABC.csv")
T3 = ghi(bo_cot(pd.read_csv(RES / "step3_theta_global.csv")),
         "05_buoc3_minUtil_HUIM_chung.csv")
T4 = ghi(bo_cot(pd.read_csv(RES / "step4_per_building.csv")),
         "06_buoc4_HUIM_theo_toa.csv")
T6 = ghi(bo_cot(pd.read_csv(RES / "step6_selection_rules.csv", dtype={"par": str})),
         "07_buoc6_quy_tac_chon_AP.csv")
E7 = pd.read_csv(RES / "step7_ensembles.csv")
ghi(E7, "08_buoc7_ensemble.csv")
ghi(pd.read_csv(RES / "step8_time_memory.csv"), "09_buoc8_thoi_gian_bo_nho.csv")

# 10 - xếp hạng mọi cấu hình theo dev ---------------------------------------
import run_huim_opt as R                               # noqa: E402
A = R.all_rows()
A["loai"] = "don"
E7c = E7.assign(loai="ensemble", scope="ensemble")
ALL = pd.concat([A, E7c], ignore_index=True).sort_values("dev_mean_m")
ALL["hang_theo_dev"] = np.arange(1, len(ALL) + 1)
ghi(bo_cot(ALL[["hang_theo_dev", "loai", "config", "scope", "model",
                "theta_pct", "rule", "par", "n_ap"] + VAL]),
    "10_xep_hang_tat_ca_cau_hinh.csv")

best = ALL.iloc[0]
start = A.set_index("config").loc["G_A__1.9294pct"]

# 11-13 - phân tích cấu hình tốt nhất và cấu hình ban đầu ------------------------
P_best = H.load_preds(best.config)
P_start = H.load_preds("G_A__1.9294pct")
frames, rows, cells = [], [], []
for ten, P in (("ban_dau", P_start), ("tot_nhat", P_best)):
    lab = P["val_label"].astype(str)
    pb = np.array([s.split("_")[0] for s in lab]).astype(int)
    pf = np.array([s.split("_")[1] for s in lab]).astype(int)
    e = P["val_err"]
    f = pd.DataFrame({"cau_hinh": ten, "dong_csv": D.va.index + 2,
                      "toa_that": D.bv, "tang_that": D.va.FLOOR.to_numpy(),
                      "toa_du_doan": pb, "tang_du_doan": pf,
                      "x_that": D.Cv[:, 0], "y_that": D.Cv[:, 1],
                      "x_du_doan": P["val_xy"][:, 0], "y_du_doan": P["val_xy"][:, 1],
                      "sai_so_m": e})
    f["toa_tang_dung"] = (f.toa_that == f.toa_du_doan) & (f.tang_that == f.tang_du_doan)
    frames.append(f)
    for b, g in list(f.groupby("toa_that")) + [("Tong", f)]:
        rows.append({"cau_hinh": ten, "toa": b, "so_mau": len(g),
                     "sai_so_tb_m": g.sai_so_m.mean(),
                     "trung_vi_m": g.sai_so_m.median(),
                     "p90_m": np.percentile(g.sai_so_m, 90),
                     "lon_nhat_m": g.sai_so_m.max(),
                     "toa_dung_pct": 100 * (g.toa_that == g.toa_du_doan).mean(),
                     "toa_tang_dung_pct": 100 * g.toa_tang_dung.mean(),
                     "trong_5m_pct": 100 * (g.sai_so_m <= 5).mean(),
                     "trong_10m_pct": 100 * (g.sai_so_m <= 10).mean()})
    for (b, fl), g in f.groupby(["toa_that", "tang_that"]):
        cells.append({"cau_hinh": ten, "toa": b, "tang": fl, "so_mau": len(g),
                      "sai_so_tb_m": g.sai_so_m.mean(),
                      "toa_tang_dung_pct": 100 * g.toa_tang_dung.mean()})
ghi(pd.DataFrame(rows), "11_sai_so_theo_toa.csv")
ghi(pd.DataFrame(cells), "12_sai_so_theo_toa_tang.csv")
ghi(pd.concat(frames), "13_du_doan_tung_mau_tap_test.csv")


def mo_ta(row) -> dict:
    keep = ["config", "scope", "model", "theta_pct", "rule", "par", "n_ap",
            "n_ap_b0", "n_ap_b1", "n_ap_b2", "members", "how"] + VAL
    return {k: (None if (isinstance(row.get(k), float) and np.isnan(row.get(k)))
                else (row.get(k).item() if hasattr(row.get(k), "item") else row.get(k)))
            for k in keep if k in row}


# θ "cân bằng": ít AP nhất trong các cấu hình có dev <= 105 % dev tốt nhất của phạm vi
CAN_BANG = 1.05
can_bang = {}
for scope, T in (("global", R.all_rows().query("step == 3")),
                 ("per_building", R.all_rows().query("step == 4"))):
    lim = CAN_BANG * T.dev_mean_m.min()
    c = T[T.dev_mean_m <= lim].sort_values(["n_ap", "dev_mean_m"]).iloc[0]
    can_bang[scope] = {**mo_ta(c.to_dict()), "nguong_dev_m": float(lim)}

T8 = pd.read_csv(RES / "step8_time_memory.csv")
(SO_LIEU / "00_cau_hinh_cuoi_cung.json").write_text(json.dumps(doi_khoa_test({
    "tieu_chi_chon": "sai số trung bình (m) trên 6 fold dev leave-users-out của "
                     "trainingData; tập test (validationData) chỉ dùng để báo cáo",
    "tot_nhat": mo_ta(best.to_dict()),
    "ban_dau": mo_ta({**start.to_dict(), "config": "G_A__1.9294pct"}),
    "so_cau_hinh_da_thu": int(len(ALL)),
    "can_bang_quy_tac": "ít AP nhất trong các cấu hình có sai số dev <= 105 % dev tốt nhất của cùng phạm vi",
    "can_bang": can_bang,
    "thoi_gian_bo_nho": T8.to_dict(orient="records"),
}), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("00_cau_hinh_cuoi_cung.json: tốt nhất =", best.config)
