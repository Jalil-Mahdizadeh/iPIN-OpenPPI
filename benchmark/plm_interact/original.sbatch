#!/usr/bin/env bash
#SBATCH --job-name=plm-original-C123
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --gpus=4
#SBATCH --gpus-per-node=4
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=180G
#SBATCH --time=72:00:00
#SBATCH --signal=USR1@300
set -euo pipefail
umask 077
plm_root=${PLM_INTERACT_BENCHMARK_ROOT:?Set by submit_original.sh}
python3 -B "$plm_root/scripts/host_guard.py"
# Explicit totals override one-GPU values inherited from an interactive allocation.
srun --ntasks=4 --gpus=4 --gpus-per-node=4 --gpus-per-task=1 --cpus-per-task=18 \
  --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$plm_root/logs/original-score-%j-rank-%t.log" \
  bash "$plm_root/score_original_worker.sh"
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --gpus-per-task=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none \
  bash "$plm_root/finish_original.sh"
