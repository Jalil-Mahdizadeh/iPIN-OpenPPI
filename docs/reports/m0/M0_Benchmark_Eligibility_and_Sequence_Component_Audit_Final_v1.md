# M0 final report: benchmark eligibility and sequence-component audit

**Report date:** 2026-08-08

**Frozen human reference:** UniProt `2026_02`

**Candidate population:** frozen HuRI Space III

**Primary design:** reference-sequence positive-unlabeled ranking (PU-R)

**Controlling checkpoint:**
`governance/checkpoints/RESUME-001-post-tf-isoform-audit.md`

## Executive conclusion

The bounded `benchmark_eligibility_and_sequence_component_audit_v1` is
technically complete and independently validated. The validator passed 21
checks with zero warnings and zero failures.

Exactly 17,172 of 17,408 Space III genes have one admissible frozen reference
sequence hash. They represent 17,000 distinct sequence endpoints and an
unordered algebraic universe of 144,491,500 possible non-self endpoint pairs.
That count was not materialized as pair rows and was not called a tested
universe.

Deterministic sequence components were constructed at 40%, 30%, and 20% exact
alignment identity with at least 80% coverage of each endpoint. There are
12,467, 11,311, and 10,497 components, respectively. Aggregate positive
mapping and component counts satisfy the prespecified total count floors at
all three thresholds, but this is only a pre-split necessary-condition audit.
It does not select a threshold, establish held-out feasibility, or authorize
C1/C2/C3 assignments or train/dev/test splits.

The primary PU-R design is unchanged. No candidate-pair table, evidence
indicator, interaction label, negative label, pseudo-negative, prevalence
estimate, calibration, structural mapping, split, or model was constructed.
Unreported eligible pairs remain unlabeled.

## 1. Scope and frozen inputs

The audit used only the already validated primary-source staging and
reconciliation artifacts named in the frozen configuration:

- HuRI Space membership;
- UniProt canonical human protein sequences and Ensembl mappings; and
- accepted HuRI and HI-II-14 direct positive-evidence gene-pair projections.

Every relevant source document, Parquet part, schema, row count, byte count,
and SHA-256 digest was verified before computation. The two quarantined
external panels were not inputs. Neither external-panel audit was reopened,
recomputed, or extended.

The endpoint unit is the SHA-256 of the exact frozen reference sequence. A
Space III gene is eligible only when its frozen mappings resolve to exactly
one distinct sequence hash. Multiple accessions are admitted only when all
mapped accessions have the same exact sequence. Multiple distinct hashes and
unmapped genes are excluded without imputation.

## 2. Eligibility census

| Mapping state | Space III genes | Disposition |
|---|---:|---|
| Unique reference sequence | 17,121 | Eligible |
| Sequence-equivalent accessions | 51 | Eligible; one exact sequence hash |
| Ambiguous multiple sequences | 16 | Excluded |
| Unmapped | 220 | Excluded |
| **Total** | **17,408** | **17,172 eligible** |

The eligible set contains 17,033 distinct UniProt accessions but only 17,000
distinct exact sequence hashes. Sequence deduplication therefore occurs before
the candidate-count algebra and component analysis.

The exact non-self unordered count is:

`17,000 × 16,999 / 2 = 144,491,500`.

No rows for these possible pairs were emitted. The count describes eligibility
only; it is not a measurement, label census, prevalence denominator, or claim
that any pair was assayed.

The frozen source contains selenocysteine in 18 eligible sequences, totalling
19 `U` residues. The audit preserves those source sequences exactly and
records the nonstandard symbol explicitly.

## 3. Frozen sequence-similarity method

MMseqs2 release `18-8cc5c`, upstream commit
`8cc5ce367b5638c4306c2d7cfc652dd099a4643f`, was installed from the official
ARM64 release archive. The binary SHA-256 is
`d5f6d96578e3dbcd1d8772bb575b112e9dd1dbf077d150914962a2356ae0d75d`.

