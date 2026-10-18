"""Shared helpers: paths, logging, environment capture, JSON-safe serialisation."""
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# The two raw CSVs are never written to. inspect_data.py verifies they exist and
# records their SHA-256 so later phases can prove they were not edited.
DATA_CANDIDATE_DIRS = [
    PROJECT_ROOT,
    PROJECT_ROOT / "ujiindoorloc" / "UJIndoorLoc",
    PROJECT_ROOT / "ujiindoorloc",
    PROJECT_ROOT / "UJIndoorLoc",
]

RESULTS = PROJECT_ROOT / "results"
METRICS = RESULTS / "metrics"
TABLES = RESULTS / "tables"
HUI_DIR = RESULTS / "hui"
LOGS = RESULTS / "logs"
FIGURES = PROJECT_ROOT / "figures"
DATA_PROCESSED = PROJECT_ROOT / "data_processed"
RESEARCH = PROJECT_ROOT / "research"
REPORT = PROJECT_ROOT / "report"
SLIDES = PROJECT_ROOT / "slides"

for _d in (RESULTS, METRICS, TABLES, HUI_DIR, LOGS, FIGURES, DATA_PROCESSED,
           RESEARCH, REPORT, SLIDES):
    _d.mkdir(parents=True, exist_ok=True)


def find_dataset() -> dict:
    """Locate trainingData.csv / validationData.csv without modifying them."""
    found = {}
    for name in ("trainingData.csv", "validationData.csv"):
        for d in DATA_CANDIDATE_DIRS:
            p = d / name
            if p.is_file():
                found[name] = p
                break
    missing = [n for n in ("trainingData.csv", "validationData.csv") if n not in found]
    if missing:
        raise FileNotFoundError(
            f"Could not locate {missing}. Searched: {[str(d) for d in DATA_CANDIDATE_DIRS]}"
        )
    return found


def relocate(recorded: str | Path) -> Path:
    """Result files store absolute paths (e.g. huim_runs.csv -> path_wap_stats),
    which break as soon as the project folder is moved or cloned elsewhere:
    the committed CSV still says D:\\ips\\results\\hui\\... . Anything under a
    'results' folder is re-anchored onto this checkout."""
    from pathlib import PurePosixPath, PureWindowsPath
    p = Path(recorded)
    if p.exists():
        return p
    s = str(recorded)
    parts = PureWindowsPath(s).parts if "\\" in s else PurePosixPath(s).parts
    if "results" in parts:
        i = len(parts) - 1 - parts[::-1].index("results")
        cand = PROJECT_ROOT.joinpath(*parts[i:])
        if cand.exists():
            return cand
    return p


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def get_logger(name: str, logfile: str | None = None) -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    if logfile:
        fh = logging.FileHandler(LOGS / logfile, mode="a", encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)
    log.propagate = False
    return log


class JSONSafe(json.JSONEncoder):
    """numpy / Path aware encoder so audit dumps never silently drop a field."""

    def default(self, o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            v = float(o)
            return v if np.isfinite(v) else None
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def dump_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, cls=JSONSafe)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def environment_info() -> dict:
    """Everything needed to state 'these numbers came from this machine'."""
    import importlib

    pkgs = {}
    for mod in ("numpy", "pandas", "sklearn", "scipy", "matplotlib",
                "docx", "pptx", "psutil", "yaml"):
        try:
            m = importlib.import_module(mod)
            pkgs[mod] = getattr(m, "__version__", "unknown")
        except Exception:
            pkgs[mod] = "not installed"

    info = {
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count_logical": os.cpu_count(),
        "packages": pkgs,
    }
    try:
        import psutil
        info["ram_total_gb"] = round(psutil.virtual_memory().total / 1024 ** 3, 2)
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
    except Exception:
        info["ram_total_gb"] = None
        info["cpu_count_physical"] = None

    if platform.system() == "Windows":
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor).Name"],
                capture_output=True, text=True, timeout=30)
            if out.returncode == 0 and out.stdout.strip():
                info["cpu_model"] = out.stdout.strip().splitlines()[0].strip()
        except Exception:
            pass
    return info


class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.seconds = time.perf_counter() - self.t0


class MemoryMonitor:
    """Peak process RSS during a block, sampled from a background thread.

    Why RSS sampling rather than `tracemalloc`: tracemalloc instruments every
    allocation and inflates runtime by a large factor, which would corrupt the
    runtime measurements that the same experiment has to report. A 20 ms RSS
    sampler costs essentially nothing. Both the absolute peak and the delta over
    the pre-run baseline are recorded; the delta is the algorithm's own
    footprint, the absolute figure includes the interpreter and the loaded
    dataframes.
    """

    def __init__(self, interval: float = 0.02) -> None:
        self.interval = interval
        self.baseline_mb = 0.0
        self.peak_mb = 0.0
        self._stop = None
        self._thread = None

    def __enter__(self):
        import threading
        import psutil
        self._proc = psutil.Process()
        self.baseline_mb = self._proc.memory_info().rss / 1024 ** 2
        self.peak_mb = self.baseline_mb
        self._stop = threading.Event()

        def _run():
            while not self._stop.wait(self.interval):
                try:
                    v = self._proc.memory_info().rss / 1024 ** 2
                except Exception:
                    return
                if v > self.peak_mb:
                    self.peak_mb = v

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *a):
        if self._stop is not None:
            self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        try:
            v = self._proc.memory_info().rss / 1024 ** 2
            self.peak_mb = max(self.peak_mb, v)
        except Exception:
            pass

    @property
    def delta_mb(self) -> float:
        return max(0.0, self.peak_mb - self.baseline_mb)

    def as_dict(self) -> dict:
        return {"peak_rss_mb": round(self.peak_mb, 2),
                "baseline_rss_mb": round(self.baseline_mb, 2),
                "peak_delta_mb": round(self.delta_mb, 2),
                "method": "background RSS sampling @ %gms" % (self.interval * 1000)}
