"""PHASE I3 - optimise the positioning error in metres.

Why the study's k-NN is not a good coordinate estimator
-------------------------------------------------------
The k-NN of PHASE I (k=1, Manhattan, uniform) was chosen for one job - the
building-floor CLASSIFICATION - on a random 75/25 split of trainingData. Two
facts make it a poor coordinate estimator:

1. A random split puts fingerprints recorded at the same reference point in
   both train_sub and dev_sub, so the nearest neighbour is almost always a twin
   of the query and k=1 wins. validationData is a different regime: another
   user, mostly other phones, four months later, at 1,074 positions none of
   which is a training reference point.
2. With k=1 the estimate IS one training position, so every mismatched
   neighbour becomes a full-size error, and Manhattan distance on raw signal
   levels punishes a phone that simply reads a few dB lower everywhere.

Protocol - validationData is never used to choose anything
----------------------------------------------------------
* Selection split: GroupKFold over USERID on trainingData (6 folds). Every dev
  fold contains only users the model has not seen, which is the closest
  simulation of the validation split that trainingData allows (18 users; a
  reference point was measured by 1-4 of them).
* Selection criterion: mean positioning error in ground metres on the dev folds.
* Stages, each keeping the best dev configuration of the stage before:
    S0  the study's frozen k-NN used as a regressor (positive, Manhattan, k=1)
    S1  best representation x distance at k=1         (3 x 4 combinations)
    S2  + number of neighbours k and weights 1/d^p    (k 1..30, p 0..4)
    S3  + test-time device-offset search: the query's detected RSSIs are
          shifted by delta dB, delta in a small grid, and the delta whose
          nearest training fingerprint is closest is kept (uses the query's own
          signal only - no position, no label)
    S4  + ensemble: average with the best model built on a second
          representation, each member with its own offset search
  A stage is adopted only if it lowers the dev mean error by >= MIN_GAIN_M.
* validationData: every stage is evaluated ONCE at the end, so the ablation
  table shows what each step bought on unseen data.

The selected model is then applied unchanged to the WAP sets of PHASE I
(baselines, top-n controls, HUIM union / top-n at their minUtil), so the HUIM
comparison can be read with the better regressor as well.

Outputs
  results/positioning_optimisation.json        protocol, selection, ablation,
                                               per-condition results
  results/metrics/positioning_dev_grid.csv     every dev configuration tried
  results/metrics/positioning_ablation.csv     S0..S4 on dev and validation
  results/metrics/positioning_conditions.csv   study k-NN vs optimised, per
                                               WAP set
  results/predictions/val_predictions_study_knn.csv   one row per validation
  results/predictions/val_predictions_optimised.csv   fingerprint (for the
                                                      manual checks)
  figures/fig18_positioning_optimisation.png (+ .csv)

Run: python src/optimize_positioning.py         (about 15 minutes, 12 threads)
"""
from __future__ import annotations

import sys
import time
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ips_model import WEB_MERCATOR_GROUND_FACTOR as GROUND
from preprocess_uji import NOT_DETECTED, fit_preprocessor, joint_label, load_splits
from utils import (FIGURES, METRICS, RESULTS, dump_json, environment_info,
                   get_logger, load_json)

LOG = get_logger("optpos", "optimize_positioning.log")
PRED_DIR = RESULTS / "predictions"
PRED_DIR.mkdir(parents=True, exist_ok=True)

N_FOLDS = 6
K_MAX = 30                       # neighbours kept per query
K_GRID = list(range(1, 21)) + [25, 30]
POWERS = [0, 1, 2, 3, 4]         # weight = 1 / d^p ; p = 0 is uniform
REPRESENTATIONS = ("positive", "powed", "exponential")
DISTANCES = ("euclidean", "manhattan", "braycurtis", "cosine")
OFFSET_RANGES = (3, 6, 9)        # search delta in [-r, +r] dB ...
OFFSET_STEP = 3                  # ... in steps of this many dB
MIN_GAIN_M = 0.05                # a stage must buy at least this on dev
STUDY = {"representation": "positive", "distance": "manhattan", "k": 1,
         "power": 0}


