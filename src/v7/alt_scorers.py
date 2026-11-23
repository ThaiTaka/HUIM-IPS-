"""Bộ chấm điểm thay thế cho bước 8 của V7 (so sánh với MLP của V7-C2 trong compare_scorers.py).

Tất cả dùng chung: đầu vào 30 ô x F đặc trưng, điểm s_i, w = softmax(s), tọa độ = sum w_i c_i, mất mát = sai số mét
(giống `direct.DirectScorer`), NumPy thuần, gradient viết tay (kiểm bằng sai phân hữu hạn: `gradient_check`).

    LinearScorer   s = z . w                                  (đường cơ sở tuyến tính)
    NoPoolScorer   MLP 32/16 KHÔNG có nhánh gộp h̄            (cắt riêng nhánh gộp)
    AttnScorer     MLP 32 -> self-attention 1 đầu trên 30 ô -> 16 (mô hình hóa quan hệ giữa các ô trực tiếp)
"""
from __future__ import annotations

import time

import numpy as np

from v7.direct import GF, DirectScorer


class AltBase:
    wkeys: tuple[str, ...] = ()

    def __init__(self, n_in: int, seed: int = 0, tf: str = "slog"):
        self.tf = tf
        self.mu, self.sd = np.zeros(n_in), np.ones(n_in)
        self.P: dict[str, np.ndarray] = {}
        self.best_epoch = 0
        self.fit_seconds = 0.0

    def n_params(self) -> int:
        return int(sum(v.size for v in self.P.values()))

    # ---- chuẩn hóa như DirectScorer
    def _tf(self, X):
        return np.sign(X) * np.log1p(np.abs(X)) if self.tf == "slog" else X

    def _norm(self, X):
        return (self._tf(X) - self.mu) / self.sd

    def scores(self, X):
        return self._fwd(self._norm(X))[0]

    def predict(self, X, C):
        w = DirectScorer.softmax(self.scores(X))
        return np.einsum("ij,ijk->ik", w, C), w

    def loss_grad(self, Xn, C, t, wd=0.0, eps=1e-6):
        s, cache = self._fwd(Xn)
        w = DirectScorer.softmax(s)
        B = len(w)
        xp = np.einsum("ij,ijk->ik", w, C)
        e = xp - t
        nrm = np.sqrt((e ** 2).sum(1) + eps)
        L = GF * nrm.mean()
        g = GF * e / nrm[:, None] / B
        ds = w * np.einsum("ijk,ik->ij", C - xp[:, None], g)
        G = self._bwd(cache, ds)
        if wd:
            for k in self.wkeys:
                G[k] = G[k] + wd * self.P[k]
        return L, G

    def fit(self, X, C, t, Xv, Cv, tv, epochs=30, batch=256, lr=5e-4, wd=1e-3, seed=0, patience=8):
        t0 = time.perf_counter()
        Xt = self._tf(X).reshape(-1, X.shape[-1])
        self.mu, self.sd = Xt.mean(0), Xt.std(0) + 1e-6
        Xn = self._norm(X)
        rng = np.random.default_rng(seed)
        m = {k: np.zeros_like(v) for k, v in self.P.items()}
        v = {k: np.zeros_like(x) for k, x in self.P.items()}
        step, hist, best, best_P, bad = 0, [], np.inf, None, 0
        n = len(Xn)
        for ep in range(epochs):
            perm = rng.permutation(n)
            for s0 in range(0, n, batch):
                ix = perm[s0:s0 + batch]
                _, G = self.loss_grad(Xn[ix], C[ix], t[ix], wd)
                step += 1
                for k in self.P:
                    m[k] = 0.9 * m[k] + 0.1 * G[k]
                    v[k] = 0.999 * v[k] + 0.001 * G[k] ** 2
                    self.P[k] -= lr * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v[k] / (1 - 0.999 ** step)) + 1e-8)
            xp, _ = self.predict(Xv, Cv)
            e = float((np.sqrt(((xp - tv) ** 2).sum(1)) * GF).mean())
            hist.append(e)
            if e < best - 1e-4:
                best, best_P, bad = e, {k: x.copy() for k, x in self.P.items()}, 0
            else:
                bad += 1
                if bad >= patience:
                    break
        if best_P is not None:
            self.P = best_P
        self.best_epoch = int(np.argmin(hist)) + 1
        self.fit_seconds = time.perf_counter() - t0
        return hist


class LinearScorer(AltBase):
    wkeys = ("w",)

    def __init__(self, n_in, seed=0, tf="slog", **_):
        super().__init__(n_in, seed, tf)
        r = np.random.default_rng(seed)
        self.P = {"w": r.standard_normal(n_in) * 0.01}

    def _fwd(self, X):
        return X @ self.P["w"], (X,)

    def _bwd(self, cache, ds):
        (X,) = cache
        return {"w": np.einsum("ijf,ij->f", X, ds)}


