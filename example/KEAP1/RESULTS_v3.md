# KEAP1: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.5178 | 0.1261 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Context | Optimized iPIN | 0.5622 | 0.1009 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Context | TUnA-retrained | 0.3667 | 0.0200 | 0.0175 | 0.0000 | 0.0000 | 0.0000 |
| Context | Original TUnA | 0.6711 | 0.1330 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Background | Original iPIN | 0.6356 | 0.0867 | 0.2000 | 1.0000 | 0.3333 | 0.1815 |
| Background | Optimized iPIN | 0.7111 | 0.1382 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Background | TUnA-retrained | 0.5356 | 0.0273 | 0.0256 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original TUnA | 0.7400 | 0.3604 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Original iPIN | 0.7356 | 0.1382 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Low plausibility | Optimized iPIN | 0.7378 | 0.3663 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | TUnA-retrained | 0.4800 | 0.0246 | 0.0238 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Original TUnA | 0.8133 | 0.3711 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Context + background | Original iPIN | 0.5767 | 0.0563 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Context + background | Optimized iPIN | 0.6367 | 0.0664 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| Context + background | TUnA-retrained | 0.4511 | 0.0117 | 0.0105 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.7056 | 0.1234 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| All U | Original iPIN | 0.6296 | 0.0437 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| All U | Optimized iPIN | 0.6704 | 0.0637 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| All U | TUnA-retrained | 0.4607 | 0.0080 | 0.0074 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.7415 | 0.1205 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |

[Expanded input](../twelve_target_comparison_v2/panels/KEAP1/keap1_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/KEAP1/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/keap1_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
