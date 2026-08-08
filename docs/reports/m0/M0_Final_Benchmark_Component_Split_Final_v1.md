# M0 final benchmark component split

**Split:** `final_benchmark_component_split_v1`

**Date:** 2026-08-08

**Primary design:** reference-sequence positive-unlabeled ranking (PU-R)

**Disposition:** technically complete, independently validated, and suitable
for freezing as the benchmark endpoint/component partition skeleton

## 1. Executive disposition

A valid final component split was obtained under the prespecified primary 30%
`local_domain_union` hard rule. The primary search produced 2,653 valid
allocations among 4,096 deterministic candidates. The lexicographically
selected candidate was index 1,064. Because primary candidates passed, the
30% `sensitive_fl80_union` fallback was not evaluated.

The selected allocation has exact endpoint counts of 11,900 training, 2,550
development, and 2,550 protected test, matching 70%/15%/15% without any
component crossing. It has zero cross-partition edges and zero split
components under both `local_domain_union` and `sensitive_fl80_union` at 30%
identity.

Independent validation rebuilt both graphs, repeated the complete 4,096-
candidate search and frozen objective, verified all 17,000 endpoint and 7,782
component assignments, and reconstructed every consequential aggregate. All
20 checks passed with zero warnings and zero failures.

This is a partition skeleton only. No candidate-pair universe, positive-pair
row, evidence-indicator row, negative or pseudo-negative, or pair-level
C1/C2/C3 assignment was created. No model, embedding, prediction, performance
result, external panel, or structural label was used.

## 2. Frozen inputs and execution

The split consumes, without reopening or recomputing them:

- the immutable 17,000 exact reference-sequence endpoints accepted by
  `DEC-0018`;
- the accepted 58,049 released-positive sequence-pair union, reconstructed
  transiently for aggregate opportunity checks;
- the accepted 30% full-length graph and the full-length/local-domain
  sensitivity edge artifacts accepted by `DEC-0020`; and
- the primary reference-sequence PU-R estimand.

Production ran from clean commit
`d348a027243e3409fefd62bb1027e774dbb7cde6`. Independent validation ran from
clean commit `410b0d0d19c53008e35c4bdac3c286da0b249d26` through the pinned ARM64
Apptainer image with SHA-256
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.

## 3. Preregistered allocation and selection

`DEC-0021` and `configs/final_benchmark_component_split_v1.yaml` froze every
selection rule before production:

- primary hard rule: 30% `local_domain_union`;
- fallback: 30% `sensitive_fl80_union`, evaluated only if zero primary
  candidates pass all gates;
- candidate count: 4,096 per evaluated definition;
- deterministic seed: `20260803`;
- public salt: `ipin-openppi-final-benchmark-component-split-v1`;
- component order: salted SHA-256 base order followed by a candidate-specific
  coprime cyclic permutation;
- allocation: assign each whole component to the largest relative endpoint
  deficit, with train/development/test as the exact tie order;
- score quantization: nearest-integer half-up at scale 1,000,000,000; and
- final tie: lowest candidate index.

All acceptance criteria were conjunctive. Each candidate had to satisfy:

- at most 0.03 absolute endpoint-fraction deviation in every partition;
- at least 500 released-positive pairs and 50 participating components in each
  C1/C2/C3 opportunity pool;
- at least 50 HI-II-14 and 50 HuRI pairs in every opportunity pool;
- at most 0.10 absolute source-presence deviation from the global released-
  positive union;
- at most 0.35 relative development/test imbalance for each C2/C3 source
  count;
- at most 0.10 degree-mass deviation and 0.10 global-hub placement deviation
  from endpoint targets; and
- zero selected-rule cross-partition edges and split components.

Valid candidates were ranked lexicographically by endpoint balance, minimum
normalized evidence retention, development/test opportunity balance, source
composition, degree mass, global-hub placement, total endpoint count error,
and candidate index. Model output was not an available input.

## 4. Search result and fallback disposition

| Quantity | Result |
|---|---:|
| Primary candidates evaluated | 4,096 |
| Primary candidates passing every frozen gate | 2,653 |
| Selected candidate index | 1,064 |
| Fallback evaluated | No |
| Selected maximum endpoint-fraction deviation | 0.000000 |
| Selected minimum normalized evidence ratio | 4.530000 |
| Selected maximum source-presence deviation | 0.046800 |
| Selected maximum development/test opportunity imbalance | 0.105980 |
| Selected maximum degree-mass deviation | 0.066234 |
| Selected maximum global-hub placement deviation | 0.091176 |

The non-exclusive primary failure counts were 489 endpoint-balance failures,
997 development/test opportunity-balance failures, 367 hub-balance failures,
21 source-composition failures, 9 degree-mass failures, and 2 component-floor
failures. No candidate failed a released-positive-pair or per-source floor.

Because 2,653 primary candidates passed, the fallback trigger was false. No
fallback candidate was generated, evaluated, or selected.

## 5. Frozen endpoint and component allocation

| Partition | Endpoints | Fraction | Components | Singletons | Largest component | Internal released-positive pairs |
|---|---:|---:|---:|---:|---:|---:|
| Training | 11,900 | 0.700000 | 5,427 | 3,992 | 1,624 | 23,823 |
| Development | 2,550 | 0.150000 | 1,071 | 796 | 643 | 2,265 |
| Protected test | 2,550 | 0.150000 | 1,284 | 931 | 111 | 2,379 |
| **Total** | **17,000** | **1.000000** | **7,782** | **5,719** | **1,624** | — |

