# DEC-0038: Authorize completed-audit scoring-census correction

**Date:** 2026-08-19

**Status:** Accepted and effective only for the exact completed-auditor census
assertion correction in `ISSUE-0011`; development results are not yet accepted
and protected evaluation remains prohibited

**Controlling records:** `DEC-0024`, `DEC-0028`, `DEC-0032`, `DEC-0037`, gate
v36, and `ISSUE-0011`

## Decision

Accept the aggregate diagnosis that the first completed-development audit
compared the nine score matrices with the larger 13-table release-package
census. Authorize only replacement of that hard-coded assertion with the exact
nine-cell scoring census:

- `9,000,000` U rows;
- `26,108` released-P rows; and
- `9,026,108` total rows.

The auditor must continue to verify every cell's row states and matrix shape
against its immutable cell manifest and every cell manifest against the
immutable scoring-run manifest. The correction must add a focused regression
test distinguishing the score-row census from the support-table-inclusive
package census.

## Incident evidence

Accept the incident report at SHA-256
`e50b7657b19a9618f06e1d2b6ad102ffc56764e2e2b2e0c07d15c72019f9783c`.
The first audit passed eight checks and failed only the census assertion after
observing the correct `9,026,108` score rows. Preserve its failed registry and
report at their recorded hashes. They may not be overwritten or represented as
passing evidence.

The completed score manifest, public aggregate result manifest, and frozen
selection/kill trace remain unchanged. Their respective SHA-256 values are
`c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99`,
`e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299`,
and
`ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45`.

## Validation and return

Freeze the exact correction and focused test in a dedicated source commit.
Then rerun the complete non-overwriting production audit from the beginning,
including all nine cells, all 49 scorers, all ten ensemble-column checks, every
metric and diagnostic, bootstrap custody and intervals, C1 novel-U, and the
selection/complexity/kill trace.

Only after that passing production evidence is frozen may a new clean-room
validator be implemented. Its source must be committed after the production
evidence and must not import the production development-evaluation modules. It
must independently validate hashes, score matrices, ensembles, metrics,
bootstrap calculations, checkpoint/control spot checks, selection/kill logic,
and development-only information flow.

A further numbered governance decision is required to accept the development
results and determine the scientific disposition. No protected action may
occur before that decision, and the current frozen kill trace already requires
stop before protected evaluation.

## Continuing prohibitions

No decryption, training, tuning, checkpoint or scorer change, score
regeneration, metric or threshold change, benchmark or pair-artifact change,
negative or pseudo-negative construction, protected key/candidate/truth access,
external panel, or structure/residue/interface work is authorized.
