#!/usr/bin/env bash
set -euo pipefail
umask 077
study_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
for stage in select features score evaluate; do
  bash "$study_root/run_gpu.sh" "$stage" > "$study_root/logs/final-${stage}.log" 2>&1
done
python3 "$study_root/scripts/freeze_execution.py" verify > "$study_root/logs/final-integrity.log" 2>&1
