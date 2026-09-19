#!/usr/bin/env bash
#SBATCH --job-name=dscript-pu-3seeds
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=3
#SBATCH --gpus=3
#SBATCH --gpus-per-node=3
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=300G
#SBATCH --time=3-00:00:00
#SBATCH --requeue
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
stage=${1:?Supply final epoch for this two-epoch stage}
python3 -B "$dscript_root/scripts/retrained_v1/host_guard.py" verify --cache
srun --ntasks=3 --gpus=3 --gpus-per-node=3 --gpus-per-task=1 --cpus-per-task=72 \
  --gpu-bind=single:1 --cpu-bind=none --kill-on-bad-exit=1 \
  --output="$dscript_root/logs/retrained-train-%j-rank-%t.log" \
  bash "$dscript_root/run_retrained_worker.sh" "$stage"
