"""Determine, empirically, what coordinate system UJIIndoorLoc's
LONGITUDE/LATITUDE columns are in - because neither the UCI attribute
description nor the dataset authors' page states one, and the answer changes
every positioning-error number in the study.

Method: take the measured coordinate bounds, invert each candidate projection,
and check whether the result lands on Universitat Jaume I in Castello de la
Plana, Spain (the campus the data was collected on). Only one candidate can.

Candidates tested
-----------------
  * EPSG:3857  Web Mercator / "pseudo-Mercator"
  * EPSG:25830 / 32630  UTM zone 30N (the zone containing Castello)
  * EPSG:25831 / 32631  UTM zone 31N (the neighbouring zone)
  * raw WGS84 degrees

Why it matters: Web Mercator is *not* an equidistant projection. Its scale
factor is 1/cos(latitude), so at ~40 deg N a distance read straight off those
coordinates is about 1.30x larger than the true distance on the ground. If the
columns are Web Mercator, then every "mean error in metres" computed directly
from them - as the UJIIndoorLoc literature does - is inflated by that factor.

Output: results/coordinate_system_verification.json
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import RESULTS, dump_json, get_logger, load_json

LOG = get_logger("coords", "coordinates.log")

R_WGS84 = 6378137.0          # WGS84 semi-major axis, used by EPSG:3857
F_WGS84 = 1 / 298.257223563  # WGS84 flattening, used by UTM

# Universitat Jaume I, Castello de la Plana. Independent of the dataset.
UJI_REFERENCE = {
    "name": "Universitat Jaume I campus, Castello de la Plana, Spain",
    "lat_deg": 39.9935,
    "lon_deg": -0.0686,
    "source": "campus location of the institution that published the dataset "
              "(Torres-Sospedra et al., IPIN 2014)",
    "assumed_uncertainty_deg": 0.004,   # ~450 m; a campus is not a point
}


def inverse_web_mercator(x: float, y: float) -> tuple[float, float]:
    """EPSG:3857 -> (lat_deg, lon_deg)."""
    lon = math.degrees(x / R_WGS84)
    lat = math.degrees(2 * math.atan(math.exp(y / R_WGS84)) - math.pi / 2)
    return lat, lon


def inverse_utm(easting: float, northing: float, zone: int,
                northern: bool = True) -> tuple[float, float]:
    """Inverse transverse Mercator (UTM), WGS84, series solution."""
    k0 = 0.9996
    a = R_WGS84
    f = F_WGS84
    e2 = f * (2 - f)
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    x = easting - 500000.0
    y = northing if northern else northing - 10000000.0
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu))
    ep2 = e2 / (1 - e2)
    c1 = ep2 * math.cos(phi1) ** 2
    t1 = math.tan(phi1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d ** 2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2
           - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d
           - (1 + 2 * t1 + c1) * d ** 3 / 6
           + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2
              + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(phi1)
    lon0 = math.radians(zone * 6 - 183)
    return math.degrees(lat), math.degrees(lon0 + lon)


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371008.8  # mean Earth radius
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def main() -> None:
    S = load_json(RESULTS / "data_summary.json")
    tr = S["training"]
    lon_s, lat_s = tr["LONGITUDE_stats"], tr["LATITUDE_stats"]
    cx = (lon_s["min"] + lon_s["max"]) / 2.0
    cy = (lat_s["min"] + lat_s["max"]) / 2.0
    LOG.info("dataset centroid of the bounding box: X=%.3f  Y=%.3f", cx, cy)

    ref = UJI_REFERENCE
    cands = []

    lat, lon = inverse_web_mercator(cx, cy)
    cands.append({"candidate": "EPSG:3857 Web Mercator (pseudo-Mercator)",
                  "lat_deg": round(lat, 6), "lon_deg": round(lon, 6)})
    for zone in (30, 31):
        try:
            la, lo = inverse_utm(cx, cy, zone)
            cands.append({"candidate": f"UTM zone {zone}N (EPSG:326{zone})",
                          "lat_deg": round(la, 6), "lon_deg": round(lo, 6)})
        except Exception as e:
            cands.append({"candidate": f"UTM zone {zone}N",
                          "error": repr(e)})
    cands.append({"candidate": "raw WGS84 degrees",
                  "lat_deg": cy, "lon_deg": cx})

    for c in cands:
        if "lat_deg" not in c:
            continue
        try:
            d = haversine_m(c["lat_deg"], c["lon_deg"],
                            ref["lat_deg"], ref["lon_deg"])
            c["distance_to_uji_campus_m"] = round(d, 1)
            c["plausible"] = bool(d < 2000)   # within 2 km of the campus
        except Exception:
            c["distance_to_uji_campus_m"] = None
            c["plausible"] = False
    cands.sort(key=lambda c: c.get("distance_to_uji_campus_m") or 1e18)

    winner = cands[0] if cands[0].get("plausible") else None
    out = {
        "question": "What coordinate system are UJIIndoorLoc's "
                    "LONGITUDE/LATITUDE columns in?",
        "why_it_matters": "The dataset documents no unit, and the projection "
                          "determines whether a distance read off these "
                          "columns is a true ground distance.",
        "measured_bounds": {
            "X_min": lon_s["min"], "X_max": lon_s["max"],
            "Y_min": lat_s["min"], "Y_max": lat_s["max"],
            "X_extent": lon_s["range"], "Y_extent": lat_s["range"]},
        "reference_location": ref,
        "candidates_tested": cands,
        "conclusion": None,
    }

    if winner:
        lat_c = winner["lat_deg"]
        k = 1.0 / math.cos(math.radians(lat_c))     # Web Mercator scale factor
        is_merc = winner["candidate"].startswith("EPSG:3857")
        out["conclusion"] = {
            "identified_as": winner["candidate"],
            "inverted_centroid_lat_deg": lat_c,
            "inverted_centroid_lon_deg": winner["lon_deg"],
            "distance_to_uji_campus_m": winner["distance_to_uji_campus_m"],
            "unit_of_the_columns": "metres (projected)",
            "is_equidistant_projection": not is_merc,
        }
        if is_merc:
            out["conclusion"].update({
                "web_mercator_scale_factor_at_this_latitude": round(k, 6),
                "ground_distance_correction_factor": round(1.0 / k, 6),
                "meaning": "Web Mercator is conformal, NOT equidistant: its "
                           "scale factor is 1/cos(latitude). A distance of D "
                           f"read straight off these columns corresponds to "
                           f"about D x {1.0/k:.4f} metres on the ground at "
                           f"latitude {lat_c:.4f} deg N.",
                "consequence_for_this_study": "Positioning error is reported "
                                              "BOTH ways: raw projected "
                                              "distance (the convention the "
                                              "UJIIndoorLoc literature uses) "
                                              "and geodesically corrected "
                                              "ground distance.",
                "true_extent_m": {
                    "x": round(out["measured_bounds"]["X_extent"] / k, 2),
                    "y": round(out["measured_bounds"]["Y_extent"] / k, 2)},
                "projected_extent_m": {
                    "x": round(out["measured_bounds"]["X_extent"], 2),
                    "y": round(out["measured_bounds"]["Y_extent"], 2)},
                "projected_bbox_area_m2": round(
                    out["measured_bounds"]["X_extent"]
                    * out["measured_bounds"]["Y_extent"], 1),
                "true_bbox_area_m2": round(
                    out["measured_bounds"]["X_extent"]
                    * out["measured_bounds"]["Y_extent"] / k ** 2, 1),
                "note_on_the_published_area_figure":
                    "Secondary literature quotes ~108,703 m2 for the site. "
                    "That matches the PROJECTED bounding box, not the "
                    "corrected one, which is further evidence that the "
                    "published figure was itself computed in these projected "
                    "coordinates.",
            })
    else:
        out["conclusion"] = {"identified_as": None,
                             "note": "No candidate projection placed the "
                                     "dataset centroid near the campus; the "
                                     "unit remains unverified and errors are "
                                     "reported in coordinate units only."}

    dump_json(out, RESULTS / "coordinate_system_verification.json")
    print(f"dataset bbox centroid: X={cx:.3f}  Y={cy:.3f}\n")
    for c in cands:
        print(f"  {c['candidate']:42s} -> lat {c.get('lat_deg')!s:>12.12} "
              f"lon {c.get('lon_deg')!s:>12.12}  "
              f"dist to UJI = {c.get('distance_to_uji_campus_m')} m")
    print()
    if winner:
        print("IDENTIFIED:", winner["candidate"])
        for k2 in ("web_mercator_scale_factor_at_this_latitude",
                   "ground_distance_correction_factor", "true_extent_m",
                   "projected_extent_m", "projected_bbox_area_m2",
                   "true_bbox_area_m2"):
            if k2 in out["conclusion"]:
                print(f"  {k2} = {out['conclusion'][k2]}")
    else:
        print("NOT IDENTIFIED - errors stay in coordinate units")


if __name__ == "__main__":
    main()
