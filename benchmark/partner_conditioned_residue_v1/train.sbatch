#!/usr/bin/env bash
#SBATCH --job-name=ipin-residue-train
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --gpus=4
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=256G
#SBATCH --time=08:00:00
set -euo pipefail
umask 077
unset SLURM_CPU_BIND SLURM_CPU_BIND_LIST SLURM_CPU_BIND_TYPE SLURM_CPU_BIND_VERBOSE
study_root=${RESIDUE_STUDY_ROOT:?Must be submitted through submit.py}
python3 -B "$study_root/scripts/freeze.py" verify
scontrol show job "$SLURM_JOB_ID" > "$study_root/logs/slurm-${SLURM_JOB_ID}.txt"
srun --ntasks=4 --gpus=4 --gpus-per-task=1 --cpus-per-task=18 --cpu-bind=none \
  --output="$study_root/logs/train-%j-task%t.log" \
  bash "$study_root/worker.sh"
