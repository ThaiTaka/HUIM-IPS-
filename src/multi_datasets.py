"""Loaders for the datasets in dataset-20261013T020803Z-1-001/dataset.

Every loader returns the same schema the HUIM-IPS pipeline was written for, so
the study can be re-run with ONLY the data changed:

    WAP*        one column per access point, raw dBm, 100 = not detected
                (the UJIIndoorLoc convention, preprocess_uji.NOT_DETECTED)
    X, Y        reference position (metres, or EPSG:3857 for UJIIndoorLoc)
    BUILDINGID, FLOOR
    RP          reference-point id (one id per distinct training position)
    GROUP       the unit the cross-validation folds are grouped by
    SRC_FILE, SRC_ROW   original file and row (header = row 1), so every
                        prediction can be traced back to a line of the source

What differs between datasets, and what each loader decides
------------------------------------------------------------
* the "not detected" value: UJIIndoorLoc, UJI_LIB and HCXY write 100; DLULIB
  writes -100 (40,869 cells at -100 against 17 at -99 on floor 1, i.e. a floor
  value, not a reading); HUS has no missing reading at all;
* the coordinate unit, hence the factor that turns a coordinate distance into
  metres on the ground (`ground_factor`): 0.766126 for UJIIndoorLoc (Web
  Mercator, src/verify_coordinates.py), 1 for the local metric grids;
* the CV grouping (`group_col`): PHASE I3 selects on folds that imitate how the
  test split differs from the training split. UJIIndoorLoc: other users
  (USERID, as in the study). Others: see each loader.

The two folders `syl`, `tuji` and `UJI_LIB_DB_Floor_5` are empty, also inside
the downloaded zip; `empty_folders()` reports them instead of guessing.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ips_model import WEB_MERCATOR_GROUND_FACTOR
from preprocess_uji import NOT_DETECTED
from utils import DATA_PROCESSED, PROJECT_ROOT, find_dataset, sha256

MULTI_ROOT = PROJECT_ROOT / "dataset-20261013T020803Z-1-001" / "dataset"
CACHE = DATA_PROCESSED / "multi_dataset"
STD_COLS = ["X", "Y", "BUILDINGID", "FLOOR", "RP", "GROUP", "SRC_FILE",
            "SRC_ROW"]


@dataclass
class Bundle:
    key: str
    title: str
    train: pd.DataFrame
    tests: Dict[str, pd.DataFrame]          # ordered; the first is primary
    ground_factor: float
    coord_note: str
    group_col: str | None                   # None = shuffled KFold over rows
    group_note: str
    sources: List[str]
    cleaning: List[str] = field(default_factory=list)

    @property
    def wap_cols(self) -> List[str]:
        return [c for c in self.train.columns if c.startswith("WAP")]

    @property
    def n_buildings(self) -> int:
        return int(self.train["BUILDINGID"].nunique())

    @property
    def n_floors(self) -> int:
        return int(self.train[["BUILDINGID", "FLOOR"]].drop_duplicates()
                   .shape[0])


def bf_label(df: pd.DataFrame) -> np.ndarray:
    """BUILDINGID_FLOOR, exactly preprocess_uji.joint_label."""
    return (df["BUILDINGID"].astype(str) + "_" + df["FLOOR"].astype(str)
            ).to_numpy()


def class_label(b: Bundle, df: pd.DataFrame) -> np.ndarray:
    """[DESIGN] The location class used wherever the study needs a label: the
    k-NN classifier of PHASE I and the mutual information of Models B and C.
    The study uses BUILDINGID_FLOOR. A single-floor dataset has one class, so
    I(A;Y) = 0 for every AP and Model B cannot be built; there the finest
    location class the data defines - the reference point - takes its place."""
    if b.n_floors > 1:
        return bf_label(df)
    return ("RP" + df["RP"].astype(str)).to_numpy()


def label_kind(b: Bundle) -> str:
    return "BUILDINGID_FLOOR" if b.n_floors > 1 else "RP (reference point)"


# --------------------------------------------------------------------- helpers
def _pos_keys(df: pd.DataFrame) -> List[tuple]:
    """A position is (building, floor, X, Y): DLULIB reuses the same X, Y grid
    on all three floors."""
    return list(zip(df["BUILDINGID"], df["FLOOR"], df["X"].round(6),
                    df["Y"].round(6)))


def _rp_ids(frames: List[pd.DataFrame]) -> None:
    """One RP id per distinct position, numbered in order of first appearance,
    training frame first; test positions never seen in training get new ids."""
    ids: Dict[tuple, int] = {}
    for df in frames:
        keys = _pos_keys(df)
        for k in keys:
            ids.setdefault(k, len(ids) + 1)
        df["RP"] = [ids[k] for k in keys]


def _rename_aps(df: pd.DataFrame, ap_cols: List[str]) -> pd.DataFrame:
    return df.rename(columns={c: f"WAP_{c}" for c in ap_cols})


def _xlsx(path: Path, key: str) -> pd.DataFrame:
    """Read an .xlsx once and cache it as .csv.gz keyed by the file's SHA-256
    (the 21 MB UJI_LIB workbook takes over a minute to parse)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{key}__{sha256(path)[:16]}.csv.gz"
    if cached.exists():
        return pd.read_csv(cached)
    df = pd.read_excel(path)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]
    df.to_csv(cached, index=False)
    return df


