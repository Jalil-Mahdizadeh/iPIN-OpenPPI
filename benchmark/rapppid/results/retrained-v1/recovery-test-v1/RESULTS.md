# RAPPPID latest recovery checkpoints: C1/C2/C3 test

Completed: 2026-09-17T18:15:15.280704+00:00. All three user-selected mid-epoch-8 recovery checkpoints; no training restart.

Metric: design-weighted positive-versus-unlabeled concordance (higher is better). U is not confirmed negative.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| rapppid_recovery_mean_logit | 0.775316 | 0.729804 | 0.700049 |
| rapppid_recovery_seed_20260803 | 0.743063 | 0.705840 | 0.663315 |
| rapppid_recovery_seed_20260817 | 0.719083 | 0.701415 | 0.674414 |
| rapppid_recovery_seed_20260831 | 0.794204 | 0.718401 | 0.663223 |
| rapppid_original_released_mult | 0.597417 | 0.600243 | 0.607067 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary candidate: FP64 mean of all three native pre-sigmoid logits. All three seed results are also reported, with no seed selection based on test scores.

Primary panel: C3; C1/C2 and individual seeds are secondary descriptive comparisons. The 95% percentile intervals and paired differences use the same 2,000 two-endpoint component-bootstrap draws as the previous iPIN/original RAPPPID evaluation. These are pointwise, not multiplicity-adjusted intervals.

These snapshots each completed seven epochs plus 75.142%, 78.896% and 77.824% of epoch 8 (seeds 20260803, 20260817 and 20260831). They are not completed epoch-8 or completed 20-epoch models. The user selected them after an additional C3-development look and chose not to restart failed job 2578434. No additional training, repair, averaging of weights, fitting or test-dependent scorer changes were applied.

Native singleton endpoint encoding and singleton head moments; deterministic TRAIN-fitted 250-piece SentencePiece; first 1,500 residues per endpoint; FP32 model with AMP/TF32 disabled. The three-seed ensemble uses FP64 mean logits, not mean probabilities. Native source and learned state are unchanged. The matched-data model is PU-RAPPPID-mult, not an exact reproduction of the paper training recipe.

All 3,019,012 test pairs have finite scores for every seed and the ensemble. Long sequences are truncated, not excluded; see coverage.csv. Candidate-only inference and complete prediction freezing preceded truth access. Original RAPPPID and both iPIN prediction files were reused byte-for-byte; their point estimates and historical component-draw definitions were reproduced.

These panels were previously examined by other benchmark evaluations and are not a newly untouched holdout. Original RAPPPID has possible external PPI-training exposure; the retrained model was fitted on TRAIN only.

Files: scores.csv (all scores and intervals), paired_differences.csv (every candidate versus the three references), coverage.csv, RESULTS.json. Pair-level token-keyed logits remain in ../../../private/recovery-test-v1/predictions/. All artifacts are benchmark-local.
