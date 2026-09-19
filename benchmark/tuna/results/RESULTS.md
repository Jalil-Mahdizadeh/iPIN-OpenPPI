# TUnA final benchmark results

Completed: 2026-09-12T18:14:54.914165+00:00. Retrained ensemble: epoch 4.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| tuna_original | 0.716166 | 0.698193 | 0.695658 |
| tuna_retrained_ensemble | 0.948619 | 0.880401 | 0.815875 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary contrast: retrained PU-TUnA ensemble minus optimized iPIN on C3. See paired_differences.csv for intervals; C1/C2 are secondary.

The metric is weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original TUnA has external PPI-training exposure; retrained PU-TUnA is a declared loss/GP-curvature adaptation. This is a disclosed follow-up on previously used test panels.

All three cells have complete finite prediction coverage. The original iPIN prediction files were reused byte-for-byte, and their metric points and paired component-draw definitions were reproduced.

See scores.csv for member scores, intervals and finite bootstrap counts. No protected pair identities are included in these aggregate files.
