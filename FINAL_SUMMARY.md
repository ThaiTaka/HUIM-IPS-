# FINAL SUMMARY — HUIM trong Indoor Positioning System (UJIIndoorLoc)

> Sinh tự động bởi `src/make_final_summary.py` lúc 2026-10-09T04:06:36+00:00 (UTC). Mọi con số đọc từ `results/`. Không có giá trị nào nhập tay.

---

## 0. Phạm vi — đây là BÀI TÌM HIỂU, chưa phải đồ án

Tài liệu này là kết quả của một **bài tìm hiểu thuật toán** trong học phần cao học, **không phải đồ án tốt nghiệp hay luận văn**. Nhiệm vụ được giao gồm đúng ba phần:

1. **Tìm hiểu thuật toán** — HUIM và EFIM.
2. **Mô hình hoá áp dụng cho IPS** — ánh xạ HUIM ↔ Wi-Fi fingerprint.
3. **Cài đặt và đánh giá trên UJIIndoorLoc**.

Kèm hai tiêu chí đánh giá: **độ chính xác định vị** (mức tham chiếu 7–8 m) và **thời gian, bộ nhớ**.

Hệ quả: mọi phát biểu ở đây là kết quả kiểm chứng trên MỘT bộ dữ liệu, với MỘT cấu hình bộ phân loại và các định nghĩa utility tự đặt. Không có tuyên bố nào về tính tổng quát hay tính mới.

## 1. Tôi đã làm gì?

Thực hiện một nghiên cứu thích nghi: dùng **High Utility Itemset Mining** (thuật toán **EFIM**) làm cơ chế **chọn nhóm Access Point** cho bài toán **định vị trong nhà bằng vân tay Wi-Fi**, thực nghiệm trên **UJIIndoorLoc**, và đánh giá có đối chứng.

Các bước đã chạy thật, theo đúng thứ tự PHASE A → N:

1. **Audit dữ liệu** — đọc read-only hai file CSV, xác minh schema (520 cột WAP, phát hiện bằng cách đếm chứ không hard-code), kiểm chứng giả thuyết `100 = không phát hiện` bằng ba nguồn độc lập, và tìm ra bốn bất thường không có trong tài liệu bộ dữ liệu.
2. **Literature review** — đề xuất 40 DOI, xác minh từng cái qua Crossref API; **4 DOI không tồn tại** và **12 DOI trả về bài báo khác hẳn** bài định trích dẫn, tất cả đã bị loại. Còn **24 nguồn** có tên khớp đúng.
3. **Cài đặt EFIM bằng Python** và kiểm chứng đối chiếu một oracle brute-force độc lập (không có cắt tỉa, tính thẳng từ định nghĩa).
4. **Thiết kế ba utility model** dùng chung internal utility, chỉ khác external utility, để ablation cô lập đúng một biến.
5. **Pilot** trên mẫu con để hiệu chỉnh lưới minUtil, rồi **chạy đầy đủ** 37 lần khai thác trên 19,861 utility transaction.
6. **Đánh giá IPS** trên 190 điều kiện, mỗi điều kiện đánh giá đúng một lần trên 1,111 fingerprint kiểm định, với cùng một cấu hình k-NN đã đóng băng.
7. **Phân tích theo tư duy ngược**, **ablation**, **biểu đồ**, **báo cáo Word**, **PowerPoint**, **speaker notes**.

## 2. Thuật toán cuối cùng

**EFIM** — Zida, Fournier-Viger, Lin, Wu & Tseng, *Knowledge and Information Systems*, vol. 51, no. 2, pp. 595–625, DOI `10.1007/s10115-016-0986-0`.

**Vì sao EFIM, dựa trên literature:** căn cứ chính là đánh giá thực nghiệm **độc lập** của Zhang, Almpanidis, Wang & Liu, *Expert Systems with Applications*, vol. 101, pp. 91–115, 2018, DOI `10.1016/j.eswa.2018.02.008` — không do nhóm tác giả EFIM viết.

**Cài đặt:** Python (`src/huim/efim.py`). SPMF là thư viện tham chiếu nhưng viết bằng Java và môi trường thực nghiệm không có JVM. Hệ quả: bản cài đặt phải tự chứng minh tính đúng.

**Kiểm chứng tính đúng (PHASE F):**

