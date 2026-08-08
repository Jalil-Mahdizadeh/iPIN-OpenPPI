# Protected pair-level PU-R evaluation procedure

**Version:** 1
**Controls:** DEC-0024 and DEC-0025
**Package:** pair_level_pu_r_benchmark_artifacts_v1

## Binding visibility boundary

Unlabeled rows are not negatives. This package supports recovery and ranking of
released-positive evidence; it does not identify prevalence, biological
precision, calibrated probability, or universal nonbinding.

The protected candidate list must not be public. The endpoint universe, sample
salt, seed, strata, and bottom-hash rule are public, so publishing all protected
positives plus the deterministic unlabeled sample would make positive
identities inferable by set difference. A prediction submission is therefore a
frozen scorer executed inside the evaluator, not a public pair-keyed score
file. Candidate identities, predictions, and truth remain evaluator-private.

## Package boundaries

- `training/` contains only training-role positives, the training unlabeled
  sample, rational probabilities and weights, and nonidentifying manifests.
- `sealed/development_release.cms` contains development and supported
  source-exclusive artifacts. It cannot be released until a future training
  artifact SHA-256 is frozen.
- `sealed/protected_candidates.cms` contains the label-free candidate table and
  evaluator-only routing/validation metadata. The controlled opener persists
  only the exact four-column scorer projection; it retains no pair identifier,
  state, truth, source membership, degree, stratum, component, or weight.
- `sealed/protected_truth.cms` contains protected positive identities, detailed
  unlabeled rows and weights, and the curator-only role ledger.

Development, candidate, and truth private keys are distinct. Only public
certificates are versioned. Private keys remain under non-versioned,
account-protected evaluator escrow with no group/world access. No private key or
decrypted identity may enter reports, logs, source control, model-development
mounts, or metric receipts.

## Development release

A separately authorized operator must verify the package, ciphertext,
certificate, and immutable training artifact before using the
`release-development` subcommand of
`scripts/benchmark/evaluate_pair_level_pu_r_benchmark_v1.py`. Output remains
under an account-protected `.private/` directory. Its receipt records the
training artifact SHA-256 and confirms that protected test was not accessed.
`DEC-0025` does not itself authorize release.

## Protected scoring

Before candidate access, governance must freeze the scorer, container,
dependencies, feature provenance, and permitted outputs. The evaluator runs
without network access and without model-development filesystems mounted.
'IPIN_EVALUATOR_NETWORK_ISOLATED=1' may be set only inside that verified
boundary.

The `open-protected-candidates` subcommand records the scorer SHA-256 before
candidate decryption. Unprojected candidate plaintext exists only in its
temporary decrypt workspace and is deleted before the scoring session is
persisted. The scorer session contains exactly `candidate_token`, two endpoint
sequence hashes, and `cell_id`; no component, degree, stratum, source, role,
state, or weight metadata remains. The scorer emits exactly `candidate_token`
and a finite symmetric `score` in Parquet. Missing, extra, duplicate, unknown,
or nonfinite rows are fatal. Scorer logs and predictions stay private because
they can form a covert identity channel.

## Prediction freeze and truth access

After scoring, the operator must:

1. close the scorer;
2. validate complete two-column prediction coverage;
3. compute and record the prediction SHA-256;
4. rehash the frozen scorer and verify the scoring-session sidecar;
5. verify that the package has no prior attempt and atomically reserve the
   package-scoped one-first ledger with an exclusive create;
6. only then provide the protected-truth key to the metric process; and
7. use `evaluate-protected` to emit aggregate metrics and hashes only.

The reservation is written before truth decryption and irrevocably consumes
the attempt even if decryption, metric computation, or receipt writing later
fails. Success adds a separate completion record and an aggregate-only receipt
under `artifacts/validation/protected_evaluation_receipts/`. Any rerun requires
a new protocol and split version. Editing or deleting custody records does not
create authorization.

## Metric boundary

The sealed harness computes Horvitz-Thompson-weighted positive-unlabeled
pairwise concordance separately by cell. The realized sample alone does not
support exact Recall@10/100/1000, exact positive rank percentile, or another
full-universe rank metric. Those remain demoted unless later authority provides
exact streaming full-universe scoring without materialization. The sample may
never be renamed the full universe.

Future uncertainty must use the frozen 2,000-replicate two-endpoint
local-domain-component pigeonhole bootstrap and paired draws. Construction
computes no model metric or uncertainty.

Every receipt must affirm prediction hashing before truth, unique finite
coverage, network isolation, one-first use, separate cells, no protected
identity output, no negative interpretation, no sampled-as-full metric, and no
prevalence, calibration, probability, biological-precision,
universal-nonbinding, family, PLM-unseen, or exhaustive-homology claim. Any
failed integrity, visibility, custody, or ledger check releases no metric.
