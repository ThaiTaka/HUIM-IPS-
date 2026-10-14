# So sánh HUIM-IPS trên nhiều bộ dữ liệu

Chỉ thay bộ dữ liệu; tiền xử lý, 3 mô hình utility, EFIM, lưới minUtil, k-NN của nghiên cứu và quy trình tối ưu PHASE I3 (quy trình đã cho 5,36 m trên UJIIndoorLoc) giữ nguyên. Mọi số dưới đây được `src/make_multi_dataset_summary.py` đọc từ `results/multi_dataset/`.

Thư mục rỗng (cả trong file zip), không chạy được: `UJI_LIB_DB_Floor_5`, `syl`, `tuji`.

## 1. Dữ liệu

| Bộ dữ liệu | Train | Test | Số AP (phát hiện ở train) | Vị trí train | Tòa / lớp tòa-tầng | Nhãn vị trí | Nhóm CV (PHASE I3) |
|---|---|---|---|---|---|---|---|
| UJIIndoorLoc | 19937 | validationData: 1111 dòng, 1053 vị trí (18 có trong train) | 520 (465) | 933 | 3 / 13 | BUILDINGID_FLOOR | USERID |
| UJI_LIB tầng 3 | 11520 | Test-01: 7200 dòng, 24 vị trí (24 có trong train); Test-02: 7200 dòng, 24 vị trí (0 có trong train) | 620 (306) | 24 | 1 / 1 | RP (reference point) | Month |
| DLULIB | 13000 | Testing: 6500 dòng, 650 vị trí (650 có trong train) | 17 (17) | 650 | 1 / 3 | BUILDINGID_FLOOR | SampleTimes |
| HCXY | 11370 | test_HCXY: 860 dòng, 86 vị trí (0 có trong train) | 347 (345) | 379 | 1 / 1 | RP (reference point) | RP |
| HUS (bỏ dòng chép) | 20091 | testcase1: 205 dòng, 205 vị trí (205 có trong train); testcase2: 205 dòng, 205 vị trí (205 có trong train) | 5 (5) | 205 | 1 / 1 | RP (reference point) | none |
| HUS nguyên bản | 20500 | testcase1: 205 dòng, 205 vị trí (205 có trong train); testcase2: 205 dòng, 205 vị trí (205 có trong train) | 5 (5) | 205 | 1 / 1 | RP (reference point) | none |

Nguồn dữ liệu:

- **UJIIndoorLoc**: Torres-Sospedra et al., IPIN 2014, DOI 10.1109/IPIN.2014.7275492.
- **UJI_LIB tầng 3**: Mendoza-Silva, Richter, Torres-Sospedra, Lohan, Huerta, "Long-Term WiFi Fingerprinting Dataset for Research on Robust Indoor Positioning", Data 3(1):3, 2018, DOI 10.3390/data3010003 (Crossref).
- **DLULIB**: không có tài liệu mô tả đi kèm trong thư mục.
- **HCXY**: không có tài liệu mô tả đi kèm; đơn vị toạ độ không được ghi.
- **HUS (bỏ dòng chép)**: không có tài liệu mô tả đi kèm trong thư mục.
- **HUS nguyên bản**: không có tài liệu mô tả đi kèm trong thư mục.

Làm sạch / ghi chú dữ liệu:

