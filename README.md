# HUIM applied to Wi-Fi fingerprint Indoor Positioning (UJIIndoorLoc)

High Utility Itemset Mining (**EFIM**) used as an **access-point selection**
mechanism for Wi-Fi fingerprint indoor localisation, evaluated against controls
on **UJIIndoorLoc**.

Written for: the person running this project and a reviewer checking its claims.

---

## What this is, and what it is not

**It is** an adaptation study. The HUIM formalism and the EFIM algorithm come
from the literature; the mapping of a Wi-Fi fingerprint onto a utility
transaction, and the three utility definitions, are this project's own design.

**It is not** a claim that HUIM is a standard or superior method for indoor
positioning. The literature review (`research/literature_review.md` §7) found no
work applying HUIM to UJIIndoorLoc or to Wi-Fi fingerprinting, so the mapping is
a **proposed model**, not an established one. No novelty priority is asserted
anywhere. Access-point selection itself, including by information-theoretic
criteria, is established prior art (Chen et al., *IEEE TKDE* 18:877–888, 2006).

Every number in the Word report, the slide deck and `FINAL_SUMMARY.md` is read
from `results/` at build time. The document builders contain no experimental
values: if a result file is missing, the build fails rather than emitting prose
with holes in it.

---

## 0. Scope, and credit for the data

**Scope.** This is a *study assignment* (bài tìm hiểu) for a master's course —
understand the algorithm, model its application to indoor positioning, implement
it and evaluate it on UJIIndoorLoc. It is **not** a thesis or a capstone
project, and nothing here claims novelty.

**Dataset.** `ujiindoorloc/UJIndoorLoc/` holds the UJIIndoorLoc database,
redistributed here unmodified so the pipeline runs from a single clone. It is
not this repository's work. Please cite the authors:

