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


# ============================================================ re-ranking features
K_CAND = 30
FEATS = ["S", "logS", "S_rel", "rank", "P21", "P11", "V", "R", "Pidf", "raw_rel",
         "d_est", "d_top1", "dens5", "n_ap", "PL3", "VL3", "SL3_rel", "rankL3"]


def features(k: int) -> None:
    """Per dev query: the K_CAND best cells of the chosen floor (baseline score)
    and HUI-evidence features for each; target = ground distance cell-truth."""
    b = load(KEY)
    _p, Q, _cell, XY, BF = inputs(b, KIND)
    gf = b.ground_factor
    pos, ex = load_model(fold_path(k), gf)
    dvi = ex["dvi"]
    kid = hui_keys(pos)
    Cws = {"base": pos.Cw, "idf": cell_matrix(pos, pos.hui_util / local_df(pos, kid, 10.0) ** 2)}
    P, V, R = components_multi(pos, Q[dvi], [(2.0, 20.0), (1.0, 20.0)], Cws)
    P21, P11, Pidf = P[("base", (2.0, 20.0))], P[("base", (1.0, 20.0))], P[("idf", (2.0, 20.0))]
    raw = P21 * V ** 3
    S = raw @ pos._kernel(3.0)
    floor = pos.floor_of(S, 20)
    est, *_ = pos.locate(S, floor, 12, 8.0)
    Sf = np.where(pos.cell_bf[None, :] == floor[:, None], S, -1.0)
    top = np.argsort(-Sf, 1)[:, :K_CAND]
    # level model on the same cells (cell ids are the same RP list)
    posL, _ = load_model(fold_path(k, tag(3)), gf)
    assert np.array_equal(posL.cells, pos.cells)
    PL, VL, _R = components_multi(posL, expand_levels(Q[dvi], 3), [(1.0, 20.0)], {"base": posL.Cw})
    PL = PL[("base", (1.0, 20.0))]
    SL = (PL * VL ** 3) @ posL._kernel(3.0)
    SLf = np.where(pos.cell_bf[None, :] == floor[:, None], SL, -1.0)
    rankL = np.argsort(np.argsort(-SLf, 1), 1)
    n, Kc = len(dvi), top.shape[1]
    tk = lambda A: np.take_along_axis(A, top, 1)
    cxy = pos.cell_xy[top]
    Stop = tk(S)
    smax = np.maximum(Stop[:, :1], 1e-12)
    d_est = np.sqrt(((cxy - est[:, None]) ** 2).sum(-1)) * gf
    d_top1 = np.sqrt(((cxy - cxy[:, :1]) ** 2).sum(-1)) * gf
    dd = np.sqrt(((cxy[:, :, None] - cxy[:, None]) ** 2).sum(-1)) * gf
    dens5 = (dd <= 5.0).sum(-1)
    F = np.stack([Stop, np.log(Stop + 1e-9), Stop / smax, np.tile(np.arange(Kc), (n, 1)),
                  tk(P21), tk(P11), tk(V), tk(R), tk(Pidf),
                  tk(raw) / np.maximum(tk(raw).max(1, keepdims=True), 1e-12),
                  d_est, d_top1, dens5, np.tile((Q[dvi] > 0).sum(1)[:, None], (1, Kc)),
                  tk(PL), tk(VL), tk(SL) / np.maximum(tk(SL).max(1, keepdims=True), 1e-12),
                  tk(rankL)], -1).astype(np.float32)
    dist = np.sqrt(((cxy - XY[dvi][:, None]) ** 2).sum(-1)) * gf
    np.savez_compressed(RES / f"feat_fold{k}.npz", F=F, dist=dist, cxy=cxy, true=XY[dvi],
                        est=est, floor_ok=floor == BF[dvi], dvi=dvi)
    e = np.sqrt(((est - XY[dvi]) ** 2).sum(1)) * gf
    print(f"fold {k}: baseline {e.mean():.3f} m, best-of-{K_CAND} {dist.min(1).mean():.3f} m", flush=True)


FEATS2 = ["prof_mae", "prof_corr", "prof_cos", "top_ap_mass", "shared_n", "prof_maeL3", "prof_cosL3"]


def strength_profile(pos: HUIPositioner):
    """Per cell c and AP i, from the HUIs of c only:
    mass m_c(i) = sum_{X in HUI_c, i in X} w(X)            (pattern mass on i)
    qhat_c(i)   = sum w(X) qbar_c(X) / sum w(X) over X in HUI_c containing i
                  (estimated strength of i in c)."""
    Wq = pos.Cw.multiply(pos.qbar[None, :]).tocsr()
    num = np.asarray((Wq @ pos.H).todense())
    den = np.asarray((pos.Cw @ pos.H).todense())
    qhat = np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)
    mass = den / np.maximum(den.sum(1, keepdims=True), 1e-12)
    return mass.astype(np.float32), qhat.astype(np.float32)


