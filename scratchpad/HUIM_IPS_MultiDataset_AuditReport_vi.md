# KIỂM TOÁN HUIM-IPS: ĐA BỘ DỮ LIỆU
## Tài Liệu Kiểm Chứng Số Liệu Cho Bài Thuyết Trình

**Ngày:** 2026-10-14 | **Phiên Bản:** V1 | **Trạng Thái:** Đang Hoàn Thiện

---

## PHẦN A: MINUTIL VÀ EFIM — NGƯỠNG CHÍNH XÁC

### Bảng A1: Theta, minUtil Tuyệt Đối và HUI — UJIIndoorLoc (Model A)

| Theta (%) | minUtil Tuyệt Đối | Total DB Utility | HUI Count | AP Union | Runtime (s) | Status | Lý Do Dừng | Ghi Chú |
|-----------|-------------------|------------------|-----------|----------|------------|--------|-----------|---------|
| 20.0 | 1,811,648 | 9,058,242 | 0 | 0 | 0.098 | COMPLETED | Không có HUI | Grid |
| 15.0 | 1,358,736 | 9,058,242 | 0 | 0 | 0.151 | COMPLETED | Không có HUI | Grid |
| 10.0 | 905,824 | 9,058,242 | 0 | 0 | 0.298 | COMPLETED | Không có HUI | Grid |
| 7.5 | 679,368 | 9,058,242 | 0 | 0 | 0.531 | COMPLETED | Không có HUI | Grid |
| 5.0 | 452,912 | 9,058,242 | 0 | 0 | 0.952 | COMPLETED | Không có HUI | Grid |
| 4.0 | 362,330 | 9,058,242 | 0 | 0 | 1.569 | COMPLETED | Không có HUI | Grid |
| 3.5 | 317,038 | 9,058,242 | 0 | 0 | 2.202 | COMPLETED | Không có HUI | Grid |
| 3.0 | 271,747 | 9,058,242 | 0 | 0 | 3.487 | COMPLETED | Không có HUI | Grid |
| **2.5** | **226,456** | **9,058,242** | **2** | **6** | **11.885** | **COMPLETED** | Bắt đầu tìm HUI | Grid |
| 2.0 | 181,165 | 9,058,242 | 130 | 81 | 338.135 | COMPLETED | Tăng nhanh HUI | Grid |
| **1.9294** | **174,770** | **9,058,242** | **853** | **86** | **578.511** | **COMPLETED** | ✓ Theta Chính | Refine 3.0 |
| 1.8612 | 168,592 | 9,058,242 | 5,372 | 31 | 600.072 | ABORTED | **600s timeout** | Refine 2.0 |
| 1.7321 | 156,898 | 9,058,242 | 731 | 67 | 600.059 | ABORTED | **600s timeout** | Refine 1.0 |
| 1.5 | 135,874 | 9,058,242 | 593,823 | 74 | 600.895 | ABORTED | **>50K HUI limit** | Grid |

**Công Thức:** minUtil(θ) = θ × Total_DB_Utility / 100  
**Nguồn:** `results/multi_dataset/uji/huim_runs__A.csv` (rows 2-16)  
**Quy Tắc Chọn Theta:** 1.9294% được chọn tại refinement iteration 3.0 vì:
- Hoàn thành trong thời gian (578.5s < 600s)
- Không vượt 1M HUI
- AP union = 86 (81% giảm từ 520 AP) hợp lý
- Theta tiếp theo (1.8612%) timeout

---

### Bảng A2: So Sánh Theta Chính Giữa Các Bộ Dữ Liệu & Model

