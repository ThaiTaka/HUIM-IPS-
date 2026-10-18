# HUIM applied to Wi-Fi fingerprint Indoor Positioning (UJIIndoorLoc)

High Utility Itemset Mining (**EFIM**) used as an **access-point selection**
mechanism for Wi-Fi fingerprint indoor localisation, evaluated against controls
on **UJIIndoorLoc**.

Written for: the person running this project and a reviewer checking its claims.

> **Final deliverables are in `BAOCAO/`** (read `BAOCAO/00_HUONG_DAN_DOC.md` first):
> the Word report, the slide deck, the model diagrams (`diagram/`), the numbers and
> the Excel / Python kits that recompute every mean error (`so_lieu/`), and the source
> code (`ma_nguon/`). The final system is the HUIM-only positioner (§10, no k-NN);
> `src/baocao/` rebuilds the folder. The older `report/`, `slides/` and `verification/`
> outputs mentioned below were removed; their build scripts still write there if rerun.

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
| `audit`, `coordinates`, `audit_md` | PHASE A — read-only inspection of both CSVs; coordinate system of LONGITUDE/LATITUDE | `results/data_summary.json`, `results/coordinate_system_verification.json`, `results/data_audit.md` |
| `literature*` | PHASE B — DOI verification via Crossref, papers table, review (needs network) | `research/doi_verification.json`, `research/papers_table.csv`, `research/references.bib`, `research/literature_review.md` |
| `tests` | PHASE F — unit tests, EFIM vs brute-force oracle | console + `results/logs/` |
| `pilot` | PHASE G — small-sample calibration of the minUtil grid | `results/metrics/pilot_runs.csv` |
| `huim` | PHASE H — full HUIM experiment | `results/metrics/huim_runs.csv`, `results/hui/*` |
| `refine` | PHASE H2 — adaptive refinement of the grid | appends to `huim_runs.csv`, `results/huim_refinement.json` |
| `ips` | PHASE I — positioning evaluation, all conditions | `results/metrics/ips_results.csv`, `results/ips_summary.json` |
| `ips_cost` | PHASE I — time and memory of the positioning system | `results/metrics/ips_cost.csv`, `results/ips_cost_summary.json` |
| `positioning` | PHASE I3 — positioning error in metres, optimised on leave-users-out folds of trainingData (≈ 22 min) | `results/positioning_optimisation.json`, `results/metrics/positioning_*.csv`, `results/predictions/`, `figures/fig18_*` |
| `verify_huim`, `verify_positioning` | PHASE V — independent re-computation of every HUI and of every positioning number | `results/verification/*.json`, `*.csv` |
| `reverse` | PHASE K — reverse-thinking analysis | `research/reverse_thinking_analysis.md`, `results/reverse_thinking_observations.json` |
| `figures`, `diagrams` | PHASE J — charts and schematics | `figures/*.png` + a matching `*.csv` per chart |
| `ablation` | PHASE J — ablation table | `results/tables/ablation_study.csv` / `.md` |
| `report` | PHASE L — Word report | `report/HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx` |
| `slides` | PHASE M — deck + speaker notes | `slides/HUIM_IPS_UJIIndoorLoc_Presentation.pptx`, `slides/speaker_notes.md` |
| `abc_slides` | PHASE M — refresh the two charts of the 4-slide Model A/B/C deck, labelled with minUtil | `slides/HUIM_ModelABC_4slides.pptx` |
| `kit` | PHASE V — Excel workbook that recomputes every key number with formulas | `verification/kiem_chung_thu_cong.xlsx` |
| `summary` | PHASE N — final summary and deliverable verification | `FINAL_SUMMARY.md`, `results/deliverables.csv`, `results/verification.json` |
| `code_guide` | PHASE N — Vietnamese guide to every Python file (purpose, principle, input, output) | `report/HUIM_IPS_Mo_ta_cac_file_Python.docx` |

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

### Checking the reported numbers yourself

Three layers, none of which trusts the experiment code:

```bash
python src/verify_huim.py                   # every HUI recomputed from the raw CSV
python src/verify_positioning.py            # accuracies and metres, csv + math only
python src/verify_positioning.py --brute 25 # nearest neighbours searched again
python src/verify_positioning.py --row 854  # one validation row, step by step
```

- `verify_huim.py` re-implements q(i,T), p(i) and u(X) from their definitions
  and, for the three runs the charts use, checks the threshold arithmetic,
  every reported HUI (utility, support, u(X) ≥ minUtil) and — by exhaustive
  enumeration of every 1-, 2- and 3-WAP itemset — that EFIM missed nothing.
