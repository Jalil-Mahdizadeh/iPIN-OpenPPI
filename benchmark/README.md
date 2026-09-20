# Published-model benchmarks

Current aggregate results, checked against the completed local reports on
20 September 2026. These comparisons reuse the frozen iPIN C1/C2/C3 test panels
and reference predictions. Each predictor scored all 3,019,012 requested rows.
The metric is design-weighted positive-versus-unlabeled concordance; C3 is
primary. Unlabeled pairs are not verified negatives.

## Completed comparisons

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
superiority. The [six-target example](../example/six_target_comparison_v1/REPORT.md)
is a separate descriptive application using freshly retrieved sequences.

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
