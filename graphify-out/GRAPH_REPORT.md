# Graph Report - iPIN-OpenPPI  (2026-08-08)

## Corpus Check
- 296 files · ~270,705 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1758 nodes · 4402 edges · 145 communities (89 shown, 56 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 163 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1001cc8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- reconciliation/pipeline.py
- tf_isoform_audit/pipeline.py
- stable_id
- negative_evidence.py
- intact.py
- sql_string
- benchmark/systematic_screen_audit.py
- verify_raw_acquisition.py
- acquire_manifest_assets.py
- validation/systematic_screen_audit.py
- Checks
- tf_isoform.py
- load_contract
- ValueError
- iPIN-OpenPPI Novelty Claim Matrix
- lambourne_audit/pipeline.py
- huri.py
- lambourne_audit/semantics.py
- DEC-0012: Accept negative-evidence discovery audit
- qualify_torch_gpu.py
- pre_split_feasibility.py
- uniprot.py
- unordered_pair
- Preacquisition Index v6
- Issue 0003: HuRI Attempted Pair Universe
- execute
- imex.py
- test_estimand_policy_validation.py
- Source Policy 001
- run_four_gpu_qualification.sh
- run_four_gpu_qualification_long.sh
- sifts.py
- run_single_gpu_qualification.sh
- run_single_gpu_qualification_v2.sh
- Final Computational Blueprint and Workflow v3
- Technical Response to Independent Review
- sequence_component_audit/semantics.py
- ParquetBatchWriter
- M0 Negative-Evidence Discovery Audit
- LambournePreacquisitionTests
- Negative Evidence Audit
- sequence_component_audit/pipeline.py
- project_paths.sh
- M0 final report: benchmark eligibility and sequence-component audit
- TFIsoformPreacquisitionTests
- Source-native Staging
- AcquisitionIntegrityTests
- ScopedRawAcquisitionVerificationTests
- test_pipeline_v4_safety.py
- ParsingContext
- verify_raw_acquisition_v3.py
- Graphify Skill
- RawAcquisitionVerificationTests
- HardenedRawPathTests
- M0 Lambourne 2026 Human Y2H Pair-Semantics Audit
- M0 TF-Isoform 2025 Y2H Semantics and Contamination Audit
- build_data_sif_v0_1_2.sh
- build_qualification_sif.sh
- parse_args
- parse_args
- ProviderCountSemanticsTests
- M0 Start Manifest
- Primary Reconciliation Schema v1
- Benchmark Design Utilities
- Active Raw Verification Entry Point
- Executable Entry Points
- Primary Source Parsing v4
- Active Pre-acquisition Manifest Set v5
- Active Pre-acquisition Manifest Set v6
- M0 Primary-Source Parsing and Evidence Quality-Control Report
- DEC-0002 Repository and Artifact Layout
- Gate Status
- Issue 0006: IM-30553 Preview Not Integrated
- Source TLS Provenance
- Immutable Release
- Data Acquisition Utilities
- download_data_image_wheels_v0_1_2.sh
- Active Primary Source Parser
- ipin_openppi/__init__.py
- pre_split_audit/pipeline.py
- validation/__init__.py
- Preserved Lambourne Validator Attempt 001
- Project Qualification Gates v3
- Project Path Policy
- Primary Evidence Staging Validation Gate v1
- iPIN-OpenPPI Project Configuration
- Primary Reconciliation Run v1
- Primary Raw Acquisition v1 README
- Source Manifests README
- Frozen Benchmark Splits README
- Staging Data README
- M0 Primary Raw Acquisition and Integrity Report
- M0 Primary-Source Reconciliation and Construct Mapping Report
- M0 Project Initiation and Single-GPU Qualification
- Project Reports README
- DEC-0003: Accept single-GPU platform qualification
- DEC-0004: Pass the M0 qualification-container gate
- DEC-0005: Authorize acquisition from audited primary sources
- DEC-0006: Authorize final audited source manifest set v3
- Issue 0001: Checkpoint RNG Map Location
- Issue 0002: Explicit Distributed Device ID
- Issue 0007: Public 4100-Pair Universe Not Reconstructable
- Issue 0007: Zenodo Content GET Last-Modified Omission
- Project Status v10
- Project Status v14
- ipin-openppi
- iPIN-OpenPPI
- Test Policy
- pipeline_v4.py
- common.py
- graphify reference: extra exports and benchmark
- DEC-0018: Accept the benchmark-eligibility and sequence-component audit
- iPIN-OpenPPI project status and execution checkpoint
- graphify reference: query, path, explain
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0017: Accept the TF-isoform Y2H audit and quarantine disposition
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- artifacts/README.md
- containers/README.md
- canonical/README.md
- derived/README.md
- raw/README.md
- data/README.md
- sha256_file
- M0 final report: pre-split feasibility and leakage stress-test
- sequence_component_audit/support.py
- require_apptainer
- test_huri_workbooks_v2.py
- validate_manifest
- DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work.
- Q: what is the exact next step?
- lambourne_audit/source.py
- ReconciliationProvenance
- scan_tar_gzip_archive
- ArrowQueryDatasetWriter
- build_candidate_relations
- DEC-0020: Accept the pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push.
- validate_config
- Path

## God Nodes (most connected - your core abstractions)
1. `sha256_file()` - 84 edges
2. `stable_id()` - 77 edges
3. `Checks` - 74 edges
4. `ParquetBatchWriter` - 50 edges
5. `run_audit()` - 49 edges
6. `canonical_json()` - 44 edges
7. `ParsingContext` - 41 edges
8. `load_contract()` - 38 edges
9. `require_apptainer()` - 37 edges
10. `project_root_from()` - 37 edges

## Surprising Connections (you probably didn't know these)
- `test_stable_id_is_framed_and_deterministic()` --calls--> `stable_id()`  [EXTRACTED]
  tests/unit/test_ingestion_parsers.py → src/ipin_openppi/ingestion/common.py
- `test_workbook_headers_are_strict()` --calls--> `_headers()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/huri_v2.py
- `test_staging_v2_contract_and_active_parser_version()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/schema.py
- `test_schema_contract_rejects_bad_enum_and_missing_required()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_ingestion_parsers.py → src/ipin_openppi/ingestion/schema.py
- `test_schema_is_aggregate_only_and_has_explicit_false_guards()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_pre_split_safety.py → src/ipin_openppi/ingestion/schema.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Panel Governance Return** — docs_reports_m0_m0_lambourne_2026_human_y2h_pair_semantics_audit_final_v1_document, docs_reports_m0_m0_tf_isoform_2025_y2h_semantics_and_contamination_audit_final_v1_document, governance_checkpoints_resume_001_post_tf_isoform_audit_document [INFERRED 0.85]
- **Conditional Non-detection Governance** — governance_source_surveys_public_experimental_nondetection_survey_v1_nondetection_survey, governance_risks_risk_register_risk_register, schemas_canonical_negative_evidence_audit_v1_negative_evidence_audit_schema, schemas_warehouse_evidence_warehouse_v1_evidence_warehouse_schema [INFERRED 0.85]
- **Version 3 Blueprint Provenance** — docs_blueprints_ipin_openppi_final_computational_blueprint_and_workflow_v3_final_computational_blueprint_v3, docs_blueprints_ipin_openppi_expert_project_blueprint_v2_professional_expert_project_blueprint_v2, docs_blueprints_ipin_openppi_independent_technical_review_independent_technical_review, docs_blueprints_ipin_openppi_response_to_independent_review_technical_response_to_independent_review, docs_blueprints_ipin_openppi_expert_comments_on_review_response_expert_group_comments [EXTRACTED 1.00]

## Communities (145 total, 56 thin omitted)

### Community 0 - "reconciliation/pipeline.py"
Cohesion: 0.17
Nodes (19): AtomicDatasetDirectory, Create a dataset in a sibling temporary directory, then rename atomically., Deterministic source, identifier, sequence, and construct reconciliation., build_argument_parser(), _iter_manifest_files(), main(), _make_read_only(), Any (+11 more)

### Community 1 - "tf_isoform_audit/pipeline.py"
Cohesion: 0.06
Nodes (66): Governance-bounded audit of the 2025 human TF-isoform Y2H panel., AuditReferenceMaps, Any, Path, Deterministic mapping of exact TF clones and ORFeome partner constructs., _sorted_strings(), _aggregate_findings(), _bool_token() (+58 more)

### Community 2 - "stable_id"
Cohesion: 0.06
Nodes (71): stable_id(), conflict_overlays(), effective_tier(), permitted_role(), Reliability tiers and conflict overlays for conditional negative evidence., reliability_tier(), build_positive_pair_index(), _glob() (+63 more)

### Community 3 - "negative_evidence.py"
Cohesion: 0.16
Nodes (31): build_argument_parser(), _build_independent_positive_index(), _collect_metrics(), _collect_pnu(), _column_counts(), contains_record_level_report_keys(), _load_json(), _load_yaml() (+23 more)

### Community 4 - "intact.py"
Cohesion: 0.36
Nodes (24): Element, _assay_family(), _attributes(), _child(), _children(), _confidence_values(), _cv_term(), _descendant_text() (+16 more)

### Community 5 - "sql_string"
Cohesion: 0.16
Nodes (20): build_huri_work_tables(), DuckDBPyConnection, HuRI detailed-evidence to provider-pair representation reconciliation., parquet_glob(), Path, Frozen reconciliation provenance and safe SQL literal helpers., sql_string(), build_sifts_work_table() (+12 more)

### Community 6 - "benchmark/systematic_screen_audit.py"
Cohesion: 0.12
Nodes (41): _archive_inventory(), _assert_expected(), assess_universe_completeness(), audit_systematic_screen_metadata(), build_argument_parser(), classify_binary_panel_result(), classify_y2h_score(), _collect_metrics() (+33 more)

### Community 7 - "verify_raw_acquisition.py"
Cohesion: 0.12
Nodes (39): atomic_json(), ensure_regular_unlinked(), ensure_repo_path(), gzip_inventory(), line_inventory(), load_json(), local_name(), main() (+31 more)

### Community 8 - "acquire_manifest_assets.py"
Cohesion: 0.15
Nodes (41): OpenerDirector, acquire_asset(), AcquisitionError, atomic_json(), build_https_opener(), build_plan(), detect_format(), ensure_inside_apptainer() (+33 more)

### Community 9 - "validation/systematic_screen_audit.py"
Cohesion: 0.13
Nodes (36): Benchmark-design audits and policy support., build_argument_parser(), _json_field(), _load_json(), _load_yaml(), main(), _nested(), Any (+28 more)

### Community 10 - "Checks"
Cohesion: 0.05
Nodes (85): DataType, Schema, build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any (+77 more)

### Community 11 - "tf_isoform.py"
Cohesion: 0.13
Nodes (34): load_asset_index(), build_parser(), contains_record_keys(), _evidence_checks(), _glob(), _independent_filter(), independent_y2h_outcome(), _load_json() (+26 more)

### Community 12 - "load_contract"
Cohesion: 0.14
Nodes (30): load_contract(), Path, build_parser(), contains_record_level_report_keys(), _glob(), _independent_evidence_checks(), independent_orf_id(), independent_raw_outcome() (+22 more)

### Community 13 - "ValueError"
Cohesion: 0.21
Nodes (27): Book, Cell, _raw_bool(), _append_contact_row(), _append_fusion_row(), _append_generic_workbook_row(), _assert_expected_headers(), _headers() (+19 more)

### Community 14 - "iPIN-OpenPPI Novelty Claim Matrix"
Cohesion: 0.07
Nodes (28): EMBL-EBI Terms of Use snapshot, HuRI Downloads and Terms snapshot, IntAct Portal license snapshot, PDBe Public Data Access statement snapshot, RCSB PDB Usage Policy snapshot, UniProt license snapshot, License Compliance, Source and License Register v7 (+20 more)

### Community 15 - "lambourne_audit/pipeline.py"
Cohesion: 0.15
Nodes (30): Governance-bounded audit of the Lambourne et al. human Y2H-v1 panel., _aggregate_panel_metrics(), _archive_inventory_rows(), _bool_value(), build_parser(), _family_ids_for_candidates(), _load_json(), _load_yaml() (+22 more)

### Community 16 - "huri.py"
Cohesion: 0.26
Nodes (20): _ensembl_by_kind(), _feature_parts(), _identifiers(), _identifiers_for_database(), _interaction_semantics(), _pair_token(), parse_huri(), _parse_identifier() (+12 more)

### Community 17 - "lambourne_audit/semantics.py"
Cohesion: 0.13
Nodes (17): benchmark_claim_identifiability(), classify_paper_outcome(), OutcomeSemantics, Any, Pure semantic rules for the Lambourne Y2H-v1 audit. These functions…, Independently count the final Zhang subset and preserve all five outcomes., Frozen claim boundary used by both the pipeline and independent validator., Map the five reported states to assay-bounded semantics, fail closed. (+9 more)

### Community 18 - "DEC-0012: Accept negative-evidence discovery audit"
Cohesion: 0.26
Nodes (20): DEC-0007: Accept primary raw-source acquisition, DEC-0008: Accept primary evidence staging layer, DEC-0009: Accept primary source reconciliation, DEC-0010: Propose PU compatibility as primary benchmark design, Reference-sequence Positive-Unlabeled Ranking, DEC-0011: Accept Blueprint Amendment 001 and authorize negative-evidence audit, DEC-0012: Accept negative-evidence discovery audit, Conditional Negative Evidence (+12 more)

### Community 19 - "qualify_torch_gpu.py"
Cohesion: 0.19
Nodes (16): LRScheduler, assert_nested_equal(), execute_fixture(), main(), make_model(), parse_args(), Any, Module (+8 more)

### Community 20 - "pre_split_feasibility.py"
Cohesion: 0.06
Nodes (58): Pair, Governance-bounded aggregate pre-split feasibility and leakage audit., allocate_components(), allocation_order(), degree_gini(), degree_histogram(), degree_summary(), deterministic_components() (+50 more)

### Community 21 - "uniprot.py"
Cohesion: 0.23
Nodes (16): strip_version(), _clean_annotation(), iter_fasta(), parse_dat_metadata(), _parse_fasta_header(), parse_uniprot(), Any, Path (+8 more)

### Community 22 - "unordered_pair"
Cohesion: 0.16
Nodes (19): FamilyMap, build_contamination_index(), contamination_flags(), ContaminationIndex, _family_pair_signatures(), load_negatome_pair_index(), load_sequence_family_maps(), Any (+11 more)

### Community 23 - "Preacquisition Index v6"
Cohesion: 0.19
Nodes (16): HuRI Preacquisition Manifest v1, Human Reference Interactome, HuRI Preacquisition Manifest v2, Preacquisition Index v5, Preacquisition Index v6, IntAct IMEx Preacquisition Manifest, IntAct IMEx Evidence, Lambourne Human Y2H Preacquisition Manifest (+8 more)

### Community 24 - "Issue 0003: HuRI Attempted Pair Universe"
Cohesion: 0.23
Nodes (16): Gate Status v3, Gate Status v4, Gate Status v5, Gate Status v6, Gate Status v7, Gate Status v8, Gate Status v9, Issue 0003: HuRI Attempted Pair Universe (+8 more)

### Community 25 - "execute"
Cohesion: 0.24
Nodes (14): DistributedDataParallel, execute(), main(), make_model(), parse_args(), Any, Module, Namespace (+6 more)

### Community 26 - "imex.py"
Cohesion: 0.33
Nodes (8): first_uniprot_accession(), parse_mitab27(), Any, Path, Loss-minimizing parsing of the dated IM-30553 preview exports., Independently count local XML element names and interaction identifiers., _tokens(), xml_preview_inventory()

### Community 27 - "test_estimand_policy_validation.py"
Cohesion: 0.36
Nodes (14): _failures(), _policy(), test_accepted_status_is_rejected_before_expert_approval(), test_calibration_metric_cannot_become_primary(), test_construct_threshold_cannot_be_weakened(), test_effective_policy_is_rejected_before_expert_approval(), test_frozen_proposal_semantics_pass(), test_label_authority_is_rejected() (+6 more)

### Community 28 - "Source Policy 001"
Cohesion: 0.19
Nodes (13): Source Policy 001, Source Policy 002, Source Policy 003, Lambourne et al. Molecular Cell 2025, Source Policy 004, Systematic Screen Metadata Audit v1, TF-Isoform Y2H Semantics and Contamination Audit v1, Active Pre-acquisition Manifest Set v3 (+5 more)

### Community 29 - "run_four_gpu_qualification.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 30 - "run_four_gpu_qualification_long.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 31 - "sifts.py"
Cohesion: 0.21
Nodes (13): _extract_release(), _mapping_row(), _optional_int(), _parse_gzip_tsv(), parse_sifts(), Any, Path, Streaming parsers for frozen PDBe/SIFTS mapping snapshots. (+5 more)

### Community 32 - "run_single_gpu_qualification.sh"
Cohesion: 0.17
Nodes (11): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUBLAS_WORKSPACE_CONFIG, APPTAINERENV_HF_HOME, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID, APPTAINERENV_TMPDIR (+3 more)

### Community 33 - "run_single_gpu_qualification_v2.sh"
Cohesion: 0.17
Nodes (11): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUBLAS_WORKSPACE_CONFIG, APPTAINERENV_HF_HOME, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID, APPTAINERENV_TMPDIR (+3 more)

### Community 34 - "Final Computational Blueprint and Workflow v3"
Cohesion: 0.29
Nodes (11): Blueprint Amendment 001 PU Compatibility Proposal, Positive-Unlabeled Ranking, Accepted Blueprint Amendment 001, Expert Comments on Review Response, Final Computational Blueprint and Workflow v3, Evidence Record First Design, Immutable Benchmark Ladder, Partner-Aware Sparse Routing (+3 more)

### Community 35 - "Technical Response to Independent Review"
Cohesion: 0.31
Nodes (11): Expert Group Comments on Review Response, Operational Appendix Requirement, Expert Project Blueprint Version 2, Binding Gates, Final Computational Blueprint Version 3, Independent Technical Review and Feasibility Assessment, Strict Leakage-Resistant Evaluation, Assay-Aware Evidence-First Programme (+3 more)

### Community 36 - "sequence_component_audit/semantics.py"
Cohesion: 0.12
Nodes (20): classify_gene_mapping(), classify_positive_projection(), ComponentMembership, deterministic_component_memberships(), DeterministicDisjointSet, endpoint_coverage(), exact_identity(), exact_unordered_pair_count() (+12 more)

### Community 37 - "ParquetBatchWriter"
Cohesion: 0.23
Nodes (14): canonical_json(), ParquetBatchWriter, Any, Write validated, fixed-schema Parquet parts and retain exact statistics., _emit_interaction(), _emit_participant(), parse_intact(), _parse_mutations() (+6 more)

### Community 38 - "M0 Negative-Evidence Discovery Audit"
Cohesion: 0.20
Nodes (10): M0 Final Evidence-Source and License Audit, Positive-Unlabeled or Latent-Observation Design, M0 Evidence-Source and License Audit, M0 Negative-Evidence Discovery Audit, Separate Manual-Negative and Structural-Non-Contact Evidence Families, M0 Systematic-Screen Metadata Audit and Benchmark Estimand Proposal, PU-R Reference-Sequence Positive-Unlabeled Ranking Estimand, Historical Project Status and Restart Checkpoint (+2 more)

### Community 40 - "Negative Evidence Audit"
Cohesion: 0.25
Nodes (9): Benchmark Estimand Policy Proposal v1, Conditional Panel Diagnostics, Reference-Sequence Positive-Unlabeled Ranking, Benchmark Estimand Policy v1, Audit-Only, No Benchmark Integration, Lambourne Human Y2H Pair-Semantics Audit, Negative Evidence Audit, Provenance-Preserving Negative Evidence (+1 more)

### Community 41 - "sequence_component_audit/pipeline.py"
Cohesion: 0.17
Nodes (28): build_argument_parser(), _build_components(), _build_eligibility(), _build_feasibility(), _build_positive_aggregates(), main(), _nearest_rank(), _normalize_alignments() (+20 more)

### Community 42 - "project_paths.sh"
Cohesion: 0.22
Nodes (5): IPIN_APPTAINER_CACHE, IPIN_APPTAINER_TMP, IPIN_RUNTIME_CACHE, IPIN_RUNTIME_TMP, project_paths.sh script

### Community 43 - "M0 final report: benchmark eligibility and sequence-component audit"
Cohesion: 0.15
Nodes (12): 10. Scientific interpretation and governance return, 1. Scope and frozen inputs, 2. Eligibility census, 3. Frozen sequence-similarity method, 4. Fail-closed alignment reconciliation, 5. Deterministic component census, 6. Aggregate positive-evidence mapping, 7. Pre-split component feasibility aggregates (+4 more)

### Community 45 - "Source-native Staging"
Cohesion: 0.25
Nodes (8): Data Contracts, Versioned Data Contracts, Source-native Staging, Source-native Staging Schemas, Source-native Schema v2, Evidence Warehouse Schema v1, Evidence-record-first Warehouse, Evidence Warehouse Schemas

### Community 49 - "ParsingContext"
Cohesion: 0.16
Nodes (13): ParsingContext, Any, iter_reconstructed_mutation_rows(), parse_intact(), _parse_mutations_v2(), Any, Path, Active IntAct parser with deterministic repair of malformed TSV line wraps. The… (+5 more)

### Community 50 - "verify_raw_acquisition_v3.py"
Cohesion: 0.48
Nodes (5): discrepancy_aware_text_inventory(), final_atomic_json(), Any, Path, sha256_file()

### Community 51 - "Graphify Skill"
Cohesion: 0.33
Nodes (6): Semantic Extraction Specification, GitHub Clone and Graph Merge Workflow, Video and Audio Transcription Workflow, Incremental Graph Update Workflow, Graphify Skill, Project Graphify Instructions

### Community 54 - "M0 Lambourne 2026 Human Y2H Pair-Semantics Audit"
Cohesion: 0.50
Nodes (4): M0 Lambourne 2026 Human Y2H Pair-Semantics Audit, Quarantined External Lambourne Panel, Project Status v13, Governance Records Overview

### Community 55 - "M0 TF-Isoform 2025 Y2H Semantics and Contamination Audit"
Cohesion: 0.67
Nodes (4): M0 TF-Isoform 2025 Y2H Semantics and Contamination Audit, External-Only TF-Isoform Diagnostic Candidate, Post-TF-Isoform-Audit Resume Checkpoint, Project Status v15

### Community 56 - "build_data_sif_v0_1_2.sh"
Cohesion: 0.50
Nodes (3): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, build_data_sif_v0_1_2.sh script

### Community 57 - "build_qualification_sif.sh"
Cohesion: 0.50
Nodes (3): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, build_qualification_sif.sh script

### Community 58 - "parse_args"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Namespace

### Community 59 - "parse_args"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Namespace

### Community 61 - "M0 Start Manifest"
Cohesion: 0.67
Nodes (3): DEC-0001 Start Project Execution, Computational Claim Ceiling, M0 Start Manifest

### Community 62 - "Primary Reconciliation Schema v1"
Cohesion: 1.00
Nodes (3): Primary Reconciliation Schema v1, Canonical Auditable Mapping, Canonical Data Schemas

### Community 63 - "Benchmark Design Utilities"
Cohesion: 0.67
Nodes (3): Benchmark Design Utilities, Label-Free Benchmark Design, Production Report Immutability

### Community 64 - "Active Raw Verification Entry Point"
Cohesion: 0.67
Nodes (3): Active Raw Verification Entry Point, Source Representation Warning, Raw Acquisition Verification

### Community 65 - "Executable Entry Points"
Cohesion: 0.67
Nodes (3): Executable Entry Points, Arrhenius Slurm Jobs, Source Modules

### Community 80 - "pre_split_audit/pipeline.py"
Cohesion: 0.14
Nodes (34): _allocation_summary(), _base_component_order(), _build_aggregate_tables(), build_argument_parser(), _claim_rows(), _component_degree_row(), _component_summary(), _degree_row() (+26 more)

### Community 109 - "pipeline_v4.py"
Cohesion: 0.15
Nodes (16): Source-specific, provenance-preserving ingestion for iPIN-OpenPPI., _CardinalityCorrectingWriter, _correct_participant_cardinality(), _emit_interaction_v3(), parse_intact(), Any, Path, IntAct parser revision with exact unary/binary/n-ary semantics. Revision 2… (+8 more)

### Community 110 - "common.py"
Cohesion: 0.19
Nodes (18): git_provenance(), Shared ingestion primitives with deterministic IDs and atomic Parquet output., RawAsset, utc_now(), verify_asset(), Typed context shared by source parsers., build_argument_parser(), main() (+10 more)

### Community 111 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 112 - "DEC-0018: Accept the benchmark-eligibility and sequence-component audit"
Cohesion: 0.25
Nodes (7): Accepted evidence, Accepted findings, Continuing prohibitions and next authority, DEC-0018: Accept the benchmark-eligibility and sequence-component audit, Decision, External-panel disposition remains binding, Fail-closed disposition

### Community 113 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted aggregate results, Completed bounded audit, Current stopping point, External-panel governance remains closed, Immutable evidence, iPIN-OpenPPI project status and execution checkpoint

### Community 114 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 115 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Binding prohibitions, Immutable evidence accepted without recomputation, iPIN-OpenPPI project status and execution checkpoint, Minimal governance disposition, Resumed work package

### Community 116 - "DEC-0017: Accept the TF-isoform Y2H audit and quarantine disposition"
Cohesion: 0.40
Nodes (4): Accepted evidence, Continuing authority, DEC-0017: Accept the TF-isoform Y2H audit and quarantine disposition, Decision

### Community 117 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 118 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 125 - "sha256_file"
Cohesion: 0.17
Nodes (22): sha256_file(), Governance-bounded benchmark eligibility and sequence-component audit., build_argument_parser(), _check_sidecar(), _independent_components(), _independent_eligibility(), _independent_positive_metrics(), _IndependentDisjointSet (+14 more)

### Community 126 - "M0 final report: pre-split feasibility and leakage stress-test"
Cohesion: 0.11
Nodes (17): 1. Scope and immutable inputs, 2.1 Positive-network summaries, 2.2 Similarity challenges, 2.3 Ephemeral allocation trials, 2. Governed methods, 3.1 Source composition, 3.2 Endpoint degree and hub concentration, 3.3 ALL-source component positive-edge load (+9 more)

### Community 127 - "sequence_component_audit/support.py"
Cohesion: 0.24
Nodes (21): _verify_inputs(), Path, Fail-closed configuration and output guards for the pre-split audit., require_output_paths(), artifact_inventory(), find_table_summary(), iter_table_summaries(), load_json() (+13 more)

### Community 128 - "require_apptainer"
Cohesion: 0.14
Nodes (22): main(), require_apptainer(), validate_config(), _download(), _load_yaml(), prepare_mmseqs_install(), Any, Path (+14 more)

### Community 129 - "test_huri_workbooks_v2.py"
Cohesion: 0.29
Nodes (8): SimpleNamespace, _asset(), CaptureWriter, _config(), test_contact_annotation_is_typed_but_never_label_authorized(), test_fusion_interference_preserves_orientation_and_missingness(), test_staging_v2_contract_and_active_parser_version(), test_workbook_headers_are_strict()

### Community 130 - "validate_manifest"
Cohesion: 0.56
Nodes (8): add_check(), load_yaml(), main(), nested_get(), Any, Path, sha256_file(), validate_manifest()

### Community 131 - "DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test"
Cohesion: 0.29
Nodes (6): Binding scientific design, Continuing prohibitions, DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test, Decision, Necessary interpretation of the expert comment, Required return

### Community 132 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Authorization now active, Binding hold, External panels remain closed, Immutable parent evidence, iPIN-OpenPPI project status and execution checkpoint

### Community 133 - "Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work., Source Nodes

### Community 134 - "Q: what is the exact next step?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: what is the exact next step?, Source Nodes

### Community 135 - "lambourne_audit/source.py"
Cohesion: 0.27
Nodes (14): unordered_text_pair(), assay_metadata_row(), _boolish(), _orf(), parse_orf_accession_map(), parse_paper_records(), parse_raw_assay_records(), parse_selection_records() (+6 more)

### Community 136 - "ReconciliationProvenance"
Cohesion: 0.24
Nodes (11): build_evidence_mapping_relation(), DuckDBPyConnection, Evidence-level sequence-mapping coverage and pair projection relation., build_mapping_work_tables(), DuckDBPyConnection, Build participant and evidence mapping relations in dependency order., build_participant_mapping_relation(), DuckDBPyConnection (+3 more)

### Community 137 - "scan_tar_gzip_archive"
Cohesion: 0.24
Nodes (11): Path, Safe, non-extracting inventory of the archived Lambourne code and inputs., Stream the archive once; inventory headers and retain only bounded selected…, _safe_member_name(), scan_tar_gzip_archive(), scan_zip_archive(), Path, test_imex_reconciliation_distinguishes_records_from_distinct_panel_pairs() (+3 more)

### Community 138 - "ArrowQueryDatasetWriter"
Cohesion: 0.18
Nodes (8): RecordBatch, ArrowQueryDatasetWriter, Any, DuckDBPyConnection, Path, Deterministic Arrow/Parquet output for DuckDB reconciliation queries., Stream a DuckDB query into fixed-schema, checksummed Parquet parts., Table

### Community 139 - "build_candidate_relations"
Cohesion: 0.21
Nodes (10): build_candidate_relations(), DuckDBPyConnection, Priority-ordered participant-to-sequence candidate generation., Stop after the first route yielding candidates for a participant., _validate_policy(), _fixture_connection(), DuckDBPyConnection, test_manifest_file_discovery_stops_at_table_summary() (+2 more)

### Community 140 - "DEC-0020: Accept the pre-split feasibility and leakage stress-test"
Cohesion: 0.22
Nodes (8): Accepted evidence, Accepted findings, C3 and claim disposition, Continuing prohibitions and next authority, DEC-0020: Accept the pre-split feasibility and leakage stress-test, Decision, External-panel disposition remains binding, Final-split feasibility disposition

### Community 141 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted audit, Binding hold, Claim boundary, External panels remain closed, Feasibility disposition, iPIN-OpenPPI project status and execution checkpoint

### Community 142 - "Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push., Source Nodes

### Community 143 - "validate_config"
Cohesion: 0.40
Nodes (4): Any, validate_config(), test_config_preserves_pu_r_parent_and_all_prohibitions(), test_schema_is_aggregate_only_and_has_explicit_false_guards()

## Knowledge Gaps
- **264 isolated node(s):** `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE`, `IPIN_APPTAINER_TMP`, `IPIN_RUNTIME_CACHE` (+259 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Reference-sequence Positive-Unlabeled Ranking` (2× useful, score=1.9924797)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sha256_file()` connect `sha256_file` to `reconciliation/pipeline.py`, `require_apptainer`, `stable_id`, `tf_isoform_audit/pipeline.py`, `negative_evidence.py`, `benchmark/systematic_screen_audit.py`, `validation/systematic_screen_audit.py`, `Checks`, `ArrowQueryDatasetWriter`, `load_contract`, `tf_isoform.py`, `lambourne_audit/pipeline.py`, `pre_split_feasibility.py`, `uniprot.py`, `unordered_pair`, `ParquetBatchWriter`, `sequence_component_audit/pipeline.py`, `pre_split_audit/pipeline.py`, `common.py`, `sequence_component_audit/support.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `load_yaml()` connect `acquire_manifest_assets.py` to `ValueError`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `stable_id()` connect `stable_id` to `tf_isoform_audit/pipeline.py`, `intact.py`, `ParquetBatchWriter`, `sequence_component_audit/semantics.py`, `lambourne_audit/source.py`, `sequence_component_audit/pipeline.py`, `ValueError`, `common.py`, `lambourne_audit/pipeline.py`, `huri.py`, `ParsingContext`, `pre_split_audit/pipeline.py`, `uniprot.py`, `unordered_pair`, `sha256_file`, `sifts.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `ValueError` (e.g. with `load_yaml()` and `load_yaml()`) actually correct?**
  _`ValueError` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Checks` (e.g. with `IndependentDisjointSet` and `_IndependentDisjointSet`) actually correct?**
  _`Checks` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE` to the rest of the system?**
  _264 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tf_isoform_audit/pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06394027913015254 - nodes in this community are weakly interconnected._