- `verify_positioning.py` uses only the standard library to recount building,
  floor and joint accuracy and recompute every error in metres from the
  per-row prediction files in `results/predictions/`.
- `verification/kiem_chung_thu_cong.xlsx` does the same with Excel formulas
  (blue = input copied from a file, black = formula, green = check cell).

Every HUIM bar or point on a chart carries its minUtil threshold; the figure's
CSV adds the absolute value (minUtil% × total database utility).

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
    verify_coordinates.py   PHASE A  coordinate system (Web Mercator) of the columns
    pilot.py                PHASE G
    run_huim.py             PHASE H
    run_huim_refine.py      PHASE H2 adaptive grid refinement
    run_ips.py              PHASE I
    run_ips_cost.py         PHASE I  time and memory of the positioning system
    optimize_positioning.py PHASE I3 positioning error optimisation (metres)
    verify_huim.py          PHASE V  every HUI recomputed from the raw CSV
    verify_positioning.py   PHASE V  accuracies / metres recomputed, stdlib only
    make_verification_kit.py PHASE V Excel workbook for checking by hand
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
    update_modelabc_slides.py PHASE M charts of the 4-slide Model A/B/C deck
    make_prep_slides.py     preprocessing deck (stand-alone, numbers typed in)
    make_final_summary.py   PHASE N  FINAL_SUMMARY.md + verification
    make_code_guide.py      PHASE N  Word guide to every Python file
    check_glyphs.py         glyphs Times New Roman cannot render

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
    metrics/                huim_runs.csv, ips_results.csv, pilot_runs.csv,
                            ips_cost.csv, positioning_*.csv
    hui/                    per-run HUI sets (full when small) and per-WAP evidence
    predictions/            one row per validation fingerprint, both models
    verification/           results of verify_huim.py / verify_positioning.py
    tables/                 ablation_study.csv / .md
    logs/                   every run's stdout and structured log
    deliverables.csv, verification.json
