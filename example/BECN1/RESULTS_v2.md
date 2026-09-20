# BECN1: three frozen iPIN models

Part of the [twelve-target comparison](../twelve_target_comparison_v1/REPORT.md).
Main panel: 3 P and 300 U; U is unknown. Scores and ranks
are in [becn1_three_model_scores.csv](becn1_three_model_scores.csv).

| Metric | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- |
| P/U concordance | 0.754 | 0.792 | 0.843 |
| Average precision | 0.127 | 0.246 | 0.507 |
| Expected first-positive rank (lower is better) | 4.000 | 2.000 | 1.000 |
| Reciprocal rank | 0.250 | 0.500 | 1.000 |
| Recovered P@5 | 1.000 | 1.000 | 2.000 |
| Recall@5 | 0.333 | 0.333 | 0.667 |
| Known-positive precision@5 | 0.200 | 0.200 | 0.400 |
| EF@5 | 20.200 | 20.200 | 40.400 |
| NDCG@5 | 0.202 | 0.296 | 0.671 |
| Target success@5 | 1.000 | 1.000 | 1.000 |
| Recovered P@10 | 1.000 | 2.000 | 2.000 |
| Recall@10 | 0.333 | 0.667 | 0.667 |
| Known-positive precision@10 | 0.100 | 0.200 | 0.200 |
| EF@10 | 10.100 | 20.200 | 20.200 |
| NDCG@10 | 0.202 | 0.437 | 0.671 |
| Target success@10 | 1.000 | 1.000 | 1.000 |
| Recovered P@20 | 2.000 | 2.000 | 2.000 |
| Recall@20 | 0.667 | 0.667 | 0.667 |
| Known-positive precision@20 | 0.100 | 0.100 | 0.100 |
| EF@20 | 10.100 | 10.100 | 10.100 |
| NDCG@20 | 0.315 | 0.437 | 0.671 |
| Target success@20 | 1.000 | 1.000 | 1.000 |

## Positive-partner ranks

| Known partner | Exposure / pair type | Original iPIN | Optimized iPIN | TUnA-retrained |
| --- | --- | --- | --- | --- |
| ATG14 | TRAIN_P | 4.000 | 2.000 | 1.000 |
| UVRAG | TRAIN_P | 17.000 | 9.000 | 4.000 |
| BCL2 | No checked TRAIN/dev pair overlap | 206.000 | 182.000 | 142.000 |

Ranks are one-based and averaged over exact ties. See the [metric protocol](../twelve_target_comparison_v1/METRICS.md)
and [complete metrics](../twelve_target_comparison_v1/per_target_metrics.csv) for
context/background results and exposure/homomer sensitivities. The target-level
result is descriptive, with only 3 nominated positives.
