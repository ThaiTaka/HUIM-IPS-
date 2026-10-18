# Hướng dẫn đọc thư mục BAOCAO

Đề tài: **Ứng dụng khai thác tập mục lợi ích cao (HUIM) trong hệ thống định vị trong nhà.**
Hệ thống định vị chỉ dùng HUIM: mỗi điểm tham chiếu là một ô, EFIM khai thác tập HUI của từng ô,
tập HUI là mô hình định vị. Tầng và các ô ứng viên được chọn theo điểm khớp giữa vân tay và HUI của các ô
(Bước 1–7). Với UJIIndoorLoc, Bước 8 xếp hạng lại các ô ứng viên bằng bằng chứng rút ra từ ba mô hình HUI;
một bộ hồi quy học trên dev chỉ cân các bằng chứng đó. Hệ thống không dùng k-NN và không lưu vân tay huấn luyện.

## Nội dung thư mục

| Thành phần | Nội dung |
|---|---|
| `Bao_cao_HUIM_IPS_UJIIndoorLoc.docx` | Báo cáo theo bố cục luận văn: tóm tắt, mục lục, 5 chương, tài liệu tham khảo, phụ lục. Công thức là phương trình Word, sửa được trực tiếp. |
| `Slide_HUIM_IPS_UJIIndoorLoc.pptx` | Bài thuyết trình 22 slide, có ghi chú cho người trình bày. |
| `diagram/` | 10 sơ đồ mô hình từ đầu vào tới đầu ra (xem bảng dưới). |
| `so_lieu/` | Số liệu, dự đoán từng mẫu và công cụ kiểm chứng sai số trung bình. |
| `ma_nguon/` | Mã nguồn hệ thống, kiểm thử và các script dựng thư mục này. |

Nếu Word hỏi có cập nhật các trường (field) khi mở báo cáo, chọn **Yes** để làm mới số trang
trong mục lục. Mục lục đã được điền sẵn nên không cập nhật cũng không sao.

## Sơ đồ mô hình (`diagram/`)

Các sơ đồ bước 1–8 dùng một vân tay thật: dòng 573 của validationData (UJIIndoorLoc), truy vấn có sai số bằng trung vị của mô hình cuối.

| File | Bước |
|---|---|
| `d01_tong_quan.png` | Toàn hệ thống: pha huấn luyện và pha định vị |
| `d02_buoc1_utility.png` | Bước 1: RSSI thành lợi ích nội q(i,T), dạng rank |
| `d03_buoc2_o_giao_dich.png` | Bước 2: một ô (điểm tham chiếu) là một cơ sở dữ liệu giao dịch |
| `d04_buoc3_efim.png` | Bước 3: EFIM liệt kê HUI của ô, hai chặn trên lu và su |
| `d05_buoc4_mo_hinh.png` | Bước 4: mô hình là tập HUI của mọi ô |
| `d06_buoc5_cham_diem.png` | Bước 5: chấm điểm khớp P_c, V_c, score_c |
| `d07_buoc6_lam_muot_tang.png` | Bước 6: làm mượt không gian, chọn tòa và tầng |
| `d08_buoc7_toa_do.png` | Bước 7: ô ứng viên của tầng đã chọn và ước lượng ban đầu |
| `d09_buoc8_xep_hang_lai.png` | Bước 8: bằng chứng HUI, bộ hồi quy, toạ độ cuối |
| `d10_giao_thuc.png` | Giao thức đánh giá và kiểm chứng |

## Kết quả trên tập kiểm tra

Sai số là khoảng cách Euclid theo mét thực địa. Tham số được chọn trên các fold dev, và mỗi tập kiểm tra chỉ được chấm một lần.

| Bộ dữ liệu | Tập kiểm tra | Số mẫu | Sai số TB (m) | Trung vị (m) | Dưới 7 m |
|---|---|---:|---:|---:|---|
| UJIIndoorLoc (mô hình cuối, Bước 1–8) | validationData | 1 111 | 6,87 | 5,14 | đạt |
| UJI_LIB tầng 3 | Test-01 | 7 200 | 2,57 | 2,17 | đạt |
| UJI_LIB tầng 3 | Test-02 | 7 200 | 2,68 | 2,31 | đạt |
| DLULIB | Testing | 6 500 | 6,01 | 4,88 | đạt |
| HCXY | test_HCXY | 860 | 2,82 | 2,14 | đạt |
| HUS | testcase1 / testcase2 | 205 / 205 | 1,30 / 1,54 | 1,03 / 1,30 | đạt |
| HUS (khử trùng lặp) | testcase1 / testcase2 | 205 / 205 | 1,30 / 1,54 | 1,05 / 1,30 | đạt |

