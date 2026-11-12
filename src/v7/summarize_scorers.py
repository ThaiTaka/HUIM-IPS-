"""Tổng hợp kết quả compare_scorers.py: sai số dev, số fold tốt hơn bộ chuẩn, thời gian huấn luyện và suy luận.

    python src/v7/summarize_scorers.py
Ghi results/huim_only/uji/v7/scorer_compare/summary.json. Quy tắc chọn (khai báo trước): sai số dev (vân tay có thông tin) thấp hơn
bộ chuẩn VÀ tốt hơn ở ít nhất 4/6 fold. Sàng lọc so với mlp_c2 (1 thành viên); xác nhận so với V7-C2 đã lưu (5 thành viên).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import OUT, err_m  # noqa: E402
from v7.experiments import load_oof  # noqa: E402
from v7.rerank import N_FOLDS, load_dev  # noqa: E402

RES = OUT / "scorer_compare"


def c2_saved() -> dict:
    D = load_dev()
    o = load_oof("C_rel_absL3")
    f = {k: float(err_m(o[k][0], D[k]["true"])[D[k]["F"][:, 0, 13] > 0].mean()) for k in range(N_FOLDS)}
    return {"inf_mean": float(np.mean(np.concatenate([err_m(o[k][0], D[k]["true"])[D[k]["F"][:, 0, 13] > 0] for k in range(N_FOLDS)]))), "fold_inf": {str(k): v for k, v in f.items()}}


def main() -> None:
    rows = {p.stem: json.load(open(p, encoding="utf-8")) for p in sorted(RES.glob("*.json")) if p.stem != "summary"}
    ref1 = rows.get("mlp_c2_m1")
    saved = c2_saved()
    out = {"c2_saved_5members": saved, "rows": {}}
    print(f"{'ứng viên':18s} {'dev (m)':>8s} {'fold tốt hơn':>13s} {'huấn luyện s/fold':>18s} {'suy luận ms/vân tay':>20s} {'tham số':>8s}")
    for name, r in rows.items():
        ref = saved if r.get("members") == 5 else ref1
        better = sum(r["fold_inf"][str(k)] < ref["fold_inf"][str(k)] for k in range(N_FOLDS)) if ref and len(r["fold_inf"]) == N_FOLDS else None
        passes = bool(ref and better is not None and r["inf_mean"] < ref["inf_mean"] and better >= 4)
        out["rows"][name] = {**{k: r[k] for k in ("inf_mean", "fold_inf", "train_s_per_fold", "infer_ms_per_query", "n_params", "members")}, "folds_better_than_ref": better, "passes_rule": passes,
                             "ref": "V7-C2 đã lưu (5 thành viên)" if r.get("members") == 5 else "mlp_c2 (1 thành viên)"}
        print(f"{name:18s} {r['inf_mean']:8.4f} {str(better) + '/6':>13s} {r['train_s_per_fold']:18.0f} {r['infer_ms_per_query']:20.4f} {str(r['n_params']):>8s}  {'ĐẠT quy tắc' if passes else ''}")
    json.dump(out, open(RES / "summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("V7-C2 đã lưu (5 thành viên): %.4f" % saved["inf_mean"])


if __name__ == "__main__":
    main()