def _txt(path: Path) -> pd.DataFrame:
    # index_col=False: the HUS/HCXY rows end with a tab, which would otherwise
    # shift every column one place to the left
    df = pd.read_csv(path, sep="\t", index_col=False)
    return df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]


def _std(df: pd.DataFrame, src: str, ap_cols: List[str], extra: List[str]
         ) -> pd.DataFrame:
    df = df.copy()
    df["SRC_FILE"] = src
    df["SRC_ROW"] = df.index.to_numpy() + 2            # header is row 1
    df = _rename_aps(df, ap_cols)
    waps = [f"WAP_{c}" for c in ap_cols]
    return df[waps + [c for c in STD_COLS if c in df] + extra].copy()


# -------------------------------------------------------------------- loaders
def load_uji() -> Bundle:
    d = MULTI_ROOT / "ujiindoorloc_raw"
    proj = find_dataset()
    notes = []
    for n in ("trainingData.csv", "validationData.csv"):
        same = sha256(d / n) == sha256(proj[n])
        notes.append(f"{n}: SHA-256 {'identical to' if same else 'DIFFERS from'}"
                     f" the copy the study used ({proj[n].relative_to(PROJECT_ROOT)})")
    out = []
    for n in ("trainingData.csv", "validationData.csv"):
        df = pd.read_csv(d / n)
        std = pd.DataFrame({"X": df["LONGITUDE"], "Y": df["LATITUDE"],
                            "GROUP": df["USERID"],
                            "SRC_FILE": f"ujiindoorloc_raw/{n}",
                            "SRC_ROW": df.index.to_numpy() + 2},
                           index=df.index)
        out.append(pd.concat([df, std], axis=1).copy())
    _rp_ids(out)
    return Bundle(
        key="uji", title="UJIIndoorLoc (3 tòa, 13 tầng)",
        train=out[0], tests={"validationData": out[1]},
        ground_factor=WEB_MERCATOR_GROUND_FACTOR,
        coord_note="EPSG:3857 Web Mercator; ground metres = projected x "
                   f"{WEB_MERCATOR_GROUND_FACTOR} (src/verify_coordinates.py)",
        group_col="GROUP",
        group_note="USERID - leave-users-out, exactly as PHASE I3 of the study "
                   "(validationData is another user, other phones, 4 months "
                   "later)",
        sources=[f"ujiindoorloc_raw/{n}" for n in ("trainingData.csv",
                                                   "validationData.csv")],
        cleaning=notes)


