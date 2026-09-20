# ERN1: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.4600 | 0.0350 | 0.0769 | 0.0000 | 0.0000 | 0.0000 |
| Context | Optimized iPIN | 0.4900 | 0.0579 | 0.1667 | 1.0000 | 0.2500 | 0.1391 |
| Context | TUnA-retrained | 0.5737 | 0.2705 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Context | Original TUnA | 0.5975 | 0.2703 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Background | Original iPIN | 0.4900 | 0.0584 | 0.1667 | 1.0000 | 0.2500 | 0.1391 |
| Background | Optimized iPIN | 0.5200 | 0.0451 | 0.1111 | 1.0000 | 0.2500 | 0.1175 |
| Background | TUnA-retrained | 0.7412 | 0.2909 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Background | Original TUnA | 0.8450 | 0.3005 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Low plausibility | Original iPIN | 0.4763 | 0.0664 | 0.2000 | 1.0000 | 0.2500 | 0.1510 |
| Low plausibility | Optimized iPIN | 0.4888 | 0.0661 | 0.2000 | 1.0000 | 0.2500 | 0.1510 |
| Low plausibility | TUnA-retrained | 0.8538 | 0.3498 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Low plausibility | Original TUnA | 0.9850 | 0.5799 | 1.0000 | 4.0000 | 1.0000 | 0.7992 |
| Context + background | Original iPIN | 0.4750 | 0.0221 | 0.0556 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Optimized iPIN | 0.5050 | 0.0263 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.6575 | 0.2638 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| Context + background | Original TUnA | 0.7212 | 0.2648 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| All U | Original iPIN | 0.4754 | 0.0169 | 0.0455 | 0.0000 | 0.0000 | 0.0000 |
| All U | Optimized iPIN | 0.4996 | 0.0195 | 0.0556 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.7229 | 0.2621 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |
| All U | Original TUnA | 0.8092 | 0.2644 | 1.0000 | 1.0000 | 0.2500 | 0.3904 |

[Expanded input](../twelve_target_comparison_v2/panels/ERN1/ern1_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/ERN1/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/ern1_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
