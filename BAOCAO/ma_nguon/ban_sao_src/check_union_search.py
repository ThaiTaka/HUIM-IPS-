"""Check the HUI-union tables against every EFIM run that COMPLETED on UJIIndoorLoc.

    python src/run_union_tables.py      # first: builds results/huim_opt/union_*.npz
    python src/check_union_search.py

For the global scope, the union of huim/union_search.py at each minUtil of
PHASE H must equal the WAP set of the EFIM run (results/hui/<run>__waps.json).
Writes results/huim_opt/union_check.csv; fails loudly on any difference.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import huim_opt as H                                   # noqa: E402


def main() -> None:
    D = H.data()
    rows = []
    for m in "ABC":
        T = H.union_table(m, "global")
        runs = H.huim_runs(m)
        assert abs(float(T["total_utility"]) - runs.total_db_utility.iloc[0]) \
            < 1e-6 * float(T["total_utility"])
        for _, r in runs[runs.status == "COMPLETED"].iterrows():
            k = np.flatnonzero(np.isclose(T["theta_pct"], r.rel_minutil_pct))
            if not len(k):
                assert r.n_huis == 0, r.run_tag    # 15% / 20%: empty anyway
                continue
            k = int(k[0])
            got = {D.wap[j] for j in np.flatnonzero(T["member"][:, k])}
            efim = set(H.wap_stats(m, r.rel_minutil_pct)) if r.n_huis else set()
            rows.append({"model": m, "theta_pct": r.rel_minutil_pct,
                         "efim_n_huis": int(r.n_huis),
                         "efim_runtime_s": r.runtime_s,
                         "efim_nodes": int(r.search_nodes_visited),
                         "efim_union": len(efim), "search_union": len(got),
                         "identical": efim == got,
                         "search_level_seconds": round(float(T["level_seconds"][k]), 2),
                         "search_level_nodes": int(T["level_nodes"][k])})
    C = pd.DataFrame(rows)
    C.to_csv(H.OUT / "union_check.csv", index=False)
    print(C.to_string(index=False))
    assert C.identical.all(), C[~C.identical]
    print("ALL", len(C), "COMPLETED EFIM RUNS REPRODUCED EXACTLY")


if __name__ == "__main__":
    main()
