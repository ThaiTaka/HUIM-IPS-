"""Correctness of huim/union_search.py: the HUI union without enumerating HUIs.

The union at minUtil is compared with the union of `brute_force_hui` (the raw
definition, no pruning) on random databases, including dense ones where many
items co-occur - the regime where the covering rule prunes most. Every
threshold of a database is checked, both through union_levels (all levels,
carry-over between them) and through _union_at on one level alone.

Run:  python -m pytest tests/test_union_search.py -q
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from huim.brute_force import brute_force_hui, total_utility    # noqa: E402
from huim.union_search import _union_at, union_levels         # noqa: E402


def random_db(seed: int, n_tx: int, n_items: int, density: float):
    rng = random.Random(seed)
    db = []
    for _ in range(n_tx):
        t = {i: rng.randint(1, 10) for i in range(n_items) if rng.random() < density}
        if t:
            db.append(t)
    p = {i: round(rng.uniform(0.2, 3.0), 3) for i in range(n_items)}
    return db, p


def matrix(db, p, n_items):
    U = np.zeros((len(db), n_items))
    for r, t in enumerate(db):
        for i, q in t.items():
            U[r, i] = q * p[i]
    return U


CASES = [(s, n_tx, n_it, dens) for s in range(6)
         for (n_tx, n_it, dens) in ((12, 7, 0.4), (25, 9, 0.6), (30, 10, 0.85))]


@pytest.mark.parametrize("seed,n_tx,n_items,density", CASES)
def test_union_equals_brute_force(seed, n_tx, n_items, density):
    db, p = random_db(seed, n_tx, n_items, density)
    U = matrix(db, p, n_items)
    total = total_utility(db, p)
    assert abs(U.sum() - total) < 1e-9
    fracs = [0.02, 0.05, 0.1, 0.2, 0.35, 0.5]
    R = union_levels(U, [total * f for f in fracs])
    for k, mu in enumerate(R.thresholds):
        want = {i for x, _u, _s in brute_force_hui(db, p, mu) for i in x}
        assert set(R.union(k).tolist()) == want, (seed, mu)
        cov, wu = np.zeros(n_items, bool), np.zeros(n_items)
        _union_at(U, mu, cov, wu)
        assert set(np.flatnonzero(cov).tolist()) == want, ("single level", seed, mu)
        # every covered item carries the utility of a real witness HUI
        assert (wu[cov] >= mu - 1e-9).all()


def test_union_is_monotone_in_minutil():
    db, p = random_db(42, 40, 11, 0.7)
    U = matrix(db, p, 11)
    total = U.sum()
    R = union_levels(U, [total * f for f in np.linspace(0.01, 0.6, 12)])
    M = R.member                                  # thresholds descending
    assert (M[:, 1:] >= M[:, :-1]).all()
