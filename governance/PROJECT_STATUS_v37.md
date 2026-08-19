# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Scientific programme state:** frozen development scoring and evaluation are
complete, but the results remain unaccepted while the exact `ISSUE-0011`
completed-auditor scoring-census correction and independent validation are
performed

The authoritative gate is `governance/gates/gate_status_v37.yaml`.

## Completed frozen execution

All nine development cells have immutable 49-column score matrices covering
30 selected checkpoints, ten three-seed ensembles, and nine deterministic
controls. The scoring manifest is
`c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99`.
The unchanged evaluator produced all preregistered aggregate metrics,
diagnostics, bootstrap intervals, C1 novel-U sensitivity, and the frozen
selection/kill trace.

No retraining, tuning, checkpoint change, second development decryption, or
protected access occurred.

## Fail-closed audit incident

The first completed production audit passed eight of nine checks and failed
only because it expected the 13-table package census (`9,044,323`) as the
nine-cell score-row census. The correct score census is `9,026,108`: exactly
`9,000,000` U and `26,108` released P. The extra package rows are `18,081`
source-visible training-positive support rows and `134` strata rows, neither of
which is scored.

`DEC-0038` authorizes only correction of that assertion plus a focused
regression test. The failed evidence and aggregate incident report are
preserved. No score, metric, bootstrap, model, result, benchmark, or protocol
artifact may change.

## Current hold

Repeat the full production audit after freezing the exact fix. Only after its
evidence is committed may the clean-room completed-evaluation validator be
implemented and run. A further numbered decision must accept the final results
and disposition.

The current frozen evaluator output is
`stop_complex_model_claim_and_stop_before_protected_evaluation`; it is not yet
an accepted governance disposition. Protected candidates, truth, and private
key remain sealed and protected evaluation is prohibited.
