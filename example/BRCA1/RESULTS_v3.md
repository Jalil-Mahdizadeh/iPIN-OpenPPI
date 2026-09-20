# BRCA1: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.6267 | 0.0571 | 0.1111 | 1.0000 | 0.3333 | 0.1413 |
| Context | Optimized iPIN | 0.8156 | 0.0855 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Context | TUnA-retrained | 0.9422 | 0.4398 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Context | Original TUnA | 0.9333 | 0.1843 | 0.1667 | 2.0000 | 0.6667 | 0.3152 |
| Background | Original iPIN | 0.7356 | 0.0699 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Background | Optimized iPIN | 0.8978 | 0.1226 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Background | TUnA-retrained | 0.9333 | 0.2114 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Background | Original TUnA | 0.9689 | 0.3547 | 0.3333 | 2.0000 | 0.6667 | 0.4367 |
| Low plausibility | Original iPIN | 0.9111 | 0.2419 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Low plausibility | Optimized iPIN | 0.9889 | 0.5556 | 0.5000 | 3.0000 | 1.0000 | 0.6979 |
| Low plausibility | TUnA-retrained | 0.9911 | 0.5889 | 0.5000 | 3.0000 | 1.0000 | 0.7123 |
| Low plausibility | Original TUnA | 1.0000 | 1.0000 | 1.0000 | 3.0000 | 1.0000 | 1.0000 |
| Context + background | Original iPIN | 0.6811 | 0.0328 | 0.0625 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.8567 | 0.0520 | 0.0667 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.9378 | 0.1671 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Context + background | Original TUnA | 0.9511 | 0.1396 | 0.1250 | 2.0000 | 0.6667 | 0.2837 |
| All U | Original iPIN | 0.7578 | 0.0301 | 0.0588 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.9007 | 0.0497 | 0.0625 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.9556 | 0.1366 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| All U | Original TUnA | 0.9674 | 0.1396 | 0.1250 | 2.0000 | 0.6667 | 0.2837 |

[Expanded input](../twelve_target_comparison_v2/panels/BRCA1/brca1_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/BRCA1/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/brca1_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