- Đối chiếu với oracle brute-force trên ví dụ chuẩn của literature tại 16 ngưỡng khác nhau.
- 40 cơ sở dữ liệu ngẫu nhiên độc lập × 5 ngưỡng mỗi cái.
- 15 cơ sở dữ liệu có hình dạng thưa-và-rộng giống Wi-Fi.
- Một trường hợp external utility là số thực (vì Model B dùng p không nguyên).
- Hai giá trị utility **tính tay** trong file test (u({b,d}) = 30, u({b,c,d,e}) = 40) để phủ cả tình huống 'cả hai bản cài đặt sai giống nhau'.
- Kiểm chứng TWU là chặn trên (vét cạn), utility KHÔNG anti-monotone, support chính xác sau transaction merging, cắt tỉa thực sự xảy ra, cơ chế dừng có kiểm soát hoạt động, và cổng chặn data leakage raise đúng lúc.
- Mutual information đối chiếu `sklearn.metrics.mutual_info_score` trên 25 bộ dữ liệu ngẫu nhiên.

**Nguyên tắc đã thi hành:** không dòng nào của UJIIndoorLoc được chạy trước khi toàn bộ kiểm thử đạt.

## 3. Utility models

| Model | q(i,T) | p(i) | Tổng utility DB | Vai trò |
|---|---|---|---|---|
| A_signal | RSSI chuẩn hoá (1…100) | `p(i) = 1` | 9,058,242 | Đối chứng: tái tạo chế độ thất bại của frequent itemset mining |
| B_discriminative | RSSI chuẩn hoá (1…100) | `max(I(A_i;Y), 1e-6) / max_j I(A_j;Y)` | 4,354,299 | Model chính |
| C_rare_discriminative | RSSI chuẩn hoá (1…100) | `∝ I(A_i;Y) × log(N/(1+support_i))` | 6,211,852 | Arm thứ ba (tuỳ chọn) |

Cả ba dùng **chung** internal utility: `q(i,T) = round(1 + (RSSI − -104)/(0 − -104) × (100 − 1))`, fit **chỉ trên trainingData**. AP không phát hiện ⟹ item vắng mặt.

[EXPERIMENT RESULT] Tổng utility chênh **2.08×** giữa ba model dù cơ sở dữ liệu và internal utility hoàn toàn giống nhau — chỉ p thay đổi. Đây là lý do minUtil **phải** biểu diễn theo % tổng utility.

## 4. Experiment protocol

| Bước | Dùng dữ liệu nào |
|---|---|
| Chuẩn hoá RSSI (RSSI_min, RSSI_max) | trainingData |
| Trọng số p (mutual information) | trainingData |
| Khai thác HUIM (EFIM) | trainingData |
| Chọn tập AP từ HUI | trainingData |
| Chọn siêu tham số k-NN | train_sub / dev_sub — đều từ trainingData |
| Huấn luyện bộ phân loại cuối | toàn bộ trainingData |
| **ĐÁNH GIÁ** | **validationData — một lần duy nhất mỗi điều kiện** |

**Cấu hình k-NN đã ĐÓNG BĂNG** cho mọi điều kiện: k = 1, metric = manhattan, weights = uniform; chọn một lần trên dev_sub với tập đặc trưng ALL-WAP (joint accuracy trên dev_sub khi chọn: 99.56%). Nhờ vậy khác biệt duy nhất giữa các điều kiện là **cột nào có mặt**. Việc tinh chỉnh trên baseline khiến mọi lợi thế của tinh chỉnh thuộc về **baseline**, không thuộc về phương pháp của bài tìm hiểu.

**Cơ chế cưỡng chế chống leakage:** hàm `build_external_utility` nhận tham số bắt buộc `split_name` và **raise lỗi** nếu khác `'training'` — một lời gọi vô tình trên validationData không thể âm thầm sinh trọng số bị rò rỉ. Có unit test riêng.

**Ngân sách mỗi lần khai thác:** 600 giây hoặc 1,000,000 itemset. Vượt một trong hai ⟹ dừng **có kiểm soát**, ghi `STATUS = ABORTED_RESOURCE_LIMIT`, **giữ lại** kết quả một phần.

**Ba điều kiện đối chứng ở ngân sách khớp nhau:** random-n (3 seed), top-n theo số lần được phát hiện, top-n theo mutual information. Đối chứng thứ ba là khó nhất: nó dùng chính thước đo Model B được cho sẵn nhưng **không** khai thác itemset.

## 5. Kết quả quan trọng

### 5.1. Dữ liệu

