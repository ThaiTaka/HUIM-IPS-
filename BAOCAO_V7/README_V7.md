# HUIM-IPS V7 — cách chạy và cấu trúc mô hình

V7 là bản nghiên cứu tiếp theo của HUIM-IPS V6 trên UJIIndoorLoc. **V6 vẫn nguyên vẹn** (mã, mô hình, dự đoán và
số liệu của V6 không bị sửa; kiểm chứng T9 trong `verification.json` so sánh với `git HEAD`). Toàn bộ mã V7 nằm trong
`src/v7/`, test ở `tests/test_v7.py`, kết quả máy ở `results/huim_only/uji/v7/`, báo cáo ở thư mục này.

Kết quả và phân tích: [`HUIM_IPS_V7_RESEARCH_REPORT.md`](HUIM_IPS_V7_RESEARCH_REPORT.md) ·
So sánh V6 ↔ V7: [`V6_V7_COMPARISON.md`](V6_V7_COMPARISON.md) · Kiểm toán V6: [`KIEM_TOAN_V6.md`](KIEM_TOAN_V6.md).

## Kết quả chính (số đo thật, xem báo cáo để biết chi tiết)

| | V6 | V7-C2 (chọn theo dev) |
|---|---|---|
| validationData, sai số TB / trung vị / P90 | 6,866 / 5,140 / 14,02 m (tái tạo: 6,861) | **6,309** / 4,636 / 12,85 m |
| dev out-of-fold, vân tay có thông tin (19.861) | 6,209 m (V6\*, float64) | **5,702** m |
| đúng tầng / đúng tòa (test) | 80,38% / 99,91% | 80,38% / 99,91% (giữ quy tắc chọn tầng) |

**Mục tiêu dưới 6,00 m chưa đạt.** Chênh lệch V7-C2 so với V6 trên test là −0,557 m (KTC 95% theo cụm điện thoại [−1,103; −0,149]).
V7-A (hợp nhất thích ứng), khối bù lệch thiết bị, khối đồng thuận không gian, trộn với GBM và V7-D (HUI cấp tầng) không phải cải tiến; xem
báo cáo §6.9 và §7. Kiểm tra rò rỉ chặt (lồng nhau) trên fold ngoài số 2: chênh lệch −0,0035 m (§6.8). Kiểm chứng độc lập: 16 phép, 0 thất bại.

**Thử nghiệm bổ sung V7-E (sau báo cáo chính):** cùng mô hình V7-C2 nhưng tập hợp 5 seed (30 thành viên thay vì 6; `python src/v7/run_dev.py --variant E_seeds`, `python src/v7/final_stage.py E_seeds`). Dev 5,6814 m (thấp hơn V7-C2 0,020 m, tốt hơn ở 6/6 fold, đạt quy tắc chọn đã khai báo); test chấm một lần **6,2775 m** (trung vị 4,6138; P90 12,8264; tự tính lại từ `predictions/E_seeds.csv`). Cải thiện nhỏ (0,032 m) và bộ kiểm chứng Excel/Python chưa phủ V7-E, nên số chính của báo cáo và slide vẫn là V7-C2 (6,309 m).

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
| Kiểm tra rò rỉ chặt (lồng nhau) | `src/v7/nested_check.py` (`run_v7.py --stage nested`) |
| Phân tích phụ | `src/v7/weight_analysis.py`, `src/v7/position_type.py`, `src/v7/exploration_table.py`, `src/v7/measure_inference.py` |
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
python -m pytest tests/test_v7.py -q    # 15 test (toàn bộ `pytest tests`: 171 đạt, 1 bỏ qua)
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

## 5. Slide và bộ kiểm chứng trong thư mục BAOCAO

* `BAOCAO/Slide_HUIM_IPS_V7.pptx`: 55 slide (cùng thiết kế với slide V6): lý thuyết có ví dụ số, các bước thuật toán tới 6,309 m với công thức có chú thích ký hiệu,
  ví dụ trọn vẹn một vân tay thật (hàng 335) tính tay, kết quả, kiểm chứng 6,309 m, kết luận và **slide cuối: tóm tắt một slide cho người mới học HUIM trong IPS**.
* `BAOCAO/so_lieu_V7/`: bộ kiểm chứng giống `BAOCAO/so_lieu/` (Excel `kiem_chung_V7_mean.xlsx`, Python `kiem_tra_V7.py`, dự đoán từng mẫu, `kiem_chung_V7.json`);
  hướng dẫn ở `BAOCAO/so_lieu_V7/HUONG_DAN_KIEM_CHUNG.md` và `BAOCAO/00_HUONG_DAN_DOC.md`.
* Dựng lại: `python src/baocao/export_data_v7.py`, `python src/baocao/make_so_lieu_kit_v7.py`, `node src/baocao/build_slides_v7.js` (cần npm `pptxgenjs`).
