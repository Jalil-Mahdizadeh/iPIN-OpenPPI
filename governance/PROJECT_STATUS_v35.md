# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Scientific programme state:** development scoring has four complete
manifested cells and is paused before the failed fifth cell's first score while
the exact `ISSUE-0010` degree-semantics guard correction is requalified

The authoritative gate is `governance/gates/gate_status_v35.yaml`.

## Incident disposition

Source-exclusive rows correctly contain non-target-source-visible degree
metadata used for their frozen sampling strata. `DEC-0028` scorer features
correctly require degrees from the pooled 16,799-positive public-training
graph. One guard incorrectly required those two quantities to be equal.

The aggregate incident report has SHA-256
`547288eeece915366505277ed5a5bf427b8a758f2ddf0d38892857a1a529b35b`.
Three C3 cells and primary C2 are complete and manifested. The failed
HI-II-14-exclusive C2 directory is empty. No metric, bootstrap, selection, or
scientific disposition exists.

## Authorized correction

`DEC-0036` permits only cell-aware validation: primary metadata must equal the
pooled graph, while source-exclusive metadata must be nonnegative and reproduce
the frozen stratum. Every actual score still uses the pooled graph. Pair
artifacts, rows, weights, strata, models, checkpoints, metrics, and criteria
remain unchanged.

Freeze and requalify the correction with production and independent no-private-
data checks. A further numbered acceptance is required before exact resume.
Development cannot be decrypted again. Protected candidates, truth, and keys
remain fully sealed.
