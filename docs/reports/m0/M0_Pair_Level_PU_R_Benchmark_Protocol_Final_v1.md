# M0 Pair-Level PU-R Benchmark Protocol Final v1

**Date:** 2026-08-08

**Status:** Technically complete, independently validated, and accepted by
DEC-0024 as the immutable protocol for any later pair-level benchmark
construction

## Disposition

The pair-level positive-unlabeled ranking protocol is internally consistent and
scientifically feasible under the frozen DEC-0022 endpoint/component split.
Production passed 16 checks with no warnings or failures. An independently
implemented validator passed 18 checks with no warnings or failures.

This package froze rules only. It emitted no positive-pair, unlabeled-pair,
candidate, evidence-indicator, or C1/C2/C3 rows; realized no unlabeled sample;
and performed no model, embedding, structure, external-panel, prevalence, or
calibration work.

The primary estimand remains recovery and ranking of withheld released-positive
evidence within a declared eligible candidate design. Unreported eligible pairs
are unlabeled, not negatives.

## Immutable parent

The protocol consumes, but does not modify, the DEC-0022 split:

| Partition | Endpoints | 30% local-domain components |
|---|---:|---:|
| Training | 11,900 | 5,427 |
| Development | 2,550 | 1,071 |
| Protected test | 2,550 | 1,284 |
| **Total** | **17,000** | **7,782** |

The hard separation rule remains 30% local_domain_union. C3 does not imply
unseen biological family, unseen domain, PLM-unseen protein, or exhaustive
nonhomology.

## Information cutoffs

| Information layer | Frozen cutoff | Later information |
|---|---|---|
| Positive evidence | Published-2020 HI-II-14/HuRI release union; acquisition run primary-raw-v1-20260803T135432Z; parsed 2026-08-03; reconciled 2026-08-03 | Not visible to training or development selection and not used for candidate exclusion |
| Sequences | UniProt release 2026_02; endpoint identity is the frozen reference-sequence SHA-256 | Sequence replacement or remapping prohibited |
| Partitions | final_benchmark_component_split_v1 frozen 2026-08-08 under 30% local_domain_union | Modification prohibited |
| External evidence/features | Structures, diagnostic panels, teacher predictions, text-mined or post-cutoff PPI evidence absent from this protocol | Requires separate authority and a new freeze |
| Future PLM provenance | Not yet frozen | Must be frozen before model authorization; no PLM-unseen claim is available |

The exact input manifests and their hashes, rather than publication year alone,
define the reproducible evidence snapshot.

## Evidence visibility

| Actor/stage | Visible evidence | Sealed evidence |
|---|---|---|
| Common before modeling | Frozen endpoint/component skeleton, protocol configuration and hashes, aggregate feasibility counts | Every pair identity and every sample identity |
| Benchmark curator/evaluator | Complete frozen positive union, pair roles, quarantine states, and later protected sample identities | Must not expose protected identities to model or tuner |
| Interaction-supervised training | Only C1 hash-role training positives with two training endpoints; only a later authorized training unlabeled sample | Withheld C1 identities, all development/test positive evidence, and all development/test endpoints as interaction supervision |
| Development | Development C1/C2/C3 positives only after the trained artifact hash is frozen; may guide selection and stopping | Every protected-test positive identity and metric |
| Protected test | Read-only evaluator after prediction artifact hashing | Hidden from training, tuning, and model selection; one first evaluation only |

Any protected-test rerun after seeing a result requires a new protocol and split
version. Source, assay, publication, or protected full-graph degree is not a
model feature.

## Pair identity and evidence co-location

A biological benchmark pair is one unordered pair of distinct exact frozen
reference-sequence SHA-256 endpoints, sorted ascending. Its identifier is the
full SHA-256 digest of endpoint_a, a literal vertical bar, and endpoint_b,
prefixed by pair:.

