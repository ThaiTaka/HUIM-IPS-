"""Bằng chứng cho slide "Bổ sung: vì sao chọn vậy / con số này từ đâu" của HUIM-IPS V7.

Mọi con số trong các slide bổ sung được TÍNH LẠI ở đây từ dữ liệu gốc và kết quả đã có (không gõ tay):
  results/huim_only/uji/{dev_grid.csv, selection.json, theta_pilot.json, window_pilot.json, version_history.json, cell_runs.csv}
  results/huim_only/uji/research/rerank_grid.csv, rerank3_grid.csv
  results/huim_only/uji/v7/cache/dev_fold*.npz       (khoảng cách ô ứng viên - vị trí thật; chỉ để ĐO)
  results/coordinate_system_verification.json, BAOCAO_V7/so_lieu/exploration_runs.csv, nhật ký huấn luyện
  ujiindoorloc/UJIndoorLoc/trainingData.csv
Ghi: BAOCAO/so_lieu_V7/nguon_goc_hang_so.json

    python src/baocao/export_why_v7.py
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
UJI = ROOT / "results" / "huim_only" / "uji"
GF = 0.766126


def grid_views() -> dict:
    d = pd.read_csv(UJI / "dev_grid.csv")
    sel = json.load(open(UJI / "selection.json", encoding="utf-8"))
    p = sel["params"]
    r = d[d.utility == "rank"]

    def vary(col: str) -> list[dict]:
        q = r.copy()
        for k, v in p.items():
            if k != col:
                q = q[q[k] == v]
        return [{col: (float(a) if col not in ("m", "kf") else int(a)), "dev_mean_m": float(b), "joint_accuracy": float(c)}
                for a, b, c in zip(q[col], q.dev_mean_m, q.dev_joint_accuracy)]

    gt = r[(r.beta == p["beta"]) & (r.m == p["m"]) & (r.p == p["p"]) & (r.sigma == p["sigma"]) & (r.kf == p["kf"])]
    return {
        "n_configurations": int(len(d)), "n_rank": int(len(r)), "selected": p, "selected_dev_mean_m": sel["dev_mean_m"],
        "gamma_tau": [{"gamma": float(a), "tau": float(b), "dev_mean_m": float(c)} for a, b, c in zip(gt.gamma, gt.tau, gt.dev_mean_m)],
        "beta": vary("beta"), "sigma": vary("sigma"), "kf": vary("kf"), "m": vary("m"), "p": vary("p"),
        "utility_best": {u: float(d[d.utility == u].dev_mean_m.min()) for u in ("rank", "abs")},
        "grid_sizes": {c: sorted(float(x) for x in d[c].unique()) for c in ("gamma", "tau", "beta", "sigma", "kf", "m", "p")},
    }


def cells_view() -> dict:
    c = pd.read_csv(UJI / "cell_runs.csv")
    c1 = c.iloc[0]
    return {"n_cells": int(len(c)), "mean_transactions": float(c.n_transactions.mean()), "mean_theta_used_pct": float(c.theta_used_pct.mean()),
            "share_escalated": float((c.n_attempts > 1).mean()), "max_attempts": int(c.n_attempts.max()), "mean_huis": float(c.n_huis.mean()),
            "total_huis": int(c.n_huis.sum()), "max_runtime_s": float(c.runtime_s.max()),
            "cell1": {"n_attempts": int(c1.n_attempts), "theta_used_pct": float(c1.theta_used_pct), "n_transactions": int(c1.n_transactions)}}


def best_of_k() -> list[dict]:
    from v7.rerank import load_dev
    D = load_dev()
    d = np.concatenate([x["dist"] for x in D])
    keep = np.concatenate([x["F"][:, 0, 13] > 0 for x in D])
    dm = d[keep]
    out = []
    for K in (1, 3, 5, 10, 12, 20, 30):
        m = dm[:, :K].min(1)
        out.append({"K": K, "mean_m": float(m.mean()), "under3": float((m < 3).mean()), "under5": float((m < 5).mean())})
    return out


def nn_cells() -> dict:
    c = pd.read_csv(ROOT / "BAOCAO" / "so_lieu_V7" / "mo_hinh_uji_cells.csv")
    nn = []
    for _f, g in c.groupby("building_floor"):
        p = g[["x", "y"]].values * GF
        dd = np.sqrt(((p[:, None] - p[None]) ** 2).sum(-1))
        np.fill_diagonal(dd, 1e9)
        nn += list(dd.min(1))
    nn = np.array(nn)
    return {"n": int(len(nn)), "median": float(np.median(nn)), "mean": float(nn.mean()), "p25": float(np.percentile(nn, 25)),
            "p75": float(np.percentile(nn, 75)), "p90": float(np.percentile(nn, 90))}


def rssi_view() -> dict:
    t = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv")
    W = t.iloc[:, :520].values
    det = W != 100
    mx = np.where(det, W, -999).max(1, keepdims=True)
    gap = (mx - W)[det & (mx > -999)]
    return {"min_detected": int(W[det].min()), "max_detected": int(W[det].max()), "n_readings": int(det.sum()),
            "share_within_db": {str(w): float((gap <= w).mean()) for w in (20, 30, 40, 50)},
            "n_rows": int(len(t)), "n_phones": int(t.PHONEID.nunique()), "n_users": int(t.USERID.nunique()),
            "n_rows_with_ap": int((det.sum(1) > 0).sum())}


def folds_view() -> list[dict]:
    from sklearn.model_selection import GroupKFold
    t = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv", usecols=["PHONEID"])
    return [{"fold": k, "phones": [int(x) for x in sorted(t.PHONEID.iloc[b].unique())], "rows": int(len(b))}
            for k, (_a, b) in enumerate(GroupKFold(6).split(t, groups=t.PHONEID))]


def coord_view() -> dict:
    j = json.load(open(ROOT / "results" / "coordinate_system_verification.json", encoding="utf-8"))
    mb = j["measured_bounds"]
    lat = j["candidates_tested"][0]["lat_deg"]
    return {"lat_deg": lat, "cos_lat": math.cos(math.radians(lat)), "x_extent": mb["X_extent"], "y_extent": mb["Y_extent"],
            "x_extent_m": mb["X_extent"] * GF, "y_extent_m": mb["Y_extent"] * GF,
            "dist_to_campus_m": j["candidates_tested"][0]["distance_to_uji_campus_m"],
            "dist_utm31_km": j["candidates_tested"][1]["distance_to_uji_campus_m"] / 1000}


def epochs_view() -> dict:
    def parse(f: Path) -> list[int]:
        ep: list[int] = []
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.search(r"epochs (\[[^\]]*\])", ln)
            if m:
                ep += ast.literal_eval(m.group(1))
        return ep
    out = {}
    for k, f in (("C2", ROOT / "results" / "logs" / "v7_explore" / "b2_rel_absL3.log"), ("E", ROOT / "results" / "logs" / "v7_dev_E_seeds.log")):
        if f.exists():
            e = parse(f)
            if e:
                out[k] = {"n_members": len(e), "min": min(e), "max": max(e), "median": float(np.median(e)), "n_at_cap": int(sum(x >= 30 for x in e))}
    return out


def main() -> None:
    ex = pd.read_csv(ROOT / "BAOCAO_V7" / "so_lieu" / "exploration_runs.csv")
    row = lambda name: ex[ex.log == name].iloc[0]
    theta = json.load(open(UJI / "theta_pilot.json", encoding="utf-8"))
    hist = json.load(open(UJI / "version_history.json", encoding="utf-8"))
    rg = pd.read_csv(UJI / "research" / "rerank_grid.csv")
    rg3 = pd.read_csv(UJI / "research" / "rerank3_grid.csv")
    gbm = rg[rg.model == "gbm"]
    n_in = {"V7-B": 33 * 4, "V7-C2": 49 * 4}
    params = {k: (v * 32 + 32) + (64 * 16 + 16) + 16 for k, v in n_in.items()}
    E = {
        "grid": grid_views(), "theta_pilot": theta, "window_pilot": json.load(open(UJI / "window_pilot.json", encoding="utf-8")),
        "versions": [{k: v[k] for k in ("version", "dev_folds", "utility", "theta_pct", "config", "dev_mean_m", "test_mean_m")} for v in hist["versions"]],
        "cells": cells_view(), "best_of_k": best_of_k(), "nn_cells": nn_cells(), "rssi": rssi_view(), "folds": folds_view(), "coord": coord_view(),
        "scorer": {"mlp64_32_wd1e-4": float(row("b_c1.log").tb_co_trong_so), "mlp32_16_wd1e-3": float(row("b_c3.log").tb_co_trong_so),
                   "aux_listwise": float(row("b_c2.log").tb_co_trong_so), "devrob": float(row("b_c3_devrob.log").tb_co_trong_so),
                   "ens5_slog_base": float(row("b2_base.log").tb_co_trong_so), "params": params, "inputs": n_in},
        "epochs": epochs_view(),
        "v6_rerank_grid": {"gbm_floor": {f"{int(m)}|{l}": float(v) for m, l, v in zip(gbm.m, gbm.lam, gbm.dev_mean_m)},
                           "gbm_building_k40": {f"{int(m)}|{l}": float(v) for m, l, v in zip(rg3.m, rg3.lam, rg3.dev_mean_m)},
                           "ridge_best": float(rg[rg.model == "ridge"].dev_mean_m.min()), "gbm_best": float(gbm.dev_mean_m.min())},
        "levels3": {"low": [1, 34], "mid": [35, 67], "high": [68, 100]},
    }
    p = ROOT / "BAOCAO" / "so_lieu_V7" / "nguon_goc_hang_so.json"
    json.dump(E, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written", p, p.stat().st_size)


if __name__ == "__main__":
    main()