figures/                    *.png, each with the *.csv it was plotted from
BAOCAO/                     final report, slides, diagrams, numbers, source code
src/baocao/                 the scripts that build BAOCAO/
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
- **The coordinate system is not documented by the dataset.** Neither the UCI
  attribute description nor the authors' page states one for
  `LONGITUDE`/`LATITUDE`; `src/verify_coordinates.py` identifies it as
  EPSG:3857 Web Mercator, so positioning error is reported both in projected
  metres (the literature's convention) and in ground metres (× cos latitude).
- **The study's k-NN (k = 1) was tuned for floor classification, not for
  coordinates.** PHASE I3 (`src/optimize_positioning.py`) optimises the metre
  error separately, on leave-users-out folds of trainingData; the HUIM-versus-
  control comparisons keep the frozen k-NN.
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

---

## 8. The same study on other datasets (PHASE X)

`dataset-20261013T020803Z-1-001/dataset/` holds further Wi-Fi fingerprint
datasets. `src/run_multi_dataset.py` re-runs the study on each of them with
**only the data changed**: it calls the study's own modules (EFIM, utility
Models A/B/C, the PHASE H grid and H2 refinement rules, PHASE I's frozen k-NN
and controls, PHASE I3's `select_on_dev`) with their own constants.

```bash
python src/run_multi_dataset.py --dataset all          # hours; or one key:
python src/run_multi_dataset.py --dataset dlulib --stage all
python src/run_multi_dataset.py --dataset hcxy --stage timing   # machine idle!
python src/make_multi_dataset_summary.py   # comparison.csv, fig40-42, TONG_HOP_DA_DATASET.md
python src/make_multi_dataset_kit.py       # verification/kiem_chung_da_dataset.xlsx
```

What has to be decided per dataset is decided in `src/multi_datasets.py` and
recorded in `results/multi_dataset/<key>/dataset_summary.json`:

| Key | Data | Location label (Model B/C, PHASE I k-NN) | PHASE I3 dev folds grouped by |
|---|---|---|---|
| `uji` | UJIIndoorLoc, byte-identical to the study's copy; mining reused | BUILDINGID_FLOOR | USERID (as the study) |
| `uji_lib3` | UJI library floor 3, Test-01 (training positions) and Test-02 (other positions) | reference point | Month |
| `dlulib` | DLULIB, 3 floors stacked (the 17 AP columns are the same APs on every floor) | BUILDINGID_FLOOR | SampleTimes |
| `hcxy` | HCXY, test RPs disjoint from training RPs | reference point | RP |
| `hus` | HUS as provided | reference point | none (shuffled KFold) |
| `hus_dedup` | HUS with the test cases' copies removed from training | reference point | none (shuffled KFold) |

- A single-floor dataset has one BUILDINGID_FLOOR class, so I(A;Y) = 0 for every
  AP and Model B cannot be built; the reference point replaces the floor as the
  label there. Building / floor accuracy is reported only where more than one
  class exists.
- DLULIB writes -100 for "not detected"; it is mapped to the study's 100.
- The `UJI_LIB` workbooks end with summary rows that have no position; they are
  dropped and listed in `dataset_summary.json`.
- **HUS: 204/205 rows of testcase1 and 205/205 of testcase2 are exact copies of
  rows of `hus_trainall.txt`.** `hus` shows what that does to the error;
  `hus_dedup` removes one training copy per test row and is the honest figure.
- The `syl`, `tuji` and `UJI_LIB_DB_Floor_5` folders are empty, inside the zip
  as well (a multi-part Google Drive export usually puts them in the other
  parts, `...-1-002.zip` etc.).
- `transfer` applies the configuration PHASE I3 selected on UJIIndoorLoc
  unchanged; `positioning` re-runs the selection on the dataset itself.
- `timing` measures wall-clock (median of 3 after a warm-up, at most 1,111
  rows of the primary test set = the size of UJIIndoorLoc validationData,
  `n_jobs=-1`); run it alone. EFIM runtimes were measured with other jobs on
  the machine and are comparable within a dataset, less so across datasets.

---

## 9. Zone-wise HUIM: HUIM as the AP selector of the positioning system (PHASE Z)

PHASE H mined one database for the whole site; its largest complete AP set
(79–91 WAPs) gives 17–20 m on UJIIndoorLoc, so the 5.36 m of PHASE I3 came
from all 520 APs, not from HUIM. PHASE Z changes how HUIM is applied and keeps
the positioner fixed:

1. split the training fingerprints into zones — building-floor classes, or
   8 k-means clusters of the training positions on a single-floor site;
2. mine each zone with EFIM at minUtil_z = θ% of that zone's total utility
   (a zone that exceeds its budget is re-mined at θ × 1.25 until complete);
3. the positioning features are the union of the WAPs occurring in the zones'
   HUIs — the positioner never sees any other column;
4. utility model (A or B) and θ ∈ {10, 7, 5, 4, 3}% are chosen on the dev
   folds of the training data; each test set is scored once.

```bash
python src/run_huim_zone.py --dataset all     # mine, select on dev, evaluate
python src/verify_huim_zone.py                # independent re-computation
python src/plots_huim_zone.py                 # figures/huim_zone/fig50-55 (+ CSV)
python src/make_huim_zone_report.py           # report/Bao_Cao_HUIM_IPS_Theo_Vung.docx
```

Outputs per dataset in `results/huim_zone/<key>/`: `zone_mining.csv`,
`hui/<set>.json` (per zone: minUtil, selected WAPs, one witness HUI per WAP),
`ap_sets.json`, `dev_selection.csv`, `selection.json`, `test_results.csv`
(every AP set, the all-AP baseline and matched-budget controls),
`predictions/`, `selected.json`. The headline numbers are in the report and in
`results/huim_zone/<key>/selected.json`.

---

## 10. Positioning by HUIM alone, no k-NN (PHASE Q)

In PHASE Z the positioner is still k-NN; HUIM only selects its columns. PHASE Q
removes k-NN: the positioning model *is* the HUI sets.

1. every training reference point is a cell; EFIM mines each cell's
   transactions at minUtil = θ% of the cell's utility (`src/huim_positioning.py`);
2. a query fingerprint is a transaction; each cell is scored by how much of its
   HUI utility the query contains (soft containment, signal agreement) and how
   much of the query its HUIs explain; scores are smoothed over same-floor
   neighbouring cells;
3. the floor whose best cells score highest is chosen, and the position is the
   score-weighted centroid of the best cells of that floor.

No training fingerprint is compared with a query. Internal utility (abs / rel /
rank), θ and the scoring parameters are chosen on dev folds of the training
data; UJIIndoorLoc's dev folds hold out phones, because 9 of the 11
validationData phones are unseen in training. Every version tried on
UJIIndoorLoc is listed in `results/huim_only/uji/version_history.json`.

```bash
python src/run_huim_only.py --dataset all     # select on dev, final model, test once
python src/verify_huim_only.py                # independent re-computation
python src/plots_huim_only.py                 # figures/huim_only/fig60-63 (+ CSV)
python src/make_huim_only_report.py           # report/Bao_Cao_HUIM_IPS_Dinh_Vi_Chi_Bang_HUIM.docx
```
