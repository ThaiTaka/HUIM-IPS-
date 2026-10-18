"""HUIM-only optimisation on UJIIndoorLoc - shared evaluation code.

Every configuration evaluated here positions with a HUIM-selected AP set and
the S4 positioner of PHASE I3 (exponential + Bray-Curtis, k = 12, w = 1/d^4,
device-offset search +-6 dB, ensemble with the positive representation).
Nothing in this module uses all 520 APs.

Protocol (the same as PHASE I3):
* every choice - utility model, minUtil, selection rule - is made on the mean
  ground-metre error of the 6 leave-users-out folds of trainingData
  (GroupKFold over USERID);
* validationData is evaluated once per configuration and never used to choose.

Caveat recorded with the results: the HUIs are mined on the whole of
trainingData, so the dev folds of an AP set are not fully independent of its
selection (Model B/C also read BUILDINGID_FLOOR there). The bias is shared by
every candidate, so it does not favour one of them; the validation number is
the clean one.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
import optimize_positioning as op                          # noqa: E402
from preprocess_uji import NOT_DETECTED, load_splits       # noqa: E402
from utils import RESULTS, get_logger                      # noqa: E402

LOG = get_logger("huim_opt", "huim_opt.log")
OUT = RESULTS / "huim_opt"
OUT.mkdir(parents=True, exist_ok=True)
HUI_DIR = RESULTS / "hui"
RUNS = RESULTS / "multi_dataset" / "uji"

S4 = op.Config("exponential", "braycurtis", 12, 4.0, 6, "positive")
MODEL_TAG = {"A": "A_signal", "B": "B_discriminative",
             "C": "C_rare_discriminative"}


# ------------------------------------------------------------------- data
class Data:
    def __init__(self) -> None:
        tr, va = load_splits()
        self.tr, self.va = tr, va
        self.wap = [c for c in tr.columns if c.startswith("WAP")]
        self.col_of = {w: j for j, w in enumerate(self.wap)}
        self.W = tr[self.wap].to_numpy(np.float64)
        self.Wv = va[self.wap].to_numpy(np.float64)
        self.C = tr[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
        self.Cv = va[["LONGITUDE", "LATITUDE"]].to_numpy(np.float64)
        self.y = (tr.BUILDINGID.astype(str) + "_" + tr.FLOOR.astype(str)).to_numpy()
        self.yv = (va.BUILDINGID.astype(str) + "_" + va.FLOOR.astype(str)).to_numpy()
        self.b = tr.BUILDINGID.to_numpy()
        self.bv = va.BUILDINGID.to_numpy()
        self.folds = list(GroupKFold(n_splits=op.N_FOLDS).split(
            self.W, groups=tr["USERID"]))
        op.GROUND = 0.766126


@lru_cache(maxsize=1)
def data() -> Data:
    return Data()


# --------------------------------------------------------------- HUI sets
def huim_runs(model: str) -> pd.DataFrame:
    return pd.read_csv(RUNS / f"huim_runs__{model}.csv")


def union_of_run(model: str, pct: float) -> list[str] | None:
    """WAPs occurring in at least one HUI of a COMPLETED run, sorted by
    descending utility contribution (feature_selection.select_waps order).
    None for a run that was aborted: its HUI set is incomplete, so its union
    is not the union at that minUtil."""
    R = huim_runs(model)
    r = R[np.isclose(R.rel_minutil_pct, pct)]
    if not len(r) or r.iloc[0].status != "COMPLETED":
        return None
    stats = wap_stats(model, pct)
    return sorted(stats, key=lambda w: (-stats[w]["utility_contribution"], w))


def wap_stats(model: str, pct: float) -> dict:
    tag = f"{MODEL_TAG[model]}__{pct:g}pct"
    d = json.loads((HUI_DIR / f"{tag}__waps.json").read_text(encoding="utf-8"))
    return d["per_wap"]


# ------------------------------------------------------------- evaluation
def _summary(prefix: str, e: np.ndarray, lab, ytrue, btrue) -> dict:
    lab = np.asarray(lab)
    pb = np.array([s.split("_")[0] for s in lab]).astype(int)
    out = {f"{prefix}_mean_m": float(e.mean()),
           f"{prefix}_median_m": float(np.median(e)),
           f"{prefix}_p90_m": float(np.percentile(e, 90)),
           f"{prefix}_building_acc": float((pb == btrue).mean()),
           f"{prefix}_joint_acc": float((lab == ytrue).mean())}
    for b in (0, 1, 2):
        out[f"{prefix}_mean_b{b}_m"] = float(e[btrue == b].mean())
    return out


class WeightedPositioner(op.Positioner):
    """S4 with one weight per AP multiplied into both representations, i.e. a
    weighted Bray-Curtis distance sum_i w_i|x_i - y_i| / sum_i w_i(x_i + y_i).
    Used by the 'weighted' selection rule of step 6."""

    def __init__(self, W_ref, coords, labels, cfg, cols, w) -> None:
        super().__init__(W_ref, coords, labels, cfg, cols=cols)
        self.w = np.asarray(w, dtype=np.float64)

    def ref(self, kind):
        if kind not in self._ref:
            self._ref[kind] = op.representation(self.W_ref, kind) * self.w
        return self._ref[kind]

    def member(self, Wq, kind, folds=None):
        cfg = self.cfg
        deltas = ([0.0] if not cfg.offset_range else
                  list(np.arange(-cfg.offset_range, cfg.offset_range + 1e-9,
                                 op.OFFSET_STEP)))
        by = {}
        for d in deltas:
            Xq = op.representation(op.shift(Wq[:, self.cols], d), kind) * self.w
            by[float(d)] = (op.knn_folds(self.ref(kind), Xq, cfg.distance, folds)
                            if folds is not None else
                            op.knn(self.ref(kind), Xq, cfg.distance))
        if len(by) == 1:
            return by[0.0], np.zeros(len(Wq))
        return op.offset_select(by, cfg.offset_range)


def positioner(W, C, y, cfg, cols, w=None) -> op.Positioner:
    if w is None:
        return op.Positioner(W, C, y, cfg, cols=cols)
    return WeightedPositioner(W, C, y, cfg, cols, w)


def evaluate(cols, cfg: op.Config = S4, dev: bool = True, w=None) -> dict:
    """S4 on the AP columns `cols`: dev folds (leave-users-out) and validation.
    Returns summary statistics plus the raw per-row arrays under '_val' and
    '_dev' for later per-building tables and ensembles."""
    D = data()
    cols = list(cols)
    pos = positioner(D.W, D.C, D.y, cfg, cols, w)
    t0 = time.perf_counter()
    ov = pos.predict(D.Wv)
    ev = op.err_ground(ov["xy"], D.Cv)
    res = {"n_ap": len(cols),
           **_summary("val", ev, ov["label"], D.yv, D.bv),
           "val_no_ap_seen_pct": float(
               100 * ((D.Wv[:, cols] == NOT_DETECTED).all(axis=1)).mean()),
           "val_no_ap_seen_b1_pct": float(
               100 * ((D.Wv[D.bv == 1][:, cols] == NOT_DETECTED).all(axis=1)).mean()),
           "_val": {"xy": ov["xy"], "err": ev, "label": np.asarray(ov["label"])}}
    if dev:
        od = pos.predict(D.W, folds=D.folds)
        ed = op.err_ground(od["xy"], D.C)
        res.update(_summary("dev", ed, od["label"], D.y, D.b))
        res["_dev"] = {"xy": od["xy"], "err": ed, "label": np.asarray(od["label"])}
    res["seconds"] = round(time.perf_counter() - t0, 1)
    return res


def public(r: dict) -> dict:
    """The CSV-able part of an evaluate() result."""
    return {k: (round(v, 4) if isinstance(v, float) else v)
            for k, v in r.items() if not k.startswith("_")}


# ------------------------------------------------ maxU and the union at any θ
THETA_GRID = [0.5, 1.0, 1.5, 1.9294, 2.5, 3.0]     # minUtil, % of total utility


@lru_cache(maxsize=None)
def prep_and_q():
    from preprocess_uji import fit_preprocessor
    D = data()
    prep = fit_preprocessor(D.tr)
    return prep, prep.internal_utility_matrix(D.tr).astype(np.float64)


def utility_matrix(model: str, scope: str) -> np.ndarray:
    """u(i,T) = q(i,T) p(i) on the transactions of `scope`: 'global' (all of
    trainingData) or 'b0' / 'b1' / 'b2' (one building). For Model B/C, p(i)
    is the mutual information with the location label OF THAT SCOPE:
    BUILDINGID_FLOOR globally, the floor inside one building."""
    from utility_models import build_external_utility
    D = data()
    prep, Q = prep_and_q()
    rows = (np.ones(len(D.tr), bool) if scope == "global"
            else D.b == int(scope[1]))
    um = build_external_utility(model, D.tr[rows], prep, D.y[rows], "training")
    p = np.array([um.external_utility[w] for w in D.wap])
    return Q[rows] * p


# union sizes are reported on this finer grid; S4 is evaluated on THETA_GRID
# (contains every minUtil at which a PHASE H EFIM run completed with HUIs, so
# the global tables can be checked against EFIM: src/check_union_search.py)
THETA_CURVE = sorted({0.5, 0.75, 1.0, 1.25, 1.5, 1.7321, 1.9294, 2.0, 2.5, 3.0,
                      3.5, 4.0, 5.0, 7.5, 10.0} | set(THETA_GRID))


def union_table(model: str, scope: str) -> dict:
    """HUI union membership of every AP at every θ of THETA_CURVE, cached on
    disk together with its cost (wall-clock, peak memory, search nodes)."""
    from huim.union_search import union_levels
    from utils import MemoryMonitor
    f = OUT / f"union_{scope}_{model}.npz"
    if f.exists():
        z = np.load(f)
        return {k: z[k] for k in z.files}
    lv = OUT / "levels"
    if all((lv / f"union_level_{scope}_{model}_{t:g}.npz").exists()
           for t in THETA_CURVE):
        return assemble_union_table(model, scope)
    U = utility_matrix(model, scope)
    total = float(U.sum())
    with MemoryMonitor() as mem:
        R = union_levels(U, [total * t / 100.0 for t in THETA_CURVE], log=LOG)
    pct = R.thresholds / total * 100.0
    out = {"theta_pct": pct, "member": R.member, "witness_util": R.witness_util,
           "level_seconds": R.seconds, "level_nodes": R.nodes,
           "seconds": np.float64(R.seconds.sum()),
           "peak_delta_mb": np.float64(mem.as_dict()["peak_delta_mb"]),
           "total_utility": np.float64(total),
           "n_transactions": np.int64((U.sum(axis=1) > 0).sum())}
    np.savez_compressed(f, **out)
    LOG.info("union %s %s: %.1fs, %.1f MB, %d nodes", model, scope,
             out["seconds"], out["peak_delta_mb"], R.nodes.sum())
    return out


def union_cols(model: str, scope: str, theta_pct: float) -> list[int]:
    """Columns of the HUI union at minUtil = theta % of the scope's total
    utility, ordered by the highest minUtil at which each AP is still in the
    union (then by column). Before the scope's table is assembled, a single
    finished level file is used; a level not computed yet raises LookupError."""
    if not (OUT / f"union_{scope}_{model}.npz").exists():
        lv = OUT / "levels"
        if not all((lv / f"union_level_{scope}_{model}_{t:g}.npz").exists()
                   for t in THETA_CURVE):
            f = lv / f"union_level_{scope}_{model}_{theta_pct:g}.npz"
            if not f.exists():
                raise LookupError(f"union {model} {scope} {theta_pct}% not computed yet")
            z = np.load(f)
            # files written before the time limit existed have no status: they
            # ran to completion by construction
            if "status" in z.files and str(z["status"]) != "COMPLETED":
                raise LookupError(f"union {model} {scope} {theta_pct}% did not complete")
            return [int(j) for j in np.flatnonzero(z["member"])]
    T = union_table(model, scope)
    k = int(np.argmin(np.abs(T["theta_pct"] - theta_pct)))
    assert abs(T["theta_pct"][k] - theta_pct) < 1e-6, theta_pct
    if "level_status" in T and str(T["level_status"][k]) != "COMPLETED":
        raise LookupError(f"union {model} {scope} {theta_pct}% did not complete")
    M = T["member"]
    first = np.where(M.any(axis=1), M.argmax(axis=1), M.shape[1])
    c = np.flatnonzero(M[:, k])
    return [int(j) for j in c[np.lexsort((c, first[c]))]]


# -------------------------------------------------- per-building positioning
class PBModel:
    """Per-building HUIM positioning, two stages, both on HUIM APs only.
    1. building = weighted vote of the S4 neighbours on AP_0 u AP_1 u AP_2
       (all reference rows);
    2. inside the predicted building, S4 on that building's own AP set and
       reference rows -> (x, y) and floor.
    Building the object is the 'training' (radio maps per AP set); predict()
    is the online part that the timing measures."""

    def __init__(self, ap_sets: dict, cfg: op.Config = S4,
                 weights: dict | None = None, ref: np.ndarray | None = None):
        D = data()
        ref = np.arange(len(D.W)) if ref is None else ref
        self.ap_sets = ap_sets
        self.allc = sorted(set().union(*ap_sets.values()))
        # stage 1 only needs the vote, which Positioner takes from the first
        # ensemble member's neighbours - the second member would not change it
        self.p1 = op.Positioner(D.W[ref], D.C[ref], D.b[ref].astype(str),
                                replace(cfg, ensemble_with=""), cols=self.allc)
        self.per = {}
        for b, cols in ap_sets.items():
            rb = ref[D.b[ref] == b]
            w = None if weights is None else weights[b]
            self.per[b] = positioner(D.W[rb], D.C[rb], D.y[rb], cfg, cols, w)
        self.n_ref = {b: int((D.b[ref] == b).sum()) for b in ap_sets}
        self.n_ref_all = len(ref)

    def predict(self, Wq: np.ndarray) -> dict:
        pb = np.asarray(self.p1.predict(Wq)["label"]).astype(int)
        xy = np.zeros((len(Wq), 2))
        lab = np.empty(len(Wq), dtype=object)
        for b, pos in self.per.items():
            q = pb == b
            if not q.any():
                continue
            o = pos.predict(Wq[q])
            xy[q] = o["xy"]
            lab[q] = o["label"]
        return {"xy": xy, "label": lab.astype(str), "building": pb}

    def radio_map_mb(self) -> float:
        """float64: stage 1 holds one representation over AP_0 u AP_1 u AP_2,
        stage 2 two representations (the S4 ensemble) per building."""
        cells = self.n_ref_all * len(self.allc) + 2 * sum(
            self.n_ref[b] * len(c) for b, c in self.ap_sets.items())
        return cells * 8 / 2 ** 20


def _pb_predict(ref: np.ndarray, Wq: np.ndarray, ap_sets: dict, cfg: op.Config,
                weights: dict | None = None) -> dict:
    return PBModel(ap_sets, cfg, weights, ref).predict(Wq)


def evaluate_per_building(ap_sets: dict, cfg: op.Config = S4,
                          dev: bool = True, weights: dict | None = None) -> dict:
    D = data()
    t0 = time.perf_counter()
    ov = _pb_predict(np.arange(len(D.W)), D.Wv, ap_sets, cfg, weights)
    ev = op.err_ground(ov["xy"], D.Cv)
    allc = sorted(set().union(*ap_sets.values()))
    res = {"n_ap": len(allc),
           **{f"n_ap_b{b}": len(c) for b, c in ap_sets.items()},
           **_summary("val", ev, ov["label"], D.yv, D.bv),
           "val_no_ap_seen_pct": float(100 * np.mean([
               (D.Wv[r, ap_sets[D.bv[r]]] == NOT_DETECTED).all()
               for r in range(len(D.Wv))])),
           "_val": {"xy": ov["xy"], "err": ev, "label": ov["label"]}}
    if dev:
        xy = np.zeros((len(D.W), 2))
        lab = np.empty(len(D.W), dtype=object)
        for tri, dvi in D.folds:
            o = _pb_predict(tri, D.W[dvi], ap_sets, cfg, weights)
            xy[dvi], lab[dvi] = o["xy"], o["label"]
        ed = op.err_ground(xy, D.C)
        lab = lab.astype(str)
        res.update(_summary("dev", ed, lab, D.y, D.b))
        res["_dev"] = {"xy": xy, "err": ed, "label": lab}
    res["seconds"] = round(time.perf_counter() - t0, 1)
    return res


# ------------------------------------------- full HUI sets (for step 6 rules)
def hui_stats(model: str, scope: str, theta_pct: float,
              time_limit_s: float = 300.0, max_huis: int = 1_000_000) -> dict:
    """Per-AP statistics of the complete HUI set (feature_selection.
    per_wap_statistics), needed by the top-n / frequent / weighted rules. Read
    from PHASE H for the global scope; mined with EFIM for one building.
    Returns {'status', 'n_huis', 'runtime_s', 'peak_delta_mb', 'per_wap'}."""
    from feature_selection import per_wap_statistics
    from huim.efim import mine_efim
    from utility_models import build_external_utility
    from utils import MemoryMonitor
    f = OUT / f"huistats_{scope}_{model}_{theta_pct:g}pct.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    if scope == "global":
        R = huim_runs(model)
        r = R[np.isclose(R.rel_minutil_pct, theta_pct)]
        if len(r) and r.iloc[0].status == "COMPLETED":
            out = {"status": "COMPLETED", "n_huis": int(r.iloc[0].n_huis),
                   "runtime_s": float(r.iloc[0].runtime_s),
                   "peak_delta_mb": float(r.iloc[0].peak_memory_delta_mb),
                   "per_wap": wap_stats(model, theta_pct)}
            f.write_text(json.dumps(out), encoding="utf-8")
            return out
    D = data()
    prep, _Q = prep_and_q()
    rows = (np.ones(len(D.tr), bool) if scope == "global"
            else D.b == int(scope[1]))
    tr = D.tr[rows]
    um = build_external_utility(model, tr, prep, D.y[rows], "training")
    txs = [t for t in prep.transactions(tr)[0] if t]
    mu = um.total_database_utility(txs) * theta_pct / 100.0
    t0 = time.perf_counter()
    with MemoryMonitor() as mem:
        huis, st = mine_efim(txs, um.external_utility, min_util=mu,
                             time_limit_s=time_limit_s, max_huis=max_huis)
    out = {"status": st.status, "n_huis": len(huis),
           "runtime_s": round(time.perf_counter() - t0, 3),
           "peak_delta_mb": mem.as_dict()["peak_delta_mb"],
           "per_wap": per_wap_statistics(huis) if huis else {}}
    f.write_text(json.dumps(out), encoding="utf-8")
    LOG.info("EFIM %s %s %g%%: %s, %d HUIs, %.1fs", model, scope, theta_pct,
             st.status, len(huis), out["runtime_s"])
    return out


# ------------------------------------------------------------- ensembles
def load_preds(name: str) -> dict:
    z = np.load(OUT / "preds" / f"{name}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def ensemble(names: list[str], how: str = "mean") -> dict:
    """Combine saved per-row predictions of several configurations: (x, y) by
    the mean or the coordinate-wise median, building-floor by majority vote
    (ties go to the first member)."""
    D = data()
    P = [load_preds(n) for n in names]
    res = {"members": " + ".join(names), "how": how}
    for split, C, y, b in (("val", D.Cv, D.yv, D.bv), ("dev", D.C, D.y, D.b)):
        xy = np.stack([p[f"{split}_xy"] for p in P])
        xy = xy.mean(axis=0) if how == "mean" else np.median(xy, axis=0)
        labs = np.stack([p[f"{split}_label"].astype(str) for p in P])
        lab = []
        for col in labs.T:
            v, c = np.unique(col, return_counts=True)
            best = v[c == c.max()]
            lab.append(next(x for x in col if x in best))
        e = op.err_ground(xy, C)
        res.update(_summary(split, e, np.array(lab), y, b))
        res[f"_{split}"] = {"xy": xy, "err": e, "label": np.array(lab)}
    return res


# ------------------------------------------------------- time and memory
def time_and_memory(predict, n_ref: int, n_ap: int, repeats: int = 3) -> dict:
    """Wall-clock of locating all 1,111 validation rows in one batch (median of
    `repeats` after one warm-up, every core), peak RSS above the pre-run
    baseline, and the radio-map size (n_ref x n_ap float64, x2 for the two
    representations of the S4 ensemble)."""
    from utils import MemoryMonitor
    D = data()
    predict(D.Wv[:64])
    ts, peaks = [], []
    for _ in range(repeats):
        with MemoryMonitor() as mem:
            t0 = time.perf_counter()
            predict(D.Wv)
            ts.append(time.perf_counter() - t0)
        peaks.append(mem.as_dict()["peak_delta_mb"])
    t = float(np.median(ts))
    return {"total_s": round(t, 4), "ms_per_fp": round(1000 * t / len(D.Wv), 4),
            "samples_s": [round(x, 4) for x in ts],
            "peak_delta_mb": round(float(np.median(peaks)), 2),
            "radio_map_mb": round(2 * n_ref * n_ap * 8 / 2 ** 20, 3) if n_ap else None}


# ------------------------------------------------- one minUtil level at a time
LEVEL_TIME_LIMIT_S = 30 * 60      # per minUtil level; beyond it: "TIMEOUT"


def union_level(model: str, scope: str, theta_pct: float,
                time_limit_s: float | None = LEVEL_TIME_LIMIT_S) -> dict:
    """Union at ONE θ, computed on its own (no carry-over from other levels),
    cached as union_level_<scope>_<model>_<θ>.npz with its cost. Levels are
    independent, so they can run in parallel processes."""
    from huim.union_search import TimeLimit, _union_at
    from utils import MemoryMonitor
    f = OUT / "levels" / f"union_level_{scope}_{model}_{theta_pct:g}.npz"
    f.parent.mkdir(exist_ok=True)
    if f.exists():
        z = np.load(f)
        return {k: z[k] for k in z.files}
    U = utility_matrix(model, scope)
    total = float(U.sum())
    covered = np.zeros(U.shape[1], bool)
    wutil = np.zeros(U.shape[1])
    status = "COMPLETED"
    with MemoryMonitor() as mem:
        t0 = time.perf_counter()
        try:
            nodes = _union_at(U, total * theta_pct / 100.0, covered, wutil,
                              time_limit_s)
        except TimeLimit as e:
            nodes, status = int(e.args[0]), "TIMEOUT"
        el = time.perf_counter() - t0
    out = {"theta_pct": np.float64(theta_pct), "member": covered,
           "status": np.array(status),
           "witness_util": wutil, "seconds": np.float64(el),
           "nodes": np.int64(nodes),
           "peak_delta_mb": np.float64(mem.as_dict()["peak_delta_mb"]),
           "total_utility": np.float64(total),
           "n_transactions": np.int64((U.sum(axis=1) > 0).sum())}
    np.savez_compressed(f, **out)
    LOG.info("level %s %s %g%%: %s, %d items, %d nodes, %.1fs", model, scope,
             theta_pct, status, covered.sum(), nodes, el)
    return out


def assemble_union_table(model: str, scope: str) -> dict:
    """union_<scope>_<model>.npz built from the per-level files."""
    L = [union_level(model, scope, t) for t in sorted(THETA_CURVE, reverse=True)]
    out = {"theta_pct": np.array([float(l["theta_pct"]) for l in L]),
           "member": np.stack([l["member"] for l in L], axis=1),
           "witness_util": np.stack([l["witness_util"] for l in L], axis=1),
           "level_seconds": np.array([float(l["seconds"]) for l in L]),
           "level_nodes": np.array([int(l["nodes"]) for l in L]),
           "level_status": np.array([str(l["status"]) if "status" in l else "COMPLETED"
                                     for l in L]),
           "level_peak_mb": np.array([float(l["peak_delta_mb"]) for l in L]),
           "seconds": np.float64(sum(float(l["seconds"]) for l in L)),
           "peak_delta_mb": np.float64(max(float(l["peak_delta_mb"]) for l in L)),
           "total_utility": L[0]["total_utility"],
           "n_transactions": L[0]["n_transactions"]}
    # the union can only grow as minUtil falls - a free consistency check
    ok = out["level_status"] == "COMPLETED"
    M = out["member"][:, ok]
    assert (M[:, 1:] >= M[:, :-1]).all(), "union not monotone in minUtil"
    import os
    tmp = OUT / f"union_{scope}_{model}.tmp.npz"
    np.savez_compressed(tmp, **out)
    os.replace(tmp, OUT / f"union_{scope}_{model}.npz")   # readers never see half a file
    return out
