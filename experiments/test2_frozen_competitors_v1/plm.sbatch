#!/usr/bin/env bash
#SBATCH --job-name=test2-plm
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=4
#SBATCH --gpus-per-node=4
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=180G
#SBATCH --time=12:00:00
#SBATCH --signal=B:USR1@300
set -euo pipefail
run_dir=${TEST2_RUN_DIR:?Set by submitter}
srun --ntasks=16 --ntasks-per-node=4 --gpus=16 --gpus-per-node=4 --gpus-per-task=1 --cpus-per-task=18 \
  --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$run_dir/logs/plm-%j-rank-%t.log" bash "$run_dir/launch.sh" shard plm
