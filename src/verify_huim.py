"""Independent check of the mined High Utility Itemsets, straight from the raw
trainingData.csv - so that "EFIM found these HUIs at this minUtil" does not
have to be taken on trust.

Nothing in the checks below calls EFIM or the project's preprocessing / utility
code: q(i,T), p(i) and u(X) are re-implemented here from their definitions,
and the project's own values are then compared against them.

For each of the three runs the charts use (the lowest COMPLETED minUtil per
utility model) it verifies:

  1. threshold   minUtil% x total database utility == abs_minutil recorded in
                 results/metrics/huim_runs.csv
  2. weights     q(i,T) and p(i) re-computed here == the project's values
  3. soundness   every reported itemset X has u(X) >= minUtil, with u(X)
                 re-computed from the transactions containing X
  4. exactness   that recomputed u(X) equals the utility EFIM reported
  5. support     |{T : X subset of T}| equals the support EFIM reported
  6. completeness (lengths 1, 2, 3) - EVERY combination of 1, 2 or 3 detected
                 WAPs is evaluated exhaustively (about 16.8 million itemsets),
                 and exactly those with u(X) >= minUtil must be in the HUI list.
                 This catches an itemset EFIM wrongly pruned.
  7. union       the WAP set used by the positioning experiment
                 (results/metrics/ips_results.csv) is exactly the union of the
                 HUI itemsets.

Model C's richest run kept only its top-1000 HUIs on disk (52,902 HUIs is above
the 50,000 persistence limit), so that run is re-mined here (about 30 s) and the
re-mined list must reproduce the recorded HUI count and WAP union before it is
checked like the others.

Outputs
  results/verification/huim_checks.json         every check, PASS/FAIL, numbers
  results/verification/hui_samples.csv          HUIs with EFIM vs recomputed u(X)
  results/verification/hui_breakdown_<run>.csv  one HUI, transaction by
                                                transaction (for the Excel sheet)
  results/verification/p_values.csv             p(i) per WAP for models A, B, C

Run: python src/verify_huim.py
"""
from __future__ import annotations

import gzip
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import HUI_DIR, METRICS, RESULTS, dump_json, find_dataset, get_logger

LOG = get_logger("verifyhuim", "verify_huim.log")
OUT = RESULTS / "verification"
OUT.mkdir(parents=True, exist_ok=True)

NOT_DETECTED = 100
REL_TOL = 1e-9            # utilities are float sums; compare relatively
# The project's MI adds EPS = 1e-12 to a denominator as a numerical guard; the
# definition implemented here does not, so p(i) agrees to ~1e-9, not exactly.
P_TOL = 1e-6
U_TOL = 1e-7              # relative agreement required of every u(X)
MODEL_CODE = {"A_signal": "A", "B_discriminative": "B",
              "C_rare_discriminative": "C"}


