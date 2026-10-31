"""Shared pieces of V7: cached dev features with provenance, V6 re-ranker reproduction, metrics.

The V6 modules (src/huim_rerank_final.py, src/huim_research.py, ...) are imported, never edited.
Everything V7 writes goes to results/huim_only/uji/v7/ ; every cache carries a sidecar
`<name>.meta.json` with the source-data digest, fold definition digest, code revision and config,
and `load_cache` refuses a cache whose metadata does not match.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
from utils import PROJECT_ROOT  # noqa: E402

GF = 0.766126                      # Web-Mercator -> ground metres (src/verify_coordinates.py)
UJI = PROJECT_ROOT / "results" / "huim_only" / "uji"
RES = UJI / "research"             # fold models (gitignored, rebuilt by huim_research.py)
OUT = UJI / "v7"
CACHE = OUT / "cache"
TRAIN_CSV = PROJECT_ROOT / "ujiindoorloc" / "UJIndoorLoc" / "trainingData.csv"
VALID_CSV = PROJECT_ROOT / "ujiindoorloc" / "UJIndoorLoc" / "validationData.csv"
SEED = 0


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def sha256_arrays(*arrs: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in arrs:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def git_rev() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def base_meta(**extra) -> dict:
    return {"train_csv_sha256": sha256_file(TRAIN_CSV), "git_rev": git_rev(), "seed": SEED, **extra}


def save_cache(name: str, meta: dict, **arrays) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{name}.npz"
    np.savez_compressed(p, **arrays)
    json.dump(meta, open(CACHE / f"{name}.meta.json", "w"), indent=1, sort_keys=True)
    return p


def load_cache(name: str, expect: dict | None = None) -> dict:
    """Load a cache; every key in `expect` must equal the stored metadata value."""
    p = CACHE / f"{name}.npz"
    m = json.load(open(CACHE / f"{name}.meta.json"))
    bad = {k: (m.get(k), v) for k, v in (expect or {}).items() if m.get(k) != v}
    if bad:
        raise RuntimeError(f"cache {name} does not match the requested configuration: {bad}")
    if m["train_csv_sha256"] != sha256_file(TRAIN_CSV):
        raise RuntimeError(f"cache {name} was built from a different trainingData.csv")
    return {k: v for k, v in np.load(p, allow_pickle=False).items()} | {"_meta": m}


def err_m(xy: np.ndarray, true: np.ndarray) -> np.ndarray:
    return np.sqrt(((xy - true) ** 2).sum(-1)) * GF


def stats(e: np.ndarray) -> dict:
    return {"mean": float(e.mean()), "median": float(np.median(e)), "p75": float(np.percentile(e, 75)),
            "p90": float(np.percentile(e, 90)), "p95": float(np.percentile(e, 95)), "n": int(len(e))}
