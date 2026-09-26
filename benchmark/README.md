# Model benchmarks

The current primary/default human iPIN model is **iPIN-TUnA-31k**, registered
under [DEC-0056](../governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md)
in the [four-model catalogue](../docs/models/FROZEN_PAIR_MODELS_v3.md).

## Expanded test2 comparison, 26 September 2026

The [completed 15-predictor comparison](../experiments/x_pair_test2_v1/results/RESULTS.md)
covers all 3,774,966 rows in the expanded C1/C2/C3 test2 partitions. Its macro
metric gives equal weight to weighted P/U concordance on reconciled legacy and
added cohorts. These values have a different candidate/label scope from the
historical benchmark below.

| Predictor | C1 test2 macro | C2 test2 macro | C3 test2 macro |
|---|---:|---:|---:|
| **iPIN-TUnA-31k (primary)** | **0.886903** | **0.827113** | **0.786652** |
| Original iPIN | 0.744322 | 0.718876 | 0.726124 |
| Optimized pooled iPIN | 0.793734 | 0.750272 | 0.742563 |
| Historical PU-TUnA, 17k | 0.821205 | 0.772189 | 0.743871 |
| Released X-PAIR default multitask | 0.704050 | 0.693652 | 0.741983 |
| Released X-PAIR interaction-only | 0.701583 | 0.680655 | 0.733382 |

The primary model ranks first among all 15 predictors in each macro partition.
Its C3 gain over historical PU-TUnA is +0.042781 [0.019768, 0.070150]; the gain
over default X-PAIR is +0.044669 [0.012224, 0.075317]. All 14 paired C3
pointwise 95% intervals favor selected 31k and are unadjusted for multiplicity.
On added C3 alone, X-PAIR interaction-only/default score 0.783830/0.773173,
PLM-interact 0.767828, and selected 31k 0.740105. The exploratory X-PAIR-versus-31k
cohort intervals include zero. Test2 is a
historical follow-up; different training corpora and selection histories prevent
a controlled architecture comparison. See the
[X-PAIR comparison report](../docs/reports/m1/M1_XPAIR_Test2_Comparison_v1.md),
[original promotion report](../docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md), and
[X-PAIR paired contrasts](../experiments/x_pair_test2_v1/results/paired_differences.csv).
Original experiment data/results remain under `experiments/test2_frozen_competitors_v1/`;
aggregate release copies are byte-identical. The original TUnA architecture
retains attribution, and all earlier benchmark records remain unchanged.

X-PAIR uses the released default `multitask_xfair` and prespecified secondary
`interaction_xfair`, with newly computed full-length Ankh-large embeddings.
Both cover every candidate; no retraining or test-based checkpoint selection
occurred. The audit found 17,380 exact training/validation pair overlaps
(982 benchmark P, 16,398 U). Removing those pairs gives C3 macro 0.780593 for
selected 31k versus 0.725758 for default X-PAIR, paired gain
+0.054834 [0.019269, 0.087869]. Exact matching does not rule out homologs,
fragments or pretraining exposure. C1/C2/C3 remain defined relative to iPIN
training, not X-PAIR training. All new experiment artifacts remain under
`experiments/x_pair_test2_v1/`; the original 13-predictor release stays intact.

## Original benchmark, 20 September 2026

Historical aggregate results, checked against the completed local reports on
20 September 2026. These comparisons reuse the frozen iPIN C1/C2/C3 test panels
and reference predictions. Each predictor scored all 3,019,012 requested rows.
The metric is design-weighted positive-versus-unlabeled concordance; C3 is
primary. Unlabeled pairs are not verified negatives.

The completed epoch-4 PU-TUnA ensemble was registered as **the third frozen
iPIN model**, under its unchanged result ID `tuna_retrained_ensemble`. See the
[three-model catalogue](../docs/models/FROZEN_PAIR_MODELS_v2.md). This later
registration preserves the benchmark's weights, predictions, selection, and
results; the authors' original TUnA remains a separate comparator.

### Completed original-panel comparisons

The table below concerns the human C1/C2/C3 benchmark. A separate
[non-human transfer evaluation](nonhuman_transfer_v1/REPORT.md) applies all three
unchanged frozen iPIN ensembles within six organisms: 300 targets, 1,385 P rows,
and 60,000 U rows. It reports species-specific background/matched retrieval,
training-exposure and sequence-similarity sensitivities, and exploratory paired
target-bootstrap intervals. Its candidate design differs from human C3; it is
not an additional C1/C2/C3 test or a new model-selection step.

