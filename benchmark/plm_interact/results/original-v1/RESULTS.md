# Original PLM-interact benchmark results

Completed: 2026-09-17T02:13:46.105805+00:00. Original 650M humanV11 checkpoint; no retraining.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| plm_interact_original_650m_humanv11 | 0.558772 | 0.532392 | 0.567018 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary contrast: original PLM-interact minus optimized iPIN on C3. See paired_differences.csv for intervals; C1/C2 are secondary.

The metric is weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original PLM-interact has external PPI-training exposure. Frozen sequence SHA256 orders the two proteins deterministically before the native predictor. Native longest-first tokenization is capped at 1603 tokens; every pair is retained, but long inputs are truncated. Learned weights, FP32 scoring and the native sigmoid are unchanged; no retraining or order averaging. This is a disclosed follow-up on previously used test panels.

All three cells have complete finite prediction coverage. The original iPIN prediction files were reused byte-for-byte, and their metric points and paired component-draw definitions were reproduced.

See scores.csv for model scores, intervals and finite bootstrap counts. No protected pair identities are included in these aggregate files.