# ------------------------------------------------------------------- features
def representation(W: np.ndarray, kind: str) -> np.ndarray:
    """Signal representation of raw RSSI (sentinel 100 = not detected -> 0).

    positive     1..100, the study's own (preprocess_uji.positive_representation)
    powed        ((RSSI + 105)/105)^e      (Torres-Sospedra et al., ESWA 2015)
    exponential  exp((RSSI + 105)/24) / exp(105/24)          (same paper)
    """
    det = W != NOT_DETECTED
    r = np.clip(W, -104.0, 0.0)
    if kind == "positive":
        return np.where(det, 1.0 + (r + 104.0) / 104.0 * 99.0, 0.0)
    if kind == "powed":
        return np.where(det, ((r + 105.0) / 105.0) ** np.e, 0.0)
    if kind == "exponential":
        return np.where(det, np.exp((r + 105.0) / 24.0) / np.exp(105.0 / 24.0),
                        0.0)
    raise ValueError(kind)


def shift(W: np.ndarray, delta: float) -> np.ndarray:
    """Add delta dB to every DETECTED reading (clipped to the documented range);
    'not detected' stays not detected."""
    return np.where(W != NOT_DETECTED, np.clip(W + delta, -104.0, 0.0),
                    NOT_DETECTED)


# --------------------------------------------------------------- neighbours
@dataclass
class Lists:
    nbr: np.ndarray        # (n_query, K_MAX) indices into the reference set
    dst: np.ndarray        # (n_query, K_MAX) distances, ascending


def knn(ref: np.ndarray, query: np.ndarray, metric: str) -> Lists:
    """K_MAX nearest reference rows per query, ordered by (distance, row).

    RSSI is integer-valued, so exact distance ties are common (two training
    fingerprints at the same distance from the query). The explicit secondary
    key makes the order - and therefore every k-NN estimate - independent of
    how scikit-learn happens to break ties internally."""
    nn = NearestNeighbors(n_neighbors=K_MAX, algorithm="brute", metric=metric,
                          n_jobs=-1).fit(ref)
    d, i = nn.kneighbors(query)
    o = np.lexsort((i, d), axis=1)
    return Lists(np.take_along_axis(i, o, axis=1),
                 np.take_along_axis(d, o, axis=1))


def knn_folds(X: np.ndarray, Xq: np.ndarray, metric: str, folds) -> Lists:
    """Dev lists: each query only sees the training users of its own fold."""
    nbr = np.zeros((len(Xq), K_MAX), np.int64)
    dst = np.zeros((len(Xq), K_MAX))
    for tri, dvi in folds:
        L = knn(X[tri], Xq[dvi], metric)
        nbr[dvi] = tri[L.nbr]
        dst[dvi] = L.dst
    return Lists(nbr, dst)


def weights(dst: np.ndarray, k: int, power: float) -> np.ndarray:
    w = 1.0 / np.maximum(dst[:, :k], 1e-9) ** power
    return w / w.sum(axis=1, keepdims=True)


def estimate(L: Lists, coords: np.ndarray, k: int, power: float) -> np.ndarray:
    return np.einsum("ij,ijk->ik", weights(L.dst, k, power), coords[L.nbr[:, :k]])


def vote(L: Lists, labels: np.ndarray, k: int, power: float) -> np.ndarray:
    """Building-floor label by weighted vote of the same neighbours."""
    w = weights(L.dst, k, power)
    lab = labels[L.nbr[:, :k]]
    classes = np.unique(labels)
    score = np.stack([(w * (lab == c)).sum(axis=1) for c in classes], axis=1)
    return classes[score.argmax(axis=1)]


def offset_select(by_delta: dict[float, Lists], rng: int
                  ) -> tuple[Lists, np.ndarray]:
    """Keep, per query, the delta whose nearest neighbour is closest. Deltas
    are tried from 0 outwards, so a tie keeps the smaller shift."""
    grid = sorted((d for d in by_delta if abs(d) <= rng),
                  key=lambda d: (abs(d), d))
    n = len(next(iter(by_delta.values())).nbr)
    best = np.full(n, np.inf)
    nbr = np.zeros((n, K_MAX), np.int64)
    dst = np.zeros((n, K_MAX))
    chosen = np.zeros(n)
    for d in grid:
        L = by_delta[d]
        s = L.dst[:, 0]
        b = s < best
        best[b], nbr[b], dst[b], chosen[b] = s[b], L.nbr[b], L.dst[b], d
    return Lists(nbr, dst), chosen


