#!/usr/bin/env bash
set -euo pipefail
xpair_run="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
xpair_repo="$(cd -- "$xpair_run/../.." && pwd)"
xpair_phase="${1:?phase required}"
shift
export APPTAINER_TMPDIR="$xpair_run/runtime/tmp"
export APPTAINER_CACHEDIR="$xpair_run/runtime/cache"
xpair_binds=(--bind "$xpair_run:/work:rw")
xpair_nv=(--nv)
xpair_python=/work/runtime/venv/bin/python
case "$xpair_phase" in
  runtime)
    xpair_nv=()
    xpair_command=(bash /work/scripts/install_runtime.sh) ;;
  prepare|exposure|preserve)
    xpair_nv=()
    xpair_binds+=(--bind "$xpair_repo:/repo:ro")
    xpair_command=("$xpair_python" "/work/scripts/$xpair_phase.py" "$@") ;;
  evaluate|cohort_detail)
    xpair_binds+=(--bind "$xpair_repo/experiments/test2_frozen_competitors_v1:/reference:ro")
    xpair_binds+=(--bind "$xpair_repo/experiments/human_ppi_data_scaling_v1/private/test:/truth:ro")
    xpair_binds+=(--bind "$xpair_repo/experiments/human_ppi_data_scaling_v1/data:/studydata:ro")
    xpair_binds+=(--bind "$xpair_repo/experiments/human_ppi_data_scaling_v1/scripts:/metrics:ro")
    xpair_binds+=(--bind "$xpair_repo/benchmark/tuna/scripts:/native:ro")
    xpair_command=("$xpair_python" "/work/scripts/$xpair_phase.py" "$@") ;;
  *) xpair_command=("$xpair_python" "/work/scripts/$xpair_phase.py" "$@") ;;
esac
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec "${xpair_nv[@]}" --no-mount bind-paths,home,cwd,hostfs --no-home --containall --cleanenv --pwd /work \
  "${xpair_binds[@]}" \
  --env "PYTHONPATH=/work/scripts:/work/sources/X-PAIR:/metrics:/native,PYTHONDONTWRITEBYTECODE=1,PYTHONUNBUFFERED=1,UCX_VFS_ENABLE=n,OMP_NUM_THREADS=8,OPENBLAS_NUM_THREADS=1,NVIDIA_TF32_OVERRIDE=0,CUBLAS_WORKSPACE_CONFIG=:4096:8,CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0},HF_HOME=/work/runtime/cache/huggingface,TRANSFORMERS_CACHE=/work/runtime/cache/huggingface/hub,HF_HUB_DISABLE_TELEMETRY=1,XDG_CACHE_HOME=/work/runtime/cache,MPLCONFIGDIR=/work/runtime/cache/matplotlib,TMPDIR=/work/runtime/tmp" \
  "$xpair_repo/benchmark/containers/images/plm-interact-native-arm64-v1.sif" "${xpair_command[@]}"
