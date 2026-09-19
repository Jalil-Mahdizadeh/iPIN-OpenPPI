#!/usr/bin/env bash
# Automatic follow-on: no historical ledger writes and no test-guided refitting.
set -euo pipefail
umask 077
tuna_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$tuna_root")
repo_root=$(dirname -- "$bench_root")
python3 "$tuna_root/scripts/freeze_execution.py" verify
test "$(sha256sum "$bench_root/containers/images/tuna-arm64-v1.sif" | cut -d ' ' -f1)" = 98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1
bash "$tuna_root/run.sh" env UCX_VFS_ENABLE=n python /code/select_and_freeze.py \
  > "$tuna_root/logs/selection-and-scorer-freeze.log" 2>&1
tuna_bundle="$tuna_root/runs/scorer_bundle"
tuna_private="$tuna_root/private"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/runtime"
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --nv --cleanenv --containall --no-home
      --no-mount bind-paths,home,cwd,hostfs --pwd /output
      --bind "$tuna_bundle:/bundle:ro" --bind "$tuna_bundle/code:/code:ro")
runtime=(env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
         OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
         XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output)
entry=(python /code/gpu_guard.py /code/comparison.py)
image="$bench_root/containers/images/tuna-arm64-v1.sif"
mkdir "$tuna_private/session"
"${base[@]}" --bind "$repo_root/.private/model_optimization_followup_v1/session:/previous_session:ro" \
  --bind "$tuna_private/session:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" open \
  > "$tuna_root/logs/final-open.log" 2>&1
mkdir "$tuna_private/predictions"
"${base[@]}" --bind "$tuna_private/session:/session:ro" --bind "$tuna_private/predictions:/output:rw" \
  "$image" "${runtime[@]}" "${entry[@]}" score > "$tuna_root/logs/final-score.log" 2>&1
mkdir "$tuna_private/references"
"${base[@]}" --bind "$tuna_private/session:/session:ro" --bind "$tuna_private/predictions:/predictions:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/predictions/lightweight_esm2_150m_linear__linear_lr3e-4:/original_baseline:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json:/baseline_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/predictions/candidate/esm2_150m__residual_wide__epoch04_ensemble3:/original_optimized:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json:/optimized_freeze.json:ro" \
  --bind "$tuna_private/references:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" references \
  > "$tuna_root/logs/final-reference-import.log" 2>&1
mkdir "$tuna_private/freeze"
"${base[@]}" --bind "$tuna_private/session:/session:ro" --bind "$tuna_private/predictions:/predictions:ro" \
  --bind "$tuna_private/references:/references:ro" --bind "$tuna_private/freeze:/output:rw" \
  "$image" "${runtime[@]}" "${entry[@]}" freeze > "$tuna_root/logs/final-prediction-freeze.log" 2>&1
mkdir "$tuna_private/evaluation"
"${base[@]}" --bind "$tuna_private/session:/session:ro" --bind "$tuna_private/predictions:/predictions:ro" \
  --bind "$tuna_private/references:/references:ro" --bind "$tuna_private/freeze:/freeze:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json:/historical_scorer_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json:/historical_results.json:ro" \
  --bind "$repo_root/data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms:/cipher.cms:ro" \
  --bind "$repo_root/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem:/certificate.pem:ro" \
  --bind "$repo_root/.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem:/key.pem:ro" \
  --bind "$tuna_private/evaluation:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" evaluate \
  > "$tuna_root/logs/final-evaluate.log" 2>&1
mkdir "$tuna_root/results"
# Publication receives aggregates only, no keys/candidates/predictions.
"${base[@]}" --bind "$tuna_private/evaluation/RESULTS.json:/aggregate/RESULTS.json:ro" \
  --bind "$tuna_root/results:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" publish \
  > "$tuna_root/logs/final-publish.log" 2>&1
python3 "$bench_root/workspace_guard.py" verify > "$tuna_root/logs/final-repository-scope.log" 2>&1