The search was all eligible sequences against themselves with a 20% search
floor, sensitivity 7.5, both-endpoint coverage mode, nominal minimum coverage
0.80, self matches enabled, and bounded acceptance/rejection queues of 20,000.
Raw output retained coordinates, endpoint lengths, mismatch count, alignment
length, E-value, and bit score.

The governed postfilter independently derives integer identical residues as:

`query_span + target_span - alignment_length - mismatch_count`.

Exact identity is that integer divided by alignment columns including gaps.
Coverage is independently recomputed as query span divided by query length and
target span divided by target length. An edge is admitted only when both
coverages are at least 0.80 and exact identity reaches the requested threshold.

Components are deterministic single-linkage connected components. The member
representative is the lexicographically smallest sequence hash; the component
identifier is a stable hash of the threshold and sorted member hashes.

## 4. Fail-closed alignment reconciliation

| Alignment result | Count |
|---|---:|
| Raw directional/self alignment records | 163,441 |
| Structurally invalid records | 0 |
| Below exact identity floor | 531 |
| Below exact endpoint coverage | 0 |
| Exact-criteria rejected records | 531 |
| Queries with a valid self match | 17,000 |
| Normalized non-self edges at 20% | 75,662 |

The 531 search candidates that did not meet the independently recomputed exact
identity rule were excluded and counted. They were not treated as malformed,
silently retained, or used to relax the threshold. Raw alignments and the
normalized edge table are immutable, hashed run artifacts.

## 5. Deterministic component census

| Exact identity | Edges | Components | Singletons | Largest | Q50 | Q90 | Q95 | Q99 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 40% | 31,474 | 12,467 | 10,366 | 312 | 1 | 2 | 3 | 5 |
| 30% | 63,074 | 11,311 | 9,059 | 362 | 1 | 2 | 3 | 7 |
| 20% | 75,662 | 10,497 | 8,268 | 485 | 1 | 2 | 3 | 9 |

All 17,000 sequences have exactly one assignment at each threshold, producing
51,000 canonical assignment rows. Independent reconstruction matched every
assignment and verified that lowering the threshold only merges components.

The 30% threshold remains the prespecified primary audit threshold and 40% and
20% remain sensitivity thresholds. This audit does not select among them for a
future split or model.

## 6. Aggregate positive-evidence mapping

The positive source projections are retained as accepted assay-specific direct
positive evidence. Mapping them to eligible distinct sequence endpoints is an
aggregate accounting exercise only; no positive pair table or binary evidence
indicator was emitted.

| Source | Evidence rows | Eligible distinct-endpoint rows | Eligible fraction | Distinct eligible sequence pairs |
|---|---:|---:|---:|---:|
| HI-II-14 | 49,389 | 45,958 | 0.930531 | 12,353 |
| HuRI | 171,545 | 166,198 | 0.968830 | 50,545 |
| **ALL** | **220,934** | **212,156** | **0.960269** | **58,049** |

The governed exclusion-precedence counters are:

| Source | Unresolved projection | Outside Space III | Unmapped endpoint | Ambiguous endpoint | Same sequence |
|---|---:|---:|---:|---:|---:|
| HI-II-14 | 282 | 130 | 564 | 681 | 1,774 |
| HuRI | 924 | 0 | 2,033 | 726 | 1,664 |
| **ALL** | **1,206** | **130** | **2,597** | **1,407** | **3,438** |

The `ALL` distinct pair count is a union and therefore is not the arithmetic
sum of the two source-specific counts. Repeated evidence observations remain
distinct from distinct sequence-pair counts.

## 7. Pre-split component feasibility aggregates

