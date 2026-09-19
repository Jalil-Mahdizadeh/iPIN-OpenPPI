# Early-enrichment training: independent experiment

Completed 2026-09-19T13:27:43.129345+00:00. This study does not replace any existing model or result.

The C3-development-selected primary method is **query_balanced**. This identity was frozen before new test predictions and never changed using test performance.

## Development selection

| Method | Epoch | C3-dev macro EF@20 |
|---|---:|---:|
| historical_ef_selected | 4 | 6.9227 |
| query_balanced | 1 | 7.4266 |
| shortlist_weighted | 1 | 7.4266 |

Saved epoch-4/8 TUnA development results are in [saved_checkpoint_audit.csv](results/saved_checkpoint_audit.csv). That audit did not change the frozen TUnA comparator or initiate TUnA retraining.

## Test comparison

Recovery below means **mean known-positive hits per query** and **macro recall of the query’s known positives**. EF compares those hits with random ranking of that same query’s fixed P+U list. All methods use identical eligible queries and candidate lists. Budgets are never enlarged.

### C1_test

| Model | EF@10 / 20 / 30 | Hits@10 / 20 / 30 | Recall % @10 / 20 / 30 |
|---|---:|---:|---:|
| ipin_baseline | 8.50 / 6.42 / 5.35 | 0.55 / 0.84 / 1.07 | 19.8 / 29.9 / 37.4 |
| ipin_optimized | 14.83 / 10.18 / 7.99 | 0.93 / 1.34 / 1.61 | 34.6 / 47.4 / 55.8 |
| tuna_retrained | 18.10 / 12.12 / 9.31 | 1.15 / 1.61 / 1.90 | 42.2 / 56.4 / 65.0 |
| combo_55_45 | 17.46 / 11.70 / 9.21 | 1.10 / 1.56 / 1.85 | 40.7 / 54.5 / 64.2 |
| historical_ef_selected | 14.83 / 10.18 / 7.99 | 0.93 / 1.34 / 1.61 | 34.6 / 47.4 / 55.8 |
| query_balanced (dev-selected) | 10.09 / 7.35 / 6.01 | 0.60 / 0.90 / 1.13 | 23.5 / 34.2 / 42.0 |
| shortlist_weighted | 10.09 / 7.35 / 6.01 | 0.60 / 0.90 / 1.13 | 23.5 / 34.2 / 42.0 |

At K=20, the prespecified winner changes EF by -2.830 (-27.8%) versus frozen optimized iPIN; paired 95% component-bootstrap interval: [-3.136, -2.543].

### C2_test

| Model | EF@10 / 20 / 30 | Hits@10 / 20 / 30 | Recall % @10 / 20 / 30 |
|---|---:|---:|---:|
| ipin_baseline | 5.82 / 4.44 / 3.62 | 1.18 / 1.94 / 2.48 | 21.1 / 32.8 / 40.2 |
| ipin_optimized | 7.64 / 5.38 / 4.33 | 1.46 / 2.29 / 2.89 | 26.9 / 38.5 / 46.9 |
| tuna_retrained | 8.17 / 5.94 / 4.79 | 1.56 / 2.53 / 3.21 | 28.4 / 41.9 / 51.1 |
| combo_55_45 | 8.53 / 6.09 / 4.91 | 1.61 / 2.56 / 3.23 | 30.1 / 43.6 / 53.1 |
| historical_ef_selected | 7.64 / 5.38 / 4.33 | 1.46 / 2.29 / 2.89 | 26.9 / 38.5 / 46.9 |
| query_balanced (dev-selected) | 6.42 / 4.73 / 3.87 | 1.19 / 1.94 / 2.49 | 22.9 / 34.4 / 42.7 |
| shortlist_weighted | 6.42 / 4.73 / 3.87 | 1.19 / 1.94 / 2.49 | 22.9 / 34.4 / 42.7 |

At K=20, the prespecified winner changes EF by -0.650 (-12.1%) versus frozen optimized iPIN; paired 95% component-bootstrap interval: [-0.776, -0.528].

### C3_test

