"""PHASE R - learned combination of HUI-evidence features (dev folds only).

Every dev query has K candidate cells (the best cells of its chosen floor under
the baseline HUI score) and, for each, features computed from HUI matching only
(src/huim_research.py features). A regressor learns, from the OTHER dev folds,
the ground distance between a candidate cell and the true position; the query
is then placed at the weighted centroid of the m candidates predicted closest,
weights exp(-d_pred / lam). Leave-one-fold-out over the 6 dev folds, so every
number here is out-of-fold. The test data is never read.

Run: python src/huim_rerank.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_research import FEATS, FEATS2, RES

GF = 0.766126


def load_folds(extra: bool = True):
    out = []
    for k in range(6):
        f = dict(np.load(RES / f"feat_fold{k}.npz"))
        if extra:
            f["F"] = np.concatenate([f["F"], np.load(RES / f"feat2_fold{k}.npz")["F2"]], -1)
        out.append(f)
    return out


def model(kind: str):
    if kind == "gbm":
        return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                             min_samples_leaf=40, l2_regularization=1.0, random_state=0)
    return Ridge(alpha=1.0)


def place(pred, cxy, m, lam):
    o = np.argsort(pred, 1)[:, :m]
    d = np.take_along_axis(pred, o, 1)
    w = np.exp(-(d - d[:, :1]) / lam)
    w /= w.sum(1, keepdims=True)
    return np.einsum("ij,ijk->ik", w, np.take_along_axis(cxy, o[..., None], 1))


def main() -> None:
    extra = "--base-feats" not in sys.argv
    F = load_folds(extra)
    NF = F[0]["F"].shape[-1]
    base = np.concatenate([np.sqrt(((f["est"] - f["true"]) ** 2).sum(1)) * GF for f in F])
    print(f"baseline (current model) dev mean {base.mean():.3f} m over {len(base)} queries")
    rows = []
    for kind in ("ridge", "gbm"):
        preds = []
        for k in range(6):
            tr = [F[j] for j in range(6) if j != k]
            X = np.concatenate([f["F"].reshape(-1, NF) for f in tr])
            y = np.concatenate([np.log1p(f["dist"]).ravel() for f in tr])
            mdl = model(kind).fit(X, y)
            te = F[k]
            preds.append(np.expm1(mdl.predict(te["F"].reshape(-1, NF))).reshape(te["dist"].shape))
        for m, lam in itertools.product((1, 3, 5, 8, 12), (0.5, 1.0, 2.0, 4.0)):
            e = np.concatenate([np.sqrt(((place(p, f["cxy"], m, lam) - f["true"]) ** 2).sum(1)) * GF
                                for p, f in zip(preds, F)])
            rows.append({"model": kind, "m": m, "lam": lam, "dev_mean_m": e.mean(),
                         "dev_median_m": np.median(e),
                         "per_fold": [round(float(x.mean()), 3) for x in np.split(e, np.cumsum([len(f["true"]) for f in F])[:-1])]})
        if kind == "gbm":
            imp = None
    D = pd.DataFrame(rows).sort_values("dev_mean_m")
    D.to_csv(RES / f"rerank_grid{'' if extra else '_base'}.csv", index=False)
    print(D.head(12).to_string())
    print("per-fold baseline", [round(float(x.mean()), 3) for x in np.split(base, np.cumsum([len(f["true"]) for f in F])[:-1])])


if __name__ == "__main__":
    main()
