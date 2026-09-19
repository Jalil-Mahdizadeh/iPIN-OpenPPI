# EF-oriented training: findings

Completed 19 September 2026. Everything new is in `early_enrichment/`, independent
of the completed `combo/` study. Current models, checkpoints, results, and the
rest of the repository were left unchanged.

## Bottom line

**This is a C3-specific improvement over optimized iPIN, not an overall upgrade.**
The development-selected query-balanced model improves C3-test EF and macro
recall at 10, 20, and 30. It substantially worsens C1 and C2, and it does not beat
the existing TUnA or combo on C3 EF at these budgets. Keep the current models.
The experimental checkpoints and all results are retained, including the
unsuccessful shortlist-weighting runs.

## What was selected, without using test results

- The existing optimized-iPIN architecture was trained from scratch with frozen
  ESM2-150M embeddings. Three seeds, eight epochs, and 2,000,000 sampled P/U
  comparisons per epoch were used for each new variant.
- `query_balanced` compares a P and a U partner **for the same TRAIN query**.
  Queries are sampled uniformly, with a list-size loss scale. This changes both
  comparison sampling and the old population-weighted objective; it is not a
  pure change to the loss formula alone.
- `shortlist_weighted` adds capped weight to U in each query's complete-list
  top 40 from epoch 2. It does not label U as confirmed negatives.
- C3-development macro EF@20 selected **epoch 1** for both variants: **7.4266**,
  versus **6.9227** for frozen optimized iPIN. The prospective tie rule selected
  the simpler query-balanced variant as the primary model.
- Both selected variants are the **identical warmup model**, before shortlist
  weighting begins. Their identical test results are not two independent wins
  and are not evidence that shortlist weighting helps. No weighted epoch beat
  the shared warmup checkpoint on development EF@20.
- Reselecting historical iPIN between saved epochs 4 and 8 retained epoch 4.
  TUnA's saved-checkpoint audit was development-only; its epoch-4 frozen test
  comparator was unchanged.

The full protocol and selected checkpoint hashes were frozen before new test
scoring. No winner was reselected on test. All 48 new checkpoints are retained.

## Recovery and enrichment: optimized iPIN versus the new model

Each arrow means **preserved optimized iPIN → query-balanced epoch 1**.
Recovery is reported both as mean known-positive hits per query and as macro
recall of each query's known positives. The query lists and eligibility are
identical across models. EF is relative to random ranking within those lists.

| Test | K | Macro EF | Mean hits/query | Macro recall (%) |
|---|---:|---:|---:|---:|
| C1 | 10 | 14.83 → 10.09 | 0.93 → 0.60 | 34.59 → 23.53 |
| C1 | 20 | 10.18 → 7.35 | 1.34 → 0.90 | 47.38 → 34.23 |
| C1 | 30 | 7.99 → 6.01 | 1.61 → 1.13 | 55.79 → 41.96 |
| C2 | 10 | 7.64 → 6.42 | 1.46 → 1.19 | 26.90 → 22.86 |
| C2 | 20 | 5.38 → 4.73 | 2.29 → 1.94 | 38.52 → 34.38 |
| C2 | 30 | 4.33 → 3.87 | 2.89 → 2.49 | 46.87 → 42.70 |
| C3 | 10 | 11.25 → 12.97 | 0.77 → 0.79 | 14.29 → 16.48 |
| C3 | 20 | 8.25 → 9.08 | 1.33 → 1.30 | 20.94 → 23.03 |
| C3 | 30 | 7.04 → 7.37 | 1.78 → 1.66 | 26.76 → 28.05 |

At the primary budget of 20, EF changes by **−27.8% on C1, −12.1% on C2,
and +10.1% on C3**. The C3 paired EF difference is +0.8305, with a 95%
query-component-bootstrap interval of [+0.1164, +1.5066]. These are conditional,
unadjusted intervals on an already-used test set, not independent external
validation.

**The C3 recovery tradeoff matters:** better macro EF/recall does not necessarily
mean more total positives found. Queries have different positive counts; macro
recall rewards the fraction recovered within each query, whereas mean hits
rewards the absolute number. At K=20, C3 mean hits fall from 1.3314 to 1.3029
(difference interval −0.0835 to +0.0265). Total *oriented query hits* fall from
1,121 to 1,097; these are not counts of unique physical interactions. Thus this
experiment does not demonstrate a higher average number of experimental hits
per 20 follow-ups, even though its primary C3 enrichment metric improves.

## Context: all preserved references at K=20

| Model | C1 EF@20 | C2 EF@20 | C3 EF@20 |
|---|---:|---:|---:|
| iPIN baseline | 6.42 | 4.44 | 6.91 |
| iPIN optimized | 10.18 | 5.38 | 8.25 |
| Retrained TUnA, frozen epoch 4 | 12.12 | 5.94 | 9.68 |
| Existing 55:45 combo | 11.70 | 6.09 | 9.50 |
| New query-balanced, epoch 1 | 7.35 | 4.73 | 9.08 |

The new model beats baseline iPIN on EF at all three budgets in all three panels,
but not the stronger current models overall. On C3, its EF@20 differences versus
TUnA and combo have intervals spanning zero; the point estimates are lower,
not an established advantage.

## Interpretation and recommended next decision

1. Keep optimized iPIN, TUnA, and combo intact. Do not replace any frozen model
   with this experimental head.
2. The results justify interest in query-aware objectives for C3, but do not
   establish that the training change itself caused the improvement. Historical
   iPIN only had epochs 4/8 available, while the new model could stop at epoch 1.
   **A matched original-objective control saving every epoch is needed** to
   separate early stopping from query-aware training. This additional experiment
   was not run after observing these test results.
3. The tested top-40 U weighting did not earn selection. Do not infer that all
   early-enrichment training strategies fail; this was one bounded surrogate,
   two variants, and an eight-epoch budget, not a broad hyperparameter search.
4. Decide whether real screening prioritizes macro EF/recall across queries or
   the total number of known hits per screening budget. Report both. Known-P
   recovery is also imperfect: U can contain genuinely novel interactors.

There was no new embedding generation, full-candidate-pool experiment, six-target
evaluation, TUnA retraining, or ensemble-weight retuning in this study.

## Files, timing, and checks

- [Full seven-model report at K=10/20/30](REPORT.md)
- [Metrics CSV, intervals, and C2 query-side subgroups](results/all_panel_metrics.csv)
- [Paired comparisons against every preserved reference](results/paired_comparisons.csv)
- [Development epoch curves](results/development_curves.csv)
- [Saved iPIN/TUnA epoch-4/8 audit](results/saved_checkpoint_audit.csv)
- [Independent audit](provenance/AUDIT.json)

Execution used the existing iPIN SIF on the allocated GH200 GPU. The training
phase took about **83 seconds**, test scoring **7 seconds**, evaluation
**18 seconds**, and independent audit **22 seconds**. These are prediction-head
times with embeddings reused, not protein-encoder retraining costs. Setup,
implementation, and validation are additional.

Validation passed all 18 tests and exactly reproduced the historical checkpoint's
qualification scores. The final audit independently checked **575,820** EF/hits/
recall/rate values with zero discrepancy, reproduced **135** historical metric
values, and verified **267** existing source/checkpoint/result artifacts unchanged.
The only new top-level repository item is `early_enrichment/`.
