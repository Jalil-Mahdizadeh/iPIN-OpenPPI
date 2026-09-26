# Selected 31k TUnA: unchanged 12-target panel

Completed 2026-09-26T09:45:40.203514+00:00. The selected 31,188-positive, epoch-1 ensemble was scored on all 5,587 historical pairs (37 P, 5,550 U; 12 targets).

Against the previous frozen retrained TUnA, all-U macro P-versus-U concordance changed from 0.780305 to 0.864008 (+0.083704); 8/12 targets improved. Known positives recovered at 10 candidates per target changed from 7/37 to 10/37.

The source is `example/twelve_target_comparison_v2`, the latest established panel. Pairs, frozen sequence snapshot, P/U labels, U strata, and old predictions are unchanged. The context+background subset is reported separately to retain the older candidate population. U means unlabeled, not experimentally confirmed negative; these are retrieval results on nominated positives, not estimates of biological precision.

## All three U strata

| Model | Macro P/U concordance | MAP | MRR | P@5 /37 | P@10 /37 | P@20 /37 |
|---|---:|---:|---:|---:|---:|---:|
| Original iPIN | 0.725112 | 0.048140 | 0.093259 | 3 | 4 | 7 |
| Optimized iPIN | 0.754410 | 0.104734 | 0.215415 | 3 | 7 | 13 |
| Previous retrained TUnA | 0.780305 | 0.106105 | 0.237261 | 4 | 7 | 7 |
| Original published TUnA | 0.804221 | 0.183589 | 0.345600 | 8 | 10 | 11 |
| Selected 31k TUnA | 0.864008 | 0.158252 | 0.237088 | 5 | 10 | 14 |

P@K here is the total number of nominated positives recovered across 12 separate top-K lists. Metrics use the original tie rules and equal target weighting.

## Candidate-set comparison

| U candidate set | Original iPIN | Optimized iPIN | Previous retrained TUnA | Original TUnA | Selected 31k | Delta vs previous retrained |
|---|---:|---:|---:|---:|---:|---:|
| context | 0.645185 | 0.698611 | 0.722072 | 0.728681 | 0.827373 | +0.105301 |
| background | 0.720648 | 0.747593 | 0.771030 | 0.806528 | 0.845359 | +0.074329 |
| low_plausibility | 0.809502 | 0.817025 | 0.847812 | 0.877454 | 0.919294 | +0.071481 |
| context_background | 0.682917 | 0.723102 | 0.746551 | 0.767604 | 0.836366 | +0.089815 |
| all_U | 0.725112 | 0.754410 | 0.780305 | 0.804221 | 0.864008 | +0.083704 |

## Changes by target, all U

| Target | Previous retrained P/U | Selected 31k P/U | Delta | Previous P@10 | Selected P@10 |
|---|---:|---:|---:|---:|---:|
| ERN1 | 0.722917 | 0.742917 | +0.020000 | 1 | 1 |
| TP53 | 0.868148 | 0.985185 | +0.117037 | 0 | 2 |
| EGFR | 0.750370 | 0.997037 | +0.246667 | 0 | 3 |
| BCL2 | 0.838519 | 0.735556 | -0.102963 | 0 | 0 |
| KEAP1 | 0.460741 | 0.808889 | +0.348148 | 0 | 0 |
| BRCA1 | 0.955556 | 0.816296 | -0.139259 | 1 | 1 |
| KRAS | 0.928148 | 0.911111 | -0.017037 | 0 | 0 |
| CDK2 | 0.938519 | 0.887407 | -0.051111 | 1 | 0 |
| HIF1A | 0.771852 | 0.960000 | +0.188148 | 1 | 2 |
| CTNNB1 | 0.685926 | 0.843704 | +0.157778 | 0 | 1 |
| TNFRSF1A | 0.591852 | 0.779259 | +0.187407 | 1 | 0 |
| BECN1 | 0.851111 | 0.900741 | +0.049630 | 2 | 0 |

## Prior exposure

