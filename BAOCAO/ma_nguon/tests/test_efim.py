"""PHASE F - correctness of the EFIM implementation.

Strategy: EFIM is never trusted on its own output. Every test compares it with
`brute_force_hui`, which implements the raw definition with no pruning. Because
the two share no code path beyond the database format, agreement is meaningful.

Additionally, two utility values in `test_running_example_hand_computed` are
computed by hand below, so that the case "both implementations are wrong in the
same way" is also covered.

Run:  python -m pytest tests -q        (or)   python tests/test_efim.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from huim.brute_force import (brute_force_hui, itemset_utility, total_utility,
                              transaction_utility, twu)
from huim.efim import EFIM, ResourceLimitExceeded, mine_efim

# ---------------------------------------------------------------------------
# The running example used across the HUIM literature (Zida et al. 2017,
# Fournier-Viger et al. 2014, Liu & Qu 2012 all use this database).
# ---------------------------------------------------------------------------
RUNNING_DB = [
    {"a": 1, "c": 1, "d": 1},
    {"a": 2, "c": 6, "e": 2, "g": 5},
    {"a": 1, "b": 2, "c": 1, "d": 6, "e": 1, "f": 5},
    {"b": 4, "c": 3, "d": 3, "e": 1},
    {"b": 2, "c": 2, "e": 1, "g": 2},
]
RUNNING_P = {"a": 5, "b": 2, "c": 1, "d": 2, "e": 3, "f": 1, "g": 1}


def _norm(res):
    """Canonical comparable form: {frozenset(itemset): utility}."""
    return {frozenset(x): round(float(u), 9) for x, u, _s in res}


# ---------------------------------------------------------------------- basics
def test_transaction_and_total_utility():
    # TU(T1) = 1*5 + 1*1 + 1*2 = 8, by hand.
    assert transaction_utility(RUNNING_DB[0], RUNNING_P) == 8
    # TU over the five transactions: 8 + 27 + 30 + 20 + 11 = 96, by hand.
    expected = [8, 27, 30, 20, 11]
    assert [transaction_utility(t, RUNNING_P) for t in RUNNING_DB] == expected
    assert total_utility(RUNNING_DB, RUNNING_P) == 96


def test_twu_is_an_upper_bound_on_utility_of_supersets():
    """The property that makes TWU usable for pruning: for any itemset X and
    any item i in X, u(X) <= TWU(i). Checked exhaustively on the example."""
    items = sorted(RUNNING_P)
    from itertools import combinations
    for k in range(1, len(items) + 1):
        for combo in combinations(items, k):
            u = itemset_utility(combo, RUNNING_DB, RUNNING_P)
            for i in combo:
                assert u <= twu(i, RUNNING_DB, RUNNING_P) + 1e-9, (combo, i)


def test_utility_is_not_anti_monotonic():
    """A concrete counter-example, which is the whole reason TWU exists:
    a subset can have LOWER utility than its superset."""
    sub = itemset_utility(("b",), RUNNING_DB, RUNNING_P)
    sup = itemset_utility(("b", "d"), RUNNING_DB, RUNNING_P)
    assert sub == 16 and sup == 30
    assert sup > sub, "superset utility must be able to exceed subset utility"
    # ... and it is not monotonic either: adding an item can lower utility,
    # because the itemset then occurs in fewer transactions.
    assert itemset_utility(("b", "d", "f"), RUNNING_DB, RUNNING_P) < sup


def test_running_example_hand_computed():
    """Two utilities derived by hand, independent of either implementation.

    {b,d} occurs in T3 and T4 only.
        u({b,d},T3) = 2*2 + 6*2 = 16 ; u({b,d},T4) = 4*2 + 3*2 = 14 ; u = 30
    {b,c,d,e} occurs in T3 and T4 only.
        T3: 2*2 + 1*1 + 6*2 + 1*3 = 20 ; T4: 4*2 + 3*1 + 3*2 + 1*3 = 20 ; u = 40
    """
    assert itemset_utility(("b", "d"), RUNNING_DB, RUNNING_P) == 30
    assert itemset_utility(("b", "c", "d", "e"), RUNNING_DB, RUNNING_P) == 40
    huis, _ = mine_efim(RUNNING_DB, RUNNING_P, min_util=30)
    got = _norm(huis)
    assert got[frozenset("bd")] == 30
    assert got[frozenset("bcde")] == 40


@pytest.mark.parametrize("min_util", [1, 5, 10, 15, 20, 25, 29, 30, 31, 40,
                                      50, 60, 90, 96, 97, 200])
def test_running_example_matches_brute_force(min_util):
    huis, stats = mine_efim(RUNNING_DB, RUNNING_P, min_util=min_util)
    exp = brute_force_hui(RUNNING_DB, RUNNING_P, min_util)
    assert _norm(huis) == _norm(exp), f"min_util={min_util}"
    assert stats.status == "COMPLETED"
    assert stats.total_db_utility == 96


def test_support_is_exact_despite_transaction_merging():
    huis, _ = mine_efim(RUNNING_DB, RUNNING_P, min_util=1)
    exp = {frozenset(x): s for x, _u, s in
           brute_force_hui(RUNNING_DB, RUNNING_P, 1)}
    got = {frozenset(x): s for x, _u, s in huis}
    assert got == exp


# ------------------------------------------------------------ randomised tests
def _random_db(rng: random.Random, n_tx: int, n_items: int,
               max_q: int = 8, max_p: int = 9, density: float = 0.5):
    items = [f"i{k}" for k in range(n_items)]
    p = {i: rng.randint(1, max_p) for i in items}
    db = []
    for _ in range(n_tx):
        t = {i: rng.randint(1, max_q) for i in items if rng.random() < density}
        if t:
            db.append(t)
    return db, p


@pytest.mark.parametrize("seed", list(range(40)))
def test_random_databases_match_brute_force(seed):
    """40 independent random utility databases, each checked at several
    thresholds expressed as a fraction of the database's total utility."""
    rng = random.Random(seed)
    n_items = rng.randint(3, 11)
    n_tx = rng.randint(1, 25)
    density = rng.choice([0.2, 0.4, 0.6, 0.85])
    db, p = _random_db(rng, n_tx, n_items, density=density)
    if not db:
        pytest.skip("degenerate empty database")
    tot = total_utility(db, p)
    for frac in (0.9, 0.5, 0.25, 0.1, 0.02):
        mu = max(1.0, tot * frac)
        huis, stats = mine_efim(db, p, min_util=mu)
        exp = brute_force_hui(db, p, mu)
        assert _norm(huis) == _norm(exp), (
            f"seed={seed} n_items={n_items} n_tx={n_tx} density={density} "
            f"min_util={mu}")
        assert stats.status == "COMPLETED"
        assert abs(stats.total_db_utility - tot) < 1e-9


