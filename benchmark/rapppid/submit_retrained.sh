#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
export RAPPPID_BENCHMARK_ROOT="$rapppid_root"
python3 -B "$rapppid_root/scripts/retrained_v1/host_guard.py" verify
exec python3 -B "$rapppid_root/scripts/retrained_v1/submit_jobs.py"
