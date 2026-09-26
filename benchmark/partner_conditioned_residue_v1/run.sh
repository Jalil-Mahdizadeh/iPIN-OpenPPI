#!/usr/bin/env bash
set -euo pipefail
umask 077
study_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$study_root")
study_code="$study_root/scripts"
if [[ -f "$study_root/runs/TRAINING_FREEZE.json" ]]; then
  study_code="$study_root/runs/code"
fi
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/runtime"
mkdir -p "$study_root/runs/.tmp"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home \
  --no-mount bind-paths,home,cwd,hostfs --pwd /output \
  --bind "$study_code:/code:ro" \
  --bind "$study_root/config.json:/config.json:ro" \
  --bind "$bench_root/tuna/data:/source_data:ro" \
  --bind "$bench_root/tuna/runs/residue_cache:/cache:ro" \
  --bind "$study_root/runs:/output:rw" \
  "$bench_root/containers/images/tuna-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib \
  TMPDIR=/output/.tmp SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" "$@"
