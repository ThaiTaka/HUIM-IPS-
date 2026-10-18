# BAOCAO1 - HUIM cho định vị trong nhà trên 4 bộ dữ liệu (chỉ cấu hình có HUIM)

Thư mục này áp dụng quy trình HUIM của `BAOCAO/` (UJIIndoorLoc) cho 4 bộ dữ liệu còn lại của `dataset-20261013T020803Z-1-001/dataset`: **UJI_LIB tầng 3, DLULIB, HCXY, HUS**. Thư mục `syl`, `tuji`, `UJI_LIB_DB_Floor_5` rỗng (cả trong file zip) nên không chạy được; UJIIndoorLoc đã làm ở `BAOCAO/`.

## Đọc theo thứ tự này

1. **`Bao_cao_HUIM_IPS_4_bo_du_lieu.docx`** - báo cáo đầy đủ. Đọc khung *Kết quả chính* ở trang 1, rồi mục 1.2-1.3 (tập test của từng bộ dữ liệu, giao thức chọn trên dev) và mục 7 (kết quả cuối cùng trên tập test).
2. **`Slide_HUIM_IPS_4_bo_du_lieu.pptx`** - bản trình bày, cùng số liệu với báo cáo.
3. **`diagram/`** - 15 hình; mọi hình đều ghi ngưỡng minUtil θ. Hình 1 là sơ đồ luồng một trang, Hình 10 là kết quả chính.
4. **`so_lieu/`** - mọi bảng số mà hình và báo cáo đọc; dùng để kiểm tra lại từng con số.
5. **`ma_nguon/`** - script sinh ra tất cả những thứ trên.

## Tập test

Mỗi bộ dữ liệu đi kèm file test riêng; đó là **tập test** của báo cáo, chỉ dùng để báo cáo, không dùng để chọn bất cứ thứ gì. Mọi lựa chọn dựa trên 6 fold dev tách từ tập train. Trong `so_lieu/`, cột `test_*` là tập test thứ nhất, `test2_*` là tập test thứ hai (cột `tap_test`, `tap_test2` ghi tên file), `dev_*` là trung bình 6 fold dev.

| Bộ dữ liệu | Tập test | Ban đầu | **Tốt nhất (chọn theo dev)** | Cấu hình tốt nhất | AP |
|---|---|---|---|---|---|
| UJI_LIB tầng 3 | Test-01 | 1,21 m | **1,14 m** | Ensemble trung vị: Theo vùng A, θ = 1,5 %, định vị chọn lại + Theo vùng C, θ = 0,25 % + Chung B, θ = 1 % | 83 → 168 |
| UJI_LIB tầng 3 | Test-02 | 2,04 m | **2,06 m** | Ensemble trung vị: Theo vùng A, θ = 1,5 %, định vị chọn lại + Theo vùng C, θ = 0,25 % + Chung B, θ = 1 % | 83 → 168 |
| DLULIB | Testing | 3,43 m | **3,43 m** | Ensemble trung bình: Theo tầng A, θ = 0,25 % + Chung A, θ = 1 % | 17 → 17 |
| HCXY | test_HCXY | 2,12 m | **1,58 m** | Ensemble trung vị: Chung C, θ = 1 % + Chung B, θ = 1 % + Theo vùng B, θ = 3 % | 67 → 193 |
| HUS | testcase1 | 0,39 m | **0,39 m** | HUIM chung, Model A, θ = 20 % | 5 → 5 |
| HUS | testcase2 | 0,25 m | **0,25 m** | HUIM chung, Model A, θ = 20 % | 5 → 5 |
| UJIIndoorLoc (`BAOCAO/`) | validationData | 19,36 m | **5,28 m** | xem `BAOCAO/` | 86 → 310 |

Thuật toán tìm union khớp EFIM ở 128/128 mức θ mà EFIM liệt kê xong.

## Nội dung thư mục

