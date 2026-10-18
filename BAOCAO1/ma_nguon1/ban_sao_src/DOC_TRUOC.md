Bản sao các file trong src/ mà thí nghiệm BAOCAO1 dùng, chép lúc tạo báo cáo để đọc kèm.
Chạy thật luôn dùng bản ở src/ (BAOCAO1/ma_nguon/01_chay_thi_nghiem.py gọi src/).

- huim_multi.py: toàn bộ thí nghiệm BAOCAO1 (union mọi θ, bước 3-8, kiểm chứng với EFIM)
- multi_datasets.py: đọc 4 bộ dữ liệu về một khuôn chung (AP, toạ độ, tầng, nhóm fold, làm sạch)
- huim/union_search.py: thuật toán tìm union HUI chính xác; huim/efim.py: EFIM liệt kê đầy đủ
- utility_models.py: q(i,T) và p(i) của Model A/B/C; preprocess_uji.py: chuẩn hoá RSSI
- optimize_positioning.py: bộ định vị k-NN và quy trình chọn trên dev
- huim_opt.py: WeightedPositioner (quy tắc weighted); feature_selection.py: thống kê AP trên HUI
- run_multi_dataset.py: lần chạy đa dữ liệu trước (EFIM, bộ định vị gốc của mỗi bộ dữ liệu)