Với UJIIndoorLoc, Bước 1–7 cho 8,06 m (v4). Bước 8 được chọn vì sai số trên dev thấp hơn
(7,65 m xuống 6,83 m); sau khi chọn, tập kiểm tra được chấm đúng một lần và cho 6,87 m.
Kết quả dưới 7 m với biên nhỏ: sai số chuẩn của trung bình là 0,20 m (mục 4.7).
Phần sai số còn lại chủ yếu nằm trong tầng (75,9%), và 9 trong 11 điện thoại của tập kiểm tra không có trong tập huấn luyện.

## Kiểm chứng sai số trung bình (`so_lieu/`)

Có ba cách kiểm tra độc lập. Cả ba đều tính lại sai số từ toạ độ thật và toạ độ dự đoán của từng mẫu, rồi so với con số trong báo cáo.

1. **Excel:** mở `so_lieu/kiem_chung_mean.xlsx`.
   - Sheet `Tong_hop`: cột *Kết luận* ghi KHỚP cho từng tập kiểm tra.
   - Mỗi sheet `<dataset>_<tập test>`: cột F tính sai số từng mẫu bằng `=SQRT((x̂−x)^2+(ŷ−y)^2)*hệ số`, ô L3 là `AVERAGE`.
   - Sheet `Vi_du_UJI_mot_truy_van` dựng lại toạ độ của một truy vấn từ 12 ô HUIM chọn, bằng `SUMPRODUCT`.
2. **Python (chỉ thư viện chuẩn):** trong thư mục `so_lieu`, chạy `python kiem_tra_mean.py`. Script in KHỚP hoặc LỆCH cho từng tập kiểm tra.
3. **Chương trình kiểm chứng độc lập:**
   - `kiem_chung_doc_lap.json` lưu kết quả của `ma_nguon/src/verify_huim_only.py`. Chương trình này không gọi EFIM hay bộ định vị; nó chạy 42 phép kiểm và không có phép nào thất bại.
   - `kiem_chung_v6_uji.json` lưu kết quả của `ma_nguon/src/verify_v6.py` cho mô hình cuối của UJIIndoorLoc: 8 phép kiểm, không phép nào thất bại. Các phép kiểm xác nhận rằng toạ độ dự đoán bằng tổng có trọng số của các ô được chọn và các ô nằm trên tầng dự đoán.

Hệ số mét: UJIIndoorLoc dùng toạ độ Web Mercator, nên mét thực địa = mét chiếu × 0,766126. Các bộ dữ liệu còn lại dùng mét trực tiếp, hệ số 1.

| File số liệu | Nội dung |
|---|---|
| `01_ket_qua_tong_hop.csv` | Kết quả mọi tập kiểm tra |
| `02_cau_hinh_chon_tren_dev.csv` | Cấu hình được chọn trên dev |
| `03_lich_su_phien_ban_uji.csv` | Các phiên bản đã thử trên UJIIndoorLoc |
| `04_tach_sai_so_theo_tang_uji.csv` | Sai số tách theo đoán đúng hoặc sai tầng |
| `05_tham_chieu.csv` | Các hệ thống tham chiếu dùng k-NN |
| `06_mo_ta_du_lieu.csv`, `07_khai_thac_theo_o.csv` | Mô tả dữ liệu, thống kê khai thác theo ô |
| `du_doan/*.csv` | Dự đoán từng mẫu, kèm các ô được chọn và trọng số (UJIIndoorLoc: thêm cột ước lượng ban đầu v4) |
| `mo_hinh_uji_cells.csv` | Toạ độ các ô của mô hình UJIIndoorLoc |
| `du_lieu_bao_cao.json` | Nguồn số liệu duy nhất của báo cáo và slide |

## Dựng lại thư mục

Chạy các lệnh sau từ thư mục gốc dự án, sau khi có kết quả trong `results/huim_only` (Bước 8 của UJIIndoorLoc: xem `ma_nguon/README.md`):

```bash
python src/baocao/export_data.py        # so_lieu/*.csv, du_lieu_bao_cao.json
python src/baocao/make_so_lieu_kit.py   # kiem_chung_mean.xlsx, kiem_tra_mean.py
python src/plots_huim_only.py           # figures/huim_only (biểu đồ kết quả)
python src/baocao/make_diagrams.py      # diagram/*.png
node   src/baocao/build_report.js       # báo cáo .docx (cần npm docx, LibreOffice để điền mục lục)
node   src/baocao/build_slides.js       # slide .pptx (cần npm pptxgenjs, matplotlib)
python src/baocao/make_ma_nguon.py      # ma_nguon/
```
