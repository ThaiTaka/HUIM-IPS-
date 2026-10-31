"""Out-of-fold dev run of a declared V7 variant; the per-query predictions and weights are cached
(results/huim_only/uji/v7/cache/oof_<variant>.npz) so that tables, bootstraps, ablations and figures are
computed from them.

    python src/v7/run_dev.py --variant C_rel_absL3

Protocol (identical for every variant): 6 dev folds = GroupKFold over PHONEID (as V6). For evaluation fold k the
HUI models of the features were mined on the other five folds' phones only; the scorer ensemble (5 members,
each early-stopped on one of the other folds and fitted on the remaining four) never reads fold k.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import OUT  # noqa: E402
from v7.experiments import direct_oof, prepare, summarize  # noqa: E402
from v7.rerank import load_dev  # noqa: E402

CFG = dict(lr=5e-4, h1=32, h2=16, wd=1e-3, ep=30, tf="slog", patience=8)
VARIANTS = {
    "B_base": (),                        # V7-B  direct optimisation, V6 features only
    "C_rel": ("rel",),                   # + HUI model on the relative-strength utility
    "C_rel_absL3": ("rel", "absL3"),     # + HUI model on (AP, absolute-strength level) items
    "C_rel_geo": ("rel", "geo"),         # + spatial-consensus features (neutral result)
    "C_devrob": ("devrob",),             # device-offset features (negative result)
}


def run(variant: str, seed: int = 0) -> dict:
    blocks = VARIANTS[variant]
    D = load_dev()
    data = prepare(D, blocks)
    out = direct_oof(data, CFG, seed=seed, name=variant, blocks=blocks)
    r = summarize(D, {k: v[0] for k, v in out.items()}, f"{variant} {blocks}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dev").mkdir(exist_ok=True)
    json.dump(r | {"blocks": list(blocks), "cfg": CFG, "seed": seed}, open(OUT / "dev" / f"{variant}.json", "w"), indent=1)
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(VARIANTS))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    run(a.variant, a.seed)
