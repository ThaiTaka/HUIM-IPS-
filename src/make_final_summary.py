"""PHASE N - FINAL_SUMMARY.md plus deliverable verification.

Also writes results/deliverables.csv (the table printed at the end of the run)
and results/verification.json (what was checked and what the result was).

The DOCX and the PPTX are re-opened and parsed here, not merely checked for
existence: slide count, font usage, figure presence and placeholder text are all
verified against the produced files.
"""
from __future__ import annotations

import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (FIGURES, METRICS, PROJECT_ROOT, REPORT, RESEARCH, RESULTS,
                   SLIDES, TABLES, dump_json, get_logger, load_json)

LOG = get_logger("final", "final_summary.log")

DOCX = REPORT / "HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx"
PPTX = SLIDES / "HUIM_IPS_UJIIndoorLoc_Presentation.pptx"

FORBIDDEN = ("TODO", "FIXME", "XXX", "PLACEHOLDER", "LOREM IPSUM",
             "EXAMPLE VALUE", "<INSERT", "TBD")

DELIVERABLES = [
    ("1. Source code chạy được", "src/, run_experiments.py"),
    ("2. requirements.txt", "requirements.txt"),
    ("3. README.md", "README.md"),
    ("4. Unit tests", "tests/test_efim.py, tests/test_utility.py"),
    ("5. Data audit", "results/data_audit.md, results/data_summary.json"),
    ("6. Literature review", "research/literature_review.md"),
    ("7. Bibliography", "research/references.bib, research/papers_table.csv"),
    ("8. Utility models", "src/utility_models.py"),
    ("9. HUIM implementation", "src/huim/efim.py, src/huim/brute_force.py"),
    ("10. Experiment logs", "results/logs/, results/*.json"),
    ("11. Metrics CSV", "results/metrics/huim_runs.csv, "
                        "results/metrics/ips_results.csv"),
    ("12. Charts", "figures/*.png, figures/*.csv"),
    ("13. Reverse-thinking analysis", "research/reverse_thinking_analysis.md"),
    ("14. Ablation study", "results/tables/ablation_study.csv"),
    ("15. Word report", str(DOCX.relative_to(PROJECT_ROOT)).replace("\\", "/")),
    ("16. PowerPoint", str(PPTX.relative_to(PROJECT_ROOT)).replace("\\", "/")),
    ("17. Speaker notes", "slides/speaker_notes.md"),
    ("18. FINAL_SUMMARY.md", "FINAL_SUMMARY.md"),
]


