# M0 final primary-source parsing and evidence quality-control report

**Project:** iPIN-OpenPPI
**Date:** 2026-08-03
**Run family:** `primary_sources_v1`
**Executor:** Codex
**Runtime:** Accepted Apptainer data SIF on NAISS Arrhenius
**Result:** **PASS WITH ONE DOWNSTREAM STRUCTURAL BLOCKER**

## Executive result

The frozen HuRI, UniProt, IntAct/IMEx, and PDB/SIFTS source payloads were parsed successfully into a provenance-preserving, construct-aware staging layer. The canonical production run completed without an override flag and published atomically to `data/staging/primary_sources_v1`.

The strict independent validator reports 150 passed checks, zero failed checks, and one warning. The warning is not a parsing defect: the frozen SIFTS snapshot declares UniProt `2026.03`, whereas the frozen human sequence corpus is UniProt `2026_02`. Consequently, source reconciliation may proceed, but exact structural mapping, label construction, and model training remain unauthorized.

This milestone materially supports project feasibility. The source formats, evidence cardinalities, identifiers, sequences, and provenance can all be handled computationally on Arrhenius without laboratory work. The remaining feasibility constraint is scientific rather than computational: defensible learning targets require explicit treatment of the incomplete HuRI attempted-pair universe and release-safe structural mappings.

## Production disposition

| Item | Result |
|---|---:|
| Source families | 4 |
| Selected raw scientific inputs reverified | 17 |
| Staging datasets | 21 |
| Parquet files | 152 |
| Rows across all staging tables | 14,021,899 |
| Parquet payload bytes | 1,369,917,702 |
| Validation checks passed | 150 |
| Validation checks failed | 0 |
| Validation warnings | 1 |
| Source reconciliation authorized | Yes |
| Label construction authorized | No |
| Model training authorized | No |

“Rows across all staging tables” is an engineering inventory, not a count of unique PPIs. It includes evidence, participants, features, sequences, identifier mappings, controlled vocabulary, mutation annotations, supplementary source-native records, and structural mappings.

## Parsed table inventory

| Source | Dataset | Rows |
|---|---|---:|
| HuRI | `evidence_records` | 220,934 |
| HuRI | `participants` | 441,868 |
| HuRI | `participant_features` | 441,868 |
| HuRI | `source_pair_views` | 80,781 |
| HuRI | `huri_orf_mappings` | 17,436 |
| HuRI | `huri_space_membership` | 19,818 |
| HuRI | `huri_structural_contact_annotations` | 3,431 |
| HuRI | `huri_fusion_interference` | 3,738 |
| HuRI | `supplementary_raw_tabular_records` | 564,178 |
| **HuRI subtotal** | **9 datasets** | **1,794,052** |
| UniProt | `protein_sequences` | 169,637 |
| UniProt | `identifier_mappings` | 4,377,974 |
| **UniProt subtotal** | **2 datasets** | **4,547,611** |
| IntAct/IMEx | `evidence_records` | 552,442 |
| IntAct/IMEx | `participants` | 1,771,656 |
| IntAct/IMEx | `participant_features` | 955,451 |
| IntAct/IMEx | `interactors` | 653,933 |
| IntAct/IMEx | `experiments` | 48,876 |
| IntAct/IMEx | `controlled_vocabulary_terms` | 4,082 |
| IntAct/IMEx | `mutations` | 89,925 |
| **IntAct/IMEx subtotal** | **7 datasets** | **4,076,365** |
| PDB/SIFTS | `sifts_chain_uniprot` | 1,007,697 |
| PDB/SIFTS | `sifts_chain_taxonomy` | 1,076,304 |
| PDB/SIFTS | `sifts_observed_segments` | 1,519,870 |
| **PDB/SIFTS subtotal** | **3 datasets** | **3,603,871** |
| **Total** | **21 datasets** | **14,021,899** |

## Evidence-layer findings

The common evidence layer contains 773,376 records: 220,934 HuRI evidence records and 552,442 IntAct/IMEx evidence records. It contains 2,213,524 participant rows and 1,397,319 participant-feature rows.

Across both evidence sources, 772,437 records carry a positive observation state and 939 carry an explicit negative observation state. All 939 negatives are source-explicit IntAct assertions. No technical-failure record was converted into a negative, and absence from HuRI was never interpreted as evidence of non-interaction.

The parser preserves evidence units rather than manufacturing a consensus pair table. Stable source record identifiers, experiment/publication identifiers, participant cardinality, pair projections, assay and host context, observation/technical state, raw locators, file hashes, parser version, schema hash, and container hash remain attached to every applicable record.

### Corrected interaction cardinality

The final IntAct parser distinguishes unary, binary, and n-ary source records correctly:

| IntAct property | Records |
|---|---:|
| Unary (`participant_count = 1`) | 2,198 |
| Two participants (`participant_count = 2`) | 508,280 |
| More than two participants | 41,964 |
| Direct two-protein records | 482,044 |
| Explicit negative records | 939 |
| Expanded projections | 0 |

`original_nary` now means strictly more than two participants. The 2,198 unary records remain source-native unary observations and carry a dedicated quality flag; they are not silently discarded, expanded, or relabeled as n-ary. Every declared participant count matches the stored participant rows, and pair identifiers occur only where binary semantics permit them.

## Source-specific findings

### HuRI

The detailed HuRI and HI-II-14 PSI-MI files were retained as evidence records, while the four provider pair files were retained as distinct source-derived views. This separation is essential because evidence rows, ORF/construct pairs, mapped gene pairs, and portal headline counts are not interchangeable units.