# ------------------------------------------------- independent re-implementation
def q_matrix(W: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """q(i,T) = round(1 + (RSSI - lo)/(hi - lo) * 99) for a detected WAP, 0 if
    the cell is the sentinel 100. Rounded half-to-even like numpy.rint."""
    det = W != NOT_DETECTED
    v = np.clip((W - lo) / (hi - lo), 0.0, 1.0)
    q = np.where(det, np.rint(1.0 + v * 99.0), 0.0)
    q[det & (q < 1)] = 1.0
    return q


def mutual_information_bits(W: np.ndarray, y: np.ndarray) -> np.ndarray:
    """I(A_i;Y) in bits, with A_i in 6 states: 0 = not detected, 1..5 = dBm bins
    (-inf,-90], (-90,-80], (-80,-70], (-70,-60], (-60,0]. Plain counting."""
    det = W != NOT_DETECTED
    state = np.zeros(W.shape, dtype=np.int64)
    for k, edge in enumerate((-90, -80, -70, -60, 0), start=1):
        lower = -np.inf if k == 1 else (-90, -80, -70, -60)[k - 2]
        state[det & (W > lower) & (W <= edge)] = k
    labels, yi = np.unique(y, return_inverse=True)
    n = len(y)
    py = np.bincount(yi, minlength=len(labels)) / n
    out = np.zeros(W.shape[1])
    for j in range(W.shape[1]):
        joint = np.zeros((6, len(labels)))
        np.add.at(joint, (state[:, j], yi), 1.0)
        pj = joint / n
        pa = pj.sum(axis=1)
        mi = 0.0
        for a in range(6):
            for c in range(len(labels)):
                if pj[a, c] > 0:
                    mi += pj[a, c] * math.log2(pj[a, c] / (pa[a] * py[c]))
        out[j] = max(mi, 0.0)
    return out


def p_vector(model: str, W: np.ndarray, y: np.ndarray) -> np.ndarray:
    if model == "A_signal":
        return np.ones(W.shape[1])
    mi = mutual_information_bits(W, y)
    if model == "B_discriminative":
        raw = mi / mi.max()
    else:
        support = (W != NOT_DETECTED).sum(axis=0)
        idf = np.maximum(np.log(len(W) / (1.0 + support)), 0.0)
        raw = mi * idf
        raw = raw / raw.max()
    return np.where(raw <= 0, 1e-6, raw)


def itemset_utility(cols: list[int], D: np.ndarray, U: np.ndarray
                    ) -> tuple[float, int]:
    """u(X) = sum over transactions containing every item of X of
    sum_{i in X} q(i,T) p(i); also returns the support."""
    rows = D[:, cols].all(axis=1)
    return float(U[np.ix_(rows, cols)].sum()), int(rows.sum())


def all_utilities_upto3(D: np.ndarray, U: np.ndarray, items: np.ndarray,
                        min_util: float) -> dict[int, set]:
    """Every itemset of length 1, 2, 3 over `items` with u(X) >= min_util.

    Length 2 uses   u({i,j})   = (U^T D)_ij + (U^T D)_ji
    Length 3 uses, for each i, the transactions T containing i:
                    u({i,j,k}) = sum_T D_Tj D_Tk (U_Ti + U_Tj + U_Tk)
    which is a few matrix products per i instead of 16 million Python loops.
    """
    Ds = D[:, items].astype(np.float64)
    Us = U[:, items]
    m = len(items)
    found = {1: set(), 2: set(), 3: set()}
    u1 = Us.sum(axis=0)
    for a in np.flatnonzero(u1 >= min_util * (1 - REL_TOL)):
        found[1].add((items[a],))
    M = Us.T @ Ds
    U2 = M + M.T
    iu = np.triu_indices(m, k=1)
    for a, b in zip(*[x[U2[iu] >= min_util * (1 - REL_TOL)] for x in iu]):
        found[2].add(tuple(sorted((items[a], items[b]))))
    for a in range(m):
        r = Ds[:, a] > 0
        if not r.any():
            continue
        A = Ds[r]                       # n_a x m
        V = Us[r]                       # n_a x m
        ua = V[:, a]
        # sum_T A_j A_k (u_a + V_j + V_k) for all j, k
        S = (A * ua[:, None]).T @ A + V.T @ A + A.T @ V
        j, k = np.triu_indices(m, k=1)
        keep = (j > a) & (k > a)
        j, k = j[keep], k[keep]
        hit = S[j, k] >= min_util * (1 - REL_TOL)
        for b, c in zip(j[hit], k[hit]):
            found[3].add(tuple(sorted((items[a], items[b], items[c]))))
    return found


# ----------------------------------------------------------------------- main
def load_huis(run: pd.Series, txs_for_remine=None) -> tuple[list, str]:
    """The full HUI list of a run: from disk if it was saved, else re-mined."""
    tag = run["run_tag"]
    p = HUI_DIR / f"{tag}.jsonl.gz"
    if p.exists():
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh], f"saved list {p.name}"
    if txs_for_remine is None:
        raise FileNotFoundError(p)
    from huim.efim import mine_efim
    db, pmap = txs_for_remine
    t0 = time.perf_counter()
    huis, st = mine_efim(db, pmap, min_util=float(run["abs_minutil"]))
    LOG.info("re-mined %s in %.1fs: %d HUIs (%s)", tag,
             time.perf_counter() - t0, len(huis), st.status)
    return ([{"itemset": list(x), "utility": u, "support": s}
             for x, u, s in huis],
            f"re-mined with src/huim/efim.py ({st.status}); the saved file "
            f"kept only the top-1000")


