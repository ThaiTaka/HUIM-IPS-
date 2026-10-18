"""Brute-force High Utility Itemset enumeration.

This module deliberately contains NO pruning and NO clever data structures. It
is the oracle: it computes the definition straight from the formulas, so that
any disagreement with EFIM is an EFIM bug rather than two implementations of the
same mistake. Exponential by construction - only for toy databases in tests.

Database format used throughout the project
-------------------------------------------
A utility transaction database is a list of dicts:

    D = [ {item: internal_utility_q, ...}, ... ]

plus an external-utility table:

    P = {item: external_utility_p, ...}

with u(i,T) = q(i,T) * p(i). Items absent from a transaction's dict are not in
that transaction (this is how "WAP not detected" is represented).
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, Hashable, Iterable, List, Sequence, Tuple

Item = Hashable
Transaction = Dict[Item, float]
Database = Sequence[Transaction]
ExternalUtility = Dict[Item, float]


def item_utility(item: Item, t: Transaction, p: ExternalUtility) -> float:
    """u(i,T) = q(i,T) x p(i); 0 if the item is not in the transaction."""
    if item not in t:
        return 0.0
    return t[item] * p[item]


def transaction_utility(t: Transaction, p: ExternalUtility) -> float:
    """TU(T) = sum over all items of T of u(i,T)."""
    return sum(q * p[i] for i, q in t.items())


def itemset_utility_in_transaction(x: Iterable[Item], t: Transaction,
                                   p: ExternalUtility) -> float:
    """u(X,T) = sum_{i in X} u(i,T), defined only when X is a subset of T."""
    x = list(x)
    if not all(i in t for i in x):
        return 0.0
    return sum(t[i] * p[i] for i in x)


def itemset_utility(x: Iterable[Item], d: Database,
                    p: ExternalUtility) -> float:
    """u(X) = sum over transactions containing X of u(X,T)."""
    x = list(x)
    total = 0.0
    for t in d:
        if all(i in t for i in x):
            total += sum(t[i] * p[i] for i in x)
    return total


def itemset_support(x: Iterable[Item], d: Database) -> int:
    """|g(X)| - how many transactions contain X. Not used for HUI membership,
    but reported so support and utility can be compared later."""
    x = list(x)
    return sum(1 for t in d if all(i in t for i in x))


def twu(item: Item, d: Database, p: ExternalUtility) -> float:
    """TWU(i) = sum over transactions containing i of TU(T)."""
    return sum(transaction_utility(t, p) for t in d if item in t)


def total_utility(d: Database, p: ExternalUtility) -> float:
    """Sum of TU(T) over the whole database - the base for a relative minUtil."""
    return sum(transaction_utility(t, p) for t in d)


def brute_force_hui(d: Database, p: ExternalUtility, min_util: float,
                    max_len: int | None = None
                    ) -> List[Tuple[Tuple[Item, ...], float, int]]:
    """Every non-empty itemset X over the items that actually occur in D, with
    u(X) >= min_util. Returns (itemset, utility, support) sorted canonically.

    Complexity is O(2^|I| * |D| * |I|). |I| must stay tiny.
    """
    items = sorted({i for t in d for i in t}, key=repr)
    n = len(items)
    if max_len is None:
        max_len = n
    out: List[Tuple[Tuple[Item, ...], float, int]] = []
    for k in range(1, max_len + 1):
        for combo in combinations(items, k):
            u = itemset_utility(combo, d, p)
            if u >= min_util:
                out.append((tuple(combo), u, itemset_support(combo, d)))
    out.sort(key=lambda r: (len(r[0]), [repr(i) for i in r[0]]))
    return out
