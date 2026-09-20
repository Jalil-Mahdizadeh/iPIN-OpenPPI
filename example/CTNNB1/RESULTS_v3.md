# CTNNB1: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.8667 | 0.1639 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Context | Optimized iPIN | 0.5756 | 0.0293 | 0.0222 | 0.0000 | 0.0000 | 0.0000 |
| Context | TUnA-retrained | 0.6022 | 0.0393 | 0.0588 | 0.0000 | 0.0000 | 0.0000 |
| Context | Original TUnA | 0.6978 | 0.0452 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original iPIN | 0.9044 | 0.2370 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Background | Optimized iPIN | 0.6244 | 0.0343 | 0.0294 | 0.0000 | 0.0000 | 0.0000 |
| Background | TUnA-retrained | 0.6311 | 0.0678 | 0.1429 | 1.0000 | 0.3333 | 0.1564 |
| Background | Original TUnA | 0.7022 | 0.0489 | 0.0625 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Original iPIN | 0.9444 | 0.4435 | 1.0000 | 1.0000 | 0.3333 | 0.4693 |
| Low plausibility | Optimized iPIN | 0.7844 | 0.0640 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | TUnA-retrained | 0.8244 | 0.2069 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Low plausibility | Original TUnA | 0.7089 | 0.0539 | 0.0769 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original iPIN | 0.8856 | 0.1149 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Context + background | Optimized iPIN | 0.6000 | 0.0160 | 0.0128 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | TUnA-retrained | 0.6167 | 0.0246 | 0.0435 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.7000 | 0.0239 | 0.0278 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.9052 | 0.1088 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| All U | Optimized iPIN | 0.6615 | 0.0128 | 0.0110 | 0.0000 | 0.0000 | 0.0000 |
| All U | TUnA-retrained | 0.6859 | 0.0221 | 0.0417 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.7030 | 0.0167 | 0.0208 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/CTNNB1/ctnnb1_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/CTNNB1/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/ctnnb1_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