| Predictor | C1 | C2 | C3 | Result record |
|---|---:|---:|---:|---|
| Original iPIN affine ensemble | 0.843493 | 0.805299 | 0.789249 | [Frozen model cards](../docs/models/FROZEN_PAIR_MODELS_v1.md) |
| Optimized iPIN residual ensemble | 0.916037 | 0.851301 | 0.807948 | [Follow-up report](../docs/reports/m1/M1_Model_Optimization_Followup_v1.md) |
| Original TUnA | 0.716166 | 0.698193 | 0.695658 | [TUnA results](tuna/results/RESULTS.md) |
| PU-TUnA, three seeds, epoch 4 | 0.948619 | 0.880401 | 0.815875 | [TUnA results](tuna/results/RESULTS.md) |
| Original D-SCRIPT human_v1 | 0.462863 | 0.439297 | 0.498680 | [D-SCRIPT original results](dscript/results/original-v1/RESULTS.md) |
| PU-D-SCRIPT, three seeds, epoch 4 | 0.504429 | 0.481321 | 0.511437 | [D-SCRIPT retrained results](dscript/results/retrained-v1/RESULTS.md) |
| Original PLM-interact 650M humanV11 | 0.558772 | 0.532392 | 0.567018 | [PLM-interact results](plm_interact/results/original-v1/RESULTS.md) |
| Original RAPPPID released multiplicative head | 0.597417 | 0.600243 | 0.607067 | [RAPPPID original results](rapppid/results/original-v1/RESULTS.md) |
| PU-RAPPPID, three recovery checkpoints | 0.775316 | 0.729804 | 0.700049 | [RAPPPID recovery results](rapppid/results/retrained-v1/recovery-test-v1/RESULTS.md) |
| Native SPRINT with TRAIN-positive graph | 0.832588 | 0.666864 | 0.505227 | [SPRINT results](sprint/results/original-v1/RESULTS.md) |

The highest C3 point estimate here is PU-TUnA's 0.815875. Its difference from
optimized iPIN is +0.007927, with paired 95% interval [−0.028978, +0.038272],
which does not establish primary C3 superiority. Full score intervals, seed
results where applicable, and paired contrasts are in each result directory's
`scores.csv` and `paired_differences.csv`; the point estimates above are rounded.

## Predictor scope and limitations

- [X-PAIR](../experiments/x_pair_test2_v1/README.md): two released X-fair
  checkpoints, evaluated on expanded test2 on 26 September 2026 with no new
  training. Native inference, coverage, preservation and exact-pair exposure
  checks passed. [Interpretation](../experiments/x_pair_test2_v1/results/INTERPRETATION.md)
  distinguishes the combined metric from the added-C3 subgroup.
- [TUnA](tuna/README.md): released Bernett predictor and a separately identified
  three-seed PU adaptation, selected at epoch 4 using C3 development. Completed
  12 September 2026.
- [D-SCRIPT](dscript/README.md): released human_v1 and a three-seed PU adaptation,
  selected at epoch 4 using C3 development. Retrained evaluation completed
  18 September 2026. Member performance is heterogeneous, including one
  below-chance seed; all members remain reported. Evaluation uses full sequences
  with the qualified length-safe adapter.
- [PLM-interact](plm_interact/README.md): original 650M humanV11 evaluation
  completed 17 September 2026. No matched-data retrained result is available.
- [RAPPPID](rapppid/README.md): original and recovery-model evaluations completed
  17 September 2026. Training stopped during epoch 8. The user-selected recovery
  states have unequal progress within that epoch and were selected after an
  additional development look; they are not completed epoch-8 or 20-epoch models.
- [SPRINT](sprint/README.md): native algorithm using only the 16,799 frozen TRAIN
  positives, completed 17 September 2026. Neural-checkpoint retraining does not
  apply to this method.

Released models may have external interaction-training exposure. The retrained
adaptations have their own declared objectives and are not interchangeable with
the authors' original recipes. These are disclosed comparisons on previously
examined test panels, with pointwise paired component-bootstrap intervals.
They do not establish calibrated binding probabilities or universal biological
superiority. The [twelve-target example](../example/twelve_target_comparison_v1/REPORT.md)
is a separate descriptive application of all three frozen iPIN models using
freshly retrieved sequences and recomputed embeddings. Its 3,737 pairs have
known-positive retrieval metrics and exposure sensitivities. The original
[six-target comparison](../example/six_target_comparison_v1/REPORT.md) remains
unchanged, including its original-TUnA comparator.

The remaining candidate directories contain planning notes, not completed
evaluations. The [recommendation document](PUBLISHED_MODEL_BENCHMARK_RECOMMENDATIONS.md)
records the original plan. Historical startup reports retain their dated job
snapshots; their queued/running labels are not live execution status.

## Execution and provenance

Candidate code, configurations, logs, freezes, and aggregate results live with
each method. Shared dedicated images and build records live in `containers/`.
Downloads, embeddings, weights, private predictions, and images are local
execution assets excluded from Git. Original iPIN inputs and predictions are
read-only. Completed protected evaluations have single-use guards and must not
be resubmitted as ordinary reproduction commands.

The six repository-wide `repository-before*.json` inventories under
PLM-interact, RAPPPID, and SPRINT provenance have been pruned to retained project
paths during repository maintenance. They are partial historical inventories,
not fresh snapshots of the current checkout. Their associated historical scope
audits retain the original execution-time counts and outcomes; those counts
therefore exceed the retained inventory lengths. Predictor/data freezes,
prediction hashes, result files, and evaluation receipts are separate records.
