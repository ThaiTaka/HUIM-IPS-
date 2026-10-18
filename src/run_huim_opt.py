"""HUIM-only optimisation on UJIIndoorLoc - the steps of the "HUIM only" update.

    python src/run_huim_opt.py --step 1    remove the non-HUIM rows (S0, 520 AP,
                                           465 AP) from the result tables
    python src/run_huim_opt.py --step 2    Model A / B / C at every COMPLETED
                                           minUtil, S4 positioner, dev + validation

Outputs go to results/huim_opt/; step 1 also rewrites the three tables named in
the update brief (results/multi_dataset/uji/positioning_conditions.csv,
positioning_ablation.csv, BAOCAO/so_lieu/sai_so_theo_toa.csv). A copy of them
from before step 1 is in D:/HUIM-IPS-_sao_luu_2026-10-16_truoc_HUIM_only.zip.
"""
from __future__ import annotations

import argparse
import time
import json
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import huim_opt as H                                     # noqa: E402
import optimize_positioning as op                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BAOCAO_SO_LIEU = ROOT / "BAOCAO" / "so_lieu"
PRED = H.OUT / "preds"
PRED.mkdir(exist_ok=True)


def save_preds(name: str, r: dict) -> None:
    """Per-row predictions, so later steps (per-building tables, ensembles)
    reuse them instead of recomputing."""
    arr = {f"val_{k}": v for k, v in r["_val"].items()}
    if "_dev" in r:
        arr.update({f"dev_{k}": v for k, v in r["_dev"].items()})
    np.savez_compressed(PRED / f"{name}.npz", **arr)


# ------------------------------------------------------------------ step 1
def step1() -> None:
    D = H.data()
    # positioning_conditions.csv: drop the 520 / 465 AP rows and the study
    # k-NN (S0) columns; every remaining row is S4 on a selected AP set
    p = H.RUNS / "positioning_conditions.csv"
    T = pd.read_csv(p)
    T = T[T.family != "baseline"]
    T = T.drop(columns=[c for c in T.columns if c.startswith("study_")])
    T.to_csv(p, index=False)
    H.LOG.info("positioning_conditions.csv: %d rows, families %s", len(T),
               sorted(T.family.unique()))

    # positioning_ablation.csv: S0-S3 were stages of the 520 AP model; keep one
    # S4 row, evaluated on the HUIM AP set (Model A, minUtil 1.9294%)
    u = H.union_of_run("A", 1.9294)
    cols = [D.col_of[w] for w in u]
    r = H.evaluate(cols)
    dev = op.stats(r["_dev"]["err"])
    ev, lab = r["_val"]["err"], r["_val"]["label"]
    pb = np.array([s.split("_")[0] for s in lab]).astype(int)
    pf = np.array([s.split("_")[1] for s in lab]).astype(int)
    old = pd.read_csv(H.RUNS / "positioning_ablation.csv")
    row = {"test_set": "validationData", "stage": "S4",
           "what": "S4 on the HUIM AP set",
           "config": H.S4.label(),
           "ap_set": "huim_union__A_signal__1.9294pct", "n_waps": len(cols),
           **{f"dev_{k}": v for k, v in dev.items()},
           "test_n_test": len(ev),
           "test_building_accuracy": round(float((pb == D.bv).mean()), 6),
           "test_floor_accuracy": round(float((pf == D.va.FLOOR.to_numpy()).mean()), 6),
           "test_joint_accuracy": round(float((lab == D.yv).mean()), 6),
           "test_mean_err_m": round(float(ev.mean()), 4),
           "test_median_err_m": round(float(np.median(ev)), 4),
           "test_p75_err_m": round(float(np.percentile(ev, 75)), 4),
           "test_p90_err_m": round(float(np.percentile(ev, 90)), 4),
           "test_p95_err_m": round(float(np.percentile(ev, 95)), 4),
           "test_max_err_m": round(float(ev.max()), 4),
           "test_mean_err_coord": round(float(ev.mean() / op.GROUND), 4),
           "test_share_within_2m": round(float((ev <= 2).mean()), 4),
           "test_share_within_5m": round(float((ev <= 5).mean()), 4)}
    cols_out = list(old.columns[:4]) + ["ap_set", "n_waps"] + list(old.columns[4:])
    pd.DataFrame([row])[cols_out].to_csv(H.RUNS / "positioning_ablation.csv",
                                         index=False)
    expect = pd.read_csv(p).set_index("condition").loc[
        "huim_union__A_signal__1.9294pct", "opt_mean_err_m"]
    assert abs(row["test_mean_err_m"] - expect) < 5e-4, (row, expect)
    H.LOG.info("positioning_ablation.csv: S4 on 86 HUIM APs, dev %.3f m, "
               "validation %.4f m", dev["mean_ground_m"], row["test_mean_err_m"])

    # BAOCAO/so_lieu: keep only the S4 + HUIM configuration
    for name in ("sai_so_theo_toa.csv", "du_doan_tung_mau_validation.csv"):
        f = BAOCAO_SO_LIEU / name
        S = pd.read_csv(f)
        S[S.cau_hinh == "S4_86AP_HUIM"].to_csv(f, index=False, float_format="%.4f"
                                               if name.startswith("sai") else None)
        H.LOG.info("%s: kept cau_hinh S4_86AP_HUIM only", name)


