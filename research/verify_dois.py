"""PHASE B helper - verify every cited DOI against Crossref before anything is
written into the literature review. Crossref is the DOI registration agency for
IEEE/ACM/Springer/Elsevier, so it is the authoritative record for
title / authors / year / container / publisher / type.

Output: research/doi_verification.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils import RESEARCH, dump_json

MAILTO = "research-script@example.invalid"  # Crossref polite-pool identifier

SEED_DOIS = {
    "gan2021survey": "10.1109/TKDE.2019.2942594",
    "liu2012huiminer": "10.1145/2396761.2396773",
    "tseng2010upgrowth": "10.1145/1835804.1835839",
    "zida2017efim": "10.1007/s10115-016-0986-0",
    "zhang2018empirical": "10.1016/j.eswa.2018.02.008",
    "torressospedra2014uji": "10.1109/IPIN.2014.7275492",
    # candidates found while searching; verified the same way
    "fournierviger2014fhm": "10.1007/978-3-319-08326-1_9",
    "tseng2013twophase": "10.1109/TKDE.2012.59",
    "liu2005twophase": "10.1007/11430919_79",
    "agrawal1993mining": "10.1145/170035.170072",
    "han2000fpgrowth": "10.1145/342009.335372",
    "yao2004foundational": "10.1137/1.9781611972740.51",
    "torressospedra2015comprehensive": "10.1016/j.eswa.2015.06.009",
    "moreira2015wifi": "10.1109/IPIN.2015.7346749",
    "sinha2019survey": "10.1109/JSEN.2019.2893168",
    "song2019novel": "10.1155/2019/1689371",
    "nowicki2017lowefforts": "10.1007/978-3-319-60438-1_57",
    "bozkurt2015comparative": "10.1109/SIU.2015.7130164",
    "lohan2017wlan": "10.3390/data2040032",
    "khalajmehrabadi2017modern": "10.1109/COMST.2017.2671454",
    "hoang2019recurrent": "10.1109/TVT.2019.2901245",
    "kim2018scalable": "10.3390/s18040967",
    "jedari2015comparison": "10.1109/IPIN.2015.7346754",
    "wang2017indoor": "10.1109/TVT.2016.2635165",
    "gan2018privacy": "10.1016/j.eswa.2018.06.039",
    "fournierviger2016spmf": "10.1007/978-3-319-46131-1_8",
    "fournierviger2019survey": "10.1007/978-3-030-04921-8_1",
    "krishnamoorthy2017hminer": "10.1016/j.eswa.2017.03.035",
    "duong2018efficient": "10.1007/s10115-017-1066-9",
    "nguyen2019mining": "10.1016/j.ins.2019.03.043",
}


def fetch(doi: str) -> dict:
    url = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(url, params={"mailto": MAILTO}, timeout=40,
                         headers={"User-Agent": f"HUIM-IPS-study (mailto:{MAILTO})"})
    except Exception as e:  # network problems must be visible, not silent
        return {"doi": doi, "status": "REQUEST_FAILED", "error": repr(e)}
    if r.status_code == 404:
        return {"doi": doi, "status": "NOT_FOUND_IN_CROSSREF"}
    if r.status_code != 200:
        return {"doi": doi, "status": f"HTTP_{r.status_code}"}
    m = r.json()["message"]
    authors = []
    for a in m.get("author", []) or []:
        authors.append(" ".join(x for x in (a.get("given"), a.get("family")) if x)
                       or a.get("name", "?"))
    issued = (m.get("issued", {}).get("date-parts") or [[None]])[0]
    container = m.get("container-title") or []
    return {
        "doi": m.get("DOI"),
        "status": "VERIFIED",
        "title": (m.get("title") or ["?"])[0],
        "authors": authors,
        "n_authors": len(authors),
        "year_issued": issued[0] if issued else None,
        "published_print": (m.get("published-print", {}).get("date-parts")
                            or [[None]])[0],
        "published_online": (m.get("published-online", {}).get("date-parts")
                             or [[None]])[0],
        "container_title": container[0] if container else None,
        "short_container_title": (m.get("short-container-title") or [None])[0],
        "publisher": m.get("publisher"),
        "type": m.get("type"),
        "volume": m.get("volume"),
        "issue": m.get("issue"),
        "page": m.get("page"),
        "issn": m.get("ISSN"),
        "isbn": m.get("ISBN"),
        "event": (m.get("event") or {}).get("name"),
        "is_referenced_by_count": m.get("is-referenced-by-count"),
        "url": m.get("URL"),
    }


def main() -> None:
    out = {}
    for key, doi in SEED_DOIS.items():
        rec = fetch(doi)
        out[key] = rec
        print(f"{key:34s} {rec['status']:22s} {str(rec.get('container_title'))[:58]}")
        time.sleep(0.25)
    dump_json(out, RESEARCH / "doi_verification.json")
    n_ok = sum(1 for v in out.values() if v["status"] == "VERIFIED")
    print(f"\nVERIFIED {n_ok}/{len(out)}")


if __name__ == "__main__":
    main()