def err_ground(pred: np.ndarray, true: np.ndarray) -> np.ndarray:
    return np.sqrt(((pred - true) ** 2).sum(axis=1)) * GROUND


STAT_KEYS = ("mean_ground_m", "median_ground_m", "p75_ground_m",
             "p90_ground_m", "p95_ground_m", "max_ground_m",
             "mean_projected_m", "share_within_8m")


def stats(e: np.ndarray) -> dict:
    """Ground-metre statistics plus the projected mean, for comparability."""
    return {"mean_ground_m": round(float(e.mean()), 4),
            "median_ground_m": round(float(np.median(e)), 4),
            "p75_ground_m": round(float(np.percentile(e, 75)), 4),
            "p90_ground_m": round(float(np.percentile(e, 90)), 4),
            "p95_ground_m": round(float(np.percentile(e, 95)), 4),
            "max_ground_m": round(float(e.max()), 4),
            "mean_projected_m": round(float(e.mean() / GROUND), 4),
            "share_within_8m": round(float((e <= 8.0).mean()), 4)}


# ------------------------------------------------------------------- the model
@dataclass
class Config:
    representation: str = "positive"
    distance: str = "manhattan"
    k: int = 1
    power: float = 0
    offset_range: int = 0            # 0 = no offset search
    ensemble_with: str = ""          # second representation, "" = none

    def label(self) -> str:
        s = f"{self.representation}+{self.distance}, k={self.k}, w=1/d^{self.power:g}"
        if self.offset_range:
            s += f", offset +-{self.offset_range} dB"
        if self.ensemble_with:
            s += f", ensemble with {self.ensemble_with}"
        return s


class Positioner:
    """The positioning model, usable on dev folds or on validation."""

    def __init__(self, W_ref: np.ndarray, coords: np.ndarray,
                 labels: np.ndarray, cfg: Config, cols=None) -> None:
        self.cfg = cfg
        self.cols = np.arange(W_ref.shape[1]) if cols is None else np.asarray(cols)
        self.W_ref = W_ref[:, self.cols]
        self.coords, self.labels = coords, labels
        self._ref = {}

    def ref(self, kind):
        if kind not in self._ref:
            self._ref[kind] = representation(self.W_ref, kind)
        return self._ref[kind]

    def member(self, Wq: np.ndarray, kind: str, folds=None
               ) -> tuple[Lists, np.ndarray]:
        cfg = self.cfg
        deltas = [0.0]
        if cfg.offset_range:
            deltas = list(np.arange(-cfg.offset_range, cfg.offset_range + 1e-9,
                                    OFFSET_STEP))
        by = {}
        for d in deltas:
            Xq = representation(shift(Wq[:, self.cols], d), kind)
            by[float(d)] = (knn_folds(self.ref(kind), Xq, cfg.distance, folds)
                            if folds is not None else
                            knn(self.ref(kind), Xq, cfg.distance))
        if len(by) == 1:
            return by[0.0], np.zeros(len(Wq))
        return offset_select(by, cfg.offset_range)

    def predict(self, Wq: np.ndarray, folds=None) -> dict:
        cfg = self.cfg
        L, delta = self.member(Wq, cfg.representation, folds)
        xy = estimate(L, self.coords, cfg.k, cfg.power)
        out = {"xy": xy, "lists": L, "delta": delta,
               "label": vote(L, self.labels, cfg.k, cfg.power)}
        if cfg.ensemble_with:
            L2, d2 = self.member(Wq, cfg.ensemble_with, folds)
            xy2 = estimate(L2, self.coords, cfg.k, cfg.power)
            out.update({"xy_member1": xy, "xy_member2": xy2, "lists2": L2,
                        "delta2": d2, "xy": (xy + xy2) / 2.0})
        return out


