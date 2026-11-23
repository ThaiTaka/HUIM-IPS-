"""Mine the full-training-data HUI models that V6/V7 need at test time (idempotent).

    python src/v7/final_models.py abs        # V6 absolute-strength model  (cache: v5/model_abs.npz)
    python src/v7/final_models.py L3         # V6 level-item model         (cache: v5/model_L3.npz)
    python src/v7/final_models.py KIND LEVELS   # V7 extra models, e.g. `rel 1`, `abs 3` (cache: v7/models/<kind>_L<levels>.npz)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_positioning import HUIPositioner  # noqa: E402
from huim_rerank_final import KEY, OUT, final_abs_model  # noqa: E402
from huim_research import THETA, expand_levels, save_model  # noqa: E402
from multi_datasets import load  # noqa: E402
from run_huim_only import inputs  # noqa: E402
from v7.common import OUT as V7OUT  # noqa: E402


def mine_final(b, kind: str, levels: int, f: Path) -> None:
    if f.exists():
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    _p, Q, cell, XY, BF = inputs(b, kind)
    t0 = time.perf_counter()
    pos = HUIPositioner(THETA, ground_factor=b.ground_factor).fit(expand_levels(Q, levels), cell, XY, BF)
    save_model(pos, f)
    print(f"final {kind} L{levels} model: {len(pos.hui_items)} HUIs, {time.perf_counter() - t0:.0f}s", flush=True)


def final_path(kind: str, levels: int) -> Path:
    return V7OUT / "models" / f"{kind}_L{levels}.npz"


if __name__ == "__main__":
    b = load(KEY)
    if sys.argv[1:] == ["abs"]:
        final_abs_model(b)
    elif sys.argv[1:] == ["L3"]:
        mine_final(b, "rank", 3, OUT / "model_L3.npz")
    else:
        kind, levels = sys.argv[1], int(sys.argv[2])
        mine_final(b, kind, levels, final_path(kind, levels))
