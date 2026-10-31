"""Table of the exploratory dev runs (log files copied to BAOCAO_V7/so_lieu/logs): per-fold errors and the query-weighted mean."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v7.common import PROJECT_ROOT  # noqa: E402
from v7.rerank import load_dev  # noqa: E402

LOG = PROJECT_ROOT / "results" / "logs" / "v7_explore"
DEST = PROJECT_ROOT / "BAOCAO_V7" / "so_lieu"
RUNS = [("b_c1.log", "1 thành viên, MLP 64/32, lr 5e-4, wd 1e-4, dừng sớm theo 1 fold", "V6"),
        ("b_c2.log", "như trên + mất mát phụ listwise (aux 0,3)", "V6"),
        ("b_c3.log", "1 thành viên, MLP 32/16, wd 1e-3", "V6"),
        ("b_c3_devrob.log", "như dòng trên + khối bù lệch thiết bị (13 cột)", "V6 + devrob"),
        ("b2_base.log", "tập hợp 5 thành viên + log có dấu (= V7-B)", "V6"),
        ("b2_rel.log", "như trên + HUI rel (= V7-C1)", "V6 + rel"),
        ("b2_rel_geo.log", "như trên + đồng thuận không gian (15 cột)", "V6 + rel + geo"),
        ("b2_rel_absL3.log", "như trên + HUI abs mức-3 (= V7-C2)", "V6 + rel + absL3")]


def main() -> None:
    n = np.array([(d["F"][:, 0, 13] > 0).sum() for d in load_dev()])
    rows = []
    (DEST / "logs").mkdir(parents=True, exist_ok=True)
    for f, desc, feats in RUNS:
        shutil.copy(LOG / f, DEST / "logs" / f)
        txt = (LOG / f).read_text(errors="ignore")
        e = [float(x) for _k, x in re.findall(r"(?:outer )?fold (\d): direct ([0-9.]+)", txt)][:6]
        if len(e) == 6:
            rows.append({"log": f, "mo_ta": desc, "dac_trung": feats, **{f"fold{k}": v for k, v in enumerate(e)}, "tb_co_trong_so": float((np.array(e) * n).sum() / n.sum())})
    df = pd.DataFrame(rows)
    df.round(4).to_csv(DEST / "exploration_runs.csv", index=False)
    print(df[["log", "dac_trung", "tb_co_trong_so"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