class NoPoolScorer(AltBase):
    wkeys = ("W1", "W2", "w3")

    def __init__(self, n_in, seed=0, tf="slog", h1=32, h2=16):
        super().__init__(n_in, seed, tf)
        r = np.random.default_rng(seed)
        g = lambda a, b: r.standard_normal((a, b)) * np.sqrt(2.0 / a)
        self.P = {"W1": g(n_in, h1), "b1": np.zeros(h1), "W2": g(h1, h2), "b2": np.zeros(h2), "w3": r.standard_normal(h2) * 0.01}

    def _fwd(self, X):
        P = self.P
        Z1 = X @ P["W1"] + P["b1"]
        H1 = np.maximum(Z1, 0)
        Z2 = H1 @ P["W2"] + P["b2"]
        H2 = np.maximum(Z2, 0)
        return H2 @ P["w3"], (X, Z1, H1, Z2, H2)

    def _bwd(self, cache, ds):
        X, Z1, H1, Z2, H2 = cache
        P = self.P
        G = {"w3": np.einsum("ij,ijh->h", ds, H2)}
        dZ2 = ds[..., None] * P["w3"] * (Z2 > 0)
        G["W2"] = np.einsum("ijh,ijg->hg", H1, dZ2)
        G["b2"] = dZ2.sum((0, 1))
        dZ1 = (dZ2 @ P["W2"].T) * (Z1 > 0)
        G["W1"] = np.einsum("ijf,ijh->fh", X, dZ1)
        G["b1"] = dZ1.sum((0, 1))
        return G


class AttnScorer(AltBase):
    """MLP 32 -> một đầu self-attention giữa 30 ô (Q, K, V: 16 chiều) -> ghép [h ; attn] -> 16 -> điểm."""
    wkeys = ("W1", "Wq", "Wk", "Wv", "W2", "w3")

    def __init__(self, n_in, seed=0, tf="slog", h1=32, d=16, h2=16):
        super().__init__(n_in, seed, tf)
        r = np.random.default_rng(seed)
        g = lambda a, b: r.standard_normal((a, b)) * np.sqrt(2.0 / a)
        self.d = d
        self.P = {"W1": g(n_in, h1), "b1": np.zeros(h1), "Wq": g(h1, d), "Wk": g(h1, d), "Wv": g(h1, d),
                  "W2": g(h1 + d, h2), "b2": np.zeros(h2), "w3": r.standard_normal(h2) * 0.01}

    def _fwd(self, X):
        P, d = self.P, self.d
        Z1 = X @ P["W1"] + P["b1"]
        H = np.maximum(Z1, 0)
        Q, Kk, V = H @ P["Wq"], H @ P["Wk"], H @ P["Wv"]
        S = np.einsum("bid,bjd->bij", Q, Kk) / np.sqrt(d)
        A = np.exp(S - S.max(-1, keepdims=True))
        A /= A.sum(-1, keepdims=True)
        O = np.einsum("bij,bjd->bid", A, V)
        Hc = np.concatenate([H, O], -1)
        Z2 = Hc @ P["W2"] + P["b2"]
        H2 = np.maximum(Z2, 0)
        return H2 @ P["w3"], (X, Z1, H, Q, Kk, V, A, Hc, Z2, H2)

    def _bwd(self, cache, ds):
        X, Z1, H, Q, Kk, V, A, Hc, Z2, H2 = cache
        P, d, h1 = self.P, self.d, P_h(self)
        G = {"w3": np.einsum("ij,ijh->h", ds, H2)}
        dZ2 = ds[..., None] * P["w3"] * (Z2 > 0)
        G["W2"] = np.einsum("ijh,ijg->hg", Hc, dZ2)
        G["b2"] = dZ2.sum((0, 1))
        dHc = dZ2 @ P["W2"].T
        dH, dO = dHc[..., :h1].copy(), dHc[..., h1:]
        dA = np.einsum("bid,bjd->bij", dO, V)
        dV = np.einsum("bij,bid->bjd", A, dO)
        dS = A * (dA - (dA * A).sum(-1, keepdims=True)) / np.sqrt(d)
        dQ = np.einsum("bij,bjd->bid", dS, Kk)
        dK = np.einsum("bij,bid->bjd", dS, Q)
        G["Wq"], G["Wk"], G["Wv"] = (np.einsum("bih,bid->hd", H, x) for x in (dQ, dK, dV))
        dH += dQ @ P["Wq"].T + dK @ P["Wk"].T + dV @ P["Wv"].T
        dZ1 = dH * (Z1 > 0)
        G["W1"] = np.einsum("bif,bih->fh", X, dZ1)
        G["b1"] = dZ1.sum((0, 1))
        return G


def P_h(m: AttnScorer) -> int:
    return m.P["W1"].shape[1]


def gradient_check(cls, n_in=9, B=4, K=6, seed=0, **kw) -> float:
    """Sai lệch tương đối lớn nhất giữa gradient giải tích và sai phân hữu hạn (float64)."""
    r = np.random.default_rng(seed)
    m = cls(n_in, seed=seed, tf="none", **kw)
    X, C, t = r.standard_normal((B, K, n_in)), r.standard_normal((B, K, 2)) * 5, r.standard_normal((B, 2)) * 5
    _, G = m.loss_grad(X, C, t, wd=0.0)
    worst = 0.0
    for k, arr in m.P.items():
        for _ in range(5):
            ix = tuple(int(r.integers(0, s)) for s in arr.shape)
            old = arr[ix]
            h = 1e-6
            arr[ix] = old + h
            Lp, _ = m.loss_grad(X, C, t, wd=0.0)
            arr[ix] = old - h
            Lm, _ = m.loss_grad(X, C, t, wd=0.0)
            arr[ix] = old
            num = (Lp - Lm) / (2 * h)
            worst = max(worst, abs(num - G[k][ix]) / max(1e-8, abs(num) + abs(G[k][ix])))
    return worst


if __name__ == "__main__":
    for c in (LinearScorer, NoPoolScorer, AttnScorer):
        print(c.__name__, "gradient check (sai lệch tương đối lớn nhất): %.2e" % gradient_check(c))