Reverse orientations, all detailed evidence records, source memberships,
construct/orientation variants, and repeated detection-method records for the
same pair share one role. No evidence group can cross training, development,
test, or an auxiliary holdout.

## Exact primary C1/C2/C3 assignment

### Label-blind C1 role

For every released-positive pair with two training-partition endpoints:

1. Hash the literal payload
   ipin-openppi-pair-level-pu-r-protocol-v1:20260803:primary:C1:{pair_id}
   with SHA-256.
2. Interpret the first eight digest bytes as an unsigned big-endian integer and
   reduce modulo 10,000.
3. Assign buckets 0-6,999 to training, 7,000-8,499 to development, and
   8,500-9,999 to test.

The hash does not use source, study, assay, endpoint degree, labels beyond
eligibility for this operation, or any model result.

Interaction-supervised training positives are exactly the train/train released
positives with C1 role training. A training endpoint is exposed only if its
degree is at least one in that training-positive graph.

### Evaluation cells

- **C1 development/test:** both endpoints are training-partition and exposed;
  the pair has the matching development/test hash role; the pair itself is
  absent from interaction-supervised training.
- **Exclusive C2 development/test:** exactly one endpoint is an exposed
  training endpoint and the other is in the named held-out partition.
- **C3 development/test:** both exact endpoints are in the same named held-out
  partition. They are absent from interaction-supervised training and their
  frozen components are disjoint from training under local_domain_union_30.

Development-test cross-partition positives, C1 pairs failing the exposure
guard, C2 pairs whose training endpoint is not exposed, self/same-sequence
pairs, ambiguous projections, and out-of-cutoff pairs are quarantined. They are
never reassigned.

The observed quarantine counts are 282 C1-development exposure failures, 296
C1-test exposure failures, 472 C2-development exposure failures, 688 C2-test
exposure failures, and 3,649 development-test cross-partition positives.

## Primary positive-evidence feasibility

The training graph contains 16,799 positive pairs and exposes 4,675 training
endpoints. The source counts below overlap where one pair has both sources.

| Cell | Positive pairs | Endpoints | Components | HI-II-14 | HuRI |
|---|---:|---:|---:|---:|---:|
| C1 development | 3,259 | 2,191 | 1,378 | 619 | 2,892 |
| C1 test | 3,187 | 2,083 | 1,348 | 570 | 2,854 |
| C2 development | 11,327 | 3,647 | 2,125 | 2,702 | 9,583 |
| C2 test | 13,446 | 3,930 | 2,436 | 2,739 | 11,822 |
| C3 development | 2,265 | 814 | 353 | 588 | 1,953 |
| C3 test | 2,379 | 842 | 505 | 510 | 2,110 |

Every primary cell exceeds the frozen floors of 500 released-positive pairs,
50 participating components, and 50 pairs from each named source.

## Withholding and leakage controls

All evidence for a withheld pair is removed from interaction supervision.
Withheld positive pairs cannot be presented to training as unlabeled. No pair
can occupy multiple positive roles. Development evidence cannot influence test
selection, and test evidence cannot influence training or development.

For any source/study/assay/temporal diagnostic, a pair supported by both visible
and held-out evidence is excluded from the strict held-out positive set.
Visible evidence alone excludes it from the unlabeled state. A target-only
held-out label is never used to remove that pair from its candidate pool.

The primary cells mix the accepted source union and therefore support no
source-, study-, assay-, or time-generalization claim.

## Candidate algebra and deterministic unlabeled sampling

Candidate universes exclude self-pairs and reverse duplicates and are evaluated
by streaming or algebra, never by materializing the full universe. A candidate
without visible qualifying positive evidence has state unlabeled.

The following sample sizes are frozen for a later authorized construction; no
sample was realized here:

