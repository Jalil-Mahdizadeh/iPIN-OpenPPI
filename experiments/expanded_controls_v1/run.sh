#!/usr/bin/env bash
set -euo pipefail
umask 077
study_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo_dir=$(cd -- "$study_dir/../.." && pwd -P)
scaled_dir="$repo_dir/experiments/human_ppi_data_scaling_v1"
reference_dir="$repo_dir/experiments/test2_frozen_competitors_v1/results"
mode="$1"
shift
mkdir -p "$study_dir/logs" "$study_dir/work" "$study_dir/features" "$study_dir/runtime/tmp" "$study_dir/runtime/cache"
export APPTAINER_TMPDIR="$study_dir/runtime/tmp"
export APPTAINER_CACHEDIR="$study_dir/runtime/cache"
image="$repo_dir/benchmark/containers/images/tuna-arm64-v1.sif"
binds=(--bind "$study_dir/scripts:/code:ro,$repo_dir/src:/library:ro,$repo_dir/benchmark/tuna/scripts:/native:ro")
binds+=(--bind "$study_dir/PROTOCOL.json:/experiment/PROTOCOL.json:ro")
nv=(--nv)
if [[ -f "$study_dir/INPUT_FREEZE.json" ]]; then
  binds+=(--bind "$study_dir/INPUT_FREEZE.json:/experiment/INPUT_FREEZE.json:ro")
fi
if [[ -f "$study_dir/IMPLEMENTATION_FREEZE.json" ]]; then
  binds+=(--bind "$study_dir/IMPLEMENTATION_FREEZE.json:/experiment/IMPLEMENTATION_FREEZE.json:ro")
  binds+=(--bind "$study_dir/scripts:/experiment/scripts:ro,$study_dir/tests:/experiment/tests:ro,$study_dir/run.sh:/experiment/run.sh:ro")
fi
case "$mode" in
  prepare)
    image="$repo_dir/containers/images/ipin-data-arm64_0.1.2.sif"
    nv=()
    output="$study_dir"
    binds+=(--bind "$repo_dir:/repo:ro") ;;
  sequence_features)
    output="$study_dir/features"
    binds+=(--bind "$study_dir/data/sequences.json:/sequences/sequences.json:ro,$study_dir/data/train:/train:ro")
    binds+=(--bind "$repo_dir/artifacts/embeddings/model_governance_and_baseline_training_protocol_v1/esm2_150m:/raw:ro")
    binds+=(--bind "$scaled_dir/runs/pooled_features.npy:/pooled/pooled_features.npy:ro,$repo_dir/.private/frozen_pair_models_v1/bundle/encoder:/encoder:ro") ;;
  alignment)
    image="$repo_dir/containers/images/ipin-data-arm64_0.1.2.sif"
    nv=()
    output="$study_dir/features"
    binds+=(--bind "$study_dir/data/sequences.json:/sequences/sequences.json:ro")
    binds+=(--bind "$repo_dir/artifacts/cache/tools/mmseqs2/18-8cc5c/mmseqs/bin:/mmseqs:ro,$study_dir/work:/work:rw") ;;
  qualify)
    output="$study_dir/validation"
    binds+=(--bind "$study_dir/tests:/tests:ro,$scaled_dir/scripts:/metrics:ro") ;;
  train_unary)
    output="$study_dir/training"
    binds+=(--bind "$study_dir/data/sequences.json:/sequences/sequences.json:ro")
    binds+=(--bind "$study_dir/data/train:/train:ro,$study_dir/features:/features:ro") ;;
  score)
    output="$study_dir/predictions"
    binds+=(--bind "$study_dir/data/sequences.json:/sequences/sequences.json:ro")
    binds+=(--bind "$study_dir/data/candidates:/candidates:ro,$study_dir/features:/features:ro,$study_dir/training:/training:ro")
    binds+=(--bind "$scaled_dir/runs/frozen:/selected/frozen:ro,$scaled_dir/runs/SCORER_FREEZE.json:/selected/SCORER_FREEZE.json:ro")
    binds+=(--bind "$reference_dir/predictions:/reference_predictions:ro,$reference_dir/PREDICTION_FREEZE.json:/reference_predictions/FREEZE.json:ro")
    binds+=(--bind "$repo_dir/benchmark/tuna/upstream/TUnA:/upstream:ro,$repo_dir/benchmark/tuna/weights:/weights:ro") ;;
  evaluate|diagnostics)
    if [[ "$mode" == evaluate ]]; then output="$study_dir/results"; else output="$study_dir/results/diagnostics"; fi
    binds+=(--bind "$study_dir/data/sequences.json:/sequences/sequences.json:ro")
    binds+=(--bind "$study_dir/data/candidates:/candidates:ro,$study_dir/features:/features:ro,$study_dir/predictions:/predictions:ro")
    binds+=(--bind "$scaled_dir/private/test:/truth:ro,$scaled_dir/data/development:/devtruth:ro")
    binds+=(--bind "$reference_dir:/reference:ro,$scaled_dir/scripts:/metrics:ro") ;;
  validate)
    output="$study_dir/validation"
    binds+=(--bind "$repo_dir:/repo:ro,$study_dir:/study:ro,$scaled_dir/scripts:/metrics:ro") ;;
  *) echo "Unknown phase: $mode" >&2; exit 2 ;;
esac
mkdir -p "$output/tmp"
gpu_device=$(printenv CUDA_VISIBLE_DEVICES || true)
if [[ -z "$gpu_device" ]]; then gpu_device=0; fi
exec env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec "${nv[@]}" --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --pwd /output "${binds[@]}" --bind "$output:/output:rw" \
  --env "PYTHONPATH=/code:/library:/native:/metrics:/opt/tuna/vendor,PYTHONDONTWRITEBYTECODE=1,PYTHONUNBUFFERED=1,OMP_NUM_THREADS=8,OPENBLAS_NUM_THREADS=1,UCX_VFS_ENABLE=n,CUBLAS_WORKSPACE_CONFIG=:4096:8,NVIDIA_TF32_OVERRIDE=0,CUDA_VISIBLE_DEVICES=$gpu_device,HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,TUNA_UPSTREAM_DIR=/upstream/results/bernett/TUnA,XDG_CACHE_HOME=/output/.cache,MPLCONFIGDIR=/output/.cache/matplotlib,TMPDIR=/output/tmp" \
  "$image" python "/code/$mode.py" "$@"