The main table preserves the complete historical panel. It is not an independent held-out benchmark. The new audit checks unordered exact-sequence pairs and annotated UniProt accession pairs against the 31k training P, training U pool, and the C3 development populations used for checkpoint selection. Training-U membership indicates potential sampling exposure. This audit does not measure homology exposure.

| New-model overlap | Panel P | Panel U |
|---|---:|---:|
| train_17k_P | 2 | 0 |
| train_31k_P | 17 | 2 |
| train_U_pool | 0 | 71 |
| selection_dev_legacy_P | 0 | 0 |
| selection_dev_legacy_U | 0 | 0 |
| selection_dev_added_P | 0 | 0 |
| selection_dev_added_U | 0 | 2 |
| newly_added_train_P | 15 | 2 |
| selected_31k_prior_pair | 17 | 75 |

A common sensitivity analysis removes the union of historical prior-pair flags and newly audited 31k exposure from every model's candidate lists. Target coverage can fall when no P remains; it is reported explicitly and should not be compared directly with the 12-target headline.

| Common exposure-excluded subset, all U | Model | Targets | P | U | Macro P/U | MAP | P@10 |
|---|---|---:|---:|---:|---:|---:|---:|
| exclude_all_five_prior_pairs | Original iPIN | 9 | 16 | 4133 | 0.677277 | 0.028312 | 1 |
| exclude_all_five_prior_pairs | Optimized iPIN | 9 | 16 | 4133 | 0.740469 | 0.032826 | 0 |
| exclude_all_five_prior_pairs | Previous retrained TUnA | 9 | 16 | 4133 | 0.764762 | 0.074966 | 2 |
| exclude_all_five_prior_pairs | Original published TUnA | 9 | 16 | 4133 | 0.781822 | 0.128088 | 3 |
| exclude_all_five_prior_pairs | Selected 31k TUnA | 9 | 16 | 4133 | 0.859993 | 0.154483 | 5 |
| exclude_all_five_prior_pairs_and_homomers | Original iPIN | 9 | 15 | 4133 | 0.659125 | 0.026892 | 1 |
| exclude_all_five_prior_pairs_and_homomers | Optimized iPIN | 9 | 15 | 4133 | 0.722938 | 0.031209 | 0 |
| exclude_all_five_prior_pairs_and_homomers | Previous retrained TUnA | 9 | 15 | 4133 | 0.754404 | 0.046968 | 1 |
| exclude_all_five_prior_pairs_and_homomers | Original published TUnA | 9 | 15 | 4133 | 0.774731 | 0.100084 | 2 |
| exclude_all_five_prior_pairs_and_homomers | Selected 31k TUnA | 9 | 15 | 4133 | 0.851610 | 0.152983 | 5 |

## Reproducibility

The three selected checkpoint seeds are 20260803, 20260817, and 20260831. All checkpoint hashes match `human_ppi_data_scaling_v1/runs/SELECTION.json` and `SCORER_FREEZE.json`. No training or checkpoint selection was performed here.

Historical FP32, full-length ESM residue embeddings were verified and reused; 4,012 learned endpoint features were recomputed for each selected seed. Scores are mean-field-adjusted logits, averaged in float64 across seeds. The loaded GP `fitted` flag is set before `eval()` so the exact saved covariance is retained, as established in the completed study's scorer-replay review. No covariance refit was performed.

Each seed passed native pair-forward agreement (13 panel fixtures, tolerance 1e-5), exact pair-order symmetry, and equality of all checkpoint parameters and buffers before/after inference. Every archived per-target metric, macro metric, and positive rank was reproduced within 2e-12 from the unchanged old scores. Historical files were mounted read-only. See the run-level `PRESERVATION.json` for final input-hash and tracked-status verification.

Outputs: `all_twelve_targets_scores.csv` (all old and new scores); `primary_comparison.csv`; `per_target_comparison.csv`; `per_target_metrics.csv`; `macro_metrics.csv`; `positive_partner_ranks.csv`; `selected_31k_exposure.csv`; `retrieval_curves.csv`; `comparison.png` and `comparison.pdf`. The historical sensitivity subsets retain their original definitions; only the two explicitly named `exclude_all_five_prior_pairs` subsets incorporate this run's new exposure audit.