- **UJIIndoorLoc**: trainingData.csv: SHA-256 identical to the copy the study used (ujiindoorloc\UJIndoorLoc\trainingData.csv)
- **UJIIndoorLoc**: validationData.csv: SHA-256 identical to the copy the study used (ujiindoorloc\UJIndoorLoc\validationData.csv)
- **UJI_LIB tầng 3**: Data-Training.xlsx: dropped 2 rows without x/y/Floor/Month (Excel rows [11522, 11523]); they are summary rows below the data, not fingerprints
- **UJI_LIB tầng 3**: Test-01.xlsx: dropped 5 rows without x/y/Floor/Month (Excel rows [7202, 7203, 7204, 7205, 7206]); they are summary rows below the data, not fingerprints
- **DLULIB**: Training_DLULIB_Floor1_All_20.xlsx: 6280 rows; 40869 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Testing_DLULIB_Floor1.xlsx: 3140 rows; 22819 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Training_DLULIB_Floor2_All_20.xlsx: 3720 rows; 23219 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Testing_DLULIB_Floor2.xlsx: 1860 rows; 11477 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Training_DLULIB_Floor3_All_20.xlsx: 3000 rows; 26690 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Testing_DLULIB_Floor3.xlsx: 1500 rows; 10393 cells at -100 mapped to 'not detected' (100)
- **DLULIB**: Training_DLULIB_Floor*_Mean.xlsx not used: one averaged fingerprint per RP; the study trains on raw samples (the *_All_20 files)
- **HUS (bỏ dòng chép)**: testcase1.txt: 204 of 205 rows are exact copies of a hus_trainall row (same RP, same 5 RSSIs)
- **HUS (bỏ dòng chép)**: testcase2.txt: 205 of 205 rows are exact copies of a hus_trainall row (same RP, same 5 RSSIs)
- **HUS (bỏ dòng chép)**: dedup: removed 409 training rows that the test cases copy; training keeps 20091 rows
- **HUS nguyên bản**: testcase1.txt: 204 of 205 rows are exact copies of a hus_trainall row (same RP, same 5 RSSIs)
- **HUS nguyên bản**: testcase2.txt: 205 of 205 rows are exact copies of a hus_trainall row (same RP, same 5 RSSIs)

## 2. Độ chính xác tòa, tầng, khoảng cách và thời gian (mọi WAP)

| Bộ dữ liệu · tập test | Phương pháp | Tòa | Tầng | Sai số TB (m) | Trung vị (m) | P90 (m) | ms / fingerprint |
|---|---|---|---|---|---|---|---|
| UJIIndoorLoc · validationData | k-NN nghiên cứu (S0) | 98.74% | 87.94% | 9.28 | 4.61 | 17.02 | 4.969 |
| UJIIndoorLoc · validationData | Tối ưu PHASE I3 (S4) | 99.91% | 94.69% | 5.36 | 3.52 | 11.89 | 30.791 |
| UJIIndoorLoc · validationData | Cấu hình UJI 5,36 m áp nguyên | 99.91% | 94.69% | 5.36 | 3.52 | 11.89 | — |
| UJI_LIB tầng 3 · Test-01 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 1.33 | 0.85 | 3.55 | 3.615 |
| UJI_LIB tầng 3 · Test-01 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 1.21 | 0.58 | 3.34 | 2.700 |
| UJI_LIB tầng 3 · Test-01 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 1.35 | 0.90 | 3.32 | — |
| UJI_LIB tầng 3 · Test-02 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 1.94 | 1.50 | 3.68 | — |
| UJI_LIB tầng 3 · Test-02 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 2.03 | 1.54 | 3.96 | — |
| UJI_LIB tầng 3 · Test-02 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 1.91 | 1.52 | 3.63 | — |
| DLULIB · Testing | k-NN nghiên cứu (S0) | — (1 tòa) | 99.22% | 4.18 | 3.24 | 8.44 | 0.167 |
| DLULIB · Testing | Tối ưu PHASE I3 (S2) | — (1 tòa) | 99.48% | 3.43 | 2.52 | 7.29 | 0.139 |
| DLULIB · Testing | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | 99.42% | 3.95 | 3.13 | 7.98 | — |
| HCXY · test_HCXY | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 1.93 | 1.27 | 5.01 | 2.663 |
| HCXY · test_HCXY | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 1.55 | 1.12 | 3.12 | 1.542 |
| HCXY · test_HCXY | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 1.62 | 1.20 | 3.37 | — |
| HUS (bỏ dòng chép) · testcase1 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 0.42 | 0.00 | 1.38 | 0.531 |
| HUS (bỏ dòng chép) · testcase1 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 0.39 | 0.00 | 1.43 | 0.177 |
| HUS (bỏ dòng chép) · testcase1 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 0.54 | 0.00 | 1.89 | — |
| HUS (bỏ dòng chép) · testcase2 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 0.33 | 0.00 | 1.16 | — |
| HUS (bỏ dòng chép) · testcase2 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 0.25 | 0.00 | 0.60 | — |
| HUS (bỏ dòng chép) · testcase2 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 0.35 | 0.00 | 1.11 | — |
| HUS nguyên bản · testcase1 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 0.05 | 0.00 | 0.00 | 0.572 |
| HUS nguyên bản · testcase1 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 0.07 | 0.00 | 0.00 | 0.130 |
| HUS nguyên bản · testcase1 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 0.05 | 0.00 | 0.00 | — |
| HUS nguyên bản · testcase2 | k-NN nghiên cứu (S0) | — (1 tòa) | — (1 tầng) | 0.03 | 0.00 | 0.00 | — |
| HUS nguyên bản · testcase2 | Tối ưu PHASE I3 (S2) | — (1 tòa) | — (1 tầng) | 0.06 | 0.00 | 0.00 | — |
| HUS nguyên bản · testcase2 | Cấu hình UJI 5,36 m áp nguyên | — (1 tòa) | — (1 tầng) | 0.03 | 0.00 | 0.00 | — |