All 29 scientific supplementary tables were parsed without silently dropping workbook content. The parser preserved 1,416 source error cells as explicit source-native values for later interpretation. It also typed 3,431 structural-contact annotations—1,364 `in_contact=true` and 2,067 `in_contact=false`—and 3,738 fusion-interference records, including 515 self-pairs. These are annotations, not approved project labels: every `label_authorized` value is false. The same prohibition holds for all 80,781 source pair-view rows.

ISSUE-0003 remains decisive: public HuRI files do not establish the complete attempted and technically evaluable pair universe. Missing pairs remain unknown. Unless an auditable screen log becomes available, the scientifically defensible primary route is positive–unlabeled or latent-observation modelling, not ordinary positive-versus-unreported binary classification.

ISSUE-0004 also remains open for the next unit. The parser preserved portal counts, downloadable pair views, detailed evidence, orientations, self-pair information, and ORF mappings separately; it did not alter records to force the differing representations to agree.

### UniProt

The frozen `2026_02` human corpus produced 169,637 sequence rows: 20,652 canonical sequences, 148,288 additional isoform sequences, and 697 additional non-isoform sequence records. It also produced 4,377,974 identifier-mapping rows. Sequence lengths and sequence SHA-256 values were independently recomputed and passed validation, and canonical versus additional sequence-view semantics remain explicit.

### IntAct/IMEx

The `release_252_archive_2026-01-09` PSI-MI XML archive yielded 552,442 source interactions/evidence records, 48,876 experiments, 653,933 interactors, 1,771,656 participants, and 955,451 participant features. The optional mutation file yielded 89,925 logical records, and the controlled vocabulary yielded 4,082 terms.

Original n-ary interactions were not spoke-expanded. Explicit negatives remain explicit source assertions with their context; technical state is represented independently from observation state.

### PDB/SIFTS

The source-native SIFTS parse is complete, but its exact join to the frozen sequence corpus is provisional. Through chains having at least one `taxid=9606` taxonomy row, the diagnostic found 9,812 distinct SIFTS accessions. Of these, 8,947 match a frozen primary accession and another 84 match an explicitly retained additional-sequence identifier, for a disjoint union of 9,031 present accessions; 781 are absent from the frozen `2026_02` corpus.

The parser preserved 72 descending chain-to-UniProt intervals verbatim and found zero descending observed-segment intervals. It did not swap or normalize endpoints. Mixed/multiple chain taxonomy, accession presence, and interval direction mean these figures are diagnostics—not a final estimate of human structural coverage.

ISSUE-0005 therefore blocks exact structure-to-sequence assertions and all structure-derived labels until a release-aligned source or a fully audited exact-sequence subset is established.

## Quality-control coverage

The validator independently checked:

- the accepted SIF path, SHA-256, architecture, Python/runtime versions, parser version, schema hashes, config hash, acquisition manifest, and clean parser Git commit;
- exact dataset inventory, file inventory, row counts, byte counts, file hashes, read-only permissions, and absence of links;
- required fields, enum values, primary keys, participant/evidence foreign keys, and feature/participant foreign keys;
- evidence-state consistency, exact participant cardinality, unary/n-ary flags, binary pair-ID semantics, and prohibition of technical-failure negatives;
- source-report counts against Parquet content;
- UniProt sequence lengths, sequence hashes, and canonical/additional semantics;
- preservation of HuRI workbook source errors and prohibition of label authorization; and
- SIFTS interval diagnostics and frozen-UniProt accession overlap.

The sole warning is `blocker.ISSUE-0005.sifts_uniprot_release_alignment`. There are no failed checks.

## Feasibility assessment

The computational project remains feasible under the no-laboratory constraint, with three qualifications:

1. **Evidence engineering is feasible and has passed this milestone.** The sources can be parsed reproducibly at production scale inside Apptainer on the available Arrhenius allocation.
2. **Identifier/construct reconciliation is feasible but must be auditable.** The next unit can map source-native identifiers and quantify every mapping, exclusion, ambiguity, orientation, self-pair, and deduplication transition.
3. **Naive supervised binary training is not yet scientifically feasible.** ISSUE-0003 prevents treating unreported HuRI pairs as negatives, and ISSUE-0005 prevents using unaudited structural mappings as labels. The likely viable modelling design is PU/latent-observation learning, supplemented only by explicitly qualified controls and release-safe structural evidence.

This is a controlled limitation, not a reason to stop the project. It determines the estimand and the next analyses that must be completed before training.

## Gate decision and next unit

The source-parsing and evidence-schema quality-control subgate passes with one downstream structural blocker. The overall evidence gate remains in progress.

The next authorized unit is **source reconciliation and identifier/construct mapping**. It must produce deterministic transformation audits for HuRI representations, establish exact mapping states for proteins and constructs, and isolate any release-safe structural subset. It may not create training labels or train a model.

## Reproducibility record

- Production staging root: `data/staging/primary_sources_v1`
- Parse manifest: `data/staging/primary_sources_v1/PARSE_MANIFEST.json`
- Parse-manifest SHA-256: `ca8380eec0cc1899823b43b109aa2ff9466aa44ba62a6856af76858c352960aa`
- Validation report: `artifacts/validation/evidence_parsing/primary_sources_v1/VALIDATION_REPORT.json`
- Validation-report SHA-256: `375aadc78db8783bd338a1703e84395023f26b9517999ff8985168206df271ba`
- Parser Git commit: `403397cd52dec8d7e37f571b13c73f47173fd6f0`
- Parser version: `1.2.0`
- Apptainer image: `containers/images/ipin-data-arm64_0.1.2.sif`
- Image SHA-256: `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`
- Run started: `2026-08-03T17:36:40.410533+00:00`
- Run completed: `2026-08-03T17:58:34.440329+00:00`
- Validation completed: `2026-08-03T17:59:05.933274+00:00`

The production manifest, its checksum sidecar, the validation report, and its checksum sidecar are read-only. No incomplete production directory remains.
