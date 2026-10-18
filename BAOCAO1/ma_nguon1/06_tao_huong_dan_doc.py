"""BAOCAO1 / bước 6 - viết BAOCAO1/00_HUONG_DAN_DOC.md: đọc gì trước, mỗi file là gì,
các con số chính, cách chạy lại; chép bản sao mã nguồn thí nghiệm vào ma_nguon/ban_sao_src.
Danh sách file được lấy từ thư mục thật.

    python BAOCAO1/ma_nguon/06_tao_huong_dan_doc.py
"""
from __future__ import annotations

import shutil

import pandas as pd

from hinh_chung import (BAOCAO, DIAGRAM, KEYS, ROOT, SO_LIEU, TAP_TEST, TEN_DS, cau_hinh,
                        theta_txt, vn)
from nhan import lbl, theta_cua

J = cau_hinh()
B = J["bo_du_lieu"]
UJI = J["uji_tham_chieu_BAOCAO"]
KQ = pd.read_csv(SO_LIEU / "12_ket_qua_theo_tap_test.csv")
CHK = pd.read_csv(SO_LIEU / "02_kiem_chung_union_vs_EFIM.csv")
TM = pd.read_csv(SO_LIEU / "10_buoc8_thoi_gian_bo_nho.csv")
ok = int(CHK.identical.astype(str).str.lower().eq("true").sum())

MO_TA_SO_LIEU = {
    "00_cau_hinh_cuoi_cung.json": "theo từng bộ dữ liệu: cấu hình ban đầu, đơn tốt nhất, tốt nhất, cân bằng; "
                                  "bộ định vị; thời gian - bộ nhớ; tham chiếu UJIIndoorLoc (BAOCAO/)",
    "01_du_lieu.csv": "mô tả 4 bộ dữ liệu: số AP, dòng, vị trí, tập test, cách chia fold dev, làm sạch",
    "02_kiem_chung_union_vs_EFIM.csv": "union của thuật toán tìm kiếm so với union EFIM ở mọi θ EFIM chạy xong",
    "03_so_AP_theo_minUtil.csv": "số AP trong union theo bộ dữ liệu × phạm vi (chung / vùng) × model × θ; "
                                 "thời gian, bộ nhớ, số nút tìm kiếm",
    "04_EFIM_so_HUI_thoi_gian_bo_nho.csv": "EFIM liệt kê đầy đủ: số HUI, trạng thái, thời gian, bộ nhớ theo θ",
    "05_buoc3_HUIM_chung.csv": "bước 3: HUIM chung ở mọi θ (dev, tập test)",
    "06_buoc4_HUIM_theo_vung.csv": "bước 4: HUIM theo vùng / tầng ở mọi θ",
    "07_buoc5_bo_dinh_vi_chon_lai.csv": "bước 5: bước 3 / 4 chạy lại với bộ định vị chọn lại trên AP HUIM",
    "07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv": "bước 5: các giai đoạn chọn bộ định vị và sai số dev",
    "08_buoc6_quy_tac_chon_AP.csv": "bước 6: union / top-n / frequent / weighted",
    "09_buoc7_ensemble.csv": "bước 7: ensemble 2-3 cấu hình (trung bình / trung vị)",
    "10_buoc8_thoi_gian_bo_nho.csv": "bước 8: ms / vân tay, radio map MB, RSS, thời gian dựng mô hình",
    "11_xep_hang_tat_ca_cau_hinh.csv": "mọi cấu hình đã thử, xếp theo sai số dev trong từng bộ dữ liệu",
    "12_ket_qua_theo_tap_test.csv": "ban đầu / đơn tốt nhất / tốt nhất trên từng file test: TB, trung vị, p90, ...",
    "13_du_doan_tung_mau_tap_test.csv": "từng mẫu test: vị trí thật, dự đoán, sai số (ban đầu và tốt nhất)",
}
MO_TA_MA = {
    "00_chay_lai_toan_bo.py": "chạy lại tất cả theo thứ tự (thêm --bao-cao để bỏ qua thí nghiệm)",
    "01_chay_thi_nghiem.py": "thí nghiệm: union HUI mọi θ, kiểm chứng với EFIM, các bước 3-8",
    "02_tong_hop_so_lieu.py": "gom kết quả results/huim_multi thành so_lieu/",
    "03_ve_bieu_do.py": "vẽ 15 hình vào diagram/ (PNG + SVG)",
    "04_tao_bao_cao_word.py": "tạo file Word",
    "05_tao_slide_pptx.py": "tạo file PowerPoint",
    "06_tao_huong_dan_doc.py": "tạo file hướng dẫn này",
    "hinh_chung.py": "màu, font, định dạng số, tên bộ dữ liệu dùng chung",
    "word_chung.py": "hàm dựng bảng, hình, chú thích cho Word",
    "slide_chung.py": "hàm dựng chữ, thẻ số, biểu đồ gốc cho PowerPoint",
    "nhan.py": "tên tiếng Việt của mỗi cấu hình (luôn kèm θ)",
    "nhan_xet.py": "các nhận xét / kết luận rút ra từ số liệu (dùng chung cho Word và PowerPoint)",
    "ban_sao_src": "bản sao mã nguồn thí nghiệm của src/ tại lúc tạo báo cáo (bản gốc vẫn ở src/)",
}

