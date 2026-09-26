# Completed human PPI expansion review

Reviewed September 26, 2026. All 12 eight-epoch fits and the final evaluation
completed successfully. The training jobs took 7h15m–7h44m each. Final job
2979722 completed in 9m45s, at 11:04:35 Stockholm time. The entire submitted
workflow took approximately 23h12m.

**The expansion improved ranking on the added evaluation cohorts, but did not
produce a model that improved every original benchmark. Its combined C3-test2
advantage over the fresh 17k control remains uncertain.** This iteration is
complete; this review does not initiate further training or change the selected
model.

## Selection and learning curves

The frozen selection rule chose a three-seed ensemble with **31,188 training
positives at epoch 1**. The fresh 16,799-P control also selected epoch 1.
Selection used the equal-weight mean of concordance on the reconciled original
C3-dev cohort and the added C3-dev cohort. It did not pool their candidate rows.

These are the recorded selection-time scores; each row uses its selected common
epoch across all three seeds:

| Training P | Selected epoch | Original C3-dev1 | Reconciled original | Added C3-dev | C3-dev2 macro |
|---|---:|---:|---:|---:|---:|
| 16,799 | 1 | 0.826704 | 0.807777 | 0.682996 | 0.745386 |
| 20,000 | 6 | 0.823229 | 0.807920 | 0.713618 | 0.760769 |
| 25,000 | 2 | 0.834335 | 0.820093 | 0.729379 | 0.774736 |
| 31,188 | 1 | 0.824425 | 0.813156 | 0.744679 | 0.778918 |

Added-cohort and macro scores rise across these selected budgets; original-dev1
scores do not rise monotonically. This is evidence that source and population
coverage matter, rather than evidence of a volume-only effect.

Three budgets select epochs 1 or 2. However, the 20k ensemble recovers after its
epoch-2 decline and peaks at epoch 6. Thus its first decline did not establish
permanent saturation. The mean training loss decreases from epoch 1 to epoch 8
at every budget, while the development objective is lower at epoch 8 than its
selected maximum. Better training fit did not consistently improve transfer.

The new 17k run's original C3-dev1 score actually peaks at epoch 4 (0.837611).
The historical 17k model at epoch 4 scored 0.804456 on that same panel. Earlier
checkpoint availability alone therefore cannot explain the entire dev1
improvement. The changed U/background recipe remains a confound.

Each epoch contains 2 million P-versus-U comparisons and 31,250 optimizer
updates. Mean positive-pair reuse per epoch is approximately 119, 100, 80 and 64
at the four budgets, respectively. One epoch is already substantial training.

## Original test panels

All values below are weighted P-versus-U concordance, not binary-classification
accuracy or calibrated interaction probability. These are the original frozen
test1 candidate identities, labels and weights.

| Cell | Original iPIN | Optimized iPIN | Frozen PU-TUnA | Fresh 17k control | Selected 31k |
|---|---:|---:|---:|---:|---:|
| C1 | 0.843493 | 0.916037 | **0.948620** | 0.924111 | 0.900615 |
| C2 | 0.805299 | 0.851301 | 0.880401 | **0.885417** | 0.860617 |
| C3 | 0.789249 | 0.807948 | 0.815875 | **0.867272** | 0.844384 |

The selected 31k model is below the fresh control on all original cells. Its
paired differences, selected minus fresh control, are:

| Cell | Difference | Paired component-bootstrap 95% interval |
|---|---:|---:|
| C1 | -0.023496 | [-0.029749, -0.015859] |
| C2 | -0.024800 | [-0.037370, -0.013789] |
| C3 | -0.022888 | [-0.050365, -0.003243] |

Relative to frozen PU-TUnA, the selected model improves original C3 but loses
original C1 and C2. The fresh 17k control improves original C3 by 0.051397
over frozen PU-TUnA, with paired interval [0.022099, 0.102310]. That comparison
does not measure an increase in positive count: both use the original 16,799 P.
It combines the changed U/background recipe and checkpoint-selection changes.

## Added and expanded test panels

| Added test cohort | Frozen PU-TUnA | Fresh 17k control | Selected 31k | Selected minus control | Paired 95% interval |
|---|---:|---:|---:|---:|---:|
| C1 | 0.726456 | 0.712128 | 0.875191 | +0.163063 | [0.129415, 0.199241] |
| C2 | 0.669781 | 0.672003 | 0.795270 | +0.123266 | [0.098573, 0.147746] |
| C3 | 0.686601 | 0.693900 | 0.740192 | +0.046292 | [0.020885, 0.076241] |