# ------------------------------------------------------------------ step 2
def step2() -> pd.DataFrame:
    rows = []
    for m in ("A", "B", "C"):
        R = H.huim_runs(m)
        for _, run in R.sort_values("rel_minutil_pct", ascending=False).iterrows():
            pct = float(run.rel_minutil_pct)
            u = H.union_of_run(m, pct)
            if not u:                 # aborted, or no HUI at this minUtil
                continue
            name = f"{m}__{pct:g}pct__union"
            cols = [H.data().col_of[w] for w in u]
            r = H.evaluate(cols)
            save_preds(name, r)
            rows.append({"config": name, "model": m, "theta_pct": pct,
                         "n_huis": int(run.n_huis),
                         "mining_s": round(float(run.runtime_s), 1),
                         **H.public(r), "aps": ";".join(u)})
            H.LOG.info("%-22s %3d AP  dev %6.2f m  val %6.2f m  (b1 %6.2f m)",
                       name, len(cols), r["dev_mean_m"], r["val_mean_m"],
                       r["val_mean_b1_m"])
    T = pd.DataFrame(rows)
    T.to_csv(H.OUT / "step2_models_ABC.csv", index=False)
    best = T.loc[T.dev_mean_m.idxmin()]
    per_model = {m: g.loc[g.dev_mean_m.idxmin()].config
                 for m, g in T.groupby("model")}
    (H.OUT / "step2_summary.json").write_text(json.dumps({
        "selection_criterion": "mean ground-metre error on 6 leave-users-out "
                               "dev folds of trainingData",
        "best_overall_on_dev": best.config,
        "best_per_model_on_dev": per_model,
        "skipped": "aborted minUtil runs (incomplete HUI set) and runs with "
                   "no HUI",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()},
        indent=2), encoding="utf-8")
    return T


def _cached(name: str, fn) -> dict:
    """Evaluate once; later steps and re-runs read the saved row."""
    f = H.OUT / "rows" / f"{name}.json"
    f.parent.mkdir(exist_ok=True)
    if f.exists() and (PRED / f"{name}.npz").exists():
        return json.loads(f.read_text(encoding="utf-8"))
    r = fn()
    save_preds(name, r)
    row = H.public(r)
    f.write_text(json.dumps(row), encoding="utf-8")
    return row


# ------------------------------------------------------------------ step 3
# the brief's grid, plus the two PHASE H minUtils of Model B / C
STEP3_GRID = sorted(set(H.THETA_GRID) | {1.7321, 2.0})
# one building's HUIs reach a larger share of that building's utility, so the
# per-building grid continues upwards to reach AP budgets comparable to the
# global sets (~80-90 APs)
STEP4_GRID = sorted(set(H.THETA_GRID) | {4.0, 5.0, 7.5, 10.0})


