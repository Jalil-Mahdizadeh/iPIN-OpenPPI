#!/usr/bin/env bash
set -euo pipefail
umask 077
study_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(dirname -- "$study_root")
mkdir -p "$study_root/runtime/cache" "$study_root/runtime/tmp" "$study_root/logs"
export APPTAINER_CACHEDIR="$study_root/runtime/cache"
export APPTAINER_TMPDIR="$study_root/runtime/tmp"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
 apptainer exec --nv --cleanenv --containall --no-home \
 --no-mount bind-paths,home,cwd,hostfs --pwd /work \
 --bind "$repo_root:/source:ro" --bind "$study_root:/work:rw" \
 --bind "$study_root/runtime/tmp:/tmp:rw" \
 "$repo_root/containers/images/ipin-model-arm64_0.1.0.sif" \
 env PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CUBLAS_WORKSPACE_CONFIG=:4096:8 \
 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 \
 TMPDIR=/work/runtime/tmp XDG_CACHE_HOME=/work/runtime/cache \
 TORCH_HOME=/work/runtime/cache/torch CUDA_CACHE_PATH=/work/runtime/cache/cuda \
 python -B /work/scripts/study.py "$@"
