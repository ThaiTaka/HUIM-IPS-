# So sánh HUIM-IPS V6 và V7

Mọi số lấy từ `BAOCAO_V7/so_lieu/*.csv` và `results/huim_only/uji/v7/*.json`. "Dev" = 6 fold out-of-fold theo điện thoại của
`trainingData.csv`; "Test" = `validationData.csv` (1.111 vân tay). Các hàng V4, V5 và "V6 (lưu)" lấy từ dự đoán đã lưu
của lịch sử dự án; các hàng còn lại do V7 chạy trong phiên này.

## 1. So sánh thuật toán

| Khía cạnh | V6 | V7 |
|---|---|---|
| Khai thác HUI | EFIM theo ô, 3 mô hình: rank, rank-mức-3, abs (7,33 triệu HUI) | như V6 và thêm 2 mô hình: **rel**, **abs-mức-3** (12,90 triệu HUI) |
| Điểm khớp HUI, tầng, 30 ô ứng viên | S = P·V³, làm mượt σ=3 m, tầng theo trung bình 20 ô tốt nhất | **giữ nguyên** |
| Học trên đặc trưng HUI | `HistGradientBoostingRegressor` dự đoán log(1+khoảng cách ô→vị trí thật) của từng ô | bộ chấm điểm dùng chung (MLP 5,3–7,4 nghìn tham số, nhánh gộp ứng viên) học **trực tiếp** điểm s_i |
| Cách thành tọa độ | 20 ô có khoảng cách dự đoán nhỏ nhất, w ∝ exp(−(d̂−d̂_min)/2), cố định | w = softmax(s) trên 30 ô, học cùng mất mát cuối |
| Hàm mất mát | sai số bình phương log-khoảng-cách từng ô | sai số Euclid của **tọa độ hợp nhất** (mét thực địa, hệ số 0,766126) |
| Số đặc trưng/ô | 33 (×4 phép tương đối) | 33 + 8 mỗi mô hình bổ sung = 49 (×4, log có dấu) |
| Ổn định huấn luyện | một mô hình | tập hợp chéo 5 thành viên, mỗi thành viên dừng sớm trên một fold huấn luyện khác nhau |
| Số học | trọng số float32 × tọa độ ~4,9·10⁶ (nhiễu ≈ 0,5–1 đơn vị tọa độ) | float64, tọa độ tương đối so với ô số 1 |
| Vân tay không có AP | gộp vào dev (10% tổng sai số) | báo cáo cả hai cách; chọn mô hình theo vân tay có thông tin |
| k-NN / lưu vân tay huấn luyện | không | không (kiểm tĩnh + test) |
| Nguồn gốc cache | không có siêu dữ liệu | SHA-256 dữ liệu, băm hàng fold, mã, seed, cấu hình; từ chối cache sai |

## 2. Bảng kết quả (theo mẫu của đề bài)

Sai số tính bằng mét. Độ chính xác tầng và tòa không đổi giữa các hàng vì mọi phiên bản dùng cùng quy tắc chọn tầng bằng bằng chứng HUI.

| Mô hình | Dev TB (tất cả 19.937) | Dev TB (có thông tin 19.861) | Test TB | Trung vị (test) | P75 (test) | P90 (test) | Tòa (test) | Tầng (test) | Suy luận (ms/vân tay) |
|---|---|---|---|---|---|---|---|---|---|
| V4 | 7,677 (tham chiếu lịch sử: 7,653) | 7,039 | 8,059 (lưu) | 6,151 | 10,719 | 16,946 | 99,91% | 80,38% | 136,4 (tham chiếu lịch sử) |
| V5 | 7,100 (tái tạo; tham chiếu 7,084) | 6,449 | 7,178 (lưu) | 5,392 | 9,494 | 14,309 | 99,91% | 80,38% | 171,1 (tham chiếu lịch sử) |
| V6 (lưu) | — | — | 6,866 | 5,140 | 8,943 | 14,018 | 99,91% | 80,38% | 266,3 (tham chiếu lịch sử) |
| V6 (tái tạo) | 6,879 (tham chiếu 6,827) | 6,215 | 6,861 | 5,044 | 8,876 | 14,103 | 99,91% | 80,38% | 206,2 (đo lại) |
| V7-A | 6,821 | 6,181 | 6,886 | 5,007 | 9,043 | 14,345 | 99,91% | 80,38% | 206,2 |
| V7-B | 6,536 | 5,930 | 6,430 | 4,890 | 8,539 | 13,064 | 99,91% | 80,38% | 206,7 |
| V7-C1 (+ rel) | 6,338 | 5,735 | 6,393 | 4,763 | 8,557 | 12,965 | 99,91% | 80,38% | 279,4 |
| **V7-C2 (+ rel + abs mức-3) — chọn theo dev** | **6,301** | **5,702** | **6,309** | **4,636** | **8,615** | **12,853** | 99,91% | 80,38% | 336,4 |
| V7-C (+ bù lệch thiết bị, không chọn) | 6,601 | 5,994 | không chấm test | — | — | — | — | — | — |
| V7-D (HUI cấp tầng) | chưa chạy xong | chưa chạy xong | chưa chạy xong | — | — | — | — | — | — |

