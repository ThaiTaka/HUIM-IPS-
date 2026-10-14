# Speaker notes — HUIM trong Indoor Positioning System

> Sinh tự động bởi `src/make_slides.py`. Mỗi slide có ba phần: tôi cần nói gì, thông điệp chính, và nếu cô hỏi sâu thì trả lời gì.

Ngôn ngữ nói tự nhiên — KHÔNG đọc chữ trên slide.


## Slide 1 — Trang bìa

**Tôi cần nói gì:** Giới thiệu đề tài trong một câu — tôi thử dùng một thuật toán khai thác dữ liệu của bài toán giỏ hàng siêu thị (HUIM) để chọn ra nhóm Access Point hữu ích cho định vị trong nhà, và kiểm chứng trên bộ dữ liệu UJIIndoorLoc.

**Thông điệp chính:** Nói RÕ NGAY TỪ ĐẦU rằng đây là BÀI TÌM HIỂU — ba nhiệm vụ là tìm hiểu thuật toán, mô hình hoá áp dụng cho IPS, và cài đặt đánh giá trên UJIIndoorLoc. Không phải đồ án, không tuyên bố phương pháp mới.

**Nếu cô hỏi sâu:** Hình minh hoạ là tự vẽ bằng matplotlib, không dùng ảnh có bản quyền. Luồng trong hình chính là luồng của bài tìm hiểu: toà nhà → tín hiệu Wi-Fi → fingerprint → utility transaction → HUIM → nhóm AP → vị trí.

## Slide 2 — Bài toán

**Tôi cần nói gì:** Dẫn từ 'vì sao cần IPS' đến 'vì sao số chiều là một vấn đề thật'. Nhấn con số 96,5% — đó là lý do toàn bộ bài tìm hiểu tồn tại.

**Thông điệp chính:** Vấn đề không phải thiếu dữ liệu, mà là dữ liệu quá rộng và quá rỗng.

**Nếu cô hỏi sâu:** Offline phase là pha khảo sát, tạo ra cơ sở dữ liệu vân tay; online phase là pha định vị, so khớp vân tay mới. HUIM nằm ở pha offline.

## Slide 3 — Câu hỏi nghiên cứu

**Tôi cần nói gì:** Đặt câu hỏi dưới dạng CÂU HỎI, không phải kết luận. Và nói ngay rằng literature review không tìm thấy tiền lệ HUIM + UJIIndoorLoc, nên đây là mô hình đề xuất.

**Thông điệp chính:** Bài tìm hiểu đi tìm câu trả lời, kể cả khi câu trả lời là bất lợi.

**Nếu cô hỏi sâu:** Em đã kiểm tra 40 DOI qua Crossref; 4 không tồn tại và 12 trả về bài báo khác hẳn bài em định trích — tất cả đã bị loại. Danh sách 24 nguồn còn lại ở research/papers_table.csv.

## Slide 4 — Kết quả trước

**Tôi cần nói gì:** Đưa số thật lên trước, chưa giải thích gì. Đọc bảng: baseline bao nhiêu WAP và bao nhiêu accuracy, HUIM bao nhiêu WAP và bao nhiêu accuracy. Rồi dừng lại và đặt câu hỏi ở cuối slide.

**Thông điệp chính:** Có hiện tượng cần giải thích — và đó là lý do phải học lý thuyết, chứ không phải ngược lại.

**Nếu cô hỏi sâu:** Mọi số trong bảng đọc từ results/metrics/ips_results.csv. Siêu tham số k-NN được chọn một lần trên ALL-WAP rồi đóng băng, nên lợi thế của tinh chỉnh thuộc về baseline chứ không thuộc về phương pháp của em.

## Slide 5 — minUtil và số HUI

**Tôi cần nói gì:** Chỉ vào vùng chuyển pha trên đồ thị. Nhấn rằng trục x là log và giảm dần sang phải, trục y là symlog. Vòng tròn đỏ là các lần chạy bị dừng do hết ngân sách — em giữ lại, không xoá.

