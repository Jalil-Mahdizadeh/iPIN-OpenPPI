# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric
protein–protein interactions. The implemented benchmark measures ranking of
released positives against sampled unlabeled pairs; unlabeled pairs are not
verified noninteractions.

## Current project

The repository contains the evidence-processing and benchmark pipeline, two
frozen pooled iPIN ensembles, the frozen TUnA-retrained ensemble as iPIN model 3,
completed comparisons with five published methods, and
twelve protein-screening examples. Start with these records:

| Area | Current reference |
|---|---|
| Frozen iPIN predictors | [Three-model registry and cards](docs/models/FROZEN_PAIR_MODELS_v2.md) |
| Published-method comparisons | [Benchmark results and execution status](benchmark/README.md) |
| Protein-screening examples | [Twelve-target comparison](example/twelve_target_comparison_v1/REPORT.md), [panel index](example/README.md) |
| Scientific reports and diagnostics | [Report index](docs/reports/README.md) |
| Core model freeze and decisions | [Governance index](governance/README.md) |
| Implementation and tests | [Source map](src/README.md), [entry points](scripts/README.md), [test policy](tests/README.md) |

The two pooled iPIN predictors use frozen ESM-2 150M sequence representations, training-only
normalization, symmetric pair features, and equal-weight three-seed raw-score
ensembles. The original affine ensemble is the confirmatory baseline; the
optimized residual-MLP ensemble has the higher observed scores of these two
iPIN models. Exact checkpoints and prediction definitions are frozen under
[DEC-0054](governance/decisions/DEC-0054-freeze-and-designate-both-models.md).

Under [DEC-0055](governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md),
**TUnA-retrained is the third frozen iPIN model** (`tuna_retrained_ensemble`).
It retains the selected epoch-4 checkpoints for all three seeds, full-context
residue representations, trained GP covariance, and the equal mean of
mean-field-adjusted logits. Its C1/C2/C3 concordances are
**0.948619 / 0.880401 / 0.815875**. This registration preserves the completed
PU-TUnA adaptation and its published architecture attribution; the existing
two-model freeze remains unchanged.

| Test cell | Original iPIN | Optimized iPIN | Gain and paired 95% interval |
|---|---:|---:|---|
| **C3 (primary)** | 0.789249 | 0.807948 | +0.018699 [−0.001358, +0.050000] |
| C2 | 0.805299 | 0.851301 | +0.046002 [+0.031561, +0.061559] |
| C1 | 0.843493 | 0.916037 | +0.072544 [+0.063093, +0.081869] |

The primary C3 gain remains inconclusive because its paired interval includes
zero. The optimized-model evaluation is a disclosed follow-up on the existing,
previously examined test, not independent replication. See the
[original final-test report](docs/reports/m1/M1_Protected_Final_Test_v1.md) and
[fixed-ensemble follow-up](docs/reports/m1/M1_Model_Optimization_Followup_v1.md).
The original evaluation, the follow-up, and their spent access ledgers remain
separate records.

Published-method results are complete for TUnA, D-SCRIPT, PLM-interact, RAPPPID,
and SPRINT. TUnA's retrained ensemble has C3 concordance 0.815875; its paired
difference from optimized iPIN also includes zero. Retraining coverage and
checkpoint-selection limitations differ by method, especially RAPPPID's
partially trained recovery ensemble. The [benchmark index](benchmark/README.md)
links each result and its caveats. The twelve-target application scores 37
nominated positives and 3,700 unlabeled pairs with all three frozen iPIN models.
It uses freshly retrieved sequences and recomputed embeddings, and reports PU
concordance, AP/MAP, MRR, recall, NDCG, enrichment, and target success at fixed
screening budgets. The [report](example/twelve_target_comparison_v1/REPORT.md)
discloses training/development overlaps and sensitivity analyses. This separate
descriptive application retains the original six-target results.

Concordance is neither binary binding accuracy nor calibrated interaction
probability. Genuine partner-specific/direct-binding generalization remains
unresolved. BioPlex AP-MS provides secondary cross-assay association evidence;
its frozen negative findings are retained in the [report index](docs/reports/README.md).

## Pipeline and benchmark design

1. Acquire checksum-registered source snapshots and preserve assay, construct,
   orientation, evaluability, and outcome semantics during ingestion and
   reconciliation.
2. Audit eligible sequences, homology components, and leakage before freezing
   the endpoint split: 17,000 endpoints in 7,782 components, partitioned into
   11,900 training, 2,550 development, and 2,550 test endpoints.
3. Construct the frozen pair-level positive–unlabeled benchmark with explicit
   evidence visibility, deterministic sampling, and design weights. Training
   uses 16,799 positives; development and protected packages are separated.
4. Prepare sequence representations and fit models on training inputs. Use
   development data for model selection and freeze the full scorer before its
   separately authorized evaluation.
5. Report C3 as primary, C2/C1 as secondary, and use paired component-bootstrap
   uncertainty. C3 tests two interaction-training-naïve endpoints; sequence
   pretraining exposure and broader biological generalization require separate
   interpretation.

The [Version 3 blueprint](docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md),
[frozen split decision](governance/decisions/DEC-0022-accept-final-benchmark-component-split.md),
[pair protocol](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md),
and [artifact report](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md)
record the scientific design. Numbered protocols, status files, and checkpoints
describe their original phase boundaries. The current three-model disposition is
[status v55](governance/PROJECT_STATUS_v55.md); benchmark and example
work is documented in its own directories.

## Repository layout

| Path | Purpose |
|---|---|
| `src/ipin_openppi/` | Evidence processing, benchmark construction, modeling, diagnostics, and validation |
| `scripts/` | Data, benchmark, model, analysis, and platform entry points |
| `tests/` | Synthetic unit, safety, validation, and model tests |
| `benchmark/` | Published-method implementations, execution records, aggregate comparisons, and dedicated containers |
| `example/` | Twelve target panels, three-model scoring, retrieval metrics, and preserved historical examples |
| `docs/` | Blueprints, scientific protocols, reports, and model cards |
| `governance/` | Decisions, phase-specific status records, gates, risks, and licenses |
| `configs/`, `schemas/` | Versioned configuration and data contracts |
| `containers/` | Core ARM64 Apptainer recipes, dependency locks, and image provenance |
| `slurm/` | Core Arrhenius job specifications and scheduler logs |
| `data/` | Source manifests and local raw, staging, canonical, derived, and split data |
| `artifacts/` | Registries, validation evidence, run records, and local generated products |
| `releases/` | Public-release policy |
| `graphify-out/` | Repository knowledge graph and navigation reports |

## Execution and preservation

All production computation runs on NAISS Arrhenius in checksum-identified ARM64
Apptainer SIF images. The [container guide](containers/README.md) identifies the
qualification, data, and model environments. Scientific Python dependencies
belong inside an accepted SIF; do not install or run a native project environment
on the host. See the [test guide](tests/README.md) for synthetic validation.

Keep project artifacts under this repository and credentials in protected
locations outside source control. Give each material run a unique directory and
machine-readable manifest. Raw sources, frozen splits, model weights, container
images, sealed truth, and completed scientific results must not be overwritten;
new scientific work requires its own version and authorization. Preserve the
[embedding-identity correction](docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md)
and the earlier invalid evaluation as distinct evidence. Never reset a spent
evaluation ledger or tune on protected test results.

Generated datasets, private predictions, checkpoints, and SIF images remain
local and are intentionally excluded from Git. A checkout contains the code,
configuration, provenance, and public aggregates, not every execution input.
Untested predictions are computational hypotheses, not validated interactions.
