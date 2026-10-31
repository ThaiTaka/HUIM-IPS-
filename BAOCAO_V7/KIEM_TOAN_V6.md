# Kiểm toán HUIM-IPS V6 (trước khi xây V7)

Mọi con số dưới đây đo trực tiếp trên máy này (Python 3.13.14, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1; 12 luồng
CPU, 15,7 GB RAM với khoảng 4 GB trống khi chạy, không GPU, ổ D: còn ~80 GB). Chỗ nào là số lấy từ báo cáo V6 thì ghi
"tham chiếu".

## 1. Pipeline V6 thực tế (đọc từ mã)

| Bước | Thực tế trong mã | Tệp |
|---|---|---|
| Dữ liệu | `trainingData.csv` 19.937 vân tay, 520 AP, 16 điện thoại; `validationData.csv` 1.111 vân tay, 11 điện thoại; 933 ô tham chiếu (mỗi vị trí huấn luyện khác nhau = một ô, `results/huim_only/uji/model/cells.csv`) | `multi_datasets.py` |
| Đơn vị | tọa độ Web-Mercator; mét ngoài thực địa = khoảng cách tọa độ × `g` = 0,766126 | `verify_coordinates.py` |
| Lợi ích nội q(i,T) ∈ [1,100] | `rank` (hạng của AP trong vân tay, bất biến với méo đơn điệu), `abs` (cường độ tuyệt đối), `rel` (so với AP mạnh nhất, cửa sổ 40 dB); lợi ích ngoài p(i)=1 | `huim_positioning.internal_utility` |
| EFIM | một lần chạy cho mỗi ô: giao dịch = vân tay huấn luyện của ô (trung bình 21,3), `minUtil` = θ% × tổng lợi ích của ô, θ=20%; nếu vượt 10 s hoặc 10.000 HUI thì nâng θ ×1,25 và chạy lại (θ trung bình thực dùng 34,5%) | `HUIPositioner.fit` |
| Mô hình | chỉ giữ HUI (tập mục, u, support) + tọa độ/tầng của ô: mô hình rank 3.238.416 HUI, rank-mức-3 1.031.786, abs 3.062.754 — **tổng 7.332.956 ≈ 7,33 triệu** (đúng số trong báo cáo V6) | `huim_rerank_final.py` |
| Điểm HUI | P_c = Σ_X w(X)·frac(X,T)^γ·exp(−\|q_T(X)−q̄_c(X)\|/τ), V_c = độ phủ, S = P·V³, rồi làm mượt Gaussian σ=3 m trong cùng tầng | `components`, `cell_scores` |
| Chọn tầng | tầng có trung bình điểm S của 20 ô tốt nhất cao nhất (kf=20) | `floor_of` |
| Chọn ứng viên | 30 ô điểm cao nhất của tầng đã chọn | `compute` |
| Tọa độ ban đầu (V4) | tâm có trọng số S⁸ của 12 ô tốt nhất | `locate` |
| Bước 8 (V5/V6) | `HistGradientBoostingRegressor` (300 vòng, lr 0,06, 31 lá, min_leaf 40, l2=1) dự đoán log1p(khoảng cách ô→vị trí thật) từ 33 đặc trưng HUI × 4 phép tương đối = 132 cột; huấn luyện trên 6 fold dev | `regressor`, `relative` |
| Trọng số 20 ô cuối | 20 ô có khoảng cách dự đoán nhỏ nhất, w ∝ exp(−(d̂−d̂_min)/2) | `place` |
| Fold | `GroupKFold(6)` theo `PHONEID` (16 điện thoại); validation là 9 điện thoại lạ + 2 điện thoại (13, 14) có trong huấn luyện | `folds_for` |

## 2. Thành phần tái sử dụng

Toàn bộ EFIM và `HUIPositioner`; hàm `compute` (30 ứng viên + 33 đặc trưng HUI); `relative`; 18 mô hình fold
(6 × rank/L3/abs) và 3 mô hình cuối của V6 đào lại được **y hệt** (xem §5); `place` làm đường cơ sở.

## 3. Hạn chế đo được (đây là cơ sở của thiết kế V7)

1. **Cách kết hợp ô chưa tối ưu cho tọa độ.** Với 19.861 vân tay có thông tin, 30 ứng viên chứa một ô cách vị trí thật
   dưới 3 m ở 92,4% truy vấn (dưới 5 m: 95,9%; dưới 10 m: 99,0%), sai số trung bình của ô gần nhất chỉ 0,59 m — nhưng
   tọa độ cuối của V6 sai 6,21 m (chỉ 37,1% dưới 3 m). Ô điểm HUI cao nhất cách vị trí thật 7,52 m (32,7% dưới 3 m). Vậy
   HUI hầu như không chọn sai vùng; sai số sinh ra ở bước **xếp hạng và kết hợp** các ứng viên.
2. **Tầng.** Đúng tầng 84,2% (dev); sai tầng sai số 9,35 m so với 5,62 m khi đúng tầng; nhóm sai tầng chiếm 23,8% tổng sai số.
3. **Đuôi sai số.** 10% truy vấn tệ nhất (≥ 13,3 m) chiếm 35,2% tổng sai số, trong đó 32,1% sai tầng; ô gần nhất trong 30
   ứng viên của chúng vẫn chỉ cách 2,27 m trung bình.