The 1,624-endpoint primary component is in training; the largest development
component has 643 endpoints and the largest test component has 111. The exact
balance is an outcome of the preregistered search, not a post-result adjustment.

## 6. Released-positive C1/C2/C3 opportunities

These are aggregate opportunity counts, not pair-level benchmark assignments.

| Axis/pool | ALL pairs | Components | HI-II-14 pairs | HuRI pairs |
|---|---:|---:|---:|---:|
| C1 training holdout pool | 22,333 | 2,182 | 4,216 | 19,827 |
| C2 development | 11,455 | 2,187 | 2,748 | 9,680 |
| C2 protected test | 13,633 | 2,516 | 2,784 | 11,975 |
| C3 development | 2,265 | 353 | 588 | 1,953 |
| C3 protected test | 2,379 | 505 | 510 | 2,110 |

HI-II-14 and HuRI values are source-presence counts; a pair present in both
sources contributes to both columns, so those columns are not additive.

C1 is necessarily a training-endpoint pool: both proteins must be exposed in
interaction-supervised training while the future evaluation pair is withheld.
This skeleton does not allocate C1 pairs between development and test. C2 and
C3 opportunity counts are inherent to the endpoint partitions shown above.

All pools exceed the frozen 500-pair, 50-component, and 50-pairs-per-source
floors. Future evidence grouping, temporal/source/assay constraints, and actual
pair allocation may reduce these opportunities and require their own
authorization and gates.

## 7. Source, degree, and hub balance

The selected partition shares of total ALL released-positive endpoint degree
are 0.633766 training, 0.172079 development, and 0.194155 test. The maximum
absolute deviation from the 70%/15%/15% endpoint targets is 0.066234, within
the frozen 0.10 limit.

For the global top 1% of ALL positive-degree endpoints (170 endpoints), the
partition counts are 105 training, 24 development, and 41 test, corresponding
to fractions 0.617647, 0.141176, and 0.241176. The maximum deviation is
0.091176, within the frozen limit. Top-5% and top-10% placement also pass.

The selected maximum source-presence deviation across all opportunity pools is
0.046800. The selected maximum matched development/test C2/C3 source-count
imbalance is 0.105980. HuRI remains the dominant released-positive source, as
it is in the immutable parent evidence; the allocator preserves source
representation rather than manufacturing equal source prevalence.

## 8. Independent leakage verification

| Definition | Edges | Components | Largest component | Cross-partition edges | Split components |
|---|---:|---:|---:|---:|---:|
| 30% `local_domain_union` | 176,264 | 7,782 | 1,624 | 0 | 0 |
| 30% `sensitive_fl80_union` | 63,180 | 11,292 | 362 | 0 | 0 |

The local/domain graph is the selected hard partition rule. The independently
verified zero counts under the full-length sensitivity union provide the
required secondary check. These heuristic graphs do not prove exhaustive
nonhomology or define biological families.

## 9. C3 definition and claim boundary

For this frozen skeleton, C3 means exactly:

> Both exact frozen reference-sequence endpoints are absent from
> interaction-supervised training and component-disjoint from training under
> `local_domain_union_v1` at 30% identity.

Development- and test-assigned endpoints are ineligible for future
interaction-supervised training. This supports the exact operational statement
above only. It does not support:

- unseen biological family or family-generalizing performance;
- unseen gene, isoform, homolog, domain architecture, or universal protein
  novelty;
- PLM-unseen protein or absence from pretraining corpora;
- proven nonhomology or exhaustively homology-free evaluation;
- universal-nonbinding, prevalence, or calibrated-probability claims; or
- any model-performance or experimental-validation claim.

## 10. Scope and continuing holds

The primary PU-R design remains unchanged. Unreported eligible pairs remain
unlabeled. No negatives or pseudo-negatives were created, and the full
candidate-pair universe was not materialized or sampled.

The TF-isoform and Lambourne panels were not inputs. They remain external-only
and closed. In particular, the TF-isoform panel remains unsuitable for training
negatives or any training role, universal-nonbinding claims, prevalence,
calibration, and unseen-endpoint or family benchmarking.

This package does not authorize pair-level benchmark construction, external-
panel integration, structural-label work, model implementation, embedding,
training, tuning, selection, calibration, or evaluation.

## 11. Immutable evidence

| Evidence | SHA-256/result |
|---|---|
| Production audit report | `bbb8e65efd661342b22f54a6fa72ffe4115dfc1e18b4f97d066e4124fe9124c8` |
| Independent validation report | 20 pass, 0 warning, 0 fail; `e0864a857285c21341ce4db44d1a142ff6532101804ead5b8f421df6ab4d6e0f` |
| Production run manifest | `615051b335c25351a46a6de0eba8b87c9a82391cf7c63216c21280846b06d52e` |
| Canonical split manifest | `81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a` |
| Frozen configuration | `b8dac7c7de5fc3935a5bf642afe12b2b5e7e5b40fa9883d1dc04962bfed25ecf` |
| Canonical schema | `e18c999753640c7d3b15bdaee60636d329b94ae3876cfaffc2290b7f1536ed30` |

## 12. Final disposition

Accept `final_benchmark_component_split_v1` as technically complete and freeze
its endpoint/component assignments as the benchmark partition skeleton. The
primary `local_domain_union` definition passed; fallback was neither needed nor
evaluated. The exact-endpoint, named-rule C3 wording is permitted, while unseen
biological-family, PLM-unseen, exhaustive-homology, prevalence, calibration,
and universal-nonbinding interpretations remain prohibited.
