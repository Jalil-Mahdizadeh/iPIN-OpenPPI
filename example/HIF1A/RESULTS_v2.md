# HIF1A: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [hif1a_three_model_scores.csv](hif1a_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.730 | 0.652 | 0.698 |
| Average precision | 0.030 | 0.041 | 0.054 |
| Expected first-positive rank (lower is better) | 22.000 | 12.000 | 8.000 |
| Reciprocal rank | 0.045 | 0.083 | 0.125 |
| Recovered P@5 | 0.000 | 0.000 | 0.000 |
| Recall@5 | 0.000 | 0.000 | 0.000 |
| Known-positive precision@5 | 0.000 | 0.000 | 0.000 |
| EF@5 | 0.000 | 0.000 | 0.000 |
| NDCG@5 | 0.000 | 0.000 | 0.000 |
| Target success@5 | 0.000 | 0.000 | 0.000 |
| Recovered P@10 | 0.000 | 0.000 | 1.000 |
| Recall@10 | 0.000 | 0.000 | 0.333 |
| Known-positive precision@10 | 0.000 | 0.000 | 0.100 |
| EF@10 | 0.000 | 0.000 | 10.100 |
| NDCG@10 | 0.000 | 0.000 | 0.148 |
| Target success@10 | 0.000 | 0.000 | 1.000 |
| Recovered P@20 | 0.000 | 1.000 | 1.000 |
| Recall@20 | 0.000 | 0.333 | 0.333 |
| Known-positive precision@20 | 0.000 | 0.050 | 0.050 |
| EF@20 | 0.000 | 5.050 | 5.050 |
| NDCG@20 | 0.000 | 0.127 | 0.148 |
| Target success@20 | 0.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| ARNT | No checked TRAIN/dev pair overlap | 100.000 | 72.000 | 8.000 |
| VHL | No checked TRAIN/dev pair overlap | 22.000 | 12.000 | 153.000 |
| EP300 | No checked TRAIN/dev pair overlap | 127.000 | 235.000 | 117.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
