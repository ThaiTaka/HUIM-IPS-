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

## HUIM-IPS V7: slide và kiểm chứng 6,309 m

V7 (sau V6) đạt **6,309 m** trên validationData (V6: 6,866 m); mục tiêu dưới 6 m **chưa đạt**. Báo cáo văn bản của V7 nằm ở `../BAOCAO_V7/`
(`HUIM_IPS_V7_RESEARCH_REPORT.md`, `V6_V7_COMPARISON.md`, `README_V7.md`); mã ở `../src/v7/`. Các tệp dưới đây thuộc thư mục này.

| Thành phần | Nội dung |
|---|---|
| `Slide_HUIM_IPS_V7.pptx` | 55 slide cùng thiết kế với slide cũ: lý thuyết (vân tay Wi-Fi, HUIM, EFIM, điểm khớp) kèm ví dụ số; các bước thuật toán V7 tới 6,309 m với công thức có chú thích ký hiệu; ví dụ trọn vẹn một vân tay thật tính tay (hàng 335); kết quả; **kiểm chứng 6,309 m**; kết luận; **slide cuối: tóm tắt một slide cho người mới học HUIM trong IPS** (lý thuyết + ví dụ). Có ghi chú cho người trình bày. |
| `Slide_HUIM_IPS_V7_day_du.pptx` | **Bộ slide V7 đầy đủ để thuyết trình** (55 slide, có 3 diagram của báo cáo V7: F5, F6, F8): đi theo đúng đường của dữ liệu, từ UJIIndoorLoc đến 6,309 m trên tập kiểm tra, không dạy lại lý thuyết HUIM. Mỗi slide thuật toán có công thức, **chú thích mọi ký hiệu**, *vì sao chọn* và *vì sao các con số này* (đếm / định nghĩa / đo / quy ước / chọn trên dev / ngân sách); **ghi chú của từng slide là kịch bản thuyết trình** có ví dụ đời thường (quán trà sữa, thi chạy, bỏ phiếu…). Có ví dụ trọn vẹn hàng 335, kết quả, kiểm chứng, hỏi–đáp, bản đồ nguồn gốc con số và slide tóm tắt. Số liệu: `so_lieu_V7/du_lieu_dataset_uji.json`, `nguon_goc_hang_so.json`, `du_lieu_bao_cao_V7.json`. |
| `Slide_HUIM_IPS_V7_bo_sung.pptx` | **Bản bổ sung để trả lời vấn đáp** (71 slide = 55 slide gốc + 16 slide đánh dấu BỔ SUNG): sau mỗi thuật toán có slide *"Vì sao chọn vậy"* (0,766126; ba lợi ích rank/abs/rel, −104/0 dBm, 40 dB; θ = 20% và ngân sách 10 s/10 000 HUI/×1,25; γ, τ, β; σ, kf, K = 30; V6 m, λ; 5 góc nhìn; 49 cột và ×4; MLP 32/16 và 7 360 tham số; softmax; mất mát, Adam, epoch, ε; 6 fold và 5 thành viên) và cuối bộ có 2 slide hỏi–đáp dự kiến, 2 slide *"bản đồ nguồn gốc con số"* (mỗi số là đếm / định nghĩa / đo / quy ước / chọn trên dev / ngân sách). Mỗi số đều tính lại được từ `so_lieu_V7/nguon_goc_hang_so.json`; chỗ nào chưa dò thì ghi thẳng "chưa dò". Slide gốc không bị sửa; có thể ẩn các slide BỔ SUNG khi trình bày. |
| `so_lieu_V7/` | Bộ kiểm chứng sai số V7, cùng cấu trúc với `so_lieu/` (xem bên dưới) |
| `ma_nguon/tao_bao_cao/*_v7*`, `export_data_v7.py`, `make_so_lieu_kit_v7.py`, `recalc_xlsx.ps1` | Bản sao các script dựng slide V7 và bộ kiểm chứng (bản gốc ở `src/baocao/`) |

### Kiểm chứng 6,309 m (`so_lieu_V7/`)

Ba cách kiểm tra độc lập; cả ba tính lại sai số từ toạ độ thật và toạ độ dự đoán của từng vân tay (hệ số mét 0,766126):

1. **Excel:** `so_lieu_V7/kiem_chung_V7_mean.xlsx`. Sheet `Tong_hop`: cột *Kết luận* ghi KHỚP cho 9 mô hình (V4, V5, V6, V6 tái tạo, V7-A, V7-B, V7-C1, V7-C2, V7-D);
   mỗi sheet mô hình có công thức sai số từng mẫu và `AVERAGE`; `V7C2_dung_lai_toa_do` dựng lại (x̂, ŷ) = Σ w·tâm ô từ 30 trọng số; `Vi_du_mot_truy_van` dựng tay hàng 335; `Dev_OOF` tính lại dev.
2. **Python (chỉ thư viện chuẩn):** trong `so_lieu_V7` chạy `python kiem_tra_V7.py`; in KHỚP/LỆCH cho từng mô hình, dựng lại toạ độ V7-C2 và tính lại dev (kết quả: "Tất cả khớp").
3. **Chương trình kiểm chứng của dự án:** `so_lieu_V7/kiem_chung_V7.json` lưu kết quả `src/v7/verify_v7.py`: 16 phép kiểm, 0 thất bại.

Dựng lại slide và bộ kiểm chứng từ thư mục gốc dự án (sau khi có kết quả V7 trong `results/huim_only/uji/v7`):

```bash
python src/baocao/export_data_v7.py          # so_lieu_V7/du_lieu_bao_cao_V7.json (nguồn số liệu của slide)
python src/baocao/make_so_lieu_kit_v7.py     # so_lieu_V7/*.xlsx, kiem_tra_V7.py, du_doan/*.csv
powershell -File src/baocao/recalc_xlsx.ps1 BAOCAO/so_lieu_V7/kiem_chung_V7_mean.xlsx   # Excel tính lại để lưu giá trị
node src/baocao/build_slides_v7.js           # Slide_HUIM_IPS_V7.pptx (cần npm pptxgenjs, Python có matplotlib, pandas)
python src/baocao/export_why_v7.py           # so_lieu_V7/nguon_goc_hang_so.json (bằng chứng cho các slide bổ sung)
SUPP=1 node src/baocao/build_slides_v7.js    # Slide_HUIM_IPS_V7_bo_sung.pptx (đặt biến môi trường SUPP=1 trước lệnh node)
python src/baocao/export_dataset_v7.py       # so_lieu_V7/du_lieu_dataset_uji.json (số liệu dataset tính từ CSV gốc)
node src/baocao/build_slides_v7_day_du.js    # Slide_HUIM_IPS_V7_day_du.pptx (bộ slide đầy đủ có kịch bản)
```