| Source | Identity | Positive-exposed components | Within-component positive pairs | Cross-component positive pairs | Total components |
|---|---:|---:|---:|---:|---:|
| HI-II-14 | 40% | 3,373 | 94 | 12,259 | 12,467 |
| HI-II-14 | 30% | 3,219 | 194 | 12,159 | 11,311 |
| HI-II-14 | 20% | 3,080 | 241 | 12,112 | 10,497 |
| HuRI | 40% | 6,525 | 359 | 50,186 | 12,467 |
| HuRI | 30% | 6,087 | 851 | 49,694 | 11,311 |
| HuRI | 20% | 5,762 | 985 | 49,560 | 10,497 |
| ALL | 40% | 6,940 | 386 | 57,663 | 12,467 |
| ALL | 30% | 6,468 | 896 | 57,153 | 11,311 |
| ALL | 20% | 6,117 | 1,047 | 57,002 | 10,497 |

The prespecified aggregate floors of at least 50 total components and at least
500 total positive pairs are numerically met for every source/threshold row.
These broad totals are necessary but not sufficient for a future held-out
design. The audit did not assess a held-out floor, assign components to
partitions, measure train/test exposure, construct C1/C2/C3 cases, or determine
later split feasibility.

## 8. Canonical outputs and explicit non-outputs

Exactly five bounded canonical tables were emitted:

| Table | Rows |
|---|---:|
| `space_iii_gene_eligibility` | 17,408 |
| `eligible_reference_sequences` | 17,000 |
| `sequence_component_assignments` | 51,000 |
| `positive_mapping_aggregates` | 3 |
| `positive_component_feasibility` | 9 |

The canonical inventory contains no candidate pairs, positive/unlabeled
indicators, negative labels, pseudo-negatives, C1/C2/C3 assignments, splits,
structure mappings, model inputs, predictions, prevalence, or calibration.
Every guard field that would imply such work is false.

## 9. Reproducibility and independent validation

Production ran from clean commit
`3ea96166eab2c3600a290ee8109410a7d040b153` in
`containers/images/ipin-data-arm64_0.1.2.sif`, SHA-256
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`,
on ARM64 with Python 3.12.3, DuckDB 1.5.5, and PyArrow 19.0.1.

The final independent validator ran from clean commit
`d0ed03735ce6adb0566c39c4396ad08b669f20c4`. It independently re-read the
frozen sources and raw MMseqs2 alignments, rebuilt eligibility and all exact
edges, reconstructed every component without production assignments,
recomputed all positive aggregates, and checked manifests, schemas, hashes,
sidecars, permissions, inventories, production provenance, and scope guards.

| Artifact | Result | SHA-256 |
|---|---|---|
| Production audit report | Complete | `6f77fe0fb65205e0a45dd9c61631a3982c4b999efc0c5575f1799b7a726df41c` |
| Independent validation | 21 pass, 0 warning, 0 fail | `6fd3b822c9c02e138d94f6ea78386fcdea2f43acff9156f5fc0e0a4e632f58a8` |
| Production run manifest | Four immutable run files | `81af038c3468e5b15f0e9dc287fd8f191181a059cfed239a9e36485c82cc47b4` |
| Canonical manifest | Five tables | `1a7769fa550ac7eef9acd40da72c8f5247c0c81cb1bb77a913e185d090d83f96` |
| Frozen configuration | Version 1 | `b3bc6d802799d2fb47f351b6311c951945a8517d27e573be7fc4209e452a22e5` |
| Canonical schema | Version 1 | `60698389ee17e5c9d2cf8a586fbe92af9ef331120d01785f13b071759749a481` |

The complete unit suite passed 158 tests in the pinned container. The real
pinned MMseqs2 binary was also exercised by an exact-identity fixture.

## 10. Scientific interpretation and governance return

This audit establishes a frozen eligible endpoint set and deterministic
sequence-component inventories suitable for later governed design work. It
does not establish an experimentally tested universe, population prevalence,
calibrated probability, universal nonbinding, or expected generalization.

The project returns to governance with the primary PU-R estimand and claim
ceiling unchanged. No downstream benchmark-construction work is authorized.
Any later candidate, label, component-assignment, split, structure, or model
work requires a new explicit decision.

The external-panel quarantine also remains unchanged: the TF-isoform panel is
external-only and unsuitable for training negatives, universal-nonbinding
claims, prevalence, calibration, or unseen-endpoint/family benchmarking.
