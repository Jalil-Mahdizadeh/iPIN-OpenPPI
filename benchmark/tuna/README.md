# TUnA benchmark

Status at 12 September 2026 startup: qualified; three-seed training running as Slurm job `2325231`; automatic final comparison queued as `2326461` with an `afterok` dependency. See [REPORT.md](REPORT.md) for the scientific protocol, measured feasibility, caveats, and operational history. This is not yet a completed test-performance result.

Upstream: [official repository](https://github.com/Wang-lab-UCSD/TUnA).

Required comparison: authors' original released predictor and a separately identified predictor retrained on iPIN TRAIN, each evaluated on the identical C1/C2/C3 test cells against the frozen baseline and optimized iPIN ensembles. Development data alone determine retraining choices. Original-checkpoint interaction exposure is disclosed; an original training objective is not an original pretrained model.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.

The dedicated image is `../containers/images/tuna-arm64-v1.sif`. Entry points are [run.sh](run.sh), [train_seeds.sbatch](train_seeds.sbatch), and [final.sh](final.sh). Do not resubmit them while the recorded jobs are active. The final pipeline refuses changed frozen code, incomplete training, overwritten predictions, or a repeated truth-access reservation.

After successful completion, aggregate outputs will be `results/scores.csv`, `results/paired_differences.csv`, `results/RESULTS.json`, and `results/RESULTS.md`. Protected per-pair predictions remain under ignored `private/`; they are not included in the public aggregate CSVs.
