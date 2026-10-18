"""PHASE D - the three utility models (the HUIM <-> IPS mapping).

This is the part of the project that is NOT taken from the literature. The HUIM
formalism requires two ingredients that a Wi-Fi fingerprint database simply does
not contain:

    q(i,T) - internal utility, classically a purchased QUANTITY
    p(i)   - external utility, classically a UNIT PROFIT

A fingerprint has neither. So they have to be *defined*, and the definitions are
a modelling decision of this project, not a standard. All three models share the
same internal utility so that the ablation isolates exactly one variable: what
the external utility means.

    Model A  "Signal utility"          p(i) = 1
    Model B  "Discriminative utility"  p(i) ~ mutual information I(A_i ; Y)
    Model C  "Rare-discriminative"     p(i) ~ I(A_i ; Y) x IDF(i)

Leakage: every p(i) is estimated from trainingData only. `build_external_utility`
physically refuses a dataframe it was not told is the training split.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess_uji import NOT_DETECTED, Preprocessor
from utils import get_logger

LOG = get_logger("utility", "utility_models.log")

# [DESIGN] Signal-strength bin edges for the mutual-information estimate, in
# dBm, over the documented range [-104, 0]. State 0 is reserved for "not
# detected", which is itself informative (an AP being invisible localises you
# just as much as it being strong). Five signal states keep the joint histogram
# well populated: with 19,937 training rows and 13 classes, 6 states x 13
# classes = 78 cells, i.e. ~256 samples per cell on average.
RSSI_BINS = [-104.0, -90.0, -80.0, -70.0, -60.0, 0.0]
N_STATES = len(RSSI_BINS)          # 5 signal bins + 1 "not detected" state

EPS = 1e-12


def discretise(df: pd.DataFrame, wap_cols: Sequence[str]) -> np.ndarray:
    """Map each WAP cell to a discrete state in {0..N_STATES-1}.

    state 0        : AP not detected (raw value 100)
    state 1..5     : detected, binned by raw dBm using RSSI_BINS
    """
    W = df[wap_cols].to_numpy(dtype=np.float64)
    det = W != NOT_DETECTED
    S = np.zeros(W.shape, dtype=np.int8)
    # np.digitize with right=True puts -104 in bin 1 and 0 dBm in bin 5
    edges = np.asarray(RSSI_BINS[1:], dtype=np.float64)
    idx = np.digitize(np.clip(W, RSSI_BINS[0], RSSI_BINS[-1]), edges,
                      right=True) + 1
    S[det] = np.clip(idx[det], 1, N_STATES - 1 + 1 - 1).astype(np.int8)
    return S


def mutual_information(states: np.ndarray, y: np.ndarray) -> np.ndarray:
    """I(A_i ; Y) in bits, for every column of `states`, computed directly from
    the joint histogram:

        I(A;Y) = sum_a sum_y P(a,y) * log2( P(a,y) / (P(a) P(y)) )

    Deterministic and exactly reproducible (no estimator randomness), and it is
    the same quantity the AP-selection literature calls *information gain*
    (cf. Chen et al., IEEE TKDE 2006; Song et al., ISPRS IJGI 2016).
    """
    n, m = states.shape
    classes, y_idx = np.unique(y, return_inverse=True)
    n_cls = len(classes)
    py = np.bincount(y_idx, minlength=n_cls) / n

    mi = np.zeros(m, dtype=np.float64)
    # joint counts per column: (N_STATES x n_cls)
    for j in range(m):
        s = states[:, j].astype(np.int64)
        flat = s * n_cls + y_idx
        joint = np.bincount(flat, minlength=N_STATES * n_cls).reshape(
            N_STATES, n_cls).astype(np.float64)
        pj = joint / n
        pa = pj.sum(axis=1, keepdims=True)
        denom = pa * py[None, :]
        nz = pj > 0
        mi[j] = float(np.sum(pj[nz] * np.log2(pj[nz] / (denom[nz] + EPS))))
    return np.maximum(mi, 0.0)


def conditional_entropy_reduction(states: np.ndarray, y: np.ndarray
                                  ) -> Tuple[np.ndarray, float]:
    """Returns (MI, H(Y)) so that MI/H(Y) can be reported as the fraction of the
    label entropy a single AP explains - a far more readable number than raw
    bits when talking to a non-specialist."""
    _, y_idx = np.unique(y, return_inverse=True)
    py = np.bincount(y_idx) / len(y_idx)
    py = py[py > 0]
    h_y = float(-np.sum(py * np.log2(py)))
    return mutual_information(states, y), h_y


@dataclass
class UtilityModel:
    """A fully specified (q, p) pair plus the provenance needed for the report."""

    name: str
    description: str
    external_utility: Dict[str, float]
    diagnostics: dict

    def total_database_utility(self, transactions: Sequence[Dict[str, int]]
                               ) -> float:
        p = self.external_utility
        return float(sum(q * p[i] for t in transactions for i, q in t.items()))

    def transaction_utilities(self, transactions: Sequence[Dict[str, int]]
                              ) -> np.ndarray:
        p = self.external_utility
        return np.array([sum(q * p[i] for i, q in t.items())
                         for t in transactions], dtype=np.float64)


def build_external_utility(model: str, train_df: pd.DataFrame,
                           prep: Preprocessor, y_train: np.ndarray,
                           split_name: str) -> UtilityModel:
    """Construct p(i) for one model.

    Parameters
    ----------
    split_name
        Must be "training". This is a hard gate: any other value raises, so an
        accidental call on validationData cannot silently produce a leaked
        weight vector.
    """
    if split_name != "training":
        raise ValueError(
            f"build_external_utility was called with split_name={split_name!r}. "
            "External utilities (p) may be estimated from trainingData ONLY; "
            "using validationData here would be data leakage.")
    wap = prep.wap_cols
    W = train_df[wap].to_numpy()
    det = (W != NOT_DETECTED)
    support = det.sum(axis=0).astype(np.int64)
    n = len(train_df)

    if model == "A":
        p = {w: 1.0 for w in wap}
        diag = {
            "model": "A - Signal utility",
            "p_formula": "p(i) = 1 for every WAP",
            "p_rationale": "With p == 1 the utility of an itemset is driven "
                           "purely by signal strength and by how often the "
                           "WAPs co-occur. This is the control condition of "
                           "the ablation.",
            "p_min": 1.0, "p_max": 1.0, "p_mean": 1.0,
            "n_items_with_p_gt_0": len(wap),
            "estimated_from": "nothing (constant)",
        }
        return UtilityModel("A_signal",
                            "Internal utility = normalised RSSI; external "
                            "utility = 1 (signal strength only)", p, diag)

    states = discretise(train_df, wap)
    mi, h_y = conditional_entropy_reduction(states, y_train)
    mi_max = float(mi.max()) if mi.size else 0.0
    if mi_max <= 0:
        raise RuntimeError("all mutual informations are zero; cannot build "
                           "a discriminative utility")

    if model == "B":
        # [DESIGN] p(i) = I(A_i;Y) / max_j I(A_j;Y), floored at a tiny positive
        # value so EFIM's positivity requirement holds. Ratio form (rather than
        # 1 + k*MI) is deliberate: it lets a non-informative AP's utility decay
        # towards zero, which is the behaviour we actually want to test.
        raw = np.maximum(mi, 0.0) / mi_max
        raw = np.where(raw <= 0, 1e-6, raw)
        p = {w: float(raw[j]) for j, w in enumerate(wap)}
        diag = {
            "model": "B - Discriminative utility",
            "p_formula": "p(i) = max(I(A_i;Y), 1e-6) / max_j I(A_j;Y), with "
                         "Y = BUILDINGID_FLOOR and I estimated from the joint "
                         "histogram over 6 signal states",
            "p_rationale": "External utility is read as 'how much knowing this "
                           "AP's state tells us about the floor we are on'. "
                           "This is the information-gain criterion the AP "
                           "selection literature already uses, inserted into "
                           "the HUIM utility slot.",
            "estimated_from": "trainingData.csv ONLY",
            "target_label": "BUILDINGID_FLOOR",
            "label_entropy_H_Y_bits": round(h_y, 5),
            "n_signal_states": N_STATES,
            "rssi_bin_edges_dbm": RSSI_BINS,
            "mi_bits_max": round(mi_max, 5),
            "mi_bits_mean_over_detected": round(
                float(mi[support > 0].mean()), 5) if (support > 0).any() else 0,
            "mi_bits_max_as_fraction_of_H_Y": round(mi_max / h_y, 5),
            "p_min": float(raw.min()), "p_max": float(raw.max()),
            "p_mean": round(float(raw.mean()), 6),
            "top10_waps_by_mi": [
                {"wap": wap[j], "mi_bits": round(float(mi[j]), 5),
                 "support": int(support[j])}
                for j in np.argsort(-mi)[:10]],
        }
        return UtilityModel("B_discriminative",
                            "Internal utility = normalised RSSI; external "
                            "utility = normalised mutual information with "
                            "BUILDINGID_FLOOR", p, diag)

    if model == "C":
        # [DESIGN] Rare-but-informative. IDF(i) = log(N / (1 + support_i)) is the
        # standard inverse-document-frequency; multiplying by MI keeps an AP only
        # if it is both informative AND not ubiquitous. Clipped at 0 because an
        # AP seen in every single row has IDF ~ 0.
        idf = np.log(n / (1.0 + support))
        idf = np.maximum(idf, 0.0)
        raw = mi * idf
        raw = raw / raw.max() if raw.max() > 0 else raw
        raw = np.where(raw <= 0, 1e-6, raw)
        p = {w: float(raw[j]) for j, w in enumerate(wap)}
        diag = {
            "model": "C - Rare-discriminative utility",
            "p_formula": "p(i) proportional to I(A_i;Y) * log(N/(1+support_i)), "
                         "normalised to (0,1]",
            "p_rationale": "Tests whether down-weighting ubiquitous APs - which "
                           "are detected everywhere and therefore separate "
                           "nothing - changes the selected AP set. Optional "
                           "third arm of the ablation.",
            "estimated_from": "trainingData.csv ONLY",
            "target_label": "BUILDINGID_FLOOR",
            "label_entropy_H_Y_bits": round(h_y, 5),
            "p_min": float(raw.min()), "p_max": float(raw.max()),
            "p_mean": round(float(raw.mean()), 6),
            "top10_waps_by_score": [
                {"wap": wap[j], "mi_bits": round(float(mi[j]), 5),
                 "idf": round(float(idf[j]), 4), "support": int(support[j])}
                for j in np.argsort(-raw)[:10]],
        }
        return UtilityModel("C_rare_discriminative",
                            "Internal utility = normalised RSSI; external "
                            "utility = MI x IDF", p, diag)

    raise ValueError(f"unknown utility model {model!r}; expected A, B or C")
