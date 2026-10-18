"""Contribution of each group of HUI evidence to step 8 (v6), on the dev folds.

For a held-out dev fold, the regressor is trained on the other five folds; then
the features of one group are permuted across queries (the candidates keep their
positions) and the increase of the dev mean error is recorded. Test data is not read.

Run: python src/importance_v6.py --fold k   (k = 0..5) ; python src/importance_v6.py --merge
-> results/huim_only/uji/research/importance_fold<k>.json, importance.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from huim_rerank_final import RES, dev_files, place, regressor, relative

GF = 0.766126
GROUPS = {
    "Điểm khớp HUI của mô hình rank": list(range(0, 10)),
    "Đồng thuận không gian và ngữ cảnh": list(range(10, 14)),
    "Mô hình mục theo mức cường độ": [14, 15, 16, 17, 23, 24],
    "Hồ sơ cường độ suy ra từ HUI (rank)": list(range(18, 23)),
    "Mô hình HUI lợi ích abs": list(range(25, 33)),
}


def run(k: int) -> None:
    D = [dict(np.load(f)) for f in dev_files(True)]
    X = np.concatenate([relative(d["F"]).reshape(-1, relative(d["F"]).shape[-1]) for j, d in enumerate(D) if j != k])
    y = np.concatenate([np.log1p(d["dist"]).ravel() for j, d in enumerate(D) if j != k])
    reg = regressor().fit(X, y)
    te = D[k]
    rng = np.random.default_rng(0)

    def err(F):
        G = relative(F)
        p = np.expm1(reg.predict(G.reshape(-1, G.shape[-1]))).reshape(te["dist"].shape)
        xy, *_ = place(p, te["cxy"])
        return float((np.sqrt(((xy - te["true"]) ** 2).sum(1)) * GF).mean())

    out = {"fold": k, "n": int(len(te["true"])), "base": err(te["F"]), "groups": {}}
    for g, idx in GROUPS.items():
        F = te["F"].copy()
        perm = rng.permutation(len(F))
        F[:, :, idx] = F[perm][:, :, idx]
        out["groups"][g] = err(F)
    json.dump(out, open(RES / f"importance_fold{k}.json", "w"), ensure_ascii=False, indent=1)
    print(out, flush=True)


def merge() -> None:
    R = [json.load(open(RES / f"importance_fold{k}.json")) for k in range(6)]
    n = np.array([r["n"] for r in R])
    base = float((np.array([r["base"] for r in R]) * n).sum() / n.sum())
    res = {"base_dev_mean_m": round(base, 4), "increase_m": {}}
    for g in GROUPS:
        v = float((np.array([r["groups"][g] for r in R]) * n).sum() / n.sum())
        res["increase_m"][g] = round(v - base, 4)
    json.dump(res, open(RES / "importance.json", "w"), ensure_ascii=False, indent=1)
    print(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int)
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    merge() if a.merge else run(a.fold)
