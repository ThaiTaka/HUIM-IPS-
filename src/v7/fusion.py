"""V7-A: adaptive fusion of the HUI candidate cells.

Input per query: the 30 candidate cells (centres `cxy`), the V6 HUI re-ranker's predicted ground distance
`p` of each candidate to the truth (derived from HUI evidence only), and optionally the HUI matching
score of each candidate. Output: weights (non-negative, sum 1) and the weighted centre.

Rules (all return (xy, w) with w of shape (n,30), zero outside the fused set):
  v6        top m by p, w ~ exp(-(p - pmin)/T)                       (V6: m=20, T=2)
  cut       every candidate with p - pmin <= delta (at most m)        adaptive number of cells
  adaptT    T = T0 * (1 + c * pmin)  - softer weights when the best predicted distance is large
  cluster   keep the cluster (radius r around the cell with the largest softmax mass) with the strongest evidence
  floorS    drop candidates whose relative HUI score S/S_top1 < s_min (limit weak-evidence cells)
"""
from __future__ import annotations

import numpy as np


def _w(p: np.ndarray, T, mask: np.ndarray) -> np.ndarray:
    """softmax(-p / T) over the masked candidates; T scalar or one value per query."""
    T = np.broadcast_to(np.asarray(T, np.float64), (len(p),))[:, None]
    a = -(p - np.where(mask, p, np.inf).min(1, keepdims=True)) / T
    w = np.where(mask, np.exp(np.clip(a, -700, 0)), 0.0)
    return w / w.sum(1, keepdims=True)


def _topm(p: np.ndarray, m: int) -> np.ndarray:
    o = np.argsort(p, 1)[:, :m]
    mk = np.zeros(p.shape, bool)
    np.put_along_axis(mk, o, True, 1)
    return mk


def _xy(w: np.ndarray, cxy: np.ndarray) -> np.ndarray:
    return np.einsum("ij,ijk->ik", w, cxy)


def fuse(p, cxy, rule: str, S_rel=None, gf: float = 0.766126, **kw):
    n, K = p.shape
    m = kw.get("m", 20)
    if rule == "v6":
        w = _w(p, kw["T"], _topm(p, m))
    elif rule == "cut":
        mk = _topm(p, m) & (p - p.min(1, keepdims=True) <= kw["delta"])
        w = _w(p, kw["T"], mk)
    elif rule == "adaptT":
        T = kw["T0"] * (1.0 + kw["c"] * p.min(1))
        w = _w(p, T, _topm(p, m))
    elif rule == "floorS":
        mk = _topm(p, m) & (S_rel >= kw["s_min"])
        mk[np.arange(n), p.argmin(1)] = True
        w = _w(p, kw["T"], mk)
    elif rule == "cluster":
        w0 = _w(p, kw["T"], _topm(p, m))
        D = np.sqrt(((cxy[:, :, None] - cxy[:, None]) ** 2).sum(-1)) * gf        # (n,K,K) metres
        near = D <= kw["r"]
        mass = np.einsum("ij,ikj->ik", w0, near.astype(w0.dtype))                # softmax mass within r of each cell
        c = mass.argmax(1)
        mk = near[np.arange(n), c] & (w0 > 0)
        w = _w(p, kw["T"], mk)
    else:
        raise ValueError(rule)
    return _xy(w, cxy), w
