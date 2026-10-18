# Mã nguồn — định vị trong nhà chỉ bằng HUIM

Bản sao các file của dự án cần cho hệ thống cuối (thư mục gốc của dự án: `src/`, `tests/`).

| File | Vai trò |
|---|---|
| `src/huim/efim.py` | Thuật toán EFIM (Zida và cộng sự, 2017): khai thác toàn bộ High Utility Itemset |
| `src/huim/brute_force.py` | Oracle vét cạn dùng để kiểm chứng EFIM |
| `src/huim_positioning.py` | Mô hình định vị: khai thác HUI theo từng ô, chấm điểm truy vấn, làm mượt, chọn tầng, ước lượng toạ độ |
| `src/run_huim_only.py` | Thực nghiệm: chọn tham số trên dev, huấn luyện mô hình cuối, chấm tập test một lần |
| `src/verify_huim_only.py` | Kiểm chứng độc lập mọi con số (không gọi EFIM, không gọi bộ định vị) |
| `src/plots_huim_only.py` | Biểu đồ kết quả |
| `src/huim_research.py` | Bước 8, phần chuẩn bị: khai thác HUI theo từng fold dev (mô hình rank, mục theo mức cường độ, lợi ích abs), hồ sơ cường độ suy ra từ HUI |
| `src/huim_rerank.py` | Bước 8, nghiên cứu: so các biến thể xếp hạng lại bằng kiểm định chéo trên dev |
| `src/huim_rerank_final.py` | Bước 8, mô hình cuối (v6): đặc trưng bằng chứng HUI, bộ hồi quy học trên dev, chấm tập test một lần |
| `src/verify_v6.py` | Kiểm chứng độc lập kết quả v6 của UJIIndoorLoc (8 phép kiểm) |
| `src/preprocess_uji.py`, `src/multi_datasets.py`, `src/utility_models.py` | Đọc dữ liệu, chuẩn hoá RSSI, nhãn vị trí |
| `src/run_multi_dataset.py`, `src/utils.py` và các module còn lại | Hàm dùng chung (chia fold, tính sai số, đường dẫn) |
| `tests/` | Kiểm thử: EFIM so với oracle vét cạn, bộ định vị so với HUI vét cạn |
| `tao_bao_cao/` | Script dựng thư mục BAOCAO (số liệu, sơ đồ, báo cáo, slide) |

## Chạy

Cần Python 3.12 và `pip install -r requirements.txt`. Dữ liệu (UJIIndoorLoc và
dataset-20261013T020803Z-1-001) nằm ở thư mục gốc dự án; đặt biến
`HUIM_IPS_ROOT` trỏ tới thư mục đó:

```bash
export HUIM_IPS_ROOT=/duong/dan/toi/HUIM-IPS-
python -m pytest tests -q                       # kiểm thử
python src/run_huim_only.py --dataset uji       # Bước 1–7: chọn trên dev, chấm test (v4)
python src/verify_huim_only.py                  # kiểm chứng độc lập Bước 1–7
# Bước 8 (UJIIndoorLoc, mô hình cuối v6)
for k in 0 1 2 3 4 5; do
  python src/huim_research.py --stage mine --fold $k                 # mô hình rank theo fold
  python src/huim_research.py --stage mine --fold $k --levels 3      # mô hình mục theo mức cường độ
  python src/huim_research.py --stage mine --fold $k --kind abs      # mô hình lợi ích abs
  python src/huim_rerank_final.py --stage dev --fold $k --with-abs   # đặc trưng dev
done
python src/huim_rerank_final.py --stage final --with-abs            # học trên dev, chấm test một lần
python src/verify_v6.py                                            # kiểm chứng v6
```

Chạy ngay trong thư mục gốc dự án (không cần biến môi trường): các lệnh trên với `src/` của dự án.
