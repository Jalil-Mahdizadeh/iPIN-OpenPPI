# M0 final report: pre-split feasibility and leakage stress-test

**Report date:** 2026-08-08

**Frozen endpoint universe:** 17,000 exact reference-sequence hashes

**Primary design:** reference-sequence positive-unlabeled ranking (PU-R)

**Authorization:** `DEC-0019`

**Immutable parent:** `DEC-0018`

## Executive conclusion

The bounded `pre_split_feasibility_and_leakage_stress_test_v1` is technically
complete and independently validated. The clean-tree validator passed 13
checks with zero warnings and zero failures.

Final split construction is **scientifically feasible in principle but remains
unauthorized**. The exact disposition depends on the leakage definition:

- the accepted 30% identity, 80%-of-both-endpoints graph (`frozen_fl80`) is
  robustly feasible in all 1,000 aggregate trials, but it is not sufficient as
  the sole future leakage control because the separate full-length challenge
  recovered 106 additional qualifying 30% edges, 42 of which joined accepted
  components;
- the 30% full-length sensitivity union (`sensitive_fl80_union`) is the minimum
  defensible full-length leakage graph and is robustly feasible in all 1,000
  trials;
- the stronger 30% local/domain union (`local_domain_union`) is conditionally
  feasible: 893 of 1,000 trials met the 70%/15%/15% sequence-balance tolerance,
  and every one of those trials also met all C1/C2/C3 positive-pair,
  component, and C3 source-diversity floors. A later split package would need a
  constrained allocator and exact chosen-split verification;
- the analogous local/domain rule is robust at 40% but conditional at 20%,
  where a 4,932-sequence component makes balance substantially less stable.

The local/domain stress-test found substantial residual similarity missed by
the accepted full-length rule. At the primary 30% threshold it added 113,190
edges, including 69,112 edges crossing accepted components, reduced the
component count from 11,311 to 7,782, and increased the largest component from
362 to 1,624 sequences. That result precludes treating the frozen graph alone
as a biological-family definition.

A future C3 claim may describe both **exact frozen reference-sequence
endpoints** as absent from training and component-disjoint under an explicitly
named, versioned leakage graph. It may not claim unseen biological families,
family generalization, universal nonhomology, or exhaustive absence of local
similarity. No C1/C2/C3 label or split is authorized by this report.

## 1. Scope and immutable inputs

The audit verified and consumed the accepted parent manifests and hashes
without modifying them. It preserved exactly:

- 17,000 eligible sequence endpoints;
- 12,467, 11,311, and 10,497 accepted components at 40%, 30%, and 20%
  identity, respectively;
- 31,474, 63,074, and 75,662 accepted full-length similarity edges at those
  thresholds;
- 58,049 distinct released-positive sequence pairs across HI-II-14 and HuRI;
  and
- the reference-sequence PU-R estimand, under which unreported eligible pairs
  remain unlabeled.

Released-positive pairs were reconstructed transiently to calculate
aggregates. No positive pair rows, endpoint/component metric rows, trial
assignments, candidate-pair universe, labels, or split were emitted.

The TF-isoform and Lambourne external panels were not inputs. Their audits were
not reopened, recomputed, or extended. The TF-isoform panel remains
external-only and unsuitable for training negatives or any training role,
universal-nonbinding claims, prevalence, calibration, and unseen-endpoint or
family benchmarking.

## 2. Governed methods

### 2.1 Positive-network summaries

Endpoint degree includes all 17,000 eligible endpoints, including zero-degree
endpoints. Component positive-edge load counts a within-component positive
pair once and a cross-component pair once for each of its two endpoint
components. The audit reports quantiles, maximum, Gini coefficient, degree
histogram, and the shares carried by the top 1%, 5%, and 10% of entities.

Source composition is the mutually exclusive union of `HI-II-14_only`,
`HuRI_only`, and `both`.

### 2.2 Similarity challenges

The accepted graph was not rewritten. Two separate MMseqs2 release `18-8cc5c`
searches ran against the frozen FASTA:

1. a full-length sensitivity challenge using the ungapped prefilter path,
   sensitivity 7.5, exact identity at least 20%, and at least 80% coverage of
   both endpoints; and
2. a local/domain challenge using increasing sensitivity, similar-kmer target
   search, exact identity at least 20%, at least 20% coverage of both
   endpoints, minimum aligned endpoint span 80 residues, and E-value at most
   `1e-3`.

