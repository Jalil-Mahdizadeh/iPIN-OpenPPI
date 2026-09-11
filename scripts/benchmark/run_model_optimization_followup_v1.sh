#!/usr/bin/env bash
# Separate, one-attempt follow-up. Never reset the original final-test ledger.
set -euo pipefail
umask 077
task_project=/nobackup/proj/disk/theo-storage/personal/jalil/iPIN-OpenPPI
task_private=$task_project/.private/model_optimization_followup_v1
task_bundle=$task_private/bundle
task_custody=$task_project/.private/pair_level_pu_r_benchmark_artifacts_v1
task_followup=$task_custody/followup_evaluations/model_optimization_followup_v1
task_original=$task_project/.private/protected_final_test_v1
task_package=$task_project/data/canonical/pair_level_pu_r_benchmark_artifacts_v1
task_image=$task_project/containers/images/ipin-model-arm64_0.1.0.sif
task_phase=${1:?Specify preflight, open, score, import-baseline, freeze-predictions, reserve, evaluate, or publish}
test -f "$task_bundle/SCORER_FREEZE.json"
task_image_digest=$(sha256sum "$task_image")
test "${task_image_digest%% *}" = c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91
task_original_digest=$(sha256sum "$task_custody/protected_evaluation_ledger.json")
test "${task_original_digest%% *}" = e23a6a8980d3e9d148a40be8e9b3d1316ff1c2c6ed8f7f03ab2bd899b777914f
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --cleanenv --containall --no-home
      --no-mount bind-paths,proc,sys,home,cwd,hostfs --pwd /)
