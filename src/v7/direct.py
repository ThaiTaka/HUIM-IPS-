"""V7-B: direct coordinate optimisation of the candidate weights.

A small shared scorer maps the HUI-derived features of each candidate cell to a score s_i; the weights are
w = softmax(s) over the 30 candidates and the position is x_pred = sum_i w_i c_i (c_i = cell centre).
The scorer is trained with the metric itself,

    loss = mean( GF * || sum_i w_i c_i - x_true || )  (+ optional listwise and entropy terms),

so the weights are learned for the quality of the fused coordinate, not for per-cell distance prediction.
Only features that come from the mined HUIs and the cell centres are used; the true position is a training
label only. Pure NumPy (manual back-propagation, Adam): no deep-learning dependency.

Architecture: per-candidate MLP  x -> relu(W1 x) -> [h, mean_over_candidates(h)] -> relu(W2 .) -> w3 . h2
(the pooled branch lets a candidate's score depend on the other candidates of the same query).
"""
from __future__ import annotations

import numpy as np

GF = 0.766126


class DirectScorer:
    def __init__(self, n_in: int, h1: int = 64, h2: int = 32, seed: int = 0, tf: str = "none"):
        self.tf = tf
        r = np.random.default_rng(seed)
        g = lambda a, b: (r.standard_normal((a, b)) * np.sqrt(2.0 / a)).astype(np.float64)
        self.P = {"W1": g(n_in, h1), "b1": np.zeros(h1), "W2": g(2 * h1, h2), "b2": np.zeros(h2),
                  "w3": (r.standard_normal(h2) * 0.01)}
        self.mu = np.zeros(n_in)
        self.sd = np.ones(n_in)
        self.h1, self.h2 = h1, h2

    # ---------------------------------------------------------------- forward
    def _fwd(self, X: np.ndarray):
        P = self.P
        Z1 = X @ P["W1"] + P["b1"]
        H1 = np.maximum(Z1, 0)
        Hc = np.concatenate([H1, np.broadcast_to(H1.mean(1, keepdims=True), H1.shape)], -1)
        Z2 = Hc @ P["W2"] + P["b2"]
        H2 = np.maximum(Z2, 0)
        s = H2 @ P["w3"]
        return s, (X, Z1, H1, Hc, Z2, H2)

    def scores(self, X: np.ndarray) -> np.ndarray:
        return self._fwd(self._norm(X))[0]

    def _tf(self, X: np.ndarray) -> np.ndarray:
        return np.sign(X) * np.log1p(np.abs(X)) if self.tf == "slog" else X

    def _norm(self, X: np.ndarray) -> np.ndarray:
        return (self._tf(X) - self.mu) / self.sd

    @staticmethod
    def softmax(s: np.ndarray) -> np.ndarray:
        e = np.exp(s - s.max(1, keepdims=True))
        return e / e.sum(1, keepdims=True)

    def predict(self, X: np.ndarray, C: np.ndarray):
        w = self.softmax(self.scores(X))
        return np.einsum("ij,ijk->ik", w, C), w

    # --------------------------------------------------------------- loss/grad
    def loss_grad(self, Xn, C, t, dist=None, lam_aux=0.0, tau_aux=3.0, ent=0.0, eps=1e-6, wd=0.0):
        """Xn normalised features (B,K,F); C (B,K,2); t (B,2); dist (B,K) metres, for the listwise term."""
        s, (X, Z1, H1, Hc, Z2, H2) = self._fwd(Xn)
        w = self.softmax(s)
        B, K = w.shape
        xp = np.einsum("ij,ijk->ik", w, C)
        e = xp - t
        nrm = np.sqrt((e ** 2).sum(1) + eps)
        L = GF * nrm.mean()
        g = GF * e / nrm[:, None] / B                              # dL/dxp
        ds = w * np.einsum("ijk,ik->ij", C - xp[:, None], g)       # dL/ds
        if lam_aux > 0 and dist is not None:
            q = self.softmax(-dist / tau_aux)
            L += lam_aux * (-(q * np.log(w + 1e-12)).sum(1)).mean()
            ds += lam_aux * (w - q) / B
        if ent != 0.0:
            H = -(w * np.log(w + 1e-12)).sum(1, keepdims=True)
            L += ent * H.mean()
            ds += ent * (-w * (np.log(w + 1e-12) + H)) / B
        P = self.P
        G = {"w3": np.einsum("ij,ijh->h", ds, H2)}
        dH2 = ds[..., None] * P["w3"]
        dZ2 = dH2 * (Z2 > 0)
        G["W2"] = np.einsum("ijh,ijg->hg", Hc, dZ2)
        G["b2"] = dZ2.sum((0, 1))
        dHc = dZ2 @ P["W2"].T
        dH1 = dHc[..., :self.h1] + dHc[..., self.h1:].sum(1, keepdims=True) / K
        dZ1 = dH1 * (Z1 > 0)
        G["W1"] = np.einsum("ijf,ijh->fh", X, dZ1)
        G["b1"] = dZ1.sum((0, 1))
        if wd:
            for k in ("W1", "W2", "w3"):
                G[k] = G[k] + wd * P[k]
        return L, G

    # ------------------------------------------------------------------- fit
    def fit(self, X, C, t, dist=None, Xv=None, Cv=None, tv=None, epochs=40, batch=256, lr=2e-3,
            lam_aux=0.0, tau_aux=3.0, ent=0.0, wd=1e-4, seed=0, patience=8, verbose=False):
        """Adam on the training queries; when a validation set is given, the epoch with the lowest validation
        error is kept (early stopping). Returns the list of validation errors (m) per epoch."""
        Xt = self._tf(X).reshape(-1, X.shape[-1])
        self.mu = Xt.mean(0)
        self.sd = Xt.std(0) + 1e-6
        Xn = self._norm(X)
        Xvn = self._norm(Xv) if Xv is not None else None
        rng = np.random.default_rng(seed)
        m = {k: np.zeros_like(v) for k, v in self.P.items()}
        v = {k: np.zeros_like(x) for k, x in self.P.items()}
        step, hist, best, best_P, bad = 0, [], np.inf, None, 0
        n = len(Xn)
        for ep in range(epochs):
            perm = rng.permutation(n)
            for s0 in range(0, n, batch):
                ix = perm[s0:s0 + batch]
                _, G = self.loss_grad(Xn[ix], C[ix], t[ix], None if dist is None else dist[ix],
                                      lam_aux, tau_aux, ent, wd=wd)
                step += 1
                for k in self.P:
                    m[k] = 0.9 * m[k] + 0.1 * G[k]
                    v[k] = 0.999 * v[k] + 0.001 * G[k] ** 2
                    self.P[k] -= lr * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v[k] / (1 - 0.999 ** step)) + 1e-8)
            if Xvn is not None:
                xp, _ = self.predict(Xv, Cv)
                e = float((np.sqrt(((xp - tv) ** 2).sum(1)) * GF).mean())
                hist.append(e)
                if verbose:
                    print(f"    epoch {ep + 1}: val {e:.3f} m", flush=True)
                if e < best - 1e-4:
                    best, best_P, bad = e, {k: x.copy() for k, x in self.P.items()}, 0
                else:
                    bad += 1
                    if bad >= patience:
                        break
        if best_P is not None:
            self.P = best_P
        self.best_epoch = int(np.argmin(hist)) + 1 if hist else epochs
        return hist


