# Original RAPPPID benchmark results

Completed: 2026-09-17T06:28:30.407927+00:00. Authors’ released red-dreamy multiplicative-head checkpoint; no retraining.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| rapppid_original_released_mult | 0.597417 | 0.600243 | 0.607067 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary contrast: original RAPPPID minus optimized iPIN on C3. See paired_differences.csv for intervals; C1/C2 are secondary.

The metric is weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original RAPPPID has external PPI-training exposure. Each endpoint is encoded as a native singleton; the original multiplicative head is evaluated with per-pair moments, qualified against singleton native calls. This explicitly avoids upstream cross-pair normalization and padding dependence. Deterministic released SentencePiece tokenization follows a 1500-residue prefix cap per endpoint; every pair is retained, but long sequences are truncated. Learned weights, FP32 scoring and the native sigmoid are unchanged; no retraining or order averaging. This authors’ release uses the mult head rather than the paper’s concat head. This is a disclosed follow-up on previously used test panels.

All three cells have complete finite prediction coverage. The original iPIN prediction files were reused byte-for-byte, and their metric points and paired component-draw definitions were reproduced.

See scores.csv for model scores, intervals and finite bootstrap counts. No protected pair identities are included in these aggregate files.
