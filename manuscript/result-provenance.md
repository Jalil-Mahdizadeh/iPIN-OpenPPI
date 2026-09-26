# Result provenance — internal verification record

This file documents the manuscript package, not a proposed new analysis. All scientific sources were read without modification. The protected evaluation operators, pair-level truth, prediction archives and model fitting were not run. The package uses aggregate results and implementation inspection. Historical namespace names below identify the authoritative final development artifacts; they are not part of the submitted scientific narrative.

Paths in this file are relative to the repository root unless prefixed `manuscript/`. Exact source SHA-256 fingerprints and byte counts are in `source-data/source-manifest.csv`. Portable snapshots retain only relevant fields and do not include protected pair identities or row predictions. Figure CSVs retain source paths and JSON-key locations at row level. A slash-separated key denotes traversal through JSON objects; numeric path elements index arrays from zero. Where a row references a parent object, the point/interval field names are specified below.

## Authoritative evidence map

| Evidence | Authoritative file | Relevant fields | Scientific report / protocol |
|---|---|---|---|
| Final development primary results | `artifacts/results/development_evaluation/development_embedding_identity_correction_v2/PRIMARY_METRICS.json` | `cells/<cell>/metrics/<model>/ht_positive_vs_U_concordance`; `bootstrap_percentile_95_for_controls_and_ensembles/<model>` | Final validated development evaluation; pair-level PU-R protocol |
| Development source-exclusive diagnostics | Same directory, `SOURCE_EXCLUSIVE_METRICS.json` | `cells/<source-cell>/<model>/ht_positive_vs_U_concordance` | Final development source diagnostics; points only in this file |
| Original protected evaluation | `artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json` | `cells/<cell>/metrics/<model>/{ht_P_vs_U_concordance,percentile_95}`; `model_minus_controls/<control>/{model_minus_control,paired_percentile_95}` | `docs/reports/m1/M1_Protected_Final_Test_v1.md`; `docs/protocols/PROTECTED_FINAL_TEST_v1.md` |
| Optimized follow-up | `artifacts/results/model_optimization_followup_v1/FOLLOWUP_TEST_RESULTS.json` | `cells/<cell>/metrics/<model>`; `ensemble_minus_baseline/{difference,paired_percentile_95}`; `test_previously_examined` | `docs/reports/m1/M1_Model_Optimization_Followup_v1.md`; matching follow-up protocol |
| Bounded optimization | `artifacts/results/model_optimization_v1/RESULTS.json` | `all_evaluations`; `all_ensemble_groups`; `selected`; `development_gate` | `docs/reports/m1/M1_Model_Optimization_v1.md`; `configs/model_optimization_v1.json` |
| Development component sensitivities | `artifacts/results/c3_control_shift_investigation_v1/RESULTS.json` | `development`; `bootstrap/scores`; `published_comparison` | `docs/reports/m1/M1_C3_Control_Shift_Investigation_v1.md`; initial diagnostic protocol |
| Development positive-group decomposition | Same directory, `COMPONENT_SUPPLEMENT.json` | `groups`; `all_positive_participating_component_influences`; `sensitivities` | Component supplement protocol; same scientific report |
| Partner conditioning | `artifacts/results/within_anchor_partner_specificity_v1/RESULTS.json` | `macro_concordance`; `model_ci95`; `primary_delta`; `primary_delta_ci95`; `quartets`; `folds` | `docs/reports/m1/M1_Within_Anchor_Partner_Specificity_Diagnostic_v1.md`; matching protocol/config |
| Internal partner panel support | Same directory, `FEASIBILITY.json` | `folds`: counts, concentration and panel support | Same partner study |
| Homology/source stress tests | `artifacts/results/homology_source_challenge_v1/RESULTS.json` | `arms/<arm>/{macro,model_intervals,deltas,folds,quartet,stratum_summary}` | `docs/reports/m1/M1_Homology_and_Source_Challenge_v1.md`; matching protocol/config |
| Homology/source fitting support | Same directory, `FEASIBILITY.json` | `folds`: fit/evaluation counts, removed endpoints, quartet support | Same challenge |
| Residual detected alignments | `artifacts/validation/homology_source_challenge_v1/HOMOLOGY_EDGE_AUDIT.json` | `counts/<identity>/cross_original_folds`; per-fold cross links | Homology edge audit |
| Public positive source membership | `artifacts/results/homology_source_challenge_v1/SOURCE_PROJECTION.json` | `counts/1`, `counts/2`, `counts/3` | Public-positive source projection |
| Pair-role and sampling census | `artifacts/validation/benchmark_design/pair_level_pu_r_benchmark_artifacts_v1/CONSTRUCTION_REPORT.json` | `construction/{cell_counts,role_counts,cross_cell_unlabeled_overlap}` | `docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md` |
| Endpoint/component split | `artifacts/validation/benchmark_design/final_benchmark_component_split_v1/AUDIT_REPORT.json` | `aggregate_metrics/{partition_summaries,selection_summaries}` | `docs/reports/m0/M0_Final_Benchmark_Component_Split_Final_v1.md` |
| Final model specifications | `artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json` | `models`, `encoder`, `embedding_dimension`, `optimized_recipe` | `docs/models/FROZEN_PAIR_MODELS_v1.md` |
| Assay-denominator limitation | `artifacts/validation/benchmark_design/systematic_screen_metadata_v1/AUDIT_REPORT.json` | `scientific_conclusion`; `systematic_universe_assessment` | Systematic-screen metadata report |
| Negative-evidence feasibility | `artifacts/validation/negative_evidence/negative_evidence_audit_v1/AUDIT_REPORT.json` | `pnu_feasibility`; `metrics`; `scientific_conclusion` | Negative-evidence discovery audit final report |

