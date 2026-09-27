# Validation record

[VALIDATION.json](VALIDATION.json) records the passed final readback. It checks
7,547,402 development/test candidate rows, 17 predictors, seven primary macro
views, and 1,089 reported point/interval/contrast summaries. All 54 frozen
historical parent files are unchanged. Training pairs have no exact candidate
overlap with evaluation pairs.

The synthetic qualification passed eleven tests. The independent macro
bootstrap oracle differs by at most 2.22e-16. Real-data exhaustive transfer
checks enumerate every train2 positive edge in both orientations for fixed
candidate fixtures, and match all four accelerated kernels exactly. Feature
row identities, raw embedding replay, model freezing and prediction hashes are
recorded in the compact manifests here.

Existing selected-31k test2 points and all 2,000 paired reference draws replay
exactly. Independent within-anchor points and checked quartet-bootstrap draws
also match exactly. Bootstrap interval readback and the remaining numerical
checks retain an absolute tolerance of 1e-12.

## Full-panel summation-order audit

The original frozen [validator](../scripts/validate.py) stopped when comparing
full-panel P/U concordance at an absolute tolerance of 1e-12. All 204 full-panel
predictor/cohort comparisons were audited in
[POINT_PRECISION_AUDIT.json](POINT_PRECISION_AUDIT.json). The largest difference
was 1.491373691209219e-11.

The published metric obtains total U weight from the last entry of a sorted
cumulative sum; the independent oracle divides by a NumPy sum. These FP64
summation orders yield slightly different totals on panels with about a million
rows. Applying the ratio of those totals explains the discrepancies to within
4.2521541843143495e-14. A higher-precision calculation on the worst case places
both results within 9.01e-12 of the reference value.

The [numerical addendum](NUMERICAL_VALIDATION_ADDENDUM.json) preserves the
original validator and records the hash of a separate
[final validator](../scripts/validate_final.py). Only its independent full-panel
point comparison uses 1e-10; other checks retain 1e-12. It also verifies the
precision-audit hash and bounds. No protocol, fitted model, prediction, metric,
bootstrap draw or interval was changed to resolve this check. The initial
failure remains in the local `logs/validate.log`; the final pass is in
`logs/validate_final.log`.

## Repeat the final readback

With the original local artifacts and container available, run the following
from the repository root. A fresh output directory avoids replacing the
recorded validation. The original frozen `run.sh validate` invokes the original
1e-12 validator; the command below invokes the documented final version.

```bash
repo_dir=$(pwd -P)
study_dir="$repo_dir/experiments/expanded_controls_v1"
mkdir -p "$study_dir/work"
validation_dir=$(mktemp -d "$study_dir/work/validation-readback.XXXXXX")
env -u APPTAINER_BIND -u APPTAINER_BINDPATH -u SINGULARITY_BIND -u SINGULARITY_BINDPATH \
  apptainer exec --cleanenv --containall --no-home --no-mount bind-paths,home,cwd,hostfs \
  --pwd /output \
  --bind "$repo_dir:/repo:ro,$study_dir:/study:ro,$study_dir/scripts:/code:ro,$repo_dir/src:/library:ro,$validation_dir:/output:rw" \
  --env PYTHONPATH=/code:/library,PYTHONDONTWRITEBYTECODE=1,OPENBLAS_NUM_THREADS=1,PYTHONUNBUFFERED=1 \
  "$repo_dir/containers/images/ipin-data-arm64_0.1.2.sif" \
  python /code/validate_final.py
```

This is validation of the recorded run. A fresh scientific reproduction creates
new timestamped freezes and audit hashes, as described in
[PUBLICATION.md](../PUBLICATION.md).
