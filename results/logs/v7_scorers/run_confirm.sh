#!/bin/bash
cd /d/HUIM-IPS-/src
export PYTHONIOENCODING=utf-8
for c in linear_lr5e-3 mlp_nopool attn_lr5e-3; do
  python v7/compare_scorers.py --cand $c --members 5 > ../results/logs/v7_scorers/${c}_m5.log 2>&1
done
python v7/compare_scorers.py --cand gbm49 --folds 0 > ../results/logs/v7_scorers/gbm49_timing.log 2>&1
echo DONE3 > ../results/logs/v7_scorers/DONE3