# ----------------------------------------------------------------- selection
def select_on_dev(W, C, y, folds) -> tuple[list[dict], list[dict]]:
    """Run the staged search on the leave-users-out folds of trainingData.
    Returns (stages, full grid)."""
    grid: list[dict] = []
    cache: dict[tuple, Lists] = {}

    def lists(kind, metric):
        key = (kind, metric)
        if key not in cache:
            t0 = time.perf_counter()
            X = representation(W, kind)
            cache[key] = knn_folds(X, X, metric, folds)
            LOG.info("dev lists %-11s %-10s %5.1fs", kind, metric,
                     time.perf_counter() - t0)
        return cache[key]

    # S0 / S1 / S2: representation x distance x k x weighting
    for kind in REPRESENTATIONS:
        for metric in DISTANCES:
            L = lists(kind, metric)
            for k in K_GRID:
                for p in POWERS:
                    if k == 1 and p:
                        continue                 # one neighbour: weight moot
                    e = err_ground(estimate(L, C, k, p), C)
                    grid.append({"stage": "S1-S2", "representation": kind,
                                 "distance": metric, "k": k, "power": p,
                                 "offset_range": 0, "ensemble_with": "",
                                 **stats(e)})
    G = pd.DataFrame(grid)
    s0 = G[(G.representation == "positive") & (G.distance == "manhattan")
           & (G.k == 1)].iloc[0]
    s1 = G[G.k == 1].sort_values("mean_ground_m").iloc[0]
    s2 = G.sort_values("mean_ground_m").iloc[0]
    cfg0 = Config(**STUDY)
    cfg1 = Config(s1.representation, s1.distance, 1, 0)
    cfg2 = Config(s2.representation, s2.distance, int(s2.k), float(s2.power))
    stages = [{"stage": "S0", "what": "study k-NN as regressor", "cfg": cfg0,
               "dev": s0[list(STAT_KEYS)].to_dict()},
              {"stage": "S1", "what": "best representation x distance (k=1)",
               "cfg": cfg1, "dev": s1[list(STAT_KEYS)].to_dict()},
              {"stage": "S2", "what": "+ k and 1/d^p weighting", "cfg": cfg2,
               "dev": s2[list(STAT_KEYS)].to_dict()}]
    LOG.info("S0 %s -> dev mean %.3f m", cfg0.label(), s0.mean_ground_m)
    LOG.info("S1 %s -> dev mean %.3f m", cfg1.label(), s1.mean_ground_m)
    LOG.info("S2 %s -> dev mean %.3f m", cfg2.label(), s2.mean_ground_m)

    # S3: device-offset search for the S2 model
    best = stages[-1]
    deltas = np.arange(-max(OFFSET_RANGES), max(OFFSET_RANGES) + 1e-9,
                       OFFSET_STEP)

    def offset_lists(kind):
        by = {}
        for d in deltas:
            if d == 0:
                by[0.0] = lists(kind, cfg2.distance)       # already computed
                continue
            t0 = time.perf_counter()
            Xq = representation(shift(W, d), kind)
            by[float(d)] = knn_folds(representation(W, kind), Xq,
                                     cfg2.distance, folds)
            LOG.info("dev offset lists %-11s delta %+5.1f dB %5.1fs", kind, d,
                     time.perf_counter() - t0)
        return by

    by1 = offset_lists(cfg2.representation)
    s3_best = None
    for rng in OFFSET_RANGES:
        L, _ = offset_select(by1, rng)
        for k in sorted({max(1, cfg2.k - 3), cfg2.k, cfg2.k + 3}):
            for p in sorted({cfg2.power, 2.0, 4.0}):
                e = err_ground(estimate(L, C, k, p), C)
                r = {"stage": "S3", "representation": cfg2.representation,
                     "distance": cfg2.distance, "k": k, "power": p,
                     "offset_range": rng, "ensemble_with": "", **stats(e)}
                grid.append(r)
                if s3_best is None or r["mean_ground_m"] < s3_best["mean_ground_m"]:
                    s3_best = r
    cfg3 = Config(cfg2.representation, cfg2.distance, int(s3_best["k"]),
                  float(s3_best["power"]), int(s3_best["offset_range"]))
    LOG.info("S3 %s -> dev mean %.3f m", cfg3.label(), s3_best["mean_ground_m"])
    if best["dev"]["mean_ground_m"] - s3_best["mean_ground_m"] >= MIN_GAIN_M:
        stages.append({"stage": "S3", "what": "+ device-offset search",
                       "cfg": cfg3, "dev": {k: s3_best[k] for k in STAT_KEYS}})
    best = stages[-1]
    cfg = best["cfg"]

    # S4: ensemble with the best model on a second representation that uses
    # the same distance; the second member gets the same k, p and offsets
    G2 = G[(G.representation != cfg.representation)
           & (G.distance == cfg.distance)]
    if not len(G2):
        LOG.info("S4 skipped: no second representation with %s", cfg.distance)
        return stages, grid
    second = G2.sort_values("mean_ground_m").iloc[0].representation
    by2 = offset_lists(second) if cfg.offset_range else {
        0.0: lists(second, cfg.distance)}
    L1 = (offset_select(by1, cfg.offset_range)[0] if cfg.offset_range
          else lists(cfg.representation, cfg.distance))
    L2 = offset_select(by2, cfg.offset_range)[0] if cfg.offset_range else by2[0.0]
    xy = (estimate(L1, C, cfg.k, cfg.power) + estimate(L2, C, cfg.k, cfg.power)) / 2
    cfg4 = replace(cfg, ensemble_with=second)
    r = {"stage": "S4", **asdict(cfg4), **stats(err_ground(xy, C))}
    grid.append(r)
    LOG.info("S4 %s -> dev mean %.3f m", cfg4.label(), r["mean_ground_m"])
    if best["dev"]["mean_ground_m"] - r["mean_ground_m"] >= MIN_GAIN_M:
        stages.append({"stage": "S4", "what": "+ ensemble of two "
                                               "representations",
                       "cfg": cfg4, "dev": {k: r[k] for k in STAT_KEYS}})
    return stages, grid


