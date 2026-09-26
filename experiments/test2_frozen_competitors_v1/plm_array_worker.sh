#!/usr/bin/env bash
set -euo pipefail
export SLURM_PROCID=${SLURM_ARRAY_TASK_ID:?Array task required}
export SLURM_NTASKS=16
bash "$TEST2_RUN_DIR/launch.sh" shard plm
