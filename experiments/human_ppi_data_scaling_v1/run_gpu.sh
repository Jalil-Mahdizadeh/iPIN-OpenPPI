#!/usr/bin/env bash
set -euo pipefail
umask 077
study_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
experiments_root=$(dirname -- "$study_root")
repo_root=$(dirname -- "$experiments_root")
bench_root="$repo_root/benchmark"
mode=${1:?mode required}
shift
if [[ -f "$study_root/audit/EXECUTION_FREEZE.json" ]]; then
  python3 "$study_root/scripts/freeze_execution.py" verify
fi
mkdir -p "$study_root/runs" "$study_root/logs" "$study_root/runs/.tmp"
export APPTAINER_TMPDIR="$study_root/work/apptainer-tmp"
export APPTAINER_CACHEDIR="$study_root/work/apptainer-cache"
mkdir -p "$APPTAINER_TMPDIR" "$APPTAINER_CACHEDIR"
extra=()
case "$mode" in
  embeddings)
    entry=extend_embeddings.py
    extra+=(--bind "$bench_root/tuna/runs/residue_cache:/old_cache:ro")
    extra+=(--bind "$bench_root/tuna/data:/old_data:ro")
    extra+=(--bind "$repo_root/.private/frozen_pair_models_v1/bundle:/pooled:ro")
    extra+=(--bind "$repo_root/src:/library:ro")
    extra+=(--bind "$repo_root/.private/frozen_pair_models_v1/bundle/encoder:/encoder:ro") ;;
  qualify) entry=qualify_study.py ;;
  qualify-metrics) entry=macro_metrics.py ;;
  train) entry=train_curve.py ;;
  select) entry=select_models.py ;;
  features)
    entry=freeze_features.py
    extra+=(--bind "$repo_root/.private/frozen_pair_models_v2/bundle:/old_models:ro") ;;
  score)
    entry=score_panels.py
    extra+=(--bind "$study_root/private/candidates:/candidates:ro")
    extra+=(--bind "$repo_root/.private/frozen_pair_models_v1/bundle:/pooled:ro") ;;
  evaluate)
    entry=evaluate_panels.py
    extra+=(--bind "$study_root/private/test:/truth:ro") ;;
  *) exit 2 ;;
esac
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home \
  --no-mount bind-paths,home,cwd,hostfs --pwd /output \
  --bind "$study_root/scripts:/code:ro" \
  --bind "$bench_root/tuna/scripts:/native:ro" \
  --bind "$bench_root/tuna/upstream/TUnA:/upstream:ro" \
  --bind "$bench_root/tuna/weights:/weights:ro" \
  --bind "$study_root/data:/data:ro" \
  --bind "$study_root/audit:/freeze:ro" \
  --bind "$study_root/runs:/output:rw" "${extra[@]}" \
  "$bench_root/containers/images/tuna-arm64-v1.sif" \
  env PYTHONPATH=/code:/native:/library:/opt/tuna/vendor PYTHONDONTWRITEBYTECODE=1 \
  TUNA_UPSTREAM_DIR=/upstream/results/bernett/TUnA HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  UCX_VFS_ENABLE=n OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1 \
  MPLCONFIGDIR=/output/.cache/matplotlib XDG_CACHE_HOME=/output/.cache TMPDIR=/output/.tmp \
  CUBLAS_WORKSPACE_CONFIG=:4096:8 SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  python /native/gpu_guard.py "/code/$entry" "$@"
