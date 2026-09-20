# BCL2: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [bcl2_three_model_scores.csv](bcl2_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.960 | 0.972 | 0.859 |
| Average precision | 0.204 | 0.188 | 0.056 |
| Expected first-positive rank (lower is better) | 3.000 | 7.000 | 18.000 |
| Reciprocal rank | 0.333 | 0.143 | 0.056 |
| Recovered P@5 | 1.000 | 0.000 | 0.000 |
| Recall@5 | 0.333 | 0.000 | 0.000 |
| Known-positive precision@5 | 0.200 | 0.000 | 0.000 |
| EF@5 | 20.200 | 0.000 | 0.000 |
| NDCG@5 | 0.235 | 0.000 | 0.000 |
| Target success@5 | 1.000 | 0.000 | 0.000 |
| Recovered P@10 | 1.000 | 2.000 | 0.000 |
| Recall@10 | 0.333 | 0.667 | 0.000 |
| Known-positive precision@10 | 0.100 | 0.200 | 0.000 |
| EF@10 | 10.100 | 20.200 | 0.000 |
| NDCG@10 | 0.235 | 0.298 | 0.000 |
| Target success@10 | 1.000 | 1.000 | 0.000 |
| Recovered P@20 | 2.000 | 3.000 | 1.000 |
| Recall@20 | 0.667 | 1.000 | 0.333 |
| Known-positive precision@20 | 0.100 | 0.150 | 0.050 |
| EF@20 | 10.100 | 15.150 | 5.050 |
| NDCG@20 | 0.361 | 0.415 | 0.110 |
| Target success@20 | 1.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| BCL2L11 | No checked TRAIN/dev pair overlap | 12.000 | 7.000 | 18.000 |
| BAD | No checked TRAIN/dev pair overlap | 27.000 | 15.000 | 25.000 |
| BBC3 | No checked TRAIN/dev pair overlap | 3.000 | 9.000 | 90.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
