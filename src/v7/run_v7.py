"""One command for the whole V7 study (every step skips itself when its output already exists).

    python src/v7/run_v7.py                 # everything, in order
    python src/v7/run_v7.py --stage dev     # one stage:  mine | features | dev | test | report | verify
    python src/v7/run_v7.py --list          # print the commands without running them

Stages
  mine      EFIM on the training phones of each dev fold (rank, rank-L3, abs, rel, abs-L3 and the floor-level models)
            and the full-training-data models (abs, L3, rel, abs-L3, floor-level). The base rank model of V6 is shipped
            in results/huim_only/uji/model/. Slow (hours); the results are cached under results/huim_only/uji/.
  features  V6/V7 HUI-evidence features of the 30 candidate cells for the dev folds and the test set
  dev       diagnosis, V7-A, out-of-fold runs of the V7-B/C variants
  test      the declared variants on validationData (scored once per variant, no selection on it)
  report    tables, figures
  verify    pytest + independent checks (src/v7/verify_v7.py)
  nested    strict nested leakage check for outer fold 2 (15 extra HUI models; ~2 h), optional
Memory: each fold model needs ~1-2 GB while mined or scored; the stages run one process at a time.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
UJI = ROOT / "results" / "huim_only" / "uji"
RES, V7 = UJI / "research", UJI / "v7"
PY = sys.executable
FOLDS = range(6)


def cmds(stage: str) -> list[tuple[Path, list[str]]]:
    """(output that proves the step is done, command) in execution order."""
    out = []
    if stage == "mine":
        for k in FOLDS:
            out += [(RES / f"fold{k}.npz", ["huim_research.py", "--stage", "mine", "--fold", str(k)]),
                    (RES / f"fold{k}_L3_t20.npz", ["huim_research.py", "--stage", "mine", "--fold", str(k), "--levels", "3"]),
                    (RES / f"fold{k}_abs_L1_t20.npz", ["huim_research.py", "--stage", "mine", "--fold", str(k), "--kind", "abs"]),
                    (RES / f"fold{k}_rel_L1_t20.npz", ["huim_research.py", "--stage", "mine", "--fold", str(k), "--kind", "rel"]),
                    (RES / f"fold{k}_abs_L3_t20.npz", ["huim_research.py", "--stage", "mine", "--fold", str(k), "--levels", "3", "--kind", "abs"])]
        out += [(RES / f"fold{k}_floor_t12.5.npz", ["v7/hier.py", "mine", "--fold", str(k)]) for k in FOLDS]
        out += [(V7 / "models" / "floor_L1_final.npz", ["v7/hier.py", "mine", "--final"])]
        out += [(UJI / "v5" / "model_abs.npz", ["v7/final_models.py", "abs"]), (UJI / "v5" / "model_L3.npz", ["v7/final_models.py", "L3"]),
                (V7 / "models" / "rel_L1.npz", ["v7/final_models.py", "rel", "1"]),
                (V7 / "models" / "abs_L3.npz", ["v7/final_models.py", "abs", "3"])]
    elif stage == "features":
        for k in FOLDS:
            out.append((V7 / "cache" / f"dev_fold{k}.npz", ["v7/dev_features.py", "--fold", str(k)]))
        for blk in ("rel", "absL3"):
            for k in FOLDS:
                out.append((V7 / "cache" / f"dev_fold{k}_{blk}.npz", ["v7/extra_models.py", "--block", blk, "--fold", str(k)]))
        for k in FOLDS:
            out.append((V7 / "cache" / f"dev_fold{k}_devrob.npz", ["v7/device.py", "--fold", str(k)]))
        out += [(V7 / "cache" / f"dev_fold{k}_hier.npz", ["v7/hier.py", "block", "--fold", str(k)]) for k in FOLDS]
        out.append((V7 / "cache" / "test_validationData_absL3.npz", ["v7/test_features.py", "rel", "absL3"]))
        out.append((V7 / "cache" / "test_validationData_hier.npz", ["v7/hier.py", "test"]))
    elif stage == "dev":
        out += [(V7 / "diagnosis.json", ["v7/diagnose.py"]), (V7 / "V7A_dev.json", ["v7/run_a.py"])]
        for v in ("B_base", "C_rel", "C_rel_absL3", "C_devrob", "D_hier"):
            out.append((V7 / "dev" / f"{v}.json", ["v7/run_dev.py", "--variant", v]))
    elif stage == "test":
        out.append((V7 / "test_summary.json", ["v7/final_stage.py", "B_base", "C_rel", "C_rel_absL3", "D_hier"]))
    elif stage == "report":
        out += [(ROOT / "BAOCAO_V7" / "so_lieu" / "dev_summary_informative.csv", ["v7/analysis.py"]),
                (ROOT / "BAOCAO_V7" / "so_lieu" / "dev_weight_analysis.csv", ["v7/weight_analysis.py"]),
                (ROOT / "BAOCAO_V7" / "so_lieu" / "by_position_type.csv", ["v7/position_type.py"]),
                (ROOT / "BAOCAO_V7" / "so_lieu" / "exploration_runs.csv", ["v7/exploration_table.py"]),
                (ROOT / "BAOCAO_V7" / "so_lieu" / "inference_cost_v6.json", ["v7/measure_inference.py", "v6"]),
                (ROOT / "BAOCAO_V7" / "so_lieu" / "inference_cost_v7.json", ["v7/measure_inference.py", "v7"]),
                (ROOT / "BAOCAO_V7" / "bieu_do" / "F1_cdf_dev.png", ["v7/figures.py"]),
                (ROOT / "BAOCAO_V7" / "cau_hinh" / "v7_config.json", ["v7/write_config.py"])]
    elif stage == "nested":
        for j in (0, 1, 3, 4, 5):
            out += [(RES / f"nested_k2_j{j}_abs.npz", ["v7/nested_check.py", "mine", "--outer", "2", "--inner", str(j)]),
                    (V7 / "cache" / f"nested_k2_j{j}.npz", ["v7/nested_check.py", "feat", "--outer", "2", "--inner", str(j)])]
        out.append((ROOT / "results" / "logs" / "v7_nested_eval.log", ["v7/nested_check.py", "eval", "--outer", "2"]))
    elif stage == "verify":
        out += [(V7 / "verification.json", ["v7/verify_v7.py", "C_rel_absL3"])]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["mine", "features", "dev", "test", "report", "verify", "nested", "all"], default="all")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    for stage in (["mine", "features", "dev", "test", "report", "verify"] if a.stage == "all" else [a.stage]):
        for done, cmd in cmds(stage):
            if done.exists():
                print(f"[{stage}] skip (exists): {done.relative_to(ROOT)}")
                continue
            print(f"[{stage}] {' '.join(cmd)}", flush=True)
            if not a.list:
                subprocess.run([PY, *cmd], cwd=SRC, check=True)
    if not a.list and a.stage in ("all", "verify"):
        subprocess.run([PY, "-m", "pytest", "-q", "tests/test_v7.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
