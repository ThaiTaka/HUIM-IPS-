#!/bin/bash
cd /d/HUIM-IPS-/src
export PYTHONIOENCODING=utf-8
while [ ! -f ../results/logs/v7_scorers/DONE ]; do sleep 20; done
for c in mlp_c2_lr5e-3 mlp_nopool_lr5e-3 attn_lr5e-3; do
  python v7/compare_scorers.py --cand $c --members 1 > ../results/logs/v7_scorers/${c}_m1.log 2>&1
done
echo DONE2 > ../results/logs/v7_scorers/DONE2
