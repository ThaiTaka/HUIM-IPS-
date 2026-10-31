"""Phase 2: where does the V6 error come from? Offline analysis on the out-of-fold dev queries.

Labels (true position, true floor) are used here only to MEASURE; none of these quantities is a model input.
Outputs: results/huim_only/uji/v7/diagnosis/*.csv and diagnosis.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import place  # noqa: E402
from v7.common import GF, OUT, err_m  # noqa: E402
from v7.rerank import load_dev, oof_v6  # noqa: E402


def table() -> pd.DataFrame:
    D = load_dev()
    P = oof_v6(D)
    rows = []
    for k, (d, p) in enumerate(zip(D, P)):
        xy, o, w = place(p, d["cxy"])
        n = len(p)
        true_bf = pd.Series(d["bld"].astype(str)).str.cat(pd.Series(d["flr"].astype(str)), sep="_").to_numpy()
        dist = d["dist"]
        pred_rank12 = np.argsort(p, 1)[:, :12]
        rows.append(pd.DataFrame({
            "fold": k, "query": np.arange(n), "dvi": d["dvi"], "phone": d["phone"], "bld": d["bld"], "flr": d["flr"],
            "true_bf": true_bf, "pred_bf": d["floor"], "floor_ok": d["floor"] == true_bf,
            "bld_ok": pd.Series(d["floor"]).str.split("_").str[0].to_numpy() == d["bld"].astype(str),
            "err_v6": err_m(xy, d["true"]), "err_v4": err_m(d["est"], d["true"]),
            "d_top1": dist[:, 0], "d_best30": dist.min(1),
            "d_best20pred": np.take_along_axis(dist, o, 1).min(1),
            "d_best12pred": np.take_along_axis(dist, pred_rank12, 1).min(1),
            "d_pick1": dist[np.arange(n), p.argmin(1)],
            "x": d["true"][:, 0], "y": d["true"][:, 1]}))
    return pd.concat(rows, ignore_index=True)


def analyse(T: pd.DataFrame) -> dict:
    r: dict = {"n_queries": int(len(T)), "dev_mean_v6": float(T.err_v6.mean()), "dev_median_v6": float(T.err_v6.median()),
               "dev_p90_v6": float(T.err_v6.quantile(0.9)), "dev_mean_v4": float(T.err_v4.mean())}
    tot = T.err_v6.sum()
    # A. floor
    g = T.groupby("floor_ok").err_v6.agg(["count", "mean", "median"])
    r["A_floor"] = {"floor_accuracy": float(T.floor_ok.mean()), "building_accuracy": float(T.bld_ok.mean()),
                    "right_floor": g.loc[True].to_dict(), "wrong_floor": g.loc[False].to_dict(),
                    "share_of_total_error_wrong_floor": float(T.err_v6[~T.floor_ok].sum() / tot)}
    # B. candidate quality (metres)
    B = {}
    for c in ("d_top1", "d_best30", "d_pick1", "d_best20pred", "d_best12pred", "err_v6"):
        B[c] = {"mean": float(T[c].mean()), "median": float(T[c].median())}
    B["share_best30_below"] = {f"{t}m": float((T.d_best30 < t).mean()) for t in (3, 5, 10)}
    B["share_top1_below"] = {f"{t}m": float((T.d_top1 < t).mean()) for t in (3, 5, 10)}
    B["share_v6_position_below"] = {f"{t}m": float((T.err_v6 < t).mean()) for t in (3, 5, 10)}
    for sub, name in ((T.floor_ok, "right_floor"), (~T.floor_ok, "wrong_floor")):
        B[name] = {c: float(T.loc[sub, c].mean()) for c in ("d_top1", "d_best30", "d_pick1", "d_best20pred", "err_v6")}
        B[name]["share_best30_below_5m"] = float((T.loc[sub, "d_best30"] < 5).mean())
    r["B_candidates"] = B
    # C. V6 vs V4 and the error tail
    imp = T.err_v4 - T.err_v6
    r["C_v6_vs_v4"] = {"v6_better_gt0.5m": int((imp > 0.5).sum()), "v6_worse_gt0.5m": int((imp < -0.5).sum()),
                       "similar": int((imp.abs() <= 0.5).sum())}
    q90 = T.err_v6.quantile(0.9)
    tail = T[T.err_v6 >= q90]
    r["C_tail_p90"] = {"threshold_m": float(q90), "n": int(len(tail)), "share_wrong_floor": float((~tail.floor_ok).mean()),
                       "share_of_total_error": float(tail.err_v6.sum() / tot), "mean_best30_in_tail": float(tail.d_best30.mean())}
    return r


def main() -> None:
    out = OUT / "diagnosis"
    out.mkdir(parents=True, exist_ok=True)
    T = table()
    D = load_dev()
    T["n_ap"] = np.concatenate([d["F"][:, 0, 13] for d in D])
    T.to_csv(out / "dev_per_query.csv", index=False)
    info = T[T.n_ap > 0].copy()
    empty = T[T.n_ap == 0]
    r = {"all_queries": analyse(T), "informative_queries": analyse(info),
         "empty_fingerprints": {"n": int(len(empty)), "phones": empty.phone.value_counts().to_dict(),
                                "mean_err_v6": float(empty.err_v6.mean()), "mean_err_v4": float(empty.err_v4.mean()),
                                "share_of_dev_error_sum": float(empty.err_v6.sum() / T.err_v6.sum()),
                                "note": "no AP detected: every cell scores 0, the 12/20 'best' cells are an arbitrary tie-break; validationData has none"}}
    # by phone / floor / density / error band (informative queries)
    ph = info.groupby("phone").agg(n=("err_v6", "size"), v6=("err_v6", "mean"), v4=("err_v4", "mean"), floor_acc=("floor_ok", "mean"),
                                   best30=("d_best30", "mean")).round(3)
    ph.to_csv(out / "by_phone.csv")
    info.groupby("true_bf").agg(n=("err_v6", "size"), v6=("err_v6", "mean"), v4=("err_v4", "mean"), floor_acc=("floor_ok", "mean"),
                                best30=("d_best30", "mean")).round(3).to_csv(out / "by_floor.csv")
    cxy = D[0]["cell_xy"]
    info["cells_within_10m"] = np.concatenate([(np.sqrt(((d["true"][:, None] - cxy[None]) ** 2).sum(-1)) * GF < 10).sum(1) for d in D])[(T.n_ap > 0).to_numpy()]
    info["dens_bin"] = pd.cut(info.cells_within_10m, [-1, 2, 5, 10, 20, 1000], labels=["0-2", "3-5", "6-10", "11-20", ">20"])
    info.groupby("dens_bin", observed=True).agg(n=("err_v6", "size"), v6=("err_v6", "mean"), best30=("d_best30", "mean"),
                                                floor_acc=("floor_ok", "mean")).round(3).to_csv(out / "by_cell_density.csv")
    tot = info.err_v6.sum()
    bands = pd.cut(info.err_v6, [0, 3, 5, 10, 20, 1000])
    info.groupby(bands, observed=True).agg(n=("err_v6", "size"), share_of_error=("err_v6", lambda s: s.sum() / tot)).round(3).to_csv(out / "error_bands.csv")
    json.dump(r, open(OUT / "diagnosis.json", "w"), indent=1)
    print(json.dumps(r["informative_queries"], indent=1)[:2500])
    print(json.dumps(r["empty_fingerprints"], indent=1))


if __name__ == "__main__":
    main()
