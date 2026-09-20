# Twelve-target metric protocol

Defined before this run's scoring. The original six panels and their scores
were previously examined; these expanded metrics are descriptive follow-up
analyses, not newly prespecified confirmatory endpoints for those panels.
No model, checkpoint, target, or partner is selected using the new scores.

Each target is ranked separately, with larger scores first. The three frozen
predictors have different score scales. Scores are never pooled across targets
or subjected to a common threshold. P denotes a nominated supported partner;
U denotes an unlabeled candidate, not a verified negative. No historical
benchmark sampling weights are transferred to this panel design.

For a candidate list with N pairs, P positives, and H(K) recovered positives:

| Output | Definition |
|---|---|
| `P_vs_U_concordance` | Mean of `1(score_P > score_U) + 0.5 * 1(score_P == score_U)` over all P/U comparisons; identical to AUROC on the reference P/U labels |
| `average_precision` | Noninterpolated, threshold-group AP: sum of precision after each complete equal-score group times the increase in known-positive recall |
| `first_positive_rank_min/max/expected` | Best, worst, and expected rank of the first nominated positive under uniformly random within-tie ordering |
| `reciprocal_rank` | Expected reciprocal of the first-positive rank; generally different from the reciprocal of its expected rank |
| `recovered_P_at_K` | H(K); fractional expected count when a score tie crosses K |
| `recall_at_K` | H(K)/P; recall of the nominated positives only |
| `known_positive_precision_at_K` | H(K)/K; observed known-positive fraction, not estimated biological interaction precision |
| `EF_at_K` | `(H(K)/K)/(P/N)`; 1 is the random-order expectation; this is `N/K * recall_at_K`, not independent evidence |
| `NDCG_at_K` | Binary P gain, discounted by `1/log2(rank+1)`, normalized by the ideal placement of the available positives in the top K |
| `target_success_at_K` | Probability of at least one nominated positive within K under uniform tie ordering; ordinarily 0 or 1 |

K is fixed at **5, 10, and 20** for every cutoff metric. `retrieval_curves.csv`
also records known-positive recall/count and target success at every K from
1 through 50, without selecting a best cutoff after seeing results.

AP uses complete score thresholds, as in
[scikit-learn AP](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html),
and is not trapezoidal PR-AUC. NDCG averages tied gains, following
[scikit-learn NDCG](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html).
Ranks, recovery, success, and reciprocal rank use exact expected tie credit;
accession order never breaks score ties. For m positives in the first positive
tie group of width t after g higher scores, expected first rank is
`g + (t+1)/(m+1)` and first-positive slot j has probability
`choose(t-j,m-1)/choose(t,m)`.

## Aggregation, controls, and exposure

Report all 12 target rows and equal-target arithmetic means. `MAP` is mean AP;
`MRR` is mean reciprocal rank. The macro report also gives total recovered P
and expected successful-target counts, with their denominators. Total recovery
is distinguished from macro recall because ERN1 has four positives and other
targets have three. There are three separately reported cohorts: all twelve,
the original six, and the additional six. No significance or superiority claim
is inferred from these small, purposefully chosen panels.

Each metric is calculated against all U, context U, and background U. The
positive-specific matched analysis uses each partner's own 100 U, and separately
its 50 context and 50 background U. Candidate lists and therefore cutoffs are
local to each comparison; these metrics are not directly interchangeable.

Five positive subsets are reported: all P; excluding development-exposed P;
also excluding homomers; excluding any TRAIN/development-exposed P (whether the
prior pair was P or U); and that last subset also excluding homomers. Excluded
positives are removed from both numerator and ranked candidate list, never
relabeled U. U lists remain fixed. Every current target retains at least one P
in every subset; absence of P fails rather than silently changing a denominator.
The main result retains the ERN1 homodimer. Exact-pair/sequence exposure checks
do not establish homology independence or absence from sequence pretraining.

AP, NDCG, recall, and precision here concern the nominated reference positives.
They do not estimate performance against all true interacting/noninteracting
pairs. Accuracy, F1, MCC, specificity, and calibrated interaction probabilities
are not reported; PU corrections require assumptions and information not
established for these purposively curated panels. See
[Jain, White, and Radivojac (2017)](https://ojs.aaai.org/index.php/AAAI/article/view/10937).
