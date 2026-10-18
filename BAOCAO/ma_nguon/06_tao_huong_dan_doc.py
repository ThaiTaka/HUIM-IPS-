"""BAOCAO / bước 6 - viết BAOCAO/00_HUONG_DAN_DOC.md: đọc gì trước, mỗi file là gì,
các con số chính, cách chạy lại. Danh sách file được lấy từ thư mục thật.

    python BAOCAO/ma_nguon/06_tao_huong_dan_doc.py
"""
from __future__ import annotations

import json

import pandas as pd

from hinh_chung import BAOCAO, DIAGRAM, SO_LIEU, theta_txt, vn
from nhan import lbl

J = json.loads((SO_LIEU / "00_cau_hinh_cuoi_cung.json").read_text(encoding="utf-8"))
B, S = J["tot_nhat"], J["ban_dau"]
TOA = pd.read_csv(SO_LIEU / "11_sai_so_theo_toa.csv", dtype={"toa": str})
S8 = pd.read_csv(SO_LIEU / "09_buoc8_thoi_gian_bo_nho.csv")
CHK = pd.read_csv(SO_LIEU / "01_kiem_chung_union_vs_EFIM.csv")


def toa(k, b):
    return TOA[(TOA.cau_hinh == k) & (TOA.toa == b)].iloc[0]


MO_TA_SO_LIEU = {
    "00_cau_hinh_cuoi_cung.json": "cấu hình tốt nhất (chọn theo dev) và cấu hình ban đầu, các chỉ số chính",
    "01_kiem_chung_union_vs_EFIM.csv": "union của thuật toán tìm union so với union EFIM ở mọi θ EFIM chạy xong",
    "02_so_AP_theo_minUtil.csv": "số AP trong union theo θ, model, phạm vi (chung / theo tòa); thời gian, số nút tìm kiếm",
    "03_EFIM_so_HUI_thoi_gian_bo_nho.csv": "EFIM liệt kê đầy đủ: số HUI, trạng thái, thời gian, bộ nhớ theo θ",
    "03b_EFIM_theo_toa.csv": "EFIM liệt kê đầy đủ theo từng tòa (vì sao quy tắc bước 6 không áp dụng được theo tòa)",
    "04_buoc2_model_ABC.csv": "bước 2: Model A/B/C ở các θ EFIM chạy xong (dev, tập test, theo tòa)",
    "05_buoc3_minUtil_HUIM_chung.csv": "bước 3: lưới θ, HUIM chung 3 tòa",
    "06_buoc4_HUIM_theo_toa.csv": "bước 4: lưới θ, HUIM riêng từng tòa",
    "07_buoc6_quy_tac_chon_AP.csv": "bước 6: union / top-n / frequent / weighted",
    "08_buoc7_ensemble.csv": "bước 7: ensemble 2-3 cấu hình (trung bình / trung vị)",
    "09_buoc8_thoi_gian_bo_nho.csv": "bước 8: ms/fingerprint, radio map MB, RSS, thời gian dựng mô hình",
    "10_xep_hang_tat_ca_cau_hinh.csv": "mọi cấu hình đã thử, xếp theo sai số dev",
    "11_sai_so_theo_toa.csv": "sai số theo tòa: ban đầu và tốt nhất",
    "12_sai_so_theo_toa_tang.csv": "sai số theo tòa × tầng (dữ liệu Hình 12)",
    "13_du_doan_tung_mau_tap_test.csv": "2 × 1.111 dòng: vị trí thật, dự đoán, sai số từng mẫu",
}
MO_TA_MA = {
    "00_chay_lai_toan_bo.py": "chạy lại tất cả theo thứ tự (thêm --bao-cao để bỏ qua thí nghiệm)",
    "01_chay_thi_nghiem.py": "thí nghiệm: union HUI mọi θ, kiểm chứng với EFIM, các bước 2-8",
    "02_tong_hop_so_lieu.py": "gom kết quả results/huim_opt thành so_lieu/",
    "03_ve_bieu_do.py": "vẽ 15 hình vào diagram/ (PNG + SVG)",
    "04_tao_bao_cao_word.py": "tạo file Word",
    "05_tao_slide_pptx.py": "tạo file PowerPoint",
    "06_tao_huong_dan_doc.py": "tạo file hướng dẫn này",
    "hinh_chung.py": "màu, font, định dạng số dùng chung cho hình",
    "word_chung.py": "hàm dựng bảng, hình, chú thích cho Word",
    "nhan.py": "tên tiếng Việt của mỗi cấu hình (luôn kèm θ)",
    "ban_sao_src": "bản sao mã nguồn thí nghiệm của src/ tại lúc tạo báo cáo (bản gốc vẫn ở src/)",
}

