# Interpretation of the completed X-PAIR comparison

**Selected iPIN-TUnA-31k remains the strongest predictor on the prespecified
combined test-2 metric.** Both released X-PAIR models score every one of the
3,774,966 frozen candidates. All 13 previous competitors are included in
[RESULTS.md](RESULTS.md), with their original predictions and paired draws retained.

| Model | C1 macro | C2 macro | C3 macro |
|---|---:|---:|---:|
| iPIN-TUnA-31k | 0.886903 | 0.827113 | 0.786652 |
| X-PAIR default multitask | 0.704050 | 0.693652 | 0.741983 |
| X-PAIR interaction only | 0.701583 | 0.680655 | 0.733382 |

The score is equal-cohort macro design-weighted P/U concordance, not accuracy
against confirmed noninteractions. Selected 31k exceeds both X-PAIR models on
all three cells; every corresponding pointwise paired 95% interval excludes
zero. On primary C3, selected 31k minus default X-PAIR is **+0.044669**,
95% interval **[+0.012224, +0.075317]**, from 2,000 paired component draws.

X-PAIR is competitive with the older iPIN and PU-TUnA models on C3. The default
scores above the released D-SCRIPT, PLM-interact and RAPPPID predictors on C3,
with positive pointwise paired intervals against those three releases.
Its small C3 point differences from optimized iPIN, PU-TUnA-17k and the
cross-attention ensemble are not resolved by the paired intervals. These are
comparisons of existing predictors with different training data and exposure.

## The added C3 cohort behaves differently

The prespecified macro gives equal weight to the legacy and added cohorts.
Their individual scores show a reversal:

| C3 cohort | iPIN-TUnA-31k | X-PAIR default | X-PAIR interaction |
|---|---:|---:|---:|
| Reconciled legacy | 0.833198 | 0.710793 | 0.682934 |
| Added | 0.740105 | 0.773173 | 0.783830 |

We computed **exploratory** cohort-specific paired intervals after noticing
this reversal. On added C3, default X-PAIR minus selected 31k is +0.033067,
95% interval [-0.012105, +0.079234]; interaction-only X-PAIR minus selected 31k
is +0.043724, interval [-0.010593, +0.094291]. Both intervals include zero.
These point estimates suggest useful differences between the models, but do
not establish a reliable X-PAIR advantage on that subgroup. The exploratory
analysis does not change the primary metric or select a checkpoint.

## Exact exposure exclusion preserves the main conclusion

The audit found 17,380 candidate pairs in released X-PAIR interaction/interface
training or validation: 982 benchmark P and 16,398 benchmark U. Full sequence
and encoder-normalized matching agreed. This is exact pair exposure; it does
not rule out homologs, fragments, sequence variants or PLM pretraining exposure.

After removing those pairs from both models' comparison, C3 macro is 0.780593
for selected 31k, 0.725758 for default X-PAIR and 0.716736 for interaction-only
X-PAIR. Selected 31k minus default is +0.054834, paired 95% interval
[+0.019269, +0.087869]. The exploratory added-C3 advantage also becomes smaller,
and its intervals continue to include zero. C1 development-overlap exclusion
likewise preserves selected 31k's advantage.

The audit also records benchmark U pairs labeled positive by X-PAIR's external
training data; these remain U in the untouched benchmark. That reinforces why
this evaluation is a P/U ranking comparison, not a measurement of confirmed
binding/nonbinding accuracy.

## What this supports

These results support retaining selected 31k as the current default for this
human test-2 benchmark. They do not show that the TUnA architecture is inherently
better, that more data cannot help, or that X-PAIR's interface predictions lack
value. The cohort reversal could reflect data-source, sequence or interaction
distribution differences; this experiment does not identify their cause.

All inference uses full-length Ankh features and the original X-PAIR forward
modules. Embedding generation matched the authors' function exactly; independent
forward/production checks passed. Original iPIN points and bootstrap draws
replayed exactly. All 302 frozen original input files and released source
weights passed the final preservation check in [PRESERVATION.json](../PRESERVATION.json).

Detailed outputs: [all predictors and primary contrasts](RESULTS.md),
[cohort scores](cohort_scores.csv), [paired contrasts](paired_differences.csv),
[exposure counts](exposure.csv), and
[exploratory C3 cohort intervals](C3_COHORT_EXPLORATORY.json).
