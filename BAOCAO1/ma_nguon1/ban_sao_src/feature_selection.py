"""PHASE E - turning a set of High Utility Itemsets into a set of WAPs.

This is the step where HUIM is supposed to *help* the positioning system, so it
has to be stated precisely and it must not be reverse-engineered from accuracy.

Two selection rules are implemented, and both are reported:

`union`
    Every WAP that occurs in at least one mined HUI. This is the honest,
    parameter-free reading of "HUIM selected these APs": the minUtil threshold
    is the only knob. At a high threshold the union is small; as minUtil falls
    the union grows towards every WAP, which is itself one of the findings.

`topn`
    The n highest-ranked WAPs by `utility_contribution`. Needed because the
    union is a step function of minUtil and cannot produce an arbitrary feature
    budget; without it the "feature reduction vs accuracy" curve would have only
    a handful of points.

[DESIGN] The ranking score is

    utility_contribution(i) = sum over HUIs X containing i of  u(X) / |X|

i.e. each HUI divides its utility equally among its members. Chosen before any
accuracy number was computed, for two reasons: it is the only attribution rule
that makes the per-WAP scores sum exactly to the total utility of the HUI set
(so it is a genuine decomposition, not an arbitrary index), and it does not
need a tuning parameter. Alternative statistics (`n_huis`, `max_hui_utility`,
support-weighted variants) are computed and saved alongside so the report can
show they rank WAPs similarly, rather than claiming the chosen one is uniquely
correct.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

import numpy as np


def per_wap_statistics(huis: Sequence[Tuple[Tuple[str, ...], float, int]],
                       top_k: int = 100) -> Dict[str, dict]:
    """Aggregate a HUI set down to per-WAP evidence."""
    stats: Dict[str, dict] = defaultdict(
        lambda: {"n_huis": 0, "utility_contribution": 0.0,
                 "max_hui_utility": 0.0, "sum_hui_utility": 0.0,
                 "support_weighted_contribution": 0.0,
                 "n_top_huis": 0, "min_hui_len": 10 ** 9, "max_hui_len": 0})
    ranked = sorted(huis, key=lambda r: -r[1])
    top_set = {id(r) for r in ranked[:top_k]}
    for rec in huis:
        xs, u, sup = rec
        share = u / len(xs)
        for w in xs:
            s = stats[w]
            s["n_huis"] += 1
            s["utility_contribution"] += share
            s["sum_hui_utility"] += u
            s["max_hui_utility"] = max(s["max_hui_utility"], u)
            s["support_weighted_contribution"] += share * max(sup, 0)
            s["min_hui_len"] = min(s["min_hui_len"], len(xs))
            s["max_hui_len"] = max(s["max_hui_len"], len(xs))
    for rec in ranked[:top_k]:
        for w in rec[0]:
            stats[w]["n_top_huis"] += 1
    out = {}
    for w, s in stats.items():
        s = dict(s)
        if s["min_hui_len"] == 10 ** 9:
            s["min_hui_len"] = 0
        s["mean_hui_utility"] = (s["sum_hui_utility"] / s["n_huis"]
                                 if s["n_huis"] else 0.0)
        out[w] = s
    return out


def select_waps(huis: Sequence[Tuple[Tuple[str, ...], float, int]],
                mode: str = "union", n: int | None = None,
                ) -> Tuple[List[str], Dict[str, dict]]:
    """Returns (selected WAP names sorted by descending score, per-WAP stats)."""
    stats = per_wap_statistics(huis)
    ordered = sorted(stats, key=lambda w: (-stats[w]["utility_contribution"], w))
    if mode == "union":
        return ordered, stats
    if mode == "topn":
        if n is None:
            raise ValueError("mode='topn' requires n")
        return ordered[:n], stats
    raise ValueError(f"unknown selection mode {mode!r}")


def hui_length_distribution(huis: Sequence[Tuple[Tuple[str, ...], float, int]]
                            ) -> Dict[str, object]:
    if not huis:
        return {"n_huis": 0, "by_length": {}, "max_len": 0, "mean_len": 0.0,
                "min_len": 0, "median_len": 0.0,
                "utility_min": None, "utility_max": None,
                "utility_mean": None, "utility_median": None,
                "support_min": None, "support_max": None,
                "support_mean": None}
    lens = np.array([len(x) for x, _u, _s in huis])
    us = np.array([u for _x, u, _s in huis], dtype=np.float64)
    sups = np.array([s for _x, _u, s in huis], dtype=np.float64)
    by_len: Dict[str, int] = {}
    for L, c in zip(*np.unique(lens, return_counts=True)):
        by_len[str(int(L))] = int(c)
    return {
        "n_huis": int(len(huis)),
        "by_length": by_len,
        "max_len": int(lens.max()), "min_len": int(lens.min()),
        "mean_len": round(float(lens.mean()), 4),
        "median_len": float(np.median(lens)),
        "utility_min": float(us.min()), "utility_max": float(us.max()),
        "utility_mean": round(float(us.mean()), 4),
        "utility_median": float(np.median(us)),
        "support_min": float(sups.min()), "support_max": float(sups.max()),
        "support_mean": round(float(sups.mean()), 4),
    }


def feature_reduction_pct(n_selected: int, n_total: int) -> float:
    """(1 - selected/total) x 100, as mandated by the project brief."""
    if n_total <= 0:
        return float("nan")
    return round((1.0 - n_selected / n_total) * 100.0, 4)


def rank_agreement(stats: Dict[str, dict]) -> Dict[str, float]:
    """Spearman rank correlation between the chosen score and the alternatives,
    so the report can say whether the choice of attribution rule matters."""
    from scipy.stats import spearmanr
    waps = sorted(stats)
    if len(waps) < 3:
        return {}
    base = np.array([stats[w]["utility_contribution"] for w in waps])
    out = {}
    for alt in ("n_huis", "max_hui_utility", "mean_hui_utility",
                "support_weighted_contribution", "n_top_huis"):
        v = np.array([stats[w][alt] for w in waps], dtype=np.float64)
        if np.all(v == v[0]):
            out[alt] = float("nan")
            continue
        rho = spearmanr(base, v).statistic
        out[alt] = round(float(rho), 4)
    return out