@pytest.mark.parametrize("seed", list(range(15)))
def test_random_sparse_wide_like_wifi(seed):
    """Shape closer to UJIIndoorLoc: many items, few per transaction."""
    rng = random.Random(1000 + seed)
    db, p = _random_db(rng, n_tx=rng.randint(5, 30), n_items=14,
                       density=0.18)
    if not db:
        pytest.skip("degenerate empty database")
    tot = total_utility(db, p)
    for frac in (0.4, 0.15, 0.05):
        mu = max(1.0, tot * frac)
        huis, _ = mine_efim(db, p, min_util=mu)
        assert _norm(huis) == _norm(brute_force_hui(db, p, mu))


def test_float_utilities_match_brute_force():
    """Model B uses non-integer external utilities, so floats must work too."""
    rng = random.Random(7)
    db, _ = _random_db(rng, 18, 9, density=0.5)
    p = {f"i{k}": round(rng.uniform(0.05, 3.0), 4) for k in range(9)}
    tot = total_utility(db, p)
    for frac in (0.5, 0.2, 0.05):
        mu = tot * frac
        huis, _ = mine_efim(db, p, min_util=mu)
        assert _norm(huis) == _norm(brute_force_hui(db, p, mu))


# ------------------------------------------------------------------ edge cases
def test_empty_database():
    huis, stats = mine_efim([], {}, min_util=1)
    assert huis == [] and stats.n_huis == 0


