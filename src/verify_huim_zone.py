"""PHASE ZV - independent checks of every number PHASE Z reports.

Nothing here calls EFIM, the positioner or the metric code. From the raw
fingerprints (through the dataset loaders) and the saved result files it
re-derives:

  HUIM, for every AP set of every dataset
    Z0  every zone run COMPLETED (a truncated HUI list is never used)
    Z1  internal utility q(i,T) recomputed from raw dBm with its formula, total
        utility of each zone equal to the logged value
    Z2  minUtil_z = theta_used% x total utility of the zone
    Z3  every selected WAP has a witness HUI: its utility and support,
        recomputed by scanning the zone's rows, match the log and are
        >= minUtil_z
    Z4  completeness up to length 2: every 1- and 2-itemset of the zone whose
        recomputed utility reaches minUtil_z has all its WAPs selected
    Z5  the AP set is exactly the union of the zones' WAPs
  positioning, for the selected set on every test set
    P1  error of every row = sqrt(dx^2 + dy^2) x ground factor, mean / median
        equal to selected.json
    P2  (x, y) of every row = sum_j w_j (x_j, y_j) over the listed training
        rows (mean of the two members for an ensemble), weights sum to 1
    P3  building / floor / joint accuracy recounted
    P4  the AP set selected is the one with the lowest dev error

Output: results/huim_zone/verification.json
Run: python src/verify_huim_zone.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_zone import zone_labels
from multi_datasets import load
from run_huim_zone import ORDER, OUT_ROOT

NOT_DET = 100


def q_matrix(W: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """q = round(1 + (RSSI - lo)/(hi - lo) x 99), >= 1 when detected, else 0."""
    det = W != NOT_DET
    v = np.clip((W - lo) / (hi - lo), 0, 1)
    q = np.where(det, np.rint(1 + v * 99), 0)
    q[det & (q < 1)] = 1
    return q


def close(a, b, rel=1e-6) -> bool:
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))


def check_dataset(key: str) -> dict:
    out = OUT_ROOT / key
    b = load(key)
    tr = b.train
    wap = b.wap_cols
    W = tr[wap].to_numpy(np.float64)
    det_vals = W[W != NOT_DET]
    Q = q_matrix(W, det_vals.min(), det_vals.max())
    zones, _ = zone_labels(tr)
    res = {"dataset": key, "checks": []}

    def add(name, ok, detail=""):
        res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    sets = json.load(open(out / "ap_sets.json", encoding="utf-8"))["sets"]
    for name in sets:
        H = json.load(open(out / "hui" / f"{name}.json", encoding="utf-8"))
        p = np.array([H["external_utility"][w] for w in wap])
        U = Q * p
        D = (W != NOT_DET).astype(np.float64)
        bad_tot = bad_mu = bad_wit = bad_cmp = 0
        n_wit = n_pairs = 0
        union = set()
        for z in H["zones"]:
            rows = np.flatnonzero(zones == z["zone"])
            Uz, Dz = U[rows], D[rows]
            tot = float(Uz.sum())
            bad_tot += not close(tot, z["total_utility"])
            mu = tot * z["theta_used_pct"] / 100.0
            bad_mu += not close(mu, z["abs_minutil"])
            for wt in z["witnesses"]:
                j = [wap.index(w) for w in wt["items"]]
                cover = Dz[:, j].all(axis=1)
                u = float(Uz[cover][:, j].sum())
                n_wit += 1
                bad_wit += not (close(u, wt["utility"]) and int(cover.sum()) == wt["support"]
                                and u >= mu * (1 - 1e-9) and wt["wap"] in wt["items"])
            sel = set(z["waps"])
            union |= sel
            # length 1 and 2: u({a}) = sum U_a ; u({a,b}) = M[a,b] + M[b,a]
            u1 = Uz.sum(axis=0)
            act = np.flatnonzero(Dz.any(axis=0))
            M = Dz[:, act].T @ Uz[:, act]
            u2 = M + M.T
            np.fill_diagonal(u2, u1[act])
            hit = np.argwhere(np.triu(u2) >= mu)
            n_pairs += len(act) * (len(act) + 1) // 2
            for a, c in hit:
                if wap[act[a]] not in sel or wap[act[c]] not in sel:
                    bad_cmp += 1
        n_inc = sum(z["status"] != "COMPLETED" for z in H["zones"])
        add(f"Z0 {name}: every zone run complete (no truncated HUI set)",
            n_inc == 0, f"{n_inc} incomplete zones")
        add(f"Z1 {name}: zone total utility", bad_tot == 0,
            f"{len(H['zones'])} zones, {bad_tot} mismatches")
        add(f"Z2 {name}: minUtil = theta x total", bad_mu == 0, f"{bad_mu} mismatches")
        add(f"Z3 {name}: witness HUIs recomputed", bad_wit == 0,
            f"{n_wit} witnesses, {bad_wit} failures")
        add(f"Z4 {name}: 1/2-itemsets >= minUtil are selected", bad_cmp == 0,
            f"{n_pairs} itemsets scanned, {bad_cmp} missed")
        add(f"Z5 {name}: union of zones", sorted(union) == sorted(H["selected_waps"])
            == sorted(sets[name]), f"{len(union)} WAPs")

    S = json.load(open(out / "selected.json", encoding="utf-8"))
    dev = pd.read_csv(out / "dev_selection.csv")
    h = dev[dev["set"] != "all_aps"]
    best = h.loc[h["dev_mean_ground_m"].idxmin(), "dev_mean_ground_m"]
    chosen = h[h["set"] == S["selection"]["selected_set"]]["dev_mean_ground_m"].iloc[0]
    add("P4 selected set has the lowest dev error", close(best, chosen),
        f"{S['selection']['selected_set']} dev {chosen}")

    tx = dict(zip(zip(tr["SRC_FILE"], tr["SRC_ROW"]), tr["X"]))
    ty = dict(zip(zip(tr["SRC_FILE"], tr["SRC_ROW"]), tr["Y"]))
    one_file = tr["SRC_FILE"].nunique() == 1
    f0 = tr["SRC_FILE"].iloc[0]
    for tname, T in S["tests"].items():
        P = pd.read_csv(out / "predictions" / f"{tname}__huim_zone.csv")
        e = [math.hypot(a - c, bb - d) * b.ground_factor for a, bb, c, d in
             zip(P.true_x, P.true_y, P.pred_x, P.pred_y)]
        hz = T["huim_zone"]
        add(f"P1 {tname}: mean error", close(round(sum(e) / len(e), 4), hz["mean_err_m"], 1e-4),
            f"recomputed {sum(e) / len(e):.4f} m, reported {hz['mean_err_m']}")
        add(f"P1 {tname}: median error", close(round(float(np.median(e)), 4),
                                               hz["median_err_m"], 1e-4), "")
        bad_xy = bad_w = 0
        members = [""] + (["m2_"] if any(c.startswith("m2_nbr") for c in P.columns) else [])
        for _, r in P.iterrows():
            xs, ys = [], []
            for pre in members:
                k = 1
                sx = sy = sw = 0.0
                while f"{pre}nbr{k}_weight" in P.columns:
                    w = r[f"{pre}nbr{k}_weight"]
                    f = f0 if one_file else r[f"{pre}nbr{k}_train_file"]
                    key2 = (f, int(r[f"{pre}nbr{k}_train_row"]))
                    sx += w * tx[key2]; sy += w * ty[key2]; sw += w
                    k += 1
                bad_w += not close(sw, 1.0, 1e-6)
                xs.append(sx); ys.append(sy)
            bad_xy += not (close(sum(xs) / len(xs), r.pred_x, 1e-6)
                           and close(sum(ys) / len(ys), r.pred_y, 1e-6))
        add(f"P2 {tname}: (x,y) from neighbours", bad_xy == 0 and bad_w == 0,
            f"{len(P)} rows, {bad_xy} position / {bad_w} weight mismatches")
        jb = (P.true_building == P.pred_building)
        jf = (P.true_floor == P.pred_floor)
        add(f"P3 {tname}: accuracies", close(round(jb.mean(), 6), hz["building_accuracy"], 1e-5)
            and close(round((jb & jf).mean(), 6), hz["joint_accuracy"], 1e-5),
            f"building {jb.mean():.4f}, joint {(jb & jf).mean():.4f}")
    res["n_checks"] = len(res["checks"])
    res["n_failed"] = sum(not c["ok"] for c in res["checks"])
    return res


def main() -> None:
    keys = [k for k in ORDER if (OUT_ROOT / k / "selected.json").exists()]
    allr = [check_dataset(k) for k in keys]
    for r in allr:
        print(f"{r['dataset']:10s} {r['n_checks']:4d} checks, {r['n_failed']} failed")
        for c in r["checks"]:
            if not c["ok"]:
                print("   FAIL", c["check"], c["detail"])
    json.dump({"datasets": allr,
               "n_checks": sum(r["n_checks"] for r in allr),
               "n_failed": sum(r["n_failed"] for r in allr)},
              open(OUT_ROOT / "verification.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
