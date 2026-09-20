# TNFRSF1A: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.5756 | 0.0383 | 0.0500 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.7267 | 0.3627 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Context | TUnA-retrained | 0.5000 | 0.0985 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Context | Original TUnA | 0.4844 | 0.0245 | 0.0222 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original iPIN | 0.6444 | 0.0514 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Background | Optimized iPIN | 0.7933 | 0.2116 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Background | TUnA-retrained | 0.5622 | 0.1291 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Background | Original TUnA | 0.6400 | 0.0342 | 0.0263 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Original iPIN | 0.7000 | 0.0758 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Low plausibility | Optimized iPIN | 0.8911 | 0.4296 | 1.0000 | 2.0000 | 0.6667 | 0.6105 |
| Low plausibility | TUnA-retrained | 0.7133 | 0.3835 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Original TUnA | 0.9800 | 0.4444 | 0.5000 | 3.0000 | 1.0000 | 0.6395 |
| Context + background | Original iPIN | 0.6100 | 0.0224 | 0.0303 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.7600 | 0.1848 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Context + background | TUnA-retrained | 0.5311 | 0.0639 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| Context + background | Original TUnA | 0.5622 | 0.0144 | 0.0122 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.6400 | 0.0175 | 0.0250 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.8037 | 0.1823 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| All U | TUnA-retrained | 0.5919 | 0.0624 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| All U | Original TUnA | 0.7015 | 0.0141 | 0.0120 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/TNFRSF1A/tnfrsf1a_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/TNFRSF1A/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/tnfrsf1a_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
