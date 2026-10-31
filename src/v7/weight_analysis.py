"""How the V7 weights differ from V6's (dev, out-of-fold; labels used only to measure)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.analysis import DEST  # noqa: E402
from v7.common import err_m  # noqa: E402
from v7.experiments import load_oof  # noqa: E402
from v7.fusion import fuse  # noqa: E402
from v7.rerank import load_dev, oof_v6  # noqa: E402

D = load_dev()
P = oof_v6(D)
O = load_oof("C_rel_absL3")
rows = []
for k, d in enumerate(D):
    keep = d["F"][:, 0, 13] > 0
    _x, w6 = fuse(P[k].astype(np.float64), d["cxy"], rule="v6", m=20, T=2.0)
    w7 = O[k][1]
    near = d["dist"] < 3.0
    for nm, w in (("V6*", w6), ("V7", w7)):
        rows.append(pd.DataFrame({"model": nm, "fold": k, "mass_within_3m": (w * near).sum(1), "eff_cells": 1 / (w ** 2).sum(1),
                                  "max_weight": w.max(1), "mass_top1_hui_cell": w[:, 0], "keep": keep, "floor_ok": d["floor"] == np.char.add(np.char.add(d["bld"].astype(str), "_"), d["flr"].astype(str))}))
W = pd.concat(rows)
W = W[W.keep]
out = W.groupby("model")[["mass_within_3m", "eff_cells", "max_weight", "mass_top1_hui_cell"]].mean().round(4)
print(out)
out.to_csv(DEST / "dev_weight_analysis.csv")
T = pd.read_csv(DEST / "dev_per_query.csv")
T = T[T.informative]
d = T["err_V6*"] - T["err_C_rel_absL3"]
worse, better = T[d < -0.5], T[d > 0.5]
rep = pd.DataFrame({"group": ["V7 tốt hơn > 0,5 m", "V7 kém hơn > 0,5 m"], "n": [len(better), len(worse)],
                    "dung_tang": [better.floor_ok.mean(), worse.floor_ok.mean()],
                    "mean_gain_m": [(better["err_V6*"] - better["err_C_rel_absL3"]).mean(), (worse["err_V6*"] - worse["err_C_rel_absL3"]).mean()],
                    "mean_err_V6*": [better["err_V6*"].mean(), worse["err_V6*"].mean()], "mean_best30": [better.best30_m.mean(), worse.best30_m.mean()]})
print(rep.round(3).to_string(index=False))
rep.round(4).to_csv(DEST / "dev_improved_vs_worsened.csv", index=False)
print("phones where V7 worse on dev:", T.groupby("phone").apply(lambda g: g["err_V6*"].mean() - g["err_C_rel_absL3"].mean()).round(3).sort_values().head(5).to_dict())