- 19,937 fingerprint huấn luyện × 529 cột; 520 cột WAP (đếm thực tế).
- **96.54%** ma trận WAP là sentinel 100; trung bình 17.995 AP được phát hiện mỗi fingerprint.
- Số ô có giá trị trong khoảng 1…99: **0** trên 10,367,240 ô ⟹ 100 là sentinel, cách giá trị kế tiếp 100 đơn vị.
- 465/520 AP từng được phát hiện trong training; **55** AP chỉ có trong validation (trần chặn với MỌI phương pháp).
- 323 AP chỉ nằm trong một toà nhà, chỉ 3 AP thấy được ở cả ba ⟹ dự đoán trước: Building dễ, Floor khó.
- Bất thường: 76 fingerprint không phát hiện AP nào; 137 ô bằng đúng 0 dBm, **toàn bộ từ một thiết bị duy nhất**; 637 dòng trùng lặp hoàn toàn; SPACEID trong validationData đồng nhất bằng 0.
- Hai split **không chung USERID nào**, chỉ chung 2 PHONEID, cách nhau ~90 ngày ⟹ kết quả là con số **cross-device, cross-time**.

### 5.2. Khai thác HUIM

| Utility model | Lần chạy | 0 HUI | Số HUI lớn nhất | Runtime (s) | Peak mem (MB) | ABORTED |
|---|---|---|---|---|---|---|
| A_signal | 14 | 8 | 593,823 | 0.10 – 600.89 | 0.6 – 354.7 | 3 |
| B_discriminative | 11 | 4 | 1,000,001 | 0.23 – 23.29 | 0.0 – 492.8 | 1 |
| C_rare_discriminative | 12 | 6 | 1,000,001 | 0.19 – 99.17 | 0.0 – 518.9 | 1 |

Bước nhảy mạnh nhất đo được:

- **A_signal**: minUtil 1.7321% → 1.5% (1.1547×) ⟹ số HUI 731 → 593,823; item sau TWU chỉ đổi 258 → 263.
- **B_discriminative**: minUtil 2% → 1.5% (1.3333×) ⟹ số HUI 24,621 → 1,000,001; item sau TWU chỉ đổi 204 → 235.
- **C_rare_discriminative**: minUtil 1.7321% → 1.5% (1.1547×) ⟹ số HUI 52,902 → 1,000,001; item sau TWU chỉ đổi 245 → 259.

Tập HUI phong phú nhất **và không bị cắt ngang** của mỗi model:

| Model | Lần chạy | minUtil | Số HUI | Số WAP riêng biệt |
|---|---|---|---|---|
| A_signal | `A_signal__1.9294pct` | 1.9294% | 853 | 86 |
| B_discriminative | `B_discriminative__2pct` | 2% | 24,621 | 79 |
| C_rare_discriminative | `C_rare_discriminative__1.7321pct` | 1.7321% | 52,902 | 91 |

[OUR INTERPRETATION] Tỷ lệ 'rất nhiều HUI / rất ít WAP' là dấu hiệu nhận dạng: các HUI phần lớn là **tập con của nhau**. Một triệu HUI không phải một triệu phát hiện.

### 5.3. Định vị

**Baseline, tất cả 520 WAP:** Building **98.74%**, Floor **87.94%**, Joint **87.76%**, Macro F1 0.8557.

Sai số định vị: trung vị **6.02 m** toạ độ chiếu = **4.61 m thực địa**; trung bình **12.11 m** chiếu = **9.28 m thực địa** (p75 9.39 m, p90 17.02 m, p95 27.81 m thực địa).

**Baseline chỉ các AP từng được phát hiện (465 WAP):** giảm chiều 10.58% **miễn phí**, Joint 87.76%. Phần này **không** nhờ HUIM.

| Utility model | Số WAP | Giảm chiều | Building | Floor | Joint | Δ Joint |
|---|---|---|---|---|---|---|
| A_signal | 75 | 85.58% | 80.20% | 58.42% | **50.86%** | -36.90 pp |
| B_discriminative | 75 | 85.58% | 97.03% | 66.61% | **66.07%** | -21.69 pp |
| C_rare_discriminative | 75 | 85.58% | 97.03% | 66.52% | **65.98%** | -21.78 pp |

[EXPERIMENT RESULT] **Không** tập con nào do HUIM chọn đạt được Joint accuracy của baseline toàn bộ WAP.

### 5.4. So với đối chứng — bảng quyết định kết quả dương hay âm

[EXPERIMENT RESULT] Trên **8** ngân sách đặc trưng khớp nhau, lựa chọn HUIM tốt nhất:

- vượt **chọn ngẫu nhiên**: 5/8
- vượt **top-n theo mutual information**: 3/8
- vượt **top-n theo số lần được phát hiện**: 3/8

### 5.5. Thiếu hụt là do XẾP HẠNG kém hay do QUÁ ÍT đặc trưng?

[EXPERIMENT RESULT] Tập AP lớn nhất mà bất kỳ điều kiện HUIM nào tạo ra là **91 WAP** (`huim_union__C_rare_discriminative__1.7321pct`). Trong trần ngân sách đó, độ chính xác joint cao nhất mà **mọi** phương pháp trong nghiên cứu đạt được là **74.44%** (`control_top_mi__n91`), so với baseline 87.76%.

