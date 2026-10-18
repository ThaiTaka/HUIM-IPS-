"""PHASE R (v5) - HUI evidence re-ranking for UJIIndoorLoc, end to end.

v4 places a query at the weighted centroid of the 12 best cells of the chosen
floor, ranked by one HUI score. v5 keeps v4's HUI models and floor decision but
re-ranks the 30 best cells of that floor with a regressor that combines several
pieces of HUI evidence per cell (pattern scores, coverages, a level-item HUI
model, the cell's strength profile derived from its HUIs, spatial agreement
between candidates), each also relative to the query's other candidates. No
fingerprint is stored or compared; every feature is computed from the mined
HUIs. The regressor is trained on the 6 dev folds only (features from fold
models, i.e. out-of-fold), and m, lam were chosen on dev
(src/huim_rerank.py, results/huim_only/uji/research/).

    dev     features of every dev fold                -> research/v5_dev_fold<k>.npz
    final   L3 model on the full training data, features of the test set,
            regressor fit on all dev rows, test scored ONCE
                                                      -> results/huim_only/uji/v5/

Run: python src/huim_rerank_final.py --stage dev --fold k ; --stage final
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_positioning import HUIPositioner
from huim_research import (KIND, RES, THETA, cell_matrix, components_multi, expand_levels,
                           fold_path, hui_keys, load_model, local_df, profile_feats,
                           save_model, strength_profile, tag)
from multi_datasets import load
from run_huim_only import OUT_ROOT, metrics, q_matrix, inputs

KEY = "uji"
K_CAND = 30
M_TOP, LAM = 20, 2.0           # chosen on dev (out-of-fold grid in huim_rerank.py)
OUT = OUT_ROOT / KEY / "v5"
BASE_FEATS = ["S", "logS", "S_rel", "rank", "P21", "P11", "V", "R", "Pidf", "raw_rel",
              "d_est", "d_top1", "dens5", "n_ap", "PL3", "VL3", "SL3_rel", "rankL3",
              "prof_mae", "prof_corr", "prof_cos", "top_ap_mass", "shared_n",
              "prof_maeL3", "prof_cosL3"]


def compute(pos: HUIPositioner, posL: HUIPositioner, q: np.ndarray, gf: float) -> dict:
    """HUI-evidence features of the K_CAND best cells of the chosen floor."""
    kid = hui_keys(pos)
    Cws = {"base": pos.Cw, "idf": cell_matrix(pos, pos.hui_util / local_df(pos, kid, 10.0) ** 2)}
    P, V, R = components_multi(pos, q, [(2.0, 20.0), (1.0, 20.0)], Cws)
    P21, P11, Pidf = P[("base", (2.0, 20.0))], P[("base", (1.0, 20.0))], P[("idf", (2.0, 20.0))]
    raw = P21 * V ** 3
    S = raw @ pos._kernel(3.0)
    floor = pos.floor_of(S, 20)
    est, *_ = pos.locate(S, floor, 12, 8.0)              # v4's estimate
    Sf = np.where(pos.cell_bf[None, :] == floor[:, None], S, -1.0)
    top = np.argsort(-Sf, 1)[:, :K_CAND]
    qL = expand_levels(q, 3)
    PL, VL, _ = components_multi(posL, qL, [(1.0, 20.0)], {"base": posL.Cw})
    PL = PL[("base", (1.0, 20.0))]
    SL = (PL * VL ** 3) @ posL._kernel(3.0)
    SLf = np.where(pos.cell_bf[None, :] == floor[:, None], SL, -1.0)
    rankL = np.argsort(np.argsort(-SLf, 1), 1)
    n, Kc = len(q), top.shape[1]
    tk = lambda A: np.take_along_axis(A, top, 1)
    cxy = pos.cell_xy[top]
    Stop = tk(S)
    d_est = np.sqrt(((cxy - est[:, None]) ** 2).sum(-1)) * gf
    d_top1 = np.sqrt(((cxy - cxy[:, :1]) ** 2).sum(-1)) * gf
    dd = np.sqrt(((cxy[:, :, None] - cxy[:, None]) ** 2).sum(-1)) * gf
    F = [Stop, np.log(Stop + 1e-9), Stop / np.maximum(Stop[:, :1], 1e-12), np.tile(np.arange(Kc), (n, 1)),
         tk(P21), tk(P11), tk(V), tk(R), tk(Pidf),
         tk(raw) / np.maximum(tk(raw).max(1, keepdims=True), 1e-12),
         d_est, d_top1, (dd <= 5.0).sum(-1), np.tile((q > 0).sum(1)[:, None], (1, Kc)),
         tk(PL), tk(VL), tk(SL) / np.maximum(tk(SL).max(1, keepdims=True), 1e-12), tk(rankL)]
    mass, qhat = strength_profile(pos)
    massL, qhatL = strength_profile(posL)
    ext = []
    for s in range(0, n, 256):
        mae, corr, cos, tm, shn = profile_feats(q[s:s + 256], mass, qhat, top[s:s + 256])
        maeL, _c, cosL, _t, _n = profile_feats(qL[s:s + 256], massL, qhatL, top[s:s + 256])
        ext.append(np.stack([mae, corr, cos, tm, shn, maeL, cosL], -1))
    F = np.concatenate([np.stack(F, -1), np.concatenate(ext)], -1).astype(np.float32)
    return {"F": F, "cand": top, "cxy": cxy, "est": est, "floor": floor}


def relative(X: np.ndarray) -> np.ndarray:
    """Each feature, plus the same relative to the query's other candidates:
    minus the best value, min-max scaled within the query, and its rank."""
    mx, mn = X.max(1, keepdims=True), X.min(1, keepdims=True)
    rk = np.argsort(np.argsort(-X, 1), 1).astype(np.float32)
    return np.concatenate([X, X - mx, (X - mn) / np.maximum(mx - mn, 1e-9), rk], -1)


def regressor() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                         min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def place(pred: np.ndarray, cxy: np.ndarray, m: int = M_TOP, lam: float = LAM):
    """Weighted centroid of the m candidates predicted closest,
    weights exp(-(d_pred - min d_pred) / lam)."""
    o = np.argsort(pred, 1)[:, :m]
    d = np.take_along_axis(pred, o, 1)
    w = np.exp(-(d - d[:, :1]) / lam)
    w /= w.sum(1, keepdims=True)
    return np.einsum("ij,ijk->ik", w, np.take_along_axis(cxy, o[..., None], 1)), o, w


def stage_dev(k: int) -> None:
    b = load(KEY)
    _p, Q, _c, XY, _BF = inputs(b, KIND)
    pos, ex = load_model(fold_path(k), b.ground_factor)
    posL, _ = load_model(fold_path(k, tag(3)), b.ground_factor)
    assert np.array_equal(pos.cells, posL.cells)
    dvi = ex["dvi"]
    f = compute(pos, posL, Q[dvi], b.ground_factor)
    dist = np.sqrt(((f["cxy"] - XY[dvi][:, None]) ** 2).sum(-1)) * b.ground_factor
    np.savez_compressed(RES / f"v5_dev_fold{k}.npz", F=f["F"], cxy=f["cxy"], dist=dist,
                        true=XY[dvi], est=f["est"], dvi=dvi)
    print(f"dev fold {k}: features {f['F'].shape}", flush=True)


def dev_check() -> dict:
    """Out-of-fold dev error of v5 (leave-one-fold-out), to confirm the
    refactored features reproduce the research numbers."""
    D = [dict(np.load(RES / f"v5_dev_fold{k}.npz")) for k in range(6)]
    gf = load(KEY).ground_factor
    e, e4 = [], []
    for k in range(6):
        tr = [D[j] for j in range(6) if j != k]
        X = np.concatenate([relative(d["F"]).reshape(-1, relative(d["F"]).shape[-1]) for d in tr])
        y = np.concatenate([np.log1p(d["dist"]).ravel() for d in tr])
        G = relative(D[k]["F"])
        p = np.expm1(regressor().fit(X, y).predict(G.reshape(-1, G.shape[-1]))).reshape(D[k]["dist"].shape)
        xy, *_ = place(p, D[k]["cxy"])
        e.append(np.sqrt(((xy - D[k]["true"]) ** 2).sum(1)) * gf)
        e4.append(np.sqrt(((D[k]["est"] - D[k]["true"]) ** 2).sum(1)) * gf)
    e, e4 = np.concatenate(e), np.concatenate(e4)
    r = {"dev_mean_v5_m": round(float(e.mean()), 4), "dev_median_v5_m": round(float(np.median(e)), 4),
         "dev_mean_v4_m": round(float(e4.mean()), 4), "dev_queries": int(len(e))}
    print(r, flush=True)
    return r


def load_final_base(gf: float) -> HUIPositioner:
    d = OUT_ROOT / KEY / "model"
    z = np.load(d / "huis.npz")
    c = pd.read_csv(d / "cells.csv")
    pos = HUIPositioner(THETA, ground_factor=gf)
    ip, it = z["indptr"], z["items"]
    pos.hui_items = [it[ip[i]:ip[i + 1]] for i in range(len(ip) - 1)]
    pos.hui_util, pos.hui_supp, pos.hui_cell = z["utility"], z["support"], z["cell_index"]
    pos.cells = c.cell.to_numpy()
    pos.cell_xy = c[["x", "y"]].to_numpy(np.float64)
    pos.cell_bf = c.building_floor.astype(str).to_numpy()
    pos.n_aps = 520
    pos._index()
    return pos


def stage_final() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "predictions").mkdir(exist_ok=True)
    b = load(KEY)
    gf = b.ground_factor
    prep, Q, cell, XY, BF = inputs(b, KIND)
    pos = load_final_base(gf)
    fL = OUT / "model_L3.npz"
    if not fL.exists():
        t0 = time.perf_counter()
        posL = HUIPositioner(THETA, ground_factor=gf).fit(expand_levels(Q, 3), cell, XY, BF)
        save_model(posL, fL)
        print(f"final L3 model: {len(posL.hui_items)} HUIs, {time.perf_counter() - t0:.0f}s", flush=True)
    posL, _ = load_model(fL, gf)
    assert np.array_equal(np.asarray(pos.cells).astype(str), np.asarray(posL.cells).astype(str))
    posL.cell_bf = pos.cell_bf
    dev = dev_check()
    D = [dict(np.load(RES / f"v5_dev_fold{k}.npz")) for k in range(6)]
    X = np.concatenate([relative(d["F"]).reshape(-1, relative(d["F"]).shape[-1]) for d in D])
    y = np.concatenate([np.log1p(d["dist"]).ravel() for d in D])
    reg = regressor().fit(X, y)
    tests = {}
    for tname, te in b.tests.items():
        q = q_matrix(prep, te, KIND)
        t0 = time.perf_counter()
        f = compute(pos, posL, q, gf)
        G = relative(f["F"])
        p = np.expm1(reg.predict(G.reshape(-1, G.shape[-1]))).reshape(G.shape[:2])
        xy, o, w = place(p, f["cxy"])
        ms = (time.perf_counter() - t0) / len(q) * 1000.0
        m = metrics(te, f["floor"].astype(str), xy, gf)
        cand = np.take_along_axis(f["cand"], o, 1)
        P = pd.DataFrame({"src_file": te["SRC_FILE"].to_numpy(), "src_row": te["SRC_ROW"].to_numpy(),
                          "true_building": te["BUILDINGID"].to_numpy(), "true_floor": te["FLOOR"].to_numpy(),
                          "pred_building_floor": f["floor"].astype(str),
                          "true_x": te["X"].to_numpy(), "true_y": te["Y"].to_numpy(),
                          "pred_x": xy[:, 0], "pred_y": xy[:, 1]})
        P["err_m"] = np.sqrt(((xy - te[["X", "Y"]].to_numpy(np.float64)) ** 2).sum(1)) * gf
        P["v4_x"], P["v4_y"] = f["est"][:, 0], f["est"][:, 1]
        P["v4_err_m"] = np.sqrt(((f["est"] - te[["X", "Y"]].to_numpy(np.float64)) ** 2).sum(1)) * gf
        for j in range(o.shape[1]):
            P[f"cell{j + 1}_index"] = cand[:, j]
            P[f"cell{j + 1}_weight"] = w[:, j]
        P.to_csv(OUT / "predictions" / f"{tname}.csv", index=False)
        tests[tname] = {**m, "ms_per_fp": round(ms, 3), "v4_mean_err_m": round(float(P.v4_err_m.mean()), 4),
                        "below_target": bool(m["mean_err_m"] < 7.0)}
        print(tname, tests[tname], flush=True)
    json.dump({"dataset": KEY, "version": "v5", "dev": dev, "m": M_TOP, "lam": LAM, "k_candidates": K_CAND,
               "features": BASE_FEATS, "feature_transform": "each feature + (x - max), min-max within query, rank",
               "regressor": "HistGradientBoostingRegressor(max_iter=300, lr=0.06, leaves=31, "
                            "min_leaf=40, l2=1.0, random_state=0) on log1p(distance cell-truth)",
               "trained_on": "6 dev folds of trainingData (features from fold models)",
               "l3_model_huis": int(len(posL.hui_items)), "tests": tests,
               "timestamp_utc": datetime.now(timezone.utc).isoformat()},
              open(OUT / "summary.json", "w"), indent=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev", "check", "final"], required=True)
    ap.add_argument("--fold", type=int)
    a = ap.parse_args()
    {"dev": lambda: stage_dev(a.fold), "check": dev_check, "final": stage_final}[a.stage]()


if __name__ == "__main__":
    main()
