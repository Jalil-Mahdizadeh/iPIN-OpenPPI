# BRCA1: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [brca1_three_model_scores.csv](brca1_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.681 | 0.857 | 0.938 |
| Average precision | 0.033 | 0.052 | 0.167 |
| Expected first-positive rank (lower is better) | 16.000 | 15.000 | 3.000 |
| Reciprocal rank | 0.063 | 0.067 | 0.333 |
| Recovered P@5 | 0.000 | 0.000 | 1.000 |
| Recall@5 | 0.000 | 0.000 | 0.333 |
| Known-positive precision@5 | 0.000 | 0.000 | 0.200 |
| EF@5 | 0.000 | 0.000 | 20.200 |
| NDCG@5 | 0.000 | 0.000 | 0.235 |
| Target success@5 | 0.000 | 0.000 | 1.000 |
| Recovered P@10 | 0.000 | 0.000 | 1.000 |
| Recall@10 | 0.000 | 0.000 | 0.333 |
| Known-positive precision@10 | 0.000 | 0.000 | 0.100 |
| EF@10 | 0.000 | 0.000 | 10.100 |
| NDCG@10 | 0.000 | 0.000 | 0.235 |
| Target success@10 | 0.000 | 0.000 | 1.000 |
| Recovered P@20 | 1.000 | 1.000 | 1.000 |
| Recall@20 | 0.333 | 0.333 | 0.333 |
| Known-positive precision@20 | 0.050 | 0.050 | 0.050 |
| EF@20 | 5.050 | 5.050 | 5.050 |
| NDCG@20 | 0.115 | 0.117 | 0.235 |
| Target success@20 | 1.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| BARD1 | No checked TRAIN/dev pair overlap | 16.000 | 15.000 | 26.000 |
| PALB2 | No checked TRAIN/dev pair overlap | 132.000 | 38.000 | 3.000 |
| BRIP1 | No checked TRAIN/dev pair overlap | 145.000 | 82.000 | 33.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