| Cell | Target positives | Unlabeled population | Nonempty degree strata | Later cap |
|---|---:|---:|---:|---:|
| Training | 16,799 | 10,902,230 | 36 | 2,000,000 |
| C1 development | 3,259 | 10,902,230 | 36 | 1,000,000 |
| C1 test | 3,187 | 10,902,230 | 36 | 1,000,000 |
| C2 development | 11,327 | 11,909,923 | 8 | 1,000,000 |
| C2 test | 13,446 | 11,907,804 | 8 | 1,000,000 |
| C3 development | 2,265 | 3,247,710 | 1 | 1,000,000 |
| C3 test | 2,379 | 3,247,596 | 1 | 1,000,000 |

The later sampler is deterministic stratified bottom-hash sampling without
replacement:

- public salt ipin-openppi-benchmark-v1 and seed 20260803;
- hash payload
  {salt}:{seed}:unlabeled:{cell_id}:{stratum_id}:{pair_id};
- full 256-bit digest order ascending, then pair identifier ascending;
- degree bins 0, 1, 2, 3-4, 5-9, 10-19, 20-49, 50-99, and 100+;
- one allocation per nonempty stratum, followed by exact Hamilton proportional
  apportionment; fractional-remainder ties use ascending stratum identifier;
- within stratum h, inclusion probability p_h = m_h / N_h and design weight
  w_h = N_h / m_h;
- positive pairs are a census with inclusion probability and weight equal to 1.

Strict source diagnostics use canonical cell identifier
source_exclusive:{target_source}:{primary_cell}, inherit the underlying cell cap,
and recompute exposure from non-target-source training positives only. Full
streaming scoring is preferred. If it is not possible, exact recall and exact
rank metrics are demoted; the sampled universe is never renamed the full
universe.

## Primary PU-retrieval metrics

The primary metrics, always reported separately for C1/C2/C3 and
development/test, are:

1. **PU pairwise concordance:** the Horvitz-Thompson-weighted probability that a
   held-out released positive scores above an unlabeled candidate, with half
   credit for ties.
2. **Held-out-positive Recall@10, @100, and @1000:** macro-averaged over queries,
   with positive-pair micro summaries secondary. C1 and C3 use both endpoints as
   queries; C2 uses the held-out endpoint only. This requires full candidate
   ranking.
3. **Released-positive enrichment** at candidate fractions 0.0001, 0.001, and
   0.01, using the ceiling of fraction times query-candidate count, minimum one.
   This is recovery enrichment, not biological precision.
4. **Positive rank percentile:** the fraction of eligible candidates below a
   positive plus half the tied fraction; report mean, median, q10, and q90.

Scores are symmetric nonprobabilistic prioritization scores. Exact score ties
are resolved by ascending pair identifier. Sampled positive-vs-unlabeled AUROC
or AUPRC may be diagnostic only and cannot be interpreted as biological
classification performance.

## Uncertainty

The primary interval is a 2,000-replicate two-endpoint component pigeonhole
bootstrap using the frozen local_domain_union_30 component as the dependence
unit, seed 20260803, and NumPy PCG64DXSM in the pinned container.

Participating components are drawn with replacement. A pair joining distinct
components receives the product of their multiplicities; a within-component
pair receives that component multiplicity. Query metrics receive the query
component multiplicity. Sampling-design and bootstrap weights are both
retained. Report percentile 95% intervals.

Paired comparisons must reuse identical candidate samples and bootstrap draws.
A query-endpoint cluster bootstrap and supported leave-one-visible-source-out
analyses are sensitivities. Independent-pair-trial claims are prohibited.

## Supported and unsupported auxiliary holdouts

Field completeness is decisive:

| Source | Evidence rows | Publication groups | Experiment IDs | Assay version | Assay batch | Creation-date values |
|---|---:|---:|---:|---:|---:|---:|
| HI-II-14 | 49,389 | 1 | 0 | 0 | 0 | 1 |
| HuRI | 171,545 | 1 | 0 | 0 | 0 | 1 |

Both sources are Y2H. HI-II-14 has one PubMed group; HuRI has one unresolved
publication group. Both share the creation value 2019/10/16, which is release
metadata, not independent pair chronology. Detection-method terms distinguish
pipeline evidence types, not assay versions or batches.

