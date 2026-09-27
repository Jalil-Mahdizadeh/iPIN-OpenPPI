# Expanded control evaluation

The frozen 31,188-P TUnA ensemble is compared with all eleven original fixed controls,
two train2-fitted additive endpoint controls, and three additional transfer kernels.
C3 is primary. These are follow-up results on previously examined development/test data.
U is unlabeled, and all intervals are pointwise 95% component-bootstrap intervals.

## Test2 macro scores

| Predictor | C1 | C2 | C3 |
|---|---:|---:|---:|
| selected_31k | 0.886903 | 0.827113 | 0.786652 |
| deterministic_hash | 0.500089 | 0.496857 | 0.494121 |
| training_degree_sum | 0.875255 | 0.771793 | 0.500000 |
| preferential_attachment | 0.874664 | 0.500000 | 0.500000 |
| component_degree_mass_product | 0.668617 | 0.500000 | 0.500000 |
| training_common_neighbors | 0.664953 | 0.500000 | 0.500000 |
| sequence_length_sum | 0.530026 | 0.470358 | 0.435530 |
| sequence_length_ratio | 0.539952 | 0.530342 | 0.555477 |
| within_pair_3mer_cosine | 0.554087 | 0.504617 | 0.548756 |
| exact_training_interolog_3mer | 0.635400 | 0.546692 | 0.518960 |
| pooled_150m_cosine | 0.563489 | 0.520095 | 0.544270 |
| aac_cosine | 0.561468 | 0.486915 | 0.498283 |
| interolog_pooled_150m | 0.683004 | 0.556623 | 0.490269 |
| interolog_alignment_local | 0.644444 | 0.527916 | 0.511379 |
| interolog_alignment_coverage | 0.644787 | 0.528017 | 0.511356 |
| endpoint_linear | 0.721541 | 0.718727 | 0.740487 |
| endpoint_mlp64 | 0.858397 | 0.781272 | 0.720991 |

## Primary C3 paired comparisons

| Control | Selected 31k minus control | Paired 95% interval |
|---|---:|---|
| deterministic_hash | +0.292531 | [+0.256273, +0.321586] |
| training_degree_sum | +0.286652 | [+0.256519, +0.309229] |
| preferential_attachment | +0.286652 | [+0.256519, +0.309229] |
| component_degree_mass_product | +0.286652 | [+0.256519, +0.309229] |
| training_common_neighbors | +0.286652 | [+0.256519, +0.309229] |
| sequence_length_sum | +0.351122 | [+0.258227, +0.415714] |
| sequence_length_ratio | +0.231175 | [+0.181432, +0.276134] |
| within_pair_3mer_cosine | +0.237896 | [+0.173975, +0.292856] |
| exact_training_interolog_3mer | +0.267692 | [+0.187670, +0.326979] |
| pooled_150m_cosine | +0.242382 | [+0.173401, +0.285413] |
| aac_cosine | +0.288368 | [+0.212544, +0.339536] |
| interolog_pooled_150m | +0.296383 | [+0.174403, +0.375448] |
| interolog_alignment_local | +0.275273 | [+0.245609, +0.296871] |
| interolog_alignment_coverage | +0.275296 | [+0.245689, +0.296889] |
| endpoint_linear | +0.046164 | [+0.021851, +0.075851] |
| endpoint_mlp64 | +0.065661 | [+0.030077, +0.106083] |

## Development2 macro scores

| Predictor | C1 | C2 | C3 |
|---|---:|---:|---:|
| selected_31k | 0.890167 | 0.839880 | 0.778918 |
| deterministic_hash | 0.497554 | 0.500526 | 0.493719 |
| training_degree_sum | 0.874835 | 0.797021 | 0.500000 |
| preferential_attachment | 0.874722 | 0.500000 | 0.500000 |
| component_degree_mass_product | 0.681386 | 0.500000 | 0.500000 |
| training_common_neighbors | 0.661822 | 0.500000 | 0.500000 |
| sequence_length_sum | 0.513166 | 0.531408 | 0.534625 |
| sequence_length_ratio | 0.539754 | 0.544487 | 0.600576 |
| within_pair_3mer_cosine | 0.542245 | 0.563180 | 0.610499 |
| exact_training_interolog_3mer | 0.632604 | 0.606780 | 0.620723 |
| pooled_150m_cosine | 0.578453 | 0.574407 | 0.630621 |
| aac_cosine | 0.566143 | 0.544477 | 0.566689 |
| interolog_pooled_150m | 0.698217 | 0.597338 | 0.549917 |
| interolog_alignment_local | 0.663924 | 0.548806 | 0.521819 |
| interolog_alignment_coverage | 0.664545 | 0.548808 | 0.521840 |
| endpoint_linear | 0.731519 | 0.734037 | 0.736402 |
| endpoint_mlp64 | 0.858644 | 0.793104 | 0.725048 |

The CSVs and RESULTS.json contain every interval, paired difference, both constituent
cohorts, and the C1 sensitivity excluding development-overlapping identities.
Reference test2 points and all 2,000 paired draws are replayed against the completed
frozen-competitor study. Development uses the same exact saved GP covariance policy.

The network and transfer controls use only the 31,188 train2 positive edges.
Pooled controls use the manuscript's raw windowed embeddings, not TUnA endpoint features.
Endpoint controls retain the historical architectures and fixed five-pass fitting recipe.
These comparisons do not capacity-match TUnA or establish physical binding specificity.
Separate C3 within-anchor and selected-quartet results are in diagnostics/.