Ghi chú: (1) V7-C-bù-lệch-thiết-bị chỉ chạy ở dev vì bị loại ngay ở dev. (2) Dev của V4/V5/V6 "tái tạo" có chênh nhẹ so với
số tham chiếu do 76 vân tay rỗng chọn ô theo thứ tự hòa điểm phụ thuộc phiên bản thư viện (xem `KIEM_TOAN_V6.md` §5). (3) Thời
gian của V4/V5/V6 gốc đo ở thời điểm khác; chỉ so V6 (tái đo) với V7 trong cùng một phép đo.

## 3. Mức giảm sai số

| So sánh | Dev, có thông tin | Dev, tất cả | Test |
|---|---|---|---|
| V6\* → V7-A | −0,027 m (−0,4%) | −0,052 m | **+0,020 m** (tệ hơn) |
| V6\* → V7-B | −0,279 m (−4,5%) | −0,337 m | −0,436 m (−6,3%) |
| V6\* → V7-C1 | −0,474 m (−7,6%) | −0,535 m | −0,473 m (−6,9%) |
| **V6\* → V7-C2** | **−0,507 m (−8,2%)** | **−0,573 m (−8,3%)** | **−0,557 m (−8,1%)** (so với V6 lưu) |

Khoảng tin cậy 95% (bootstrap theo cụm điện thoại, chênh lệch cặp): V7-C2 so với V6\* trên dev [−0,734; −0,261]; V7-C2 so với
V6 (lưu) trên test [−1,103; −0,149]. Trong 4.000 lần lấy mẫu lại điện thoại, V7-C2 tốt hơn V6 ở 99,98% (dev) và 99,5% (test).

## 4. Theo đúng tầng / sai tầng (test, V6 → V7-C2)

| | n | V6 | V7-C2 | Thay đổi |
|---|---|---|---|---|
| đúng tầng | 893 | 6,481 (lưu) / 6,476 (tái tạo) | 5,859 | −0,617 m (−9,5%) so với tái tạo |
| sai tầng | 218 | 8,443 (lưu) / 8,440 (tái tạo) | 8,154 | −0,286 m (−3,4%) so với tái tạo |

Dev (vân tay có thông tin): đúng tầng 5,618 → 5,079 m; sai tầng 9,345 → 9,008 m. V7 cải thiện chủ yếu khi tầng đã đúng.

## 5. Tái lập V6 (test)

| Phép đo | Kết quả |
|---|---|
| V6 lưu | TB 6,8658 m, trung vị 5,1398 m, P90 14,0185 m |
| V6 tái tạo (mô hình đào lại; GBM huấn luyện lại ở scikit-learn 1.9.1) | TB **6,8614 m** (lệch −0,0044 m, khoảng tin cậy cặp [−0,042; +0,022]) |
| Ước lượng V4 trong V6 | trùng bản lưu, lệch lớn nhất < 1 mm |
| Tầng dự đoán | trùng 100% |
| 20 ô lưu trong 30 ứng viên tính lại | 100% truy vấn |
| Danh sách 20 ô theo đúng thứ tự | trùng ở 0,6% truy vấn (GBM huấn luyện lại sắp xếp lại các ô gần hòa điểm) |

Không có hiện tượng nào làm V6 "không tái lập được"; chênh lệch còn lại do phiên bản thư viện ở bước GBM.

## 6. Mẫu cải thiện và mẫu xấu đi

Dev, ngưỡng 0,5 m: 8.324 truy vấn tốt hơn (giảm trung bình 2,89 m; ở đó V6\* sai 7,76 m), 6.248 kém hơn (tăng trung bình 2,24 m; ở
đó V6\* chỉ sai 5,45 m), 5.289 không đổi. Test: 486 / 354 / 271. Điện thoại không được cải thiện: dev 17, 19, 16, 24; test 2.
Hình: `bieu_do/F2_…`, `F8_…`, `F4_…`, `F10_…`.

## 7. Chi phí

V7-C2 dùng 12,90 triệu HUI (V6: 7,33 triệu), tệp mô hình 74,3 MB (V6: 43,0 MB), 336 ms/vân tay (V6 đo lại: 206 ms); số HUI phải nạp vào
bộ nhớ nhiều hơn 1,76 lần (chưa đo RAM riêng). V7-B (đặc trưng V6, không thêm mô hình HUI) rẻ gần bằng V6 (206,7 ms) và đã giảm 0,44 m trên test.
