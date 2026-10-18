"""Full HUI sets (EFIM) per building, for the step-6 selection rules.

    python src/run_hui_stats.py A          # model A, buildings 0/1/2 in parallel

For each building, θ goes DOWN the step-4 grid and stops at the first θ where
EFIM aborts (time / output budget): every lower θ has a superset of HUIs.
Results: results/huim_opt/huistats_b<k>_<model>_<θ>pct.json.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def frontier(args):
    import huim_opt as H
    import run_huim_opt as R
    m, scope = args
    out = []
    for th in sorted(R.STEP4_GRID, reverse=True):
        s = H.hui_stats(m, scope, th)
        out.append((th, s["status"], s["n_huis"], round(s["runtime_s"], 1)))
        if s["status"] != "COMPLETED":
            break
    return m, scope, out


if __name__ == "__main__":
    models = sys.argv[1] if len(sys.argv) > 1 else "A"
    jobs = [(m, f"b{b}") for m in models for b in range(3)]
    with Pool(len(jobs)) as pool:
        for m, scope, out in pool.imap_unordered(frontier, jobs):
            for th, st, n, sec in out:
                print(f"{m} {scope} {th:g}%: {st} {n} HUIs {sec}s", flush=True)
