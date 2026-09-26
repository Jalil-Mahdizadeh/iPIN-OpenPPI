#!/usr/bin/env bash
set -euo pipefail
export SLURM_PROCID=${SLURM_ARRAY_TASK_ID:?Array task required}
export SLURM_NTASKS=4
for method in dscript_original dscript_retrained; do
  bash "$TEST2_RUN_DIR/launch.sh" shard "$method"
done