Cấu hình PHASE I3 được chọn (chỉ trên tập train):

- **UJIIndoorLoc**: `exponential+braycurtis, k=12, w=1/d^4, offset +-6 dB, ensemble with positive` — sai số dev theo giai đoạn được giữ: S0 12.308 m, S1 7.602 m, S2 6.758 m, S3 6.332 m, S4 6.208 m. k-NN nghiên cứu của bộ này: k=1, manhattan, uniform.
  - Kiểm tra tái lập UJI: bản chung cho 5.3558 m, nghiên cứu gốc 5.3558 m → KHỚP.
- **UJI_LIB tầng 3**: `exponential+braycurtis, k=3, w=1/d^4` — sai số dev theo giai đoạn được giữ: S0 1.547 m, S1 1.405 m, S2 1.358 m. k-NN nghiên cứu của bộ này: k=5, manhattan, distance.
- **DLULIB**: `powed+braycurtis, k=7, w=1/d^4` — sai số dev theo giai đoạn được giữ: S0 3.156 m, S1 2.858 m, S2 2.540 m. k-NN nghiên cứu của bộ này: k=7, manhattan, distance.
- **HCXY**: `powed+braycurtis, k=30, w=1/d^3` — sai số dev theo giai đoạn được giữ: S0 1.832 m, S1 1.827 m, S2 1.413 m. k-NN nghiên cứu của bộ này: k=7, manhattan, distance.
- **HUS (bỏ dòng chép)**: `powed+manhattan, k=4, w=1/d^4` — sai số dev theo giai đoạn được giữ: S0 0.456 m, S1 0.406 m, S2 0.405 m. k-NN nghiên cứu của bộ này: k=11, manhattan, distance.
- **HUS nguyên bản**: `exponential+euclidean, k=1, w=1/d^0` — sai số dev theo giai đoạn được giữ: S0 0.451 m, S1 0.398 m, S2 0.398 m. k-NN nghiên cứu của bộ này: k=11, manhattan, distance.

## 3. HUIM: tập WAP được chọn, thời gian khai thác, so với đối chứng

