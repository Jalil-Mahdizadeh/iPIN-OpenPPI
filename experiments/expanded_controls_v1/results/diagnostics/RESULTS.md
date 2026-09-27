# Direct C3 partner diagnostics

These analyses use the frozen 31k TUnA scores and train2 controls on the existing
dev2/test2 candidate panels. They do not reproduce the historical internal refits.
All alternative edges remain unlabeled. Intervals are paired pointwise 95% intervals.

## Test2 equal-cohort macro

| Predictor | Within-anchor concordance [95% CI] | Selected-quartet preference [95% CI] |
|---|---|---|
| selected_31k | 0.738896 [0.721325, 0.771727] | 0.755000 [0.678791, 0.816518] |
| deterministic_hash | 0.498424 [0.481337, 0.513899] | 0.490750 [0.429035, 0.555701] |
| training_degree_sum | 0.500000 [0.500000, 0.500000] | 0.500000 [0.500000, 0.500000] |
| preferential_attachment | 0.500000 [0.500000, 0.500000] | 0.500000 [0.500000, 0.500000] |
| component_degree_mass_product | 0.500000 [0.500000, 0.500000] | 0.500000 [0.500000, 0.500000] |
| training_common_neighbors | 0.500000 [0.500000, 0.500000] | 0.500000 [0.500000, 0.500000] |
| sequence_length_sum | 0.474305 [0.435945, 0.511806] | 0.500000 [0.500000, 0.500000] |
| sequence_length_ratio | 0.570047 [0.548932, 0.607157] | 0.575250 [0.514415, 0.632905] |
| within_pair_3mer_cosine | 0.576245 [0.551596, 0.624547] | 0.678000 [0.585939, 0.744546] |
| exact_training_interolog_3mer | 0.523470 [0.487470, 0.557698] | 0.592250 [0.517870, 0.656657] |
| pooled_150m_cosine | 0.599953 [0.578420, 0.649741] | 0.695000 [0.605907, 0.759205] |
| aac_cosine | 0.570322 [0.547489, 0.617551] | 0.677500 [0.576940, 0.745354] |
| interolog_pooled_150m | 0.542024 [0.507513, 0.586253] | 0.642250 [0.558519, 0.700000] |
| interolog_alignment_local | 0.512753 [0.505542, 0.524359] | 0.521250 [0.499716, 0.544712] |
| interolog_alignment_coverage | 0.512700 [0.505487, 0.524235] | 0.521375 [0.500378, 0.546291] |
| endpoint_linear | 0.665134 [0.639937, 0.688119] | 0.500000 [0.500000, 0.500000] |
| endpoint_mlp64 | 0.650359 [0.618358, 0.678443] | 0.500000 [0.500000, 0.500000] |

## Support

| Partition / cohort | Anchors | Anchor components | Quartets | Quartet components |
|---|---:|---:|---:|---:|
| development/legacy | 997 | 441 | 2000 | 411 |
| development/added | 630 | 332 | 1660 | 328 |
| test/legacy | 1076 | 626 | 2000 | 587 |
| test/added | 783 | 471 | 2000 | 450 |

Every model's cohort and macro results, paired differences, finite replicate counts,
support-floor flags and additive-control cancellation checks are recorded in RESULTS.json.
The reference scores use their native raw scale; nonlinear score transformations can
change quartet preferences even when ordinary ranking is unchanged.

Within-anchor means weight eligible anchors equally within each cohort.
Macro results weight the two cohort-specific metrics equally; they do not pool anchor
populations or claim independent cohorts. Quartets are a capped, deterministically
selected candidate-panel sample and have no full-population sampling-weight claim.
Sparse panels do not support inferential conclusions when the recorded floors fail.
