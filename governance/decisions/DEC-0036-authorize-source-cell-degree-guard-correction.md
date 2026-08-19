# DEC-0036: Authorize source-cell degree-semantics guard correction

**Date:** 2026-08-19

**Status:** Accepted and effective only for the exact validation correction in
`ISSUE-0010`; development scoring is paused pending repeated production and
independent qualification

**Controlling records:** `DEC-0024`, `DEC-0028`, `DEC-0032`, `DEC-0035`,
gate v34, and `ISSUE-0010`

## Decision

Authorize a cell-aware correction to the pre-score degree-metadata guard:

1. primary-cell recorded degrees must exactly equal endpoint degree in the
   frozen pooled 16,799-positive public-training graph;
2. source-exclusive recorded degrees must be nonnegative and their ordered
   degree-bin pair must exactly reproduce the frozen row `stratum_id`; and
3. deterministic degree, preferential-attachment, component-mass,
   common-neighbor, interolog, and all learned scorer calculations continue to
   use the same pooled public-training graph and frozen embeddings/checkpoints.

This reconciles two existing semantics; it does not change either one. The
sealed source-cell degree fields remain source-visible sampling-design metadata
under `DEC-0024`, while all model/control features remain pooled-training-only
under `DEC-0028`.

## Incident and partial-run custody

Accept the aggregate incident report at SHA-256
`547288eeece915366505277ed5a5bf427b8a758f2ddf0d38892857a1a529b35b`.
The completed C3 primary/source cells and primary C2 cell each have 49 finite
scores and immutable cell manifests. The failed source-exclusive C2 directory
contains no file and no score row. No run manifest, metric, bootstrap,
selection, or disposition exists.

The completed cell artifacts may be reused only by the frozen scorer's exact
`--resume` path after requalification. Their manifest and constituent hashes
must be reverified; the correction cannot alter their computations. The empty
failed directory may be moved intact to a uniquely named private incident path
before resume.

## Requalification requirement

Before scoring resumes:

1. freeze only the cell-aware guard and focused primary/source fixtures;
2. extend the no-key production audit to prove the two degree semantics,
   unchanged pooled scorer inputs, and exact stratum validation;
3. freeze a new production audit report;
4. only afterward implement and freeze a new clean-room validator fixed to the
   corrected source and production-evidence hashes;
5. freeze its passing report; and
6. record a numbered acceptance authorizing exact resume from the existing
   release and completed manifested cells.

Neither validator may inspect development pair identities, scores, plaintext,
or private keys. A failure stops execution. No additional development
decryption is authorized.

## Continuing prohibitions

Pair-artifact, sampling-stratum, rational-weight, benchmark, protocol, model,
checkpoint, ensemble, metric, threshold, and kill-rule changes are prohibited.
Training, tuning, negatives or pseudo-negatives, protected access, external
panels, and structure/residue/interface work remain prohibited.
