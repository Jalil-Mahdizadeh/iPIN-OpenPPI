#!/usr/bin/env bash
#SBATCH --job-name=xpair-compare
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=18
#SBATCH --mem=80G
#SBATCH --time=12:00:00
set -euo pipefail
xpair_dir=${XPAIR_RUN_DIR:?Set by submitter}
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none \
  --output="$xpair_dir/logs/collect-%j.log" bash "$xpair_dir/run.sh" collect
srun --ntasks=1 --gpus=1 --gpus-per-node=1 --cpus-per-task=18 --gpu-bind=single:1 --cpu-bind=none \
  --output="$xpair_dir/logs/evaluate-%j.log" bash "$xpair_dir/run.sh" evaluate
bash "$xpair_dir/run.sh" preserve > "$xpair_dir/logs/preserve-$SLURM_JOB_ID.log" 2>&1
