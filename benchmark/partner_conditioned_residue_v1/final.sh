#!/usr/bin/env bash
# Development selection and a new, isolated one-attempt follow-up comparison.
set -euo pipefail
umask 077
study_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bench_root=$(dirname -- "$study_root")
repo_root=$(dirname -- "$bench_root")
python3 -B "$study_root/scripts/freeze.py" verify
bash "$study_root/run.sh" python /code/gpu_guard.py /code/selection.py \
  > "$study_root/logs/selection.log" 2>&1
cp -- "$study_root/runs/DEVELOPMENT.md" "$study_root/results/DEVELOPMENT.md"
cp -- "$study_root/runs/SELECTION.json" "$study_root/results/SELECTION.json"
if [[ -f "$study_root/runs/NO_PROMOTION.json" ]]; then
  cp -- "$study_root/runs/NO_PROMOTION.json" "$study_root/results/NO_PROMOTION.json"
  python3 -B "$study_root/scripts/publish_status.py" no_promotion
  exit 0
fi
study_bundle="$study_root/runs/scorer_bundle"
study_private="$study_root/private"
export APPTAINER_CACHEDIR="$bench_root/containers/cache/apptainer"
export APPTAINER_TMPDIR="$bench_root/containers/tmp/runtime"
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --nv --cleanenv --containall --no-home
      --no-mount bind-paths,home,cwd,hostfs --pwd /output
      --bind "$study_bundle:/bundle:ro" --bind "$study_bundle/code:/code:ro")
runtime=(env UCX_VFS_ENABLE=n PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
         OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
         XDG_CACHE_HOME=/output/.cache MPLCONFIGDIR=/output/.cache/matplotlib TMPDIR=/output)
entry=(python /code/gpu_guard.py /code/comparison.py)
image="$bench_root/containers/images/tuna-arm64-v1.sif"
mkdir "$study_private/session"
"${base[@]}" --bind "$repo_root/.private/model_optimization_followup_v1/session:/previous_session:ro" \
  --bind "$study_private/session:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" open \
  > "$study_root/logs/test-open.log" 2>&1
mkdir "$study_private/predictions"
"${base[@]}" --bind "$study_private/session:/session:ro" --bind "$study_private/predictions:/output:rw" \
  "$image" "${runtime[@]}" "${entry[@]}" score > "$study_root/logs/test-score.log" 2>&1
mkdir "$study_private/references"
"${base[@]}" --bind "$study_private/session:/session:ro" --bind "$study_private/predictions:/predictions:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/predictions/lightweight_esm2_150m_linear__linear_lr3e-4:/original_baseline:ro" \
  --bind "$repo_root/.private/protected_final_test_v1/freeze/PREDICTION_FREEZE.json:/baseline_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/predictions/candidate/esm2_150m__residual_wide__epoch04_ensemble3:/original_optimized:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/freeze/PREDICTION_FREEZE.json:/optimized_freeze.json:ro" \
  --bind "$bench_root/tuna/private/predictions:/original_tuna:ro" \
  --bind "$bench_root/tuna/private/predictions/PREDICTIONS.json:/tuna_predictions_manifest.json:ro" \
  --bind "$study_private/references:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" references \
  > "$study_root/logs/test-references.log" 2>&1
mkdir "$study_private/freeze"
"${base[@]}" --bind "$study_private/session:/session:ro" --bind "$study_private/predictions:/predictions:ro" \
  --bind "$study_private/references:/references:ro" --bind "$study_private/freeze:/output:rw" \
  "$image" "${runtime[@]}" "${entry[@]}" freeze > "$study_root/logs/test-freeze.log" 2>&1
mkdir "$study_private/evaluation"
"${base[@]}" --bind "$study_private/session:/session:ro" --bind "$study_private/predictions:/predictions:ro" \
  --bind "$study_private/references:/references:ro" --bind "$study_private/freeze:/freeze:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json:/historical_scorer_freeze.json:ro" \
  --bind "$repo_root/.private/model_optimization_followup_v1/evaluation/FOLLOWUP_TEST_RESULTS.json:/historical_results.json:ro" \
  --bind "$bench_root/tuna/results/RESULTS.json:/historical_tuna_results.json:ro" \
  --bind "$repo_root/data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms:/cipher.cms:ro" \
  --bind "$repo_root/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem:/certificate.pem:ro" \
  --bind "$repo_root/.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem:/key.pem:ro" \
  --bind "$study_private/evaluation:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" evaluate \
  > "$study_root/logs/test-evaluate.log" 2>&1
"${base[@]}" --bind "$study_private/evaluation/RESULTS.json:/aggregate/RESULTS.json:ro" \
  --bind "$study_root/results:/output:rw" "$image" "${runtime[@]}" "${entry[@]}" publish \
  > "$study_root/logs/test-publish.log" 2>&1
python3 -B "$study_root/scripts/publish_status.py" complete