SRC_FILES = ["huim_multi.py", "multi_datasets.py", "huim/union_search.py", "huim/efim.py",
             "huim_opt.py", "utility_models.py", "preprocess_uji.py", "optimize_positioning.py",
             "feature_selection.py", "ips_model.py", "utils.py", "run_multi_dataset.py"]
dst = BAOCAO / "ma_nguon" / "ban_sao_src"
if dst.exists():
    shutil.rmtree(dst)
for f in SRC_FILES:
    target = dst / f
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "src" / f, target)
(dst / "DOC_TRUOC.md").write_text("\n".join([
    "Bản sao các file trong src/ mà thí nghiệm BAOCAO1 dùng, chép lúc tạo báo cáo để đọc kèm.",
    "Chạy thật luôn dùng bản ở src/ (BAOCAO1/ma_nguon/01_chay_thi_nghiem.py gọi src/).",
    "",
    "- huim_multi.py: toàn bộ thí nghiệm BAOCAO1 (union mọi θ, bước 3-8, kiểm chứng với EFIM)",
    "- multi_datasets.py: đọc 4 bộ dữ liệu về một khuôn chung (AP, toạ độ, tầng, nhóm fold, làm sạch)",
    "- huim/union_search.py: thuật toán tìm union HUI chính xác; huim/efim.py: EFIM liệt kê đầy đủ",
    "- utility_models.py: q(i,T) và p(i) của Model A/B/C; preprocess_uji.py: chuẩn hoá RSSI",
    "- optimize_positioning.py: bộ định vị k-NN và quy trình chọn trên dev",
    "- huim_opt.py: WeightedPositioner (quy tắc weighted); feature_selection.py: thống kê AP trên HUI",
    "- run_multi_dataset.py: lần chạy đa dữ liệu trước (EFIM, bộ định vị gốc của mỗi bộ dữ liệu)",
]) + "\n", encoding="utf-8")


def kq(k, vai, tn):
    return KQ[(KQ.bo_du_lieu == k) & (KQ.vai_tro == vai) & (KQ.tap_test == tn)].iloc[0]


docx = sorted(BAOCAO.glob("*.docx"))
pptx = sorted(BAOCAO.glob("Slide_*.pptx"))
hinh = sorted(DIAGRAM.glob("*.png"))
so = sorted(p.name for p in SO_LIEU.iterdir())
ma = sorted(p.name for p in (BAOCAO / "ma_nguon").iterdir() if p.name != "__pycache__")

L = []
L.append("# BAOCAO1 - HUIM cho định vị trong nhà trên 4 bộ dữ liệu (chỉ cấu hình có HUIM)\n")
L.append("Thư mục này áp dụng quy trình HUIM của `BAOCAO/` (UJIIndoorLoc) cho 4 bộ dữ liệu còn lại của "
         "`dataset-20261013T020803Z-1-001/dataset`: **UJI_LIB tầng 3, DLULIB, HCXY, HUS**. Thư mục `syl`, "
         "`tuji`, `UJI_LIB_DB_Floor_5` rỗng (cả trong file zip) nên không chạy được; UJIIndoorLoc đã làm ở "
         "`BAOCAO/`.\n")
