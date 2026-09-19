#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
export DSCRIPT_BENCHMARK_ROOT="$dscript_root"
python3 -B "$dscript_root/scripts/retrained_v1/host_guard.py" verify
exec python3 -B "$dscript_root/scripts/retrained_v1/submit_jobs.py"
