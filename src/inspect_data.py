"""PHASE A - Data audit for UJIIndoorLoc.

Reads the two raw CSVs read-only, verifies the schema empirically (no hard-coded
520), and in particular tests the widespread claim that the value 100 in a WAP
column encodes "access point not detected". Everything measured is written to
results/data_summary.json; make_audit_report.py renders results/data_audit.md
from that JSON so the prose can never disagree with the numbers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (RESULTS, dump_json, environment_info, find_dataset,
                   get_logger, sha256)

LOG = get_logger("audit", "data_audit.log")

NON_WAP_EXPECTED = ["LONGITUDE", "LATITUDE", "FLOOR", "BUILDINGID",
                    "SPACEID", "RELATIVEPOSITION", "USERID", "PHONEID",
                    "TIMESTAMP"]


def describe_split(name: str, path: Path):
    LOG.info("Reading %s (%s)", name, path)
    df = pd.read_csv(path)
    out: dict = {"file": str(path), "sha256": sha256(path),
                 "n_rows": int(df.shape[0]), "n_cols": int(df.shape[1])}

    # --- schema: discover WAP columns instead of assuming a count -------------
    wap_cols = [c for c in df.columns if c.upper().startswith("WAP")]
    other_cols = [c for c in df.columns if c not in wap_cols]
    out["n_wap_columns_detected"] = len(wap_cols)
    out["wap_column_first"] = wap_cols[0] if wap_cols else None
    out["wap_column_last"] = wap_cols[-1] if wap_cols else None
    out["non_wap_columns"] = other_cols
    out["dtypes"] = {c: str(t) for c, t in df.dtypes.items()}
    out["wap_dtypes_unique"] = sorted({str(df[c].dtype) for c in wap_cols})
    nums = sorted(int(c[3:]) for c in wap_cols if c[3:].isdigit())
    out["wap_numbering_dense_1_based"] = bool(
        nums and nums[0] == 1 and nums[-1] == len(nums)
        and len(set(nums)) == len(nums))
    out["non_wap_columns_match_expected"] = (other_cols == NON_WAP_EXPECTED)

    # --- integrity -----------------------------------------------------------
    out["missing_values_total"] = int(df.isna().sum().sum())
    out["columns_with_missing"] = {c: int(v) for c, v in
                                   df.isna().sum().items() if v > 0}
    out["duplicate_rows_full"] = int(df.duplicated().sum())
    out["duplicate_rows_wap_only"] = int(df.duplicated(subset=wap_cols).sum())

    W = df[wap_cols].to_numpy()

    # --- the "100 == not detected" question ----------------------------------
    vals = W.ravel()
    uniq, cnts = np.unique(vals, return_counts=True)
    total_cells = int(vals.size)
    probe = {
        "total_wap_cells": total_cells,
        "global_min": float(vals.min()),
        "global_max": float(vals.max()),
        "n_distinct_values": int(uniq.size),
        "count_eq_100": int(cnts[uniq == 100].sum()) if (uniq == 100).any() else 0,
        "count_gt_0": int((vals > 0).sum()),
        "count_eq_0": int((vals == 0).sum()),
        "count_lt_0": int((vals < 0).sum()),
        "count_in_1_to_99": int(((vals >= 1) & (vals <= 99)).sum()),
        "count_gt_100": int((vals > 100).sum()),
        "count_lt_minus_104": int((vals < -104).sum()),
    }
    probe["share_eq_100_pct"] = round(100.0 * probe["count_eq_100"] / total_cells, 4)
    non100 = vals[vals != 100]
    probe["max_value_excluding_100"] = float(non100.max()) if non100.size else None
    probe["min_value_excluding_100"] = float(non100.min()) if non100.size else None
    probe["gap_between_100_and_next_lower_value"] = (
        float(100 - non100.max()) if non100.size else None)
    order = np.argsort(-cnts)[:15]
    probe["most_frequent_values"] = [
        {"value": float(uniq[i]), "count": int(cnts[i]),
         "pct_of_cells": round(100.0 * cnts[i] / total_cells, 4)} for i in order]
    det = (W != 100).sum(axis=1)
    probe["detections_per_fingerprint"] = {
        "min": int(det.min()), "max": int(det.max()),
        "mean": round(float(det.mean()), 3), "median": float(np.median(det)),
        "std": round(float(det.std()), 3),
        "n_rows_with_zero_detections": int((det == 0).sum()),
        "percentiles": {str(p): float(np.percentile(det, p))
                        for p in (1, 5, 25, 50, 75, 95, 99)},
    }
    all100 = [wap_cols[j] for j in range(len(wap_cols)) if (W[:, j] == 100).all()]
    probe["n_wap_columns_always_100"] = len(all100)
    probe["wap_columns_always_100_sample"] = all100[:20]
    out["not_detected_probe"] = probe

    # --- RSSI statistics over detected readings only -------------------------
    detected = non100.astype(float)
    out["rssi_detected_stats"] = {
        "n": int(detected.size),
        "min": float(detected.min()), "max": float(detected.max()),
        "mean": round(float(detected.mean()), 4),
        "median": float(np.median(detected)),
        "std": round(float(detected.std()), 4),
        "percentiles": {str(p): float(np.percentile(detected, p))
                        for p in (1, 5, 25, 50, 75, 95, 99)},
        "n_positive_detected": int((detected > 0).sum()),
        "n_zero_detected": int((detected == 0).sum()),
    }
    out["rssi_raw_stats_including_sentinel"] = {
        "mean": round(float(vals.mean()), 4), "std": round(float(vals.std()), 4)}

    # --- labels --------------------------------------------------------------
    for col in ("BUILDINGID", "FLOOR", "SPACEID", "RELATIVEPOSITION",
                "USERID", "PHONEID"):
        if col in df.columns:
            vc = df[col].value_counts().sort_index()
            out[f"{col}_n_unique"] = int(df[col].nunique())
            out[f"{col}_values"] = [int(v) for v in sorted(df[col].unique())]
            if df[col].nunique() <= 40:
                out[f"{col}_distribution"] = {str(k): int(v) for k, v in vc.items()}

    if {"BUILDINGID", "FLOOR"} <= set(df.columns):
        ct = pd.crosstab(df["BUILDINGID"], df["FLOOR"])
        out["building_x_floor"] = {str(b): {str(f): int(ct.loc[b, f])
                                            for f in ct.columns}
                                   for b in ct.index}
        joint = df["BUILDINGID"].astype(str) + "_" + df["FLOOR"].astype(str)
        out["joint_building_floor_n_classes"] = int(joint.nunique())
        out["joint_building_floor_distribution"] = {
            str(k): int(v) for k, v in joint.value_counts().sort_index().items()}

    for col in ("LONGITUDE", "LATITUDE"):
        if col in df.columns:
            s = df[col].astype(float)
            out[f"{col}_stats"] = {
                "min": float(s.min()), "max": float(s.max()),
                "mean": round(float(s.mean()), 4),
                "range": round(float(s.max() - s.min()), 4)}

    if "TIMESTAMP" in df.columns:
        ts = df["TIMESTAMP"].astype("int64")
        out["TIMESTAMP_present"] = True
        out["TIMESTAMP_stats"] = {
            "min": int(ts.min()), "max": int(ts.max()),
            "min_utc": pd.to_datetime(ts.min(), unit="s", utc=True).isoformat(),
            "max_utc": pd.to_datetime(ts.max(), unit="s", utc=True).isoformat(),
            "span_days": round(float((ts.max() - ts.min()) / 86400.0), 3),
            "n_unique": int(ts.nunique()),
            "looks_like_unix_seconds": bool(1_000_000_000 < ts.min() < 2_000_000_000)}
    else:
        out["TIMESTAMP_present"] = False
    return out, df, wap_cols


def anomaly_probes(df, wap_cols) -> dict:
    """Follow-ups on the oddities the first pass surfaced: empty fingerprints,
    0 dBm readings, per-WAP support, and how far each AP is seen across the
    three buildings (relevant later for discriminative utility)."""
    W = df[wap_cols].to_numpy()
    det_mask = (W != 100)
    det_per_row = det_mask.sum(axis=1)
    a: dict = {}

    empty = det_per_row == 0
    a["n_empty_fingerprints"] = int(empty.sum())
    if empty.any():
        sub = df.loc[empty]
        a["empty_fingerprints_by_building"] = {
            str(k): int(v) for k, v in sub["BUILDINGID"].value_counts().sort_index().items()}
        a["empty_fingerprints_by_joint_class"] = {
            str(k): int(v) for k, v in
            (sub["BUILDINGID"].astype(str) + "_" + sub["FLOOR"].astype(str))
            .value_counts().sort_index().items()}
        a["empty_fingerprints_by_phoneid"] = {
            str(k): int(v) for k, v in sub["PHONEID"].value_counts().sort_index().items()}

    zero_dbm = (W == 0)
    a["n_cells_equal_0_dbm"] = int(zero_dbm.sum())
    a["n_rows_containing_a_0_dbm_reading"] = int(zero_dbm.any(axis=1).sum())
    a["n_wap_columns_containing_a_0_dbm_reading"] = int(zero_dbm.any(axis=0).sum())
    if zero_dbm.any():
        rows0 = df.loc[zero_dbm.any(axis=1)]
        a["rows_with_0_dbm_by_phoneid"] = {
            str(k): int(v) for k, v in rows0["PHONEID"].value_counts().sort_index().items()}
        a["rows_with_0_dbm_by_building"] = {
            str(k): int(v) for k, v in rows0["BUILDINGID"].value_counts().sort_index().items()}

    sup = det_mask.sum(axis=0)
    detected_sup = sup[sup > 0]
    a["wap_support"] = {
        "n_waps_detected_at_least_once": int((sup > 0).sum()),
        "n_waps_never_detected": int((sup == 0).sum()),
        "support_min_over_detected": int(detected_sup.min()) if detected_sup.size else None,
        "support_max": int(sup.max()),
        "support_mean_over_detected": round(float(detected_sup.mean()), 2)
        if detected_sup.size else None,
        "support_median_over_detected": float(np.median(detected_sup))
        if detected_sup.size else None,
        "n_waps_with_support_lt_10": int(((sup > 0) & (sup < 10)).sum()),
        "n_waps_with_support_lt_50": int(((sup > 0) & (sup < 50)).sum()),
        "n_waps_with_support_ge_1000": int((sup >= 1000).sum()),
        "top10_waps_by_support": [
            {"wap": wap_cols[j], "support": int(sup[j]),
             "support_pct": round(100.0 * sup[j] / len(df), 3)}
            for j in np.argsort(-sup)[:10]],
    }

    # Spatial spread: in how many of the 3 buildings is each AP ever detected?
    bids = sorted(df["BUILDINGID"].unique())
    per_building_seen = np.zeros((len(bids), len(wap_cols)), dtype=bool)
    for i, b in enumerate(bids):
        per_building_seen[i] = det_mask[(df["BUILDINGID"] == b).to_numpy()].any(axis=0)
    n_bld = per_building_seen.sum(axis=0)
    a["ap_building_spread"] = {
        "n_waps_in_0_buildings": int((n_bld == 0).sum()),
        "n_waps_in_exactly_1_building": int((n_bld == 1).sum()),
        "n_waps_in_exactly_2_buildings": int((n_bld == 2).sum()),
        "n_waps_in_all_3_buildings": int((n_bld == 3).sum()),
    }
    return a


def cross_split_checks(dtr, dva, wap_tr, wap_va) -> dict:
    x = {
        "same_columns": list(dtr.columns) == list(dva.columns),
        "same_wap_count": len(wap_tr) == len(wap_va),
        "train_rows": int(dtr.shape[0]), "validation_rows": int(dva.shape[0]),
    }
    Wtr, Wva = dtr[wap_tr].to_numpy(), dva[wap_va].to_numpy()
    seen_tr = (Wtr != 100).any(axis=0)
    seen_va = (Wva != 100).any(axis=0)
    x["waps_detected_in_train"] = int(seen_tr.sum())
    x["waps_detected_in_validation"] = int(seen_va.sum())
    x["waps_detected_in_both"] = int((seen_tr & seen_va).sum())
    x["waps_only_in_validation"] = int(((~seen_tr) & seen_va).sum())
    x["waps_only_in_train"] = int((seen_tr & (~seen_va)).sum())
    x["waps_detected_in_neither"] = int(((~seen_tr) & (~seen_va)).sum())
    jtr = set((dtr["BUILDINGID"].astype(str) + "_" + dtr["FLOOR"].astype(str)).unique())
    jva = set((dva["BUILDINGID"].astype(str) + "_" + dva["FLOOR"].astype(str)).unique())
    x["joint_classes_train"] = sorted(jtr)
    x["joint_classes_validation"] = sorted(jva)
    x["joint_classes_only_in_train"] = sorted(jtr - jva)
    x["joint_classes_only_in_validation"] = sorted(jva - jtr)
    for col in ("SPACEID", "RELATIVEPOSITION"):
        if col in dva.columns:
            x[f"validation_{col}_n_unique"] = int(dva[col].nunique())
            x[f"validation_{col}_all_zero"] = bool((dva[col] == 0).all())
    for col in ("PHONEID", "USERID"):
        if col in dtr.columns and col in dva.columns:
            a, b = set(dtr[col].unique()), set(dva[col].unique())
            x[f"{col}_train_values"] = sorted(int(v) for v in a)
            x[f"{col}_validation_values"] = sorted(int(v) for v in b)
            x[f"{col}_overlap"] = sorted(int(v) for v in (a & b))
            x[f"{col}_validation_only"] = sorted(int(v) for v in (b - a))
    key_tr = set(map(tuple, Wtr.tolist()))
    x["validation_rows_with_wap_vector_identical_to_a_train_row"] = int(
        sum(1 for r in Wva.tolist() if tuple(r) in key_tr))
    return x


def main() -> None:
    paths = find_dataset()
    tr, dtr, wtr = describe_split("trainingData.csv", paths["trainingData.csv"])
    va, dva, wva = describe_split("validationData.csv", paths["validationData.csv"])
    tr["anomaly_probes"] = anomaly_probes(dtr, wtr)
    va["anomaly_probes"] = anomaly_probes(dva, wva)
    cross = cross_split_checks(dtr, dva, wtr, wva)

    summary = {
        "audit_phase": "PHASE A - data audit",
        "environment": environment_info(),
        "training": tr,
        "validation": va,
        "cross_split": cross,
    }
    dump_json(summary, RESULTS / "data_summary.json")
    LOG.info("Wrote %s", RESULTS / "data_summary.json")
    p = tr["not_detected_probe"]
    LOG.info("train: %d rows x %d cols, %d WAP cols", tr["n_rows"], tr["n_cols"],
             tr["n_wap_columns_detected"])
    LOG.info("value 100 occupies %.2f%% of WAP cells; max value excluding 100 = %s",
             p["share_eq_100_pct"], p["max_value_excluding_100"])
    LOG.info("detections/fingerprint: mean %.2f, min %d, max %d",
             p["detections_per_fingerprint"]["mean"],
             p["detections_per_fingerprint"]["min"],
             p["detections_per_fingerprint"]["max"])


if __name__ == "__main__":
    main()
