"""Tables for the V7 report, computed from the cached out-of-fold predictions and the test predictions.

Writes (all numbers come from files, nothing is typed in):
    BAOCAO_V7/so_lieu/dev_per_query.csv       one row per dev query: fold, phone, floor flags, error of every model
    BAOCAO_V7/so_lieu/dev_summary.csv         per model: informative mean / all mean / median / P75 / P90 / P95 (+95% CI)
    BAOCAO_V7/so_lieu/dev_paired_vs_V6star.csv  paired phone-cluster bootstrap of the difference to V6*
    BAOCAO_V7/so_lieu/dev_by_phone.csv, dev_by_floor_correct.csv, dev_by_floor.csv, dev_candidate_selection.csv
    BAOCAO_V7/so_lieu/test_per_query.csv, test_summary.csv, test_paired_vs_V6.csv
    BAOCAO_V7/so_lieu/ablation.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import place  # noqa: E402
from v7.common import OUT, PROJECT_ROOT, UJI, err_m, load_cache  # noqa: E402
from v7.experiments import load_oof  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import N_FOLDS, load_dev, oof_v6  # noqa: E402
from v7.stats import cluster_bootstrap_mean, paired_cluster_bootstrap  # noqa: E402

DEST = PROJECT_ROOT / "BAOCAO_V7" / "so_lieu"
VARIANTS = ["B_base", "C_rel", "C_rel_absL3", "C_rel_geo", "C_devrob", "D_hier"]
LABEL = {"V4": "V4", "V5": "V5 (tái tạo)", "V6": "V6 (như công bố, float32)", "V6*": "V6* (V6, trọng số float64)",
         "V7-A": "V7-A (hợp nhất thích ứng)", "B_base": "V7-B (tối ưu tọa độ trực tiếp)",
         "C_rel": "V7-C1 (+ HUI lợi ích rel)", "C_rel_absL3": "V7-C2 (+ HUI abs mức-3) = V7 cuối",
         "C_rel_geo": "V7-C (+ rel + đồng thuận không gian)", "C_devrob": "V7-C (+ đặc trưng bù lệch thiết bị)",
         "D_hier": "V7-D (V7-C2 + ngữ cảnh HUI cấp tầng)"}


def v5_errors(D: list[dict]) -> list[np.ndarray]:
    """V5 = the V6 pipeline without the absolute-strength HUI model: first 25 feature columns."""
    for d in D:
        d["F5"] = d["F"][..., :25]
    from v7.rerank import oof_v6 as _o
    P5 = _o(D, feat_key="F5", name="v5_oof")
    return [err_m(place(p, d["cxy"])[0], d["true"]) for p, d in zip(P5, D)]


def dev_table() -> pd.DataFrame:
    D = load_dev()
    P = oof_v6(D)
    adapt = json.load(open(OUT / "V7A_dev.json"))["adaptT"]["nested_choices"]
    cols = {"V4": [], "V5": v5_errors(D), "V6": [], "V6*": [], "V7-A": []}
    for k, (d, p) in enumerate(zip(D, P)):
        cols["V4"].append(err_m(d["est"], d["true"]))
        cols["V6"].append(err_m(place(p, d["cxy"])[0], d["true"]))
        cols["V6*"].append(err_m(fuse(p.astype(np.float64), d["cxy"], rule="v6", m=20, T=2.0)[0], d["true"]))
        cols["V7-A"].append(err_m(fuse(p.astype(np.float64), d["cxy"], **adapt[k])[0], d["true"]))
    for v in VARIANTS:
        try:
            o = load_oof(v)
        except (FileNotFoundError, RuntimeError):
            continue
        cols[v] = [err_m(o[k][0], D[k]["true"]) for k in range(N_FOLDS)]
    T = pd.DataFrame({
        "fold": np.concatenate([np.full(len(d["true"]), k) for k, d in enumerate(D)]),
        "dvi": np.concatenate([d["dvi"] for d in D]), "phone": np.concatenate([d["phone"] for d in D]),
        "bld": np.concatenate([d["bld"] for d in D]), "flr": np.concatenate([d["flr"] for d in D]),
        "pred_bf": np.concatenate([d["floor"] for d in D]), "n_ap": np.concatenate([d["F"][:, 0, 13] for d in D]),
        "true_x": np.concatenate([d["true"][:, 0] for d in D]), "true_y": np.concatenate([d["true"][:, 1] for d in D]),
        "best30_m": np.concatenate([d["dist"].min(1) for d in D]), "top1_m": np.concatenate([d["dist"][:, 0] for d in D])})
    T["true_bf"] = T.bld.astype(str) + "_" + T.flr.astype(str)
    T["floor_ok"] = T.pred_bf == T.true_bf
    T["informative"] = T.n_ap > 0
    for name, lst in cols.items():
        T["err_" + name] = np.concatenate(lst)
    return T


def summarize(T: pd.DataFrame, models: list[str], mask: np.ndarray, groups: np.ndarray, ref: str | None) -> pd.DataFrame:
    rows = []
    for m in models:
        e = T["err_" + m].to_numpy()[mask]
        mean, lo, hi = cluster_bootstrap_mean(e, groups[mask])
        r = {"model": m, "label": LABEL.get(m, m), "n": int(mask.sum()), "mean": mean, "ci95_lo": lo, "ci95_hi": hi,
             "median": float(np.median(e)), "p75": float(np.percentile(e, 75)), "p90": float(np.percentile(e, 90)),
             "p95": float(np.percentile(e, 95)), "max": float(e.max())}
        if ref and m != ref:
            d, dlo, dhi, pb = paired_cluster_bootstrap(e, T["err_" + ref].to_numpy()[mask], groups[mask])
            r |= {f"diff_vs_{ref}": d, "diff_lo": dlo, "diff_hi": dhi, "p_better": pb,
                  "pct_vs_ref": 100 * d / T["err_" + ref].to_numpy()[mask].mean(),
                  "queries_improved_gt0.5m": int((e < T["err_" + ref].to_numpy()[mask] - 0.5).sum()),
                  "queries_worsened_gt0.5m": int((e > T["err_" + ref].to_numpy()[mask] + 0.5).sum())}
        rows.append(r)
    return pd.DataFrame(rows)


TEST_FILES = {"V4": UJI / "predictions" / "validationData.csv", "V5": UJI / "v5" / "predictions" / "validationData.csv",
              "V6": UJI / "v6" / "predictions" / "validationData.csv"}
TEST_V7 = {"V6_reproduced": "V6r", "V6_star": "V6*", "V7_A": "V7-A", "B_base": "B_base", "C_rel": "C_rel", "C_rel_absL3": "C_rel_absL3",
           "C_rel_geo": "C_rel_geo", "D_hier": "D_hier"}


def test_table() -> pd.DataFrame:
    raw = pd.read_csv(PROJECT_ROOT / "ujiindoorloc" / "UJIndoorLoc" / "validationData.csv")
    T = load_cache("test_validationData")
    r = T["src_row"] - T["src_row"].min()
    df = pd.DataFrame({"src_row": T["src_row"], "phone": raw.PHONEID.to_numpy()[r], "bld": T["bld"], "flr": T["flr"],
                       "pred_bf": T["floor"], "true_x": T["true"][:, 0], "true_y": T["true"][:, 1]})
    df["true_bf"] = df.bld.astype(str) + "_" + df.flr.astype(str)
    df["floor_ok"] = df.pred_bf == df.true_bf
    df["top1_m"] = err_m(T["cxy"][:, 0], T["true"])
    df["best30_m"] = np.sqrt(((T["cxy"] - T["true"][:, None]) ** 2).sum(-1)).min(1) * 0.766126
    for name, f in TEST_FILES.items():
        d = pd.read_csv(f)
        assert (d.src_row.to_numpy() == df.src_row.to_numpy()).all()
        df["err_" + name] = d.err_m.to_numpy()
    for name in TEST_V7:
        f = OUT / "predictions" / f"{name}.csv"
        if f.exists():
            d = pd.read_csv(f)
            assert (d.src_row.to_numpy() == df.src_row.to_numpy()).all()
            df["err_" + TEST_V7[name]] = d.err_m.to_numpy()
    return df


def candidate_selection(T: pd.DataFrame, final: str) -> pd.DataFrame:
    rows = []
    for nm, col in (("HUI cell 1 (điểm cao nhất)", "top1_m"), ("ô gần nhất trong 30 (tiên tri)", "best30_m"),
                    ("V6* (tọa độ hợp nhất)", "err_V6*"), ("V7 cuối (tọa độ hợp nhất)", "err_" + final)):
        rows.append({"nguon": nm} | {f"duoi_{t}m": float((T[col] < t).mean()) for t in (3, 5, 10)} | {"mean_m": float(T[col].mean())})
    return pd.DataFrame(rows)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    T = dev_table()
    T.to_csv(DEST / "dev_per_query.csv", index=False)
    models = [c[4:] for c in T.columns if c.startswith("err_")]
    groups = T.phone.to_numpy()
    inf = T.informative.to_numpy()
    S_inf = summarize(T, models, inf, groups, "V6*")
    S_all = summarize(T, models, np.ones(len(T), bool), groups, "V6*")
    S_inf.to_csv(DEST / "dev_summary_informative.csv", index=False)
    S_all.to_csv(DEST / "dev_summary_all_queries.csv", index=False)
    rows = []
    for nm, mk in (("floor_right", T.floor_ok.to_numpy() & inf), ("floor_wrong", ~T.floor_ok.to_numpy() & inf)):
        for m in models:
            rows.append({"group": nm, "model": m, "n": int(mk.sum()), "mean": float(T["err_" + m][mk].mean()),
                         "median": float(T["err_" + m][mk].median())})
    pd.DataFrame(rows).to_csv(DEST / "dev_by_floor_correct.csv", index=False)
    best = "C_rel_absL3" if "err_C_rel_absL3" in T else "B_base"
    g = T[inf].groupby("phone")
    pd.DataFrame({"n": g.size(), "floor_acc": g.floor_ok.mean(), "V4": g.err_V4.mean(), "V6*": g["err_V6*"].mean(),
                  "V7-A": g["err_V7-A"].mean(), "V7": g["err_" + best].mean(),
                  "gain_vs_V6*": g["err_V6*"].mean() - g["err_" + best].mean(), "best30": g.best30_m.mean()}).round(4).to_csv(
        DEST / "dev_by_phone.csv")
    g = T[inf].groupby("true_bf")
    pd.DataFrame({"n": g.size(), "floor_acc": g.floor_ok.mean(), "V4": g.err_V4.mean(), "V6*": g["err_V6*"].mean(),
                  "V7": g["err_" + best].mean(), "gain_vs_V6*": g["err_V6*"].mean() - g["err_" + best].mean()}).round(4).to_csv(
        DEST / "dev_by_floor.csv")
    candidate_selection(T[inf], best).to_csv(DEST / "dev_candidate_selection.csv", index=False)
    print(S_inf[["model", "mean", "ci95_lo", "ci95_hi", "median", "p90"] + [c for c in S_inf.columns if c.startswith("diff_vs")]].round(4).to_string())
    if (OUT / "test_summary.json").exists():
        Te = test_table()
        Te.to_csv(DEST / "test_per_query.csv", index=False)
        tm = [c[4:] for c in Te.columns if c.startswith("err_")]
        ST = summarize(Te, tm, np.ones(len(Te), bool), Te.phone.to_numpy(), "V6")
        ST.to_csv(DEST / "test_summary.csv", index=False)
        for nm, mk in (("floor_right", Te.floor_ok.to_numpy()), ("floor_wrong", ~Te.floor_ok.to_numpy())):
            pd.DataFrame([{"group": nm, "model": m, "n": int(mk.sum()), "mean": float(Te["err_" + m][mk].mean())} for m in tm]).to_csv(
                DEST / f"test_by_{nm}.csv", index=False)
        g = Te.groupby("phone")
        pd.DataFrame({"n": g.size(), "floor_acc": g.floor_ok.mean(), "V6": g.err_V6.mean(), "V7": g["err_" + best].mean(),
                      "gain": g.err_V6.mean() - g["err_" + best].mean()}).round(4).to_csv(DEST / "test_by_phone.csv")
        candidate_selection(Te.assign(**{"err_V6*": Te["err_V6*"]}), best).to_csv(DEST / "test_candidate_selection.csv", index=False)
        print(ST[["model", "mean", "ci95_lo", "ci95_hi", "median", "p90"] + [c for c in ST.columns if c.startswith("diff_vs")]].round(4).to_string())


if __name__ == "__main__":
    main()
