# PLM-interact benchmark

Status at 18:27 CEST, 16 September 2026: the dedicated SIF is built and qualified. The original **650M humanV11** C1/C2/C3 benchmark is running as Slurm job **2555430** on **n538**, with four GH200 GPUs. Expected completion: approximately **03:30–06:30 CEST, 17 September** (9–12 hours from job start; 72-hour safety limit). No performance results are available yet and no retraining is scheduled. See the [execution report](REPORT.md) for qualification evidence, frozen input policies and timing.

On successful completion, `results/original-v1/RESULTS.md`, `scores.csv`, `paired_differences.csv` and `coverage.csv` will report original PLM-interact against the frozen baseline and optimized iPIN predictions on the identical test cells.

Upstream: [official repository](https://github.com/liudan111/PLM-interact).

Required comparison: authors' original released predictor and a separately identified predictor retrained on iPIN TRAIN, each evaluated on the identical C1/C2/C3 test cells against the frozen baseline and optimized iPIN ensembles. Development data alone determine retraining choices. Original-checkpoint interaction exposure is disclosed; an original training objective is not an original pretrained model.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.
