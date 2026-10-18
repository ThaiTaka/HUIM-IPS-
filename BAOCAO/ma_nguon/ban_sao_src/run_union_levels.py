"""Compute HUI-union levels (huim_opt.union_level) in a process pool, then
assemble union_<scope>_<model>.npz.

    python src/run_union_levels.py b1            # all models, every θ of the curve
    python src/run_union_levels.py b1 global --workers 9

One θ per task; BLAS pinned to one thread per worker.
"""
from __future__ import annotations

import os

os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                  MKL_NUM_THREADS="1")

import argparse                                          # noqa: E402
import sys                                               # noqa: E402
from multiprocessing import Pool                         # noqa: E402
from pathlib import Path                                 # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))


def task(args):
    import huim_opt as H
    m, scope, th = args
    r = H.union_level(m, scope, th)
    return m, scope, th, int(r["member"].sum()), float(r["seconds"])


def main() -> None:
    import huim_opt as H
    ap = argparse.ArgumentParser()
    ap.add_argument("scopes", nargs="+")
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--models", default="ABC")
    ap.add_argument("--no-assemble", action="store_true")
    a = ap.parse_args()
    jobs = [(m, s, th) for s in a.scopes for m in a.models
            for th in sorted(H.THETA_CURVE)]           # low θ first: cheap ones
    with Pool(a.workers) as pool:
        for m, s, th, n, sec in pool.imap_unordered(task, jobs):
            print(f"{s} {m} {th:g}%: {n} AP, {sec:.1f}s", flush=True)
    for s in ([] if a.no_assemble else a.scopes):
        for m in a.models:
            H.assemble_union_table(m, s)
            print("assembled", s, m, flush=True)


if __name__ == "__main__":
    main()
