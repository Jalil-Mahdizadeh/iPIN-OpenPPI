# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric
protein–protein interactions. The implemented benchmark measures ranking of
released positives against sampled unlabeled pairs; unlabeled pairs are not
verified noninteractions.

## Current project

**iPIN-TUnA-31k is the primary/default iPIN predictor for human PPI ranking.**
The current catalogue contains this selected 31,188-positive, epoch-1,
three-seed ensemble and three preserved historical reference models.
The repository also contains the evidence-processing pipeline, completed
published-method comparisons, twelve human screening examples and historical
non-human transfer evaluations. Start with these records:

| Area | Current reference |
|---|---|
| Primary model and historical references | [Four-model registry and cards](docs/models/FROZEN_PAIR_MODELS_v3.md) |
| Latest human comparison | [15-predictor test2 comparison including X-PAIR](docs/reports/m1/M1_XPAIR_Test2_Comparison_v1.md) |
| Published-method comparisons | [Current and historical benchmark results](benchmark/README.md) |
| Protein-screening examples | [Selected 31k on the fixed panel](artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/REPORT.md), [panel index](example/INDEX.md) |
| Non-human transfer | [Six-organism frozen-model evaluation](benchmark/nonhuman_transfer_v1/REPORT.md) |
| Scientific reports and diagnostics | [Report index](docs/reports/README.md) |
| Core model freeze and decisions | [Governance index](governance/README.md) |
| Implementation and tests | [Source map](src/README.md), [entry points](scripts/README.md), [test policy](tests/README.md) |

Under [DEC-0056](governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md),
`ipin_tuna_31k_ensemble` is the primary/default registry entry; the completed
experiment ID `selected_31k` remains an alias. It retains the published Bernett
TUnA architecture, the iPIN PU adaptation, all three selected seeds, and the
exact saved GP covariance. Its **C1/C2/C3 test2 macro concordances are
0.886903 / 0.827113 / 0.786652**, highest among the 15 evaluated predictors,
including the two released X-PAIR checkpoints in the
[completed follow-up](experiments/x_pair_test2_v1/results/INTERPRETATION.md).
The paired C3 gain over historical 17k PU-TUnA is **+0.042781
[0.019768, 0.070150]**. Intervals are pointwise, without multiplicity correction.
Default X-PAIR scores **0.704050 / 0.693652 / 0.741983** on C1/C2/C3.
The paired C3 gain of selected 31k over default X-PAIR is **+0.044669
[0.012224, 0.075317]** and persists after excluding exact X-PAIR training and
validation pair overlaps. On added C3 alone, X-PAIR scores higher by point
estimate (0.773173 default; 0.783830 interaction-only; selected 31k 0.740105),
but its exploratory paired intervals include zero. PLM-interact also scores
higher on that cohort (0.767828).
Test2 is a previously examined follow-up, and the twelve-target panel has
training exposure. The designation is scoped to human P/U ranking.

The new [v3 release](docs/models/FROZEN_PAIR_MODELS_v3.md) preserves the exact
prediction unit and aggregate evidence. The three earlier models retain their
existing IDs, aliases, weights and historical results.

## Historical reference models and applications

The two pooled iPIN predictors use frozen ESM-2 150M sequence representations, training-only
normalization, symmetric pair features, and equal-weight three-seed raw-score
ensembles. The original affine ensemble is the confirmatory baseline; the
optimized residual-MLP ensemble has the higher observed scores of these two
iPIN models. Exact checkpoints and prediction definitions are frozen under
[DEC-0054](governance/decisions/DEC-0054-freeze-and-designate-both-models.md).

Under [DEC-0055](governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md),
TUnA-retrained was registered as the third iPIN model (`tuna_retrained_ensemble`).
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

The historical optimized-versus-original C3 gain remains inconclusive because
its paired interval includes zero. That evaluation is a disclosed follow-up on the existing,
previously examined test, not independent replication. See the
[original final-test report](docs/reports/m1/M1_Protected_Final_Test_v1.md) and
[fixed-ensemble follow-up](docs/reports/m1/M1_Model_Optimization_Followup_v1.md).
The original evaluation, the follow-up, and their spent access ledgers remain
separate records.

