Bản sao các file trong src/ mà thí nghiệm HUIM dùng, chép lúc tạo báo cáo để đọc kèm.
Chạy thật luôn dùng bản ở src/ (BAOCAO/ma_nguon/01_chay_thi_nghiem.py gọi src/).

- huim/union_search.py: thuật toán tìm union HUI chính xác (mục 3.2 báo cáo)
- huim/efim.py: EFIM liệt kê đầy đủ (PHASE H); huim/brute_force.py: oracle kiểm thử
- utility_models.py: q(i,T) và p(i) của Model A/B/C
- huim_opt.py: union theo θ, HUIM theo tòa (PBModel), đánh giá dev/tập test, ensemble, đo thời gian
- run_huim_opt.py: các bước 2-8; run_union_levels.py: union mọi θ song song; check_union_search.py: kiểm chứng với EFIM
- optimize_positioning.py: bộ định vị S4; preprocess_uji.py, ips_model.py, utils.py: đọc dữ liệu, hằng số
- tests/test_union_search.py: union của thuật toán = union của oracle vét cạn (19 kiểm thử)
