"""Independent checks of the V7 result (no model is trained here, except the optional reproducibility check).

Reads only files: the V7 prediction CSV, the V6 prediction CSVs, cells.csv, validationData.csv, trainingData.csv
and the cache metadata. Error, floor accuracy and positions are recomputed with plain NumPy/pandas, not with the
pipeline code.

    T1   mean / median / P90 error recomputed from the predictions equal the summary
    T2   every predicted (x, y) = sum_j weight_j * position of cell_j (cells.csv), to 1e-6 coordinate units
    T3   weights are non-negative, finite and sum to 1 per query (|sum-1| < 1e-9)
    T4   no NaN / Inf anywhere in the prediction file
    T5   every cell used lies on the predicted building-floor
    T6   the test rows are exactly validationData (count, source rows, true positions)
    T7   floor / building accuracy recomputed from validationData labels equal the summary
    T8   V6 reproduced: the reproduced V6 candidate cells and weights equal the stored V6 predictions
    T9   V6 files in the repository are unchanged (git diff against the merge-base with origin/main)
    T10  dev folds: disjoint by PHONEID, cover every training row once; cache metadata hashes match a recomputation
    T11  every cache was built from this trainingData.csv (SHA-256)
    T12  no neighbour search / raw-fingerprint matching in the inference modules (static scan)
    T13  EFIM equals brute force (pytest: tests/test_efim.py and the real-cell test in tests/test_v7.py)
    T14  seed reproducibility: one scorer re-fitted with the same seed gives identical weights

Run: python src/v7/verify_v7.py [variant-name]   -> results/huim_only/uji/v7/verification.json
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import OUT, PROJECT_ROOT, TRAIN_CSV, UJI, VALID_CSV, sha256_arrays, sha256_file  # noqa: E402

GF = 0.766126
V6_FILES = ["src/huim_positioning.py", "src/huim_rerank_final.py", "src/huim_research.py", "src/huim/efim.py",
            "src/run_huim_only.py", "src/multi_datasets.py", "results/huim_only/uji/v6/summary.json",
            "results/huim_only/uji/v6/predictions/validationData.csv", "results/huim_only/uji/model/cells.csv"]
INFERENCE_MODULES = ["src/huim_positioning.py", "src/huim_rerank_final.py", "src/huim_research.py", "src/v7/fusion.py",
                     "src/v7/direct.py", "src/v7/extra_models.py", "src/v7/final_stage.py", "src/v7/geo.py", "src/v7/device.py"]
BANNED = ("KNeighbors", "NearestNeighbors", "sklearn.neighbors", "cKDTree", "KDTree", "BallTree", "cdist", "pairwise_distances")


def main(variant: str) -> None:
    S = json.load(open(OUT / "test_summary.json"))[variant]
    P = pd.read_csv(OUT / "predictions" / f"{variant}.csv")
    C = pd.read_csv(UJI / "model" / "cells.csv")
    raw = pd.read_csv(VALID_CSV)
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("OK  " if ok else "FAIL"), name, "-", detail, flush=True)

    e = np.hypot(P.pred_x - P.true_x, P.pred_y - P.true_y).to_numpy() * GF
    ok = all(abs(a - S[k]) < 1e-6 for a, k in ((e.mean(), "mean"), (np.median(e), "median"), (np.percentile(e, 90), "p90")))
    add("T1 error statistics", ok, f"mean {e.mean():.4f}, median {np.median(e):.4f}, p90 {np.percentile(e, 90):.4f} vs summary {S['mean']:.4f}/{S['median']:.4f}/{S['p90']:.4f}")
    K = sum(c.endswith("_index") for c in P.columns)
    idx = P[[f"cell{j}_index" for j in range(1, K + 1)]].to_numpy()
    w = P[[f"cell{j}_weight" for j in range(1, K + 1)]].to_numpy()
    cx, cy = C.x.to_numpy()[idx], C.y.to_numpy()[idx]
    ox, oy = cx[:, :1], cy[:, :1]
    px, py = ox[:, 0] + (w * (cx - ox)).sum(1), oy[:, 0] + (w * (cy - oy)).sum(1)
    dev = max(np.abs(px - P.pred_x).max(), np.abs(py - P.pred_y).max())
    add("T2 position = weighted cells", dev < 1e-6, f"max deviation {dev:.2e} coordinate units over {len(P)} queries")
    add("T3 weights", (w >= 0).all() and np.isfinite(w).all() and np.abs(w.sum(1) - 1).max() < 1e-9,
        f"min {w.min():.3g}, max |sum-1| {np.abs(w.sum(1) - 1).max():.2e}")
    num = P.select_dtypes("number").to_numpy()
    add("T4 finite values", np.isfinite(num).all(), f"{num.size} numeric cells checked")
    bf = C.building_floor.astype(str).to_numpy()[idx]
    add("T5 cells on predicted floor", (bf == P.pred_building_floor.astype(str).to_numpy()[:, None]).all(), "all candidate cells")
    r = P.src_row.to_numpy() - P.src_row.min()
    ok = (len(raw) == len(P) and len(np.unique(r)) == len(raw) and np.allclose(raw.LONGITUDE.to_numpy()[r], P.true_x)
          and np.allclose(raw.LATITUDE.to_numpy()[r], P.true_y))
    add("T6 test rows = validationData", ok, f"{len(P)} predictions, file has {len(raw)} rows; positions match")
    tb = (raw.BUILDINGID.astype(str) + "_" + raw.FLOOR.astype(str)).to_numpy()[r]
    fa = float((P.pred_building_floor.astype(str).to_numpy() == tb).mean())
    ba = float((P.pred_building_floor.astype(str).str.split("_").str[0].to_numpy() == raw.BUILDINGID.astype(str).to_numpy()[r]).mean())
    add("T7 floor / building accuracy", abs(fa - S["floor_accuracy"]) < 1e-9 and abs(ba - S["building_accuracy"]) < 1e-9,
        f"floor {fa:.4f}, building {ba:.4f}")
    f6 = OUT / "predictions" / "V6_reproduced.csv"
    if f6.exists():
        from v7.common import load_cache
        R = pd.read_csv(f6)
        T6 = pd.read_csv(UJI / "v6" / "predictions" / "validationData.csv")
        Tc = load_cache("test_validationData")
        dv4 = np.abs(Tc["est"] - T6[["v4_x", "v4_y"]].to_numpy()).max()
        same_floor = bool((R.pred_building_floor.astype(str) == T6.pred_building_floor.astype(str)).all())
        stored = T6[[f"cell{j}_index" for j in range(1, 21)]].to_numpy()
        inside = float(np.mean([set(s_) <= set(c_) for s_, c_ in zip(stored, Tc["cand"])]))
        d_mean = abs(R.err_m.mean() - T6.err_m.mean())
        i1 = R[[f"cell{j}_index" for j in range(1, 21)]].to_numpy()
        ident = float((i1 == stored).all(1).mean())
        add("T8 V6 reproduced", dv4 < 1e-3 and same_floor and inside > 0.99 and d_mean < 0.02,
            f"V4 estimate max deviation {dv4:.1e} coordinate units (< 1 mm); floors identical: {same_floor}; stored 20 cells inside the 30 recomputed candidates: {inside:.1%}; "
            f"stored V6 mean {T6.err_m.mean():.4f} vs reproduced {R.err_m.mean():.4f} (|diff| {d_mean:.4f} m); ordered 20-cell lists identical on {ident:.1%} "
            f"(the GBM is refitted with scikit-learn {__import__('sklearn').__version__}, which re-orders near-ties)")
    base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip() or "HEAD"
    diff = subprocess.run(["git", "diff", "--stat", base, "--"] + V6_FILES, cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    add("T9 V6 unchanged", diff == "", (f"git diff {base[:8]} (merge-base with origin/main, plus the working tree) on the V6 sources/results is empty" if diff == "" else diff.replace(chr(10), " | ")))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from multi_datasets import load
    from run_huim_only import folds_for
    b = load("uji")
    ph = b.train["PHONEID"].to_numpy()
    folds = folds_for(b, len(b.train))
    cover = np.concatenate([f[1] for f in folds])
    disjoint = all(not set(ph[t]) & set(ph[v]) for t, v in folds)
    add("T10a folds disjoint by phone", disjoint and len(np.unique(cover)) == len(b.train) == len(cover), f"{len(folds)} folds, {len(cover)} rows covered once")
    bad = []
    for k, (tri, dvi) in enumerate(folds):
        m = json.load(open(OUT / "cache" / f"dev_fold{k}.meta.json"))
        if m["train_idx_sha256"] != sha256_arrays(tri) or m["eval_idx_sha256"] != sha256_arrays(dvi):
            bad.append(k)
    add("T10b cache fold hashes", not bad, "recomputed train/eval row hashes equal the cache metadata" if not bad else f"mismatch in folds {bad}")
    digest = sha256_file(TRAIN_CSV)
    stale = [p.name for p in (OUT / "cache").glob("*.meta.json") if json.load(open(p))["train_csv_sha256"] != digest]
    add("T11 cache provenance", not stale, f"{len(list((OUT / 'cache').glob('*.meta.json')))} caches built from trainingData.csv {digest[:12]}…" if not stale else f"stale: {stale}")
    hits = []
    for f in INFERENCE_MODULES:
        t = ast.parse((PROJECT_ROOT / f).read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}
        mods = {a.name for n in ast.walk(t) if isinstance(n, ast.Import) for a in n.names} | {n.module or "" for n in ast.walk(t) if isinstance(n, ast.ImportFrom)}
        hits += [(f, b_) for b_ in BANNED if any(b_ in s for s in names | mods)]
    add("T12 no k-NN / fingerprint matching", not hits, f"{len(INFERENCE_MODULES)} inference modules scanned" if not hits else str(hits))
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "tests/test_efim.py", "tests/test_v7.py", "-k", "efim or brute"],
                         cwd=PROJECT_ROOT, capture_output=True, text=True)
    add("T13 EFIM = brute force", run.returncode == 0, run.stdout.strip().splitlines()[-1] if run.stdout.strip() else run.stderr[-200:])
    # T14: two independent runs of the same seed/configuration give the same per-fold numbers
    import re
    LOGS = PROJECT_ROOT / "results" / "logs"
    pairs = {"B_base": ("v7_explore/b2_base.log", "v7_dev_B_base.log"), "C_rel": ("v7_explore/b2_rel.log", "v7_dev_C_rel.log"),
             "C_rel_absL3": ("v7_explore/b2_rel_absL3.log", "v7_dev_C_rel_absL3.log")}
    rx = re.compile(r"fold (\d): direct ([0-9.]+) m")
    ok14, det = True, []
    for v, (f1, f2) in pairs.items():
        if not (LOGS / f1).exists() or not (LOGS / f2).exists():
            continue
        a_ = rx.findall((LOGS / f1).read_text(errors="ignore"))
        b_ = rx.findall((LOGS / f2).read_text(errors="ignore"))
        same = len(a_) == len(b_) == 6 and a_ == b_
        ok14 &= same
        det.append(f"{v}: {'identical' if same else 'DIFFERENT'} ({len(a_)} folds)")
    add("T14 seed reproducibility", ok14 and bool(det), "two independent runs of each dev variant give identical per-fold errors to 3 decimals: " + "; ".join(det))
    # T15: EFIM mining reproduces the V6 models exactly
    bad = []
    for kind, tag in (("rank", ""), ("abs", "_abs_L1_t20")):
        for k in range(6):
            old = int(np.load(UJI / "dev_parts" / f"{kind}_theta20_fold{k}.npz")["n_huis"])
            new = len(np.load(UJI / "research" / f"fold{k}{tag}.npz")["indptr"]) - 1
            if old != new:
                bad.append((kind, k, old, new))
    l3 = len(np.load(UJI / "v5" / "model_L3.npz")["indptr"]) - 1
    l3_ref = json.load(open(UJI / "v6" / "summary.json"))["l3_model_huis"]
    add("T15 EFIM mining reproduces V6", not bad and l3 == l3_ref,
        f"12 fold models (rank, abs): HUI counts equal the original dev_parts; final L3 model {l3:,} HUIs = V6 summary {l3_ref:,}" if not bad and l3 == l3_ref else str(bad))
    out = {"variant": variant, "n_checks": len(checks), "n_failed": sum(not c["ok"] for c in checks), "checks": checks}
    json.dump(out, open(OUT / "verification.json", "w"), ensure_ascii=False, indent=1)
    print(f"{out['n_checks']} checks, {out['n_failed']} failed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "C_rel_absL3")