Published-method results are complete for TUnA, D-SCRIPT, PLM-interact, RAPPPID,
SPRINT, and released X-PAIR. X-PAIR was evaluated on expanded test2 only,
with outputs in [experiments/x_pair_test2_v1](experiments/x_pair_test2_v1/README.md).
On the original benchmark, TUnA's retrained ensemble has C3 concordance 0.815875; its paired
difference from optimized iPIN also includes zero. Retraining coverage and
checkpoint-selection limitations differ by method, especially RAPPPID's
partially trained recovery ensemble. The [benchmark index](benchmark/README.md)
links each result and its caveats. The expanded twelve-target application scores
37 nominated positives and 5,550 unlabeled pairs with the three historical iPIN models
and original published TUnA. Each positive has 50 context-matched, 50 background,
and 50 low-plausibility U. The [report](example/twelve_target_comparison_v2/REPORT.md)
compares all five requested candidate sets using PU concordance, AP/MAP, MRR,
positive ranks, recall, NDCG, enrichment, precision and target success at fixed
screening budgets, with fresh sequences and embeddings. Evidence tiers distinguish
1,711 compartment-separated additions from 139 weaker EGFR candidates; all remain
unlabeled. Exposure and evidence sensitivities accompany the results. Prior
six-target and twelve-target applications remain preserved historical records.

The [original TUnA investigation](example/original_tuna_investigation_v1/REPORT.md)
finds that EGFR accounts for most of its net example advantage over retrained
TUnA. Native scoring checks pass, and original TRAIN contains positive pairs
between sequence relatives of all three EGFR positives. This is a plausible
training-data explanation; the small example does not establish general superiority.

A separate [U score comparison](example/u_context_background_analysis_v1/REPORT.md)
finds modestly higher scores for context-matched than background candidates in
all three models, with target-specific results and exploratory uncertainty estimates.

The [non-human transfer study](benchmark/nonhuman_transfer_v1/REPORT.md) evaluates
the three unchanged models within mouse, fly, worm, budding yeast, Arabidopsis,
and E. coli K-12: 300 targets, 1,385 positive rows and 60,000 unlabeled rows.
It compares background and length/degree-matched candidate pools, with fresh
embeddings, original IntAct evidence validation, exact human-training exposure
checks, sequence-similarity strata, and complete retrieval metrics. Candidate
sets and evidence differ from human C3, so the two score scales do not directly
estimate a controlled species effect.

Concordance is neither binary binding accuracy nor calibrated interaction
probability. Genuine partner-specific/direct-binding generalization remains
unresolved. BioPlex AP-MS provides secondary cross-assay association evidence;
its frozen negative findings are retained in the [report index](docs/reports/README.md).

## Original pipeline and benchmark design

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

The later human data-scaling study preserves the original partitions and adds
eligible evidence/endpoints, producing nested training budgets up to 31,188 P
and a 17,583-sequence universe. It selects using C3 development and evaluates
both legacy and added cohorts. Test2 macro scores above are distinct from the
historical test scores; the [promotion report](docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md)
records the comparison and its limits.

The [Version 3 blueprint](docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md),
[frozen split decision](governance/decisions/DEC-0022-accept-final-benchmark-component-split.md),
[pair protocol](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md),
and [artifact report](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md)
record the scientific design. Numbered protocols, status files, and checkpoints
describe their original phase boundaries. The current four-model disposition is
[status v56](governance/PROJECT_STATUS_v56.md); benchmark and example
work is documented in its own directories.

## Repository layout

| Path | Purpose |
|---|---|
| `src/ipin_openppi/` | Evidence processing, benchmark construction, modeling, diagnostics, and validation |
| `scripts/` | Data, benchmark, model, analysis, and platform entry points |
| `tests/` | Synthetic unit, safety, validation, and model tests |
| `benchmark/` | Published-method implementations, execution records, aggregate comparisons, and dedicated containers |
| `example/` | Target panels, retrieval metrics and preserved historical applications |
| `experiments/` | Local scaling, selected-31k panel and test2 studies; promotion aggregates are preserved in the v3 release |
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
