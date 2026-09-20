# CDK2: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.6156 | 0.0529 | 0.1000 | 1.0000 | 0.3333 | 0.1357 |
| Context | Optimized iPIN | 0.8467 | 0.4318 | 1.0000 | 2.0000 | 0.6667 | 0.6173 |
| Context | TUnA-retrained | 0.9044 | 0.1567 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Context | Original TUnA | 0.4422 | 0.0225 | 0.0182 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original iPIN | 0.7422 | 0.0601 | 0.0909 | 0.0000 | 0.0000 | 0.0000 |
| Background | Optimized iPIN | 0.9022 | 0.4411 | 1.0000 | 2.0000 | 0.6667 | 0.6173 |
| Background | TUnA-retrained | 0.9311 | 0.1625 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| Background | Original TUnA | 0.6600 | 0.0365 | 0.0303 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Original iPIN | 0.8867 | 0.3923 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Optimized iPIN | 0.9800 | 0.7500 | 1.0000 | 2.0000 | 0.6667 | 0.7654 |
| Low plausibility | TUnA-retrained | 0.9800 | 0.4206 | 0.5000 | 3.0000 | 1.0000 | 0.6197 |
| Low plausibility | Original TUnA | 0.8844 | 0.1124 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Context + background | Original iPIN | 0.6789 | 0.0287 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.8744 | 0.3906 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Context + background | TUnA-retrained | 0.9178 | 0.0837 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| Context + background | Original TUnA | 0.5511 | 0.0141 | 0.0115 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.7481 | 0.0268 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.9096 | 0.3898 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| All U | TUnA-retrained | 0.9385 | 0.0753 | 0.1000 | 1.0000 | 0.3333 | 0.1357 |
| All U | Original TUnA | 0.6622 | 0.0126 | 0.0108 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/CDK2/cdk2_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/CDK2/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/cdk2_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
