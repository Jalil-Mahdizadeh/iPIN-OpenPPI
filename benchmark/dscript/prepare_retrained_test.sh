#!/usr/bin/env bash
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Use submit_retrained.sh}
bench_root=$(dirname -- "$dscript_root")
repo_root=$(dirname -- "$bench_root")
run="$dscript_root/runs/retrained-v1"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --nv --cleanenv --containall --no-home --no-mount "bind-paths,home,cwd,hostfs" --pwd /output)
runtime=(env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0
         OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?}"
         XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output)
image="$bench_root/containers/images/dscript-native-arm64-v1.sif"
mkdir "$run/selection_output"
"${base[@]}" --bind "$run/code:/code:ro" --bind "$run/data:/data:ro" --bind "$run/residue_cache:/cache:ro" \
  --bind "$run/training:/training:ro" --bind "$run/TRAINING_FREEZE.json:/protocol.json:ro" \
  --bind "$run/selection_output:/output:rw" "$image" "${runtime[@]}" python /code/gpu_guard.py /code/select_and_freeze.py \
  > "$dscript_root/logs/retrained-selection-and-freeze.log" 2>&1
test ! -e "$run/scorer_bundle"
mv -T "$run/selection_output/scorer_bundle" "$run/scorer_bundle"
private="$dscript_root/private/retrained-v1"
mkdir -p "$private"
mkdir "$private/session"
"${base[@]}" --bind "$run/scorer_bundle:/bundle:ro" --bind "$run/scorer_bundle/code:/code:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/session:/previous_session:ro" \
  --bind "$private/session:/output:rw" "$image" "${runtime[@]}" \
  python /code/gpu_guard.py /code/comparison.py open > "$dscript_root/logs/retrained-open-session.log" 2>&1
