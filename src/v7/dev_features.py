"""Stage 1 of V7: HUI-evidence features of the 30 candidate cells of every dev query, per dev fold.

Identical computation to V6 (`huim_rerank_final.compute`, `with_abs=True`), but it additionally stores the
candidate cell indices, the predicted building-floor, PHONEID and the true building/floor so that the
diagnosis can be done per phone / per floor. Fold k's three HUI models (rank, rank-L3, abs) were mined on
the training fingerprints of the other five PHONEID groups only; the features of fold k's queries use
those models and nothing else (out-of-fold).

Run: python src/v7/dev_features.py --fold k
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import KEY, compute  # noqa: E402
from huim_research import THETA, fold_path, load_model, tag  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import folds_for, inputs  # noqa: E402
from v7.common import GF, base_meta, save_cache, sha256_arrays  # noqa: E402


def build(k: int) -> None:
    b = load(KEY)
    _p, Q, _c, XY, _BF = inputs(b, "rank")
    _pa, QA, *_ = inputs(b, "abs")
    tri, dvi = folds_for(b, len(Q))[k]
    pos, ex = load_model(fold_path(k), b.ground_factor)
    posL, _ = load_model(fold_path(k, tag(3)), b.ground_factor)
    posA, exA = load_model(fold_path(k, tag(1, THETA, "abs")), b.ground_factor)
    assert np.array_equal(pos.cells, posL.cells) and np.array_equal(pos.cells, posA.cells)
    assert np.array_equal(ex["dvi"], dvi) and np.array_equal(exA["dvi"], dvi), "fold definition changed"
    assert not np.intersect1d(tri, dvi).size, "train/eval overlap"
    ph = b.train["PHONEID"].to_numpy()
    assert not np.intersect1d(np.unique(ph[tri]), np.unique(ph[dvi])).size, "a phone is in both sides of the fold"
    f = compute(pos, posL, Q[dvi], b.ground_factor, posA, QA[dvi])
    dist = np.sqrt(((f["cxy"] - XY[dvi][:, None]) ** 2).sum(-1)) * b.ground_factor
    tr = b.train.iloc[dvi]
    meta = base_meta(kind="dev_features", fold=int(k), n_queries=int(len(dvi)),
                     train_idx_sha256=sha256_arrays(tri), eval_idx_sha256=sha256_arrays(dvi),
                     models="rank theta20 + rank-L3 theta20 + abs theta20 (mined on the fold's training rows only)",
                     n_features=int(f["F"].shape[-1]), k_candidates=int(f["cand"].shape[1]))
    save_cache(f"dev_fold{k}", meta, F=f["F"], cxy=f["cxy"], dist=dist, true=XY[dvi], est=f["est"], dvi=dvi,
               cand=f["cand"], floor=f["floor"].astype(str), phone=tr["PHONEID"].to_numpy(),
               bld=tr["BUILDINGID"].to_numpy(), flr=tr["FLOOR"].to_numpy(), cell_xy=pos.cell_xy,
               cell_bf=pos.cell_bf.astype(str))
    print(f"dev fold {k}: {len(dvi)} queries, features {f['F'].shape}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True)
    build(ap.parse_args().fold)
