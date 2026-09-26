# Released X-PAIR on frozen test2

Completed 26 September 2026. This follow-up evaluates released X-PAIR against
the existing 13 predictors on the unchanged human C1/C2/C3 test2 candidates.
The user authorized applying X-PAIR, then updating documentation and publishing
the completed comparison. Full outputs remain in
[`experiments/x_pair_test2_v1/`](../../../experiments/x_pair_test2_v1/README.md).

**iPIN-TUnA-31k remains the highest-scoring predictor on all three combined
test2 metrics.** The default iPIN model, its exact ensemble and all prior
release records remain unchanged. This adds comparison evidence, not a new
model selection or a causal architecture comparison.

## Prespecified comparison

All 15 predictors cover the same 3,774,966 candidate pairs. The primary metric
is equal-cohort macro design-weighted P/U concordance on reconciled legacy and
added cohorts; C3 is primary. U is unlabeled, not confirmed noninteraction.
The X-PAIR checkpoints were specified before scoring: authors' default
`multitask_xfair`, with `interaction_xfair` as a secondary comparison. Neither
was retrained, selected by test score or calibrated on this benchmark.

| Predictor | C1 macro | C2 macro | C3 macro |
|---|---:|---:|---:|
| iPIN-TUnA-31k | 0.886903 | 0.827113 | 0.786652 |
| X-PAIR default multitask | 0.704050 | 0.693652 | 0.741983 |
| X-PAIR interaction-only | 0.701583 | 0.680655 | 0.733382 |

Selected 31k exceeds both X-PAIR models in all three cells, with pointwise
paired 95% intervals excluding zero. Its C3 gain over default X-PAIR is
**+0.044669 [0.012224, 0.075317]**; its gain over interaction-only X-PAIR is
**+0.053270 [0.013519, 0.089097]**. These use 2,000 common component-bootstrap
draws and are not corrected for multiple comparisons. The
[complete 15-predictor table](../../../experiments/x_pair_test2_v1/results/RESULTS.md)
includes D-SCRIPT, PLM-interact, RAPPPID, SPRINT and the older iPIN/TUnA models.

## Cohort reversal and exposure

On added C3 alone, selected 31k scores 0.740105, default X-PAIR 0.773173 and
interaction-only X-PAIR 0.783830. Exploratory cohort intervals were computed
after observing the reversed ranking: X-PAIR minus selected 31k is +0.033067
[-0.012105, 0.079234] for the default and +0.043724 [-0.010593, 0.094291] for
interaction-only. Both include zero. These point estimates suggest differences
between the predictors, but do not establish a subgroup advantage.

Exact unordered sequence-pair matching against X-PAIR interaction/interface
training and validation found 17,380 overlapping candidates: 982 benchmark P
and 16,398 U. Matching after Ankh residue normalization gave the same mask.
After removing these pairs from both predictors, C3 macro is 0.780593 for
selected 31k versus 0.725758 for default X-PAIR; the paired difference is
**+0.054834 [0.019269, 0.087869]**. The original C1 development-overlap
sensitivity is also retained, with selected 31k's advantage preserved.

Exact exclusion does not rule out homologs, fragments, sequence variants or
encoder pretraining exposure. C1/C2/C3 are defined relative to iPIN training;
they do not establish unseen endpoints for X-PAIR. Different training data,
objectives and endpoint exposure prevent attributing this difference solely
to architecture. Test2 remains a previously examined historical follow-up.

## Inference, validation and preservation

Both models use full-length Ankh-large features for all 7,320 test endpoints,
including 100 proteins longer than the checkpoint's 2,000-residue training
maximum; the longest has 7,570 residues. This uses the supported all-length
inference policy. FP32 scoring retains the native cross-attention, rotary
positions, masks, pooling, interaction head and sigmoid; the independent
initial linear projection is cached without changing the learned model.

Embeddings matched the unchanged upstream generator exactly. Scoring and
production-indexing checks passed against complete native forward inference,
including long sequences, padding, batches and swapped endpoints. Full finite
coverage was frozen before label-based evaluation. Selected 31k's existing
point estimates and paired draws replayed exactly. All 302 original inputs
and released source weights passed preservation checks. See the
[validation summary](../../../experiments/x_pair_test2_v1/validation/SUMMARY.json)
and [preservation record](../../../experiments/x_pair_test2_v1/PRESERVATION.json).

## Records

- [Interpretation and limitations](../../../experiments/x_pair_test2_v1/results/INTERPRETATION.md).
- [Machine-readable results](../../../experiments/x_pair_test2_v1/results/RESULTS.json),
  [scores](../../../experiments/x_pair_test2_v1/results/scores.csv), and
  [paired contrasts](../../../experiments/x_pair_test2_v1/results/paired_differences.csv).
- [Cohort scores](../../../experiments/x_pair_test2_v1/results/cohort_scores.csv),
  [exposure counts](../../../experiments/x_pair_test2_v1/results/exposure.csv), and
  [exploratory C3 cohort intervals](../../../experiments/x_pair_test2_v1/results/C3_COHORT_EXPLORATORY.json).
- [C3 comparison figure](../../../experiments/x_pair_test2_v1/results/C3_comparison.png).
- [Protocol](../../../experiments/x_pair_test2_v1/PROTOCOL.json) and
  [publication/reproduction scope](../../../experiments/x_pair_test2_v1/PUBLICATION.md).

The original [v3 model card](../../models/FROZEN_PAIR_MODELS_v3.md),
[promotion report](M1_iPIN_TUnA_31k_Promotion_v1.md), registry and their
checksum-bound 13-predictor evidence are preserved as issued.
