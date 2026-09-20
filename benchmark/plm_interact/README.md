# PLM-interact benchmark

Status: **original 650M humanV11 evaluation completed on 17 September 2026**.
C1/C2/C3 concordance is **0.558772 / 0.532392 / 0.567018**, with complete finite
coverage. No matched-data retraining was performed. See the
[completed results](results/original-v1/RESULTS.md), the
[cross-method index](../README.md), and the [execution report](REPORT.md) for
qualification evidence, frozen input policies, and historical startup timing.

Completed outputs in `results/original-v1/` include `RESULTS.md`, `scores.csv`,
`paired_differences.csv`, and `coverage.csv`, comparing original PLM-interact
against the frozen baseline and optimized iPIN predictions on identical cells.

Upstream: [official repository](https://github.com/liudan111/PLM-interact).

Completed scope: the authors' original released predictor against both frozen
iPIN ensembles. The broader benchmark plan's retrained comparison remains
unperformed for this method. Original-checkpoint interaction exposure is
disclosed in the execution and result records.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.
