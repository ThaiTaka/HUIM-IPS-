"""V7-C: device-robust HUI evidence for the candidate cells.

Extra per-candidate features computed ONLY from the mined HUIs (item mass m_c(i), estimated strength
qhat_c(i), HUI support) and from the query's own reading. They target the failure the per-phone analysis
shows: a phone with a different gain/offset reads every AP a constant number of dB off, which breaks the
absolute-strength agreement while leaving the relative structure intact.

  off_c        mass-weighted mean signed deviation of the query from the cell's expected strength (abs model)
               = the device offset this cell would imply
  mae_cen      mean |deviation - off_c|            strength agreement AFTER removing the implied offset
  pair_diff    relative RSSI differences: among the query's strongest APs that the cell also expects,
               mean |(q_a - q_b) - (qhat_a - qhat_b)| over pairs (offset cancels)
  key_miss     mass of the cell's 5 most important APs (by HUI mass) that are absent from the query
  key_miss_w   same but weighted by the key APs' expected strength
  stab         mass-weighted support-stability of the query's APs inside the cell's HUIs
  occ          share of the cell's HUI mass on APs the query detects (as a rank-model statement)
  rk_spread    spread (max - min) of the candidate's rank under the 3 HUI models, std of their relative scores
No training fingerprint is read; the cell centre is not used here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_research import strength_profile  # noqa: E402

NAMES = ["off_c", "mae_cen", "pair_diff", "key_miss", "key_miss_w", "stab", "occ", "n_pair", "off_abs_dev"]


def stability(pos) -> np.ndarray:
    """stab_c(i): HUI-weight-averaged support of the HUIs of cell c that contain AP i, scaled to [0,1] per cell."""
    Ws = pos.Cw.multiply(pos.hui_supp[None, :].astype(np.float32)).tocsr()
    num = np.asarray((Ws @ pos.H).todense())
    den = np.asarray((pos.Cw @ pos.H).todense())
    st = np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)
    return (st / np.maximum(st.max(1, keepdims=True), 1e-12)).astype(np.float32)


class DeviceEvidence:
    def __init__(self, posR, posA):
        self.massR, self.qhatR = strength_profile(posR)
        self.massA, self.qhatA = strength_profile(posA)
        self.stabA = stability(posA)

    def __call__(self, q: np.ndarray, qA: np.ndarray, cand: np.ndarray, batch: int = 128) -> np.ndarray:
        """q: rank-utility (n,nA); qA: abs-utility (n,nA); cand (n,K) -> (n,K,len(NAMES))."""
        out = []
        for s in range(0, len(q), batch):
            out.append(self._one(q[s:s + batch], qA[s:s + batch], cand[s:s + batch]))
        return np.concatenate(out)

    def _one(self, q, qA, cand):
        n, K = cand.shape
        MA, QhA, ST = self.massA[cand], self.qhatA[cand], self.stabA[cand]       # (n,K,nA)
        MR = self.massR[cand]
        qq = qA[:, None, :].astype(np.float32)
        det = qq > 0
        sh = det & (QhA > 0)
        wm = np.where(sh, MA, 0.0)
        wsum = np.maximum(wm.sum(-1), 1e-9)
        dev = np.where(sh, qq - QhA, 0.0)
        off = (wm * dev).sum(-1) / wsum
        mae_cen = (wm * np.abs(np.where(sh, dev - off[..., None], 0.0))).sum(-1) / wsum
        # pairwise differences among the query's strongest 5 APs that the cell expects
        top = np.argsort(-qA, 1)[:, :5]                                          # (n,5)
        qt = np.take_along_axis(qA, top, 1)[:, None, :].astype(np.float32)       # (n,1,5)
        ht = np.take_along_axis(QhA, np.repeat(top[:, None, :], K, 1), 2)        # (n,K,5)
        ok = (qt > 0) & (ht > 0)
        dq = qt[..., :, None] - qt[..., None, :]
        dh = ht[..., :, None] - ht[..., None, :]
        pm = ok[..., :, None] & ok[..., None, :] & np.triu(np.ones((5, 5), bool), 1)
        npair = pm.sum((-1, -2))
        pair = (np.abs(dq - dh) * pm).sum((-1, -2)) / np.maximum(npair, 1)
        pair = np.where(npair > 0, pair, 50.0)
        # key APs of the cell: 5 largest HUI mass (abs model)
        kidx = np.argsort(-MA, 2)[..., :5]
        km = np.take_along_axis(MA, kidx, 2)
        kd = np.take_along_axis(np.broadcast_to(det, MA.shape), kidx, 2)
        kq = np.take_along_axis(QhA, kidx, 2)
        kmiss = (km * ~kd).sum(-1) / np.maximum(km.sum(-1), 1e-9)
        kmiss_w = (km * kq * ~kd).sum(-1) / np.maximum((km * kq).sum(-1), 1e-9)
        stab = (wm * ST).sum(-1) / wsum
        occ = (MR * (q[:, None, :] > 0)).sum(-1)
        return np.stack([off, mae_cen, pair, kmiss, kmiss_w, stab, occ, npair.astype(np.float32),
                         np.abs(off)], -1).astype(np.float32)


def consistency(F: np.ndarray) -> np.ndarray:
    """Agreement of the three HUI models (rank, level-item, absolute) on each candidate, from the V6 feature
    columns: rank under each model (3, 17, 29) and relative score (2, 16, 28)."""
    ranks = F[..., [3, 17, 29]]
    rel = F[..., [2, 16, 28]]
    return np.stack([ranks.max(-1) - ranks.min(-1), ranks.mean(-1), rel.std(-1), rel.min(-1)], -1).astype(np.float32)


CONSIST_NAMES = ["rk_spread", "rk_mean", "rel_std", "rel_min"]


def dev_block(k: int) -> None:
    from huim_research import THETA, fold_path, load_model
    from multi_datasets import load
    from run_huim_only import folds_for, inputs
    from v7.common import base_meta, load_cache, save_cache
    b = load("uji")
    _p, Q, *_ = inputs(b, "rank")
    _pa, QA, *_ = inputs(b, "abs")
    base = load_cache(f"dev_fold{k}")
    tri, dvi = folds_for(b, len(Q))[k]
    assert np.array_equal(dvi, base["dvi"])
    posR, _ = load_model(fold_path(k), b.ground_factor)
    posA, _ = load_model(fold_path(k, "_abs_L1_t20"), b.ground_factor)
    X = np.concatenate([DeviceEvidence(posR, posA)(Q[dvi], QA[dvi], base["cand"]), consistency(base["F"])], -1)
    meta = base_meta(kind="dev_extra_block", block="devrob", fold=int(k), n_queries=int(len(dvi)),
                     names=NAMES + CONSIST_NAMES, model="rank + abs HUI models mined on the fold's training phones only")
    save_cache(f"dev_fold{k}_devrob", meta, X=X)
    print(f"devrob fold {k}: {X.shape}", flush=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True)
    dev_block(ap.parse_args().fold)
