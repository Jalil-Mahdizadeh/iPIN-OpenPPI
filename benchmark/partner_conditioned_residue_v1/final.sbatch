#!/usr/bin/env bash
#SBATCH --job-name=ipin-residue-compare
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=128G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077
unset SLURM_CPU_BIND SLURM_CPU_BIND_LIST SLURM_CPU_BIND_TYPE SLURM_CPU_BIND_VERBOSE
study_root=${RESIDUE_STUDY_ROOT:?Must be submitted through submit.py}
python3 -B "$study_root/scripts/freeze.py" verify
srun --ntasks=1 --gpus=1 --gpus-per-task=1 --cpus-per-task=72 --cpu-bind=none \
  bash "$study_root/final.sh"