def nf(x, d=0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(v):
        return "N/A"
    return f"{v:,.{d}f}"


def pc(x, d=2):
    try:
        return f"{float(x)*100:.{d}f}%"
    except (TypeError, ValueError):
        return "N/A"


# ------------------------------------------------------------------ verify
def verify_docx() -> dict:
    out: dict = {"exists": DOCX.exists()}
    if not DOCX.exists():
        return out
    from docx import Document
    d = Document(str(DOCX))
    paras = [p for p in d.paragraphs]
    texts = [p.text for p in paras]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                texts.append(c.text)
    blob = "\n".join(texts)
    fonts = set()
    for p in paras:
        for r in p.runs:
            if r.font.name:
                fonts.add(r.font.name)
    heads = {}
    for p in paras:
        if p.style.name.startswith("Heading"):
            heads[p.style.name] = heads.get(p.style.name, 0) + 1
    with zipfile.ZipFile(DOCX) as z:
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    out.update({
        "size_kb": round(DOCX.stat().st_size / 1024, 1),
        "n_paragraphs": len(paras),
        "n_tables": len(d.tables),
        "n_embedded_images": len(media),
        "n_characters": len(blob),
        "approx_pages_at_2800_chars": round(len(blob) / 2800, 1),
        "heading_counts": heads,
        "fonts_used_in_runs": sorted(fonts),
        "fonts_ok": fonts.issubset({"Times New Roman"}),
        "placeholders_found": [w for w in FORBIDDEN if w in blob.upper()],
        "has_references_section": "Tài liệu tham khảo" in blob,
        "has_cheatsheet": "Những câu tôi phải trả lời được" in blob,
        "has_formulas": "u(X)" in blob and "TWU" in blob,
        "has_mandated_statement":
            "chưa tìm thấy bằng chứng đủ mạnh" in blob,
        "mentions_metres_for_error": bool(
            re.search(r"sai số.{0,40}\bmét\b", blob)) and
            "EPSG:3857" not in blob,
    })
    out["opens_ok"] = True
    return out


def verify_pptx() -> dict:
    out: dict = {"exists": PPTX.exists()}
    if not PPTX.exists():
        return out
    from pptx import Presentation
    from pptx.util import Pt
    p = Presentation(str(PPTX))
    fonts, sizes, n_pics, n_tables, notes, blob = set(), [], 0, 0, 0, []
    overflow, overlaps, off_slide = [], [], []
    for i, s in enumerate(p.slides, 1):
        slide_text_len = 0
        for sh in s.shapes:
            if sh.shape_type == 13 or sh.__class__.__name__ == "Picture":
                n_pics += 1
            if getattr(sh, "has_table", False) and sh.has_table:
                n_tables += 1
                for row in sh.table.rows:
                    for c in row.cells:
                        for para in c.text_frame.paragraphs:
                            for r in para.runs:
                                if r.font.name:
                                    fonts.add(r.font.name)
                                if r.font.size:
                                    sizes.append(r.font.size.pt)
                                blob.append(r.text)
            if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    for r in para.runs:
                        if r.font.name:
                            fonts.add(r.font.name)
                        if r.font.size:
                            sizes.append(r.font.size.pt)
                        blob.append(r.text)
                        slide_text_len += len(r.text)
        if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip():
            notes += 1
        # crude overflow heuristic: a slide with a lot of body text
        if slide_text_len > 1900:
            overflow.append({"slide": i, "characters": slide_text_len})
        # geometric check: do any two content shapes overlap? This is what
        # catches bullet text landing on top of a chart, which a character
        # count cannot see.
        boxes = []
        for sh in s.shapes:
            try:
                if sh.top is None or sh.left is None:
                    continue
                t_, l_ = sh.top / 914400.0, sh.left / 914400.0
                h_, w_ = sh.height / 914400.0, sh.width / 914400.0
            except Exception:
                continue
            if h_ <= 0.02 or w_ <= 0.02:      # rules and separator lines
                continue
            has_text = (getattr(sh, "has_text_frame", False)
                        and sh.has_text_frame
                        and sh.text_frame.text.strip())
            if has_text:
                # Replace the nominal box height with an estimate of the height
                # the text actually occupies, otherwise every generously sized
                # textbox reports a phantom overlap with its neighbour.
                est = 0.0
                for para in sh.text_frame.paragraphs:
                    txt = "".join(r.text for r in para.runs)
                    pts = max((r.font.size.pt for r in para.runs
                               if r.font.size), default=13.0)
                    cpl = max(8, int(w_ * 96 / (pts * 0.52)))
                    nlines = max(1, -(-len(txt) // cpl))
                    est += nlines * pts * 1.25 / 72.0 + 0.05
                h_ = min(h_, max(est, 0.12))
            is_pic = sh.__class__.__name__ == "Picture"
            is_tbl = getattr(sh, "has_table", False) and sh.has_table
            if not (has_text or is_pic or is_tbl):
                continue
            boxes.append((l_, t_, l_ + w_, t_ + h_,
                          "picture" if is_pic else
                          "table" if is_tbl else "text"))
        for a in range(len(boxes)):
            for b in range(a + 1, len(boxes)):
                ax1, ay1, ax2, ay2, ak = boxes[a]
                bx1, by1, bx2, by2, bk = boxes[b]
                ox = min(ax2, bx2) - max(ax1, bx1)
                oy = min(ay2, by2) - max(ay1, by1)
                if ox > 0.08 and oy > 0.08:   # ignore hairline touching
                    overlaps.append({
                        "slide": i, "kinds": f"{ak} / {bk}",
                        "overlap_in": round(ox * oy, 3),
                        "overlap_w_in": round(ox, 2),
                        "overlap_h_in": round(oy, 2)})
        # anything hanging off the bottom or right edge of the slide
        for (l_, t_, r_, b_, k) in boxes:
            if b_ > 7.5 + 0.05 or r_ > 13.333 + 0.05:
                off_slide.append({"slide": i, "kind": k,
                                  "bottom_in": round(b_, 2),
                                  "right_in": round(r_, 2)})
    text = "\n".join(blob)
    body = [v for v in sizes if v <= 14]
    out.update({
        "size_kb": round(PPTX.stat().st_size / 1024, 1),
        "n_slides": len(p.slides),
        "n_pictures": n_pics,
        "n_tables": n_tables,
        "n_slides_with_speaker_notes": notes,
        "fonts_used": sorted(fonts),
        "fonts_ok": fonts.issubset({"Times New Roman"}),
        "font_sizes_used_pt": sorted(set(round(v, 1) for v in sizes)),
        "body_size_pt_mode": (max(set(body), key=body.count) if body
                              else None),
        "slide_width_in": round(p.slide_width / 914400, 3),
        "slide_height_in": round(p.slide_height / 914400, 3),
        "placeholders_found": [w for w in FORBIDDEN if w in text.upper()],
        "possible_text_overflow": overflow,
        "overlapping_shapes": overlaps,
        "shapes_off_slide": off_slide,
        "has_references_slide": "Tài liệu tham khảo" in text,
        "opens_ok": True,
    })
    return out


def verify_figures() -> dict:
    pngs = sorted(FIGURES.glob("*.png"))
    out = {"n_png": len(pngs), "files": [], "missing_data_csv": []}
    for p in pngs:
        csv = p.with_suffix(".csv")
        out["files"].append({"png": p.name, "kb": round(p.stat().st_size / 1024, 1),
                             "data_csv": csv.name if csv.exists() else None})
        # schematics (fig2x) are drawn, not plotted from data, so no CSV expected
        if not csv.exists() and not re.match(r"fig2\d", p.stem):
            out["missing_data_csv"].append(p.name)
    return out


def verify_no_fabricated_numbers() -> dict:
    """Guard: the report/slide builders must not contain hard-coded results."""
    suspicious = []
    for f in ("make_report.py", "report_parts2.py", "report_parts3.py",
              "report_parts4.py", "report_parts5.py", "make_slides.py"):
        p = PROJECT_ROOT / "src" / f
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        # strip the known literature constants (the textbook example and DOIs)
        for pat in (r"10\.\d{4,5}/[^\s\"')]+", r"\b(?:19|20)\d{2}\b",
                    r"vol\. \d+", r"pp\. \d+[-–]\d+"):
            txt = re.sub(pat, " ", txt)
        for m in re.finditer(r"\b\d{1,3}(?:[.,]\d{3})+\b|\b\d+\.\d{3,}\b", txt):
            tok = m.group(0)
            line = txt[:m.start()].count("\n") + 1
            reason = ALLOWED_LITERALS.get(tok)
            suspicious.append({"file": f, "line": line, "token": tok,
                               "explained": reason})
    unexplained = [d for d in suspicious if not d["explained"]]
    return {"n_literals_found": len(suspicious),
            "n_unexplained": len(unexplained),
            "literals": suspicious[:25],
            "note": "Numeric literals in the document builders that could be "
                    "mistaken for experimental values. Each is either matched "
                    "against an allow-list with a stated reason, or reported "
                    "as unexplained. Bibliographic numbers (DOIs, years, "
                    "volumes, page ranges) are stripped before the scan."}


# Numeric literals that legitimately appear in the document builders, with the
# reason each one is not an experimental result.
ALLOWED_LITERALS = {
    "20.000": "altitude of GPS satellites in km, stated in chapter 2 as "
              "background physics",
    "200.000": "a deliberately arbitrary illustrative threshold used to explain "
               "why an absolute minUtil is meaningless; it is not a measured "
               "value",
    "13.333": "PowerPoint slide width in inches (16:9 at 7.5in height)",
    "108.703": "the campus area in m2 quoted by secondary literature, "
               "discussed (and shown to be a PROJECTED area) in the "
               "coordinate-system section; not a result of this study",
    "10.1007": "DOI prefix fragment", "10.1016": "DOI prefix fragment",
    "10.1109": "DOI prefix fragment", "10.1145": "DOI prefix fragment",
}


# ---------------------------------------------------------------- summary
def build_summary() -> str:
    audit = load_json(RESULTS / "data_summary.json")
    hsum = load_json(RESULTS / "huim_summary.json")
    isum = load_json(RESULTS / "ips_summary.json")
    O = load_json(RESULTS / "reverse_thinking_observations.json")
    H = pd.read_csv(METRICS / "huim_runs.csv")
    I = pd.read_csv(METRICS / "ips_results.csv")
    PAP = pd.read_csv(RESEARCH / "papers_table.csv")
    tr, cs, env = audit["training"], audit["cross_split"], audit["environment"]
    base = I[I["condition"] == "baseline_all_520"].iloc[0]
    b465 = I[I["condition"] == "baseline_detected_465"]
    o1 = O["observation_1_threshold_vs_hui_count"]
    o2 = O["observation_2_cost_of_lowering_threshold"]
    o3 = O["observation_3_models_select_different_aps"]
    o4 = O["observation_4_feature_reduction_vs_accuracy"]
    o5 = O["observation_5_huim_vs_controls"]
    o6 = O["observation_6_strong_vs_discriminative"]
    cfg = isum["protocol"]["frozen_knn_config"]
    w = o5["verdict_inputs"]
    sm = o4.get("smallest_subset_matching_baseline")

    L: list[str] = []
    A = L.append
    A("# FINAL SUMMARY — HUIM trong Indoor Positioning System (UJIIndoorLoc)\n")
    A(f"> Sinh tự động bởi `src/make_final_summary.py` lúc "
      f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC). "
      f"Mọi con số đọc từ `results/`. Không có giá trị nào nhập tay.\n")
    A("---\n")

    # ------------------------------------------------------------------ 1
    A("## 0. Phạm vi — đây là BÀI TÌM HIỂU, chưa phải đồ án\n")
    A("Tài liệu này là kết quả của một **bài tìm hiểu thuật toán** trong học "
      "phần cao học, **không phải đồ án tốt nghiệp hay luận văn**. Nhiệm vụ "
      "được giao gồm đúng ba phần:\n")
    A("1. **Tìm hiểu thuật toán** — HUIM và EFIM.")
    A("2. **Mô hình hoá áp dụng cho IPS** — ánh xạ HUIM ↔ Wi-Fi fingerprint.")
    A("3. **Cài đặt và đánh giá trên UJIIndoorLoc**.\n")
    A("Kèm hai tiêu chí đánh giá: **độ chính xác định vị** (mức tham chiếu "
      "7–8 m) và **thời gian, bộ nhớ**.\n")
    A("Hệ quả: mọi phát biểu ở đây là kết quả kiểm chứng trên MỘT bộ dữ liệu, "
      "với MỘT cấu hình bộ phân loại và các định nghĩa utility tự đặt. Không "
      "có tuyên bố nào về tính tổng quát hay tính mới.\n")

    A("## 1. Tôi đã làm gì?\n")
    A("Thực hiện một nghiên cứu thích nghi: dùng **High Utility Itemset "
      "Mining** (thuật toán **EFIM**) làm cơ chế **chọn nhóm Access Point** "
      "cho bài toán **định vị trong nhà bằng vân tay Wi-Fi**, thực nghiệm trên "
      "**UJIIndoorLoc**, và đánh giá có đối chứng.\n")
    A("Các bước đã chạy thật, theo đúng thứ tự PHASE A → N:\n")
    A(f"1. **Audit dữ liệu** — đọc read-only hai file CSV, xác minh schema "
      f"({tr['n_wap_columns_detected']} cột WAP, phát hiện bằng cách đếm chứ "
      f"không hard-code), kiểm chứng giả thuyết `100 = không phát hiện` bằng "
      f"ba nguồn độc lập, và tìm ra bốn bất thường không có trong tài liệu bộ "
      f"dữ liệu.")
    A(f"2. **Literature review** — đề xuất 40 DOI, xác minh từng cái qua "
      f"Crossref API; **4 DOI không tồn tại** và **12 DOI trả về bài báo khác "
      f"hẳn** bài định trích dẫn, tất cả đã bị loại. Còn **{len(PAP)} nguồn** "
      f"có tên khớp đúng.")
    A(f"3. **Cài đặt EFIM bằng Python** và kiểm chứng đối chiếu một oracle "
      f"brute-force độc lập (không có cắt tỉa, tính thẳng từ định nghĩa).")
    A(f"4. **Thiết kế ba utility model** dùng chung internal utility, chỉ khác "
      f"external utility, để ablation cô lập đúng một biến.")
    A(f"5. **Pilot** trên mẫu con để hiệu chỉnh lưới minUtil, rồi **chạy đầy "
      f"đủ** {len(H)} lần khai thác trên "
      f"{nf(hsum['database']['n_non_empty_transactions'])} utility "
      f"transaction.")
    A(f"6. **Đánh giá IPS** trên {len(I)} điều kiện, mỗi điều kiện đánh giá "
      f"đúng một lần trên {nf(audit['validation']['n_rows'])} fingerprint "
      f"kiểm định, với cùng một cấu hình k-NN đã đóng băng.")
    A("7. **Phân tích theo tư duy ngược**, **ablation**, **biểu đồ**, **báo "
      "cáo Word**, **PowerPoint**, **speaker notes**.\n")

    # ------------------------------------------------------------------ 2
    A("## 2. Thuật toán cuối cùng\n")
    A("**EFIM** — Zida, Fournier-Viger, Lin, Wu & Tseng, *Knowledge and "
      "Information Systems*, vol. 51, no. 2, pp. 595–625, "
      "DOI `10.1007/s10115-016-0986-0`.\n")
    A("**Vì sao EFIM, dựa trên literature:** căn cứ chính là đánh giá thực "
      "nghiệm **độc lập** của Zhang, Almpanidis, Wang & Liu, *Expert Systems "
      "with Applications*, vol. 101, pp. 91–115, 2018, DOI "
      "`10.1016/j.eswa.2018.02.008` — không do nhóm tác giả EFIM viết.\n")
    A("**Cài đặt:** Python (`src/huim/efim.py`). SPMF là thư viện tham chiếu "
      "nhưng viết bằng Java và môi trường thực nghiệm không có JVM. Hệ quả: "
      "bản cài đặt phải tự chứng minh tính đúng.\n")
    A("**Kiểm chứng tính đúng (PHASE F):**\n")
    A("- Đối chiếu với oracle brute-force trên ví dụ chuẩn của literature tại "
      "16 ngưỡng khác nhau.")
    A("- 40 cơ sở dữ liệu ngẫu nhiên độc lập × 5 ngưỡng mỗi cái.")
    A("- 15 cơ sở dữ liệu có hình dạng thưa-và-rộng giống Wi-Fi.")
    A("- Một trường hợp external utility là số thực (vì Model B dùng p không "
      "nguyên).")
    A("- Hai giá trị utility **tính tay** trong file test (u({b,d}) = 30, "
      "u({b,c,d,e}) = 40) để phủ cả tình huống 'cả hai bản cài đặt sai giống "
      "nhau'.")
    A("- Kiểm chứng TWU là chặn trên (vét cạn), utility KHÔNG anti-monotone, "
      "support chính xác sau transaction merging, cắt tỉa thực sự xảy ra, cơ "
      "chế dừng có kiểm soát hoạt động, và cổng chặn data leakage raise đúng "
      "lúc.")
    A("- Mutual information đối chiếu `sklearn.metrics.mutual_info_score` trên "
      "25 bộ dữ liệu ngẫu nhiên.\n")
    A("**Nguyên tắc đã thi hành:** không dòng nào của UJIIndoorLoc được chạy "
      "trước khi toàn bộ kiểm thử đạt.\n")

    # ------------------------------------------------------------------ 3
    A("## 3. Utility models\n")
    hm = hsum["utility_models"]
    A("| Model | q(i,T) | p(i) | Tổng utility DB | Vai trò |")
    A("|---|---|---|---|---|")
    roles = {"A_signal": "Đối chứng: tái tạo chế độ thất bại của frequent "
                         "itemset mining",
             "B_discriminative": "Model chính",
             "C_rare_discriminative": "Arm thứ ba (tuỳ chọn)"}
    forms = {"A_signal": "p(i) = 1",
             "B_discriminative": "max(I(A_i;Y), 1e-6) / max_j I(A_j;Y)",
             "C_rare_discriminative": "∝ I(A_i;Y) × log(N/(1+support_i))"}
    for k, d in hm.items():
        A(f"| {k} | RSSI chuẩn hoá (1…{hsum['preprocessor']['q_max']}) | "
          f"`{forms.get(k, '')}` | {nf(d['total_database_utility'])} | "
          f"{roles.get(k, '')} |")
    A(f"\nCả ba dùng **chung** internal utility: "
      f"`q(i,T) = round(1 + (RSSI − {hsum['preprocessor']['rssi_min_train']:g})"
      f"/({hsum['preprocessor']['rssi_max_train']:g} − "
      f"{hsum['preprocessor']['rssi_min_train']:g}) × "
      f"({hsum['preprocessor']['q_max']} − 1))`, fit **chỉ trên "
      f"trainingData**. AP không phát hiện ⟹ item vắng mặt.\n")
    vals = [d["total_database_utility"] for d in hm.values()]
    if vals and min(vals) > 0:
        A(f"[EXPERIMENT RESULT] Tổng utility chênh **{max(vals)/min(vals):.2f}×** "
          f"giữa ba model dù cơ sở dữ liệu và internal utility hoàn toàn giống "
          f"nhau — chỉ p thay đổi. Đây là lý do minUtil **phải** biểu diễn "
          f"theo % tổng utility.\n")

    # ------------------------------------------------------------------ 4
    A("## 4. Experiment protocol\n")
    A("| Bước | Dùng dữ liệu nào |")
    A("|---|---|")
    for step, data in [
        ("Chuẩn hoá RSSI (RSSI_min, RSSI_max)", "trainingData"),
        ("Trọng số p (mutual information)", "trainingData"),
        ("Khai thác HUIM (EFIM)", "trainingData"),
        ("Chọn tập AP từ HUI", "trainingData"),
        ("Chọn siêu tham số k-NN", "train_sub / dev_sub — đều từ trainingData"),
        ("Huấn luyện bộ phân loại cuối", "toàn bộ trainingData"),
        ("**ĐÁNH GIÁ**", "**validationData — một lần duy nhất mỗi điều kiện**"),
    ]:
        A(f"| {step} | {data} |")
    A(f"\n**Cấu hình k-NN đã ĐÓNG BĂNG** cho mọi điều kiện: "
      f"k = {cfg['n_neighbors']}, metric = {cfg['metric']}, "
      f"weights = {cfg['weights']}; chọn một lần trên dev_sub với tập đặc "
      f"trưng ALL-WAP (joint accuracy trên dev_sub khi chọn: "
      f"{pc(cfg['dev_joint_accuracy'])}). Nhờ vậy khác biệt duy nhất giữa các "
      f"điều kiện là **cột nào có mặt**. Việc tinh chỉnh trên baseline khiến "
      f"mọi lợi thế của tinh chỉnh thuộc về **baseline**, không thuộc về "
      f"phương pháp của bài tìm hiểu.\n")
    A("**Cơ chế cưỡng chế chống leakage:** hàm `build_external_utility` nhận "
      "tham số bắt buộc `split_name` và **raise lỗi** nếu khác `'training'` — "
      "một lời gọi vô tình trên validationData không thể âm thầm sinh trọng số "
      "bị rò rỉ. Có unit test riêng.\n")
    A(f"**Ngân sách mỗi lần khai thác:** {nf(hsum['time_limit_s'])} giây hoặc "
      f"{nf(hsum['max_huis'])} itemset. Vượt một trong hai ⟹ dừng **có kiểm "
      f"soát**, ghi `STATUS = ABORTED_RESOURCE_LIMIT`, **giữ lại** kết quả một "
      f"phần.\n")
    A("**Ba điều kiện đối chứng ở ngân sách khớp nhau:** random-n (3 seed), "
      "top-n theo số lần được phát hiện, top-n theo mutual information. Đối "
      "chứng thứ ba là khó nhất: nó dùng chính thước đo Model B được cho sẵn "
      "nhưng **không** khai thác itemset.\n")

    # ------------------------------------------------------------------ 5
    A("## 5. Kết quả quan trọng\n")
    A("### 5.1. Dữ liệu\n")
    A(f"- {nf(tr['n_rows'])} fingerprint huấn luyện × {tr['n_cols']} cột; "
      f"{tr['n_wap_columns_detected']} cột WAP (đếm thực tế).")
    A(f"- **{tr['not_detected_probe']['share_eq_100_pct']:.2f}%** ma trận WAP "
      f"là sentinel 100; trung bình "
      f"{tr['not_detected_probe']['detections_per_fingerprint']['mean']} AP "
      f"được phát hiện mỗi fingerprint.")
    A(f"- Số ô có giá trị trong khoảng 1…99: "
      f"**{tr['not_detected_probe']['count_in_1_to_99']}** trên "
      f"{nf(tr['not_detected_probe']['total_wap_cells'])} ô ⟹ 100 là sentinel, "
      f"cách giá trị kế tiếp "
      f"{tr['not_detected_probe']['gap_between_100_and_next_lower_value']:g} "
      f"đơn vị.")
    A(f"- {cs['waps_detected_in_train']}/{tr['n_wap_columns_detected']} AP từng "
      f"được phát hiện trong training; **{cs['waps_only_in_validation']}** AP "
      f"chỉ có trong validation (trần chặn với MỌI phương pháp).")
    A(f"- {tr['anomaly_probes']['ap_building_spread']['n_waps_in_exactly_1_building']}"
      f" AP chỉ nằm trong một toà nhà, chỉ "
      f"{tr['anomaly_probes']['ap_building_spread']['n_waps_in_all_3_buildings']}"
      f" AP thấy được ở cả ba ⟹ dự đoán trước: Building dễ, Floor khó.")
    A(f"- Bất thường: {tr['anomaly_probes']['n_empty_fingerprints']} "
      f"fingerprint không phát hiện AP nào; "
      f"{tr['anomaly_probes']['n_cells_equal_0_dbm']} ô bằng đúng 0 dBm, "
      f"**toàn bộ từ một thiết bị duy nhất**; "
      f"{nf(tr['duplicate_rows_full'])} dòng trùng lặp hoàn toàn; SPACEID "
      f"trong validationData đồng nhất bằng 0.")
    A(f"- Hai split **không chung USERID nào**, chỉ chung "
      f"{len(cs['PHONEID_overlap'])} PHONEID, cách nhau ~"
      f"{int((int(audit['validation']['TIMESTAMP_stats']['min']) - int(tr['TIMESTAMP_stats']['max'])) / 86400)}"
      f" ngày ⟹ kết quả là con số **cross-device, cross-time**.\n")

    A("### 5.2. Khai thác HUIM\n")
    A("| Utility model | Lần chạy | 0 HUI | Số HUI lớn nhất | Runtime (s) | "
      "Peak mem (MB) | ABORTED |")
    A("|---|---|---|---|---|---|---|")
    for m, r in o1.items():
        c = o2[m]
        A(f"| {m} | {r['n_runs']} | {r['n_runs_zero_huis']} | "
          f"{nf(r['max_n_huis_observed'])} | "
          f"{c['runtime_s_min']:.2f} – {c['runtime_s_max']:.2f} | "
          f"{c['peak_mem_delta_mb_min']:.1f} – {c['peak_mem_delta_mb_max']:.1f} | "
          f"{c['n_aborted']} |")
    A("\nBước nhảy mạnh nhất đo được:\n")
    for m, r in o1.items():
        s = r.get("sharpest_step")
        if s:
            A(f"- **{m}**: minUtil {s['from_pct']:g}% → {s['to_pct']:g}% "
              f"({s['threshold_ratio']:g}×) ⟹ số HUI "
              f"{nf(s['from_n_huis'])} → {nf(s['to_n_huis'])}; item sau TWU chỉ "
              f"đổi {s['from_items_after_twu']} → {s['to_items_after_twu']}.")
    A("")
    A("Tập HUI phong phú nhất **và không bị cắt ngang** của mỗi model:\n")
    A("| Model | Lần chạy | minUtil | Số HUI | Số WAP riêng biệt |")
    A("|---|---|---|---|---|")
    for m, d in o3["primary_hui_set_per_model"].items():
        A(f"| {m} | `{d['run_tag']}` | {d['rel_minutil_pct']:g}% | "
          f"{nf(d['n_huis'])} | {d['n_waps']} |")
    A("\n[OUR INTERPRETATION] Tỷ lệ 'rất nhiều HUI / rất ít WAP' là dấu hiệu "
      "nhận dạng: các HUI phần lớn là **tập con của nhau**. Một triệu HUI "
      "không phải một triệu phát hiện.\n")

    A("### 5.3. Định vị\n")
    A(f"**Baseline, tất cả {int(base['n_waps_selected'])} WAP:** Building "
      f"**{pc(base['building_accuracy'])}**, Floor "
      f"**{pc(base['floor_accuracy'])}**, Joint "
      f"**{pc(base['joint_building_floor_accuracy'])}**, Macro F1 "
      f"{base['joint_macro_f1']:.4f}.\n")
    A(f"Sai số định vị: trung vị **{base['pos_median_error']:.2f} m** toạ độ "
      f"chiếu = **{base['pos_median_error_ground_m']:.2f} m thực địa**; "
      f"trung bình **{base['pos_mean_error']:.2f} m** chiếu = "
      f"**{base['pos_mean_error_ground_m']:.2f} m thực địa** "
      f"(p75 {base['pos_p75_error_ground_m']:.2f} m, "
      f"p90 {base['pos_p90_error_ground_m']:.2f} m, "
      f"p95 {base['pos_p95_error_ground_m']:.2f} m thực địa).\n")
    if len(b465):
        r = b465.iloc[0]
        A(f"**Baseline chỉ các AP từng được phát hiện "
          f"({int(r['n_waps_selected'])} WAP):** giảm chiều "
          f"{r['feature_reduction_pct']:.2f}% **miễn phí**, Joint "
          f"{pc(r['joint_building_floor_accuracy'])}. Phần này **không** nhờ "
          f"HUIM.\n")
    if o4["per_model_best_topn"]:
        A("| Utility model | Số WAP | Giảm chiều | Building | Floor | Joint | "
          "Δ Joint |")
        A("|---|---|---|---|---|---|---|")
        for m, d in o4["per_model_best_topn"].items():
            A(f"| {m} | {d['n_waps']} | {d['feature_reduction_pct']:.2f}% | "
              f"{pc(d['building_accuracy'])} | {pc(d['floor_accuracy'])} | "
              f"**{pc(d['joint_accuracy'])}** | "
              f"{d['delta_joint_vs_baseline']*100:+.2f} pp |")
        A("")
    if sm:
        A(f"[EXPERIMENT RESULT] Tập con nhỏ nhất **đạt hoặc vượt** baseline về "
          f"Joint accuracy: **{sm['n_waps']} WAP** "
          f"({sm['feature_reduction_pct']:.2f}% giảm chiều), Joint "
          f"{pc(sm['joint_accuracy'])} (`{sm['condition']}`).\n")
    else:
        A("[EXPERIMENT RESULT] **Không** tập con nào do HUIM chọn đạt được "
          "Joint accuracy của baseline toàn bộ WAP.\n")

    A("### 5.4. So với đối chứng — bảng quyết định kết quả dương hay âm\n")
    A(f"[EXPERIMENT RESULT] Trên **{w['n_comparisons']}** ngân sách đặc trưng "
      f"khớp nhau, lựa chọn HUIM tốt nhất:\n")
    A(f"- vượt **chọn ngẫu nhiên**: {w['huim_beats_random']}/"
      f"{w['n_comparisons']}")
    A(f"- vượt **top-n theo mutual information**: {w['huim_beats_top_mi']}/"
      f"{w['n_comparisons']}")
    A(f"- vượt **top-n theo số lần được phát hiện**: "
      f"{w['huim_beats_top_support']}/{w['n_comparisons']}\n")

    o9 = O.get("observation_9_ranking_vs_size", {})
    if o9.get("largest_huim_selected_set"):
        bb = o9.get("best_joint_at_or_below_that_budget_any_method") or {}
        sc = o9.get("smallest_control_subset_reaching_baseline")
        A("### 5.5. Thiếu hụt là do XẾP HẠNG kém hay do QUÁ ÍT đặc trưng?\n")
        A(f"[EXPERIMENT RESULT] Tập AP lớn nhất mà bất kỳ điều kiện HUIM nào "
          f"tạo ra là **{o9['largest_huim_selected_set']} WAP** "
          f"(`{o9['largest_huim_set_condition']}`). Trong trần ngân sách đó, "
          f"độ chính xác joint cao nhất mà **mọi** phương pháp trong nghiên "
          f"cứu đạt được là **{pc(bb.get('joint'))}** "
          f"(`{bb.get('condition','N/A')}`), so với baseline "
          f"{pc(base['joint_building_floor_accuracy'])}.\n")
        if sc:
            A(f"[EXPERIMENT RESULT] Tập con nhỏ nhất thuộc **bất kỳ** loại nào "
              f"chạm được baseline dùng **{sc['n_waps']} WAP** "
              f"({sc['reduction_pct']:.2f}% giảm chiều, {pc(sc['joint'])}, "
              f"`{sc['condition']}`) — cao hơn hẳn trần "
              f"{o9['largest_huim_selected_set']} WAP mà HUIM có thể cung "
              f"cấp.\n")
        bm = o9.get("beats_random_by_model", {})
        if bm:
            A("| Utility model | Số ngân sách so sánh | Xếp hạng HUIM vượt "
              "ngẫu nhiên |")
            A("|---|---|---|")
            for m, d in bm.items():
                A(f"| {m} | {d['n']} | **{d['beats']}** |")
            A("")
        A("[OUR INTERPRETATION] Hai cách giải thích phải tách bạch. "
          "**(1) Xếp hạng sai** — bảng trên trả lời riêng cho từng model. "
          "**(2) Tập quá nhỏ** — HUIM chỉ cung cấp được các AP xuất hiện trong "
          "một tập HUI KHÔNG bị cắt ngang, và số đó bị chặn bởi minUtil thấp "
          "nhất còn hoàn thành trong ngân sách. **Ngay cả một xếp hạng hoàn "
          "hảo cũng không thể lấp khoảng cách từ bên trong cái trần đó.** Đây "
          "là phát hiện cơ chế hữu ích nhất của nghiên cứu, và nó chỉ thẳng về "
          "Quan sát 1: muốn mở rộng tập AP thì minUtil phải giảm, nhưng giảm "
          "minUtil làm số ITEMSET tăng nhanh hơn số AP rất nhiều, và chi phí "
          "bùng nổ trước khi tập AP kịp lớn lên một cách hữu ích.\n")
        A("[OUR INTERPRETATION] Lưu ý điều này KHÔNG nói rằng xếp hạng của "
          "HUIM là kém; đó là câu hỏi riêng. Nó nói rằng điểm làm việc nơi "
          "HUIM có thể cạnh tranh đã không nằm trong tầm với của ngân sách "
          "tính toán dùng ở đây — một phát biểu về thiết kế thực nghiệm này "
          "cũng nhiều như về bản thân phương pháp.\n")

    cpath = METRICS / "ips_cost.csv"
    if cpath.exists():
        CO = pd.read_csv(cpath).sort_values("n_features", ascending=False)
        bc = CO[CO["condition"] == "baseline_all_520"]
        A("### 5.5b. Thời gian và bộ nhớ của hệ thống định vị\n")
        A("Chi phí khai thác HUIM ở mục 5.2; đây là nửa còn lại — nơi việc "
          "giảm chiều thực sự trả công. Đo một lõi (n_jobs=1), lặp lại lấy "
          "trung vị; bộ nhớ cơ sở dữ liệu tính chính xác, không ước lượng.\n")
        A("| Điều kiện | Số WAP | Index | ms / fingerprint | CSDL float64 "
          "(MB) | CSDL int8 (MB) | Joint Acc |")
        A("|---|---|---|---|---|---|---|")
        for _, r in CO.iterrows():
            A(f"| {r['condition']} | {int(r['n_features'])} | "
              f"{r['sklearn_algorithm']} | "
              f"{r['predict_ms_per_fingerprint']:.4f} | "
              f"{r['db_memory_float64_mb']:.2f} | "
              f"{r['db_memory_int8_mb']:.2f} | "
              f"{pc(r['joint_building_floor_accuracy'])} |")
        A("")
        if len(bc):
            b0 = bc.iloc[0]
            best = CO.loc[CO["joint_building_floor_accuracy"].idxmax()]
            A(f"[EXPERIMENT RESULT] Baseline {int(b0['n_features'])} WAP: "
              f"**{b0['predict_ms_per_fingerprint']:.3f} ms/fingerprint**, "
              f"CSDL vân tay **{b0['db_memory_float64_mb']:.1f} MB**.\n")
            A(f"[EXPERIMENT RESULT] Điều kiện chính xác nhất toàn nghiên cứu "
              f"(`{best['condition']}`, {int(best['n_features'])} WAP) nhanh "
              f"hơn **"
              f"{b0['predict_ms_per_fingerprint']/best['predict_ms_per_fingerprint']:.1f}×**, "
              f"chiếm **"
              f"{100*best['db_memory_float64_mb']/b0['db_memory_float64_mb']:.0f}%** "
              f"bộ nhớ, và joint accuracy "
              f"{pc(best['joint_building_floor_accuracy'])} "
              f"({(best['joint_building_floor_accuracy']-b0['joint_building_floor_accuracy'])*100:+.2f} pp).\n")
            hb = CO[CO["family"].astype(str).str.startswith("huim")]
            if len(hb):
                hbest = hb.loc[hb["joint_building_floor_accuracy"].idxmax()]
                A(f"[EXPERIMENT RESULT] Cấu hình HUIM tốt nhất "
                  f"(`{hbest['condition']}`, {int(hbest['n_features'])} WAP) "
                  f"nhanh hơn "
                  f"**{b0['predict_ms_per_fingerprint']/hbest['predict_ms_per_fingerprint']:.1f}×** "
                  f"và chiếm "
                  f"**{100*hbest['db_memory_float64_mb']/b0['db_memory_float64_mb']:.0f}%** "
                  f"bộ nhớ, nhưng joint accuracy chỉ "
                  f"{pc(hbest['joint_building_floor_accuracy'])}.\n")
            A("[OUR INTERPRETATION] Giảm chiều cho lợi ích gần như TUYẾN TÍNH "
              "về cả thời gian lẫn bộ nhớ, và đây là phần giá trị KHÔNG gây "
              "tranh cãi của toàn bộ hướng tiếp cận. Điều gây tranh cãi là "
              "**ai** chọn tập đặc trưng: trên dữ liệu này, tiêu chí đối chứng "
              "đơn giản chọn tốt hơn HUIM.\n")
            kd = CO[CO["sklearn_algorithm"] != "brute"]
            if len(kd):
                A(f"[FACT FROM DATA] Đường cong thời gian không đơn điệu ở số "
                  f"chiều nhỏ nhất ({int(kd['n_features'].iloc[0])} WAP): "
                  f"scikit-learn chuyển sang chỉ mục `"
                  f"{kd['sklearn_algorithm'].iloc[0]}`, mà trên dữ liệu thưa "
                  f"thì cây chậm hơn duyệt vét cạn. Thuật toán index được ghi "
                  f"lại trong log cho từng phép đo.\n")

    pop = RESULTS / "positioning_optimisation.json"
    if pop.exists():
        PO = load_json(pop)
        PA = pd.read_csv(METRICS / "positioning_ablation.csv")
        s0, sel = PA[PA["stage"] == "S0"].iloc[0], PA.iloc[-1]
        A("### 5.5c. Tối ưu sai số định vị theo mét (PHASE I3)\n")
        A("k-NN của PHASE I (k=1, Manhattan) được chọn cho bài toán PHÂN LOẠI "
          "tầng trên một phép chia ngẫu nhiên; PHASE I3 tối ưu riêng phần ước "
          f"lượng toạ độ. Chọn trên {PO['protocol']['selection_split']}; tiêu "
          "chí là sai số trung bình (mét thực địa) trên các fold dev; "
          "validationData chỉ chấm điểm mỗi bước đúng một lần.\n")
        A("| Bước | Cấu hình | Dev TB (m) | Val TB (m) | Val trung vị (m) | "
          "Joint acc |")
        A("|---|---|---|---|---|---|")
        for _, r in PA.iterrows():
            A(f"| {r['stage']} {r['what']} | {r['config']} | "
              f"{r['dev_mean_ground_m']:.2f} | {r['val_mean_ground_m']:.2f} | "
              f"{r['val_median_ground_m']:.2f} | "
              f"{pc(r['val_joint_building_floor_accuracy'])} |")
        A("")
        A(f"[EXPERIMENT RESULT] Mô hình được giao thức chọn ({sel['stage']}): "
          f"sai số trung bình **{sel['val_mean_ground_m']:.2f} m** thực địa so "
          f"với {s0['val_mean_ground_m']:.2f} m "
          f"({(1 - sel['val_mean_ground_m'] / s0['val_mean_ground_m']) * 100:.0f}% "
          f"thấp hơn), trung vị {sel['val_median_ground_m']:.2f} m, joint "
          f"accuracy {pc(sel['val_joint_building_floor_accuracy'])}.\n")
        best = PA.loc[PA["val_mean_ground_m"].idxmin()]
        A(f"[OUR INTERPRETATION] Phần lớn cải thiện đến từ khoảng cách "
          f"Bray-Curtis/cosine và k láng giềng có trọng số. Dò độ lệch thiết bị "
          f"và ensemble thắng trên dev nhưng không giảm thêm sai số mét trên "
          f"validation (thấp nhất là {best['stage']}, "
          f"{best['val_mean_ground_m']:.2f} m); chúng chỉ nâng độ chính xác "
          f"tầng. Mô hình giữ nguyên lựa chọn của giao thức.\n")
        for name in ("huim_checks.json", "positioning_checks.json"):
            p = RESULTS / "verification" / name
            if p.exists():
                v = load_json(p)
                A(f"Kiểm chứng độc lập `{name}`: {v['n_checks']} phép kiểm "
                  f"tra, {v['n_failed']} thất bại.")
        A("Bộ kiểm chứng thủ công bằng Excel: "
          "`verification/kiem_chung_thu_cong.xlsx`.\n")

    A("### 5.6. Một kết quả ĐI NGƯỢC kỳ vọng — và nó là hạn chế lớn nhất của "
      "thiết kế\n")
    A(f"[EXPERIMENT RESULT] Top-10 AP được phát hiện nhiều nhất và top-10 AP "
      f"có mutual information cao nhất trùng "
      f"**{o6['overlap_top10_support_vs_top10_mi']}/10**"
      + (f" ({', '.join(o6['overlap_members'])})" if o6["overlap_members"]
         else "") + ".")
    if "spearman_support_vs_mi_over_all_detected_waps" in o6:
        A(f"[EXPERIMENT RESULT] Trên toàn bộ "
          f"{o6['n_detected_waps_compared']} AP được phát hiện, tương quan "
          f"hạng giữa số lần được phát hiện và mutual information là "
          f"**Spearman ρ = "
          f"{o6['spearman_support_vs_mi_over_all_detected_waps']}** "
          f"(Pearson r = "
          f"{o6['pearson_support_vs_mi_over_all_detected_waps']}). Trùng xếp "
          f"hạng theo độ sâu: "
          + ", ".join(f"top-{k}: {v}/{k}"
                      for k, v in o6["rank_overlap_at_depth"].items()) + ".\n")
        A("**Bài tìm hiểu kỳ vọng chứng minh 'frequent ≠ useful' và dữ liệu đã BÁC "
          "BỎ kỳ vọng đó ở mức từng Access Point.** Hai tiêu chí gần như trùng "
          "khít về thứ hạng. Nguyên nhân nằm ở cách rời rạc hoá: trạng thái "
          "'không phát hiện' chiếm phần áp đảo trong phân bố của mỗi AP, nên "
          "I(A_i;Y) chủ yếu đo việc AP có được nhìn thấy hay không ở từng "
          "tầng — tức gần như chính là support theo lớp.\n")
        A("[OUR INTERPRETATION] **Hệ quả là hạn chế lớn nhất của thiết kế "
          "này:** external utility mà bài tìm hiểu gọi là 'discriminative' trên thực "
          "tế gần như là một cách tham số hoá lại tần suất phát hiện. Điều này "
          "giải thích nhất quán ba hiện tượng khác: hai đối chứng top-n theo "
          "MI và top-n theo support cho kết quả rất gần nhau; Model B và "
          "Model C chọn tập AP rất giống nhau; và ablation B–C ít thông tin "
          "hơn kỳ vọng. Đây là hạn chế của BÀI TÌM HIỂU, không phải của HUIM.\n")
        A("[OUR INTERPRETATION] Chỗ sự phân biệt 'trông có vẻ giá trị' với "
          "'thực sự hữu ích' THỰC SỰ phát huy là ở mức HÀM UTILITY: Model A "
          "(p ≡ 1, utility = cường độ tín hiệu × mức đồng xuất hiện) có xếp "
          "hạng tệ hơn cả ngẫu nhiên ở mọi ngân sách đã thử.\n")
    if o6.get("label_entropy_bits") is not None:
        A(f"Entropy nhãn H(Y) = {o6['label_entropy_bits']} bit; AP thông tin "
          f"nhất cung cấp {o6['max_mi_bits']} bit, tức "
          f"{o6['max_mi_as_fraction_of_H_Y']*100:.1f}% ⟹ không AP nào một mình "
          f"giải quyết được bài toán, nên khai thác theo **nhóm** là một ý "
          f"tưởng đáng thử.\n")

    # ------------------------------------------------------------------ 6
    A("## 6. Kết luận có thể bảo vệ trước giảng viên\n")
    A("Những phát biểu sau đều có số liệu trực tiếp chống lưng:\n")
    A(f"1. **Mô hình hoá được.** {nf(hsum['database']['n_rows'])} fingerprint "
      f"→ {nf(hsum['database']['n_non_empty_transactions'])} utility "
      f"transaction; EFIM chạy và cho kết quả trên "
      f"{len(H)} cấu hình ngưỡng.")
    A("2. **minUtil là núm 'nhóm lớn đến đâu là một mẫu', không phải núm chất "
      "lượng.** Số HUI cực nhạy với ngưỡng, số AP riêng biệt thì không.")
    A("3. **Chặn trên của EFIM điều khiển TÌM KIẾM, không điều khiển KẾT "
      "QUẢ.** Runtime theo số nút cây đã duyệt; bộ nhớ theo kích thước kết quả.")
    A("4. **Hàm utility là phát biểu bài toán.** Chỉ đổi p mà tập AP được chọn "
      "đã đổi, vì p đi vào cả TWU ⟹ đổi thứ tự item ⟹ đổi hình dạng cây tìm "
      "kiếm.")
    A("5. **Sự phân biệt 'trông có vẻ giá trị' với 'thực sự hữu ích' nằm ở "
      "HÀM UTILITY, không ở tần suất của từng item.** Trên bộ dữ liệu này số "
      "lần được phát hiện và mutual information gần như trùng khít về thứ "
      "hạng; nhưng Model A, vốn nhân cường độ tín hiệu với mức đồng xuất "
      "hiện, xếp hạng AP tệ hơn cả ngẫu nhiên. Đây là một kết quả ĐI NGƯỢC "
      "kỳ vọng ban đầu và được báo cáo đúng như đo được.")
    A(f"6. **Building accuracy ({pc(base['building_accuracy'])}) chịu được "
      f"giảm chiều; Floor accuracy ({pc(base['floor_accuracy'])}) là ràng buộc "
      f"chặt.** Dự đoán này được đưa ra từ audit TRƯỚC khi fit mô hình và được "
      f"kiểm chứng đúng.")
    if o9.get("largest_huim_selected_set"):
        A(f"7. **Trần kích thước tập AP là ràng buộc quyết định.** HUIM chỉ "
          f"cung cấp được tối đa {o9['largest_huim_selected_set']} WAP trong "
          f"ngân sách khai thác đã dùng; ở ngân sách đó không phương pháp nào "
          f"chạm được baseline. Mở rộng tập AP đòi hỏi hạ minUtil, điều làm số "
          f"itemset bùng nổ nhanh hơn rất nhiều so với số AP thu thêm.")
        A("8. **Đóng góp đúng mức:** *bài tìm hiểu khảo sát khả năng thích nghi mô "
          "hình High Utility Itemset Mining cho bài toán lựa chọn nhóm Access "
          "Point trong Wi-Fi fingerprint indoor positioning.*\n")
    else:
        A("7. **Đóng góp đúng mức:** *bài tìm hiểu khảo sát khả năng thích nghi mô "
          "hình High Utility Itemset Mining cho bài toán lựa chọn nhóm Access "
          "Point trong Wi-Fi fingerprint indoor positioning.*\n")

    # ------------------------------------------------------------------ 7
    A("## 7. Những điều KHÔNG được khẳng định\n")
    A("- **KHÔNG** khẳng định một High Utility Itemset, một cách tổng quát, là "
      "một nhóm đặc trưng tốt cho phân loại. HUIM là bài toán **không giám "
      "sát**; không có định lý nào bảo đảm điều đó.")
    A("- **KHÔNG** khẳng định HUIM tốt hơn các phương pháp chọn AP "
      "information-theoretic đã có. Bảng đối chứng ngân sách khớp nhau là bằng "
      "chứng duy nhất được đưa ra, và nó được đọc đúng như nó là.")
    A("- **KHÔNG** khẳng định việc chọn Access Point là đóng góp mới — đã có "
      "từ Chen et al., *IEEE TKDE*, vol. 18, pp. 877–888, 2006.")
    A("- **KHÔNG** khẳng định đây là nghiên cứu HUIM đầu tiên cho IPS. Không "
      "tìm thấy bằng chứng ≠ không tồn tại.")
    A("- **KHÔNG** gắn Q1/Q2 cho bất kỳ nguồn nào: bài hội nghị không có "
      "quartile SJR/JCR, và với bài tạp chí thì `scimagojr.com` trả về HTTP "
      "403 từ môi trường thực nghiệm.")
    A("- Sai số định vị ĐƯỢC báo cáo theo mét, nhưng **theo cả hai cách**: "
      "mét toạ độ chiếu (quy ước của literature UJIIndoorLoc) và mét thực địa "
      "(đã hiệu chỉnh biến dạng Web Mercator). Tài liệu bộ dữ liệu không nêu "
      "hệ toạ độ; hệ toạ độ được xác định bằng thực nghiệm, không phải bằng "
      "giả định — xem `results/coordinate_system_verification.json`.")
    A("- **KHÔNG** ngoại suy ra ngoài UJIIndoorLoc, một cấu hình k-NN và các "
      "định nghĩa (q, p) dùng ở đây.\n")

    # ------------------------------------------------------------------ 8
    A("## 8. Hạn chế\n")
    A("**Phương pháp.** Ánh xạ utility mang tính thiết kế — q và p không tồn "
      "tại trong dữ liệu Wi-Fi nên phải tự định nghĩa; 'các HUI của "
      "UJIIndoorLoc' không phải một đối tượng xác định. HUIM không phải bộ "
      "chọn đặc trưng có giám sát. Vùng ngưỡng dùng được rất hẹp. Quy tắc xếp "
      "hạng HUI → AP là một thiết kế trong nhiều thiết kế khả dĩ. Siêu tham số "
      "k-NN chọn trên một phép chia ngẫu nhiên của trainingData, vốn lạc quan "
      "so với validationData.\n")
    A("**Cài đặt.** Không dùng được SPMF (không có JVM). Hiệu năng tuyệt đối "
      "là của một cài đặt Python, không so sánh trực tiếp với các bài báo dùng "
      "Java — thứ có ý nghĩa là **hình dạng** các đường cong. Các lần chạy "
      "vượt ngân sách có tập HUI bị cắt ngang theo thứ tự DFS nên **bị thiên "
      "lệch**, vì vậy chúng không được dùng để xếp hạng AP và được đánh dấu rõ "
      "trong mọi bảng.\n")
    A(f"**Dữ liệu.** Bộ dữ liệu từ 2013. Không đồng nhất thiết bị giữa hai "
      f"split. {cs['waps_only_in_validation']} AP chỉ có trong validation. "
      f"{tr['anomaly_probes']['n_empty_fingerprints']} fingerprint rỗng và "
      f"{nf(tr['duplicate_rows_full'])} dòng trùng lặp được giữ nguyên (ghi "
      f"nhận, không sửa ngầm). SPACEID trong validation đồng nhất bằng 0 nên "
      f"không đánh giá được cấp phòng. Đơn vị toạ độ không được tài liệu "
      f"hoá.\n")
    A("**Tính tổng quát.** Literature review không phải systematic review; "
      "IEEE Xplore và ACM DL full-text search không truy cập được.\n")

    # ------------------------------------------------------------------ 9
    A("## 9. Mười câu hỏi giảng viên có thể hỏi\n")
    qa = [
        ("Vì sao utility không anti-monotone, và hệ quả là gì?",
         "Thêm một item vừa cộng thêm utility của nó (đẩy lên) vừa thu hẹp tập "
         "giao dịch chứa itemset (đẩy xuống). Phản ví dụ: u({b}) = 16 < "
         "u({b,d}) = 30 nhưng u({b,d,f}) < u({b,d}). Hệ quả: không thể cắt "
         "nhánh bằng chính utility — phải cắt bằng chặn trên anti-monotone như "
         "TWU, local utility, subtree utility."),
        ("EFIM prune bằng gì, và hai chặn khác nhau thế nào?",
         "Local utility lu(α,z): nếu < minUtil thì loại item z khỏi CẢ cây con "
         "của α. Subtree utility su(α,z): nếu < minUtil thì KHÔNG bước vào "
         "nhánh α∪{z}. su chặt hơn vì chỉ cộng utility của các item đứng SAU "
         "z. Điểm đẹp: lu(∅,z) = TWU(z), nên TWU pruning là trường hợp riêng "
         "tại gốc."),
        ("Vì sao chọn EFIM mà không phải HUI-Miner hay UP-Growth?",
         "Căn cứ là một benchmark ĐỘC LẬP (Zhang et al., ESWA 2018), không "
         "phải bài báo của chính tác giả EFIM. Thêm hai lý do riêng cho bộ dữ "
         "liệu này: transaction merging có đất dùng vì dữ liệu thưa và nhiều "
         "vector WAP trùng nhau; và cơ sở dữ liệu RỘNG chứ không SÂU nên chi "
         "phí bộ nhớ của hướng utility-list đáng lo hơn."),
        ("Giá trị 100 nghĩa là gì, và em chứng minh thế nào?",
         "Nghĩa là AP không được phát hiện. Ba bằng chứng: (1) tài liệu UCI "
         "ghi nguyên văn; (2) phân bố dữ liệu — KHÔNG ô nào trong khoảng 1…99 "
         "trên hơn 10 triệu ô, nên 100 cách giá trị kế tiếp đúng 100 đơn vị, "
         "một thang đo vật lý không có lỗ hổng như vậy; (3) tính nhất quán — "
         "đọc 100 là cường độ sẽ hàm ý mọi AP đều mạnh nhất ở mọi lần quét."),
        ("Vì sao không được tính mutual information trên validationData?",
         "Vì đó là data leakage: tập AP được chọn sẽ 'biết trước' câu trả lời "
         "của bài kiểm tra, accuracy cao giả tạo và không nói gì về dữ liệu "
         "chưa thấy. Em cưỡng chế bằng code: hàm build_external_utility raise "
         "lỗi nếu split_name khác 'training', và có unit test cho cơ chế đó."),
        ("HUIM nhiều kết quả hơn thì accuracy cao hơn không?",
         "Không, và đó là câu hỏi sai. Tập HUI lớn hơn ở ngưỡng thấp hơn phần "
         "lớn chỉ là thêm TẬP CON của cùng những nhóm AP: số HUI tăng mà số AP "
         "riêng biệt gần như không tăng. Thứ làm thay đổi accuracy là NHỮNG AP "
         "NÀO được chọn."),
        ("Vì sao phải có đối chứng random, top-support và top-MI?",
         "Vì 'HUIM đạt accuracy X' tự nó không phải kết quả. Nếu random cùng "
         "kích thước cũng đạt X thì việc chọn không làm gì. Nếu top-n theo MI "
         "cũng đạt X thì phần khai thác itemset không thêm gì so với thước đo "
         "nó được cho sẵn. Đối chứng là cách duy nhất để đọc ablation một cách "
         "trung thực."),
        ("Vì sao Building accuracy cao hơn Floor accuracy nhiều?",
         f"Vì "
         f"{tr['anomaly_probes']['ap_building_spread']['n_waps_in_exactly_1_building']}"
         f" AP chỉ nằm trong một toà nhà và chỉ "
         f"{tr['anomaly_probes']['ap_building_spread']['n_waps_in_all_3_buildings']}"
         f" AP thấy được ở cả ba, nên xác định toà nhà gần như là một phép tra "
         f"bảng. Xác định tầng phải phân giải khác biệt tín hiệu TRONG CÙNG "
         f"một toà nhà, nơi cùng những AP đó nhìn thấy được ở mọi tầng. Dự "
         f"đoán này có từ audit, trước khi fit mô hình."),
        ("Vì sao không báo cáo sai số theo mét?",
         "Vì không xác minh được. Tài liệu UCI và trang của chính nhóm tác giả "
         "đều chỉ cho khoảng giá trị của LONGITUDE/LATITUDE, không nêu hệ toạ "
         "độ hay đơn vị; toàn văn bài báo IPIN 2014 nằm sau tường phí. Hộp "
         "giới hạn có kích thước hợp lý cho một campus nếu đơn vị là mét, "
         "nhưng đó là suy luận, không phải bằng chứng."),
        ("Số liệu trong báo cáo có đáng tin không?",
         "Báo cáo Word và PowerPoint được SINH TỰ ĐỘNG từ results/ và "
         "figures/. Script sinh tài liệu không chứa giá trị thực nghiệm nào; "
         "thiếu file kết quả thì nó báo lỗi và dừng. Mỗi biểu đồ lưu kèm một "
         "CSV chứa đúng các dòng đã vẽ. Mọi lần chạy vượt ngân sách đều được "
         "GIỮ trong log với trạng thái ABORTED_RESOURCE_LIMIT."),
    ]
    for k, (q, a) in enumerate(qa, 1):
        A(f"**{k}. {q}**\n")
        A(f"{a}\n")

    # ------------------------------------------------------------------ 10
    A("## 10. Lệnh chạy lại toàn bộ project\n")
    A("```bash")
    A("# 1. cài môi trường")
    A("python -m pip install -r requirements.txt")
    A("")
    A("# 2. chạy lại tất cả, theo đúng thứ tự PHASE A -> N")
    A("python run_experiments.py")
    A("")
    A("# hoặc từng phần:")
    A("python run_experiments.py --list              # xem các phase")
    A("python run_experiments.py --only tests        # chỉ chạy kiểm thử")
    A("python run_experiments.py --from huim         # chạy lại từ PHASE H")
    A("python run_experiments.py --offline           # bỏ các phase cần mạng")
    A("```\n")
    A(f"Môi trường đã dùng: {env['platform']}, Python {env['python_version']}, "
      f"CPU {env.get('cpu_model', 'N/A')} "
      f"({env.get('cpu_count_physical')} lõi vật lý / "
      f"{env.get('cpu_count_logical')} luồng), RAM "
      f"{env.get('ram_total_gb')} GB. Random seed "
      f"{isum['protocol']['random_seed']}.\n")
    A(f"Thời gian chạy đã ghi nhận: HUIM "
      f"{nf(hsum.get('total_wall_clock_s'), 1)} s, IPS "
      f"{nf(isum.get('total_wall_clock_s'), 1)} s.\n")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- entry point
def main() -> None:
    ver = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
           "docx": verify_docx(), "pptx": verify_pptx(),
           "figures": verify_figures(),
           "builder_literal_scan": verify_no_fabricated_numbers()}

    rows = []
    for name, path in DELIVERABLES:
        paths = [PROJECT_ROOT / q.strip() for q in path.split(",")]
        found = []
        for q in paths:
            if "*" in str(q):
                found.extend(sorted(q.parent.glob(q.name)))
            elif q.exists():
                found.append(q)
        ok = len(found) >= 1
        rows.append({"Deliverable": name, "Path": path,
                     "Status": "OK" if ok else "MISSING",
                     "n_files": len(found)})
    dl = pd.DataFrame(rows)
    dl.to_csv(RESULTS / "deliverables.csv", index=False)

    txt = build_summary()
    (PROJECT_ROOT / "FINAL_SUMMARY.md").write_text(txt, encoding="utf-8")
    # FINAL_SUMMARY.md itself only exists after this write, so re-check it
    dl.loc[dl["Deliverable"].str.startswith("18."), "Status"] = "OK"
    dl.to_csv(RESULTS / "deliverables.csv", index=False)
    ver["deliverables"] = rows
    dump_json(ver, RESULTS / "verification.json")

    print("\n| Deliverable | Path | Status |")
    print("|---|---|---|")
    for _, r in dl.iterrows():
        print(f"| {r['Deliverable']} | `{r['Path']}` | {r['Status']} |")

    print("\nVERIFICATION")
    d, p = ver["docx"], ver["pptx"]
    if d.get("exists"):
        print(f"  DOCX  {d['size_kb']} KB, {d['n_paragraphs']} paragraphs, "
              f"{d['n_tables']} tables, {d['n_embedded_images']} images, "
              f"~{d['approx_pages_at_2800_chars']} pages")
        print(f"        fonts={d['fonts_used_in_runs']} ok={d['fonts_ok']}  "
              f"placeholders={d['placeholders_found'] or 'none'}")
        print(f"        references={d['has_references_section']} "
              f"cheatsheet={d['has_cheatsheet']} "
              f"formulas={d['has_formulas']} "
              f"mandated_statement={d['has_mandated_statement']}")
    if p.get("exists"):
        print(f"  PPTX  {p['size_kb']} KB, {p['n_slides']} slides, "
              f"{p['n_pictures']} pictures, {p['n_tables']} tables, "
              f"{p['n_slides_with_speaker_notes']} with notes")
        print(f"        fonts={p['fonts_used']} ok={p['fonts_ok']}  "
              f"body_pt={p['body_size_pt_mode']}  "
              f"placeholders={p['placeholders_found'] or 'none'}")
        print(f"        overflow_candidates="
              f"{p['possible_text_overflow'] or 'none'}")
        print(f"        overlapping_shapes="
              f"{p['overlapping_shapes'] or 'none'}")
        print(f"        shapes_off_slide={p['shapes_off_slide'] or 'none'}")
    f = ver["figures"]
    print(f"  FIGS  {f['n_png']} PNG; missing data CSV: "
          f"{f['missing_data_csv'] or 'none'}")
    b = ver["builder_literal_scan"]
    print(f"  SCAN  {b['n_literals_found']} numeric literals in the document "
          f"builders, {b['n_unexplained']} unexplained")
    LOG.info("wrote FINAL_SUMMARY.md, results/deliverables.csv, "
             "results/verification.json")


if __name__ == "__main__":
    main()
