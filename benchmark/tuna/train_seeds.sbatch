#!/usr/bin/env bash
#SBATCH --job-name=tuna-pu-3seeds
#SBATCH --account=naiss2025-3-10-gpu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=3
#SBATCH --gpus=3
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=180G
#SBATCH --time=16:00:00
# Paths for --chdir/--output/--error are supplied by submit_training.sh.
set -euo pipefail
umask 077
unset SLURM_CPU_BIND SLURM_CPU_BIND_LIST SLURM_CPU_BIND_TYPE SLURM_CPU_BIND_VERBOSE
tuna_root=${TUNA_BENCHMARK_ROOT:?Must be submitted by benchmark/tuna/submit_training.sh}
bench_root=$(dirname -- "$tuna_root")
test -f "$tuna_root/runs/TRAINING_FREEZE.json"
test "$(sha256sum "$bench_root/containers/images/tuna-arm64-v1.sif" | cut -d ' ' -f1)" = 98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1
scontrol show job "$SLURM_JOB_ID" > "$tuna_root/logs/slurm-${SLURM_JOB_ID}.txt"
pids=()
for tuna_seed in 20260803 20260817 20260831; do
  srun --exclusive --cpu-bind=none --nodes=1 --ntasks=1 --cpus-per-task=72 --gpus=1 --gpus-per-task=1 --mem=60G \
    bash "$tuna_root/run.sh" python /code/train.py --seed "$tuna_seed" --resume \
    > "$tuna_root/logs/train-${tuna_seed}-${SLURM_JOB_ID}.log" 2>&1 &
  pids+=("$!")
done
tuna_status=0
for tuna_pid in "${pids[@]}"; do
  if ! wait "$tuna_pid"; then tuna_status=1; fi
done
exit "$tuna_status"
