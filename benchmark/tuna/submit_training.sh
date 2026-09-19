#!/usr/bin/env bash
set -euo pipefail
umask 077
tuna_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
test -f "$tuna_root/runs/TRAINING_FREEZE.json"
test ! -e "$tuna_root/runs/TRAINING_JOB.txt"
export TUNA_BENCHMARK_ROOT="$tuna_root"
tuna_job=$(sbatch --parsable --chdir="$tuna_root" \
  --output="$tuna_root/logs/slurm-%j.stdout.log" \
  --error="$tuna_root/logs/slurm-%j.stderr.log" \
  "$tuna_root/train_seeds.sbatch")
printf '%s\n' "$tuna_job" | tee "$tuna_root/runs/TRAINING_JOB.txt"
