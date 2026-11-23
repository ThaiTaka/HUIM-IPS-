"""V7-D: hierarchical HUI - floor-level HUIs as context for the cell-level decision.

Level 1 (new): one EFIM run per building-floor on ALL training fingerprints of that floor
(minUtil = theta% of the floor's total utility, theta = 12.5; a floor whose run finds more than 150,000 HUIs is
re-run at theta x 1.25, as for cells; no wall-clock limit, so the model does not depend on machine load). The resulting floor-level HUIs describe the floor's dominant AP patterns.
Level 2 (V6): one EFIM run per cell -> the cell-level HUIs, which still produce the 30 candidate cells and
all their evidence.

The floor-level HUIs enter only as CONTEXT: for the chosen floor f* of a query, from the same matching
functions as the cell level (pattern score P, coverage V, reverse coverage R over the floor's HUIs):

    P_f*, V_f*, R_f*                      floor-level evidence for the chosen floor
    margin_P, margin_V, margin_R          f* minus the best other floor of the same building
    S_f*/max_f S_f, rank of f*            S = P * V^3 over all floors / over the floors of f*'s building
    gap_cell_floor                        cell-level top-20 mean score of f* minus its floor-level rank gap

The block is constant over the query's candidates; the scorer's pooled branch lets it modulate how sharply the
weights concentrate. Region-level HUIs (between floor and cell) were not mined; the 4 m / 8 m overlapping-cell
windows of the V6 study are the negative precedent for that level.

    python src/v7/hier.py mine  --fold k      (k = 0..5, or --final)
    python src/v7/hier.py block --fold k
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_positioning import HUIPositioner  # noqa: E402
from huim_research import components_multi, fold_path, load_model, save_model  # noqa: E402
from huim_rerank_final import KEY  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import folds_for, inputs, q_matrix  # noqa: E402
from v7.common import OUT, RES, base_meta, load_cache, save_cache  # noqa: E402

THETA_FLOOR = 12.5       # start threshold; raised x1.25 only when a run exceeds MAX_HUIS (deterministic)
MAX_HUIS = 150000
TIME_LIMIT_S = 1e9       # no wall-clock limit: the V6 escalation also reacts to the clock, which would make the model depend on machine load
NAMES = ["fP", "fV", "fR", "mP", "mV", "mR", "fS_rel", "f_rank", "fS_rel_bld", "f_rank_bld", "top20_gap"]


def floor_path(k: int | None) -> Path:
    return OUT / "models" / "floor_L1_final.npz" if k is None else RES / f"fold{k}_floor_t{THETA_FLOOR:g}.npz"


def mine(k: int | None) -> None:
    b = load(KEY)
    _p, Q, _cell, XY, BF = inputs(b, "rank")
    if k is None:
        rows = np.arange(len(Q))
        extra = {}
    else:
        tri, dvi = folds_for(b, len(Q))[k]
        rows, extra = tri, {"dvi": dvi}
    labs = np.unique(BF)
    code = np.array([int(np.searchsorted(labs, l)) for l in BF])
    t0 = time.perf_counter()
    pos = HUIPositioner(THETA_FLOOR, cell_time_s=TIME_LIMIT_S, cell_max_huis=MAX_HUIS, ground_factor=b.ground_factor).fit(
        Q[rows], code[rows], XY[rows], BF[rows])
    floor_path(k).parent.mkdir(parents=True, exist_ok=True)
    save_model(pos, floor_path(k), **extra)
    runs = [(r["cell"], r["n_huis"], round(r["theta_used_pct"], 1)) for r in pos.cell_runs]
    print(f"floor-level model {'final' if k is None else k}: {len(pos.hui_items)} HUIs in {time.perf_counter() - t0:.0f}s; "
          f"(floor, HUIs, theta used) {runs}", flush=True)


def context(posF, q: np.ndarray, chosen: np.ndarray, S20: np.ndarray) -> np.ndarray:
    """q (n,nA) rank utilities; chosen (n,) building-floor labels; S20 (n,) cell-level mean score of the chosen floor's
    top-20 cells. Returns (n, len(NAMES))."""
    P, V, R = components_multi(posF, q, [(2.0, 20.0)], {"base": posF.Cw})
    P = P[("base", (2.0, 20.0))]
    S = P * V ** 3
    fl = np.asarray(posF.cell_bf).astype(str)                     # label of each floor-level "cell"
    bld = np.char.partition(fl, "_")[:, 0]
    n = len(q)
    f = np.array([int(np.flatnonzero(fl == c)[0]) for c in chosen])
    ar = np.arange(n)
    same_b = bld[None, :] == bld[f][:, None]
    other = np.ones_like(S, bool)
    other[ar, f] = False
    oth_b = other & same_b
    mx = lambda A, mk: np.where(mk, A, -np.inf).max(1)
    feats = [P[ar, f], V[ar, f], R[ar, f],
             P[ar, f] - np.maximum(mx(P, oth_b), 0), V[ar, f] - np.maximum(mx(V, oth_b), 0), R[ar, f] - np.maximum(mx(R, oth_b), 0),
             S[ar, f] / np.maximum(S.max(1), 1e-12), (S > S[ar, f][:, None]).sum(1),
             S[ar, f] / np.maximum(np.where(same_b, S, -np.inf).max(1), 1e-12), (np.where(same_b, S, -np.inf) > S[ar, f][:, None]).sum(1),
             S20]
    return np.stack(feats, -1).astype(np.float32)


def dev_block(k: int) -> None:
    b = load(KEY)
    _p, Q, *_ = inputs(b, "rank")
    base = load_cache(f"dev_fold{k}")
    tri, dvi = folds_for(b, len(Q))[k]
    assert np.array_equal(dvi, base["dvi"])
    posF, ex = load_model(floor_path(k), b.ground_factor)
    assert np.array_equal(ex["dvi"], dvi)
    X = context(posF, Q[dvi], base["floor"], base["F"][:, :20, 0].mean(1))
    X = np.repeat(X[:, None, :], base["cand"].shape[1], 1)
    meta = base_meta(kind="dev_extra_block", block="hier", fold=int(k), names=NAMES, theta_floor=THETA_FLOOR, n_queries=int(len(dvi)),
                     model="floor-level HUIs mined on the fold's training phones only")
    save_cache(f"dev_fold{k}_hier", meta, X=X)
    print(f"hier block fold {k}: {X.shape}", flush=True)


def test_block() -> None:
    b = load(KEY)
    te = b.tests["validationData"]
    prep = inputs(b, "rank")[0]
    T = load_cache("test_validationData")
    posF, _ = load_model(floor_path(None), b.ground_factor)
    X = context(posF, q_matrix(prep, te, "rank"), T["floor"], T["F"][:, :20, 0].mean(1))
    X = np.repeat(X[:, None, :], T["cand"].shape[1], 1)
    save_cache("test_validationData_hier", base_meta(kind="test_extra_block", block="hier", names=NAMES, theta_floor=THETA_FLOOR), X=X)
    print(f"hier test block: {X.shape}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["mine", "block", "test"])
    ap.add_argument("--fold", type=int)
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    if a.stage == "mine":
        mine(None if a.final else a.fold)
    elif a.stage == "block":
        dev_block(a.fold)
    else:
        test_block()
