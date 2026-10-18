"""Independent checks of the v6 UJIIndoorLoc result (no model is run).

    C1  mean / median error recomputed from predictions (true and predicted x, y)
    C2  every predicted (x, y) = sum_j weight_j * position of cell_j (cells.csv)
    C3  weights are positive and sum to 1 per query
    C4  every cell used lies on the predicted building-floor
    C5  the v4 estimate embedded in v6 equals v4's own predictions file
    C6  the test rows are exactly validationData (count and source rows)
    C7  the dev number in summary.json equals the out-of-fold research number

Run: python src/verify_v6.py   -> results/huim_only/uji/v6/verification.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import PROJECT_ROOT

R = PROJECT_ROOT / "results" / "huim_only" / "uji"
GF = 0.766126


def main() -> None:
    S = json.load(open(R / "v6" / "summary.json"))
    P = pd.read_csv(R / "v6" / "predictions" / "validationData.csv")
    P4 = pd.read_csv(R / "predictions" / "validationData.csv")
    C = pd.read_csv(R / "model" / "cells.csv")
    T = S["tests"]["validationData"]
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    e = np.hypot(P.pred_x - P.true_x, P.pred_y - P.true_y) * GF
    add("C1 mean error", abs(e.mean() - T["mean_err_m"]) < 1e-4, f"{e.mean():.4f} vs {T['mean_err_m']}")
    add("C1 median error", abs(np.median(e) - T["median_err_m"]) < 1e-4, f"{np.median(e):.4f} vs {T['median_err_m']}")
    m = S["m"]
    idx = P[[f"cell{j}_index" for j in range(1, m + 1)]].to_numpy()
    w = P[[f"cell{j}_weight" for j in range(1, m + 1)]].to_numpy()
    x = (w * C.x.to_numpy()[idx]).sum(1)
    y = (w * C.y.to_numpy()[idx]).sum(1)
    d = np.abs(np.c_[x - P.pred_x, y - P.pred_y]).max()
    add("C2 position = weighted cells", d < 1e-6, f"max deviation {d:.2e}")
    add("C3 weights", (w > 0).all() and np.allclose(w.sum(1), 1), f"min {w.min():.3g}, sum range {w.sum(1).min():.6f}-{w.sum(1).max():.6f}")
    bf = C.building_floor.astype(str).to_numpy()[idx]
    add("C4 cells on predicted floor", (bf == P.pred_building_floor.astype(str).to_numpy()[:, None]).all(), "all cells")
    d4 = np.abs(np.c_[P.v4_x - P4.pred_x, P.v4_y - P4.pred_y]).max()
    add("C5 v4 reproduced", d4 < 1e-6 and (P.pred_building_floor.astype(str) == P4.pred_building_floor.astype(str)).all(),
        f"max deviation {d4:.2e}; floors identical")
    raw = pd.read_csv(PROJECT_ROOT / "ujiindoorloc" / "UJIndoorLoc" / "validationData.csv")
    r = P.src_row.to_numpy() - P.src_row.min()
    ok = (len(raw) == len(P) and len(np.unique(r)) == len(raw)
          and np.allclose(raw.LONGITUDE.to_numpy()[r], P.true_x) and np.allclose(raw.LATITUDE.to_numpy()[r], P.true_y))
    add("C6 test rows = validationData", ok, f"{len(P)} rows, file has {len(raw)}; positions match")
    oof = json.load(open(R / "research" / "summary.json"))["dev_mean_m"]["v5 + abs HUI model (v6)"]
    add("C7 dev number", abs(oof - S["dev"]["dev_mean_v5_m"]) < 1e-3, f"{S['dev']['dev_mean_v5_m']} vs research {oof}")
    out = {"n_checks": len(checks), "n_failed": sum(not c["ok"] for c in checks), "checks": checks}
    json.dump(out, open(R / "v6" / "verification.json", "w"), ensure_ascii=False, indent=1)
    for c in checks:
        print(("OK  " if c["ok"] else "FAIL"), c["check"], "-", c["detail"])


if __name__ == "__main__":
    main()
