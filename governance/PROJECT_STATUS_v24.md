# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** DEC-0022 endpoint/component skeleton immutable;
DEC-0024 pair-level PU-R benchmark protocol accepted and frozen; DEC-0025
authorizes only sealed pair-artifact construction and deterministic sample
realization; all model work remains unauthorized

The authoritative gate is governance/gates/gate_status_v24.yaml.

## Accepted pair-level protocol

DEC-0024 accepts configuration revision 2 of
pair_level_pu_r_benchmark_protocol_v1. Production from clean commit
8ee0ae58b365c68ffb5732c9995803d24e5fe6fa passed 16 checks. Independent
validation from clean commit d32a26508eb9438cb693ae1ae3cf48f5324a37f7
passed 18 checks. Neither layer emitted pair rows or realized a sample.

The protocol freezes:

- the published-2020 HI-II-14/HuRI evidence snapshot, UniProt 2026_02
  reference-sequence endpoint identities, and immutable DEC-0022 split;
- training/development/protected-test evidence visibility and a one-first-use
  protected evaluator;
- unordered pair identity, evidence-group co-location, deterministic C1 roles,
  exposure-guarded C1/C2/C3 assignment, and quarantine without reassignment;
- deterministic stratified unlabeled sampling with exact salts, seeds,
  inclusion probabilities, weights, caps, and Hamilton apportionment;
- PU-retrieval metrics, clustered uncertainty, degree/hub strata, and future
  simple baseline formulas; and
- supported named-source diagnostics plus fail-closed study, assay, temporal,
  and claim dispositions.

## Feasibility return

Interaction supervision has 16,799 released-positive pairs and 4,675 exposed
training endpoints. Development/test positive counts are:

- C1: 3,259 / 3,187;
- C2: 11,327 / 13,446; and
- C3: 2,265 / 2,379.

All six primary cells pass the frozen pair, component, and source-presence
floors. Strict HI-II-14-target C1/C3 source cells are descriptive only; strict
HI-II-14 C2 and all HuRI-target cells pass. Independent study,
assay-version/batch, and temporal holdouts remain inactive.

## Binding semantics

Unreported eligible pairs remain unlabeled, not negatives. C3 means only both
exact frozen reference-sequence endpoints absent from interaction-supervised
training and component-disjoint under 30% local_domain_union. It does not mean
unseen biological family, family generalization, unseen domain, PLM-unseen
protein, or exhaustive nonhomology.

Primary metrics are released-positive PU retrieval statistics, not biological
precision, prevalence, calibration, or binding probability.

## Active bounded work package

DEC-0025 authorizes 'pair_level_pu_r_benchmark_artifacts_v1'. Production may
persist the frozen training and development positive pairs, realize the exact
cell-specific unlabeled samples, and construct source-exclusive diagnostic
artifacts. It must not change any DEC-0024 rule.

The public training package is limited to training positives and rows whose
state is 'unlabeled'. The development package remains encrypted until a future
training artifact hash is frozen. Protected-test candidates and protected truth
use separate keys; prediction means a frozen scorer executed in the sealed
evaluator, not a public pair-keyed score file. Predictions must be complete and
hashed before protected truth is opened.

The cell-specific public hash payload permits an unlabeled pair to recur in
different cell samples. Such reuse must be counted and is not positive-label
leakage. Any held-out positive in the training package, source-visible positive
represented as unlabeled, role overlap, public protected-test identity, or
sample/hash/weight mismatch is a hard failure.

## Immutable parent and panels

The 17,000 endpoints, 7,782 hard-rule components, and 11,900/2,550/2,550
training/development/test assignments accepted by DEC-0022 are unchanged.

The TF-isoform and Lambourne panels remain external-only and unused. The
TF-isoform panel remains unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

## Binding authorization and hold

Only DEC-0025 construction is authorized. It may materialize the frozen bounded
samples but not the full candidate-pair universe. The following remain
prohibited:

- negative labels or pseudo-negatives;
- public protected-test candidate, prediction, or truth identities;
- development release before a training artifact hash is frozen;
- full candidate-pair universe materialization;
- modification of the frozen endpoint/component skeleton;
- external-panel integration or structural-label work;
- prevalence, probability, biological-precision, or calibration claims; and
- model implementation, embedding, training, tuning, selection, evaluation,
  routing, or release.

The construction must return with production evidence, independent validation,
a scientific report, a numbered acceptance decision, and a new gate. Any later
development release or model work requires separate numbered authorization.