| Bộ dữ liệu · tập test | Model | Cách lấy WAP | minUtil | Số WAP (giảm) | Khai thác EFIM (s) | Sai số TB HUIM (m) | Top-MI cùng n | Top-support cùng n | Mọi WAP | Tầng HUIM / mọi WAP |
|---|---|---|---|---|---|---|---|---|---|---|
| UJIIndoorLoc · validationData | A | union | 1.9294% | 86 (83.5%) | 578.51 | 19.36 | 19.37 | 16.36 | 5.36 | 66.43% / 94.69% |
| UJIIndoorLoc · validationData | B | union | 2% | 79 (84.8%) | 23.29 | 19.91 | 19.75 | 16.61 | 5.36 | 69.13% / 94.69% |
| UJIIndoorLoc · validationData | C | union | 1.7321% | 91 (82.5%) | 26.76 | 17.49 | 14.73 | 15.79 | 5.36 | 74.26% / 94.69% |
| UJIIndoorLoc · validationData | A | top-n | 1.9294% | 75 (85.6%) | 578.51 | 32.59 | 19.99 | 16.62 | 5.36 | 59.05% / 94.69% |
| UJIIndoorLoc · validationData | B | top-n | 2% | 75 (85.6%) | 23.29 | 20.13 | 19.99 | 16.62 | 5.36 | 68.23% / 94.69% |
| UJIIndoorLoc · validationData | C | top-n | 1.7321% | 75 (85.6%) | 26.76 | 20.68 | 19.99 | 16.62 | 5.36 | 66.97% / 94.69% |
| UJI_LIB tầng 3 · Test-01 | A | union | 1% | 83 (86.6%) | 328.75 | 1.21 | 1.20 | 1.22 | 1.21 | — |
| UJI_LIB tầng 3 · Test-01 | B | union | 1% | 87 (86.0%) | 290.99 | 1.19 | 1.19 | 1.22 | 1.21 | — |
| UJI_LIB tầng 3 · Test-01 | C | union | 1% | 79 (87.3%) | 241.49 | 1.23 | 1.21 | 1.22 | 1.21 | — |
| UJI_LIB tầng 3 · Test-01 | A | top-n | 1.5% | 50 (91.9%) | 152.83 | 1.47 | 1.30 | 1.39 | 1.21 | — |
| UJI_LIB tầng 3 · Test-01 | B | top-n | 1.5% | 75 (87.9%) | 317.35 | 1.25 | 1.23 | 1.23 | 1.21 | — |
| UJI_LIB tầng 3 · Test-01 | C | top-n | 1.5% | 50 (91.9%) | 196.82 | 1.53 | 1.30 | 1.39 | 1.21 | — |
| UJI_LIB tầng 3 · Test-02 | A | union | 1% | 83 (86.6%) | 328.75 | 2.04 | 2.04 | 2.04 | 2.03 | — |
| UJI_LIB tầng 3 · Test-02 | B | union | 1% | 87 (86.0%) | 290.99 | 2.04 | 2.03 | 2.04 | 2.03 | — |
| UJI_LIB tầng 3 · Test-02 | C | union | 1% | 79 (87.3%) | 241.49 | 2.05 | 2.05 | 2.04 | 2.03 | — |
| UJI_LIB tầng 3 · Test-02 | A | top-n | 1.5% | 50 (91.9%) | 152.83 | 2.20 | 2.10 | 2.16 | 2.03 | — |
| UJI_LIB tầng 3 · Test-02 | B | top-n | 1.5% | 75 (87.9%) | 317.35 | 2.05 | 2.07 | 2.05 | 2.03 | — |
| UJI_LIB tầng 3 · Test-02 | C | top-n | 1.5% | 50 (91.9%) | 196.82 | 2.24 | 2.10 | 2.16 | 2.03 | — |
| DLULIB · Testing | A | union | 1% | 17 (0.0%) | 2.31 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| DLULIB · Testing | B | union | 1% | 17 (0.0%) | 2.09 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| DLULIB · Testing | C | union | 1% | 17 (0.0%) | 2.11 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| DLULIB · Testing | A | top-n | 1% | 17 (0.0%) | 2.31 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| DLULIB · Testing | B | top-n | 1% | 17 (0.0%) | 2.09 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| DLULIB · Testing | C | top-n | 1% | 17 (0.0%) | 2.11 | 3.43 | 3.43 | 3.43 | 3.43 | 99.48% / 99.48% |
| HCXY · test_HCXY | A | union | 6.1237% | 67 (80.7%) | 55.65 | 2.12 | 1.80 | 2.14 | 1.55 | — |
| HCXY · test_HCXY | B | union | 6.1237% | 73 (79.0%) | 603.71 | 2.15 | 1.76 | 2.01 | 1.55 | — |
| HCXY · test_HCXY | C | union | 5% | 82 (76.4%) | 153.84 | 2.12 | 1.88 | 1.89 | 1.55 | — |
| HCXY · test_HCXY | A | top-n | 6.1237% | 40 (88.5%) | 55.65 | 2.95 | 2.04 | 1.90 | 1.55 | — |
| HCXY · test_HCXY | B | top-n | 6.777% | 50 (85.6%) | 141.89 | 2.62 | 1.93 | 2.09 | 1.55 | — |
| HCXY · test_HCXY | C | top-n | 7.5% | 20 (94.2%) | 8.92 | 30.56 | 3.50 | 3.48 | 1.55 | — |
| HUS (bỏ dòng chép) · testcase1 | A | union | 20% | 5 (0.0%) | 0.18 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase1 | B | union | 20% | 5 (0.0%) | 0.30 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase1 | C | union | 20% | 5 (0.0%) | 0.18 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase1 | A | top-n | 0.125% | 5 (0.0%) | 0.18 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase1 | B | top-n | 0.125% | 5 (0.0%) | 0.19 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase1 | C | top-n | 0.125% | 5 (0.0%) | 0.19 | 0.39 | 0.39 | 0.39 | 0.39 | — |
| HUS (bỏ dòng chép) · testcase2 | A | union | 20% | 5 (0.0%) | 0.18 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS (bỏ dòng chép) · testcase2 | B | union | 20% | 5 (0.0%) | 0.30 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS (bỏ dòng chép) · testcase2 | C | union | 20% | 5 (0.0%) | 0.18 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS (bỏ dòng chép) · testcase2 | A | top-n | 0.125% | 5 (0.0%) | 0.18 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS (bỏ dòng chép) · testcase2 | B | top-n | 0.125% | 5 (0.0%) | 0.19 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS (bỏ dòng chép) · testcase2 | C | top-n | 0.125% | 5 (0.0%) | 0.19 | 0.25 | 0.25 | 0.25 | 0.25 | — |
| HUS nguyên bản · testcase1 | A | union | 20% | 5 (0.0%) | 0.17 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase1 | B | union | 20% | 5 (0.0%) | 0.25 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase1 | C | union | 20% | 5 (0.0%) | 0.16 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase1 | A | top-n | 0.125% | 5 (0.0%) | 0.17 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase1 | B | top-n | 0.125% | 5 (0.0%) | 0.15 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase1 | C | top-n | 0.125% | 5 (0.0%) | 0.16 | 0.07 | 0.07 | 0.07 | 0.07 | — |
| HUS nguyên bản · testcase2 | A | union | 20% | 5 (0.0%) | 0.17 | 0.06 | 0.06 | 0.06 | 0.06 | — |
| HUS nguyên bản · testcase2 | B | union | 20% | 5 (0.0%) | 0.25 | 0.06 | 0.06 | 0.06 | 0.06 | — |
| HUS nguyên bản · testcase2 | C | union | 20% | 5 (0.0%) | 0.16 | 0.06 | 0.06 | 0.06 | 0.06 | — |
| HUS nguyên bản · testcase2 | A | top-n | 0.125% | 5 (0.0%) | 0.17 | 0.06 | 0.06 | 0.06 | 0.06 | — |
| HUS nguyên bản · testcase2 | B | top-n | 0.125% | 5 (0.0%) | 0.15 | 0.06 | 0.06 | 0.06 | 0.06 | — |
| HUS nguyên bản · testcase2 | C | top-n | 0.125% | 5 (0.0%) | 0.16 | 0.06 | 0.06 | 0.06 | 0.06 | — |