# ------------------------------------------------------------- per-row files
def prediction_frame(va: pd.DataFrame, out: dict, k: int, power: float,
                     member_lists: Lists, delta: np.ndarray | None,
                     with_delta: bool) -> pd.DataFrame:
    xy = out["xy"]
    lab = out["label"]
    df = pd.DataFrame({
        "csv_line": va.index.to_numpy() + 2,
        "true_building": va["BUILDINGID"].to_numpy(),
        "true_floor": va["FLOOR"].to_numpy(),
        "pred_building": [int(str(s).split("_")[0]) for s in lab],
        "pred_floor": [int(str(s).split("_")[1]) for s in lab],
        "true_x": va["LONGITUDE"].to_numpy(),
        "true_y": va["LATITUDE"].to_numpy(),
        "pred_x": xy[:, 0], "pred_y": xy[:, 1]})
    e = np.sqrt((df.true_x - df.pred_x) ** 2 + (df.true_y - df.pred_y) ** 2)
    df["err_projected_m"] = e
    df["err_ground_m"] = e * GROUND
    if with_delta:
        df["delta_db"] = delta
    members = [("", member_lists)]
    if "lists2" in out:              # ensemble: (x, y) = mean of two members
        members.append(("m2_", out["lists2"]))
        df["m2_delta_db"] = out["delta2"]
    for pre, L in members:
        w = weights(L.dst, k, power)
        for j in range(k):
            df[f"{pre}nbr{j + 1}_train_line"] = L.nbr[:, j] + 2
            df[f"{pre}nbr{j + 1}_distance"] = L.dst[:, j]
            df[f"{pre}nbr{j + 1}_weight"] = w[:, j]
    return df


