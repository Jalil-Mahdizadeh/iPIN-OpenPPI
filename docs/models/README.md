# Model registry

**iPIN-TUnA-31k is the primary/default iPIN predictor for human PPI ranking.**
The current catalogue is [Frozen pair models v3](FROZEN_PAIR_MODELS_v3.md),
authorized by [DEC-0056](../../governance/decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md).

| Predictor | Registry ID | Role |
|---|---|---|
| iPIN-TUnA-31k | `ipin_tuna_31k_ensemble` | Primary/default human model |
| Original iPIN | `lightweight_esm2_150m_linear__linear_lr3e-4` | Historical confirmatory reference |
| Optimized pooled iPIN | `esm2_150m__residual_wide__epoch04_ensemble3` | Historical pooled reference |
| TUnA-retrained / PU-TUnA, 17k | `tuna_retrained_ensemble` | Historical epoch-4 reference |

The primary model retains all three selected epoch-1 members trained on 31,188
positive pairs, exact saved GP covariance, and equal FP64 averaging of FP32
mean-field-adjusted logits. Its aliases are `iPIN-TUnA-31k`, `ipin-tuna-31k`
and the completed experiment ID `selected_31k`. The earlier `tuna-retrained`
and `ipin_tuna_retrained` aliases continue to identify the 17k epoch-4 ensemble.

The [machine-readable registry](../../artifacts/models/frozen_pair_models_v3/MODEL_REGISTRY.json)
records both primary/default pointers, checkpoint hashes, seed order, runtime,
architecture attribution, evidence and exact prediction definitions. Private
weights, endpoint identities and embeddings remain local. The published Bernett
TUnA architecture and iPIN PU adaptation retain explicit attribution.

The latest [15-predictor test2 follow-up](../reports/m1/M1_XPAIR_Test2_Comparison_v1.md)
adds released default and interaction-only X-PAIR to the original comparison.
Selected 31k leads all three macro scores; its C3 gain over default X-PAIR is
+0.044669 [0.012224, 0.075317], and the gain persists after exact-pair exposure
exclusion. X-PAIR has higher added-C3 point estimates, with exploratory paired
intervals including zero. These historically examined P/U results do not
establish universal superiority, independent replication or calibrated
interaction probabilities. X-PAIR remains an external comparator; the four
registered iPIN predictors and default pointer are unchanged.

The checksum-bound [promotion report](../reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md)
and v3 model card retain their original 13-predictor evidence and release scope.
The new experiment reports subsequent evidence separately, with all results
under [experiments/x_pair_test2_v1](../../experiments/x_pair_test2_v1/README.md).

The [v1](FROZEN_PAIR_MODELS_v1.md) and [v2](FROZEN_PAIR_MODELS_v2.md) cards,
registries and private bundles remain unchanged historical records. In v2,
historical TUnA's C3 difference from optimized pooled iPIN included zero; that
statement retains its original dataset/model scope. Original published TUnA
remains a comparator rather than a registered iPIN model.

The [selected-31k twelve-target report](../../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/REPORT.md)
adds the primary predictor to the unchanged 5,587-row panel. Exposure is explicit:
17/37 panel positives occur in 31k training P. Common exposure-excluded results
are reported separately. See the [panel index](../../example/INDEX.md).

The [six-organism transfer evaluation](../../benchmark/nonhuman_transfer_v1/REPORT.md)
applies the previous three models; it does not evaluate iPIN-TUnA-31k. Its
species-specific evidence and human-training exposure audits remain unchanged.
