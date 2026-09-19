#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
test -f "$dscript_root/runs/original-v1/scorer_bundle/SCORER_FREEZE.json"
test -f "$dscript_root/private/original-v1/session/SESSION.json"
test ! -e "$dscript_root/runs/original-v1/JOB.txt"
export DSCRIPT_BENCHMARK_ROOT="$dscript_root"
dscript_job=$(sbatch --parsable --chdir="$dscript_root" \
  --output="$dscript_root/logs/original-job-%j.stdout.log" \
  --error="$dscript_root/logs/original-job-%j.stderr.log" "$dscript_root/original.sbatch")
printf '%s\n' "$dscript_job" | tee "$dscript_root/runs/original-v1/JOB.txt"
