"""Compute the HUI-union tables (huim_opt.union_table) for every utility model
and scope, one process per (model, scope), all in parallel.

    python src/run_union_tables.py              # all 12: A/B/C x global/b0/b1/b2
    python src/run_union_tables.py --one A b1   # a single table (used by the pool)

Each worker pins BLAS to one thread, so 12 workers share the 12 cores evenly.
Results: results/huim_opt/union_<scope>_<model>.npz (+ timings in the log).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def one(model: str, scope: str) -> None:
    sys.path.insert(0, str(HERE))
    import huim_opt as H
    H.union_table(model, scope)


def main() -> None:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    log_dir = HERE.parent / "results" / "huim_opt" / "union_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    procs = []
    for scope in ("b0", "b1", "b2", "global"):
        for model in "ABC":
            fh = open(log_dir / f"{scope}_{model}.log", "w", encoding="utf-8")
            procs.append((model, scope, fh, subprocess.Popen(
                [sys.executable, str(Path(__file__)), "--one", model, scope],
                stdout=fh, stderr=subprocess.STDOUT, env=env)))
    bad = 0
    for model, scope, fh, p in procs:
        rc = p.wait()
        fh.close()
        print(f"{model} {scope}: exit {rc}", flush=True)
        bad += rc != 0
    sys.exit(bad)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--one":
        one(sys.argv[2], sys.argv[3])
    else:
        main()