def profile_feats(q, mass, qhat, cand):
    """q: (n, nA) query utilities; cand: (n, K) cell indices."""
    M, Qh = mass[cand], qhat[cand]                       # (n, K, nA)
    qq = q[:, None, :].astype(np.float32)
    det = qq > 0
    sh = det & (Qh > 0)
    wq = np.where(sh, qq, 0)
    mae = (wq * np.abs(qq - Qh)).sum(-1) / np.maximum(wq.sum(-1), 1)
    a = np.where(sh, qq, 0); bq = np.where(sh, Qh, 0)
    nsh = np.maximum(sh.sum(-1), 1)
    am = a.sum(-1, keepdims=True) / nsh[..., None]; bm = bq.sum(-1, keepdims=True) / nsh[..., None]
    da, db = np.where(sh, a - am, 0), np.where(sh, bq - bm, 0)
    corr = (da * db).sum(-1) / np.sqrt(np.maximum((da ** 2).sum(-1) * (db ** 2).sum(-1), 1e-9))
    full = M * Qh
    cos = (qq * full).sum(-1) / np.sqrt(np.maximum((qq ** 2).sum(-1) * (full ** 2).sum(-1), 1e-12))
    strongest = q.argmax(1)
    top_mass = M[np.arange(len(q)), :, strongest] if False else np.take_along_axis(
        M, np.repeat(strongest[:, None, None], M.shape[1], 1), 2)[..., 0]
    return mae, corr, cos, top_mass, sh.sum(-1)


def features2(k: int) -> None:
    b = load(KEY)
    _p, Q, _cell, XY, BF = inputs(b, KIND)
    gf = b.ground_factor
    f = dict(np.load(RES / f"feat_fold{k}.npz"))
    pos, _ = load_model(fold_path(k), gf)
    # candidates were stored by position; (x, y, floor) is unique and every
    # candidate of a query lies on that query's chosen floor
    look: dict = {}
    for i, xy in enumerate(pos.cell_xy):
        look.setdefault(tuple(np.round(xy, 4)), {})[pos.cell_bf[i]] = i
    cand = np.zeros(f["cxy"].shape[:2], np.int64)
    for r in range(len(cand)):
        opts = [look[tuple(np.round(xy, 4))] for xy in f["cxy"][r]]
        fl = set.intersection(*[set(o) for o in opts])
        assert len(fl) == 1, r
        fl = fl.pop()
        cand[r] = [o[fl] for o in opts]
    q = Q[f["dvi"]]
    out = []
    for s in range(0, len(q), 256):
        mass, qhat = strength_profile(pos) if s == 0 else (mass, qhat)
        mae, corr, cos, tm, shn = profile_feats(q[s:s + 256], mass, qhat, cand[s:s + 256])
        out.append(np.stack([mae, corr, cos, tm, shn], -1))
    posL, _ = load_model(fold_path(k, tag(3)), gf)
    massL, qhatL = strength_profile(posL)
    qL = expand_levels(q, 3)
    outL = []
    for s in range(0, len(q), 256):
        mae, corr, cos, tm, shn = profile_feats(qL[s:s + 256], massL, qhatL, cand[s:s + 256])
        outL.append(np.stack([mae, cos], -1))
    F2 = np.concatenate([np.concatenate(out), np.concatenate(outL)], -1).astype(np.float32)
    np.savez_compressed(RES / f"feat2_fold{k}.npz", F2=F2, cand=cand)
    print(f"fold {k}: profile features {F2.shape}", flush=True)


FEATS3 = FEATS + ["same_floor", "floor_rel"] + FEATS2
K3 = 40
FLOOR_FEATS_PER = ["S1", "S3", "S10", "S20", "SL1", "SL10", "Vmax", "Pmax", "Rmax", "n_cells"]


