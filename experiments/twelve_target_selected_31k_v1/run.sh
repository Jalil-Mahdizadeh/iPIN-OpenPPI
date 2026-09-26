#!/usr/bin/env bash
# From an empty output directory: bash run.sh prepare; bash run.sh score;
# bash run.sh compare; bash run.sh verify
set -euo pipefail
panel_run_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
panel_repo_dir="$(cd -- "$panel_run_dir/../.." && pwd)"
panel_study_dir="$panel_repo_dir/experiments/human_ppi_data_scaling_v1"
panel_phase="${1:?Specify prepare, score, compare, or verify}"
if [[ "$panel_phase" == prepare ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$panel_run_dir/scripts/freeze_inputs.py"
elif [[ "$panel_phase" == verify ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$panel_run_dir/scripts/verify_outputs.py"
elif [[ "$panel_phase" == score || "$panel_phase" == compare ]]; then
  panel_entry=score_panel.py
  if [[ "$panel_phase" == compare ]]; then panel_entry=compare_panel.py; fi
  test ! -e "$panel_run_dir/$panel_phase.log"
  apptainer exec --nv --no-mount bind-paths,home,cwd,hostfs --no-home --containall --cleanenv --pwd /output \
    --bind "$panel_run_dir/scripts:/code:ro,$panel_run_dir/INPUT_FREEZE.json:/freeze/INPUT_FREEZE.json:ro,$panel_run_dir/output:/output:rw" \
    --bind "$panel_repo_dir/example/twelve_target_comparison_v2:/panel:ro,$panel_study_dir/runs:/model:ro" \
    --bind "$panel_study_dir/data:/studydata:ro,$panel_study_dir/audit:/audit:ro" \
    --bind "$panel_repo_dir/benchmark/tuna/scripts:/native:ro,$panel_repo_dir/benchmark/tuna/upstream/TUnA:/upstream:ro" \
    --env "PYTHONPATH=/code:/native:/panel:/opt/tuna/vendor,TUNA_UPSTREAM_DIR=/upstream/results/bernett/TUnA,PYTHONDONTWRITEBYTECODE=1,HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,UCX_VFS_ENABLE=n,OMP_NUM_THREADS=8,OPENBLAS_NUM_THREADS=1,PYTHONUNBUFFERED=1,CUBLAS_WORKSPACE_CONFIG=:4096:8,CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0},MPLCONFIGDIR=/output/.cache/matplotlib,XDG_CACHE_HOME=/output/.cache" \
    "$panel_repo_dir/benchmark/containers/images/tuna-arm64-v1.sif" \
    python /native/gpu_guard.py "/code/$panel_entry" 2>&1 | tee "$panel_run_dir/$panel_phase.log"
else
  echo "Unknown phase: $panel_phase" >&2
  exit 2
fi
