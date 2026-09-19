#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$rapppid_root")
repo_root=$(dirname -- "$bench_root")
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs --pwd /output \
  --bind "$rapppid_root/runtime:/opt/rapppid/runtime:ro" \
  --bind "$rapppid_root/upstream:/opt/rapppid/upstream:ro" \
  --bind "$rapppid_root/scripts:/code:ro" \
  --bind "$bench_root/containers/manifests/rapppid-downloads.json:/opt/rapppid/downloads.json:ro" \
  --bind "$bench_root/tuna/data/sequences.json:/sequences.json:ro" \
  --bind "$rapppid_root/runs/original-v1:/output:rw" \
  "$repo_root/containers/images/ipin-model-arm64_0.1.0.sif" \
  env PYTHONPATH=/opt/rapppid/runtime:/opt/rapppid/upstream/rapppid PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/output/.cache/matplotlib XDG_CACHE_HOME=/output/.cache TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/inspect_native.py