Exact identity was independently recomputed from integer coordinate spans,
alignment length, and mismatch count. Both searches required a valid self
match for every endpoint. The full-length sensitivity union adds challenge
edges to the accepted graph. The local/domain union adds both full-length
sensitivity and qualifying local/domain edges; it never removes an accepted
edge.

These are operational heuristic graphs. They can detect missed qualifying
edges but cannot prove exhaustive completeness, nonhomology, or biological
family identity.

### 2.3 Ephemeral allocation trials

For each of the nine leakage graph/identity combinations, 1,000 deterministic
hash-order trials assigned whole components in memory toward 70% training, 15%
development, and 15% test sequence fractions. A trial was target-valid only
when every sequence fraction was within 0.03 of its target.

The reported C1/C2/C3 quantities are opportunity counts, not labels:

- C1 opportunity: a within-training released-positive pair whose endpoints
  each have at least one other within-training positive partner;
- C2 opportunity: a released-positive train/test component edge whose training
  endpoint has within-training positive exposure; and
- C3 opportunity: a released-positive pair with both endpoints in test
  components.

The prespecified per-axis floors are 500 released-positive pairs and 50
participating components. C3 source diversity additionally requires at least
50 HI-II-14 and 50 HuRI positive pairs. Robust feasibility requires a joint
pass fraction of at least 0.95. Trial identities and assignments were
discarded.

## 3. Positive-edge distribution and concentration

### 3.1 Source composition

| Source membership | Distinct positive pairs | Fraction |
|---|---:|---:|
| HI-II-14 only | 7,504 | 0.129270 |
| HuRI only | 45,696 | 0.787197 |
| Both | 4,849 | 0.083533 |
| **Union** | **58,049** | **1.000000** |

HuRI therefore dominates the released-positive union. The result is a source
composition property of released positives, not prevalence in the eligible
pair universe.

### 3.2 Endpoint degree and hub concentration

| Source | Positive-exposed endpoints | Pairs | Q90 | Q95 | Q99 | Maximum | Top 1% share | Top 5% share | Gini |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HI-II-14 | 3,969 | 12,353 | 3 | 6 | 27 | 281 | 0.406460 | 0.735166 | 0.922022 |
| HuRI | 8,058 | 50,545 | 15 | 32 | 86 | 508 | 0.232585 | 0.573390 | 0.855524 |
| ALL | 8,596 | 58,049 | 17 | 35 | 97 | 603 | 0.236206 | 0.566177 | 0.849127 |

Only 8,596 of 17,000 endpoints occur in the positive union. Positive evidence
is strongly hub-concentrated: the top 1% of endpoints carry 23.6% of ALL
endpoint degree, and the top 5% carry 56.6%. This concentration is one reason
that aggregate positive totals cannot by themselves guarantee a defensible
held-out split.

### 3.3 ALL-source component positive-edge load

| Identity | Leakage definition | Components | Positive-exposed | Q99 load | Maximum load | Top 1% share | Gini |
|---:|---|---:|---:|---:|---:|---:|---:|
| 40% | frozen_fl80 | 12,467 | 6,940 | 121 | 2,057 | 0.278147 | 0.848089 |
| 40% | sensitive_fl80_union | 12,461 | 6,935 | 120 | 2,057 | 0.281593 | 0.848578 |
| 40% | local_domain_union | 10,300 | 5,919 | 136 | 4,594 | 0.322798 | 0.855854 |
| 30% | frozen_fl80 | 11,311 | 6,468 | 128 | 2,597 | 0.291349 | 0.847917 |
| 30% | sensitive_fl80_union | 11,292 | 6,455 | 128 | 2,597 | 0.295558 | 0.848738 |
| 30% | local_domain_union | 7,782 | 4,715 | 159 | 9,361 | 0.392827 | 0.867475 |
| 20% | frozen_fl80 | 10,497 | 6,117 | 137 | 2,931 | 0.305204 | 0.849466 |
| 20% | sensitive_fl80_union | 10,375 | 6,053 | 136 | 3,582 | 0.315374 | 0.851190 |
| 20% | local_domain_union | 6,208 | 3,956 | 165 | 27,452 | 0.439659 | 0.871861 |

Stricter unions concentrate positive evidence into fewer components. The
effect is strongest for local/domain similarity at 20%, where a single
component carries a positive-edge load of 27,452 under the governed counting
rule.

