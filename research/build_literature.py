"""PHASE B - build research/papers_table.csv, research/references.bib and the
metadata block of research/literature_review.md from VERIFIED Crossref records
only. Nothing is typed by hand here except the 'role in this study' column and
the indexing/quartile evidence, and both of those record how they were checked.

Indexing is probed against DBLP (dblp.org), which is a real, queryable
bibliographic index for computer science. Scopus / Web of Science and the
SJR quartile tables are NOT reachable from this environment, so those cells say
so instead of guessing.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils import RESEARCH, dump_json

MAILTO = "research-script@example.invalid"

# key -> (expected title fragment, role in this study). The title fragment is an
# assertion: build fails loudly if Crossref returned a different paper, which is
# exactly how four of our first-guess DOIs were caught.
CURATED = {
    "torressospedra2014uji": (
        "UJIIndoorLoc", "Dataset of record: defines UJIIndoorLoc, its collection "
        "protocol, train/validation split and attribute semantics."),
    "torressospedra2015distance": (
        "Comprehensive analysis of distance and similarity",
        "Establishes that k-NN with a suitable distance/representation is a strong, "
        "standard baseline on UJIIndoorLoc; motivates our k-NN baseline choice."),
    "khalajmehrabadi2017modern": (
        "Modern WLAN Fingerprinting",
        "Survey framing offline/online phases, RSSI fingerprinting and the "
        "dimensionality/deployment problems that motivate AP selection."),
    "bahl2000radar": (
        "RADAR", "Origin of RF fingerprinting + nearest-neighbour matching in "
        "signal space; the conceptual ancestor of our baseline."),
    "youssef2005horus": (
        "Horus", "Probabilistic fingerprinting alternative; cited to show k-NN is "
        "one of several standard matchers, not the only one."),
    "kaemarungsi2004modeling": (
        "Modeling of indoor positioning systems based on location fingerprint",
        "Analyses RSSI fingerprint properties (variability, AP informativeness) "
        "that make some APs more useful than others."),
    "chen2006power": (
        "Power-efficient access-point selection",
        "Prior art for AP SELECTION in fingerprinting; shows information-theoretic "
        "AP subset selection predates this study - our contribution is not 'AP "
        "selection' but 'AP selection driven by HUIM'."),
    "ijgi2016": (
        "Best-Discriminating AP Selection",
        "Prior art: discriminative AP selection for fingerprint localization, the "
        "closest existing idea to our Model B external utility."),
    "adler2015survey": (
        "survey of experimental evaluation in indoor localization",
        "Evaluation-protocol discipline for IPS experiments (what must be reported)."),
    "jedari2015randomforest": (
        "random forest classifier",
        "Precedent for tree-ensemble classifiers on Wi-Fi fingerprints; justifies "
        "Random Forest as our secondary classifier."),
    "lohan2017data": (
        "Wi-Fi Crowdsourced Fingerprinting Dataset",
        "Shows RSSI representation choices (powed/exponential) matter; supports our "
        "explicit, documented RSSI-to-utility mapping."),
    "agrawal1993mining": (
        "association rules between sets of items",
        "Origin of itemset mining: items, itemsets, transactions, support."),
    "han2000fpgrowth": (
        "frequent patterns without candidate generation",
        "Pattern-growth paradigm; the ancestor of UP-Growth."),
    "yao2004foundational": (
        "Foundational Approach to Mining Itemset Utilities",
        "Formal foundation of utility mining: internal/external utility, and the "
        "fact that utility is neither monotone nor anti-monotone."),
    "liu2005twophase": (
        "Two-Phase Algorithm for Fast Discovery of High Utility",
        "Introduces TWU and the Two-Phase candidate-then-verify scheme; the "
        "upper-bound idea every later algorithm refines."),
    "tseng2010upgrowth": (
        "UP-Growth", "Pattern-growth HUIM with UP-Tree and DGU/DGN/DLU/DLN "
        "strategies; the 'phase 1 candidate reduction' line of work."),
    "tseng2013twophase": (
        "Efficient Algorithms for Mining High Utility Itemsets",
        "Journal version (UP-Growth+); authoritative statement of the "
        "candidate-generation bottleneck we cite."),
    "liu2012huiminer": (
        "Mining high utility itemsets without candidate generation",
        "HUI-Miner: utility-list structure, iutil/rutil, one-phase mining. The "
        "direct conceptual predecessor of EFIM."),
    "fournierviger2014fhm": (
        "FHM", "EUCP co-occurrence pruning; marks the incremental-improvement "
        "line that EFIM later outperforms."),
    "zida2017efim": (
        "EFIM", "PRIMARY ALGORITHM of this study. Defines local utility, subtree "
        "utility, high-utility database projection, transaction merging and Fast "
        "Utility Counting."),
    "zhang2018empirical": (
        "empirical evaluation of high utility itemset mining",
        "Independent third-party benchmark; the EVIDENCE BASE for choosing EFIM "
        "rather than our own preference."),
    "gan2021survey": (
        "Survey of Utility-Oriented Pattern Mining",
        "Mandated survey: taxonomy of utility-oriented mining, formal definitions, "
        "and the statement that utility mining extends beyond market-basket data."),
    "fournierviger2019survey": (
        "Survey of High Utility Itemset Mining",
        "Book-chapter survey used for definitions and for the application domains "
        "actually reported in the literature."),
    "fournierviger2016spmf": (
        "SPMF Open-Source Data Mining Library",
        "Reference implementation library for HUIM; cited as the de-facto standard "
        "whose EFIM semantics our Python implementation must match."),
}

# Journal-level ranking: only journals can carry an SJR quartile at all.
JOURNAL_RANKING_NOTE = (
    "Not verified - scimagojr.com returns HTTP 403 from this environment "
    "(checked 2026-10-07, both the journal page and the bulk CSV export), so no "
    "quartile is asserted here")
CONF_RANKING_NOTE = (
    "Not applicable - SJR/JCR quartiles rank journals, not conference proceedings")


def openalex_lookup(doi: str) -> dict:
    """Independent index check. DBLP refuses connections from this environment,
    so we use OpenAlex: an open bibliographic index that also exposes, per venue,
    whether it belongs to the curated CORE set and which services list it."""
    try:
        r = requests.get(f"https://api.openalex.org/works/doi:{doi}",
                         params={"mailto": MAILTO}, timeout=40,
                         headers={"User-Agent": f"HUIM-IPS-study (mailto:{MAILTO})"})
        if r.status_code != 200:
            return {"openalex_indexed": f"check failed (HTTP {r.status_code})"}
        w = r.json()
        src = (w.get("primary_location") or {}).get("source") or {}
        listed = src.get("listed_in") or []
        return {
            "openalex_indexed": "yes",
            "openalex_venue": src.get("display_name"),
            "openalex_venue_type": src.get("type"),
            "openalex_issn_l": src.get("issn_l"),
            "openalex_host_org": src.get("host_organization_name"),
            "openalex_is_core_venue": src.get("is_core"),
            "openalex_listed_in": ",".join(listed) if listed else "",
            "openalex_cited_by": w.get("cited_by_count"),
        }
    except Exception as e:
        return {"openalex_indexed": f"check failed ({type(e).__name__})"}


def bibtex(key: str, r: dict) -> str:
    authors = " and ".join(r["authors"]) if r["authors"] else "Unknown"
    typ = "article" if r["type"] == "journal-article" else (
        "inproceedings" if r["type"] == "proceedings-article" else "incollection")
    fields = [("author", authors),
              ("title", "{" + r["title"] + "}"),
              ("year", r["year_issued"])]
    if typ == "article":
        fields.append(("journal", r["container_title"]))
        if r["volume"]:
            fields.append(("volume", r["volume"]))
        if r["issue"]:
            fields.append(("number", r["issue"]))
    else:
        fields.append(("booktitle", r["container_title"]))
    if r["page"]:
        fields.append(("pages", r["page"].replace("-", "--")))
    fields += [("publisher", r["publisher"]), ("doi", r["doi"])]
    body = ",\n  ".join(f"{k} = {{{v}}}" for k, v in fields if v)
    return f"@{typ}{{{key},\n  {body}\n}}\n"


def main() -> None:
    v = {}
    for f in ("doi_verification.json", "doi_verification_extra.json"):
        p = RESEARCH / f
        if p.exists():
            v.update(json.load(open(p, encoding="utf-8")))
    # the four extras whose intended identity differed from the DOI we guessed
    alias = {"adler2015survey": "moreira2015wifi",
             "jedari2015randomforest": "jedari2015comparison",
             "lohan2017data": "lohan2017wlan"}
    for new, old in alias.items():
        if old in v:
            v[new] = v[old]

    rows, bib, failures = [], [], []
    for key, (frag, role) in CURATED.items():
        r = v.get(key)
        if not r or r.get("status") != "VERIFIED":
            failures.append((key, "not verified against Crossref"))
            continue
        if frag.lower() not in r["title"].lower():
            failures.append((key, f"TITLE MISMATCH: expected '{frag}' in "
                                  f"'{r['title']}'"))
            continue
        idx = openalex_lookup(r["doi"])
        time.sleep(0.3)
        is_journal = r["type"] == "journal-article"
        rows.append({
            "key": key,
            "paper": r["title"],
            "authors": "; ".join(r["authors"]),
            "year": r["year_issued"],
            "venue": r["container_title"],
            "venue_type": "Journal" if is_journal else (
                "Conference" if r["type"] == "proceedings-article" else
                "Book chapter / LNCS"),
            "publisher": r["publisher"],
            "doi": r["doi"],
            "volume": r["volume"] or "",
            "issue": r["issue"] or "",
            "pages": r["page"] or "",
            "metadata_source": "Crossref API (authoritative DOI registry)",
            "indexed_in_openalex": idx.get("openalex_indexed"),
            "openalex_venue_name": idx.get("openalex_venue") or "",
            "openalex_venue_is_core": idx.get("openalex_is_core_venue"),
            "openalex_listed_in": idx.get("openalex_listed_in") or "",
            "openalex_cited_by_count": idx.get("openalex_cited_by"),
            "indexing_scopus_wos_direct": "Not verified - no Scopus/WoS "
                                          "subscription access in this environment",
            "quartile": JOURNAL_RANKING_NOTE if is_journal else CONF_RANKING_NOTE,
            "quartile_year_source": "n/a - no quartile asserted",
            "crossref_citation_count": r["is_referenced_by_count"],
            "role_in_this_study": role,
        })
        bib.append(bibtex(key, r))
        print(f"OK  {key:30s} {r['type']:20s} openalex_core={idx.get('openalex_is_core_venue')}")

    for k, why in failures:
        print(f"SKIP {k}: {why}")

    rows.sort(key=lambda d: (d["venue_type"], d["year"] or 0))
    out_csv = RESEARCH / "papers_table.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (RESEARCH / "references.bib").write_text(
        "% Generated by research/build_literature.py from Crossref-verified\n"
        "% metadata only. Do not hand-edit.\n\n" + "\n".join(bib), encoding="utf-8")
    dump_json({"n_verified_entries": len(rows), "skipped": failures,
               "quartile_policy": {"journals": JOURNAL_RANKING_NOTE,
                                   "conferences": CONF_RANKING_NOTE}},
              RESEARCH / "literature_build_log.json")
    print(f"\n{len(rows)} entries -> {out_csv}, references.bib")


if __name__ == "__main__":
    main()
