# CTNNB1: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [ctnnb1_three_model_scores.csv](ctnnb1_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.886 | 0.600 | 0.617 |
| Average precision | 0.115 | 0.016 | 0.025 |
| Expected first-positive rank (lower is better) | 4.000 | 78.000 | 23.000 |
| Reciprocal rank | 0.250 | 0.013 | 0.043 |
| Recovered P@5 | 1.000 | 0.000 | 0.000 |
| Recall@5 | 0.333 | 0.000 | 0.000 |
| Known-positive precision@5 | 0.200 | 0.000 | 0.000 |
| EF@5 | 20.200 | 0.000 | 0.000 |
| NDCG@5 | 0.202 | 0.000 | 0.000 |
| Target success@5 | 1.000 | 0.000 | 0.000 |
| Recovered P@10 | 1.000 | 0.000 | 0.000 |
| Recall@10 | 0.333 | 0.000 | 0.000 |
| Known-positive precision@10 | 0.100 | 0.000 | 0.000 |
| EF@10 | 10.100 | 0.000 | 0.000 |
| NDCG@10 | 0.202 | 0.000 | 0.000 |
| Target success@10 | 1.000 | 0.000 | 0.000 |
| Recovered P@20 | 1.000 | 0.000 | 0.000 |
| Recall@20 | 0.333 | 0.000 | 0.000 |
| Known-positive precision@20 | 0.050 | 0.000 | 0.000 |
| EF@20 | 5.050 | 0.000 | 0.000 |
| NDCG@20 | 0.202 | 0.000 | 0.000 |
| Target success@20 | 1.000 | 0.000 | 0.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| CDH1 | No checked TRAIN/dev pair overlap | 51.000 | 180.000 | 191.000 |
| CTNNA1 | No checked TRAIN/dev pair overlap | 4.000 | 78.000 | 23.000 |
| TCF7L2 | No checked TRAIN/dev pair overlap | 54.000 | 108.000 | 137.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
