"""PHASE R - dev-fold research cache for the HUIM-only positioner.

Mines every dev fold of UJIIndoorLoc once (the selected utility and theta) and
saves the per-cell HUI model of each fold, so that scoring variants can be
compared on the dev folds without re-mining. The test data is never read here.

    python src/huim_research.py --stage mine --fold 0      # one fold
    python src/huim_research.py --stage mine_all            # every missing fold

Outputs: results/huim_only/uji/research/fold<k>.npz
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_positioning import HUIPositioner
from multi_datasets import load
from run_huim_only import OUT_ROOT, folds_for, inputs

KEY = "uji"
KIND = "rank"
THETA = 20.0
RES = OUT_ROOT / KEY / "research"


def fold_path(k: int, tag: str = "") -> Path:
    return RES / f"fold{k}{tag}.npz"


def expand_levels(Q: np.ndarray, L: int) -> np.ndarray:
    """Items = (AP, strength level): AP i at level l becomes column i*L + l,
    l = floor((q - 1) / 100 * L) from the internal utility q in [1, 100];
    the utility of the item stays q. L = 1 is the plain AP item."""
    if L == 1:
        return Q
    n, nA = Q.shape
    lev = np.clip(((Q - 1) / 100.0 * L).astype(np.int64), 0, L - 1)
    out = np.zeros((n, nA * L), Q.dtype)
    r, c = np.nonzero(Q)
    out[r, c * L + lev[r, c]] = Q[r, c]
    return out


def save_model(pos: HUIPositioner, f: Path, **extra) -> None:
    lens = np.array([len(x) for x in pos.hui_items], np.int64)
    np.savez_compressed(f, indptr=np.concatenate([[0], np.cumsum(lens)]),
                        items=np.concatenate(pos.hui_items).astype(np.int32),
                        util=pos.hui_util, supp=pos.hui_supp, hcell=pos.hui_cell,
                        cells=pos.cells, cell_xy=pos.cell_xy, cell_bf=pos.cell_bf,
                        n_aps=pos.n_aps, fit_seconds=pos.fit_seconds, **extra)


def load_model(f: Path, ground_factor: float) -> tuple[HUIPositioner, dict]:
    z = np.load(f, allow_pickle=False)
    pos = HUIPositioner(THETA, ground_factor=ground_factor)
    ip, it = z["indptr"], z["items"]
    pos.hui_items = [it[ip[i]:ip[i + 1]] for i in range(len(ip) - 1)]
    pos.hui_util, pos.hui_supp, pos.hui_cell = z["util"], z["supp"], z["hcell"]
    pos.cells, pos.cell_xy, pos.cell_bf = z["cells"], z["cell_xy"], z["cell_bf"]
    pos.n_aps = int(z["n_aps"])
    pos._index()
    return pos, {k: z[k] for k in z.files if k not in
                 ("indptr", "items", "util", "supp", "hcell", "cells", "cell_xy", "cell_bf")}


def mine(k: int, levels: int = 1, theta: float = THETA) -> None:
    RES.mkdir(parents=True, exist_ok=True)
    b = load(KEY)
    _p, Q, cell, XY, BF = inputs(b, KIND)
    Q = expand_levels(Q, levels)
    tri, dvi = folds_for(b, len(Q))[k]
    t0 = time.perf_counter()
    pos = HUIPositioner(theta, ground_factor=b.ground_factor).fit(Q[tri], cell[tri], XY[tri], BF[tri])
    save_model(pos, fold_path(k, tag(levels, theta)), dvi=dvi)
    print(f"fold {k}: {len(pos.hui_items)} HUIs, {time.perf_counter() - t0:.0f}s", flush=True)


def tag(levels: int, theta: float = THETA) -> str:
    return "" if levels == 1 and theta == THETA else f"_L{levels}_t{theta:g}"


# ===================================================================== eval
def hui_keys(pos: HUIPositioner) -> np.ndarray:
    """Integer id of each distinct itemset (same id = same AP set in several cells)."""
    keys = {}
    return np.array([keys.setdefault(x.tobytes(), len(keys)) for x in pos.hui_items], np.int64)


def local_df(pos: HUIPositioner, kid: np.ndarray, radius_m: float) -> np.ndarray:
    """df(X, c): number of same-floor cells within radius_m of cell c (c included)
    whose HUI set also contains the itemset X."""
    order = np.argsort(kid, kind="stable")
    ks = kid[order]
    cuts = np.flatnonzero(np.diff(ks)) + 1
    df = np.ones(len(kid), np.float32)
    xy, bf, gf = pos.cell_xy, pos.cell_bf, pos.ground_factor
    for g in np.split(order, cuts):
        if len(g) < 2:
            continue
        c = pos.hui_cell[g]
        d = np.sqrt(((xy[c][:, None] - xy[c][None]) ** 2).sum(-1)) * gf
        near = (d <= radius_m) & (bf[c][:, None] == bf[c][None])
        df[g] = near.sum(1)
    return df


def cell_matrix(pos: HUIPositioner, w: np.ndarray):
    from scipy import sparse
    nC, nH = len(pos.cells), len(pos.hui_items)
    tot = np.bincount(pos.hui_cell, w, minlength=nC)
    w = (w / tot[pos.hui_cell]).astype(np.float32)
    return sparse.csr_matrix((w, (pos.hui_cell, np.arange(nH))), shape=(nC, nH))


def item_mass(pos: HUIPositioner):
    """m_c(i): share of cell c's HUI utility carried by AP i (each HUI spreads
    its weight w(X) evenly over its items); rows sum to 1."""
    from scipy import sparse
    Hn = sparse.diags(1.0 / pos.L) @ pos.H
    M = (pos.Cw @ Hn).tocsr()
    return M


def components_multi(pos: HUIPositioner, Qq: np.ndarray, gt: list, Cws: dict, batch: int = 16):
    """P for every (weighting, gamma, tau), the coverage V and the reverse
    coverage R (mass of the cell's HUI items present in the query)."""
    n, nC = len(Qq), len(pos.cells)
    P = {(name, g): np.zeros((n, nC), np.float32) for name in Cws for g in gt}
    V = np.zeros((n, nC), np.float32)
    R = np.zeros((n, nC), np.float32)
    M = item_mass(pos)
    Qq = Qq.astype(np.float32)
    for s in range(0, n, batch):
        q = Qq[s:s + batch]
        d = (q > 0).astype(np.float32)
        inter = np.asarray(pos.H @ d.T)
        frac = inter / pos.L[:, None]
        dev = np.abs(np.asarray(pos.H @ q.T) / np.maximum(inter, 1.0) - pos.qbar[:, None])
        for (gamma, tau) in gt:
            f = frac ** gamma * (np.exp(-dev / tau) if tau else 1.0)
            for name, Cw in Cws.items():
                P[(name, (gamma, tau))][s:s + batch] = np.asarray((Cw @ f).T)
        V[s:s + batch] = np.asarray((pos.cell_items @ q.T).T) / np.maximum(q.sum(1, keepdims=True), 1.0)
        R[s:s + batch] = np.asarray((M @ d.T).T)
    return P, V, R


def locate_local(pos: HUIPositioner, S, floor, m, p, radius_m):
    """Like locate, but only cells within radius_m of the best cell count."""
    S = np.where(pos.cell_bf[None, :] == floor[:, None], S, -1.0)
    best = S.argmax(1)
    d = np.sqrt(((pos.cell_xy[None, :, :] - pos.cell_xy[best][:, None, :]) ** 2).sum(-1)) * pos.ground_factor
    S = np.where(d <= radius_m, S, -1.0)
    return pos.locate(S, floor, m, p)


def evaluate(k: int, levels: int = 1, theta: float = THETA) -> None:
    import itertools
    import pandas as pd
    b = load(KEY)
    _p, Q, _cell, XY, BF = inputs(b, KIND)
    Q = expand_levels(Q, levels)
    gf = b.ground_factor
    GT = [(2.0, 20.0), (1.0, 20.0)]
    rows = []
    light = levels > 1
    if True:
        pos, ex = load_model(fold_path(k, tag(levels, theta)), gf)
        dvi = ex["dvi"]
        t0 = time.perf_counter()
        kid = hui_keys(pos)
        nC = len(pos.cells)
        df_glob = np.bincount(kid, minlength=kid.max() + 1)[kid].astype(np.float32)
        Cws = {"base": pos.Cw}
        for r, aa in (() if light else ((10.0, (1.0, 2.0)), (20.0, (1.0,)))):
            dfl = local_df(pos, kid, r)
            for a in aa:
                Cws[f"idf_r{r:g}_a{a:g}"] = cell_matrix(pos, pos.hui_util / dfl ** a)
        if not light:
            Cws["idf_glob"] = cell_matrix(pos, pos.hui_util * np.log1p(nC / df_glob))
        print(f"fold {k}: weights built {time.perf_counter() - t0:.0f}s", flush=True)
        P, V, R = components_multi(pos, Q[dvi], GT, Cws)
        print(f"fold {k}: components {time.perf_counter() - t0:.0f}s", flush=True)
        for (name, gt), Pm in P.items():
            for beta, delta, sigma in itertools.product((1.0, 3.0), (0.0, 1.0, 3.0, 5.0, 8.0), (0.0, 3.0)):
                S = Pm * V ** beta * (R ** delta if delta else 1.0)
                if sigma:
                    S = S @ pos._kernel(sigma)
                fl = {kf: pos.floor_of(S, kf) for kf in (20,)}
                for kf, m, p in itertools.product((20,), (8, 12, 20), (8.0, 16.0)):
                    xy, *_ = pos.locate(S, fl[kf], m, p)
                    e = np.sqrt(((xy - XY[dvi]) ** 2).sum(1)) * gf
                    rows.append({"fold": k, "weight": name, "gamma": gt[0], "tau": gt[1],
                                 "beta": beta, "delta": delta, "sigma": sigma, "kf": kf,
                                 "m": m, "p": p, "loc": "top-m", "n": len(dvi),
                                 "sum_err": float(e.sum()), "floor_ok": int((fl[kf] == BF[dvi]).sum())})
                    for rad in (6.0, 10.0):
                        xy, *_ = locate_local(pos, S, fl[kf], m, p, rad)
                        e = np.sqrt(((xy - XY[dvi]) ** 2).sum(1)) * gf
                        rows.append({**rows[-1], "loc": f"r{rad:g}", "sum_err": float(e.sum())})
        print(f"fold {k}: done {time.perf_counter() - t0:.0f}s", flush=True)
        pd.DataFrame(rows).to_csv(RES / f"eval_fold{k}{tag(levels, theta)}.csv", index=False)


def merge(t: str = "") -> None:
    import pandas as pd
    prefix = "eval"
    D = pd.concat([pd.read_csv(RES / f"{prefix}_fold{k}{t}.csv") for k in range(6)])
    keys = [c for c in D.columns if c not in ("fold", "n", "sum_err", "floor_ok")]
    G = D.groupby(keys).agg(n=("n", "sum"), s=("sum_err", "sum"), f=("floor_ok", "sum"), folds=("fold", "nunique")).reset_index()
    G = G[G.folds == 6]
    G["dev_mean_m"] = G.s / G.n
    G["dev_floor"] = G.f / G.n
    G.sort_values("dev_mean_m").to_csv(RES / f"{prefix}_grid{t}.csv", index=False)
    print(G.sort_values("dev_mean_m").head(15).to_string())
    for c in keys:
        print(G.groupby(c).dev_mean_m.min().sort_values().to_string(), "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["mine", "mine_all", "eval", "merge"], required=True)
    ap.add_argument("--fold", type=int)
    ap.add_argument("--levels", type=int, default=1)
    ap.add_argument("--theta", type=float, default=THETA)
    a = ap.parse_args()
    if a.stage == "mine":
        mine(a.fold, a.levels, a.theta)
    elif a.stage == "eval":
        evaluate(a.fold, a.levels, a.theta)
    elif a.stage == "merge":
        merge(tag(a.levels, a.theta))
    else:
        for k in range(6):
            if not fold_path(k).exists():
                mine(k)


if __name__ == "__main__":
    main()