def step3() -> pd.DataFrame:
    """minUtil grid, one HUIM over the three buildings (unions read from maxU,
    so every θ of the grid is exact even where EFIM explodes)."""
    D = H.data()
    rows = []
    for m in "ABC":
        M = (H.union_table(m, "global") if (H.OUT / f"union_global_{m}.npz").exists()
             else {"seconds": np.nan, "peak_delta_mb": np.nan})
        for th in STEP3_GRID:
            try:
                cols = H.union_cols(m, "global", th)
            except LookupError as err:   # union level not finished / TIMEOUT
                rows.append({"config": f"G_{m}__{th:g}pct", "scope": "global",
                             "model": m, "theta_pct": th,
                             "status": str(err)})
                continue
            base = {"config": f"G_{m}__{th:g}pct", "scope": "global",
                    "model": m, "theta_pct": th, "n_ap": len(cols),
                    "union_seconds": round(float(M["seconds"]), 1),
                    "union_peak_mb": round(float(M["peak_delta_mb"]), 1)}
            if not cols:
                rows.append(base)
                continue
            r = _cached(base["config"], lambda c=cols: H.evaluate(c))
            home = [int(np.sum(_home()[cols] == b)) for b in range(3)]
            rows.append({**base, **r, **{f"n_ap_b{b}": home[b] for b in range(3)},
                         "aps": ";".join(D.wap[j] for j in cols)})
            H.LOG.info("%-18s %3d AP  dev %6.2f  val %6.2f", base["config"],
                       len(cols), r["dev_mean_m"], r["val_mean_m"])
    T = pd.DataFrame(rows)
    T.to_csv(H.OUT / "step3_theta_global.csv", index=False)
    return T


@lru_cache(maxsize=1)
def _home() -> np.ndarray:
    """Building in which each AP is detected most often in trainingData."""
    D = H.data()
    det = D.W != op.NOT_DETECTED
    return np.array([np.bincount(D.b[det[:, j]], minlength=3).argmax()
                     if det[:, j].any() else -1 for j in range(det.shape[1])])


# ------------------------------------------------------------------ step 4
def pb_sets(m: str, th: float) -> dict:
    return {b: H.union_cols(m, f"b{b}", th) for b in range(3)}


def step4() -> pd.DataFrame:
    """One HUIM per building, minUtil relative to that building's utility."""
    D = H.data()
    rows = []
    for m in "ABC":
        cost = [H.union_table(m, f"b{b}") if (H.OUT / f"union_b{b}_{m}.npz").exists()
                else {"seconds": np.nan, "peak_delta_mb": np.nan} for b in range(3)]
        for th in STEP4_GRID:
            try:
                sets = pb_sets(m, th)
            except LookupError as err:   # union level not finished / TIMEOUT
                rows.append({"config": f"PB_{m}__{th:g}pct",
                             "scope": "per_building", "model": m,
                             "theta_pct": th, "status": str(err)})
                continue
            base = {"config": f"PB_{m}__{th:g}pct", "scope": "per_building",
                    "model": m, "theta_pct": th,
                    "union_seconds": round(sum(float(c["seconds"]) for c in cost), 1),
                    "union_peak_mb": round(max(float(c["peak_delta_mb"]) for c in cost), 1),
                    **{f"n_ap_b{b}": len(sets[b]) for b in range(3)}}
            if not all(sets.values()):
                rows.append({**base, "n_ap": len(set().union(*sets.values()))})
                continue
            r = _cached(base["config"], lambda s=sets: H.evaluate_per_building(s))
            rows.append({**base, **r, **{f"aps_b{b}": ";".join(D.wap[j] for j in sets[b])
                                         for b in range(3)}})
            H.LOG.info("%-18s %3d AP (%d/%d/%d)  dev %6.2f  val %6.2f",
                       base["config"], r["n_ap"], *(len(sets[b]) for b in range(3)),
                       r["dev_mean_m"], r["val_mean_m"])
    T = pd.DataFrame(rows)
    T.to_csv(H.OUT / "step4_per_building.csv", index=False)
    return T


