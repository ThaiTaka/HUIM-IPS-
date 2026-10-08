"""Reproduce the entire study.

    python run_experiments.py                 # everything, in order
    python run_experiments.py --from huim     # resume from a phase
    python run_experiments.py --only ips      # one phase
    python run_experiments.py --list          # show the phases
    python run_experiments.py --skip-tests    # not recommended

Phases run in the order mandated by the project brief:

    audit       PHASE A   read-only inspection of the two CSVs
    literature  PHASE B   DOI verification + literature review (needs network)
    tests       PHASE F   unit tests; EFIM vs brute-force oracle
    pilot       PHASE G   small-sample calibration of the minUtil grid
    huim        PHASE H   full HUIM experiment
    refine      PHASE H2  adaptive refinement of the grid
    ips         PHASE I   indoor positioning evaluation
    figures     PHASE J   charts + schematics
    ablation    PHASE J   ablation table
    reverse     PHASE K   reverse-thinking analysis
    report      PHASE L   Word report
    slides      PHASE M   PowerPoint + speaker notes
    summary     PHASE N   FINAL_SUMMARY.md + deliverable verification

Nothing downstream of `huim` invents numbers: each phase reads the files the
previous one wrote, so a phase that has not run yet makes the next one fail
loudly rather than produce prose with holes in it.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

PHASES = [
    ("audit", "PHASE A  data audit", [sys.executable, "src/inspect_data.py"]),
    ("audit_md", "PHASE A  render data_audit.md",
     [sys.executable, "src/make_audit_report.py"]),
    ("literature", "PHASE B  DOI verification (network)",
     [sys.executable, "research/verify_dois.py"]),
    ("literature_tbl", "PHASE B  papers table + bibtex (network)",
     [sys.executable, "research/build_literature.py"]),
    ("literature_md", "PHASE B  literature review",
     [sys.executable, "research/make_literature_review.py"]),
    ("tests", "PHASE F  unit tests (EFIM vs brute-force oracle)",
     [sys.executable, "-m", "pytest", "tests", "-q"]),
    ("pilot", "PHASE G  pilot calibration", [sys.executable, "src/pilot.py"]),
    ("huim", "PHASE H  full HUIM experiment",
     [sys.executable, "src/run_huim.py"]),
    ("refine", "PHASE H2 adaptive grid refinement",
     [sys.executable, "src/run_huim_refine.py"]),
    ("ips", "PHASE I  IPS evaluation", [sys.executable, "src/run_ips.py"]),
    ("reverse", "PHASE K  reverse-thinking analysis",
     [sys.executable, "src/make_reverse_analysis.py"]),
    ("figures", "PHASE J  charts", [sys.executable, "src/plots.py"]),
    ("diagrams", "PHASE J  schematic diagrams",
     [sys.executable, "src/make_diagrams.py"]),
    ("ablation", "PHASE J  ablation table",
     [sys.executable, "src/make_ablation.py"]),
    ("report", "PHASE L  Word report", [sys.executable, "src/build_report.py"]),
    ("slides", "PHASE M  PowerPoint + speaker notes",
     [sys.executable, "src/make_slides.py"]),
    ("summary", "PHASE N  FINAL_SUMMARY.md + verification",
     [sys.executable, "src/make_final_summary.py"]),
]

# Phases that need the internet. They are skipped (with a warning) rather than
# failing the run, because the verified outputs are already committed.
NETWORK_PHASES = {"literature", "literature_tbl"}


def run(name: str, label: str, cmd: list[str], allow_fail: bool) -> dict:
    print(f"\n{'=' * 78}\n>>> {label}\n    {' '.join(cmd)}\n{'=' * 78}",
          flush=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    el = time.perf_counter() - t0
    ok = r.returncode == 0
    print(f"<<< {label}: {'OK' if ok else 'FAILED'} (exit {r.returncode}) "
          f"in {el:.1f}s", flush=True)
    if not ok and not allow_fail:
        raise SystemExit(f"phase '{name}' failed with exit {r.returncode}; "
                         "fix the cause and re-run rather than skipping it")
    return {"phase": name, "label": label, "returncode": r.returncode,
            "seconds": round(el, 2)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", help="resume from this phase")
    ap.add_argument("--only", help="run just this phase")
    ap.add_argument("--list", action="store_true", help="list phases and exit")
    ap.add_argument("--skip-tests", action="store_true",
                    help="skip the correctness tests (not recommended)")
    ap.add_argument("--offline", action="store_true",
                    help="skip the phases that need network access")
    a = ap.parse_args()

    if a.list:
        for n, lab, cmd in PHASES:
            net = "  [network]" if n in NETWORK_PHASES else ""
            print(f"  {n:16s} {lab}{net}")
        return

    todo = PHASES
    if a.only:
        todo = [p for p in PHASES if p[0] == a.only]
        if not todo:
            raise SystemExit(f"unknown phase {a.only!r}; use --list")
    elif a.start:
        names = [p[0] for p in PHASES]
        if a.start not in names:
            raise SystemExit(f"unknown phase {a.start!r}; use --list")
        todo = PHASES[names.index(a.start):]
    if a.skip_tests:
        todo = [p for p in todo if p[0] != "tests"]
    if a.offline:
        todo = [p for p in todo if p[0] not in NETWORK_PHASES]

    results = []
    t0 = time.perf_counter()
    for name, label, cmd in todo:
        results.append(run(name, label, cmd,
                           allow_fail=name in NETWORK_PHASES))
    total = time.perf_counter() - t0

    print(f"\n{'=' * 78}\nPIPELINE SUMMARY ({total:.1f}s total)\n{'=' * 78}")
    for r in results:
        status = "OK    " if r["returncode"] == 0 else "FAILED"
        print(f"  {status} {r['phase']:16s} {r['seconds']:8.1f}s  {r['label']}")
    bad = [r for r in results if r["returncode"] != 0]
    if bad:
        print(f"\n{len(bad)} phase(s) did not succeed: "
              f"{', '.join(r['phase'] for r in bad)}")
        if all(r["phase"] in NETWORK_PHASES for r in bad):
            print("All of them are network phases; their verified outputs are "
                  "already on disk, so the rest of the pipeline is unaffected.")
    else:
        print("\nAll phases succeeded.")


if __name__ == "__main__":
    main()
