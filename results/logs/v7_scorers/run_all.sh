#!/bin/bash
cd /d/HUIM-IPS-/src
export PYTHONIOENCODING=utf-8
for c in mlp_c2 linear linear_lr5e-3 mlp_nopool gbm33 gbm49 mlp_wide attn knn49; do
  python v7/compare_scorers.py --cand $c --members 1 > ../results/logs/v7_scorers/${c}_m1.log 2>&1
done
echo ALLDONE > ../results/logs/v7_scorers/DONE