runtime=(env OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 UCX_VFS_ENABLE=n PYTHONDONTWRITEBYTECODE=1)
entry=(python /bundle/code/protected_final_guard_v1.py /bundle/code/model_optimization_followup_core_v1.py)
case "$task_phase" in
  preflight)
    test ! -e "$task_followup/ledger.json"
    mkdir -m 700 "$task_private/preflight"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" "$task_image" "${runtime[@]}" \
      python /bundle/code/protected_final_guard_v1.py --probe </dev/null \
      >"$task_private/preflight/GUARD.json" 2>"$task_private/preflight/GUARD.stderr.log"
    for task_test in test_protected_final_test_v1.py test_model_optimization_followup_v1.py test_model_optimization_followup_publication_v1.py; do
      "${base[@]}" --bind "$task_bundle:/bundle:ro" "$task_image" "${runtime[@]}" \
        python /bundle/code/protected_final_guard_v1.py "/bundle/code/$task_test" </dev/null \
        >"$task_private/preflight/$task_test.stdout.log" 2>"$task_private/preflight/$task_test.stderr.log"
    done
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/preflight:/output:rw" \
      "$task_image" "${runtime[@]}" "${entry[@]}" qualify </dev/null \
      >"$task_private/preflight/SCORER.stdout.log" 2>"$task_private/preflight/SCORER.stderr.log"
    ;;
  open)
    test ! -e "$task_followup/ledger.json"
    test -f "$task_private/preflight/SCORER_QUALIFICATION.json"
    mkdir -m 700 "$task_private/session"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" \
      --bind "$task_package/sealed/protected_candidates.cms:/cipher.cms:ro" \
      --bind "$task_project/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_candidates_certificate.pem:/certificate.pem:ro" \
      --bind "$task_custody/protected_candidates_private.pem:/key.pem:ro" \
      --bind "$task_private/session:/output:rw" "$task_image" "${runtime[@]}" "${entry[@]}" open </dev/null \
      >"$task_private/OPEN.stdout.log" 2>"$task_private/OPEN.stderr.log"
    ;;
  score)
    test ! -e "$task_followup/ledger.json"
    mkdir -m 700 "$task_private/predictions"
    mkdir -m 700 "$task_private/predictions/candidate"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/session:/session:ro" \
      --bind "$task_private/predictions/candidate:/output:rw" \
      "$task_image" "${runtime[@]}" "${entry[@]}" score </dev/null \
      >"$task_private/SCORE.stdout.log" 2>"$task_private/SCORE.stderr.log"
    ;;
  import-baseline)
    test ! -e "$task_followup/ledger.json"
    mkdir -m 700 "$task_private/predictions/baseline"
    baseline_mounts=(--bind "$task_original/freeze/PREDICTION_FREEZE.json:/original_predictions/PREDICTION_FREEZE.json:ro")
    for task_scorer in lightweight_esm2_150m_linear__linear_lr3e-4 seed20260803 seed20260817 seed20260831; do
      baseline_mounts+=(--bind "$task_original/predictions/$task_scorer:/original_predictions/$task_scorer:ro")
    done
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/session:/session:ro" \
      --bind "$task_private/predictions/candidate:/candidate:ro" "${baseline_mounts[@]}" \
      --bind "$task_private/predictions/baseline:/output:rw" \
      "$task_image" "${runtime[@]}" "${entry[@]}" import-baseline </dev/null \
      >"$task_private/BASELINE.stdout.log" 2>"$task_private/BASELINE.stderr.log"
    ;;
  freeze-predictions)
    test ! -e "$task_followup/ledger.json"
    mkdir -m 700 "$task_private/freeze"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/session:/session:ro" \
      --bind "$task_private/predictions:/predictions:ro" --bind "$task_private/freeze:/output:rw" \
      "$task_image" "${runtime[@]}" "${entry[@]}" freeze-predictions </dev/null \
      >"$task_private/FREEZE.stdout.log" 2>"$task_private/FREEZE.stderr.log"
    ;;
  reserve)
    mkdir -p -m 700 "$task_custody/followup_evaluations"
    mkdir -m 700 "$task_followup"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/freeze:/freeze:ro" \
      --bind "$task_custody/protected_evaluation_ledger.json:/original_ledger.json:ro" \
      --bind "$task_followup:/custody:rw" "$task_image" "${runtime[@]}" "${entry[@]}" reserve </dev/null \
      >"$task_private/RESERVE.stdout.log" 2>"$task_private/RESERVE.stderr.log"
    ;;
  evaluate)
    test -f "$task_followup/ledger.json"
    test ! -e "$task_followup/completion.json"
    mkdir -m 700 "$task_private/evaluation"
    "${base[@]}" --bind "$task_bundle:/bundle:ro" --bind "$task_private/session:/session:ro" \
      --bind "$task_private/predictions:/predictions:ro" --bind "$task_private/freeze:/freeze:ro" \
      --bind "$task_followup/ledger.json:/ledger.json:ro" \
      --bind "$task_package/sealed/protected_truth.cms:/cipher.cms:ro" \
      --bind "$task_project/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem:/certificate.pem:ro" \
      --bind "$task_custody/protected_truth_private.pem:/key.pem:ro" \
      --bind "$task_private/evaluation:/output:rw" "$task_image" "${runtime[@]}" "${entry[@]}" evaluate </dev/null \
      >"$task_private/EVALUATE.stdout.log" 2>"$task_private/EVALUATE.stderr.log"
    ;;
  publish)
    task_results=$task_project/artifacts/results/model_optimization_followup_v1
    mkdir -m 700 "$task_results"
    # Publication sees only frozen code, aggregate metadata and new custody;
    # no model states, candidate/score rows, truth packages or escrow keys.
    "${base[@]}" --bind "$task_bundle/code:/bundle/code:ro" \
      --bind "$task_private/evaluation/FOLLOWUP_TEST_RESULTS.json:/result.json:ro" \
      --bind "$task_private/freeze/PREDICTION_FREEZE.json:/prediction_freeze.json:ro" \
      --bind "$task_bundle/SCORER_FREEZE.json:/scorer_freeze.json:ro" \
      --bind "$task_followup/ledger.json:/ledger.json:ro" \
      --bind "$task_followup:/custody:rw" --bind "$task_results:/results:rw" \
      --bind "$task_project/artifacts/validation/protected_evaluation_receipts:/receipts:rw" \
      "$task_image" "${runtime[@]}" python /bundle/code/protected_final_guard_v1.py \
      /bundle/code/publish_model_optimization_followup_v1.py </dev/null \
      >"$task_private/PUBLISH.stdout.log" 2>"$task_private/PUBLISH.stderr.log"
    ;;
  *) printf 'Unknown follow-up phase\n' >&2; exit 2 ;;
esac
printf 'Fixed-ensemble follow-up phase completed: %s\n' "$task_phase"
