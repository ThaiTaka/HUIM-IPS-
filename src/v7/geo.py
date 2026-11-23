"""Spatial-consensus evidence of the HUI models over the 30 candidate cells (V7-C/D helper).

Each HUI model gives every candidate a relative score s in [0, 1] (its HUI matching score divided by the
best candidate's). From the scores and the cell centres only, per model:

    centroid_m   = sum_i w_i c_i,  w_i ~ s_i^p                  evidence-weighted centre of the candidates
    dcen_m,i     = ground distance of candidate i to centroid_m
    kde_m,i(sig) = sum_j w_j exp(-d_ij^2 / 2 sig^2) / sum_j w_j  how much of the model's evidence lies within
                                                                 ~sig metres of candidate i  (sig = 3, 8 m)

and the same for the mean score of all models. Candidates on which several independent HUI models agree
spatially get high kde and low dcen for every model. No fingerprint is read.
"""
from __future__ import annotations

import numpy as np

GF = 0.766126


def geo_block(scores: list[np.ndarray], cxy: np.ndarray, p: float = 4.0, sigmas=(3.0, 8.0)) -> np.ndarray:
    """scores: list of (n,K) relative scores; cxy (n,K,2) centres in coordinate units. Returns (n,K,3*(M+1))."""
    d = np.sqrt(((cxy[:, :, None] - cxy[:, None]) ** 2).sum(-1)) * GF                 # (n,K,K) metres
    allv = list(scores) + [np.mean(scores, 0)]
    feats = []
    for s in allv:
        w = np.clip(s, 0, None) ** p
        z = w.sum(1, keepdims=True)
        w = np.where(z > 0, w / np.where(z > 0, z, 1), 1.0 / w.shape[1])
        cen = np.einsum("ij,ijk->ik", w, cxy - cxy[:, :1]) + cxy[:, 0]
        feats.append(np.sqrt(((cxy - cen[:, None]) ** 2).sum(-1)) * GF)
        for sg in sigmas:
            feats.append(np.einsum("ij,ikj->ik", w, np.exp(-d ** 2 / (2 * sg ** 2))))
    return np.stack(feats, -1).astype(np.float32)


GEO_SCORE_COLS = [2, 16, 28]   # relative score of the rank, level-3 and absolute models in the V6 feature vector
