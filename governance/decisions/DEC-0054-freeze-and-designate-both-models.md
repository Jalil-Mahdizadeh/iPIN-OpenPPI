# DEC-0054: Freeze both ensembles and designate their distinct roles

Date: 2026-09-11. Status: accepted; user-authorized preservation and designation.
Preceding decision: [DEC-0053](DEC-0053-authorize-fixed-ensemble-followup.md).

The user requests: “freeze both models, make the optimized ensemble the
best-performing model while retaining the affine model as the original
confirmatory baseline. Then, commit and push”.

## Decision

The **best-performing model** is
`esm2_150m__residual_wide__epoch04_ensemble3`: the already development-selected
and tested residual-MLP ensemble, without refitting or changing epoch, seeds,
features, parameters, score transformation or ensemble weights. “Best-performing”
means the higher observed primary C3 score among the two evaluated PLM ensembles;
its point scores are also higher in all nine reported test cells.

The **original confirmatory baseline** is
`lightweight_esm2_150m_linear__linear_lr3e-4`: the original three-seed affine
ensemble at pass 5. It remains the model from DEC-0051's original protected
evaluation and the immutable reference for subsequent comparisons. It is not
retired, overwritten, renamed in historical results, or stripped of that role.

Each prediction is the equal arithmetic mean of all three raw member scores
(FP32 member inference, FP64 averaging), not a member score or mean metric.
The seeds remain 20260803, 20260817 and 20260831, in that order.

Both models are preserved in a new, exclusively created read-only local bundle,
with state-only checkpoints, the shared frozen encoder/tokenizer, training-only
normalizer, identity-aligned embedding matrix and source snapshots. A public
SHA-256 registry records both roles and exact provenance; weights and endpoint
identities are not added to Git. This is preservation, not a deployment release.

## Evidence and limits

C3 development concordance was 0.784142 → 0.799419. C3 test concordance was
0.789249 → 0.807948; the paired gain was +0.018699 with 95% interval
[−0.001358, +0.050000]. Designating the optimized ensemble best-performing by
observed score **does not establish statistically conclusive primary C3
superiority**, equivalence, or absence of benefit.

DEC-0052's failed original individual-seed gate remains unchanged. DEC-0053's
post-development/pre-follow-up-test ensemble amendment and completed follow-up
remain separate from the original confirmatory evaluation. This designation is
post-follow-up and is not represented as a prospective selection decision.
The existing test has been examined; there is no independent replication claim.
PU concordance is not binary binding accuracy or a calibrated probability.
Genuine partner specificity, direct-binding generalization and shortcut-free
prediction remain unresolved. BioPlex remains secondary cross-assay evidence,
not a direct-binary selection gate.

## Execution boundary

No new fitting, prediction of benchmark pairs, truth access, metric recomputation,
test set, evaluation attempt or ledger reset. Hash/state validation and synthetic
runtime tests are permitted. Preserve every closed protocol, result, receipt,
checkpoint and both consumed evaluation ledgers. Update only living indexes and
add new versioned records. Commit and push the public registry, code and docs.

See [model cards and preservation record](../../docs/models/FROZEN_PAIR_MODELS_v1.md),
[status v54](../PROJECT_STATUS_v54.md) and
[gate record v54](../gates/gate_status_v54.yaml).
