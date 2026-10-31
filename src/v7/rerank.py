"""V6 re-ranker reproduction on the cached dev features, and out-of-fold predictions.

`oof_v6` repeats `huim_rerank_final.dev_check` fold by fold and keeps the per-query predictions
(predicted ground distance cell->truth for each of the 30 candidates), which V7-A and V7-B need.
Training rows of fold k's regressor: the other 5 dev folds (their features come from fold models).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import place, regressor, relative  # noqa: E402  (V6 code, unchanged)
from v7.common import err_m, load_cache, save_cache, base_meta  # noqa: E402

N_FOLDS = 6


def load_dev(extra: str = "") -> list[dict]:
    return [load_cache(f"dev_fold{k}{extra}") for k in range(N_FOLDS)]


def flat(F: np.ndarray) -> np.ndarray:
    R = relative(F)
    return R.reshape(-1, R.shape[-1])


def oof_v6(D: list[dict], feat_key: str = "F", name: str = "v6_oof") -> list[np.ndarray]:
    """Predicted ground distance (n,30) for every dev query, regressor never trained on its own fold."""
    try:
        c = load_cache(name, {"feat_key": feat_key})
        return [c[f"p{k}"] for k in range(N_FOLDS)]
    except (FileNotFoundError, RuntimeError):
        pass
    out = []
    for k in range(N_FOLDS):
        tr = [D[j] for j in range(N_FOLDS) if j != k]
        X = np.concatenate([flat(d[feat_key]) for d in tr])
        y = np.concatenate([np.log1p(d["dist"]).ravel() for d in tr])
        p = np.expm1(regressor().fit(X, y).predict(flat(D[k][feat_key]))).reshape(D[k]["dist"].shape)
        out.append(p.astype(np.float32))
        print(f"  oof fold {k}: V6 error {err_m(place(p, D[k]['cxy'])[0], D[k]['true']).mean():.3f} m", flush=True)
    save_cache(name, base_meta(kind="oof_predictions", feat_key=feat_key), **{f"p{k}": p for k, p in enumerate(out)})
    return out


def v6_errors(D: list[dict], P: list[np.ndarray]) -> np.ndarray:
    return np.concatenate([err_m(place(p, d["cxy"])[0], d["true"]) for p, d in zip(P, D)])
