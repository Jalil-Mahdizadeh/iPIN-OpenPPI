#!/usr/bin/env bash
# Execute only after all frozen candidate-only scoring shards complete.
set -euo pipefail
umask 077
dscript_root=${DSCRIPT_BENCHMARK_ROOT:?Set by submit_retrained.sh}
bench_root=$(dirname -- "$dscript_root")
repo_root=$(dirname -- "$bench_root")
private="$dscript_root/private/retrained-v1"
bundle="$dscript_root/runs/retrained-v1/scorer_bundle"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/dscript-v1"
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --nv --cleanenv --containall --no-home --no-mount "bind-paths,home,cwd,hostfs" --pwd /output
      --bind "$bundle:/bundle:ro" --bind "$bundle/code:/code:ro")
runtime=(env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NVIDIA_TF32_OVERRIDE=0
         OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
         XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output)
entry=(python /code/gpu_guard.py /code/comparison.py)
image="$bench_root/containers/images/dscript-native-arm64-v1.sif"
mkdir "$private/predictions"
"${base[@]}" --bind "$private/session:/session:ro" --bind "$private/shards:/shards:ro" \
  --bind "$private/predictions:/output:rw" "$image" "${runtime[@]}" \
  python /code/gpu_guard.py /code/score_shard.py merge --workers 4 > "$dscript_root/logs/retrained-merge.log" 2>&1
mkdir "$private/references"
"${base[@]}" --bind "$private/session:/session:ro" --bind "$private/predictions:/predictions:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/predictions/lightweight_esm2_150m_linear__linear_lr3e-4:/original_baseline:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json:/baseline_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/predictions/candidate/esm2_150m__residual_wide__epoch04_ensemble3:/original_optimized:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json:/optimized_freeze.json:ro" \
  --bind "$dscript_root/private/original-v1/predictions:/original_dscript:ro" \
  --bind "$private/references:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" references \
  > "$dscript_root/logs/retrained-reference-import.log" 2>&1
mkdir "$private/freeze"
"${base[@]}" --bind "$private/session:/session:ro" --bind "$private/predictions:/predictions:ro" \
  --bind "$private/references:/references:ro" --bind "$private/freeze:/output:rw" \
  "$image" "${runtime[@]}" "${entry[@]}" freeze > "$dscript_root/logs/retrained-prediction-freeze.log" 2>&1
mkdir "$private/evaluation"
"${base[@]}" --bind "$private/session:/session:ro" --bind "$private/predictions:/predictions:ro" \
  --bind "$private/references:/references:ro" --bind "$private/freeze:/freeze:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json:/historical_scorer_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json:/historical_results.json:ro" \
  --bind "$repo_root/data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms:/cipher.cms:ro" \
  --bind "$repo_root/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem:/certificate.pem:ro" \
  --bind "$repo_root/.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem:/key.pem:ro" \
  --bind "$dscript_root/results/original-v1/RESULTS.json:/original_results.json:ro" \
  --bind "$private/evaluation:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" evaluate \
  > "$dscript_root/logs/retrained-evaluate.log" 2>&1
mkdir -p "$dscript_root/results"
mkdir "$dscript_root/results/retrained-v1"
"${base[@]}" --bind "$private/evaluation/RESULTS.json:/aggregate/RESULTS.json:ro" \
  --bind "$dscript_root/results/retrained-v1:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" publish \
  > "$dscript_root/logs/retrained-publish.log" 2>&1
# Stop after this completed retraining comparison; no additional model is queued.
