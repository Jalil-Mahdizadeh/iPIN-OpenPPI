#!/usr/bin/env bash
# GPU runtime: allowlisted read-only inputs, benchmark-local writable outputs.
set -euo pipefail
umask 077
tuna_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$tuna_root")
repo_root=$(dirname -- "$bench_root")
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/runtime"
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" "$tuna_root/runs" "$tuna_root/logs"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home \
  --no-mount bind-paths,home,cwd,hostfs --pwd /output \
  --bind "$tuna_root/scripts:/code:ro" \
  --bind "$tuna_root/upstream/TUnA:/upstream:ro" \
  --bind "$tuna_root/weights:/weights:ro" \
  --bind "$tuna_root/data:/data:ro" \
  --bind "$repo_root/.private/frozen_pair_models_v1/bundle/encoder:/encoder:ro" \
  --bind "$tuna_root/runs:/output:rw" \
  "$bench_root/containers/images/tuna-arm64-v1.sif" \
  env TUNA_UPSTREAM_DIR=/upstream/results/bernett/TUnA \
  MPLCONFIGDIR=/output/.cache/matplotlib HF_HOME=/output/.cache/huggingface \
  XDG_CACHE_HOME=/output/.cache TMPDIR=/output/.tmp PYTHONUNBUFFERED=1 \
  SLURM_JOB_ID="${SLURM_JOB_ID:-}" CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  "$@"
