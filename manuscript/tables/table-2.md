**Table 2 | Final model specifications**

| Property | Original affine | Optimized residual |
| --- | --- | --- |
| Frozen encoder | ESM-2 150M | ESM-2 150M |
| Head parameters per member | 1,922 | 498,053 |
| Ensemble members | 3 | 3 |
| Hidden width | — | 256 |
| Training dropout | 0.0 | 0.3 |
| Initial learning rate | 3e-04 | 1e-04 |
| Weight decay | 0.0001 | 0.01 |
| Comparisons per batch | 4,096 | 8,192 |
| Selected pass / epoch | 5 | 4 |
| Scheduled passes / epochs | 5 | 8 |

Both models use the same 640-dimensional standardized embeddings and 1,921-dimensional symmetric pair features. Optimization changes the training recipe as well as the head. The optimized epoch-four checkpoint comes from an eight-epoch schedule.
