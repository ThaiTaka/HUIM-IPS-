"""HUIM-only optimisation on the datasets of dataset-20261013T020803Z-1-001
(BAOCAO1): UJI_LIB floor 3, DLULIB, HCXY and HUS (test-copy rows removed).

The UJIIndoorLoc procedure of src/huim_opt.py / src/run_huim_opt.py with only
the data changed:

  unions  exact HUI union at every minUtil of theta_curve(key) (src/huim/
          union_search.py), Models A/B/C, over the whole training set and per
          zone - the floors of DLULIB, 3 k-means zones of the reference points
          for the one-floor sets UJI_LIB3 and HCXY (HUS: 5 APs, no zones)
  step 3  global HUIM: every distinct union, the dataset's positioner
  step 4  per-zone HUIM: zone vote, then one positioner per zone
  step 5  positioner re-selected on the dev folds for the best HUIM AP set
          (optimize_positioning.select_on_dev on the HUIM columns only)
  step 6  selection rules on complete EFIM HUI sets (top-n, frequent, weighted)
  step 7  ensembles of HUIM configurations
  step 8  online time and memory (run with nothing else on the machine)
  check   union search against the union of every completed EFIM run

Protocol: every choice is made on the dev folds of the training data (grouped
as in results/multi_dataset/<key>/dataset_summary.json, cv_group); each test
file is evaluated once per configuration and never used to choose.

    python src/huim_multi.py unions --workers 10
    python src/huim_multi.py steps --key hcxy --steps 3 4 5 6 7
    python src/huim_multi.py check
    python src/huim_multi.py step8
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from dataclasses import asdict, replace
from functools import cached_property, lru_cache
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
import multi_datasets as md                                # noqa: E402
import optimize_positioning as op                          # noqa: E402
from huim_opt import WeightedPositioner                    # noqa: E402
from ips_model import RANDOM_SEED                          # noqa: E402
from preprocess_uji import NOT_DETECTED, fit_preprocessor  # noqa: E402
from utils import RESULTS, MemoryMonitor, get_logger       # noqa: E402

LOG = get_logger("huim_multi", "huim_multi.log")
OUT = RESULTS / "huim_multi"
MD = RESULTS / "multi_dataset"
KEYS = ("uji_lib3", "dlulib", "hcxy", "hus_dedup")
MODELS = ("A", "B", "C")
MODEL_TAG = {"A": "A_signal", "B": "B_discriminative", "C": "C_rare_discriminative"}

BASE_CURVE = [50.0, 30.0, 20.0, 15.0, 10.0, 7.5, 5.0, 4.0, 3.0, 2.0, 1.5, 1.0,
              0.75, 0.5, 0.25, 0.1, 0.05]
# the minUtil of the HUIM Model A configuration the earlier multi-dataset run
# used (results/multi_dataset/comparison.csv) - the starting point
START_THETA = {"uji_lib3": 1.0, "dlulib": 1.0, "hcxy": 6.1237, "hus_dedup": 20.0}
ZONE_K = 3
N_ZONES = {"uji_lib3": ZONE_K, "dlulib": 3, "hcxy": ZONE_K, "hus_dedup": 0}
LEVEL_TIME_LIMIT_S = 15 * 60
TIMING_ROWS = 1111
BALANCE = 1.05            # "balanced": fewest APs with dev <= 105 % of best


def efim_runs(key: str, model: str) -> pd.DataFrame:
    return pd.read_csv(MD / key / f"huim_runs__{model}.csv")


@lru_cache(maxsize=None)
def theta_curve(key: str) -> tuple:
    """minUtil levels (% of the scope's total utility), descending: the base
    grid, the starting minUtil and every minUtil an EFIM run used (so the
    union search can be checked against EFIM at the same levels)."""
    th = set(BASE_CURVE) | {START_THETA[key]}
    for m in MODELS:
        th |= {round(float(t), 6) for t in efim_runs(key, m).rel_minutil_pct}
    return tuple(sorted(th, reverse=True))


def tg(th: float) -> str:
    return f"{th:g}"


# ====================================================================== data
class DS:
    def __init__(self, key: str) -> None:
        b = md.load(key)
        tr = b.train
        self.key, self.b, self.title = key, b, b.title
        self.wap = b.wap_cols
        self.col_of = {w: j for j, w in enumerate(self.wap)}
        self.W = tr[self.wap].to_numpy(np.float64)
        self.C = tr[["X", "Y"]].to_numpy(np.float64)
        self.y = md.bf_label(tr)
        self.ycls = md.class_label(b, tr)
        self.rp = ("RP" + tr["RP"].astype(str)).to_numpy()
        self.gf = float(b.ground_factor)
        self.multi_floor = b.n_floors > 1
        # exactly run_multi_dataset.folds_for
        if b.group_col:
            self.folds = list(GroupKFold(n_splits=op.N_FOLDS).split(
                np.zeros(len(tr)), groups=tr[b.group_col]))
        else:
            self.folds = list(KFold(n_splits=op.N_FOLDS, shuffle=True,
                                    random_state=RANDOM_SEED).split(np.zeros(len(tr))))
        self.tests, self.prefix = {}, {}
        for i, (name, te) in enumerate(b.tests.items()):
            self.prefix[name] = "test" if i == 0 else f"test{i + 1}"
            self.tests[name] = {"W": te[self.wap].to_numpy(np.float64),
                                "C": te[["X", "Y"]].to_numpy(np.float64),
                                "y": md.bf_label(te), "df": te}
        pj = json.loads((MD / key / "positioning.json").read_text(encoding="utf-8"))
        self.cfg = op.Config(**pj["selected_config"])
        self.zone, self.zone_kind, self.centroids = self._zones()
        self.n_zones = 0 if self.zone is None else int(self.zone.max()) + 1
        assert self.n_zones == N_ZONES[key], (key, self.n_zones)

    def _zones(self):
        tr = self.b.train
        if self.multi_floor:
            fl = sorted(tr["FLOOR"].unique())
            return np.array([fl.index(f) for f in tr["FLOOR"]]), "tầng", None
        if N_ZONES[self.key] == 0:
            return None, None, None
        from sklearn.cluster import KMeans
        pos = tr[["X", "Y"]].drop_duplicates().to_numpy(np.float64)
        km = KMeans(n_clusters=ZONE_K, n_init=10, random_state=0).fit(pos)
        order = np.lexsort((km.cluster_centers_[:, 1], km.cluster_centers_[:, 0]))
        cent = km.cluster_centers_[order]                  # zones numbered by x
        return self._nearest(self.C, cent), "vùng", cent

    @staticmethod
    def _nearest(C, cent):
        return ((C[:, None, :] - cent[None]) ** 2).sum(axis=2).argmin(axis=1)

    def zone_of_test(self, name: str) -> np.ndarray | None:
        te = self.tests[name]["df"]
        if self.zone is None:
            return None
        if self.multi_floor:
            fl = sorted(self.b.train["FLOOR"].unique())
            return np.array([fl.index(f) for f in te["FLOOR"]])
        return self._nearest(self.tests[name]["C"], self.centroids)

    # ------------------------------------------------------------- utility
    @cached_property
    def prep_q(self):
        prep = fit_preprocessor(self.b.train)
        assert list(prep.wap_cols) == self.wap
        return prep, prep.internal_utility_matrix(self.b.train).astype(np.float64)

    def scopes(self) -> list[str]:
        return ["global"] + [f"z{z}" for z in range(self.n_zones)]

    def rows_of(self, scope: str) -> np.ndarray:
        if scope == "global":
            return np.ones(len(self.W), bool)
        return self.zone == int(scope[1:])

    def utility_matrix(self, model: str, scope: str) -> np.ndarray:
        """u(i,T) = q(i,T) p(i) on the transactions of the scope. Models B/C
        take p(i) from the mutual information with the dataset's location
        label (floor for DLULIB, reference point otherwise); inside one floor
        the floor is constant, so the reference point is used there."""
        from utility_models import build_external_utility
        rows = self.rows_of(scope)
        prep, Q = self.prep_q
        lab = self.ycls[rows]
        if len(np.unique(lab)) < 2:
            lab = self.rp[rows]
        um = build_external_utility(model, self.b.train[rows], prep, lab, "training")
        p = np.array([um.external_utility[w] for w in self.wap])
        return Q[rows] * p


@lru_cache(maxsize=None)
def data(key: str) -> DS:
    return DS(key)


def kdir(key: str, *sub) -> Path:
    p = OUT.joinpath(key, *sub)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ============================================================ union search
def union_table(key: str, model: str, scope: str, compute: bool = True) -> dict:
    """HUI union of every AP at every minUtil of theta_curve(key), from the
    highest minUtil down (items found at one level start covered at the next).
    Status per level: COMPLETED, TIMEOUT (LEVEL_TIME_LIMIT_S hit; lower levels
    are then SKIPPED). Once every AP present in the scope is in the union,
    lower levels are the same set (marked saturated, no search)."""
    from huim.union_search import TimeLimit, _union_at
    f = kdir(key, "union") / f"union_{scope}_{model}.npz"
    if f.exists():
        with np.load(f) as z:
            return {k: z[k] for k in z.files}
    if not compute:
        raise LookupError(f"{key} union {scope} {model} not computed")
    D = data(key)
    U = D.utility_matrix(model, scope)
    total = float(U.sum())
    present = (U > 0).any(axis=0)
    curve = theta_curve(key)
    K, m = len(curve), U.shape[1]
    part = f.with_suffix(".partial.npz")
    st = {"member": np.zeros((m, K), bool), "witness_util": np.zeros((m, K)),
          "level_seconds": np.zeros(K), "level_nodes": np.zeros(K, np.int64),
          "level_peak_mb": np.zeros(K), "saturated": np.zeros(K, bool),
          "level_status": np.array(["PENDING"] * K, dtype="<U10")}
    covered, wutil = np.zeros(m, bool), np.zeros(m)
    if part.exists():                       # resume after an interruption
        with np.load(part) as z:
            st = {k: z[k].copy() for k in st}
        done = np.flatnonzero(st["level_status"] != "PENDING")
        if len(done):
            covered = st["member"][:, done[-1]].copy()
            wutil = st["witness_util"][:, done[-1]].copy()
    stop = (st["level_status"] == "TIMEOUT").any()
    for k, th in enumerate(curve):
        if st["level_status"][k] != "PENDING":
            continue
        if stop:
            st["level_status"][k] = "SKIPPED"
        elif covered[present].all():
            st["level_status"][k], st["saturated"][k] = "COMPLETED", True
        else:
            with MemoryMonitor() as mem:
                t0 = time.perf_counter()
                try:
                    n = _union_at(U, total * th / 100.0, covered, wutil,
                                  LEVEL_TIME_LIMIT_S)
                    s = "COMPLETED"
                except TimeLimit as e:
                    n, s, stop = int(e.args[0]), "TIMEOUT", True
                st["level_seconds"][k] = time.perf_counter() - t0
            st["level_peak_mb"][k] = mem.as_dict()["peak_delta_mb"]
            st["level_nodes"][k], st["level_status"][k] = n, s
            LOG.info("%s union %s %s %s%%: %s, %d APs, %d nodes, %.1fs", key,
                     scope, model, tg(th), s, covered.sum(), n,
                     st["level_seconds"][k])
        st["member"][:, k], st["witness_util"][:, k] = covered, wutil
        np.savez_compressed(part, **st)
    out = {**st, "theta_pct": np.array(curve), "total_utility": np.float64(total),
           "n_transactions": np.int64((U.sum(axis=1) > 0).sum()),
           "n_items_present": np.int64(present.sum())}
    ok = out["level_status"] == "COMPLETED"
    M = out["member"][:, ok]
    assert (M[:, 1:] >= M[:, :-1]).all(), "union not monotone in minUtil"
    tmp = f.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, **out)
    tmp.replace(f)
    part.unlink(missing_ok=True)
    return out


def union_cols(key: str, model: str, scope: str, th: float) -> list[int]:
    """Columns of the union, ordered by the highest minUtil at which each AP
    is already in it, then by column. LookupError if the level did not
    complete."""
    T = union_table(key, model, scope, compute=False)
    k = int(np.argmin(np.abs(T["theta_pct"] - th)))
    assert abs(T["theta_pct"][k] - th) < 1e-6, (key, th)
    if str(T["level_status"][k]) != "COMPLETED":
        raise LookupError(str(T["level_status"][k]))
    M = T["member"]
    first = np.where(M.any(axis=1), M.argmax(axis=1), M.shape[1])
    c = np.flatnonzero(M[:, k])
    return [int(j) for j in c[np.lexsort((c, first[c]))]]


def _union_job(args) -> str:
    key, model, scope = args
    t0 = time.perf_counter()
    T = union_table(key, model, scope)
    return (f"{key} {scope} {model}: {list(T['level_status']).count('COMPLETED')}"
            f"/{len(T['level_status'])} levels, {time.perf_counter() - t0:.0f}s")


def all_union_jobs() -> list[tuple]:
    jobs = []
    for key in ("hcxy", "uji_lib3", "dlulib", "hus_dedup"):      # biggest first
        for scope in ["global"] + [f"z{z}" for z in range(N_ZONES[key])]:
            for m in MODELS:
                jobs.append((key, m, scope))
    return jobs


# =============================================================== positioning
def positioner(W, C, y, cfg, cols, w=None) -> op.Positioner:
    if w is None:
        return op.Positioner(W, C, y, cfg, cols=list(cols))
    return WeightedPositioner(W, C, y, cfg, list(cols), w)


def err_m(xy, C, gf) -> np.ndarray:
    return np.sqrt(((xy - C) ** 2).sum(axis=1)) * gf


def summ(prefix: str, e, lab, ytrue, multi_floor: bool) -> dict:
    d = {f"{prefix}_mean_m": float(e.mean()),
         f"{prefix}_median_m": float(np.median(e)),
         f"{prefix}_p90_m": float(np.percentile(e, 90)),
         f"{prefix}_max_m": float(e.max())}
    if multi_floor:
        d[f"{prefix}_floor_acc"] = float((np.asarray(lab).astype(str) == ytrue).mean())
    return d


def evaluate(D: DS, cols, cfg: op.Config, w=None, dev: bool = True) -> dict:
    cols = list(cols)
    pos = positioner(D.W, D.C, D.y, cfg, cols, w)
    t0 = time.perf_counter()
    res = {"n_ap": len(cols)}
    for name, T in D.tests.items():
        p = D.prefix[name]
        o = pos.predict(T["W"])
        e = err_m(o["xy"], T["C"], D.gf)
        res.update(summ(p, e, o["label"], T["y"], D.multi_floor))
        res[f"{p}_no_ap_seen_pct"] = float(
            100 * (T["W"][:, cols] == NOT_DETECTED).all(axis=1).mean())
        res["_" + p] = {"xy": o["xy"], "err": e,
                        "label": np.asarray(o["label"]).astype(str)}
    if dev:
        o = pos.predict(D.W, folds=D.folds)
        e = err_m(o["xy"], D.C, D.gf)
        res.update(summ("dev", e, o["label"], D.y, D.multi_floor))
        res["_dev"] = {"xy": o["xy"], "err": e,
                       "label": np.asarray(o["label"]).astype(str)}
    res["seconds"] = round(time.perf_counter() - t0, 1)
    return res


class ZoneModel:
    """Per-zone HUIM positioning (the per-building model of huim_opt.PBModel
    with zones = floors / k-means zones).
    1. zone = weighted vote of the neighbours on the union of the zone AP sets
       (all reference rows, first representation only - the vote reads the
       first member's neighbours);
    2. inside the predicted zone, the positioner on that zone's AP set and
       reference rows -> (x, y) and floor."""

    def __init__(self, D: DS, sets: dict, cfg: op.Config, weights=None, ref=None):
        ref = np.arange(len(D.W)) if ref is None else ref
        self.sets = sets
        self.allc = sorted(set().union(*sets.values()))
        self.p1 = op.Positioner(D.W[ref], D.C[ref], D.zone[ref].astype(str),
                                replace(cfg, ensemble_with=""), cols=self.allc)
        self.per, self.n_ref = {}, {}
        for z, cols in sets.items():
            rz = ref[D.zone[ref] == z]
            if not len(rz):
                continue
            w = None if weights is None else weights[z]
            self.per[z] = positioner(D.W[rz], D.C[rz], D.y[rz], cfg, cols, w)
            self.n_ref[z] = len(rz)
        self.n_ref_all = len(ref)
        self.n_members = 2 if cfg.ensemble_with else 1

    def predict(self, Wq: np.ndarray) -> dict:
        pz = np.asarray(self.p1.predict(Wq)["label"]).astype(int)
        xy = np.zeros((len(Wq), 2))
        lab = np.empty(len(Wq), dtype=object)
        for z, pos in self.per.items():
            q = pz == z
            if q.any():
                o = pos.predict(Wq[q])
                xy[q], lab[q] = o["xy"], o["label"]
        return {"xy": xy, "label": lab.astype(str), "zone": pz}

    def radio_map_mb(self) -> float:
        cells = self.n_ref_all * len(self.allc) + self.n_members * sum(
            self.n_ref[z] * len(self.sets[z]) for z in self.per)
        return cells * 8 / 2 ** 20


def evaluate_zone(D: DS, sets: dict, cfg: op.Config, weights=None,
                  dev: bool = True) -> dict:
    t0 = time.perf_counter()
    allc = sorted(set().union(*sets.values()))
    res = {"n_ap": len(allc), **{f"n_ap_z{z}": len(c) for z, c in sets.items()}}
    model = ZoneModel(D, sets, cfg, weights)
    for name, T in D.tests.items():
        p = D.prefix[name]
        o = model.predict(T["W"])
        e = err_m(o["xy"], T["C"], D.gf)
        res.update(summ(p, e, o["label"], T["y"], D.multi_floor))
        res[f"{p}_zone_acc"] = float((o["zone"] == D.zone_of_test(name)).mean())
        res["_" + p] = {"xy": o["xy"], "err": e, "label": o["label"], "zone": o["zone"]}
    if dev:
        xy = np.zeros((len(D.W), 2))
        lab = np.empty(len(D.W), dtype=object)
        pz = np.zeros(len(D.W), int)
        for tri, dvi in D.folds:
            o = ZoneModel(D, sets, cfg, weights, ref=tri).predict(D.W[dvi])
            xy[dvi], lab[dvi], pz[dvi] = o["xy"], o["label"], o["zone"]
        e = err_m(xy, D.C, D.gf)
        lab = lab.astype(str)
        res.update(summ("dev", e, lab, D.y, D.multi_floor))
        res["dev_zone_acc"] = float((pz == D.zone).mean())
        res["_dev"] = {"xy": xy, "err": e, "label": lab, "zone": pz}
    res["seconds"] = round(time.perf_counter() - t0, 1)
    return res


# ------------------------------------------------------------ cached rows
def public(r: dict) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v)
            for k, v in r.items() if not k.startswith("_")}


def cached(key: str, name: str, sig, fn) -> dict:
    """Evaluate once per configuration; a configuration whose signature (AP
    columns, weights, positioner) equals an earlier one reuses that result."""
    rows, preds = kdir(key, "rows"), kdir(key, "preds")
    f, pf = rows / f"{name}.json", preds / f"{name}.npz"
    if f.exists() and pf.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    h = hashlib.sha1(repr(sig).encode()).hexdigest()
    idx_f = rows / "_index.json"
    idx = json.loads(idx_f.read_text(encoding="utf-8")) if idx_f.exists() else {}
    src = idx.get(h)
    if src and (rows / f"{src}.json").exists() and (preds / f"{src}.npz").exists():
        row = {**json.loads((rows / f"{src}.json").read_text(encoding="utf-8")),
               "same_as": src}
        shutil.copyfile(preds / f"{src}.npz", pf)
    else:
        r = fn()
        arr = {}
        for split in [k for k in r if k.startswith("_")]:
            for k, v in r[split].items():
                arr[f"{split[1:]}_{k}"] = v
        np.savez_compressed(pf, **arr)
        row = public(r)
        idx[h] = name
        idx_f.write_text(json.dumps(idx), encoding="utf-8")
    f.write_text(json.dumps(row), encoding="utf-8")
    return row


def load_preds(key: str, name: str) -> dict:
    with np.load(kdir(key, "preds") / f"{name}.npz", allow_pickle=True) as z:
        return {k: z[k] for k in z.files}


def ap_names(D: DS, cols) -> str:
    return ";".join(D.wap[j] for j in cols)


def cfg_of(row) -> op.Config:
    return op.Config(**json.loads(row["positioner"]))


# ===================================================================== steps
def step3(key: str, cfg: op.Config | None = None, tag: str = "G",
          models=MODELS) -> pd.DataFrame:
    """Global HUIM at every minUtil level, one positioner."""
    D = data(key)
    cfg = cfg or D.cfg
    rows = []
    for m in models:
        T = union_table(key, m, "global", compute=False)
        for k, th in enumerate(theta_curve(key)):
            name = f"{tag}_{m}__{tg(th)}pct"
            base = {"config": name, "scope": "global", "model": m, "theta_pct": th,
                    "positioner": json.dumps(asdict(cfg)),
                    "positioner_label": cfg.label(),
                    "status": str(T["level_status"][k])}
            try:
                cols = union_cols(key, m, "global", th)
            except LookupError:
                rows.append(base)
                continue
            base["n_ap"] = len(cols)
            if not cols:
                rows.append(base)
                continue
            r = cached(key, name, ("global", asdict(cfg), tuple(cols)),
                       lambda c=cols: evaluate(D, c, cfg))
            rows.append({**base, **r, "aps": ap_names(D, cols)})
            LOG.info("%s %-20s %3d AP  dev %.3f  test %.3f", key, name, len(cols),
                     r["dev_mean_m"], r["test_mean_m"])
    T = pd.DataFrame(rows)
    T.to_csv(kdir(key) / f"step{'3' if tag == 'G' else '5'}_{tag}_global.csv",
             index=False)
    return T


def zone_sets(key: str, m: str, th: float) -> dict:
    D = data(key)
    return {z: union_cols(key, m, f"z{z}", th) for z in range(D.n_zones)}


def step4(key: str, cfg: op.Config | None = None, tag: str = "Z",
          models=MODELS) -> pd.DataFrame:
    """One HUIM per zone, minUtil relative to that zone's utility."""
    D = data(key)
    if not D.n_zones:
        pd.DataFrame().to_csv(kdir(key) / f"step4_{tag}_zones.csv", index=False)
        return pd.DataFrame()
    cfg = cfg or D.cfg
    rows = []
    for m in models:
        for th in theta_curve(key):
            name = f"{tag}_{m}__{tg(th)}pct"
            base = {"config": name, "scope": "zone", "model": m, "theta_pct": th,
                    "positioner": json.dumps(asdict(cfg)),
                    "positioner_label": cfg.label()}
            try:
                sets = zone_sets(key, m, th)
            except LookupError as e:
                rows.append({**base, "status": str(e)})
                continue
            base.update({"status": "COMPLETED",
                         **{f"n_ap_z{z}": len(c) for z, c in sets.items()},
                         "n_ap": len(set().union(*sets.values()))})
            if not all(sets.values()):           # a zone without AP: no model
                rows.append(base)
                continue
            r = cached(key, name, ("zone", asdict(cfg),
                                   tuple(tuple(sets[z]) for z in sorted(sets))),
                       lambda s=sets: evaluate_zone(D, s, cfg))
            rows.append({**base, **r, **{f"aps_z{z}": ap_names(D, c)
                                         for z, c in sets.items()}})
            LOG.info("%s %-20s %3d AP  dev %.3f  test %.3f", key, name, r["n_ap"],
                     r["dev_mean_m"], r["test_mean_m"])
    T = pd.DataFrame(rows)
    T.to_csv(kdir(key) / f"step4_{tag}_zones.csv", index=False)
    return T


def best_by_dev(T: pd.DataFrame) -> pd.Series:
    """Lowest dev error; ties (the same AP set at several minUtil) go to fewer
    APs, then the higher minUtil."""
    T = T.dropna(subset=["dev_mean_m"]).copy()
    T["_r"] = T.dev_mean_m.round(6)
    return T.sort_values(["_r", "n_ap", "theta_pct"],
                         ascending=[True, True, False]).iloc[0]


def read(key: str, name: str) -> pd.DataFrame:
    p = kdir(key) / name
    if not p.exists() or p.stat().st_size < 5:
        return pd.DataFrame()
    return pd.read_csv(p, dtype={"par": str})


def step5(key: str) -> dict:
    """Re-select the positioner (representation, distance, k, weighting,
    offset, ensemble) on the dev folds, using ONLY the columns of the best
    HUIM AP set of step 3 / 4; then re-run steps 3 and 4 with it."""
    D = data(key)
    G = read(key, "step3_G_global.csv")
    Z = read(key, "step4_Z_zones.csv")
    best = best_by_dev(pd.concat([G, Z], ignore_index=True))
    cols = sorted(set(union_cols(key, best.model, "global", best.theta_pct))
                  if best.scope == "global" else
                  set().union(*zone_sets(key, best.model, best.theta_pct).values()))
    op.GROUND = D.gf
    t0 = time.perf_counter()
    stages, grid = op.select_on_dev(D.W[:, cols], D.C, D.y, D.folds)
    secs = time.perf_counter() - t0
    cfg2 = stages[-1]["cfg"]
    pd.DataFrame(grid).to_csv(kdir(key) / "step5_dev_grid.csv", index=False)
    info = {"selected_on": best.config, "n_ap": len(cols), "seconds": round(secs, 1),
            "base_positioner": D.cfg.label(), "new_positioner": cfg2.label(),
            "new_config": asdict(cfg2), "same_as_base": cfg2 == D.cfg,
            "stages": [{"stage": s["stage"], "what": s["what"],
                        "label": s["cfg"].label(), "dev": s["dev"]} for s in stages]}
    (kdir(key) / "step5_positioner.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.info("%s step 5: %s -> %s (on %s, %d AP, %.0fs)", key, D.cfg.label(),
             cfg2.label(), best.config, len(cols), secs)
    if cfg2 != D.cfg:
        step3(key, cfg2, "T")
        step4(key, cfg2, "TZ", models=(best.model,))
    return info


# ------------------------------------------------------------------ step 6
RULES = [("topn", 0.5), ("topn", 0.75), ("frequent", 2), ("frequent", "median"),
         ("weighted", 0.5), ("weighted", 1.0)]


def apply_rule(D: DS, stats: dict, rule: str, par):
    uc = {w: s["utility_contribution"] for w, s in stats.items()}
    order = sorted(uc, key=lambda w: (-uc[w], w))
    if rule == "union":
        return [D.col_of[w] for w in order], None
    if rule == "topn":
        return [D.col_of[w] for w in order[:max(1, int(np.ceil(par * len(order))))]], None
    if rule == "frequent":
        nh = {w: s["n_huis"] for w, s in stats.items()}
        k = float(np.median(list(nh.values()))) if par == "median" else par
        return [D.col_of[w] for w in order if nh[w] >= k], None
    if rule == "weighted":
        top = max(uc.values())
        return [D.col_of[w] for w in order], np.array([(uc[w] / top) ** par for w in order])
    raise ValueError(rule)


def efim_stats(key: str, m: str, th: float) -> dict | None:
    R = efim_runs(key, m)
    r = R[np.isclose(R.rel_minutil_pct, th)]
    if not len(r) or r.iloc[0].status != "COMPLETED" or not r.iloc[0].n_huis:
        return None
    r = r.iloc[0]
    d = json.loads((md.PROJECT_ROOT / str(r.path_wap_stats).replace("\\", "/"))
                   .read_text(encoding="utf-8"))
    return {"per_wap": d["per_wap"], "n_huis": int(r.n_huis),
            "runtime_s": float(r.runtime_s),
            "peak_mb": float(r.peak_memory_delta_mb)}


def single_rows(key: str) -> pd.DataFrame:
    parts = []
    for f, step in (("step3_G_global.csv", 3), ("step4_Z_zones.csv", 4),
                    ("step5_T_global.csv", 5), ("step4_TZ_zones.csv", 5),
                    ("step6_rules.csv", 6)):
        t = read(key, f)
        if len(t):
            t["step"] = step
            parts.append(t)
    A = pd.concat(parts, ignore_index=True).dropna(subset=["dev_mean_m"])
    A["rule"] = A["rule"].fillna("union") if "rule" in A else "union"
    A["par"] = A["par"].fillna("") if "par" in A else ""
    return A.drop_duplicates("config").reset_index(drop=True)


def step6(key: str) -> pd.DataFrame:
    """Rules on the complete HUI set of the best global (model, minUtil) by
    dev - or of the closest minUtil above it at which EFIM completed."""
    D = data(key)
    A = single_rows(key)
    best = best_by_dev(A[A.scope == "global"])
    m, cfg = best.model, cfg_of(best)
    efim_th = sorted({round(float(t), 6) for t in efim_runs(key, m).rel_minutil_pct})
    best_set = set(union_cols(key, m, "global", best.theta_pct))
    # the EFIM level closest at or above the best minUtil; failing that, the
    # highest EFIM level below it with the SAME union (the same AP set)
    cand = [t for t in efim_th if t >= best.theta_pct - 1e-9]
    cand += [t for t in sorted(efim_th, reverse=True) if t < best.theta_pct - 1e-9
             and set(union_cols(key, m, "global", t)) == best_set]
    spec, th = None, None
    for th in cand:
        spec = efim_stats(key, m, th)
        if spec is not None:
            break
    if spec is None:
        LOG.warning("%s step 6: no complete EFIM HUI set at or above %s%%", key,
                    tg(best.theta_pct))
        pd.DataFrame().to_csv(kdir(key) / "step6_rules.csv", index=False)
        return pd.DataFrame()
    rows = []
    for rule, par in [("union", None)] + RULES:
        name = f"R_{m}__{tg(th)}pct__{rule}{'' if par is None else par}"
        cols, w = apply_rule(D, spec["per_wap"], rule, par)
        if rule == "union":
            assert set(cols) == set(union_cols(key, m, "global", th)), name
        r = cached(key, name, ("rule", asdict(cfg), tuple(cols),
                               None if w is None else tuple(np.round(w, 10))),
                   lambda c=cols, w=w: evaluate(D, c, cfg, w=w))
        rows.append({"config": name, "scope": "global", "model": m,
                     "theta_pct": th, "rule": rule,
                     "par": "" if par is None else str(par),
                     "theta_best_on_dev": best.theta_pct, "from_config": best.config,
                     "positioner": json.dumps(asdict(cfg)),
                     "positioner_label": cfg.label(),
                     "efim_n_huis": spec["n_huis"], "efim_seconds": spec["runtime_s"],
                     **r, "aps": ap_names(D, cols)})
        LOG.info("%s %-34s %3d AP  dev %.3f  test %.3f", key, name, r["n_ap"],
                 r["dev_mean_m"], r["test_mean_m"])
    R = pd.DataFrame(rows)
    R.to_csv(kdir(key) / "step6_rules.csv", index=False)
    return R


# ------------------------------------------------------------------ step 7
def splits(D: DS) -> list[tuple]:
    out = [("dev", D.C, D.y)]
    for name, T in D.tests.items():
        out.append((D.prefix[name], T["C"], T["y"]))
    return out


def ensemble(key: str, names: list[str], how: str) -> dict:
    D = data(key)
    P = [load_preds(key, n) for n in names]
    res = {"members": " + ".join(names), "how": how}
    for split, C, y in splits(D):
        xy = np.stack([p[f"{split}_xy"] for p in P])
        xy = xy.mean(axis=0) if how == "mean" else np.median(xy, axis=0)
        labs = np.stack([p[f"{split}_label"].astype(str) for p in P])
        lab = []
        for col in labs.T:
            v, c = np.unique(col, return_counts=True)
            top = v[c == c.max()]
            lab.append(next(x for x in col if x in top))
        e = err_m(xy, C, D.gf)
        res.update(summ(split, e, np.array(lab), y, D.multi_floor))
        res["_" + split] = {"xy": xy, "err": e, "label": np.array(lab)}
    return res


def step7(key: str) -> pd.DataFrame:
    A = single_rows(key)
    D = data(key)

    def same(r) -> str:
        """Configurations that read the same APs with the same positioner and
        rule predict identically; an ensemble of them is pointless."""
        srt = lambda s: ";".join(sorted(str(s).split(";")))     # noqa: E731
        aps = ("|".join(srt(r.get(f"aps_z{z}")) for z in range(D.n_zones))
               if r.scope == "zone" else srt(r.aps))
        w = f"{r.rule}{r.par}" if r.rule == "weighted" else ""
        return f"{r.scope}#{r.positioner_label}#{w}#{aps}"

    A["same_key"] = A.apply(same, axis=1)
    single = A[A.rule == "union"].copy()
    single["fam"] = single.config.str.split("_").str[0]
    cand = (single.sort_values(["dev_mean_m", "n_ap"])
                  .groupby(["fam", "model"], as_index=False).first())
    rules = A[(A.step == 6) & (A.rule != "union")]
    if len(rules):
        cand = pd.concat([cand, rules])
    cand = (cand.sort_values(["dev_mean_m", "n_ap"]).drop_duplicates("config")
                .drop_duplicates("same_key").head(6))
    LOG.info("%s step 7 candidates: %s", key, list(cand.config))
    Ai = A.set_index("config", drop=False)
    rows = []
    for k in (2, 3):
        for names in combinations(cand.config, k):
            for how in (("mean",) if k == 2 else ("mean", "median")):
                name = f"E_{how}__" + "+".join(names)
                r = cached(key, name, ("ens", how, names),
                           lambda n=list(names), h=how: ensemble(key, n, h))
                aps = set()
                for c in names:
                    rr = Ai.loc[c]
                    aps |= ({D.wap[j] for j in set().union(*zone_sets(
                        key, rr.model, float(rr.theta_pct)).values())}
                        if rr.scope == "zone" else set(str(rr.aps).split(";")))
                rows.append({"config": name, "k": k, "n_ap": len(aps), **r})
    E = pd.DataFrame(rows).sort_values("dev_mean_m") if rows else pd.DataFrame()
    E.to_csv(kdir(key) / "step7_ensembles.csv", index=False)
    cand.to_csv(kdir(key) / "step7_candidates.csv", index=False)
    if len(E):
        LOG.info("%s best ensemble: %s dev %.3f test %.3f", key, E.iloc[0].config,
                 E.iloc[0].dev_mean_m, E.iloc[0].test_mean_m)
    return E


# ----------------------------------------------------------------- summary
def summary(key: str) -> dict:
    D = data(key)
    A = single_rows(key)
    E = read(key, "step7_ensembles.csv")
    start = A.set_index("config").loc[f"G_A__{tg(START_THETA[key])}pct"]
    best_single = best_by_dev(A)
    allc = pd.concat([A, E.assign(scope="ensemble", theta_pct=np.nan)], ignore_index=True)
    allc["_r"] = allc.dev_mean_m.round(6)
    best = allc.sort_values(["_r", "n_ap"]).iloc[0]
    # a configuration that ties with the start (same APs, same predictions - e.g. HUS, where
    # every minUtil gives the same 5 APs) is reported as the start itself
    st = start.copy()
    st["config"] = start.name
    for name, r in (("best_single", best_single), ("best", best)):
        if round(r.dev_mean_m, 6) == round(start.dev_mean_m, 6) and r.n_ap == start.n_ap and \
                abs(r.test_mean_m - start.test_mean_m) < 1e-9:
            if name == "best_single":
                best_single = st
            else:
                best = st
    bal = {}
    for scope, T in (("global", A[(A.scope == "global") & (A.rule == "union")]),
                     ("zone", A[(A.scope == "zone") & (A.rule == "union")])):
        if len(T):
            lim = BALANCE * T.dev_mean_m.min()
            c = T[T.dev_mean_m <= lim].sort_values(["n_ap", "dev_mean_m"]).iloc[0]
            if c.n_ap == start.n_ap and round(c.dev_mean_m, 6) == round(start.dev_mean_m, 6) \
                    and abs(c.test_mean_m - start.test_mean_m) < 1e-9:
                c = c.copy()
                c["config"] = start.name          # the same APs and predictions as the start
            bal[scope] = {"config": c.config, "n_ap": int(c.n_ap),
                          "dev_limit_m": round(float(lim), 4)}

    def pick(r):
        keep = [k for k in r.index if k.startswith(("dev_", "test")) or k in (
            "config", "scope", "model", "theta_pct", "rule", "par", "n_ap",
            "positioner_label", "members", "how")]
        return {k: (None if isinstance(r[k], float) and np.isnan(r[k]) else
                    (r[k].item() if hasattr(r[k], "item") else r[k])) for k in keep}

    out = {"key": key, "title": D.title, "tests": {D.prefix[n]: n for n in D.tests},
           "n_ap_columns": len(D.wap), "positioner_base": D.cfg.label(),
           "start": {**pick(start), "config": start.name},
           "best_single": pick(best_single), "best": pick(best),
           "balanced": bal, "n_configs": int(len(allc))}
    (kdir(key) / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=2,
                                                      default=str), encoding="utf-8")
    return out


# ------------------------------------------------------------------ check
def check() -> pd.DataFrame:
    """Union search vs the union of the HUIs of every completed EFIM run."""
    rows = []
    for key in KEYS:
        D = data(key)
        for m in MODELS:
            for r in efim_runs(key, m).itertuples():
                if r.status != "COMPLETED":
                    continue
                th = round(float(r.rel_minutil_pct), 6)
                efim = set()
                if r.n_huis:
                    efim = set(json.loads((md.PROJECT_ROOT / str(r.path_wap_stats)
                                           .replace("\\", "/")).read_text(
                        encoding="utf-8"))["per_wap"])
                try:
                    srch = {D.wap[j] for j in union_cols(key, m, "global", th)}
                    st = "COMPLETED"
                except LookupError as e:
                    srch, st = None, str(e)
                rows.append({"dataset": key, "model": m, "minUtil_pct": th,
                             "efim_n_huis": int(r.n_huis), "efim_seconds": r.runtime_s,
                             "efim_union": len(efim), "search_status": st,
                             "search_union": None if srch is None else len(srch),
                             "identical": None if srch is None else srch == efim})
    T = pd.DataFrame(rows)
    T.to_csv(OUT / "union_check.csv", index=False)
    LOG.info("union check: %d/%d identical", int(T.identical.fillna(False).sum()), len(T))
    return T


# ------------------------------------------------------------------ step 8
def predictor(key: str, row):
    """(predict function, radio-map MB, n_ap) of one single configuration."""
    D = data(key)
    cfg = cfg_of(row)
    nm = 2 if cfg.ensemble_with else 1
    if row["scope"] == "zone":
        model = ZoneModel(D, zone_sets(key, row["model"], float(row["theta_pct"])), cfg)
        return model.predict, model.radio_map_mb(), len(model.allc)
    if row["rule"] not in ("union", "", None):
        par = row["par"]
        par = par if par == "median" else float(par)
        cols, w = apply_rule(D, efim_stats(key, row["model"], float(row["theta_pct"]))
                             ["per_wap"], row["rule"], par)
    else:
        cols, w = union_cols(key, row["model"], "global", float(row["theta_pct"])), None
    pos = positioner(D.W, D.C, D.y, cfg, cols, w)
    return (lambda Wq: pos.predict(Wq)), nm * len(D.W) * len(cols) * 8 / 2 ** 20, len(cols)


def timing(predict, Wq, repeats: int = 3) -> dict:
    predict(Wq[:64])
    ts, peaks = [], []
    for _ in range(repeats):
        with MemoryMonitor() as mem:
            t0 = time.perf_counter()
            predict(Wq)
            ts.append(time.perf_counter() - t0)
        peaks.append(mem.as_dict()["peak_delta_mb"])
    t = float(np.median(ts))
    return {"n_rows": len(Wq), "total_s": round(t, 4),
            "ms_per_fp": round(1000 * t / len(Wq), 4),
            "peak_delta_mb": round(float(np.median(peaks)), 2)}


def step8(key: str) -> pd.DataFrame:
    D = data(key)
    S = summary(key)
    A = single_rows(key).set_index("config", drop=False)
    E = read(key, "step7_ensembles.csv")
    Wq = next(iter(D.tests.values()))["W"][:TIMING_ROWS]
    picks = {"ban_dau": S["start"]["config"], "don_tot_nhat": S["best_single"]["config"]}
    for scope, v in S["balanced"].items():
        picks[f"can_bang_{scope}"] = v["config"]
    rows = []
    for label, cfgname in picks.items():
        row = A.loc[cfgname]
        with MemoryMonitor() as mem:
            t0 = time.perf_counter()
            pred, mb, n_ap = predictor(key, row)
            pred(Wq[:8])
            build_s = time.perf_counter() - t0
        tm = timing(pred, Wq)
        rows.append({"label": label, "config": cfgname, "scope": row.scope,
                     "model": row.model, "theta_pct": row.theta_pct, "rule": row.rule,
                     "n_ap": n_ap, "radio_map_mb": round(mb, 3),
                     "build_s": round(build_s, 3),
                     "build_peak_mb": mem.as_dict()["peak_delta_mb"], **tm,
                     "dev_mean_m": row.dev_mean_m, "test_mean_m": row.test_mean_m})
        LOG.info("%s time %-14s %3d AP %.3f ms/fp %.2f MB", key, label, n_ap,
                 tm["ms_per_fp"], mb)
    if S["best"]["config"].startswith("E_"):
        b = E.set_index("config").loc[S["best"]["config"]]
        members = S["best"]["config"].split("__", 1)[1].split("+")
        preds = [predictor(key, A.loc[c]) for c in members]
        for p, _, _ in preds:
            p(Wq[:8])
        tm = timing(lambda X: [p(X) for p, _, _ in preds], Wq)
        rows.append({"label": "tot_nhat_ensemble", "config": S["best"]["config"],
                     "scope": "ensemble", "model": "+".join(A.loc[c].model for c in members),
                     "theta_pct": np.nan, "rule": "ensemble", "n_ap": int(b.n_ap),
                     "radio_map_mb": round(sum(mb for _, mb, _ in preds), 3), **tm,
                     "dev_mean_m": b.dev_mean_m, "test_mean_m": b.test_mean_m})
    T = pd.DataFrame(rows)
    T.to_csv(kdir(key) / "step8_time_memory.csv", index=False)
    return T


# ======================================================================= CLI
STEPS = {3: step3, 4: step4, 5: step5, 6: step6, 7: step7}


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("unions")
    u.add_argument("--workers", type=int, default=10)
    u.add_argument("--keys", nargs="+", default=list(KEYS))
    s = sub.add_parser("steps")
    s.add_argument("--key", required=True)
    s.add_argument("--steps", type=int, nargs="+", default=[3, 4, 5, 6, 7])
    sub.add_parser("check")
    t = sub.add_parser("step8")
    t.add_argument("--keys", nargs="+", default=list(KEYS))
    a = ap.parse_args()
    if a.cmd == "unions":
        from concurrent.futures import ProcessPoolExecutor, as_completed
        jobs = [j for j in all_union_jobs() if j[0] in a.keys]
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(_union_job, j): j for j in jobs}
            for f in as_completed(futs):
                print(f.result(), flush=True)
    elif a.cmd == "steps":
        for st in a.steps:
            t0 = time.perf_counter()
            STEPS[st](a.key)
            print(f"{a.key} step {st}: {time.perf_counter() - t0:.0f}s", flush=True)
        summary(a.key)
    elif a.cmd == "check":
        T = check()
        print(T.groupby("dataset").identical.agg(["count", "sum"]))
    elif a.cmd == "step8":
        for key in a.keys:
            print(step8(key).to_string(), flush=True)


if __name__ == "__main__":
    main()
