#!/usr/bin/env bash
#SBATCH --job-name=dscript-select-freeze
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=300G
#SBATCH --time=24:00:00
set -euo pipefail
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
python3 -B "$dscript_root/scripts/retrained_v1/host_guard.py" verify --cache
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --gpus-per-task=1 --cpus-per-task=72 --cpu-bind=none \
  bash "$dscript_root/prepare_retrained_test.sh"
