#!/usr/bin/env bash
#SBATCH --job-name=test2-dscript
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=64G
#SBATCH --array=0-3
#SBATCH --time=12:00:00
#SBATCH --signal=USR1@300
set -euo pipefail
run_dir=${TEST2_RUN_DIR:?Set by submitter}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$run_dir/logs/dscript-array-%A-task-%a.log" bash "$run_dir/dscript_array_worker.sh"
