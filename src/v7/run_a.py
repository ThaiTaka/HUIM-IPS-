"""V7-A: adaptive HUI candidate fusion, evaluated out-of-fold with nested parameter selection.

The input is the V6 re-ranker's out-of-fold predicted distances (derived from HUI evidence). For every rule
and parameter grid, the parameters are picked on five dev folds and the rule is evaluated on the sixth
(leave-one-fold-out), so the reported number does not use its own fold for selection. "informative" = dev
queries with at least one detected AP (the 76 empty fingerprints are listed separately, see the report).

Run: python src/v7/run_a.py     -> results/huim_only/uji/v7/V7A_dev.json
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import OUT, err_m  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import N_FOLDS, load_dev, oof_v6  # noqa: E402

GRIDS = {
    "v6": [dict(rule="v6", m=m, T=T) for m, T in itertools.product((5, 8, 12, 20, 30), (0.5, 1, 1.5, 2, 3, 4))],
    "cut": [dict(rule="cut", m=30, T=T, delta=d) for T, d in itertools.product((1, 2, 3, 4), (2, 4, 6, 8, 12, 20))],
    "adaptT": [dict(rule="adaptT", m=m, T0=t0, c=c) for m, t0, c in
               itertools.product((12, 20, 30), (0.25, 0.5, 1, 1.5, 2), (0, 0.1, 0.2, 0.4, 0.8, 1.2))],
    "floorS": [dict(rule="floorS", m=20, T=T, s_min=s) for T, s in itertools.product((1, 1.5, 2, 3), (0.0, 0.1, 0.2, 0.3, 0.5))],
    "cluster": [dict(rule="cluster", m=30, T=T, r=r) for T, r in itertools.product((1, 2, 3, 4, 6), (3, 5, 8, 12, 16))],
}


def main() -> None:
    D = load_dev()
    P = [p.astype(np.float64) for p in oof_v6(D)]
    keep = [d["F"][:, 0, 13] > 0 for d in D]
    Srel = [d["F"][:, :, 2] for d in D]

    def fold_err(k, kw):
        xy, _w = fuse(P[k], D[k]["cxy"], S_rel=Srel[k], **kw)
        return err_m(xy, D[k]["true"])

    res = {}
    base = [fold_err(k, GRIDS["v6"][0] | dict(m=20, T=2.0)) for k in range(N_FOLDS)]
    n_inf = np.array([keep[k].sum() for k in range(N_FOLDS)])
    mean_inf = lambda errs: float(np.concatenate([e[kp] for e, kp in zip(errs, keep)]).mean())
    res["V6*"] = {"dev_informative_mean": mean_inf(base), "params": dict(rule="v6", m=20, T=2.0)}
    for name, grid in GRIDS.items():
        E = [[fold_err(k, kw) for k in range(N_FOLDS)] for kw in grid]                      # [config][fold] -> errors
        S = np.array([[e[k][keep[k]].sum() for k in range(N_FOLDS)] for e in E])             # error sums (informative)
        in_sample = S.sum(1) / n_inf.sum()
        nested = []
        for k in range(N_FOLDS):
            others = [j for j in range(N_FOLDS) if j != k]
            best = int(np.argmin(S[:, others].sum(1) / n_inf[others].sum()))
            nested.append((E[best][k], grid[best]))
        res[name] = {"in_sample_best": {"params": grid[int(in_sample.argmin())], "dev_informative_mean": float(in_sample.min())},
                     "nested_dev_informative_mean": mean_inf([e for e, _ in nested]),
                     "nested_choices": [g for _, g in nested]}
        print(f"{name:8s} in-sample best {in_sample.min():.4f} {grid[int(in_sample.argmin())]} | nested {res[name]['nested_dev_informative_mean']:.4f}"
              f" | V6* {res['V6*']['dev_informative_mean']:.4f}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(OUT / "V7A_dev.json", "w"), indent=1)


if __name__ == "__main__":
    main()
