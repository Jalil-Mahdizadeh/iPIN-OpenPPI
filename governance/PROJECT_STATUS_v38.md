# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Scientific programme state:** development evaluation is complete, accepted,
and independently validated; the complex-model claim is stopped and the
programme stops before protected evaluation

The authoritative gate is `governance/gates/gate_status_v38.yaml`. The
acceptance and disposition authority is `DEC-0039`.

## Accepted development execution

Development was decrypted exactly once after the prerelease gate passed. All
nine frozen cells were evaluated with exactly nine deterministic controls, 30
selected checkpoints, and ten three-seed ensembles on 9,026,108 score rows.
All C3, C2, and C1 PU-R metrics, paired 2,000-replicate component-bootstrap
intervals, degree/hub strata, source-exclusive cells, seed stability, and C1
novel-U sensitivity are frozen.

There was no retraining, tuning, checkpoint or ensemble change, second
development decryption, new scorer, benchmark change, negative or
pseudo-negative construction, or protected access.

## Scientific disposition

The exact accepted outcome is:

**stop the complex-model claim and stop before protected evaluation.**

The best partner-gated C3 ensemble scores `0.49134652604741336`, interval
`[0.4622492977197828, 0.5372847754287488]`. It is worse than within-pair 3-mer
by `-0.15333611147533133`; improves on 650M linear by only
`0.006206836644593983`; and has a positive `0.014917351434742432` point delta
over matched no-gate whose paired interval includes zero. Both named-source
deltas and the non-hub delta fail direction requirements.

Simple controls explain the structure: C3 sequence-length ratio, within-pair
3-mer, and exact interolog score `0.6608800512102514`,
`0.6446826375227447`, and `0.635701358715407`; C2 degree sum scores
`0.8392632813073615`; and C1 preferential attachment scores
`0.9069423975969924`. The partner-gated line therefore shows no qualifying
transferable-sequence advantage.

The frozen selection cascade chooses the 150M linear lr-3e-4 candidate, but
the model-level kill rules override advancement. No model or simpler baseline
advances to protected evaluation. Simple controls remain explanatory evidence
only.

## Validation and evidence

The corrected production audit passed 9 of 9 checks. The standalone clean-room
validator passed 16 of 16, recomputing every deterministic score and every
checkpoint score on all rows at maximum absolute difference `0.0`, all ten
ensembles, all metrics and diagnostics, all bootstraps, and the exact selection
and kill trace.

Authoritative hashes are:

| Artifact | SHA-256 |
|---|---|
| Development scoring manifest | `c82be153593ad46101f1ce49e1c79d341da535c71b34ded748c63e478b10dc99` |
| Development results manifest | `e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299` |
| Selection and kill trace | `ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45` |
| Completed-evaluation registry | `42aa8b19c4c5cfaf36bfbe1bd19bdf74e7de81df27cccb793809a5ec80d0e189` |
| Production completed audit | `1724a645e39ec232827aa8d1a8b6142fd257ec9404f133e985f2330e15e073ba` |
| Independent completed validation | `0d3bc35047bd8971177dbe148d1f5a4bbe515ba6d396552e6f3f3cf49f11039e` |

`ISSUE-0009`, `ISSUE-0010`, and `ISSUE-0011` are closed after narrowly scoped,
numbered, regression-tested, production- and independently requalified
corrections. No scientific output or frozen semantic changed.

## Closed boundary

Protected candidates, truth, and both protected private keys remain sealed.
Protected evaluation is prohibited. The development work package is closed and
there is no active model work package. Any future scientific phase requires a
new prospective protocol and numbered governance decision; it cannot retrain
on development, change this benchmark or its criteria, or reinterpret the
protected packages under the stopped claim.
