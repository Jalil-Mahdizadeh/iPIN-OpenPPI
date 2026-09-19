#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$rapppid_root/logs"
test ! -e "$rapppid_root/runs/original-v1/QUALIFICATION.json"
bash "$rapppid_root/run_setup.sh" --probe > "$rapppid_root/logs/container-guard.json" 2> "$rapppid_root/logs/container-guard.stderr.log"
bash "$rapppid_root/run_setup.sh" /code/qualify_original.py > "$rapppid_root/logs/qualification.log" 2>&1
echo 'Original-model and metric qualifications passed; no test pairs or truth read.'