def load_uji_lib3() -> Bundle:
    """UJI library, floor 3 (long-term dataset): 25 monthly collections at 24
    training positions. Test-01 revisits the training positions, Test-02 is
    taken at 24 other positions (x shifted by 1 m)."""
    d = MULTI_ROOT / "UJI_LIB_DB_Floor_3"
    names = {"Data-Training": "train", "Test-01": "Test-01",
             "Test-02": "Test-02"}
    frames, notes = {}, []
    for fname, role in names.items():
        raw = _xlsx(d / f"{fname}.xlsx", f"uji_lib3__{fname}")
        ap = [c for c in raw.columns if str(c).startswith("AP")]
        lab = ["x", "y", "Floor", "Month"]
        bad = raw[lab].isna().any(axis=1)
        if bad.any():
            rows = (raw.index[bad] + 2).tolist()
            notes.append(f"{fname}.xlsx: dropped {int(bad.sum())} rows without "
                         f"x/y/Floor/Month (Excel rows {rows}); they are summary "
                         "rows below the data, not fingerprints")
        df = raw[~bad].copy()
        if df[ap].isna().any().any():
            raise ValueError(f"{fname}: missing RSSI after cleaning")
        df["X"], df["Y"] = df["x"].astype(float), df["y"].astype(float)
        df["BUILDINGID"], df["FLOOR"] = 0, df["Floor"].astype(int)
        df["GROUP"] = df["Month"].astype(int)
        df["Month"] = df["Month"].astype(int)
        frames[role] = _std(df, f"UJI_LIB_DB_Floor_3/{fname}.xlsx", ap,
                            ["Month"])
    _rp_ids([frames["train"], frames["Test-01"], frames["Test-02"]])
    return Bundle(
        key="uji_lib3", title="UJI Library tầng 3 (dài hạn 25 tháng)",
        train=frames["train"],
        tests={"Test-01": frames["Test-01"], "Test-02": frames["Test-02"]},
        ground_factor=1.0, coord_note="local metric grid (metres)",
        group_col="GROUP",
        group_note="Month - leave-months-out: both test sets span the same 25 "
                   "months as training and differ from it by collection "
                   "session; no user/device column exists (one phone)",
        sources=[f"UJI_LIB_DB_Floor_3/{n}.xlsx" for n in names],
        cleaning=notes)


def load_dlulib() -> Bundle:
    """DLULIB, three floors of one building. The 17 AP columns are the same
    physical APs on every floor (AP1-AP7 are strongest on floor 1, AP12-AP13 on
    floor 2, AP14-AP15 on floor 3), so the floors are stacked into one
    3-class problem."""
    tr, te, notes = [], [], []
    for f in (1, 2, 3):
        d = MULTI_ROOT / "dlulib" / f"DLULIB_Floor_{f}"
        for name, role in ((f"Training_DLULIB_Floor{f}_All_20", tr),
                           (f"Testing_DLULIB_Floor{f}", te)):
            raw = _xlsx(d / f"{name}.xlsx", f"dlulib__{name}")
            ap = [c for c in raw.columns if str(c).startswith("AP")]
            df = raw.copy()
            n_floor = int((df[ap] == -100).sum().sum())
            df[ap] = df[ap].where(df[ap] != -100, NOT_DETECTED)
            notes.append(f"{name}.xlsx: {len(df)} rows; {n_floor} cells at -100 "
                         "mapped to 'not detected' (100)")
            df["BUILDINGID"], df["FLOOR"] = 0, df["FloorID"].astype(int)
            df["RP"] = df["ID_RP"].astype(int)
            if "SampleTimes" in df:
                df["GROUP"] = df["SampleTimes"].astype(int)
            extra = [c for c in ("Smartphones", "Users", "Direction",
                                 "SampleTimes") if c in df]
            role.append(_std(df, f"dlulib/DLULIB_Floor_{f}/{name}.xlsx", ap,
                             extra))
    notes.append("Training_DLULIB_Floor*_Mean.xlsx not used: one averaged "
                 "fingerprint per RP; the study trains on raw samples "
                 "(the *_All_20 files)")
    return Bundle(
        key="dlulib", title="DLULIB (1 tòa, 3 tầng)",
        train=pd.concat(tr, ignore_index=True),
        tests={"Testing": pd.concat(te, ignore_index=True)},
        ground_factor=1.0, coord_note="local metric grid (metres), RP spacing "
                                      "1.2 m",
        group_col="GROUP",
        group_note="SampleTimes - leave-sample-indices-out: the test set "
                   "revisits every training RP with the same phones, so a dev "
                   "fold must keep each RP in training and hold out other "
                   "samples of it",
        sources=[f"dlulib/DLULIB_Floor_{f}/{n}" for f in (1, 2, 3)
                 for n in (f"Training_DLULIB_Floor{f}_All_20.xlsx",
                           f"Testing_DLULIB_Floor{f}.xlsx")],
        cleaning=notes)


