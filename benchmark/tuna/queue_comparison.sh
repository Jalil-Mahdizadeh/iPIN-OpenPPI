#!/usr/bin/env bash
set -euo pipefail
umask 077
tuna_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
test -f "$tuna_root/runs/EXECUTION_CODE_FREEZE.json"
test ! -e "$tuna_root/runs/COMPARISON_JOB.txt"
tuna_training_job=$(head -n 1 "$tuna_root/runs/TRAINING_JOB.txt")
[[ "$tuna_training_job" =~ ^[0-9]+$ ]]
export TUNA_BENCHMARK_ROOT="$tuna_root"
tuna_job=$(sbatch --parsable --dependency="afterok:$tuna_training_job" --chdir="$tuna_root" \
  --output="$tuna_root/logs/comparison-%j.stdout.log" --error="$tuna_root/logs/comparison-%j.stderr.log" \
  "$tuna_root/final.sbatch")
printf '%s\n' "$tuna_job" | tee "$tuna_root/runs/COMPARISON_JOB.txt"
