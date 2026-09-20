# EGFR: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.6267 | 0.0357 | 0.0270 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.6667 | 0.0368 | 0.0244 | 0.0000 | 0.0000 | 0.0000 |
| Context | TUnA-retrained | 0.7778 | 0.0768 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| Context | Original TUnA | 0.9978 | 0.9167 | 1.0000 | 3.0000 | 1.0000 | 0.9675 |
| Background | Original iPIN | 0.6467 | 0.0391 | 0.0323 | 0.0000 | 0.0000 | 0.0000 |
| Background | Optimized iPIN | 0.6000 | 0.0313 | 0.0189 | 0.0000 | 0.0000 | 0.0000 |
| Background | TUnA-retrained | 0.6800 | 0.0543 | 0.0833 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original TUnA | 0.9978 | 0.9167 | 1.0000 | 3.0000 | 1.0000 | 0.9675 |
| Low plausibility | Original iPIN | 0.5933 | 0.0331 | 0.0256 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Optimized iPIN | 0.6889 | 0.0397 | 0.0238 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | TUnA-retrained | 0.7933 | 0.0911 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Low plausibility | Original TUnA | 1.0000 | 1.0000 | 1.0000 | 3.0000 | 1.0000 | 1.0000 |
| Context + background | Original iPIN | 0.6367 | 0.0190 | 0.0149 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.6333 | 0.0172 | 0.0108 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.7289 | 0.0330 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.9978 | 0.8667 | 1.0000 | 3.0000 | 1.0000 | 0.9469 |
| All U | Original iPIN | 0.6222 | 0.0122 | 0.0095 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.6519 | 0.0122 | 0.0075 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.7504 | 0.0249 | 0.0385 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.9985 | 0.8667 | 1.0000 | 3.0000 | 1.0000 | 0.9469 |

[Expanded input](../twelve_target_comparison_v2/panels/EGFR/egfr_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/EGFR/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/egfr_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
