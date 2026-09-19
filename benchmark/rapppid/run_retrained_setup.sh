#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$rapppid_root")
mkdir -p "$rapppid_root/runs/retrained-v1/tmp" "$rapppid_root/logs"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$rapppid_root/scripts/retrained_v1:/code:ro" \
  --bind "$bench_root/dscript/runs/retrained-v1/data:/source_data:ro" \
  --bind "$rapppid_root/runs/retrained-v1:/output:rw" --pwd /output \
  "$bench_root/containers/images/rapppid-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /code/gpu_guard.py "$@"