[EXPERIMENT RESULT] Tập con nhỏ nhất thuộc **bất kỳ** loại nào chạm được baseline dùng **200 WAP** (61.54% giảm chiều, 88.48%, `control_top_support__n200`) — cao hơn hẳn trần 91 WAP mà HUIM có thể cung cấp.

| Utility model | Số ngân sách so sánh | Xếp hạng HUIM vượt ngẫu nhiên |
|---|---|---|
| A_signal | 8 | **0** |
| B_discriminative | 8 | **5** |
| C_rare_discriminative | 8 | **3** |

[OUR INTERPRETATION] Hai cách giải thích phải tách bạch. **(1) Xếp hạng sai** — bảng trên trả lời riêng cho từng model. **(2) Tập quá nhỏ** — HUIM chỉ cung cấp được các AP xuất hiện trong một tập HUI KHÔNG bị cắt ngang, và số đó bị chặn bởi minUtil thấp nhất còn hoàn thành trong ngân sách. **Ngay cả một xếp hạng hoàn hảo cũng không thể lấp khoảng cách từ bên trong cái trần đó.** Đây là phát hiện cơ chế hữu ích nhất của nghiên cứu, và nó chỉ thẳng về Quan sát 1: muốn mở rộng tập AP thì minUtil phải giảm, nhưng giảm minUtil làm số ITEMSET tăng nhanh hơn số AP rất nhiều, và chi phí bùng nổ trước khi tập AP kịp lớn lên một cách hữu ích.

[OUR INTERPRETATION] Lưu ý điều này KHÔNG nói rằng xếp hạng của HUIM là kém; đó là câu hỏi riêng. Nó nói rằng điểm làm việc nơi HUIM có thể cạnh tranh đã không nằm trong tầm với của ngân sách tính toán dùng ở đây — một phát biểu về thiết kế thực nghiệm này cũng nhiều như về bản thân phương pháp.

### 5.5b. Thời gian và bộ nhớ của hệ thống định vị

Chi phí khai thác HUIM ở mục 5.2; đây là nửa còn lại — nơi việc giảm chiều thực sự trả công. Đo một lõi (n_jobs=1), lặp lại lấy trung vị; bộ nhớ cơ sở dữ liệu tính chính xác, không ước lượng.

| Điều kiện | Số WAP | Index | ms / fingerprint | CSDL float64 (MB) | CSDL int8 (MB) | Joint Acc |
|---|---|---|---|---|---|---|
| baseline_all_520 | 520 | brute | 1.2066 | 79.10 | 9.89 | 87.76% |
| baseline_detected_465 | 465 | brute | 1.1838 | 70.73 | 8.84 | 87.76% |
| control_top_mi__n300 | 300 | brute | 0.7771 | 45.63 | 5.70 | 88.30% |
| control_top_support__n300 | 300 | brute | 0.7550 | 45.63 | 5.70 | 88.30% |
| control_top_support__n200 | 200 | brute | 0.4915 | 30.42 | 3.80 | 88.48% |
| control_top_mi__n200 | 200 | brute | 0.5120 | 30.42 | 3.80 | 86.95% |
| control_top_support__n100 | 100 | brute | 0.2153 | 15.21 | 1.90 | 72.82% |
| control_top_mi__n100 | 100 | brute | 0.2365 | 15.21 | 1.90 | 80.56% |
| huim_union__C_rare_discriminative__1.7321pct | 91 | brute | 0.2250 | 13.84 | 1.73 | 71.56% |
| control_top_mi__n91 | 91 | brute | 0.1873 | 13.84 | 1.73 | 74.44% |
| control_top_support__n91 | 91 | brute | 0.1861 | 13.84 | 1.73 | 71.83% |
| huim_union__A_signal__1.9294pct | 86 | brute | 0.2110 | 13.08 | 1.64 | 64.99% |
| huim_union__B_discriminative__2pct | 79 | brute | 0.1969 | 12.02 | 1.50 | 66.79% |
| huim_topn__A_signal__1.9294pct__n75 | 75 | brute | 0.1885 | 11.41 | 1.43 | 50.86% |
| huim_topn__C_rare_discriminative__1.7321pct__n75 | 75 | brute | 0.1875 | 11.41 | 1.43 | 65.98% |
| huim_topn__B_discriminative__2pct__n75 | 75 | brute | 0.1831 | 11.41 | 1.43 | 66.07% |
| control_top_mi__n50 | 50 | brute | 0.1034 | 7.61 | 0.95 | 58.51% |
| control_top_support__n50 | 50 | brute | 0.1037 | 7.61 | 0.95 | 45.09% |
| control_top_support__n25 | 25 | brute | 0.0524 | 3.80 | 0.48 | 26.73% |
| control_top_mi__n25 | 25 | brute | 0.0562 | 3.80 | 0.48 | 24.75% |
| control_top_mi__n10 | 10 | kd_tree | 0.1121 | 1.52 | 0.19 | 18.99% |
| control_top_support__n10 | 10 | kd_tree | 0.0943 | 1.52 | 0.19 | 18.63% |