## 4. Cần giữ bao nhiêu WAP? (mô hình tối ưu, tập test chính)

Số WAP nhỏ nhất (trong các ngân sách top-n đã thử) mà sai số TB không vượt quá 1.1 x sai số khi dùng mọi WAP.

| Bộ dữ liệu · tập test | Mọi WAP: số WAP / sai số (m) | HUIM A | HUIM B | HUIM C | Top-MI | Top-support | Ngẫu nhiên |
|---|---|---|---|---|---|---|---|
| UJIIndoorLoc · validationData | 520 / 5.36 | không đạt | không đạt | không đạt | không đạt | không đạt | không đạt |
| UJI_LIB tầng 3 · Test-01 | 620 / 1.21 | không đạt | 75 WAP (1.25 m) | không đạt | 50 WAP (1.30 m) | 75 WAP (1.23 m) | không đạt |
| DLULIB · Testing | 17 / 3.43 | 13 WAP (3.68 m) | 13 WAP (3.68 m) | 13 WAP (3.68 m) | 14 WAP (3.60 m) | 13 WAP (3.68 m) | 14 WAP (3.66 m) |
| HCXY · test_HCXY | 347 / 1.55 | không đạt | không đạt | không đạt | không đạt | không đạt | không đạt |
| HUS (bỏ dòng chép) · testcase1 | 5 / 0.39 | 5 WAP (0.39 m) | 5 WAP (0.39 m) | 5 WAP (0.39 m) | 5 WAP (0.39 m) | 5 WAP (0.39 m) | 5 WAP (0.39 m) |
| HUS nguyên bản · testcase1 | 5 / 0.07 | 5 WAP (0.07 m) | 5 WAP (0.07 m) | 5 WAP (0.07 m) | 5 WAP (0.07 m) | 5 WAP (0.07 m) | 5 WAP (0.07 m) |