The selected model also has higher point estimates than both other frozen iPIN
models on every added cohort. These gains support improved coverage of the
added evaluation population within this study.

| Test2 macro | Frozen PU-TUnA | Fresh 17k control | Selected 31k | Selected minus control | Paired 95% interval |
|---|---:|---:|---:|---:|---:|
| C1 | 0.821205 | 0.802568 | 0.886915 | +0.084347 | [0.065984, 0.103703] |
| C2 | 0.772189 | 0.775817 | 0.827151 | +0.051333 | [0.038097, 0.065345] |
| C3 | 0.743871 | 0.770085 | 0.786724 | +0.016639 | **[-0.001754, 0.034846]** |

Test2 macro gives 50% weight to the reconciled original cohort and 50% to the
added cohort. The C3 interval includes zero: the combined C3 improvement over
the fresh control is not established at this interval level, even though its
added-cohort improvement is clearer. Intervals are conditional component
bootstrap intervals; they do not represent independent study replication or
uncertainty across alternative corpus samples.

## Interpretation limits retained from the audit

- All original endpoint assignments were anchored, and training pair identities
  were excluded from all held-out candidate panels. C2/C3 endpoint separation
  passed the declared checks. Homology separation remains based on a heuristic
  similarity graph, not a guarantee of unseen biological families.
- Reconciled C1 violates some original positive-assignment semantics: 445 dev
  and 404 test promoted positives conflict with the original positive hash role;
  57 promoted positives are shared between dev and test. The additional C1
  test2 view excluding all development identities gives 0.887232 for selected
  versus 0.804448 for the control, but does not repair every hash-role conflict.
  Original test1 and added-only views should be distinguished from that full
  reconciled C1 population.
- Every new fit uses the same regenerated U sample, which draws from all TRAIN
  endpoints. The original recipe restricted U to training-positive-exposed
  endpoints. The current 17k control therefore controls the new learning curve,
  not an exact replication of the historical training recipe.
- Protein-family balancing was not implemented. Added evidence changes source
  composition, coverage and redundancy as well as P count. The 31,188 maximum
  is for the frozen local-source policy; it is not a maximum attainable corpus
  or a model performance ceiling.
- Test1 was historically inspected and test2 incorporates it by design. This is
  a historical follow-up, not independent replication.
- Only the selected model and fresh control, plus frozen references, were scored
  on test. Other budget checkpoints have development comparisons; this review
  does not select another model after examining test results.

## Completion and numerical review

The execution freeze passes. Eleven historical parent artifact hashes remain
unchanged. The review checked all 60 epoch checkpoint hashes, all 60 saved
checkpoint-prediction hashes, 30 frozen scorer artifacts, and 12 final prediction
files. Sixty main test metric points and 81 development metric points reproduce
exactly from the saved final predictions. All 65 bootstrap model summaries and
their stored paired intervals reproduce from the saved draws.

One scorer-replay discrepancy was found. The final loader calls `model.eval()`
before setting `gp_layer.fitted=True`. The native GP implementation then replaces
the loaded covariance with a float32 pseudoinverse of the saved precision.
Training-time checkpoint evaluation used the saved covariance computed through
the qualified float64 Cholesky path. This changes final scores slightly.

A separate post-completion inference audit set the fitted flag before eval,
retained the exact saved covariance, and replayed the selected model, fresh
control and frozen PU-TUnA. It performed no training or model reselection.
Selection-time C3 metrics reproduce within about 1.2e-9. Across original,
reconciled, added and macro C1/C2/C3 test point estimates, the largest change
from the published output is **0.000292**. The principal point-estimate
comparisons retain their directions. The selected/control C3-test2 scores in
that audit are 0.786652/0.769830, versus published 0.786724/0.770085.

The published results and bootstrap intervals are retained unchanged; replay
point estimates are diagnostic and are not substituted into those intervals.
The loader-order issue should be corrected in any future scorer release. It
does not require retraining these checkpoints.

## Artifacts

- [Full generated model comparison](runs/results/RESULTS.md)
- [Machine-readable results and paired intervals](runs/results/RESULTS.json)
- [Selection record and every evaluated epoch](runs/SELECTION.json)
- [Learning curves](runs/results/learning_curves.png)
- [Completion review record](audit/COMPLETED_REVIEW.json)
- [Covariance replay review and embedded reproduction script](audit/SCORER_REPLAY_REVIEW.json)

The supported outcome is a population-dependent improvement: expanded training
helps the added cohorts while sacrificing some original-panel performance.
There is no uniformly superior replacement and no demonstrated performance
ceiling. Those conclusions close this iteration without initiating another
experiment.
