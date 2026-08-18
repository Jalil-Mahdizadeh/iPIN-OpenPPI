# DEC-0027: Authorize model-governance and baseline/training-protocol design

**Date:** 2026-08-18

**Status:** Accepted and effective for this design-only work package

**Decision basis:** Explicit project-owner instruction supplied in the active
session after successful execution of the `RESUME-002` preflight

**Controlling records:** `RESUME-002` and `DEC-0026`

## Decision

Authorize `model_governance_and_baseline_training_protocol_v1` as the sole next
work package. The package may design, machine-encode, report, test, and
independently validate the rules that a later model implementation and public-
training stage would have to follow.

This is governance work, not model execution. It may inspect public model
cards, repository metadata, licenses, checkpoint revisions, and checksum
records. It may read only already-public training-package metadata and
immutable parent manifests needed to prove scope. It may not acquire model
weights, build a model image, generate embeddings, instantiate or train a
model, release development, or access any protected identity or result.

## Required frozen design

Before any model result exists, the package shall freeze:

1. a deliberately small PLM candidate set with exact repository revisions,
   weight hashes, tokenizer/runtime versions, pooling and long-sequence rules,
   local-cache custody, license/provenance evidence, and conservative
   pretraining-exposure claim boundaries;
2. all mandatory zero-parameter graph/degree, sequence-length,
   sequence-similarity/interolog, and deterministic-hash controls, plus a
   lightweight frozen-PLM pair baseline;
3. the primary positive-versus-unlabeled ranking objective and the exact use of
   the 16,799 public training positives, 2,000,000 frozen public training-U
   observations, rational design weights, and deterministic comparison order;
4. one simple pooled, swap-symmetric, partner-conditioned architecture and only
   the ablations required to separate backbone capacity, nonlinear pair-head,
   and partner-gating effects;
5. optimizer, batch, checkpoint/restart, hyperparameter-budget,
   reproducibility-seed, fixed-pass stopping, numerical-failure, compute, and
   storage rules;
6. the training-artifact freeze that must precede a separately authorized
   development release, plus a nonadaptive development model-selection rule
   that permits no post-release retraining or new candidate;
7. the already frozen PU-R metrics and uncertainty hierarchy, C1/C2/C3
   reporting order, degree/hub analyses, and a view-only C1 novel-U
   sensitivity with unchanged rows and weights;
8. evidence thresholds for retaining the simple partner-conditioned model or
   proposing a more complex architecture; and
9. fail-closed model-level kill criteria when degree, graph, length,
   sequence-similarity, interolog, or frozen-PLM baselines explain the apparent
   gain.

Residue/interface prediction, structural labels, routing, retrieval,
calibration, full PLM fine-tuning, LoRA, custom pretraining, and external-panel
integration are outside this package.

## Immutable parent boundary

The work package must preserve without reconstruction or reinterpretation:

- the 17,000 exact reference-sequence endpoints and all frozen similarity
  graphs/components;
- the 11,900/2,550/2,550 endpoint/component split;
- exact pair identity, C1/C2/C3 roles, quarantine, visibility, sampler,
  probability, weight, metric, bootstrap, and protected-custody rules;
- the public training package exactly as accepted by `DEC-0026`; and
- the external-only status of the Lambourne, TF-isoform, Negatome, and IntAct-
  negative evidence families.

Unlabeled observations remain unlabeled. A ranking loss may contrast P with U
only as a sampled comparison distribution; it may not create a scientific
negative class, pseudo-negative artifact, prevalence estimate, or probability
target.

## Required validation and return

The production audit and an independently implemented validator must run from
clean commits through the checksum-pinned ARM64 data SIF. They must verify the
exact parent hashes, design-only authorization, protected-path exclusions,
model revisions and weight hashes, long-sequence embedding rule, baseline
formulas, objective algebra, P/U coverage, design-weight handling, symmetry,
bounded search matrix, seeds, fixed stopping, development freeze/release
ordering, metric hierarchy, stratification, novel-U conditioning, complexity
gate, kill criteria, and continuing prohibitions.

The package must return with an immutable machine-readable production audit,
independent validation report, scientific protocol/report, numbered acceptance
decision, new gate, updated project status, and a fresh restart checkpoint.

## Continuing prohibitions

This decision does not authorize:

- model/checkpoint/tokenizer download or local model-cache population;
- a new container build or model-runtime qualification;
- embedding extraction, feature-cache construction, model implementation,
  training, tuning, checkpoint creation, scoring, or evaluation;
- development release or any development identity, label, score, or metric;
- protected-candidate or protected-truth access, scorer execution, prediction,
  or metric computation;
- additional pair/sample rows, negative or pseudo-negative construction, or
  full candidate-universe materialization;
- endpoint, leakage-graph, component, split, C1/C2/C3, PU-R, pair-artifact, or
  protected-package modification;
- external diagnostic panels, structures, residue/interface labels, teachers,
  text-mined evidence, or post-cutoff PPI evidence; or
- probability, calibration, prevalence, biological-precision,
  universal-nonbinding, unseen-family, PLM-unseen, or exhaustive-homology
  claims.

Training may begin only after this protocol is independently validated and
accepted by a later numbered governance decision, and then only if another
numbered decision separately authorizes the exact implementation stage.
