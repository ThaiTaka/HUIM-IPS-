"""So sánh các bộ chấm điểm cho bước 8 của V7 trên dev out-of-fold (6 fold theo điện thoại): sai số mét và thời gian.

    python src/v7/compare_scorers.py --cand mlp_c2 --members 1          # giai đoạn sàng lọc: 1 thành viên / fold
    python src/v7/compare_scorers.py --cand attn --members 5            # xác nhận: tập hợp 5 thành viên, như V7-C2

Giao thức giống V7: với fold đánh giá k, mô hình chỉ huấn luyện trên 5 fold còn lại (thành viên i dừng sớm trên fold huấn luyện
thứ i, huấn luyện trên 4 fold khác); đặc trưng là 49 cột (rel + absL3) đã ở dạng tương đối (196). validationData KHÔNG được đọc ở đây.
Ứng viên GBM / k-NN theo cách V6: dự đoán log(1 + khoảng cách ô) rồi trọng số exp(-d/λ), m = 20, λ = 2.

Kết quả: results/huim_only/uji/v7/scorer_compare/<cand>_m<members>.json (+ .npz sai số từng vân tay).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.alt_scorers import AttnScorer, LinearScorer, NoPoolScorer  # noqa: E402
from v7.common import OUT, err_m  # noqa: E402
from v7.direct import DirectScorer  # noqa: E402
from v7.experiments import prepare  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import N_FOLDS, load_dev  # noqa: E402

RES = OUT / "scorer_compare"
BLOCKS = ("rel", "absL3")
CFG = dict(lr=5e-4, wd=1e-3, ep=30, patience=8)

NN = {   # tên: (lớp, tham số khởi tạo, lr)
    "mlp_c2": (DirectScorer, dict(h1=32, h2=16), 5e-4),
    "mlp_wide": (DirectScorer, dict(h1=64, h2=32), 5e-4),
    "mlp_nopool": (NoPoolScorer, dict(h1=32, h2=16), 5e-4),
    "attn": (AttnScorer, dict(h1=32, d=16, h2=16), 5e-4),
    "linear": (LinearScorer, {}, 5e-4),
    "linear_lr5e-3": (LinearScorer, {}, 5e-3),
    "mlp_c2_lr5e-3": (DirectScorer, dict(h1=32, h2=16), 5e-3),
    "mlp_nopool_lr5e-3": (NoPoolScorer, dict(h1=32, h2=16), 5e-3),
    "attn_lr5e-3": (AttnScorer, dict(h1=32, d=16, h2=16), 5e-3),
}
TREE = ("gbm49", "gbm33", "knn49")


def make(name, n_in, seed):
    cls, kw, _ = NN[name]
    return cls(n_in, seed=seed, tf="slog", **kw) if cls is not DirectScorer else DirectScorer(n_in, kw["h1"], kw["h2"], seed=seed, tf="slog")


def fit_member(name, m, data, fit_ids, va, seed):
    cat = lambda key, js: np.concatenate([data[j][key][data[j]["keep"]] for j in js])
    lr = NN[name][2]
    if isinstance(m, DirectScorer):
        t0 = time.perf_counter()
        m.fit(cat("X", fit_ids), cat("C", fit_ids), cat("t", fit_ids), cat("dist", fit_ids), cat("X", [va]), cat("C", [va]), cat("t", [va]),
              epochs=CFG["ep"], lr=lr, wd=CFG["wd"], seed=seed, patience=CFG["patience"])
        m.fit_seconds = time.perf_counter() - t0
    else:
        m.fit(cat("X", fit_ids), cat("C", fit_ids), cat("t", fit_ids), cat("X", [va]), cat("C", [va]), cat("t", [va]),
              epochs=CFG["ep"], lr=lr, wd=CFG["wd"], seed=seed, patience=CFG["patience"])


def run_nn(name: str, members: int, folds, data, D):
    out = {"fold_inf": {}, "train_s": {}, "infer_ms": {}, "epochs": {}, "err": {}}
    n_params = None
    for k in folds:
        train_ids = [j for j in range(N_FOLDS) if j != k]
        ms = []
        for i in range(members):
            va = train_ids[i]
            fit_ids = [j for j in train_ids if j != va]
            m = make(name, data[fit_ids[0]]["X"].shape[-1], seed=i)
            fit_member(name, m, data, fit_ids, va, seed=i)
            ms.append(m)
        n_params = ms[0].n_params() if hasattr(ms[0], "n_params") else int(sum(v.size for v in ms[0].P.values()))
        X, C = data[k]["X"], data[k]["C"]
        t0 = time.perf_counter()
        s = np.mean([m.scores(X) for m in ms], 0)
        w = DirectScorer.softmax(s)
        xp = np.einsum("ij,ijk->ik", w, C)
        dt = time.perf_counter() - t0
        e = err_m(data[k]["o"] + xp, data[k]["t"] + data[k]["o"])
        keep = data[k]["keep"]
        out["fold_inf"][k] = float(e[keep].mean())
        out["err"][k] = e
        out["train_s"][k] = float(sum(m.fit_seconds for m in ms))
        out["infer_ms"][k] = 1000 * dt / len(X)
        out["epochs"][k] = [int(m.best_epoch) for m in ms]
        print(f"  [{name} m={members}] fold {k}: {out['fold_inf'][k]:.3f} m | train {out['train_s'][k]:.0f} s | infer {out['infer_ms'][k]:.4f} ms/q | epochs {out['epochs'][k]}", flush=True)
    out["n_params"] = n_params
    return out


def run_tree(name: str, folds, data, D, n_sub=60000):
    from huim_rerank_final import regressor
    out = {"fold_inf": {}, "train_s": {}, "infer_ms": {}, "epochs": {}, "err": {}}
    for k in folds:
        train_ids = [j for j in range(N_FOLDS) if j != k]
        X = np.concatenate([data[j]["X"].reshape(-1, data[j]["X"].shape[-1]) for j in train_ids])
        y = np.concatenate([np.log1p(data[j]["dist"]).ravel() for j in train_ids])
        Xk = data[k]["X"].reshape(-1, X.shape[-1])
        t0 = time.perf_counter()
        if name.startswith("gbm"):
            model = regressor().fit(X, y)
            tf = time.perf_counter() - t0
            t1 = time.perf_counter()
            p = np.expm1(model.predict(Xk)).reshape(data[k]["dist"].shape)
        else:                                                   # k-NN trên đặc trưng (tham khảo; lấy mẫu con để tính được)
            from sklearn.neighbors import KNeighborsRegressor
            rng = np.random.default_rng(0)
            ix = rng.choice(len(X), min(n_sub, len(X)), replace=False)
            Xs = np.sign(X[ix]) * np.log1p(np.abs(X[ix]))
            mu, sd = Xs.mean(0), Xs.std(0) + 1e-6
            model = KNeighborsRegressor(n_neighbors=15, weights="distance", algorithm="brute", n_jobs=-1).fit((Xs - mu) / sd, y[ix])
            tf = time.perf_counter() - t0
            t1 = time.perf_counter()
            Q = (np.sign(Xk) * np.log1p(np.abs(Xk)) - mu) / sd
            p = np.expm1(model.predict(Q)).reshape(data[k]["dist"].shape)
        xy = fuse(p.astype(np.float64), D[k]["cxy"], rule="v6", m=20, T=2.0)[0]
        dt = time.perf_counter() - t1
        e = err_m(xy, D[k]["true"])
        keep = data[k]["keep"]
        out["fold_inf"][k], out["err"][k] = float(e[keep].mean()), e
        out["train_s"][k], out["infer_ms"][k], out["epochs"][k] = float(tf), 1000 * dt / len(Xk) * 30, []
        print(f"  [{name}] fold {k}: {out['fold_inf'][k]:.3f} m | fit {tf:.0f} s | infer {out['infer_ms'][k]:.4f} ms/q", flush=True)
    out["n_params"] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, choices=list(NN) + list(TREE))
    ap.add_argument("--members", type=int, default=1)
    ap.add_argument("--folds", type=int, nargs="*", default=list(range(N_FOLDS)))
    a = ap.parse_args()
    D = load_dev()
    blocks = () if a.cand == "gbm33" else BLOCKS
    data = prepare(D, blocks)
    t0 = time.perf_counter()
    r = run_nn(a.cand, a.members, a.folds, data, D) if a.cand in NN else run_tree(a.cand, a.folds, data, D)
    keep = np.concatenate([data[k]["keep"] for k in a.folds])
    e = np.concatenate([r["err"][k] for k in a.folds])
    res = {"cand": a.cand, "members": a.members if a.cand in NN else None, "blocks": list(blocks), "folds": a.folds, "n_inputs": int(data[0]["X"].shape[-1]),
           "inf_mean": float(e[keep].mean()), "fold_inf": {str(k): v for k, v in r["fold_inf"].items()},
           "train_s_total": float(sum(r["train_s"].values())), "train_s_per_fold": float(np.mean(list(r["train_s"].values()))),
           "infer_ms_per_query": float(np.mean(list(r["infer_ms"].values()))), "n_params": r["n_params"], "epochs": {str(k): v for k, v in r["epochs"].items()},
           "wall_s": time.perf_counter() - t0, "scope": "dev OOF, vân tay có thông tin; validationData không được đọc"}
    RES.mkdir(parents=True, exist_ok=True)
    tag = f"{a.cand}_m{a.members}" if a.cand in NN else a.cand
    if a.folds != list(range(N_FOLDS)):
        tag += "_f" + "".join(map(str, a.folds))
    json.dump(res, open(RES / f"{tag}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    np.savez_compressed(RES / f"{tag}.npz", **{f"e{k}": r["err"][k] for k in a.folds})
    print(f"{tag}: dev (có thông tin) {res['inf_mean']:.4f} m | train {res['train_s_per_fold']:.0f} s/fold | infer {res['infer_ms_per_query']:.4f} ms/query", flush=True)


if __name__ == "__main__":
    main()