The implementation, data design, validation summaries, final model cards, protocols and matching scientific reports were inspected together. The direct-binary feasibility review and the earlier conditional-panel audits were consulted for the external-validation boundary, without reopening their quarantined pair data. Their detailed triage is not reproduced because it is not an experiment supporting the principal claims.

## Figure and table lineage

| Manuscript artifact | Snapshot(s) / exact source keys | Generation script |
|---|---|---|
| Figure 1 / `figure-1.csv` | `split`: `aggregate_metrics/partition_summaries`; C1/C2/C3 definitions from `configs/pair_level_pu_r_benchmark_protocol_v1.yaml:pair_assignment`; schematic entities correspond to `model_optimization/models.py` and the frozen model specification | `scripts/extract_results.py`; `scripts/plot_figures.py:figure1` |
| Figure 2 / `figure-2.csv` | `development`, `original`: primary cells, selected model/control metrics and marginal intervals | `extract_results.py`; `plot_figures.py:figure2` |
| Figure 3 / `figure-3.csv` | `development`, `original`, `followup`: C3 metrics; `optimization/development_gate/candidate_concordance` | `extract_results.py`; `plot_figures.py:figure3` |
| Figure 4a / `figure-4.csv` | Full points: `shift/development/full_concordance`; full intervals: `shift/bootstrap/scores/<model>/full_ci95`; largest-removal points: `development/both_P_and_U_without_largest/concordance`; corresponding `without_largest_ci95`; other rows: `components/sensitivities/<subset>/{concordance,ci95}` | `extract_results.py`; `plot_figures.py:figure4` |
| Figure 4b / `figure-4.csv` | `components/groups/{within_component,between_component,neither_in_third}` and component influence with `endpoint_size_rank=3`; `positive_fraction`, `positive_group_vs_full_U`, `positive_rows`, `HT_U_fraction` | `extract_results.py` calculates only the exact displayed arithmetic decomposition; `plot_figures.py:figure4` |
| Figure 5a / `figure-5.csv` | `partner/{macro_concordance,model_ci95,primary_delta,primary_delta_ci95}`; linear-unary marginal CI from `homology/arms/union/model_intervals/endpoint_linear/ci95` | `extract_results.py`; `plot_figures.py:figure5` |
| Figure 5b,c / `figure-5.csv` | `homology/arms/<arm>/deltas/endpoint_linear/{point,ci95}`; `quartet/{points/pair_linear,pair_interval/ci95}`; counts summed over `folds` | `extract_results.py`; `plot_figures.py:figure5` |
| Figure 6 / `figure-6.csv` | `optimization/all_evaluations[stage=1]`; `all_ensemble_groups`; `development_gate`; `followup/cells/C3_test/ensemble_minus_baseline` | `extract_results.py`; `plot_figures.py:figure6` |
| Supplementary Figure S1 / `figure-s1.csv` | `original/cells/C[1–3]_test/model_minus_controls` | `extract_results.py`; `plot_figures.py:figures1` |
| Table 1 / `tables/table-1.csv` | `construction/construction/cell_counts`: training and six primary cells | `extract_results.py`; `render_tables_references.py` |
| Table 2 / `tables/table-2.csv` | `model_spec/models`, `model_spec/optimized_recipe`; original configuration `optimization_and_search`; new `recipes` configuration | `extend_tables.py`; `render_tables_references.py` |
| Supplementary Table S1 / `tables/table-s1.csv` | `split/aggregate_metrics/partition_summaries` | `extract_results.py`; `render_tables_references.py` |
| Supplementary Table S2 / `tables/table-s2.csv` | Primary and source-specific final development/protected outputs, plus optimized development point; each CSV row has its source path/key | `extract_results.py`; `extend_tables.py`; `render_tables_references.py` |
| Supplementary Table S3 / `tables/table-s3.csv` | `optimization/all_evaluations` joined to frozen recipe definitions; display adds ensemble values from `all_ensemble_groups` | `extract_results.py`; `render_tables_references.py` |
| Supplementary Table S4 / `tables/table-s4.csv` | `homology_support/folds`: all twelve arm/fold records | `extend_tables.py`; `render_tables_references.py` |

