"""PHASE Q - the HUIM-only positioner."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from huim.brute_force import brute_force_hui, total_utility
from huim_positioning import HUIPositioner, Params


def _site(seed=0):
    rng = np.random.default_rng(seed)
    nA, Q, cell, xy, bf = 9, [], [], [], []
    sig = {0: [0, 1, 2], 1: [3, 4, 5], 2: [6, 7, 8]}
    for c in range(3):
        for _ in range(12):
            row = np.zeros(nA)
            for j in sig[c]:
                if rng.random() < 0.9:
                    row[j] = rng.integers(40, 90)
            row[rng.integers(0, nA)] = rng.integers(1, 15)
            Q.append(row); cell.append(c); xy.append([10.0 * c, 0.0]); bf.append(f"0_{c}")
    return np.array(Q), np.array(cell), np.array(xy), np.array(bf)


def test_cell_huis_equal_brute_force():
    Q, cell, xy, bf = _site()
    pos = HUIPositioner(theta=20.0).fit(Q, cell, xy, bf)
    for k, c in enumerate(pos.cells):
        rows = np.flatnonzero(cell == c)
        db = [{int(j): float(Q[i, j]) for j in np.flatnonzero(Q[i])} for i in rows]
        p = {j: 1.0 for j in range(Q.shape[1])}
        mu = total_utility(db, p) * pos.cell_runs[k]["theta_used_pct"] / 100
        want = {frozenset(x): u for x, u, _ in brute_force_hui(db, p, mu)}
        got = {frozenset(pos.hui_items[i]): pos.hui_util[i]
               for i in np.flatnonzero(pos.hui_cell == k)}
        assert got.keys() == want.keys()
        assert all(abs(got[x] - want[x]) < 1e-9 for x in want)


def test_query_lands_in_the_cell_with_its_signature():
    Q, cell, xy, bf = _site()
    pos = HUIPositioner(theta=20.0).fit(Q, cell, xy, bf)
    q = np.zeros((3, Q.shape[1]))
    q[0, [0, 1, 2]] = 70
    q[1, [3, 4]] = 70          # one AP of the signature missing: soft match
    q[2, [6, 7, 8]] = 60
    xy_hat, lab, top, a, sc = pos.predict(q, Params(gamma=1, tau=20, beta=1, m=1, p=1))
    assert list(lab) == ["0_0", "0_1", "0_2"]
    assert np.allclose(xy_hat[:, 0], [0, 10, 20])


def test_weights_sum_to_one_and_position_is_convex():
    Q, cell, xy, bf = _site(3)
    pos = HUIPositioner(theta=20.0).fit(Q, cell, xy, bf)
    xy_hat, _lab, top, a, _ = pos.predict(Q[:5], Params(m=3, p=2))
    assert np.allclose(a.sum(axis=1), 1)
    assert (xy_hat[:, 0] >= 0).all() and (xy_hat[:, 0] <= 20).all()
