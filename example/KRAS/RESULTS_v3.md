# KRAS: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.6200 | 0.0327 | 0.0204 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.9022 | 0.1354 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Context | TUnA-retrained | 0.8578 | 0.0831 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Context | Original TUnA | 0.9511 | 0.2103 | 0.1667 | 2.0000 | 0.6667 | 0.3152 |
| Background | Original iPIN | 0.7622 | 0.0507 | 0.0385 | 0.0000 | 0.0000 | 0.0000 |
| Background | Optimized iPIN | 0.9311 | 0.1551 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| Background | TUnA-retrained | 0.9289 | 0.1528 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Background | Original TUnA | 0.9289 | 0.1582 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Low plausibility | Original iPIN | 0.9422 | 0.1797 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Low plausibility | Optimized iPIN | 0.9978 | 0.9167 | 1.0000 | 3.0000 | 1.0000 | 0.9675 |
| Low plausibility | TUnA-retrained | 0.9978 | 0.9167 | 1.0000 | 3.0000 | 1.0000 | 0.9675 |
| Low plausibility | Original TUnA | 0.8422 | 0.0912 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| Context + background | Original iPIN | 0.6911 | 0.0202 | 0.0135 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.9167 | 0.0753 | 0.0667 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.8933 | 0.0569 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.9400 | 0.0993 | 0.0833 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.7748 | 0.0185 | 0.0125 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.9437 | 0.0747 | 0.0667 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.9281 | 0.0565 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.9074 | 0.0489 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/KRAS/kras_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/KRAS/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/kras_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
