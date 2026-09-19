#!/usr/bin/env bash
set -euo pipefail
umask 077
plm_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$plm_root/logs"
test ! -e "$plm_root/runs/original-v1/QUALIFICATION.json"
bash "$plm_root/run_setup.sh" --probe > "$plm_root/logs/container-guard.json" 2> "$plm_root/logs/container-guard.stderr.log"
bash "$plm_root/run_setup.sh" /code/qualify_original.py > "$plm_root/logs/qualification.log" 2>&1
echo 'Original-model and metric qualifications passed; no test pairs or truth read.'