## 4. Independent full-length sensitivity result

The full-length challenge emitted 165,547 raw alignment records. There were
zero structurally invalid rows, all 17,000 endpoints had a self match, and
76,851 normalized non-self edges remained at the 20% search floor.

| Identity | Accepted edges | Challenge edges | Accepted rediscovered | Not rediscovered | Newly recovered | Union edges |
|---:|---:|---:|---:|---:|---:|---:|
| 40% | 31,474 | 31,509 | 31,474 | 0 | 35 | 31,509 |
| 30% | 63,074 | 63,180 | 63,074 | 0 | 106 | 63,180 |
| 20% | 75,662 | 76,851 | 75,662 | 0 | 1,189 | 76,851 |

The separate challenge rediscovered every accepted edge, which is reassuring
for sensitivity, but it also found qualifying edges absent from the accepted
graph. At 30%, 42 of the 106 new edges cross accepted components and reduce
the union component count by 19. Consequently, the frozen graph is preserved
as accepted evidence but should not be the sole leakage guard for a future
split.

This result is not an exhaustive completeness proof. It establishes only
agreement and parameter sensitivity relative to the named MMseqs2 challenge.

## 5. Residual local/domain leakage stress

The local/domain challenge emitted 479,922 raw alignment records and 236,718
normalized non-self edges at its 20% search floor. It found zero structurally
invalid rows and valid self matches for all endpoints.

| Identity | Definition | Graph edges | Added vs accepted | Added crossing accepted components | Components | Largest component | Within-component positives | Cross-component positives |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 40% | frozen_fl80 | 31,474 | 0 | 0 | 12,467 | 312 | 386 | 57,663 |
| 40% | sensitive_fl80_union | 31,509 | 35 | 8 | 12,461 | 312 | 449 | 57,600 |
| 40% | local_domain_union | 81,470 | 49,996 | 29,144 | 10,300 | 536 | 896 | 57,153 |
| 30% | frozen_fl80 | 63,074 | 0 | 0 | 11,311 | 362 | 896 | 57,153 |
| 30% | sensitive_fl80_union | 63,180 | 106 | 42 | 11,292 | 362 | 980 | 57,069 |
| 30% | local_domain_union | 176,264 | 113,190 | 69,112 | 7,782 | 1,624 | 2,086 | 55,963 |
| 20% | frozen_fl80 | 75,662 | 0 | 0 | 10,497 | 485 | 1,047 | 57,002 |
| 20% | sensitive_fl80_union | 76,851 | 1,189 | 190 | 10,375 | 509 | 1,206 | 56,843 |
| 20% | local_domain_union | 243,668 | 168,006 | 103,206 | 6,208 | 4,932 | 6,620 | 51,429 |

At primary 30%, local/domain union membership moves 1,190 additional positive
pairs inside components. By source-membership stratum, within-component pairs
change from 45 to 169 for HI-II-14-only, 702 to 1,628 for HuRI-only, and 149
to 289 for pairs present in both sources.

These changes are too large to describe local/domain leakage as negligible.
They also demonstrate why connected components under an 80% full-length rule
cannot be equated with biological families.

## 6. Component-disjoint opportunity feasibility

The table reports the 5th percentile of retained opportunity evidence across
all trials. `Target/joint` is both the target-valid fraction and the joint
floor-pass fraction; where they are equal, every target-valid trial passed all
positive-evidence gates.

| Identity | Leakage definition | Target/joint | C1 pairs Q05 | C2 pairs Q05 | C3 pairs Q05 | C3 components Q05 | C3 HI-II-14 Q05 | C3 HuRI Q05 | Status |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 40% | frozen_fl80 | 1.000 | 24,784 | 10,442 | 1,018 | 475 | 184 | 889 | Robust |
| 40% | sensitive_fl80_union | 1.000 | 24,762 | 10,377 | 992 | 475 | 188 | 868 | Robust |
| 40% | local_domain_union | 1.000 | 24,133 | 10,077 | 962 | 379 | 178 | 847 | Robust |
| 30% | frozen_fl80 | 1.000 | 24,727 | 10,220 | 985 | 436 | 182 | 865 | Robust |
| 30% | sensitive_fl80_union | 1.000 | 24,498 | 10,051 | 954 | 433 | 183 | 832 | Robust |
| 30% | local_domain_union | 0.893 | 23,110 | 9,574 | 939 | 187 | 170 | 837 | Conditional |
| 20% | frozen_fl80 | 1.000 | 24,346 | 9,783 | 911 | 394 | 167 | 810 | Robust |
| 20% | sensitive_fl80_union | 1.000 | 24,140 | 9,778 | 904 | 383 | 168 | 805 | Robust |
| 20% | local_domain_union | 0.614 | 14,586 | 6,792 | 763 | 143 | 139 | 673 | Conditional |

