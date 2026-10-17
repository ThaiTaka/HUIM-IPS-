"""PHASE QV - independent checks of the HUIM-only positioner (PHASE Q).

Uses the raw fingerprints (through the dataset loaders) and the saved model /
prediction files only. It does not call EFIM, HUIPositioner or the metric code.

  M1  every cell's minUtil = theta_used% x the cell's total utility,
      recomputed from raw dBm
  M2  a sample of HUIs (every HUI of SAMPLE_CELLS random cells): utility and
      support recomputed by scanning the cell's rows, >= minUtil
  M3  completeness up to length 2, EVERY cell: each 1- and 2-itemset whose
      recomputed utility reaches minUtil is in the saved model
  M4  for N_QUERY random test rows: the cell scores, the top-m cells, the
      weights and (x, y) recomputed with plain Python loops over the HUIs
  M5  mean / median error and building-floor accuracy recounted from the
      prediction files
  M6  the selected configuration is the dev-grid minimum

Output: results/huim_only/verification.json
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from multi_datasets import load
from run_huim_only import ORDER, OUT_ROOT

SAMPLE_CELLS = 25
N_QUERY = 8
NOT_DET = 100


def q_of(W, lo, hi):
    det = W != NOT_DET
    v = np.clip((W - lo) / (hi - lo), 0, 1)
    q = np.where(det, np.rint(1 + v * 99), 0)
    q[det & (q < 1)] = 1
    return q


def close(a, b, rel=1e-6):
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))


def check(key: str) -> dict:
    out = OUT_ROOT / key
    b = load(key)
    tr = b.train
    wap = b.wap_cols
    W = tr[wap].to_numpy(np.float64)
    det = W[W != NOT_DET]
    lo, hi = det.min(), det.max()
    Q = q_of(W, lo, hi)
    M = np.load(out / "model" / "huis.npz")
    cells = pd.read_csv(out / "model" / "cells.csv")
    runs = pd.read_csv(out / "cell_runs.csv")
    sel = json.load(open(out / "selection.json", encoding="utf-8"))
    S = json.load(open(out / "summary.json", encoding="utf-8"))
    prm = sel["params"]
    ip, it = M["indptr"], M["items"]
    huis = [tuple(int(x) for x in it[ip[k]:ip[k + 1]]) for k in range(len(ip) - 1)]
    U, SUP, CI = M["utility"], M["support"], M["cell_index"]
    res = {"dataset": key, "checks": []}

    def add(n, ok, d=""):
        res["checks"].append({"check": n, "ok": bool(ok), "detail": d})

    rp = tr["RP"].astype(str).to_numpy()
    cell_rows = {str(c): np.flatnonzero(rp == str(c)) for c in cells["cell"]}
    by_cell: dict[int, list[int]] = {}
    for k, c in enumerate(CI):
        by_cell.setdefault(int(c), []).append(k)

    bad = 0
    mu = {}
    for i, r in runs.iterrows():
        rows = cell_rows[str(cells.loc[i, "cell"])]
        tot = float(Q[rows].sum())
        mu[i] = tot * r["theta_used_pct"] / 100
        bad += not (close(tot, r["total_utility"]) and close(mu[i], r["abs_minutil"]))
    add("M1 minUtil per cell", bad == 0, f"{len(runs)} cells, {bad} mismatches")

    rnd = random.Random(20251007)
    pick = rnd.sample(range(len(cells)), min(SAMPLE_CELLS, len(cells)))
    bad = n = 0
    for c in pick:
        rows = cell_rows[str(cells.loc[c, "cell"])]
        Qc = Q[rows]
        for k in by_cell.get(c, []):
            X = list(huis[k])
            cov = (Qc[:, X] > 0).all(axis=1)
            u = float(Qc[cov][:, X].sum())
            n += 1
            bad += not (close(u, U[k]) and int(cov.sum()) == int(SUP[k]) and u >= mu[c] * (1 - 1e-9))
    add("M2 HUI utility / support recomputed", bad == 0,
        f"{n} HUIs in {len(pick)} cells, {bad} failures")

    bad = scanned = 0
    for c in range(len(cells)):
        rows = cell_rows[str(cells.loc[c, "cell"])]
        Qc = Q[rows]
        D = (Qc > 0).astype(np.float64)
        act = np.flatnonzero(D.any(axis=0))
        Mx = D[:, act].T @ Qc[:, act]
        u2 = Mx + Mx.T
        np.fill_diagonal(u2, Qc[:, act].sum(axis=0))
        have = {huis[k] for k in by_cell.get(c, []) if len(huis[k]) <= 2}
        for a_, b_ in np.argwhere(np.triu(u2) >= mu[c] * (1 - 1e-9)):
            X = tuple(sorted({int(act[a_]), int(act[b_])}))
            bad += X not in have
        scanned += len(act) * (len(act) + 1) // 2
    add("M3 every 1/2-itemset >= minUtil is in the model", bad == 0,
        f"{scanned} itemsets scanned in {len(cells)} cells, {bad} missing")

    tot_u = {c: sum(U[k] for k in ks) for c, ks in by_cell.items()}
    cxy = cells[["x", "y"]].to_numpy()
    for tname, T in S["tests"].items():
        P = pd.read_csv(out / "predictions" / f"{tname}.csv")
        te = b.tests[tname]
        Qt = q_of(te[wap].to_numpy(np.float64), lo, hi)
        bad = 0
        for i in rnd.sample(range(len(te)), min(N_QUERY, len(te))):
            q = Qt[i]
            qs = float(q.sum())
            score = []
            for c in range(len(cells)):
                pc = 0.0
                items_c = set()
                for k in by_cell.get(c, []):
                    X = huis[k]
                    items_c.update(X)
                    inter = [j for j in X if q[j] > 0]
                    frac = len(inter) / len(X)
                    qt = sum(q[j] for j in inter) / max(len(inter), 1)
                    qbar = U[k] / (SUP[k] * len(X))
                    ag = math.exp(-abs(qt - qbar) / prm["tau"]) if prm["tau"] else 1.0
                    pc += U[k] / tot_u[c] * frac ** prm["gamma"] * ag
                cov = sum(q[j] for j in items_c) / max(qs, 1.0)
                score.append(pc * cov ** prm["beta"])
            order = sorted(range(len(score)), key=lambda c: -score[c])[:prm["m"]]
            a = [score[c] ** prm["p"] for c in order]
            z = sum(a)
            a = [x / z for x in a] if z > 0 else [1 / len(a)] * len(a)
            x = sum(w * cxy[c, 0] for w, c in zip(a, order))
            y = sum(w * cxy[c, 1] for w, c in zip(a, order))
            same_top = set(order) == {int(P.loc[i, f"cell{j + 1}_index"]) for j in range(len(order))}
            bad += not (same_top and close(x, P.loc[i, "pred_x"], 1e-4) and close(y, P.loc[i, "pred_y"], 1e-4))
        add(f"M4 {tname}: scores, top cells and (x,y) recomputed", bad == 0,
            f"{N_QUERY} rows, {bad} mismatches")
        e = [math.hypot(r.true_x - r.pred_x, r.true_y - r.pred_y) * b.ground_factor
             for r in P.itertuples()]
        jt = (P.true_building.astype(str) + "_" + P.true_floor.astype(str) == P.pred_building_floor)
        add(f"M5 {tname}: metrics recounted",
            close(round(sum(e) / len(e), 4), T["mean_err_m"], 1e-4)
            and close(round(float(np.median(e)), 4), T["median_err_m"], 1e-4)
            and close(round(float(jt.mean()), 6), T["joint_accuracy"], 1e-5),
            f"mean {sum(e) / len(e):.4f} m, joint {jt.mean():.4f}")
    G = pd.read_csv(out / "dev_grid.csv")
    add("M6 selected = dev-grid minimum", close(G.dev_mean_m.min(), sel["dev_mean_m"]),
        f"dev {sel['dev_mean_m']} m over {len(G)} configurations")
    res["n_checks"] = len(res["checks"])
    res["n_failed"] = sum(not c["ok"] for c in res["checks"])
    return res


def main() -> None:
    keys = [k for k in ORDER if (OUT_ROOT / k / "summary.json").exists()]
    allr = [check(k) for k in keys]
    for r in allr:
        print(f"{r['dataset']:10s} {r['n_checks']:3d} checks, {r['n_failed']} failed")
        for c in r["checks"]:
            print(("   ok   " if c["ok"] else "   FAIL ") + c["check"] + " | " + c["detail"])
    json.dump({"datasets": allr, "n_checks": sum(r["n_checks"] for r in allr),
               "n_failed": sum(r["n_failed"] for r in allr)},
              open(OUT_ROOT / "verification.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
