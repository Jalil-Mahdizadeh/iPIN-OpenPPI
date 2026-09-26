#!/usr/bin/env bash
#SBATCH --job-name=xpair-ankh
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=80G
#SBATCH --array=0-7
#SBATCH --time=12:00:00
set -euo pipefail
xpair_dir=${XPAIR_RUN_DIR:?Set by submitter}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none \
  --output="$xpair_dir/logs/embedding-%A-%a.log" bash "$xpair_dir/run.sh" embedding --rank "$SLURM_ARRAY_TASK_ID"