[EXPERIMENT RESULT] Baseline 520 WAP: **1.207 ms/fingerprint**, CSDL vân tay **79.1 MB**.

[EXPERIMENT RESULT] Điều kiện chính xác nhất toàn nghiên cứu (`control_top_support__n200`, 200 WAP) nhanh hơn **2.5×**, chiếm **38%** bộ nhớ, và joint accuracy 88.48% (+0.72 pp).

[EXPERIMENT RESULT] Cấu hình HUIM tốt nhất (`huim_union__C_rare_discriminative__1.7321pct`, 91 WAP) nhanh hơn **5.4×** và chiếm **18%** bộ nhớ, nhưng joint accuracy chỉ 71.56%.

[OUR INTERPRETATION] Giảm chiều cho lợi ích gần như TUYẾN TÍNH về cả thời gian lẫn bộ nhớ, và đây là phần giá trị KHÔNG gây tranh cãi của toàn bộ hướng tiếp cận. Điều gây tranh cãi là **ai** chọn tập đặc trưng: trên dữ liệu này, tiêu chí đối chứng đơn giản chọn tốt hơn HUIM.

[FACT FROM DATA] Đường cong thời gian không đơn điệu ở số chiều nhỏ nhất (10 WAP): scikit-learn chuyển sang chỉ mục `kd_tree`, mà trên dữ liệu thưa thì cây chậm hơn duyệt vét cạn. Thuật toán index được ghi lại trong log cho từng phép đo.

### 5.5c. Tối ưu sai số định vị theo mét (PHASE I3)

k-NN của PHASE I (k=1, Manhattan) được chọn cho bài toán PHÂN LOẠI tầng trên một phép chia ngẫu nhiên; PHASE I3 tối ưu riêng phần ước lượng toạ độ. Chọn trên GroupKFold(6) over USERID on trainingData (leave-users-out); tiêu chí là sai số trung bình (mét thực địa) trên các fold dev; validationData chỉ chấm điểm mỗi bước đúng một lần.

| Bước | Cấu hình | Dev TB (m) | Val TB (m) | Val trung vị (m) | Joint acc |
|---|---|---|---|---|---|
| S0 study k-NN as regressor | positive+manhattan, k=1, w=1/d^0 | 12.31 | 9.28 | 4.61 | 87.76% |
| S1 best representation x distance (k=1) | positive+cosine, k=1, w=1/d^0 | 7.60 | 6.66 | 4.61 | 92.17% |
| S2 + k and 1/d^p weighting | exponential+braycurtis, k=12, w=1/d^4 | 6.76 | 5.30 | 3.39 | 93.70% |
| S3 + device-offset search | exponential+braycurtis, k=12, w=1/d^4, offset +-6 dB | 6.33 | 5.31 | 3.49 | 94.69% |
| S4 + ensemble of two representations | exponential+braycurtis, k=12, w=1/d^4, offset +-6 dB, ensemble with positive | 6.21 | 5.36 | 3.52 | 94.69% |

[EXPERIMENT RESULT] Mô hình được giao thức chọn (S4): sai số trung bình **5.36 m** thực địa so với 9.28 m (42% thấp hơn), trung vị 3.52 m, joint accuracy 94.69%.

[OUR INTERPRETATION] Phần lớn cải thiện đến từ khoảng cách Bray-Curtis/cosine và k láng giềng có trọng số. Dò độ lệch thiết bị và ensemble thắng trên dev nhưng không giảm thêm sai số mét trên validation (thấp nhất là S2, 5.30 m); chúng chỉ nâng độ chính xác tầng. Mô hình giữ nguyên lựa chọn của giao thức.

Kiểm chứng độc lập `huim_checks.json`: 28 phép kiểm tra, 0 thất bại.
Kiểm chứng độc lập `positioning_checks.json`: 24 phép kiểm tra, 0 thất bại.
Bộ kiểm chứng thủ công bằng Excel: `verification/kiem_chung_thu_cong.xlsx`.

### 5.6. Một kết quả ĐI NGƯỢC kỳ vọng — và nó là hạn chế lớn nhất của thiết kế

