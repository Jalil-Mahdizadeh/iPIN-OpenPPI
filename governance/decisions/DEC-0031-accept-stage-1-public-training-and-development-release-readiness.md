# DEC-0031: Accept Stage 1 public training and development-release readiness

**Date:** 2026-08-19

**Status:** Accepted and effective for the Stage 1 training freeze and
readiness determination; this decision does not release development

**Controlling records:** `DEC-0028`, `DEC-0029`, `DEC-0030`, and gate v29

## Decision

Accept the complete, independently validated Stage 1 public-training execution
and freeze its exact scorer candidates. Determine that every prerequisite
specified by `DEC-0028` for a later development release has been satisfied.

This is not the separate development-release authorization required by the
frozen protocol. The development package remains encrypted and may not be
accessed or decrypted. A later effective numbered decision must explicitly
authorize that release. Protected candidates and truth remain encrypted and
evaluator-only.

## Accepted execution

Accept:

1. both exact ESM-2 custody snapshots and the accepted one-GPU ARM64 runtime;
2. complete label-blind FP32 pooled embeddings for all 17,000 endpoints from
   both encoders, with training-only normalization and independently validated
   one-percent repeats at maximum absolute difference `0.0`;
3. the frozen mandatory shortcut, graph/degree, sequence/interolog, PLM-linear,
   nonlinear no-gate, and partner-gated implementations;
4. exact use of the 16,799 public P census and 2,000,000 public U observations
   under the design-weighted PU ranking objective, without assigning a
   negative label to U;
5. all 30 preregistered runs, 150 complete passes, 73,350 steps, and exactly
   300,000,000 comparisons, with zero failures and zero resumes;
6. the training-only checkpoint rule, which selected pass 5 in all 30 runs;
7. all frozen configs, orders, logs, states, metrics, checkpoints, sidecars,
   code/input/runtime dependencies, and 10 three-seed ensemble definitions in
   the complete registry; and
8. the production audit and clean-room independent validation, both passing
   without warning or failure.

The authoritative complete registry is
`artifacts/validation/model_execution/stage1_model_execution_v1/TRAINING_ARTIFACT_REGISTRY.json`
with SHA-256
`11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318`.
It contains 647 unique registered artifacts totaling 15,124,997,716 bytes,
including 150 checkpoints, 30 selected checkpoints, and 10 ensemble
definitions.

## Validation basis

Production training audit passed 12 of 12 checks with zero warnings and zero
failures. The independently implemented final validator passed 14 of 14 checks
with zero warnings and zero failures. It rehashed all 647 artifacts,
independently reconstructed orders and exact rational weights, inspected every
checkpoint, functionally rescored every selected checkpoint in both partner
orientations, confirmed swap maximum absolute difference `0.0`, and found no
development, protected, private-key, temporary, or sensitive-path leakage.

The accepted evidence hashes are recorded in
`docs/reports/m1/M1_Stage_1_Public_Training_Execution_Final_v1.md`. The complete
registry was frozen at
`a46639245fc34d9b53063ec46370a6139a2bd021`; independent validation evidence
was frozen at `1003d3e4a0270047d904f06e9acb025bce78cd94`.

## Development-release prerequisite determination

The following frozen prerequisites are satisfied: every prespecified run
completed or failed closed; all selected checkpoints and ensemble definitions
were fixed; the complete registry was frozen before any development access;
and the registry passed an independent validation covering embeddings, data
visibility, objective weighting, model implementation, run completeness,
reproducibility state, and absence of leakage.

No development metric has been calculated and no candidate has been selected.
Training-monitor values are optimization diagnostics only. They do not satisfy
any C1/C2/C3 efficacy, complexity, shortcut, or model-level kill criterion.

## Frozen next boundary

There is no active executable work package after this decision. The only
possible next scientific action is a separately numbered decision that releases
the encrypted development package to the frozen scorer candidates and frozen
evaluation procedure. If authorized later, development must:

- score only the already-frozen deterministic controls and 10 three-seed
  ensembles;
- perform no training, checkpoint change, feature change, new run, or adaptive
  search;
- report C3, then C2, then C1, with the frozen bootstrap, degree/hub strata,
  and C1 novel-U sensitivity;
- apply the frozen decimal-`0.001` `ROUND_HALF_UP` selection cascade and
  complexity/kill rules exactly; and
- return to governance before any protected-test action.

## Continuing prohibitions

Development access without a new release decision, protected-candidate or
truth access, negative or pseudo-negative construction, P/U or benchmark
modification, full candidate-universe materialization, external-panel
integration, structures or residue/interface modelling, additional or adaptive
training, multi-GPU/multi-node execution, post-release retraining, probability
or prevalence claims, and unsupported PLM-exposure claims remain prohibited.
