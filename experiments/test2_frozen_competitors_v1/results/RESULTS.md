# Frozen competitors on test2

Completed 2026-09-26T11:32:45.481450+00:00. All 13 frozen predictors cover all 3,774,966 requested candidate rows.

The primary score is the existing test2 macro: equal weight to weighted P-versus-U concordance in the reconciled legacy and added cohorts. C3 is primary. U is unlabeled, and test2 is a previously examined historical follow-up.

| Predictor | C1 test2 | C2 test2 | C3 test2 |
|---|---:|---:|---:|
| Selected 31k TUnA | 0.886903 | 0.827113 | 0.786652 |
| Original iPIN | 0.744322 | 0.718876 | 0.726124 |
| Optimized iPIN | 0.793734 | 0.750272 | 0.742563 |
| Frozen PU-TUnA (17k, epoch 4) | 0.821205 | 0.772189 | 0.743871 |
| Original TUnA | 0.681572 | 0.655440 | 0.678435 |
| Original D-SCRIPT | 0.540871 | 0.517678 | 0.566320 |
| PU-D-SCRIPT | 0.517491 | 0.494301 | 0.517715 |
| PLM-interact 650M humanV11 | 0.687722 | 0.646995 | 0.681772 |
| Original RAPPPID | 0.660427 | 0.645283 | 0.655007 |
| PU-RAPPPID recovery | 0.720019 | 0.687932 | 0.668772 |
| Native SPRINT (17k graph) | 0.736191 | 0.635095 | 0.562710 |
| Cross-attention ensemble | 0.816128 | 0.764781 | 0.739851 |
| Mean-pooling ensemble | 0.798878 | 0.747921 | 0.732231 |

## Paired C3 comparisons

Positive differences favor selected 31k. Intervals are pointwise and are not corrected for multiple comparisons.

| Reference | Selected 31k minus reference | Paired 95% interval |
|---|---:|---:|
| Original iPIN | +0.060528 | [+0.027164, +0.094832] |
| Optimized iPIN | +0.044088 | [+0.018689, +0.073923] |
| Frozen PU-TUnA (17k, epoch 4) | +0.042781 | [+0.019768, +0.070150] |
| Original TUnA | +0.108216 | [+0.072859, +0.138784] |
| Original D-SCRIPT | +0.220332 | [+0.170839, +0.266766] |
| PU-D-SCRIPT | +0.268937 | [+0.214479, +0.322201] |
| PLM-interact 650M humanV11 | +0.104879 | [+0.038655, +0.154796] |
| Original RAPPPID | +0.131644 | [+0.080296, +0.172053] |
| PU-RAPPPID recovery | +0.117879 | [+0.085258, +0.153627] |
| Native SPRINT (17k graph) | +0.223942 | [+0.102421, +0.308636] |
| Cross-attention ensemble | +0.046801 | [+0.024041, +0.070817] |
| Mean-pooling ensemble | +0.054420 | [+0.025848, +0.085936] |

## Reconciled legacy and added cohorts

