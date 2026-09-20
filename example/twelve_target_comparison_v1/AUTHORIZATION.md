# Application-extension scope

Date: 2026-09-20. This application follows the three-model preservation decision
[DEC-0055](../../governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md).

The user requested:

> i want you to double the size of example from 6 to 12, apply all three frozen ipin models, calculate all metrics you mentioned + PU concordance, update all files and docs. ask questions if clarifications needed.

When asked whether to nominate the new genes, the user selected:

> Select six diverse human targets using the existing panel design (Recommended)

This authorizes six additional biological panels, inference with the unchanged
three registered predictors, the previously discussed retrieval metrics, and
corresponding code, results, figures, and documentation. The added targets and
partners are recorded in [panel_config.json](panel_config.json), selected without
model scores. The [metric protocol](METRICS.md) and code identities were recorded
in [INPUT_FREEZE.json](INPUT_FREEZE.json) before inference.

The original six targets remain intact. Each addition has three positives and
300 U, yielding twelve targets and 3,737 pairs; target count is doubled, while
the original ERN1 panel retains its fourth positive. All three models are applied
to every pair with freshly recomputed embeddings. Original TUnA remains a
comparator in the preserved historical six-target result.

This work does not change the frozen benchmark, its primary metric/split,
model definitions, TRAIN normalization, selected checkpoints, GP buffers,
protected-test custody, or spent evaluation ledgers. The application is a
versioned descriptive extension, with explicit TRAIN/development exposure and
homomer sensitivities. It does not assert statistical superiority, calibrated
interaction probability, or experimentally verified noninteraction for U.