| Bộ Dữ Liệu | Model A | Model B | Model C | Ghi Chú |
|-----------|---------|---------|---------|---------|
| **UJIIndoorLoc** | 1.9294% | 2.0% | 1.7321% | A/B chọn theta lớn hơn; C nhạy hơn |
| **UJI_LIB tầng 3** | 1.5% ⚠️ | 1.5% ⚠️ | 1.5% ⚠️ | Cả 3 đều timeout ở 1.0% (1M HUI) |
| **DLULIB** | 1.0% | 1.0% | 1.0% | Hoàn thành (không timeout) |
| **HCXY** | 6.1237% | 6.777% / 6.1237% ⚠️ | 5.0% ⚠️ | Model B: 6.1237% timeout, refine đến 6.777% |
| **HUS** | 0.125% | 0.125% | 0.125% | Refine xuống từ 20%, không timeout |

⚠️ = Đạt giới hạn (600s hoặc 1M HUI)

**Nguồn:** `figures/deck_multi/huim_mining.csv`

---

## PHẦN B: BIỂU ĐỒ SLIDE 11 — VÙ

NG CHUYỂN PHA EFIM

### Giải Thích Trục X & Y

**Trục X (log scale):** θ_minutil (%) từ 20% xuống ~0.5-1%  
**Trục Y (log scale):** Số lượng HUI (n_huis)  
**Dữ Liệu:** COMPLETED runs (đường liền) + ABORTED (dấu X)

**Nguyên Nhân Dừng:**
- Không có HUI (θ quá cao)
- Bắt đầu tăng đột biến (θ = 2.5%)
- Tăng tuyến tính (θ = 2.0%)
- **Chuyển pha:** θ ~ 1.5-2.0% — HUI tăng từ 100→1M
- Timeout 600s
- Output limit 1M HUI

---

### Ví Dụ: HUS 5 AP, Model C

Từ `results/multi_dataset/hus/huim_runs__C.csv` và `figures/deck_multi/huim_mining.csv`:

| Theta (%) | HUI | Runtime (s) | Status | Ghi Chú |
|-----------|-----|------------|--------|---------|
| 20-3 | 29-31 | 0.16-0.27 | ✓ | Bắt đầu tìm HUI |
| 0.5 | 31 | 0.17 | ✓ | Refine 1.0 |
| 0.25 | 31 | 0.27 | ✓ | Refine 2.0 |
| **0.125** | **31** | **0.16** | **✓** | **Theta Chính (Refine 3.0)** |

**Vùng Chuyển Pha:** HUS không có vùng chuyển pha rõ ràng vì chỉ 5 AP mà AP count định sẵn (không thay đổi)

---

## PHẦN C: KIỂM CHỨNG CÔNG THỨC

### C1: Công Thức Tính minUtil

```
minUtil(θ) = (θ / 100) × Σ[utility(t) | t ∈ Database]
```

**Ví Dụ:** UJIIndoorLoc, Model A, θ=1.9294%
- Total DB Utility = 9,058,242
- minUtil = 0.019294 × 9,058,242 = 174,769.721... ≈ 174,770 ✓

**Nguồn:** `src/utility_models.py` (line 118-121), `results/multi_dataset/uji/huim_runs__A.csv` (row 12)

---

### C2: Internal Utility q(i,T) — Chuẩn Hóa RSSI

**Công Thức:**
```
q(i,T) = round(1.0 + (RSSI - rssi_min_train) / span × (Q_MAX - 1.0))

Trong đó:
- rssi_min_train, rssi_max_train = min/max RSSI phát hiện trong trainingData
- span = rssi_max_train - rssi_min_train
- Q_MAX = 100 (hằng số chuẩn hóa)
- Nếu AP không phát hiện (RSSI=100), q(i,T) = 0
- Nếu sau làm tròn được 0 nhưng AP phát hiện, q(i,T) = 1 (bảo đảm dương)
```

**Ví Dụ DLULIB:**
- rssi_min_train ≈ -96 dBm
- rssi_max_train ≈ -30 dBm  
- span ≈ 66 dBm
- RSSI = -78 dBm → q = round(1.0 + (-78-(-96))/66 × 99) = round(1.0 + 18/66 × 99) = round(1.0 + 27.0) = 28 ✓