def test_single_transaction_all_subsets():
    db = [{"x": 2, "y": 3}]
    p = {"x": 1, "y": 1}
    huis, _ = mine_efim(db, p, min_util=1)
    assert _norm(huis) == _norm(brute_force_hui(db, p, 1))
    assert _norm(huis) == {frozenset("x"): 2.0, frozenset("y"): 3.0,
                           frozenset("xy"): 5.0}


def test_threshold_above_total_utility_returns_nothing():
    huis, stats = mine_efim(RUNNING_DB, RUNNING_P, min_util=97)
    assert huis == []
    assert stats.n_items_after_twu_pruning == 0


def test_rejects_non_positive_utilities():
    with pytest.raises(ValueError):
        EFIM(min_util=1).mine([{"a": 1}], {"a": 0})
    with pytest.raises(ValueError):
        EFIM(min_util=1).mine([{"a": 0}], {"a": 1})
    with pytest.raises(ValueError):
        EFIM(min_util=1).mine([{"a": -3}], {"a": 2})


def test_rejects_item_without_external_utility():
    with pytest.raises(KeyError):
        EFIM(min_util=1).mine([{"a": 1, "b": 1}], {"a": 1})


def test_controlled_abort_on_output_limit():
    eng = EFIM(min_util=1, max_huis=3, check_every_nodes=1)
    with pytest.raises(ResourceLimitExceeded):
        eng.mine(RUNNING_DB, RUNNING_P)
    assert eng.stats.status == "ABORTED_RESOURCE_LIMIT"
    assert eng.stats.abort_reason and "output limit" in eng.stats.abort_reason
    # the wrapper must degrade gracefully rather than lose the run
    huis, stats = mine_efim(RUNNING_DB, RUNNING_P, min_util=1, max_huis=3)
    assert stats.status == "ABORTED_RESOURCE_LIMIT"
    assert 0 < len(huis) <= 4


def test_controlled_abort_on_time_limit():
    rng = random.Random(3)
    db, p = _random_db(rng, 400, 22, density=0.6)
    huis, stats = mine_efim(db, p, min_util=1, time_limit_s=0.05)
    assert stats.status in ("COMPLETED", "ABORTED_RESOURCE_LIMIT")
    if stats.status == "ABORTED_RESOURCE_LIMIT":
        assert "time limit" in (stats.abort_reason or "")


def test_pruning_actually_happens():
    """If no pruning occurred the implementation would be brute force wearing a
    costume, so assert the counters move on a threshold that must prune."""
    # At minUtil=30 every item still has TWU >= 30 (TWU(f)=TU(T3)=30,
    # TWU(g)=TU(T2)+TU(T5)=38), so root TWU pruning correctly removes nothing.
    _huis, s30 = mine_efim(RUNNING_DB, RUNNING_P, min_util=30)
    assert s30.n_items_after_twu_pruning == s30.n_items_initial == 7
    assert s30.n_candidates_pruned_by_su > 0
    # At minUtil=40, TWU(f)=30 < 40, so the root bound must drop item f.
    _huis, s40 = mine_efim(RUNNING_DB, RUNNING_P, min_util=40)
    assert s40.n_items_after_twu_pruning < s40.n_items_initial
    # Search must be far smaller than enumerating the whole lattice.
    for s in (s30, s40):
        assert s.n_nodes_visited < 2 ** s.n_items_initial
        assert s.n_items_pruned_by_lu > 0 or s.n_candidates_pruned_by_su > 0


def test_merging_reduces_transactions_when_duplicates_exist():
    db = [{"a": 1, "b": 1}] * 6 + [{"a": 2, "b": 2}] * 4
    p = {"a": 1, "b": 1}
    _huis, stats = mine_efim(db, p, min_util=1)
    assert stats.n_transactions_saved_by_merging > 0
    # and the answer is still exact
    huis, _ = mine_efim(db, p, min_util=1)
    assert _norm(huis) == _norm(brute_force_hui(db, p, 1))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
