# DEC-0025: Authorize pair-level PU-R benchmark artifact construction

**Date:** 2026-08-08

**Status:** Accepted and effective for this construction-only work package

**Decision basis:** Explicit project-owner instruction conveying the expert
group's bounded construction request

**Controlling record:** DEC-0024

## Decision

Authorize construction and freezing of
'pair_level_pu_r_benchmark_artifacts_v1' exactly under the immutable DEC-0024
protocol. This decision authorizes pair-level persistence only for the frozen
training, development-release, and protected-test evaluation packages defined
below. It does not authorize any model work or any protocol change.

The construction must use the immutable 17,000 endpoint universe,
'final_benchmark_component_split_v1', the published-2020 HI-II-14/HuRI evidence
snapshot, the frozen C1 hash rule, exposure guards, C1/C2/C3 assignments,
source-exclusive diagnostics, deterministic bottom-hash sampling, rational
inclusion probabilities and weights, and all DEC-0024 claim boundaries.

## Authorized artifact boundaries

1. The public training package may contain only the 16,799 training-role
   released-positive pairs, their training-positive degree metadata, and the
   prescribed 2,000,000-row sample whose state is exactly 'unlabeled'.
2. The development package must contain the prescribed primary development
   positive censuses and unlabeled samples plus supported named-source
   development diagnostics. It remains encrypted until a future training
   artifact hash is frozen. No release is authorized by this decision.
3. The protected-test scorer-input package must be encrypted separately from
   protected truth. Candidate identities may be opened only inside a
   no-network evaluator after the submitted scoring artifact is frozen.
4. The protected-test truth package must use a distinct private key. Predictions
   must be complete, validated, and hashed before truth access. Only aggregate
   metric output may leave the evaluator.
5. A curator/evaluator-only role ledger may contain the complete released-
   positive union, primary role or quarantine state, and source-diagnostic
   roles. It must remain inside the protected-truth package.

Public certificates and their fingerprints are versioned evidence. Private
keys must be non-versioned, account-protected, mode-0600 evaluator escrow. The
development-release, protected-candidate, and protected-truth keys must be
distinct.

## Protected-test non-inference rule

A public protected-test candidate list is prohibited. Because the endpoint
universe, sampler salt, seed, and selection rule are public, publishing a list
formed from all evaluation positives plus the sampled unlabeled rows would
make positive identities inferable by set difference.

Accordingly, “prediction submission” means submission of a frozen scoring
artifact for execution inside the sealed evaluator. It does not mean a public
pair-keyed score file. Candidate rows, internal predictions, and positive truth
remain evaluator-private. The evaluator must project only label-free scorer
inputs and reject extra, duplicate, missing, nonfinite, or unknown prediction
rows before hashing the accepted prediction artifact.

## Sampling and overlap interpretation

The exact frozen hash payload is
'{salt}:{seed}:unlabeled:{cell_id}:{stratum_id}:{pair_id}' with salt
'ipin-openppi-benchmark-v1' and seed '20260803'. Every nonempty stratum receives
one seat before Hamilton proportional apportionment; the selected rows are the
lowest full SHA-256 digests, breaking ties by pair identifier.

DEC-0024 assigns separate samplers to separate cell identifiers. It does not
declare unlabeled pair identities exclusive across cells. Cross-cell reuse of
an unlabeled pair is therefore permitted, must be quantified, and must not be
misreported as evidence or label leakage. The following remain hard failures:

- any released-positive pair represented as training-unlabeled;
- any positive pair occupying multiple primary positive roles;
- any development or test positive identity visible in the training package;
- any test candidate or truth identity visible in a development artifact;
- any development/test endpoint entering interaction-supervised training;
- any source-visible pair represented as unlabeled in its source diagnostic;
- any role, sample, inclusion probability, weight, hash, or stratum differing
  from the frozen protocol.

## Independent validation

Construction and an independently implemented validator must run from clean
commits through the pinned ARM64 Apptainer image. They must verify:

- all immutable parent hashes and all 17,000 endpoint/component assignments;
- complete pair grouping, exact role/quarantine counts, and primary role
  exclusivity;
- every primary and source-specific C1/C2/C3 assignment;
- candidate-population algebra, every stratum allocation, selected bottom
  hashes, rational inclusion probabilities, and design weights;
- row counts, table hashes, deterministic archive hashes, CMS ciphertext
  hashes, public-certificate fingerprints, and private-key permissions;
- no positive/evidence leakage across training, development, and test;
- zero public test pair identities and separate candidate/truth encryption;
- explicit cross-cell unlabeled overlap counts; and
- continuing absence of negatives, pseudo-negatives, external panels,
  structural labels, split mutation, and model operations.

Smoke qualification must use only '_smoke_' outputs. Production must refuse a
dirty tracked worktree and must write new versioned outputs atomically and
read-only. The production construction evidence must be committed before the
independent validator is run.

## Evaluation procedure boundary

The package may implement and fixture-test a read-only evaluation harness. No
real model, embedding, score, prediction, metric, tuning choice, or evaluation
is authorized in this work package. A later model authorization must freeze the
scorer/container and its information provenance before candidate access.

Exact full-universe Recall@K and exact rank metrics remain conditional on later
streaming full-candidate scoring. A sampled candidate set may not be renamed the
full universe. Unsupported exact metrics must be demoted exactly as DEC-0024
requires.

## Continuing prohibitions

This decision does not authorize:

- modification or reinterpretation of DEC-0024 or the frozen split;
- materialization of the full candidate-pair universe;
- a 'negative', 'nonbinding', or pseudo-negative state;
- external diagnostic-panel integration or parent-audit reopening;
- structural mapping or structure-derived labels;
- model implementation, embeddings, training, tuning, model selection,
  calibration, evaluation, routing, or release;
- study, assay, temporal, family, domain, PLM-unseen, or exhaustive-homology
  claims beyond the frozen operational wording; or
- prevalence, biological precision, probability, calibration,
