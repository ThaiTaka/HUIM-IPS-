# Kiểm chứng sai số V7 (6,309 m trên validationData)

Ba cách kiểm tra độc lập; cả ba tính lại sai số từ **toạ độ thật** và **toạ độ dự đoán** của từng vân tay, rồi so với con số trong báo cáo.

1. **Excel** — mở `kiem_chung_V7_mean.xlsx`:
   - `Tong_hop`: cột *Kết luận* ghi KHỚP cho từng mô hình (V4, V5, V6, V6 tái tạo, V7-A, V7-B, V7-C1, V7-C2, V7-D).
   - Mỗi sheet mô hình: cột F tính sai số từng mẫu bằng `=SQRT((x̂−x)^2+(ŷ−y)^2)*g`; B3 là `AVERAGE` (sai số trung bình), B4 trung vị, B5 P90.
   - `V7C2_dung_lai_toa_do`: dựng lại (x̂, ŷ) = Σ wᵢ·(xᵢ, yᵢ) từ **30 trọng số và tâm 30 ô** bằng `SUMPRODUCT`, rồi tính sai số.
   - `Vi_du_mot_truy_van`: một vân tay thật (hàng 335), V6\* sai 7,9938 m, V7 sai 4,6357 m, dựng bằng tay.
   - `Dev_OOF`: dev out-of-fold của V6\* và V7-C2 (19.937 vân tay; 19.861 có ít nhất một AP).
2. **Python, chỉ thư viện chuẩn** — trong thư mục này chạy `python kiem_tra_V7.py`; script in KHỚP hoặc LỆCH cho từng mô hình, dựng lại toạ độ V7-C2 từ trọng số và tính lại dev.
3. **Chương trình kiểm chứng độc lập của dự án** — `kiem_chung_V7.json` lưu kết quả của `src/v7/verify_v7.py`: 16 phép kiểm, 0 thất bại
   (tính lại sai số, trọng số ≥ 0 và tổng bằng 1, tọa độ = tổng có trọng số của tâm ô, ô nằm trên tầng dự đoán, fold rời nhau theo điện thoại,
   cache cùng nguồn dữ liệu, không k-NN, EFIM = vét cạn, tái lập theo seed, V6 không bị đổi).

Hệ số mét: UJIIndoorLoc dùng toạ độ Web Mercator nên mét thực địa = đơn vị toạ độ × **0,766126**.

| Tệp | Nội dung |
|---|---|
| `00_ket_qua_tong_hop_V7.csv` | số liệu báo cáo (trung bình, trung vị, P90, đúng tòa+tầng) của từng mô hình |
| `du_doan/*.csv` | dự đoán từng mẫu của validationData; các tệp V7 kèm 30 ô ứng viên và 30 trọng số |
| `du_doan_dev/dev_oof_V6star_V7C2.csv` | toạ độ dự đoán out-of-fold của dev |
| `mo_hinh_uji_cells.csv` | toạ độ 933 ô tham chiếu (chỉ số ô = số dòng, từ 0) |
| `du_lieu_bao_cao_V7.json` | nguồn số liệu duy nhất của slide V7 |
| `kiem_chung_V7.json` | kết quả `verify_v7.py` |

Tự kiểm bằng tay một vân tay: lấy `pred_x, pred_y, true_x, true_y` của một dòng, tính √((x̂−x)²+(ŷ−y)²)×0,766126. Ví dụ hàng 335 của validationData: Δx = −0,99923; Δy = 5,96774; √(…) = 6,05050; × 0,766126 = 4,6357 m.