[EXPERIMENT RESULT] Top-10 AP được phát hiện nhiều nhất và top-10 AP có mutual information cao nhất trùng **7/10** (WAP070, WAP077, WAP078, WAP087, WAP496, WAP502, WAP517).
[EXPERIMENT RESULT] Trên toàn bộ 465 AP được phát hiện, tương quan hạng giữa số lần được phát hiện và mutual information là **Spearman ρ = 0.9908** (Pearson r = 0.9593). Trùng xếp hạng theo độ sâu: top-10: 7/10, top-25: 18/25, top-50: 45/50, top-100: 90/100, top-200: 186/200.

**Bài tìm hiểu kỳ vọng chứng minh 'frequent ≠ useful' và dữ liệu đã BÁC BỎ kỳ vọng đó ở mức từng Access Point.** Hai tiêu chí gần như trùng khít về thứ hạng. Nguyên nhân nằm ở cách rời rạc hoá: trạng thái 'không phát hiện' chiếm phần áp đảo trong phân bố của mỗi AP, nên I(A_i;Y) chủ yếu đo việc AP có được nhìn thấy hay không ở từng tầng — tức gần như chính là support theo lớp.

[OUR INTERPRETATION] **Hệ quả là hạn chế lớn nhất của thiết kế này:** external utility mà bài tìm hiểu gọi là 'discriminative' trên thực tế gần như là một cách tham số hoá lại tần suất phát hiện. Điều này giải thích nhất quán ba hiện tượng khác: hai đối chứng top-n theo MI và top-n theo support cho kết quả rất gần nhau; Model B và Model C chọn tập AP rất giống nhau; và ablation B–C ít thông tin hơn kỳ vọng. Đây là hạn chế của BÀI TÌM HIỂU, không phải của HUIM.

[OUR INTERPRETATION] Chỗ sự phân biệt 'trông có vẻ giá trị' với 'thực sự hữu ích' THỰC SỰ phát huy là ở mức HÀM UTILITY: Model A (p ≡ 1, utility = cường độ tín hiệu × mức đồng xuất hiện) có xếp hạng tệ hơn cả ngẫu nhiên ở mọi ngân sách đã thử.

Entropy nhãn H(Y) = 3.63916 bit; AP thông tin nhất cung cấp 0.43812 bit, tức 12.0% ⟹ không AP nào một mình giải quyết được bài toán, nên khai thác theo **nhóm** là một ý tưởng đáng thử.

## 6. Kết luận có thể bảo vệ trước giảng viên

Những phát biểu sau đều có số liệu trực tiếp chống lưng:

1. **Mô hình hoá được.** 19,937 fingerprint → 19,861 utility transaction; EFIM chạy và cho kết quả trên 37 cấu hình ngưỡng.
2. **minUtil là núm 'nhóm lớn đến đâu là một mẫu', không phải núm chất lượng.** Số HUI cực nhạy với ngưỡng, số AP riêng biệt thì không.
3. **Chặn trên của EFIM điều khiển TÌM KIẾM, không điều khiển KẾT QUẢ.** Runtime theo số nút cây đã duyệt; bộ nhớ theo kích thước kết quả.
4. **Hàm utility là phát biểu bài toán.** Chỉ đổi p mà tập AP được chọn đã đổi, vì p đi vào cả TWU ⟹ đổi thứ tự item ⟹ đổi hình dạng cây tìm kiếm.
5. **Sự phân biệt 'trông có vẻ giá trị' với 'thực sự hữu ích' nằm ở HÀM UTILITY, không ở tần suất của từng item.** Trên bộ dữ liệu này số lần được phát hiện và mutual information gần như trùng khít về thứ hạng; nhưng Model A, vốn nhân cường độ tín hiệu với mức đồng xuất hiện, xếp hạng AP tệ hơn cả ngẫu nhiên. Đây là một kết quả ĐI NGƯỢC kỳ vọng ban đầu và được báo cáo đúng như đo được.
6. **Building accuracy (98.74%) chịu được giảm chiều; Floor accuracy (87.94%) là ràng buộc chặt.** Dự đoán này được đưa ra từ audit TRƯỚC khi fit mô hình và được kiểm chứng đúng.
7. **Trần kích thước tập AP là ràng buộc quyết định.** HUIM chỉ cung cấp được tối đa 91 WAP trong ngân sách khai thác đã dùng; ở ngân sách đó không phương pháp nào chạm được baseline. Mở rộng tập AP đòi hỏi hạ minUtil, điều làm số itemset bùng nổ nhanh hơn rất nhiều so với số AP thu thêm.
8. **Đóng góp đúng mức:** *bài tìm hiểu khảo sát khả năng thích nghi mô hình High Utility Itemset Mining cho bài toán lựa chọn nhóm Access Point trong Wi-Fi fingerprint indoor positioning.*

