# iPIN-TUnA-31k primary-model designation

Date: 2026-09-26. Decision: [DEC-0056](../../../governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md).

**iPIN-TUnA-31k is the current primary/default iPIN predictor for human PPI ranking.** The preserved model is the already selected 31,188-P, epoch-1 three-seed ensemble. This report supports a project designation after completed studies; it performs no new model fitting, selection or evaluation.

## Complete test2 comparison

All 13 predictors cover all 3,774,966 C1/C2/C3 candidate rows. The macro score gives equal weight to design-weighted P/U concordance in the reconciled legacy and added cohorts. C3 is primary; C1/C2 are secondary. U is unlabeled. These are ranking scores, not binding accuracy or calibrated probabilities.

| Predictor | C1 test2 macro | C2 test2 macro | C3 test2 macro |
|---|---:|---:|---:|
| iPIN-TUnA-31k (primary) | 0.886903 | 0.827113 | 0.786652 |
| Historical PU-TUnA, 17k | 0.821205 | 0.772189 | 0.743871 |
| Optimized pooled iPIN | 0.793734 | 0.750272 | 0.742563 |
| Cross-attention ensemble | 0.816128 | 0.764781 | 0.739851 |
| Mean-pooling ensemble | 0.798878 | 0.747921 | 0.732231 |
| Original iPIN | 0.744322 | 0.718876 | 0.726124 |
| PLM-interact 650M humanV11 | 0.687722 | 0.646995 | 0.681772 |
| Original TUnA | 0.681572 | 0.655440 | 0.678435 |
| PU-RAPPPID recovery | 0.720019 | 0.687932 | 0.668772 |
| Original RAPPPID | 0.660427 | 0.645283 | 0.655007 |
| Original D-SCRIPT | 0.540871 | 0.517678 | 0.566320 |
| SPRINT, 17k training graph | 0.736191 | 0.635095 | 0.562710 |
| PU-D-SCRIPT | 0.517491 | 0.494301 | 0.517715 |

## Paired C3 evidence

Every paired C3 pointwise 95% interval favors the primary model. Each interval uses 2,000 common component-bootstrap draws; none is corrected for multiplicity. The primary model's own C3 interval is [0.756519, 0.809229].

| Reference | Primary minus reference | Paired 95% interval |
|---|---:|---|
| Historical PU-TUnA, 17k | +0.042781 | [+0.019768, +0.070150] |
| Optimized pooled iPIN | +0.044088 | [+0.018689, +0.073923] |
| Cross-attention ensemble | +0.046801 | [+0.024041, +0.070817] |
| Mean-pooling ensemble | +0.054420 | [+0.025848, +0.085936] |
| Original iPIN | +0.060528 | [+0.027164, +0.094832] |
| PLM-interact 650M humanV11 | +0.104879 | [+0.038655, +0.154796] |
| Original TUnA | +0.108216 | [+0.072859, +0.138784] |
| PU-RAPPPID recovery | +0.117879 | [+0.085258, +0.153627] |
| Original RAPPPID | +0.131644 | [+0.080296, +0.172053] |
| Original D-SCRIPT | +0.220332 | [+0.170839, +0.266766] |
| SPRINT, 17k training graph | +0.223942 | [+0.102421, +0.308636] |
| PU-D-SCRIPT | +0.268937 | [+0.214479, +0.322201] |

## Cohort differences and claim limits

Compared with historical 17k PU-TUnA, primary-model C3 improves on both the reconciled legacy cohort (0.801141 to 0.833198) and added cohort (0.686601 to 0.740105). However, PLM-interact scores higher on added C3 alone: **0.767828 versus 0.740105**. This is a numerical cohort-specific advantage; no separate uncertainty interval for that contrast was computed in this report. Historical PU-TUnA also scores higher on reconciled legacy C1/C2, despite losing the two-cohort macro comparison.

The separate C1 sensitivity removes 91,781 development-overlapping candidate identities. The primary model remains first at 0.887219. C2/C3 have no corresponding exact development/test candidate overlap in the expanded study.

Test2 and its added cohort are a disclosed historical follow-up, not independent replication. C3 describes interaction-training-naive endpoints under the frozen split, not absence from sequence pretraining or all homology. Released comparators may have external interaction-training exposure. PU adaptations generally retain the earlier training corpus and differ in checkpoint selection. This comparison identifies the best current predictor on the declared benchmark; it does not isolate architecture from training data, establish a performance ceiling, or prove direct binding or partner specificity.

## Supporting twelve-target application

On the unchanged 5,587-row human panel (37 P and 5,550 U), the primary model raises all-U macro concordance from historical PU-TUnA's 0.780305 to 0.864008. Eight of twelve targets improve; nominated positives retrieved at ten candidates per target increase from 7/37 to 10/37. Original published TUnA remains higher on some retrieval metrics, including full-panel MAP/MRR.

Seventeen of the 37 panel positives occur in 31k training P. The common exposure-excluded sensitivity retains nine targets and 16 P; concordance is 0.859993 versus 0.764762 for historical PU-TUnA, with 5 versus 2 positives retrieved at ten candidates per target. These are descriptive applications with different subset coverage, not independent confirmation.

See the [preserved panel report](../../../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/REPORT.md), [validation](../../../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/VALIDATION.json), and [exposure census](../../../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/EXPOSURE_AUDIT.json).

## Reproducibility and preservation

The model retains the exact saved GP covariance. Its fitted flag is set before evaluation mode. The initial scaling report used a reload order that caused small numerical drift; the later replay audit and this test2 comparison preserve the saved covariance. Original reports remain unchanged, and this promotion uses the completed corrected comparison.

Native-scoring checks, finite candidate coverage, ensemble arithmetic and the paired metric oracle passed. The completed comparison verified that all 271 original source inputs were unchanged. Promotion adds a fourth registry entry and a byte-identical local preservation bundle, while preserving the prior three model definitions. Published Bernett TUnA architecture attribution and licenses remain explicit.

Public evidence: [full original comparison report](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/RESULTS.md), [machine-readable results](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/results.json), [scores and intervals](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/scores.csv), [paired contrasts](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/paired_differences.csv), [cohort scores](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/cohort_scores.csv), [C3 figure](../../../artifacts/models/frozen_pair_models_v3/evidence/test2/C3_comparison.png), [development selection](../../../artifacts/models/frozen_pair_models_v3/evidence/scaling/selection.json), and [covariance replay audit](../../../artifacts/models/frozen_pair_models_v3/evidence/scaling/covariance_replay.json). These are unchanged copies of aggregate outputs from `experiments/`; model weights, embeddings and pair-level data remain local.

The [v3 model card](../../models/FROZEN_PAIR_MODELS_v3.md), [registry](../../../artifacts/models/frozen_pair_models_v3/MODEL_REGISTRY.json) and [freeze audit](../../../artifacts/validation/frozen_pair_models_v3/FREEZE_AUDIT.json) define the exact primary prediction unit.
