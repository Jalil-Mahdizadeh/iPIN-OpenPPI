# Graph Report - iPIN-OpenPPI  (2026-09-11)

## Corpus Check
- 740 files · ~647,236 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4194 nodes · 9929 edges · 332 communities (241 shown, 91 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 371 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c0e5ba49`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- validate_development_completed_independent_v1.py
- tf_isoform_audit/pipeline.py
- sha256_file
- pair_artifacts/support.py
- test_composition_order.py
- reconciliation/pipeline.py
- benchmark/systematic_screen_audit.py
- verify_raw_acquisition.py
- acquire_manifest_assets.py
- validation/systematic_screen_audit.py
- model_governance.py
- tf_isoform.py
- partner_specificity/pipeline.py
- huri_v2.py
- iPIN-OpenPPI Novelty Claim Matrix
- lambourne_audit/semantics.py
- project_root_from
- scoring.py
- DEC-0012: Accept negative-evidence discovery audit
- qualify_torch_gpu.py
- pre_split_feasibility.py
- stage1/models.py
- validate
- Preacquisition Index v6
- Issue 0003: HuRI Attempted Pair Universe
- execute
- component_split/semantics.py
- test_external_bioplex.py
- Source Policy 001
- run_four_gpu_qualification.sh
- run_four_gpu_qualification_long.sh
- negative_evidence.py
- run_single_gpu_qualification.sh
- run_single_gpu_qualification_v2.sh
- Final Computational Blueprint and Workflow v3
- Technical Response to Independent Review
- sequence_component_audit/semantics.py
- run_stage1_training_matrix_v1.py
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
- evaluation.py
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
- git_provenance
- M0 final report: pre-split feasibility and leakage stress-test
- ParquetBatchWriter
- pair_protocol/semantics.py
- intact.py
- DEC-0026: Accept and freeze the pair-level PU-R benchmark artifacts
- DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: explore this repo deeply and fully understand it first. You can use the graphify skill if it helps a better navigation. Resume from governance/checkpoints/RESUME-001-post-tf-isoform-audit.md. First, perform a minimal governance cleanup only: accept the TF-isoform audit and DEC-0016 disposition as technically complete; preserve the panel as external-only and unsuitable for training negatives, universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family benchmarking; do not reopen, recompute, or extend either audit. Then begin the previously authorized sequence-component audit exactly from the checkpoint scope. Preserve the primary PU-R design, remain fail-closed, run relevant validation and tests, and commit and push all completed work.
- Q: what is the exact next step?
- completed_audit.py
- huri.py
- lambourne_audit/pipeline.py
- sequence_component_audit/pipeline.py
- M0 final benchmark component split
- DEC-0020: Accept the pre-split feasibility and leakage stress-test
- iPIN-OpenPPI project status and execution checkpoint
- Q: below is the group comment. Deeply review and act accordingly only if the comments are valid: Starting from the current `main` state and accepted `DEC-0018`, conduct a bounded **pre-split feasibility and leakage stress-test** for the future C1/C2/C3 benchmark design. Required work: * preserve the frozen 17,000 sequence-endpoint universe and existing 40/30/20% MMseqs2 components; * quantify positive-edge distribution across components, endpoint/component degree, hub concentration, and source composition; * determine whether component-disjoint train/dev/test assignments can retain sufficient positive evidence for meaningful C1/C2/C3 evaluation; * evaluate feasibility at 40%, 30%, and 20% identity without yet freezing a split; * stress-test residual cross-component homology, especially substantial local/domain-level similarity that may escape the current ≥80% bidirectional full-length coverage rule; * perform an independent completeness/sensitivity check of the primary 30% MMseqs2 similarity graph to identify potentially missed qualifying edges; * quantify how stricter leakage controls change component structure and retained positive evidence; * explicitly assess whether any proposed C3 regime genuinely supports unseen-protein/family claims. Remain fail-closed. Do not: * create or sample negatives/pseudo-negatives; * materialize the full candidate-pair universe; * construct or freeze train/dev/test splits; * authorize C1/C2/C3 labels; * integrate external diagnostic panels; * perform structural-label work; * train, tune, calibrate, or evaluate models; * change the primary PU-R design. Return a clear governance disposition: whether final split construction is scientifically feasible, under which leakage definition(s), and what claim boundaries must apply. Independently validate all consequential counts, update the report/decision/gate/status artifacts, run targeted tests, then commit and push.
- main
- M0 Pair-Level PU-R Benchmark Protocol Final v1
- ValueError
- construction.py
- DEC-0024: Accept and freeze the pair-level PU-R benchmark protocol
- DEC-0022: Accept and freeze the final benchmark component split
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0023: Authorize the pair-level PU-R benchmark protocol freeze
- overlap.py
- iPIN-OpenPPI project status and execution checkpoint
- RESUME-002: Post-PU-R-benchmark-freeze phase checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- Q: Starting from accepted DEC-0020, construct and freeze the final benchmark component split without any model involvement, using 30% local_domain_union as primary and sensitive_fl80_union only as a documented zero-valid-primary fallback.
- Q: Starting from accepted DEC-0022, freeze the pair-level PU-R benchmark protocol before any model work.
- validate_development_prerelease_independent_v1.py
- DEC-0025: Authorize pair-level PU-R benchmark artifact construction
- Model governance and baseline/training protocol v1
- RESUME-005: Post-development-evaluation stop checkpoint
- Protected pair-level PU-R evaluation procedure
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- Q: Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work.
- RESUME-003: Post-model-governance-protocol-freeze phase checkpoint
- qualify_model_runtime_v0_1_0.py
- load_contract
- M1 model-governance and baseline/training-protocol report v1
- acquire_frozen_esm2_models_v1.py
- DEC-0029: Authorize Stage 1 executable model work
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0027: Authorize model-governance and baseline/training-protocol design
- DEC-0028: Accept and freeze the model-governance and baseline/training protocol
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- test_stage1_model_custody.py
- M1 Stage 1 public-training execution final report v1
- Model-governance utilities
- build_model_sif_v0_1_0.sh
- download_model_image_wheels_v0_1_0.sh
- release.py
- test_partner_specificity.py
- protected_final_core_v1.py
- stable_id
- DEC-0031: Accept Stage 1 public training and development-release readiness
- publish_model_optimization_followup_v1.py
- stage1/audit.py
- local_diagnostic/pipeline.py
- scan_tar_gzip_archive
- RESUME-006: Post-local-representation-diagnostic stop checkpoint
- DEC-0033: Accept development pre-release qualification and activate release
- sha256_file
- attempt-001-partition-label-pre-fix/README.md
- ParsingContext
- M1 model runtime and custody qualification final report v1
- DEC-0030: Accept model runtime and custody for Stage 1
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- component_split.py
- estimand_policy_validation.py
- run.py
- DEC-0032: Authorize development release and frozen-scorer evaluation
- test_homology_source.py
- iPIN-OpenPPI project status and execution checkpoint
- reconciliation.py
- RESUME-004: Post-Stage 1 public-training-freeze phase checkpoint
- DEC-0042-authorize-fp32-reconstruction-tolerance-correction.md
- Locked external BioPlex co-association challenge v1
- DEC-0035: Accept nullability-correction requalification and resume development scoring
- iPIN-OpenPPI project status and execution checkpoint
- ISSUE-0012-local-segment-fp32-reconstruction-tolerance.md
- stage1/support.py
- external_bioplex/pipeline.py
- Public-training local-representation diagnostic protocol v1
- iPIN-OpenPPI project status and execution checkpoint
- M1 development release and evaluation final report v1
- DEC-0039: Accept development evaluation and stop complex-model claim
- lambourne.py
- DEC-0034: Authorize nullability-only development loader correction
- ISSUE-0009: Filtered development row nullability blocks strict concatenation
- iPIN-OpenPPI project status and execution checkpoint
- PROJECT_STATUS_v41.md
- DEC-0037: Accept source-degree guard requalification and resume scoring
- Research reassessment and development embedding identity incident
- validate_development_completed_independent_v2.py
- DEC-0038: Authorize completed-audit scoring-census correction
- iPIN-OpenPPI project status and execution checkpoint
- DEC-0036: Authorize source-cell degree-semantics guard correction
- ISSUE-0010: Source-cell design degree metadata was compared to the pooled feature graph
- iPIN-OpenPPI project status and execution checkpoint
- iPIN-OpenPPI project status and execution checkpoint
- ISSUE-0011: Completed auditor used the release-table census as the score-row census
- iPIN-OpenPPI project status and execution checkpoint
- validate
- M1 public-training local-representation diagnostic: final report
- composition_order/data.py
- DEC-0040: Authorize public-training local-representation diagnostic
- DEC-0041: Clarify local cosine reductions before execution
- DEC-0045: Authorize development embedding identity correction and reevaluation
- PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1_revision_2.md
- PROJECT_STATUS_v39.md
- PROJECT_STATUS_v40.md
- ingestion/pipeline.py
- Q: Act on the proposed next step and determine quickly whether a local, residue/domain-aware representation shows incremental public-training signal.
- Q: so this project is a real dead end?
- DEC-0043-authorize-fp64-local-cosine-reductions.md
- ISSUE-0013-local-cosine-gpu-reduction-precision.md
- PROJECT_STATUS_v42.md
- sifts.py
- Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end.
- summarize_direct_binary_feasibility_v1.py
- protocol.py
- DEC-0044-accept-local-representation-diagnostic-and-stop-branch.md
- ISSUE-0014-development-embedding-identity-mismatch.md
- PROJECT_STATUS_v43.md
- PROJECT_STATUS_v44.md
- pair_protocol.py
- FinalTestFixtures
- training.py
- Homology/interolog and source-aware challenge: findings
- Within-anchor partner-specificity diagnostic: results
- close_protected_final_test_v1.py
- validate_manifest
- Within-anchor partner-specificity diagnostic v1
- validate_degree_metadata
- Q: act according to your recommendations.
- audit_within_anchor_supporting_metrics_v1.py
- PROJECT_STATUS_v46.md
- Q: continue with the best next step, generate a concise report, update relevant docs, commit and push.
- Homology/interolog and source-aware internal challenge v1
- validate
- Q: ok! now challenge the signal with stronger homology/interolog controls and source-aware validation, as you suggested.
- Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end.
- Composition, sequence order and matched-partner diagnostic v1
- Q: what is the best next step? maybe a prospectively designed within-anchor partner-specificity test? what do you think?
- DEC-0048-authorize-locked-external-bioplex-challenge.md
- DEC-0046: Authorize a within-anchor partner-specificity diagnostic
- PROJECT_STATUS_v45.md
- composition_order/validation.py
- BIOPLEX_PUBLISHED_RELEASE_USE_v1.md
- mapping.py
- Fixed-ensemble follow-up on the existing test v1
- DEC-0047-authorize-homology-and-source-challenge.md
- ISSUE-0015-residual-homology-in-frozen-component-folds.md
- PROJECT_STATUS_v47.md
- external_bioplex/data.py
- FollowupPublicationFixtures
- close_homology_source_challenge_v1.py
- One-time protected final test v1
- DEC-0049-authorize-composition-order-diagnostic.md
- PROJECT_STATUS_v49.md
- Q: Act according to your recommendation: one bounded independent direct-binary feasibility check after assessing whether the project is a dead end.
- Q: i did not fullt inderstand. what is the status of the project now? explain it cincisely in a simple language.
- Q: but there is still a frozen test set which has never been seen or studied. am i right?
- test_direct_binary_feasibility.py
- main
- build_positive_pair_index
- protected_final_guard_v1.py
- Bounded direct-binary feasibility assessment
- Q: go ahead with the best next step. Think and act as a serior researcher in AI and bioinformatics. Then, commit and push.
- Q: is it a dead end project?
- REPRODUCIBILITY.md
- pair_artifacts.py
- run_protected_final_test_v1.sh
- validate_direct_binary_feasibility_v1.py
- Counter
- PublicationFixtures
- Q: alright! 1- Heavily de-emphasize the BioPlex experiment. 2- Prospectively amend the repo’s one-shot protocol while preserving the original evaluation and its records. 3- Initiate model-architecture/parameter optimization experiments and try diffent models, architecture, parameters, etc., select the best performing development-based model, and re-test it on the test panel if it outperforms the baselone on the development panel. No new test set needed. First, ask questions if more clarifications needed.
- DEC-0050-bounded-direct-binary-feasibility-and-model-stop.md
- PROJECT_STATUS_v50.md
- AST
- validate_development_prerelease_independent_v3.py
- Q: commit and push if all relevant docs and files are up to date.
- Development-only model optimization v1
- ContractError
- validate
- test_development_completed_independent_validator_v2.py
- Q: conduct the model's performance on the final test.
- Q: I would ignore the BioPlex experiment because it is not a valid binary interaction panel. Moreover, the unseen test's results is extremely interesting and align very well with the development results. A surprisingly simple frozen-PLM sequence model generalizes strongly to interaction-naïve proteins in a rigorously protected PU benchmark, while network shortcuts dominate when endpoints have prior interaction exposure and genuine partner-specific/direct-binding generalization remains unresolved.
- Q: since a simple PLM pair model was successful, I would like to suggest a model-architecture optimization on the train/development panel. If it showed improvment, we re-test on the test panel. What do you think?
- Q: I do not agree with you. If you optimize architecture/hyperparameters exclusively on the development panel, freeze the final model, and then evaluate that final model on the test set, that is a standard and defensible train/dev/test workflow. We only apply the optimized model if it shows improvement on the development panel over the base model. We do not need to develop another unseen test set.
- test_development_completed_independent_validator.py
- test_development_independent_prerelease_validator.py
- test_development_independent_prerelease_validator_v3.py
- test_stage1_independent_completed_training_validator.py
- Q: The actual model being proposed is a three-seed ensemble. Its prediction is the averaged ensemble score—not any individual seed.
- run_model_optimization_v1.sh
- normalize_followup_guard_log_v1.py
- GuardLogFixtures
- run_model_optimization_followup_v1.sh

## God Nodes (most connected - your core abstractions)
1. `sha256_file()` - 127 edges
2. `stable_id()` - 77 edges
3. `project_root_from()` - 55 edges
4. `require_apptainer()` - 53 edges
5. `ParquetBatchWriter` - 52 edges
6. `sha256_file()` - 51 edges
7. `_write_report()` - 51 edges
8. `git_provenance()` - 49 edges
9. `run_audit()` - 49 edges
10. `canonical_json()` - 48 edges

## Surprising Connections (you probably didn't know these)
- `test_issue_0009_permissive_concat_changes_only_nullability_metadata()` --indirect_call--> `load_cell_rows()`  [INFERRED]
  tests/unit/test_development_scoring_and_release.py → src/ipin_openppi/development_evaluation/scoring.py
- `prepare()` --calls--> `verify()`  [INFERRED]
  scripts/benchmark/prepare_protected_final_test_v1.py → src/ipin_openppi/model_optimization/common.py
- `_selection_and_kill()` --indirect_call--> `selection_key()`  [INFERRED]
  scripts/model/validate_development_completed_independent_v1.py → src/ipin_openppi/development_evaluation/semantics.py
- `_selection_and_kill()` --indirect_call--> `selection_key()`  [INFERRED]
  scripts/model/validate_development_completed_independent_v2.py → src/ipin_openppi/development_evaluation/semantics.py
- `validate()` --indirect_call--> `pair_id()`  [INFERRED]
  scripts/model/validate_stage1_pretraining_independent_v1.py → src/ipin_openppi/pair_protocol/semantics.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **External Panel Governance Return** — docs_reports_m0_m0_lambourne_2026_human_y2h_pair_semantics_audit_final_v1_document, docs_reports_m0_m0_tf_isoform_2025_y2h_semantics_and_contamination_audit_final_v1_document, governance_checkpoints_resume_001_post_tf_isoform_audit_document [INFERRED 0.85]
- **Conditional Non-detection Governance** — governance_source_surveys_public_experimental_nondetection_survey_v1_nondetection_survey, governance_risks_risk_register_risk_register, schemas_canonical_negative_evidence_audit_v1_negative_evidence_audit_schema, schemas_warehouse_evidence_warehouse_v1_evidence_warehouse_schema [INFERRED 0.85]
- **Version 3 Blueprint Provenance** — docs_blueprints_ipin_openppi_final_computational_blueprint_and_workflow_v3_final_computational_blueprint_v3, docs_blueprints_ipin_openppi_expert_project_blueprint_v2_professional_expert_project_blueprint_v2, docs_blueprints_ipin_openppi_independent_technical_review_independent_technical_review, docs_blueprints_ipin_openppi_response_to_independent_review_technical_response_to_independent_review, docs_blueprints_ipin_openppi_expert_comments_on_review_response_expert_group_comments [EXTRACTED 1.00]

## Communities (332 total, 91 thin omitted)

### Community 0 - "validate_development_completed_independent_v1.py"
Cohesion: 0.18
Nodes (35): _average_precision(), _bootstrap_gpu(), _cell_seed(), CellView, _check(), _commutative(), _concordance(), _contains_identity() (+27 more)

### Community 1 - "tf_isoform_audit/pipeline.py"
Cohesion: 0.07
Nodes (63): load_sequence_family_maps(), Return accession and exact-sequence mappings for frozen UniRef100/90/50., Governance-bounded audit of the 2025 human TF-isoform Y2H panel., _aggregate_findings(), _bool_token(), build_argument_parser(), _build_group_rows(), _build_mapping_rows() (+55 more)

### Community 2 - "sha256_file"
Cohesion: 0.13
Nodes (24): main(), Shared ingestion primitives with deterministic IDs and atomic Parquet output., require_apptainer(), Load and enforce versioned Arrow table contracts., sha256_file(), Deterministic Arrow/Parquet output for DuckDB reconciliation queries., _download(), _load_yaml() (+16 more)

### Community 3 - "pair_artifacts/support.py"
Cohesion: 0.08
Nodes (54): AtomicDatasetDirectory, Path, Create a dataset in a sibling temporary directory, then rename atomically., SchemaContract, build_argument_parser(), _decrypt_checked(), evaluate_protected(), main() (+46 more)

### Community 4 - "test_composition_order.py"
Cohesion: 0.10
Nodes (33): Frozen explanatory diagnostics of composition, order and partner matching., build_matches(), diagnostic_flags(), encode(), frequencies(), lower_above(), matched_metrics(), Order-free controls and matched within-bait estimands; no fitting. (+25 more)

### Community 5 - "reconciliation/pipeline.py"
Cohesion: 0.05
Nodes (66): RecordBatch, utc_now(), build_candidate_relations(), DuckDBPyConnection, Priority-ordered participant-to-sequence candidate generation., Stop after the first route yielding candidates for a participant., _validate_policy(), build_evidence_mapping_relation() (+58 more)

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
Nodes (33): build_argument_parser(), _independent_input_verification(), independent_repetition_counts(), independent_run_budget(), independent_selection_key(), independent_window_starts(), IndependentChecks, _load_json() (+25 more)

### Community 11 - "tf_isoform.py"
Cohesion: 0.13
Nodes (34): build_parser(), contains_record_keys(), _evidence_checks(), _glob(), _independent_filter(), independent_y2h_outcome(), _load_json(), _load_yaml() (+26 more)

### Community 12 - "partner_specificity/pipeline.py"
Cohesion: 0.12
Nodes (56): freeze(), annotate(), config(), correct_precision(), freeze(), kmer_similarity(), prepare(), project_sources() (+48 more)

### Community 13 - "huri_v2.py"
Cohesion: 0.13
Nodes (33): Book, Cell, _raw_bool(), _append_contact_row(), _append_fusion_row(), _append_generic_workbook_row(), _assert_expected_headers(), _headers() (+25 more)

### Community 14 - "iPIN-OpenPPI Novelty Claim Matrix"
Cohesion: 0.07
Nodes (28): EMBL-EBI Terms of Use snapshot, HuRI Downloads and Terms snapshot, IntAct Portal license snapshot, PDBe Public Data Access statement snapshot, RCSB PDB Usage Policy snapshot, UniProt license snapshot, License Compliance, Source and License Register v7 (+20 more)

### Community 15 - "lambourne_audit/semantics.py"
Cohesion: 0.13
Nodes (17): benchmark_claim_identifiability(), classify_paper_outcome(), OutcomeSemantics, Any, Pure semantic rules for the Lambourne Y2H-v1 audit. These functions…, Independently count the final Zhang subset and preserve all five outcomes., Frozen claim boundary used by both the pipeline and independent validator., Map the five reported states to assay-bounded semantics, fail closed. (+9 more)

### Community 16 - "project_root_from"
Cohesion: 0.12
Nodes (31): project_root_from(), main(), build_argument_parser(), Checks, DatasetSummary, _iter_summaries(), _load_json(), _load_yaml() (+23 more)

### Community 17 - "scoring.py"
Cohesion: 0.10
Nodes (41): prepare(), Path, Public-input-only preparation; never resolve or read evaluator keys., main(), align_embedding_matrix(), embedding_row_indices(), Any, ndarray (+33 more)

### Community 18 - "DEC-0012: Accept negative-evidence discovery audit"
Cohesion: 0.26
Nodes (20): DEC-0007: Accept primary raw-source acquisition, DEC-0008: Accept primary evidence staging layer, DEC-0009: Accept primary source reconciliation, DEC-0010: Propose PU compatibility as primary benchmark design, Reference-sequence Positive-Unlabeled Ranking, DEC-0011: Accept Blueprint Amendment 001 and authorize negative-evidence audit, DEC-0012: Accept negative-evidence discovery audit, Conditional Negative Evidence (+12 more)

### Community 19 - "qualify_torch_gpu.py"
Cohesion: 0.13
Nodes (26): LRScheduler, assert_nested_equal(), execute_fixture(), main(), make_model(), parse_args(), Any, Module (+18 more)

### Community 20 - "pre_split_feasibility.py"
Cohesion: 0.11
Nodes (37): Governance-bounded aggregate pre-split feasibility and leakage audit., Any, validate_config(), build_argument_parser(), _check_sidecar(), _compare_fields(), _components(), _degree_values() (+29 more)

### Community 21 - "stage1/models.py"
Cohesion: 0.14
Nodes (15): EndpointHead, Matched additive endpoint controls; the historical pair head is unchanged., build_model(), commutative_features(), exact_cosine(), initialize_exact(), LinearPairHead, NonlinearPairHead (+7 more)

### Community 22 - "validate"
Cohesion: 0.30
Nodes (14): _all_finite(), _check(), _commutative(), _independent_score(), _order(), _ordered_digest(), Any, ndarray (+6 more)

### Community 23 - "Preacquisition Index v6"
Cohesion: 0.19
Nodes (16): HuRI Preacquisition Manifest v1, Human Reference Interactome, HuRI Preacquisition Manifest v2, Preacquisition Index v5, Preacquisition Index v6, IntAct IMEx Preacquisition Manifest, IntAct IMEx Evidence, Lambourne Human Y2H Preacquisition Manifest (+8 more)

### Community 24 - "Issue 0003: HuRI Attempted Pair Universe"
Cohesion: 0.23
Nodes (16): Gate Status v3, Gate Status v4, Gate Status v5, Gate Status v6, Gate Status v7, Gate Status v8, Gate Status v9, Issue 0003: HuRI Attempted Pair Universe (+8 more)

### Community 25 - "execute"
Cohesion: 0.24
Nodes (14): DistributedDataParallel, execute(), main(), make_model(), parse_args(), Any, Module, Namespace (+6 more)

### Community 26 - "component_split/semantics.py"
Cohesion: 0.16
Nodes (21): allocate_candidate(), base_component_order(), candidate_order_indices(), deterministic_components(), DisjointSet, evaluate_candidate(), opportunity_masks(), _pool_counts() (+13 more)

### Community 27 - "test_external_bioplex.py"
Cohesion: 0.11
Nodes (31): accession_lookup(), classify(), make_panel(), positive_interval(), project_source(), Directed external-panel semantics, independent of model fitting., Exact accessions only; detect ambiguity before the public projection., Validate source-local inventories before the exact public projection. (+23 more)

### Community 28 - "Source Policy 001"
Cohesion: 0.19
Nodes (13): Source Policy 001, Source Policy 002, Source Policy 003, Lambourne et al. Molecular Cell 2025, Source Policy 004, Systematic Screen Metadata Audit v1, TF-Isoform Y2H Semantics and Contamination Audit v1, Active Pre-acquisition Manifest Set v3 (+5 more)

### Community 29 - "run_four_gpu_qualification.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 30 - "run_four_gpu_qualification_long.sh"
Cohesion: 0.15
Nodes (12): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, APPTAINERENV_CUDA_VISIBLE_DEVICES, APPTAINERENV_HF_HOME, APPTAINERENV_OMP_NUM_THREADS, APPTAINERENV_PYTHONHASHSEED, APPTAINERENV_PYTHONNOUSERSITE, APPTAINERENV_SLURM_JOB_ID (+4 more)

### Community 31 - "negative_evidence.py"
Cohesion: 0.16
Nodes (32): build_argument_parser(), _build_independent_positive_index(), _collect_metrics(), _collect_pnu(), _column_counts(), contains_record_level_report_keys(), _load_json(), _load_yaml() (+24 more)

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

### Community 37 - "run_stage1_training_matrix_v1.py"
Cohesion: 0.47
Nodes (8): CompletedProcess, embedding_gpu_hours(), governed_storage_bytes(), invocation_command(), invoke(), logged_training_gpu_seconds(), main(), Path

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
Cohesion: 0.07
Nodes (58): _allocation_summary(), _base_component_order(), _build_aggregate_tables(), build_argument_parser(), _claim_rows(), _component_degree_row(), _component_summary(), _degree_row() (+50 more)

### Community 109 - "uniprot.py"
Cohesion: 0.27
Nodes (15): strip_version(), _clean_annotation(), iter_fasta(), parse_dat_metadata(), _parse_fasta_header(), parse_uniprot(), Any, Path (+7 more)

### Community 110 - "evaluation.py"
Cohesion: 0.26
Nodes (20): _atomic_json(), main(), Path, apply_selection_and_kill_rules(), c1_novel_u_metrics(), _candidate_metadata(), _component_indexes(), degree_and_hub_diagnostics() (+12 more)

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

### Community 125 - "git_provenance"
Cohesion: 0.17
Nodes (23): git_provenance(), Governance-bounded benchmark eligibility and sequence-component audit., build_argument_parser(), _check_sidecar(), _independent_components(), _independent_eligibility(), _independent_positive_metrics(), _IndependentDisjointSet (+15 more)

### Community 126 - "M0 final report: pre-split feasibility and leakage stress-test"
Cohesion: 0.11
Nodes (17): 1. Scope and immutable inputs, 2.1 Positive-network summaries, 2.2 Similarity challenges, 2.3 Ephemeral allocation trials, 2. Governed methods, 3.1 Source composition, 3.2 Endpoint degree and hub concentration, 3.3 ALL-source component positive-edge load (+9 more)

### Community 127 - "ParquetBatchWriter"
Cohesion: 0.20
Nodes (15): canonical_json(), ParquetBatchWriter, Any, Write validated, fixed-schema Parquet parts and retain exact statistics., _assay_family(), _emit_interaction(), _emit_participant(), _interaction_semantics() (+7 more)

### Community 128 - "pair_protocol/semantics.py"
Cohesion: 0.14
Nodes (20): _degree_analysis(), c1_role(), choose_two(), degree_bin(), degree_histogram(), degree_pair_stratum(), hamilton_sample_allocation(), nearest_rank() (+12 more)

### Community 129 - "intact.py"
Cohesion: 0.42
Nodes (22): Element, _attributes(), _child(), _children(), _confidence_values(), _cv_term(), _descendant_text(), _interaction_xrefs() (+14 more)

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

### Community 135 - "completed_audit.py"
Cohesion: 0.20
Nodes (19): main(), _artifact_record(), _atomic_json(), _check(), contains_public_pair_identity(), ensemble_columns_exact(), _load_json(), Any (+11 more)

### Community 136 - "huri.py"
Cohesion: 0.26
Nodes (20): _ensembl_by_kind(), _feature_parts(), _identifiers(), _identifiers_for_database(), _interaction_semantics(), _pair_token(), parse_huri(), _parse_identifier() (+12 more)

### Community 137 - "lambourne_audit/pipeline.py"
Cohesion: 0.10
Nodes (46): Governance-bounded audit of the Lambourne et al. human Y2H-v1 panel., load_negatome_pair_index(), Path, _aggregate_panel_metrics(), _archive_inventory_rows(), _bool_value(), _build_panel_rows(), build_parser() (+38 more)

### Community 138 - "sequence_component_audit/pipeline.py"
Cohesion: 0.10
Nodes (57): Fail-closed configuration and output guards for component splitting., construct_artifacts(), verify_documents(), Path, Fail-closed guards for the pair-level PU-R protocol freeze., resolve_and_verify_documents(), _verify_inputs(), Path (+49 more)

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

### Community 143 - "main"
Cohesion: 0.30
Nodes (15): artifact_ok(), cell(), component_split(), concordance(), interolog_gpu(), kmer_matrix(), local_scores_gpu(), main() (+7 more)

### Community 144 - "M0 Pair-Level PU-R Benchmark Protocol Final v1"
Cohesion: 0.11
Nodes (18): Candidate algebra and deterministic unlabeled sampling, Claim boundary and continuing hold, Degree, hubs, and frozen future baselines, Disposition, Evaluation cells, Evidence visibility, Exact primary C1/C2/C3 assignment, Immutable evidence (+10 more)

### Community 145 - "ValueError"
Cohesion: 0.10
Nodes (46): main(), _check(), _fixture_rows(), Any, ndarray, Path, Table, Production pre-release audit for the DEC-0032 executable boundary. (+38 more)

### Community 146 - "construction.py"
Cohesion: 0.14
Nodes (35): _allocation_rows(), build_argument_parser(), _candidate_base_sql(), _candidate_token(), _cell_specs(), CellSpec, _construct_into(), _copy_query_part() (+27 more)

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

### Community 151 - "overlap.py"
Cohesion: 0.10
Nodes (22): FamilyMap, build_contamination_index(), contamination_flags(), ContaminationIndex, _family_pair_signatures(), Any, DuckDBPyConnection, Frozen evidence overlap and bounded UniRef contamination utilities. (+14 more)

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

### Community 157 - "validate_development_prerelease_independent_v1.py"
Cohesion: 0.24
Nodes (19): _all_finite(), _bootstrap_fixture(), _cell_seed(), _check(), _commutative(), _draw_counts(), _ht(), _independent_score() (+11 more)

### Community 158 - "DEC-0025: Authorize pair-level PU-R benchmark artifact construction"
Cohesion: 0.22
Nodes (8): Authorized artifact boundaries, Continuing prohibitions, DEC-0025: Authorize pair-level PU-R benchmark artifact construction, Decision, Evaluation procedure boundary, Independent validation, Protected-test non-inference rule, Sampling and overlap interpretation

### Community 159 - "Model governance and baseline/training protocol v1"
Cohesion: 0.11
Nodes (18): 10. Metrics and reporting hierarchy, 11. Degree/hub analyses and C1 novel-U sensitivity, 12. Complexity gate and model-level kill rules, 13. Exit condition, 1. Purpose and authority boundary, 2. Immutable scientific and custody boundary, 3.1 Future local custody, 3. Frozen PLM candidates and provenance (+10 more)

### Community 160 - "RESUME-005: Post-development-evaluation stop checkpoint"
Cohesion: 0.12
Nodes (15): 10. Frozen development result evidence, 11. Verification record, 12. Current closed boundary, 13. Exact fresh-thread preflight, 14. Fail-closed escalation, 1. Exact repository anchor and handoff invariant, 2. Current authority, 3. Immutable parent benchmark, model, and training state (+7 more)

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

### Community 167 - "load_contract"
Cohesion: 0.10
Nodes (34): Governance-bounded final benchmark component-partition skeleton., build_argument_parser(), _edge_set(), _load_graphs(), _load_parent_state(), _load_positive_pairs(), main(), Any (+26 more)

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

### Community 177 - "M1 Stage 1 public-training execution final report v1"
Cohesion: 0.20
Nodes (9): Frozen evidence, Frozen implementations, Independent final validation, M1 Stage 1 public-training execution final report v1, Objective and execution census, Result, Runtime, model custody, and embeddings, Scientific disposition (+1 more)

### Community 179 - "build_model_sif_v0_1_0.sh"
Cohesion: 0.40
Nodes (4): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, EXPECTED_WHEELS, build_model_sif_v0_1_0.sh script

### Community 181 - "release.py"
Cohesion: 0.24
Nodes (21): main(), _atomic_json(), _load_json(), _load_yaml(), _private_target(), _public_regular(), Any, Path (+13 more)

### Community 182 - "test_partner_specificity.py"
Cohesion: 0.13
Nodes (20): anchor_points(), embedding_indices(), weighted_concordance(), fixture_queries(), parametrize, test_bad_embedding_identities_fail(), test_canonical_pair_codes_symmetric_and_self_rejected(), test_component_bootstrap_matches_direct_weighted_comparisons() (+12 more)

### Community 183 - "protected_final_core_v1.py"
Cohesion: 0.14
Nodes (40): cell_path(), evaluate(), freeze_predictions(), import_baseline(), now(), open_candidates(), qualify(), One fixed-ensemble follow-up; reuse frozen primitives without changing them.… (+32 more)

### Community 184 - "stable_id"
Cohesion: 0.08
Nodes (56): stable_id(), conflict_overlays(), effective_tier(), permitted_role(), Reliability tiers and conflict overlays for conditional negative evidence., reliability_tier(), index_intact_negatives(), IntactNegativeRecord (+48 more)

### Community 185 - "DEC-0031: Accept Stage 1 public training and development-release readiness"
Cohesion: 0.25
Nodes (7): Accepted execution, Continuing prohibitions, DEC-0031: Accept Stage 1 public training and development-release readiness, Decision, Development-release prerequisite determination, Frozen next boundary, Validation basis

### Community 187 - "publish_model_optimization_followup_v1.py"
Cohesion: 0.24
Nodes (13): digest(), encode(), exclusive(), finite(), interval(), main(), Strictly allowlisted aggregate publication; no row, model or key inputs., validate() (+5 more)

### Community 188 - "stage1/audit.py"
Cohesion: 0.15
Nodes (25): audit_stage1_implementation(), _check(), Any, Path, Production audit of the frozen Stage 1 implementation before execution., build_training_graph(), common_neighbors_score(), component_mass_product_score() (+17 more)

### Community 189 - "local_diagnostic/pipeline.py"
Cohesion: 0.11
Nodes (43): Prospective DEC-0041 public-training local-representation diagnostic., _artifact(), _bootstrap(), _concat_rows(), evaluate_phase_a(), extract_local_embeddings(), _input_preflight(), _load_cell_rows() (+35 more)

### Community 190 - "scan_tar_gzip_archive"
Cohesion: 0.13
Nodes (20): Path, Safe, non-extracting inventory of the archived Lambourne code and inputs., Stream the archive once; inventory headers and retain only bounded selected…, _safe_member_name(), scan_tar_gzip_archive(), scan_zip_archive(), first_uniprot_accession(), parse_mitab27() (+12 more)

### Community 191 - "RESUME-006: Post-local-representation-diagnostic stop checkpoint"
Cohesion: 0.18
Nodes (10): 1. Resume authority, 2. Recorded repository state, 3. Exact scientific result, 4. Extraction and execution record, 5. Validation record, 6. Fail-closed implementation incidents, 7. Authoritative hashes, 8. Mandatory resume preflight (+2 more)

### Community 192 - "DEC-0033: Accept development pre-release qualification and activate release"
Cohesion: 0.29
Nodes (6): Accepted implementation and evidence, Activated release boundary, Continuing prohibitions, DEC-0033: Accept development pre-release qualification and activate release, Decision, Required execution and return

### Community 193 - "sha256_file"
Cohesion: 0.13
Nodes (34): main(), _all_finite(), _artifact(), audit_embeddings(), _check(), _max_standardization_difference(), Any, ndarray (+26 more)

### Community 195 - "ParsingContext"
Cohesion: 0.11
Nodes (25): ParsingContext, Any, Typed context shared by source parsers., _parse_obo(), iter_reconstructed_mutation_rows(), parse_intact(), _parse_mutations_v2(), Any (+17 more)

### Community 196 - "M1 model runtime and custody qualification final report v1"
Cohesion: 0.29
Nodes (6): Disposition, Frozen evidence, Independent validation, M1 model runtime and custody qualification final report v1, Production qualification, Result

### Community 197 - "DEC-0030: Accept model runtime and custody for Stage 1"
Cohesion: 0.33
Nodes (5): Accepted construction and evidence, Continuing hold, DEC-0030: Accept model runtime and custody for Stage 1, Decision, Scientific-use boundary

### Community 198 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): Accepted runtime and custody, Active execution boundary, Continuing hold and return, iPIN-OpenPPI project status and execution checkpoint

### Community 199 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Accepted pre-release qualification, Active development-only execution, Continuing boundary, iPIN-OpenPPI project status and execution checkpoint, Required return

### Community 200 - "component_split.py"
Cohesion: 0.12
Nodes (34): _allocate(), build_argument_parser(), _check_sidecar(), _component_id(), _components(), _contains(), _edges(), _evaluate() (+26 more)

### Community 201 - "estimand_policy_validation.py"
Cohesion: 0.17
Nodes (28): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Checks (+20 more)

### Community 202 - "run.py"
Cohesion: 0.07
Nodes (59): inference_mode, audit(), Close this follow-up without decryption, scoring, fitting or new truth access., historical_check(), prepare(), Verify fixed state and GPU/CPU development replay before protected access., synthetic_tests(), audit() (+51 more)

### Community 203 - "DEC-0032: Authorize development release and frozen-scorer evaluation"
Cohesion: 0.17
Nodes (11): Authorized development release, Authorized implementation and pre-release gate, Complexity and kill rules, Continuing prohibitions, DEC-0032: Authorize development release and frozen-scorer evaluation, Decision, Exact evaluation and reporting, Exact scorer census (+3 more)

### Community 204 - "test_homology_source.py"
Cohesion: 0.12
Nodes (33): alignment_scores(), alignment_values(), exhaustive_transfer_numpy(), fit_rows(), panel_mask(), purged_fit_mask(), Pure homology, source visibility and transfer primitives., Hide target-only public P as unit-weight U, never use target exclusion. (+25 more)

### Community 205 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Completed Stage 1 execution, Current hold, Frozen evidence and validation, iPIN-OpenPPI project status and execution checkpoint, Scientific interpretation boundary

### Community 206 - "reconciliation.py"
Cohesion: 0.16
Nodes (37): build_argument_parser(), _load_json(), _load_yaml(), main(), _nested(), Any, ArgumentParser, Checks (+29 more)

### Community 207 - "RESUME-004: Post-Stage 1 public-training-freeze phase checkpoint"
Cohesion: 0.13
Nodes (14): 10. Verification record, 11. Next-phase gate, 12. Exact fresh-thread preflight, 13. Fail-closed escalation, 1. Exact repository anchor and handoff invariant, 2. Current authority, 3. Immutable parent benchmark and sealed boundary, 4. Accepted runtime, PLMs, and embeddings (+6 more)

### Community 209 - "Locked external BioPlex co-association challenge v1"
Cohesion: 0.12
Nodes (13): Endpoint-balanced partner alternatives, Locked external BioPlex co-association challenge v1, Panels and comparisons, Question and lock, Source, mapping and exposure, Uncertainty and decision, Verification and claim ceiling, Bottom line (+5 more)

### Community 210 - "DEC-0035: Accept nullability-correction requalification and resume development scoring"
Cohesion: 0.29
Nodes (6): Accepted correction and evidence, Continuing prohibitions, DEC-0035: Accept nullability-correction requalification and resume development scoring, Decision, Required return, Resumed execution boundary

### Community 211 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Accepted preconditions, Authorized development package, Continuing boundary, iPIN-OpenPPI project status and execution checkpoint, Required return

### Community 213 - "stage1/support.py"
Cohesion: 0.08
Nodes (42): Exact constants frozen by DEC-0028 and activated by DEC-0030., deterministic_order(), order_key(), ordered_pair_id_digest(), Exact public P-versus-U ordering and rational-weight objective helpers., _artifact(), audit_training_preparation(), _check() (+34 more)

### Community 214 - "external_bioplex/pipeline.py"
Cohesion: 0.13
Nodes (36): save_npz(), compute(), evaluate(), match_census(), point_record(), A single frozen execution: features and matches, then explanatory readout., restricted_queries(), score_map() (+28 more)

### Community 215 - "Public-training local-representation diagnostic protocol v1"
Cohesion: 0.29
Nodes (6): Conditional Phase B: low-capacity feature test, Frozen local representation, Phase A: label-free late-interaction oracle, Prospective nested component test, Public-training local-representation diagnostic protocol v1, Question and scope

### Community 216 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): Accepted requalification, Active development scoring, iPIN-OpenPPI project status and execution checkpoint, Required return

### Community 217 - "M1 development release and evaluation final report v1"
Cohesion: 0.12
Nodes (15): C1 development, C2 development, C3 development — primary claim cell, Complexity and model-level kill rules, Degree and hub stratification, Final boundary, Frozen evidence, M1 development release and evaluation final report v1 (+7 more)

### Community 218 - "DEC-0039: Accept development evaluation and stop complex-model claim"
Cohesion: 0.22
Nodes (8): Accepted execution and custody, Accepted scientific result, Closed boundary, DEC-0039: Accept development evaluation and stop complex-model claim, Decision, Exact complexity and kill determination, Incident closure, Validation basis

### Community 219 - "lambourne.py"
Cohesion: 0.15
Nodes (29): build_parser(), contains_record_level_report_keys(), _glob(), _independent_evidence_checks(), independent_orf_id(), independent_raw_outcome(), _independent_source_metrics(), _load_json() (+21 more)

### Community 220 - "DEC-0034: Authorize nullability-only development loader correction"
Cohesion: 0.33
Nodes (5): Continuing prohibitions, DEC-0034: Authorize nullability-only development loader correction, Decision, Incident boundary, Requalification requirement

### Community 221 - "ISSUE-0009: Filtered development row nullability blocks strict concatenation"
Cohesion: 0.40
Nodes (4): Exact correction, Impact, ISSUE-0009: Filtered development row nullability blocks strict concatenation, Observation

### Community 222 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): iPIN-OpenPPI project status and execution checkpoint, Next gate, Released development state, Scoring incident

### Community 224 - "DEC-0037: Accept source-degree guard requalification and resume scoring"
Cohesion: 0.33
Nodes (5): Accepted implementation and evidence, Continuing prohibitions, DEC-0037: Accept source-degree guard requalification and resume scoring, Decision, Exact resume and return

### Community 225 - "Research reassessment and development embedding identity incident"
Cohesion: 0.15
Nodes (12): Authorized correction, Confirmed defect, Corrected development results, Correction verification and custody, Initial assessment at discovery, Initial read-only verification at discovery, Original prioritized continuation, Recommendation after the correction (+4 more)

### Community 226 - "validate_development_completed_independent_v2.py"
Cohesion: 0.17
Nodes (38): _average_precision(), _bootstrap_gpu(), _cell_seed(), CellView, _check(), _commutative(), _concordance(), _contains_identity() (+30 more)

### Community 227 - "DEC-0038: Authorize completed-audit scoring-census correction"
Cohesion: 0.33
Nodes (5): Continuing prohibitions, DEC-0038: Authorize completed-audit scoring-census correction, Decision, Incident evidence, Validation and return

### Community 228 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.50
Nodes (3): Accepted requalification, Active exact resume, iPIN-OpenPPI project status and execution checkpoint

### Community 229 - "DEC-0036: Authorize source-cell degree-semantics guard correction"
Cohesion: 0.33
Nodes (5): Continuing prohibitions, DEC-0036: Authorize source-cell degree-semantics guard correction, Decision, Incident and partial-run custody, Requalification requirement

### Community 230 - "ISSUE-0010: Source-cell design degree metadata was compared to the pooled feature graph"
Cohesion: 0.40
Nodes (4): Aggregate impact, Exact correction boundary, ISSUE-0010: Source-cell design degree metadata was compared to the pooled feature graph, Observation

### Community 231 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.33
Nodes (5): Accepted development execution, Closed boundary, iPIN-OpenPPI project status and execution checkpoint, Scientific disposition, Validation and evidence

### Community 232 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.50
Nodes (3): Authorized correction, Incident disposition, iPIN-OpenPPI project status and execution checkpoint

### Community 233 - "ISSUE-0011: Completed auditor used the release-table census as the score-row census"
Cohesion: 0.40
Nodes (4): Aggregate evidence and custody, Exact correction boundary, ISSUE-0011: Completed auditor used the release-table census as the score-row census, Observation

### Community 234 - "iPIN-OpenPPI project status and execution checkpoint"
Cohesion: 0.40
Nodes (4): Completed frozen execution, Current hold, Fail-closed audit incident, iPIN-OpenPPI project status and execution checkpoint

### Community 235 - "validate"
Cohesion: 0.38
Nodes (11): _check(), _expected_runs(), _order(), _ordered_digest(), Any, ndarray, Path, _safe_regular() (+3 more)

### Community 236 - "M1 public-training local-representation diagnostic: final report"
Cohesion: 0.25
Nodes (7): Extraction and evaluation census, Frozen evidence identifiers, M1 public-training local-representation diagnostic: final report, Phase A results, Question and frozen design, Scientific interpretation, Validation and information-flow controls

### Community 237 - "composition_order/data.py"
Cohesion: 0.35
Nodes (10): config(), freeze(), prior_closures(), Fail-closed, append-only registration for a diagnostic of existing evidence., register(), runtime(), save_numpy(), verify_freeze() (+2 more)

### Community 238 - "DEC-0040: Authorize public-training local-representation diagnostic"
Cohesion: 0.33
Nodes (5): Continuing prohibitions, DEC-0040: Authorize public-training local-representation diagnostic, Decision, Required evidence, Verified authorization preflight

### Community 239 - "DEC-0041: Clarify local cosine reductions before execution"
Cohesion: 0.50
Nodes (3): Binding records, DEC-0041: Clarify local cosine reductions before execution, Decision

### Community 240 - "DEC-0045: Authorize development embedding identity correction and reevaluation"
Cohesion: 0.40
Nodes (4): Authority, Authorized work, DEC-0045: Authorize development embedding identity correction and reevaluation, Preserved boundaries

### Community 244 - "ingestion/pipeline.py"
Cohesion: 0.11
Nodes (22): load_asset_index(), RawAsset, verify_asset(), Source-specific, provenance-preserving ingestion for iPIN-OpenPPI., build_argument_parser(), main(), _make_read_only(), parse_primary_sources() (+14 more)

### Community 245 - "Q: Act on the proposed next step and determine quickly whether a local, residue/domain-aware representation shows incremental public-training signal."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Act on the proposed next step and determine quickly whether a local, residue/domain-aware representation shows incremental public-training signal., Source Nodes

### Community 246 - "Q: so this project is a real dead end?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: so this project is a real dead end?, Source Nodes

### Community 250 - "sifts.py"
Cohesion: 0.21
Nodes (13): _extract_release(), _mapping_row(), _optional_int(), _parse_gzip_tsv(), parse_sifts(), Any, Path, Streaming parsers for frozen PDBe/SIFTS mapping snapshots. (+5 more)

### Community 251 - "Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end., Source Nodes

### Community 252 - "summarize_direct_binary_feasibility_v1.py"
Cohesion: 0.25
Nodes (16): csv_inventory(), digest(), git_blob(), json_bytes(), main(), Path, Bounded source acquisition/schema inventory; no outcome labels or model scores.…, Inventory missingness without replacing missing values by assay zeros. (+8 more)

### Community 253 - "protocol.py"
Cohesion: 0.19
Nodes (22): Static governance for the first bounded model protocol., _all_false(), _all_prohibited(), audit_protocol(), build_argument_parser(), _check(), load_yaml(), main() (+14 more)

### Community 258 - "pair_protocol.py"
Cohesion: 0.11
Nodes (29): Any, validate_config(), _base_pair_strata(), build_argument_parser(), Checks, _choose_two(), _independent_apportion(), _independent_bin() (+21 more)

### Community 259 - "FinalTestFixtures"
Cohesion: 0.08
Nodes (5): SimpleNamespace, FollowupFixtures, Synthetic-only fixed-ensemble, import, token and one-attempt custody tests., FinalTestFixtures, Synthetic-only final-test harness checks; never load protected data.

### Community 260 - "training.py"
Cohesion: 0.15
Nodes (25): main(), parameter_count(), learning_rate_multiplier(), positive_positions_for_batch(), positive_repetition_counts(), ndarray, Tensor, rational_weights() (+17 more)

### Community 261 - "Homology/interolog and source-aware challenge: findings"
Cohesion: 0.18
Nodes (10): Anchor-ranking results, Artifacts and execution, Endpoint-balanced swap results, Homology/interolog and source-aware challenge: findings, Judgment, Next decision, Remote-homology stress test and a newly documented limitation, Source-aware validation: useful, explicitly bounded (+2 more)

### Community 262 - "Within-anchor partner-specificity diagnostic: results"
Cohesion: 0.20
Nodes (9): Artifacts and navigation, Bottom line, Coverage and feasibility, Frozen decision, Limits and recommended next decision, Primary and endpoint-balanced results, Verification and operational record, What was frozen and executed (+1 more)

### Community 263 - "close_protected_final_test_v1.py"
Cohesion: 0.60
Nodes (5): main(), Close the public final-test record; no scoring, decryption or row access., read(), sha(), write()

### Community 264 - "validate_manifest"
Cohesion: 0.56
Nodes (8): add_check(), load_yaml(), main(), nested_get(), Any, Path, sha256_file(), validate_manifest()

### Community 265 - "Within-anchor partner-specificity diagnostic v1"
Cohesion: 0.22
Nodes (8): Endpoint-balanced partner swaps, Matched learning experiment, Paired uncertainty and decision, Primary and supporting estimands, Question and interpretation, Reproducibility and validation, Split, census, and execution freeze, Within-anchor partner-specificity diagnostic v1

### Community 266 - "validate_degree_metadata"
Cohesion: 0.19
Nodes (13): Keep source-design strata distinct from pooled scorer features., validate_degree_metadata(), degree_bin(), degree_pair_stratum(), parametrize, test_degree_bins(), _degree_rows(), parametrize (+5 more)

### Community 267 - "Q: act according to your recommendations."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: act according to your recommendations., Source Nodes

### Community 270 - "Q: continue with the best next step, generate a concise report, update relevant docs, commit and push."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: continue with the best next step, generate a concise report, update relevant docs, commit and push., Source Nodes

### Community 271 - "Homology/interolog and source-aware internal challenge v1"
Cohesion: 0.29
Nodes (6): Feasibility, execution and inference, Homology/interolog and source-aware internal challenge v1, Question and information boundary, Sequence search and stronger controls, Three challenges; no joint-axis claim, Verification and claim ceiling

### Community 272 - "validate"
Cohesion: 0.27
Nodes (16): _all_finite(), _bytes_sha256(), _cache_key(), _check(), _layout(), _order_key(), _parameter_counts(), Any (+8 more)

### Community 273 - "Q: ok! now challenge the signal with stronger homology/interolog controls and source-aware validation, as you suggested."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: ok! now challenge the signal with stronger homology/interolog controls and source-aware validation, as you suggested., Source Nodes

### Community 274 - "Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end., Source Nodes

### Community 275 - "Composition, sequence order and matched-partner diagnostic v1"
Cohesion: 0.10
Nodes (17): Composition, sequence order and matched-partner diagnostic v1, Execution and verification, Fixed scores, Matched panels (both frozen, no tuning), Question and scope, Uncertainty and interpretation rules, Bottom line, Composition/order challenge: concise findings (+9 more)

### Community 276 - "Q: what is the best next step? maybe a prospectively designed within-anchor partner-specificity test? what do you think?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: what is the best next step? maybe a prospectively designed within-anchor partner-specificity test? what do you think?, Source Nodes

### Community 278 - "DEC-0046: Authorize a within-anchor partner-specificity diagnostic"
Cohesion: 0.50
Nodes (3): Authority and scope, Boundaries, DEC-0046: Authorize a within-anchor partner-specificity diagnostic

### Community 280 - "composition_order/validation.py"
Cohesion: 0.11
Nodes (32): edges(), readout(), Independent counter/direct-comparison audit; same author, not peer review., Include a unit-multiplier draw for the point, then explicit per-bait ratios., reference_matched(), reference_matches(), reference_shuffle(), validate() (+24 more)

### Community 282 - "mapping.py"
Cohesion: 0.36
Nodes (5): AuditReferenceMaps, Any, Path, Deterministic mapping of exact TF clones and ORFeome partner constructs., _sorted_strings()

### Community 283 - "Fixed-ensemble follow-up on the existing test v1"
Cohesion: 0.25
Nodes (6): Fixed-ensemble follow-up on the existing test v1, Fixed predictor and acceptance, Metrics and interpretation, Qualification before access, Staged execution and baseline, DEC-0053: Accept the fixed ensemble for one follow-up test comparison

### Community 287 - "external_bioplex/data.py"
Cohesion: 0.20
Nodes (13): acquire(), allowed_url(), AllowlistedRedirect, config(), passed_tests(), Immutable registration and bounded published-source acquisition., register(), tsv() (+5 more)

### Community 288 - "FollowupPublicationFixtures"
Cohesion: 0.43
Nodes (3): FollowupPublicationFixtures, Aggregate schema, arithmetic, custody-chain and overwrite rejection fixtures., result_fixture()

### Community 290 - "One-time protected final test v1"
Cohesion: 0.11
Nodes (14): Frozen inputs and numerical implementation, Historical sequence, Protected final test v1: execution record, Estimand and uncertainty, Execution and custody, Fixed scientific question, Interpretation and stopping, One-time protected final test v1 (+6 more)

### Community 293 - "Q: Act according to your recommendation: one bounded independent direct-binary feasibility check after assessing whether the project is a dead end."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Act according to your recommendation: one bounded independent direct-binary feasibility check after assessing whether the project is a dead end., Source Nodes

### Community 294 - "Q: i did not fullt inderstand. what is the status of the project now? explain it cincisely in a simple language."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: i did not fullt inderstand. what is the status of the project now? explain it cincisely in a simple language., Source Nodes

### Community 295 - "Q: but there is still a frozen test set which has never been seen or studied. am i right?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: but there is still a frozen test set which has never been seen or studied. am i right?, Source Nodes

### Community 296 - "test_direct_binary_feasibility.py"
Cohesion: 0.20
Nodes (3): parametrize, Source triage must preserve missingness and never manufacture labels., test_reject_malformed_tables()

### Community 297 - "main"
Cohesion: 0.73
Nodes (5): _atomic_json(), _load(), main(), Path, _verified()

### Community 298 - "build_positive_pair_index"
Cohesion: 0.29
Nodes (8): build_positive_pair_index(), _glob(), Any, DuckDBPyConnection, Path, Register only the frozen local tables admitted by the audit policy., Index current binary mapped positives and reproducible HuRI-family views., register_evidence_views()

### Community 300 - "Bounded direct-binary feasibility assessment"
Cohesion: 0.40
Nodes (4): Acquisition and verification, Bounded direct-binary feasibility assessment, Decision sequence, Question and boundary

### Community 301 - "Q: go ahead with the best next step. Think and act as a serior researcher in AI and bioinformatics. Then, commit and push."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: go ahead with the best next step. Think and act as a serior researcher in AI and bioinformatics. Then, commit and push., Source Nodes

### Community 302 - "Q: is it a dead end project?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: is it a dead end project?, Source Nodes

### Community 304 - "pair_artifacts.py"
Cohesion: 0.17
Nodes (28): build_argument_parser(), _candidate_sql(), _candidate_union_check(), Checks, _decrypt_package(), _expected_positive_keys(), IndependentSpec, main() (+20 more)

### Community 306 - "validate_direct_binary_feasibility_v1.py"
Cohesion: 0.67
Nodes (3): main(), Separate pandas-based structural reference check and prior-closure audit. Same-…, sha()

### Community 307 - "Counter"
Cohesion: 0.20
Nodes (25): Counter, _prepare_state(), Frozen pair-level positive-unlabeled ranking protocol., _analyze(), audit_protocol(), build_argument_parser(), _candidate_designs(), _cell_summary() (+17 more)

### Community 309 - "Q: alright! 1- Heavily de-emphasize the BioPlex experiment. 2- Prospectively amend the repo’s one-shot protocol while preserving the original evaluation and its records. 3- Initiate model-architecture/parameter optimization experiments and try diffent models, architecture, parameters, etc., select the best performing development-based model, and re-test it on the test panel if it outperforms the baselone on the development panel. No new test set needed. First, ask questions if more clarifications needed."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: alright! 1- Heavily de-emphasize the BioPlex experiment. 2- Prospectively amend the repo’s one-shot protocol while preserving the original evaluation and its records. 3- Initiate model-architecture/parameter optimization experiments and try diffent models, architecture, parameters, etc., select the best performing development-based model, and re-test it on the test panel if it outperforms the baselone on the development panel. No new test set needed. First, ask questions if more clarifications needed., Source Nodes

### Community 312 - "AST"
Cohesion: 0.19
Nodes (7): AST, _module(), test_revision_2_clean_room_nullability_fixture_and_exact_ast(), _load_module(), test_independent_window_order_and_parameter_algebra(), _module(), test_independent_preparation_matrix_and_order_fixture()

### Community 313 - "validate_development_prerelease_independent_v3.py"
Cohesion: 0.53
Nodes (9): _degree_bin(), _independent_degree_check(), _load_hash_pinned_base(), Any, Path, _sha256(), _stratum(), validate() (+1 more)

### Community 314 - "Q: commit and push if all relevant docs and files are up to date."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: commit and push if all relevant docs and files are up to date., Source Nodes

### Community 315 - "Development-only model optimization v1"
Cohesion: 0.11
Nodes (15): Conditional follow-up on the existing test, Fixed search and compute, Frozen baseline and development gate, Model optimization v1 and conditional follow-up amendment, Pre-fit launcher erratum, 2026-09-11, Question and scope, Development-only model optimization v1, Outcome (+7 more)

### Community 316 - "ContractError"
Cohesion: 0.31
Nodes (6): DataType, Schema, _arrow_type(), ContractError, Any, Raised when a schema contract or row violates the frozen contract.

### Community 317 - "validate"
Cohesion: 0.71
Nodes (7): _independent_nullability_check(), _load_hash_pinned_base(), Any, Path, _sha256(), validate(), _write_json()

### Community 318 - "test_development_completed_independent_validator_v2.py"
Cohesion: 0.52
Nodes (5): _manifest(), _module(), parametrize, test_independent_identity_map_fails_closed(), test_independent_storage_coordinate_translation_matches_training_forward()

### Community 319 - "Q: conduct the model's performance on the final test."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: conduct the model's performance on the final test., Source Nodes

### Community 320 - "Q: I would ignore the BioPlex experiment because it is not a valid binary interaction panel. Moreover, the unseen test's results is extremely interesting and align very well with the development results. A surprisingly simple frozen-PLM sequence model generalizes strongly to interaction-naïve proteins in a rigorously protected PU benchmark, while network shortcuts dominate when endpoints have prior interaction exposure and genuine partner-specific/direct-binding generalization remains unresolved."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: I would ignore the BioPlex experiment because it is not a valid binary interaction panel. Moreover, the unseen test's results is extremely interesting and align very well with the development results. A surprisingly simple frozen-PLM sequence model generalizes strongly to interaction-naïve proteins in a rigorously protected PU benchmark, while network shortcuts dominate when endpoints have prior interaction exposure and genuine partner-specific/direct-binding generalization remains unresolved., Source Nodes

### Community 321 - "Q: since a simple PLM pair model was successful, I would like to suggest a model-architecture optimization on the train/development panel. If it showed improvment, we re-test on the test panel. What do you think?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: since a simple PLM pair model was successful, I would like to suggest a model-architecture optimization on the train/development panel. If it showed improvment, we re-test on the test panel. What do you think?, Source Nodes

### Community 322 - "Q: I do not agree with you. If you optimize architecture/hyperparameters exclusively on the development panel, freeze the final model, and then evaluate that final model on the test set, that is a standard and defensible train/dev/test workflow. We only apply the optimized model if it shows improvement on the development panel over the base model. We do not need to develop another unseen test set."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: I do not agree with you. If you optimize architecture/hyperparameters exclusively on the development panel, freeze the final model, and then evaluate that final model on the test set, that is a standard and defensible train/dev/test workflow. We only apply the optimized model if it shows improvement on the development panel over the base model. We do not need to develop another unseen test set., Source Nodes

### Community 323 - "test_development_completed_independent_validator.py"
Cohesion: 0.60
Nodes (3): _module(), test_independent_metric_ties_and_component_draws(), test_independent_model_forward_is_swap_symmetric()

### Community 324 - "test_development_independent_prerelease_validator.py"
Cohesion: 0.60
Nodes (3): _module(), test_clean_room_ht_half_tie_and_component_multiplier(), test_clean_room_nonlinear_forward_is_swap_symmetric()

### Community 325 - "test_development_independent_prerelease_validator_v3.py"
Cohesion: 0.60
Nodes (3): _module(), test_revision_3_clean_room_degree_semantics_fixture(), test_revision_3_validator_rejects_source_hash_drift()

### Community 327 - "Q: The actual model being proposed is a three-seed ensemble. Its prediction is the averaged ensemble score—not any individual seed."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: The actual model being proposed is a three-seed ensemble. Its prediction is the averaged ensemble score—not any individual seed., Source Nodes

### Community 329 - "normalize_followup_guard_log_v1.py"
Cohesion: 0.67
Nodes (3): normalize(), parse(), Preserve UCX-prefixed probe stdout and expose its unchanged JSON attestation.…

## Knowledge Gaps
- **854 isolated node(s):** `ipin-openppi`, `run_model_optimization_followup_v1.sh script`, `run_protected_final_test_v1.sh script`, `project_paths.sh script`, `IPIN_APPTAINER_CACHE` (+849 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **91 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `Reference-sequence Positive-Unlabeled Ranking` (4× useful, score=1.827475219)
- `DEC-0050: Bound the data feasibility check; stop the current model track` (2× useful, score=1.993016676)
- `composition_order/pipeline.py` (2× useful, score=1.991510811)
- `composition_order/validation.py` (2× useful, score=1.991510811)
- `validation/systematic_screen_audit.py` (2× useful, score=1.979547767)
- `Prospective nested component test` (2× useful, score=1.976008824)
- `Primary PU-retrieval metrics` (2× useful, score=1.976008824)
- `component_split.py` (2× useful, score=1.447983138)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sha256_file()` connect `sha256_file` to `tf_isoform_audit/pipeline.py`, `pair_protocol.py`, `pair_artifacts/support.py`, `reconciliation/pipeline.py`, `benchmark/systematic_screen_audit.py`, `lambourne_audit/pipeline.py`, `sequence_component_audit/pipeline.py`, `model_governance.py`, `validation/systematic_screen_audit.py`, `tf_isoform.py`, `project_root_from`, `construction.py`, `pre_split_feasibility.py`, `overlap.py`, `negative_evidence.py`, `load_contract`, `pair_artifacts.py`, `Counter`, `release.py`, `stable_id`, `component_split.py`, `estimand_policy_validation.py`, `reconciliation.py`, `pre_split_audit/pipeline.py`, `lambourne.py`, `ingestion/pipeline.py`, `git_provenance`, `protocol.py`, `ParquetBatchWriter`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `validate_protocol()` connect `pair_protocol.py` to `sha256_file`, `Counter`, `git_provenance`, `sequence_component_audit/pipeline.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `Checks` connect `project_root_from` to `pair_artifacts/support.py`, `component_split.py`, `estimand_policy_validation.py`, `validation/systematic_screen_audit.py`, `tf_isoform.py`, `sequence_component_audit/pipeline.py`, `reconciliation.py`, `pre_split_feasibility.py`, `lambourne.py`, `git_provenance`, `negative_evidence.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 141 inferred relationships involving `ValueError` (e.g. with `csv_inventory()` and `main()`) actually correct?**
  _`ValueError` has 141 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `Counter` (e.g. with `prepare()` and `main()`) actually correct?**
  _`Counter` has 80 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ipin-openppi`, `run_model_optimization_followup_v1.sh script`, `run_protected_final_test_v1.sh script` to the rest of the system?**
  _854 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `tf_isoform_audit/pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07246376811594203 - nodes in this community are weakly interconnected._