4. **76 vân tay huấn luyện không phát hiện AP nào** (59 của điện thoại 1, 14 của 22, 2 của 13, 1 của 6; toàn bộ nằm
   trong dev, `validationData.csv` có 0). Mọi ô điểm 0 nên 12/20 ô "tốt nhất" là kết quả hòa điểm tùy ý; sai số trung
   bình 180,5 m, chiếm **10,0% tổng sai số dev**. Gộp chúng vào, dev của V6 là 6,879 m; bỏ ra, 6,215 m. Số tham chiếu
   6,8274 m của V6 vì vậy chứa ~0,66 m không liên quan đến chất lượng định vị.
5. **Nhiễu số học.** Trọng số float32 có tổng lệch ~1e-7, nhân với tọa độ Web-Mercator ~4,9·10⁶ cho tâm lệch 0,5–1 đơn vị
   tọa độ (≈ 0,4–0,8 m) ở hầu hết truy vấn. Ảnh hưởng lên sai số trung bình nhỏ (6,2148 → 6,2087 m khi tính float64) nhưng
   là sai sót thật; V7 tính tâm bằng float64 và tọa độ tương đối.
6. **Chính sách tự nâng θ phụ thuộc đồng hồ thật** (giới hạn 10 s/ô): mô hình HUI có thể khác nhau giữa các máy/tải.
   Với cấp ô, thời gian tối đa 4,7 s nên chưa từng kích hoạt khi kiểm (xem §5). V7 tránh giới hạn đồng hồ ở mô hình mới
   (cấp tầng).
7. **Tập validation đã được dùng nhiều lần** (lịch sử V1–V6), nên số trên đó là chỉ báo, không phải ước lượng độc lập.

## 4. Nguy cơ rò rỉ dữ liệu

* Nhãn/vị trí của fold đánh giá không bao giờ vào mô hình HUI của fold đó (đã kiểm: tập điện thoại của hàng huấn luyện và
  hàng đánh giá rời nhau trong cả 6 fold, `dev_features.py` có assert; kiểm lại ở T10 của `verify_v7.py`).
* **Rò rỉ gián tiếp bậc hai:** bộ xếp hạng đánh giá trên fold k được huấn luyện bằng đặc trưng của các fold j≠k, mà mô
  hình HUI M_j của fold j đã đọc vân tay của fold k. Bộ xếp hạng không thấy cặp (đặc trưng, nhãn) nào của fold k, nên đây
  chỉ là rò rỉ gián tiếp; V7 định lượng nó bằng `nested_check.py` (xem báo cáo).
* Chọn tham số (m, λ ở V6; T₀, c ở V7-A; số epoch dừng sớm ở V7-B) chỉ dùng dev; V7-A và số epoch được chọn lồng nhau.
* Chưa có tập kiểm tra độc lập mới; `validationData.csv` chỉ dùng để chấm cuối từng biến thể đã khai báo.

## 5. Tái lập V6 trên máy này

| Phép đo | Kết quả |
|---|---|
| Số HUI 12 mô hình fold (rank, abs) so với `dev_parts/*.npz` gốc | **bằng nhau tuyệt đối** (ví dụ fold 0 rank 3.225.283; fold 5 abs 3.041.539) |
| Mô hình rank cuối / L3 cuối | 3.238.416 (bằng `cell_runs.csv`) / 1.031.786 (bằng `l3_model_huis` trong `summary.json`) |
| Độ chính xác tầng dev | 0,8384 — bằng số tham chiếu |
| Sai số dev V4 | 7,6767 m (tham chiếu 7,6532 m) |
| Sai số dev V6 | 6,8790 m (tham chiếu 6,8274 m) |
| Nguồn lệch | so từng truy vấn với `dev_parts` gốc: fold 0, 2, 4 trùng đến 1e-3; fold 1 khác 2 truy vấn, fold 3 khác 15, fold 5 khác 59 — **đúng 76 truy vấn rỗng** (mọi ô điểm 0, chọn 12 ô theo thứ tự hòa điểm của `argpartition`, phụ thuộc phiên bản numpy). Loại chúng ra, dev khớp |
| Test V6 | xem `V6_V7_COMPARISON.md` §Tái lập V6 |

## 6. Thiết kế V7 đã triển khai

* **V7-A** — hợp nhất thích ứng trên chính dự đoán của bộ xếp hạng V6 (số ô linh hoạt, nhiệt độ softmax thích ứng, cắt
  theo chênh lệch, loại ô điểm HUI thấp, chọn cụm): `fusion.py`, tham số chọn lồng nhau theo fold.
* **V7-B** — bộ chấm điểm dùng chung học trực tiếp trọng số w = softmax(s) bằng hàm mất mát là sai số tọa độ (mét): `direct.py`.
* **V7-C** — thêm bằng chứng HUI mới: mô hình HUI trên lợi ích `rel` (bất biến với độ lệch thu của điện thoại) và trên
  (AP, mức cường độ tuyệt đối); thử thêm đặc trưng bù lệch thiết bị và đồng thuận không gian.
* **V7-D** — HUI cấp tầng làm ngữ cảnh cho quyết định theo ô: `hier.py`.