The complete numerical data for each quantitative figure panel are in its same-basename CSV. Figure 1's CSV documents entities, labels, counts and processing relationships. Plot layout and style are in the plotting script. No figure requires private scores, model weights or a rerun of scientific analysis. Missing intervals remain missing; they are not inferred from marginal intervals or individual seeds.

## Major numerical claims

This map groups repeated claims across the Abstract, Results, Discussion, Methods and SI. The figure/table CSVs retain full precision. Additional values and exact nested paths are flattened in `source-data/ancillary-claim-values.csv`.

| Claim group | Values in the manuscript | Source/key |
|---|---|---|
| Eligible universe and split | 17,000 endpoints; 7,782 components; 11,900/2,550/2,550 allocation | `split/aggregate_metrics/partition_summaries`: sums of `endpoint_count`, `component_count`, and individual partition rows |
| Positive universe and roles | 58,049 released pairs; 16,799 fitting positives; 5,387 quarantined | `construction/construction/role_counts`; total is the sum of mutually exclusive primary roles |
| C1/C2/C3 sample counts | Table 1 positive counts; 1,000,000 U per primary evaluation cell; 2,000,000 training U | `construction/construction/cell_counts` |
| Original development/test C3 | 0.784142 / 0.789249, with corresponding marginal CIs | Figure 3 rows for affine iPIN |
| All eleven protected C3 control differences | Positive lower bounds; length-ratio gain 0.239947 with CI approximately [0.128, 0.313] | `original/cells/C3_test/model_minus_controls`; Figure S1 |
| C1/C2 network comparisons | C1 −0.069337 versus preferential attachment; C2 −0.005353 versus degree sum | `original/cells/C1_test/model_minus_controls/preferential_attachment`; analogous C2 degree-sum key |
| Fixed-control cohort shifts | 3-mer 0.644683→0.493970; interolog 0.635701→0.484037; length ratio 0.660880→0.549302; length sum 0.520454→0.327235 | Figure 3, each control's development/test rows |
| Test-only controls | Composition 0.414414; raw pooled ESM 0.494045 | Figure 3 original-test rows |
| Within-component enrichment and decomposition | 825/2,265 P; 6.6144% U mass; 0.873516 / 0.513580 subgroup 3-mer scores; 94.0% excess contribution | `components/groups/{within_component,between_component}`; displayed share = `positive_fraction*(group_concordance-0.5)/(full_concordance-0.5)` |
| Rank-three component and interolog | 61 endpoints; 692 P; 70.1% excess contribution | `components/all_positive_participating_component_influences` where `endpoint_size_rank=3`; same arithmetic definition |
| Component-removal outcomes | All full/removal/between-component estimates, CIs and retained P/U counts | Figure 4a source rows |
| Length-conditional and source-conditional checks | 3-mer 0.676796, interolog 0.665245, affine 0.778967; HuRI 3-mer 0.652732→0.471040, interolog 0.627836→0.472572 | `shift/development/within_length_bin_full/positive_weighted_within_bin_concordance`; `shift/published_comparison/HuRI_exclusive_C3` |
| Within-anchor conditioning | 3,072 anchors; 0.663612 pair / 0.584203 linear unary / 0.557894 MLP unary; primary difference 0.105718 [0.093729, 0.139639] | `partner/folds`, `macro_concordance`, `primary_delta`, `primary_delta_ci95` |
| Propensity sensitivity | Positive direction; 0.128169 conditional gain | `partner/propensity_sensitivity/delta` |
| Original swaps | 6,000 selected; preference 0.727833; 3-mer 0.631; paired gap 0.096833 [0.033463, 0.152123] | `partner/quartets/{point,all_points,control_deltas,paired_control_ci95}`; support from `partner_support/folds/selected_quartets` |
| Anchor concentration | Fold 0: 1,075 anchors, 598 components, 36.1% largest-component share, effective component count 7.63 | `partner_support/folds/0/{eligible_anchors,anchor_components,largest_anchor_component_fraction,effective_anchor_components}` |
| Homology/source performance | All four anchor results, paired gains, swap preferences and CIs | Figure 5b,c; `homology/arms` |
| Homology challenge residual edges | 344 cross-fold links at ≥30% identity | `homology_edges/counts/30/cross_original_folds` |
| Purge and source support | Per-fold fitting endpoints/P and source-specific quartet support | Table S4, underlying `homology_support/folds` |
| Source memberships | 1,970 / 13,547 / 1,282 | `source_membership/counts/{1,2,3}` |
| Sparse reverse-source interval | 66 quartets, 29/17/20 by fold; 1,998 finite draws | `homology/arms/huri_to_hi/folds`; `quartet/pair_interval/valid_replicates` |
| Optimization scope and selection | 24 initial recipes; four promoted recipes; 12 promoted fits; 168 total epochs; width 256; 498,053 parameters | `optimization/{stage1_runs,stage2_runs,total_epochs,selected}`; `recipes` and `model_spec` |
| Near-tied heads / encoder comparison | 0.799419 residual; 0.799379 150M MLP; 0.794405 promoted 650M MLP | `optimization/all_ensemble_groups`, epoch-four rows |
| Development optimized gain / seed behavior | 0.015277 [0.002942,0.034460]; matched seed gains and 0.021207 range | `optimization/development_gate` |
| Protected optimized gain | C3 0.018699 [−0.001358,0.050000]; C2 0.046002; C1 0.072544 with CIs | `followup/cells/<cell>/ensemble_minus_baseline`; `source-data/claim-values.csv` |
| Assay-negative feasibility | 1,163 unique conditional pairs; 315 publications; no identified population-calibrated primary design | `negative/pnu_feasibility` |
| Cross-cell U reuse | 20,000,000 cell rows / 15,536,850 distinct pair IDs | `construction/construction/cross_cell_unlabeled_overlap` |
| Split-search support | 4,096 candidates; 2,653 valid | `split/aggregate_metrics/selection_summaries` |