def main() -> None:
    t_start = time.perf_counter()
    paths = find_dataset()
    tr = pd.read_csv(paths["trainingData.csv"])
    wap = [c for c in tr.columns if c.startswith("WAP")]
    W = tr[wap].to_numpy(np.float64)
    y = (tr["BUILDINGID"].astype(str) + "_" + tr["FLOOR"].astype(str)).to_numpy()
    det_vals = W[W != NOT_DETECTED]
    lo, hi = float(det_vals.min()), float(det_vals.max())
    Q = q_matrix(W, lo, hi)
    keep = (Q > 0).any(axis=1)                 # empty fingerprints are dropped
    Qt = Q[keep]
    D = Qt > 0
    LOG.info("%d transactions (of %d rows), %d WAP columns, RSSI range [%g, %g]",
             len(Qt), len(W), len(wap), lo, hi)

    H = pd.read_csv(METRICS / "huim_runs.csv")
    I = pd.read_csv(METRICS / "ips_results.csv")
    checks: list[dict] = []
    samples: list[dict] = []
    pvals = {"wap": wap}

    def record(run_tag, name, ok, detail):
        checks.append({"run": run_tag, "check": name,
                       "result": "PASS" if ok else "FAIL", "detail": detail})
        LOG.info("%-34s %-26s %s  %s", run_tag, name,
                 "PASS" if ok else "FAIL", detail)

    # project values, to compare the independent re-implementation against
    from preprocess_uji import fit_preprocessor
    from utility_models import build_external_utility
    prep = fit_preprocessor(tr)
    q_proj = prep.internal_utility_matrix(tr)[keep]

    for model in ("A_signal", "B_discriminative", "C_rare_discriminative"):
        done = H[(H["utility_model"] == model) & (H["status"] == "COMPLETED")
                 & (H["n_huis"] > 0)]
        run = done.loc[done["rel_minutil_pct"].idxmin()]
        tag = run["run_tag"]
        p = p_vector(model, W, y)
        pvals[f"p_{MODEL_CODE[model]}"] = p
        U = Qt * p[None, :]
        total = float(U.sum())
        mu = total * float(run["rel_minutil_pct"]) / 100.0

        # 1. threshold
        record(tag, "1 threshold", math.isclose(mu, run["abs_minutil"],
                                                rel_tol=1e-7),
               f"{run['rel_minutil_pct']:g}% x {total:,.4f} = {mu:,.4f}; "
               f"huim_runs.csv says {run['abs_minutil']:,.4f}")
        # 2. q and p against the project's implementation
        um = build_external_utility(MODEL_CODE[model], tr, prep, y, "training")
        p_proj = np.array([um.external_utility[w] for w in wap])
        q_ok = bool(np.array_equal(q_proj, Qt.astype(np.int64)))
        # WAPs whose MI is ~0 sit at the 1e-6 positivity floor on one side and
        # at a tiny positive value on the other; compare the rest strictly
        floor = (p_proj <= 1e-5) | (p <= 1e-5)
        p_err = float(np.max(np.abs(p_proj - p)[~floor])) if (~floor).any() else 0.0
        f_err = float(np.max(np.abs(p_proj - p)[floor])) if floor.any() else 0.0
        record(tag, "2 q(i,T) and p(i)", q_ok and p_err < 1e-8 and f_err < 1e-5,
               f"q identical: {q_ok}; max |p_project - p_here| = {p_err:.2e} over "
               f"{int((~floor).sum())} WAPs, {f_err:.2e} over the "
               f"{int(floor.sum())} WAPs at the 1e-6 floor (MI ~ 0)")

        remine = None
        if not (HUI_DIR / f"{tag}.jsonl.gz").exists():
            cols = np.arange(len(wap))
            db = [{wap[j]: int(Qt[r, j]) for j in cols[D[r]]}
                  for r in range(len(Qt))]
            remine = (db, {w: float(p[j]) for j, w in enumerate(wap)})
        huis, source = load_huis(run, remine)
        if remine is not None:
            record(tag, "0 re-mined list", len(huis) == int(run["n_huis"]),
                   f"{len(huis):,} HUIs re-mined; huim_runs.csv records "
                   f"{int(run['n_huis']):,}")

        # 3-5. soundness, exact utility, support for EVERY reported HUI
        col = {w: j for j, w in enumerate(wap)}
        worst_rel, below, sup_bad = 0.0, 0, 0
        min_u = math.inf
        for h in huis:
            cols = [col[w] for w in h["itemset"]]
            u, s = itemset_utility(cols, D, U)
            rel = abs(u - h["utility"]) / max(abs(u), 1.0)
            worst_rel = max(worst_rel, rel)
            min_u = min(min_u, u)
            below += u < mu * (1 - REL_TOL)
            sup_bad += s != int(h["support"])
        record(tag, "3 soundness u(X) >= minUtil", below == 0,
               f"{len(huis):,} HUIs ({source}); smallest recomputed u(X) = "
               f"{min_u:,.4f} vs minUtil {mu:,.4f}; {below} below")
        record(tag, "4 exact utilities", worst_rel < U_TOL,
               f"max relative difference EFIM vs recomputed = {worst_rel:.2e}")
        record(tag, "5 exact supports", sup_bad == 0,
               f"{sup_bad} supports differ")

        # 6. completeness for every itemset of length <= 3
        items = np.flatnonzero(D.any(axis=0))
        t0 = time.perf_counter()
        exh = all_utilities_upto3(D, U, items, mu)
        rep = {k: {tuple(sorted(col[w] for w in h["itemset"]))
                   for h in huis if len(h["itemset"]) == k} for k in (1, 2, 3)}
        n_eval = (len(items) + len(items) * (len(items) - 1) // 2
                  + len(items) * (len(items) - 1) * (len(items) - 2) // 6)
        for k in (1, 2, 3):
            miss = exh[k] - rep[k]
            extra = rep[k] - exh[k]
            # a disagreement is only acceptable if the itemset sits within
            # floating-point distance of the threshold
            margins = [abs(itemset_utility(list(x), D, U)[0] - mu) / mu
                       for x in miss | extra]
            borderline = all(m < U_TOL for m in margins)
            note = (f"; all {len(margins)} disagreement(s) within "
                    f"{U_TOL:g} of minUtil (rounding)" if margins and borderline
                    else "")
            record(tag, f"6 completeness length {k}",
                   (not miss and not extra) or borderline,
                   f"exhaustive search finds {len(exh[k]):,} itemsets with "
                   f"u >= minUtil, EFIM reported {len(rep[k]):,}; missing "
                   f"{len(miss)}, extra {len(extra)}" + note)
        LOG.info("  exhaustive search over %d items (%d itemsets of length "
                 "1-3) took %.1fs", len(items), n_eval,
                 time.perf_counter() - t0)

        # 7. the WAP union the positioning experiment used
        union = sorted({w for h in huis for w in h["itemset"]})
        cond = I[I["condition"] == f"huim_union__{tag}"]
        used = sorted(str(cond.iloc[0]["selected_waps"]).split(";")) \
            if len(cond) else []
        record(tag, "7 WAP union = IPS feature set", union == used,
               f"union of HUIs = {len(union)} WAPs; ips_results.csv uses "
               f"{len(used)}")

        # samples for the workbook: top-5, the 5 closest to minUtil, 5 random
        rng = np.random.default_rng(20251007)
        by_u = sorted(huis, key=lambda h: -h["utility"])
        pick = by_u[:5] + by_u[-5:] + [huis[i] for i in rng.choice(
            len(huis), size=min(5, len(huis)), replace=False)]
        for h in pick:
            cols = [col[w] for w in h["itemset"]]
            u, s = itemset_utility(cols, D, U)
            samples.append({"run": tag, "utility_model": model,
                            "minutil_pct": float(run["rel_minutil_pct"]),
                            "minutil_abs": mu,
                            "itemset": " ".join(h["itemset"]),
                            "length": len(h["itemset"]),
                            "u_efim": h["utility"], "u_recomputed": u,
                            "support_efim": int(h["support"]),
                            "support_recomputed": s,
                            "u_ge_minutil": u >= mu * (1 - REL_TOL)})

        # one HUI transaction by transaction: the smallest pair, so the sheet
        # stays short enough to add up by hand
        pairs = [h for h in huis if len(h["itemset"]) == 2] or huis
        h = min(pairs, key=lambda h: h["support"])
        cols = [col[w] for w in h["itemset"]]
        rows = np.flatnonzero(D[:, cols].all(axis=1))
        orig_rows = np.flatnonzero(keep)[rows]
        br = {"csv_row": orig_rows + 2}          # +1 header, +1 one-based
        for w, c in zip(h["itemset"], cols):
            br[f"RSSI_{w}"] = W[orig_rows, c]
            br[f"q_{w}"] = Qt[rows, c]
            br[f"p_{w}"] = p[c]
        pd.DataFrame(br).to_csv(OUT / f"hui_breakdown_{tag}.csv", index=False)
        dump_json({"run": tag, "itemset": h["itemset"],
                   "u_efim": h["utility"], "support": h["support"],
                   "minutil_abs": mu, "minutil_pct": float(run["rel_minutil_pct"]),
                   "total_db_utility": total},
                  OUT / f"hui_breakdown_{tag}.json")

    pd.DataFrame(samples).to_csv(OUT / "hui_samples.csv", index=False)
    pd.DataFrame(pvals).to_csv(OUT / "p_values.csv", index=False)
    n_fail = sum(c["result"] == "FAIL" for c in checks)
    dump_json({"what": "independent re-computation of the HUIM results from "
                       "trainingData.csv",
               "n_checks": len(checks), "n_failed": n_fail, "checks": checks,
               "seconds": round(time.perf_counter() - t_start, 1)},
              OUT / "huim_checks.json")
    LOG.info("%d checks, %d failed -> %s", len(checks), n_fail,
             OUT / "huim_checks.json")
    if n_fail:
        raise SystemExit(f"{n_fail} HUIM check(s) failed")


if __name__ == "__main__":
    main()