## 7. Những điều KHÔNG được khẳng định

- **KHÔNG** khẳng định một High Utility Itemset, một cách tổng quát, là một nhóm đặc trưng tốt cho phân loại. HUIM là bài toán **không giám sát**; không có định lý nào bảo đảm điều đó.
- **KHÔNG** khẳng định HUIM tốt hơn các phương pháp chọn AP information-theoretic đã có. Bảng đối chứng ngân sách khớp nhau là bằng chứng duy nhất được đưa ra, và nó được đọc đúng như nó là.
- **KHÔNG** khẳng định việc chọn Access Point là đóng góp mới — đã có từ Chen et al., *IEEE TKDE*, vol. 18, pp. 877–888, 2006.
- **KHÔNG** khẳng định đây là nghiên cứu HUIM đầu tiên cho IPS. Không tìm thấy bằng chứng ≠ không tồn tại.
- **KHÔNG** gắn Q1/Q2 cho bất kỳ nguồn nào: bài hội nghị không có quartile SJR/JCR, và với bài tạp chí thì `scimagojr.com` trả về HTTP 403 từ môi trường thực nghiệm.
- Sai số định vị ĐƯỢC báo cáo theo mét, nhưng **theo cả hai cách**: mét toạ độ chiếu (quy ước của literature UJIIndoorLoc) và mét thực địa (đã hiệu chỉnh biến dạng Web Mercator). Tài liệu bộ dữ liệu không nêu hệ toạ độ; hệ toạ độ được xác định bằng thực nghiệm, không phải bằng giả định — xem `results/coordinate_system_verification.json`.
- **KHÔNG** ngoại suy ra ngoài UJIIndoorLoc, một cấu hình k-NN và các định nghĩa (q, p) dùng ở đây.

## 8. Hạn chế

**Phương pháp.** Ánh xạ utility mang tính thiết kế — q và p không tồn tại trong dữ liệu Wi-Fi nên phải tự định nghĩa; 'các HUI của UJIIndoorLoc' không phải một đối tượng xác định. HUIM không phải bộ chọn đặc trưng có giám sát. Vùng ngưỡng dùng được rất hẹp. Quy tắc xếp hạng HUI → AP là một thiết kế trong nhiều thiết kế khả dĩ. Siêu tham số k-NN chọn trên một phép chia ngẫu nhiên của trainingData, vốn lạc quan so với validationData.

**Cài đặt.** Không dùng được SPMF (không có JVM). Hiệu năng tuyệt đối là của một cài đặt Python, không so sánh trực tiếp với các bài báo dùng Java — thứ có ý nghĩa là **hình dạng** các đường cong. Các lần chạy vượt ngân sách có tập HUI bị cắt ngang theo thứ tự DFS nên **bị thiên lệch**, vì vậy chúng không được dùng để xếp hạng AP và được đánh dấu rõ trong mọi bảng.

**Dữ liệu.** Bộ dữ liệu từ 2013. Không đồng nhất thiết bị giữa hai split. 55 AP chỉ có trong validation. 76 fingerprint rỗng và 637 dòng trùng lặp được giữ nguyên (ghi nhận, không sửa ngầm). SPACEID trong validation đồng nhất bằng 0 nên không đánh giá được cấp phòng. Đơn vị toạ độ không được tài liệu hoá.

**Tính tổng quát.** Literature review không phải systematic review; IEEE Xplore và ACM DL full-text search không truy cập được.

## 9. Mười câu hỏi giảng viên có thể hỏi

**1. Vì sao utility không anti-monotone, và hệ quả là gì?**

Thêm một item vừa cộng thêm utility của nó (đẩy lên) vừa thu hẹp tập giao dịch chứa itemset (đẩy xuống). Phản ví dụ: u({b}) = 16 < u({b,d}) = 30 nhưng u({b,d,f}) < u({b,d}). Hệ quả: không thể cắt nhánh bằng chính utility — phải cắt bằng chặn trên anti-monotone như TWU, local utility, subtree utility.

**2. EFIM prune bằng gì, và hai chặn khác nhau thế nào?**

Local utility lu(α,z): nếu < minUtil thì loại item z khỏi CẢ cây con của α. Subtree utility su(α,z): nếu < minUtil thì KHÔNG bước vào nhánh α∪{z}. su chặt hơn vì chỉ cộng utility của các item đứng SAU z. Điểm đẹp: lu(∅,z) = TWU(z), nên TWU pruning là trường hợp riêng tại gốc.

**3. Vì sao chọn EFIM mà không phải HUI-Miner hay UP-Growth?**

