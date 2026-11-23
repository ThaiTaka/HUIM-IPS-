"""Stage 2 of V7: HUI-evidence features of the 30 candidate cells for the test set (validationData).

Models: the three V6 HUI models mined on the FULL training data (rank, rank-level-3, absolute) and, for V7-C,
the extra models (`rel`, ...) mined on the full training data. Exactly the computation of
`huim_rerank_final.stage_final` (V6): same `compute`, same models, same query preprocessing. The test labels
are stored only so that the error can be measured afterwards; no V7 component reads them.

Run: python src/v7/test_features.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import KEY, OUT, compute, final_abs_model, load_final_base  # noqa: E402
from huim_research import load_model  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import inputs, q_matrix  # noqa: E402
from v7.common import VALID_CSV, base_meta, save_cache, sha256_file  # noqa: E402
from v7.extra_models import BLOCKS, extra_block  # noqa: E402
from v7.final_models import final_path  # noqa: E402

TEST = "validationData"


def build(blocks=("rel",)) -> None:
    b = load(KEY)
    gf = b.ground_factor
    te = b.tests[TEST]
    prep = inputs(b, "rank")[0]
    prepA = inputs(b, "abs")[0]
    pos = load_final_base(gf)
    posL, _ = load_model(OUT / "model_L3.npz", gf)
    posL.cell_bf = pos.cell_bf
    posA = final_abs_model(b)
    assert np.array_equal(np.asarray(pos.cells).astype(str), np.asarray(posL.cells).astype(str))
    assert np.array_equal(np.asarray(pos.cells).astype(str), np.asarray(posA.cells).astype(str))
    q = q_matrix(prep, te, "rank")
    t0 = time.perf_counter()
    f = compute(pos, posL, q, gf, posA, q_matrix(prepA, te, "abs"))
    sec = time.perf_counter() - t0
    arrays = {"F": f["F"], "cxy": f["cxy"], "cand": f["cand"], "floor": f["floor"].astype(str), "est": f["est"],
              "true": te[["X", "Y"]].to_numpy(np.float64), "bld": te["BUILDINGID"].to_numpy(), "flr": te["FLOOR"].to_numpy(),
              "phone": te["PHONEID"].to_numpy(), "src_row": te["SRC_ROW"].to_numpy(), "cell_xy": pos.cell_xy,
              "cell_bf": pos.cell_bf.astype(str)}
    meta = base_meta(kind="test_features", test_csv_sha256=sha256_file(VALID_CSV), n_queries=int(len(q)),
                     models="rank + rank-L3 + abs, mined on the full training data", seconds_per_query_v6_part=round(sec / len(q), 4))
    save_cache(f"test_{TEST}", meta, **arrays)
    print(f"test features: {f['F'].shape} in {sec:.0f}s", flush=True)
    for name in blocks:
        kind, levels = BLOCKS[name]
        pe, _ = load_model(final_path(kind, levels), gf)
        assert np.array_equal(np.asarray(pe.cells).astype(str), np.asarray(pos.cells).astype(str))
        from huim_research import expand_levels
        qe = expand_levels(q_matrix(inputs(b, kind)[0], te, kind), levels)
        t0 = time.perf_counter()
        X = extra_block(pe, qe, f["cand"], f["floor"])
        meta = base_meta(kind="test_extra_block", block=name, test_csv_sha256=sha256_file(VALID_CSV), n_queries=int(len(q)),
                         seconds_per_query=round((time.perf_counter() - t0) / len(q), 4))
        save_cache(f"test_{TEST}_{name}", meta, X=X)
        print(f"test block {name}: {X.shape}", flush=True)


if __name__ == "__main__":
    build(tuple(sys.argv[1:]) or ("rel",))
