# DEC-0023: Authorize the pair-level PU-R benchmark protocol freeze

**Date:** 2026-08-08

**Status:** Accepted and effective for this protocol-only work package

**Decision basis:** Explicit project-owner instruction supplied in the active
session

**Controlling record:** `DEC-0022`

## Decision

Authorize `pair_level_pu_r_benchmark_protocol_v1` as the sole next technical
work package. It may define, aggregate-check, independently validate, and freeze
the pair-level protocol that a later benchmark-construction package must
follow. It may transiently reconstruct the already accepted released-positive
sequence-pair union to test the rules, but it may emit only aggregate counts and
protocol metadata.

This authorization does not permit pair-row or candidate-row persistence,
unlabeled-sample realization, model inputs, scores, predictions, or any form of
model work.

## Required frozen protocol

Before any model result exists, the work package shall freeze:

1. exact source, sequence, partition, and protocol information cutoffs;
2. the evidence visible to training, development evaluation, and the protected
   one-shot test evaluator;
3. pair identity, evidence-group co-location, and exact C1, exclusive-C2, and
   C3 positive-assignment rules under the immutable component split;
4. a label-blind deterministic C1 training/development/test assignment and
   exposure guard;
5. candidate-pool semantics, deterministic unlabeled sampling, public salts,
   seeds, inclusion probabilities, and design weights, without realizing a
   sample in this package;
6. primary PU-retrieval metrics, tie handling, candidate-fraction cut points,
   and clustered uncertainty;
7. source, study, assay, and temporal holdout rules only where the frozen
   evidence supports them, with unsupported axes explicitly inactive;
8. training-visible degree/hub strata and simple later baselines; and
9. acceptance floors, demotion rules, protected-test controls, and claim
   boundaries.

All reverse orientations, construct/orientation records, repeated records, and
source observations for one unordered frozen sequence pair must share one pair
assignment. A source-, study-, assay-, or temporal-held-out label may not be
used to remove that pair from the corresponding candidate pool.

## Binding C1/C2/C3 semantics

- C1 evaluation positives have two training-partition endpoints, are assigned
  development or test by a prespecified label-blind pair hash, are absent from
  interaction-supervised training as pairs, and have both endpoints exposed by
  at least one other training-visible positive pair.
- Exclusive C2 positives join exactly one interaction-supervision-exposed
  training endpoint to one endpoint in the named held-out partition.
- C3 positives have both exact endpoints in the same named held-out partition.
  Those endpoints are absent from interaction-supervised training and their
  frozen components are disjoint from training under 30%
  `local_domain_union_v1`.
- Development-to-test pairs and any positive that fails its exposure or
  metadata guard are quarantined rather than reassigned or relabelled.

The C3 definition does not authorize unseen-family, unseen-domain,
PLM-unseen-protein, or exhaustive-nonhomology claims.

## Evidence and holdout boundary

The qualifying positive union remains exactly the accepted HI-II-14/HuRI
reference-sequence projection. Unreported eligible pairs remain unlabeled.

The work package must inspect field completeness before activating auxiliary
holdouts. Coarse source identity may support a source-exclusive diagnostic.
Publication, assay-version/batch, or record-date fields may not be promoted to
independent holdouts when they are missing, unresolved, shared, or merely
release/creation metadata. Conditional or undersized axes must be demoted
before modeling, not pooled to hide failure.

## Required validation and return

Production and an independently implemented validator must run from clean
commits through the pinned ARM64 Apptainer image. They must verify all parent
hashes, the immutable 17,000 endpoint assignments, positive-pair/source
reconstruction, C1 hash roles, exposure guards, C1/C2/C3 aggregate counts,
source-exclusive feasibility, candidate-count algebra, sampling probabilities,
metric definitions, visibility controls, and continuing prohibitions.

The package must return to governance with an immutable machine-readable audit,
independent validation report, scientific report, numbered acceptance decision,
new gate, and updated restart documentation.

## Continuing prohibitions

This decision does not authorize:

- persisted positive/unlabeled evidence-indicator or C1/C2/C3 pair rows;
- candidate-pair universe materialization or unlabeled-sample realization;
- negative labels or pseudo-negatives;
- modification of the frozen endpoint/component split;
- external-panel integration or reopening any accepted parent audit;
- structural mapping or structure-derived labels;
- model implementation, embedding, training, tuning, selection, calibration,
  evaluation, routing, or release;
- prevalence, biological precision, universal-nonbinding, or calibrated-
  probability claims; or
- a change to the accepted reference-sequence PU-R design.

The TF-isoform panel remains external-only and unsuitable for training
negatives or any training role, universal-nonbinding claims, prevalence,
calibration, and unseen-endpoint or family benchmarking.
