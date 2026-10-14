"""Build report/Bao_Cao_HUIM_IPS_Da_Dataset.docx - how the HUIM-IPS study
(HUIM / EFIM for access-point selection + k-NN + the PHASE I3 positioning
optimisation that gave 5.36 m on UJIIndoorLoc) was applied, unchanged, to every
dataset of dataset-20261013T020803Z-1-001, and what came out. In Vietnamese.

Format: that of report/Bao_Cao_Thuat_Toan_HUIM.docx (the Report class of
src/make_huim_report_docx.py): A4, Times New Roman, body 13 pt, table captions
above, figure captions below, formulas as images. Every chart is followed by
the table of the values it plots (long tables go to the appendix), and every
number in the text is read from results/multi_dataset/ at build time.

Inputs  results/multi_dataset/** (src/run_multi_dataset.py,
        src/make_multi_dataset_summary.py), the dataset files themselves (the
        worked example, the DLULIB floor evidence, the duplicate check),
        verification/kiem_chung_da_dataset.xlsx (number of checks),
        research/doi_verification_*.json (references)
Outputs report/Bao_Cao_HUIM_IPS_Da_Dataset.docx,
        figures/multi_dataset/figR*.png (+ .csv)

Run: python src/make_multi_dataset_report_docx.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_huim_report_docx as hr                       # Report, REFS, vn ...
import make_multi_dataset_summary as ms
from make_deck_v2 import _crossref_entry
from multi_datasets import class_label, load
from preprocess_uji import NOT_DETECTED, fit_preprocessor
from utility_models import build_external_utility
from run_multi_dataset import TIMING_MAX_ROWS, TIMING_REPEATS
from utils import PROJECT_ROOT, REPORT, RESULTS, get_logger, load_json

LOG = get_logger("multireport")
OUT = REPORT / "Bao_Cao_HUIM_IPS_Da_Dataset.docx"
FIG = ms.FIG
ROOT = ms.ROOT
vn, pc, vi = hr.vn, hr.pc, hr.vi
MODELS = ["A_signal", "B_discriminative", "C_rare_discriminative"]
MCOL = hr.MODEL_COL
LET = hr.LETTER
GRAY, BLUE, ORANGE = ms.GRAY, ms.BLUE, ms.ORANGE


def mu(p) -> str:
    return f"{float(p):g}".replace(".", ",")


def acc(v, n_classes: int) -> str:
    return pc(v) if n_classes > 1 else "—"


def set_label(cond: str) -> str:
    """'huim_topn__B_discriminative__2pct__n75' -> 'HUIM top-75 B, θ = 2%'."""
    if cond == "baseline_all":
        return "mọi AP"
    if cond == "baseline_detected":
        return "AP phát hiện ở train"
    if cond.startswith("huim_"):
        parts = cond.split("__")
        model = LET.get(parts[1], parts[1])
        pct = parts[2].replace("pct", "")
        kind = (f"top-{parts[3][1:]}" if parts[0] == "huim_topn" else "union")
        return f"HUIM {kind} {model}, θ = {mu(pct)}%"
    return cond


# ------------------------------------------------------------- references
class Refs:
    """IEEE-style numbering in order of first citation. Entries come from the
    Crossref-verified lists of the project only."""

    PROJECT = {   # key -> unique fragment of an entry of hr.REFS
        "bahl2000": "INFCOM.2000.832252", "torres2014": "IPIN.2014.7275492",
        "agrawal1993": "170035.170072", "yao2004": "1.9781611972740.51",
        "liu2005": "11430919_79", "zida2017": "s10115-016-0986-0",
        "zhang2018": "j.eswa.2018.02.008", "gan2021": "TKDE.2019.2942594",
        "chen2006": "TKDE.2006.112", "khalaj2017": "COMST.2017.2671454",
        "kaem2004": "INFCOM.2004.1356988", "torres2015": "j.eswa.2015.08.013",
        "adler2015": "IPIN.2015.7346749", "spmf2016": "978-3-319-46131-1_8"}
    JSON = {"shannon1948": ("doi_verification_formulas.json", "Shannon1948"),
            "sparck1972": ("doi_verification_formulas.json", "SparckJones1972"),
            "bray1957": ("doi_verification_formulas.json", "BrayCurtis1957"),
            "shepard1968": ("doi_verification_formulas.json", "Shepard1968"),
            "snyder1987": ("doi_verification_formulas.json", "Snyder1987"),
            "mendoza2018": ("doi_verification_multi_dataset.json",
                            "MendozaSilva2018")}

    def __init__(self) -> None:
        self.entry = {}
        for k, tag in self.PROJECT.items():
            hit = [r for r in hr.REFS if tag in r]
            if len(hit) != 1:
                raise KeyError(k)
            self.entry[k] = hit[0]
        for k, (f, tag) in self.JSON.items():
            src = load_json(PROJECT_ROOT / "research" / f)["sources"][tag]
            self.entry[k] = _crossref_entry(src)
        self.order: list[str] = []

    def c(self, *keys: str) -> str:
        for k in keys:
            if k not in self.entry:
                raise KeyError(k)
            if k not in self.order:
                self.order.append(k)
        return "[" + "], [".join(str(self.order.index(k) + 1) for k in keys) + "]"


# -------------------------------------------------------------------- data
class MD:
    """Every number of the report."""

    def __init__(self) -> None:
        self.DS = [D for D in (ms.load_ds(k) for k in ms.ORDER) if D]
        self.keys = [D["key"] for D in self.DS]
        self.by = {D["key"]: D for D in self.DS}
        self.cmp = ms.comparison(self.DS)
        self.hv = ms.huim_vs_controls(self.DS)
        self.cv = ms.curve_table(self.DS)
        self.B = {k: load(k) for k in self.keys}
        self.diag = {k: self._diag(k) for k in self.keys}
        self.runs = {k: self.by[k]["huim"] for k in self.keys}
        self.kit = self._kit()
        self.phase1 = self._phase1_match()
        real = [k for k in self.keys if k != "hus"]
        aps = [self.by[k]["summary"]["n_wap_columns"] for k in real]
        cls = [self.by[k]["summary"]["n_building_floor_classes"] for k in real]
        self.ap_range = (min(aps), max(aps)) if aps else (0, 0)
        self.cls_range = (min(cls), max(cls)) if cls else (0, 0)

    def _diag(self, key: str) -> dict:
        out = {}
        for code, m in zip("ABC", MODELS):
            f = ROOT / key / f"huim_summary__{code}.json"
            if f.exists():
                j = load_json(f)
                out[m] = {**j["diagnostics"],
                          "total_database_utility": j["total_database_utility"],
                          "n_transactions": j["n_transactions"]}
            else:                                # uji: the study's PHASE H
                j = load_json(RESULTS / "huim_summary.json")["utility_models"][m]
                out[m] = j
        return out

    def _kit(self) -> dict | None:
        p = PROJECT_ROOT / "verification" / "kiem_chung_da_dataset.xlsx"
        if not p.exists():
            return None
        from openpyxl import load_workbook
        wb = load_workbook(p, data_only=True, read_only=True)
        ok = bad = 0
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if v == "KHỚP":
                        ok += 1
                    elif v == "LỆCH":
                        bad += 1
        return {"ok": ok, "bad": bad, "sheets": len(wb.sheetnames)}

    def _phase1_match(self) -> dict | None:
        """PHASE I on UJIIndoorLoc through the generic code against the study's
        own results/metrics/ips_results.csv, condition by condition."""
        f = ROOT / "uji" / "ips_results.csv"
        if not f.exists():
            return None
        g = pd.read_csv(f)
        p = pd.read_csv(RESULTS / "metrics" / "ips_results.csv")
        ren = {"baseline_all": "baseline_all_520",
               "baseline_detected": "baseline_detected_465"}
        g["pc"] = g["condition"].map(lambda c: ren.get(c, c))
        m = g.merge(p, left_on="pc", right_on="condition", suffixes=("", "_s"))
        same = ((m["joint_accuracy"] - m["joint_building_floor_accuracy"]).abs()
                < 1e-9) & ((m["mean_err_m"] - m["pos_mean_error_ground_m"])
                           .abs() < 1e-3)
        return {"n_study": len(p), "n_generic": len(g), "n_matched": len(m),
                "n_identical": int(same.sum())}

    def name(self, k: str) -> str:
        return ms.SHORT[k]

    def tests(self, k: str) -> list[str]:
        return list(self.B[k].tests)

    def abl(self, k: str) -> pd.DataFrame:
        return self.by[k]["abl"]

    def row(self, k: str, test: str, method_prefix: str) -> pd.Series:
        c = self.cmp
        r = c[(c["dataset"] == k) & (c["test_set"] == test)
              & c["method"].str.startswith(method_prefix)]
        if not len(r):          # a stage not run yet: every metric reads as NaN
            return pd.Series({col: np.nan for col in c.columns})
        return r.iloc[0]


# ------------------------------------------------------------------ charts
def _save(fig, name: str, data: pd.DataFrame) -> Path:
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / f"{name}.png"
    fig.savefig(p)
    plt.close(fig)
    data.to_csv(FIG / f"{name}.csv", index=False)
    return p


def dlulib_floor_table(M: MD) -> pd.DataFrame:
    b = M.B["dlulib"]
    W = b.train[b.wap_cols].to_numpy(float)
    det = W != NOT_DETECTED
    rows = []
    for j, w in enumerate(b.wap_cols):
        r = {"AP": w.replace("WAP_", "")}
        for f in sorted(b.train["FLOOR"].unique()):
            m = (b.train["FLOOR"] == f).to_numpy()
            r[f"floor_{f}_detect_pct"] = 100 * det[m, j].mean()
            v = W[m, j][det[m, j]]
            r[f"floor_{f}_mean_rssi"] = v.mean() if v.size else np.nan
        rows.append(r)
    T = pd.DataFrame(rows)
    fl = sorted(b.train["FLOOR"].unique())
    T["strongest_floor"] = [fl[int(np.nanargmax([r[f"floor_{f}_mean_rssi"]
                                                   for f in fl]))]
                            for _, r in T.iterrows()]
    return T


def ch_dlulib(M: MD, T: pd.DataFrame) -> Path:
    fl = [c for c in T.columns if c.endswith("_detect_pct")]
    Z = T[fl].to_numpy().T
    fig, ax = plt.subplots(figsize=(10.5, 2.9))
    im = ax.imshow(Z, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            ax.text(j, i, f"{Z[i, j]:.0f}", ha="center", va="center",
                    fontsize=8.5, color="white" if Z[i, j] > 60 else "#14223A")
    ax.set_xticks(range(len(T)))
    ax.set_xticklabels(T["AP"], fontsize=9)
    ax.set_yticks(range(len(fl)))
    ax.set_yticklabels([f"Tầng {c.split('_')[1]}" for c in fl])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.set_label("% fingerprint thấy AP", fontsize=9)
    ax.set_title("DLULIB: tỉ lệ fingerprint huấn luyện phát hiện từng AP, theo "
                 "tầng", fontsize=11)
    return _save(fig, "figR1_dlulib_ap_by_floor", T)


def ch_mining(M: MD) -> Path:
    keys = [k for k in M.keys if k != "hus"]
    n = len(keys)
    ncol = min(3, n)
    nrow = int(np.ceil(n / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(5.2 * ncol, 3.6 * nrow),
                            squeeze=False, gridspec_kw={"hspace": 0.5,
                                                        "wspace": 0.3})
    rows = []
    for a, k in zip(axs.flat, keys):
        H = M.runs[k]
        for m in MODELS:
            g = H[H["utility_model"] == m].sort_values("rel_minutil_pct",
                                                       ascending=False)
            ok = g[g["status"] == "COMPLETED"]
            a.plot(ok["rel_minutil_pct"], ok["n_huis"].clip(lower=0.8),
                   marker="o", ms=3.5, lw=1.6, color=MCOL[m],
                   label=f"Model {LET[m]}")
            ab = g[g["status"] != "COMPLETED"]
            a.scatter(ab["rel_minutil_pct"], ab["n_huis"], marker="x", s=40,
                      color=MCOL[m])
            for _, r in g.iterrows():
                rows.append({"dataset": M.name(k), "model": LET[m],
                             "minutil_pct": r["rel_minutil_pct"],
                             "status": r["status"], "n_huis": int(r["n_huis"]),
                             "n_waps_in_huis": int(r["unique_waps_in_huis"]),
                             "runtime_s": r["runtime_s"]})
        a.set_xscale("log")
        a.set_yscale("log")
        a.invert_xaxis()
        a.set_title(M.name(k), fontsize=11)
        a.set_xlabel("minUtil (% tổng utility)")
        a.set_ylabel("Số HUI")
        a.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    for a in list(axs.flat)[n:]:
        a.set_visible(False)
    axs.flat[0].legend(fontsize=8.5, loc="upper left")
    fig.text(0.01, -0.01, "x = lần chạy dừng vì chạm ngân sách (600 s hoặc 1.000.000 "
             "HUI); đường nối các lần chạy hoàn tất.", fontsize=9, color="#444")
    return _save(fig, "figR2_huim_mining_by_dataset", pd.DataFrame(rows))


def cdf_rows(M: MD) -> pd.DataFrame:
    rows = []
    for k in M.keys:
        for t in M.tests(k):
            for tag, f in (("k-NN nghiên cứu (S0)", "study_knn"),
                           ("Mô hình tối ưu", "optimised")):
                e = pd.read_csv(ROOT / k / "predictions" / f"{t}__{f}.csv")["err_m"]
                rows.append({"dataset": M.name(k), "test_set": t, "model": tag,
                             "n": len(e), "p25_m": e.quantile(.25),
                             "p50_m": e.median(), "p75_m": e.quantile(.75),
                             "p90_m": e.quantile(.9), "p95_m": e.quantile(.95),
                             "share_le_2m": (e <= 2).mean(),
                             "share_le_5m": (e <= 5).mean()})
    return pd.DataFrame(rows)


def ch_cdf(M: MD, C: pd.DataFrame) -> Path:
    pairs = [(k, t) for k in M.keys if k != "hus" for t in M.tests(k)]
    n = len(pairs)
    ncol = min(4, n)
    nrow = int(np.ceil(n / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(4.1 * ncol, 3.2 * nrow),
                            squeeze=False, gridspec_kw={"hspace": 0.55,
                                                        "wspace": 0.3})
    for a, (k, t) in zip(axs.flat, pairs):
        xmax = 0
        for f, col, lab in (("study_knn", GRAY, "k-NN nghiên cứu (S0)"),
                            ("optimised", BLUE, "Mô hình tối ưu")):
            e = np.sort(pd.read_csv(ROOT / k / "predictions" /
                                    f"{t}__{f}.csv")["err_m"].to_numpy())
            a.plot(e, np.arange(1, len(e) + 1) / len(e) * 100, color=col,
                   lw=1.8, label=lab)
            xmax = max(xmax, np.percentile(e, 97))
        a.set_xlim(0, xmax * 1.05 if xmax > 0 else 1)
        a.set_ylim(0, 100)
        a.set_title(f"{M.name(k)} · {t}", fontsize=10)
        a.set_xlabel("Sai số (m)")
        a.set_ylabel("% fingerprint ≤ x")
    for a in list(axs.flat)[n:]:
        a.set_visible(False)
    axs.flat[0].legend(fontsize=8, loc="lower right")
    return _save(fig, "figR3_error_cdf_by_test_set", C)


# -------------------------------------------------------------- the report
def build(M: MD) -> hr.Report:
    R = hr.Report()
    rf = Refs()
    K = M.keys
    real = [k for k in K if k != "hus"]           # hus is shown as a warning
    n_tests = sum(len(M.tests(k)) for k in real)
    uji = M.by.get("uji")
    rep = uji["pos"].get("reproduces_study") if uji else None
    empty = M.DS[0]["summary"].get("empty_folders_in_dataset_root", [])

    def final_row(k, t):
        return M.row(k, t, "Tối ưu PHASE I3")

    def s0_row(k, t):
        return M.row(k, t, "k-NN")

    better = [(k, t) for k in real for t in M.tests(k)
              if final_row(k, t)["mean_err_m"] < s0_row(k, t)["mean_err_m"]]

    # ------------------------------------------------------------ title
    R.title_page([
        ("HỌC PHẦN CAO HỌC — BÀI TÌM HIỂU THUẬT TOÁN", 13, False),
        ("", 12, False), ("", 12, False),
        ("BÁO CÁO ÁP DỤNG HUIM", 22, True),
        ("VÀ MÔ HÌNH ĐỊNH VỊ TRONG NHÀ", 18, True),
        ("TRÊN NHIỀU BỘ DỮ LIỆU WI-FI FINGERPRINT", 16, True),
        ("", 12, False),
        ("Chỉ thay dữ liệu, giữ nguyên phương pháp: chuẩn hoá RSSI, ba mô hình "
         "utility,", 14, False),
        ("EFIM, chọn điểm truy cập, k-NN và quy trình tối ưu sai số theo mét "
         "(Version 2)", 14, False),
        ("", 12, False),
        (f"{len(real)} bộ dữ liệu · {n_tests} tập kiểm tra · đánh giá tòa nhà, "
         "tầng, sai số mét và thời gian", 13, False),
        ("", 12, False), ("", 12, False),
        ("Mọi số liệu trong báo cáo được sinh tự động từ các file kết quả "
         "(results/multi_dataset/); không có số liệu nhập tay.", 11, False),
    ])
    R.toc_title("Mục lục")
    R.toc_field()
    R.page_break()

    # ------------------------------------------------------------ abstract
    R.h(1, "Tóm tắt")
    ab_bits = []
    for k in real:
        for t in M.tests(k):
            f = final_row(k, t)
            ab_bits.append(f"{M.name(k)} ({t}) {vn(f['mean_err_m'])} m")
    R.para(f"Báo cáo này trình bày việc áp dụng lại toàn bộ nghiên cứu HUIM–IPS "
           f"— khai phá tập mục hữu ích cao (HUIM) bằng EFIM {rf.c('zida2017')} để "
           f"chọn điểm truy cập (AP), định vị bằng k láng giềng gần nhất (k-NN) "
           f"{rf.c('bahl2000')} và quy trình tối ưu sai số theo mét đã cho "
           f"{ms.M_SEL} trên UJIIndoorLoc {rf.c('torres2014')} — lên {len(real)} bộ dữ "
           f"liệu Wi-Fi fingerprint trong thư mục được cung cấp, với nguyên tắc "
           f"chỉ thay dữ liệu, không thay phương pháp.")
    R.para(f"Sau khi tối ưu (chọn hoàn toàn trên dữ liệu huấn luyện), sai số "
           f"trung bình trên từng tập kiểm tra là: {'; '.join(ab_bits)}. Quy "
           f"trình tối ưu giảm sai số so với k-NN của nghiên cứu ở "
           f"{len(better)}/{n_tests} tập kiểm tra. "
           + ((f"Khi chạy lại trên UJIIndoorLoc qua đúng đường code chung, kết "
               f"quả trùng với nghiên cứu gốc ({vn(rep['generic_mean_ground_m'])} "
               f"m so với {vn(rep['study_mean_ground_m'])} m), chứng tỏ phần mở "
               "rộng không làm thay đổi phương pháp.")
              if rep and rep["match"] else
              (f"Chạy lại UJIIndoorLoc qua code chung cho "
               f"{vn(rep['generic_mean_ground_m'])} m so với "
               f"{vn(rep['study_mean_ground_m'])} m của nghiên cứu gốc (xem mục "
               "4.3).") if rep else ""))
    R.para("Hai phát hiện về dữ liệu ảnh hưởng trực tiếp tới cách đọc kết quả: "
           "(i) hai tập kiểm tra của HUS gần như được chép nguyên từ tập huấn "
           "luyện, nên sai số ‘gần 0 m’ của bộ này là ảo; báo cáo dùng phiên bản "
           "đã loại các dòng bị chép; (ii) 17 cột AP của DLULIB là cùng một bộ AP "
           "trên cả ba tầng, nên ba file theo tầng được ghép thành một bài toán "
           "định vị tầng thật sự.")
    R.para([("Từ khoá: ", "b"), ("HUIM; EFIM; định vị trong nhà; Wi-Fi "
                                 "fingerprint; chọn điểm truy cập; k-NN; "
                                 "tổng quát hoá giữa các bộ dữ liệu.", "")])

    # ------------------------------------------------------------ 1
    R.h(1, "1. Mục tiêu và câu hỏi")
    R.para("Ở hai phiên bản trước, nghiên cứu chỉ chạy trên một bộ dữ liệu "
           "(UJIIndoorLoc). Một kết quả chỉ đo trên một bộ dữ liệu luôn có nguy "
           "cơ ‘khớp’ với đặc thù của bộ đó. Vì vậy lần này cùng một chương trình "
           "được chạy trên mọi bộ dữ liệu có trong thư mục "
           "dataset-20261013T020803Z-1-001 để trả lời bốn câu hỏi:")
    R.numbered([
        "Quy trình HUIM → chọn AP → định vị có chạy được trên dữ liệu khác mà "
        "không phải sửa phương pháp không?",
        "Trên mỗi bộ, độ chính xác tòa nhà, độ chính xác tầng, sai số khoảng "
        "cách (mét) và thời gian định vị là bao nhiêu?",
        f"Quy trình tối ưu sai số (đã đưa UJIIndoorLoc từ {ms.M_S0} xuống "
        f"{ms.M_SEL}) có còn giúp ích không, và cấu hình ‘{ms.M_SEL}’ có dùng "
        "lại nguyên xi được "
        "không?",
        "Tập AP do HUIM chọn có tốt hơn các cách chọn đơn giản cùng số AP "
        "(ngẫu nhiên, AP hay được phát hiện nhất, AP có thông tin tương hỗ cao "
        "nhất) không?"])
    R.para([("Nguyên tắc ‘chỉ đổi dữ liệu’. ", "b"),
            ("Mọi bước đều gọi lại đúng mã nguồn và hằng số của nghiên cứu: "
             "chuẩn hoá RSSI, ba mô hình utility, EFIM với cùng lưới ngưỡng "
             "minUtil và cùng ngân sách, cùng quy tắc chọn AP, cùng lưới siêu "
             "tham số k-NN, cùng các bước tối ưu S0–S4. Chỉ những điều mà dữ "
             "liệu buộc phải quyết định (giá trị ‘không phát hiện’, đơn vị toạ "
             "độ, nhãn vị trí khi chỉ có một tầng, cách chia fold kiểm định) "
             "mới được quyết định riêng cho từng bộ, và đều được ghi lại ở "
             "mục 2.", "")])

    # ------------------------------------------------------------ 2 data
    R.h(1, "2. Dữ liệu")
    R.h(2, "2.1. Các bộ dữ liệu trong thư mục")
    srcs = [ms.SHORT[k].split(" (")[0] for k in K if k != "hus_dedup"]
    R.para(f"Thư mục chứa {len(srcs)} bộ dữ liệu dùng được "
           f"({', '.join(s_.replace(' nguyên bản', '') for s_ in srcs)}). "
           + (f"Ba thư mục {', '.join(empty)} rỗng — rỗng cả trong file zip "
              "gốc, nên không có gì để chạy; tên file zip "
              "(…-1-001.zip) cho thấy đây là phần đầu của một bản xuất nhiều "
              "phần từ Google Drive, nhiều khả năng nội dung các thư mục này "
              "nằm ở các phần sau (…-1-002.zip, …). " if empty else "")
           + f"Bảng {R._tab + 1} tóm tắt số dòng, số AP, số vị trí và cấu "
             "trúc tập kiểm tra của từng bộ.")
    rows = []
    for k in K:
        s = M.by[k]["summary"]
        tst = "; ".join(f"{n}: {vi(v['rows'])} dòng, {v['positions']} vị trí "
                        f"({v['positions_also_in_training']} trùng train)"
                        for n, v in s["tests"].items())
        rows.append({"Bộ dữ liệu": M.name(k),
                     "Dòng train": vi(s["train"]["rows"]),
                     "AP (phát hiện ở train)": f"{s['n_wap_columns']} "
                                               f"({s['train']['aps_ever_detected']})",
                     "Vị trí train": s["train"]["positions"],
                     "Tòa / tầng": f"{s['n_buildings']} / "
                                   f"{s['n_building_floor_classes']}",
                     "AP thấy / dòng": vn(s["train"]["detections_per_row_mean"], 1),
                     "RSSI (dBm)": f"{s['train']['rssi_min']:g} … "
                                   f"{s['train']['rssi_max']:g}",
                     "Tập kiểm tra": tst})
    R.tbl(pd.DataFrame(rows), "Tổng quan các bộ dữ liệu (số liệu đọc từ "
          "dataset_summary.json của từng bộ)",
          [2.6, 1.5, 1.7, 1.3, 1.2, 1.2, 1.6, 5.0], size=9.5)

    R.h(2, "2.2. Đặc điểm từng bộ dữ liệu")
    s = M.by["uji"]["summary"] if "uji" in K else None
    if s:
        R.para([("UJIIndoorLoc. ", "b"),
                (f"Bộ dữ liệu của Đại học Jaume I (Tây Ban Nha) {rf.c('torres2014')}: "
                 f"{vi(s['train']['rows'])} fingerprint huấn luyện, "
                 f"{vi(s['tests']['validationData']['rows'])} fingerprint kiểm "
                 f"định, {s['n_wap_columns']} cột AP, {s['n_buildings']} tòa nhà "
                 f"và {s['n_building_floor_classes']} tổ hợp tòa–tầng. File "
                 "trong thư mục mới giống hệt từng byte bản mà nghiên cứu đã "
                 "dùng (cùng mã băm SHA-256). Toạ độ là hệ chiếu Web Mercator, "
                 "nên khoảng cách trên bản đồ được nhân 0,766126 (= cos vĩ độ) "
                 f"để ra mét thực địa {rf.c('snyder1987')}.", "")])
    if "uji_lib3" in K:
        s = M.by["uji_lib3"]["summary"]
        t1, t2 = s["tests"]["Test-01"], s["tests"]["Test-02"]
        R.para([("UJI_LIB tầng 3. ", "b"),
                (f"Bộ dữ liệu dài hạn ở thư viện Đại học Jaume I "
                 f"{rf.c('mendoza2018')}: đo lặp lại hằng tháng trong "
                 f"{M.B['uji_lib3'].train['Month'].nunique()} tháng tại "
                 f"{s['train']['positions']} vị trí, một điện thoại, "
                 f"{s['n_wap_columns']} cột AP (chỉ {s['train']['aps_ever_detected']} "
                 f"AP từng được thấy ở tầng 3). Có hai tập kiểm tra: Test-01 đo "
                 f"lại đúng {t1['positions_also_in_training']}/{t1['positions']} "
                 f"vị trí huấn luyện, còn Test-02 đo ở {t2['positions']} vị trí "
                 f"khác hẳn ({t2['positions_also_in_training']} vị trí trùng) — "
                 "đây là tình huống khó hơn vì mô hình phải nội suy giữa các "
                 "điểm đã khảo sát.", "")])
    if "dlulib" in K:
        b = M.B["dlulib"]
        s = M.by["dlulib"]["summary"]
        R.para([("DLULIB. ", "b"),
                (f"Ba file huấn luyện và ba file kiểm tra theo tầng (tầng 1, 2, "
                 f"3) của cùng một tòa nhà; {s['n_wap_columns']} AP; mỗi điểm "
                 f"tham chiếu (RP) có 20 mẫu huấn luyện đo bởi một trong "
                 f"{b.train['Smartphones'].nunique()} điện thoại, xoay đủ "
                 f"{b.train['Direction'].nunique()} hướng (Đông, Tây, Nam, "
                 f"Bắc), và 10 mẫu kiểm tra. Tập kiểm tra đo lại đúng "
                 f"{s['tests']['Testing']['positions_also_in_training']} RP của "
                 "tập huấn luyện. Các file *_Mean (một vân tay trung bình cho "
                 "mỗi RP) không được dùng vì nghiên cứu huấn luyện trên mẫu "
                 "gốc.", "")])
    if "hcxy" in K:
        s = M.by["hcxy"]["summary"]
        R.para([("HCXY. ", "b"),
                (f"{s['n_wap_columns']} địa chỉ MAC, {s['train']['positions']} "
                 f"RP huấn luyện × 30 mẫu, tập kiểm tra gồm "
                 f"{s['tests']['test_HCXY']['positions']} RP × 10 mẫu và không "
                 f"RP kiểm tra nào trùng RP huấn luyện. Trung bình mỗi vân tay "
                 f"thấy {vn(s['train']['detections_per_row_mean'], 1)} AP — dày "
                 "gấp đôi UJIIndoorLoc. Thư mục không có tài liệu mô tả; đơn vị "
                 "toạ độ trong mapxy_HCXY.txt không được ghi, báo cáo coi là "
                 "mét vì khoảng cách giữa hai RP liền kề là 0,59–1,2, đúng cỡ "
                 "một lưới khảo sát.", "")])
    if "hus_dedup" in K or "hus" in K:
        s = M.by["hus"]["summary"] if "hus" in K else M.by["hus_dedup"]["summary"]
        R.para([("HUS. ", "b"),
                (f"Một phòng, {s['n_wap_columns']} AP, {s['train']['positions']} "
                 f"RP trên lưới 0,5 m, mỗi RP {vi(s['train']['rows'] / s['train']['positions'])} "
                 "mẫu huấn luyện; hai tập kiểm tra (testcase1, testcase2) mỗi "
                 "tập một mẫu cho mỗi RP. Mọi AP đều được thấy ở mọi vân tay. "
                 "Mục 2.4 cho thấy hai tập kiểm tra được lấy ra từ chính tập "
                 "huấn luyện.", "")])

    R.h(2, "2.3. Đưa mọi bộ dữ liệu về cùng một lược đồ")
    R.para("Chương trình của nghiên cứu được viết cho lược đồ của UJIIndoorLoc: "
           "mỗi AP một cột, RSSI tính bằng dBm, giá trị 100 nghĩa là ‘không phát "
           "hiện’, kèm toạ độ, tòa nhà và tầng. Mô-đun src/multi_datasets.py "
           f"chuyển từng bộ về đúng lược đồ này; Bảng {R._tab + 1} liệt kê "
           "mọi quyết định riêng của từng bộ.")
    rows = []
    sentinel = {"uji": "100 (gốc)", "uji_lib3": "100 (gốc)",
                "dlulib": "-100 → 100", "hcxy": "100 (gốc)",
                "hus": "không có (thấy đủ 5 AP)",
                "hus_dedup": "không có (thấy đủ 5 AP)"}
    for k in K:
        s = M.by[k]["summary"]
        rows.append({"Bộ dữ liệu": M.name(k),
                     "‘Không phát hiện’": sentinel.get(k, ""),
                     "Hệ số ra mét": vn(s["ground_factor"], 6)
                     if s["ground_factor"] != 1 else "1 (toạ độ mét)",
                     "Nhãn vị trí (Model B/C, k-NN)":
                         "tòa_tầng" if s["n_building_floor_classes"] > 1
                         else "điểm tham chiếu (RP)",
                     "Fold kiểm định PHASE I3": s["cv_group"].split(" - ")[0],
                     "Số nhóm": s["n_cv_groups"] if s["n_cv_groups"] else "—"})
    R.tbl(pd.DataFrame(rows), "Các quyết định riêng cho từng bộ dữ liệu",
          [3.0, 3.0, 2.3, 3.2, 3.6, 1.3], size=10)
    t_schema = R._tab
    R.para([("Vì sao nhãn là ‘điểm tham chiếu’ khi chỉ có một tầng? ", "b"),
            ("Model B và C đo mức độ một AP ‘cho biết’ về vị trí bằng thông tin "
             f"tương hỗ I(A;Y) {rf.c('shannon1948')}. Nghiên cứu dùng Y = tòa_tầng. "
             "Nếu cả bộ chỉ có một tầng thì Y không đổi, I(A;Y) = 0 với mọi AP "
             "và Model B không xác định được. Khi đó lớp vị trí mịn nhất mà dữ "
             "liệu có — điểm tham chiếu — được dùng thay cho tầng. Độ chính xác "
             "tòa nhà/tầng chỉ được báo cáo ở bộ có nhiều hơn một lớp.", "")])
    R.para([("Vì sao fold kiểm định khác nhau giữa các bộ? ", "b"),
            ("Quy trình tối ưu chọn mô hình trên các fold được nhóm sao cho "
             "mỗi fold ‘giống’ tập kiểm tra nhất có thể. Trên UJIIndoorLoc, tập "
             "kiểm định là người đo khác nên fold được nhóm theo người đo "
             "(USERID). Trên HCXY, các RP kiểm tra không có trong tập huấn "
             "luyện nên fold nhóm theo RP. DLULIB kiểm tra lại đúng các RP đã "
             "đo, nên fold giữ RP và giữ lại các lần đo (SampleTimes). UJI_LIB "
             "có hai tập kiểm tra trải đủ 25 tháng, nên fold nhóm theo tháng. "
             "HUS không có cột người đo, thiết bị hay thời điểm nên dùng "
             "KFold ngẫu nhiên 6 phần.", "")])
    if "dlulib" in K:
        T = dlulib_floor_table(M)
        p = ch_dlulib(M, T)
        R.para("Ghép ba tầng DLULIB thành một bài toán chỉ đúng nếu cột AP_k ở "
               f"ba file là cùng một AP vật lý. Hình {R._fig + 1} kiểm tra điều "
               "đó: mỗi AP có một ‘tầng nhà’ nơi nó được thấy nhiều và mạnh "
               "nhất, và yếu dần ở các tầng khác — đúng như một AP cố định lan "
               "sóng qua sàn bê tông.")
        R.fig(p, "DLULIB — tỉ lệ (%) vân tay huấn luyện của mỗi tầng phát hiện "
              "từng AP (số trong ô). Mỗi AP mạnh nhất ở một tầng.", 16)
        f_dl = R._fig
        home = T.groupby("strongest_floor")["AP"].apply(lambda s: ", ".join(s))
        T2 = T.copy()
        for c in T2.columns:
            if c.endswith("_detect_pct"):
                T2[c] = T2[c].map(lambda v: vn(v, 1))
            elif c.endswith("_mean_rssi"):
                T2[c] = T2[c].map(lambda v: "—" if pd.isna(v) else vn(v, 1))
        T2.columns = ["AP"] + [f"Tầng {c.split('_')[1]}: "
                               + ("% thấy" if c.endswith("pct") else "RSSI TB")
                               for c in T2.columns[1:-1]] + ["Tầng mạnh nhất"]
        R.tbl(T2, f"Số liệu của Hình {f_dl}: tỉ lệ phát hiện và RSSI trung bình "
              "(dBm, chỉ tính lần phát hiện) của từng AP theo tầng",
              [1.3] + [1.9] * 6 + [1.6], size=9.5)
        R.para("AP mạnh nhất theo tầng: " + "; ".join(
            f"tầng {f}: {v}" for f, v in home.items()) + ".")

    R.h(2, "2.4. Kiểm tra rò rỉ giữa tập huấn luyện và tập kiểm tra")
    R.para("Trước khi tin một con số, cần chắc rằng tập kiểm tra thật sự là dữ "
           "liệu mới. Với mỗi bộ, chương trình đếm số dòng kiểm tra trùng y hệt "
           "(cùng vị trí, cùng mọi giá trị RSSI) một dòng huấn luyện, và so với "
           "tỉ lệ trùng tự nhiên ngay bên trong tập huấn luyện.")
    rows = []
    for k in K:
        b = M.B[k]
        key = b.wap_cols + ["X", "Y", "FLOOR"]
        twin = b.train.duplicated(subset=key, keep=False).mean()
        trk = b.train[key].drop_duplicates()
        for t, te in b.tests.items():
            m = te[key].merge(trk, on=key, how="left", indicator=True)
            hit = int((m["_merge"] == "both").sum())
            rows.append({"Bộ dữ liệu": M.name(k), "Tập kiểm tra": t,
                         "Dòng test trùng hệt 1 dòng train": f"{vi(hit)} / {vi(len(te))}",
                         "Tỉ lệ": pc(hit / len(te), 1),
                         "Trùng tự nhiên trong train": pc(twin, 1)})
    R.tbl(pd.DataFrame(rows), "Dòng kiểm tra trùng hệt dòng huấn luyện",
          [3.6, 2.4, 4.0, 1.8, 3.6], size=10)
    if "hus" in K:
        n_rm = (len(M.B["hus"].train) - len(M.B["hus_dedup"].train)
                if "hus_dedup" in K else 0)
        hs = ([f"Đã loại {vi(n_rm)} dòng huấn luyện bị chép sang hai tập kiểm "
               f"tra; tập huấn luyện còn {vi(len(M.B['hus_dedup'].train))} "
               "dòng."] if n_rm else [])
        R.para([("Phát hiện: tập kiểm tra của HUS được chép từ tập huấn luyện. ",
                 "b"),
                ("Gần như mọi dòng của testcase1 và testcase2 xuất hiện nguyên "
                 "vẹn trong hus_trainall.txt, trong khi chỉ khoảng một nửa số "
                 "dòng huấn luyện có ‘bản sao tự nhiên’. Nếu đánh giá như vậy, "
                 "k-NN chỉ cần tìm lại chính bản sao và sai số gần như bằng 0 — "
                 "đó là học thuộc, không phải định vị. Báo cáo giữ bản gốc "
                 "(‘HUS nguyên bản’) để minh hoạ hiệu ứng này, còn mọi kết luận "
                 "dùng bản ‘HUS (bỏ dòng chép)’: với mỗi dòng kiểm tra, đúng một "
                 "bản sao của nó bị loại khỏi tập huấn luyện. ", ""),
                (hs[-1] if hs else "", "i")])

    # ------------------------------------------------------------ 3 methods
    R.h(1, "3. Phương pháp áp dụng lên dữ liệu")
    R.para("Ý tưởng cốt lõi của HUIM {0} là coi mỗi vân tay Wi-Fi như một ‘giỏ "
           "hàng’: mỗi AP nghe được là một ‘mặt hàng’, độ mạnh tín hiệu là ‘số "
           "lượng’ và mức quan trọng của AP là ‘lợi nhuận đơn vị’. Một nhóm AP "
           "có ‘tổng lợi nhuận’ cao trên toàn bộ dữ liệu là một tập mục hữu ích "
           "cao (HUI). Phần này viết lại từng công thức như nó được áp dụng lên "
           "dữ liệu.".format(rf.c("yao2004")))
    R.h(2, "3.1. Từ vân tay đến giao dịch utility")
    R.para("Bước 1 — chuẩn hoá RSSI (utility nội, q). Giá trị RSSI của AP i "
           "trong vân tay T được đổi thành số nguyên dương từ 1 (yếu nhất) đến "
           "100 (mạnh nhất); AP không phát hiện có q = 0 và không thuộc giao "
           "dịch:")
    R.eq(r"q(i,T)=\mathrm{round}\left(1+\frac{RSSI_{i,T}-RSSI_{\min}}"
         r"{RSSI_{\max}-RSSI_{\min}}\times 99\right)")
    R.para("RSSI_min và RSSI_max chỉ được học trên tập huấn luyện của từng bộ "
           "(bảng tham số ở mục 3.2). Bước 2 — mỗi vân tay trở thành một giao dịch; utility của "
           "AP i trong T, của tập X trong T và của X trên toàn cơ sở dữ liệu là:")
    R.eq(r"u(i,T)=q(i,T)\cdot p(i),\quad u(X,T)=\sum_{i\in X}u(i,T),\quad "
         r"u(X)=\sum_{T\supseteq X}u(X,T)")
    R.para("Tập X là HUI khi u(X) ≥ minUtil, với minUtil là một tỉ lệ θ của "
           f"tổng utility của cơ sở dữ liệu {rf.c('liu2005')}:")
    R.eq(r"TU(T)=\sum_{i\in T}u(i,T),\qquad \mathrm{minUtil}=\theta\times"
         r"\sum_{T}TU(T)")
    if "dlulib" in K:
        b = M.B["dlulib"]
        tr = b.train
        prep = fit_preprocessor(tr)
        y = class_label(b, tr)
        P = {m: build_external_utility(m[0], tr, prep, y, "training")
             for m in MODELS}
        row = tr.iloc[[0]]
        tx = prep.transactions(row)[0][0]
        rows = []
        for w, q in tx.items():
            rows.append({"AP": w.replace("WAP_", ""),
                         "RSSI (dBm)": int(row[w].iloc[0]), "q(i,T)": q,
                         **{f"p(i) Model {LET[m]}": vn(P[m].external_utility[w], 4)
                            for m in MODELS},
                         "u(i,T) Model B": vn(q * P["B_discriminative"]
                                              .external_utility[w], 2)})
        tu = {m: sum(q * P[m].external_utility[w] for w, q in tx.items())
              for m in MODELS}
        n_nd = len(b.wap_cols) - len(tx)
        R.para(f"Ví dụ trên dữ liệu thật — dòng {int(row['SRC_ROW'].iloc[0])} "
               f"của {row['SRC_FILE'].iloc[0].split('/')[-1]} (DLULIB, tầng "
               f"{int(row['FLOOR'].iloc[0])}): vân tay thấy {len(tx)} AP, "
               f"{n_nd} AP còn lại không phát hiện nên không vào giao dịch. "
               f"Với RSSI_min = {prep.rssi_min_train:g} dBm và RSSI_max = "
               f"{prep.rssi_max_train:g} dBm của tập huấn luyện DLULIB, Bảng "
               f"{R._tab + 1} cho q, p và u của từng AP.".replace("-", "−"))
        R.tbl(pd.DataFrame(rows), "Một vân tay DLULIB đi qua các công thức "
              "(tính bằng chính mã nguồn của nghiên cứu)",
              [1.4, 1.8, 1.4, 2.3, 2.3, 2.3, 2.6], size=10)
        m_ = lambda v: f"{v:g}".replace("-", "−")
        r0, lo_, hi_ = rows[0]["RSSI (dBm)"], prep.rssi_min_train, prep.rssi_max_train
        R.para(f"Tổng utility của giao dịch: TU = {vn(tu['A_signal'], 0)} "
               f"(Model A), {vn(tu['B_discriminative'], 2)} (Model B), "
               f"{vn(tu['C_rare_discriminative'], 2)} (Model C). Kiểm tay AP "
               f"đầu tiên: q = 1 + ({m_(r0)} − ({m_(lo_)})) / ({m_(hi_)} − "
               f"({m_(lo_)})) × 99 = 1 + {m_(r0 - lo_)}/{m_(hi_ - lo_)} × 99 = "
               f"{vn(1 + (r0 - lo_) / (hi_ - lo_) * 99, 3)}, làm tròn được "
               f"{rows[0]['q(i,T)']}; u(i,T) của Model B = q × p(i) = "
               f"{rows[0]['q(i,T)']} × {rows[0]['p(i) Model B']} = "
               f"{rows[0]['u(i,T) Model B']}.")

    R.h(2, "3.2. Ba cách định nghĩa ‘lợi nhuận đơn vị’ p(i)")
    R.para("Ba mô hình dùng chung q(i,T) và chỉ khác p(i), để mọi khác biệt về "
           "kết quả chỉ đến từ p(i):")
    R.para([("Model A — tín hiệu (đối chứng): ", "b"), ("p(i) = 1.", "")])
    R.para([("Model B — phân biệt vị trí: ", "b"),
            ("p(i) tỉ lệ với thông tin tương hỗ giữa trạng thái của AP và nhãn "
             f"vị trí Y {rf.c('shannon1948')}, cùng tinh thần chọn AP theo "
             f"lượng thông tin {rf.c('chen2006')}:", "")])
    R.eq(r"p(i)=\frac{\max\left(I(A_i;Y),\,10^{-6}\right)}{\max_j I(A_j;Y)},"
         r"\qquad I(A;Y)=\sum_{a}\sum_{y}P(a,y)\log_2\frac{P(a,y)}{P(a)P(y)}")
    R.para("trong đó trạng thái A_i gồm 6 mức: không phát hiện và 5 khoảng RSSI "
           "(−104/−90/−80/−70/−60/0 dBm).")
    R.para([("Model C — hiếm và phân biệt: ", "b"),
            (f"nhân thêm hệ số IDF {rf.c('sparck1972')} để giảm trọng số AP ‘ở "
             "đâu cũng thấy’:", "")])
    R.eq(r"p(i)\propto I(A_i;Y)\cdot\log\frac{N}{1+\mathrm{support}_i}")
    rows = []
    for k in K:
        d = M.diag[k]
        b = d["B_discriminative"]
        top = b.get("top10_waps_by_mi", [])[:3]
        rows.append({"Bộ dữ liệu": M.name(k),
                     "Nhãn Y": "tòa_tầng" if M.by[k]["summary"]
                     ["n_building_floor_classes"] > 1 else "RP",
                     "RSSI min / max (train)": f"{M.by[k]['summary']['train']['rssi_min']:g}"
                                               f" / {M.by[k]['summary']['train']['rssi_max']:g}",
                     "H(Y) (bit)": vn(b["label_entropy_H_Y_bits"], 3),
                     "max I(A;Y) (bit)": vn(b["mi_bits_max"], 3),
                     "3 AP có I lớn nhất": ", ".join(
                         t["wap"].replace("WAP_", "") for t in top),
                     "Tổng utility A / B / C": " / ".join(
                         vi(d[m]["total_database_utility"]) for m in MODELS)})
    R.tbl(pd.DataFrame(rows), "Tham số của ba mô hình utility trên từng bộ "
          "(tính chỉ trên tập huấn luyện)",
          [2.6, 1.3, 2.1, 1.5, 1.7, 3.6, 3.6], size=9.5)
    R.para("Nói đơn giản: H(Y) là độ ‘bất định’ của vị trí khi chưa nghe AP "
           "nào; max I(A;Y) là lượng bất định mà AP tốt nhất một mình gỡ được. "
           "Với nhãn là RP (hàng trăm lớp), H(Y) lớn hơn nhiều so với nhãn tầng.")

    R.h(2, "3.3. Khai phá HUI bằng EFIM, lưới minUtil và ngân sách")
    R.para(f"EFIM {rf.c('zida2017')} được chọn vì là một trong các thuật toán "
           f"nhanh và tiết kiệm bộ nhớ nhất trong đánh giá độc lập "
           f"{rf.c('zhang2018')}. Nó duyệt cây tập mục theo thứ tự TWU tăng "
           "dần, cắt nhánh bằng hai cận trên (local utility và subtree "
           "utility), thu nhỏ cơ sở dữ liệu bằng phép chiếu và gộp giao dịch "
           "trùng nhau. Bản cài Python của dự án đã được đối chiếu với một bộ "
           "duyệt vét cạn trên dữ liệu ngẫu nhiên (bộ kiểm thử tests/). Trên mỗi "
           "bộ dữ liệu, cùng một quy trình như nghiên cứu được lặp lại:")
    R.numbered([
        "Chạy θ = 20%, 15%, 10%, 7,5%, 5%, 4%, 3,5%, 3%, 2,5%, 2%, 1,5%, 1% "
        "(giảm dần); dừng ở lần đầu tiên một lần chạy chạm ngân sách 600 giây "
        "hoặc 1.000.000 HUI (ghi trạng thái ABORTED, không xoá kết quả).",
        "Tinh chỉnh tối đa 3 lần: chia đôi (theo trung bình nhân) khoảng giữa "
        "ngưỡng hoàn tất thấp nhất và ngưỡng bị dừng cao nhất; nếu không lần "
        "nào bị dừng thì hạ tiếp θ/2 — chỉ khi tập HUI giàu nhất còn dưới "
        "20.000 HUI.",
        "Tập HUI ‘chính’ của mỗi mô hình là lần chạy HOÀN TẤT có θ thấp nhất "
        "(tập không bị cắt cụt, giàu thông tin nhất)."])

    R.h(2, "3.4. Từ HUI đến tập AP, và các đối chứng")
    R.para("Mỗi HUI chia đều utility của nó cho các AP thành viên; điểm của "
           "AP i là:")
    R.eq(r"\mathrm{contrib}(i)=\sum_{X\in\mathrm{HUIs},\;i\in X}\frac{u(X)}{|X|}")
    R.para("Hai quy tắc chọn: union — mọi AP xuất hiện trong ít nhất một HUI "
           "(chỉ phụ thuộc minUtil); top-n — n AP có contrib cao nhất. Để biết "
           "HUIM có thật sự giúp, mỗi tập HUIM được so với ba đối chứng có cùng "
           "số AP: n AP ngẫu nhiên (3 lần lấy mẫu), n AP được phát hiện nhiều "
           "nhất, n AP có I(A;Y) cao nhất. Đối chứng thứ ba khó nhất vì nó dùng "
           "chính thước đo của Model B nhưng không khai phá tập mục.")

    R.h(2, "3.5. Định vị bằng k-NN (PHASE I — mô hình của nghiên cứu)")
    R.para(f"Định vị bằng vân tay là tìm các vân tay huấn luyện ‘giống’ vân tay "
           f"cần định vị nhất {rf.c('bahl2000', 'khalaj2017')}. k-NN của nghiên "
           "cứu vừa bỏ phiếu lớp vị trí (tòa_tầng hoặc RP), vừa ước lượng toạ độ "
           "bằng trung bình có trọng số của k láng giềng:")
    R.eq(r"\hat{x}=\frac{\sum_{j=1}^{k}w_j\,x_j}{\sum_{j=1}^{k}w_j},\qquad "
         r"w_j\in\{1,\;1/d_j\}")
    R.para("k ∈ {1, 3, 5, 7, 9, 11}, khoảng cách Euclid hoặc Manhattan, trọng số "
           "đều hoặc nghịch đảo khoảng cách được chọn một lần trên một phần "
           "chia ngẫu nhiên 75/25 của tập huấn luyện (theo độ chính xác lớp vị "
           f"trí), rồi đóng băng cho mọi tập AP. Bảng {R._tab + 1} cho cấu "
           "hình chọn được ở từng bộ.")
    rows = []
    for k in K:
        c = M.by[k]["ips"]["frozen_knn_config"]
        rows.append({"Bộ dữ liệu": M.name(k), "k": c["n_neighbors"],
                     "Khoảng cách": c["metric"], "Trọng số": c["weights"],
                     "Độ chính xác lớp vị trí trên dev": pc(c["dev_joint_accuracy"])})
    R.tbl(pd.DataFrame(rows), "Cấu hình k-NN của nghiên cứu, chọn lại trên "
          "từng bộ", [3.4, 1.0, 2.4, 2.2, 4.5], size=10.5)

    R.h(2, f"3.6. Tối ưu sai số theo mét (PHASE I3 — quy trình đã cho {ms.M_SEL})")
    R.para("k-NN ở mục 3.5 được chọn để PHÂN LOẠI tầng, không phải để ước lượng "
           "toạ độ. Quy trình Version 2 tối ưu thẳng sai số theo mét qua năm "
           "bước nối tiếp, mỗi bước giữ cấu hình tốt nhất của bước trước:")
    R.numbered([
        [("S0 — ", "b"), ("k-NN của nghiên cứu dùng như bộ ước lượng toạ độ.", "")],
        [("S1 — biểu diễn × khoảng cách (k = 1): ", "b"),
         ("biểu diễn positive, powed hoặc exponential "
          f"{rf.c('torres2015')}; khoảng cách Euclid, Manhattan, Bray–Curtis "
          f"{rf.c('bray1957')} hoặc cosine.", "")],
        [("S2 — số láng giềng và trọng số: ", "b"),
         (f"k từ 1 đến 30, trọng số w = 1/d^p với p = 0…4 {rf.c('shepard1968')}.", "")],
        [("S3 — dò lệch thiết bị: ", "b"),
         ("cộng δ dB vào mọi RSSI phát hiện được của vân tay cần định vị "
          "(δ ∈ ±3, ±6, ±9 dB) và giữ mức δ mà láng giềng gần nhất ở gần nhất; "
          "chỉ dùng tín hiệu của chính vân tay đó, không dùng vị trí hay nhãn.",
          "")],
        [("S4 — ghép hai biểu diễn: ", "b"),
         ("lấy trung bình toạ độ của mô hình tốt nhất với mô hình tốt nhất trên "
          "một biểu diễn thứ hai.", "")]])
    R.eq(r"\mathrm{powed}=\left(\frac{RSSI+105}{105}\right)^{e},\quad "
         r"\mathrm{exponential}=\frac{e^{(RSSI+105)/24}}{e^{105/24}},\quad "
         r"d_{BC}(a,b)=\frac{\sum_i|a_i-b_i|}{\sum_i|a_i+b_i|}")
    R.para("Mọi lựa chọn được đo bằng sai số trung bình trên 6 fold kiểm định "
           f"lấy từ tập huấn luyện (nhóm như Bảng {t_schema}); S3 và S4 chỉ được nhận nếu "
           "giảm sai số dev ít nhất 0,05 m. Tập kiểm tra chỉ được dùng một lần "
           "cho mỗi bước, sau khi đã chọn xong. Ngoài việc tối ưu lại trên từng "
           "bộ, báo cáo còn áp NGUYÊN XI cấu hình đã chọn trên UJIIndoorLoc "
           f"(cấu hình {ms.M_SEL}) lên từng bộ, để trả lời câu hỏi ‘dùng lại mô hình "
           "cũ có được không’.")

    R.h(2, "3.7. Thước đo")
    R.para("Độ chính xác tòa nhà và độ chính xác tầng được tính từ cùng một dự "
           "đoán tòa_tầng (đúng tầng nghĩa là đúng số tầng). Sai số vị trí của "
           "một vân tay:")
    R.eq(r"e=c\cdot\sqrt{(x-\hat{x})^2+(y-\hat{y})^2}")
    R.para("với c = 0,766126 trên UJIIndoorLoc (toạ độ Web Mercator, c = cos "
           "vĩ độ) và c = 1 trên các bộ còn lại (toạ độ đã tính bằng mét).")
    R.para(f"Thời gian định vị được đo bằng đồng hồ thực: định vị tối đa "
           f"{vi(TIMING_MAX_ROWS)} vân tay đầu của tập kiểm tra chính (bằng cỡ "
           "tập kiểm định của UJIIndoorLoc, để mọi bộ được đo trên cùng một cỡ "
           "lô; với k-NN vét cạn, chi phí mỗi vân tay không phụ thuộc cỡ lô), "
           "gồm cả dựng chỉ mục láng giềng, chạy khởi động một lần rồi lấy "
           f"trung vị của {TIMING_REPEATS} lần, dùng mọi lõi CPU, máy không "
           "chạy việc khác; kết quả quy ra mili-giây cho mỗi vân tay.")

    # ------------------------------------------------------------ 4 results
    R.h(1, "4. Kết quả")
    R.h(2, "4.1. Khai phá HUIM trên từng bộ dữ liệu")
    if real:
        p = ch_mining(M)
        R.para(f"Hình {R._fig + 1} cho số HUI theo ngưỡng minUtil. Hình dạng giống hệt "
               "UJIIndoorLoc: gần như không có HUI ở ngưỡng cao, rồi bùng nổ khi "
               "θ giảm qua một ‘vùng chuyển pha’ hẹp. Bộ có nhiều AP mỗi vân tay "
               "(HCXY) bùng nổ ở θ cao hơn hẳn.")
        R.fig(p, "Số HUI theo minUtil (% tổng utility) trên từng bộ và từng mô "
              "hình utility; dấu x là lần chạy dừng vì chạm ngân sách.", 16)
        f_mine = R._fig
        rows = []
        for k in real:
            H = M.runs[k]
            for m in MODELS:
                g = H[H["utility_model"] == m]
                c = g[(g["status"] == "COMPLETED") & (g["n_huis"] > 0)]
                if not len(c):
                    continue
                r = c.loc[c["rel_minutil_pct"].idxmin()]
                ab = g[g["status"] != "COMPLETED"]
                rows.append({"Bộ dữ liệu": M.name(k), "Model": LET[m],
                             "Số lần chạy": len(g),
                             "θ chính": mu(r["rel_minutil_pct"]) + "%",
                             "Số HUI": vi(r["n_huis"]),
                             "AP trong HUI": f"{int(r['unique_waps_in_huis'])}"
                                             f"/{int(r['n_wap_columns_total'])}",
                             "Thời gian EFIM (s)": vn(r["runtime_s"], 2),
                             "Dừng ở θ": ", ".join(mu(v) + "%" for v in
                                                   ab["rel_minutil_pct"]) or "—"})
        R.tbl(pd.DataFrame(rows), "Tập HUI chính của mỗi mô hình (lần chạy "
              "hoàn tất có θ thấp nhất); toàn bộ các lần chạy ở Phụ lục A",
              [3.0, 1.1, 1.4, 1.4, 1.8, 1.8, 2.0, 3.2], size=10)

    R.h(2, "4.2. Độ chính xác tòa nhà, tầng và sai số mét")
    R.para(f"Bảng {R._tab + 1} là kết quả chính: với mỗi tập kiểm tra, ba mô "
           f"hình dùng mọi AP — k-NN của nghiên cứu (S0), cấu hình {ms.M_SEL} của "
           "UJIIndoorLoc áp nguyên xi, và mô hình tối ưu lại trên chính bộ đó. "
           f"Hình {R._fig + 1} vẽ cùng số liệu.")
    allw = M.cmp[M.cmp["wap_set"] == "all"]
    rows = []
    for _, r in allw.iterrows():
        rows.append({"Bộ · tập test": f"{r['dataset_name']} · {r['test_set']}",
                     "Mô hình": r["method"].replace("Tối ưu PHASE I3",
                                                    "Tối ưu lại"),
                     "Tòa": acc(r["building_accuracy"], r["n_buildings"]),
                     "Tầng": acc(r["floor_accuracy"], r["n_floor_classes"]),
                     "Sai số TB (m)": vn(r["mean_err_m"]),
                     "Trung vị (m)": vn(r["median_err_m"]),
                     "P90 (m)": vn(r["p90_err_m"]),
                     "ms / vân tay": "" if pd.isna(r["ms_per_fp"])
                     else vn(r["ms_per_fp"], 3)})
    R.tbl(pd.DataFrame(rows), "Độ chính xác và sai số trên mọi tập kiểm tra "
          "(mọi AP); ‘—’ = bộ chỉ có một tòa / một tầng",
          [3.9, 3.8, 1.4, 1.4, 1.5, 1.5, 1.3, 1.6], size=9.5)
    t_main = R._tab
    R.fig(FIG / "fig40_multi_dataset_comparison.png",
          "Sai số trung bình, tỉ lệ đoán sai tầng và thời gian định vị: k-NN "
          "của nghiên cứu (xám), cấu hình UJIIndoorLoc áp nguyên (cam) và mô "
          f"hình tối ưu lại (xanh). Số liệu ở Bảng {t_main}.", 16.5)
    best_transfer = [(k, t) for k in real for t in M.tests(k)
                     if M.row(k, t, ms.TRANSFER)["mean_err_m"]
                     <= final_row(k, t)["mean_err_m"]]
    R.para(f"Mô hình tối ưu lại có sai số trung bình thấp hơn k-NN của nghiên "
           f"cứu ở {len(better)}/{n_tests} tập kiểm tra. Cấu hình UJIIndoorLoc "
           f"áp nguyên xi bằng hoặc tốt hơn mô hình tối ưu lại ở "
           f"{len(best_transfer)}/{n_tests} tập"
           + (" (trên chính UJIIndoorLoc hai mô hình là một)" if "uji" in K
              else "")
           + (" — nghĩa là quy trình chọn mới là thứ tổng quát hoá được, còn "
              "bản thân các siêu tham số thì phụ thuộc bộ dữ liệu."
              if len(best_transfer) * 2 <= n_tests else
              " — cấu hình của UJIIndoorLoc tổng quát hoá khá tốt sang các bộ "
              "khác."))
    transfer_ok = len(best_transfer) * 2 > n_tests

    R.h(2, "4.3. Mô hình được chọn ở từng bộ")
    rows = []
    for k in K:
        A = M.abl(k)
        for t in M.tests(k):
            for _, r in A[A["test_set"] == t].iterrows():
                rows.append({"Bộ · test": f"{M.name(k)} · {t}",
                             "Bước": r["stage"], "Cấu hình": r["config"],
                             "Dev TB (m)": vn(r["dev_mean_ground_m"]),
                             "Test TB (m)": vn(r["test_mean_err_m"]),
                             "Test trung vị (m)": vn(r["test_median_err_m"]),
                             "Tầng (test)": acc(r["test_floor_accuracy"],
                                                M.by[k]["summary"]
                                                ["n_building_floor_classes"])})
    R.para(f"Bảng {R._tab + 1} cho các bước S0 → S4 được giữ lại trên từng bộ, sai số trên "
           "fold kiểm định (dùng để CHỌN) và trên tập kiểm tra (chỉ để BÁO "
           "CÁO). Các bước không có trong bảng là các bước không đạt ngưỡng "
           "cải thiện 0,05 m trên dev nên bị bỏ.")
    R.tbl(pd.DataFrame(rows), "Các bước tối ưu được giữ lại: sai số dev "
          "(chọn) và test (báo cáo)",
          [3.6, 1.0, 5.4, 1.5, 1.5, 1.6, 1.6], size=9)
    if rep:
        p1 = M.phase1
        p1_txt = (f" Ở PHASE I, {p1['n_identical']}/{p1['n_study']} điều kiện "
                  "chọn AP cho cùng độ chính xác và cùng sai số với nghiên cứu "
                  "gốc." if p1 else "")
        if rep["match"]:
            rep_txt = (f"Chạy lại qua đường code chung, quy trình chọn đúng cấu "
                       f"hình ‘{rep['study_selected_label']}’ và cho "
                       f"{vn(rep['generic_mean_ground_m'], 4)} m, độ chính xác "
                       f"tòa–tầng {pc(rep['generic_joint_accuracy'])} — trùng "
                       f"nghiên cứu gốc ({vn(rep['study_mean_ground_m'], 4)} m, "
                       f"{pc(rep['study_joint_accuracy'])}).")
        else:
            rep_txt = (f"Chạy lại qua đường code chung cho "
                       f"{vn(rep['generic_mean_ground_m'], 4)} m so với "
                       f"{vn(rep['study_mean_ground_m'], 4)} m của nghiên cứu "
                       "gốc — KHÔNG trùng.")
        R.para([("Kiểm tra tái lập trên UJIIndoorLoc. ", "b"),
                (rep_txt + p1_txt, "")])
        R.para([("Lưu ý khi tự chạy lại. ", "b"),
                ("Ở bước tối ưu, nhiều cặp vân tay có khoảng cách đúng bằng "
                 "nhau (RSSI là số nguyên), và hai cấu hình ứng viên có thể chỉ "
                 "hơn kém nhau vài phần vạn mét trên dev. Khi giới hạn số luồng "
                 "CPU, thư viện tính khoảng cách cộng các số theo thứ tự khác, "
                 "sai khác ở chữ số rất nhỏ đủ đổi thứ tự láng giềng và lật lựa "
                 "chọn. Mọi kết quả trong báo cáo được chạy với cấu hình luồng "
                 "mặc định của máy, như nghiên cứu gốc; người tự chạy lại cần "
                 "giữ nguyên điều đó.", "")])

    R.h(2, "4.4. Phân bố sai số")
    C = cdf_rows(M)
    p = ch_cdf(M, C)
    R.fig(p, "Hàm phân phối tích luỹ của sai số trên từng tập kiểm tra: đường "
          "càng dịch sang trái càng tốt.", 16.5)
    f_cdf = R._fig
    C2 = C.copy()
    C2["Bộ · test"] = C2["dataset"] + " · " + C2["test_set"]
    C2 = C2[["Bộ · test", "model", "p25_m", "p50_m", "p75_m", "p90_m", "p95_m",
             "share_le_2m", "share_le_5m"]]
    for c in ("p25_m", "p50_m", "p75_m", "p90_m", "p95_m"):
        C2[c] = C2[c].map(lambda v: vn(v))
    for c in ("share_le_2m", "share_le_5m"):
        C2[c] = C2[c].map(lambda v: pc(v, 1))
    C2.columns = ["Bộ · test", "Mô hình", "P25", "P50", "P75", "P90", "P95",
                  "≤ 2 m", "≤ 5 m"]
    R.tbl(C2, f"Số liệu của Hình {f_cdf}: phân vị sai số (m) và tỉ lệ vân tay có sai "
          "số ≤ 2 m, ≤ 5 m", [3.8, 3.0, 1.2, 1.2, 1.2, 1.2, 1.2, 1.4, 1.4],
          size=9.5)

    R.h(2, "4.5. HUIM có chọn AP tốt hơn đối chứng?")
    R.fig(FIG / "fig41_multi_dataset_huim_vs_controls.png",
          "Sai số của mô hình tối ưu trên tập AP do HUIM chọn (union, tập tốt "
          "nhất của mỗi mô hình) so với top-n theo MI và theo tần suất phát "
          "hiện cùng số AP; vạch đen = dùng mọi AP. Tập test chính của mỗi "
          "bộ.", 15)
    f_hv = R._fig
    H = M.hv[M.hv["dataset"] != "hus"].copy()
    rows = []
    win = 0
    for _, r in H.iterrows():
        bestc = np.nanmin([r["opt_mean_err_top_mi_m"],
                           r["opt_mean_err_top_support_m"]])
        w = r["opt_mean_err_huim_m"] < bestc - 1e-9
        win += bool(w)
        rows.append({"Bộ · test": f"{r['dataset_name']} · {r['test_set']}",
                     "Tập AP": f"{r['utility_model']} "
                               f"{'union' if r['family'] == 'huim_union' else 'top-n'}"
                               f", θ={mu(r['minutil_pct'])}%",
                     "Số AP": int(r["n_waps"]),
                     "HUIM (m)": vn(r["opt_mean_err_huim_m"]),
                     "Top-MI (m)": vn(r["opt_mean_err_top_mi_m"]),
                     "Top-support (m)": vn(r["opt_mean_err_top_support_m"]),
                     "Mọi AP (m)": vn(r["opt_mean_err_all_waps_m"]),
                     "HUIM tốt nhất?": "có" if w else "không"})
    R.tbl(pd.DataFrame(rows), f"Số liệu của Hình {f_hv} (thêm cả tập top-n tốt nhất "
          "của mỗi mô hình): sai số TB của mô hình tối ưu",
          [3.6, 3.6, 1.2, 1.6, 1.6, 1.9, 1.6, 1.6], size=9)
    huim_wins = win * 2 > len(H)
    R.para(f"Trên {len(H)} tập AP do HUIM chọn, {win} tập có sai số thấp hơn "
           "hẳn cả hai đối chứng cùng số AP. "
           + ("Kết luận của nghiên cứu gốc vì vậy vẫn đứng vững trên dữ liệu "
              "mới: HUIM tìm ra những nhóm AP ‘mạnh và hay xuất hiện cùng "
              "nhau’, nhưng điều đó không làm chúng thành đặc trưng định vị "
              "tốt hơn các tiêu chí chọn đơn giản." if not huim_wins else
              "Trên dữ liệu mới HUIM thắng đối chứng ở đa số trường hợp — "
              "khác với kết luận trên UJIIndoorLoc."))
    if len(M.cv):
        R.fig(FIG / "fig42_multi_dataset_error_vs_waps.png",
              "Sai số của mô hình tối ưu theo số AP giữ lại: HUIM Model B "
              "(top-n) so với các đối chứng; đường chấm = dùng mọi AP.", 16)
        f_cv = R._fig
        cv = M.cv[M.cv["dataset"] != "hus"]
        rows = []
        for k in dict.fromkeys(cv["dataset"]):
            g = cv[cv["dataset"] == k]
            lim = ms.CURVE_TOL * g["all_waps_mean_err_m"].iloc[0]
            r = {"Bộ · test": f"{g['dataset_name'].iloc[0]} · {g['test_set'].iloc[0]}",
                 "Mọi AP": f"{g['n_wap_columns'].iloc[0]} AP: "
                           f"{vn(g['all_waps_mean_err_m'].iloc[0])} m"}
            for ser, lab in (("HUIM A", "HUIM A"), ("HUIM B", "HUIM B"),
                             ("HUIM C", "HUIM C"), ("control_top_mi", "Top-MI"),
                             ("control_top_support", "Top-support"),
                             ("control_random", "Ngẫu nhiên")):
                h = g[(g["series"] == ser) & (g["opt_mean_err_m"] <= lim)]
                r[lab] = ("không đạt" if not len(h) else
                          f"{int(h['budget_n'].min())} AP")
            rows.append(r)
        R.tbl(pd.DataFrame(rows), f"Số AP nhỏ nhất (trong các mức đã thử) mà sai "
              f"số không vượt {vn(ms.CURVE_TOL, 1)} × sai số khi dùng mọi AP; "
              f"số liệu đầy đủ của Hình {f_cv} ở Phụ lục B",
              [3.6, 2.6, 1.5, 1.5, 1.5, 1.5, 1.8, 1.7], size=9.5)

    R.h(2, "4.6. Thời gian")
    rows = []
    for k in real:
        t = M.by[k]["timing"]
        if t is None:
            continue
        for _, r in t.iterrows():
            lab = set_label(r["condition"])
            rows.append({"Bộ · test": f"{M.name(k)} · {r['test_set']}",
                         "Tập AP": lab, "Số AP": int(r["n_waps"]),
                         "k-NN nghiên cứu (ms/vân tay)": vn(r["study_ms_per_fp"], 3),
                         "Mô hình tối ưu (ms/vân tay)": vn(r["opt_ms_per_fp"], 3),
                         "Bộ nhớ CSDL (MB)": vn(r["db_memory_mb"], 2),
                         "Khai phá EFIM (s)": "" if pd.isna(r["huim_runtime_s"])
                         else vn(r["huim_runtime_s"], 2)})
    if rows:
        R.tbl(pd.DataFrame(rows), f"Thời gian định vị (trung vị {TIMING_REPEATS} "
              f"lần, tối đa {vi(TIMING_MAX_ROWS)} vân tay của tập kiểm tra chính) "
              "và thời gian khai phá của tập HUI tương ứng",
              [3.4, 4.6, 1.2, 2.2, 2.2, 1.6, 1.8], size=9)
        R.para("Mô hình tối ưu chậm hơn k-NN của nghiên cứu vì nó dò lệch thiết "
               "bị (thử nhiều mức δ) và chạy hai biểu diễn khi ghép mô hình. "
               "Bớt AP làm giảm bộ nhớ cơ sở dữ liệu vân tay tỉ lệ thuận với số "
               "AP, còn thời gian định vị giảm ít hơn vì chi phí còn nằm ở số "
               "vân tay huấn luyện. Thời gian khai phá EFIM chỉ phải trả một lần "
               "khi xây dựng hệ thống.")

    # ------------------------------------------------------------ 5 discussion
    R.h(1, "5. Thảo luận")
    pts = []
    if "uji_lib3" in K:
        a, b2 = final_row("uji_lib3", "Test-01"), final_row("uji_lib3", "Test-02")
        pts.append(f"Trong cùng một bộ dữ liệu, vị trí kiểm tra đã khảo sát hay "
                   f"chưa quyết định độ khó. Trên UJI_LIB, Test-01 (đo lại đúng "
                   f"vị trí huấn luyện) có sai số {vn(a['mean_err_m'])} m còn "
                   f"Test-02 (vị trí mới) có {vn(b2['mean_err_m'])} m với cùng "
                   "một mô hình: k-NN ước lượng vị trí bằng trung bình các vị "
                   "trí đã khảo sát, nên khi điểm cần định vị nằm giữa các điểm "
                   "khảo sát, sai số bị chặn dưới bởi mật độ lưới khảo sát. So "
                   "giữa các bộ thì không có quy luật đơn giản như vậy: HCXY "
                   "toàn vị trí mới nhưng lưới RP dày nên sai số vẫn nhỏ.")
        s2 = s0_row("uji_lib3", "Test-02")
        t2 = M.row("uji_lib3", "Test-02", ms.TRANSFER)
        if b2["mean_err_m"] > s2["mean_err_m"]:
            n_worse = n_tests - len(better)
            pts.append(f"{'Ngoại lệ duy nhất' if n_worse == 1 else 'Một ngoại lệ'}"
                       f" cần nói rõ: trên UJI_LIB Test-02, mô "
                       f"hình tối ưu lại ({vn(b2['mean_err_m'])} m) kém k-NN của "
                       f"nghiên cứu ({vn(s2['mean_err_m'])} m) và kém cả cấu hình "
                       f"UJIIndoorLoc áp nguyên ({vn(t2['mean_err_m'])} m). Lý "
                       "do: fold kiểm định của UJI_LIB được nhóm theo tháng, mô "
                       "phỏng đúng Test-01 (vị trí cũ, thời điểm khác) nhưng không "
                       "mô phỏng tình huống vị trí chưa khảo sát của Test-02; "
                       "quy trình chọn vì vậy ưu tiên cấu hình "
                       f"‘{M.by['uji_lib3']['pos']['selected_label']}’, có lợi "
                       "khi gặp lại vị trí cũ nhưng nội suy giữa các vị trí kém "
                       "hơn. Đây là giới hạn của cách chia fold, "
                       "không phải của dữ liệu; kết quả được giữ nguyên, không "
                       "chọn lại theo tập kiểm tra.")
    if "hus" in K and "hus_dedup" in K:
        a = final_row("hus", "testcase1")
        b2 = final_row("hus_dedup", "testcase1")
        pts.append(f"Rò rỉ dữ liệu làm đẹp kết quả rất mạnh. Cùng mô hình, HUS "
                   f"testcase1 cho {vn(a['mean_err_m'])} m khi tập kiểm tra còn "
                   f"bản sao trong tập huấn luyện và {vn(b2['mean_err_m'])} m "
                   "khi bỏ bản sao. Một con số đẹp bất thường cần được kiểm tra "
                   "rò rỉ trước khi tin.")
    if "dlulib" in K:
        a, s0 = final_row("dlulib", "Testing"), s0_row("dlulib", "Testing")
        pts.append(f"Định vị tầng là bài toán dễ khi các tầng có AP ‘riêng’: "
                   f"DLULIB đạt {pc(a['floor_accuracy'])} đúng tầng chỉ với "
                   f"{M.by['dlulib']['summary']['n_wap_columns']} AP (k-NN gốc "
                   f"{pc(s0['floor_accuracy'])}).")
    if "uji" in K and final_row("uji", "validationData")["mean_err_m"] >= max(
            final_row(k, t)["mean_err_m"] for k in real for t in M.tests(k)):
        a = final_row("uji", "validationData")
        pts.append(f"UJIIndoorLoc vẫn là bộ khó nhất về sai số mét "
                   f"({vn(a['mean_err_m'])} m) vì tập kiểm định do người khác "
                   "đo, bằng điện thoại khác, sau bốn tháng, ở các vị trí "
                   "không có trong tập huấn luyện.")
    pts.append("Giới hạn: đơn vị toạ độ của HCXY và HUS không được tài liệu hoá "
               "(đọc là mét); cách nhóm fold cho UJI_LIB (theo tháng) mô phỏng "
               "Test-01 tốt hơn Test-02; thời gian khai phá EFIM được đo khi máy "
               "chạy song song nhiều việc nên chỉ so sánh tốt bên trong một bộ "
               "dữ liệu; ba thư mục dữ liệu rỗng chưa được đánh giá.")
    for t in pts:
        R.para(t)

    # ------------------------------------------------------------ 6 conclusion
    R.h(1, "6. Kết luận")
    concl = [
        f"Phương pháp chạy được trên {len(real)} bộ dữ liệu khác nhau về quy mô "
        f"({M.ap_range[0]} đến {M.ap_range[1]} AP), số tầng ({M.cls_range[0]} "
        f"đến {M.cls_range[1]} tổ hợp tòa–tầng) và cách thu thập, "
        "mà không phải sửa thuật toán; chỉ các quyết định do dữ liệu buộc phải "
        "có được ghi riêng.",
        f"Quy trình tối ưu sai số theo mét giảm sai số so với k-NN gốc ở "
        f"{len(better)}/{n_tests} tập kiểm tra; "
        + ("cái tổng quát hoá được là QUY TRÌNH CHỌN trên fold kiểm định, "
           "không phải bộ siêu tham số của UJIIndoorLoc." if not transfer_ok
           else "cấu hình của UJIIndoorLoc cũng dùng lại được khá tốt."),
        ("Tập AP do HUIM chọn không vượt các đối chứng đơn giản cùng số AP — "
         "kết luận của nghiên cứu gốc được lặp lại trên dữ liệu mới."
         if not huim_wins else
         "Tập AP do HUIM chọn vượt các đối chứng cùng số AP ở đa số trường "
         "hợp — khác kết luận trên UJIIndoorLoc, cần kiểm tra thêm."),
        "Kiểm tra dữ liệu là một phần của phương pháp: phát hiện tập kiểm tra "
        "của HUS bị chép từ tập huấn luyện đã đổi hẳn cách đọc kết quả của bộ "
        "này."]
    R.numbered(concl)

    # ------------------------------------------------------------ appendices
    R.h(1, "Phụ lục A. Toàn bộ các lần chạy EFIM")
    rows = []
    for k in K:
        if k == "hus":
            continue
        for _, r in M.runs[k].sort_values(["utility_model", "rel_minutil_pct"],
                                          ascending=[True, False]).iterrows():
            rows.append({"Bộ": M.name(k), "Model": LET[r["utility_model"]],
                         "θ (%)": mu(r["rel_minutil_pct"]),
                         "Trạng thái": "hoàn tất" if r["status"] == "COMPLETED"
                         else "dừng (ngân sách)",
                         "Số HUI": vi(r["n_huis"]),
                         "AP trong HUI": int(r["unique_waps_in_huis"]),
                         "Thời gian (s)": vn(r["runtime_s"], 2)})
    R.tbl(pd.DataFrame(rows), f"Số liệu đầy đủ của Hình {f_mine}",
          [3.4, 1.3, 1.5, 2.8, 2.2, 2.0, 2.2], size=9)
    if len(M.cv):
        R.h(1, "Phụ lục B. Sai số theo số AP")
        cv = M.cv[M.cv["dataset"] != "hus"].copy()
        cv["series"] = cv["series"].map(lambda s: {
            "control_top_mi": "Top-MI", "control_top_support": "Top-support",
            "control_random": "Ngẫu nhiên (TB 3 seed)"}.get(s, s))
        piv = cv.pivot_table(index=["dataset_name", "budget_n"],
                             columns="series", values="opt_mean_err_m").reset_index()
        piv = piv.map(lambda v: ("—" if pd.isna(v) else vn(v))
                      if isinstance(v, float) else v)
        piv = piv.rename(columns={"dataset_name": "Bộ", "budget_n": "Số AP"})
        R.tbl(piv, f"Số liệu đầy đủ của Hình {f_cv}: sai số TB (m) của mô hình tối ưu",
              [3.2, 1.3] + [1.8] * (len(piv.columns) - 2), size=9)

    R.h(1, "Phụ lục C. Tự kiểm chứng các con số")
    kit = M.kit
    R.para("Mọi con số của báo cáo có thể kiểm lại theo ba cách, không cần tin "
           "mã thực nghiệm:")
    R.numbered([
        "Mở verification/kiem_chung_da_dataset.xlsx: mỗi sheet là một tập kiểm "
        "tra × mô hình, mỗi dòng là một vân tay với công thức Excel tính đúng "
        "tòa, đúng tầng, sai số, và dựng lại (x, y) từ láng giềng và trọng số. "
        + (f"Excel tính lại được {kit['ok']} phép kiểm tra KHỚP, "
           f"{kit['bad']} phép LỆCH." if kit else ""),
        "File dự đoán theo từng dòng: results/multi_dataset/<bộ>/predictions/"
        "<tập test>__{study_knn,optimised}.csv (dòng nguồn, toạ độ thật, toạ độ "
        "dự đoán, láng giềng, trọng số).",
        "Chạy lại: python src/run_multi_dataset.py --dataset <bộ> --stage all; "
        "python src/make_multi_dataset_summary.py; python "
        "src/make_multi_dataset_kit.py; python "
        "src/make_multi_dataset_report_docx.py."])

    # ------------------------------------------------------------ references
    R.h(1, "Tài liệu tham khảo")
    for i, k in enumerate(rf.order, 1):
        R.para(f"[{i}] {rf.entry[k]}", align="left")
    return R


def main() -> None:
    M = MD()
    R = build(M)
    info = R.save(OUT)
    hr.word_finish(OUT)
    LOG.info("saved %s: %d tables, %d figures", info["path"], info["n_tables"],
             info["n_figures"])
    print("OK", info["path"], f"({info['n_tables']} tables, "
                              f"{info['n_figures']} figures)")


if __name__ == "__main__":
    main()
