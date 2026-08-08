# M0 Pair-Level PU-R Benchmark Artifacts Final v1

**Date:** 2026-08-08

**Status:** Technically complete, independently validated, accepted by
`DEC-0026`, and frozen as the model-free pair-level benchmark package

## Disposition

The expert-group construction request is valid under the immutable `DEC-0024`
protocol. `pair_level_pu_r_benchmark_artifacts_v1` was constructed from clean
implementation commit `043bd73f4b0e6d102b339b5ac66213a88674bb94` and
independently validated from clean production-evidence commit
`7dc5e0ea1bfb87526178d569350bdb4d86c15559`.

Construction completed without warnings or failures. The independent validator
passed 13 checks with zero warnings and zero failures. No model, embedding,
score, prediction, metric, tuning result, external panel, structure, negative,
or pseudo-negative was created or used.

The package preserves the primary reference-sequence positive-unlabeled
ranking design. Every unreported eligible pair remains unlabeled, not negative.

## Immutable parent and pair semantics

The accepted 17,000 endpoint, 7,782 `local_domain_union_30` component, and
11,900/2,550/2,550 train/development/test partition skeleton is unchanged.
The evidence cutoff remains the published-2020 HI-II-14/HuRI snapshot frozen
by `DEC-0024`. Pair ordering, full SHA-256 identity, C1 role hashing, exposure
guards, exclusive C2, C3, quarantine, source-exclusive diagnostics, degree
strata, sample caps, salts, seeds, and Hamilton allocation are unchanged.

C3 continues to mean only that both exact frozen sequence endpoints are absent
from interaction-supervised training and component-disjoint from training
under `local_domain_union_30`. It does not mean unseen biological family,
unseen domain, PLM-unseen protein, or exhaustive nonhomology.

## Frozen package layers

| Layer | Positive rows | Sampled-unlabeled rows | Visibility |
|---|---:|---:|---|
| Public training | 16,799 | 2,000,000 | Public training artifact |
| Encrypted development | 26,108 across primary and source cells | 9,000,000 | Sealed; release not authorized |
| Encrypted protected candidates | 28,821 across primary and source cells | 9,000,000 | Sealed separately from truth |
| Encrypted protected truth | 28,821 truth rows plus the 58,049-row role ledger | 9,000,000 | Evaluator/curator only |

The encrypted development package additionally contains 18,081 source-visible
training-positive rows: 14,829 for the HI-II-14-target diagnostic and 3,252 for
the HuRI-target diagnostic. These are supported visible-evidence subsets, not
new labels.

The persisted state vocabulary is exactly `released_positive` and `unlabeled`.
No negative, pseudo-negative, nonbinding, evidence-absence, or probability
state exists.

## Primary positive and sampling results

| Cell | Positive pairs | Unlabeled population | Sample rows | Strata |
|---|---:|---:|---:|---:|
| Training | 16,799 | 10,902,230 | 2,000,000 | 36 |
| C1 development | 3,259 | 10,902,230 | 1,000,000 | 36 |
| C1 test | 3,187 | 10,902,230 | 1,000,000 | 36 |
| C2 development | 11,327 | 11,909,923 | 1,000,000 | 8 |
| C2 test | 13,446 | 11,907,804 | 1,000,000 | 8 |
| C3 development | 2,265 | 3,247,710 | 1,000,000 | 1 |
| C3 test | 2,379 | 3,247,596 | 1,000,000 | 1 |

All twelve strict source-exclusive development/test cells were also realized
at their inherited 1,000,000-row caps. Across all 19 samplers, the validator
independently verified 20,000,000 rows against 129,614,029 cell-specific
unlabeled opportunities.

Every nonempty stratum received its frozen allocation. Every selected row was
independently proven to lie at the exact bottom-hash threshold, with the
prescribed salt, seed, cell identifier, stratum identifier, pair identifier,
full 256-bit ordering, and tie-break. Inclusion probabilities and weights were
verified as exact reduced rational values.

## Role and leakage validation

The complete independently reconstructed released-positive ledger is:

| Role | Pairs |
|---|---:|
| Training | 16,799 |
| C1 development / test | 3,259 / 3,187 |
| C2 development / test | 11,327 / 13,446 |
| C3 development / test | 2,265 / 2,379 |
| Quarantine | 5,387 |
| **Total** | **58,049** |

Consequential leakage checks all passed:

- zero positive pairs occupied more than one primary role;
- zero development/test endpoints entered interaction-supervised training;
- zero training-sample rows were released positives;
- zero sampled-unlabeled rows were released positives in their governing cell;
- zero protected pair identities appeared in public JSON or workflows;
- zero protected-candidate rows were missing, extra, or duplicated; and
- the exact protected candidate union contained 9,028,821 rows.

