# SPRINT benchmark

Status: **native SPRINT C1/C2/C3 evaluation completed on 17 September 2026**.
Concordance is **0.832588 / 0.666864 / 0.505227**, with complete finite coverage.
See the [completed results](results/original-v1/RESULTS.md), the
[cross-method index](../README.md), and [REPORT.md](REPORT.md) for methods and
historical preprocessing/job timing.

Upstream: [official repository](https://github.com/lucian-ilie/SPRINT).

Comparison: original unmodified SPRINT algorithm supplied with only the 16,799
frozen iPIN TRAIN-positive interactions, against baseline and optimized iPIN on
the identical C1/C2/C3 panels. There is no neural pretrained checkpoint or separate
epoch-based retraining run. No external interaction graph or held-out PPI labels
are used by SPRINT.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

SPRINT has no learned neural checkpoint to retrain. Record this distinction; compare the original algorithm configured with the permitted TRAIN-positive graph, and only add an alternative graph/parameter configuration if its information source and development selection are explicitly defined. Do not fabricate an original-versus-retrained neural comparison.

Completed aggregate results are in `results/original-v1/`; protected
token-aligned predictions remain in `private/original-v1/`. The success marker is
`runs/original-v1/RUN_COMPLETE.json`. The pipeline is deliberately single-use:
do not resubmit it or repeat a completed test evaluation.
