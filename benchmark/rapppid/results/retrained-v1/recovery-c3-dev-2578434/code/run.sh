#!/usr/bin/env bash
set -euo pipefail
umask 077
rapppid_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
bench_root=$(dirname -- "$rapppid_root")
case ${1:-} in snapshot|evaluate) ;; *) echo 'Usage: run.sh snapshot|evaluate' >&2; exit 2 ;; esac
output="$rapppid_root/results/retrained-v1/recovery-c3-dev-2578434"
mkdir -p "$output/tmp"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/rapppid-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$rapppid_root/scripts/recovery_dev_v1:/code:ro" \
  --bind "$rapppid_root/runs/retrained-v1/code:/frozen_code:ro" \
  --bind "$rapppid_root/runs/retrained-v1/data:/data:ro" \
  --bind "$rapppid_root/runs/retrained-v1/training:/training:ro" \
  --bind "$rapppid_root/runs/retrained-v1/TRAINING_FREEZE.json:/protocol.json:ro" \
  --bind "$rapppid_root/results/retrained-v1/development:/previous:ro" \
  --bind "$output:/output:rw" --pwd /output \
  "$bench_root/containers/images/rapppid-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  SLURM_JOB_ID="${SLURM_JOB_ID:?Use an allocated GPU}" \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output/tmp \
  python /frozen_code/gpu_guard.py /code/evaluate.py "$1"