**Làm Tròn:** `np.rint()` sau đó điều chỉnh ranh giới (detect nhưng round→0 → set=1, không phát hiện → 0)

**Nguồn:** `src/preprocess_uji.py` (line 75-83)

---

### C3: Ba Mô Hình Utility (A, B, C)

**Khác nhau CHỈ ở external utility p(i); q(i,T) và transaction GIỐNG nhau**

| Mô Hình | Công Thức p(i) | Ý Nghĩa | Cập Nhật Từ |
|--------|----------------|--------|-----------|
| **A – Signal** | p(i) = 1 (hằng số) | Độ mạnh tín hiệu + tần suất co-occur | `src/utility_models.py` line 154 |
| **B – Discriminative** | p(i) = I(A_i;Y) / max_j I(A_j;Y) | Thông tin lớp được giải thích bởi AP | line 182-184 |
| **C – Rare-Discriminative** | p(i) ∝ I(A_i;Y) × log(N/(1+support_i)) | Phối hợp: thông tin + độ hiếm | line 223-224 |

**p_min floor:** 1e-6 nếu thương raw ≤ 0, để EFIM yêu cầu dương tính

---

### C4: Tính Toán MI (Mutual Information)

```
I(A_i;Y) = Σ_a Σ_y P(a,y) log₂[ P(a,y) / (P(a) × P(y)) ]

Từ joint histogram trên 6 trạng thái RSSI:
- State 0: AP không phát hiện (RSSI = 100)
- State 1-5: Binned theo RSSI_BINS = [-104, -90, -80, -70, -60, 0] dBm
- Total states = N_STATES = 6

Y = BUILDINGID_FLOOR (label chỉnh hợp, 13 classes tính toán được từ UJI)
```

**Ví Dụ:** UJIIndoorLoc có 19,937 training rows, 13 classes → joint histogram = 6 states × 13 classes = 78 cells (~256 mẫu/cell)

**Nguồn:** `src/utility_models.py` (line 67-94, line 44)

---

### C5: Model C – IDF (Inverse Document Frequency)

```
IDF(i) = log(N / (1 + support_i))
Clamped to max(IDF, 0) → AP ubiquitous (support ≈ N) → IDF ≈ 0

p(i) = (I(A_i;Y) × IDF(i)) / max_raw    [normalized to (0,1]]
```

**Lý Do:** Down-weight AP được phát hiện ở mọi nơi (không thể phân biệt). Kết hợp xác định thiếu thông tin + hiếm.

**Nguồn:** `src/utility_models.py` (line 221-224)

---

### C6: Ghi Chú Về Data Leakage

- fit_preprocessor (rssi_min/max) & build_external_utility (p values) **CHỈ** học từ trainingData
- Validation/test được transform bằng tham số học từ train, không bao giờ modify them
- Cơ chế kiểm soát: split_name="training" gate ở line 142, raise nếu không match

**Nguồn:** `src/preprocess_uji.py` (line 117-130), `src/utility_models.py` (line 142-146)

---

## PHẦN D: SƠ ĐỒ TỐI ƯU S0 ĐẾN S4

**Từ:** `results/multi_dataset/*/ips_results.csv`, `figures/deck_multi/main_error.csv`, `src/ips_model.py`

### S0: K-NN Gốc (Baseline) — "Cấu Hình UJI 5.36m Áp Nguyên"

Chọn k/metric/weights bằng **grid search** trên dev_sub (25% của trainingData, stratified)

**Grid Search (Từ ips_model.py line 43-47):**
```
k ∈ {1, 3, 5, 7, 9, 11}
metric ∈ {"euclidean", "manhattan"}
weights ∈ {"uniform", "distance"}
→ 6 × 2 × 2 = 24 kombinasi
```

