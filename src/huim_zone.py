"""PHASE Z - zone-wise High Utility Itemset Mining as the AP selector.

Why mining per zone
-------------------
Mining one database of every fingerprint (PHASE H) ranks itemsets by their
utility over the WHOLE site. On UJIIndoorLoc a building-floor holds about 8% of
the rows, so an AP group that is strong on one floor but invisible elsewhere
never reaches a site-wide minUtil before the itemset count explodes: the
largest uncut union PHASE H could reach was 91 WAPs, and with the PHASE I3
positioner those sets give 17-20 m.

PHASE Z partitions trainingData into zones, mines each zone's transactions
with EFIM, and keeps the union of the per-zone HUI unions:

    zone z          building-floor class (BUILDINGID_FLOOR) when the site has
                    more than one; a single-floor site is split into
                    N_SPATIAL_ZONES k-means clusters of the training positions
    D_z             utility transactions of the training rows in zone z
    minUtil_z       theta% x total utility of D_z   (relative per zone, so a
                    small floor is not out-voted by a large one)
    HUI_z           EFIM(D_z, p, minUtil_z)
    S_z             every WAP occurring in some itemset of HUI_z
    S               union of S_z over all zones  -> the positioning features

Everything here reads trainingData only. The zone label is a training label,
used the same way Model B already uses it; no test row is touched.

Budget
------
Each zone run has the study's per-run budget scaled to a zone (ZONE_TIME_S,
MAX_HUIS). A zone whose run hits it is re-mined at theta x ESCALATE until a run
COMPLETES (above theta = 100% no itemset qualifies, so this terminates), so S_z is always the union of a
complete HUI set - a truncated list is biased by DFS order and is never used.
The theta actually used per zone is recorded.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from huim.efim import mine_efim
from ips_model import RANDOM_SEED

N_SPATIAL_ZONES = 8
ZONE_TIME_S = 120.0
MAX_HUIS = 1_000_000
ESCALATE = 1.25
MAX_ESCALATIONS = 40
N_WITNESS_TOP = 50


def zone_labels(train: pd.DataFrame, x_col: str = "X", y_col: str = "Y"
                ) -> tuple[np.ndarray, str]:
    """Zone of every training row, and a one-line description of the rule."""
    bf = (train["BUILDINGID"].astype(str) + "_"
          + train["FLOOR"].astype(str)).to_numpy()
    if len(set(bf)) > 1:
        return bf, "building-floor class (BUILDINGID_FLOOR)"
    xy = train[[x_col, y_col]].to_numpy(np.float64)
    k = min(N_SPATIAL_ZONES, len(np.unique(xy, axis=0)))
    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_SEED).fit(xy)
    return (np.array([f"Z{c}" for c in km.labels_]),
            f"single floor: {k} k-means clusters of the training positions "
            f"(seed {RANDOM_SEED})")


@dataclass
class ZoneRun:
    zone: str
    n_transactions: int
    n_items: int
    total_utility: float
    theta_requested: float
    theta_used: float
    abs_minutil: float
    n_attempts: int
    n_huis: int
    status: str
    runtime_s: float
    search_nodes: int
    waps: List[str]
    witnesses: List[dict] = field(default_factory=list)
    top_huis: List[dict] = field(default_factory=list)

    def row(self) -> dict:
        return {"zone": self.zone, "n_transactions": self.n_transactions,
                "n_items": self.n_items,
                "total_utility": round(self.total_utility, 6),
                "theta_requested_pct": self.theta_requested,
                "theta_used_pct": round(self.theta_used, 6),
                "abs_minutil": round(self.abs_minutil, 6),
                "n_attempts": self.n_attempts, "n_huis": self.n_huis,
                "status": self.status, "runtime_s": round(self.runtime_s, 4),
                "search_nodes": self.search_nodes,
                "n_waps": len(self.waps)}


def mine_zone(zone: str, txs: Sequence[Dict[str, float]],
              p: Dict[str, float], theta: float) -> ZoneRun:
    txs = [t for t in txs if t]
    total = float(sum(q * p[i] for t in txs for i, q in t.items()))
    th, attempts, spent = theta, 0, 0.0
    while True:
        attempts += 1
        mu = total * th / 100.0
        t0 = time.perf_counter()
        huis, st = mine_efim(txs, p, min_util=mu, time_limit_s=ZONE_TIME_S,
                             max_huis=MAX_HUIS)
        spent += time.perf_counter() - t0
        if st.status == "COMPLETED":
            break
        if attempts > MAX_ESCALATIONS:
            raise RuntimeError(f"zone {zone}: no complete run up to theta {th}%")
        th *= ESCALATE
    best: Dict[str, tuple] = {}
    for xs, u, s in huis:
        for w in xs:
            if w not in best or u > best[w][1]:
                best[w] = (xs, u, s)
    waps = sorted(best)
    wit = [{"wap": w, "items": list(best[w][0]), "utility": float(best[w][1]),
            "support": int(best[w][2])} for w in waps]
    top = sorted(huis, key=lambda r: -r[1])[:N_WITNESS_TOP]
    return ZoneRun(zone, len(txs), len({i for t in txs for i in t}), total,
                   theta, th, total * th / 100.0, attempts, len(huis),
                   st.status, spent, st.n_nodes_visited, waps, wit,
                   [{"items": list(x), "utility": float(u), "support": int(s)}
                    for x, u, s in top])


class ZoneCache:
    """Per zone, across a DESCENDING theta grid: once a zone's run at theta_f
    hit the budget, any request at theta <= theta_f would only fail again and
    escalate back up, so it reuses the zone's smallest COMPLETED run instead.
    Same result as escalating, without paying for the failed attempts again."""

    def __init__(self) -> None:
        self.failed_at: Dict[str, float] = {}
        self.completed: Dict[str, ZoneRun] = {}

    def get(self, zone: str, txs, p, theta: float) -> ZoneRun:
        f = self.failed_at.get(zone)
        if f is not None and theta <= f and zone in self.completed:
            prev = self.completed[zone]
            return ZoneRun(**{**prev.__dict__, "theta_requested": theta,
                              "n_attempts": 0, "runtime_s": 0.0})
        r = mine_zone(zone, txs, p, theta)
        if r.n_attempts > 1:
            self.failed_at[zone] = r.theta_used / ESCALATE
        if r.status == "COMPLETED":
            self.completed[zone] = r
        return r


def mine_all_zones(txs: Sequence[Dict[str, float]], zones: np.ndarray,
                   p: Dict[str, float], theta: float,
                   cache: ZoneCache | None = None) -> List[ZoneRun]:
    cache = cache or ZoneCache()
    out = []
    for z in sorted(set(zones)):
        idx = np.flatnonzero(zones == z)
        out.append(cache.get(z, [txs[i] for i in idx], p, theta))
    return out


def union_waps(runs: Sequence[ZoneRun], wap_order: Sequence[str]) -> List[str]:
    s = set().union(*(r.waps for r in runs)) if runs else set()
    return [w for w in wap_order if w in s]
