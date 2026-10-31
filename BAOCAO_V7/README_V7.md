# HUIM-IPS V7 — cách chạy và cấu trúc mô hình

V7 là bản nghiên cứu tiếp theo của HUIM-IPS V6 trên UJIIndoorLoc. **V6 vẫn nguyên vẹn** (mã, mô hình, dự đoán và
số liệu của V6 không bị sửa; kiểm chứng T9 trong `verification.json` so sánh với `git HEAD`). Toàn bộ mã V7 nằm trong
`src/v7/`, test ở `tests/test_v7.py`, kết quả máy ở `results/huim_only/uji/v7/`, báo cáo ở thư mục này.

Kết quả và phân tích: [`HUIM_IPS_V7_RESEARCH_REPORT.md`](HUIM_IPS_V7_RESEARCH_REPORT.md) ·
So sánh V6 ↔ V7: [`V6_V7_COMPARISON.md`](V6_V7_COMPARISON.md) · Kiểm toán V6: [`KIEM_TOAN_V6.md`](KIEM_TOAN_V6.md).

## 1. Mô hình V7 trong một đoạn

```
fingerprint truy vấn T (không lưu fingerprint huấn luyện)
   │  EFIM đã khai thác sẵn HUI của từng ô tham chiếu, ở 5 "góc nhìn" lợi ích:
   │  rank (θ=20%) · rank-mức-3 · abs · rel · abs-mức-3          (≈ 12,9 triệu HUI; V6 dùng 3 góc nhìn, ≈ 7,33 triệu)
   ▼
điểm khớp HUI của mọi ô  ──►  tầng = tầng có 20 ô điểm cao nhất trung bình lớn nhất        (như V6)
   ▼
30 ô ứng viên của tầng đó + bằng chứng HUI của từng ô (P, V, R, điểm tương đối, hạng, hồ sơ cường độ...)
   ▼
bộ chấm điểm dùng chung (MLP nhỏ, có nhánh gộp các ứng viên) → s_i → w = softmax(s) → (x, y) = Σ w_i · tâm_ô_i
   ▲
huấn luyện bằng chính sai số tọa độ:  loss = trung bình( 0,766126 · ‖Σ w_i c_i − vị trí thật‖ )
```

HUIM vẫn là lõi: ô ứng viên, tầng, và mọi đặc trưng đầu vào của bộ chấm điểm đều sinh ra từ các tập HUI do EFIM khai
thác và từ tọa độ tâm ô. Pha định vị không dùng k-NN/WKNN và không so khớp fingerprint huấn luyện thô (kiểm bằng test
tĩnh T12 và `tests/test_v7.py`). Tọa độ thật chỉ là nhãn huấn luyện/đo lường.

## 2. Các tệp chính

| Việc | Tệp |
|---|---|
| Cấu hình mô hình được chọn | `BAOCAO_V7/cau_hinh/v7_config.json` |
| Điều phối toàn bộ quy trình | `src/v7/run_v7.py` |
| Chẩn đoán nguồn sai số (offline) | `src/v7/diagnose.py` |
| V7-A hợp nhất thích ứng | `src/v7/fusion.py`, `src/v7/run_a.py` |
| V7-B tối ưu tọa độ trực tiếp | `src/v7/direct.py`, `src/v7/experiments.py`, `src/v7/run_dev.py` |
| V7-C bằng chứng HUI bổ sung | `src/v7/extra_models.py` (rel, abs-L3), `src/v7/device.py`, `src/v7/geo.py` |
| V7-D HUI phân cấp (cấp tầng) | `src/v7/hier.py` |
| Đặc trưng dev / test | `src/v7/dev_features.py`, `src/v7/test_features.py` |
| Chấm test | `src/v7/final_stage.py` |
| Bảng, khoảng tin cậy, biểu đồ | `src/v7/analysis.py`, `src/v7/stats.py`, `src/v7/figures.py` |
| Kiểm chứng độc lập | `src/v7/verify_v7.py` → `results/huim_only/uji/v7/verification.json` |
| Kiểm tra rò rỉ chặt (lồng nhau) | `src/v7/nested_check.py` |
| Test | `tests/test_v7.py` (cộng `tests/test_efim.py` có sẵn) |

## 3. Chạy lại

Yêu cầu: Python 3.13 (kết quả báo cáo tạo trên 3.13.14, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.0.6),
`pip install -r requirements.txt`. Không cần GPU, không cần PyTorch (bộ chấm điểm viết bằng NumPy, gradient viết tay,
đã kiểm bằng sai phân hữu hạn). RAM: nên có ≥ 8 GB trống (mỗi mô hình fold nạp vào ~1–2 GB). Dữ liệu gốc đọc ở
`ujiindoorloc/UJIndoorLoc/` và không bao giờ bị ghi.

```bash
python src/v7/run_v7.py --list          # in các lệnh sẽ chạy (bước đã có kết quả sẽ được bỏ qua)
python src/v7/run_v7.py                 # chạy toàn bộ: mine → features → dev → test → report → verify
python src/v7/run_v7.py --stage dev     # hoặc từng giai đoạn
python -m pytest tests/test_v7.py -q    # 15 test
python src/v7/verify_v7.py C_rel_absL3  # kiểm chứng độc lập
```

Giai đoạn `mine` (EFIM cho 6 fold × 5 mô hình và 4 mô hình cuối) mất vài giờ; kết quả được cache trong
`results/huim_only/uji/research/` và `.../v7/models/` (các tệp lớn nằm trong `.gitignore`, sinh lại được). Mọi cache
của V7 (`results/huim_only/uji/v7/cache/*.npz`) có tệp `.meta.json` ghi: SHA-256 của `trainingData.csv`, băm chỉ số
hàng huấn luyện/đánh giá của fold, phiên bản mã, seed và cấu hình; `load_cache` từ chối cache không khớp.

Tái lập V6 (không ghi đè): V6 gốc ghi vào `results/huim_only/uji/v6/`. V7 tái tạo V6 từ cùng mô hình và đặc trưng,
ghi kết quả vào `results/huim_only/uji/v7/predictions/V6_reproduced.csv` và so khớp với bản lưu (kiểm chứng T8).

## 4. Giao thức đánh giá (tóm tắt)

* 6 fold dev = `GroupKFold` theo `PHONEID` của `trainingData.csv` (16 điện thoại), đúng như V6. Với fold đánh giá k,
  mọi mô hình HUI của đặc trưng được đào chỉ trên các điện thoại khác; bộ chấm điểm của V7 cũng chỉ huấn luyện và dừng
  sớm trên các fold khác (tập hợp 5 thành viên, mỗi thành viên dừng sớm trên một fold huấn luyện khác nhau).
* Chọn mô hình **chỉ dựa trên dev OOF**. `validationData.csv` được chấm một lần cho mỗi biến thể đã khai báo trước và
  báo cáo cả những biến thể không được chọn; nó đã được nhìn thấy nhiều lần từ V1 đến V6 nên không phải tập kiểm tra
  "chưa từng quan sát".
* "Vân tay có thông tin" = có ≥ 1 AP. 76 vân tay huấn luyện không phát hiện AP nào (mọi ô điểm 0, vị trí là kết quả
  hòa điểm) được báo cáo riêng; `validationData.csv` không có vân tay nào như vậy. Mọi bảng dev có cả hai cách tính.