# ------------------------------------------------------------------ step 6
# selection rules on the complete HUI set (feature_selection's statistics):
#   union     every AP of some HUI (= steps 3/4)
#   topn      the top fraction of the union by utility contribution
#   frequent  APs occurring in >= k HUIs (k = 2, or the median count)
#   weighted  every union AP, Bray-Curtis weight (contribution / max)^gamma
RULES = [("topn", 0.5), ("topn", 0.75), ("frequent", 2), ("frequent", "median"),
         ("weighted", 0.5), ("weighted", 1.0)]


def apply_rule(stats: dict, rule: str, par) -> tuple[list[int], np.ndarray | None]:
    D = H.data()
    uc = {w: s["utility_contribution"] for w, s in stats.items()}
    order = sorted(uc, key=lambda w: (-uc[w], w))
    if rule == "union":
        names = order
    elif rule == "topn":
        names = order[:max(1, int(np.ceil(par * len(order))))]
    elif rule == "frequent":
        nh = {w: s["n_huis"] for w, s in stats.items()}
        k = float(np.median(list(nh.values()))) if par == "median" else par
        names = [w for w in order if nh[w] >= k]
    elif rule == "weighted":
        top = max(uc.values())
        return ([D.col_of[w] for w in order],
                np.array([(uc[w] / top) ** par for w in order]))
    else:
        raise ValueError(rule)
    return [D.col_of[w] for w in names], None


def best_by_dev(T: pd.DataFrame) -> pd.Series:
    return T.dropna(subset=["dev_mean_m"]).sort_values("dev_mean_m").iloc[0]


def _known_abort(m: str, scope: str, th: float) -> bool:
    """EFIM already aborted for this (model, scope) at some θ' >= θ: a lower θ
    only has more HUIs, so it would abort too - do not spend the budget."""
    for f in H.OUT.glob(f"huistats_{scope}_{m}_*pct.json"):
        t = float(f.stem.rsplit("_", 1)[1].replace("pct", ""))
        if t >= th - 1e-9 and json.loads(f.read_text(encoding="utf-8"))["status"] != "COMPLETED":
            return True
    return False


def rule_spec(scope: str, m: str, th: float) -> dict | None:
    """Complete HUI statistics for (scope, model, θ): PHASE H for the global
    scope, one EFIM run per building otherwise. None if a run aborted."""
    if scope != "global" and any(_known_abort(m, f"b{b}", th) for b in range(3)):
        return None
    if scope == "global":
        s = H.hui_stats(m, "global", th)
        return {"g": s} if s["status"] == "COMPLETED" and s["n_huis"] else None
    out = {}
    for b in range(3):
        s = H.hui_stats(m, f"b{b}", th)
        if s["status"] != "COMPLETED" or not s["n_huis"]:
            return None                     # aborted, or no HUI: no AP set
        out[b] = s
    return out


def rule_sets(scope, m, th, rule, par):
    """(AP columns, weights) of a rule: a list + array for the global scope,
    two dicts keyed by building otherwise."""
    if scope == "global":
        if rule == "union":
            return H.union_cols(m, "global", th), None
        return apply_rule(H.hui_stats(m, "global", th)["per_wap"], rule, par)
    sets, ws = {}, {}
    for b in range(3):
        if rule == "union":
            sets[b], ws[b] = H.union_cols(m, f"b{b}", th), None
        else:
            sets[b], ws[b] = apply_rule(H.hui_stats(m, f"b{b}", th)["per_wap"],
                                        rule, par)
    return sets, (ws if rule == "weighted" else None)