| Cell / cohort | P | U | Predictor | Weighted P/U concordance |
|---|---:|---:|---|---:|
| C1 / reconciled_legacy | 3670 | 999517 | Original iPIN | 0.817226 |
| C1 / reconciled_legacy | 3670 | 999517 | Optimized iPIN | 0.886095 |
| C1 / reconciled_legacy | 3670 | 999517 | Selected 31k TUnA | 0.898637 |
| C1 / reconciled_legacy | 3670 | 999517 | Frozen PU-TUnA (17k, epoch 4) | 0.915954 |
| C1 / reconciled_legacy | 3670 | 999517 | Original TUnA | 0.706925 |
| C1 / reconciled_legacy | 3670 | 999517 | Original RAPPPID | 0.612270 |
| C1 / reconciled_legacy | 3670 | 999517 | PU-RAPPPID recovery | 0.759716 |
| C1 / reconciled_legacy | 3670 | 999517 | Cross-attention ensemble | 0.911677 |
| C1 / reconciled_legacy | 3670 | 999517 | Mean-pooling ensemble | 0.893395 |
| C1 / reconciled_legacy | 3670 | 999517 | PLM-interact 650M humanV11 | 0.589730 |
| C1 / reconciled_legacy | 3670 | 999517 | Original D-SCRIPT | 0.479058 |
| C1 / reconciled_legacy | 3670 | 999517 | PU-D-SCRIPT | 0.511297 |
| C1 / reconciled_legacy | 3670 | 999517 | Native SPRINT (17k graph) | 0.808472 |
| C1 / added | 645 | 250000 | Original iPIN | 0.671418 |
| C1 / added | 645 | 250000 | Optimized iPIN | 0.701373 |
| C1 / added | 645 | 250000 | Selected 31k TUnA | 0.875168 |
| C1 / added | 645 | 250000 | Frozen PU-TUnA (17k, epoch 4) | 0.726455 |
| C1 / added | 645 | 250000 | Original TUnA | 0.656219 |
| C1 / added | 645 | 250000 | Original RAPPPID | 0.708584 |
| C1 / added | 645 | 250000 | PU-RAPPPID recovery | 0.680321 |
| C1 / added | 645 | 250000 | Cross-attention ensemble | 0.720580 |
| C1 / added | 645 | 250000 | Mean-pooling ensemble | 0.704362 |
| C1 / added | 645 | 250000 | PLM-interact 650M humanV11 | 0.785715 |
| C1 / added | 645 | 250000 | Original D-SCRIPT | 0.602684 |
| C1 / added | 645 | 250000 | PU-D-SCRIPT | 0.523684 |
| C1 / added | 645 | 250000 | Native SPRINT (17k graph) | 0.663909 |
| C2 / reconciled_legacy | 13833 | 999613 | Original iPIN | 0.800423 |
| C2 / reconciled_legacy | 13833 | 999613 | Optimized iPIN | 0.845643 |
| C2 / reconciled_legacy | 13833 | 999613 | Selected 31k TUnA | 0.859017 |
| C2 / reconciled_legacy | 13833 | 999613 | Frozen PU-TUnA (17k, epoch 4) | 0.874597 |
| C2 / reconciled_legacy | 13833 | 999613 | Original TUnA | 0.695956 |
| C2 / reconciled_legacy | 13833 | 999613 | Original RAPPPID | 0.602980 |
| C2 / reconciled_legacy | 13833 | 999613 | PU-RAPPPID recovery | 0.727432 |
| C2 / reconciled_legacy | 13833 | 999613 | Cross-attention ensemble | 0.865716 |
| C2 / reconciled_legacy | 13833 | 999613 | Mean-pooling ensemble | 0.840713 |
| C2 / reconciled_legacy | 13833 | 999613 | PLM-interact 650M humanV11 | 0.539196 |
| C2 / reconciled_legacy | 13833 | 999613 | Original D-SCRIPT | 0.443557 |
| C2 / reconciled_legacy | 13833 | 999613 | PU-D-SCRIPT | 0.481445 |
| C2 / reconciled_legacy | 13833 | 999613 | Native SPRINT (17k graph) | 0.663301 |
| C2 / added | 4375 | 250000 | Original iPIN | 0.637329 |
| C2 / added | 4375 | 250000 | Optimized iPIN | 0.654900 |
| C2 / added | 4375 | 250000 | Selected 31k TUnA | 0.795208 |
| C2 / added | 4375 | 250000 | Frozen PU-TUnA (17k, epoch 4) | 0.669780 |
| C2 / added | 4375 | 250000 | Original TUnA | 0.614925 |
| C2 / added | 4375 | 250000 | Original RAPPPID | 0.687586 |
| C2 / added | 4375 | 250000 | PU-RAPPPID recovery | 0.648433 |
| C2 / added | 4375 | 250000 | Cross-attention ensemble | 0.663845 |
| C2 / added | 4375 | 250000 | Mean-pooling ensemble | 0.655130 |
| C2 / added | 4375 | 250000 | PLM-interact 650M humanV11 | 0.754794 |
| C2 / added | 4375 | 250000 | Original D-SCRIPT | 0.591799 |
| C2 / added | 4375 | 250000 | PU-D-SCRIPT | 0.507157 |
| C2 / added | 4375 | 250000 | Native SPRINT (17k graph) | 0.606890 |
| C3 / reconciled_legacy | 2757 | 999622 | Original iPIN | 0.775274 |
| C3 / reconciled_legacy | 2757 | 999622 | Optimized iPIN | 0.791534 |
| C3 / reconciled_legacy | 2757 | 999622 | Selected 31k TUnA | 0.833198 |
| C3 / reconciled_legacy | 2757 | 999622 | Frozen PU-TUnA (17k, epoch 4) | 0.801141 |
| C3 / reconciled_legacy | 2757 | 999622 | Original TUnA | 0.690597 |
| C3 / reconciled_legacy | 2757 | 999622 | Original RAPPPID | 0.621308 |
| C3 / reconciled_legacy | 2757 | 999622 | PU-RAPPPID recovery | 0.694380 |
| C3 / reconciled_legacy | 2757 | 999622 | Cross-attention ensemble | 0.786909 |
| C3 / reconciled_legacy | 2757 | 999622 | Mean-pooling ensemble | 0.770950 |
| C3 / reconciled_legacy | 2757 | 999622 | PLM-interact 650M humanV11 | 0.595717 |
| C3 / reconciled_legacy | 2757 | 999622 | Original D-SCRIPT | 0.516921 |
| C3 / reconciled_legacy | 2757 | 999622 | PU-D-SCRIPT | 0.508890 |
| C3 / reconciled_legacy | 2757 | 999622 | Native SPRINT (17k graph) | 0.516942 |
| C3 / added | 934 | 250000 | Original iPIN | 0.676974 |
| C3 / added | 934 | 250000 | Optimized iPIN | 0.693593 |
| C3 / added | 934 | 250000 | Selected 31k TUnA | 0.740105 |
| C3 / added | 934 | 250000 | Frozen PU-TUnA (17k, epoch 4) | 0.686601 |
| C3 / added | 934 | 250000 | Original TUnA | 0.666274 |
| C3 / added | 934 | 250000 | Original RAPPPID | 0.688707 |
| C3 / added | 934 | 250000 | PU-RAPPPID recovery | 0.643165 |
| C3 / added | 934 | 250000 | Cross-attention ensemble | 0.692792 |
| C3 / added | 934 | 250000 | Mean-pooling ensemble | 0.693512 |
| C3 / added | 934 | 250000 | PLM-interact 650M humanV11 | 0.767828 |
| C3 / added | 934 | 250000 | Original D-SCRIPT | 0.615719 |
| C3 / added | 934 | 250000 | PU-D-SCRIPT | 0.526539 |
| C3 / added | 934 | 250000 | Native SPRINT (17k graph) | 0.608478 |

