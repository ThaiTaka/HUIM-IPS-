"""Tests of the V7 modules (src/v7): fusion invariants, direct-scorer gradients, cache provenance,
fold separation, no k-NN in the positioning code, and EFIM exactness on real cell data.

Run:  python -m pytest tests/test_v7.py -q
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from v7.direct import DirectScorer, fit_members, predict_members  # noqa: E402
from v7.fusion import fuse  # noqa: E402

TRAIN = ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv"
RULES = [dict(rule="v6", m=20, T=2.0), dict(rule="cut", m=30, T=1.0, delta=6.0),
         dict(rule="adaptT", m=20, T0=0.5, c=0.4), dict(rule="floorS", m=20, T=1.5, s_min=0.2),
         dict(rule="cluster", m=30, T=2.0, r=8.0)]


def _synthetic(n=64, K=30, seed=0):
    r = np.random.default_rng(seed)
    # Web-Mercator magnitudes, where float32 weights would lose metres
    cxy = np.stack([-7.6e3 + r.uniform(0, 200, (n, K)), 4.865e6 + r.uniform(0, 200, (n, K))], -1)
    return np.abs(r.standard_normal((n, K))) * 10, cxy, r.uniform(0, 1, (n, K))


@pytest.mark.parametrize("kw", RULES, ids=[k["rule"] for k in RULES])
def test_fusion_weights_valid_and_position_is_weighted_centre(kw):
    p, cxy, S_rel = _synthetic()
    xy, w = fuse(p, cxy, S_rel=S_rel, **kw)
    assert np.isfinite(xy).all() and np.isfinite(w).all()
    assert (w >= 0).all()
    assert np.abs(w.sum(1) - 1).max() < 1e-12
    assert np.abs(xy - np.einsum("ij,ijk->ik", w, cxy)).max() < 1e-6


def test_fusion_degenerate_ties_are_finite_and_deterministic():
    p = np.full((3, 30), 5.0)
    cxy = np.tile(np.arange(30.0)[None, :, None], (3, 1, 2))
    a, b = fuse(p, cxy, rule="v6", m=20, T=2.0), fuse(p, cxy, rule="v6", m=20, T=2.0)
    assert np.isfinite(a[0]).all() and np.array_equal(a[1], b[1])


def test_v6_rule_matches_v6_place_up_to_its_float32_noise():
    from huim_rerank_final import place
    p, cxy, _ = _synthetic()
    xy6, o, w6 = place(p.astype(np.float32), cxy)
    xy7, w7 = fuse(p.astype(np.float32).astype(np.float64), cxy, rule="v6", m=20, T=2.0)
    assert np.abs(np.take_along_axis(w7, o, 1) - w6).max() < 1e-5
    assert np.abs(xy6 - xy7).max() < 3.0      # V6's float32 weights move the centre by up to ~1 coordinate unit


def test_direct_scorer_gradient_matches_finite_differences():
    r = np.random.default_rng(1)
    B, K, F = 5, 7, 6
    X, C = r.standard_normal((B, K, F)), r.standard_normal((B, K, 2)) * 10
    t, d = r.standard_normal((B, 2)) * 5, np.abs(r.standard_normal((B, K))) * 10
    m = DirectScorer(F, 8, 4, seed=2)
    m.P["w3"] = r.standard_normal(4)
    kw = dict(lam_aux=0.3, ent=0.2)
    _, G = m.loss_grad(X, C, t, d, **kw)
    worst = 0.0
    for k, p in m.P.items():
        flat = p.reshape(-1)
        for i in r.choice(flat.size, min(6, flat.size), replace=False):
            o = flat[i]
            flat[i] = o + 1e-6
            lp = m.loss_grad(X, C, t, d, **kw)[0]
            flat[i] = o - 1e-6
            lm = m.loss_grad(X, C, t, d, **kw)[0]
            flat[i] = o
            num, an = (lp - lm) / 2e-6, G[k].reshape(-1)[i]
            worst = max(worst, abs(num - an) / (abs(num) + abs(an) + 1e-9))
    assert worst < 1e-5


def test_direct_prediction_is_convex_combination_of_candidates():
    r = np.random.default_rng(3)
    X, C = r.standard_normal((20, 30, 5)), r.standard_normal((20, 30, 2)) * 50
    xp, w = DirectScorer(5, 8, 4, seed=0).predict(X, C)
    assert np.isfinite(xp).all() and (w >= 0).all() and np.abs(w.sum(1) - 1).max() < 1e-12
    assert np.abs(xp - np.einsum("ij,ijk->ik", w, C)).max() < 1e-9
    assert (xp >= C.min(1) - 1e-9).all() and (xp <= C.max(1) + 1e-9).all()


def test_direct_training_reduces_the_loss_on_learnable_data():
    r = np.random.default_rng(4)
    n, K, F = 400, 10, 4
    C = r.uniform(0, 100, (n, K, 2))
    best = r.integers(0, K, n)
    X = r.standard_normal((n, K, F))
    X[np.arange(n), best, 0] += 3.0                       # feature 0 marks the candidate nearest the truth
    t = C[np.arange(n), best]
    m = DirectScorer(F, 16, 8, seed=0)
    m.mu, m.sd = X.reshape(-1, F).mean(0), X.reshape(-1, F).std(0)
    before = m.loss_grad(m._norm(X), C, t)[0]
    m.fit(X, C, t, epochs=40, batch=32, lr=1e-2)
    assert m.loss_grad(m._norm(X), C, t)[0] < 0.3 * before


def test_ensemble_members_never_see_their_evaluation_fold():
    r = np.random.default_rng(5)
    data = [{"X": r.standard_normal((30, 6, 4)).astype(np.float32), "C": r.standard_normal((30, 6, 2)),
             "t": r.standard_normal((30, 2)), "dist": np.abs(r.standard_normal((30, 6))),
             "keep": np.ones(30, bool)} for _ in range(4)]
    seen, orig = [], DirectScorer.fit

    def spy(self, X, C, t, dist=None, Xv=None, *a, **k):
        seen.append(X.shape[0] + Xv.shape[0])
        return orig(self, X, C, t, dist, Xv, *a, **k)

    DirectScorer.fit = spy
    try:
        members = fit_members(data, [0, 1, 2], dict(h1=4, h2=4, ep=1), seed=0)   # fold 3 = held-out evaluation fold
    finally:
        DirectScorer.fit = orig
    assert len(members) == 3 and all(n == 90 for n in seen)                     # 3 folds x 30 queries, never 4
    xp, w = predict_members(members, data[3]["X"], data[3]["C"])
    assert xp.shape == (30, 2) and np.abs(w.sum(1) - 1).max() < 1e-12


@pytest.mark.skipif(not TRAIN.exists(), reason="dataset not available")
def test_cache_metadata_is_enforced(tmp_path, monkeypatch):
    import v7.common as c
    monkeypatch.setattr(c, "CACHE", tmp_path)
    c.save_cache("x", c.base_meta(kind="t", fold=3), a=np.arange(3))
    assert c.load_cache("x", {"fold": 3})["a"].tolist() == [0, 1, 2]
    with pytest.raises(RuntimeError, match="does not match"):
        c.load_cache("x", {"fold": 4})
    m = json.load(open(tmp_path / "x.meta.json"))
    m["train_csv_sha256"] = "0" * 64
    json.dump(m, open(tmp_path / "x.meta.json", "w"))
    with pytest.raises(RuntimeError, match="different trainingData"):
        c.load_cache("x")


def test_no_knn_or_raw_fingerprint_matching_in_v7_positioning_code():
    banned = ("KNeighbors", "NearestNeighbors", "sklearn.neighbors", "cKDTree", "KDTree", "BallTree", "cdist",
              "pairwise_distances")
    for f in (ROOT / "src" / "v7").glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
                {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        text = " ".join(names | mods)
        assert not any(b in text for b in banned), f"{f.name} references a neighbour-search facility"


@pytest.mark.skipif(not TRAIN.exists(), reason="dataset not available")
def test_dev_folds_are_disjoint_by_phone():
    from multi_datasets import load
    from run_huim_only import folds_for
    b = load("uji")
    ph = b.train["PHONEID"].to_numpy()
    seen = set()
    for tri, dvi in folds_for(b, len(b.train)):
        assert not set(ph[tri]) & set(ph[dvi])
        assert not set(tri) & set(dvi) and not set(dvi) & seen
        seen |= set(dvi)
    assert len(seen) == len(b.train)


@pytest.mark.skipif(not TRAIN.exists(), reason="dataset not available")
def test_efim_equals_brute_force_on_real_cell_transactions():
    """EFIM on the rank-utility transactions of real cells, restricted to the 11 most frequent APs so the
    exhaustive enumeration (2^11 itemsets) is possible: identical HUIs, utilities and supports."""
    import pandas as pd
    from huim.brute_force import brute_force_hui
    from huim.efim import mine_efim
    from huim_positioning import internal_utility
    df = pd.read_csv(TRAIN)
    Q = internal_utility(df[[c for c in df.columns if c.startswith("WAP")]].to_numpy(float), "rank")
    cells = df.groupby(["BUILDINGID", "FLOOR", "SPACEID", "RELATIVEPOSITION"]).indices
    checked = 0
    for idx in list(cells.values())[:80:8]:
        q = Q[idx]
        top = np.argsort(-(q > 0).sum(0), kind="stable")[:11]
        db = [t for t in ({int(j): float(q[i, j]) for j in top if q[i, j] > 0} for i in range(len(q))) if t]
        if len(db) < 3:
            continue
        p = {int(j): 1.0 for j in top}
        mu = 0.2 * sum(sum(t.values()) for t in db)
        got, _st = mine_efim(db, p, mu)
        ref = brute_force_hui(db, p, mu)
        key = lambda rows: {frozenset(x): (round(u, 6), s) for x, u, s in rows}
        assert key(got) == key(ref) and len(got) > 0
        checked += 1
    assert checked >= 3