> J. Torres-Sospedra, R. Montoliu, A. Martínez-Usó, J. P. Avariento,
> T. J. Arnau, M. Benedito-Bordonau and J. Huerta, "UJIIndoorLoc: A new
> multi-building and multi-floor database for WLAN fingerprint-based indoor
> localization problems," *2014 International Conference on Indoor Positioning
> and Indoor Navigation (IPIN)*, pp. 261–270.
> DOI: [10.1109/IPIN.2014.7275492](https://doi.org/10.1109/IPIN.2014.7275492)

Both CSVs are byte-identical to the originals; `results/data_summary.json`
records their SHA-256 digests, and `.gitattributes` disables line-ending
conversion so a clone preserves them exactly.

---

## 1. Setup

```bash
python -m pip install -r requirements.txt
```

Python 3.12 is what the reported results were produced with. The dataset is
expected at `ujiindoorloc/UJIndoorLoc/trainingData.csv` and
`validationData.csv`; `src/utils.py::find_dataset` also looks in the project
root and a few other obvious places. **Neither CSV is ever written to** — their
SHA-256 digests are recorded in `results/data_summary.json` so that can be
checked.

No JVM is required. SPMF would have been the preferred reference implementation
for EFIM, but it is a Java library and no JVM was available in the environment
these results were produced in; EFIM is therefore re-implemented in Python and
validated against a brute-force oracle (see §3).

---

## 2. Run everything

```bash
python run_experiments.py
```

That executes the phases in the order the study requires. Individual phases:

```bash
python run_experiments.py --list          # show every phase
python run_experiments.py --only tests    # just one phase
python run_experiments.py --from huim     # resume from PHASE H
python run_experiments.py --offline       # skip the two phases that need network
```

| Phase | What it does | Writes |
|---|---|---|
| `audit`, `audit_md` | PHASE A — read-only inspection of both CSVs | `results/data_summary.json`, `results/data_audit.md` |
| `literature*` | PHASE B — DOI verification via Crossref, papers table, review (needs network) | `research/doi_verification.json`, `research/papers_table.csv`, `research/references.bib`, `research/literature_review.md` |
| `tests` | PHASE F — unit tests, EFIM vs brute-force oracle | console + `results/logs/` |
| `pilot` | PHASE G — small-sample calibration of the minUtil grid | `results/metrics/pilot_runs.csv` |
| `huim` | PHASE H — full HUIM experiment | `results/metrics/huim_runs.csv`, `results/hui/*` |
| `refine` | PHASE H2 — adaptive refinement of the grid | appends to `huim_runs.csv`, `results/huim_refinement.json` |
| `ips` | PHASE I — positioning evaluation, all conditions | `results/metrics/ips_results.csv`, `results/ips_summary.json` |
| `reverse` | PHASE K — reverse-thinking analysis | `research/reverse_thinking_analysis.md`, `results/reverse_thinking_observations.json` |
| `figures`, `diagrams` | PHASE J — charts and schematics | `figures/*.png` + a matching `*.csv` per chart |
| `ablation` | PHASE J — ablation table | `results/tables/ablation_study.csv` / `.md` |
| `report` | PHASE L — Word report | `report/HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx` |
| `slides` | PHASE M — deck + speaker notes | `slides/HUIM_IPS_UJIIndoorLoc_Presentation.pptx`, `slides/speaker_notes.md` |
| `summary` | PHASE N — final summary and deliverable verification | `FINAL_SUMMARY.md`, `results/deliverables.csv`, `results/verification.json` |

### Step by step

```bash
# 2. data audit
python src/inspect_data.py && python src/make_audit_report.py

# 3. correctness tests  (MUST pass before anything touches UJIIndoorLoc)
python -m pytest tests -q

# 4. preprocessing is exercised by the pilot and by the tests
python src/pilot.py

# 5. HUIM
python src/run_huim.py
python src/run_huim_refine.py

# 6. IPS
python src/run_ips.py

# 7. charts
python src/plots.py && python src/make_diagrams.py

# 8. report
python src/make_reverse_analysis.py && python src/make_ablation.py
python src/build_report.py

# 9. slides
python src/make_slides.py

# 10. final summary + verification
python src/make_final_summary.py
```

On Windows, set `PYTHONIOENCODING=utf-8` if your console mangles Vietnamese
output; `run_experiments.py` already sets it for every child process.

---

## 3. How the EFIM implementation is trusted

`src/huim/brute_force.py` is an **oracle**: it enumerates every non-empty
subset and computes `u(X)` straight from the definition, with no pruning and no
clever data structures. It shares no code path with EFIM beyond the database
format, so agreement between the two is meaningful.

`tests/test_efim.py` compares them on

- the running example used throughout the HUIM literature, at 16 thresholds;
- 40 independent random utility databases × 5 thresholds each;
- 15 sparse-and-wide databases shaped like Wi-Fi data;
- float external utilities (Model B's `p` is not integral);

plus two utilities **computed by hand in the test file** (`u({b,d}) = 30`,
`u({b,c,d,e}) = 40`), which covers the case where both implementations are wrong
in the same way. It also asserts the theory: TWU is an upper bound (checked
exhaustively), utility is *not* anti-monotone (explicit counter-example),
support survives transaction merging exactly, pruning actually fires, and the
controlled-abort paths work.

`tests/test_utility.py` checks the preprocessing semantics (sentinel handling,
positivity, monotonicity), verifies the mutual-information estimator against
`sklearn.metrics.mutual_info_score` on 25 random inputs, and asserts the
**leakage gate** raises.

---

## 4. Leakage policy

`validationData` appears in exactly one place: the final evaluation, once per
condition.

| Step | Data used |
|---|---|
| RSSI normalisation bounds | trainingData |
| External utilities `p(i)` (mutual information) | trainingData |
| HUIM mining | trainingData |
| AP selection from the HUIs | trainingData |
| k-NN hyper-parameters | `train_sub` / `dev_sub`, both split from trainingData |
| Final classifier fit | full trainingData |
| **Evaluation** | **validationData, once per condition** |

This is enforced in code, not promised in prose: `build_external_utility` takes
a required `split_name` and raises unless it is `"training"`.

The k-NN configuration (k, metric, weights) is selected **once**, on the ALL-WAP
feature set, and then frozen for every condition. So the only thing that differs
between "All-WAP" and "HUIM-selected" is which columns are present. Tuning on
the baseline also means any benefit of tuning accrues to the baseline.

---

## 5. Layout

```
trainingData.csv / validationData.csv   under ujiindoorloc/UJIndoorLoc/ (read-only)

src/
    utils.py                paths, logging, environment capture, memory monitor
    inspect_data.py         PHASE A  data audit
    make_audit_report.py    PHASE A  renders results/data_audit.md from the JSON
    preprocess_uji.py       fingerprint -> features and -> utility transactions
    utility_models.py       Models A / B / C, mutual information, leakage gate
    huim/
        efim.py             EFIM: local & subtree utility, projection, merging, FUC
        brute_force.py      the oracle: raw definition, no pruning
    feature_selection.py    HUI set -> ranked AP set
    ips_model.py            k-NN protocol, metrics, positioning error
    pilot.py                PHASE G
    run_huim.py             PHASE H
    run_huim_refine.py      PHASE H2 adaptive grid refinement
    run_ips.py              PHASE I
    make_reverse_analysis.py PHASE K
    plots.py                PHASE J charts
    make_diagrams.py        PHASE J schematics (drawn, not copied)
    make_ablation.py        PHASE J ablation table
    report_builder.py       python-docx wrapper, Times New Roman, placeholder guard
    make_report.py          cover + ch1-3        (+ Ctx: loads every result file)
    report_parts2.py        ch4-ch8
    report_parts3.py        ch9-ch11
    report_parts4.py        ch12-ch14, ch16, references
    report_parts5.py        ch15, ch17-18, appendix cheat sheet
    build_report.py         PHASE L  assembles the DOCX
    make_slides.py          PHASE M  PPTX + speaker notes
    make_final_summary.py   PHASE N  FINAL_SUMMARY.md + verification

tests/                      test_efim.py, test_utility.py, conftest.py
configs/experiment.yaml     every knob in one place
research/                   literature review, verified DOIs, papers table, bibtex,
                            reverse-thinking analysis
results/
    data_summary.json       everything the audit measured
    data_audit.md           rendered from that JSON
    huim_summary.json       mining run, utility-model diagnostics
    ips_summary.json        protocol, frozen config, grid-search trace, per-condition
    reverse_thinking_observations.json
    metrics/                huim_runs.csv, ips_results.csv, pilot_runs.csv
    hui/                    per-run HUI sets (full when small) and per-WAP evidence
    tables/                 ablation_study.csv / .md
    logs/                   every run's stdout and structured log
    deliverables.csv, verification.json
figures/                    *.png, each with the *.csv it was plotted from
report/                     the DOCX
slides/                     the PPTX and speaker_notes.md
run_experiments.py          the whole pipeline
```

---

## 6. Reproducibility notes

- **Random seed** 20251007, used for the train_sub/dev_sub split, the random
  controls and Random Forest.
- **Environment** is captured automatically into every result file
  (`results/*.json` → `environment`): OS, CPU model, core counts, RAM, Python
  and package versions.
- **Memory** is measured by sampling process RSS every 20 ms, not with
  `tracemalloc`: tracemalloc instruments every allocation and would corrupt the
  runtime numbers the same experiment has to report. Both the absolute peak and
  the delta over the pre-run baseline are recorded.
- **minUtil is always relative** — a percentage of total database utility —
  because total utility differs several-fold between the three utility models
  even though the database and the internal utilities are identical.
- **Controlled aborts are kept.** A run exceeding its budget (600 s or 1,000,000
  itemsets) stops and is recorded with `STATUS = ABORTED_RESOURCE_LIMIT`.
  Partial results are retained, never deleted. Because a truncated HUI list is
  biased by depth-first search order, aborted runs are used for the mining
  performance analysis but **never** to rank APs, and they are flagged in every
  table.
- **Every chart writes its data.** `figures/<name>.png` always has a
  `figures/<name>.csv` holding exactly the rows plotted (schematics in
  `fig2x_*` are drawn rather than plotted, so they have no CSV).

---

## 7. Known limitations, stated up front

- The utility mapping is a **design decision**. `q` and `p` do not exist in
  Wi-Fi data; a different definition yields different HUIs and a different AP
  set. "The high utility itemsets of UJIIndoorLoc" is not a well-defined object.
- HUIM is **not a supervised feature selector**. Nothing in its definition
  optimises a classification objective, so whether a HUI is a good feature group
  is purely empirical — which is why the matched-budget controls exist.
- **Positioning error is reported in dataset coordinate units, never in
  metres.** Neither the UCI attribute description nor the dataset authors' own
  page states a coordinate system or unit for `LONGITUDE`/`LATITUDE`.
- **No Q1/Q2 label is attached to any reference.** Conference papers have no
  SJR/JCR quartile at all, and for the journal articles `scimagojr.com` returned
  HTTP 403 from this environment (journal pages, ISSN search and the bulk CSV
  export alike). "IEEE = Q1" is a category error: IEEE is a publisher.
- `SPACEID` is identically 0 in `validationData`, so no room-level metric is
  reported. Evaluation is at building and floor level only.
- The two splits share **no** user and only two device ids, and were collected
  about four months apart, so all accuracies here are cross-device, cross-time
  numbers and are not comparable with work that re-splits the training file
  randomly.

`results/data_audit.md`, `research/literature_review.md`,
`research/reverse_thinking_analysis.md` and `FINAL_SUMMARY.md` carry the full
versions of these, with the measurements behind them.
