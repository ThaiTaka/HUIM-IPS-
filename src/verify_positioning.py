"""Re-check every reported positioning number with nothing but the Python
standard library (csv + math): no numpy, no pandas, no scikit-learn.

The point is independence. The experiment code computes accuracies with
sklearn and errors with numpy; this script reads the raw CSVs and the
per-fingerprint prediction files and does the arithmetic again from scratch,
so agreement means the reported numbers really follow from the predictions.

What it checks
  A. accuracy      building / floor / joint accuracy = (correct rows) / 1,111
  B. metres        error = sqrt(dx^2 + dy^2) per row, scaled to ground metres
                   with a Web Mercator factor recomputed here from the latitude
  C. statistics    mean / median / p75 / p90 / p95 of those errors
  D. coordinates   for the optimised model, each predicted (x, y) is rebuilt
                   from its neighbours: sum(w_i * x_i) / sum(w_i), with x_i read
                   from trainingData.csv
  E. neighbours    --brute N: for N validation rows, the nearest training row is
                   searched again over all 19,937 rows with a hand-written
                   distance, and must be the row the model used

Every reported value is compared with the JSON written by the experiment:
results/ips_summary.json (the study's k-NN) and
results/positioning_optimisation.json (the optimised positioning model).

Usage
  python src/verify_positioning.py               # checks A-D
  python src/verify_positioning.py --brute 25    # + E on 25 random rows
  python src/verify_positioning.py --row 17      # explain validation line 17
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "results" / "predictions"
OUT = ROOT / "results" / "verification"
R_WGS84 = 6378137.0
NOT_DETECTED = 100


def find_csv(name: str) -> Path:
    for d in (ROOT / "ujiindoorloc" / "UJIndoorLoc", ROOT / "ujiindoorloc", ROOT):
        if (d / name).is_file():
            return d / name
    raise FileNotFoundError(name)


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        head = next(r)
        return head, list(r)


def percentile(sorted_vals: list[float], q: float) -> float:
    """Linear interpolation between closest ranks - numpy's default method,
    written out so it can be checked by hand."""
    pos = (len(sorted_vals) - 1) * q / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def ground_factor(train_y: list[float]) -> float:
    """cos(latitude) at the centre of the site: the Web Mercator scale factor
    is 1/cos(lat), so projected metres x cos(lat) = metres on the ground."""
    yc = (min(train_y) + max(train_y)) / 2.0
    lat = 2.0 * math.atan(math.exp(yc / R_WGS84)) - math.pi / 2.0
    return math.cos(lat)


def summary(errors: list[float]) -> dict:
    s = sorted(errors)
    return {"mean": sum(s) / len(s), "median": percentile(s, 50),
            "p75": percentile(s, 75), "p90": percentile(s, 90),
            "p95": percentile(s, 95)}


def compare(label: str, mine: float, reported: float, tol: float,
            log: list) -> bool:
    ok = abs(mine - reported) <= tol
    log.append({"check": label, "recomputed": round(mine, 6),
                "reported": reported, "result": "PASS" if ok else "FAIL"})
    print(f"  {'PASS' if ok else 'FAIL'}  {label:<44s} recomputed "
          f"{mine:12.6f}   reported {reported:12.6f}")
    return ok


def check_file(name: str, pred_path: Path, reported: dict, factor: float,
               train_xy: dict[int, tuple[float, float]], log: list) -> None:
    print(f"\n=== {name}: {pred_path.name}")
    head, rows = read_rows(pred_path)
    ix = {h: i for i, h in enumerate(head)}
    n = len(rows)
    b_ok = sum(r[ix["true_building"]] == r[ix["pred_building"]] for r in rows)
    f_ok = sum(r[ix["true_floor"]] == r[ix["pred_floor"]] for r in rows)
    j_ok = sum(r[ix["true_building"]] == r[ix["pred_building"]]
               and r[ix["true_floor"]] == r[ix["pred_floor"]] for r in rows)
    print(f"  rows: {n};  building correct {b_ok}, floor correct {f_ok}, "
          f"both correct {j_ok}")
    compare(f"{name}: building accuracy", b_ok / n,
            reported["building_accuracy"], 5e-7, log)
    compare(f"{name}: floor accuracy", f_ok / n,
            reported["floor_accuracy"], 5e-7, log)
    compare(f"{name}: joint accuracy", j_ok / n,
            reported["joint_building_floor_accuracy"], 5e-7, log)

    proj, ground = [], []
    worst_xy = 0.0
    for r in rows:
        tx, ty = float(r[ix["true_x"]]), float(r[ix["true_y"]])
        px, py = float(r[ix["pred_x"]]), float(r[ix["pred_y"]])
        if "nbr1_train_line" in ix:          # rebuild (x, y) from neighbours
            pts = []                         # one point per ensemble member
            for pre in ("", "m2_"):
                if f"{pre}nbr1_train_line" not in ix:
                    continue
                sw = sx = sy = 0.0
                k = 1
                while f"{pre}nbr{k}_train_line" in ix:
                    w = float(r[ix[f"{pre}nbr{k}_weight"]])
                    x, y = train_xy[int(r[ix[f"{pre}nbr{k}_train_line"]])]
                    sw += w
                    sx += w * x
                    sy += w * y
                    k += 1
                pts.append((sx / sw, sy / sw))
            bx = sum(p[0] for p in pts) / len(pts)
            by = sum(p[1] for p in pts) / len(pts)
            worst_xy = max(worst_xy, abs(bx - px), abs(by - py))
        d = math.hypot(tx - px, ty - py)
        proj.append(d)
        ground.append(d * factor)
    if "nbr1_train_line" in ix:
        ok = worst_xy < 1e-6
        log.append({"check": f"{name}: (x, y) = weighted mean of neighbours",
                    "recomputed": worst_xy, "reported": 0.0,
                    "result": "PASS" if ok else "FAIL"})
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: (x,y) rebuilt from the "
              f"neighbours, largest difference {worst_xy:.2e} m")
    sg, sp = summary(ground), summary(proj)
    pe = reported["positioning_error"]
    compare(f"{name}: mean error, projected m", sp["mean"],
            pe["mean_error"], 5e-4, log)
    for key in ("mean", "median", "p75", "p90", "p95"):
        compare(f"{name}: {key} error, ground m", sg[key],
                pe[f"{key}_error_ground_m"], 5e-4, log)


def bray_curtis(a: list[float], b: list[float]) -> float:
    num = sum(abs(x - y) for x, y in zip(a, b))
    den = sum(x + y for x, y in zip(a, b))
    return num / den if den else 1.0


def manhattan(a: list[float], b: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def positive(raw: list[float]) -> list[float]:
    """The study's representation: 100 (not detected) -> 0, RSSI in
    [-104, 0] dBm -> 1 + (RSSI + 104)/104 * 99, i.e. 1..100."""
    return [0.0 if v == NOT_DETECTED else
            1.0 + (min(max(v, -104.0), 0.0) + 104.0) / 104.0 * 99.0
            for v in raw]


def exponential(raw: list[float]) -> list[float]:
    """exp((RSSI + 105)/24) / exp(105/24), 0 when not detected."""
    return [0.0 if v == NOT_DETECTED else
            math.exp((min(max(v, -104.0), 0.0) + 105.0) / 24.0)
            / math.exp(105.0 / 24.0) for v in raw]


def powed(raw: list[float]) -> list[float]:
    """((RSSI + 105)/105)^e, 0 when not detected."""
    return [0.0 if v == NOT_DETECTED else
            ((min(max(v, -104.0), 0.0) + 105.0) / 105.0) ** math.e
            for v in raw]


REPRESENTATION = {"positive": positive, "exponential": exponential,
                  "powed": powed}


def shifted(raw: list[float], delta: float) -> list[float]:
    """Add delta dB to every detected reading, clipped to [-104, 0]."""
    return [v if v == NOT_DETECTED else min(max(v + delta, -104.0), 0.0)
            for v in raw]


def members(cfg: dict) -> list[tuple[str, str, str]]:
    """(column prefix, representation, delta column) per ensemble member."""
    out = [("", cfg["representation"], "delta_db")]
    if cfg.get("ensemble_with"):
        out.append(("m2_", cfg["ensemble_with"], "m2_delta_db"))
    return out


def load_fingerprints(path: Path):
    head, rows = read_rows(path)
    wcols = [i for i, h in enumerate(head) if h.startswith("WAP")]
    ix = {h: i for i, h in enumerate(head)}
    fps = {}
    for line, r in enumerate(rows, start=2):        # Excel/CSV line number
        fps[line] = {"raw": [float(r[i]) for i in wcols],
                     "x": float(r[ix["LONGITUDE"]]),
                     "y": float(r[ix["LATITUDE"]]),
                     "b": r[ix["BUILDINGID"]], "f": r[ix["FLOOR"]]}
    return [head[i] for i in wcols], fps


def brute_force(n: int, log: list) -> None:
    """Search the nearest training fingerprint again, by hand, for n rows."""
    print(f"\n=== E. nearest neighbour searched again over every training row "
          f"({n} random validation rows; pure Python, takes a while)")
    _, train = load_fingerprints(find_csv("trainingData.csv"))
    _, val = load_fingerprints(find_csv("validationData.csv"))
    cfg = json.load(open(ROOT / "results" / "positioning_optimisation.json",
                         encoding="utf-8"))["selected_config"]
    reps = {}

    def train_rep(kind):
        if kind not in reps:
            f = REPRESENTATION[kind]
            reps[kind] = {k: f(v["raw"]) for k, v in train.items()}
        return reps[kind]

    lines = random.Random(20251007).sample(sorted(val), n)
    checks = [("study k-NN (positive + Manhattan, k=1)",
               PRED / "val_predictions_study_knn.csv", "", "positive",
               None, manhattan)]
    for pre, kind, dcol in members(cfg):
        checks.append((f"optimised, member {'2' if pre else '1'} ({kind} + "
                       f"Bray-Curtis)", PRED / "val_predictions_optimised.csv",
                       pre, kind, dcol, bray_curtis))
    for name, path, pre, kind, dcol, dist in checks:
        head, rows = read_rows(path)
        ix = {h: i for i, h in enumerate(head)}
        by_line = {int(r[ix["csv_line"]]): r for r in rows}
        T = train_rep(kind)
        f = REPRESENTATION[kind]
        agree = 0
        for line in lines:
            r = by_line[line]
            raw = val[line]["raw"]
            if dcol:
                raw = shifted(raw, float(r[ix[dcol]]))
            q = f(raw)
            dmin = min(dist(q, t) for t in T.values())
            used = int(r[ix[f"{pre}nbr1_train_line"]])
            # ties: any row at the minimum distance is an equally valid choice
            agree += abs(dmin - dist(q, T[used])) <= 1e-12 * max(1.0, dmin)
        ok = agree == n
        log.append({"check": f"E. {name}: nearest training row",
                    "recomputed": agree, "reported": n,
                    "result": "PASS" if ok else "FAIL"})
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {agree}/{n} rows have "
              f"the same nearest-neighbour distance as the model's choice")


def explain(line: int) -> None:
    """Print, for one validation row, every step of both models' calculation."""
    names, train = load_fingerprints(find_csv("trainingData.csv"))
    _, val = load_fingerprints(find_csv("validationData.csv"))
    cfg = json.load(open(ROOT / "results" / "positioning_optimisation.json",
                         encoding="utf-8"))["selected_config"]
    v = val[line]
    factor = ground_factor([t["y"] for t in train.values()])
    print(f"validationData.csv line {line}: BUILDINGID {v['b']}, FLOOR {v['f']}, "
          f"LONGITUDE {v['x']}, LATITUDE {v['y']}")
    det = [(names[j], v["raw"][j]) for j in range(len(names))
           if v["raw"][j] != NOT_DETECTED]
    print(f"{len(det)} WAPs detected (all other {len(names) - len(det)} columns "
          f"are 100 = not detected):")
    print("   " + ", ".join(f"{w}={int(r)}" for w, r in det))
    plan = [("STUDY k-NN (positive + Manhattan, k=1)",
             "val_predictions_study_knn.csv", [("", "positive", None)])]
    plan.append((f"OPTIMISED model ({cfg['representation']} + Bray-Curtis, "
                 f"k={cfg['k']}, w=1/d^{cfg['power']:g}"
                 + (f", ensemble with {cfg['ensemble_with']}"
                    if cfg.get("ensemble_with") else "") + ")",
                 "val_predictions_optimised.csv", members(cfg)))
    for title, fname, mems in plan:
        head, rows = read_rows(PRED / fname)
        ix = {h: i for i, h in enumerate(head)}
        r = next(r for r in rows if int(r[ix["csv_line"]]) == line)
        print(f"\n--- {title}")
        pts = []
        for pre, kind, dcol in mems:
            if dcol:
                print(f"member {'2' if pre else '1'} ({kind}): device offset "
                      f"{r[ix[dcol]]} dB added to every detected RSSI")
            k = 1
            sw = sx = sy = 0.0
            while f"{pre}nbr{k}_train_line" in ix:
                t = int(r[ix[f"{pre}nbr{k}_train_line"]])
                w = float(r[ix[f"{pre}nbr{k}_weight"]])
                d = float(r[ix[f"{pre}nbr{k}_distance"]])
                tt = train[t]
                print(f"  neighbour {k:2d}: trainingData.csv line {t:5d}  "
                      f"distance {d:.6f}  weight {w:.6f}  B{tt['b']} F{tt['f']}"
                      f"  x={tt['x']:.4f} y={tt['y']:.4f}")
                sw += w
                sx += w * tt["x"]
                sy += w * tt["y"]
                k += 1
            pts.append((sx / sw, sy / sw))
            print(f"  -> (sum w*x / sum w, sum w*y / sum w) = "
                  f"({sx / sw:.4f}, {sy / sw:.4f})")
        px = sum(p[0] for p in pts) / len(pts)
        py = sum(p[1] for p in pts) / len(pts)
        if len(pts) > 1:
            print(f"ensemble: mean of the {len(pts)} member estimates = "
                  f"({px:.4f}, {py:.4f})")
        d = math.hypot(v["x"] - px, v["y"] - py)
        print(f"predicted (x, y) = ({px:.4f}, {py:.4f})   [file: "
              f"{r[ix['pred_x']]}, {r[ix['pred_y']]}]")
        print(f"predicted building/floor: {r[ix['pred_building']]}/"
              f"{r[ix['pred_floor']]}   true: {v['b']}/{v['f']}")
        print(f"error = sqrt(({v['x']:.4f} - {px:.4f})^2 + ({v['y']:.4f} - "
              f"{py:.4f})^2) = {d:.4f} projected m  x {factor:.6f} = "
              f"{d * factor:.4f} m on the ground")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brute", type=int, default=0,
                    help="also re-search the nearest neighbour for N rows")
    ap.add_argument("--row", type=int, default=0,
                    help="explain one validationData.csv line and exit")
    a = ap.parse_args()
    if a.row:
        explain(a.row)
        return

    _, train_rows = read_rows(find_csv("trainingData.csv"))
    head, _ = read_rows(find_csv("trainingData.csv"))
    ix = {h: i for i, h in enumerate(head)}
    train_xy = {line: (float(r[ix["LONGITUDE"]]), float(r[ix["LATITUDE"]]))
                for line, r in enumerate(train_rows, start=2)}
    factor = ground_factor([xy[1] for xy in train_xy.values()])
    print(f"Web Mercator ground factor recomputed from the latitude: "
          f"cos(lat) = {factor:.6f}")

    log: list = []
    study = json.load(open(ROOT / "results" / "ips_summary.json",
                           encoding="utf-8"))
    base = study["conditions"]["baseline_all_520"]["result"]["knn"]
    compare("Web Mercator factor vs ips_model.py", factor,
            base["positioning_error"]["ground_correction_factor"], 5e-7, log)
    check_file("study k-NN", PRED / "val_predictions_study_knn.csv", base,
               factor, train_xy, log)
    opt = json.load(open(ROOT / "results" / "positioning_optimisation.json",
                         encoding="utf-8"))
    check_file("optimised", PRED / "val_predictions_optimised.csv",
               opt["validation"]["selected"], factor, train_xy, log)
    if a.brute:
        brute_force(a.brute, log)

    n_fail = sum(c["result"] == "FAIL" for c in log)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "positioning_checks.json", "w", encoding="utf-8") as fh:
        json.dump({"what": "pure-Python re-computation of the positioning "
                           "results", "n_checks": len(log),
                   "n_failed": n_fail, "checks": log}, fh, indent=2,
                  ensure_ascii=False)
    print(f"\n{len(log)} checks, {n_fail} failed -> {OUT / 'positioning_checks.json'}")
    if n_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
