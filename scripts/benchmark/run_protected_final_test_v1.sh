#!/usr/bin/env bash
# Explicit staged operator. No whole-checkout bind; no automatic test retry.
set -euo pipefail
umask 077
final_root=/nobackup/proj/disk/theo-storage/personal/jalil/iPIN-OpenPPI
final_bundle=$final_root/artifacts/runs/protected_final_test_v1/frozen_bundle
final_private=$final_root/.private/protected_final_test_v1
final_custody=$final_root/.private/pair_level_pu_r_benchmark_artifacts_v1
final_package=$final_root/data/canonical/pair_level_pu_r_benchmark_artifacts_v1
final_image=$final_root/containers/images/ipin-model-arm64_0.1.0.sif
phase=${1:?Specify preflight, open, score, freeze-predictions, reserve, or evaluate}
mkdir -p -m 700 "$final_private"
base=(env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH
      apptainer exec --cleanenv --containall --no-home
      --no-mount bind-paths,proc,sys,home,cwd,hostfs
      --bind "$final_bundle:/bundle:ro" --pwd /)
entry=(python /bundle/code/protected_final_guard_v1.py /bundle/code/protected_final_core_v1.py)
runtime=(env OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 UCX_VFS_ENABLE=n PYTHONDONTWRITEBYTECODE=1)
case "$phase" in
  preflight)
    mkdir -m 700 "$final_private/preflight"
    "${base[@]}" "$final_image" "${runtime[@]}" python /bundle/code/protected_final_guard_v1.py --probe </dev/null >"$final_private/preflight/GUARD.json" 2>"$final_private/preflight/GUARD.stderr.log"
    "${base[@]}" "$final_image" "${runtime[@]}" python /bundle/code/protected_final_guard_v1.py /bundle/code/test_protected_final_test_v1.py </dev/null >"$final_private/preflight/SYNTHETIC.stdout.log" 2>"$final_private/preflight/SYNTHETIC.stderr.log"
    "${base[@]}" --bind "$final_private/preflight:/output:rw" "$final_image" "${runtime[@]}" "${entry[@]}" qualify </dev/null >"$final_private/preflight/SCORER.stdout.log" 2>"$final_private/preflight/SCORER.stderr.log"
    ;;
  open)
    test ! -e "$final_custody/protected_evaluation_ledger.json"
    test ! -e "$final_custody/protected_evaluation_completion.json"
    test -f "$final_private/preflight/SCORER_QUALIFICATION.json"
    mkdir -m 700 "$final_private/session"
    "${base[@]}" --bind "$final_package/sealed/protected_candidates.cms:/cipher.cms:ro" \
      --bind "$final_root/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_candidates_certificate.pem:/certificate.pem:ro" \
      --bind "$final_custody/protected_candidates_private.pem:/key.pem:ro" \
      --bind "$final_private/session:/output:rw" "$final_image" "${runtime[@]}" "${entry[@]}" open </dev/null >"$final_private/OPEN.stdout.log" 2>"$final_private/OPEN.stderr.log"
    ;;
  score)
    mkdir -m 700 "$final_private/predictions"
    "${base[@]}" --bind "$final_private/session:/session:ro" --bind "$final_private/predictions:/output:rw" \
      "$final_image" "${runtime[@]}" "${entry[@]}" score </dev/null >"$final_private/SCORE.stdout.log" 2>"$final_private/SCORE.stderr.log"
    ;;
  freeze-predictions)
    mkdir -m 700 "$final_private/freeze"
    "${base[@]}" --bind "$final_private/session:/session:ro" --bind "$final_private/predictions:/predictions:ro" \
      --bind "$final_private/freeze:/output:rw" "$final_image" "${runtime[@]}" "${entry[@]}" freeze-predictions </dev/null >"$final_private/FREEZE.stdout.log" 2>"$final_private/FREEZE.stderr.log"
    ;;
  reserve)
    # Parent is necessary for atomic O_EXCL creation. Mask every escrow key;
    # this operator receives only the prediction freeze and ledger directory.
    "${base[@]}" --bind "$final_private/freeze:/freeze:ro" --bind "$final_custody:/custody:rw" \
      --bind /dev/null:/custody/development_release_private.pem:ro \
      --bind /dev/null:/custody/protected_candidates_private.pem:ro \
      --bind /dev/null:/custody/protected_truth_private.pem:ro \
      "$final_image" "${runtime[@]}" "${entry[@]}" reserve </dev/null >"$final_private/RESERVE.stdout.log" 2>"$final_private/RESERVE.stderr.log"
    ;;
  evaluate)
    test -f "$final_custody/protected_evaluation_ledger.json"
    test ! -e "$final_custody/protected_evaluation_completion.json"
    mkdir -m 700 "$final_private/evaluation"
    "${base[@]}" --bind "$final_private/session:/session:ro" --bind "$final_private/predictions:/predictions:ro" \
      --bind "$final_private/freeze:/freeze:ro" --bind "$final_custody/protected_evaluation_ledger.json:/ledger.json:ro" \
      --bind "$final_package/sealed/protected_truth.cms:/cipher.cms:ro" \
      --bind "$final_root/governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem:/certificate.pem:ro" \
      --bind "$final_custody/protected_truth_private.pem:/key.pem:ro" \
      --bind "$final_private/evaluation:/output:rw" "$final_image" "${runtime[@]}" "${entry[@]}" evaluate </dev/null >"$final_private/EVALUATE.stdout.log" 2>"$final_private/EVALUATE.stderr.log"
    ;;
  *) printf 'Unknown phase\n' >&2; exit 2 ;;
esac
printf 'Protected final-test phase completed: %s\n' "$phase"
