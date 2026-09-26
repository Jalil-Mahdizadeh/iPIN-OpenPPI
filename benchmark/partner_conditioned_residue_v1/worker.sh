#!/usr/bin/env bash
set -euo pipefail
study_root=${RESIDUE_STUDY_ROOT:?}
recipes=(mean_pool attention_pool cross_attention cross_attention_wide)
recipe=${recipes[${SLURM_PROCID:?}]}
exec bash "$study_root/run.sh" python /code/gpu_guard.py /code/train.py --recipe "$recipe"
