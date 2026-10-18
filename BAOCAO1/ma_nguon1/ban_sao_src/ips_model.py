"""PHASE I - the indoor positioning model and its evaluation protocol.

Design constraints taken from the project brief, and why they matter:

* **One classifier, one configuration, everywhere.** k and the distance metric
  are selected once, on a train_sub/dev_sub split *of trainingData*, using the
  ALL-WAP feature set. That configuration is then frozen and reused unchanged
  for every HUIM condition. Consequence: the only thing that differs between
  "All-WAP" and "HUIM-selected" is *which columns are present*. If accuracy
  moves, feature selection moved it. Tuning on the baseline also means any
  advantage of the tuning accrues to the baseline, not to our method.

* **validationData is touched exactly once per condition**, at the very end, by
  `evaluate_once`. Nothing in this module fits anything on it.

* k-NN is the primary classifier because fingerprint localisation *is* nearest
  neighbour matching in signal space (Bahl & Padmanabhan, INFOCOM 2000) and
  because the UJIIndoorLoc literature uses it as the reference method
  (Torres-Sospedra et al., ESWA 2015). Random Forest is a secondary check only
  (precedent: Jedari et al., IPIN 2015).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import get_logger

LOG = get_logger("ips", "ips.log")

RANDOM_SEED = 20251007

# Hyper-parameter grid for the one-off selection on dev_sub.
KNN_GRID = {
    "n_neighbors": [1, 3, 5, 7, 9, 11],
    "metric": ["euclidean", "manhattan"],
    "weights": ["uniform", "distance"],
}


@dataclass
class KNNConfig:
    n_neighbors: int
    metric: str
    weights: str
    selected_on: str = "dev_sub of trainingData, ALL-WAP features"
    dev_joint_accuracy: float = float("nan")

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def split_train_dev(y: np.ndarray, dev_size: float = 0.25
                    ) -> Tuple[np.ndarray, np.ndarray]:
    """Stratified train_sub / dev_sub indices over trainingData only.

    [DESIGN + LIMITATION] A stratified random split is optimistic relative to
    validationData, because validationData was collected by a different user,
    mostly on different phones, and four months later (see the audit). It is
    used *only* to pick k / metric / weights, never to report a result, and the
    same split serves every condition. The honest reading is: these
    hyper-parameters are chosen under an easier distribution than the test set,
    which is a standard compromise but worth stating.
    """
    idx = np.arange(len(y))
    tr, dev = train_test_split(idx, test_size=dev_size, random_state=RANDOM_SEED,
                              stratify=y)
    return tr, dev


def select_knn_config(X: np.ndarray, y: np.ndarray,
                      tr_idx: np.ndarray, dev_idx: np.ndarray
                      ) -> Tuple[KNNConfig, List[dict]]:
    """Grid search on dev_sub. Returns the winner plus the whole trace."""
    trace: List[dict] = []
    best: Tuple[float, KNNConfig] | None = None
    for metric in KNN_GRID["metric"]:
        for weights in KNN_GRID["weights"]:
            for k in KNN_GRID["n_neighbors"]:
                clf = KNeighborsClassifier(n_neighbors=k, metric=metric,
                                           weights=weights, n_jobs=-1)
                clf.fit(X[tr_idx], y[tr_idx])
                acc = float(accuracy_score(y[dev_idx], clf.predict(X[dev_idx])))
                trace.append({"n_neighbors": k, "metric": metric,
                              "weights": weights,
                              "dev_joint_accuracy": round(acc, 6)})
                if best is None or acc > best[0]:
                    best = (acc, KNNConfig(k, metric, weights,
                                           dev_joint_accuracy=round(acc, 6)))
                LOG.info("dev k=%d metric=%s weights=%s -> joint acc %.4f",
                         k, metric, weights, acc)
    assert best is not None
    return best[1], trace


# --------------------------------------------------------------------- metrics
def _split_joint(labels: Sequence[str]) -> Tuple[np.ndarray, np.ndarray]:
    b, f = [], []
    for s in labels:
        bb, ff = str(s).split("_")
        b.append(int(bb))
        f.append(int(ff))
    return np.array(b), np.array(f)


def classification_metrics(y_true: Sequence[str], y_pred: Sequence[str]
                           ) -> dict:
    """Building / Floor / Joint accuracy, plus macro F1 and the joint confusion
    matrix. Building and Floor accuracy are *derived from the same joint
    prediction*, so the three numbers are mutually consistent by construction -
    a model cannot be credited with a correct floor while predicting another
    building."""
    yt = np.asarray([str(v) for v in y_true])
    yp = np.asarray([str(v) for v in y_pred])
    bt, ft = _split_joint(yt)
    bp, fp = _split_joint(yp)
    labels = sorted(set(yt) | set(yp))
    cm = confusion_matrix(yt, yp, labels=labels)
    return {
        "n_evaluated": int(len(yt)),
        "building_accuracy": round(float(accuracy_score(bt, bp)), 6),
        "floor_accuracy": round(float(accuracy_score(ft, fp)), 6),
        "joint_building_floor_accuracy": round(float(accuracy_score(yt, yp)), 6),
        "joint_macro_f1": round(float(f1_score(yt, yp, average="macro",
                                               zero_division=0)), 6),
        "building_macro_f1": round(float(f1_score(bt, bp, average="macro",
                                                  zero_division=0)), 6),
        "floor_macro_f1": round(float(f1_score(ft, fp, average="macro",
                                               zero_division=0)), 6),
        "floor_within_1_accuracy": round(
            float(np.mean((bt == bp) & (np.abs(ft - fp) <= 1))), 6),
        "confusion_matrix_labels": labels,
        "confusion_matrix": cm.tolist(),
    }


# Scale factor between the dataset's projected coordinates and true ground
# distance, established empirically in src/verify_coordinates.py: the columns
# are EPSG:3857 (Web Mercator), whose scale factor is 1/cos(latitude). At the
# UJI campus latitude that is 1.3053, so a projected distance overstates the
# ground distance by about 30%.
WEB_MERCATOR_GROUND_FACTOR = 0.766126
COORD_SYSTEM_NOTE = (
    "EPSG:3857 Web Mercator, identified in src/verify_coordinates.py by "
    "inverting the projection and checking the result lands on the UJI campus "
    "(139.7 m away; UTM 30N/31N miss by 871 km and 497 km)."
)


def positioning_error(coords_true: np.ndarray, coords_pred: np.ndarray) -> dict:
    """Planar positioning error, reported two ways.

    `*_error` columns are the straight Euclidean distance in the dataset's own
    projected coordinates. That is the convention the UJIIndoorLoc literature
    uses when it quotes "mean error in metres", so these are the numbers that
    are comparable with published results.

    `*_error_ground_m` columns apply the Web Mercator scale correction and are
    the true distance on the ground. Web Mercator is conformal, not
    equidistant: its scale factor is 1/cos(latitude), so at the UJI campus a
    projected distance is ~1.305x the real one. Both are reported because the
    first is comparable and the second is correct.
    """
    d = np.sqrt(((coords_true - coords_pred) ** 2).sum(axis=1))
    g = d * WEB_MERCATOR_GROUND_FACTOR
    out = {
        "n": int(d.size),
        "unit": "metres in EPSG:3857 projected coordinates (the convention "
                "used by the UJIIndoorLoc literature)",
        "coordinate_system": COORD_SYSTEM_NOTE,
        "ground_correction_factor": WEB_MERCATOR_GROUND_FACTOR,
        "mean_error": round(float(d.mean()), 4),
        "median_error": round(float(np.median(d)), 4),
        "p75_error": round(float(np.percentile(d, 75)), 4),
        "p90_error": round(float(np.percentile(d, 90)), 4),
        "p95_error": round(float(np.percentile(d, 95)), 4),
        "max_error": round(float(d.max()), 4),
        "std_error": round(float(d.std()), 4),
        "mean_error_ground_m": round(float(g.mean()), 4),
        "median_error_ground_m": round(float(np.median(g)), 4),
        "p75_error_ground_m": round(float(np.percentile(g, 75)), 4),
        "p90_error_ground_m": round(float(np.percentile(g, 90)), 4),
        "p95_error_ground_m": round(float(np.percentile(g, 95)), 4),
    }
    return out


# ----------------------------------------------------------------- evaluation
def evaluate_once(X_train: np.ndarray, y_train: np.ndarray,
                  coords_train: np.ndarray,
                  X_val: np.ndarray, y_val: np.ndarray,
                  coords_val: np.ndarray,
                  cfg: KNNConfig,
                  also_random_forest: bool = False,
                  rf_trees: int = 200) -> dict:
    """Fit on the FULL trainingData, predict validationData once.

    Coordinates are estimated by the same k neighbours that vote on the class
    (weighted k-NN regression), so the class result and the coordinate result
    come from one model rather than two.
    """
    import time

    res: dict = {"knn_config": cfg.as_dict(),
                 "n_features": int(X_train.shape[1]),
                 "n_train_rows": int(X_train.shape[0]),
                 "n_val_rows": int(X_val.shape[0])}

    # diagnostic: validation fingerprints in which NO selected WAP was detected
    empty_val = int((X_val.sum(axis=1) == 0).sum())
    res["val_rows_with_no_selected_wap_detected"] = empty_val
    res["train_rows_with_no_selected_wap_detected"] = int(
        (X_train.sum(axis=1) == 0).sum())

    if X_train.shape[1] == 0:
        res["status"] = "NO_FEATURES"
        return res

    t0 = time.perf_counter()
    clf = KNeighborsClassifier(n_neighbors=cfg.n_neighbors, metric=cfg.metric,
                               weights=cfg.weights, n_jobs=-1)
    clf.fit(X_train, y_train)
    res["knn_fit_seconds"] = round(time.perf_counter() - t0, 4)

    t0 = time.perf_counter()
    y_pred = clf.predict(X_val)
    res["knn_predict_seconds"] = round(time.perf_counter() - t0, 4)
    res["knn"] = classification_metrics(y_val, y_pred)

    # coordinate regression from the same neighbour set
    dist, nbr = clf.kneighbors(X_val, n_neighbors=cfg.n_neighbors)
    if cfg.weights == "distance":
        w = 1.0 / np.maximum(dist, 1e-12)
    else:
        w = np.ones_like(dist)
    w = w / w.sum(axis=1, keepdims=True)
    pred_xy = np.einsum("ij,ijk->ik", w, coords_train[nbr])
    res["knn"]["positioning_error"] = positioning_error(coords_val, pred_xy)

    if also_random_forest:
        t0 = time.perf_counter()
        rf = RandomForestClassifier(n_estimators=rf_trees,
                                    random_state=RANDOM_SEED, n_jobs=-1)
        rf.fit(X_train, y_train)
        fit_s = time.perf_counter() - t0
        rp = rf.predict(X_val)
        res["random_forest"] = classification_metrics(y_val, rp)
        res["random_forest"]["n_estimators"] = rf_trees
        res["random_forest"]["fit_seconds"] = round(fit_s, 4)

    res["status"] = "OK"
    return res