def _rp_map(path: Path) -> pd.DataFrame:
    m = pd.read_csv(path, sep="\t", header=None, names=["RP", "X", "Y"])
    if m["RP"].duplicated().any():
        raise ValueError(f"duplicate RP in {path.name}")
    return m


def load_hcxy() -> Bundle:
    d = MULTI_ROOT / "hcxy"
    m = _rp_map(d / "mapxy_HCXY.txt")
    out = []
    for name in ("train_HCXY", "test_HCXY"):
        raw = _txt(d / f"{name}.txt")
        ap = [c for c in raw.columns if c.startswith("MAC")]
        df = raw.merge(m, on="RP", how="left", validate="many_to_one").copy()
        if df[["X", "Y"]].isna().any().any():
            raise ValueError(f"{name}: RP without coordinates")
        df.index = raw.index
        df["BUILDINGID"], df["FLOOR"] = 0, 0
        df["GROUP"] = df["RP"]
        out.append(_std(df, f"hcxy/{name}.txt", ap, []))
    seen = set(out[0]["RP"])
    return Bundle(
        key="hcxy", title="HCXY (1 tầng, 347 MAC)",
        train=out[0], tests={"test_HCXY": out[1]},
        ground_factor=1.0,
        coord_note="mapxy_HCXY.txt, no unit documented; read as metres (nearest"
                   " RP spacing 0.59-1.2, a survey grid)",
        group_col="GROUP",
        group_note="RP - leave-positions-out: none of the "
                   f"{out[1]['RP'].nunique()} test RPs is a training RP "
                   f"(overlap {len(seen & set(out[1]['RP']))})",
        sources=["hcxy/train_HCXY.txt", "hcxy/test_HCXY.txt",
                 "hcxy/mapxy_HCXY.txt"])


def load_hus(dedup: bool = False) -> Bundle:
    """HUS, one room, 5 APs, 205 RPs x 100 training samples.

    The two test cases are NOT independent of the training file: 204/205 rows
    of testcase1 and 205/205 of testcase2 are exact copies (same RP, same five
    RSSIs) of a row of hus_trainall, against 59.5% of training rows that have
    such a twin among themselves. Evaluated as provided, a nearest-neighbour
    model finds the copy and the error is close to 0 m by construction.
    `dedup=True` removes from training one copy per test row (the copies are
    indistinguishable, so the first ones in file order), which is the
    evaluation the study's leakage policy requires; `hus` keeps the files as
    provided so the effect can be shown."""
    d = MULTI_ROOT / "hus"
    m = _rp_map(d / "hus_mapXY.txt")
    frames = {}
    for name in ("hus_trainall", "testcase1", "testcase2"):
        raw = _txt(d / f"{name}.txt")
        ap = [c for c in raw.columns if c.startswith("AP")]
        df = raw.merge(m, on="RP", how="left", validate="many_to_one").copy()
        df.index = raw.index
        if df[["X", "Y"]].isna().any().any():
            raise ValueError(f"{name}: RP without coordinates")
        df["BUILDINGID"], df["FLOOR"] = 0, 0
        frames[name] = _std(df, f"hus/{name}.txt", ap, [])
    train, notes = frames["hus_trainall"], []
    key = [c for c in train.columns if c.startswith("WAP")] + ["RP"]
    for name in ("testcase1", "testcase2"):
        t = frames[name]
        hit = t[key].merge(train[key].drop_duplicates(), on=key).shape[0]
        notes.append(f"{name}.txt: {hit} of {len(t)} rows are exact copies of "
                     "a hus_trainall row (same RP, same 5 RSSIs)")
    if dedup:
        # remove one training row per test row, matching (RP, RSSIs) as a
        # multiset across the two test cases
        need = pd.concat([frames["testcase1"][key], frames["testcase2"][key]]
                         ).value_counts()
        occ = train.groupby(key, sort=False).cumcount()
        k = pd.MultiIndex.from_frame(train[key])
        drop = occ.to_numpy() < need.reindex(k).fillna(0).to_numpy()
        notes.append(f"dedup: removed {int(drop.sum())} training rows that the "
                     "test cases copy; training keeps "
                     f"{int((~drop).sum())} rows")
        train = train[~drop].copy()
    return Bundle(
        key="hus_dedup" if dedup else "hus",
        title=("HUS - bỏ dòng test bị chép từ train (1 phòng, 5 AP)" if dedup
               else "HUS nguyên bản (1 phòng, 5 AP)"),
        cleaning=notes,
        train=train,
        tests={"testcase1": frames["testcase1"],
               "testcase2": frames["testcase2"]},
        ground_factor=1.0, coord_note="hus_mapXY.txt grid, 0.5 spacing, read "
                                      "as metres",
        group_col=None,
        group_note="none - the files carry no user, device, session or sample "
                   "index, and both test cases revisit the training RPs; dev "
                   "folds are a shuffled 6-fold KFold over rows",
        sources=["hus/hus_trainall.txt", "hus/testcase1.txt",
                 "hus/testcase2.txt", "hus/hus_mapXY.txt"])


