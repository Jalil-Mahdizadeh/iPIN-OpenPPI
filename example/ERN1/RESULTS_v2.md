# ERN1: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 4 P and 400 U; U is unknown. Scores and ranks
are in [ern1_three_model_scores.csv](ern1_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.475 | 0.505 | 0.658 |
| Average precision | 0.022 | 0.026 | 0.264 |
| Expected first-positive rank (lower is better) | 18.000 | 14.000 | 1.000 |
| Reciprocal rank | 0.056 | 0.071 | 1.000 |
| Recovered P@5 | 0.000 | 0.000 | 1.000 |
| Recall@5 | 0.000 | 0.000 | 0.250 |
| Known-positive precision@5 | 0.000 | 0.000 | 0.200 |
| EF@5 | 0.000 | 0.000 | 20.200 |
| NDCG@5 | 0.000 | 0.000 | 0.390 |
| Target success@5 | 0.000 | 0.000 | 1.000 |
| Recovered P@10 | 0.000 | 0.000 | 1.000 |
| Recall@10 | 0.000 | 0.000 | 0.250 |
| Known-positive precision@10 | 0.000 | 0.000 | 0.100 |
| EF@10 | 0.000 | 0.000 | 10.100 |
| NDCG@10 | 0.000 | 0.000 | 0.390 |
| Target success@10 | 0.000 | 0.000 | 1.000 |
| Recovered P@20 | 1.000 | 1.000 | 1.000 |
| Recall@20 | 0.250 | 0.250 | 0.250 |
| Known-positive precision@20 | 0.050 | 0.050 | 0.050 |
| EF@20 | 5.050 | 5.050 | 5.050 |
| NDCG@20 | 0.092 | 0.100 | 0.390 |
| Target success@20 | 1.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| ERN1 | homomer | 18.000 | 14.000 | 1.000 |
| HSPA5 | No checked TRAIN/dev pair overlap | 348.000 | 259.000 | 325.000 |
| PDIA6 | No checked TRAIN/dev pair overlap | 170.000 | 280.000 | 123.000 |
| SEC61A1 | No checked TRAIN/dev pair overlap | 314.000 | 249.000 | 109.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 4 nominated positives.
