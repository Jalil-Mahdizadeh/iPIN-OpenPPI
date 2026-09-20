# KEAP1: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [keap1_three_model_scores.csv](keap1_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.577 | 0.637 | 0.451 |
| Average precision | 0.056 | 0.066 | 0.012 |
| Expected first-positive rank (lower is better) | 7.000 | 6.000 | 95.000 |
| Reciprocal rank | 0.143 | 0.167 | 0.011 |
| Recovered P@5 | 0.000 | 0.000 | 0.000 |
| Recall@5 | 0.000 | 0.000 | 0.000 |
| Known-positive precision@5 | 0.000 | 0.000 | 0.000 |
| EF@5 | 0.000 | 0.000 | 0.000 |
| NDCG@5 | 0.000 | 0.000 | 0.000 |
| Target success@5 | 0.000 | 0.000 | 0.000 |
| Recovered P@10 | 1.000 | 1.000 | 0.000 |
| Recall@10 | 0.333 | 0.333 | 0.000 |
| Known-positive precision@10 | 0.100 | 0.100 | 0.000 |
| EF@10 | 10.100 | 10.100 | 0.000 |
| NDCG@10 | 0.156 | 0.167 | 0.000 |
| Target success@10 | 1.000 | 1.000 | 0.000 |
| Recovered P@20 | 1.000 | 1.000 | 0.000 |
| Recall@20 | 0.333 | 0.333 | 0.000 |
| Known-positive precision@20 | 0.050 | 0.050 | 0.000 |
| EF@20 | 5.050 | 5.050 | 0.000 |
| NDCG@20 | 0.156 | 0.167 | 0.000 |
| Target success@20 | 1.000 | 1.000 | 0.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| NFE2L2 | No checked TRAIN/dev pair overlap | 177.000 | 221.000 | 218.000 |
| CUL3 | No checked TRAIN/dev pair overlap | 203.000 | 106.000 | 187.000 |
| SQSTM1 | DEV_P | 7.000 | 6.000 | 95.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
