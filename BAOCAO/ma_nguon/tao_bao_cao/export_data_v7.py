"""Nguồn số liệu duy nhất cho slide V7 và bộ kiểm chứng: BAOCAO/so_lieu_V7/du_lieu_bao_cao_V7.json

Mọi con số đọc từ tệp kết quả của V7 (results/huim_only/uji/v7, BAOCAO_V7/so_lieu); ví dụ minh họa (truy vấn thật,
HUI của một ô, ví dụ HUIM đồ chơi) được tính lại ở đây bằng mã của dự án và có assert đối chiếu với cache.

Chạy: python src/baocao/export_data_v7.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from huim.brute_force import brute_force_hui  # noqa: E402
from huim.efim import mine_efim  # noqa: E402
from huim_positioning import internal_utility  # noqa: E402
from huim_rerank_final import load_final_base  # noqa: E402
from v7.common import GF, load_cache  # noqa: E402

UJI = ROOT / "results" / "huim_only" / "uji"
V7 = UJI / "v7"
SO = ROOT / "BAOCAO_V7" / "so_lieu"
OUT = ROOT / "BAOCAO" / "so_lieu_V7"
EXAMPLE_ROW = 333                      # chỉ số 0-based trong validationData = hàng 335 của tệp CSV (dòng tiêu đề là hàng 1)
FINAL = "C_rel_absL3"


def num(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def rows(csv: Path) -> list[dict]:
    return [{k: (num(v) if isinstance(v, float) else v) for k, v in r.items()} for r in pd.read_csv(csv).to_dict("records")]


def toy() -> dict:
    DB = [{"a": 1, "c": 1, "d": 1}, {"a": 2, "c": 6, "e": 2, "g": 5}, {"a": 1, "b": 2, "c": 1, "d": 6, "e": 1, "f": 5},
          {"b": 4, "c": 3, "d": 3, "e": 1}, {"b": 2, "c": 2, "e": 1, "g": 2}]
    P = {"a": 5, "b": 2, "c": 1, "d": 2, "e": 3, "f": 1, "g": 1}
    TU = [sum(q * P[i] for i, q in t.items()) for t in DB]
    r = {"db": DB, "p": P, "tu": TU, "twu": {i: sum(TU[k] for k, t in enumerate(DB) if i in t) for i in "abcdefg"}}
    for mu in (30, 40):
        ref = brute_force_hui(DB, P, mu)
        got, _ = mine_efim(DB, P, mu)
        assert {frozenset(x): u for x, u, _s in ref} == {frozenset(x): u for x, u, _s in got}, "EFIM != vét cạn"
        r[f"hui_{mu}"] = [{"items": "".join(x), "u": u, "support": s} for x, u, s in ref]
    r["u_bcde_per_T"] = [sum(t[i] * P[i] for i in "bcde") if all(i in t for i in "bcde") else 0 for t in DB]
    r["u_ac_per_T"] = [sum(t[i] * P[i] for i in "ac") if all(i in t for i in "ac") else 0 for t in DB]
    return r


def example() -> dict:
    raw = pd.read_csv(ROOT / "ujiindoorloc" / "UJIndoorLoc" / "validationData.csv")
    T = load_cache("test_validationData")
    i = EXAMPLE_ROW
    assert int(T["src_row"][i]) == 335
    wap = [c for c in raw.columns if c.startswith("WAP")]
    W = raw.loc[i, wap].to_numpy(float)
    det = np.flatnonzero(W != 100)
    qr = {k: internal_utility(W[None, :], k, -104.0, 0.0)[0] for k in ("rank", "abs", "rel")}
    Wsh = np.where(W != 100, W - 10.0, 100.0)                      # cùng vân tay, điện thoại đọc thấp hơn 10 dB
    qsh = {k: internal_utility(Wsh[None, :], k, -104.0, 0.0)[0] for k in ("rank", "abs", "rel")}
    order = sorted(det, key=lambda a: (-qr["rank"][a]))
    aps = [{"ap": int(a) + 1, "rssi": int(W[a]), "q_rank": int(qr["rank"][a]), "q_abs": int(qr["abs"][a]), "q_rel": int(qr["rel"][a]),
            "q_abs_shift": int(qsh["abs"][a]), "q_rank_shift": int(qsh["rank"][a]), "q_rel_shift": int(qsh["rel"][a])} for a in order]
    true, cxy, cand, F = T["true"][i], T["cxy"][i], T["cand"][i], T["F"][i]
    p7 = pd.read_csv(V7 / "predictions" / f"{FINAL}.csv").iloc[i]
    p6 = pd.read_csv(V7 / "predictions" / "V6_star.csv").iloc[i]
    w7 = np.array([p7[f"cell{j}_weight"] for j in range(1, 31)])
    w6 = np.array([p6[f"cell{j}_weight"] for j in range(1, 31)])
    assert (np.array([p7[f"cell{j}_index"] for j in range(1, 31)]) == cand).all()
    dx, dy = cxy[:, 0] - true[0], cxy[:, 1] - true[1]
    dist = np.hypot(dx, dy) * GF
    cells = []
    for k in range(30):
        cells.append({"rank_hui": k + 1, "cell": int(cand[k]), "dx": float(dx[k]), "dy": float(dy[k]), "dist_m": float(dist[k]),
                      "S": float(F[k, 0]), "S_rel": float(F[k, 2]), "P": float(F[k, 4]), "V": float(F[k, 6]), "R": float(F[k, 7]),
                      "w6": float(w6[k]), "w7": float(w7[k])})
    sx6, sy6 = float((w6 * dx).sum()), float((w6 * dy).sum())
    sx7, sy7 = float((w7 * dx).sum()), float((w7 * dy).sum())
    e6, e7 = GF * np.hypot(sx6, sy6), GF * np.hypot(sx7, sy7)
    assert abs(e7 - p7.err_m) < 1e-6 and abs(e6 - p6.err_m) < 1e-6
    est4 = T["est"][i]
    # HUI của ô ứng viên số 1
    pos = load_final_base(GF)
    c1 = int(cand[0])
    hs = np.flatnonzero(pos.hui_cell == c1)
    q = qr["rank"]
    uu = pos.hui_util[hs]
    tau, gamma = 20.0, 2.0
    Pc, best = 0.0, None
    for h in hs:
        X = pos.hui_items[h]
        inter = [a for a in X if q[a] > 0]
        fr = len(inter) / len(X)
        qb = pos.hui_util[h] / (pos.hui_supp[h] * len(X))
        qT = float(np.mean([q[a] for a in inter])) if inter else 0.0
        ag = float(np.exp(-abs(qT - qb) / tau)) if inter else 0.0
        w = pos.hui_util[h] / uu.sum()
        Pc += w * fr ** gamma * ag
        if tuple(int(a) for a in X) == (69, 97, 98, 116, 117, 488):
            best = {"items_ap": [int(a) + 1 for a in X], "n": len(X), "u": float(pos.hui_util[h]), "support": float(pos.hui_supp[h]),
                    "q_bar": float(qb), "n_in_query": len(inter), "frac": fr, "q_T": qT, "agree": ag, "w": float(w),
                    "term": float(w * fr ** gamma * ag), "q_of_items": [int(q[a]) for a in X]}
    assert best is not None
    Ic = set(int(a) for a in np.concatenate([pos.hui_items[h] for h in hs]))
    covered = [int(a) + 1 for a in det if int(a) in Ic]
    missing = [int(a) + 1 for a in det if int(a) not in Ic]
    Vc = sum(q[a] for a in det if int(a) in Ic) / q.sum()
    assert abs(Pc - F[0, 4]) < 1e-6 and abs(Vc - F[0, 6]) < 1e-6, (Pc, F[0, 4], Vc, F[0, 6])
    return {"src_row": 335, "phone": int(T["phone"][i]), "building": int(T["bld"][i]), "floor": int(T["flr"][i]), "pred_bf": str(T["floor"][i]),
            "n_ap": int(len(det)), "aps": aps, "true_x": float(true[0]), "true_y": float(true[1]), "cells": cells,
            "v4_est": [float(est4[0]), float(est4[1])], "v4_err_m": float(GF * np.hypot(*(est4 - true))),
            "v6": {"sum_dx": sx6, "sum_dy": sy6, "err_m": float(e6)}, "v7": {"sum_dx": sx7, "sum_dy": sy7, "err_m": float(e7),
                                                                                "pred_x": float(p7.pred_x), "pred_y": float(p7.pred_y)},
            "cell1": {"cell": c1, "n_huis": int(len(hs)), "sum_u": float(uu.sum()), "n_ap_in_Ic": len(Ic), "P": float(Pc), "V": float(Vc),
                      "S_raw": float(Pc * Vc ** 3), "S_smooth": float(F[0, 0]), "R": float(F[0, 7]), "q_sum": int(q.sum()),
                      "covered": covered, "missing": missing, "hui_example": best}}


def verification_rows() -> dict:
    P = pd.read_csv(V7 / "predictions" / f"{FINAL}.csv")
    e = np.hypot(P.pred_x - P.true_x, P.pred_y - P.true_y).to_numpy() * GF
    first = []
    for k in list(range(6)) + [333]:
        r = P.iloc[k]
        first.append({"src_row": int(r.src_row), "true_x": float(r.true_x), "true_y": float(r.true_y), "pred_x": float(r.pred_x),
                      "pred_y": float(r.pred_y), "dx": float(r.pred_x - r.true_x), "dy": float(r.pred_y - r.true_y), "err_m": float(e[k])})
    return {"n": int(len(e)), "sum_err_m": float(e.sum()), "mean_err_m": float(e.mean()), "median_err_m": float(np.median(e)),
            "p90_err_m": float(np.percentile(e, 90)), "first_rows": first, "gf": GF}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = json.load(open(V7 / "test_summary.json"))
    cfg = json.load(open(ROOT / "BAOCAO_V7" / "cau_hinh" / "v7_config.json"))
    ver = json.load(open(V7 / "verification.json"))
    nested = open(ROOT / "results" / "logs" / "v7_nested_eval.log", encoding="utf-8").read()
    nm = re.findall(r"informative mean ([0-9.]+) m", nested)
    opt = float(re.search(r"optimism of the standard protocol on fold \d+: ([+-]?[0-9.]+) m", nested).group(1))
    D = {
        "toy": toy(), "example": example(), "verif": verification_rows(),
        "test": rows(SO / "test_summary.csv"), "dev_inf": rows(SO / "dev_summary_informative.csv"), "dev_all": rows(SO / "dev_summary_all_queries.csv"),
        "test_json": ts, "phones_dev": rows(SO / "dev_by_phone.csv"), "phones_test": rows(SO / "test_by_phone.csv"),
        "floor_dev": rows(SO / "dev_by_floor_correct.csv"), "floor_right_test": rows(SO / "test_by_floor_right.csv"),
        "floor_wrong_test": rows(SO / "test_by_floor_wrong.csv"), "ptype": rows(SO / "by_position_type.csv"),
        "cand_dev": rows(SO / "dev_candidate_selection.csv"), "cand_test": rows(SO / "test_candidate_selection.csv"),
        "weights": rows(SO / "dev_weight_analysis.csv"), "improved": rows(SO / "dev_improved_vs_worsened.csv"),
        "explore": rows(SO / "exploration_runs.csv"), "cost": {m: json.load(open(SO / f"inference_cost_{m}.json")) for m in ("v6", "v7")},
        "config": cfg, "verification": ver, "nested": {"standard": float(nm[0]), "strict": float(nm[1]), "diff": opt},
        "diag": json.load(open(V7 / "diagnosis.json")), "v7a": json.load(open(V7 / "V7A_dev.json")),
        "dev_files": {m: json.load(open(V7 / "dev" / f"{m}.json")) for m in ("B_base", "C_rel", "C_rel_absL3", "C_devrob", "D_hier")},
    }
    json.dump(D, open(OUT / "du_lieu_bao_cao_V7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ghi", OUT / "du_lieu_bao_cao_V7.json", "| ví dụ: hàng", D["example"]["src_row"], "V7", round(D["example"]["v7"]["err_m"], 4),
          "m, V6*", round(D["example"]["v6"]["err_m"], 4), "m | tổng sai số", round(D["verif"]["sum_err_m"], 3), "mean", round(D["verif"]["mean_err_m"], 4))


if __name__ == "__main__":
    main()