| Đường dẫn | Nội dung |
|---|---|
| `Bao_cao_HUIM_IPS_4_bo_du_lieu.docx` | báo cáo Word |
| `Slide_HUIM_IPS_4_bo_du_lieu.pptx` | slide PowerPoint 16:9, biểu đồ cột gốc sửa được |
| `diagram/H01 ... H15` | mỗi hình có `.png` (dùng trong Word/PowerPoint) và `.svg` (vector) |
| `so_lieu/00_cau_hinh_cuoi_cung.json` | theo từng bộ dữ liệu: cấu hình ban đầu, đơn tốt nhất, tốt nhất, cân bằng; bộ định vị; thời gian - bộ nhớ; tham chiếu UJIIndoorLoc (BAOCAO/) |
| `so_lieu/01_du_lieu.csv` | mô tả 4 bộ dữ liệu: số AP, dòng, vị trí, tập test, cách chia fold dev, làm sạch |
| `so_lieu/02_kiem_chung_union_vs_EFIM.csv` | union của thuật toán tìm kiếm so với union EFIM ở mọi θ EFIM chạy xong |
| `so_lieu/03_so_AP_theo_minUtil.csv` | số AP trong union theo bộ dữ liệu × phạm vi (chung / vùng) × model × θ; thời gian, bộ nhớ, số nút tìm kiếm |
| `so_lieu/04_EFIM_so_HUI_thoi_gian_bo_nho.csv` | EFIM liệt kê đầy đủ: số HUI, trạng thái, thời gian, bộ nhớ theo θ |
| `so_lieu/05_buoc3_HUIM_chung.csv` | bước 3: HUIM chung ở mọi θ (dev, tập test) |
| `so_lieu/06_buoc4_HUIM_theo_vung.csv` | bước 4: HUIM theo vùng / tầng ở mọi θ |
| `so_lieu/07_buoc5_bo_dinh_vi_chon_lai.csv` | bước 5: bước 3 / 4 chạy lại với bộ định vị chọn lại trên AP HUIM |
| `so_lieu/07b_buoc5_cac_giai_doan_chon_bo_dinh_vi.csv` | bước 5: các giai đoạn chọn bộ định vị và sai số dev |
| `so_lieu/08_buoc6_quy_tac_chon_AP.csv` | bước 6: union / top-n / frequent / weighted |
| `so_lieu/09_buoc7_ensemble.csv` | bước 7: ensemble 2-3 cấu hình (trung bình / trung vị) |
| `so_lieu/10_buoc8_thoi_gian_bo_nho.csv` | bước 8: ms / vân tay, radio map MB, RSS, thời gian dựng mô hình |
| `so_lieu/11_xep_hang_tat_ca_cau_hinh.csv` | mọi cấu hình đã thử, xếp theo sai số dev trong từng bộ dữ liệu |
| `so_lieu/12_ket_qua_theo_tap_test.csv` | ban đầu / đơn tốt nhất / tốt nhất trên từng file test: TB, trung vị, p90, ... |
| `so_lieu/13_du_doan_tung_mau_tap_test.csv` | từng mẫu test: vị trí thật, dự đoán, sai số (ban đầu và tốt nhất) |
| `ma_nguon/00_chay_lai_toan_bo.py` | chạy lại tất cả theo thứ tự (thêm --bao-cao để bỏ qua thí nghiệm) |
| `ma_nguon/01_chay_thi_nghiem.py` | thí nghiệm: union HUI mọi θ, kiểm chứng với EFIM, các bước 3-8 |
| `ma_nguon/02_tong_hop_so_lieu.py` | gom kết quả results/huim_multi thành so_lieu/ |
| `ma_nguon/03_ve_bieu_do.py` | vẽ 15 hình vào diagram/ (PNG + SVG) |
| `ma_nguon/04_tao_bao_cao_word.py` | tạo file Word |
| `ma_nguon/05_tao_slide_pptx.py` | tạo file PowerPoint |
| `ma_nguon/06_tao_huong_dan_doc.py` | tạo file hướng dẫn này |
| `ma_nguon/ban_sao_src` | bản sao mã nguồn thí nghiệm của src/ tại lúc tạo báo cáo (bản gốc vẫn ở src/) |
| `ma_nguon/hinh_chung.py` | màu, font, định dạng số, tên bộ dữ liệu dùng chung |
| `ma_nguon/nhan.py` | tên tiếng Việt của mỗi cấu hình (luôn kèm θ) |
| `ma_nguon/nhan_xet.py` | các nhận xét / kết luận rút ra từ số liệu (dùng chung cho Word và PowerPoint) |
| `ma_nguon/slide_chung.py` | hàm dựng chữ, thẻ số, biểu đồ gốc cho PowerPoint |
| `ma_nguon/word_chung.py` | hàm dựng bảng, hình, chú thích cho Word |

### Danh sách hình

- `diagram/H01_so_do_luong_HUIM_IPS.png`
- `diagram/H02_so_AP_theo_minUtil.png`
- `diagram/H03_thoi_gian_union_vs_EFIM.png`
- `diagram/H04_sai_so_theo_minUtil.png`
- `diagram/H05_danh_doi_AP_sai_so.png`
- `diagram/H06_theo_vung_vs_chung.png`
- `diagram/H07_bo_dinh_vi_chon_lai.png`
- `diagram/H08_quy_tac_chon_AP.png`
- `diagram/H09_ensemble.png`
- `diagram/H10_ban_dau_vs_tot_nhat.png`
- `diagram/H11_CDF_sai_so.png`
- `diagram/H12_ban_do_sai_so.png`
- `diagram/H13_thoi_gian_bo_nho_dinh_vi.png`
- `diagram/H14_bo_nho_khai_pha.png`
- `diagram/H15_sai_so_theo_vung_tang.png`

## Chạy lại

Từ thư mục gốc dự án (`D:\HUIM-IPS-`):

```
python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py            # thí nghiệm + báo cáo (khoảng 1 giờ, 12 nhân)
python BAOCAO1/ma_nguon/00_chay_lai_toan_bo.py --bao-cao  # chỉ dựng lại so_lieu, diagram, docx, pptx
```

Kết quả thô của thí nghiệm nằm ở `results/huim_multi/<bộ dữ liệu>/` (bảng từng bước, dự đoán từng mẫu `preds/*.npz`, union theo θ `union/*.npz`). Thí nghiệm cần kết quả của lần chạy đa dữ liệu trước ở `results/multi_dataset/` (EFIM, bộ định vị gốc). Dữ liệu đọc nguyên bản từ thư mục `dataset-20261013T020803Z-1-001/dataset/`; phần làm sạch duy nhất được ghi ở `so_lieu/01_du_lieu.csv`.