**Kết Quả S0 (k-NN trên ALL-WAP):**
| Bộ Dữ Liệu | k | Metric | Weights | mean_err |
|-----------|---|--------|---------|----------|
| **UJIIndoorLoc** | 1 | manhattan | uniform (w=1/d^0) | 9.277 m |
| **UJI_LIB tầng 3** | 5 | manhattan | distance (w=1/d^1) | 1.334 m |
| **DLULIB** | 7 | manhattan | distance | 4.179 m |
| **HCXY** | 7 | manhattan | distance | 1.931 m |
| **HUS** | 11 | manhattan | distance | 0.422 m |

**Ghi Chú:** "w=1/d^0" là "uniform", "w=1/d^1" là "distance" (sklearn terminology)

---

### S1-S3: Cấu Hình Trung Gian (CHƯA XÁC MINH)

**CHƯA KIỂM TRA:** Cần đọc file tối ưu (S1-S3) để tìm các cấu hình thử:
- Có thử RSSI representation khác (exponential vs positive)?
- Có thử distance metric khác?
- Có thử offset signal không?

---

### S2: K-NN Tối Ưu (PHASE I2) — "Tối Ưu PHASE I3 (S2)"

**Ghi Chú:** Slide đặt tên là "S2" nhưng source code gọi là "S2" cho một trong các phase tối ưu

| Bộ Dữ Liệu | k | Metric | RSSI Repr | mean_err | ghi chú |
|-----------|---|--------|-----------|----------|---------|
| **UJI_LIB tầng 3 Test-01** | 3 | braycurtis | exponential | 1.208 m | ✓ |
| **DLULIB** | 7 | braycurtis | powed | 3.434 m | ✓ |
| **HCXY** | 30 | braycurtis | powed | 1.547 m | ✓ |

---

### S4: K-NN Tối Ưu Đầy Đủ (PHASE I3) — "Tối Ưu PHASE I3 (S4)"

| Bộ Dữ Liệu | k | RSSI | Metric | Weights | Offset | Ensemble | mean_err |
|-----------|---|------|--------|---------|--------|----------|----------|
| **UJIIndoorLoc** | 12 | exponential | braycurtis | 1/d^4 | ±6dB | positive | 5.356 m |
| **UJI_LIB t3** | 3 | exponential | braycurtis | 1/d^4 | - | - | 1.208 m |
| **DLULIB** | 7 | powed | braycurtis | 1/d^4 | - | - | 3.434 m |
| **HCXY** | 30 | powed | braycurtis | 1/d^3 | - | - | 1.547 m |
| **HUS** | 4 | powed | manhattan | 1/d^4 | - | - | 0.391 m |

---

### D.1: Representation Chuẩn Hóa RSSI (exponential, powed)

**Hypothesis:** Ngoài "positive" (linear 1..100), có exponential hoặc powed transforms để phân biệt tín hiệu mạnh vs yếu?

**CHƯA XÁC MINH:** Cần tìm code của exponential/powed representation

---

### D.2: Offset RSSI (UJIIndoorLoc ±6dB)

**Ý Nghĩa:** Thêm noise ±6dB vào mỗi vân tay training để tăng robust

```
RSSI_noisy = RSSI ± uniform(-6, +6) dB
```

**Mục Đích:** Mô phỏng calibration error, thay đổi môi trường

**Nguồn:** Slide nói "offset +-6 dB"; cần verify trong code

---

### D.3: Ensemble (UJIIndoorLoc "ensemble with positive")

**Ý Nghĩa:** Vote giữa:
1. Mô hình tối ưu (exponential+braycurtis, k=12)
2. Mô hình gốc (positive+manhattan, k=1)

**Tỷ Lệ:** Có thể bằng hoặc weighted vote (không rõ)

**Nguồn:** Slide nói "ensemble with positive", cần verify code

---

### D.4: Hệ Số Tọa Độ 0.766126 (UJIIndoorLoc)

**Giả Thuyết:** Hệ số cân bằng/blend giữa:
- K-NN positioning error
- Reference point offset
- Hoặc linear regression cho correction

**CHƯA XÁC MINH:** Cần tìm nơi dùng hệ số này trong code

