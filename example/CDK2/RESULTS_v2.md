# CDK2: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [cdk2_three_model_scores.csv](cdk2_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.679 | 0.874 | 0.918 |
| Average precision | 0.029 | 0.391 | 0.084 |
| Expected first-positive rank (lower is better) | 20.000 | 1.000 | 9.000 |
| Reciprocal rank | 0.050 | 1.000 | 0.111 |
| Recovered P@5 | 0.000 | 1.000 | 0.000 |
| Recall@5 | 0.000 | 0.333 | 0.000 |
| Known-positive precision@5 | 0.000 | 0.200 | 0.000 |
| EF@5 | 0.000 | 20.200 | 0.000 |
| NDCG@5 | 0.000 | 0.469 | 0.000 |
| Target success@5 | 0.000 | 1.000 | 0.000 |
| Recovered P@10 | 0.000 | 1.000 | 1.000 |
| Recall@10 | 0.000 | 0.333 | 0.333 |
| Known-positive precision@10 | 0.000 | 0.100 | 0.100 |
| EF@10 | 0.000 | 10.100 | 10.100 |
| NDCG@10 | 0.000 | 0.469 | 0.141 |
| Target success@10 | 0.000 | 1.000 | 1.000 |
| Recovered P@20 | 1.000 | 2.000 | 1.000 |
| Recall@20 | 0.333 | 0.667 | 0.333 |
| Known-positive precision@20 | 0.050 | 0.100 | 0.050 |
| EF@20 | 5.050 | 10.100 | 5.050 |
| NDCG@20 | 0.107 | 0.589 | 0.141 |
| Target success@20 | 1.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| CCNA2 | No checked TRAIN/dev pair overlap | 130.000 | 14.000 | 37.000 |
| CCNE1 | No checked TRAIN/dev pair overlap | 20.000 | 1.000 | 9.000 |
| CDKN1B | No checked TRAIN/dev pair overlap | 145.000 | 104.000 | 34.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
