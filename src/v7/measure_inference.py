"""Peak memory and time of the HUI-evidence stage at inference (separate process per mode, Windows peak working set).

    python src/v7/measure_inference.py v6      # V6: rank + rank-L3 + abs models
    python src/v7/measure_inference.py v7      # V7-C2: + rel + abs-L3 models and their blocks
Writes BAOCAO_V7/so_lieu/inference_cost_<mode>.json
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import KEY, OUT, compute, final_abs_model, load_final_base  # noqa: E402
from huim_research import expand_levels, load_model  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import inputs, q_matrix  # noqa: E402
from v7.common import PROJECT_ROOT  # noqa: E402
from v7.extra_models import BLOCKS, extra_block  # noqa: E402
from v7.final_models import final_path  # noqa: E402

N = 64


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def mem_mb() -> tuple[float, float]:
    k32, psapi = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("psapi", use_last_error=True)
    k32.GetCurrentProcess.restype = wt.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
    psapi.GetProcessMemoryInfo.restype = wt.BOOL
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise OSError(ctypes.get_last_error())
    return c.WorkingSetSize / 2**20, c.PeakWorkingSetSize / 2**20


def main(mode: str) -> None:
    b = load(KEY)
    gf = b.ground_factor
    te = b.tests["validationData"].iloc[:N]
    prep, prepA = inputs(b, "rank")[0], inputs(b, "abs")[0]
    q, qA = q_matrix(prep, te, "rank"), q_matrix(prepA, te, "abs")
    t0 = time.perf_counter()
    pos = load_final_base(gf)
    posL, _ = load_model(OUT / "model_L3.npz", gf)
    posL.cell_bf = pos.cell_bf
    posA = final_abs_model(b)
    extras = []
    if mode == "v7":
        for name in ("rel", "absL3"):
            kind, lv = BLOCKS[name]
            pe, _ = load_model(final_path(kind, lv), gf)
            extras.append((pe, expand_levels(q_matrix(inputs(b, kind)[0], te, kind), lv)))
    load_s = time.perf_counter() - t0
    after_load = mem_mb()
    t0 = time.perf_counter()
    f = compute(pos, posL, q, gf, posA, qA)
    for pe, qe in extras:
        extra_block(pe, qe, f["cand"], f["floor"])
    s = (time.perf_counter() - t0) / N
    cur, peak = mem_mb()
    out = {"mode": mode, "models_loaded": 3 + len(extras), "load_seconds": round(load_s, 1), "working_set_after_loading_MB": round(after_load[0]),
           "peak_working_set_MB": round(peak), "evidence_seconds_per_query_on_64_queries": round(s, 4),
           "note": "64 queries only: fixed per-call costs are not amortised, so this is NOT comparable with the 1111-query timing in test_summary.json; use it for memory"}
    json.dump(out, open(PROJECT_ROOT / "BAOCAO_V7" / "so_lieu" / f"inference_cost_{mode}.json", "w"), indent=1)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