def step6() -> pd.DataFrame:
    rows = []
    for f in ("step3_theta_global.csv", "step4_per_building.csv"):
        T = pd.read_csv(H.OUT / f)
        best = best_by_dev(T)
        scope, m = best.scope, best.model
        grid = STEP3_GRID if scope == "global" else STEP4_GRID
        spec, th = None, None
        for th in [t for t in grid if t >= best.theta_pct - 1e-9]:
            spec = rule_spec(scope, m, th)       # the best θ, else the next up
            if spec is not None:
                break
        if spec is None:
            H.LOG.warning("step 6: no complete HUI set for %s %s", scope, m)
            continue
        tag = "G" if scope == "global" else "PB"
        for rule, par in [("union", None)] + RULES:
            name = f"R_{tag}_{m}__{th:g}pct__{rule}{'' if par is None else par}"
            sets, w = rule_sets(scope, m, th, rule, par)
            if rule == "union":                  # HUI set and search agree
                stats_sets = ({"g": spec["g"]["per_wap"]} if scope == "global"
                              else {b: spec[b]["per_wap"] for b in range(3)})
                for k, st in stats_sets.items():
                    got = sets if scope == "global" else sets[k]
                    assert {H.data().wap[j] for j in got} == set(st), (name, k)
            if scope == "global":
                r = _cached(name, lambda c=sets, w=w: H.evaluate(c, w=w))
                extra = {}
            else:
                r = _cached(name, lambda s=sets, w=w:
                            H.evaluate_per_building(s, weights=w))
                extra = {f"n_ap_b{b}": len(sets[b]) for b in range(3)}
            rows.append({"config": name, "scope": scope, "model": m,
                         "theta_pct": th, "rule": rule,
                         "par": "" if par is None else str(par),
                         "theta_best_on_dev": best.theta_pct,
                         "efim_n_huis": sum(s["n_huis"] for s in spec.values()),
                         "efim_seconds": round(sum(s["runtime_s"]
                                                   for s in spec.values()), 1),
                         **r, **extra})
            H.LOG.info("%-40s %3d AP  dev %6.2f  val %6.2f", name, r["n_ap"],
                       r["dev_mean_m"], r["val_mean_m"])
    R = pd.DataFrame(rows)
    R.to_csv(H.OUT / "step6_selection_rules.csv", index=False)
    return R


# ------------------------------------------------------------------ step 7
def all_rows() -> pd.DataFrame:
    """Every single-configuration result of steps 3, 4 and 6, one row each."""
    parts = []
    for f, step in (("step3_theta_global.csv", 3), ("step4_per_building.csv", 4),
                    ("step6_selection_rules.csv", 6)):
        p = H.OUT / f
        if p.exists():
            t = pd.read_csv(p, dtype={"par": str})
            t["step"] = step
            parts.append(t)
    A = pd.concat(parts, ignore_index=True).dropna(subset=["dev_mean_m"])
    A["rule"] = A.get("rule", pd.Series(index=A.index, dtype=str)).fillna("union")
    A["par"] = A.get("par", pd.Series(index=A.index, dtype=str)).fillna("")
    return A.drop_duplicates("config")


def step7() -> pd.DataFrame:
    """Ensembles of the best configuration of each (scope, model) and of the
    best non-union rule; members and the combination rule chosen on dev."""
    from itertools import combinations
    A = all_rows()
    single = A[A.rule == "union"]
    cand = (single.sort_values("dev_mean_m")
                  .groupby(["scope", "model"], as_index=False).first())
    rules = A[(A.step == 6) & (A.rule != "union")]
    if len(rules):
        cand = pd.concat([cand, rules.sort_values("dev_mean_m").head(1)])
    cand = cand.sort_values("dev_mean_m").drop_duplicates("config").head(6)
    H.LOG.info("step 7 candidates: %s", list(cand.config))
    rows = []
    for k in (2, 3):
        for names in combinations(cand.config, k):
            for how in (("mean",) if k == 2 else ("mean", "median")):
                r = H.ensemble(list(names), how)
                name = f"E_{how}__" + "+".join(names)
                n_ap = len(set().union(*(all_cols(A.set_index("config").loc[c]
                                                  .to_dict() | {"config": c})
                                         for c in names)))
                rows.append({"config": name, "k": k, "n_ap": n_ap, **H.public(r)})
                save_preds(name, r)
    E = pd.DataFrame(rows).sort_values("dev_mean_m")
    E.to_csv(H.OUT / "step7_ensembles.csv", index=False)
    cand.to_csv(H.OUT / "step7_candidates.csv", index=False)
    b = E.iloc[0]
    H.LOG.info("best ensemble on dev: %s  dev %.2f  val %.2f", b.config,
               b.dev_mean_m, b.val_mean_m)
    return E


