#!/usr/bin/env bash
set -euo pipefail
transfer_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
transfer_repo="$(cd -- "$transfer_dir/../.." && pwd)"
transfer_phase="${1:?Specify prepare, score, compare, or verify}"
test ! -e "$transfer_dir/$transfer_phase.log"
mkdir -p "$transfer_dir/.cache/runtime" "$transfer_dir/tmp"
if [[ "$transfer_phase" == prepare || "$transfer_phase" == verify ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$transfer_dir/scripts/$transfer_phase.py" 2>&1 | tee "$transfer_dir/$transfer_phase.log"
elif [[ "$transfer_phase" == score || "$transfer_phase" == compare ]]; then
  APPTAINER_TMPDIR="$transfer_dir/.cache/runtime" apptainer exec --nv \
    --no-mount bind-paths,home,cwd,hostfs --no-home --containall --cleanenv --pwd /work \
    --bind "$transfer_repo:/project:ro,$transfer_dir:/work:rw,$transfer_dir/scripts:/code:ro,$transfer_dir/tmp:/tmp:rw" \
    --env "PYTHONPATH=/code:/opt/tuna/vendor,TUNA_UPSTREAM_DIR=/project/.private/frozen_pair_models_v3/bundle/upstream/TUnA/results/bernett/TUnA,PYTHONDONTWRITEBYTECODE=1,HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,UCX_VFS_ENABLE=n,OMP_NUM_THREADS=8,OPENBLAS_NUM_THREADS=1,PYTHONUNBUFFERED=1,CUBLAS_WORKSPACE_CONFIG=:4096:8,CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0},MPLCONFIGDIR=/work/.cache/matplotlib,XDG_CACHE_HOME=/work/.cache,NUMBA_CACHE_DIR=/work/.cache/numba,TMPDIR=/tmp" \
    "$transfer_repo/benchmark/containers/images/tuna-arm64-v1.sif" \
    python3 -B /project/benchmark/tuna/scripts/gpu_guard.py "/code/$transfer_phase.py" 2>&1 | tee "$transfer_dir/$transfer_phase.log"
else
  echo "Unknown phase: $transfer_phase" >&2
  exit 2
fi

