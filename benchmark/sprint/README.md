# SPRINT benchmark

Status, 2026-09-17: dedicated native SIF built and qualified. Full HSP preprocessing
is running as job `2600174`; automatic C1/C2/C3 evaluation is submitted as dependent
job `2600175`. See [REPORT.md](REPORT.md) for timing, methods and artifact locations.

Upstream: [official repository](https://github.com/lucian-ilie/SPRINT).

Comparison: original unmodified SPRINT algorithm supplied with only the 16,799
frozen iPIN TRAIN-positive interactions, against baseline and optimized iPIN on
the identical C1/C2/C3 panels. There is no neural pretrained checkpoint or separate
epoch-based retraining run. No external interaction graph or held-out PPI labels
are used by SPRINT.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

SPRINT has no learned neural checkpoint to retrain. Record this distinction; compare the original algorithm configured with the permitted TRAIN-positive graph, and only add an alternative graph/parameter configuration if its information source and development selection are explicitly defined. Do not fabricate an original-versus-retrained neural comparison.

On completion, aggregate results land in `results/original-v1/`; protected
token-aligned predictions remain in `private/original-v1/`. The success marker is
`runs/original-v1/RUN_COMPLETE.json`. The pipeline is deliberately single-use:
do not resubmit it or repeat a completed test evaluation.
