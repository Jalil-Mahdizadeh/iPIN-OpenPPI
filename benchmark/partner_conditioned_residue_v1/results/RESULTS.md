# Partner-conditioned residue model comparison

Completed: 2026-09-24T22:01:58.226741+00:00.

| Model | C1 | C2 | C3 |
|---|---:|---:|---:|
| ipin_baseline | 0.843493 | 0.805299 | 0.789249 |
| ipin_optimized | 0.916037 | 0.851301 | 0.807948 |
| tuna_retrained_ensemble | 0.948619 | 0.880401 | 0.815875 |
| cross_attention_ensemble | 0.944218 | 0.871586 | 0.804001 |
| mean_pool_ensemble | 0.923655 | 0.846331 | 0.786247 |

Primary contrast: cross_attention_ensemble minus frozen PU-TUnA on C3: -0.011874, paired 95% interval [-0.036281, +0.028111].

The paired interval includes zero; C3 superiority is not established.

The metric is weighted positive-versus-unlabeled concordance, not verified-positive-versus-verified-negative accuracy. This is a disclosed follow-up on previously examined test panels. Selection used C3 development only.

All three cells have complete finite prediction coverage. All three iPIN reference prediction files were reused byte-for-byte, and their metric points and paired component-draw definitions were reproduced.

Other model/cell contrasts and individual seed results are secondary/descriptive; intervals are pointwise, not multiplicity-adjusted. No frozen iPIN model is replaced by this study.

The cross-attention models use learned residue summaries, not validated physical contact maps. Training sampled up to 512 residue positions; evaluation used every residue.

Head-only scoring of 4,096 pairs with all selected three-seed models took 0.040 seconds on the qualified GPU; sequence encoding and endpoint-feature preparation are excluded.

See scores.csv for all member scores and intervals, and paired_differences.csv for every model/reference contrast. No protected pair identities are included in these aggregate files.