## Equations checked against implementation

| Equation | Implementation checked | Consequential detail |
|---|---|---|
| (1), P/U concordance | `src/ipin_openppi/development_evaluation/semantics.py:weighted_pairwise_concordance` | Half credit for ties; census P; rational-design-weighted U; normalized by P mass × U mass |
| (2), embeddings | `src/ipin_openppi/stage1/embeddings.py` pooling and normalization | Average overlapping windows at each residue before protein averaging; population SD; training-only statistics; floor 1e−6 |
| (3), pair representation | `src/ipin_openppi/stage1/models.py:commutative_features`; optimization `models.py:features` | Sum, absolute difference, product and exact standardized-vector cosine in that order |
| (4), residual score | `src/ipin_openppi/model_optimization/models.py:PairHead` | Affine + LayerNorm/MLP; GELU; dropout between GELU and scalar projection during training only |
| (5), ensemble | Protected scorer and follow-up scorer; frozen model registry | Average raw member scores in FP64 after FP32 forwards; no sigmoid |
| (6), objective | Stage-1 training and `model_optimization/run.py` | Softplus of negative P-minus-U difference; each U weight divided by fitting-set mean |
| (7), transfer | `stage1/baselines.py:exact_interolog_score`; `homology_source/semantics.py:exhaustive_transfer_numpy` | Maximum over all fitting P edges and both endpoint orientations of minimum endpoint similarity |
| (8), swaps | `partner_specificity/semantics.py:quartet_credit` | Identical four endpoints; tie tolerance 1e−6; selected-panel preference |
| (S1), bilinear branch | `model_optimization/models.py:PairHead` | Bias-free shared projection and interaction weights; division by square root of rank |
| (S2), anchor metric | `partner_specificity/semantics.py:anchor_points` | P/U ranking per anchor, then equal-anchor aggregation |
| (S3), alignment kernels | `homology_source/semantics.py:alignment_scores` | Identity × capped shorter span/80; identity × geometric-mean coverage |
| (S4), decomposition | `scripts/analysis/c3_control_shift_components_v1.py` and grouped aggregate outputs | Disjoint positive groups, common full-U reference; not a dev/test causal decomposition |

