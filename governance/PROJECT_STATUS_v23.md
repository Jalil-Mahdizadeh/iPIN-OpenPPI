# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** DEC-0022 endpoint/component skeleton immutable;
DEC-0024 pair-level PU-R benchmark protocol accepted and frozen; pair-row
construction, sample realization, and all model work remain unauthorized

The authoritative gate is governance/gates/gate_status_v23.yaml.

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

## Immutable parent and panels

The 17,000 endpoints, 7,782 hard-rule components, and 11,900/2,550/2,550
training/development/test assignments accepted by DEC-0022 are unchanged.

The TF-isoform and Lambourne panels remain external-only and unused. The
TF-isoform panel remains unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

## Binding hold

No next work package is authorized. The following remain prohibited:

- persisted positive/unlabeled evidence-indicator or C1/C2/C3 pair rows;
- candidate-pair universe materialization or unlabeled-sample realization;
- negative labels or pseudo-negatives;
- modification of the frozen endpoint/component skeleton;
- external-panel integration or structural-label work;
- prevalence, probability, biological-precision, or calibration claims; and
- model implementation, embedding, training, tuning, selection, evaluation,
  routing, or release.

Any later benchmark-row construction, sample realization, or model work
requires a new numbered authorization and must preserve DEC-0024.