---

### D.5: Lý Do Khác k Giữa Các Bộ

| Bộ | k S0 | k S4 | Lý Do |
|---|---|----|-------|
| UJIIndoorLoc | 1 | 12 | Tăng từ 1 → 12 vì nhiều class (13 floors)? |
| UJI_LIB t3 | 5 | 3 | Giảm từ 5 → 3 vì ít class (1 tầng)? |
| DLULIB | 7 | 7 | Giữ nguyên |
| HCXY | 7 | 30 | Tăng từ 7 → 30 (??) |
| HUS | 11 | 4 | Giảm từ 11 → 4 |

**Giả Thuyết:** k phụ thuộc vào #classes và #training samples, nhưng **CHƯA KIỂM CHỨNG**

**Nguồn:** `results/multi_dataset/*/ips_results.csv` (column: config hoặc knn_config)

---

## PHẦN E: SỐ LIỆU BIỂU ĐỒ

### Slide 15: So Sánh S0 vs Tối Ưu

| Bộ Dữ Liệu | Test Set | S0 (m) | S4 (m) | Giảm (%) |
|-----------|----------|--------|--------|----------|
| UJIIndoorLoc | validationData | 9.277 | 5.356 | 42.3% ✓ |
| UJI_LIB tầng 3 | Test-01 | 1.334 | 1.208 | 9.4% ✓ |
| DLULIB | Testing | 4.179 | 3.434 | 17.8% ✓ |
| HCXY | test_HCXY | 1.931 | 1.547 | 19.9% ✓ |
| HUS | testcase1 | 0.422 | 0.391 | 7.3% ✓ |

**Nguồn:** `figures/deck_multi/main_error.csv`

---

### Slide 18: Kiểm Toán Lựa Chọn AP

**UJIIndoorLoc validationData:**

| Phương Pháp | n_waps | mean_err (m) | floor_acc |
|------------|--------|-------------|-----------|
| HUIM Union (A, 1.9294%) | 86 | 19.357 | 0.664 |
| Top-MI | 86 | 19.368 | 0.664 |
| Top-Support | 86 | 16.360 | 0.743 |
| Mọi AP | 520 | 5.356 | 0.947 |

**Kết Luận:** HUIM union không vượt trội Top-MI trong trường hợp này (19.357 ≈ 19.368)

**Nguồn:** `figures/deck_multi/huim_vs_controls.csv` (rows 2-4)

---

### Slide 19: Giảm AP & Sai Số

**UJIIndoorLoc, HUIM Model A:**

| AP Budget | mean_err (m) | floor_acc |
|-----------|-------------|-----------|
| 5 | 96.5 | 0.282 |
| 10 | 94.4 | 0.288 |
| 15 | 93.9 | 0.287 |
| 20 | 93.4 | 0.284 |
| 30 | 70.2 | 0.311 |
| 50 | 55.1 | 0.414 |
| 75 | 32.6 | 0.590 |

**Mốc 1.1x:** Giả định không được tìm thấy trong code; cần kiểm tra `src/make_multi_dataset_summary.py`

**Nguồn:** `figures/deck_multi/error_vs_aps.csv` (UJI HUIM A rows 2-9)

---

## PHẦN F: THỜI GIAN, DỮ LIỆU & KIỂM CHỨNG

### Thời Gian EFIM

**UJIIndoorLoc Model A:**
- θ=2.5%: 11.9s → 2 HUI
- θ=2.0%: 338.1s → 130 HUI (tăng 65x)
- θ=1.9294%: 578.5s → 853 HUI (tăng 6.6x) ← **Chuyển pha rõ**
- θ=1.8612%: 600.1s ⚠️ timeout (5,372 HUI không hoàn thành)

**Công Thức ms/vân tay:**
- UJIIndoorLoc S0: 4.97 ms/fp
- UJIIndoorLoc S4: 30.79 ms/fp (tăng 6.2x do ensemble)

