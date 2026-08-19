# DEC-0037: Accept source-degree guard requalification and resume scoring

**Date:** 2026-08-19

**Status:** Accepted and effective only for exact resume of the frozen
development scorer from the existing release and four complete manifested
cells; no decryption or protected access is authorized

**Controlling records:** `DEC-0024`, `DEC-0028`, `DEC-0032`, `DEC-0036`,
gate v35, and `ISSUE-0010`

## Decision

Accept the repeated production and clean-room independent qualification of the
exact cell-aware source-degree metadata guard. Authorize the frozen scoring
script's `--resume` path to reuse the four hash-verified complete cells and
score only the five remaining development cells.

The empty failed-cell directory may be moved intact to
`.private/development_release_and_evaluation_v1/failed_scoring_attempt_002_source_degree_guard`
before resume. This is private incident custody, not a row or score change.

## Accepted implementation and evidence

The corrected source was frozen at
`da5a56026753ec0d58ff9a55ac994c5a6a40a885`. The revision-3 no-key
production audit was frozen at
`9bdafc3805b53ca9ff6013fa9c4e366a4cb3aae4` and passed 14 of 14
checks. The new clean-room validator was frozen only afterward at
`95a220dd1444a44cf320dc38e1864538965480ed`; its evidence was frozen at
`f70f518542c67cba381ab6e519f62dc926defe6c` and passed 14 of 14 checks.

Accept these hashes:

| Artifact | SHA-256 |
|---|---|
| Corrected scoring source | `874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f` |
| Revision-3 production audit | `778b8d68ff102aad005286bc5ab85691e949742c69f116c9027492523d823fd7` |
| Revision-3 independent validation | `77ed919c4812453fab85de94a7ce0c52838bb3b7e921db6ca99a045e305ae686` |
| Partial-cell custody recheck | `7f36b15e90a01cfba7896ab11ba389aa706a9a7ceda5c4a416501a4c747b49d5` |

Production and independent checks establish that primary row metadata must
equal pooled training degree; source-exclusive design metadata must be
nonnegative and reproduce its frozen stratum; and every calculated graph/
degree scorer still uses the pooled 16,799-positive graph. No pair artifact,
weight, stratum, feature, score formula, model, metric, or threshold changed.

Neither qualification accessed development plaintext or a private key. The
separate custody check rehashed the four completed cell manifests and every
constituent file/byte count without reading or publishing pair identities. No
protected key, candidate, truth, or score was accessed.

## Exact resume and return

Resume once, offline, on at most one GH200. Existing completed cells must be
skipped only through their complete manifests. Any hash drift, incomplete
directory, nonfinite score, scorer/checkpoint drift, or further failure stops
execution and returns to governance.

After all nine cells and the scoring-run manifest are complete, execute the
unchanged frozen evaluation, freeze all private/public hashes and production
results, then implement the independent completed-evaluation validator only
after production evidence is committed. Governance must record the final
development disposition before any protected work.

## Continuing prohibitions

A second development decryption, protected candidate/truth/key access,
training, tuning, checkpoint/scorer/model/protocol/threshold changes, pair or
weight changes, negatives or pseudo-negatives, external panels, and
structure/residue/interface work remain prohibited.