L.append("## Đọc theo thứ tự này\n")
L.append(f"1. **`{docx[0].name if docx else 'Bao_cao_...docx'}`** - báo cáo đầy đủ. Đọc khung *Kết quả chính* "
         "ở trang 1, rồi mục 1.2-1.3 (tập test của từng bộ dữ liệu, giao thức chọn trên dev) và mục 7 "
         "(kết quả cuối cùng trên tập test).")
L.append(f"2. **`{pptx[0].name if pptx else 'Slide_...pptx'}`** - bản trình bày, cùng số liệu với báo cáo.")
L.append("3. **`diagram/`** - 15 hình; mọi hình đều ghi ngưỡng minUtil θ. Hình 1 là sơ đồ luồng một trang, "
         "Hình 10 là kết quả chính.")
L.append("4. **`so_lieu/`** - mọi bảng số mà hình và báo cáo đọc; dùng để kiểm tra lại từng con số.")
L.append("5. **`ma_nguon/`** - script sinh ra tất cả những thứ trên.\n")

L.append("## Tập test\n")
L.append("Mỗi bộ dữ liệu đi kèm file test riêng; đó là **tập test** của báo cáo, chỉ dùng để báo cáo, "
         "không dùng để chọn bất cứ thứ gì. Mọi lựa chọn dựa trên 6 fold dev tách từ tập train. Trong "
         "`so_lieu/`, cột `test_*` là tập test thứ nhất, `test2_*` là tập test thứ hai (cột `tap_test`, "
         "`tap_test2` ghi tên file), `dev_*` là trung bình 6 fold dev.\n")
L.append("| Bộ dữ liệu | Tập test | Ban đầu | **Tốt nhất (chọn theo dev)** | Cấu hình tốt nhất | AP |")
L.append("|---|---|---|---|---|---|")
for k in KEYS:
    for _, tn in TAP_TEST[k].items():
        L.append(f"| {TEN_DS[k]} | {tn} | {vn(kq(k, 'ban_dau', tn).sai_so_tb_m)} m | "
                 f"**{vn(kq(k, 'tot_nhat', tn).sai_so_tb_m)} m** | {lbl(B[k]['best']['config'], k)} | "
                 f"{int(B[k]['start']['n_ap'])} → {int(B[k]['best']['n_ap'])} |")
L.append(f"| UJIIndoorLoc (`BAOCAO/`) | validationData | {vn(UJI['ban_dau']['test_mean_m'])} m | "
         f"**{vn(UJI['tot_nhat']['test_mean_m'])} m** | xem `BAOCAO/` | "
         f"{int(UJI['ban_dau']['n_ap'])} → {int(UJI['tot_nhat']['n_ap'])} |")
L.append(f"\nThuật toán tìm union khớp EFIM ở {ok}/{len(CHK)} mức θ mà EFIM liệt kê xong.\n")

L.append("## Nội dung thư mục\n")
L.append("| Đường dẫn | Nội dung |")
L.append("|---|---|")
for p in docx:
    L.append(f"| `{p.name}` | báo cáo Word |")
for p in pptx:
    L.append(f"| `{p.name}` | slide PowerPoint 16:9, biểu đồ cột gốc sửa được |")
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
L.append("python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py            # thí nghiệm + báo cáo (khoảng 1 giờ, 12 nhân)")
L.append("python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py --bao-cao  # chỉ dựng lại so_lieu, diagram, docx, pptx")
L.append("```\n")
L.append("Kết quả thô của thí nghiệm nằm ở `results/huim_multi/<bộ dữ liệu>/` (bảng từng bước, dự đoán từng "
         "mẫu `preds/*.npz`, union theo θ `union/*.npz`). Thí nghiệm cần kết quả của lần chạy đa dữ liệu "
         "trước ở `results/multi_dataset/` (EFIM, bộ định vị gốc). Dữ liệu đọc nguyên bản từ thư mục "
         "`dataset-20261013T020803Z-1-001/dataset/`; phần làm sạch duy nhất được ghi ở `so_lieu/01_du_lieu.csv`.")
(BAOCAO / "00_HUONG_DAN_DOC.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("đã ghi", BAOCAO / "00_HUONG_DAN_DOC.md")
