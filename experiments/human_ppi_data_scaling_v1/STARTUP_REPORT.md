# Initial corpus and execution report

2026-09-25. Dataset construction and qualification are complete. Formal fits have been submitted; performance results are not yet available.

| Partition | Cell | Original P | Added P on new candidate identities | Original U promoted to P in v2 | Version-2 P |
|---|---|---:|---:|---:|---:|
| development | C1 | 3,259 | 643 | 521 | 4,423 |
| development | C2 | 11,327 | 4,215 | 376 | 15,918 |
| development | C3 | 2,265 | 727 | 316 | 3,308 |
| test | C1 | 3,187 | 645 | 483 | 4,315 |
| test | C2 | 13,446 | 4,375 | 387 | 18,208 |
| test | C3 | 2,379 | 934 | 378 | 3,691 |

Training P budgets: **16,799 → 20,000 → 25,000 → 31,188**, with three fitting seeds per budget and the same frozen 2M-U background. Each expanded holdout cell retains its original million U candidate identities and adds 250,000 U candidates; newly supported old U rows have versioned state changes.

All original data snapshots, weights, predictions and results are retained. Both exact legacy-label metrics and reconciled version-2 metrics will be reported. The largest budget reflects the current frozen source/mapping/split policy, not a global data ceiling.

The endpoint universe contains 17,583 sequences. Of 803 candidate additions, 583 passed anchored homology allocation and 220 were quarantined for bridging old partitions. No original endpoint was moved.

C1 inherits 91,781 dev/test candidate overlaps from the old U samples, including 57 pairs promoted to P in both v2 views. Complete panels remain available; an additional C1 result excludes all development candidate identities. C2 and C3 have no such overlap. All new training pairs are disjoint from all held-out candidate identities.

Code and data are frozen in `audit/EXECUTION_FREEZE.json` and `audit/CORPUS_FREEZE.json`. Qualifications and the independent artifact checks passed. GPU fitting receives no test candidates or test labels.

SLURM training array: **2979721**, 12 fits, at most four GPUs concurrently. Dependent selection/scoring/evaluation job: **2979722**.

The dependent job selects common ensemble epochs and the positive budget using C3-dev-2 macro concordance, freezes weights and predictions, and compares the selected model and fresh 17k control against all three frozen iPIN models. It produces original, reconciled, added-only and combined C1/C2/C3 results, paired component-bootstrap intervals, CSV tables, and learning-curve plots under `runs/results/`.

Test-2 is a historical follow-up by design. Dataset growth also changes source composition, coverage and evidence quality; this experiment cannot by itself establish a performance ceiling or a volume-only causal effect.
