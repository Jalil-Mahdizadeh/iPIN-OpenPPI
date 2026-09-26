# DEC-0056: Designate iPIN-TUnA-31k as the primary iPIN model

Date: 2026-09-26. Status: accepted; user-authorized.

The user approved the recommendation to make selected 31k the main model and
instructed: "ok, do that. update all relevant docs, commit and push."

## Decision

Register the already evaluated three-seed, epoch-1 TUnA ensemble trained on
31,188 P as **iPIN-TUnA-31k**, ID `ipin_tuna_31k_ensemble`, in
`frozen_pair_models_v3`. Set the catalogue's primary and default human PPI
predictor roles to this entry. The completed result identifier `selected_31k`
remains an alias. Retain all three previous registered predictors, their
aliases, private bundles, definitions and historical results unchanged.

The approved description is: "iPIN-TUnA-31k is the current primary iPIN
predictor, with the strongest overall performance among the evaluated frozen
predictors on the project's human PPI benchmark."

## Basis and scope

Completed test2 macro concordance is 0.886903 / 0.827113 / 0.786652 for C1/C2/C3,
the highest among 13 frozen predictors. Paired C3 gain over historical 17k
PU-TUnA is +0.042781 [0.019768, 0.070150]; all 12 C3 contrasts have positive
pointwise 95% component-bootstrap intervals. Intervals are not adjusted for
multiple comparisons. PLM-interact exceeds this model on added C3 alone
(0.767828 versus 0.740105); historical PU-TUnA exceeds it on reconciled legacy
C1/C2. These distinctions must remain visible in the model card.

The original study selected checkpoints using C3 development before its test
evaluation. This subsequent primary-model designation follows the completed
test2 and twelve-target results. It does not create a new prospective selection
or independent replication. The expanded study used new evidence and a
reconciled U background; comparator training/selection differs. The result
does not isolate architecture or data volume causally.

## Execution and attribution

Authorize the new versioned registry and local preservation bundle,
byte-identical copies of selected checkpoints/features and aggregate evidence,
synthetic qualification, source/hash verification, current documentation
updates, and a commit/push of public metadata, code and aggregates.
Preserve the published Bernett TUnA attribution and upstream license records.
The release does not distribute model weights or pair-level data.

The prediction unit retains seeds 20260803, 20260817 and 20260831, epoch 1,
equal FP64 averaging of FP32 mean-field-adjusted logits and the exact saved
GP covariance. Set the GP fitted flag before evaluation mode. No fitting,
covariance recomputation, benchmark scoring, truth access, metric recomputation
or evaluation-ledger reset is part of this promotion. The target remains human
P/U ranking; no calibrated probability, verified-negative, direct-binding,
partner-specific, non-human or universal-superiority claim is added.

See the [v3 card](../../docs/models/FROZEN_PAIR_MODELS_v3.md),
[promotion report](../../docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md),
[status v56](../PROJECT_STATUS_v56.md) and [gate v56](../gates/gate_status_v56.yaml).
