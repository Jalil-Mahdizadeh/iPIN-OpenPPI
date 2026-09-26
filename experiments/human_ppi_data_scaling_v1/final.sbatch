#!/usr/bin/env bash
#SBATCH --job-name=human-ppi-scale-final
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=64G
#SBATCH --time=06:00:00
set -euo pipefail
unset SLURM_CPU_BIND SLURM_CPU_BIND_LIST SLURM_CPU_BIND_TYPE SLURM_CPU_BIND_VERBOSE
study_root=${HUMAN_PPI_STUDY_ROOT:?Must be submitted with scripts/submit.py}
exec srun --cpu-bind=none --nodes=1 --ntasks=1 --gpus=1 --gpus-per-task=1 --cpus-per-task=18 \
  bash "$study_root/final.sh"