The primary 30% local/domain regime is conditional solely because 107 trials
missed the sequence-fraction tolerance. All 893 target-valid trials passed the
C1, C2, C3, component, and source-diversity gates. This demonstrates feasible
allocations exist, but it does not identify one or guarantee compatibility
with future assay, evidence-grouping, or temporal constraints.

The 20% local/domain graph is less stable: its largest component contains
4,932 sequences, and only 61.4% of trials met target balance. It should not be
made a default split definition without a separately authorized design review.

## 7. C3 and claim boundaries

No proposed regime supports an unqualified unseen-family claim.

The strongest wording available to a later, fully verified split is:

> Both exact frozen reference-sequence endpoints were absent from training and
> their components were disjoint under the named, versioned leakage graph and
> thresholds.

“Unseen protein” may be used only if it is explicitly defined as unseen exact
frozen reference-sequence endpoint. It must not be allowed to imply unseen
gene, isoform, domain architecture, homolog, or biological family.

The following remain prohibited:

- unseen family, novel family, or family-generalizing performance;
- proven nonhomology or exhaustively homology-free test pairs;
- universal-nonbinding, prevalence, calibrated probability, or population
  interpretation;
- treating unreported pairs as negatives; and
- model-performance or experimental-validation claims from this audit.

## 8. Reproducibility and independent validation

Production ran from clean commit
`2dcd8b3585159a5d747176d36e08a57a11cb0950`. The accepted independent
validator ran from clean commit
`f1001cc8c9bc9c16a596139f1231bfae24f74c74` and independently reparsed both
raw search outputs, reconstructed all nine graphs, recomputed every positive
aggregate and all 9,000 allocation trials, and enforced the absence of pair,
label, split, external-panel, structure, and model outputs.

| Artifact | Result | SHA-256 |
|---|---|---|
| Production audit report | Complete | `5f4e655a81b70a4dd2143a81027188b692ca120b0fab7f919d18b53fd4eabb6f` |
| Independent validation | 13 pass, 0 warning, 0 fail | `1f0f862796f1ab581ca4c3c528987cd1fdf484269d5ca932f99eb9d946e1e809` |
| Production run manifest | Five immutable run files | `a76731632f5d137d0fa2b2eab244c2e86a7a10cd4b67013d8164bb684b902755` |
| Canonical manifest | Six aggregate-only tables | `8b2200b34149c1a4ecf92274cac886acbafc2d53b2cac3e8167c91610ec860f2` |
| Frozen configuration | Version 1 | `0648107f96f079b502dfce4c0c470c1199514463615c107f152a06603f75281f` |
| Canonical schema | Version 1 | `04fbde9975a45d8d567ea98facc470b385275db61b9e1428d1699d05b358fae5` |

The complete unit suite passed 170 tests in the pinned ARM64 Apptainer image,
including a real pinned-MMseqs2 fixture and validator tamper/fail-closed tests.

## 9. Governance disposition

Accept the audit as technically complete. Final split construction is
scientifically feasible in principle under the following boundaries:

1. preserve the accepted 30%/80%-coverage graph as immutable parent evidence;
2. do not use that frozen graph alone as the final leakage guard;
3. use at least the 30% `sensitive_fl80_union` as the hard full-length
   component constraint;
4. treat the 30% `local_domain_union` as the preferred stricter operational
   stress definition and require any future chosen split to pass its exact
   balance, evidence-floor, and cross-partition leakage checks;
5. if a future package declines to make local/domain union a hard assignment
   rule, it must report residual local/domain cross-partition leakage and limit
   claims accordingly; and
6. permit only exact-endpoint, named-rule C3 language, never unseen-family or
   exhaustive-homology claims.

This disposition authorizes no construction. A later numbered decision must
separately bound any candidate representation, evidence indicators, component
allocator, split artifact, and C1/C2/C3 assignment. Negative or pseudo-negative
creation, external-panel integration, structural labels, and all model work
remain prohibited.
