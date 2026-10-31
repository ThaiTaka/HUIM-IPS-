"""Strict nested check of the out-of-fold protocol for one outer dev fold.

Standard V7/V6 protocol: the scorer evaluated on outer fold k is trained on the features of the other dev
folds j != k, and those features come from HUI models M_j that were mined on all folds except j -- i.e. M_j
has read the fingerprints of fold k. The scorer never sees a feature/label pair of fold k, so the leakage is
only indirect, but it is not zero.

Strict protocol (this module): for every inner fold j != k the HUI models are mined WITHOUT folds k and j
(M_{k,j}); the inner features are computed with them, the scorer is trained on those, and it is evaluated on
fold k's features from M_k (mined without k, unchanged). No fingerprint of fold k reaches the scorer.
The difference between the two scores of fold k bounds the optimism of the standard protocol.

    python src/v7/nested_check.py mine  --outer 2 --inner 0       (rank, rank-L3, abs models)
    python src/v7/nested_check.py feat  --outer 2 --inner 0
    python src/v7/nested_check.py eval  --outer 2
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_positioning import HUIPositioner  # noqa: E402
from huim_rerank_final import KEY, compute  # noqa: E402
from huim_research import THETA, expand_levels, load_model, save_model  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import folds_for, inputs  # noqa: E402
from v7.common import RES, base_meta, load_cache, save_cache, sha256_arrays  # noqa: E402

KINDS = {"rank": ("rank", 1), "L3": ("rank", 3), "abs": ("abs", 1)}


def model_path(k: int, j: int, name: str) -> Path:
    return RES / f"nested_k{k}_j{j}_{name}.npz"


def rows(b, k: int, j: int):
    folds = folds_for(b, len(b.train))
    tr = np.setdiff1d(np.arange(len(b.train)), np.concatenate([folds[k][1], folds[j][1]]))
    return tr, folds[j][1]


def mine(k: int, j: int, name: str) -> None:
    b = load(KEY)
    kind, lv = KINDS[name]
    _p, Q, cell, XY, BF = inputs(b, kind)
    tr, ev = rows(b, k, j)
    ph = b.train["PHONEID"].to_numpy()
    assert not set(ph[tr]) & (set(ph[folds_for(b, len(Q))[k][1]]) | set(ph[ev])), "a held-out phone leaked into the mining rows"
    t0 = time.perf_counter()
    pos = HUIPositioner(THETA, ground_factor=b.ground_factor).fit(expand_levels(Q[tr], lv), cell[tr], XY[tr], BF[tr])
    save_model(pos, model_path(k, j, name), dvi=ev)
    print(f"nested k{k} j{j} {name}: {len(pos.hui_items)} HUIs, {time.perf_counter() - t0:.0f}s", flush=True)


def feat(k: int, j: int) -> None:
    b = load(KEY)
    _p, Q, _c, XY, _BF = inputs(b, "rank")
    _pa, QA, *_ = inputs(b, "abs")
    tr, ev = rows(b, k, j)
    pos, ex = load_model(model_path(k, j, "rank"), b.ground_factor)
    posL, _ = load_model(model_path(k, j, "L3"), b.ground_factor)
    posA, _ = load_model(model_path(k, j, "abs"), b.ground_factor)
    assert np.array_equal(ex["dvi"], ev) and np.array_equal(pos.cells, posL.cells) and np.array_equal(pos.cells, posA.cells)
    f = compute(pos, posL, Q[ev], b.ground_factor, posA, QA[ev])
    dist = np.sqrt(((f["cxy"] - XY[ev][:, None]) ** 2).sum(-1)) * b.ground_factor
    meta = base_meta(kind="nested_dev_features", outer=int(k), inner=int(j), mined_rows_sha256=sha256_arrays(tr),
                     eval_rows_sha256=sha256_arrays(ev), n_queries=int(len(ev)))
    save_cache(f"nested_k{k}_j{j}", meta, F=f["F"], cxy=f["cxy"], dist=dist, true=XY[ev], est=f["est"], dvi=ev, cand=f["cand"],
               floor=f["floor"].astype(str))
    print(f"nested features k{k} j{j}: {f['F'].shape}", flush=True)


def evaluate(k: int) -> None:
    from huim_rerank_final import relative
    from v7.common import err_m
    from v7.direct import fit_members, predict_members
    from v7.experiments import prepare
    from v7.rerank import load_dev
    D = load_dev()
    cfg = dict(lr=5e-4, h1=32, h2=16, wd=1e-3, ep=30, tf="slog")
    inner = [j for j in range(6) if j != k]
    N = {j: load_cache(f"nested_k{k}_j{j}") for j in inner}
    std = prepare(D, ())
    nested = {}
    for j in inner:
        n = N[j]
        o = n["cxy"][:, 0]
        nested[j] = {"X": relative(n["F"]).astype(np.float32), "C": n["cxy"] - o[:, None], "t": n["true"] - o,
                     "dist": n["dist"].astype(np.float64), "keep": n["F"][:, 0, 13] > 0, "o": o}
    out = {}
    for name, data in (("standard", std), ("strict nested", {**{j: nested[j] for j in inner}, k: std[k]})):
        members = fit_members(data, inner, cfg, 0)
        xp, _w = predict_members(members, data[k]["X"], data[k]["C"])
        e = err_m(data[k]["o"] + xp, D[k]["true"])
        out[name] = float(e[data[k]["keep"]].mean())
        print(f"outer fold {k}, scorer trained with {name:14s} features: informative mean {out[name]:.4f} m", flush=True)
    print(f"optimism of the standard protocol on fold {k}: {out['strict nested'] - out['standard']:+.4f} m")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["mine", "feat", "eval"])
    ap.add_argument("--outer", type=int, default=2)
    ap.add_argument("--inner", type=int)
    ap.add_argument("--model", choices=list(KINDS))
    a = ap.parse_args()
    if a.stage == "mine":
        for nm in ([a.model] if a.model else KINDS):
            mine(a.outer, a.inner, nm)
    elif a.stage == "feat":
        feat(a.outer, a.inner)
    else:
        evaluate(a.outer)
