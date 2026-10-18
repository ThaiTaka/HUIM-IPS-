"""PHASE R - candidates over the whole building + learned floor decision.

Position: the K best cells of the chosen building (any floor) re-ranked by a
regressor on HUI-evidence features (distance cell-truth); floor: a classifier
on per-floor aggregates of the HUI scores. Both trained leave-one-fold-out on
the 6 dev folds (out-of-fold numbers only). Test data never read.

Run: python src/huim_rerank3.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_research import RES

GF = 0.766126


def load():
    return [dict(np.load(RES / f"feat3_fold{k}.npz", allow_pickle=True)) for k in range(6)]


def reg():
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                         min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def clf():
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.06, max_leaf_nodes=31,
                                          min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def floor_rows(f):
    """One row per (query, floor of the query's predicted building): the floor's
    aggregates, the same divided by the best floor's, and the floor number."""
    FA, floors = f["FA"], f["floors"]
    qb = np.array([s.split("_")[0] for s in f["floor_pred"]])
    fb = np.array([s.split("_")[0] for s in floors])
    mask = fb[None, :] == qb[:, None]
    agg = FA[..., :-1]
    best = np.where(mask[..., None], agg, -np.inf).max(1, keepdims=True)
    rel = agg / np.maximum(best, 1e-12)
    fnum = np.array([int(s.split("_")[1]) for s in floors], np.float32)
    X = np.concatenate([agg, rel, np.broadcast_to(fnum[None, :, None], agg.shape[:2] + (1,)),
                        FA[..., -1:]], -1)
    y = floors[None, :] == f["floor_true"][:, None]
    return X, y, mask


def place(pred, cxy, m, lam):
    o = np.argsort(pred, 1)[:, :m]
    d = np.take_along_axis(pred, o, 1)
    w = np.exp(-(d - d[:, :1]) / lam)
    w /= w.sum(1, keepdims=True)
    return np.einsum("ij,ijk->ik", w, np.take_along_axis(cxy, o[..., None], 1))


def main() -> None:
    F = load()
    NF = F[0]["F"].shape[-1]
    base = np.concatenate([np.sqrt(((f["est"] - f["true"]) ** 2).sum(1)) * GF for f in F])
    fl0 = np.concatenate([f["floor_ok"] for f in F])
    print(f"baseline dev mean {base.mean():.3f} m, floor acc {fl0.mean():.4f}")
    preds, flo = [], []
    for k in range(6):
        tr = [F[j] for j in range(6) if j != k]
        X = np.concatenate([f["F"].reshape(-1, NF) for f in tr])
        y = np.concatenate([np.log1p(f["dist"]).ravel() for f in tr])
        te = F[k]
        preds.append(np.expm1(reg().fit(X, y).predict(te["F"].reshape(-1, NF))).reshape(te["dist"].shape))
        Xs, ys = [], []
        for f in tr:
            Xf, yf, mf = floor_rows(f)
            Xs.append(Xf[mf]); ys.append(yf[mf])
        c = clf().fit(np.concatenate(Xs), np.concatenate(ys))
        Xt, _yt, mt = floor_rows(te)
        pr = np.where(mt, c.predict_proba(Xt.reshape(-1, Xt.shape[-1]))[:, 1].reshape(mt.shape), -1)
        flo.append(te["floors"][pr.argmax(1)] == te["floor_true"])
    flo = np.concatenate(flo)
    print(f"learned floor decision: dev floor acc {flo.mean():.4f} (baseline {fl0.mean():.4f})")
    rows = []
    sizes = np.cumsum([len(f["true"]) for f in F])[:-1]
    for m, lam in itertools.product((3, 5, 8, 12, 20), (1.0, 2.0, 4.0)):
        e = np.concatenate([np.sqrt(((place(p, f["cxy"], m, lam) - f["true"]) ** 2).sum(1)) * GF
                            for p, f in zip(preds, F)])
        rows.append({"m": m, "lam": lam, "dev_mean_m": e.mean(), "dev_median_m": np.median(e),
                     "per_fold": [round(float(x.mean()), 3) for x in np.split(e, sizes)]})
    D = pd.DataFrame(rows).sort_values("dev_mean_m")
    D.to_csv(RES / "rerank3_grid.csv", index=False)
    print(D.head(8).to_string())
    print("per-fold baseline", [round(float(x.mean()), 3) for x in np.split(base, sizes)])


if __name__ == "__main__":
    main()
