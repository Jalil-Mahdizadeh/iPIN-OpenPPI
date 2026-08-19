# DEC-0032: Authorize development release and frozen-scorer evaluation

**Date:** 2026-08-19

**Status:** Accepted and effective for the bounded development-only work package
defined here; protected-test access remains prohibited

**Controlling records:** `RESUME-004`, `DEC-0028`, `DEC-0031`, gate v30, and
the complete Stage 1 training-artifact registry with SHA-256
`11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318`

## Decision

Authorize one bounded development-release and evaluation stage under the exact,
unchanged `DEC-0028` protocol. The work package may implement and independently
qualify a development-only release/scoring/evaluation pipeline, decrypt the
development package only after that qualification passes, score every frozen
method, calculate every preregistered development metric and diagnostic, apply
the frozen selection and kill rules, and return to governance with one of the
three permitted dispositions.

This decision does not authorize protected-candidate or protected-truth access,
protected scoring, new training, checkpoint change, tuning, or protocol change.

## Preconditions accepted

`DEC-0031` established, before any development access, that all 30 runs were
complete; all selected checkpoints and 10 ensemble definitions were frozen;
the complete code/config/runtime/input/embedding/checkpoint registry was
hash-fixed; and independent validation passed. The exact `RESUME-004` preflight
was repeated from clean `main` at
`dc6dbb2cf938bcc19c1b1dd423af92a0ed94b067`: local and remote were equal, all
authority and evidence hashes matched, all sealed ciphertext hashes were
unchanged, and the complete read-only unit suite passed 260 of 260 tests.

## Authorized implementation and pre-release gate

Before decryption, the project may implement only the release, scoring,
metric, bootstrap, diagnostic, selection, registry, and validation code needed
to execute the frozen protocol. It must freeze a machine-readable execution
configuration that is a lossless projection of `DEC-0028`, not an amendment.

A production audit and a separately implemented validator must pass before the
development private key is used. Together they must verify:

1. the exact authority, protocol, container, public inputs, embedding registry,
   training registry, 30 selected checkpoints, and 10 ensembles;
2. exactly nine deterministic mandatory controls and no added scorer;
3. exact score symmetry, completeness, uniqueness, finiteness, ensemble
   arithmetic, and model/source hashes on synthetic or public-training-only
   fixtures;
4. exact HT concordance, half-tie handling, paired component bootstrap,
   degree/hub, source-exclusive, seed-stability, novel-U, quantization,
   selection, fallback, and kill-rule implementations;
5. an allowlist that admits only public frozen artifacts plus, after this gate,
   the released development workspace; and
6. a development-only key resolver that neither resolves, stats, reads, hashes,
   copies, mounts, nor uses either protected private key.

The existing construction-time package configuration remains immutable. Its
historical `development_release: false` field is not edited; this numbered
decision supplies the later authority it anticipated.

## Authorized development release

