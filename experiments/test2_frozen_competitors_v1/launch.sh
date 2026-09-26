#!/usr/bin/env bash
set -euo pipefail
run_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$run_dir/../.." && pwd)"
study_dir="$repo_dir/experiments/human_ppi_data_scaling_v1"
mode="${1:?phase required}"
shift
mkdir -p "$run_dir/logs" "$run_dir/runtime/tmp" "$run_dir/runtime/cache"
export APPTAINER_TMPDIR="$run_dir/runtime/tmp"
export APPTAINER_CACHEDIR="$run_dir/runtime/cache"
if [[ "$mode" == prepare ]]; then
  exec apptainer exec --no-mount bind-paths,home,cwd,hostfs --no-home --containall --cleanenv --pwd /output \
    --bind "$repo_dir:/repo:ro,$run_dir:/output:rw,$run_dir/scripts:/code:ro" \
    --env PYTHONDONTWRITEBYTECODE=1,PYTHONPATH=/code,OPENBLAS_NUM_THREADS=1 \
    "$repo_dir/containers/images/ipin-data-arm64_0.1.2.sif" python /code/prepare_inputs.py
fi
method="${1:?method required}"
shift
case "$method" in
  plm) bundle="$repo_dir/benchmark/plm_interact/runs/original-v1/scorer_bundle"; image=plm-interact-native-arm64-v1.sif ;;
  dscript_original) bundle="$repo_dir/benchmark/dscript/runs/original-v1/scorer_bundle"; image=dscript-native-arm64-v1.sif ;;
  dscript_retrained) bundle="$repo_dir/benchmark/dscript/runs/retrained-v1/scorer_bundle"; image=dscript-native-arm64-v1.sif ;;
  rapppid_original) bundle="$repo_dir/benchmark/rapppid/runs/original-v1/scorer_bundle"; image=rapppid-native-arm64-v1.sif ;;
  rapppid_recovery) bundle="$repo_dir/benchmark/rapppid/runs/recovery-test-v1/scorer_bundle"; image=rapppid-native-arm64-v1.sif ;;
  tuna) bundle="$repo_dir/benchmark/tuna/runs/scorer_bundle"; image=tuna-arm64-v1.sif ;;
  partner) bundle="$repo_dir/benchmark/partner_conditioned_residue_v1/runs/scorer_bundle"; image=tuna-arm64-v1.sif ;;
  sprint) bundle="$repo_dir/benchmark/sprint/runs/original-v1/scorer_bundle"; image=sprint-native-arm64-v1.sif ;;
  evaluation) bundle="$repo_dir/benchmark/tuna/runs/scorer_bundle"; image=tuna-arm64-v1.sif ;;
  *) echo "Unknown method: $method" >&2; exit 2 ;;
esac
runtime_path=/code:/bundle/code:/opt/tuna/vendor:/opt/rapppid/runtime:/opt/rapppid/upstream/rapppid
extra_binds=()
nv=(--nv)
case "$mode" in
  shard)
    worker_rank="${SLURM_PROCID:-0}"
    worker_count="${SLURM_NTASKS:-1}"
    printf -v rank_name 'rank-%03d' "$worker_rank"
    output_dir="$run_dir/shards/$method/$rank_name"
    entry=score_shards.py
    args=("$method" --rank "$worker_rank" --workers "$worker_count")
    if [[ "$method" == dscript* ]]; then extra_binds+=(--bind "$run_dir/features/$method:/extension:ro"); fi ;;
  features)
    output_dir="$run_dir/features/$method"; entry=extend_dscript.py; args=("$method") ;;
  fast)
    output_dir="$run_dir/predictions/$method"; entry=score_fast.py; args=("$method")
    extra_binds+=(--bind "$study_dir/runs:/scaled:ro,$run_dir/legacy:/legacy:ro,$run_dir/data:/data:ro") ;;
  sprint)
    output_dir="$run_dir/sprint"; entry=score_sprint.py; args=(); nv=() ;;
  sprint_inputs)
    output_dir="$run_dir/sprint"; entry=prepare_sprint.py; args=(); nv=(); image=tuna-arm64-v1.sif ;;
  evaluate)
    output_dir="$run_dir/results"; entry=evaluate.py; args=()
    extra_binds+=(--bind "$run_dir:/experiment:ro,$study_dir/private/test:/truth:ro,$study_dir/data:/studydata:ro,$study_dir/scripts:/metrics:ro")
    runtime_path=/code:/metrics:/native:/opt/tuna/vendor ;;
  preflight)
    output_dir="$run_dir/preflight"; entry=preflight.py; args=()
    extra_binds+=(--bind "$run_dir:/experiment:ro,$study_dir/scripts:/metrics:ro")
    runtime_path=/code:/metrics:/native:/opt/tuna/vendor ;;
  *) echo "Unknown phase: $mode" >&2; exit 2 ;;
esac
mkdir -p "$output_dir/tmp"
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec "${nv[@]}" --no-mount bind-paths,home,cwd,hostfs --no-home --containall --cleanenv --pwd /output \
  --bind "$run_dir/scripts:/code:ro,$run_dir/data:/data:ro,$bundle:/bundle:ro,$output_dir:/output:rw" \
  --bind "$repo_dir/benchmark/tuna/scripts:/native:ro,$repo_dir/benchmark/tuna/upstream/TUnA:/upstream:ro" \
  "${extra_binds[@]}" \
  --env "PYTHONPATH=$runtime_path,PYTHONDONTWRITEBYTECODE=1,PYTHONUNBUFFERED=1,UCX_VFS_ENABLE=n,OMP_NUM_THREADS=8,OPENBLAS_NUM_THREADS=1,NVIDIA_TF32_OVERRIDE=0,CUBLAS_WORKSPACE_CONFIG=:4096:8,CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0},HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,HF_HOME=/output/.cache/huggingface,TRANSFORMERS_CACHE=/output/.cache/transformers,XDG_CACHE_HOME=/output/.cache,MPLCONFIGDIR=/output/.cache/matplotlib,TMPDIR=/output/tmp,TUNA_UPSTREAM_DIR=/upstream/results/bernett/TUnA" \
  "$repo_dir/benchmark/containers/images/$image" python3 /native/gpu_guard.py "/code/$entry" "${args[@]}" "$@"
