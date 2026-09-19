#!/usr/bin/env bash
#SBATCH --job-name=tuna-final-comparison
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=90G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077
bash "${TUNA_BENCHMARK_ROOT:?Must use queue_comparison.sh}/final.sh"
