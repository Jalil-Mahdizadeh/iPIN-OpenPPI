# ISSUE-0011: Completed auditor used the release-table census as the score-row census

**Date opened:** 2026-08-19

**Status:** Confirmed non-scientific completed-auditor assertion defect; exact
scoring-census correction authorized by `DEC-0038`; completed development
results remain unaccepted pending repeated production audit and independent
validation

## Observation

The first completed-development production audit recomputed all nine cells and
all 49 frozen scorers, then failed closed on one of nine checks. It observed
`9,026,108` score rows but the check incorrectly expected `9,044,323`.

The two values describe different frozen censuses:

- the nine score matrices contain `9,000,000` U rows and `26,108` released-P
  rows, for `9,026,108` rows; and
- the 13-table released package additionally contains `18,081` source-visible
  training-positive support rows and `134` sampling-stratum rows, for
  `9,044,323` package-table rows.

Support-table rows are inputs to cell construction and validation. They are not
scored candidates and must not occur in a cell score matrix.

## Aggregate evidence and custody

The incident report is
`artifacts/validation/development_evaluation/development_release_and_evaluation_v1/failed_completed_audit_attempt_001_scoring_row_census/INCIDENT_REPORT.json`
at SHA-256
`e50b7657b19a9618f06e1d2b6ad102ffc56764e2e2b2e0c07d15c72019f9783c`.
The failed registry and report are preserved in the same directory at SHA-256
`bc9d2e182a2cfc3199872e7099dc7b40bfb62214aebd9663f40201da7b410429`
and
`59b36f830f4541b82321c6d8637deee3fdeab88e3fdf335385d3c6e133360aab`.

The other eight audit checks passed. They covered all 49 score columns and all
ten exact ensembles; all 9 x 49 point metrics and primary degree/hub and
correlation outputs; all component draws, bootstrap hashes, finite counts, and
intervals; C1 novel-U; the full selection/complexity/kill trace; public-result
hashes and identity exclusion; and execution-log/protected-boundary flags.

The scoring manifest remains
`c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99`.
The public results manifest and selection/kill trace remain
`e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299`
and
`ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45`.
No score, metric, bootstrap, result, checkpoint, or benchmark artifact changed.

## Exact correction boundary

Replace only the completed auditor's hard-coded package-row comparison with a
scoring-cell census. It must independently require:

1. exactly nine cell manifests and their exact frozen order;
2. exactly `9,000,000` U rows and `26,108` released-P rows across those cells;
3. exactly `9,026,108` total score rows;
4. each cell's Parquet state census and matrix row count equal its immutable
   cell manifest; and
5. each cell manifest equal its entry in the immutable scoring-run manifest.

No scorer, row, score, metric, bootstrap, result, model, checkpoint, protocol,
threshold, or disposition change is authorized. The corrected production audit
must be frozen before a clean-room completed-evaluation validator is
implemented and frozen.
