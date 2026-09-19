#!/usr/bin/env bash
#SBATCH --job-name=sprint-native-C123
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=100G
#SBATCH --time=1-00:00:00
set -euo pipefail
umask 077
sprint_root=${SPRINT_BENCHMARK_ROOT:?Set by submit.py}
export PYTHONDONTWRITEBYTECODE=1
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=72 --cpu-bind=none --kill-on-bad-exit=1 \
    python3 -B "$sprint_root/scripts/pipeline.py" evaluate