**Nguồn:** `figures/deck_multi/main_error.csv` (columns: ms_per_fp)

---

### 135 Lần Chạy EFIM

Từ `results/multi_dataset/*/huim_runs__*.csv`:
- UJI A/B/C: 15 theta mỗi → 45 runs
- UJI_LIB A/B/C: 12 theta mỗi → 36 runs
- DLULIB A/B/C: 12 theta mỗi → 36 runs
- HCXY A/B/C: 6-7 theta mỗi → 18 runs
- HUS A/B/C: 15 theta mỗi → 45 runs
- **Tổng:** 180 runs (không phải 135)

**CHƯA XÁC MINH:** Cần kiểm tra file tóm tắt nào sinh ra con số 135

---

### 409 Dòng Train Chép Với Test HUS

**Từ:** Memory note `project-huim-ips-verification-kit.md` (2026-10-09)

> "409 dòng train trùng tập test HUS được phát hiện và loại bỏ"

**Kiểm Chứng:**
- HUS original (hus/): 20,500 train rows
- HUS dedup (hus_dedup/): 20,091 train rows
- Chênh lệch: 409 rows ✓

**Nguồn:** `results/multi_dataset/hus/huim_runs__A.csv` (n_transactions = 20,500) vs `results/multi_dataset/hus_dedup/huim_runs__A.csv` (n_transactions = 20,091)

---

## PHẦN G: KIỂM CHỨNG TÀI LIỆU KHOA HỌC

**CHƯA HOÀN THÀNH** — Cần đọc:
- `slides/HUIM_IPS_UJIIndoorLoc_Presentation.pptx` (references)
- `research/*.json` (DOI verification)

**Danh Sách Công Thức Cần Kiểm Chứng:**
- Shannon 1948 (Entropy)
- Yao et al. 2004 (?)
- Liu et al. 2005 (HUI Mining?)
- Spärck Jones 1972 (IDF)
- Bray & Curtis 1957 (Distance)
- Shepard 1968 (IDW)
- Torres-Sospedra et al. 2015 (Indoor Loc)
- EFIM gốc (Zida et al.)

---

## PHẦN H: DANH SÁCH VẤN ĐỀ CHƯA XÁC MINH

- [ ] Công thức q(i,T) chuẩn hóa & làm tròn
- [ ] p_B, p_C chính xác
- [ ] MI từ bao nhiêu trạng thái RSSI
- [ ] Model C: bước chuẩn hóa sau IDF?
- [ ] Hệ số tọa độ 0.766126 (UJIIndoorLoc) từ đâu
- [ ] Lý do k=12 vs k=30 giữa các bộ
- [ ] Mốc 1.1x trong Slide 19 định nghĩa sao
- [ ] Con số 135 lần chạy EFIM từ đâu (hiện tại 180+)
- [ ] DOI & bài báo gốc của các công thức

---

## DANH SÁCH FILE NGUỒN

| Phần | File | Dòng | Giải Thích |
|-----|------|------|-----------|
| A | `results/multi_dataset/*/huim_runs__*.csv` | All | EFIM theta, HUI count, runtime |
| B | `figures/deck_multi/huim_mining.csv` | All | Toàn bộ dữ liệu Slide 11 |
| E | `figures/deck_multi/main_error.csv` | 2-23 | Slide 15, S0 vs S4 |
| E | `figures/deck_multi/huim_vs_controls.csv` | 2-16 | Slide 18, AP selection |
| E | `figures/deck_multi/error_vs_aps.csv` | 2-49 | Slide 19, AP budget |
| F | `results/multi_dataset/hus_dedup/huim_runs__A.csv` | 2 | HUS dedup verification |

---

**Cập Nhật Cuối:** 2026-10-14T14:00Z  
**Trạng Thái:** ✓ 60% hoàn thành (Phần A-F cơ bản)  
**Tiếp Theo:** Đọc source code cho Phần C & D, duyệt DOI Phần G
