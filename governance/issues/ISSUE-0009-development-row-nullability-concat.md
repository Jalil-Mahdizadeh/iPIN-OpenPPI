# ISSUE-0009: Filtered development row nullability blocks strict concatenation

**Date opened:** 2026-08-19

**Status:** Confirmed implementation defect; exact correction authorized by
`DEC-0034`; no score row was produced

## Observation

After the one authorized development decryption passed every ciphertext,
archive, manifest, and table hash, the first scoring attempt stopped while
loading `C3_development`. `pyarrow.dataset.Dataset.to_table` retained non-null
field metadata for the positive table but returned the same selected U fields
as nullable. `pyarrow.concat_tables(tables)` therefore raised `ArrowInvalid`
before deterministic or learned scoring began.

The two projected tables have identical field names, logical Arrow types,
values, row states, and frozen order. Only field nullability metadata differs.
The private failed-attempt tree contains three empty directories and no files:

`.private/development_release_and_evaluation_v1/failed_scoring_attempt_001_pre_row_concat`

## Impact

- Development was released exactly once and remains hash-verified.
- No score, metric, selection result, bootstrap draw, or checkpoint change was
  produced.
- Protected candidates, protected truth, and protected private keys were not
  accessed.
- The frozen benchmark, pair rows, weights, model protocol, scorer census, and
  scientific semantics are unaffected.

## Exact correction

Replace only the strict Arrow schema-metadata concatenation with
`pa.concat_tables(tables, promote_options="permissive")`. Add a fixture proving
that the correction accepts nullability-only schema drift while preserving
column order, row order, values, logical types, and row counts exactly.

No cast, fill, row addition/removal/reorder, state change, weight change, score
change, or protocol amendment is authorized. Production and clean-room
pre-release validations must be repeated on the corrected source before scoring
resumes.
