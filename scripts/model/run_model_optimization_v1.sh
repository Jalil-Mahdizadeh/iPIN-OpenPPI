#!/usr/bin/env bash
# The training process sees only the frozen train/dev bundle and private output.
set -euo pipefail
task_project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
task_root="$task_project/.private/model_optimization_v1"
task_image="$task_project/containers/images/ipin-model-arm64_0.1.0.sif"
test -f "$task_root/bundle/SEARCH_FREEZE.json"
test ! -e "$task_root/runs/START.json"
umask 077
mkdir -p -- "$task_root/runs"
exec timeout --signal=TERM --kill-after=20s 7200s \
  env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --cleanenv --containall --no-home --nv \
    --no-mount bind-paths,home,cwd,hostfs \
    --bind "$task_root/bundle:/bundle:ro" --bind "$task_root/runs:/output:rw" --pwd / \
    "$task_image" env PYTHONPATH=/bundle/code PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTHONHASHSEED=20260803 \
    OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
    python -m ipin_openppi.model_optimization.run --bundle /bundle --output /output
