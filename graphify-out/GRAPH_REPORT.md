# Graph Report - iPIN-OpenPPI  (2026-08-08)

## Corpus Check
- 308 files · ~283,052 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1873 nodes · 4728 edges · 139 communities (85 shown, 54 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa57f379`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- component_split/pipeline.py
- tf_isoform_audit/pipeline.py
- negative_evidence/pipeline.py
- negative_evidence.py
- ParsingContext
- reconciliation/pipeline.py
- benchmark/systematic_screen_audit.py
- verify_raw_acquisition.py
- acquire_manifest_assets.py
- validation/systematic_screen_audit.py
- staging.py
- tf_isoform.py
- lambourne.py
- ValueError
- iPIN-OpenPPI Novelty Claim Matrix
- lambourne_audit/pipeline.py
- component_split.py
- summarize_final_analysis
- DEC-0012: Accept negative-evidence discovery audit
- qualify_torch_gpu.py
- pre_split_feasibility.py
- reconciliation.py
- overlap.py
- Preacquisition Index v6
- Issue 0003: HuRI Attempted Pair Universe
- execute
- imex.py
- estimand_policy_validation.py
- Source Policy 001
- run_four_gpu_qualification.sh
- run_four_gpu_qualification_long.sh
- sifts.py
- run_single_gpu_qualification.sh
- run_single_gpu_qualification_v2.sh
- Final Computational Blueprint and Workflow v3
- Technical Response to Independent Review
- sequence_component_audit/semantics.py
- reconciliation_semantics.py
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
- DEC-0021: Authorize the final benchmark component-partition skeleton
- iPIN-OpenPPI project status and execution checkpoint
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
- stable_id
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
- tooling.py
- validate_manifest
- DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work.
- Q: what is the exact next step?
- lambourne_audit/source.py
- scan_tar_gzip_archive
- DEC-0020: Accept the pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push.
- load_contract

## God Nodes (most connected - your core abstractions)
1. `sha256_file()` - 90 edges
2. `Checks` - 81 edges
3. `stable_id()` - 77 edges
4. `ParquetBatchWriter` - 52 edges
5. `run_audit()` - 49 edges
6. `canonical_json()` - 46 edges
7. `load_contract()` - 43 edges
8. `require_apptainer()` - 41 edges
9. `project_root_from()` - 41 edges
10. `ParsingContext` - 41 edges

## Surprising Connections (you probably didn't know these)
- `test_config_freezes_primary_fallback_objective_and_scope()` --calls--> `validate_config()`  [EXTRACTED]
  tests/unit/test_component_split_safety.py → src/ipin_openppi/component_split/support.py
- `test_staging_v2_contract_and_active_parser_version()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/schema.py
- `test_schema_has_only_bounded_tables_and_false_guard_columns()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_sequence_component_safety.py → src/ipin_openppi/ingestion/schema.py
- `test_negative_is_assay_bounded_and_never_authorized_as_label()` --calls--> `classify_paper_outcome()`  [EXTRACTED]
  tests/unit/test_lambourne_semantics.py → src/ipin_openppi/lambourne_audit/semantics.py
- `test_technical_state_is_not_negative()` --calls--> `classify_paper_outcome()`  [EXTRACTED]
  tests/unit/test_lambourne_semantics.py → src/ipin_openppi/lambourne_audit/semantics.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Panel Governance Return** — docs_reports_m0_m0_lambourne_2026_human_y2h_pair_semantics_audit_final_v1_document, docs_reports_m0_m0_tf_isoform_2025_y2h_semantics_and_contamination_audit_final_v1_document, governance_checkpoints_resume_001_post_tf_isoform_audit_document [INFERRED 0.85]
- **Conditional Non-detection Governance** — governance_source_surveys_public_experimental_nondetection_survey_v1_nondetection_survey, governance_risks_risk_register_risk_register, schemas_canonical_negative_evidence_audit_v1_negative_evidence_audit_schema, schemas_warehouse_evidence_warehouse_v1_evidence_warehouse_schema [INFERRED 0.85]
- **Version 3 Blueprint Provenance** — docs_blueprints_ipin_openppi_final_computational_blueprint_and_workflow_v3_final_computational_blueprint_v3, docs_blueprints_ipin_openppi_expert_project_blueprint_v2_professional_expert_project_blueprint_v2, docs_blueprints_ipin_openppi_independent_technical_review_independent_technical_review, docs_blueprints_ipin_openppi_response_to_independent_review_technical_response_to_independent_review, docs_blueprints_ipin_openppi_expert_comments_on_review_response_expert_group_comments [EXTRACTED 1.00]

## Communities (139 total, 54 thin omitted)

### Community 0 - "component_split/pipeline.py"
Cohesion: 0.09
Nodes (45): Governance-bounded final benchmark component-partition skeleton., build_argument_parser(), _edge_set(), _load_graphs(), _load_parent_state(), _load_positive_pairs(), main(), Any (+37 more)

### Community 1 - "tf_isoform_audit/pipeline.py"
Cohesion: 0.06
Nodes (66): Governance-bounded audit of the 2025 human TF-isoform Y2H panel., AuditReferenceMaps, Any, Path, Deterministic mapping of exact TF clones and ORFeome partner constructs., _sorted_strings(), _aggregate_findings(), _bool_token() (+58 more)

### Community 2 - "negative_evidence/pipeline.py"
Cohesion: 0.06
Nodes (71): conflict_overlays(), effective_tier(), permitted_role(), Reliability tiers and conflict overlays for conditional negative evidence., reliability_tier(), build_positive_pair_index(), _glob(), index_intact_negatives() (+63 more)

### Community 3 - "negative_evidence.py"
Cohesion: 0.16
Nodes (31): build_argument_parser(), _build_independent_positive_index(), _collect_metrics(), _collect_pnu(), _column_counts(), contains_record_level_report_keys(), _load_json(), _load_yaml() (+23 more)

### Community 4 - "ParsingContext"
Cohesion: 0.08
Nodes (60): Element, MonkeyPatch, ParsingContext, Any, Source-specific, provenance-preserving ingestion for iPIN-OpenPPI., _assay_family(), _attributes(), _child() (+52 more)

### Community 5 - "reconciliation/pipeline.py"
Cohesion: 0.05
Nodes (66): RecordBatch, build_candidate_relations(), DuckDBPyConnection, Priority-ordered participant-to-sequence candidate generation., Stop after the first route yielding candidates for a participant., _validate_policy(), build_evidence_mapping_relation(), DuckDBPyConnection (+58 more)

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

### Community 10 - "staging.py"
Cohesion: 0.14
Nodes (27): build_argument_parser(), DatasetSummary, _iter_summaries(), _load_json(), _load_yaml(), main(), _nested(), Any (+19 more)

### Community 11 - "tf_isoform.py"
Cohesion: 0.13
Nodes (33): build_parser(), contains_record_keys(), _evidence_checks(), _glob(), _independent_filter(), independent_y2h_outcome(), _load_json(), _load_yaml() (+25 more)

### Community 12 - "lambourne.py"
Cohesion: 0.15
Nodes (28): build_parser(), contains_record_level_report_keys(), _glob(), _independent_evidence_checks(), independent_orf_id(), independent_raw_outcome(), _independent_source_metrics(), _load_json() (+20 more)

### Community 13 - "ValueError"
Cohesion: 0.06
Nodes (81): Book, Cell, SimpleNamespace, canonical_json(), ParquetBatchWriter, Any, Write validated, fixed-schema Parquet parts and retain exact statistics., strip_version() (+73 more)

### Community 14 - "iPIN-OpenPPI Novelty Claim Matrix"
Cohesion: 0.07
Nodes (28): EMBL-EBI Terms of Use snapshot, HuRI Downloads and Terms snapshot, IntAct Portal license snapshot, PDBe Public Data Access statement snapshot, RCSB PDB Usage Policy snapshot, UniProt license snapshot, License Compliance, Source and License Register v7 (+20 more)

### Community 15 - "lambourne_audit/pipeline.py"
Cohesion: 0.16
Nodes (27): Governance-bounded audit of the Lambourne et al. human Y2H-v1 panel., _aggregate_panel_metrics(), _archive_inventory_rows(), _bool_value(), build_parser(), _load_json(), _load_yaml(), main() (+19 more)

### Community 16 - "component_split.py"
Cohesion: 0.11
Nodes (36): Any, Reject any configuration that broadens or mutates the frozen package., validate_config(), _allocate(), build_argument_parser(), _check_sidecar(), _component_id(), _components() (+28 more)

### Community 17 - "summarize_final_analysis"
Cohesion: 0.18
Nodes (10): benchmark_claim_identifiability(), Independently count the final Zhang subset and preserve all five outcomes., Frozen claim boundary used by both the pipeline and independent validator., summarize_final_analysis(), parametrize, test_claim_boundary_rejects_universal_and_biological_probability_claims(), test_final_summary_keeps_positive_negative_and_na_separate(), test_negative_is_assay_bounded_and_never_authorized_as_label() (+2 more)

### Community 18 - "DEC-0012: Accept negative-evidence discovery audit"
Cohesion: 0.26
Nodes (20): DEC-0007: Accept primary raw-source acquisition, DEC-0008: Accept primary evidence staging layer, DEC-0009: Accept primary source reconciliation, DEC-0010: Propose PU compatibility as primary benchmark design, Reference-sequence Positive-Unlabeled Ranking, DEC-0011: Accept Blueprint Amendment 001 and authorize negative-evidence audit, DEC-0012: Accept negative-evidence discovery audit, Conditional Negative Evidence (+12 more)

### Community 19 - "qualify_torch_gpu.py"
Cohesion: 0.19
Nodes (16): LRScheduler, assert_nested_equal(), execute_fixture(), main(), make_model(), parse_args(), Any, Module (+8 more)

### Community 20 - "pre_split_feasibility.py"
Cohesion: 0.11
Nodes (34): Governance-bounded aggregate pre-split feasibility and leakage audit., build_argument_parser(), _check_sidecar(), _compare_fields(), _components(), _degree_values(), _distribution(), _edge_sets() (+26 more)

### Community 21 - "reconciliation.py"
Cohesion: 0.22
Nodes (18): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Path (+10 more)

### Community 22 - "overlap.py"
Cohesion: 0.13
Nodes (20): FamilyMap, build_contamination_index(), contamination_flags(), ContaminationIndex, _family_pair_signatures(), load_negatome_pair_index(), load_sequence_family_maps(), Any (+12 more)

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

### Community 27 - "estimand_policy_validation.py"
Cohesion: 0.18
Nodes (27): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Path (+19 more)

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
Cohesion: 0.42
Nodes (8): _extract_release(), _mapping_row(), _optional_int(), _parse_gzip_tsv(), parse_sifts(), Any, Path, Streaming parsers for frozen PDBe/SIFTS mapping snapshots.

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

### Community 37 - "reconciliation_semantics.py"
Cohesion: 0.33
Nodes (17): collect_output_metrics(), Any, DuckDBPyConnection, Path, _query_scalar(), Independent row-level checks for the primary reconciliation artifact., _record_zero_counts(), register_canonical_views() (+9 more)

### Community 38 - "M0 Negative-Evidence Discovery Audit"
Cohesion: 0.20
Nodes (10): M0 Final Evidence-Source and License Audit, Positive-Unlabeled or Latent-Observation Design, M0 Evidence-Source and License Audit, M0 Negative-Evidence Discovery Audit, Separate Manual-Negative and Structural-Non-Contact Evidence Families, M0 Systematic-Screen Metadata Audit and Benchmark Estimand Proposal, PU-R Reference-Sequence Positive-Unlabeled Ranking Estimand, Historical Project Status and Restart Checkpoint (+2 more)

### Community 40 - "Negative Evidence Audit"
Cohesion: 0.25
Nodes (9): Benchmark Estimand Policy Proposal v1, Conditional Panel Diagnostics, Reference-Sequence Positive-Unlabeled Ranking, Benchmark Estimand Policy v1, Audit-Only, No Benchmark Integration, Lambourne Human Y2H Pair-Semantics Audit, Negative Evidence Audit, Provenance-Preserving Negative Evidence (+1 more)

### Community 41 - "sequence_component_audit/pipeline.py"
Cohesion: 0.15
Nodes (28): Governance-bounded benchmark eligibility and sequence-component audit., build_argument_parser(), _build_components(), _build_eligibility(), _build_feasibility(), _build_positive_aggregates(), main(), _nearest_rank() (+20 more)

### Community 42 - "project_paths.sh"
Cohesion: 0.22
Nodes (5): IPIN_APPTAINER_CACHE, IPIN_APPTAINER_TMP, IPIN_RUNTIME_CACHE, IPIN_RUNTIME_TMP, project_paths.sh script

### Community 43 - "M0 final report: benchmark eligibility and sequence-component audit"
Cohesion: 0.15
Nodes (12): 10. Scientific interpretation and governance return, 1. Scope and frozen inputs, 2. Eligibility census, 3. Frozen sequence-similarity method, 4. Fail-closed alignment reconciliation, 5. Deterministic component census, 6. Aggregate positive-evidence mapping, 7. Pre-split component feasibility aggregates (+4 more)

### Community 45 - "Source-native Staging"
Cohesion: 0.25
Nodes (8): Data Contracts, Versioned Data Contracts, Source-native Staging, Source-native Staging Schemas, Source-native Schema v2, Evidence Warehouse Schema v1, Evidence-record-first Warehouse, Evidence Warehouse Schemas

### Community 48 - "DEC-0021: Authorize the final benchmark component-partition skeleton"
Cohesion: 0.25
Nodes (7): Binding C1/C2/C3 interpretation, Claim ceiling, Continuing prohibitions, DEC-0021: Authorize the final benchmark component-partition skeleton, Decision, Frozen pre-result design, Required evidence and validation

### Community 49 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Authorization now active, Binding interpretation, Continuing hold, Immutable parents and closed panels, iPIN-OpenPPI project status and execution checkpoint

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

### Community 80 - "stable_id"
Cohesion: 0.07
Nodes (62): stable_id(), _allocation_summary(), _base_component_order(), _build_aggregate_tables(), build_argument_parser(), _claim_rows(), _component_degree_row(), _component_summary() (+54 more)

### Community 110 - "common.py"
Cohesion: 0.13
Nodes (24): main(), AtomicDatasetDirectory, git_provenance(), load_asset_index(), project_root_from(), Path, Shared ingestion primitives with deterministic IDs and atomic Parquet output., Create a dataset in a sibling temporary directory, then rename atomically. (+16 more)

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
Nodes (24): Path, sha256_file(), build_argument_parser(), _check_sidecar(), _independent_components(), _independent_eligibility(), _independent_positive_metrics(), _IndependentDisjointSet (+16 more)

### Community 126 - "M0 final report: pre-split feasibility and leakage stress-test"
Cohesion: 0.11
Nodes (17): 1. Scope and immutable inputs, 2.1 Positive-network summaries, 2.2 Similarity challenges, 2.3 Ephemeral allocation trials, 2. Governed methods, 3.1 Source composition, 3.2 Endpoint degree and hub concentration, 3.3 ALL-source component positive-edge load (+9 more)

### Community 127 - "sequence_component_audit/support.py"
Cohesion: 0.24
Nodes (24): _verify_inputs(), Fail-closed configuration and output guards for component splitting., _verify_inputs(), Path, Fail-closed configuration and output guards for the pre-split audit., require_output_paths(), _verify_inputs(), artifact_inventory() (+16 more)

### Community 128 - "tooling.py"
Cohesion: 0.16
Nodes (20): validate_config(), _download(), _load_yaml(), prepare_mmseqs_install(), Any, Path, Checksum-pinned, fail-closed preparation of the MMseqs2 ARM64 release., Reject links, special files, absolute names, and path traversal. (+12 more)

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
Cohesion: 0.15
Nodes (21): classify_paper_outcome(), OutcomeSemantics, Any, Pure semantic rules for the Lambourne Y2H-v1 audit. These functions…, Map the five reported states to assay-bounded semantics, fail closed., Reproduce the archived raw-readout crosswalk without collapsing NA states., raw_readout_to_reported_outcome(), unordered_text_pair() (+13 more)

### Community 137 - "scan_tar_gzip_archive"
Cohesion: 0.22
Nodes (12): Path, Safe, non-extracting inventory of the archived Lambourne code and inputs., Stream the archive once; inventory headers and retain only bounded selected…, _safe_member_name(), scan_tar_gzip_archive(), scan_zip_archive(), _reconcile_imex(), Path (+4 more)

### Community 140 - "DEC-0020: Accept the pre-split feasibility and leakage stress-test"
Cohesion: 0.22
Nodes (8): Accepted evidence, Accepted findings, C3 and claim disposition, Continuing prohibitions and next authority, DEC-0020: Accept the pre-split feasibility and leakage stress-test, Decision, External-panel disposition remains binding, Final-split feasibility disposition

### Community 141 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted audit, Binding hold, Claim boundary, External panels remain closed, Feasibility disposition, iPIN-OpenPPI project status and execution checkpoint

### Community 142 - "Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push., Source Nodes

### Community 143 - "load_contract"
Cohesion: 0.12
Nodes (16): DataType, Schema, _arrow_type(), ContractError, load_contract(), Any, Load and enforce versioned Arrow table contracts., Raised when a schema contract or row violates the frozen contract. (+8 more)

## Knowledge Gaps
- **274 isolated node(s):** `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE`, `IPIN_APPTAINER_TMP`, `IPIN_RUNTIME_CACHE` (+269 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Reference-sequence Positive-Unlabeled Ranking` (3× useful, score=2.989519338)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sha256_file()` connect `sha256_file` to `component_split/pipeline.py`, `tooling.py`, `negative_evidence/pipeline.py`, `tf_isoform_audit/pipeline.py`, `negative_evidence.py`, `reconciliation/pipeline.py`, `benchmark/systematic_screen_audit.py`, `validation/systematic_screen_audit.py`, `staging.py`, `tf_isoform.py`, `lambourne.py`, `ValueError`, `load_contract`, `lambourne_audit/pipeline.py`, `component_split.py`, `pre_split_feasibility.py`, `reconciliation.py`, `overlap.py`, `estimand_policy_validation.py`, `sequence_component_audit/pipeline.py`, `stable_id`, `common.py`, `sequence_component_audit/support.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `stable_id()` connect `stable_id` to `tf_isoform_audit/pipeline.py`, `negative_evidence/pipeline.py`, `ParsingContext`, `sequence_component_audit/semantics.py`, `lambourne_audit/source.py`, `scan_tar_gzip_archive`, `sequence_component_audit/pipeline.py`, `ValueError`, `common.py`, `lambourne_audit/pipeline.py`, `overlap.py`, `sha256_file`, `sifts.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `load_yaml()` connect `acquire_manifest_assets.py` to `ValueError`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `ValueError` (e.g. with `load_yaml()` and `load_yaml()`) actually correct?**
  _`ValueError` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Checks` (e.g. with `IndependentDisjointSet` and `IndependentDisjointSet`) actually correct?**
  _`Checks` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE` to the rest of the system?**
  _274 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `component_split/pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08563134978229318 - nodes in this community are weakly interconnected._