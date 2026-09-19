# Original D-SCRIPT benchmark results

Completed: 2026-09-12T20:56:15.671754+00:00. Original human_v1 checkpoint; no retraining.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| dscript_original | 0.462863 | 0.439297 | 0.498680 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |

Primary contrast: original D-SCRIPT minus optimized iPIN on C3. See paired_differences.csv for intervals; C1/C2 are secondary.

The metric is weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original D-SCRIPT has external PPI-training exposure. Only a nonlearned positional-index extension, an exact FP32 projection cache and halo-correct contact-map tiling were added; learned weights and native scoring rules are unchanged. This is a disclosed follow-up on previously used test panels.

All three cells have complete finite prediction coverage. The original iPIN prediction files were reused byte-for-byte, and their metric points and paired component-draw definitions were reproduced.

See scores.csv for model scores, intervals and finite bootstrap counts. No protected pair identities are included in these aggregate files.
