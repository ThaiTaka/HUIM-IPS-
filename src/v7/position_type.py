"""Error by the geometry of the reference cells around the TRUE position (analysis only; labels are never a model input).

For a query at true position p on floor f, take the cells of floor f within 8 m. Their directions from p leave a largest
empty angular gap g:
    interior   g < 180 deg    cells on every side
    edge       g >= 180 deg   cells only on one side: end of a corridor, room boundary, edge of the surveyed area
    isolated   no cell within 8 m (sparse reference points)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import GF, PROJECT_ROOT, UJI  # noqa: E402

DEST = PROJECT_ROOT / "BAOCAO_V7" / "so_lieu"
R = 8.0


def classify(tx, ty, tbf, cells) -> np.ndarray:
    out = np.empty(len(tx), object)
    by = {f: g[["x", "y"]].to_numpy() for f, g in cells.groupby("building_floor")}
    for i, (x, y, f) in enumerate(zip(tx, ty, tbf)):
        c = by.get(f)
        if c is None:
            out[i] = "isolated"
            continue
        d = np.hypot(c[:, 0] - x, c[:, 1] - y) * GF
        m = (d <= R) & (d > 1e-9)
        if not m.any():
            out[i] = "isolated"
            continue
        a = np.sort(np.arctan2(c[m, 1] - y, c[m, 0] - x))
        gaps = np.diff(np.r_[a, a[0] + 2 * np.pi])
        out[i] = "edge" if gaps.max() >= np.pi else "interior"
    return out


def main() -> None:
    cells = pd.read_csv(UJI / "model" / "cells.csv")
    cells["building_floor"] = cells.building_floor.astype(str)
    rows = []
    dev = pd.read_csv(DEST / "dev_per_query.csv")
    dev = dev[dev.informative]
    te = pd.read_csv(DEST / "test_per_query.csv")
    for nm, df, cols in (("dev", dev, {"V6*": "err_V6*", "V7": "err_C_rel_absL3"}), ("test", te, {"V6": "err_V6", "V7": "err_C_rel_absL3"})):
        df = df.assign(ptype=classify(df.true_x.to_numpy(), df.true_y.to_numpy(), df.true_bf.astype(str).to_numpy(), cells))
        for t, g in df.groupby("ptype"):
            r = {"set": nm, "vi_tri": t, "n": len(g), "share": len(g) / len(df), "floor_acc": g.floor_ok.mean()}
            r |= {k: g[c].mean() for k, c in cols.items()}
            rows.append(r)
    out = pd.DataFrame(rows).round(4)
    out.to_csv(DEST / "by_position_type.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
