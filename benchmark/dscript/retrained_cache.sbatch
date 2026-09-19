#!/usr/bin/env bash
#SBATCH --job-name=dscript-native-cache
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=40G
#SBATCH --time=06:00:00
set -euo pipefail
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Set the candidate root}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --gpus-per-task=1 --cpus-per-task=72 --cpu-bind=none \
  bash "$dscript_root/run_retrained_setup.sh" /code/build_cache.py
