# KRAS: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [kras_three_model_scores.csv](kras_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.691 | 0.917 | 0.893 |
| Average precision | 0.020 | 0.075 | 0.057 |
| Expected first-positive rank (lower is better) | 74.000 | 15.000 | 21.000 |
| Reciprocal rank | 0.014 | 0.067 | 0.048 |
| Recovered P@5 | 0.000 | 0.000 | 0.000 |
| Recall@5 | 0.000 | 0.000 | 0.000 |
| Known-positive precision@5 | 0.000 | 0.000 | 0.000 |
| EF@5 | 0.000 | 0.000 | 0.000 |
| NDCG@5 | 0.000 | 0.000 | 0.000 |
| Target success@5 | 0.000 | 0.000 | 0.000 |
| Recovered P@10 | 0.000 | 0.000 | 0.000 |
| Recall@10 | 0.000 | 0.000 | 0.000 |
| Known-positive precision@10 | 0.000 | 0.000 | 0.000 |
| EF@10 | 0.000 | 0.000 | 0.000 |
| NDCG@10 | 0.000 | 0.000 | 0.000 |
| Target success@10 | 0.000 | 0.000 | 0.000 |
| Recovered P@20 | 0.000 | 1.000 | 0.000 |
| Recall@20 | 0.000 | 0.333 | 0.000 |
| Known-positive precision@20 | 0.000 | 0.050 | 0.000 |
| EF@20 | 0.000 | 5.050 | 0.000 |
| NDCG@20 | 0.000 | 0.117 | 0.000 |
| Target success@20 | 0.000 | 1.000 | 0.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| RAF1 | No checked TRAIN/dev pair overlap | 74.000 | 15.000 | 21.000 |
| BRAF | No checked TRAIN/dev pair overlap | 99.000 | 22.000 | 48.000 |
| ARAF | No checked TRAIN/dev pair overlap | 111.000 | 44.000 | 33.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