| Model | EF@10 / 20 / 30 | Hits@10 / 20 / 30 | Recall % @10 / 20 / 30 |
|---|---:|---:|---:|
| ipin_baseline | 8.88 / 6.91 / 6.08 | 0.69 / 1.23 / 1.64 | 11.3 / 17.5 / 23.1 |
| ipin_optimized | 11.25 / 8.25 / 7.04 | 0.77 / 1.33 / 1.78 | 14.3 / 20.9 / 26.8 |
| tuna_retrained | 13.03 / 9.68 / 7.85 | 0.83 / 1.45 / 1.87 | 16.5 / 24.5 / 29.8 |
| combo_55_45 | 13.78 / 9.50 / 7.93 | 0.87 / 1.44 / 1.89 | 17.5 / 24.1 / 30.2 |
| historical_ef_selected | 11.25 / 8.25 / 7.04 | 0.77 / 1.33 / 1.78 | 14.3 / 20.9 / 26.8 |
| query_balanced (dev-selected) | 12.97 / 9.08 / 7.37 | 0.79 / 1.30 / 1.66 | 16.5 / 23.0 / 28.0 |
| shortlist_weighted | 12.97 / 9.08 / 7.37 | 0.79 / 1.30 / 1.66 | 16.5 / 23.0 / 28.0 |

At K=20, the prespecified winner changes EF by +0.830 (+10.1%) versus frozen optimized iPIN; paired 95% component-bootstrap interval: [+0.116, +1.507].

## Interpretation and limitations

The three new-study rows are prespecified ablations, not three opportunities to choose a winner on test. The historical row tests checkpoint reselection without changing training. The query-balanced row changes global comparisons to same-query comparisons and targets the existing unweighted lists. The shortlist row adds bounded top-40 U emphasis after a common warmup epoch.

Both new variants were initialized from scratch, using the original frozen 640-D ESM2-150M embeddings, 498,053-parameter optimized-iPIN architecture, original AdamW settings, three seeds, and eight epochs. Embeddings were reused without changing sequence normalization. Each epoch sampled 2,000,000 same-query P/U comparisons, uniformly by query and partner, with an Nq/mean-Nq query scale. Original U design weights were not used: this objective is for the fixed unweighted lists. This is an EF-oriented surrogate, not a differentiable implementation of exact EF@20, and the top-40 emphasis is a fixed heuristic, not a tuned hyperparameter.

U means unlabeled, not experimentally confirmed negative. High-scoring U may include real undiscovered interactors; emphasizing them can hurt biological discovery. Reported recovery is recovery of known P only. Results do not measure proteome-wide screening precision or validate novel interactions.

Historical iPIN could only be selected between epochs 4 and 8; the new variants had eight checkpoint choices. Development results are selection-biased. Test has been inspected in earlier studies, so this is a bounded, prospectively specified experiment on an already-used test set, not a new untouched external validation.

Intervals use 2,000 paired resamples of query sequence components with fixed candidate lists. They are conditional on this library, not adjusted for multiple comparisons, and do not fully model dependence from shared partner proteins. C2 train-side and test-side query breakdowns are retained in the CSV. Total oriented query hits may count the same physical pair from both endpoints; they are not unique interactions.

## Files and integrity

- [All panel metrics, confidence intervals, and C2 subgroups](results/all_panel_metrics.csv)
- [Paired differences against all frozen references](results/paired_comparisons.csv)
- [Development epoch curves](results/development_curves.csv)
- [Panel coverage](results/panel_coverage.csv)
- [Global weighted PU concordance (secondary)](results/global_concordance.csv)
- [Frozen protocol](protocol.json) and [selection](provenance/SELECTION_FREEZE.json)
- [Independent audit](provenance/AUDIT.json)

The training phase took 1.36 minutes on one GH200 GPU, including 48 checkpoint saves and development scoring. All 48 new checkpoints are retained under `checkpoints/`; test member/ensemble scores are under `private/`. These are private, git-ignored artifacts. Per-query metric CSVs are under `results/`.

Audit: 575,820 independent EF/hits/recall/rate checks, 135 reproduced historical reference metrics, and 267 existing source/checkpoint/result artifacts verified unchanged. The repository was mounted read-only during execution; only this new experiment folder was writable. `combo/` and all current models and results were left intact.
