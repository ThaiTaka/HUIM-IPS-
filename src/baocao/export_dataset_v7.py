"""Số liệu về dataset UJIIndoorLoc cho bộ slide V7 đầy đủ (Slide_HUIM_IPS_V7_day_du.pptx).

Mọi số được TÍNH TRỰC TIẾP từ hai file CSV gốc (chỉ đọc, không ghi) và từ results/huim_only/uji/cell_runs.csv:
    ujiindoorloc/UJIndoorLoc/trainingData.csv, validationData.csv
Ghi: BAOCAO/so_lieu_V7/du_lieu_dataset_uji.json

    python src/baocao/export_dataset_v7.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
UJI = ROOT / "ujiindoorloc" / "UJIndoorLoc"
NOT_DET = 100


def split_view(df: pd.DataFrame) -> dict:
    W = df.iloc[:, :520].values
    det = W != NOT_DET
    n_ap = det.sum(1)
    d = W[det]
    ts = pd.to_datetime(df.TIMESTAMP, unit="s", utc=True)
    bins = [(0, 0), (1, 5), (6, 10), (11, 15), (16, 20), (21, 30), (31, 99)]
    return {
        "rows": int(len(df)),
        "share_not_detected": float(1 - det.mean()),
        "n_readings": int(det.sum()),
        "ap_per_fp": {"mean": float(n_ap.mean()), "median": float(np.median(n_ap)), "min": int(n_ap.min()), "max": int(n_ap.max()),
                      "p5": float(np.percentile(n_ap, 5)), "p95": float(np.percentile(n_ap, 95)), "n_empty": int((n_ap == 0).sum())},
        "ap_hist": [{"lo": lo, "hi": hi, "share": float(((n_ap >= lo) & (n_ap <= hi)).mean())} for lo, hi in bins],
        "rssi": {"min": int(d.min()), "max": int(d.max()), "mean": float(d.mean()), "median": float(np.median(d))},
        "dates": [ts.min().strftime("%Y-%m-%d"), ts.max().strftime("%Y-%m-%d")],
        "phones": sorted(int(x) for x in df.PHONEID.unique()), "users": sorted(int(x) for x in df.USERID.unique()),
        "by_building": {str(b): int((df.BUILDINGID == b).sum()) for b in sorted(df.BUILDINGID.unique())},
        "n_building_floor": int(df.groupby(["BUILDINGID", "FLOOR"]).ngroups),
        "aps_ever_detected": int(det.any(0).sum()),
        "dup_rows": int(df.duplicated().sum()),
    }


def main() -> None:
    tr = pd.read_csv(UJI / "trainingData.csv")
    te = pd.read_csv(UJI / "validationData.csv")
    A, B = split_view(tr), split_view(te)
    Wtr, Wte = tr.iloc[:, :520].values != NOT_DET, te.iloc[:, :520].values != NOT_DET
    cell = tr.groupby(["LONGITUDE", "LATITUDE", "FLOOR", "BUILDINGID"]).ngroup()
    informative = Wtr.sum(1) > 0
    per_cell = pd.Series(informative).groupby(cell.values).sum()
    cr = pd.read_csv(ROOT / "results" / "huim_only" / "uji" / "cell_runs.csv")
    ap_bld = {}
    for b in sorted(tr.BUILDINGID.unique()):
        ap_bld[int(b)] = Wtr[(tr.BUILDINGID == b).values].any(0)
    n_bld = np.sum([m.astype(int) for m in ap_bld.values()], 0)
    out = {
        "train": A, "test": B,
        "phones_overlap": sorted(set(A["phones"]) & set(B["phones"])), "phones_unseen_in_test": sorted(set(B["phones"]) - set(A["phones"])),
        "users_overlap": sorted(set(A["users"]) & set(B["users"])),
        "days_gap": int((datetime.fromisoformat(B["dates"][0]) - datetime.fromisoformat(A["dates"][1])).days),
        "aps": {"train_only": int((Wtr.any(0) & ~Wte.any(0)).sum()), "test_only": int((~Wtr.any(0) & Wte.any(0)).sum()),
                "both": int((Wtr.any(0) & Wte.any(0)).sum()), "one_building": int((n_bld == 1).sum()), "all_three": int((n_bld == 3).sum())},
        "cells": {"n": int(cell.nunique()), "n_cell_runs": int(len(cr)), "mean_informative_fp": float(per_cell.mean()),
                  "min": int(per_cell.min()), "median": float(per_cell.median()), "max": int(per_cell.max()),
                  "n_informative_fp": int(informative.sum())},
        "floor_per_building": {str(b): int(tr[tr.BUILDINGID == b].FLOOR.nunique()) for b in sorted(tr.BUILDINGID.unique())},
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    p = ROOT / "BAOCAO" / "so_lieu_V7" / "du_lieu_dataset_uji.json"
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written", p)
    print(json.dumps({k: out[k] for k in ("phones_overlap", "phones_unseen_in_test", "users_overlap", "days_gap", "aps", "cells", "floor_per_building")}, ensure_ascii=False))
    print(json.dumps({k: A[k] for k in ("rows", "share_not_detected", "ap_per_fp", "rssi", "dates", "by_building", "n_building_floor", "aps_ever_detected", "dup_rows")}, ensure_ascii=False))
    print(json.dumps({k: B[k] for k in ("rows", "share_not_detected", "ap_per_fp", "rssi", "dates", "by_building", "n_building_floor", "aps_ever_detected")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
