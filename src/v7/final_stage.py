"""Test-set stage of V7 (validationData), run once per declared variant after the dev selection.

    V6 reproduction   the V6 GBM re-ranker is fitted on all dev rows and applied to the cached test features
                      (float32 `place`, exactly V6) -> compared with the stored V6 predictions
    V6*               same predictions, float64 fusion (no numerical noise)
    V7 variants       scorers fitted on all six dev folds (member i early-stops on dev fold i), applied to the
                      test features; weights -> x_pred = sum_i w_i c_i

Outputs per variant: predictions CSV (true/pred position, the 30 candidate cells and their weights),
summary entry in results/huim_only/uji/v7/test_summary.json. The test labels are only read to MEASURE.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import place, regressor, relative  # noqa: E402
from v7.common import OUT, UJI, err_m, load_cache  # noqa: E402
from v7.direct import fit_members, predict_members  # noqa: E402
from v7.experiments import MODEL_BLOCKS, prepare  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.geo import GEO_SCORE_COLS, geo_block  # noqa: E402
from v7.rerank import N_FOLDS, flat, load_dev  # noqa: E402

TEST = "validationData"


def test_features(blocks: tuple[str, ...]) -> np.ndarray:
    t = load_cache(f"test_{TEST}")
    parts, scores = [t["F"]], [t["F"][..., c] for c in GEO_SCORE_COLS]
    for b in blocks:
        if b == "geo":
            continue
        X = load_cache(f"test_{TEST}_{b}")["X"]
        parts.append(X)
        if b in MODEL_BLOCKS:
            scores.append(X[..., 3])
    if "geo" in blocks:
        parts.append(geo_block(scores, t["cxy"]))
    return np.concatenate(parts, -1)


def v6_test(D: list[dict], T: dict):
    """V6 as published: GBM on all dev rows, float32 place. Returns (xy_v6, xy_v6_float64, p_test)."""
    X = np.concatenate([flat(d["F"]) for d in D])
    y = np.concatenate([np.log1p(d["dist"]).ravel() for d in D])
    reg = regressor().fit(X, y)
    R = relative(T["F"])
    p = np.expm1(reg.predict(R.reshape(-1, R.shape[-1]))).reshape(R.shape[:2])
    xy6, o, w = place(p, T["cxy"])
    xy64, _ = fuse(p.astype(np.float64), T["cxy"], rule="v6", m=20, T=2.0)
    return xy6, xy64, p, o, w


def metrics(T: dict, xy: np.ndarray, floor_pred: np.ndarray | None = None) -> dict:
    e = err_m(xy, T["true"])
    true_bf = np.char.add(np.char.add(T["bld"].astype(str), "_"), T["flr"].astype(str))
    fl = T["floor"] if floor_pred is None else floor_pred
    ok = fl == true_bf
    bok = np.char.partition(fl.astype(str), "_")[:, 0] == T["bld"].astype(str)
    return {"n": int(len(e)), "mean": float(e.mean()), "median": float(np.median(e)), "p75": float(np.percentile(e, 75)),
            "p90": float(np.percentile(e, 90)), "p95": float(np.percentile(e, 95)), "max": float(e.max()),
            "building_accuracy": float(bok.mean()), "floor_accuracy": float(ok.mean()),
            "mean_right_floor": float(e[ok].mean()), "n_right_floor": int(ok.sum()),
            "mean_wrong_floor": float(e[~ok].mean()), "n_wrong_floor": int((~ok).sum()),
            "share_within_2m": float((e <= 2).mean()), "share_within_5m": float((e <= 5).mean())}


def direct_test(D_blocks: tuple[str, ...], cfg: dict, seed: int = 0, n_seeds: int = 1):
    """Scorers fitted on all six dev folds -> weights/positions on the test candidates."""
    D = load_dev()
    data = prepare(D, D_blocks)
    T = load_cache(f"test_{TEST}")
    Xt = relative(test_features(D_blocks)).astype(np.float32)
    o = T["cxy"][:, 0]
    members = []
    for s in range(n_seeds):
        members += fit_members(data, list(range(N_FOLDS)), cfg, seed + 100 * s)
    t0 = time.perf_counter()
    xp, w = predict_members(members, Xt, T["cxy"] - o[:, None])
    ms = (time.perf_counter() - t0) / len(Xt) * 1000
    return o + xp, w, members, ms


def write_predictions(name: str, T: dict, xy: np.ndarray, w: np.ndarray, cand_order: np.ndarray | None = None) -> Path:
    out = OUT / "predictions"
    out.mkdir(parents=True, exist_ok=True)
    cand = T["cand"] if cand_order is None else np.take_along_axis(T["cand"], cand_order, 1)
    P = pd.DataFrame({"src_row": T["src_row"], "phone": T["phone"], "true_building": T["bld"], "true_floor": T["flr"],
                      "pred_building_floor": T["floor"], "true_x": T["true"][:, 0], "true_y": T["true"][:, 1],
                      "pred_x": xy[:, 0], "pred_y": xy[:, 1], "err_m": err_m(xy, T["true"])})
    for j in range(w.shape[1]):
        P[f"cell{j + 1}_index"] = cand[:, j]
        P[f"cell{j + 1}_weight"] = w[:, j]
    p = out / f"{name}.csv"
    P.to_csv(p, index=False)
    return p


def seconds_per_query(blocks: tuple[str, ...]) -> float:
    """Measured wall time per test query of the HUI evidence (V6 part + each extra block), seconds."""
    t = load_cache(f"test_{TEST}")["_meta"]["seconds_per_query_v6_part"]
    for b in blocks:
        if b != "geo":
            t += load_cache(f"test_{TEST}_{b}")["_meta"].get("seconds_per_query", 0.0)
    return float(t)


def main(variants: dict[str, dict]) -> None:
    D = load_dev()
    T = load_cache(f"test_{TEST}")
    prev = OUT / "test_summary.json"
    res = json.load(open(prev)) if prev.exists() else {}        # variants scored earlier are kept (each is scored once)
    xy6, xy64, p6, o6, w6 = v6_test(D, T)
    res["V6_reproduced"] = metrics(T, xy6) | {"ms_per_query": round(seconds_per_query(()) * 1000, 1)}
    write_predictions("V6_reproduced", T, xy6, w6, o6)
    _x, w64 = fuse(p6.astype(np.float64), T["cxy"], rule="v6", m=20, T=2.0)
    res["V6_star"] = metrics(T, xy64) | {"ms_per_query": res["V6_reproduced"]["ms_per_query"]}
    write_predictions("V6_star", T, xy64, w64)
    pa = json.load(open(OUT / "V7A_dev.json"))["adaptT"]["in_sample_best"]["params"]
    xyA, wA = fuse(p6.astype(np.float64), T["cxy"], **pa)
    res["V7_A"] = metrics(T, xyA) | {"params": pa, "ms_per_query": res["V6_reproduced"]["ms_per_query"]}
    write_predictions("V7_A", T, xyA, wA)
    for name, v in variants.items():
        if name in res:
            print(f"{name}: already scored, kept", flush=True)
            continue
        xy, w, members, ms = direct_test(tuple(v["blocks"]), v["cfg"], v.get("seed", 0), v.get("n_seeds", 1))
        res[name] = metrics(T, xy) | {"scorer_ms_per_query": round(ms, 4), "n_members": len(members), "blocks": list(v["blocks"]),
                                      "ms_per_query": round(seconds_per_query(tuple(v["blocks"])) * 1000 + ms, 1)}
        write_predictions(name, T, xy, w)
    for k, r in res.items():
        print(f"{k:16s} test mean {r['mean']:.4f} m | median {r['median']:.3f} | P90 {r['p90']:.2f} | floor acc {r['floor_accuracy']:.4f}", flush=True)
    json.dump(res, open(OUT / "test_summary.json", "w"), indent=1)


if __name__ == "__main__":
    from v7.run_dev import CFG, N_SEEDS, VARIANTS
    want = sys.argv[1:] or ["B_base", "C_rel", "C_rel_absL3"]
    main({v: {"blocks": VARIANTS[v], "cfg": CFG, "n_seeds": N_SEEDS.get(v, 1)} for v in want})