# -------------------------------------------------------------------- figure
def figure(abl: pd.DataFrame, curves: dict, cond: pd.DataFrame) -> None:
    plt.rcParams.update({"font.family": "serif",
                         "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "font.size": 9.5, "axes.grid": True,
                         "grid.alpha": 0.3, "axes.spines.top": False,
                         "axes.spines.right": False, "legend.frameon": False,
                         "savefig.dpi": 200, "savefig.bbox": "tight"})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.6, 4.6),
                                 gridspec_kw={"width_ratios": [1, 1.0],
                                              "wspace": 0.62})
    cols = ["#9a9a9a", "#b8860b", "#1f3b73", "#8c2d04", "#145a32"]
    for (name, e), c in zip(curves.items(), cols):
        s = np.sort(e)
        a1.plot(s, np.arange(1, len(s) + 1) / len(s) * 100, color=c, lw=1.5,
                label=f"{name}: mean {e.mean():.2f} m, median {np.median(e):.2f} m")
    a1.axvspan(7, 8, color="#2e7d32", alpha=0.13)
    a1.text(7.5, 101, "7-8 m target", ha="center", va="bottom", fontsize=7.5,
            color="#2e7d32")
    a1.set_xlim(0, 40)
    a1.set_ylim(0, 100)
    a1.set_xlabel("Positioning error on the ground (m)")
    a1.set_ylabel("Validation fingerprints with error <= x (%)")
    a1.set_title("Error distribution, all 520 WAPs (validationData, 1,111 rows)",
                 pad=14)
    a1.legend(fontsize=7.2, loc="lower right")

    # horizontal bars: the WAP-set names (with minUtil for HUIM) are long
    yy = np.arange(len(cond))[::-1]
    h = 0.38
    b1 = a2.barh(yy + h / 2, cond["study_mean_ground_m"], h, color="#9a9a9a",
                 label="Study k-NN (k=1, Manhattan)")
    b2 = a2.barh(yy - h / 2, cond["opt_mean_ground_m"], h, color="#1f3b73",
                 label="Optimised positioning model")
    for bars in (b1, b2):
        for r in bars:
            a2.text(r.get_width() + 0.3, r.get_y() + r.get_height() / 2,
                    f"{r.get_width():.2f}", va="center", fontsize=6.8)
    a2.axvspan(7, 8, color="#2e7d32", alpha=0.13)
    a2.set_yticks(yy)
    a2.set_yticklabels([str(s).replace("\n", ", ") for s in cond["label"]],
                       fontsize=7.4)
    a2.set_xlabel("Mean positioning error on the ground (m)")
    a2.set_xlim(0, float(cond[["study_mean_ground_m",
                               "opt_mean_ground_m"]].max().max()) * 1.12)
    a2.set_title("Mean error per WAP set: before and after", pad=14)
    a2.legend(fontsize=7.4, loc="upper right")
    fig.text(0.01, -0.05, "Optimised model selected on leave-users-out folds of "
             "trainingData only; validationData used once per bar. Ground metres "
             "= projected metres x 0.766126 (Web Mercator correction).",
             fontsize=7, color="#444444")
    fig.savefig(FIGURES / "fig18_positioning_optimisation.png")
    plt.close(fig)
    cond.to_csv(FIGURES / "fig18_positioning_optimisation.csv", index=False)


