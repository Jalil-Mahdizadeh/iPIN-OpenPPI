#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=${RAPPPID_BENCHMARK_ROOT:?Use submit_retrained.sh}
bench_root=$(dirname -- "$rapppid_root")
output="$rapppid_root/results/retrained-v1/development"
mkdir -p "$output/tmp"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$rapppid_root/runs/retrained-v1/code:/code:ro" \
  --bind "$rapppid_root/runs/retrained-v1/data:/data:ro" \
  --bind "$rapppid_root/runs/retrained-v1/training:/training:ro" \
  --bind "$rapppid_root/runs/retrained-v1/TRAINING_FREEZE.json:/protocol.json:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/rapppid-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py /code/report_development.py --through-epoch "$1"