# ------------------------------------------------------------------ step 8
def predictor(row) -> tuple:
    """(predict function, radio-map MB, n_ap) of one single configuration;
    building it = the 'training' (radio maps for its AP sets)."""
    D = H.data()
    rule = row["rule"] or "union"
    par = row["par"]
    par = None if par in ("", None) else (par if par == "median" else float(par))
    sets, w = rule_sets(row["scope"], row["model"], float(row["theta_pct"]),
                        rule, par)
    if row["scope"] == "global":
        pos = H.positioner(D.W, D.C, D.y, H.S4, sets, w)
        return ((lambda Wq: pos.predict(Wq)),
                2 * len(D.W) * len(sets) * 8 / 2 ** 20, len(sets))
    model = H.PBModel(sets, H.S4, w)
    return model.predict, model.radio_map_mb(), len(model.allc)


def all_cols(row) -> set:
    """Every AP column a single configuration reads."""
    par = row["par"]
    par = None if par in ("", None) else (par if par == "median" else float(par))
    sets, _ = rule_sets(row["scope"], row["model"], float(row["theta_pct"]),
                        row["rule"] or "union", par)
    return set(sets) if row["scope"] == "global" else set().union(*sets.values())


def step8() -> pd.DataFrame:
    """Online time per fingerprint and memory of the configurations the
    report compares (and the cost of building their radio maps)."""
    from utils import MemoryMonitor
    A = all_rows().set_index("config", drop=False)
    E = pd.read_csv(H.OUT / "step7_ensembles.csv")
    picks = {"start: A 1.9294% global": "G_A__1.9294pct"}
    for scope in ("global", "per_building"):
        for m in "ABC":
            s = A[(A.scope == scope) & (A.model == m) & (A.rule == "union")]
            if len(s):
                picks[f"best {scope} {m}"] = s.sort_values("dev_mean_m").iloc[0].config
    r6 = A[(A.step == 6) & (A.rule != "union")]
    if len(r6):
        picks["best rule"] = r6.sort_values("dev_mean_m").iloc[0].config
    rows = []
    for label, cfg in picks.items():
        row = A.loc[cfg]
        with MemoryMonitor() as mem:
            t0 = time.perf_counter()
            pred, mb, n_ap = predictor(row)
            pred(H.data().Wv[:8])                  # first call builds the maps
            build_s = time.perf_counter() - t0
        tm = H.time_and_memory(pred, 0, 0)
        rows.append({"label": label, "config": cfg, "scope": row.scope,
                     "model": row.model, "theta_pct": row.theta_pct,
                     "rule": row.rule, "n_ap": n_ap,
                     "radio_map_mb": round(mb, 3), "build_s": round(build_s, 3),
                     "build_peak_mb": mem.as_dict()["peak_delta_mb"],
                     **{k: v for k, v in tm.items() if k != "radio_map_mb"},
                     "val_mean_m": row.val_mean_m, "dev_mean_m": row.dev_mean_m})
        H.LOG.info("time %-28s %3d AP  %.2f ms/fp  %.1f MB map", label, n_ap,
                   tm["ms_per_fp"], mb)
    b = E.iloc[0]                       # the best ensemble: members in sequence
    members = b.config.split("__", 1)[1].split("+")
    preds = [predictor(A.loc[c]) for c in members]
    for p, _, _ in preds:
        p(H.data().Wv[:8])
    tm = H.time_and_memory(lambda Wq: [p(Wq) for p, _, _ in preds], 0, 0)
    rows.append({"label": "best ensemble", "config": b.config,
                 "scope": "ensemble",
                 "model": "+".join(A.loc[c].model for c in members),
                 "theta_pct": np.nan, "rule": "ensemble",
                 "n_ap": len(set().union(*(all_cols(A.loc[c]) for c in members))),
                 "radio_map_mb": round(sum(mb for _, mb, _ in preds), 3),
                 **{k: v for k, v in tm.items() if k != "radio_map_mb"},
                 "val_mean_m": b.val_mean_m, "dev_mean_m": b.dev_mean_m})
    T = pd.DataFrame(rows)
    T.to_csv(H.OUT / "step8_time_memory.csv", index=False)
    return T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, nargs="+", required=True)
    a = ap.parse_args()
    for s in a.step:
        {1: step1, 2: step2, 3: step3, 4: step4, 6: step6, 7: step7,
         8: step8}[s]()
