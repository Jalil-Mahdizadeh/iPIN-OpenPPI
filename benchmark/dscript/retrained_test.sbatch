#!/usr/bin/env bash
#SBATCH --job-name=dscript-retrained-C123
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --gpus=4
#SBATCH --gpus-per-node=4
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=180G
#SBATCH --time=24:00:00
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
python3 -B "$dscript_root/scripts/retrained_v1/host_guard.py" verify
srun --ntasks=4 --gpus=4 --gpus-per-node=4 --gpus-per-task=1 --cpus-per-task=18 \
  --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$dscript_root/logs/retrained-score-%j-rank-%t.log" \
  bash "$dscript_root/score_retrained_worker.sh"
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --gpus-per-task=1 --cpus-per-task=18 \
  --gpu-bind=single:1 --cpu-bind=none bash "$dscript_root/finish_retrained.sh"
