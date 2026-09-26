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
- [Human PPI data scaling](human_ppi_data_scaling_v1/README.md): corpus
  construction, 12 completed fits, development selection and test1/test2
  comparisons. Read the [final review](human_ppi_data_scaling_v1/FINAL_REVIEW.md),
  [learning curves](human_ppi_data_scaling_v1/runs/results/learning_curves.png),
  and [publication scope](human_ppi_data_scaling_v1/PUBLICATION.md).
- [Original test2 competitor study](test2_frozen_competitors_v1/README.md):
  implementations and [completed 13-predictor comparison](test2_frozen_competitors_v1/results/RESULTS.md),
  retained as the reference for the subsequent X-PAIR comparison.
- [Selected 31k on the twelve-target panel](twelve_target_selected_31k_v1/README.md):
  [report](twelve_target_selected_31k_v1/output/REPORT.md), public pair scores,
  exposure audits, rank tables and comparison figures.
- [Default iPIN transfer comparison](default_ipin_transfer_comparison_v1/README.md):
  the 31k model on the existing six-species and human–laboratory-yeast panels.
  [Results](default_ipin_transfer_comparison_v1/REPORT.md) and
  [interpretation](default_ipin_transfer_comparison_v1/INTERPRETATION.md) accompany
  the full public score tables; large CSVs are
  [losslessly compressed](default_ipin_transfer_comparison_v1/PUBLICATION.md).

Historical benchmark implementations and their frozen results remain in
`../benchmark/`. Studies may consume those artifacts read-only.
All five studies have their implementation, protocol, compact execution
evidence, aggregate results and figures in Git. Protected human benchmark
records, weights, embeddings, environments and bulky generated intermediates
remain local. See the [repository deposit inventory](../DEPOSIT.md) for the
complete scope and verification instructions. Existing frozen release copies
remain unchanged.
