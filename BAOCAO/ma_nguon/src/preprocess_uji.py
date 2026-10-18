"""PHASE D/E - turn UJIIndoorLoc fingerprints into (a) classifier features and
(b) HUIM utility transactions.

Every design decision that is OURS rather than the dataset's or the
literature's is marked [DESIGN] in the docstrings, because the report has to
keep those two apart.

Leakage policy enforced here
----------------------------
`fit_preprocessor` may only ever be called on trainingData. It returns a
`Preprocessor` holding the handful of scalars (RSSI floor/ceiling) learned from
training. `transform` applies them. Validation is never passed to `fit_*`.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import find_dataset, get_logger

LOG = get_logger("prep", "preprocess.log")

# Documented by the dataset's own attribute description (UCI ML Repository,
# dataset 310) and confirmed empirically in results/data_audit.md:
NOT_DETECTED = 100          # "Positive value 100 is used to denote when a WAP
                            #  was not detected."
RSSI_DOC_MIN = -104         # "-104dBm (extremely poor signal)"
RSSI_DOC_MAX = 0            # "to 0dbM"

# [DESIGN] Internal utilities must be strictly positive integers in a bounded
# range so that (a) EFIM's bounds are valid and (b) absolute utility values stay
# interpretable. We map the weakest detectable signal to 1 and the strongest to
# Q_MAX. Q_MAX = 100 is a readability choice, not a tuned hyper-parameter.
Q_MAX = 100


@dataclass
class Preprocessor:
    """Scalars learned from trainingData only."""

    wap_cols: List[str]
    rssi_min_train: float
    rssi_max_train: float
    n_rows_fitted: int
    q_max: int = Q_MAX

    # ---------------------------------------------------------------- features
    def positive_representation(self, df: pd.DataFrame) -> np.ndarray:
        """[DESIGN, grounded in literature] The "positive" RSSI representation
        used throughout the UJIIndoorLoc literature (cf. Torres-Sospedra et al.,
        ESWA 2015; Lohan et al., Data 2017): a non-detected AP becomes 0, and a
        detected RSSI is shifted so that the weakest detectable value becomes 1
        and the strongest becomes `q_max`.

        0 therefore means "no information", never "a very weak signal", which
        is the whole reason the raw sentinel 100 cannot be fed to a distance
        function unchanged: 100 is numerically the *largest* value in the matrix
        while meaning the *absence* of signal.
        """
        W = df[self.wap_cols].to_numpy(dtype=np.float64)
        det = W != NOT_DETECTED
        span = self.rssi_max_train - self.rssi_min_train
        out = np.zeros_like(W)
        v = (W - self.rssi_min_train) / span          # 0..1 inside train range
        v = np.clip(v, 0.0, 1.0)
        out[det] = 1.0 + v[det] * (self.q_max - 1.0)
        return out

    def internal_utility_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """q(i,T) for Model A/B/C: the positive representation rounded to a
        positive integer. Rounding keeps absolute utilities integral and
        therefore exactly reproducible."""
        X = self.positive_representation(df)
        Q = np.rint(X).astype(np.int64)
        Q[X == 0.0] = 0                     # keep "not detected" at exactly 0
        Q[(X > 0.0) & (Q < 1)] = 1          # never let a detection round to 0
        return Q

    # ------------------------------------------------------------ transactions
    def transactions(self, df: pd.DataFrame
                     ) -> Tuple[List[Dict[str, int]], np.ndarray]:
        """Each fingerprint row becomes one utility transaction.

        [DESIGN] Item = WAP. An item belongs to the transaction iff that WAP was
        detected in that fingerprint (value != 100). Internal utility q(i,T) =
        normalised signal strength. Rows where nothing was detected produce an
        empty transaction; they are returned as empty dicts so that indices stay
        aligned with `df`, and the miner drops them on its own.

        Returns (transactions, n_items_per_transaction).
        """
        Q = self.internal_utility_matrix(df)
        cols = self.wap_cols
        txs: List[Dict[str, int]] = []
        for row in Q:
            nz = np.nonzero(row)[0]
            txs.append({cols[j]: int(row[j]) for j in nz})
        return txs, (Q != 0).sum(axis=1)

    def as_dict(self) -> dict:
        return {"n_wap_columns": len(self.wap_cols),
                "rssi_min_train": self.rssi_min_train,
                "rssi_max_train": self.rssi_max_train,
                "q_max": self.q_max,
                "not_detected_sentinel": NOT_DETECTED,
                "rssi_doc_min": RSSI_DOC_MIN, "rssi_doc_max": RSSI_DOC_MAX,
                "fitted_on_n_rows": self.n_rows_fitted,
                "fitted_on": "trainingData.csv ONLY"}


def fit_preprocessor(train_df: pd.DataFrame) -> Preprocessor:
    """LEAKAGE GATE: the only function allowed to look at label-free statistics,
    and it is only ever given trainingData."""
    wap_cols = [c for c in train_df.columns if c.upper().startswith("WAP")]
    W = train_df[wap_cols].to_numpy()
    detected = W[W != NOT_DETECTED]
    lo, hi = float(detected.min()), float(detected.max())
    if not (RSSI_DOC_MIN <= lo <= hi <= RSSI_DOC_MAX):
        raise ValueError(f"detected RSSI range [{lo},{hi}] falls outside the "
                         f"documented [{RSSI_DOC_MIN},{RSSI_DOC_MAX}]")
    LOG.info("fit on %d training rows: %d WAP columns, detected RSSI in [%g, %g]",
             len(train_df), len(wap_cols), lo, hi)
    return Preprocessor(wap_cols=wap_cols, rssi_min_train=lo,
                        rssi_max_train=hi, n_rows_fitted=len(train_df))


def joint_label(df: pd.DataFrame) -> np.ndarray:
    """[DESIGN] The coarse localisation class used as the primary target:
    BUILDINGID_FLOOR. It is well defined in both splits (the audit confirmed the
    same 13 classes appear in training and validation), unlike SPACEID which is
    identically 0 in validationData and therefore unusable."""
    return (df["BUILDINGID"].astype(str) + "_" + df["FLOOR"].astype(str)).to_numpy()


def load_splits() -> Tuple[pd.DataFrame, pd.DataFrame]:
    p = find_dataset()
    tr = pd.read_csv(p["trainingData.csv"])
    va = pd.read_csv(p["validationData.csv"])
    LOG.info("loaded training %s, validation %s", tr.shape, va.shape)
    return tr, va
