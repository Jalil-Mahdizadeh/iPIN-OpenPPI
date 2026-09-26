#!/usr/bin/env bash
#SBATCH --job-name=test2-compare
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=80G
#SBATCH --time=12:00:00
set -euo pipefail
run_dir=${TEST2_RUN_DIR:?Set by submitter}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none \
  --output="$run_dir/logs/evaluate-%j.log" bash "$run_dir/launch.sh" evaluate evaluation
python3 -B "$run_dir/scripts/verify_preservation.py"
python3 -B "$run_dir/scripts/status.py"
