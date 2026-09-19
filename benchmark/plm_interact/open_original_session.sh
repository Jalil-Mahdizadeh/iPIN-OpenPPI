#!/usr/bin/env bash
set -euo pipefail
umask 077
plm_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$plm_root")
repo_root=$(dirname -- "$bench_root")
bundle="$plm_root/runs/original-v1/scorer_bundle"
test -f "$bundle/SCORER_FREEZE.json"
python3 -B "$plm_root/scripts/host_guard.py"
mkdir -p "$plm_root/private/original-v1"
mkdir "$plm_root/private/original-v1/session"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/plm-interact-v1"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --nv --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --bind "$bundle:/bundle:ro" --bind "$bundle/code:/code:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/session:/previous_session:ro" \
  --bind "$plm_root/private/original-v1/session:/output:rw" --pwd /output \
  "$bench_root/containers/images/plm-interact-native-arm64-v1.sif" \
  env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0 \
  OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
  HF_HOME=/output/.cache/huggingface TRANSFORMERS_CACHE=/output/.cache/transformers \
  XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output \
  python /code/gpu_guard.py /code/comparison.py open
