# EGFR: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [egfr_three_model_scores.csv](egfr_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.637 | 0.633 | 0.729 |
| Average precision | 0.019 | 0.017 | 0.033 |
| Expected first-positive rank (lower is better) | 67.000 | 93.000 | 20.000 |
| Reciprocal rank | 0.015 | 0.011 | 0.050 |
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
| Recovered P@20 | 0.000 | 0.000 | 1.000 |
| Recall@20 | 0.000 | 0.000 | 0.333 |
| Known-positive precision@20 | 0.000 | 0.000 | 0.050 |
| EF@20 | 0.000 | 0.000 | 5.050 |
| NDCG@20 | 0.000 | 0.000 | 0.107 |
| Target success@20 | 0.000 | 0.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| GRB2 | No checked TRAIN/dev pair overlap | 76.000 | 93.000 | 20.000 |
| SHC1 | No checked TRAIN/dev pair overlap | 190.000 | 127.000 | 65.000 |
| CBL | No checked TRAIN/dev pair overlap | 67.000 | 116.000 | 165.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