def fit_members(data: list[dict], train_ids: list[int], cfg: dict, seed: int = 0) -> list[DirectScorer]:
    """Cross-fitted ensemble. Member i early-stops on training fold train_ids[i] and is fitted on the other
    training folds, so every member (and the ensemble) only ever sees the training folds; the evaluation
    fold is never touched. data[j] holds X (n,K,F), C (n,K,2) local coordinates, t (n,2), dist (n,K), keep."""
    members = []
    for i, va in enumerate(train_ids):
        fit = [j for j in train_ids if j != va]
        cat = lambda key, js: np.concatenate([data[j][key][data[j]["keep"]] for j in js])
        m = DirectScorer(data[fit[0]]["X"].shape[-1], cfg.get("h1", 32), cfg.get("h2", 16), seed=seed + i, tf=cfg.get("tf", "none"))
        m.fit(cat("X", fit), cat("C", fit), cat("t", fit), cat("dist", fit), cat("X", [va]), cat("C", [va]), cat("t", [va]),
              epochs=cfg.get("ep", 30), lr=cfg.get("lr", 5e-4), lam_aux=cfg.get("aux", 0.0), ent=cfg.get("ent", 0.0),
              wd=cfg.get("wd", 1e-3), tau_aux=cfg.get("tau", 3.0), seed=seed + i, patience=cfg.get("patience", 8))
        members.append(m)
    return members


def predict_members(members: list[DirectScorer], X: np.ndarray, C: np.ndarray):
    """Ensemble = mean of the members' scores s_i, then softmax (geometric mean of their weights)."""
    s = np.mean([m.scores(X) for m in members], 0)
    w = DirectScorer.softmax(s)
    return np.einsum("ij,ijk->ik", w, C), w
