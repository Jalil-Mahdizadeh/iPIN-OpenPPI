# What the transfer comparison shows

**The default 31k model is not a general transfer improvement over the previous
17k TUnA.** Its gains on the human benchmarks do not carry over uniformly to
these two fixed external panels. The [full report](REPORT.md) compares all four
models; the numbers below focus on the new default versus previous TUnA.

In the six-species primary matched-U comparison, concordance changes from
0.6478 to 0.6511: +0.0033, with paired 95% interval [-0.0140, +0.0209].
Mean recall@10 is essentially unchanged (22.45% versus 22.43%). Concordance
improves in two of six species. Mouse has the clearest increase (+0.0458,
interval [+0.0052, +0.0923]), although its recall@10 decreases. Changes in
overall ranking and early retrieval therefore should be assessed separately.

The nonhuman gain is larger against background U (+0.0174, interval
[+0.0005, +0.0343]) than against length/degree-matched U. This is evidence that
the observed advantage depends on candidate design; it does not by itself
identify which protein features or biological mechanisms explain the change.

The human–laboratory-yeast primary concordance decreases from 0.8163 to 0.8088,
but its paired interval includes zero. Early retrieval shows a clearer loss:

| Equal-P metric | Previous TUnA | Default 31k | Change | Paired 95% interval for change |
|---|---:|---:|---:|---:|
| Mean AP | 0.2883 | 0.2264 | -0.0619 | [-0.0795, -0.0468] |
| Recall@5 | — | — | -7.27 percentage points | [-10.06, -4.79] percentage points |
| Recall@10 | 53.63% | 48.94% | -4.69 percentage points | [-7.36, -2.37] percentage points |
| Recall@20 | — | — | -2.64 percentage points | [-5.16, -0.33] percentage points |

The concordance result alone would miss that loss near the top of the ranked
lists. The intervals above are exploratory, pointwise, and conditional on the
fixed panels; they are not adjusted for all comparisons or source dependence.

Removing the same union of historical and expanded-corpus exact endpoint
exposures from every model does not reverse the main pattern. Matched-U
nonhuman concordance changes by +0.0024; human–yeast concordance changes by
-0.0134. Both intervals include zero. This sensitivity retains 564 human–yeast
P panels and has fewer U per panel, so it is a separate estimand from the
complete 1:100 evaluation. Exact exclusions do not establish homology novelty.

The comparison changes both training corpus and selected epoch (old epoch 4,
new epoch 1), so it cannot isolate a causal effect of more training pairs.
It supports qualifying model-performance claims by domain and retrieval
objective. No model designation, historical benchmark, checkpoint or repository
configuration was changed in this experiment.

All historical metric and bootstrap rows reproduced exactly, all 218,440
pair rows were scored by the new three-member ensemble, and native inference
qualification passed. See the per-study tables and final preservation audit
for the complete numerical record.
