# TP53: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [tp53_three_model_scores.csv](tp53_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.516 | 0.478 | 0.824 |
| Average precision | 0.013 | 0.012 | 0.037 |
| Expected first-positive rank (lower is better) | 76.000 | 113.000 | 28.000 |
| Reciprocal rank | 0.013 | 0.009 | 0.036 |
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
| Recovered P@20 | 0.000 | 0.000 | 0.000 |
| Recall@20 | 0.000 | 0.000 | 0.000 |
| Known-positive precision@20 | 0.000 | 0.000 | 0.000 |
| EF@20 | 0.000 | 0.000 | 0.000 |
| NDCG@20 | 0.000 | 0.000 | 0.000 |
| Target success@20 | 0.000 | 0.000 | 0.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| MDM2 | No checked TRAIN/dev pair overlap | 201.000 | 163.000 | 28.000 |
| MDM4 | No checked TRAIN/dev pair overlap | 165.000 | 113.000 | 52.000 |
| EP300 | No checked TRAIN/dev pair overlap | 76.000 | 200.000 | 84.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
