"""PHASE Q - positioning by High Utility Itemset matching alone (no k-NN).

The positioning model IS a set of HUIs. No training fingerprint is ever
compared with a query; only mined patterns are.

Training (EFIM, one run per cell)
---------------------------------
    cell c          one training reference point (the RP column): its training
                    fingerprints are the utility transactions D_c
    HUI_c           EFIM(D_c, p = 1, minUtil_c = theta% x u(D_c)); a run that
                    exceeds the per-cell budget is re-run at theta x ESCALATE
                    until it completes (never a truncated set)
    the model       for every cell: its HUIs X with u(X), support s(X), and the
                    cell's position (mean of its training positions) and
                    building-floor; nothing else is kept

Positioning a query fingerprint T (itself one utility transaction)
------------------------------------------------------------------
For every HUI X of cell c:
    frac(X,T)  = |X n T| / |X|                       how much of the pattern is seen
    agree(X,T) = exp(-|q_T(X) - qbar_c(X)| / tau)     signal agreement, where
                 q_T(X) = mean q(i,T) over i in X n T and
                 qbar_c(X) = u(X) / (s(X) |X|), the mean item utility of X in D_c
    w(X)       = u(X) / sum_{Y in HUI_c} u(Y)         share of the cell's HUI utility

    pattern score   P_c(T) = sum_X w(X) frac(X,T)^gamma agree(X,T)
    coverage        V_c(T) = sum_{i in T, i in I_c} q(i,T) / sum_{i in T} q(i,T),
                    I_c = every WAP occurring in some HUI of c
    cell score      score_c(T) = P_c(T) x V_c(T)^beta

Locating:
    smoothing       S_c = sum_c' score_c' K(c', c), K = Gaussian of the ground
                    distance between cell positions (width sigma), same
                    building-floor only, rows normalised - a cell is supported
                    by the pattern matches of its neighbours
    building-floor  the floor whose kf best cells have the highest mean S
    (x, y)          = sum_c a_c (x_c, y_c) over the m best cells OF THAT FLOOR,
                    a_c = S_c^p / sum S^p

P_c asks "how much of cell c's high-utility pattern mass does T contain, at the
right strength"; V_c asks "how much of T is explained by c's patterns". Both
are computed from HUI_c only; the cell positions are the only other input.
(theta, gamma, tau, beta, sigma, kf, m, p) are chosen on dev folds of the
training data.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from huim.efim import mine_efim

CELL_TIME_S = 5.0
CELL_MAX_HUIS = 2000
ESCALATE = 1.25
MAX_ESCALATIONS = 60
BATCH = 64


@dataclass
class Params:
    gamma: float = 1.0
    tau: float = 15.0
    beta: float = 3.0
    m: int = 5
    p: float = 4.0
    sigma: float = 0.0
    kf: int = 1

    def label(self) -> str:
        return (f"gamma={self.gamma:g}, tau={self.tau:g}, beta={self.beta:g}, "
                f"sigma={self.sigma:g} m, kf={self.kf}, m={self.m}, p={self.p:g}")


class HUIPositioner:
    """Mines one HUI set per cell and positions queries by HUI matching."""

    def __init__(self, theta: float, cell_time_s: float = CELL_TIME_S,
                 cell_max_huis: int = CELL_MAX_HUIS,
                 ground_factor: float = 1.0) -> None:
        self.theta = theta
        self.ground_factor = ground_factor
        self.cell_time_s = cell_time_s
        self.cell_max_huis = cell_max_huis

    # ------------------------------------------------------------------ fit
    def fit(self, Q: np.ndarray, cell: np.ndarray, xy: np.ndarray,
            bf: np.ndarray) -> "HUIPositioner":
        """Q: internal utilities q(i,T) (rows = training fingerprints, 0 =
        not detected); cell: cell id per row; xy, bf: position and
        building-floor label per row."""
        nA = Q.shape[1]
        p = {j: 1.0 for j in range(nA)}
        items, util, supp, cid = [], [], [], []
        cells, cxy, cbf, crun = [], [], [], []
        t0 = time.perf_counter()
        for c in np.unique(cell):
            rows = np.flatnonzero(cell == c)
            db = [{int(j): float(Q[i, j]) for j in np.flatnonzero(Q[i])} for i in rows]
            db = [t for t in db if t]
            if not db:
                continue
            tot = float(sum(sum(t.values()) for t in db))
            th, att, spent = self.theta, 0, 0.0
            while True:
                att += 1
                s = time.perf_counter()
                huis, st = mine_efim(db, p, tot * th / 100.0,
                                     time_limit_s=self.cell_time_s,
                                     max_huis=self.cell_max_huis)
                spent += time.perf_counter() - s
                if st.status == "COMPLETED":
                    break
                if att > MAX_ESCALATIONS:
                    raise RuntimeError(f"cell {c}: no complete run")
                th *= ESCALATE
            k = len(cells)
            cells.append(c)
            cxy.append(xy[rows].mean(axis=0))
            labs, cnt = np.unique(bf[rows], return_counts=True)
            cbf.append(labs[cnt.argmax()])
            crun.append({"cell": c, "n_transactions": len(db),
                         "total_utility": tot, "theta_used_pct": th,
                         "abs_minutil": tot * th / 100.0, "n_attempts": att,
                         "n_huis": len(huis), "runtime_s": spent})
            for xs, u, s_ in huis:
                items.append(sorted(xs))
                util.append(u)
                supp.append(s_)
                cid.append(k)
        self.fit_seconds = time.perf_counter() - t0
        self.n_aps = nA
        self.cells = np.array(cells)
        self.cell_xy = np.array(cxy, dtype=np.float64)
        self.cell_bf = np.array(cbf)
        self.cell_runs = crun
        self.hui_items = items
        self.hui_util = np.array(util, np.float64)
        self.hui_supp = np.array(supp, np.float64)
        self.hui_cell = np.array(cid, np.int64)
        self._index()
        return self

    def _index(self) -> None:
        nH, nC = len(self.hui_items), len(self.cells)
        n_items = np.array([len(x) for x in self.hui_items], np.int64)
        indptr = np.concatenate([[0], np.cumsum(n_items)])
        lens = n_items.astype(np.float32)
        ind = (np.concatenate(self.hui_items).astype(np.int64) if nH
               else np.zeros(0, np.int64))
        self.H = sparse.csr_matrix((np.ones(len(ind), np.float32), ind, indptr),
                                   shape=(nH, self.n_aps))
        self.L = lens
        self.qbar = (self.hui_util / (self.hui_supp * lens)).astype(np.float32)
        tot = np.bincount(self.hui_cell, self.hui_util, minlength=nC)
        self.w = (self.hui_util / tot[self.hui_cell]).astype(np.float32)
        self.Cw = sparse.csr_matrix((self.w, (self.hui_cell, np.arange(nH))),
                                    shape=(nC, nH))
        U = sparse.csr_matrix((np.ones(nH, np.float32),
                               (self.hui_cell, np.arange(nH))), shape=(nC, nH)) @ self.H
        U.data[:] = 1.0
        self.cell_items = U.tocsr()

    # ---------------------------------------------------------------- score
    def components(self, Qq: np.ndarray, grid: list[tuple[float, float]]
                   ) -> tuple[dict, np.ndarray]:
        """Pattern scores P_c for every (gamma, tau) in grid, and coverage V_c.
        Returns ({(gamma, tau): (n_query x n_cells)}, V)."""
        n, nC = len(Qq), len(self.cells)
        P = {g: np.zeros((n, nC), np.float32) for g in grid}
        V = np.zeros((n, nC), np.float32)
        Qq = Qq.astype(np.float32)
        for s in range(0, n, BATCH):
            q = Qq[s:s + BATCH]
            d = (q > 0).astype(np.float32)
            inter = np.asarray(self.H @ d.T)
            frac = inter / self.L[:, None]
            dev = np.abs(np.asarray(self.H @ q.T) / np.maximum(inter, 1.0)
                         - self.qbar[:, None])
            for (gamma, tau) in grid:
                a = np.exp(-dev / tau) if tau else 1.0
                P[(gamma, tau)][s:s + BATCH] = np.asarray(
                    (self.Cw @ (frac ** gamma * a)).T)
            V[s:s + BATCH] = np.asarray((self.cell_items @ q.T).T) / \
                np.maximum(q.sum(axis=1, keepdims=True), 1.0)
        return P, V

    def cell_scores(self, P: np.ndarray, V: np.ndarray, beta: float,
                    sigma: float) -> np.ndarray:
        """score_c = P_c V_c^beta, then spread over same-floor cells within
        about sigma ground metres: S' = S K, K[c,c'] = g(c,c') / sum_c'' g(c,c''),
        g = exp(-d(c,c')^2 / 2 sigma^2) if c, c' share a building-floor."""
        S = P * V ** beta
        if sigma > 0:
            S = S @ self._kernel(sigma)
        return S

    def _kernel(self, sigma: float) -> np.ndarray:
        if getattr(self, "_kcache", (None,))[0] != sigma:
            d2 = ((self.cell_xy[:, None, :] - self.cell_xy[None, :, :]) ** 2
                  ).sum(-1) * self.ground_factor ** 2
            K = np.exp(-d2 / (2 * sigma ** 2)) * (
                self.cell_bf[:, None] == self.cell_bf[None, :])
            self._kcache = (sigma, (K / K.sum(axis=1, keepdims=True)).astype(np.float32))
        return self._kcache[1]

    def floor_of(self, S: np.ndarray, kf: int) -> np.ndarray:
        """Building-floor = the floor whose kf best cells score highest on
        average."""
        floors = np.unique(self.cell_bf)
        fs = np.stack([-np.sort(-S[:, self.cell_bf == f], axis=1)[:, :kf].mean(axis=1)
                       for f in floors], axis=1)
        return floors[fs.argmax(axis=1)]

    def locate(self, S: np.ndarray, floor: np.ndarray, m: int, p: float):
        """(x, y) from the m best cells of the chosen floor."""
        S = np.where(self.cell_bf[None, :] == floor[:, None], S, -1.0)
        m = min(m, S.shape[1])
        top = np.argpartition(-S, m - 1, axis=1)[:, :m]
        o = np.argsort(-np.take_along_axis(S, top, 1), axis=1)
        top = np.take_along_axis(top, o, 1)
        sc = np.clip(np.take_along_axis(S, top, 1), 0, None).astype(np.float64)
        a = sc ** p
        z = a.sum(axis=1, keepdims=True)
        a = np.where(z > 0, a / np.where(z > 0, z, 1), 1.0 / m)
        xy = np.einsum("ij,ijk->ik", a, self.cell_xy[top])
        return xy, top, a, sc

    def estimate(self, P: np.ndarray, V: np.ndarray, prm: Params):
        S = self.cell_scores(P, V, prm.beta, prm.sigma)
        floor = self.floor_of(S, prm.kf)
        xy, top, a, sc = self.locate(S, floor, prm.m, prm.p)
        return xy, floor.astype(str), top, a, sc

    def predict(self, Qq: np.ndarray, prm: Params):
        P, V = self.components(Qq, [(prm.gamma, prm.tau)])
        return self.estimate(P[(prm.gamma, prm.tau)], V, prm)
