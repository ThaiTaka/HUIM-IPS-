"""Exact HUI union at a grid of minUtil values, without enumerating the HUIs.

The AP set that HUIM hands to the positioning system is the union of the High
Utility Itemsets:

    union(minUtil) = { i : some itemset X containing i has u(X) >= minUtil }.

Below ~1.9% of the total utility of UJIIndoorLoc, EFIM cannot enumerate the
HUIs any more (PHASE H aborted at 600 s / 10^6 HUIs): a dense group of APs
that are detected together yields every one of its large subsets as a HUI.
The union, however, only needs ONE HUI per AP. This module therefore runs the
EFIM depth-first search (items in increasing TWU order, the same three upper
bounds) with one extra, exact pruning rule:

    covering rule - once every item of a node's prefix is known to be in the
    union, its subtree is explored only if it can still produce a HUI that
    contains an item NOT yet in the union. The bound used is the local
    utility restricted to the transactions holding such an item:
        sum over T containing alpha and some uncovered v in E of
            u(alpha,T) + sum_{w in E} u(w,T)
    which is >= u(X) for every X in the subtree that contains an uncovered v.

EFIM's own bounds (TWU, local utility lu, sub-tree utility su) prune exactly
as in efim.py, so a subtree is skipped only when it cannot contain a HUI that
would add an item to the union: the result is the exact union, identical to
the union of the HUIs EFIM would output (verified against every EFIM run that
completed - src/check_union_search.py).

Thresholds are processed from the highest down; union(high) is contained in
union(low), so the items found at one level start out covered at the next.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np


@dataclass
class UnionLevels:
    thresholds: np.ndarray      # (K,) absolute minUtil, descending
    member: np.ndarray          # (m, K) bool: item i in the union at threshold k
    witness_util: np.ndarray    # (m, K) utility of the HUI that put i there
    nodes: np.ndarray           # (K,) search nodes visited per threshold
    seconds: np.ndarray         # (K,) wall-clock per threshold
    total_utility: float

    def union(self, k: int) -> np.ndarray:
        return np.flatnonzero(self.member[:, k])


class TimeLimit(Exception):
    """The search hit its wall-clock budget: `covered` is then only a subset
    of the union (every item in it has a real witness), never a guess."""


def _union_at(U: np.ndarray, mu: float, covered: np.ndarray,
              wutil: np.ndarray, time_limit_s: float | None = None) -> int:
    """Covering search at one absolute minUtil; updates `covered` / `wutil` in
    place and returns the number of search nodes. Raises TimeLimit (with the
    node count in .args[0]) if `time_limit_s` is exceeded."""
    t_start = time.perf_counter()
    present = U > 0
    tu = U.sum(axis=1)
    twu = present.T.astype(np.float64) @ tu
    items = np.flatnonzero(twu >= mu)                    # TWU pruning
    if not len(items):
        return 0
    items = items[np.argsort(twu[items], kind="stable")]  # EFIM order: TWU up
    P0 = U[:, items]
    keep = P0.any(axis=1)
    P0 = P0[keep]
    n_nodes = [0]

    def cover(alpha, cols, uc):
        hit = uc >= mu
        if not hit.any():
            return
        for c, v in zip(cols[hit], uc[hit]):
            if not covered[c]:
                covered[c] = True
                wutil[c] = v
        top = float(uc[hit].max())
        for a in alpha:
            if not covered[a]:
                covered[a] = True
                wutil[a] = top

    def rec(alpha, ua, P, cols):
        n_nodes[0] += 1
        if time_limit_s is not None and n_nodes[0] % 2000 == 0 and                 time.perf_counter() - t_start > time_limit_s:
            raise TimeLimit(n_nodes[0])
        occ = P > 0
        lu = occ.T.astype(np.float64) @ (ua + P.sum(axis=1))
        k_ok = lu >= mu                                  # local-utility pruning
        if not k_ok.any():
            return
        if alpha and all(covered[a] for a in alpha) and not (
                k_ok & ~covered[cols]).any():
            # covering rule, per item: every itemset here that would add an
            # uncovered v to the union has u <= lu(alpha, v) < minUtil
            return
        if not k_ok.all():
            P, occ, cols = P[:, k_ok], occ[:, k_ok], cols[k_ok]
        uc = occ.T.astype(np.float64) @ ua + P.sum(axis=0)   # u(alpha + z)
        cover(alpha, cols, uc)
        cs = np.cumsum(P[:, ::-1], axis=1)[:, ::-1]           # sum_{v >= k}
        su = (occ * (ua[:, None] + cs)).sum(axis=0)          # sub-tree utility
        alpha_unc = any(not covered[a] for a in alpha)
        for k in range(len(cols) - 1):                       # last one: a leaf
            if su[k] < mu:
                continue
            r = occ[:, k]
            P2 = P[r][:, k + 1:]
            nz = P2.any(axis=0)
            if not nz.any():
                continue
            P2, c2 = P2[:, nz], cols[k + 1:][nz]
            ua2 = ua[r] + P[r, k]
            if not (alpha_unc or not covered[cols[k]]):
                # covering rule: only HUIs with a still-uncovered item matter
                unc = ~covered[c2]
                if not unc.any():
                    continue
                ru = (P2[:, unc] > 0).any(axis=1)
                if (ua2[ru] + P2[ru].sum(axis=1)).sum() < mu:
                    continue
            rec(alpha + (int(cols[k]),), ua2, P2, c2)

    rec((), np.zeros(len(P0)), P0, items)
    return n_nodes[0]


def union_levels(U: np.ndarray, thresholds, log=None) -> UnionLevels:
    """U: (transactions x items) utility matrix u(i,T) = q(i,T) p(i), 0 = absent.
    thresholds: absolute minUtil values (any order)."""
    U = np.asarray(U, dtype=np.float64)
    th = np.sort(np.asarray(thresholds, dtype=np.float64))[::-1]
    m = U.shape[1]
    covered = np.zeros(m, bool)
    wutil = np.zeros(m)
    member = np.zeros((m, len(th)), bool)
    wu = np.zeros((m, len(th)))
    nodes = np.zeros(len(th), np.int64)
    secs = np.zeros(len(th))
    total = float(U.sum())
    for k, mu in enumerate(th):
        t0 = time.perf_counter()
        nodes[k] = _union_at(U, mu, covered, wutil)
        secs[k] = time.perf_counter() - t0
        member[:, k] = covered
        wu[:, k] = wutil
        if log:
            log.info("  union at %.4f%% of total utility: %d items, %d nodes, %.1fs",
                     100 * mu / total, covered.sum(), nodes[k], secs[k])
    return UnionLevels(th, member, wu, nodes, secs, total)
