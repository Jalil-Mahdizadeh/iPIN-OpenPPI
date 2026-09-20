# Context versus background U score analysis

This exploratory follow-up answers the user request: "investigate if there is a
meaningful difference between two groups scores." It uses the existing twelve
target scores and annotations. No model inference, fitting, target selection,
protected benchmark access, or modification of completed results is required.
These choices were written before computing this comparison, after the parent
retrieval results had already been inspected. This is not a prospective test.

## Main comparison

Use all 1,850 context U pairs and 1,850 background U pairs, covering 37 positive
anchors and 12 targets, for each of the three frozen models. Verify the parent
run manifest, all of its public output hashes, and each panel's row annotations.

For each target, model, and positive anchor, calculate

`A = mean(1(context_score > background_score) + 0.5 * 1(equal scores))`

over the 50 by 50 cross-group comparisons. A=0.5 means no directional rank
advantage; A>0.5 means context receives higher scores. This is a score comparison,
not the probability that a protein pair interacts. It equals the context
Mann-Whitney statistic divided by 2,500. Report `2*A-1` as rank-biserial effect.
Average anchors equally within target, then targets equally. Do not compare
raw scores across different models or treat 3,700 rows as independent targets.

Report a 95% percentile interval from 100,000 whole-target bootstrap draws with
fixed seed 20260920. Use the same draws for the three models. Report a two-sided
exact sign-flip reference p-value for the mean target effect `A-0.5`, enumerating
all 4,096 sign patterns. Holm-adjust these three primary p-values together.
The sign-flip reference assumes independent, sign-symmetric target effects under
the null. It does not follow from randomized assignment of these U groups.
Bootstrap intervals describe sensitivity to target composition under an
exchangeable-target approximation, not uncertainty from model retraining or
an experimentally sampled population. Shared proteins and related targets can
violate independence; the panels were deliberately selected. P-values are
exploratory, not confirmatory biological evidence.

No biological minimum-important-effect threshold is justified for these raw
scores. Judge practical size from rank probability, target consistency, score
spread, and top-ranked composition; do not equate non-significance with equality.

## Descriptive checks and sensitivity

- Per-anchor and per-target score mean, median, quartiles, standard deviation,
  differences, rank effects, and Kolmogorov-Smirnov distance (descriptive only).
- Within each target, the fraction of the top 20 U scores belonging to context,
  with expected fractional credit for boundary ties; baseline is 50% by design.
- Leave-one-target-out main estimates; original-six and additional-six summaries.
- Parent P-versus-U concordance against context and background separately,
  reported descriptively with all nominated P retained.
- Partner-length differences and the fraction of background candidates that
  happen to satisfy their anchor's context rule. Reconstruct this rule from the
  unchanged UniProt source and panel block metadata; validate every context row.
- Repeat rank comparisons against only the background candidates failing their
  own anchor's context rule. This is a secondary sensitivity with changed group
  sizes, not a replacement for the main comparison; do not attach extra p-values.

Keep all outputs in this new directory. Preserve the parent run, all frozen
weights and records, and all panel labels. Retain code, inputs' hashes, methods,
tables, a standalone figure, independent checks, and a readable report.

## Statistical implementation references

- [SciPy Mann-Whitney statistic](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.mannwhitneyu.html)
- [SciPy paired sample/sign-flip permutation reference](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.permutation_test.html)
- [SciPy percentile bootstrap](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.bootstrap.html)

The rank statistic will be checked against SciPy. Exact sign-flip probabilities
will be checked independently against SciPy's exhaustive paired-sample procedure.
Additional synthetic checks cover ties, reversed groups, and top-K tie credit.