The inspected implementation files and hashes are listed in `source-data/implementation-provenance.csv`. This records inspection, not re-execution of those scientific pipelines.

## Validation evidence and manuscript checks

Existing validation records report passing final development numerical validation, original protected-evaluation closure, optimized follow-up audit and frozen-model preservation. They were consulted rather than rerun. Relevant records are the final development `INDEPENDENT_VALIDATION_ARTIFACT_REGISTRY.json`, `artifacts/validation/protected_final_test_v1/COMPLETED_AUDIT.json`, `artifacts/validation/model_optimization_followup_v1/COMPLETED_AUDIT.json`, and `artifacts/validation/frozen_pair_models_v1/FREEZE_AUDIT.json`. These are repository numerical checks, not independent biological replication.

`source-data/package-validation.json` records the manuscript-specific checks: required files, figure/CSV pairing, image dimensions/DPI, finite estimates, interval order, citation coverage, exclusions, portable regeneration and selected claim arithmetic. No protected results are recalculated by these checks.

Bibliography metadata were checked against primary publication records through Europe PMC and DOI content negotiation; NeurIPS proceedings supply the two entries without journal DOIs. `source-data/references/verified-references.json` records full metadata and verification URLs. The bibliography was checked to include every citation in the main text and SI, with no uncited entries. The citation count is 34.
