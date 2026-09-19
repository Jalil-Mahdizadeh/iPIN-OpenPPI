# D-SCRIPT original and matched-data retrained benchmark results

Completed: 2026-09-18T23:10:46.500606+00:00. Original human_v1 and three-seed PU-D-SCRIPT, selected epoch 4.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| dscript_original | 0.462863 | 0.439297 | 0.498680 |
| dscript_retrained | 0.504429 | 0.481321 | 0.511437 |
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |
| dscript_seed_20260803 | 0.607734 | 0.562305 | 0.536145 |
| dscript_seed_20260817 | 0.558605 | 0.514019 | 0.520058 |
| dscript_seed_20260831 | 0.348917 | 0.348844 | 0.337630 |

Primary contrast: retrained PU-D-SCRIPT ensemble minus optimized iPIN on C3. See paired_differences.csv for paired intervals, including retrained versus original; C1/C2 are secondary.

The metric is weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original human_v1 predictions are reused unchanged and have external PPI-training exposure. Retrained models used freshly initialized native PPI layers, fixed native LM embeddings, weighted P-versus-U ranking plus native contact sparsity regularization, and TRAIN-only 512-residue random crops. C3-DEV alone selected the shared checkpoint epoch. All evaluation sequences are full length, with halo-correct contact-map tiling. Ensemble/member scores are pre-sigmoid ranking logits, not calibrated interaction probabilities. This is a disclosed follow-up on previously used test panels.

All three cells have complete finite prediction coverage. Original D-SCRIPT and both iPIN prediction files were reused byte-for-byte, their metric points reproduced, and historical paired component-draw definitions retained.

See scores.csv for model scores, intervals and finite bootstrap counts. No protected pair identities are included in these aggregate files.