def features3(k: int) -> None:
    """Candidates = the K3 best cells of the chosen BUILDING (any floor), so the
    position no longer depends on the floor decision; plus per-floor aggregates
    of the HUI scores for a learned floor decision."""
    b = load(KEY)
    _p, Q, _cell, XY, BF = inputs(b, KIND)
    gf = b.ground_factor
    pos, ex = load_model(fold_path(k), gf)
    dvi = ex["dvi"]
    q = Q[dvi]
    kid = hui_keys(pos)
    Cws = {"base": pos.Cw, "idf": cell_matrix(pos, pos.hui_util / local_df(pos, kid, 10.0) ** 2)}
    P, V, R = components_multi(pos, q, [(2.0, 20.0), (1.0, 20.0)], Cws)
    P21, P11, Pidf = P[("base", (2.0, 20.0))], P[("base", (1.0, 20.0))], P[("idf", (2.0, 20.0))]
    raw = P21 * V ** 3
    S = raw @ pos._kernel(3.0)
    floor = pos.floor_of(S, 20)
    est, *_ = pos.locate(S, floor, 12, 8.0)
    posL, _ = load_model(fold_path(k, tag(3)), gf)
    assert np.array_equal(posL.cells, pos.cells)
    PL, VL, _R = components_multi(posL, expand_levels(q, 3), [(1.0, 20.0)], {"base": posL.Cw})
    PL = PL[("base", (1.0, 20.0))]
    SL = (PL * VL ** 3) @ posL._kernel(3.0)
    bld = np.array([f.split("_")[0] for f in pos.cell_bf])
    qb = np.array([f.split("_")[0] for f in floor])
    inb = bld[None, :] == qb[:, None]
    Sb = np.where(inb, S, -1.0)
    top = np.argsort(-Sb, 1)[:, :K3]
    n, Kc = len(dvi), K3
    tk = lambda A: np.take_along_axis(A, top, 1)
    cxy = pos.cell_xy[top]
    Stop = tk(S)
    smax = np.maximum(Stop[:, :1], 1e-12)
    d_est = np.sqrt(((cxy - est[:, None]) ** 2).sum(-1)) * gf
    d_top1 = np.sqrt(((cxy - cxy[:, :1]) ** 2).sum(-1)) * gf
    dd = np.sqrt(((cxy[:, :, None] - cxy[:, None]) ** 2).sum(-1)) * gf
    dens5 = (dd <= 5.0).sum(-1)
    SLb = np.where(inb, SL, -1.0)
    rankL = np.argsort(np.argsort(-SLb, 1), 1)
    floors = np.unique(pos.cell_bf)
    fscore = np.stack([-np.sort(-np.where(pos.cell_bf[None, :] == f, S, -1.0), 1)[:, :20].mean(1)
                       for f in floors], 1)
    fbest = fscore.max(1, keepdims=True)
    cfl = np.searchsorted(floors, pos.cell_bf[top])
    floor_rel = np.take_along_axis(fscore, cfl, 1) / np.maximum(fbest, 1e-12)
    F = np.stack([Stop, np.log(Stop + 1e-9), Stop / smax, np.tile(np.arange(Kc), (n, 1)),
                  tk(P21), tk(P11), tk(V), tk(R), tk(Pidf),
                  tk(raw) / np.maximum(tk(raw).max(1, keepdims=True), 1e-12),
                  d_est, d_top1, dens5, np.tile((q > 0).sum(1)[:, None], (1, Kc)),
                  tk(PL), tk(VL), tk(SL) / np.maximum(tk(SL).max(1, keepdims=True), 1e-12),
                  tk(rankL), (pos.cell_bf[top] == floor[:, None]).astype(np.float32), floor_rel], -1)
    mass, qhat = strength_profile(pos)
    massL, qhatL = strength_profile(posL)
    qL = expand_levels(q, 3)
    ext = []
    for s in range(0, n, 256):
        mae, corr, cos, tm, shn = profile_feats(q[s:s + 256], mass, qhat, top[s:s + 256])
        maeL, _c, cosL, _t, _n = profile_feats(qL[s:s + 256], massL, qhatL, top[s:s + 256])
        ext.append(np.stack([mae, corr, cos, tm, shn, maeL, cosL], -1))
    F = np.concatenate([F, np.concatenate(ext)], -1).astype(np.float32)
    dist = np.sqrt(((cxy - XY[dvi][:, None]) ** 2).sum(-1)) * gf
    # per-floor aggregates (floors of the query's building), for the floor decision
    agg = []
    for f in floors:
        m = pos.cell_bf == f
        srt = -np.sort(-np.where(m[None, :], S, -1.0), 1)
        srtL = -np.sort(-np.where(m[None, :], SL, -1.0), 1)
        agg.append(np.stack([srt[:, 0], srt[:, :3].mean(1), srt[:, :10].mean(1), srt[:, :20].mean(1),
                             srtL[:, 0], srtL[:, :10].mean(1),
                             np.where(m[None, :], V, 0).max(1), np.where(m[None, :], P21, 0).max(1),
                             np.where(m[None, :], R, 0).max(1), np.full(n, m.sum())], -1))
    FA = np.stack(agg, 1).astype(np.float32)          # (n, n_floors, feats)
    np.savez_compressed(RES / f"feat3_fold{k}.npz", F=F, dist=dist, cxy=cxy, true=XY[dvi], est=est,
                        cand=top, floor_pred=floor, floor_true=BF[dvi], floors=floors, FA=FA,
                        floor_ok=floor == BF[dvi], dvi=dvi)
    e = np.sqrt(((est - XY[dvi]) ** 2).sum(1)) * gf
    print(f"fold {k}: baseline {e.mean():.3f} m, best-of-{K3} (building) {dist.min(1).mean():.3f} m", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["mine", "mine_all", "eval", "merge", "feat", "feat2", "feat3"], required=True)
    ap.add_argument("--fold", type=int)
    ap.add_argument("--levels", type=int, default=1)
    ap.add_argument("--theta", type=float, default=THETA)
    a = ap.parse_args()
    if a.stage == "mine":
        mine(a.fold, a.levels, a.theta)
    elif a.stage == "eval":
        evaluate(a.fold, a.levels, a.theta)
    elif a.stage == "feat":
        features(a.fold)
    elif a.stage == "feat2":
        features2(a.fold)
    elif a.stage == "feat3":
        features3(a.fold)
    elif a.stage == "merge":
        merge(tag(a.levels, a.theta))
    else:
        for k in range(6):
            if not fold_path(k).exists():
                mine(k)


if __name__ == "__main__":
    main()
