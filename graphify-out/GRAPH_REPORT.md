# Graph Report - /nobackup/proj/disk/theo-storage/personal/jalil/iPIN-OpenPPI  (2026-08-05)

## Corpus Check
- 323 files · ~228,764 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1378 nodes · 3499 edges · 109 communities (60 shown, 49 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 126 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- sha256 file Cluster
- tf isoform audit pipeline Cluster
- negative evidence pipeline py Cluster
- Checks Cluster
- canonical json Cluster
- sql string Cluster
- benchmark systematic screen audit Cluster
- verify raw acquisition py Cluster
- acquire manifest assets py Cluster
- validation systematic screen audit Cluster
- reconciliation py Cluster
- tf isoform py Cluster
- lambourne py Cluster
- ValueError Cluster
- iPIN OpenPPI Novelty Claim Cluster
- lambourne audit pipeline py Cluster
- huri py Cluster
- lambourne audit semantics py Cluster
- DEC 0012 Accept negative Cluster
- qualify torch gpu py Cluster
- stable id Cluster
- uniprot py Cluster
- overlap py Cluster
- Preacquisition Index v6 Cluster
- Issue 0003 HuRI Attempted Cluster
- execute Cluster
- test lambourne archives and Cluster
- test estimand policy validation Cluster
- Source Policy 001 Cluster
- run four gpu qualification Cluster
- run four gpu qualification Cluster
- sifts py Cluster
- run single gpu qualification Cluster
- run single gpu qualification Cluster
- Final Computational Blueprint and Cluster
- Technical Response to Independent Cluster
- test huri workbooks v2 Cluster
- ParquetBatchWriter Cluster
- M0 Negative Evidence Discovery Cluster
- LambournePreacquisitionTests Cluster
- Negative Evidence Audit Cluster
- validate manifest Cluster
- project paths sh Cluster
- FrozenReferenceIndex Cluster
- TFIsoformPreacquisitionTests Cluster
- Source native Staging Cluster
- AcquisitionIntegrityTests Cluster
- ScopedRawAcquisitionVerificationTests Cluster
- ingestion init py Cluster
- pipeline v4 py Cluster
- verify raw acquisition v3 Cluster
- Graphify Skill Cluster
- RawAcquisitionVerificationTests Cluster
- HardenedRawPathTests Cluster
- M0 Lambourne 2026 Human Cluster
- M0 TF Isoform 2025 Cluster
- build data sif v0 Cluster
- build qualification sif sh Cluster
- parse args Cluster
- parse args Cluster
- ProviderCountSemanticsTests Cluster
- M0 Start Manifest Cluster
- Primary Reconciliation Schema v1 Cluster
- Benchmark Design Utilities Cluster
- Active Raw Verification Entry Cluster
- Executable Entry Points Cluster
- Primary Source Parsing v4 Cluster
- Active Pre acquisition Manifest Cluster
- Active Pre acquisition Manifest Cluster
- M0 Primary Source Parsing Cluster
- DEC 0002 Repository and Cluster
- Gate Status Cluster
- Issue 0006 IM 30553 Cluster
- Source TLS Provenance Cluster
- Immutable Release Cluster
- Data Acquisition Utilities Cluster
- download data image wheels Cluster
- Active Primary Source Parser Cluster
- ipin openppi init py Cluster
- lambourne audit init py Cluster
- validation init py Cluster
- Preserved Lambourne Validator Attempt Cluster
- Project Qualification Gates v3 Cluster
- Project Path Policy Cluster
- Primary Evidence Staging Validation Cluster
- iPIN OpenPPI Project Configuration Cluster
- Primary Reconciliation Run v1 Cluster
- Primary Raw Acquisition v1 Cluster
- Source Manifests README Cluster
- Frozen Benchmark Splits README Cluster
- Staging Data README Cluster
- M0 Primary Raw Acquisition Cluster
- M0 Primary Source Reconciliation Cluster
- M0 Project Initiation and Cluster
- Project Reports README Cluster
- DEC 0003 Accept single Cluster
- DEC 0004 Pass the Cluster
- DEC 0005 Authorize acquisition Cluster
- DEC 0006 Authorize final Cluster
- Issue 0001 Checkpoint RNG Cluster
- Issue 0002 Explicit Distributed Cluster
- Issue 0007 Public 4100 Cluster
- Issue 0007 Zenodo Content Cluster
- Project Status v10 Cluster
- Project Status v14 Cluster
- ipin openppi Cluster
- iPIN OpenPPI Cluster
- Test Policy Cluster

## God Nodes (most connected - your core abstractions)
1. `stable_id()` - 59 edges
2. `sha256_file()` - 55 edges
3. `Checks` - 52 edges
4. `run_audit()` - 49 edges
5. `ParquetBatchWriter` - 46 edges
6. `canonical_json()` - 42 edges
7. `ParsingContext` - 41 edges
8. `run_negative_evidence_audit()` - 33 edges
9. `run_audit()` - 31 edges
10. `SchemaContract` - 30 edges

## Surprising Connections (you probably didn't know these)
- `test_stable_id_is_framed_and_deterministic()` --calls--> `stable_id()`  [EXTRACTED]
  tests/unit/test_ingestion_parsers.py → src/ipin_openppi/ingestion/common.py
- `test_workbook_headers_are_strict()` --calls--> `_headers()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/huri_v2.py
- `test_staging_v2_contract_and_active_parser_version()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/schema.py
- `test_schema_contract_rejects_bad_enum_and_missing_required()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_ingestion_parsers.py → src/ipin_openppi/ingestion/schema.py
- `test_family_generalization_requires_both_class_size_thresholds()` --calls--> `_aggregate_panel_metrics()`  [EXTRACTED]
  tests/unit/test_lambourne_archives_and_imex.py → src/ipin_openppi/lambourne_audit/pipeline.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Panel Governance Return** — docs_reports_m0_m0_lambourne_2026_human_y2h_pair_semantics_audit_final_v1_document, docs_reports_m0_m0_tf_isoform_2025_y2h_semantics_and_contamination_audit_final_v1_document, governance_checkpoints_resume_001_post_tf_isoform_audit_document [INFERRED 0.85]
- **Conditional Non-detection Governance** — governance_source_surveys_public_experimental_nondetection_survey_v1_nondetection_survey, governance_risks_risk_register_risk_register, schemas_canonical_negative_evidence_audit_v1_negative_evidence_audit_schema, schemas_warehouse_evidence_warehouse_v1_evidence_warehouse_schema [INFERRED 0.85]
- **Version 3 Blueprint Provenance** — docs_blueprints_ipin_openppi_final_computational_blueprint_and_workflow_v3_final_computational_blueprint_v3, docs_blueprints_ipin_openppi_expert_project_blueprint_v2_professional_expert_project_blueprint_v2, docs_blueprints_ipin_openppi_independent_technical_review_independent_technical_review, docs_blueprints_ipin_openppi_response_to_independent_review_technical_response_to_independent_review, docs_blueprints_ipin_openppi_expert_comments_on_review_response_expert_group_comments [EXTRACTED 1.00]

## Communities (109 total, 49 thin omitted)

### Community 0 - "sha256 file Cluster"
Cohesion: 0.05
Nodes (73): DataType, RecordBatch, Schema, build_argument_parser(), _load_json(), _load_yaml(), main(), _nested() (+65 more)

### Community 1 - "tf isoform audit pipeline Cluster"
Cohesion: 0.06
Nodes (72): Path, Safe, non-extracting inventory of the archived Lambourne code and inputs., Stream the archive once; inventory headers and retain only bounded selected…, _safe_member_name(), scan_tar_gzip_archive(), scan_zip_archive(), Governance-bounded audit of the 2025 human TF-isoform Y2H panel., AuditReferenceMaps (+64 more)

### Community 2 - "negative evidence pipeline py Cluster"
Cohesion: 0.06
Nodes (70): conflict_overlays(), effective_tier(), permitted_role(), Reliability tiers and conflict overlays for conditional negative evidence., reliability_tier(), build_positive_pair_index(), _glob(), index_intact_negatives() (+62 more)

### Community 3 - "Checks Cluster"
Cohesion: 0.07
Nodes (60): build_argument_parser(), _build_independent_positive_index(), _collect_metrics(), _collect_pnu(), _column_counts(), contains_record_level_report_keys(), _load_json(), _load_yaml() (+52 more)

### Community 4 - "canonical json Cluster"
Cohesion: 0.10
Nodes (58): Element, canonical_json(), ParsingContext, Any, _assay_family(), _attributes(), _child(), _children() (+50 more)

### Community 5 - "sql string Cluster"
Cohesion: 0.09
Nodes (41): build_candidate_relations(), DuckDBPyConnection, Priority-ordered participant-to-sequence candidate generation., Stop after the first route yielding candidates for a participant., _validate_policy(), build_evidence_mapping_relation(), DuckDBPyConnection, Evidence-level sequence-mapping coverage and pair projection relation. (+33 more)

### Community 6 - "benchmark systematic screen audit Cluster"
Cohesion: 0.12
Nodes (41): _archive_inventory(), _assert_expected(), assess_universe_completeness(), audit_systematic_screen_metadata(), build_argument_parser(), classify_binary_panel_result(), classify_y2h_score(), _collect_metrics() (+33 more)

### Community 7 - "verify raw acquisition py Cluster"
Cohesion: 0.12
Nodes (39): atomic_json(), ensure_regular_unlinked(), ensure_repo_path(), gzip_inventory(), line_inventory(), load_json(), local_name(), main() (+31 more)

### Community 8 - "acquire manifest assets py Cluster"
Cohesion: 0.15
Nodes (41): OpenerDirector, acquire_asset(), AcquisitionError, atomic_json(), build_https_opener(), build_plan(), detect_format(), ensure_inside_apptainer() (+33 more)

### Community 9 - "validation systematic screen audit Cluster"
Cohesion: 0.13
Nodes (36): Benchmark-design audits and policy support., build_argument_parser(), _json_field(), _load_json(), _load_yaml(), main(), _nested(), Any (+28 more)

### Community 10 - "reconciliation py Cluster"
Cohesion: 0.16
Nodes (35): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Path (+27 more)

### Community 11 - "tf isoform py Cluster"
Cohesion: 0.13
Nodes (33): build_parser(), contains_record_keys(), _evidence_checks(), _glob(), _independent_filter(), independent_y2h_outcome(), _load_json(), _load_yaml() (+25 more)

### Community 12 - "lambourne py Cluster"
Cohesion: 0.15
Nodes (28): build_parser(), contains_record_level_report_keys(), _glob(), _independent_evidence_checks(), independent_orf_id(), independent_raw_outcome(), _independent_source_metrics(), _load_json() (+20 more)

### Community 13 - "ValueError Cluster"
Cohesion: 0.21
Nodes (27): Book, Cell, _raw_bool(), _append_contact_row(), _append_fusion_row(), _append_generic_workbook_row(), _assert_expected_headers(), _headers() (+19 more)

### Community 14 - "iPIN OpenPPI Novelty Claim Cluster"
Cohesion: 0.07
Nodes (28): EMBL-EBI Terms of Use snapshot, HuRI Downloads and Terms snapshot, IntAct Portal license snapshot, PDBe Public Data Access statement snapshot, RCSB PDB Usage Policy snapshot, UniProt license snapshot, License Compliance, Source and License Register v7 (+20 more)

### Community 15 - "lambourne audit pipeline py Cluster"
Cohesion: 0.19
Nodes (25): _aggregate_panel_metrics(), _archive_inventory_rows(), _bool_value(), build_parser(), _load_json(), _load_yaml(), main(), _make_read_only() (+17 more)

### Community 16 - "huri py Cluster"
Cohesion: 0.25
Nodes (21): strip_version(), _ensembl_by_kind(), _feature_parts(), _identifiers(), _identifiers_for_database(), _interaction_semantics(), _pair_token(), parse_huri() (+13 more)

### Community 17 - "lambourne audit semantics py Cluster"
Cohesion: 0.13
Nodes (17): benchmark_claim_identifiability(), classify_paper_outcome(), OutcomeSemantics, Any, Pure semantic rules for the Lambourne Y2H-v1 audit. These functions…, Independently count the final Zhang subset and preserve all five outcomes., Frozen claim boundary used by both the pipeline and independent validator., Map the five reported states to assay-bounded semantics, fail closed. (+9 more)

### Community 18 - "DEC 0012 Accept negative Cluster"
Cohesion: 0.26
Nodes (20): DEC-0007: Accept primary raw-source acquisition, DEC-0008: Accept primary evidence staging layer, DEC-0009: Accept primary source reconciliation, DEC-0010: Propose PU compatibility as primary benchmark design, Reference-sequence Positive-Unlabeled Ranking, DEC-0011: Accept Blueprint Amendment 001 and authorize negative-evidence audit, DEC-0012: Accept negative-evidence discovery audit, Conditional Negative Evidence (+12 more)

### Community 19 - "qualify torch gpu py Cluster"
Cohesion: 0.19
Nodes (16): LRScheduler, assert_nested_equal(), execute_fixture(), main(), make_model(), parse_args(), Any, Module (+8 more)

### Community 20 - "stable id Cluster"
Cohesion: 0.23
Nodes (17): stable_id(), _reconcile_imex(), unordered_text_pair(), assay_metadata_row(), _boolish(), _orf(), parse_orf_accession_map(), parse_paper_records() (+9 more)

### Community 21 - "uniprot py Cluster"
Cohesion: 0.24
Nodes (15): _clean_annotation(), iter_fasta(), parse_dat_metadata(), _parse_fasta_header(), parse_uniprot(), Any, Path, Streaming UniProt flat-file, FASTA, and identifier-mapping parser. (+7 more)

### Community 22 - "overlap py Cluster"
Cohesion: 0.17
Nodes (15): FamilyMap, build_contamination_index(), contamination_flags(), ContaminationIndex, _family_pair_signatures(), load_negatome_pair_index(), load_sequence_family_maps(), Any (+7 more)

### Community 23 - "Preacquisition Index v6 Cluster"
Cohesion: 0.19
Nodes (16): HuRI Preacquisition Manifest v1, Human Reference Interactome, HuRI Preacquisition Manifest v2, Preacquisition Index v5, Preacquisition Index v6, IntAct IMEx Preacquisition Manifest, IntAct IMEx Evidence, Lambourne Human Y2H Preacquisition Manifest (+8 more)

### Community 24 - "Issue 0003 HuRI Attempted Cluster"
Cohesion: 0.23
Nodes (16): Gate Status v3, Gate Status v4, Gate Status v5, Gate Status v6, Gate Status v7, Gate Status v8, Gate Status v9, Issue 0003: HuRI Attempted Pair Universe (+8 more)

### Community 25 - "execute Cluster"
Cohesion: 0.24
Nodes (14): DistributedDataParallel, execute(), main(), make_model(), parse_args(), Any, Module, Namespace (+6 more)

### Community 26 - "test lambourne archives and Cluster"
Cohesion: 0.20
Nodes (13): first_uniprot_accession(), parse_mitab27(), Any, Path, Loss-minimizing parsing of the dated IM-30553 preview exports., Independently count local XML element names and interaction identifiers., _tokens(), xml_preview_inventory() (+5 more)

### Community 27 - "test estimand policy validation Cluster"
Cohesion: 0.36
Nodes (14): _failures(), _policy(), test_accepted_status_is_rejected_before_expert_approval(), test_calibration_metric_cannot_become_primary(), test_construct_threshold_cannot_be_weakened(), test_effective_policy_is_rejected_before_expert_approval(), test_frozen_proposal_semantics_pass(), test_label_authority_is_rejected() (+6 more)

### Community 28 - "Source Policy 001 Cluster"
Cohesion: 0.19
Nodes (13): Source Policy 001, Source Policy 002, Source Policy 003, Lambourne et al. Molecular Cell 2025, Source Policy 004, Systematic Screen Metadata Audit v1, TF-Isoform Y2H Semantics and Contamination Audit v1, Active Pre-acquisition Manifest Set v3 (+5 more)

### Community 29 - "run four gpu qualification Cluster"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 30 - "run four gpu qualification Cluster"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 31 - "sifts py Cluster"
Cohesion: 0.26
Nodes (11): _extract_release(), _mapping_row(), _optional_int(), _parse_gzip_tsv(), parse_sifts(), Any, Path, Streaming parsers for frozen PDBe/SIFTS mapping snapshots. (+3 more)

### Community 32 - "run single gpu qualification Cluster"
Cohesion: 0.17
Nodes (11): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUBLAS_WORKSPACE_CONFIG, APPTAINERENV_HF_HOME, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID, APPTAINERENV_TMPDIR (+3 more)

### Community 33 - "run single gpu qualification Cluster"
Cohesion: 0.17
Nodes (11): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUBLAS_WORKSPACE_CONFIG, APPTAINERENV_HF_HOME, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID, APPTAINERENV_TMPDIR (+3 more)

### Community 34 - "Final Computational Blueprint and Cluster"
Cohesion: 0.29
Nodes (11): Blueprint Amendment 001 PU Compatibility Proposal, Positive-Unlabeled Ranking, Accepted Blueprint Amendment 001, Expert Comments on Review Response, Final Computational Blueprint and Workflow v3, Evidence Record First Design, Immutable Benchmark Ladder, Partner-Aware Sparse Routing (+3 more)

### Community 35 - "Technical Response to Independent Cluster"
Cohesion: 0.31
Nodes (11): Expert Group Comments on Review Response, Operational Appendix Requirement, Expert Project Blueprint Version 2, Binding Gates, Final Computational Blueprint Version 3, Independent Technical Review and Feasibility Assessment, Strict Leakage-Resistant Evaluation, Assay-Aware Evidence-First Programme (+3 more)

### Community 36 - "test huri workbooks v2 Cluster"
Cohesion: 0.29
Nodes (8): SimpleNamespace, _asset(), CaptureWriter, _config(), test_contact_annotation_is_typed_but_never_label_authorized(), test_fusion_interference_preserves_orientation_and_missingness(), test_staging_v2_contract_and_active_parser_version(), test_workbook_headers_are_strict()

### Community 37 - "ParquetBatchWriter Cluster"
Cohesion: 0.27
Nodes (4): ParquetBatchWriter, Write validated, fixed-schema Parquet parts and retain exact statistics., Path, test_parquet_writer_embeds_contract_and_preserves_no_label_guard()

### Community 38 - "M0 Negative Evidence Discovery Cluster"
Cohesion: 0.20
Nodes (10): M0 Final Evidence-Source and License Audit, Positive-Unlabeled or Latent-Observation Design, M0 Evidence-Source and License Audit, M0 Negative-Evidence Discovery Audit, Separate Manual-Negative and Structural-Non-Contact Evidence Families, M0 Systematic-Screen Metadata Audit and Benchmark Estimand Proposal, PU-R Reference-Sequence Positive-Unlabeled Ranking Estimand, Historical Project Status and Restart Checkpoint (+2 more)

### Community 40 - "Negative Evidence Audit Cluster"
Cohesion: 0.25
Nodes (9): Benchmark Estimand Policy Proposal v1, Conditional Panel Diagnostics, Reference-Sequence Positive-Unlabeled Ranking, Benchmark Estimand Policy v1, Audit-Only, No Benchmark Integration, Lambourne Human Y2H Pair-Semantics Audit, Negative Evidence Audit, Provenance-Preserving Negative Evidence (+1 more)

### Community 41 - "validate manifest Cluster"
Cohesion: 0.56
Nodes (8): add_check(), load_yaml(), main(), nested_get(), Any, Path, sha256_file(), validate_manifest()

### Community 42 - "project paths sh Cluster"
Cohesion: 0.22
Nodes (5): IPIN_APPTAINER_CACHE, IPIN_APPTAINER_TMP, IPIN_RUNTIME_CACHE, IPIN_RUNTIME_TMP, project_paths.sh script

### Community 43 - "FrozenReferenceIndex Cluster"
Cohesion: 0.31
Nodes (6): _build_panel_rows(), _family_ids_for_candidates(), _participant_mapping_row(), FrozenReferenceIndex, Any, Path

### Community 45 - "Source native Staging Cluster"
Cohesion: 0.25
Nodes (8): Data Contracts, Versioned Data Contracts, Source-native Staging, Source-native Staging Schemas, Source-native Schema v2, Evidence Warehouse Schema v1, Evidence-record-first Warehouse, Evidence Warehouse Schemas

### Community 48 - "ingestion init py Cluster"
Cohesion: 0.29
Nodes (3): MonkeyPatch, Source-specific, provenance-preserving ingestion for iPIN-OpenPPI., test_main_injects_v4_config_once()

### Community 49 - "pipeline v4 py Cluster"
Cohesion: 0.43
Nodes (5): main(), _option_present(), Active parser routing for the primary-source v1 staging snapshot., Keep integrity bypasses confined to explicitly named smoke outputs., _require_scoped_nonproduction_output()

### Community 50 - "verify raw acquisition v3 Cluster"
Cohesion: 0.48
Nodes (5): discrepancy_aware_text_inventory(), final_atomic_json(), Any, Path, sha256_file()

### Community 51 - "Graphify Skill Cluster"
Cohesion: 0.33
Nodes (6): Semantic Extraction Specification, GitHub Clone and Graph Merge Workflow, Video and Audio Transcription Workflow, Incremental Graph Update Workflow, Graphify Skill, Project Graphify Instructions

### Community 54 - "M0 Lambourne 2026 Human Cluster"
Cohesion: 0.50
Nodes (4): M0 Lambourne 2026 Human Y2H Pair-Semantics Audit, Quarantined External Lambourne Panel, Project Status v13, Governance Records Overview

### Community 55 - "M0 TF Isoform 2025 Cluster"
Cohesion: 0.67
Nodes (4): M0 TF-Isoform 2025 Y2H Semantics and Contamination Audit, External-Only TF-Isoform Diagnostic Candidate, Post-TF-Isoform-Audit Resume Checkpoint, Project Status v15

### Community 56 - "build data sif v0 Cluster"
Cohesion: 0.50
Nodes (3): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, build_data_sif_v0_1_2.sh script

### Community 57 - "build qualification sif sh Cluster"
Cohesion: 0.50
Nodes (3): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, build_qualification_sif.sh script

### Community 58 - "parse args Cluster"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Namespace

### Community 59 - "parse args Cluster"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Namespace

### Community 61 - "M0 Start Manifest Cluster"
Cohesion: 0.67
Nodes (3): DEC-0001 Start Project Execution, Computational Claim Ceiling, M0 Start Manifest

### Community 62 - "Primary Reconciliation Schema v1 Cluster"
Cohesion: 1.00
Nodes (3): Primary Reconciliation Schema v1, Canonical Auditable Mapping, Canonical Data Schemas

### Community 63 - "Benchmark Design Utilities Cluster"
Cohesion: 0.67
Nodes (3): Benchmark Design Utilities, Label-Free Benchmark Design, Production Report Immutability

### Community 64 - "Active Raw Verification Entry Cluster"
Cohesion: 0.67
Nodes (3): Active Raw Verification Entry Point, Source Representation Warning, Raw Acquisition Verification

### Community 65 - "Executable Entry Points Cluster"
Cohesion: 0.67
Nodes (3): Executable Entry Points, Arrhenius Slurm Jobs, Source Modules

## Knowledge Gaps
- **170 isolated node(s):** `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE`, `IPIN_APPTAINER_TMP`, `IPIN_RUNTIME_CACHE` (+165 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_yaml()` connect `acquire manifest assets py Cluster` to `ValueError Cluster`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `require_within_root()` connect `qualify torch gpu py Cluster` to `ValueError Cluster`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `sha256_file()` connect `sha256 file Cluster` to `tf isoform audit pipeline Cluster`, `negative evidence pipeline py Cluster`, `Checks Cluster`, `ParquetBatchWriter Cluster`, `benchmark systematic screen audit Cluster`, `validation systematic screen audit Cluster`, `reconciliation py Cluster`, `FrozenReferenceIndex Cluster`, `lambourne py Cluster`, `tf isoform py Cluster`, `lambourne audit pipeline py Cluster`, `uniprot py Cluster`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 72 inferred relationships involving `ValueError` (e.g. with `load_yaml()` and `load_yaml()`) actually correct?**
  _`ValueError` has 72 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE` to the rest of the system?**
  _170 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `sha256 file Cluster` be split into smaller, more focused modules?**
  _Cohesion score 0.05173572228443449 - nodes in this community are weakly interconnected._
- **Should `tf isoform audit pipeline Cluster` be split into smaller, more focused modules?**
  _Cohesion score 0.057729138166894664 - nodes in this community are weakly interconnected._