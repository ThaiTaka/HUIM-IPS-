"""PHASE Z - zone-wise mining checked against the brute-force oracle."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

import huim_zone as hz
from huim.brute_force import brute_force_hui, total_utility


def _db(seed, n=40, items=7):
    rng = random.Random(seed)
    return [{f"W{j}": rng.randint(1, 9) for j in range(items) if rng.random() < 0.45}
            for _ in range(n)]


def test_zone_union_equals_brute_force_per_zone():
    p = {f"W{j}": 1.0 + j / 10 for j in range(7)}
    for seed in range(12):
        db = _db(seed)
        zones = np.array(["z0" if i % 3 else "z1" for i in range(len(db))])
        runs = hz.mine_all_zones(db, zones, p, 12.0)
        expect = set()
        for z in ("z0", "z1"):
            dz = [t for t, l in zip(db, zones) if l == z and t]
            mu = total_utility(dz, p) * 12.0 / 100
            expect |= {w for x, _u, _s in brute_force_hui(dz, p, mu) for w in x}
            r = next(r for r in runs if r.zone == z)
            assert abs(r.abs_minutil - mu) < 1e-9
            for wt in r.witnesses:
                assert wt["utility"] >= mu and wt["wap"] in wt["items"]
        assert set(hz.union_waps(runs, sorted(p))) == expect


def test_escalation_keeps_a_complete_run(monkeypatch):
    monkeypatch.setattr(hz, "MAX_HUIS", 3)
    db = _db(1, n=60)
    p = {f"W{j}": 1.0 for j in range(7)}
    r = hz.mine_zone("z", db, p, 5.0)
    assert r.status == "COMPLETED" and r.n_attempts > 1
    assert abs(r.theta_used - 5.0 * hz.ESCALATE ** (r.n_attempts - 1)) < 1e-9
    assert r.n_huis <= 3


def test_cache_reuses_smallest_completed_run(monkeypatch):
    monkeypatch.setattr(hz, "MAX_HUIS", 3)
    db = _db(2, n=60)
    p = {f"W{j}": 1.0 for j in range(7)}
    zones = np.array(["z"] * len(db))
    c = hz.ZoneCache()
    first = hz.mine_all_zones(db, zones, p, 6.0, c)[0]
    assert first.n_attempts > 1 and first.status == "COMPLETED"
    again = hz.mine_all_zones(db, zones, p, 5.0, c)[0]
    assert again.n_attempts == 0 and again.waps == first.waps
    assert again.theta_used == first.theta_used and again.theta_requested == 5.0


def test_single_floor_sites_get_spatial_zones():
    df = pd.DataFrame({"BUILDINGID": 0, "FLOOR": 0,
                       "X": np.repeat(np.arange(20.0), 3), "Y": 0.0})
    z, rule = hz.zone_labels(df)
    assert len(set(z)) == hz.N_SPATIAL_ZONES and "k-means" in rule
    df2 = df.assign(FLOOR=np.arange(len(df)) % 2)
    z2, _ = hz.zone_labels(df2)
    assert set(z2) == {"0_0", "0_1"}
