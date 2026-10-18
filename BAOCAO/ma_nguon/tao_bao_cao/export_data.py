"""BAOCAO/so_lieu: every number of the final report, exported from results/.

Writes
  01_ket_qua_tong_hop.csv            test results, every dataset / test set
  02_cau_hinh_chon_tren_dev.csv      configuration selected on the dev folds
  03_lich_su_phien_ban_uji.csv       every version tried on UJIIndoorLoc
  04_tach_sai_so_theo_tang_uji.csv   error split by correct / wrong floor
  05_tham_chieu.csv                  reference systems that use k-NN
  06_mo_ta_du_lieu.csv               dataset description
  07_khai_thac_theo_o.csv            per-dataset mining summary
  du_doan/<dataset>__<test>.csv      one row per test fingerprint
  mo_hinh_uji_cells.csv              UJIIndoorLoc cell positions (worked example)
  kiem_chung_doc_lap.json            results/huim_only/verification.json
  du_lieu_bao_cao.json               everything above, for the .docx / .pptx

Run: python src/baocao/export_data.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
HO = RES / "huim_only"
OUT = ROOT / "BAOCAO" / "so_lieu"
ORDER = ["uji", "uji_lib3", "dlulib", "hcxy", "hus", "hus_dedup"]
TITLE = {"uji": "UJIIndoorLoc", "uji_lib3": "UJI_LIB tầng 3", "dlulib": "DLULIB",
         "hcxy": "HCXY", "hus": "HUS", "hus_dedup": "HUS (khử trùng lặp)"}
PRED_COLS = ["src_file", "src_row", "true_building", "true_floor",
             "pred_building_floor", "true_x", "true_y", "pred_x", "pred_y", "err_m"]


def J(p: Path):
    return json.load(open(p, encoding="utf-8"))


FINAL = {"uji": HO / "uji" / "v6"}      # UJIIndoorLoc: v6 (HUI-evidence re-ranking) is final


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "du_doan").mkdir(exist_ok=True)
    data: dict = {"datasets": {}, "order": ORDER, "title": TITLE}

    res, cfg, desc, mine = [], [], [], []
    for k in ORDER:
        S = J(HO / k / "summary.json")
        D = J(RES / "multi_dataset" / k / "dataset_summary.json")
        sel = S["selection"]
        gf = float(D["ground_factor"])
        runs = pd.read_csv(HO / k / "cell_runs.csv")
        tests = {}
        fin = FINAL.get(k)
        S6 = J(fin / "summary.json") if fin else None
        for t, T in (S6 or S)["tests"].items():
            P = pd.read_csv((fin or HO / k) / "predictions" / f"{t}.csv")
            m = S6["m"] if S6 else sel["params"]["m"]
            cols = PRED_COLS + (["v4_x", "v4_y", "v4_err_m"] if S6 else []) + [
                c for j in range(1, m + 1) for c in (f"cell{j}_index", f"cell{j}_weight")]
            P[cols].to_csv(OUT / "du_doan" / f"{k}__{t}.csv", index=False)
            row = {"dataset": k, "ten": TITLE[k], "tap_test": t, "so_mau": T["n_test"],
                   "sai_so_tb_m": T["mean_err_m"], "trung_vi_m": T["median_err_m"],
                   "p75_m": T["p75_err_m"], "p90_m": T["p90_err_m"], "p95_m": T["p95_err_m"],
                   "dung_toa": T["building_accuracy"], "dung_tang": T["floor_accuracy"],
                   "dung_toa_tang": T["joint_accuracy"], "ty_le_duoi_5m": T["share_within_5m"],
                   "ms_moi_fp": T["ms_per_fp"], "duoi_7m": T["below_target"],
                   "sai_so_chuan_tb_m": round(float(P.err_m.std(ddof=1) / np.sqrt(len(P))), 4),
                   "he_so_met": gf}
            res.append(row)
            tests[t] = row
        cfg.append({"dataset": k, "ten": TITLE[k], "utility": sel.get("utility", "abs"),
                    "theta_pct": sel["theta_pct"], **sel["params"],
                    "dev_tb_m": sel["dev_mean_m"], "dev_dung_tang": sel["dev_joint_accuracy"],
                    "fold_dev": sel["dev_folds"], "so_cau_hinh": sel["n_configurations"]})
        tr = D["train"]
        desc.append({"dataset": k, "ten": TITLE[k], "so_ap": D["n_wap_columns"],
                     "so_toa": D["n_buildings"], "so_lop_toa_tang": D["n_building_floor_classes"],
                     "mau_huan_luyen": tr["rows"], "diem_tham_chieu": tr["positions"],
                     "ap_tb_moi_fp": tr["detections_per_row_mean"],
                     "tap_test": "; ".join(f"{n} ({v['rows']})" for n, v in D["tests"].items()),
                     "he_so_met": D["ground_factor"]})
        mine.append({"dataset": k, "ten": TITLE[k], "so_o": S["model"]["n_cells"],
                     "so_hui": S["model"]["n_huis"],
                     "thoi_gian_khai_thac_s": S["model"]["mining_seconds"],
                     "o_phai_nang_theta": S["model"]["cells_escalated"],
                     "theta_trung_vi_dung": S["model"]["theta_used_median_pct"],
                     "ap_trong_hui": S["model"]["aps_in_some_hui"],
                     "tong_ap": S["model"]["n_aps"],
                     "giao_dich_tb_moi_o": round(float(runs.n_transactions.mean()), 2)})
        data["datasets"][k] = {"tests": tests, "selection": sel, "model": S["model"],
                               "description": desc[-1], "mining": mine[-1]}
        if S6:
            n_huis = lambda f: int(len(np.load(f)["util"]))
            data["datasets"][k]["v4_tests"] = S["tests"]
            data["datasets"][k]["v6"] = {
                "dev_mean_m": S6["dev"]["dev_mean_v5_m"], "dev_median_m": S6["dev"]["dev_median_v5_m"],
                "dev_mean_v4_m": S6["dev"]["dev_mean_v4_m"], "k_candidates": S6["k_candidates"],
                "m": S6["m"], "lam": S6["lam"], "regressor": S6["regressor"],
                "n_features": len(S6["features"]) + 8, "n_huis_L3": n_huis(HO / k / "v5" / "model_L3.npz"),
                "n_huis_abs": n_huis(HO / k / "v5" / "model_abs.npz"),
                "v5": J(HO / k / "v5" / "summary.json")["tests"],
                "v5_dev_mean_m": J(HO / k / "v5" / "summary.json")["dev"]["dev_mean_v5_m"],
                "research": J(HO / k / "research" / "summary.json"),
                "verification": J(fin / "verification.json")}

    pd.DataFrame(res).to_csv(OUT / "01_ket_qua_tong_hop.csv", index=False)
    pd.DataFrame(cfg).to_csv(OUT / "02_cau_hinh_chon_tren_dev.csv", index=False)
    pd.DataFrame(desc).to_csv(OUT / "06_mo_ta_du_lieu.csv", index=False)
    pd.DataFrame(mine).to_csv(OUT / "07_khai_thac_theo_o.csv", index=False)

    V = J(HO / "uji" / "version_history.json")
    pd.DataFrame([{k: v[k] for k in ("version", "change_vi", "dev_folds", "utility",
                                      "theta_pct", "config", "dev_mean_m", "test_mean_m",
                                      "test_median_m", "test_floor_accuracy")}
                  for v in V["versions"]]).to_csv(OUT / "03_lich_su_phien_ban_uji.csv", index=False)
    data["versions"] = V["versions"]
    data["pilots"] = {f: J(HO / "uji" / f) for f in ("theta_pilot.json", "window_pilot.json")}

    P = pd.read_csv(FINAL["uji"] / "predictions" / "validationData.csv")
    ok = (P.true_building.astype(str) + "_" + P.true_floor.astype(str)) == P.pred_building_floor
    split = [{"nhom": "Đoán đúng tòa và tầng", "so_mau": int(ok.sum()),
              "sai_so_tb_m": round(float(P.err_m[ok].mean()), 4),
              "phan_tong_sai_so": round(float(P.err_m[ok].sum() / P.err_m.sum()), 4)},
             {"nhom": "Đoán sai tầng", "so_mau": int((~ok).sum()),
              "sai_so_tb_m": round(float(P.err_m[~ok].mean()), 4),
              "phan_tong_sai_so": round(float(P.err_m[~ok].sum() / P.err_m.sum()), 4)}]
    pd.DataFrame(split).to_csv(OUT / "04_tach_sai_so_theo_tang_uji.csv", index=False)
    data["uji_floor_split"] = split
    data["uji_by_building"] = [
        {"toa": int(b), "so_mau": int((P.true_building == b).sum()),
         "sai_so_tb_m": round(float(P.err_m[P.true_building == b].mean()), 4),
         "dung_tang": round(float(ok[P.true_building == b].mean()), 4)}
        for b in sorted(P.true_building.unique())]

    C = pd.read_csv(RES / "multi_dataset" / "comparison.csv")
    C = C[C.wap_set == "all"]
    refs = []
    for k in ORDER:
        for t in data["datasets"][k]["tests"]:
            r0 = C[(C.dataset == k) & (C.test_set == t) & C.method.str.startswith("k-NN")]
            r4 = C[(C.dataset == k) & (C.test_set == t) & C.method.str.startswith("Tối ưu PHASE I3")]
            z = J(RES / "huim_zone" / k / "selected.json")["tests"].get(t)
            refs.append({"dataset": k, "ten": TITLE[k], "tap_test": t,
                         "chi_huim_m": data["datasets"][k]["tests"][t]["sai_so_tb_m"],
                         "knn_goc_m": float(r0.mean_err_m.iloc[0]) if len(r0) else None,
                         "knn_toi_uu_m": float(r4.mean_err_m.iloc[0]) if len(r4) else None,
                         "huim_chon_ap_knn_m": z["huim_zone"]["mean_err_m"] if z else None,
                         "huim_chon_ap_so_ap": z["huim_zone"]["n_waps"] if z else None,
                         "huim_toan_cuc_knn_m": (z["global_huim_best"] or {}).get("mean_err_m") if z else None,
                         "huim_toan_cuc_so_ap": (z["global_huim_best"] or {}).get("n_waps") if z else None,
                         "tong_ap": z["all_aps"]["n_waps"] if z else None})
    pd.DataFrame(refs).to_csv(OUT / "05_tham_chieu.csv", index=False)
    data["references"] = refs

    cells = pd.read_csv(HO / "uji" / "model" / "cells.csv")
    cells.to_csv(OUT / "mo_hinh_uji_cells.csv", index=False)
    shutil.copy(HO / "verification.json", OUT / "kiem_chung_doc_lap.json")
    shutil.copy(FINAL["uji"] / "verification.json", OUT / "kiem_chung_v6_uji.json")
    v6v = J(FINAL["uji"] / "verification.json")
    data["verification"] = {"n_checks": J(HO / "verification.json")["n_checks"] + v6v["n_checks"],
                            "n_failed": J(HO / "verification.json")["n_failed"] + v6v["n_failed"],
                            "n_checks_v4": J(HO / "verification.json")["n_checks"], "n_checks_v6": v6v["n_checks"],
                            "per_dataset": [{"dataset": r["dataset"], "n_checks": r["n_checks"],
                                             "n_failed": r["n_failed"]}
                                            for r in J(HO / "verification.json")["datasets"]]}
    ex = P.iloc[(P.err_m - P.err_m.median()).abs().idxmin()]
    m = data["datasets"]["uji"]["v6"]["m"]
    data["worked_example"] = {
        "src_row": int(ex.src_row), "true_x": float(ex.true_x), "true_y": float(ex.true_y),
        "pred_x": float(ex.pred_x), "pred_y": float(ex.pred_y), "err_m": float(ex.err_m),
        "v4_x": float(ex.v4_x), "v4_y": float(ex.v4_y), "v4_err_m": float(ex.v4_err_m),
        "pred_building_floor": str(ex.pred_building_floor),
        "cells": [{"index": int(ex[f"cell{j}_index"]), "weight": float(ex[f"cell{j}_weight"]),
                   "x": float(cells.loc[int(ex[f"cell{j}_index"]), "x"]),
                   "y": float(cells.loc[int(ex[f"cell{j}_index"]), "y"])}
                  for j in range(1, m + 1)]}
    json.dump(data, open(OUT / "du_lieu_bao_cao.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("so_lieu written:", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