DATASETS: Dict[str, Callable[[], Bundle]] = {
    "uji": load_uji,
    "uji_lib3": load_uji_lib3,
    "dlulib": load_dlulib,
    "hcxy": load_hcxy,
    "hus": load_hus,
    "hus_dedup": lambda: load_hus(dedup=True),
}


def load(key: str) -> Bundle:
    b = DATASETS[key]()
    for name, df in [("train", b.train), *b.tests.items()]:
        W = df[b.wap_cols].to_numpy(dtype=np.float64)
        if np.isnan(W).any():
            raise ValueError(f"{key}/{name}: NaN RSSI")
        det = W[W != NOT_DETECTED]
        if det.size and (det.min() < -104 or det.max() > 0):
            raise ValueError(f"{key}/{name}: RSSI outside [-104, 0]")
    return b


def empty_folders() -> List[str]:
    return sorted(p.name for p in MULTI_ROOT.iterdir()
                  if p.is_dir() and not any(p.rglob("*")))


def describe(b: Bundle) -> dict:
    """Row counts and signal statistics, the numbers a reader checks first."""
    def one(df):
        W = df[b.wap_cols].to_numpy(dtype=np.float64)
        det = W != NOT_DETECTED
        return {"rows": int(len(df)),
                "positions": len(set(_pos_keys(df))),
                "floors": sorted(int(f) for f in df["FLOOR"].unique()),
                "detections_per_row_mean": round(float(det.sum(1).mean()), 3),
                "rows_with_no_detection": int((det.sum(1) == 0).sum()),
                "rssi_min": float(W[det].min()) if det.any() else None,
                "rssi_max": float(W[det].max()) if det.any() else None,
                "aps_ever_detected": int(det.any(0).sum())}
    tr_pos = set(_pos_keys(b.train))
    tests = {}
    for n, df in b.tests.items():
        d = one(df)
        pos = set(_pos_keys(df))
        d["positions_also_in_training"] = len(pos & tr_pos)
        tests[n] = d
    return {"key": b.key, "title": b.title, "sources": b.sources,
            "n_wap_columns": len(b.wap_cols),
            "n_buildings": b.n_buildings, "n_building_floor_classes": b.n_floors,
            "location_label": label_kind(b),
            "ground_factor": b.ground_factor, "coordinates": b.coord_note,
            "cv_group": b.group_note,
            "n_cv_groups": int(b.train[b.group_col].nunique())
            if b.group_col else None,
            "x_range": [float(b.train["X"].min()), float(b.train["X"].max())],
            "y_range": [float(b.train["Y"].min()), float(b.train["Y"].max())],
            "train": one(b.train), "tests": tests, "cleaning": b.cleaning}
