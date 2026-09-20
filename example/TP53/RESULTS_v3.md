# TP53: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.4422 | 0.0231 | 0.0227 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.4000 | 0.0208 | 0.0159 | 0.0000 | 0.0000 | 0.0000 |
| Context | TUnA-retrained | 0.7556 | 0.0506 | 0.0435 | 0.0000 | 0.0000 | 0.0000 |
| Context | Original TUnA | 0.7844 | 0.0666 | 0.0667 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original iPIN | 0.5889 | 0.0310 | 0.0303 | 0.0000 | 0.0000 | 0.0000 |
| Background | Optimized iPIN | 0.5556 | 0.0278 | 0.0196 | 0.0000 | 0.0000 | 0.0000 |
| Background | TUnA-retrained | 0.8933 | 0.1259 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| Background | Original TUnA | 0.8933 | 0.1283 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Low plausibility | Original iPIN | 0.7733 | 0.0592 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Optimized iPIN | 0.6556 | 0.0358 | 0.0286 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | TUnA-retrained | 0.9556 | 0.2611 | 0.3333 | 2.0000 | 0.6667 | 0.3827 |
| Low plausibility | Original TUnA | 0.9867 | 0.7778 | 1.0000 | 3.0000 | 1.0000 | 0.9066 |
| Context + background | Original iPIN | 0.5156 | 0.0134 | 0.0132 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.4778 | 0.0120 | 0.0088 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.8244 | 0.0366 | 0.0357 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.8389 | 0.0459 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.6015 | 0.0110 | 0.0112 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.5370 | 0.0091 | 0.0068 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.8681 | 0.0330 | 0.0333 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.8881 | 0.0453 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/TP53/tp53_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/TP53/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/tp53_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
