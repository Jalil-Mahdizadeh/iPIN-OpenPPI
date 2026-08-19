# ISSUE-0010: Source-cell design degree metadata was compared to the pooled feature graph

**Date opened:** 2026-08-19

**Status:** Confirmed implementation defect; exact cell-aware validation
correction authorized by `DEC-0036`; scoring paused before the failed cell
produced a file

## Observation

The `DEC-0035` scoring run completed and manifested the three C3 cells and
`C2_development`. It then stopped in
`source_exclusive:HI-II-14:C2_development` before deterministic scoring
because one guard compared the row's recorded degree metadata with the pooled
16,799-positive training graph.

That comparison conflated two already frozen meanings:

- source-exclusive row degree/stratum metadata is calculated from the
  non-target-source-visible training-role graph under `DEC-0024`; and
- every `DEC-0028` degree/graph feature and primary degree/hub diagnostic uses
  the pooled 16,799-positive public-training graph.

The pair artifacts follow their frozen construction. No benchmark, protocol,
row, weight, or stratum inconsistency was found.

## Aggregate impact

The immutable aggregate incident report is
`artifacts/validation/development_evaluation/development_release_and_evaluation_v1/revision_3/SCORING_INCIDENT_REPORT.json`
at SHA-256
`547288eeece915366505277ed5a5bf427b8a758f2ddf0d38892857a1a529b35b`.

Four cells contain complete 49-scorer matrices and immutable manifests. The
failed cell directory is empty. There is no scoring-run manifest, metric,
bootstrap, selection, or scientific disposition. Development was not
decrypted again. Protected candidates, truth, and keys remain untouched.

An aggregate nine-cell audit confirms that primary rows use pooled degrees,
while source-exclusive C1/C2 rows carry the intended source-visible design
degrees. Source-exclusive C3 degrees coincide at zero, explaining why those
cells passed the overly broad equality guard.

## Exact correction boundary

Primary-cell recorded degrees must still equal the pooled training graph.
Source-exclusive recorded degrees must be nonnegative and reproduce each
frozen row's `stratum_id`; their table hashes and rational design weights
remain unchanged. All scorer features continue to use pooled graph degrees.
Only primary cells receive degree/hub stratification in the frozen evaluator.

No row, score formula, checkpoint, feature definition, metric, sampling design,
or protocol change is authorized. Production and clean-room prerelease
qualification must be repeated before an exact `--resume` may reuse the four
complete manifested cells.