Căn cứ là một benchmark ĐỘC LẬP (Zhang et al., ESWA 2018), không phải bài báo của chính tác giả EFIM. Thêm hai lý do riêng cho bộ dữ liệu này: transaction merging có đất dùng vì dữ liệu thưa và nhiều vector WAP trùng nhau; và cơ sở dữ liệu RỘNG chứ không SÂU nên chi phí bộ nhớ của hướng utility-list đáng lo hơn.

**4. Giá trị 100 nghĩa là gì, và em chứng minh thế nào?**

Nghĩa là AP không được phát hiện. Ba bằng chứng: (1) tài liệu UCI ghi nguyên văn; (2) phân bố dữ liệu — KHÔNG ô nào trong khoảng 1…99 trên hơn 10 triệu ô, nên 100 cách giá trị kế tiếp đúng 100 đơn vị, một thang đo vật lý không có lỗ hổng như vậy; (3) tính nhất quán — đọc 100 là cường độ sẽ hàm ý mọi AP đều mạnh nhất ở mọi lần quét.

**5. Vì sao không được tính mutual information trên validationData?**

Vì đó là data leakage: tập AP được chọn sẽ 'biết trước' câu trả lời của bài kiểm tra, accuracy cao giả tạo và không nói gì về dữ liệu chưa thấy. Em cưỡng chế bằng code: hàm build_external_utility raise lỗi nếu split_name khác 'training', và có unit test cho cơ chế đó.

**6. HUIM nhiều kết quả hơn thì accuracy cao hơn không?**

Không, và đó là câu hỏi sai. Tập HUI lớn hơn ở ngưỡng thấp hơn phần lớn chỉ là thêm TẬP CON của cùng những nhóm AP: số HUI tăng mà số AP riêng biệt gần như không tăng. Thứ làm thay đổi accuracy là NHỮNG AP NÀO được chọn.

**7. Vì sao phải có đối chứng random, top-support và top-MI?**

Vì 'HUIM đạt accuracy X' tự nó không phải kết quả. Nếu random cùng kích thước cũng đạt X thì việc chọn không làm gì. Nếu top-n theo MI cũng đạt X thì phần khai thác itemset không thêm gì so với thước đo nó được cho sẵn. Đối chứng là cách duy nhất để đọc ablation một cách trung thực.

**8. Vì sao Building accuracy cao hơn Floor accuracy nhiều?**

Vì 323 AP chỉ nằm trong một toà nhà và chỉ 3 AP thấy được ở cả ba, nên xác định toà nhà gần như là một phép tra bảng. Xác định tầng phải phân giải khác biệt tín hiệu TRONG CÙNG một toà nhà, nơi cùng những AP đó nhìn thấy được ở mọi tầng. Dự đoán này có từ audit, trước khi fit mô hình.

**9. Vì sao không báo cáo sai số theo mét?**

Vì không xác minh được. Tài liệu UCI và trang của chính nhóm tác giả đều chỉ cho khoảng giá trị của LONGITUDE/LATITUDE, không nêu hệ toạ độ hay đơn vị; toàn văn bài báo IPIN 2014 nằm sau tường phí. Hộp giới hạn có kích thước hợp lý cho một campus nếu đơn vị là mét, nhưng đó là suy luận, không phải bằng chứng.

**10. Số liệu trong báo cáo có đáng tin không?**

Báo cáo Word và PowerPoint được SINH TỰ ĐỘNG từ results/ và figures/. Script sinh tài liệu không chứa giá trị thực nghiệm nào; thiếu file kết quả thì nó báo lỗi và dừng. Mỗi biểu đồ lưu kèm một CSV chứa đúng các dòng đã vẽ. Mọi lần chạy vượt ngân sách đều được GIỮ trong log với trạng thái ABORTED_RESOURCE_LIMIT.

## 10. Lệnh chạy lại toàn bộ project

```bash
# 1. cài môi trường
python -m pip install -r requirements.txt

# 2. chạy lại tất cả, theo đúng thứ tự PHASE A -> N
python run_experiments.py

# hoặc từng phần:
python run_experiments.py --list              # xem các phase
python run_experiments.py --only tests        # chỉ chạy kiểm thử
python run_experiments.py --from huim         # chạy lại từ PHASE H
python run_experiments.py --offline           # bỏ các phase cần mạng
```

Môi trường đã dùng: Windows-11-10.0.26200-SP0, Python 3.12.10, CPU 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz (8 lõi vật lý / 16 luồng), RAM 15.82 GB. Random seed 20251007.

Thời gian chạy đã ghi nhận: HUIM 1,229.5 s, IPS 185.7 s.