## Prespecified cross-cell reuse

`DEC-0024` defines independent samplers by cell identifier and does not impose
cross-cell unlabeled-pair exclusivity. Production therefore contains
20,000,000 cell rows representing 15,536,850 distinct pair identifiers.
3,778,512 pair identifiers occur in more than one cell, producing 4,463,150
rows beyond the first occurrence; one pair appears in at most seven cells.

Pair-identity overlap across visibility groupings is 504,264 for
training/development, 505,482 for training/protected-test, and 1,017,784 for
development/protected-test. Independent validation confirmed zero
positive-as-unlabeled rows. This is permitted deterministic design reuse, not
positive-evidence or label leakage, and may not be reinterpreted as negatives.

## Protected-test sealing and evaluator boundary

A public protected candidate list would disclose positive identities by set
difference because the universe and deterministic sampler are public.
Accordingly, candidate and truth packages use distinct keys and remain sealed.
A future prediction submission means a frozen scorer executed in a verified
no-network evaluator, not a public pair-keyed prediction file.

The controlled candidate opener persists exactly four scorer fields:
`candidate_token`, `endpoint_a_sha256`, `endpoint_b_sha256`, and `cell_id`.
Unprojected evaluator metadata is deleted with the temporary decrypt workspace.
Predictions must be complete, unique, finite, and hashed before truth access.
The evaluator rehashes the frozen scorer and session manifest, then atomically
reserves the one-first ledger before decrypting truth. An interrupted attempt
remains consumed. Only aggregate receipts may be written beneath
`artifacts/validation/protected_evaluation_receipts/`.

Development, candidate, and truth private keys are distinct, unversioned,
account-protected, and mode `0600`. The versioned public-certificate
fingerprints are:

- development: `8845d4bccb1c999b70f3dd9189be9b09ee525ebff39f63e1176dbdf1847f98e7`;
- protected candidates: `cf6d5ecdd71efb5fbcecb68f0db82fd5bca6de1346712425603c3688a8b107e2`; and
- protected truth: `29551b486d4b814ee255960cb831db88b52ac68c3c44cf155493b3ff6a5c671c`.

Development release, protected candidate access, scoring, truth access, and
metric computation were not performed and remain separately unauthorized.

## Qualification logging note

During preproduction validator debugging, one identity-safe error path had not
yet been applied and a single curator-only quarantine pair hash appeared in a
transient operator log. It was not a training, development, or protected-test
positive identity; no protected-test positive was exposed. The log was not
versioned or admitted to any model-development workflow. All exceptions were
then made identity-safe, regression-tested, and the complete smoke and
production validations rerun successfully. The affected pair remains
quarantined and cannot enter training or evaluation.

## Claim ceiling and continuing hold

The package supports later released-positive PU retrieval evaluation only.
Unlabeled-is-negative, universal-nonbinding, biological precision, prevalence,
calibration, probability, unseen-family, PLM-unseen, and exhaustive-homology
claims remain prohibited. Exact full-universe rank and Recall@K metrics remain
demoted unless a later authorization provides exact streaming full-universe
scoring.

The TF-isoform and Lambourne panels remain external-only and unused. In
particular, the TF-isoform panel remains unsuitable for training negatives or
any training role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

No next work package is authorized. The frozen rows and allocation may not be
modified. Development release, candidate access, model implementation,
embedding, training, tuning, selection, calibration, evaluation, routing, or
release requires a new numbered decision.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Artifact configuration | `cdafad900887e74a6148cdb6d6832e56392649703c261909d5f581e39fd9e795` |
| Package manifest | `f0f850daf795481c8a1ae0ba64f6d050ae757f2738497ac0517003c6822015f5` |
| Construction report | `878beb38af78157b8b4b3ff50cb7658266900add86a96d7d9e5baca8745c3f65`; complete |
| Independent validation | `7eede006ba18dbc4dcc71128743722718bc73f0f6891834ad4ebc0a6ed614e86`; 13 pass |
| Implementation/production commit | `043bd73f4b0e6d102b339b5ac66213a88674bb94` |
| Validation input commit | `7dc5e0ea1bfb87526178d569350bdb4d86c15559` |
| Frozen split manifest | `81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a` |

The 1.9 GiB package remains in its designated project-local canonical root and
is intentionally excluded from Git. Its manifests, report hashes, public
certificates, construction code, evaluator procedure, and independent
validation evidence are versioned.