A strict named-source diagnostic is supported with cellwise demotion:

| Target source | Visible training pairs/endpoints | C1 dev/test | C2 dev/test | C3 dev/test |
|---|---:|---:|---:|---:|
| HI-II-14, HuRI visible | 14,829 / 4,320 | 305 / 280 | 1,601 / 1,488 | 312 / 269 |
| HuRI, HI-II-14 visible | 3,252 / 1,868 | 611 / 633 | 4,751 / 5,270 | 1,677 / 1,869 |

HI-II-14-target C1 and C3 cells are below the 500-pair floor and are
descriptive only. Its C2 cells pass. All HuRI-target cells pass pair and
component floors. No failed cell may be pooled to conceal failure. The only
permitted claim is transfer of released-positive recovery between the two named
source releases.

Independent study holdout is inactive because studies are not independently
identified. Assay-version/batch holdout is inactive because both fields are
missing. Independent temporal holdout is inactive because the only date is
shared source-release metadata. Source-release chronology may be reported only
as a source-confounded diagnostic.

## Degree, hubs, and frozen future baselines

Degree is computed only from the 16,799 interaction-supervision training
positives. Of 11,900 training endpoints, 4,675 are exposed and 7,225 have degree
zero. Median degree is 0; q90, q95, and q99 are 7, 14, and 41; maximum degree is
279. The top 1%, 5%, and 10% hub strata contain 119, 595, and 1,190 endpoints,
with minimum degrees 41, 14, and 7.

Protected or development positives never enter these strata. Full protected
graph degree may be described only after predictions are sealed.

The following later baselines are frozen but not implemented or run:

- deterministic hash control using salt ipin-openppi-pu-r-baseline-v1, seed
  20260803, the pair identifier, and the normalized unsigned full SHA-256
  integer;
- endpoint degree sum: log1p(d_a) + log1p(d_b);
- preferential attachment: log1p(d_a times d_b);
- component degree-mass product, where component mass is the sum of training
  positive degrees over endpoints in the frozen component.

Held-out endpoint degree is zero. No held-out label or full-graph degree may
enter a baseline, and no baseline may be tuned on test.

## Claim boundary and continuing hold

Authorized wording is limited to recovery and ranking of withheld
released-positive evidence under this frozen PU design. C3 may be described only
as both exact frozen reference-sequence endpoints absent from
interaction-supervised training and component-disjoint under
local_domain_union_30.

Unlabeled-is-negative, universal-nonbinding, prevalence, biological precision,
calibrated probability, unseen-family, family-generalization, PLM-unseen,
exhaustive-nonhomology, unsupported study/assay/temporal, and proteome-wide
precision claims remain prohibited.

The TF-isoform and Lambourne panels remain external-only and unused. No next
pair-row construction, sample realization, or model work is authorized.

## Immutable evidence

| Artifact | SHA-256 / result |
|---|---|
| Frozen configuration revision 2 | 7b0cefa1b461f0e58d3e6f4ff72da2d6ad4ac39522a897ce4057e756fa84f2a6 |
| Production audit | b226a83fa31a78aa97cc6172adb65b386f0181b86ab2c7cb0939cf6dd4ea9d66; 16 pass, 0 warning, 0 fail |
| Independent validation | 8c94f10131ed7e100fadf1dc6174c4aaf7b5301d3dbece74725a994183a10741; 18 pass, 0 warning, 0 fail |
| Production Git commit | 8ee0ae58b365c68ffb5732c9995803d24e5fe6fa |
| Validation Git commit | d32a26508eb9438cb693ae1ae3cf48f5324a37f7 |
| Frozen split manifest | 81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a |
| Pinned ARM64 Apptainer image | 72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629 |

The earlier unrevisioned audit directory is preserved as pre-hardening
qualification history and has no acceptance role. Revision 2 is the sole
accepted protocol evidence.