# bản sao mã nguồn thí nghiệm (để đọc; bản chạy thật là src/)
import shutil                                            # noqa: E402

from hinh_chung import ROOT                              # noqa: E402

SRC_FILES = ["huim/union_search.py", "huim/efim.py", "huim/brute_force.py", "huim_opt.py",
             "run_huim_opt.py", "run_union_levels.py", "check_union_search.py",
             "utility_models.py", "preprocess_uji.py", "optimize_positioning.py",
             "feature_selection.py", "ips_model.py", "utils.py", "../tests/test_union_search.py"]
dst = BAOCAO / "ma_nguon" / "ban_sao_src"
if dst.exists():
    shutil.rmtree(dst)
for f in SRC_FILES:
    target = dst / f.replace("../tests/", "tests/")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2((ROOT / "src" / f).resolve(), target)
DOC_TRUOC = [
    "Bản sao các file trong src/ mà thí nghiệm HUIM dùng, chép lúc tạo báo cáo để đọc kèm.",
    "Chạy thật luôn dùng bản ở src/ (BAOCAO/ma_nguon/01_chay_thi_nghiem.py gọi src/).",
    "",
    "- huim/union_search.py: thuật toán tìm union HUI chính xác (mục 3.2 báo cáo)",
    "- huim/efim.py: EFIM liệt kê đầy đủ (PHASE H); huim/brute_force.py: oracle kiểm thử",
    "- utility_models.py: q(i,T) và p(i) của Model A/B/C",
    "- huim_opt.py: union theo θ, HUIM theo tòa (PBModel), đánh giá dev/tập test, ensemble, đo thời gian",
    "- run_huim_opt.py: các bước 2-8; run_union_levels.py: union mọi θ song song; "
    "check_union_search.py: kiểm chứng với EFIM",
    "- optimize_positioning.py: bộ định vị S4; preprocess_uji.py, ips_model.py, utils.py: đọc dữ liệu, hằng số",
    "- tests/test_union_search.py: union của thuật toán = union của oracle vét cạn (19 kiểm thử)",
]
(dst / "DOC_TRUOC.md").write_text(chr(10).join(DOC_TRUOC) + chr(10), encoding="utf-8")

docx = sorted(BAOCAO.glob("*.docx"))
pptx = sorted(p for p in BAOCAO.glob("*.pptx") if p.name.startswith("Slide_"))
hinh = sorted(DIAGRAM.glob("*.png"))
so = sorted(p.name for p in SO_LIEU.iterdir())
ma = sorted(p.name for p in (BAOCAO / "ma_nguon").iterdir() if p.name != "__pycache__")
t0 = S8[S8.cau_hinh == "G_A__1.9294pct"].iloc[0]
tb = S8[S8.cau_hinh == B["config"]]
ok = int(CHK["identical"].astype(str).str.lower().eq("true").sum())

L = []
L.append("# BAOCAO - HUIM cho định vị trong nhà trên UJIIndoorLoc (chỉ cấu hình có HUIM)\n")
L.append("Thư mục này được tạo lại hoàn toàn ngày 16/10/2026 theo hướng mới: bỏ mọi kết quả không dùng HUIM "
         "(k-NN gốc S0, S4 với 520 AP) và tối ưu chính HUIM. Bản cũ được lưu ở "
         "`D:\\HUIM-IPS-_sao_luu_2026-10-16_truoc_HUIM_only.zip`.\n")
L.append("## Đọc theo thứ tự này\n")
L.append(f"1. **`{docx[0].name if docx else 'Bao_cao_...docx'}`** - báo cáo đầy đủ. Đọc khung *Kết quả chính* ở trang 1, "
         "rồi mục 1.2 (giao thức chọn trên dev, báo cáo trên tập test) và mục 3.2 (thuật toán tìm union).")
L.append(f"2. **`{pptx[0].name if pptx else 'Slide_...pptx'}`** - bản trình bày, cùng số liệu với báo cáo.")
L.append("3. **`diagram/`** - 15 hình; mọi hình đều ghi ngưỡng minUtil θ. Hình 1 là sơ đồ luồng một trang.")
L.append("4. **`so_lieu/`** - mọi bảng số mà hình và báo cáo đọc; dùng để kiểm tra lại từng con số.")
L.append("5. **`ma_nguon/`** - script sinh ra tất cả những thứ trên.\n")
L.append("## Các con số chính\n")
L.append("| | Ban đầu | Tốt nhất (chọn theo dev) |")
L.append("|---|---|---|")
L.append(f"| Cấu hình | {lbl(S['config'])} | {lbl(B['config'])} |")
L.append(f"| Số AP | {int(S['n_ap'])} | {int(B['n_ap'])} |")
L.append(f"| Sai số TB tập test | {vn(S['test_mean_m'])} m | **{vn(B['test_mean_m'])} m** |")
L.append(f"| Trung vị / p90 | {vn(S['test_median_m'])} / {vn(S['test_p90_m'])} m | {vn(B['test_median_m'])} / {vn(B['test_p90_m'])} m |")
L.append(f"| Sai số TB dev (6 fold) | {vn(S['dev_mean_m'])} m | {vn(B['dev_mean_m'])} m |")
L.append(f"| Đúng tòa / tòa-tầng | {vn(100*S['test_building_acc'],1)} % / {vn(100*S['test_joint_acc'],1)} % | "
         f"{vn(100*B['test_building_acc'],1)} % / {vn(100*B['test_joint_acc'],1)} % |")
