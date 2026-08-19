# DEC-0035: Accept nullability-correction requalification and resume development scoring

**Date:** 2026-08-19

**Status:** Accepted and effective only for resuming the frozen development
scoring/evaluation from the existing one-time release; no further decryption is
authorized and protected-test access remains prohibited

**Controlling records:** `DEC-0028`, `DEC-0032`, `DEC-0033`, `DEC-0034`, gate
v33, and `ISSUE-0009`

## Decision

Accept the repeated production and clean-room independent prerelease
qualification of the exact `DEC-0034` nullability-metadata correction. Resume
the frozen 49-scorer development execution from the already released and
hash-verified development package.

This is not a second release or decryption. It does not alter a row, value,
logical type, order, state, rational weight, scorer, checkpoint, ensemble,
metric, bootstrap, selection criterion, complexity threshold, or kill rule.

## Accepted correction and evidence

The corrected source was frozen at commit
`90ed5007d1deed7f50bab0f2901bf5780a1ab034`. The repeated no-key production
audit was frozen at `818cadb9e0981a9b13ac6cb70ed8a4e8e24053ca` and passed
13 of 13 checks. The revision-2 independent validator was implemented only
after that evidence was committed, frozen at
`00a039f5b5d4b3e4eabfadaf9fcba8248a8ac182`, and its passing evidence was
frozen at `6947c6907e26bed780e13a53e21a00620993f8fb`.

Accept these evidence hashes:

| Artifact | SHA-256 |
|---|---|
| Revision-2 production prerelease audit | `963b3a9d0e567bc0dd4d1850bd9d8a9382579f46ce9f4643297923f5ccb4962e` |
| Revision-2 independent prerelease validation | `aaeab6728463f188eb8d81c355a333071f695b5d7278e38c1440aed6a810e5d8` |
| Corrected scoring source | `5ccd061814a3d20bb39b54048ef11cf86bc350f832bd373b2d7aca1892feef30` |
| Frozen execution projection | `d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d` |

The two qualifications establish that:

1. `pa.concat_tables(tables, promote_options="permissive")` is the sole
   authorized loader correction and accepts only the observed nullable-schema
   mismatch while preserving exact row/value/type/order semantics;
2. the exact nine controls, 30 selected checkpoints, ten three-seed
   ensembles, score-only model algebra, HT metric, component bootstrap,
   stratification, selection, complexity, and kill rules remain qualified;
3. the first scoring attempt produced no score row, metric, selection, or
   scientific result and its empty tree remains separately preserved; and
4. neither qualification accessed development plaintext or private keys, nor
   any protected private key, candidate, truth, or score.

## Resumed execution boundary

Use only the existing release with archive SHA-256
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`
and manifest SHA-256
`3f58403138b878d912789f529dc1f8ec7d1db7356d6ccc4c3b88cfcb2f6554fa`.
Run all nine development cells with the frozen 49-scorer census, then calculate
the preregistered C3-first evaluation and diagnostics without training or
checkpoint change.

A second development decryption is prohibited. Any release-hash drift,
incomplete private output, scoring failure, nonfinite score, scorer-census
drift, checkpoint/hash drift, or criterion ambiguity stops execution and
returns to governance.

## Required return

Freeze private score artifacts plus the public hash registry and production
evaluation evidence. Only after that production evidence is committed may a
completed-evaluation independent validator be implemented and run. Return to
governance with exactly one disposition: advance a completely frozen eligible
scorer toward separately authorized protected evaluation, retain only a
simpler eligible baseline, or stop the complex-model claim.

## Continuing prohibitions

Protected candidates, protected truth, all protected keys, protected scoring,
additional development decryption, training, retraining, tuning, checkpoint or
ensemble change, scorer/protocol/threshold change, negatives or
pseudo-negatives, benchmark modification, external panels, structure/residue/
interface work, and adaptive post-release analysis remain prohibited.