**Thông điệp chính:** Giảm ngưỡng không làm kết quả lớn dần mà làm nó bùng nổ, trong khi số AP riêng biệt gần như không tăng.

**Nếu cô hỏi sâu:** Lý do là nếu một nhóm k AP đạt ngưỡng thì cả 2^k − 1 tập con của nó cũng đạt gần như đồng thời. Đó là vì utility không có downward closure.

## Slide 6 — Giá phải trả

**Tôi cần nói gì:** Runtime và bộ nhớ là hai câu chuyện KHÁC NHAU. Runtime theo số nút cây tìm kiếm; bộ nhớ theo kích thước KẾT QUẢ.

**Thông điệp chính:** Hạ ngưỡng không làm một nút đắt hơn, nó làm có nhiều nút hơn.

**Nếu cô hỏi sâu:** Em đo bộ nhớ bằng cách lấy mẫu RSS tiến trình mỗi 20 ms thay vì dùng tracemalloc, vì tracemalloc làm chậm chương trình nhiều lần và sẽ phá chính phép đo runtime trong cùng thí nghiệm.

## Slide 7 — Khái niệm HUIM

**Tôi cần nói gì:** Năm khái niệm: item, transaction, q, p, minUtil. Rồi đến điểm cốt tử: utility không anti-monotone, nên không prune trực tiếp được.

**Thông điệp chính:** Toàn bộ literature HUIM là lịch sử đi tìm chặn trên chặt hơn.

**Nếu cô hỏi sâu:** Phản ví dụ em nêu lấy từ ví dụ chạy chuẩn của literature và được kiểm chứng bằng unit test — u({b,d}) = 30 em tính tay trong file test, và brute-force cùng EFIM đều cho ra 30.

## Slide 8 — Ánh xạ

**Tôi cần nói gì:** Đi theo năm bước trong sơ đồ, rồi đọc bảng ánh xạ. Nhấn dòng cuối cùng của bảng.

**Thông điệp chính:** q và p không có sẵn trong dữ liệu Wi-Fi; em phải định nghĩa chúng, và đó vừa là đóng góp vừa là điểm yếu lớn nhất.

**Nếu cô hỏi sâu:** Giá trị 100 trong cột WAP nghĩa là 'không phát hiện' — em đã kiểm chứng bằng ba nguồn: tài liệu UCI ghi nguyên văn, phân bố dữ liệu (không có ô nào trong khoảng 1–99 trên hơn 10 triệu ô), và tính nhất quán vật lý.

## Slide 9 — Utility models

**Tôi cần nói gì:** Ba model dùng CHUNG internal utility, chỉ khác p(i). Nhờ vậy ablation cô lập đúng một biến.

**Thông điệp chính:** Model A là đối chứng có chủ đích, không phải model em kỳ vọng tốt nhất.

**Nếu cô hỏi sâu:** MI chỉ được tính trên trainingData. Em cưỡng chế bằng code: hàm build_external_utility nhận tham số split_name và raise lỗi nếu khác 'training'. Có unit test riêng cho cơ chế đó.

## Slide 10 — EFIM

**Tôi cần nói gì:** Đi từ cây tìm kiếm: nút là itemset, con là itemset thêm một item lớn hơn. Hai chặn trên làm hai việc khác nhau — một cái loại ITEM khỏi cây con, một cái không cho VÀO nhánh.

**Thông điệp chính:** su chặt hơn lu vì nó chỉ cộng utility của các item đứng SAU z.

**Nếu cô hỏi sâu:** Nhận xét ở khung dưới là chỗ lý thuyết khớp lại với nhau — tại gốc, local utility chính bằng TWU, nên TWU pruning là trường hợp đặc biệt của local utility pruning. Em có ghi nhận xét này trong mã nguồn.

## Slide 11 — Pipeline

**Tôi cần nói gì:** Chỉ vào đường kẻ đứt màu đỏ: không có mũi tên nào đi từ phải sang trái. Đó là toàn bộ cơ chế chống data leakage.

**Thông điệp chính:** validationData được dùng đúng một lần cho mỗi điều kiện, chỉ để đánh giá.