for b in ("0", "1", "2"):
    L.append(f"| Tòa {b} | {vn(toa('ban_dau', b).sai_so_tb_m)} m | {vn(toa('tot_nhat', b).sai_so_tb_m)} m |")
if len(tb):
    L.append(f"| Thời gian định vị | {vn(t0.ms_per_fp)} ms/fp | {vn(tb.iloc[0].ms_per_fp)} ms/fp |")
    L.append(f"| Radio map | {vn(t0.radio_map_mb,1)} MB | {vn(tb.iloc[0].radio_map_mb,1)} MB |")
L.append(f"\nĐã thử {J['so_cau_hinh_da_thu']} cấu hình HUIM. Thuật toán tìm union khớp EFIM ở {ok}/{len(CHK)} mức θ "
         "mà EFIM liệt kê xong.\n")
L.append("## Tập test và giao thức (vì sao tin được con số trên tập test)\n")
L.append("**Tập test = validationData (1.111 mẫu).** Kho UCI chỉ công bố hai file có nhãn của UJIIndoorLoc "
         "và gọi validationData.csv là \"1111 validation/test records\" (archive.ics.uci.edu/dataset/310/ujiindoorloc). "
         "Ở đây nó đóng vai trò tập test; vai trò validation (chọn tham số) do 6 fold dev tách từ "
         "trainingData đảm nhận. Trong `so_lieu/`, cột `test_*` là đo trên tập test, cột `dev_*` là "
         "trung bình 6 fold dev.\n")
L.append("Mọi lựa chọn (model, θ, phạm vi khai phá, quy tắc chọn AP, ensemble) dựa trên sai số trung bình của "
         "6 fold dev - GroupKFold theo USERID trên trainingData. Tập test (validationData) chỉ được đánh giá để báo cáo, "
         "không tham gia chọn. Riêng dev hơi lạc quan vì HUI được khai phá trên toàn trainingData (như nhau cho mọi "
         "cấu hình).\n")
L.append("## Nội dung thư mục\n")
L.append("| Đường dẫn | Nội dung |")
L.append("|---|---|")
for p in docx:
    L.append(f"| `{p.name}` | báo cáo Word |")
for p in pptx:
    L.append(f"| `{p.name}` | slide PowerPoint 16:9, biểu đồ gốc sửa được |")
L.append("| `diagram/H01 ... H15` | mỗi hình có `.png` (dùng trong Word/PowerPoint) và `.svg` (vector) |")
for n in so:
    L.append(f"| `so_lieu/{n}` | {MO_TA_SO_LIEU.get(n, '')} |")
for n in ma:
    L.append(f"| `ma_nguon/{n}` | {MO_TA_MA.get(n, '')} |")
L.append("\n### Danh sách hình\n")
for p in hinh:
    L.append(f"- `diagram/{p.name}`")
L.append("\n## Chạy lại\n")
L.append("Từ thư mục gốc dự án (`D:\\HUIM-IPS-`):\n")
L.append("```")
L.append("python BAOCAO/ma_nguon/00_chay_lai_toan_bo.py            # thí nghiệm + báo cáo (2-3 giờ, 12 nhân)")
L.append("python BAOCAO/ma_nguon/00_chay_lai_toan_bo.py --bao-cao  # chỉ dựng lại so_lieu, diagram, docx, pptx")
L.append("```\n")
L.append("Kết quả thô của thí nghiệm nằm ở `results/huim_opt/` (bảng từng bước, dự đoán từng mẫu `preds/*.npz`, "
         "union theo θ `union_*.npz`, `levels/`). Bộ dữ liệu UJIIndoorLoc (Torres-Sospedra và cộng sự, IPIN 2014) "
         "được dùng nguyên bản, không chỉnh sửa.")
(BAOCAO / "00_HUONG_DAN_DOC.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("đã ghi", BAOCAO / "00_HUONG_DAN_DOC.md")