## C1 sensitivity: remove development-overlapping candidate identities

| Predictor | C1 macro without development overlap |
|---|---:|
| Selected 31k TUnA | 0.887219 |
| Original iPIN | 0.745586 |
| Optimized iPIN | 0.795303 |
| Frozen PU-TUnA (17k, epoch 4) | 0.823093 |
| Original TUnA | 0.682334 |
| Original D-SCRIPT | 0.540328 |
| PU-D-SCRIPT | 0.517597 |
| PLM-interact 650M humanV11 | 0.686340 |
| Original RAPPPID | 0.659812 |
| PU-RAPPPID recovery | 0.721163 |
| Native SPRINT (17k graph) | 0.737839 |
| Cross-attention ensemble | 0.818112 |
| Mean-pooling ensemble | 0.800446 |

Removed 91,781 candidate rows only in this separate sensitivity view; the complete requested test2 panels remain unchanged.

## Scope and provenance

All predictors retain their existing weights, training graphs, selections, score definitions, and published length policies. Selected 31k is the fixed three-seed epoch-1 model. Competitor PU adaptations generally use the earlier 16,799-P corpus; this compares existing predictors and does not isolate architecture from training-data differences.

Unchanged legacy predictions were verified against their original manifests and aligned by exact endpoint-pair identity. Added pairs were scored with the frozen predictors after sequence-only feature extension. D-SCRIPT and PLM-interact retain their native score scales; no score inversion or calibration was applied. RAPPPID retains its declared singleton inference policy and recovery-checkpoint caveat.

Selected 31k and frozen PU-TUnA use the exact saved GP covariance, setting the unpersisted fitted flag before eval. This follows the completed scaling-study replay audit and may differ slightly from the earlier published reload-order results. SPRINT retains the same 16,799-P training graph but recomputes transductive HSP preprocessing on the expanded 17,583-sequence corpus, including all legacy scores.

The selected cross-attention and mean-pooling ensembles are included. Unpromoted development-only recipes and candidate methods that only have planning notes were not promoted or newly trained here. Released predictors may have external interaction-training exposure. C1 retains the previously disclosed shared-development-identity issue, reported separately above.

`scores.csv` contains macro scores and intervals, `paired_differences.csv` contains all paired contrasts, `cohort_scores.csv` contains the two constituent cohorts, and `member_scores.csv` reports individual seed point estimates. `PREDICTION_FREEZE.json` records complete finite prediction coverage before label-based evaluation. All source data and previous results remain read-only.