def redraw_figure() -> None:
    """Redraw fig18 from the saved selection, without re-running the dev
    search: the stage configurations are read back from the JSON and only the
    (fast) validation predictions are recomputed."""
    tr, va = load_splits()
    wap = [c for c in tr.columns if c.startswith("WAP")]
    W, Wv = tr[wap].to_numpy(np.float64), va[wap].to_numpy(np.float64)
    C = tr[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
    Cv = va[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
    y = joint_label(tr)
    J = load_json(RESULTS / "positioning_optimisation.json")
    study = pd.read_csv(PRED_DIR / "val_predictions_study_knn.csv")
    curves = {}
    for st in J["stages"]:
        if st["stage"] == "S0":
            e = study["err_ground_m"].to_numpy()
        else:
            out = Positioner(W, C, y, Config(**st["config"])).predict(Wv)
            e = err_ground(out["xy"], Cv)
        curves[f"{st['stage']} {st['what']}"] = e
    Cn = pd.read_csv(METRICS / "positioning_conditions.csv")
    show = Cn[~Cn["condition"].str.match(r"control_.*__n(91|86|79|75)$")]
    figure(pd.read_csv(METRICS / "positioning_ablation.csv"), curves,
           show.reset_index(drop=True))
    LOG.info("redrew fig18 from the saved selection")


# ---------------------------------------------------------------------- main
def main() -> None:
    if "--figure-only" in sys.argv:
        redraw_figure()
        return
    t_start = time.perf_counter()
    tr, va = load_splits()
    prep = fit_preprocessor(tr)            # only to assert the column layout
    wap = prep.wap_cols
    W = tr[wap].to_numpy(np.float64)
    Wv = va[wap].to_numpy(np.float64)
    C = tr[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
    Cv = va[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
    y, yv = joint_label(tr), joint_label(va)
    assert np.allclose(representation(W, "positive"),
                       prep.positive_representation(tr))

    folds = list(GroupKFold(n_splits=N_FOLDS).split(W, groups=tr["USERID"]))
    LOG.info("dev protocol: %d leave-users-out folds over trainingData "
             "(%d users); validationData untouched until the end",
             N_FOLDS, tr["USERID"].nunique())

    stages, grid = select_on_dev(W, C, y, folds)
    pd.DataFrame(grid).to_csv(METRICS / "positioning_dev_grid.csv", index=False)
    final = stages[-1]["cfg"]
    LOG.info("SELECTED on dev: %s", final.label())

    # ---- the study's own k-NN on validation (PHASE I procedure) ------------
    # S0 is evaluated with exactly PHASE I's classifier, so that it reproduces
    # the reported baseline to the last digit (tie-breaking included).
    clf = KNeighborsClassifier(n_neighbors=1, metric="manhattan",
                               weights="uniform", n_jobs=-1)
    Xp, Xpv = representation(W, "positive"), representation(Wv, "positive")
    clf.fit(Xp, y)
    d1, i1 = clf.kneighbors(Xpv, n_neighbors=1)
    study = {"xy": C[i1[:, 0]], "label": clf.predict(Xpv),
             "lists": Lists(i1, d1), "delta": np.zeros(len(Wv))}

    # ---- validation, once per stage ----------------------------------------
    abl, curves = [], {}
    outs = {}
    for st in stages:
        if st["stage"] == "S0":
            out = study
        else:
            out = Positioner(W, C, y, st["cfg"]).predict(Wv)
        e = err_ground(out["xy"], Cv)
        acc = {"building_accuracy": float(np.mean(
                   [a.split("_")[0] == b.split("_")[0] for a, b in zip(out["label"], yv)])),
               "floor_accuracy": float(np.mean(
                   [a.split("_")[1] == b.split("_")[1] for a, b in zip(out["label"], yv)])),
               "joint_building_floor_accuracy": float(np.mean(out["label"] == yv))}
        abl.append({"stage": st["stage"], "what": st["what"],
                    "config": st["cfg"].label(),
                    **{f"dev_{k}": v for k, v in st["dev"].items()},
                    **{f"val_{k}": v for k, v in stats(e).items()},
                    **{f"val_{k}": round(v, 6) for k, v in acc.items()}})
        curves[f"{st['stage']} {st['what']}"] = e
        outs[st["stage"]] = (out, e, acc)
        LOG.info("VALIDATION %s %-40s mean %.3f m  median %.3f m  joint acc %.4f",
                 st["stage"], st["what"], e.mean(), np.median(e),
                 acc["joint_building_floor_accuracy"])
    A = pd.DataFrame(abl)
    A.to_csv(METRICS / "positioning_ablation.csv", index=False)

    # sanity: S0 must reproduce PHASE I's baseline exactly
    isum = load_json(RESULTS / "ips_summary.json")
    b = isum["conditions"]["baseline_all_520"]["result"]["knn"]
    s0e = outs["S0"][1]
    assert abs(s0e.mean() - b["positioning_error"]["mean_error_ground_m"]) < 1e-3, \
        "S0 does not reproduce the PHASE I baseline"

    # ---- per-row prediction files (the manual checks read these) -----------
    # study k-NN: exactly PHASE I's classifier and coordinate rule
    sf = prediction_frame(va, study, 1, 0, study["lists"], None, False)
    assert abs((sf.true_building.astype(str) + "_" + sf.true_floor.astype(str)
                == sf.pred_building.astype(str) + "_" + sf.pred_floor.astype(str)
                ).mean() - b["joint_building_floor_accuracy"]) < 1e-6
    sf.to_csv(PRED_DIR / "val_predictions_study_knn.csv", index=False)

    out_f, e_f, acc_f = outs[stages[-1]["stage"]]
    of = prediction_frame(va, out_f, final.k, final.power, out_f["lists"],
                          out_f["delta"], bool(final.offset_range))
    of.to_csv(PRED_DIR / "val_predictions_optimised.csv", index=False)
    delta_share = (pd.Series(out_f["delta"]).value_counts(normalize=True)
                   .sort_index().round(4))
    LOG.info("device offset chosen on validation: %s",
             {f"{k:+g} dB": v for k, v in delta_share.items()})

    # ---- the selected model on the WAP sets of PHASE I ---------------------
    I = pd.read_csv(METRICS / "ips_results.csv")
    col_of = {w: j for j, w in enumerate(wap)}
    picks = ["baseline_all_520", "baseline_detected_465",
             "control_top_mi__n200", "control_top_support__n200"]
    for fam in ("huim_union", "huim_topn"):
        for model, g in I[I["family"] == fam].groupby("utility_model"):
            picks.append(g.loc[g["joint_building_floor_accuracy"].idxmax()]
                         ["condition"])
    for n in (91, 86, 79, 75):
        picks += [f"control_top_mi__n{n}", f"control_top_support__n{n}"]
    rows = []
    for cond in dict.fromkeys(picks):
        r = I[I["condition"] == cond]
        if not len(r):
            continue
        r = r.iloc[0]
        cols = [col_of[w] for w in str(r["selected_waps"]).split(";")]
        pos = Positioner(W, C, y, final, cols)
        out = pos.predict(Wv)
        e = err_ground(out["xy"], Cv)
        s = stats(e)
        letter = {"A_signal": "A", "B_discriminative": "B",
                  "C_rare_discriminative": "C"}.get(r["utility_model"], "")
        if cond.startswith("baseline_all"):
            lab = "All 520 WAP"
        elif cond.startswith("baseline_detected"):
            lab = "Detected 465 WAP"
        elif cond.startswith("control"):
            kind = "MI" if "_mi_" in cond else "detection count"
            lab = f"Top-{len(cols)} by {kind}"
        else:
            kind = "union" if cond.startswith("huim_union") else "top-n"
            lab = (f"HUIM {kind} {letter}\n{len(cols)} WAP, "
                   f"minUtil {float(r['rel_minutil_pct']):g}%")
        rows.append({"condition": cond, "label": lab,
                     "utility_model": r["utility_model"],
                     "rel_minutil_pct": r["rel_minutil_pct"],
                     "n_waps": len(cols),
                     "study_mean_ground_m": r["pos_mean_error_ground_m"],
                     "study_median_ground_m": r["pos_median_error_ground_m"],
                     "study_joint_accuracy": r["joint_building_floor_accuracy"],
                     "opt_mean_ground_m": s["mean_ground_m"],
                     "opt_median_ground_m": s["median_ground_m"],
                     "opt_p90_ground_m": s["p90_ground_m"],
                     "opt_joint_accuracy": round(float(np.mean(out["label"] == yv)), 6)})
        LOG.info("%-48s %3d WAP  study %.2f m -> optimised %.2f m",
                 cond, len(cols), r["pos_mean_error_ground_m"],
                 s["mean_ground_m"])
    Cn = pd.DataFrame(rows)
    Cn.to_csv(METRICS / "positioning_conditions.csv", index=False)
    show = Cn[~Cn["condition"].str.match(r"control_.*__n(91|86|79|75)$")]
    figure(A, curves, show.reset_index(drop=True))

    dump_json({
        "phase": "PHASE I3 - positioning error optimisation",
        "environment": environment_info(),
        "protocol": {
            "selection_split": f"GroupKFold({N_FOLDS}) over USERID on "
                               "trainingData (leave-users-out)",
            "selection_criterion": "mean ground-metre error on the dev folds",
            "validation_used_for": "evaluation only, once per stage",
            "stages": "S0 study k-NN; S1 representation x distance at k=1; "
                      "S2 + k and 1/d^p; S3 + device-offset search; "
                      "S4 + ensemble of two representations",
            "min_gain_m": MIN_GAIN_M,
            "grids": {"representations": REPRESENTATIONS,
                      "distances": DISTANCES, "k": K_GRID, "powers": POWERS,
                      "offset_ranges_db": OFFSET_RANGES,
                      "offset_step_db": OFFSET_STEP},
            "ground_factor": GROUND,
        },
        "stages": [{"stage": s["stage"], "what": s["what"],
                    "config": asdict(s["cfg"]), "label": s["cfg"].label(),
                    "dev": s["dev"]} for s in stages],
        "selected_config": asdict(final),
        "selected_label": final.label(),
        "validation_offset_share": {f"{k:+g}": float(v)
                                    for k, v in delta_share.items()},
        "validation": {
            "ablation": abl,
            "selected": {
                **{k: round(v, 6) for k, v in acc_f.items()},
                "positioning_error": {
                    "mean_error": round(float(e_f.mean() / GROUND), 4),
                    **{f"{k}_error_ground_m": round(float(v), 4) for k, v in (
                        ("mean", e_f.mean()), ("median", np.median(e_f)),
                        ("p75", np.percentile(e_f, 75)),
                        ("p90", np.percentile(e_f, 90)),
                        ("p95", np.percentile(e_f, 95)))}},
            },
        },
        "conditions": rows,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_wall_clock_s": round(time.perf_counter() - t_start, 1),
    }, RESULTS / "positioning_optimisation.json")
    LOG.info("done in %.0fs", time.perf_counter() - t_start)


if __name__ == "__main__":
    main()