**Nếu cô hỏi sâu:** Việc tinh chỉnh k-NN trên ALL-WAP là lựa chọn bảo thủ — mọi lợi thế của tinh chỉnh thuộc về baseline. Và vì hai split khác người dùng, khác thiết bị, khác thời điểm nên accuracy ở đây không so sánh được với các bài tự chia lại file huấn luyện.

## Slide 12 — Độ chính xác theo mét

**Tôi cần nói gì:** Trả lời trực tiếp tiêu chí 7–8 m. Nói rõ đang dùng thống kê nào: trung vị hay trung bình, toạ độ chiếu hay thực địa.

**Thông điệp chính:** Trung vị dưới mục tiêu, trung bình trên mục tiêu — chênh nhau vì đuôi phân bố, do một số fingerprint bị gán sai tầng.

**Nếu cô hỏi sâu:** Bộ dữ liệu KHÔNG ghi đơn vị toạ độ. Em xác định bằng thực nghiệm: nghịch đảo từng phép chiếu ứng viên rồi đo khoảng cách tới campus UJI. Web Mercator trúng trong 140 m, UTM lệch 497 và 871 km. Và vì Web Mercator bảo giác chứ không bảo khoảng cách, em báo cáo cả hai con số — con số chiếu để so với literature, con số thực địa vì nó đúng về vật lý.

## Slide 13 — Slide 12b — Tối ưu sai số theo mét

**Tôi cần nói gì:** k-NN của nghiên cứu (k=1, Manhattan) được chọn cho bài toán phân loại tầng trên một phép chia ngẫu nhiên, nên không phải bộ ước lượng toạ độ tốt. Em tối ưu riêng phần ước lượng toạ độ.

**Thông điệp chính:** mọi lựa chọn được làm trên các fold giữ lại người đo của trainingData; validationData chỉ chấm điểm mỗi bước đúng một lần.

**Nếu cô hỏi sâu:** bước dò độ lệch thiết bị và ensemble thắng trên dev nhưng không thắng trên validation về sai số mét — em vẫn giữ mô hình mà giao thức chọn, vì chọn lại theo validation là dùng tập kiểm tra để chọn mô hình. Mọi con số kiểm chứng được trong verification/kiem_chung_thu_cong.xlsx.

## Slide 14 — Thời gian và bộ nhớ

**Tôi cần nói gì:** Đây là tiêu chí thứ hai nhóm đặt ra. Chi phí khai thác HUIM đã nói ở slide trước; slide này là chi phí của chính hệ thống định vị.

**Thông điệp chính:** Giảm chiều cho lợi ích tuyến tính và rất rõ về cả thời gian lẫn bộ nhớ — nhưng tập đặc trưng tốt nhất đến từ đối chứng đơn giản, không phải từ HUIM.

**Nếu cô hỏi sâu:** Em đo với n_jobs=1 để con số là chi phí một lõi, khả chuyển. Ở số chiều nhỏ nhất đường cong không đơn điệu vì scikit-learn chuyển sang chỉ mục kd_tree, mà trên dữ liệu thưa thì cây chậm hơn duyệt vét cạn — em có ghi lại thuật toán index trong log để chứng minh.

## Slide 15 — Baseline vs HUIM

**Tôi cần nói gì:** Đọc ba cột của baseline, rồi so với HUIM tốt nhất. Nhấn rằng Building gần như được giải quyết còn Floor là phần khó.

**Thông điệp chính:** Một báo cáo chỉ nêu Building accuracy sẽ làm phương pháp trông tốt hơn thực tế rất nhiều.

**Nếu cô hỏi sâu:** Cả ba accuracy suy ra từ CÙNG một dự đoán nhãn joint, nên chúng nhất quán theo cấu trúc — mô hình không thể được ghi công 'đúng tầng' khi nó dự đoán sai toà nhà.

## Slide 16 — Ablation

**Tôi cần nói gì:** Ablation không chỉ so HUIM với 'dùng tất cả'. Phải có đối chứng ở CÙNG ngân sách đặc trưng, nếu không thì không phân biệt được CHỌN đặc trưng với XOÁ đặc trưng.

