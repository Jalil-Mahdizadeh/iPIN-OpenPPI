# RAPPPID latest recovery checkpoints: C3 development

Full panel: 2,265 observed positives + 1,000,000 unlabeled pairs. Higher weighted P-versus-U concordance is better.

| Model | Saved position | C3-dev | Epoch 4 | Change |
|---|---|---:|---:|---:|
| seed_20260803 | 7 full epochs + 75.142% of epoch 8 | 0.679389 | 0.622185 | +0.057204 |
| seed_20260817 | 7 full epochs + 78.896% of epoch 8 | 0.668486 | 0.670013 | -0.001527 |
| seed_20260831 | 7 full epochs + 77.824% of epoch 8 | 0.656541 | 0.672436 | -0.015895 |
| three_seed_mean_logit | Mean logits of the three unequal-position snapshots | 0.699429 | 0.692744 | +0.006684 |

These are the latest valid saved recovery states from failed job 2578434, not completed epoch-8 checkpoints. This is an additional user-requested development look, separate from the scheduled epoch 4/8/12/16/20 comparisons.

The original frozen singleton scorer, deterministic TRAIN-fitted tokenizer, 1,500-residue prefix policy and full-panel weighted metric were reused. All rows scored finitely; native-head/reversal checks and two independent weighted-ranking checks (tolerance 1e-9 for million-row summation roundoff) passed.

Training checkpoints, frozen code, previous development reports and test artifacts were not modified. No training, numerical repair, checkpoint selection or test evaluation was performed.

Evaluation time: 18.17 seconds, excluding snapshot creation, image verification and container startup. Allocation: 2598385 on NVIDIA GH200 120GB.

First attempt stopped before latest-checkpoint scoring: equivalent full-panel metric algorithms differed by 1.4264e-11 on the existing epoch-4 result. Verification tolerance is 1e-9 for million-row FP64 summation order; the historical scoring function is unchanged.

Files: `scores.csv`, `RESULTS.json`, per-seed/ensemble NPY predictions, `EVALUATION_FREEZE.json`, copied checkpoint snapshots and wrapper code. NPY rows follow the unchanged `development_00.npz` order.