After the pre-release gate passes, authorize exactly one decryption of
`data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms`
with ciphertext SHA-256
`bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41`.
Only the matching development certificate and
`.private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem`
may be used. The decrypted deterministic archive must hash to
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`.

Plaintext development rows, pair identities, score rows, and private keys stay
under the account-protected, Git-ignored `.private/` boundary. Public evidence
may contain only aggregate results, counts, hashes, scorer IDs, and custody
receipts that expose no protected identity and no private-key material.

The protected-candidate and protected-truth ciphertexts may be rehashed but
must remain encrypted. Their private keys and plaintext archive hashes must not
be used for this stage.

## Exact scorer census

Score all development primary and source-exclusive rows with exactly:

- nine deterministic controls: salted full-SHA-256, endpoint-degree sum,
  preferential attachment, component degree-mass product, common neighbors,
  log-length sum, negative absolute log-length difference, exact within-pair
  contiguous 3-mer cosine, and exact orientation-invariant training-interolog
  3-mer score;
- all 30 training-selected checkpoints in the frozen registry; and
- the 10 frozen candidates, each defined only as the arithmetic mean of its
  three seed scores.

The frozen sequences, training-positive graph, component mapping, pooled
embeddings, normalization, selected pass, checkpoint bytes, scorer code, and
ensemble membership may not change. Score caching may remove duplicate
computation only when keyed by exact pair ID and scorer hash; it may not change
a row or score.

## Exact evaluation and reporting

Use only HT positive-versus-U pairwise concordance with half credit for exact
ties. Report C3 first, then C2, then C1; never pool cells. Preserve all original
rational design weights. Use the exact paired two-endpoint-component
pigeonhole bootstrap with 2,000 PCG64DXSM replicates, seed `20260803`, and
percentile-95 intervals on identical rows and component draws.

Required development outputs are:

1. primary C3, C2, and C1 metrics for every deterministic scorer, every seed
   checkpoint, and every ensemble;
2. paired deltas and intervals against the strongest mandatory baseline and,
   where applicable, the 650M linear and matched no-gate candidates;
3. all within-candidate three-seed cell ranges and the `0.02` eligibility test;
4. every supported degree-pair stratum plus top-1%, top-5%, and top-10% hub
   versus non-hub views, retaining the 100-positive/10-component floor;
5. HI-II-14-exclusive and HuRI-exclusive development cells as report-only
   diagnostics;
6. the prespecified C1 novel-U view, retaining only frozen C1 U pair IDs absent
   from public training U, with original rows and weights, required counts, and
   no selection use; and
7. diagnostic-only sampled AUROC/AUPRC and score correlations where the frozen
   protocol calls for them, with no biological-classification interpretation.

Selection uses unrounded metrics for reporting and decimal-`0.001`
`ROUND_HALF_UP` only for the exact cascade: C3, C2, C1, lower frozen complexity,
then lexicographically ascending candidate ID. Individual seeds, novel-U, and
source-exclusive cells cannot select a candidate.

## Complexity and kill rules

Apply every `DEC-0028` threshold without interpretation drift. Retain a
partner-gated candidate only with C3 gain at least `0.02` over the strongest
simple sequence baseline with paired interval excluding zero, at least `0.01`
over the 650M linear candidate with paired interval excluding zero, at least
`0.005` over the matched no-gate candidate with paired interval excluding zero,
positive direction in at least one supported named-source cell, gain outside
top-10%-hub pairs, and all three seeds stable and eligible.

Failure removes complexity in order: partner gate, nonlinear head, then 650M
scale. Stop the learned line if no learned candidate beats deterministic
controls. The programme must stop before protected evaluation when any frozen
model-level kill criterion fires, including no qualifying learned C3 gain, best
learned C3 lower bound not above `0.5`, shortcut explanation without qualifying
C2/C3 gain, complex delta explained by interolog or frozen-PLM-linear scoring,
hub-only gain, seed instability, integrity failure, or unsupported claim need.

## Reproducibility, compute, and freeze

Use the accepted ARM64 containers, offline execution, deterministic algorithms,
and one NVIDIA GH200 120 GB at most. No encoder inference is needed because the
pooled embeddings are frozen. This stage is bounded by 30 GPU-hours, 100 GiB of
new governed storage, and no SLURM or multi-GPU requirement. A resource ceiling
increase requires a new numbered decision and cannot change scientific rules.

Freeze code, execution config, release receipt, development manifest hash,
score-file hashes, logs, metric tables, bootstrap draws or draw hashes,
diagnostics, selection trace, kill-rule trace, compute/storage accounting, and
one complete development-evaluation registry. Commit production evidence before
implementing the independent final validator. The validator must independently
rehash and recompute all consequential results without importing the production
metric/selection implementation.

## Required governance return

Return with exactly one evidence-supported disposition:

1. advance a completely frozen eligible scorer toward separately authorized
   protected evaluation;
2. retain only the simplest eligible baseline supported by the fallback rules;
   or
3. stop the complex-model claim and, if a model-level kill criterion requires
   it, stop before protected evaluation entirely.

No protected action follows automatically. Even an advance disposition requires
a new numbered decision after the final scorer, dependencies, and predictions
procedure are frozen.

## Continuing prohibitions

Protected-candidate or truth access, protected private-key access, new training
or retraining, checkpoint or ensemble change, tuning, adaptive thresholds,
additional scorers, new architectures or ablations, negatives or
pseudo-negatives, benchmark modification, external-panel integration,
structures or residue/interface modelling, full-universe materialization,
probability/calibration/prevalence claims, and unsupported exposure/family/
temporal/source claims remain prohibited.
