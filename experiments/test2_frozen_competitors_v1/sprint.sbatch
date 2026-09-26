#!/usr/bin/env bash
#SBATCH --job-name=test2-sprint
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=100G
#SBATCH --time=12:00:00
set -euo pipefail
run_dir=${TEST2_RUN_DIR:?Set by submitter}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=72 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$run_dir/logs/sprint-%j.log" bash "$run_dir/launch.sh" sprint sprint
