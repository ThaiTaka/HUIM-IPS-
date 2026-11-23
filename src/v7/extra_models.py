"""Extra HUI-evidence blocks for the cached candidates (V7-C).

`extra_block` is the same per-candidate evidence V6 derives from its absolute-strength HUI model (pattern
score, coverage, reverse coverage, smoothed relative score, rank, strength-profile agreement), computed for
any additional HUI model (another internal utility, level items, another minUtil). It only reads the mined
HUIs of `pos` and the query's own reading; candidates `cand` and the chosen `floor` come from the V6 stage.

`dev_block` builds one block for the 6 dev folds (fold models mined on the fold's training phones only).
Run: python src/v7/extra_models.py --block rel --fold k      (blocks: rel, absL3; device-robust block: src/v7/device.py)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_research import (THETA, components_multi, expand_levels, fold_path, load_model,  # noqa: E402
                           profile_feats, strength_profile, tag)
from huim_rerank_final import KEY  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import folds_for, inputs  # noqa: E402
from v7.common import base_meta, load_cache, save_cache  # noqa: E402

BLOCK_NAMES = ["P", "V", "R", "S_rel", "rank", "mae", "corr", "cos"]


def extra_block(pos, q: np.ndarray, cand: np.ndarray, floor: np.ndarray, batch: int = 256) -> np.ndarray:
    P, V, R = components_multi(pos, q, [(2.0, 20.0)], {"base": pos.Cw})
    P = P[("base", (2.0, 20.0))]
    S = (P * V ** 3) @ pos._kernel(3.0)
    Sf = np.where(pos.cell_bf[None, :] == floor[:, None], S, -1.0)
    rank = np.argsort(np.argsort(-Sf, 1), 1)
    tk = lambda A: np.take_along_axis(A, cand, 1)
    mass, qhat = strength_profile(pos)
    ext = []
    for s in range(0, len(q), batch):
        mae, corr, cos, _tm, _n = profile_feats(q[s:s + batch], mass, qhat, cand[s:s + batch])
        ext.append(np.stack([mae, corr, cos], -1))
    Sc = tk(S)
    B = np.stack([tk(P), tk(V), tk(R), Sc / np.maximum(Sc.max(1, keepdims=True), 1e-12), tk(rank)], -1)
    return np.concatenate([B, np.concatenate(ext)], -1).astype(np.float32)


BLOCKS = {  # name -> (utility kind, levels)
    "rel": ("rel", 1),
    "absL3": ("abs", 3),
}


def dev_block(name: str, k: int) -> None:
    kind, levels = BLOCKS[name]
    b = load(KEY)
    _p, Q, *_ = inputs(b, kind)
    base = load_cache(f"dev_fold{k}")
    tri, dvi = folds_for(b, len(Q))[k]
    assert np.array_equal(dvi, base["dvi"]), "fold definition changed"
    pos, ex = load_model(fold_path(k, tag(levels, THETA, kind)), b.ground_factor)
    assert np.array_equal(ex["dvi"], dvi)
    t0 = time.perf_counter()
    X = extra_block(pos, expand_levels(Q[dvi], levels), base["cand"], base["floor"])
    meta = base_meta(kind="dev_extra_block", block=name, fold=int(k), n_queries=int(len(dvi)),
                     model=f"{kind} utility, levels {levels}, theta {THETA:g}, mined on the fold's training phones only",
                     names=BLOCK_NAMES, seconds=round(time.perf_counter() - t0, 1))
    save_cache(f"dev_fold{k}_{name}", meta, X=X)
    print(f"block {name} fold {k}: {X.shape} in {meta['seconds']}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True)
    ap.add_argument("--fold", type=int, required=True)
    a = ap.parse_args()
    dev_block(a.block, a.fold)
