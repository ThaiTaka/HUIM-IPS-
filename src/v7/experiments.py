"""Dev-fold experiments of V7 (V7-A fusion, V7-B direct optimisation, V7-C extra HUI evidence).

All numbers are out-of-fold: for evaluation fold k, every learned component is fitted on the other five dev
folds only (the scorers additionally early-stop on one of those folds). Coordinates are handled relative to
each query's top HUI candidate and in float64 (the V6 float32 weights times Web-Mercator coordinates of
~4.9e6 add ~0.5 m of numerical noise; `V6*` below is V6 with that noise removed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import relative  # noqa: E402
from v7.common import GF, err_m, load_cache  # noqa: E402
from v7.direct import fit_members, predict_members  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import N_FOLDS, load_dev, oof_v6  # noqa: E402


MODEL_BLOCKS = ("rel", "absL3")      # extra HUI models; column 3 of their block is the relative score


def features(D: list[dict], blocks: tuple[str, ...] = ()) -> list[np.ndarray]:
    """V6 features (33) + extra blocks, per dev fold. The pseudo-block "geo" is derived from the scores of
    the HUI models present (V6's three + any model blocks) and the cell centres."""
    from v7.geo import GEO_SCORE_COLS, geo_block
    out = []
    for k, d in enumerate(D):
        parts = [d["F"]]
        scores = [d["F"][..., c] for c in GEO_SCORE_COLS]
        for b in blocks:
            if b == "geo":
                continue
            X = load_cache(f"dev_fold{k}_{b}")["X"]
            parts.append(X)
            if b in MODEL_BLOCKS:
                scores.append(X[..., 3])
        if "geo" in blocks:
            parts.append(geo_block(scores, d["cxy"]))
        out.append(np.concatenate(parts, -1))
    return out


def prepare(D: list[dict], blocks: tuple[str, ...] = ()) -> list[dict]:
    data = []
    for d, F in zip(D, features(D, blocks)):
        o = d["cxy"][:, 0]
        data.append({"X": relative(F).astype(np.float32), "C": d["cxy"] - o[:, None], "t": d["true"] - o,
                     "dist": d["dist"].astype(np.float64), "keep": d["F"][:, 0, 13] > 0, "o": o})
    return data


def direct_oof(data: list[dict], cfg: dict, folds=range(N_FOLDS), seed: int = 0, verbose: bool = True,
               name: str | None = None, blocks: tuple[str, ...] = ()):
    """Out-of-fold direct predictions. Returns {k: (xy global, weights)}; with `name`, they are cached
    (with the configuration) as oof_<name> so tables, bootstraps and figures are computed from them."""
    out = {}
    for k in folds:
        members = fit_members(data, [j for j in range(N_FOLDS) if j != k], cfg, seed)
        xp, w = predict_members(members, data[k]["X"], data[k]["C"])
        out[k] = (data[k]["o"] + xp, w)
        if verbose:
            e = err_m(out[k][0], data[k]["t"] + data[k]["o"])
            keep = data[k]["keep"]
            print(f"  fold {k}: direct {e[keep].mean():.3f} m (informative) / {e.mean():.3f} (all) | epochs {[m.best_epoch for m in members]}",
                  flush=True)
    if name and len(out) == N_FOLDS:
        from v7.common import base_meta, save_cache
        save_cache(f"oof_{name}", base_meta(kind="oof_direct", cfg=cfg, blocks=list(blocks), seed=seed),
                   **{f"xy{k}": out[k][0] for k in out}, **{f"w{k}": out[k][1] for k in out})
    return out


def load_oof(name: str) -> dict:
    c = load_cache(f"oof_{name}")
    return {k: (c[f"xy{k}"], c[f"w{k}"]) for k in range(N_FOLDS)}


def v6_star(D: list[dict], P: list[np.ndarray]) -> dict:
    """V6 rule (m=20, T=2) on the OOF GBM predictions, float64 weights."""
    return {k: fuse(P[k].astype(np.float64), D[k]["cxy"], rule="v6", m=20, T=2.0)[0] for k in range(len(D))}


def summarize(D: list[dict], xy: dict, label: str) -> dict:
    e = np.concatenate([err_m(xy[k], D[k]["true"]) for k in sorted(xy)])
    keep = np.concatenate([D[k]["F"][:, 0, 13] > 0 for k in sorted(xy)])
    ok = np.concatenate([D[k]["floor"] == np.char.add(np.char.add(D[k]["bld"].astype(str), "_"), D[k]["flr"].astype(str))
                         for k in sorted(xy)])
    r = {"label": label, "n_all": int(len(e)), "n_informative": int(keep.sum()),
         "mean_all": float(e.mean()), "mean_inf": float(e[keep].mean()), "median_inf": float(np.median(e[keep])),
         "p90_inf": float(np.percentile(e[keep], 90)), "right_floor_inf": float(e[keep & ok].mean()),
         "wrong_floor_inf": float(e[keep & ~ok].mean())}
    print(f"{label:34s} informative mean {r['mean_inf']:.4f} | median {r['median_inf']:.3f} | p90 {r['p90_inf']:.2f} | "
          f"right-floor {r['right_floor_inf']:.3f} | wrong-floor {r['wrong_floor_inf']:.3f} | all {r['mean_all']:.4f}", flush=True)
    return r
