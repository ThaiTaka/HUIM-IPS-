# KỊCH BẢN THUYẾT TRÌNH — HUIM VÀ ĐỊNH VỊ TRONG NHÀ (IPS)

**Dùng để trình bày trước giảng viên.** Kịch bản bám theo hai file:

- `slides/HUIM_va_IPS_V2.pptx` — 38 slide (Version 2), thực nghiệm trên UJIIndoorLoc.
- `report/Bao_Cao_HUIM_IPS_Da_Dataset.docx` — báo cáo mở rộng sang 5 bộ dữ liệu (phần 2 của kịch bản).

Mọi con số dưới đây chép từ hai file đó hoặc từ file CSV đi kèm từng biểu đồ (`figures/deck_v2/*.csv`, `figures/multi_dataset/*.csv`). Chỗ nào là phép tính để kiểm tay thì ghi đủ phép tính. Phần "câu chuyện nguồn gốc công thức" chỉ dùng những gì có trong các bài báo trích ở slide; mức độ đã kiểm chứng của từng câu chuyện ghi ở mục 3.

---

## MỤC LỤC

- [0. Chuẩn bị trước khi lên](#0-chuẩn-bị-trước-khi-lên)
- [1. Kịch bản từng slide — HUIM_va_IPS_V2.pptx](#1-kịch-bản-từng-slide--huim_va_ips_v2pptx)
- [2. Phần mở rộng — Báo cáo đa dữ liệu (docx)](#2-phần-mở-rộng--báo-cáo-đa-dữ-liệu-docx)
- [3. Câu chuyện nguồn gốc các công thức (có nguồn)](#3-câu-chuyện-nguồn-gốc-các-công-thức-có-nguồn)
- [4. Chuẩn bị hỏi đáp](#4-chuẩn-bị-hỏi-đáp)
- [5. Phiếu kiểm tay nhanh](#5-phiếu-kiểm-tay-nhanh)

---

## 0. Chuẩn bị trước khi lên

### 0.1. Thời lượng gợi ý

| Phần | Slide | Thời gian |
|---|---|---|
| Mở đầu, HUIM là gì, công thức | 1–7 | 6 phút |
| Tiền xử lý, mô hình hoá vân tay thành giao dịch | 8–12 | 6 phút |
| Thuật toán EFIM | 13–15 | 5 phút |
| Kết quả HUIM và định vị (Version 1) | 16–23 | 9 phút |
| Version 2: tối ưu sai số mét | 24–33 | 9 phút |
| Kiểm chứng, kết luận | 34–36 | 3 phút |
| Mở rộng đa dữ liệu (báo cáo docx) | — | 8 phút |
| **Tổng** | | **≈ 46 phút** + hỏi đáp |

**Bản rút gọn 20 phút:** slide 1, 2, 3, 5, 6, 9, 11, 13, 17, 20, 21, 24, 28, 29, 30, 35, 36 và một phút tóm tắt phần đa dữ liệu (mục 2.10).

### 0.2. Ba ngưỡng minUtil phải thuộc lòng

Hầu hết biểu đồ kết quả trên UJIIndoorLoc dùng **tập HUI chính** của mỗi mô hình — lần khai phá **hoàn tất** có minUtil thấp nhất:

| Mô hình | minUtil θ | Tổng utility CSDL | minUtil tuyệt đối = θ × tổng | Số HUI | Số WAP (union) |
|---|---|---|---|---|---|
| A — Signal (p = 1) | **1,9294%** | 9.058.242 | 0,019294 × 9.058.242 ≈ **174.770** | 853 | 86 |
| B — MI (mô hình chính) | **2%** | 4.354.299 | 0,02 × 4.354.299 ≈ **87.086** | 24.621 | 79 |
| C — MI × IDF | **1,7321%** | 6.211.852 | 0,017321 × 6.211.852 ≈ **107.595** | 52.902 | 91 |

**Vì sao có các ngưỡng lẻ 1,9294% và 1,7321%?** Quy trình khai phá:

1. Chạy lưới θ = 20%, 15%, 10%, 7,5%, 5%, 4%, 3,5%, 3%, 2,5%, 2%, 1,5% (giảm dần), dừng ở lần đầu một lần chạy chạm ngân sách 600 giây hoặc 1.000.000 HUI (ghi ABORTED).
2. Tinh chỉnh tối đa 3 lần bằng **trung bình nhân** giữa ngưỡng hoàn tất thấp nhất và ngưỡng bị dừng cao nhất, chỉ khi tập HUI giàu nhất còn dưới 20.000 HUI.

Kiểm tay cho Model A: 2% hoàn tất (130 HUI), 1,5% bị dừng →
√(2 × 1,5) = √3 = **1,7321** (bị dừng) → √(2 × 1,7321) = **1,8612** (bị dừng) → √(2 × 1,8612) = **1,9294** (hoàn tất, 853 HUI).
Model B không tinh chỉnh vì ở 2% đã có 24.621 HUI ≥ 20.000. Model C tinh chỉnh một lần ra 1,7321% (52.902 HUI ≥ 20.000 nên dừng).

### 0.3. Bảng tra nhanh: slide nào đang ở minUtil nào

| Slide | Nội dung | minUtil trên slide |
|---|---|---|
| 1–13 | Khái niệm, công thức, tiền xử lý | Chưa có ngưỡng cụ thể (chỉ định nghĩa) |
| 14 | Ví dụ chạy tay của bài báo EFIM | **minUtil = 30** (số tuyệt đối trên CSDL đồ chơi 5 giao dịch của bài báo, không phải %) |
| 15 | Bảng số item còn lại sau cắt tỉa TWU | 20%, 10%, 5%, 2,5%, 2% |
| 16 | Tổng quan thực nghiệm | Lưới 20% → 1,5% (37 lần chạy) |
| 17 | Số HUI và số WAP theo ngưỡng | Toàn bộ lưới 20% → 1,5%, kể cả 1,9294 / 1,8612 / 1,7321% |
| 18 | Thời gian EFIM ba mô hình | **Cùng 2%** cho cả A, B, C |
| 19 | Runtime và bộ nhớ theo ngưỡng | Toàn bộ lưới 20% → 1,5% |
| 20 | HUIM union so với đối chứng | A 1,9294% · B 2% · C 1,7321% |
| 21 | Giảm chiều và độ chính xác | Đường top-n: A 1,9294% · B 2% · C 1,7321%; hình thoi: mọi lần chạy có HUI (mỗi hình thoi một ngưỡng) |
| 22 | Thời gian, bộ nhớ định vị | Điểm HUIM: union và top-75 ở A 1,9294% · B 2% · C 1,7321% |
| 23 | Sai số mét Version 1 | HUIM C 1,7321% · A 1,9294% · B 2% |
| 24–29 | Version 2 (S0 → S4) | **Không có minUtil** — dùng đủ 520 WAP, không dùng HUIM |
| 30 | Version 2 trên các tập WAP của HUIM | C 1,7321% · A 1,9294% · B 2% (in ngay trên nhãn trục) |
| 31 | Bảng so sánh V1–V2 | Dòng cuối: HUIM union C, 1,7321% |
| 35 | Kết luận RQ2 | 64,99% / 66,79% / 71,56% là union A 1,9294% / B 2% / C 1,7321% |

### 0.4. Cách trình bày một bảng, một biểu đồ (dùng cho mọi slide)

**Bảng — 3 bước:**
1. Nói bảng đo cái gì, trên dữ liệu nào, ở minUtil nào.
2. Đọc mẫu **một dòng** (chỉ tay vào dòng đó).
3. Chốt kết luận bằng **một câu**.

**Biểu đồ — 5 bước:**
1. Trục X là gì (chú ý chiều: có biểu đồ minUtil **giảm dần sang phải**).
2. Trục Y là gì, có phải thang log không.
3. Mỗi màu / ký hiệu là gì (điểm rỗng = lần chạy bị dừng).
4. Chỉ vào **một điểm đáng chú ý**.
5. Kết luận một câu.

**Sơ đồ (dạng hộp và mũi tên):** đi theo mũi tên từ trái sang phải; mỗi hộp nói một câu "đầu vào → làm gì → đầu ra".

**Quy ước khi nói:** gọi "thầy/cô"; đọc số theo kiểu Việt Nam (9,28 m, 19.937 dòng). "m thực địa" là mét thật trên mặt đất; "m toạ độ chiếu" là mét đọc thẳng từ cột toạ độ Web Mercator (lớn hơn thực tế khoảng 31%). "KĐ" là validationData.

---

## 1. Kịch bản từng slide — HUIM_va_IPS_V2.pptx

### Slide 1 — Trang bìa (30 giây)

**Lời thoại:**
> "Em xin chào thầy/cô. Em xin trình bày bài tìm hiểu về **khai phá tập mục hữu ích cao — HUIM**, và thử áp dụng HUIM để chọn điểm truy cập Wi-Fi cho bài toán định vị trong nhà bằng vân tay Wi-Fi, thực nghiệm trên bộ dữ liệu UJIIndoorLoc. Đây là Version 2. Nó thay bản Version 1 làm trên Canva ngày 08/10. Mọi con số trên slide được chương trình đọc từ thư mục kết quả của dự án, em không gõ tay."

---

### Slide 2 — Version 2 có gì mới? (1 phút)

**Trên màn hình:** 4 thẻ số (V1 → V2) và hai cột "Giữ nguyên" / "Thay đổi và bổ sung".

**Cách trình bày:** đọc 4 thẻ từ trái sang phải. Mỗi thẻ là "số Version 1 → số Version 2" trên **cùng 1.111 fingerprint của validationData**.

**Lời thoại:**
> "Kết quả chính của Version 2 là sai số định vị trung bình giảm từ 9,28 m xuống 5,36 m, tính bằng mét thực địa. Trung vị giảm từ 4,61 xuống 3,52 m. Độ chính xác đoán đúng cả tòa nhà lẫn tầng tăng từ 87,76% lên 94,69%. Tỉ lệ fingerprint có sai số không quá 8 m tăng từ 69,5% lên 80,5%.
> Em xin nói rõ ngay từ đầu: phần HUIM được **giữ nguyên** từ Version 1, và kết luận về HUIM không đổi. Tập WAP do HUIM chọn vẫn thua cách chọn đơn giản là lấy top-n theo mutual information. Cải thiện của Version 2 đến từ bộ ước lượng toạ độ, không đến từ HUIM."

**Kiểm tay:** 9,28 − 5,36 = 3,92 m; 3,92 / 9,28 = 42% (đúng con số −42% ở slide 24).

**minUtil:** không có — đây là kết quả dùng đủ 520 WAP.

---

### Slide 3 — HUIM là gì? (1 phút 30)

**Trên màn hình:** bảng so sánh FIM và HUIM (mục tiêu, tiêu chí, kết quả, ví dụ) và ví dụ siêu thị.

**Cách trình bày bảng:** đọc theo hàng **TIÊU CHÍ**: FIM dùng sup(X) ≥ minSup, HUIM dùng u(X) ≥ minUtil. Rồi chỉ hàng **VÍ DỤ**: "bánh mì & sữa" so với "rượu vang & phô mai".

**Lời thoại:**
> "Khai phá tập phổ biến — FIM — chỉ đếm một nhóm mặt hàng xuất hiện bao nhiêu lần. HUIM thêm hai thông tin: **lượng** mua và **giá trị** của mỗi mặt hàng. Một chai nước hoa bán ít nhưng lời cao vẫn có thể là tập hữu ích cao, trong khi FIM sẽ bỏ qua nó vì không đủ phổ biến."

**Câu chuyện nguồn gốc (kể ngắn — chi tiết ở mục 3.1 và 3.2):**
> "FIM bắt nguồn từ bài của Agrawal, Imieliński và Swami ở hội nghị SIGMOD năm 1993, làm tại IBM. Bài toán gốc là dữ liệu 'giỏ hàng': mỗi giao dịch là các món khách mua trong một lần đến cửa hàng, và tác giả thử nghiệm trên dữ liệu bán hàng của một nhà bán lẻ lớn. Năm 2004, Yao, Hamilton và Butz ở hội nghị SDM của SIAM đặt nền móng cho bài toán utility. Bài Two-Phase năm 2005 tóm lại rất gọn: khai phá luật kết hợp truyền thống chỉ là **trường hợp riêng** của khai phá utility, khi utility mỗi mặt hàng luôn bằng 1 và lượng bán chỉ là 0 hoặc 1."

---

### Slide 4 — HUIM và Hệ thống định vị trong nhà (1 phút)

**Trên màn hình:** sơ đồ 3 vị trí A, B, C; các cột AP 1, AP 2, AP 3, …, AP N; màu ô thể hiện cường độ tín hiệu từ thấp đến cao.

**Cách trình bày sơ đồ:** chỉ vào hàng "Vị trí A" và nói: hàng này là một **vân tay** — vector cường độ của mọi AP đo tại vị trí A. Mỗi vị trí có một "mẫu màu" khác nhau, nên nhìn mẫu màu có thể đoán được vị trí.

**Lời thoại:**
> "Định vị bằng vân tay Wi-Fi làm hai bước. Bước offline: đi đo cường độ tín hiệu RSSI của mọi AP tại các vị trí đã biết. Bước online: một điện thoại đo được một vector mới thì tìm vân tay giống nhất trong cơ sở dữ liệu. UJIIndoorLoc có 520 cột WAP, nhưng không phải AP nào cũng có ích. Câu hỏi của em là: **nhóm AP có tổng utility cao mà HUIM tìm ra có phải là tập đặc trưng tốt không?** Em trả lời bằng thực nghiệm có đối chứng."

**Câu chuyện (mục 3.10):** cách làm "đo offline, so khớp online" bắt nguồn từ hệ thống RADAR của Microsoft Research (Bahl & Padmanabhan, INFOCOM 2000).

---

### Slide 5 — Định nghĩa toán học của HUIM (2 phút)

**Trên màn hình:** 4 ô công thức (1: utility, 2: HUI và minUtil, 3: TWU, 4: support) và một dòng ví dụ "utility không đơn điệu".

**Cách trình bày:** đi theo thứ tự ô 1 → 2 → 3 → 4, mỗi ô một câu.

**Lời thoại:**
> "Ô 1: utility của mục i trong giao dịch T bằng **lượng q nhân giá trị p**. Utility của một tập X là tổng trên các mục của nó, cộng qua mọi giao dịch chứa X.
> Ô 2: X là tập hữu ích cao khi u(X) ≥ minUtil. Em đặt minUtil bằng θ phần trăm của tổng utility toàn cơ sở dữ liệu. Lý do: ba mô hình p(i) cho tổng utility chênh nhau 2,08 lần, nên nếu đặt minUtil bằng một số tuyệt đối thì không so sánh được giữa ba mô hình.
> Ô 4 là support của FIM, để thầy/cô thấy HUIM khác FIM ở đâu.
> Quan trọng nhất là dòng dưới cùng: **utility không đơn điệu**. Trong ví dụ chuẩn của bài EFIM, u({b}) = 16, thêm d vào thì u({b,d}) = 30 tăng lên, thêm f thì u({b,d,f}) = 21 lại giảm. Vì vậy không thể cắt tỉa kiểu Apriori bằng chính u(X). Phải dùng một **cận trên** có tính phản đơn điệu, đó là ô 3: TWU."
>
> "TWU của X là tổng utility của các giao dịch chứa X. Nếu TWU của X nhỏ hơn minUtil thì loại X và mọi tập chứa X."

**Kiểm tay (nếu giảng viên hỏi vì sao TWU là cận trên):** với mọi Y ⊇ X và mọi giao dịch T chứa Y, ta có u(Y,T) ≤ TU(T). Các giao dịch chứa Y là tập con của các giao dịch chứa X. Do đó u(Y) ≤ Σ TU(T) trên các T chứa Y ≤ Σ TU(T) trên các T chứa X = TWU(X).

**Câu chuyện (mục 3.3):** TWU là phát minh của bài Two-Phase (Liu, Liao & Choudhary, PAKDD 2005) để vượt qua đúng khó khăn "utility không đơn điệu".

---

### Slide 6 — Mô hình hoá Utility trong IPS (1 phút)

**Trên màn hình:** sơ đồ 4 hộp nối mũi tên: GIAO DỊCH T → ITEM i → UTILITY → HUI; bên dưới là ba mô hình A, B, C; hộp MỤC TIÊU ở đáy.

**Cách trình bày sơ đồ:** đi theo mũi tên:
- **Giao dịch** = một fingerprint = một lần quét Wi-Fi.
- **Item** = một WAP được phát hiện (RSSI ≠ 100).
- **Utility** u(i,T) = q(i,T) × p(i): RSSI chuẩn hoá nhân giá trị của AP.
- **HUI** = nhóm WAP có tổng utility ≥ minUtil.

**Lời thoại:**
> "Ba mô hình dùng **chung q**, chỉ khác **p(i)**. Model A cho p = 1, nên utility chỉ do cường độ và mức đồng xuất hiện. Đây là đối chứng. Model B cho p tỉ lệ với thông tin tương hỗ giữa trạng thái của AP và nhãn tòa nhà–tầng. Model C nhân thêm một thừa số kiểu IDF để phạt AP có mặt ở khắp nơi. Vì chỉ thay p, mọi khác biệt về kết quả giữa ba mô hình đều do p(i) gây ra."

---

### Slide 7 — Ba cách định nghĩa p(i) (1 phút 30)

**Trên màn hình:** ba thẻ A / B / C, mỗi thẻ có công thức, tổng utility CSDL và nguồn.

**Lời thoại:**
> "Model A: p = 1, tổng utility 9.058.242. Model B — mô hình chính: p bằng I(A_i; Y) chia cho MI lớn nhất, có sàn 10⁻⁶ vì EFIM cần utility dương; tổng utility 4.354.299, p trung bình 0,175. Model C: p tỉ lệ với MI nhân log(N / (1 + support)); tổng 6.211.852."

**Câu chuyện (chọn 1 trong 3, mục 3.5–3.7):**
- MI → Shannon 1948, người đặt chữ "bit" theo gợi ý của John Tukey.
- Chọn AP bằng lý thuyết thông tin → Chen, Yang, Yin & Chai 2006 (HKUST): mục tiêu ban đầu là **tiết kiệm pin** điện thoại.
- IDF → Karen Spärck Jones 1972: từ hiếm có giá trị phân biệt cao hơn.

**Lưu ý trung thực:** dòng nguồn của Model B và C ghi "chuẩn hoá về (0, 1] — bài tìm hiểu" và "ghép với MI — bài tìm hiểu". Nghĩa là **cách ghép là thiết kế của em**, không lấy từ bài báo. Nên nói rõ như vậy.

---

### Slide 8 — Tổng quan: 5 bước tiền xử lý (1 phút)

**Trên màn hình:** sơ đồ 5 bước 01 → 05 (Làm sạch → Chuẩn hoá RSSI → Tạo transaction → Trọng số p(i) → Bên trong EFIM) và khung mô tả đầu vào, đầu ra.

**Cách trình bày:** mỗi bước một câu, rồi nhấn hai ý ở khung dưới.

**Lời thoại:**
> "Đầu vào là trainingData 19.937 dòng và validationData 1.111 dòng, mỗi file 520 cột WAP. Có hai điểm em muốn nhấn mạnh.
> Thứ nhất, em **không làm đầy giá trị nào**. Giá trị 100 nghĩa là không phát hiện, tức item vắng mặt. 96,54% số ô WAP bằng 100, và không có ô nào nằm trong khoảng 1 đến 99.
> Thứ hai là **chống rò rỉ**: mọi tham số học từ dữ liệu — RSSI min/max và p(i) — chỉ lấy từ trainingData. Hàm ước lượng p(i) sẽ báo lỗi nếu nhận dữ liệu khác."

---

### Slide 9 — Bước 1: chuẩn hoá RSSI (1 phút 30)

**Trên màn hình:** công thức q(i,T) và bảng 4 WAP của dòng 3.250 trong trainingData.csv.

**Cách trình bày:** đọc công thức, rồi **tính tay dòng WAP255 trước mặt giảng viên**.

**Lời thoại:**
> "RSSI phát hiện được đưa về đoạn [0, 1] theo min = −104 và max = 0 dBm của trainingData, nhân 99, cộng 1, rồi làm tròn. Kết quả q là số nguyên từ 1 đến 100. Lấy WAP255 có RSSI −77 dBm:
> q = 1 + (−77 − (−104)) / (0 − (−104)) × 99 = 1 + 27/104 × 99 = 1 + 25,70 = 26,70, làm tròn được **27**. Đúng như bảng."

**Kiểm tay thêm:**
- WAP284, −89 dBm: 1 + 15/104 × 99 = 15,28 → 15 ✓
- WAP310, −78 dBm: 1 + 26/104 × 99 = 25,75 → 26 ✓

**Lưu ý:** "dòng 3.250 của file CSV" = chỉ số pandas 3.248 (lệch 2: một dòng tiêu đề, và pandas đếm từ 0). Version 1 ghi "dòng 3248"; đây là một trong các chỗ đã đính chính.

**Câu chuyện (mục 3.8):** tên gọi biểu diễn "positive" lấy từ Torres-Sospedra và cộng sự, ESWA 2015 — cùng nhóm tác giả đã công bố UJIIndoorLoc.

---

### Slide 10 — Bước 2: mỗi fingerprint thành một transaction (1 phút)

**Trên màn hình:** sơ đồ 3 hộp (Dòng CSV 3.250 → Transaction → Sau khi có p(i)) và bảng thống kê trainingData.

**Cách trình bày sơ đồ:** hộp 1 là 520 cột, chỉ 4 cột khác 100. Hộp 2 là giao dịch {WAP255: 27, WAP284: 15, WAP310: 26, WAP366: 26}. Hộp 3 là tổng utility của giao dịch theo 3 mô hình.

**Kiểm tay:** TU Model A = 27 + 15 + 26 + 26 = **94** ✓ (vì p = 1). TU của B (≈ 15,5) và C (≈ 37,1) phụ thuộc p(i) của 4 WAP này; có trong file Excel kiểm chứng.

**Cách đọc bảng:** 19.937 dòng → 19.861 giao dịch không rỗng + 76 giao dịch rỗng. Độ dài trung bình 18,06 WAP mỗi giao dịch. Có 465/520 WAP thực sự xuất hiện.

**Lời thoại:**
> "76 dòng rỗng — tức không phát hiện AP nào — tập trung ở vài thiết bị, nhiều nhất là PHONEID 1 với 59 dòng, nên em nghi là lỗi thu thập. EFIM bỏ giao dịch rỗng. Còn bộ phân lớp vẫn giữ các dòng này để mọi điều kiện so sánh nhìn thấy cùng một dữ liệu. Không WAP nào xuất hiện trong hơn 23,8% fingerprint; WAP xuất hiện nhiều nhất là WAP496."

---

### Slide 11 — Bước 3: external utility p(i) — 3 mô hình (2 phút)

**Trên màn hình:** bảng 3 mô hình (p(i), tổng utility, vai trò), công thức entropy và MI, 4 gạch đầu dòng, 2 hệ quả.

**Cách trình bày bảng:** đọc cột "Tổng utility CSDL": 9.058.242 / 4.354.299 / 6.211.852.

**Lời thoại:**
> "Y là nhãn tòa nhà_tầng, có 13 lớp, entropy H(Y) = 3,639 bit. Trạng thái của một AP được rời rạc thành 6 mức: không phát hiện và 5 khoảng dBm. MI được ước lượng từ histogram đồng thời 6 trạng thái × 13 lớp. WAP thông tin nhất là WAP087 với 0,438 bit, bằng 12,0% của H(Y).
> Có hai hệ quả. Hệ quả 1: tổng utility chênh 2,08 lần dù cùng dữ liệu và cùng q, nên minUtil phải biểu diễn theo phần trăm. Hệ quả 2 — đây là **hạn chế lớn nhất** của đề tài: trên 465 WAP, hạng theo MI và hạng theo số lần phát hiện tương quan Spearman ρ = 0,9908. Tức là Model B gần như chỉ là tần suất phát hiện viết lại dưới dạng khác."

**Kiểm tay:**
- 0,438 / 3,639 = 0,120 → 12,0% ✓
- 9.058.242 / 4.354.299 = 2,08 ✓
- Nếu 13 lớp chia đều thì H(Y) = log₂13 = 3,70 bit. Thực tế 3,639 bit, nghĩa là các lớp gần đều.

**Câu chuyện (mục 3.5):** Shannon 1948 và chữ "bit".

---

### Slide 12 — Từ fingerprint Wi-Fi đến bài toán HUIM (1 phút 30)

**Trên màn hình:** bảng ánh xạ (Item = WAP, Transaction = một lần đo, q = RSSI chuẩn hoá 1…100, p = Model A/B/C, HUI = nhóm WAP utility cao), khung "2 quy tắc", công thức contrib(i).

**Cách trình bày bảng:** đọc ngang từng cặp "khái niệm HUIM ↔ trong IPS".

**Lời thoại:**
> "Fingerprint không có sẵn q và p như hoá đơn siêu thị, nên ánh xạ này là **lựa chọn thiết kế của em**. Từ tập HUI, em lấy tập WAP theo hai quy tắc, và cả hai được cố định **trước** khi có bất kỳ kết quả độ chính xác nào.
> **Union**: lấy mọi WAP xuất hiện trong ít nhất một HUI; minUtil là tham số duy nhất.
> **Top-n**: xếp WAP theo điểm đóng góp — mỗi HUI chia đều utility của nó cho các WAP thành viên — rồi lấy n WAP đầu.
> Lần khai phá bị dừng giữa chừng có tập HUI lệch theo thứ tự duyệt DFS, nên không dùng để xếp hạng."

**Ví dụ minh hoạ contrib (tự đặt, không phải số liệu thật):** một HUI {WAP1, WAP2} có u = 100 và một HUI {WAP1, WAP2, WAP3} có u = 90. Khi đó contrib(WAP1) = 100/2 + 90/3 = 50 + 30 = 80; contrib(WAP3) = 30.

**Nguồn:** slide ghi rõ "quy tắc xếp hạng do bài tìm hiểu đặt ra (không lấy từ tài liệu)". Cứ nói đúng như vậy.

---

### Slide 13 — Thuật toán EFIM (1 phút 30)

**Trên màn hình:** sơ đồ 5 bước 01 → 05 (Tiền xử lý → Chiếu CSDL → Duyệt sâu DFS → Tính utility → Xuất HUIs) và khung "TỐI ƯU EFIM".

**Cách trình bày sơ đồ:** đi theo mũi tên.
1. **Tiền xử lý:** tính TU, TWU; bỏ mục TWU < minUtil; sắp mục theo TWU **tăng dần**.
2. **Chiếu CSDL:** khi đi xuống nút α ∪ {z}, mỗi giao dịch chỉ giữ phần đứng sau z.
3. **DFS:** duyệt cây liệt kê tập mục; chỉ mở nhánh có su ≥ minUtil.
4. **Tính utility:** tính u(X) chính xác cho từng tập được duyệt.
5. **Xuất:** giữ các tập có u(X) ≥ minUtil.

**Lời thoại:**
> "EFIM của Zida, Fournier-Viger và cộng sự, đăng ở tạp chí Knowledge and Information Systems năm 2017, có hai ý tưởng chính. Một là hai cận trên mới, lu và su, chặt hơn TWU. Hai là chiếu và gộp giao dịch: giao dịch chiếu giống hệt nhau thì gộp lại, và kỹ thuật Fast Utility Counting tính lu, su trong một lượt quét. Em xin đính chính một lỗi của Version 1: EFIM **không dựng cây dữ liệu** kiểu FP-tree. Nó duyệt cây liệt kê tập mục bằng DFS và chiếu cơ sở dữ liệu."

**Câu chuyện (mục 3.4):** EFIM ra mắt ở hội nghị MICAI 2015 rồi mở rộng thành bài KAIS 2017; nhóm tác giả cũng là nhóm làm thư viện SPMF.

---

### Slide 14 — EFIM: hai cận trên lu và su (2 phút)

**minUtil trên slide: 30 (số tuyệt đối, trên CSDL đồ chơi 5 giao dịch của bài báo EFIM [5]).** Không liên quan đến % của UJIIndoorLoc. Nên nói rõ điều này để giảng viên không nhầm.

**Trên màn hình:** công thức re, lu, su; bảng 7 mục a…g với TWU, thứ tự, su gốc, vai trò.

**Cách trình bày bảng:**
1. Cột TWU đã **sắp tăng dần**: f 30 < g 38 < d 58 < b 61 < a 65 < e 88 < c 96.
2. Mọi TWU ≥ 30, nên ở gốc không mục nào bị loại. Cả 7 mục đều thuộc tập **Secondary** (vì tại gốc lu = TWU).
3. Cột "su gốc": e = 27 và c = 13 nhỏ hơn 30, nên **không mở nhánh** bắt đầu bằng e hoặc c. Chúng chỉ là "Secondary": vẫn được ghép vào nhánh khác nhưng không tự làm gốc nhánh.

**Lời thoại:**
> "lu dùng để quyết định mục z còn được giữ trong cây con hay không; su dùng để quyết định có mở nhánh α ∪ {z} hay không. Tại gốc, lu của z chính bằng TWU(z), nên cắt tỉa TWU chỉ là trường hợp riêng của lu. Kết quả trên ví dụ: EFIM trả về 7 HUI nhưng chỉ duyệt 18 trên 127 tập mục khả dĩ; 19 nhánh bị loại nhờ su."

**Kiểm tay:** 7 mục có 2⁷ − 1 = **127** tập con khác rỗng ✓.

**Lời thoại (vì sao chọn EFIM):**
> "Em chọn EFIM dựa trên một đánh giá thực nghiệm **độc lập**, của Zhang và cộng sự trên ESWA 2018, chứ không chỉ dựa vào bài của chính tác giả EFIM. Thư viện chuẩn SPMF viết bằng Java, nên em cài lại EFIM bằng Python và đối chiếu kết quả với một bộ duyệt vét cạn."

---

### Slide 15 — Tiền xử lý bên trong EFIM (1 phút 30)

**minUtil trên slide: 20%, 10%, 5%, 2,5%, 2% tổng utility.**

**Trên màn hình:** 6 bước tiền xử lý và bảng "số item còn lại sau cắt tỉa TWU" của A, B, C.

**Cách trình bày bảng:** đọc mẫu dòng 20%: trong 465 item ban đầu, Model A còn 17, B còn 41, C còn 31. Rồi đọc dòng 2%: A 250, B 204, C 227.

**Lời thoại:**
> "Ngưỡng càng cao thì cắt tỉa TWU càng loại nhiều item. Một chi tiết kỹ thuật: khi gộp các giao dịch giống hệt nhau, em cộng dồn số lần xuất hiện để độ hỗ trợ vẫn tính đúng."

**Điểm có thể bị hỏi:** thứ tự giữa các mô hình **đảo chiều**: ở 20% và 10% Model B giữ nhiều item nhất, nhưng từ 5% trở xuống Model A giữ nhiều nhất (151 so với 93). Đây chỉ là đọc số trên bảng; slide không giải thích nguyên nhân, nên đừng tự đưa ra lý do nếu chưa kiểm.

---

### Slide 16 — Thực nghiệm trên UJIIndoorLoc (1 phút)

**minUtil:** lưới 20% → 1,5% (cộng các ngưỡng tinh chỉnh), tổng 37 lần chạy.

**Trên màn hình:** 3 số lớn (19.937 / 1.111 / 520) và sơ đồ quy trình 5 bước 01 → 05.

**Kiểm tay:** 37 lần = 14 (A) + 11 (B) + 12 (C).

**Lời thoại:**
> "Quy trình có năm bước: tiền xử lý, chuyển fingerprint thành 19.861 giao dịch, khai phá bằng EFIM 37 lần cho 3 mô hình từ 20% xuống 1,5%, định vị bằng k-NN, và đánh giá tòa nhà, tầng, sai số mét, thời gian, bộ nhớ. Version 1 dùng k = 1, khoảng cách Manhattan; Version 2 dùng Bray–Curtis với k = 12. Mọi tham số được chọn trên trainingData. validationData chỉ dùng để đánh giá, một lần cho mỗi điều kiện: 190 điều kiện ở Version 1 và 5 bước S0 → S4 ở Version 2."

---

### Slide 17 — Số HUI và số WAP theo minUtil (2 phút)

**minUtil:** toàn bộ lưới, trục X **từ 20% giảm dần sang phải đến 1,5%**. Gồm cả các điểm tinh chỉnh 1,9294% / 1,8612% / 1,7321% (Model A) và 1,7321% (Model C).

**Trên màn hình:** biểu đồ (a) số HUI (trục Y symlog), biểu đồ (b) số WAP trong hợp các HUI. Xám = Model A, xanh = B, cam = C. **Điểm rỗng = lần chạy bị dừng** vì chạm 600 s hoặc 1.000.000 HUI.

**Cách trình bày biểu đồ (a):**
1. "Trục X là minUtil theo % tổng utility, **giảm dần sang phải**. Trục Y là số HUI, thang log."
2. Chỉ đoạn nằm ngang ở 0 bên trái: "Ở ngưỡng cao không có HUI nào."
3. Chỉ chỗ mỗi đường bắt đầu đi lên:
   - B: HUI đầu tiên ở **5%** (1 HUI); 4 lần chạy trước đó (20%, 15%, 10%, 7,5%) cho 0 HUI.
   - C: HUI đầu tiên ở **3,5%** (2 HUI); 6 lần chạy cho 0 HUI.
   - A: HUI đầu tiên ở **2,5%** (2 HUI); 8 lần chạy cho 0 HUI.
4. Chỉ phía phải: "Chỉ trong một bước ngưỡng, số HUI đi từ vài trăm lên chạm trần 1.000.000 — đó là **chuyển pha** rất gắt."

**Cách trình bày biểu đồ (b):**
> "Dù số HUI lên tới hàng chục nghìn, số WAP riêng biệt nằm trong các HUI chỉ lên tới 79–91 ở các lần chạy xong. Điểm rỗng của Model A ở 1,8612% chỉ có 31 WAP: lần chạy bị dừng giữa chừng nên tập HUI bị cắt cụt theo thứ tự DFS. Đó là lý do em không dùng lần chạy bị dừng để xếp hạng WAP."

**Số liệu để trả lời nhanh (CSV `d01_minutil_hui_wap.csv`):**

| Mô hình | Lần chạy chính | Số HUI | Số WAP |
|---|---|---|---|
| A | 1,9294% | 853 | 86 |
| B | 2% | 24.621 | 79 |
| C | 1,7321% | 52.902 | 91 |

---

### Slide 18 — p(i) quyết định chi phí khai phá (1 phút 30)

**minUtil: cùng 2% tổng utility cho cả ba mô hình**, EFIM chạy trên 19.861 giao dịch.

> **Lưu ý khi nói:** 2% là ngưỡng **chung để so sánh**. Nó là lần chạy chính của Model B, nhưng không phải lần chạy chính của A (1,9294%) và C (1,7321%).

**Trên màn hình:** biểu đồ cột thời gian chạy: A 338,1 s (130 HUI), B 23,3 s (24.621 HUI), C 12,4 s (1.001 HUI); hai thẻ số "14,5–27,2×" và "130 vs 24.621".

**Lời thoại:**
> "Cùng ngưỡng 2%, Model A chạy 338 giây, chậm hơn B 14,5 lần và chậm hơn C 27,2 lần. Điều lạ là A chỉ tìm được 130 HUI, ít hơn B rất nhiều mà vẫn chậm hơn. Lý do: khi p = 1, các cận trên ít phân biệt được mục này với mục kia, nên cắt tỉa kém và EFIM phải duyệt rất nhiều nút."

**Kiểm tay:** 338,1 / 23,3 = 14,5 ✓; 338,1 / 12,4 = 27,3 (slide làm tròn từ số chưa làm tròn 338,1349 / 12,4432 = 27,2) ✓.

**Bằng chứng cho lời giải thích (CSV `d03`):** ở 2%, số nút EFIM đã duyệt là A 3.560.578, B 224.711, C 28.670.

---

### Slide 19 — Runtime và bộ nhớ theo ngưỡng (1 phút 30)

**minUtil:** toàn bộ lưới 20% → 1,5%, trục X giảm dần sang phải.

**Trên màn hình:** (a) thời gian khai phá (thang log); (b) bộ nhớ đỉnh tăng thêm (MB). Điểm rỗng = bị dừng.

**Cách trình bày:**
1. Panel (a): "Thời gian tăng dần khi hạ ngưỡng. Model A vọt lên trần 600 s từ khoảng 2%."
2. **Chỉ điểm dễ gây hiểu nhầm:** đường xanh (B) **đi xuống** ở 1,5%. "Không phải B chạy nhanh hơn. Lần chạy này dừng sau 8 giây vì chạm trần 1.000.000 HUI, không phải trần thời gian."
3. Panel (b): "Bộ nhớ gần như bằng 0 cho đến 2%, rồi vọt lên 350–520 MB ở các lần bị dừng tại 1,5%."

**Lời thoại:**
> "Tương quan Spearman giữa số nút đã duyệt và thời gian chạy là 0,995 / 0,973 / 0,998 cho A, B, C. Nghĩa là chi phí của EFIM là **chi phí trên mỗi nút**: muốn biết lần chạy tốn bao nhiêu thì nhìn số nút phải duyệt."

**Số liệu:** A 0,10–600,89 s, bộ nhớ đỉnh 0,6–354,7 MB, dừng 3 lần; B 0,23–23,29 s, 0,0–492,8 MB, dừng 1 lần; C 0,19–99,17 s, 0,0–518,9 MB, dừng 1 lần.

---

### Slide 20 — HUIM có hơn các đối chứng không? (2 phút)

**minUtil (in dưới mỗi nhóm cột):** Model A · 86 WAP · **1,9294%**; Model B · 79 WAP · **2%**; Model C · 91 WAP · **1,7321%**.

**Trên màn hình:** biểu đồ cột độ chính xác joint (tòa nhà + tầng) trên validationData. Bốn cột mỗi nhóm: vàng = HUIM union, xanh ngọc = top-n theo MI, đen = top-n theo số lần phát hiện, xám = ngẫu nhiên (trung bình 3 seed). Đường đứt nét = baseline 520 WAP, 87,76%. Bên phải là 3 thẻ 5/8, 3/8, 3/8.

**Cách trình bày biểu đồ:**
1. "Mỗi nhóm cột so 4 cách chọn ở **cùng số WAP**. Ví dụ nhóm Model C: chọn 91 WAP."
2. Đọc nhóm C: HUIM 71,6% — top-MI 74,4% — top-phát hiện 71,8% — ngẫu nhiên 69,4%.
3. "Cột vàng thắng cột xám ở B và C, nhưng **thua cột xanh ngọc ở cả ba mô hình**. Mọi cột đều dưới đường đứt nét 87,76%."

**Cách giải thích 3 thẻ bên phải (giảng viên hay hỏi "8 là 8 cái gì?"):** 8 là **8 ngân sách WAP** n = 5, 10, 15, 20, 30, 40, 50, 75. Ở mỗi ngân sách, lấy tập **top-n** tốt nhất trong A/B/C (cùng minUtil A 1,9294% · B 2% · C 1,7321%) và so với đối chứng cùng n. Đây là top-n, khác với biểu đồ cột (union).

| n | HUIM tốt nhất | Top-MI | Top-phát hiện | Ngẫu nhiên | Thắng NN / MI / PH |
|---|---|---|---|---|---|
| 5 | 14,04% (B) | 13,41% | 11,88% | 13,11% | ✓ ✓ ✓ |
| 10 | 18,00% (B) | 18,99% | 18,63% | 13,20% | ✓ ✗ ✗ |
| 15 | 21,78% (C) | 20,79% | 20,97% | 15,27% | ✓ ✓ ✓ |
| 20 | 24,39% (B) | 22,86% | 24,03% | 24,00% | ✓ ✓ ✓ |
| 30 | 25,20% (C) | 34,02% | 28,62% | 29,46% | ✗ ✗ ✗ |
| 40 | 26,64% (B) | 43,29% | 29,61% | 37,41% | ✗ ✗ ✗ |
| 50 | 42,39% (C) | 58,51% | 45,09% | 46,89% | ✗ ✗ ✗ |
| 75 | 66,07% (B) | 69,85% | 67,96% | 56,44% | ✓ ✗ ✗ |

Đếm: thắng ngẫu nhiên 5/8, thắng top-MI 3/8, thắng top-phát hiện 3/8 ✓. HUIM chỉ thắng ở ngân sách rất nhỏ (5–20 WAP), nơi mọi phương pháp đều dưới 25%.

**Lời thoại kết:**
> "Kết luận trung thực: HUIM union thắng chọn ngẫu nhiên ở B và C, nhưng thua top-n theo MI ở cả ba mô hình. Và không cách chọn nào đạt mức dùng đủ 520 WAP."

**Lưu ý trung thực (nếu bị hỏi vì sao chọn đúng ba tập union này):** mỗi tập là union của **lần chạy chính**, và cũng là union có joint cao nhất của mô hình đó trên validationData. Cách chọn này **ưu ái HUIM**; dù vậy HUIM vẫn thua top-MI, nên kết luận càng chắc.

---

### Slide 21 — Feature Reduction và Accuracy (2 phút)

**minUtil:** các đường top-n: HUIM A **1,9294%**, B **2%**, C **1,7321%** (ghi trong chú giải). **Hình thoi** = tập union của **mọi lần chạy có HUI**, mỗi hình thoi một ngưỡng riêng:
- A: 2,5% · 2% · 1,9294% · 1,8612%* · 1,7321%* · 1,5%*
- B: 5% · 4% · 3,5% · 3% · 2,5% · 2% · 1,5%*
- C: 3,5% · 3% · 2,5% · 2% · 1,7321% · 1,5%*

(* = lần chạy bị dừng.) Hình thoi cao nhất là **C 1,7321%**: 91 WAP, giảm chiều 82,5%, joint 71,56%.

**Trên màn hình:** trục X = giảm chiều (%) = (1 − số WAP chọn / 520) × 100; trục Y = joint (%); đường đứt nét = baseline 87,76%.

**Cách trình bày biểu đồ:**
1. "Trục X càng sang phải thì càng bỏ nhiều WAP."
2. Chỉ góc trái trên: "Bỏ tới khoảng 60% số WAP, các đường top-n đối chứng vẫn bám đường baseline."
3. Chỉ vùng 80–100%: "Mọi đường cắm xuống. Các điểm HUIM — đường xám, xanh, cam và hình thoi — đều nằm ở vùng này, vì HUIM chỉ cho tối đa 91 WAP."
4. "Không hình thoi nào chạm được đường đứt nét."

**Kiểm tay:**
- 91 WAP: (1 − 91/520) × 100 = 82,5% ✓
- 200 WAP: (1 − 200/520) × 100 = 61,5% ✓

**Lời thoại:**
> "Độ chính xác tòa nhà chịu được giảm chiều mạnh, còn độ chính xác **tầng** mới là ràng buộc chặt. Ở ngân sách 91 WAP, cách tốt nhất trong mọi phương pháp chỉ đạt 74,44%, là top-91 theo MI. Phải tới 200 WAP — top-200 theo số lần phát hiện, 88,48% — mới chạm baseline. Con số đó vượt xa trần 91 WAP mà HUIM cung cấp."

---

### Slide 22 — Đánh giá thời gian và bộ nhớ định vị (1 phút 30)

**minUtil:** các chấm cam (HUIM) = union A 1,9294% (86 WAP), B 2% (79), C 1,7321% (91) và top-75 của ba tập đó.

**Trên màn hình:** (a) ms/fingerprint theo số WAP; (b) bộ nhớ CSDL vân tay theo số WAP (float64 / float32 / int8); (c) joint (%) theo ms/fingerprint.

**Cách trình bày:**
1. Panel (a), (b): "Thời gian và bộ nhớ tăng gần như **tuyến tính** theo số WAP."
2. Panel (c): "Góc **trên-trái** là lý tưởng: nhanh mà chính xác. Các điểm top-200 (≈ 0,5 ms, ≈ 88%) gần góc đó nhất. Các chấm cam HUIM nhanh (≈ 0,2 ms) nhưng joint chỉ 51–72%."

**Kiểm tay bộ nhớ** (bộ nhớ = số dòng × số cột × 8 byte):
- 19.937 × 520 × 8 = 82.937.920 byte; chia 1.048.576 = **79,1 MB** ✓
- 19.937 × 91 × 8 / 1.048.576 = 13,84 MB → 13,84 / 79,10 = **18%** ✓
- Tốc độ: 1,2066 / 0,2250 = **5,4×** ✓; top-200: 1,2066 / 0,4915 = **2,5×**, bộ nhớ 30,42 / 79,10 = **38%** ✓

**Lời thoại:**
> "Baseline 520 WAP mất 1,207 ms mỗi fingerprint, cơ sở dữ liệu vân tay 79,1 MB. HUIM tốt nhất nhanh hơn 5,4 lần và chỉ tốn 18% bộ nhớ, nhưng joint chỉ 71,56%. Top-200 theo số lần phát hiện nhanh hơn 2,5 lần, 38% bộ nhớ và vẫn giữ 88,48%. Thời gian đo trên một lõi CPU, lặp lại lấy trung vị. Bộ định vị Version 2 chưa được đo thời gian ở slide này."

---

### Slide 23 — Độ chính xác định vị theo mét — V1 (2 phút)

**minUtil:** cột HUIM C 91 WAP = **1,7321%**, HUIM A 86 WAP = **1,9294%**, HUIM B 79 WAP = **2%**. Trên trục chỉ ghi số WAP, nên **phải nói miệng ngưỡng**.

**Trên màn hình:** biểu đồ cột sai số (m thực địa) của 6 tập WAP, mỗi tập 3 cột: trung vị (xanh), trung bình (vàng), P90 (đen). Dải xanh lá = mức tham chiếu 7–8 m. Bên dưới là công thức sai số thực địa.

**Cách trình bày biểu đồ:**
1. Nhóm "Baseline 520 WAP": trung vị 4,6 — trung bình 9,3 — P90 17,0.
2. "Trung vị **dưới** dải 7–8 m, nhưng trung bình **trên** dải. Phân bố có đuôi dài: P95 = 27,8 m."
3. Chỉ các nhóm HUIM: "P90 của các tập HUIM lên tới 51–60 m."

**Giải thích công thức (rất hay bị hỏi):**
> "Toạ độ của UJIIndoorLoc là hệ chiếu Web Mercator EPSG:3857. Em xác định điều này bằng cách nghịch đảo phép chiếu: điểm rơi cách campus UJI 139,7 m. Web Mercator không bảo toàn khoảng cách; hệ số tỉ lệ ở vĩ độ φ là sec φ. Muốn ra mét thật thì nhân khoảng cách đọc từ toạ độ với cos φ = 0,766126, với φ = 39,9927°."

**Kiểm tay:**
- 1 / 0,766126 = 1,305268 → đọc thẳng từ toạ độ sẽ lớn hơn thực tế khoảng 31% ✓
- 6,02 × 0,766126 = 4,61 m ✓; 12,11 × 0,766126 = 9,28 m ✓
- cos 40° = 0,7660 (gần đúng, để giảng viên thấy hợp lý)

**Mức 7–8 m là gì?** Đây là **mốc mục tiêu đề tài đặt ra** (mã nguồn ghi "mức tham chiếu 7–8 m mà đề tài đặt ra"), không phải chuẩn công bố trong bài báo. Nếu bị hỏi nguồn thì nói đúng như vậy, đừng gán cho tài liệu nào.

**Câu chuyện (mục 3.12):** hệ số sec φ có trong cẩm nang phép chiếu bản đồ của Snyder (USGS, 1987). Cách báo cáo trung vị, trung bình và phân vị theo khảo sát của Adler et al., IPIN 2015.

---

### Slide 24 — Version 2: Tối ưu sai số định vị theo mét (20 giây)

**minUtil:** không — từ đây đến slide 29 dùng đủ 520 WAP.

**Lời thoại:**
> "Phần Version 2 giữ nguyên dữ liệu, HUIM và giao thức chống rò rỉ; chỉ thay bộ ước lượng toạ độ. Sai số trung bình giảm từ 9,28 xuống 5,36 m, tức giảm 42%, trên 1.111 fingerprint kiểm định."

---

### Slide 25 — Vì sao Version 1 sai số lớn? (1 phút 30)

**Trên màn hình:** sơ đồ 5 thẻ đánh số 1–5.

**Cách trình bày:** đọc 5 thẻ, mỗi thẻ một câu.
1. **Chọn tham số sai mục tiêu:** k = 1, Manhattan được chọn cho bài toán *phân loại tầng*, không phải ước lượng toạ độ.
2. **Phép chia dev không giống tập kiểm định:** chia ngẫu nhiên 75/25 để lọt fingerprint đo tại cùng một điểm vào cả hai phía, nên k = 1 thắng. Trong khi đó validationData dùng thiết bị khác (9/11 mã thiết bị không có trong train) tại 1.074 vị trí.
3. **Phương sai cao của k = 1:** toạ độ dự đoán chính là một vị trí huấn luyện, nên chọn sai láng giềng là sai trọn vẹn.
4. **Hoà khoảng cách:** RSSI là số nguyên, khoảng cách Manhattan thường bằng nhau; với k = 1, cách phá hoà quyết định toạ độ.
5. **Lệch thiết bị:** điện thoại khác nhau đo RSSI lệch mức [15], [16].

> **Sửa miệng một con số trên slide:** thẻ 2 ghi "1.074 vị trí". Con số này đếm cả 21 cặp toạ độ chỉ lệch nhau tối đa 7,5 × 10⁻⁹ m, tức nhiễu số thực trong file CSV. Gộp các cặp đó lại thì validationData có **1.053 vị trí**, khớp với Bảng 1 của báo cáo đa dữ liệu (18 vị trí trùng train). Khi nói, dùng "1.053 vị trí".

**Lời thoại chuyển ý:**
> "Từ năm nguyên nhân này, em sửa ở hai chỗ: **cách chọn mô hình** (slide 26) và **bộ ước lượng** (slide 27)."

---

### Slide 26 — Giao thức chọn mô hình không rò rỉ (1 phút 30)

**Trên màn hình:** sơ đồ lưới 6 hàng (Fold 1–6) × 6 ô; ô vàng = fold dev, ô xanh = huấn luyện. Bên phải là bảng "Bước — Dữ liệu dùng".

**Cách trình bày sơ đồ:**
> "Mỗi hàng là một lần thử. Ở Fold 1, nhóm người đo thứ nhất (ô vàng) bị giấu đi để chấm điểm, năm nhóm còn lại dùng để huấn luyện. Lần lượt như vậy đến Fold 6. 18 người đo của trainingData được chia thành 6 nhóm theo USERID, nên mỗi fold dev chỉ gồm người đo mà mô hình **chưa từng thấy**. Đó là kiểu 'leave-users-out', mô phỏng đúng tình huống kiểm định: người đo mới, thiết bị mới."

**Cách trình bày bảng:** chỉ dòng tô xanh "Chọn mô hình định vị (Version 2) — 6 fold giữ lại người đo", và dòng cuối "Đánh giá — validationData, 1 lần / bước".

**Lời thoại:**
> "Tiêu chí chọn là sai số trung bình theo mét thực địa trên các fold dev. Có 5 bước nối tiếp S0 → S4, và bước sau chỉ được nhận nếu giảm sai số dev ít nhất 0,05 m. validationData chỉ chấm điểm mỗi bước một lần, **sau khi** lựa chọn đã xong."

---

### Slide 27 — Các cải tiến của Version 2: công thức và nguồn (3 phút)

**minUtil:** không (520 WAP).

**Trên màn hình:** 4 ô: (1) biểu diễn powed / exponential; (2) khoảng cách Bray–Curtis; (3) k-NN trọng số nghịch đảo khoảng cách; (4) dò lệch thiết bị và ensemble.

**Ô 1 — Biểu diễn tín hiệu:**
> "Em thử ba cách biểu diễn: positive, powed và exponential. Dev chọn exponential."

**Kiểm tay exponential** = exp((RSSI + 105)/24) / exp(105/24) = exp(RSSI/24):
- RSSI = 0 dBm → 1
- RSSI = −60 dBm → e^(−2,5) = 0,082
- RSSI = −104 dBm → e^(−4,33) = 0,013

Cách hiểu của em (không phải trích bài báo): biểu diễn này kéo giãn chênh lệch giữa các tín hiệu mạnh và nén các tín hiệu yếu lại gần 0, nên tín hiệu yếu ít ảnh hưởng tới khoảng cách.

**Ô 2 — Bray–Curtis:** d = Σ|a_j − b_j| / Σ(a_j + b_j). Đây là khoảng cách tuyệt đối được **chuẩn hoá theo tổng cường độ** của hai vector.

Ví dụ tính tay (tự đặt): a = (3, 0, 5), b = (1, 2, 5). Tử số = 2 + 2 + 0 = 4; mẫu số = 4 + 2 + 10 = 16 → d = 0,25.

**Ô 3 — k-NN trọng số:** x̂ = Σ w_i x_i / Σ w_i, với w_i = 1/d_i^p. Lưới k từ 1 đến 30, p từ 0 đến 4; dev chọn k = 12, p = 4.
> "Với p = 4, một láng giềng ở xa gấp đôi chỉ có trọng số bằng 1/16. Vì vậy lấy 12 láng giềng vẫn an toàn: láng giềng xa gần như không kéo lệch kết quả."

**Ô 4 — Dò lệch thiết bị và ensemble:** cộng δ ∈ {−6, …, +6} dB (bước 3) vào RSSI của truy vấn, giữ δ làm láng giềng gần nhất gần nhất; rồi lấy trung bình toạ độ của mô hình exponential và mô hình positive.

> **Nói trung thực:** ô 4 ghi "thiết kế của bài tìm hiểu — chưa đối chiếu tài liệu về hiệu chỉnh lệch thiết bị [CẦN BỔ SUNG NGUỒN]". Phải nói rõ phần này là do em đề xuất, chưa có nguồn.

**Dòng cuối:**
> "Láng giềng được sắp theo cặp (khoảng cách, chỉ số dòng), nên kết quả không phụ thuộc vào cách thư viện xử lý các khoảng cách bằng nhau."

**Câu chuyện (chọn 1–2, mục 3.8–3.11):** Bray–Curtis vốn để so sánh **rừng cây ở Wisconsin** năm 1957. RADAR năm 2000 đã thấy lấy trung bình k láng giềng có lợi khi k nhỏ, nhưng k lớn thì kém đi. Shepard 1968 nghĩ ra trọng số nghịch đảo khoảng cách cho chương trình vẽ bản đồ.

---

### Slide 28 — Kết quả từng bước S0 → S4 (2 phút)

**minUtil:** không (520 WAP, không dùng HUIM).

**Trên màn hình:** biểu đồ cột đôi: cột xám = dev (6 fold giữ lại người đo, dùng để **chọn**), cột đen = validationData (chỉ để **báo cáo**). Dải xanh = mức tham chiếu 7–8 m. Bên phải là bảng 5 bước.

**Cách trình bày biểu đồ:**
1. "Cột xám — dev — **giảm đều** từ 12,31 xuống 6,21. Điều này là tất nhiên, vì quy tắc chỉ nhận một bước khi nó làm dev giảm."
2. "Cột đen — validationData — giảm mạnh ở S1 (6,66) và S2 (5,30), rồi **gần như đứng yên**: S3 5,31, S4 5,36."
3. "Phần lớn mức giảm đến từ S1–S2: đổi khoảng cách và dùng k láng giềng có trọng số."

**Cách đọc bảng:** đọc dòng S4: dev 6,21 — KĐ trung bình 5,36 — KĐ trung vị 3,52 — joint 94,69%.

**Lời thoại trung thực (quan trọng):**
> "Em xin nói thẳng: S2 có sai số kiểm định thấp nhất, 5,30 m, thấp hơn S4 là 5,36 m. Nhưng giao thức chọn trên dev đã chọn S4, nên em giữ S4. Nếu em quay lại chọn S2 vì nhìn thấy số kiểm định thì đó là dùng tập kiểm tra để chọn mô hình, tức là rò rỉ. Dò lệch và ensemble chủ yếu nâng độ chính xác tầng: từ 93,70% lên 94,69%."

**Kiểm tay quy tắc 0,05 m:** S3 nhận vì 6,76 − 6,33 = 0,43 ≥ 0,05; S4 nhận vì 6,33 − 6,21 = 0,12 ≥ 0,05.

---

### Slide 29 — Phân bố sai số: V1 so với V2 (2 phút)

**minUtil:** không (520 WAP).

**Trên màn hình:** đường CDF: nét đứt = V1, nét liền = V2; dải xanh 7–8 m. Bảng phân vị V1/V2; khung bootstrap.

**Cách trình bày CDF (hai cách đọc):**
1. **Đọc dọc** tại x = 8 m: đường V2 ở 80,5%, V1 ở 69,5%. "Tỉ lệ fingerprint sai không quá 8 m tăng 11 điểm phần trăm."
2. **Đọc ngang** tại y = 50%: V1 cắt ở 4,61 m, V2 cắt ở 3,52 m. "Đó chính là trung vị."
3. "Đường liền nằm **bên trái** đường đứt trên gần như cả trục: V2 dịch cả phân bố sang trái, kể cả đuôi. P95 giảm từ 27,81 xuống 16,09; sai số lớn nhất giảm từ 282,82 xuống 59,18 m."

**Điểm trung thực nên chủ động nói:** ở sai số rất nhỏ (dưới khoảng 2 m), đường V1 lại **cao hơn** V2. P25 của V1 là 1,48 m, của V2 là 1,70 m. Lý do: k = 1 trả về đúng một vị trí huấn luyện, nên đôi khi trúng gần chính xác; còn V2 lấy trung bình 12 láng giềng.

**Bootstrap:**
> "Em lấy mẫu lại 10.000 lần, khoảng tin cậy 95%. Trung bình V2 là 5,36 m (5,02–5,71). Trung bình V1 là 9,28 m (8,01–10,72). Mức giảm tính theo cặp — cùng một fingerprint ở hai phiên bản — là 3,92 m (2,74–5,30). Khoảng này không chứa 0, nên mức cải thiện không phải do may rủi. V2 sai ít hơn V1 trên 60,4% số fingerprint, nghĩa là vẫn còn khoảng 40% fingerprint mà V2 không tốt hơn."

**Câu chuyện (mục 3.13):** bootstrap — Efron, Annals of Statistics 1979.

---

### Slide 30 — Version 2 trên các tập WAP của HUIM (1 phút 30)

**minUtil (in trên nhãn trục):** HUIM union C · 91 WAP · **1,7321%**; HUIM union A · 86 WAP · **1,9294%**; HUIM union B · 79 WAP · **2%**.

**Trên màn hình:** biểu đồ "quả tạ" (dumbbell): chấm xám = V1 (k-NN, k = 1), chấm đen = V2; đoạn nối = mức cải thiện; dải xanh 7–8 m.

**Cách trình bày:**
1. "Mỗi hàng là một tập WAP. Từ trên xuống: 520 WAP, 465 WAP từng phát hiện, các top-200, các top-91, rồi ba tập HUIM."
2. "Mọi chấm đen đều nằm bên trái chấm xám: V2 giảm sai số với **mọi** tập WAP."
3. "Nhưng các tập HUIM vẫn trên 17 m, xa dải 7–8 m."
4. So sánh cùng 91 WAP: "HUIM union C đi từ 19,14 xuống 17,49 m; top-91 theo MI đi từ 18,54 xuống 14,73 m."

**Lời thoại kết:**
> "Kết luận về HUIM của Version 1 không đổi: đối chứng đơn giản vẫn chọn WAP tốt hơn. Cải thiện của V2 đến từ bộ ước lượng toạ độ, không đến từ HUIM."

---

### Slide 31 — So sánh V1 và V2: số liệu (1 phút)

**minUtil:** dòng cuối "HUIM union C (91 WAP)" ở **1,7321%**; các dòng còn lại dùng 520 WAP.

**Cách trình bày bảng:** không đọc hết. Chọn 4 dòng: trung bình (−3,92 m), P95 (−11,72 m), tỉ lệ ≤ 8 m (+10,98 điểm %), joint (+6,93 điểm %). Ô xanh = tốt hơn.

**Kiểm tay:**
- 99,91 − 98,74 = 1,17 pp ✓
- 94,69 − 87,76 = 6,93 pp ✓
- 27,81 − 16,09 = 11,72 m ✓
- 80,47 − 69,49 = 10,98 pp ✓
- 12,11 − 6,99 = 5,12 m (m toạ độ chiếu) ✓

---

### Slide 32 — So sánh phương pháp và trình bày (45 giây)

**Cách trình bày bảng:** chỉ đọc 3 dòng: "Bộ ước lượng toạ độ", "Cách chọn tham số" (75/25 ngẫu nhiên, tiêu chí độ chính xác phân loại → GroupKFold(6) theo USERID, tiêu chí sai số mét), "Phần HUIM: như nhau, không chạy lại".

---

### Slide 33 — Đính chính nội dung slide Version 1 (1 phút)

**Cách trình bày:** chủ động nhận lỗi; đọc nhanh 3 lỗi quan trọng nhất:
1. Model B: MI là **external utility p(i)**, không phải internal.
2. Thứ tự mục trong EFIM là TWU **tăng dần**.
3. Câu "HUIM nâng cao độ chính xác của IPS" là sai so với thực nghiệm, nên chuyển thành **câu hỏi nghiên cứu**.

**Lời thoại:**
> "Em liệt kê 8 chỗ sai của bản Version 1 để thầy/cô đối chiếu. Số slide trong bảng là số slide của bản Version 1, 22 trang."

---

### Slide 34 — Kiểm chứng độc lập (1 phút)

**Trên màn hình:** 3 thẻ: HUIM 28/28 phép đạt (`python src/verify_huim.py`); Định vị 24/24 (`python src/verify_positioning.py --brute 25`); Excel 206 ô KHỚP (`verification/kiem_chung_thu_cong.xlsx`).

**Lời thoại:**
> "Ba lớp kiểm tra này không dựa vào mã thí nghiệm. Kiểm HUIM tính lại q, p, u(X) từ CSV gốc và vét cạn mọi tổ hợp 1–3 WAP. Kiểm định vị chỉ dùng thư viện chuẩn của Python. File Excel có công thức tính lại minUtil, utility của HUI và mọi dự đoán của cả hai phiên bản. Nếu thầy/cô muốn, em có thể chạy ngay tại đây."

**Chuẩn bị:** mở sẵn terminal ở thư mục dự án, và mở sẵn file Excel.

---

### Slide 35 — Kết luận (2 phút)

**minUtil cho các số ở RQ2:** 64,99% / 66,79% / 71,56% là HUIM union **A 1,9294% / B 2% / C 1,7321%**. Các số 71,38% / 70,21% / 74,44% là top-n theo MI **cùng số WAP** (86 / 79 / 91).

**Lời thoại:**
> "RQ1: mô hình hoá được — 19.937 fingerprint thành 19.861 giao dịch, EFIM chạy 37 cấu hình và khớp oracle vét cạn. Em nhấn mạnh: chữ 'hợp lý' ở đây là hợp lý **của định nghĩa utility**, không phải một tính chất của dữ liệu.
> RQ2: HUIM chưa thắng đối chứng; trần tối đa của HUIM là 91 WAP.
> RQ3: khi hạ minUtil, số HUI và bộ nhớ khai phá tăng vọt nhưng số WAP gần như đứng yên; thời gian và bộ nhớ định vị giảm gần tuyến tính theo số WAP.
> RQ4: Version 2 giảm sai số từ 9,28 xuống 5,36 m mà không dùng tập kiểm định để chọn.
> Model B chọn tập WAP khác Model A — Jaccard 0,528 — nhưng MI lại gần trùng tần suất phát hiện. Đóng góp đúng mức của bài: một khảo sát khả năng thích nghi HUIM cho bài toán chọn nhóm AP, có đối chứng, báo cáo cả kết quả âm, không tuyên bố tính mới."

**Kiểm tay Jaccard:** A có 86 WAP (1,9294%), B có 79 WAP (2%), giao 57 WAP → hợp = 86 + 79 − 57 = 108 → 57 / 108 = **0,528** ✓

---

### Slide 36 — Kết luận và hướng tiếp theo (1 phút)

**Lời thoại:**
> "Tóm lại: HUIM mô hình hoá được vân tay Wi-Fi thành dữ liệu giao dịch, nhưng nhóm AP do HUIM chọn chưa tốt hơn tiêu chí đơn giản. Sai số giảm từ 9,28 xuống 5,36 m là nhờ bộ ước lượng toạ độ. Hướng tiếp theo có ba ý: một utility ngoài **độc lập với tần suất phát hiện**; dùng top-k hoặc closed HUIM để lấy nhiều WAP hơn với cùng ngân sách; và thêm một tập kiểm tra chưa từng dùng."

---

### Slide 37–38 — Tài liệu tham khảo (15 giây)

> "Dấu † là tài liệu đã kiểm DOI qua Crossref trong danh mục của dự án; dấu ‡ là kiểm DOI qua Crossref ngày 13/10/2026."

---

## 2. Phần mở rộng — Báo cáo đa dữ liệu (docx)

**Cách chiếu:** báo cáo là file Word. Có hai cách:
- Chiếu thẳng các Hình / Bảng trong docx.
- Chiếu deck có sẵn `slides/HUIM_IPS_Da_Dataset.pptx` (24 slide, cùng phong cách V2). Cột "Slide deck" bên dưới ghi slide tương ứng theo tiêu đề.

| Mục kịch bản | Nội dung báo cáo | Slide deck đa dữ liệu (theo tiêu đề) |
|---|---|---|
| 2.1 | Mục 1: mục tiêu, 4 câu hỏi | 2 "Mục tiêu và câu hỏi" |
| 2.2 | Bảng 1, Bảng 2 | 4 "5 bộ dữ liệu rất khác nhau", 5 "Đưa mọi bộ về một lược đồ chung" |
| 2.3 | Hình 1, Bảng 3 (DLULIB) | 6 "DLULIB: 17 AP dùng chung ba tầng" |
| 2.4 | Bảng 4 (rò rỉ HUS) | 7 "HUS: tập test chép từ tập train" |
| 2.5 | Bảng 5, Bảng 6 | 9 "Công thức áp lên một vân tay thật", 10 "Ba mô hình p(i) trên từng bộ" |
| 2.6 | Hình 2, Bảng 8 | 11 "Khai phá HUIM: vùng chuyển pha lặp lại" |
| 2.7 | Bảng 9, Hình 3, Bảng 10 | 14, 15, 16 |
| 2.8 | Hình 4, Bảng 11 | 17 "Phân bố sai số từng tập kiểm tra" |
| 2.9 | Hình 5, Bảng 12, Hình 6, Bảng 13 | 18 "HUIM có hơn đối chứng?", 19 "Cần giữ bao nhiêu AP?" |
| 2.10 | Bảng 14, Mục 5–6 | 20, 21, 23 |

### 2.1. Mở đầu phần mở rộng (45 giây)

**Lời thoại:**
> "Một kết quả chỉ đo trên một bộ dữ liệu luôn có nguy cơ khớp với đặc thù của bộ đó. Vì vậy em chạy **cùng một chương trình** trên mọi bộ dữ liệu trong thư mục được cung cấp, với nguyên tắc **chỉ đổi dữ liệu, không đổi phương pháp**. Cùng chuẩn hoá RSSI, ba mô hình utility, EFIM với cùng lưới minUtil và ngân sách, cùng quy tắc chọn AP, cùng lưới k-NN, cùng các bước S0–S4. Em trả lời 4 câu hỏi: chạy được không; mỗi bộ đạt độ chính xác tòa nhà, tầng, sai số mét, thời gian bao nhiêu; quy trình tối ưu và cấu hình 5,36 m có dùng lại được không; và HUIM có chọn AP tốt hơn đối chứng không."

### 2.2. Bảng 1 và Bảng 2 — các bộ dữ liệu và quyết định riêng (1 phút)

**minUtil:** không.

**Cách trình bày Bảng 1:** đọc cột "AP (phát hiện ở train)" để thấy quy mô rất khác nhau: UJIIndoorLoc 520 (465); UJI_LIB tầng 3 620 (306); DLULIB 17; HCXY 347 (345); HUS 5. Rồi đọc cột "Tập kiểm tra" để thấy **độ khó** khác nhau: Test-02 của UJI_LIB và test_HCXY có **0 vị trí trùng train** (khó); DLULIB và HUS kiểm tra lại đúng các vị trí đã đo.

**Lời thoại:**
> "Ba thư mục UJI_LIB_DB_Floor_5, syl và tuji rỗng, kể cả trong file zip gốc. Tên file zip có đuôi -1-001 nên nhiều khả năng đây là phần đầu của một bản xuất nhiều phần từ Google Drive."

**Cách trình bày Bảng 2:** nhấn cột "Nhãn vị trí".
> "Model B và C đo mức một AP 'cho biết' về vị trí bằng I(A;Y). Nếu bộ dữ liệu chỉ có một tầng thì Y không đổi, I(A;Y) = 0 với mọi AP, và Model B không xác định được. Khi đó em dùng lớp vị trí mịn nhất có sẵn, là **điểm tham chiếu RP**."

Cột "Fold kiểm định": UJIIndoorLoc theo USERID, UJI_LIB theo tháng, DLULIB theo SampleTimes, HCXY theo RP, HUS KFold ngẫu nhiên. Nguyên tắc chung: fold phải "giống" tập kiểm tra nhất có thể.

### 2.3. Hình 1 và Bảng 3 — DLULIB: 17 AP dùng chung ba tầng (1 phút)

**minUtil:** không.

**Trên hình:** bản đồ nhiệt; hàng = AP1…AP17, cột = tầng 1, 2, 3; số trong ô = % vân tay huấn luyện của tầng đó phát hiện AP.

**Cách trình bày:** đọc hàng AP1: tầng 1 thấy 89,3%, tầng 2 64,5%, tầng 3 36,8%. RSSI trung bình −62,8 → −73,5 → −83,7 dBm.
> "Mỗi AP có một tầng nơi nó mạnh nhất và yếu dần ở các tầng khác, đúng như một AP cố định phát sóng qua sàn bê tông. Điều đó chứng tỏ cột AP_k ở ba file là **cùng một AP vật lý**, nên em được phép ghép ba tầng thành một bài toán định vị tầng thật sự. Tầng 1 mạnh nhất ở AP1–AP7, tầng 2 ở AP8–AP13, tầng 3 ở AP14–AP17."

### 2.4. Bảng 4 — kiểm tra rò rỉ (1 phút) ⭐ điểm ăn tiền

**Cách trình bày:** đọc cột "Dòng test trùng hệt 1 dòng train". Mọi bộ đều 0, trừ HUS nguyên bản: testcase1 **204/205**, testcase2 **205/205**.

**Lời thoại:**
> "Trước khi tin một con số, em kiểm tra tập kiểm tra có thật sự là dữ liệu mới không. Với HUS, gần như mọi dòng kiểm tra xuất hiện nguyên vẹn trong tập huấn luyện. Nếu đánh giá như vậy, k-NN chỉ cần tìm lại chính bản sao: đó là học thuộc, không phải định vị. Em giữ bản gốc để minh hoạ hiệu ứng này, nhưng mọi kết luận dùng bản 'bỏ dòng chép': với mỗi dòng kiểm tra, loại đúng một bản sao của nó khỏi tập huấn luyện. Em đã loại 409 dòng; tập huấn luyện còn 20.091 dòng. Cùng một mô hình, HUS testcase1 cho 0,07 m khi còn bản sao và 0,39 m khi đã bỏ."

**Kiểm tay:** 20.500 − 409 = 20.091 ✓; 204 + 205 = 409 ✓.

**Lưu ý:** sau khi bỏ bản sao, HUS vẫn còn 48,3% và 67,8% dòng test trùng hệt một dòng train. Đó là trùng tự nhiên: 5 AP, lưới 0,5 m, 100 mẫu mỗi RP, và ngay trong train đã có 58,6% dòng có bản sao.

### 2.5. Bảng 5 và Bảng 6 — công thức trên một vân tay thật và tham số từng bộ (1 phút 30)

**Bảng 5 — tính tay trước mặt giảng viên** (dòng 2 của Training_DLULIB_Floor1_All_20.xlsx; RSSI_min = −99, RSSI_max = −27):
- AP1: q = 1 + (−78 − (−99)) / (−27 − (−99)) × 99 = 1 + 21/72 × 99 = 29,875 → **30**; u (Model B) = 30 × 0,6111 = **18,33** ✓
- TU Model A = tổng các q = 30 + 44 + 56 + 55 + 23 + 48 + 40 + 23 + 38 + 42 + 23 = **422** ✓

**Bảng 6 — kiểm tay H(Y) (đẹp để trình bày):** nếu các lớp chia đều thì H(Y) = log₂(số lớp).
- UJI_LIB: 24 RP → log₂24 = **4,585** ✓ (đúng bằng, vì mỗi RP có số mẫu bằng nhau)
- HCXY: 379 RP → log₂379 = **8,566** ✓
- HUS: 205 RP → log₂205 = **7,679** ✓
- DLULIB: 3 tầng → log₂3 = 1,585, thực tế **1,512**, tức ba tầng không đều số mẫu.

**Điểm lạ phải giải thích trước khi bị hỏi:** tổng utility Model C của HUS chỉ bằng **6**.
> "Ở HUS, cả 5 AP xuất hiện ở mọi vân tay, nên support = N và log(N / (1 + N)) < 0. Mã nguồn cắt về 0, nên mọi p(i) rơi xuống sàn 10⁻⁶. Tổng utility là 20.091 dòng × tổng q của 5 AP × 10⁻⁶ ≈ 6. Nói cách khác, **Model C suy biến** trên HUS: nó chỉ còn là Model A nhân một hằng số. Vì minUtil tính theo %, tập HUI của C trùng với A — đúng như Phụ lục A: số HUI của A và C giống nhau ở mọi ngưỡng."

### 2.6. Hình 2 và Bảng 8 — khai phá HUIM trên từng bộ (1 phút 30)

**minUtil:** trục X là θ (% tổng utility), **giảm dần sang phải**, thang log. Lưới chung 20% → 1%, cộng các ngưỡng tinh chỉnh. Dấu **x** = lần chạy dừng vì chạm ngân sách. Các điểm nằm sát đáy là 0 HUI (trục log không vẽ được số 0).

**Cách trình bày:** đi qua 5 ô nhỏ.
1. **UJIIndoorLoc:** giống hệt slide 17. Không có HUI ở ngưỡng cao, rồi bùng nổ quanh 2–5%.
2. **UJI_LIB:** bùng nổ sớm hơn; ở 1,5% đã có 568.656–979.199 HUI.
3. **DLULIB:** chỉ 17 AP, nên không bao giờ chạm ngân sách. Ở 1% có 32.680–40.568 HUI và cả 17/17 AP đều nằm trong HUI.
4. **HCXY:** mỗi vân tay thấy 36,4 AP, nên bùng nổ ở θ **cao hơn hẳn** (5–7,5%).
5. **HUS:** trục Y chỉ từ 24 đến 31.

**Kiểm tay cho HUS (rất hay):**
> "HUS có 5 AP nên chỉ có 2⁵ − 1 = **31** tập con khác rỗng. Ở Model A, từ θ = 15% trở xuống, số HUI là 31, tức **mọi tập con đều là HUI**. HUIM không còn chọn lọc gì nữa."

**Bảng 8 — θ chính của từng bộ** (lần chạy hoàn tất có θ thấp nhất):

| Bộ | A | B | C |
|---|---|---|---|
| UJIIndoorLoc | 1,9294% | 2% | 1,7321% |
| UJI_LIB tầng 3 | 1,5% | 1,5% | 1,5% |
| DLULIB | 1% | 1% | 1% |
| HCXY | 6,1237% | 6,777% | 7,5% |
| HUS (bỏ dòng chép) | 0,125% | 0,125% | 0,125% |

**Kiểm tay các ngưỡng lẻ của HCXY:** 7,5% hoàn tất, 5% bị dừng → √(7,5 × 5) = **6,1237** (A hoàn tất với 107.793 HUI ≥ 20.000 nên dừng tinh chỉnh). Với B: 6,1237% bị dừng → √(7,5 × 6,1237) = **6,777** (hoàn tất). HUS không bao giờ bị dừng và có ít hơn 20.000 HUI, nên hạ tiếp θ/2: 1 → 0,5 → 0,25 → **0,125**.

### 2.7. Bảng 9, Hình 3, Bảng 10 — kết quả chính (2 phút)

**minUtil:** không — dùng **mọi AP**.

**Hình 3 — cách trình bày (3 panel):**
- **Trái — sai số trung bình (m):** mỗi tập test có 3 thanh. Xám = k-NN của nghiên cứu (S0); cam = cấu hình UJI 5,36 m áp nguyên xi; xanh = tối ưu lại trên chính bộ đó.
- **Giữa — tỉ lệ đoán sai tầng** = 100 − độ chính xác tầng. Chỉ có ở UJIIndoorLoc (12,06 → 5,31) và DLULIB (0,78 → 0,52). Các bộ một tầng ghi "không áp dụng".
- **Phải — thời gian (ms/vân tay, thang log):** chỉ đo trên tập test chính.

**Lời thoại:**
> "Mô hình tối ưu lại có sai số thấp hơn k-NN của nghiên cứu ở **6/7** tập kiểm tra. Ngoại lệ duy nhất là UJI_LIB Test-02: 2,03 m so với 1,94 m. Cấu hình UJI áp nguyên xi bằng hoặc tốt hơn mô hình tối ưu lại ở 2/7 tập: trên chính UJIIndoorLoc thì hai mô hình là một, và ở UJI_LIB Test-02 là 1,91 m. Nghĩa là thứ tổng quát hoá được là **quy trình chọn**, còn bộ siêu tham số thì phụ thuộc bộ dữ liệu."

**7 tập kiểm tra** gồm: UJI validationData, UJI_LIB Test-01, UJI_LIB Test-02, DLULIB Testing, test_HCXY, HUS (bỏ dòng chép) testcase1, testcase2. "HUS nguyên bản" chỉ để minh hoạ, không tính.

**Bảng 10 — kiểm tra tái lập:**
> "Chạy lại UJIIndoorLoc qua đường code chung, quy trình chọn đúng cấu hình 'exponential + Bray–Curtis, k = 12, w = 1/d⁴, dò lệch ±6 dB, ensemble' và cho 5,3558 m, joint 94,69%, trùng nghiên cứu gốc. 190/190 điều kiện của PHASE I cũng cho cùng kết quả."

**Bảng 10 — mỗi bộ chọn một mô hình khác:** UJI_LIB chọn k = 3; DLULIB chọn powed + Bray–Curtis, k = 7; HCXY chọn k = 30, w = 1/d³; HUS chọn powed + Manhattan, k = 4. Bray–Curtis thắng ở 4/5 bộ, trừ HUS.

**Câu hỏi có thể gặp:** "Sao thời gian ở đây (4,969 ms) khác slide 22 (1,207 ms)?"
> "Hai cách đo khác nhau. Slide 22 đo trên một lõi CPU, chỉ phần dự đoán. Báo cáo đa dữ liệu đo bằng đồng hồ thực, gồm cả dựng chỉ mục láng giềng, dùng mọi lõi, chạy khởi động một lần rồi lấy trung vị của 3 lần, trên tối đa 1.111 vân tay. Chỉ nên so sánh trong cùng một bảng."

**Cái giá của V2:** trên UJIIndoorLoc, mô hình tối ưu mất 30,791 ms, so với 4,969 ms của k-NN gốc, tức chậm hơn khoảng 6,2 lần. Lý do là phải thử nhiều mức δ và chạy hai biểu diễn.

### 2.8. Hình 4 và Bảng 11 — phân bố sai số (45 giây)

**minUtil:** không.

**Cách trình bày:** "Đường càng dịch sang trái càng tốt." Đọc mẫu dòng DLULIB: tỉ lệ ≤ 2 m tăng từ 28,8% lên 40,1%; ≤ 5 m tăng từ 70,8% lên 78,6%. Rồi chỉ HCXY: P90 giảm từ 5,01 xuống 3,12 m.

### 2.9. Hình 5, Bảng 12, Hình 6, Bảng 13 — HUIM có chọn AP tốt hơn? (2 phút)

**Hình 5 — minUtil in ngay trên nhãn từng hàng:**

| Bộ | A | B | C |
|---|---|---|---|
| UJIIndoorLoc | 86 WAP, 1,9294% | 79 WAP, 2% | 91 WAP, 1,7321% |
| UJI_LIB tầng 3 | 83 WAP, 1% | 87 WAP, 1% | 79 WAP, 1% |
| DLULIB | 17 WAP, 1% | 17 WAP, 1% | 17 WAP, 1% |
| HCXY | 67 WAP, 6,1237% | 73 WAP, 6,1237% | 82 WAP, 5% |
| HUS | 5 WAP, 20% | 5 WAP, 20% | 5 WAP, 20% |

> **Chú ý:** union UJI_LIB 1%, HCXY B 6,1237% và HCXY C 5% lấy từ lần chạy **bị dừng**. Union chỉ cần biết WAP nào xuất hiện nên vẫn dùng được; chỉ top-n mới bắt buộc lần chạy hoàn tất.

**Cách trình bày Hình 5:** chấm xanh = HUIM; vuông cam = top-n MI; thoi xanh lá = top-n phát hiện; vạch đen = mọi WAP. Mỗi hàng so ở **cùng số AP**.
1. Ba hàng UJIIndoorLoc: mọi điểm nằm ở 14,7–19,9 m, rất xa vạch đen 5,36 m. HUIM C (17,49) thua MI (14,73).
2. DLULIB và HUS: các điểm chồng lên nhau, vì HUIM lấy **toàn bộ** AP (17/17, 5/5), nên không còn gì để so.

**Lời thoại (Bảng 12):**
> "Trên 42 tập AP do HUIM chọn — 7 tập test × 3 mô hình × 2 quy tắc — chỉ 3 tập có sai số thấp hơn cả hai đối chứng. Em xin nói rõ ba lần 'thắng' này: cả ba đều ở UJI_LIB, và chênh lệch chỉ **0,0002 m, 0,0034 m và 0,0048 m**, tức dưới nửa centimet. Thực chất là hoà. Kết luận của nghiên cứu gốc đứng vững trên dữ liệu mới: HUIM tìm ra các nhóm AP 'mạnh và hay xuất hiện cùng nhau', nhưng điều đó không làm chúng thành đặc trưng định vị tốt hơn."

**Chi tiết ba lần "thắng" (từ `results/multi_dataset/huim_vs_controls.csv`):**

| Tập | HUIM | Top-MI | Top-phát hiện |
|---|---|---|---|
| UJI_LIB Test-01, B union 1%, 87 AP | 1,1931 | 1,1933 | 1,2182 |
| UJI_LIB Test-02, A union 1%, 83 AP | 2,0378 | 2,0446 | 2,0412 |
| UJI_LIB Test-02, B top-n 1,5%, 75 AP | 2,0486 | 2,0690 | 2,0534 |

**Thất bại nặng nên nêu:** HCXY C top-20 (θ = 7,5%) cho **30,56 m**, trong khi top-MI 20 AP chỉ 3,50 m; UJIIndoorLoc A top-75 (θ = 1,9294%) cho 32,59 m.

**Lưu ý trung thực:** với mỗi mô hình, tập union / top-n được báo cáo là tập có kết quả tốt nhất trên **tập test chính** khi dùng k-NN gốc (`run_multi_dataset.py`). Cách chọn này ưu ái HUIM, nhưng HUIM vẫn không thắng. Nếu giảng viên hỏi thì nói đúng như vậy.

**Hình 6 — minUtil:** đường xanh là **HUIM Model B top-n** ở θ chính của từng bộ: UJIIndoorLoc **2%**, UJI_LIB **1,5%**, DLULIB **1%**, HCXY **6,777%**, HUS **0,125%**.

**Cách trình bày Hình 6:** trục X = số WAP giữ lại (thang log ở UJI, UJI_LIB, HCXY); trục Y = sai số TB (m); đường chấm = dùng mọi AP.
- **UJIIndoorLoc:** mọi đường còn ở 16–30 m tại 50–75 WAP, rất xa 5,36 m.
- **UJI_LIB và HCXY:** đường xám (ngẫu nhiên) cao hẳn; ba đường còn lại sát nhau.
- **HUS:** **không thấy đường xanh**, vì nó trùng hoàn toàn với đường cam top-MI (Bảng 16: 2,42 / 2,06 / 1,41 / 0,59 / 0,39 ở cả hai cột).
- **HCXY:** chỉ thử đến 50 AP. Ở 5 AP, HUIM B sai 31,91 m, top-MI 24,41 m; từ 10 AP trở lên các đường gần nhau (HUIM B 5,74 m, top-MI 5,07 m).

**Bảng 13 — cách đọc** (số AP nhỏ nhất mà sai số ≤ 1,1 × sai số dùng mọi AP):
- UJI_LIB: ngưỡng 1,1 × 1,21 = 1,331 m. HUIM B 75 AP = 1,25 ✓ đạt (ở 50 AP = 1,48 ✗); top-MI đạt ngay từ 50 AP (1,30).
- DLULIB: ngưỡng 1,1 × 3,43 = 3,773 m. HUIM A/B/C và top-phát hiện đạt ở **13 AP** (3,68), còn top-MI và ngẫu nhiên cần 14 AP. Đây là **trường hợp duy nhất** HUIM nhỉnh hơn top-MI một AP; nên nói ra cho công bằng.
- UJIIndoorLoc và HCXY: không phương pháp nào đạt với số AP đã thử.

### 2.10. Bảng 14, Thảo luận, Kết luận (1 phút 30)

**Bảng 14 — minUtil ghi trong cột "Tập AP".** Chú ý dòng HCXY union B θ = 6,1237%: thời gian EFIM 603,71 s, vì đó là lần chạy bị dừng.

**Lời thoại thảo luận:**
> "Bỏ AP làm bộ nhớ cơ sở dữ liệu vân tay giảm tỉ lệ thuận với số AP, nhưng thời gian giảm ít hơn, vì chi phí còn nằm ở số vân tay huấn luyện. Thời gian khai phá EFIM chỉ phải trả một lần khi xây dựng hệ thống.
> Trong cùng một bộ, vị trí kiểm tra đã khảo sát hay chưa quyết định độ khó. UJI_LIB Test-01 (đo lại vị trí cũ) có sai số 1,21 m, Test-02 (vị trí mới) 2,03 m. Lý do: k-NN ước lượng vị trí bằng trung bình các vị trí đã khảo sát, nên sai số bị chặn dưới bởi mật độ lưới khảo sát.
> Riêng UJI_LIB Test-02 là chỗ mô hình tối ưu lại kém hơn k-NN gốc. Lý do: fold nhóm theo tháng mô phỏng Test-01 (vị trí cũ, thời điểm khác) chứ không mô phỏng vị trí chưa khảo sát. Em giữ nguyên kết quả, không chọn lại theo tập kiểm tra.
> UJIIndoorLoc vẫn là bộ khó nhất về sai số mét: tập kiểm định do người khác đo, bằng điện thoại khác, sau bốn tháng, ở vị trí không có trong tập huấn luyện."

**Lời thoại kết luận phần mở rộng (4 ý):**
> "Một: phương pháp chạy được trên 5 bộ dữ liệu khác nhau — từ 5 đến 620 AP, từ 1 đến 13 tổ hợp tòa–tầng — mà không phải sửa thuật toán. Hai: quy trình tối ưu giảm sai số ở 6/7 tập kiểm tra. Cái tổng quát hoá được là quy trình chọn, không phải bộ siêu tham số. Ba: HUIM không vượt đối chứng đơn giản; kết luận gốc được lặp lại. Bốn: **kiểm tra dữ liệu là một phần của phương pháp**. Phát hiện tập kiểm tra HUS bị chép từ tập huấn luyện đã đổi hẳn cách đọc kết quả của bộ này."

**Phụ lục C — tự kiểm chứng:** file `verification/kiem_chung_da_dataset.xlsx` có 547 phép kiểm tra KHỚP, 0 phép LỆCH.

---

## 3. Câu chuyện nguồn gốc các công thức (có nguồn)

**Ký hiệu mức kiểm chứng:**
- ✅ đã đọc trực tiếp trong văn bản bài báo (PDF).
- ☑️ kiểm qua tóm tắt bài báo hoặc nguồn thứ cấp uy tín.
- ⚠️ giai thoại — **không kể như sự thật**.

Số trong ngoặc vuông là số tài liệu trên slide 37–38.

### 3.1. Support và khai phá luật kết hợp — Agrawal, Imieliński & Swami, SIGMOD 1993 [1] ☑️

- Ba tác giả làm ở IBM Almaden Research Center.
- Bài toán xuất phát từ dữ liệu giỏ hàng: một cơ sở dữ liệu lớn các giao dịch của khách, mỗi giao dịch là các món mua trong một lần đến cửa hàng.
- Tác giả thử nghiệm thuật toán trên dữ liệu bán hàng của một nhà bán lẻ lớn.
- **Câu dùng được:** "Support ra đời để trả lời câu hỏi: những món nào hay được mua cùng nhau?"
- ⚠️ **Đừng kể** chuyện "bia và tã lót" như kết quả của bài báo này. Đó là giai thoại lan truyền, không có trong [1].

### 3.2. Utility của tập mục — Yao, Hamilton & Butz, SIAM SDM 2004 [2] ☑️

- Bài đặt nền móng cho khai phá utility: utility của một mục trong giao dịch tính từ **lượng** (giá trị nội, ví dụ số lượng mua) và **giá trị đơn vị** (giá trị ngoài, ví dụ lợi nhuận mỗi đơn vị).
- Bài Two-Phase [4] (✅ đọc trực tiếp) nhận xét: luật kết hợp truyền thống là trường hợp riêng của utility mining khi utility mỗi mục luôn bằng 1 và lượng bán chỉ là 0 hoặc 1.
- [4] gọi cách dự đoán ứng viên của [2] là **MEU** (Mining using Expected Utility) và chỉ ra hai nhược điểm: ước lượng thường quá cao, khiến số ứng viên gần bằng mọi tổ hợp; và có thể **bỏ sót** tập hữu ích cao khi độ hỗ trợ của các tập dao động mạnh.

### 3.3. TWU — Liu, Liao & Choudhary, PAKDD 2005 [4] ✅

- Ba tác giả ở Đại học Northwestern (Evanston, Mỹ).
- **Câu chuyện:** bài toán utility không có tính chất đóng hướng xuống (downward closure), nên không cắt tỉa kiểu Apriori được. Lời giải của họ là tìm một đại lượng **ước lượng dư** nhưng **có** tính chất đó: *transaction-weighted utilization* (TWU), kèm định lý *Transaction-weighted Downward Closure Property*.
- Thuật toán có hai pha. Pha I tìm theo từng mức như Apriori bằng TWU; nó có thể đánh giá quá cao vài tập nhưng **không bao giờ đánh giá thấp**. Pha II chỉ quét thêm **một lần** cơ sở dữ liệu để lọc ra tập hữu ích cao thật.
- **Câu dùng được:** "Không chặn được u(X) thì đi chặn một thứ lớn hơn u(X) mà lại đơn điệu — đó là ý tưởng của TWU, và đến EFIM vẫn dùng."

### 3.4. EFIM, lu và su — Zida, Fournier-Viger, Lin, Wu & Tseng [5] ☑️

- EFIM được trình bày lần đầu ở hội nghị MICAI 2015 (Mexico), rồi mở rộng thành bài trên tạp chí *Knowledge and Information Systems* 2017.
- Tóm tắt bài báo tạp chí nêu hai cận trên mới (*revised sub-tree utility* và *local utility*), và kỹ thuật *Fast Utility Counting* tính chúng trong thời gian và bộ nhớ tuyến tính.
- Tác giả báo cáo EFIM nhanh hơn d2HUP, HUI-Miner, HUP-Miner, FHM, UP-Growth+ khoảng **hai đến ba bậc độ lớn** trên dữ liệu dày, và ưu điểm lớn là tốn ít bộ nhớ.
- Philippe Fournier-Viger cũng là người khởi xướng thư viện mã nguồn mở **SPMF** [12] (Java).
- **Câu dùng được:** "Con số nhanh hơn 100–1000 lần là do chính tác giả EFIM đo. Vì vậy em dựa thêm vào đánh giá độc lập của Zhang et al. 2018 [11] để chọn EFIM."

### 3.5. Entropy và thông tin tương hỗ — Shannon, Bell System Technical Journal 1948 [6] ☑️

- Ngay phần mở đầu bài 1948, Shannon viết rằng nếu dùng logarit cơ số 2 thì đơn vị đo thông tin có thể gọi là *binary digits*, hay ngắn gọn là ***bits*** — "một từ do J. W. Tukey gợi ý". Đơn vị "bit" ở slide 11 (H(Y) = 3,639 bit) có nguồn gốc từ câu đó.
- Trong bài, đại lượng mà ngày nay gọi là thông tin tương hỗ xuất hiện dưới dạng tốc độ truyền R = H(x) − H_y(x): lượng bất định về x được gỡ đi khi biết y. Đó đúng là ý nghĩa của I(A; Y) ở Model B: biết trạng thái AP thì gỡ được bao nhiêu bất định về tầng.
- ⚠️ Chuyện "von Neumann khuyên Shannon đặt tên là entropy" là giai thoại kể lại về sau, không có trong [6]. Không nên kể như sự thật.

### 3.6. Chọn AP bằng lý thuyết thông tin — Chen, Yang, Yin & Chai, IEEE TKDE 2006 [7] ✅

- Nhóm ở HKUST (Đại học Khoa học và Công nghệ Hồng Kông). Mục tiêu ban đầu **không phải độ chính xác mà là tiết kiệm pin**: câu hỏi của họ là có định vị được bằng ít năng lượng pin nhất không.
- Họ đề xuất thuật toán **CaDet** (Clustering and Decision-tree-based method), kết hợp lý thuyết thông tin, phân cụm và cây quyết định.
- Bài viết rằng lý thuyết thông tin cho phương pháp chọn đặc trưng tốt nhất để xác định các AP quan trọng nhất. Thực nghiệm làm trong mạng WLAN của khoa Khoa học Máy tính HKUST.
- **Câu dùng được:** "Model B của em mượn đúng tinh thần này — giá trị của một AP là lượng thông tin nó mang về vị trí — rồi đặt vào ô p(i) của HUIM. Cách ghép đó là của em."

### 3.7. IDF — Karen Spärck Jones, Journal of Documentation 1972 [8] ☑️

- Bà đề xuất diễn giải **tính đặc hiệu của từ khoá** theo thống kê, dựa trên cách từ đó được dùng trong cả bộ tài liệu chứ không dựa vào nghĩa của nó: từ xuất hiện trong ít tài liệu thì khi khớp được tính điểm cao hơn.
- Ý tưởng này về sau được biết với tên IDF và trở thành nền của TF-IDF trong máy tìm kiếm.
- **Câu dùng được:** "Một AP ở đâu cũng thấy giống như từ 'và', 'của' trong văn bản: có mặt khắp nơi nên không phân biệt được gì. Model C phạt nó bằng thừa số kiểu IDF."
- Lưu ý: dạng log(N / (1 + support)) trong Model C là một biến thể có làm trơn. Đừng nói "đúng y công thức gốc năm 1972".

### 3.8. Biểu diễn positive / exponential / powed — Torres-Sospedra et al., ESWA 2015 [9] ☑️

- Cùng nhóm ở Đại học Jaume I (Tây Ban Nha) đã công bố UJIIndoorLoc tại IPIN 2014. Theo tóm tắt, đó là cơ sở dữ liệu lớn nhất trong tài liệu khi ấy, và là cơ sở dữ liệu công khai đầu tiên thuộc loại này, đo bởi hơn 20 người với 25 thiết bị.
- Năm 2015, nhóm đánh giá **51 hàm khoảng cách** và **4 cách biểu diễn dữ liệu** (2 cách do chính nhóm đề xuất) trên UJIIndoorLoc.
- Kết luận chính: các phép đo khác Euclid làm tốt hơn Euclid trên dữ liệu thô, và việc chọn một biểu diễn phi tuyến phù hợp là quan trọng.
- **Câu dùng được:** "Trước bài này, phần lớn nghiên cứu mặc định dùng khoảng cách Euclid trên RSSI thô. Bài này cho thấy chọn khoảng cách và biểu diễn quan trọng không kém chọn thuật toán. S1 của em làm đúng việc đó."

### 3.9. Khoảng cách Bray–Curtis — Bray & Curtis, Ecological Monographs 1957 [17] ☑️

- J. Roger Bray và John T. Curtis là hai nhà sinh thái học thực vật ở Đại học Wisconsin. Họ cần **xếp các khu rừng vùng cao ở miền nam Wisconsin theo mức giống nhau về thành phần loài cây**. Từ đó ra phương pháp *polar ordination* (về sau gọi là Bray–Curtis ordination) cùng thước đo khoảng cách đi kèm.
- Thước đo này thường được viết ở dạng hệ số tương đồng 2W / (A + B): W là tổng các giá trị nhỏ hơn của mỗi loài giữa hai khu, A và B là tổng của mỗi khu. Khoảng cách Bray–Curtis = 1 − 2W / (A + B). Cách viết này lấy theo tài liệu tổng quan; em chưa đọc trực tiếp ký hiệu trong bài 1957.
- **Kiểm tay để chứng minh hai dạng là một** (dùng ví dụ slide 27, a = (3, 0, 5), b = (1, 2, 5)):
  - W = min(3,1) + min(0,2) + min(5,5) = 1 + 0 + 5 = 6
  - 1 − 2W / (A + B) = 1 − 12/16 = 0,25 = Σ|a − b| / Σ(a + b) ✓
- **Câu dùng được:** "Thước đo này sinh ra để so sánh hai khu rừng. Trong định vị Wi-Fi, mỗi AP là một 'loài cây', cường độ tín hiệu là 'số cây'. 58 năm sau, Torres-Sospedra mang nó sang vân tay Wi-Fi."

### 3.10. k-NN trong không gian tín hiệu — Bahl & Padmanabhan (Microsoft Research), RADAR, INFOCOM 2000 [18] ✅

- **Thí nghiệm:** tầng 2 của một tòa nhà 3 tầng, kích thước 43,5 m × 22,5 m (980 m²), hơn 50 phòng, **3 trạm gốc** WaveLAN 2,4 GHz. Điểm khác UJIIndoorLoc: trong RADAR, **trạm gốc** ghi cường độ tín hiệu của máy di động; còn ở UJIIndoorLoc, **điện thoại** quét các AP.
- Họ đặt tên kỹ thuật là **NNSS** (nearest neighbor(s) in signal space) và dùng khoảng cách Euclid. Bài có nhắc đã thử nhanh khoảng cách "Manhattan" nhưng không trình bày vì thiếu chỗ.
- **Kết quả:** sai số trung vị **2,94 m**, "dưới 3 m, cỡ một phòng làm việc trong tòa nhà". Phương pháp này tốt hơn 2,8 lần so với đoán theo trạm gốc mạnh nhất, và 5,5 lần so với đoán ngẫu nhiên.
- **Về k láng giềng:** với k = 5, trung vị còn **2,75 m** (tốt hơn 9%). Nhưng *k lớn thì độ chính xác giảm nhanh*, vì các điểm ở xa vị trí thật cũng bị đưa vào phép lấy trung bình.
- **Câu dùng được:** "Ngay từ năm 2000, RADAR đã thấy k lớn làm hỏng kết quả. V2 của em dùng k = 12 nhưng trọng số 1/d⁴, nên láng giềng xa gần như không được tính. Đó là cách dung hoà phát hiện của RADAR."
- Bài sau này nhận giải ACM SIGMOBILE Test of Time Paper Award (theo tin của Microsoft Research).

### 3.11. Trọng số nghịch đảo khoảng cách — Shepard, ACM National Conference 1968 [19] ☑️

- Donald Shepard phát triển phép nội suy này khi còn là sinh viên Harvard, cho chương trình vẽ bản đồ bằng máy tính **SYMAP** của Howard Fisher. Bài toán của ông là nội suy giá trị trên bản đồ từ các điểm đo nằm rải rác, không đều.
- Theo các tài liệu lịch sử về SYMAP, ông thử nhiều số mũ và chọn số mũ gần 2, giống mô hình trọng lực. Chi tiết này lấy từ nguồn thứ cấp, không đọc trực tiếp trong [19].
- **Câu dùng được:** "Bản đồ nội suy độ cao từ các điểm đo; định vị Wi-Fi nội suy toạ độ từ các láng giềng. Công thức giống nhau, chỉ khác số mũ: Shepard thường dùng khoảng 2, dev của em chọn p = 4."

### 3.12. Hệ số tỉ lệ Mercator sec φ — Snyder, USGS Professional Paper 1395, 1987 [13] ☑️

- *Map projections: A working manual* là cẩm nang phép chiếu bản đồ của Cục Địa chất Hoa Kỳ (USGS).
- Phép chiếu Mercator phóng đại khoảng cách theo hệ số sec φ: càng xa xích đạo càng phóng to. Đó là lý do Greenland trên bản đồ Mercator trông to gần bằng châu Phi.
- Ở campus UJI (φ ≈ 40°), hệ số là 1/0,766126 = 1,305: đọc thẳng toạ độ thì sai số bị phóng to khoảng 31%.

### 3.13. Bootstrap — Efron, Annals of Statistics 1979 [20] ☑️

- Tên bài là "Bootstrap Methods: **Another Look at the Jackknife**". Tóm tắt chỉ ra rằng jackknife là một phép **xấp xỉ tuyến tính** của bootstrap.
- Tên "bootstrap" gợi thành ngữ tiếng Anh "tự kéo quai giày mà đứng dậy": dùng chính mẫu dữ liệu để ước lượng độ bất định của nó, không cần thêm dữ liệu.
- **Câu dùng được:** "Em không có tập kiểm định thứ hai, nên em lấy mẫu lại có hoàn lại 1.111 fingerprint 10.000 lần để xem mức giảm 3,92 m dao động bao nhiêu."

### 3.14. Spearman 1904 [10] và Jaccard 1912 [21] ☑️

- **Charles Spearman**, nhà tâm lý học người Anh, đăng bài về đo mức liên hệ giữa hai đại lượng bằng **thứ hạng** trên *American Journal of Psychology* năm 1904. Em dùng nó vì chỉ cần thứ tự (hạng MI so với hạng tần suất), không cần quan hệ tuyến tính.
- **Paul Jaccard**, nhà thực vật học Thụy Sĩ, so sánh hệ thực vật giữa các vùng núi Alps bằng tỉ lệ "số loài chung / tổng số loài". Em dùng đúng tỉ lệ đó để so tập WAP của Model A và B: 57/108 = 0,528.

---

## 4. Chuẩn bị hỏi đáp

**H1. HUIM thua đối chứng, vậy làm đề tài này để làm gì?**
> "Bài là một khảo sát khả năng thích nghi có đối chứng. Kết quả âm cũng là kết quả: nó cho thấy định nghĩa utility hiện tại (Model B) gần như trùng tần suất phát hiện, với ρ = 0,9908. Vì vậy HUIM chỉ tìm lại các AP 'mạnh và hay xuất hiện cùng nhau'. Hướng sửa là một utility ngoài độc lập với tần suất. Và em đã lặp lại kết luận này trên 5 bộ dữ liệu."

**H2. Vì sao minUtil tính theo % chứ không theo số tuyệt đối?**
> "Vì tổng utility của ba mô hình chênh 2,08 lần. Cùng một số tuyệt đối thì với A là ngưỡng thấp, với B là ngưỡng cao, nên không so sánh được."

**H3. Sao lại ra ngưỡng lẻ 1,9294%?** → trả lời bằng phép trung bình nhân ở mục 0.2.

**H4. Sao S2 tốt hơn trên validationData mà em vẫn chọn S4?**
> "Vì chọn theo dev. Chọn lại theo số kiểm định là dùng tập kiểm tra để chọn mô hình. Chênh lệch 0,06 m cũng nằm gọn trong khoảng tin cậy bootstrap của V2 (5,02–5,71)."

**H5. Tập union có lấy từ lần chạy bị dừng không?**
> "Trên UJIIndoorLoc thì không: ba tập chính đều từ lần chạy hoàn tất. Trong báo cáo đa dữ liệu, union được phép lấy từ lần chạy bị dừng (ví dụ UJI_LIB 1%, HCXY 5%), vì union chỉ cần biết WAP nào có mặt. Top-n thì luôn dùng lần chạy hoàn tất, vì thứ tự xếp hạng bị lệch nếu DFS dừng giữa chừng."

**H6. Các tập HUIM đem so sánh được chọn thế nào — có ưu ái HUIM không?**
> "Có, và em nói rõ: mỗi mô hình lấy tập HUIM có kết quả tốt nhất trên tập đánh giá. Cách này nghiêng về phía HUIM, vậy mà HUIM vẫn không thắng top-MI. Nên kết luận 'HUIM không hơn' là kết luận thận trọng."

**H7. Dò lệch ±6 dB lấy từ đâu?**
> "Đây là thiết kế của em, slide ghi rõ chưa có nguồn. Nó chỉ dùng tín hiệu của chính truy vấn, không dùng vị trí hay nhãn, nên không rò rỉ. Phần này cần bổ sung tài liệu về hiệu chỉnh lệch thiết bị."

**H8. Mức 7–8 m lấy từ đâu?**
> "Đó là mốc mục tiêu đề tài đặt ra để so sánh, không phải chuẩn công bố."

**H9. validationData có người đo khác không? Sao không chia theo người đo cho validationData?**
> "validationData không ghi người đo (USERID = 0 ở mọi dòng). Nó có 11 mã điện thoại, trong đó 9 mã không có trong train. Nhưng validationData chỉ để đánh giá, không dùng để chọn, nên không cần chia fold."

**H10. Chạy lại có ra đúng số không?**
> "Ra đúng 5,3558 m nếu giữ cấu hình luồng CPU mặc định. Nhiều cặp vân tay có khoảng cách bằng nhau vì RSSI là số nguyên, và hai cấu hình ứng viên chỉ chênh vài phần vạn mét trên dev. Nếu giới hạn số luồng, thư viện cộng số theo thứ tự khác, sai ở chữ số rất nhỏ cũng đủ đổi thứ tự láng giềng và lật lựa chọn."

**H11. Sao kết quả HUS gần 0 m?**
> "Bản gốc có tập test chép từ tập train (204/205 và 205/205 dòng). Em dùng bản đã bỏ bản sao: 0,39 m và 0,25 m. Phần còn lại là do bộ HUS rất nhỏ: một phòng, 5 AP, lưới 0,5 m."

**H12. V2 chậm hơn V1 bao nhiêu?**
> "Trong phép đo của báo cáo đa dữ liệu, trên UJIIndoorLoc: 30,791 ms so với 4,969 ms mỗi vân tay, tức khoảng 6,2 lần, vì phải dò nhiều mức δ và chạy hai biểu diễn. Đó là cái giá của việc giảm 42% sai số."

**H13. Slide 25 ghi 1.074 vị trí, báo cáo ghi 1.053 — số nào đúng?**
> "1.053. Có 21 cặp toạ độ trong validationData chỉ lệch nhau tối đa 7,5 × 10⁻⁹ m, do nhiễu số thực. Đếm đúng từng bit thì ra 1.074; làm tròn toạ độ đến 6 chữ số thập phân thì ra 1.053. Slide V2 nên sửa thành 1.053."

**H14. Toạ độ HCXY là mét thật không?**
> "Thư mục không có tài liệu mô tả. Em coi là mét vì khoảng cách giữa hai RP liền kề là 0,59–1,2, đúng cỡ một lưới khảo sát. Đây là giới hạn đã ghi trong báo cáo."

---

## 5. Phiếu kiểm tay nhanh

| # | Con số trên slide / báo cáo | Phép tính |
|---|---|---|
| 1 | −42% (slide 2, 24) | (9,28 − 5,36) / 9,28 = 0,422 |
| 2 | q(WAP255) = 27 (slide 9) | 1 + 27/104 × 99 = 26,70 → 27 |
| 3 | TU Model A = 94 (slide 10) | 27 + 15 + 26 + 26 |
| 4 | 12,0% của H(Y) (slide 11) | 0,438 / 3,639 |
| 5 | Chênh 2,08 lần (slide 5, 11) | 9.058.242 / 4.354.299 |
| 6 | minUtil tuyệt đối B | 0,02 × 4.354.299 = 87.086 |
| 7 | 1,9294% | √(2 × √(2 × √(2 × 1,5))) = √(2 × 1,8612) |
| 8 | 127 tập khả dĩ (slide 14) | 2⁷ − 1 |
| 9 | 14,5× và 27,2× (slide 18) | 338,13 / 23,29; 338,13 / 12,44 |
| 10 | 82,5% giảm chiều (slide 21) | (1 − 91/520) × 100 |
| 11 | 79,1 MB (slide 22) | 19.937 × 520 × 8 / 1.048.576 |
| 12 | 5,4× nhanh hơn (slide 22) | 1,2066 / 0,2250 |
| 13 | 4,61 m thực địa (slide 23) | 6,02 × 0,766126 |
| 14 | Hệ số 1,305268 (slide 23) | 1 / 0,766126 |
| 15 | Quy tắc 0,05 m (slide 28) | 6,76 − 6,33 = 0,43; 6,33 − 6,21 = 0,12 |
| 16 | +6,93 pp joint (slide 31) | 94,69 − 87,76 |
| 17 | Jaccard 0,528 (slide 35) | 57 / (86 + 79 − 57) |
| 18 | q DLULIB AP1 = 30 (Bảng 5) | 1 + 21/72 × 99 = 29,875 |
| 19 | TU DLULIB Model A = 422 | tổng 11 giá trị q |
| 20 | H(Y) UJI_LIB = 4,585 (Bảng 6) | log₂ 24 |
| 21 | 31 HUI ở HUS (Hình 2) | 2⁵ − 1 |
| 22 | 409 dòng bị loại ở HUS | 204 + 205; 20.500 − 409 = 20.091 |
| 23 | 6,1237% ở HCXY | √(7,5 × 5) |
| 24 | Ngưỡng Bảng 13 ở DLULIB | 1,1 × 3,43 = 3,773 |

---

*Nguồn tra cứu đã dùng để kiểm câu chuyện ở mục 3:*
- [RADAR — bản PDF bài INFOCOM 2000](https://www.csd.uwo.ca/~hlutfiyy/Perv/Papers/Bahl2000_RADAR.pdf)
- [Two-Phase — bản PDF bài PAKDD 2005 (trang SPMF)](https://www.philippe-fournier-viger.com/spmf/two-phase-high-utility2005.pdf)
- [Chen et al. 2006 — bản PDF tại HKUST](https://cse.hkust.edu.hk/~qyang/Docs/2006/yiqiang.pdf)
- [Trang EFIM của SPMF](https://philippe-fournier-viger.com/spmf/EFIM.php)
- [Kho NYCU — bài EFIM KAIS 2017](https://ir.lib.nycu.edu.tw/handle/11536/145377?locale=en)
- [Wikipedia — A Mathematical Theory of Communication (chữ "bit" và J. W. Tukey)](https://en.wikipedia.org/wiki/A_Mathematical_Theory_of_Communication)
- [Wikipedia — Bray–Curtis dissimilarity](https://en.wikipedia.org/wiki/Bray%E2%80%93Curtis_dissimilarity)
- [Wikipedia — Inverse distance weighting (Shepard, SYMAP)](https://en.wikipedia.org/wiki/Inverse_distance_weighting)
- [Efron 1979 — bản PDF](https://sites.stat.washington.edu/courses/stat527/s13/readings/ann_stat1979.pdf)
- [Agrawal et al. 1993 — bản PDF](https://www.comp.hkbu.edu.hk/~markus/teaching/comp7650/Agrawal.pdf)
- [Spärck Jones 1972 — DOI](https://www.doi.org/10.1108/EB026526)
- [Torres-Sospedra et al. 2015 — kho UJI](https://repositori.uji.es/xmlui/handle/10234/158880)
- [Tin Microsoft Research về giải Test of Time của RADAR](https://www.microsoft.com/en-us/research/news-and-awards/?pg=188)
