# Graph Report - iPIN-OpenPPI  (2026-08-19)

## Corpus Check
- 417 files · ~373,431 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2708 nodes · 6655 edges · 198 communities (139 shown, 59 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 258 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8555d721`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- component_split/pipeline.py
- tf_isoform_audit/pipeline.py
- reference.py
- pair_artifacts.py
- pipeline_v4.py
- reconciliation/pipeline.py
- benchmark/systematic_screen_audit.py
- verify_raw_acquisition.py
- acquire_manifest_assets.py
- validation/systematic_screen_audit.py
- model_governance.py
- tf_isoform.py
- estimand_policy_validation.py
- ValueError
- iPIN-OpenPPI Novelty Claim Matrix
- lambourne_audit/pipeline.py
- component_split.py
- construction.py
- DEC-0012: Accept negative-evidence discovery audit
- qualify_torch_gpu.py
- pre_split_feasibility.py
- negative_evidence.py
- overlap.py
- Preacquisition Index v6
- Issue 0003: HuRI Attempted Pair Universe
- execute
- imex.py
- lambourne.py
- Source Policy 001
- run_four_gpu_qualification.sh
- run_four_gpu_qualification_long.sh
- staging.py
- run_single_gpu_qualification.sh
- run_single_gpu_qualification_v2.sh
- Final Computational Blueprint and Workflow v3
- Technical Response to Independent Review
- sequence_component_audit/semantics.py
- constants.py
- M0 Negative-Evidence Discovery Audit
- LambournePreacquisitionTests
- Negative Evidence Audit
- M0 Pair-Level PU-R Benchmark Artifacts Final v1
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
- uniprot.py
- negative_evidence/pipeline.py
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
- sequence_components.py
- M0 final report: pre-split feasibility and leakage stress-test
- sequence_component_audit/pipeline.py
- require_apptainer
- intact.py
- DEC-0026: Accept and freeze the pair-level PU-R benchmark artifacts
- DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work.
- Q: what is the exact next step?
- lambourne_audit/source.py
- ParsingContext
- test_estimand_policy_validation.py
- test_huri_workbooks_v2.py
- M0 final benchmark component split
- DEC-0020: Accept the pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push.
- project_root_from
- M0 Pair-Level PU-R Benchmark Protocol Final v1
- pair_artifacts/support.py
- resolve_inside
- DEC-0024: Accept and freeze the pair-level PU-R benchmark protocol
- DEC-0022: Accept and freeze the final benchmark component split
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0023: Authorize the pair-level PU-R benchmark protocol freeze
- sha256_file
- iPIN-OpenPPI project status and execution checkpoint
- RESUME-002: Post-PU-R-benchmark-freeze phase checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- Q: Starting from accepted DEC-0020, construct and freeze the final benchmark component split without any model involvement, using 30% local_domain_union as primary and sensitive_fl80_union only as a documented zero-valid-primary fallback.
- Q: Starting from accepted DEC-0022, freeze the pair-level PU-R benchmark protocol before any model work.
- _write_report
- DEC-0025: Authorize pair-level PU-R benchmark artifact construction
- Model governance and baseline/training protocol v1
- validate_manifest
- Protected pair-level PU-R evaluation procedure
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- Q: Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work.
- RESUME-003: Post-model-governance-protocol-freeze phase checkpoint
- qualify_model_runtime_v0_1_0.py
- common.py
- M1 model-governance and baseline/training-protocol report v1
- acquire_frozen_esm2_models_v1.py
- DEC-0029: Authorize Stage 1 executable model work
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0027: Authorize model-governance and baseline/training-protocol design
- DEC-0028: Accept and freeze the model-governance and baseline/training protocol
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- test_stage1_model_custody.py
- model/README.md
- build_model_sif_v0_1_0.sh
- download_model_image_wheels_v0_1_0.sh
- ParquetBatchWriter
- embeddings.py
- stable_id
- reconciliation.py
- training.py
- audit.py
- models.py
- validate
- preparation_audit.py
- canonical_json
- test_stage1_preparation_and_training.py
- attempt-001-partition-label-pre-fix/README.md
- M1 model runtime and custody qualification final report v1
- DEC-0030: Accept model runtime and custody for Stage 1
- iPIN-OpenPPI project status and execution checkpoint
- test_pipeline_v4_safety.py
- test_stage1_independent_pretraining_validator.py

## God Nodes (most connected - your core abstractions)
1. `sha256_file()` - 127 edges
2. `stable_id()` - 77 edges
3. `project_root_from()` - 55 edges
4. `require_apptainer()` - 53 edges
5. `ParquetBatchWriter` - 52 edges
6. `_write_report()` - 51 edges
7. `git_provenance()` - 49 edges
8. `run_audit()` - 49 edges
9. `canonical_json()` - 48 edges
10. `load_contract()` - 48 edges

## Surprising Connections (you probably didn't know these)
- `validate()` --indirect_call--> `pair_id()`  [INFERRED]
  scripts/model/validate_stage1_pretraining_independent_v1.py → src/ipin_openppi/pair_protocol/semantics.py
- `test_config_freezes_primary_fallback_objective_and_scope()` --calls--> `validate_config()`  [EXTRACTED]
  tests/unit/test_component_split_safety.py → src/ipin_openppi/component_split/support.py
- `test_stable_id_is_framed_and_deterministic()` --calls--> `stable_id()`  [EXTRACTED]
  tests/unit/test_ingestion_parsers.py → src/ipin_openppi/ingestion/common.py
- `test_workbook_headers_are_strict()` --calls--> `_headers()`  [EXTRACTED]
  tests/unit/test_huri_workbooks_v2.py → src/ipin_openppi/ingestion/huri_v2.py
- `test_schema_has_only_positive_unlabeled_and_role_free_scorer_input()` --calls--> `load_contract()`  [EXTRACTED]
  tests/unit/test_pair_artifacts_safety.py → src/ipin_openppi/ingestion/schema.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Panel Governance Return** — docs_reports_m0_m0_lambourne_2026_human_y2h_pair_semantics_audit_final_v1_document, docs_reports_m0_m0_tf_isoform_2025_y2h_semantics_and_contamination_audit_final_v1_document, governance_checkpoints_resume_001_post_tf_isoform_audit_document [INFERRED 0.85]
- **Conditional Non-detection Governance** — governance_source_surveys_public_experimental_nondetection_survey_v1_nondetection_survey, governance_risks_risk_register_risk_register, schemas_canonical_negative_evidence_audit_v1_negative_evidence_audit_schema, schemas_warehouse_evidence_warehouse_v1_evidence_warehouse_schema [INFERRED 0.85]
- **Version 3 Blueprint Provenance** — docs_blueprints_ipin_openppi_final_computational_blueprint_and_workflow_v3_final_computational_blueprint_v3, docs_blueprints_ipin_openppi_expert_project_blueprint_v2_professional_expert_project_blueprint_v2, docs_blueprints_ipin_openppi_independent_technical_review_independent_technical_review, docs_blueprints_ipin_openppi_response_to_independent_review_technical_response_to_independent_review, docs_blueprints_ipin_openppi_expert_comments_on_review_response_expert_group_comments [EXTRACTED 1.00]

## Communities (198 total, 59 thin omitted)

### Community 0 - "component_split/pipeline.py"
Cohesion: 0.08
Nodes (48): build_argument_parser(), _edge_set(), _load_graphs(), _load_parent_state(), _load_positive_pairs(), main(), Any, ArgumentParser (+40 more)

### Community 1 - "tf_isoform_audit/pipeline.py"
Cohesion: 0.05
Nodes (78): Path, Safe, non-extracting inventory of the archived Lambourne code and inputs., Stream the archive once; inventory headers and retain only bounded selected…, _safe_member_name(), scan_tar_gzip_archive(), scan_zip_archive(), Governance-bounded audit of the 2025 human TF-isoform Y2H panel., AuditReferenceMaps (+70 more)

### Community 2 - "reference.py"
Cohesion: 0.13
Nodes (19): _dataset_semantics(), parse_mi_accession(), parse_negatome_file(), Path, Lossless parsing and parent/stringent reconciliation for Negatome 2.0., Preserve the exact accession while separating an explicit numeric isoform., Parse one complete provider file without collapsing duplicate rows., split_accession() (+11 more)

### Community 3 - "pair_artifacts.py"
Cohesion: 0.08
Nodes (54): deterministic_tar(), verify_arrow_schema(), build_argument_parser(), _candidate_sql(), _candidate_union_check(), Checks, _decrypt_package(), _expected_positive_keys() (+46 more)

### Community 4 - "pipeline_v4.py"
Cohesion: 0.15
Nodes (16): Source-specific, provenance-preserving ingestion for iPIN-OpenPPI., _CardinalityCorrectingWriter, _correct_participant_cardinality(), _emit_interaction_v3(), parse_intact(), Any, Path, IntAct parser revision with exact unary/binary/n-ary semantics. Revision 2… (+8 more)

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
Nodes (37): Benchmark-design audits and policy support., build_argument_parser(), _json_field(), _load_json(), _load_yaml(), main(), _nested(), Any (+29 more)

### Community 10 - "model_governance.py"
Cohesion: 0.11
Nodes (33): Decimal, build_argument_parser(), _independent_input_verification(), independent_repetition_counts(), independent_run_budget(), independent_selection_key(), independent_window_starts(), IndependentChecks (+25 more)

### Community 11 - "tf_isoform.py"
Cohesion: 0.13
Nodes (34): build_parser(), contains_record_keys(), _evidence_checks(), _glob(), _independent_filter(), independent_y2h_outcome(), _load_json(), _load_yaml() (+26 more)

### Community 12 - "estimand_policy_validation.py"
Cohesion: 0.33
Nodes (14): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Checks (+6 more)

### Community 13 - "ValueError"
Cohesion: 0.23
Nodes (25): Book, Cell, _raw_bool(), _append_contact_row(), _append_fusion_row(), _append_generic_workbook_row(), _assert_expected_headers(), _headers() (+17 more)

### Community 14 - "iPIN-OpenPPI Novelty Claim Matrix"
Cohesion: 0.07
Nodes (28): EMBL-EBI Terms of Use snapshot, HuRI Downloads and Terms snapshot, IntAct Portal license snapshot, PDBe Public Data Access statement snapshot, RCSB PDB Usage Policy snapshot, UniProt license snapshot, License Compliance, Source and License Register v7 (+20 more)

### Community 15 - "lambourne_audit/pipeline.py"
Cohesion: 0.14
Nodes (31): Governance-bounded audit of the Lambourne et al. human Y2H-v1 panel., load_negatome_pair_index(), load_sequence_family_maps(), Path, Return accession and exact-sequence mappings for frozen UniRef100/90/50., _aggregate_panel_metrics(), _archive_inventory_rows(), _bool_value() (+23 more)

### Community 16 - "component_split.py"
Cohesion: 0.10
Nodes (38): Governance-bounded final benchmark component-partition skeleton., Any, Reject any configuration that broadens or mutates the frozen package., validate_config(), _allocate(), build_argument_parser(), _check_sidecar(), _component_id() (+30 more)

### Community 17 - "construction.py"
Cohesion: 0.06
Nodes (86): Counter, _allocation_rows(), build_argument_parser(), _candidate_base_sql(), _candidate_token(), _cell_specs(), CellSpec, construct_artifacts() (+78 more)

### Community 18 - "DEC-0012: Accept negative-evidence discovery audit"
Cohesion: 0.26
Nodes (20): DEC-0007: Accept primary raw-source acquisition, DEC-0008: Accept primary evidence staging layer, DEC-0009: Accept primary source reconciliation, DEC-0010: Propose PU compatibility as primary benchmark design, Reference-sequence Positive-Unlabeled Ranking, DEC-0011: Accept Blueprint Amendment 001 and authorize negative-evidence audit, DEC-0012: Accept negative-evidence discovery audit, Conditional Negative Evidence (+12 more)

### Community 19 - "qualify_torch_gpu.py"
Cohesion: 0.13
Nodes (26): LRScheduler, assert_nested_equal(), execute_fixture(), main(), make_model(), parse_args(), Any, Module (+18 more)

### Community 20 - "pre_split_feasibility.py"
Cohesion: 0.11
Nodes (35): Governance-bounded aggregate pre-split feasibility and leakage audit., build_argument_parser(), _check_sidecar(), _compare_fields(), _components(), _degree_values(), _distribution(), _edge_sets() (+27 more)

### Community 21 - "negative_evidence.py"
Cohesion: 0.16
Nodes (32): build_argument_parser(), _build_independent_positive_index(), _collect_metrics(), _collect_pnu(), _column_counts(), contains_record_level_report_keys(), _load_json(), _load_yaml() (+24 more)

### Community 22 - "overlap.py"
Cohesion: 0.23
Nodes (11): FamilyMap, build_contamination_index(), contamination_flags(), ContaminationIndex, _family_pair_signatures(), Any, DuckDBPyConnection, Frozen evidence overlap and bounded UniRef contamination utilities. (+3 more)

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

### Community 27 - "lambourne.py"
Cohesion: 0.15
Nodes (29): build_parser(), contains_record_level_report_keys(), _glob(), _independent_evidence_checks(), independent_orf_id(), independent_raw_outcome(), _independent_source_metrics(), _load_json() (+21 more)

### Community 28 - "Source Policy 001"
Cohesion: 0.19
Nodes (13): Source Policy 001, Source Policy 002, Source Policy 003, Lambourne et al. Molecular Cell 2025, Source Policy 004, Systematic Screen Metadata Audit v1, TF-Isoform Y2H Semantics and Contamination Audit v1, Active Pre-acquisition Manifest Set v3 (+5 more)

### Community 29 - "run_four_gpu_qualification.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 30 - "run_four_gpu_qualification_long.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 31 - "staging.py"
Cohesion: 0.14
Nodes (25): build_argument_parser(), Checks, DatasetSummary, _iter_summaries(), _load_json(), _load_yaml(), main(), _nested() (+17 more)

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

### Community 37 - "constants.py"
Cohesion: 0.20
Nodes (10): CompletedProcess, embedding_gpu_hours(), governed_storage_bytes(), invocation_command(), invoke(), logged_training_gpu_seconds(), main(), Path (+2 more)

### Community 38 - "M0 Negative-Evidence Discovery Audit"
Cohesion: 0.20
Nodes (10): M0 Final Evidence-Source and License Audit, Positive-Unlabeled or Latent-Observation Design, M0 Evidence-Source and License Audit, M0 Negative-Evidence Discovery Audit, Separate Manual-Negative and Structural-Non-Contact Evidence Families, M0 Systematic-Screen Metadata Audit and Benchmark Estimand Proposal, PU-R Reference-Sequence Positive-Unlabeled Ranking Estimand, Historical Project Status and Restart Checkpoint (+2 more)

### Community 40 - "Negative Evidence Audit"
Cohesion: 0.25
Nodes (9): Benchmark Estimand Policy Proposal v1, Conditional Panel Diagnostics, Reference-Sequence Positive-Unlabeled Ranking, Benchmark Estimand Policy v1, Audit-Only, No Benchmark Integration, Lambourne Human Y2H Pair-Semantics Audit, Negative Evidence Audit, Provenance-Preserving Negative Evidence (+1 more)

### Community 41 - "M0 Pair-Level PU-R Benchmark Artifacts Final v1"
Cohesion: 0.17
Nodes (11): Accepted evidence, Claim ceiling and continuing hold, Disposition, Frozen package layers, Immutable parent and pair semantics, M0 Pair-Level PU-R Benchmark Artifacts Final v1, Prespecified cross-cell reuse, Primary positive and sampling results (+3 more)

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

### Community 80 - "pre_split_audit/pipeline.py"
Cohesion: 0.06
Nodes (63): _allocation_summary(), _base_component_order(), _build_aggregate_tables(), build_argument_parser(), _claim_rows(), _component_degree_row(), _component_summary(), _degree_row() (+55 more)

### Community 109 - "uniprot.py"
Cohesion: 0.27
Nodes (15): strip_version(), _clean_annotation(), iter_fasta(), parse_dat_metadata(), _parse_fasta_header(), parse_uniprot(), Any, Path (+7 more)

### Community 110 - "negative_evidence/pipeline.py"
Cohesion: 0.13
Nodes (31): Conditional negative-evidence discovery and reconciliation., NegatomeRow, Any, Prove exact multiset subset membership and link every physical source row., Return the provider row key after boundary-whitespace normalization., reconcile_parent_and_stringent_rows(), source_row_to_record(), stringent_links() (+23 more)

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

### Community 125 - "sequence_components.py"
Cohesion: 0.17
Nodes (23): Governance-bounded benchmark eligibility and sequence-component audit., validate_config(), build_argument_parser(), _check_sidecar(), _independent_components(), _independent_eligibility(), _independent_positive_metrics(), _IndependentDisjointSet (+15 more)

### Community 126 - "M0 final report: pre-split feasibility and leakage stress-test"
Cohesion: 0.11
Nodes (17): 1. Scope and immutable inputs, 2.1 Positive-network summaries, 2.2 Similarity challenges, 2.3 Ephemeral allocation trials, 2. Governed methods, 3.1 Source composition, 3.2 Endpoint degree and hub concentration, 3.3 ALL-source component positive-edge load (+9 more)

### Community 127 - "sequence_component_audit/pipeline.py"
Cohesion: 0.17
Nodes (28): build_argument_parser(), _build_components(), _build_eligibility(), _build_feasibility(), _build_positive_aggregates(), main(), _nearest_rank(), _normalize_alignments() (+20 more)

### Community 128 - "require_apptainer"
Cohesion: 0.15
Nodes (21): main(), require_apptainer(), _download(), _load_yaml(), prepare_mmseqs_install(), Any, Path, Checksum-pinned, fail-closed preparation of the MMseqs2 ARM64 release. (+13 more)

### Community 129 - "intact.py"
Cohesion: 0.29
Nodes (30): Element, _assay_family(), _attributes(), _child(), _children(), _confidence_values(), _cv_term(), _descendant_text() (+22 more)

### Community 130 - "DEC-0026: Accept and freeze the pair-level PU-R benchmark artifacts"
Cohesion: 0.20
Nodes (9): Accepted artifacts, Accepted evidence, Accepted independent checks, Accepted protected-test boundary, Claim disposition, Continuing hold, DEC-0026: Accept and freeze the pair-level PU-R benchmark artifacts, Decision (+1 more)

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
Cohesion: 0.10
Nodes (31): benchmark_claim_identifiability(), classify_paper_outcome(), OutcomeSemantics, Any, Pure semantic rules for the Lambourne Y2H-v1 audit. These functions…, Independently count the final Zhang subset and preserve all five outcomes., Frozen claim boundary used by both the pipeline and independent validator., Map the five reported states to assay-bounded semantics, fail closed. (+23 more)

### Community 136 - "ParsingContext"
Cohesion: 0.16
Nodes (24): ParsingContext, Any, _ensembl_by_kind(), _feature_parts(), _identifiers(), _identifiers_for_database(), _interaction_semantics(), _pair_token() (+16 more)

### Community 137 - "test_estimand_policy_validation.py"
Cohesion: 0.36
Nodes (14): _failures(), _policy(), test_accepted_status_is_rejected_before_expert_approval(), test_calibration_metric_cannot_become_primary(), test_construct_threshold_cannot_be_weakened(), test_effective_policy_is_rejected_before_expert_approval(), test_frozen_proposal_semantics_pass(), test_label_authority_is_rejected() (+6 more)

### Community 138 - "test_huri_workbooks_v2.py"
Cohesion: 0.33
Nodes (7): SimpleNamespace, _asset(), CaptureWriter, _config(), test_contact_annotation_is_typed_but_never_label_authorized(), test_fusion_interference_preserves_orientation_and_missingness(), test_workbook_headers_are_strict()

### Community 139 - "M0 final benchmark component split"
Cohesion: 0.14
Nodes (13): 10. Scope and continuing holds, 11. Immutable evidence, 12. Final disposition, 1. Executive disposition, 2. Frozen inputs and execution, 3. Preregistered allocation and selection, 4. Search result and fallback disposition, 5. Frozen endpoint and component allocation (+5 more)

### Community 140 - "DEC-0020: Accept the pre-split feasibility and leakage stress-test"
Cohesion: 0.22
Nodes (8): Accepted evidence, Accepted findings, C3 and claim disposition, Continuing prohibitions and next authority, DEC-0020: Accept the pre-split feasibility and leakage stress-test, Decision, External-panel disposition remains binding, Final-split feasibility disposition

### Community 141 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted audit, Binding hold, Claim boundary, External panels remain closed, Feasibility disposition, iPIN-OpenPPI project status and execution checkpoint

### Community 142 - "Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push., Source Nodes

### Community 143 - "project_root_from"
Cohesion: 0.17
Nodes (24): git_provenance(), project_root_from(), Static governance for the first bounded model protocol., _all_false(), _all_prohibited(), audit_protocol(), build_argument_parser(), _check() (+16 more)

### Community 144 - "M0 Pair-Level PU-R Benchmark Protocol Final v1"
Cohesion: 0.11
Nodes (18): Candidate algebra and deterministic unlabeled sampling, Claim boundary and continuing hold, Degree, hubs, and frozen future baselines, Disposition, Evaluation cells, Evidence visibility, Exact primary C1/C2/C3 assignment, Immutable evidence (+10 more)

### Community 145 - "pair_artifacts/support.py"
Cohesion: 0.23
Nodes (16): certificate_fingerprint(), dataset_summary(), file_record(), manifest_payload_hash(), private_key_paths(), Any, Path, Fail-closed helpers for sealed pair-level PU-R benchmark artifacts. (+8 more)

### Community 146 - "resolve_inside"
Cohesion: 0.23
Nodes (24): Fail-closed configuration and output guards for component splitting., _verify_inputs(), Path, Fail-closed guards for the pair-level PU-R protocol freeze., resolve_and_verify_documents(), Fail-closed configuration and output guards for the pre-split audit., artifact_inventory(), find_table_summary() (+16 more)

### Community 147 - "DEC-0024: Accept and freeze the pair-level PU-R benchmark protocol"
Cohesion: 0.17
Nodes (11): Accepted evaluation and uncertainty, Accepted evidence, Accepted feasibility, Accepted information and visibility boundary, Accepted pair rules, Accepted unlabeled-sampling protocol, Auxiliary holdout disposition, Claim disposition (+3 more)

### Community 148 - "DEC-0022: Accept and freeze the final benchmark component split"
Cohesion: 0.22
Nodes (8): Accepted allocation, Accepted evidence, Accepted positive-evidence opportunity disposition, C3 and claim disposition, Continuing prohibitions and next authority, DEC-0022: Accept and freeze the final benchmark component split, Decision, Scope confirmation

### Community 149 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.22
Nodes (8): Accepted frozen package, Binding hold, Binding semantics and claims, Immutable parents and panels, Independent validation disposition, iPIN-OpenPPI project status and execution checkpoint, Protected custody, Qualification note

### Community 150 - "DEC-0023: Authorize the pair-level PU-R benchmark protocol freeze"
Cohesion: 0.25
Nodes (7): Binding C1/C2/C3 semantics, Continuing prohibitions, DEC-0023: Authorize the pair-level PU-R benchmark protocol freeze, Decision, Evidence and holdout boundary, Required frozen protocol, Required validation and return

### Community 151 - "sha256_file"
Cohesion: 0.17
Nodes (34): sha256_file(), build_argument_parser(), _decrypt_checked(), evaluate_protected(), main(), open_protected_candidates(), _prediction_rows(), _project_scorer_inputs() (+26 more)

### Community 152 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Binding C3 boundary, Binding hold, Frozen benchmark component split, iPIN-OpenPPI project status and execution checkpoint, Opportunity evidence, Parent evidence and external panels

### Community 153 - "RESUME-002: Post-PU-R-benchmark-freeze phase checkpoint"
Cohesion: 0.07
Nodes (29): 10. Frozen parent benchmark records, 11. Completed workstreams that must not be reopened, 12. Protected-test secrecy and custody rules, 13. Claim boundaries and prohibited interpretations, 14. Remaining unauthorized work, 15. Recommended next phase, subject to a new numbered authorization, 16.1 Read authority and query the graph, 16.2 Prove repository identity and synchronization (+21 more)

### Community 154 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): Authorization now active, Closed panels and continuing hold, Immutable parent and scientific boundary, iPIN-OpenPPI project status and execution checkpoint

### Community 155 - "Q: Starting from accepted DEC-0020, construct and freeze the final benchmark component split without any model involvement, using 30% local_domain_union as primary and sensitive_fl80_union only as a documented zero-valid-primary fallback."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Starting from accepted DEC-0020, construct and freeze the final benchmark component split without any model involvement, using 30% local_domain_union as primary and sensitive_fl80_union only as a documented zero-valid-primary fallback., Source Nodes

### Community 156 - "Q: Starting from accepted DEC-0022, freeze the pair-level PU-R benchmark protocol before any model work."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Starting from accepted DEC-0022, freeze the pair-level PU-R benchmark protocol before any model work., Source Nodes

### Community 157 - "_write_report"
Cohesion: 0.60
Nodes (4): _write_report(), Path, test_validation_report_and_sidecar_are_immutable(), test_validation_report_refuses_preexisting_sidecar()

### Community 158 - "DEC-0025: Authorize pair-level PU-R benchmark artifact construction"
Cohesion: 0.22
Nodes (8): Authorized artifact boundaries, Continuing prohibitions, DEC-0025: Authorize pair-level PU-R benchmark artifact construction, Decision, Evaluation procedure boundary, Independent validation, Protected-test non-inference rule, Sampling and overlap interpretation

### Community 159 - "Model governance and baseline/training protocol v1"
Cohesion: 0.11
Nodes (18): 10. Metrics and reporting hierarchy, 11. Degree/hub analyses and C1 novel-U sensitivity, 12. Complexity gate and model-level kill rules, 13. Exit condition, 1. Purpose and authority boundary, 2. Immutable scientific and custody boundary, 3.1 Future local custody, 3. Frozen PLM candidates and provenance (+10 more)

### Community 160 - "validate_manifest"
Cohesion: 0.56
Nodes (8): add_check(), load_yaml(), main(), nested_get(), Any, Path, sha256_file(), validate_manifest()

### Community 161 - "Protected pair-level PU-R evaluation procedure"
Cohesion: 0.25
Nodes (7): Binding visibility boundary, Development release, Metric boundary, Package boundaries, Prediction freeze and truth access, Protected pair-level PU-R evaluation procedure, Protected scoring

### Community 162 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.25
Nodes (7): Accepted pair-level protocol, Active bounded work package, Binding authorization and hold, Binding semantics, Feasibility return, Immutable parent and panels, iPIN-OpenPPI project status and execution checkpoint

### Community 163 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted pair-level protocol, Binding hold, Binding semantics, Feasibility return, Immutable parent and panels, iPIN-OpenPPI project status and execution checkpoint

### Community 164 - "Q: Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work."
Cohesion: 0.50
Nodes (3): Answer, Outcome, Q: Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work.

### Community 165 - "RESUME-003: Post-model-governance-protocol-freeze phase checkpoint"
Cohesion: 0.12
Nodes (15): 10. Metrics, stratification, complexity, and kill rules, 11. Validation and execution record, 12. Next-phase gate, 13. Exact fresh-thread preflight, 14. Fail-closed escalation, 1. Exact repository anchor and handoff invariant, 2. Current authority, 3. Immutable parent benchmark (+7 more)

### Community 166 - "qualify_model_runtime_v0_1_0.py"
Cohesion: 0.23
Nodes (14): dtype, EsmModel, EsmTokenizer, atomic_json(), checkpoint_restart_fixture(), configure_determinism(), main(), parse_args() (+6 more)

### Community 167 - "common.py"
Cohesion: 0.09
Nodes (38): load_asset_index(), Shared ingestion primitives with deterministic IDs and atomic Parquet output., RawAsset, utc_now(), verify_asset(), Typed context shared by source parsers., build_argument_parser(), main() (+30 more)

### Community 168 - "M1 model-governance and baseline/training-protocol report v1"
Cohesion: 0.18
Nodes (10): 1. Resume and immutable-parent check, 2. PLM freeze and exposure boundary, 3. Frozen embedding rule, 4. Mandatory diagnostic ladder, 5. Primary objective and finite execution design, 6. Release, selection, metrics, and diagnostics, 7. Complexity and kill gates, 8. Validation and authority disposition (+2 more)

### Community 169 - "acquire_frozen_esm2_models_v1.py"
Cohesion: 0.36
Nodes (11): assert_link_free(), assert_within_project(), atomic_json(), download(), git_commit(), main(), parse_args(), Any (+3 more)

### Community 170 - "DEC-0029: Authorize Stage 1 executable model work"
Cohesion: 0.22
Nodes (8): Authorized work, Continuing prohibitions, DEC-0029: Authorize Stage 1 executable model work, Decision, Evidence and commit discipline, Frozen scientific and data boundary, Return and next decision boundary, Successful authorization preflight

### Community 171 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Authority and preflight, Authorized stage, Immutable scientific boundary, iPIN-OpenPPI project status and execution checkpoint, Required execution return

### Community 172 - "DEC-0027: Authorize model-governance and baseline/training-protocol design"
Cohesion: 0.29
Nodes (6): Continuing prohibitions, DEC-0027: Authorize model-governance and baseline/training-protocol design, Decision, Immutable parent boundary, Required frozen design, Required validation and return

### Community 173 - "DEC-0028: Accept and freeze the model-governance and baseline/training protocol"
Cohesion: 0.29
Nodes (6): Accepted design, Accepted evidence, Continuing hold and next decision boundary, DEC-0028: Accept and freeze the model-governance and baseline/training protocol, Decision, Independent validation disposition

### Community 174 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.29
Nodes (6): Accepted model protocol, Binding hold, Execution record, Frozen first-stage design, Immutable benchmark boundary, iPIN-OpenPPI project status and execution checkpoint

### Community 175 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Authorization now active, Continuing hold, Immutable scientific boundary, iPIN-OpenPPI project status and execution checkpoint, Preflight disposition

### Community 176 - "test_stage1_model_custody.py"
Cohesion: 0.40
Nodes (3): Path, test_custody_path_must_remain_within_project(), test_custody_rejects_symlink()

### Community 179 - "build_model_sif_v0_1_0.sh"
Cohesion: 0.40
Nodes (4): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, EXPECTED_WHEELS, build_model_sif_v0_1_0.sh script

### Community 181 - "ParquetBatchWriter"
Cohesion: 0.36
Nodes (3): ParquetBatchWriter, Any, Write validated, fixed-schema Parquet parts and retain exact statistics.

### Community 182 - "embeddings.py"
Cohesion: 0.13
Nodes (31): main(), _all_finite(), _artifact(), audit_embeddings(), _check(), _max_standardization_difference(), Any, ndarray (+23 more)

### Community 184 - "stable_id"
Cohesion: 0.12
Nodes (28): stable_id(), _build_panel_rows(), _family_ids_for_candidates(), _participant_mapping_row(), conflict_overlays(), effective_tier(), permitted_role(), Reliability tiers and conflict overlays for conditional negative evidence. (+20 more)

### Community 185 - "reconciliation.py"
Cohesion: 0.11
Nodes (44): DataType, Schema, _arrow_type(), ContractError, Any, Raised when a schema contract or row violates the frozen contract., SchemaContract, build_argument_parser() (+36 more)

### Community 187 - "training.py"
Cohesion: 0.13
Nodes (29): main(), deterministic_order(), learning_rate_multiplier(), order_key(), positive_positions_for_batch(), positive_repetition_counts(), ndarray, Tensor (+21 more)

### Community 188 - "audit.py"
Cohesion: 0.17
Nodes (23): csr_matrix, audit_stage1_implementation(), _check(), Any, Path, Production audit of the frozen Stage 1 implementation before execution., common_neighbors_score(), component_mass_product_score() (+15 more)

### Community 189 - "models.py"
Cohesion: 0.15
Nodes (17): build_training_graph(), build_model(), commutative_features(), exact_cosine(), initialize_exact(), LinearPairHead, NonlinearPairHead, parameter_count() (+9 more)

### Community 190 - "validate"
Cohesion: 0.27
Nodes (16): _all_finite(), _bytes_sha256(), _cache_key(), _check(), _layout(), _order_key(), _parameter_counts(), Any (+8 more)

### Community 191 - "preparation_audit.py"
Cohesion: 0.18
Nodes (27): ordered_records(), ordered_pair_id_digest(), _artifact(), audit_training_preparation(), _check(), expected_run_ids(), Any, Path (+19 more)

### Community 192 - "canonical_json"
Cohesion: 0.22
Nodes (16): canonical_json(), parse_intact(), _parse_mutations(), _parse_obo(), Path, iter_reconstructed_mutation_rows(), parse_intact(), _parse_mutations_v2() (+8 more)

### Community 193 - "test_stage1_preparation_and_training.py"
Cohesion: 0.28
Nodes (7): MonkeyPatch, Path, test_atomic_checkpoint_roundtrip(), test_matrix_algebra_is_exactly_thirty_runs(), test_orchestrator_launches_exact_offline_deterministic_environment(), test_orchestrator_records_non_overwriting_attempt_log(), test_step_learning_rate_uses_one_based_exact_schedule()

### Community 196 - "M1 model runtime and custody qualification final report v1"
Cohesion: 0.29
Nodes (6): Disposition, Frozen evidence, Independent validation, M1 model runtime and custody qualification final report v1, Production qualification, Result

### Community 197 - "DEC-0030: Accept model runtime and custody for Stage 1"
Cohesion: 0.33
Nodes (5): Accepted construction and evidence, Continuing hold, DEC-0030: Accept model runtime and custody for Stage 1, Decision, Scientific-use boundary

### Community 198 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): Accepted runtime and custody, Active execution boundary, Continuing hold and return, iPIN-OpenPPI project status and execution checkpoint

## Knowledge Gaps
- **502 isolated node(s):** `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE`, `IPIN_APPTAINER_TMP`, `IPIN_RUNTIME_CACHE` (+497 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **59 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Reference-sequence Positive-Unlabeled Ranking` (4× useful, score=3.970408594)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sha256_file()` connect `sha256_file` to `component_split/pipeline.py`, `require_apptainer`, `reference.py`, `pair_artifacts.py`, `tf_isoform_audit/pipeline.py`, `reconciliation/pipeline.py`, `benchmark/systematic_screen_audit.py`, `validation/systematic_screen_audit.py`, `model_governance.py`, `tf_isoform.py`, `estimand_policy_validation.py`, `lambourne_audit/pipeline.py`, `project_root_from`, `construction.py`, `pair_artifacts/support.py`, `resolve_inside`, `component_split.py`, `negative_evidence.py`, `pre_split_feasibility.py`, `lambourne.py`, `_write_report`, `staging.py`, `common.py`, `ParquetBatchWriter`, `reconciliation.py`, `pre_split_audit/pipeline.py`, `negative_evidence/pipeline.py`, `sequence_components.py`, `sequence_component_audit/pipeline.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `audit_training_preparation()` connect `preparation_audit.py` to `construction.py`, `training.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `project_root_from()` connect `project_root_from` to `require_apptainer`, `component_split/pipeline.py`, `tf_isoform_audit/pipeline.py`, `pair_artifacts.py`, `reconciliation/pipeline.py`, `benchmark/systematic_screen_audit.py`, `validation/systematic_screen_audit.py`, `model_governance.py`, `tf_isoform.py`, `estimand_policy_validation.py`, `lambourne_audit/pipeline.py`, `component_split.py`, `construction.py`, `pre_split_feasibility.py`, `negative_evidence.py`, `sha256_file`, `lambourne.py`, `staging.py`, `common.py`, `reconciliation.py`, `pre_split_audit/pipeline.py`, `negative_evidence/pipeline.py`, `sequence_components.py`, `sequence_component_audit/pipeline.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 97 inferred relationships involving `ValueError` (e.g. with `load_yaml()` and `load_yaml()`) actually correct?**
  _`ValueError` has 97 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `Counter` (e.g. with `main()` and `validate()`) actually correct?**
  _`Counter` has 54 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ipin-openppi`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE` to the rest of the system?**
  _502 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `component_split/pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07539450613676213 - nodes in this community are weakly interconnected._