"""Chấm validationData MỘT LẦN cho bộ chấm điểm được chọn ở bước 8 sau so sánh trên dev (compare_scorers.py).

    python src/v7/test_alt.py mlp_nopool      ->  biến thể "F_nopool" trong test_summary.json, predictions/F_nopool.csv

Các thành viên (như V7-C2): thành viên i dừng sớm trên dev fold i, huấn luyện trên 5 fold còn lại; điểm trung bình rồi softmax.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from huim_rerank_final import relative  # noqa: E402
from v7.common import OUT, load_cache  # noqa: E402
from v7.compare_scorers import BLOCKS, fit_member, make  # noqa: E402
from v7.direct import DirectScorer  # noqa: E402
from v7.experiments import prepare  # noqa: E402
from v7.final_stage import TEST, metrics, seconds_per_query, test_features, write_predictions  # noqa: E402
from v7.rerank import N_FOLDS, load_dev  # noqa: E402


def main(name: str, label: str) -> None:
    D = load_dev()
    data = prepare(D, BLOCKS)
    ids = list(range(N_FOLDS))
    members, t_fit = [], 0.0
    for i, va in enumerate(ids):
        m = make(name, data[0]["X"].shape[-1], seed=i)
        fit_member(name, m, data, [j for j in ids if j != va], va, seed=i)
        t_fit += m.fit_seconds
        members.append(m)
        print(f"  thành viên {i + 1}/{N_FOLDS}: epoch tốt nhất {m.best_epoch}, {m.fit_seconds:.0f} s", flush=True)
    T = load_cache(f"test_{TEST}")
    Xt = relative(test_features(BLOCKS)).astype(np.float32)
    o = T["cxy"][:, 0]
    t0 = time.perf_counter()
    s = np.mean([m.scores(Xt) for m in members], 0)
    w = DirectScorer.softmax(s)
    xy = o + np.einsum("ij,ijk->ik", w, T["cxy"] - o[:, None])
    ms = (time.perf_counter() - t0) / len(Xt) * 1000
    prev = OUT / "test_summary.json"
    res = json.load(open(prev, encoding="utf-8"))
    assert label not in res, f"{label} đã được chấm trên test (mỗi biến thể chấm đúng một lần)"
    res[label] = metrics(T, xy) | {"scorer_ms_per_query": round(ms, 4), "n_members": len(members), "blocks": list(BLOCKS), "scorer": name,
                                   "train_s_total": round(t_fit, 1), "ms_per_query": round(seconds_per_query(BLOCKS) * 1000 + ms, 1)}
    write_predictions(label, T, xy, w)
    json.dump(res, open(prev, "w", encoding="utf-8"), indent=1)
    r = res[label]
    print(f"{label}: test mean {r['mean']:.4f} m | median {r['median']:.3f} | P90 {r['p90']:.2f} | floor {r['floor_accuracy']:.4f} | scorer {ms:.3f} ms/query")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "F_nopool")