**Thông điệp chính:** Ba đối chứng trả lời ba câu khác nhau, và chỉ câu thứ ba là về HUIM.

**Nếu cô hỏi sâu:** Nếu HUIM không vượt top-n theo MI thì đó là kết quả ÂM và em báo cáo đúng như vậy — giá trị nằm ở chỗ đã thiết lập được phép so sánh đó.

## Slide 17 — Giảm chiều và accuracy

**Tôi cần nói gì:** Đây là slide trả lời RQ4-RQ6. Đi từ phải sang: giảm chiều tăng thì accuracy đi về đâu. So HUIM với ba đường đối chứng.

**Thông điệp chính:** Câu trả lời cho 'giảm được bao nhiêu WAP' không phải một con số — nó phụ thuộc vào accuracy nào đang được bảo vệ.

**Nếu cô hỏi sâu:** Em KHÔNG gọi đây là Pareto front, vì chưa kiểm tra điều kiện Pareto một cách hình thức. Em chỉ nói có trade-off. Ở ngân sách nhỏ, một phần sụt giảm là do MẤT ĐỘ PHỦ chứ không phải mất khả năng phân biệt — em log riêng số fingerprint kiểm định không phát hiện được AP nào trong tập đã chọn.

## Slide 18 — Tư duy ngược

**Tôi cần nói gì:** Đi dọc chuỗi ở giữa, từ trên xuống: hành vi quan sát được → cơ chế bùng nổ → vai trò của chặn trên → lý thuyết (utility không có downward closure) → ý nghĩa cho IPS.

**Thông điệp chính:** Đây là cách em học được lý thuyết — từ hiện tượng, không từ định nghĩa.

**Nếu cô hỏi sâu:** Các con số trong chuỗi lấy đúng từ log, và phân tích đầy đủ 8 quan sát nằm trong research/reverse_thinking_analysis.md — file đó và chương 15 của báo cáo Word đọc cùng một file JSON nên không thể lệch nhau.

## Slide 19 — Làm được / không làm được

**Tôi cần nói gì:** Cột trái chỉ ghi điều số liệu chứng minh. Cột phải ghi điều em KHÔNG khẳng định.

**Thông điệp chính:** Giới hạn của kết luận là một phần của kết luận.

**Nếu cô hỏi sâu:** Điểm quan trọng nhất ở cột phải là dòng cuối — HUIM là bài toán không giám sát, không có gì trong định nghĩa của nó tối ưu một mục tiêu phân loại. Vì vậy không có định lý nào để viện dẫn, chỉ có số liệu đối chứng.

## Slide 20 — Kết luận

**Tôi cần nói gì:** Trả lời trực tiếp từng câu hỏi nghiên cứu bằng con số. Không dùng từ 'vượt trội'.

**Thông điệp chính:** Trade-off chính nằm ngược trực giác — ngưỡng cao tốt hơn ngưỡng thấp cho mục đích chọn AP.

**Nếu cô hỏi sâu:** Nếu cô hỏi 'vậy có nên dùng HUIM cho IPS không', câu trả lời trung thực là: dựa trên thực nghiệm này, HUIM là một cách hợp lệ để chọn nhóm AP nhưng chưa chứng minh được là tốt hơn các tiêu chí information-theoretic đơn giản hơn — và bảng đối chứng ngân sách khớp nhau là bằng chứng duy nhất em đưa ra.

## Slide 21 — Tài liệu tham khảo

**Tôi cần nói gì:** Tám nguồn mạnh nhất. Nhấn rằng metadata lấy từ Crossref chứ không từ trí nhớ.

**Thông điệp chính:** Em không gắn Q1/Q2 cho bất kỳ nguồn nào, và em giải thích được tại sao.

**Nếu cô hỏi sâu:** Trong 40 DOI em đề xuất ban đầu, 4 không tồn tại trong Crossref và 12 trả về một bài báo HOÀN TOÀN KHÁC — ví dụ một DOI em tưởng là bài utility mining thực ra là bài về nhận dạng tiếng nói. Tất cả đã bị loại. Đó là lý do phải xác minh.