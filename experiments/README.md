# Experiments

Versioned research studies that include data construction, training, model
selection, and evaluation belong here. Each study keeps its own protocol,
provenance, generated inputs, and outputs.

- [Released X-PAIR on frozen test2](x_pair_test2_v1/README.md): completed
  comparison of two released checkpoints with the 13 existing predictors.
  Selected 31k leads C1/C2/C3 macro; X-PAIR's higher added-C3 point estimates
  have exploratory intervals spanning zero. See
  [interpretation](x_pair_test2_v1/results/INTERPRETATION.md),
  [full results](x_pair_test2_v1/results/RESULTS.md), and
  [publication and reproduction scope](x_pair_test2_v1/PUBLICATION.md).
- Human PPI data scaling, local workspace `human_ppi_data_scaling_v1/`:
  nested expansion of the positive-interaction corpus and a PU-TUnA learning
  curve. Its selected 31k predictor and published evidence are documented in
  the [promotion report](../docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md).
- Original test2 competitor study, local workspace `test2_frozen_competitors_v1/`:
  the [preserved 13-predictor report](../artifacts/models/frozen_pair_models_v3/evidence/test2/RESULTS.md)
  remains the reference for the subsequent X-PAIR comparison.
- Selected 31k on the twelve-target panel, local workspace
  `twelve_target_selected_31k_v1/`: [published report](../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/REPORT.md).

Historical benchmark implementations and their frozen results remain in
`../benchmark/`. Studies may consume those artifacts read-only.
Local execution workspaces can include uncommitted datasets, weights,
environments and intermediate outputs; a public checkout contains only the
explicitly published evidence and implementation files.
