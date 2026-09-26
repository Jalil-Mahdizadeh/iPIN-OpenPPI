# TUnA benchmark

The current primary/default human iPIN model is **iPIN-TUnA-31k**, the selected
31,188-P epoch-1 ensemble from the later scaling study. Its
[v3 model card](../../docs/models/FROZEN_PAIR_MODELS_v3.md) and
[promotion report](../../docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md)
record the exact predictor, test2 comparison and limitations. This directory
preserves the earlier original/17k-retrained benchmark unchanged.

The later [X-PAIR test2 follow-up](../../docs/reports/m1/M1_XPAIR_Test2_Comparison_v1.md)
retains selected 31k's lead on the three combined test2 metrics. X-PAIR's higher
added-C3 point estimates have exploratory intervals spanning zero. Its outputs
are in `experiments/x_pair_test2_v1/`; this historical TUnA benchmark keeps its
original dataset, checkpoint selection and results.

The completed retrained predictor is **iPIN model 3, TUnA-retrained (PU-TUnA)**,
frozen under [DEC-0055](../../governance/decisions/DEC-0055-freeze-tuna-retrained-as-third-ipin-model.md).
The [v2 model catalogue](../../docs/models/FROZEN_PAIR_MODELS_v2.md) preserves its
epoch-4 three-seed states and exact prediction definition. The benchmark's
original selection and result records are unchanged.

Status: **original and retrained C1/C2/C3 comparisons completed on 12 September
2026**. The C3-development-selected retrained ensemble uses all three seeds at
epoch 4. Its C1/C2/C3 concordance is **0.948619 / 0.880401 / 0.815875**; original
TUnA scores **0.716166 / 0.698193 / 0.695658**. See the
[completed results](results/RESULTS.md) and [paired intervals](results/paired_differences.csv).
The primary retrained-versus-optimized-iPIN C3 interval includes zero.
[REPORT.md](REPORT.md) preserves the protocol, qualification, and startup history.

Upstream: [official repository](https://github.com/Wang-lab-UCSD/TUnA).

Required comparison: authors' original released predictor and a separately identified predictor retrained on iPIN TRAIN, each evaluated on the identical C1/C2/C3 test cells against the frozen baseline and optimized iPIN ensembles. Development data alone determine retraining choices. Original-checkpoint interaction exposure is disclosed; an original training objective is not an original pretrained model.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.

The dedicated image is `../containers/images/tuna-arm64-v1.sif`. Entry points are [run.sh](run.sh), [train_seeds.sbatch](train_seeds.sbatch), and [final.sh](final.sh). The evaluation is completed and its truth-access reservation is spent. The final pipeline refuses changed frozen code, incomplete training, overwritten predictions, or a repeated truth-access reservation.

Completed aggregate outputs are `results/scores.csv`, `results/paired_differences.csv`, `results/RESULTS.json`, and `results/RESULTS.md`. Protected per-pair predictions remain under ignored `private/`; they are not included in the public aggregate CSVs. See the [cross-method index](../README.md) for the other completed comparisons.
