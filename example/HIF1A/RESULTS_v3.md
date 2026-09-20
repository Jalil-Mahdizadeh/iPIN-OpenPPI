# HIF1A: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.6733 | 0.0461 | 0.0667 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.6267 | 0.0647 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Context | TUnA-retrained | 0.6378 | 0.0868 | 0.2000 | 1.0000 | 0.3333 | 0.1815 |
| Context | Original TUnA | 0.5867 | 0.3509 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Background | Original iPIN | 0.7867 | 0.0769 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Background | Optimized iPIN | 0.6778 | 0.0982 | 0.2000 | 1.0000 | 0.3333 | 0.1815 |
| Background | TUnA-retrained | 0.7578 | 0.1132 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Background | Original TUnA | 0.8022 | 0.3717 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Original iPIN | 0.9600 | 0.4911 | 1.0000 | 2.0000 | 0.6667 | 0.6257 |
| Low plausibility | Optimized iPIN | 0.7622 | 0.3854 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | TUnA-retrained | 0.9200 | 0.4150 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Original TUnA | 0.9533 | 0.5143 | 1.0000 | 2.0000 | 0.6667 | 0.6508 |
| Context + background | Original iPIN | 0.7300 | 0.0297 | 0.0455 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.6522 | 0.0413 | 0.0833 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.6978 | 0.0539 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| Context + background | Original TUnA | 0.6944 | 0.3456 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| All U | Original iPIN | 0.8067 | 0.0286 | 0.0455 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.6889 | 0.0386 | 0.0833 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.7719 | 0.0525 | 0.1250 | 1.0000 | 0.3333 | 0.1480 |
| All U | Original TUnA | 0.7807 | 0.3449 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |

[Expanded input](../twelve_target_comparison_v2/panels/HIF1A/hif1a_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/HIF1A/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/hif1a_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
