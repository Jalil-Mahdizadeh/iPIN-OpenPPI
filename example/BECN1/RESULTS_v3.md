# BECN1: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.7511 | 0.1813 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Context | Optimized iPIN | 0.7978 | 0.4777 | 1.0000 | 2.0000 | 0.6667 | 0.6508 |
| Context | TUnA-retrained | 0.8622 | 0.5159 | 1.0000 | 2.0000 | 0.6667 | 0.6714 |
| Context | Original TUnA | 0.8133 | 0.6782 | 1.0000 | 2.0000 | 0.6667 | 0.7654 |
| Background | Original iPIN | 0.7578 | 0.2595 | 0.5000 | 2.0000 | 0.6667 | 0.4441 |
| Background | Optimized iPIN | 0.7867 | 0.2884 | 0.5000 | 2.0000 | 0.6667 | 0.4632 |
| Background | TUnA-retrained | 0.8244 | 0.6789 | 1.0000 | 2.0000 | 0.6667 | 0.7654 |
| Background | Original TUnA | 0.7689 | 0.3097 | 0.5000 | 2.0000 | 0.6667 | 0.4776 |
| Low plausibility | Original iPIN | 0.8444 | 0.5694 | 1.0000 | 2.0000 | 0.6667 | 0.7039 |
| Low plausibility | Optimized iPIN | 0.8378 | 0.5689 | 1.0000 | 2.0000 | 0.6667 | 0.7039 |
| Low plausibility | TUnA-retrained | 0.8667 | 0.6825 | 1.0000 | 2.0000 | 0.6667 | 0.7654 |
| Low plausibility | Original TUnA | 0.8111 | 0.6780 | 1.0000 | 2.0000 | 0.6667 | 0.7654 |
| Context + background | Original iPIN | 0.7544 | 0.1274 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Context + background | Optimized iPIN | 0.7922 | 0.2462 | 0.5000 | 2.0000 | 0.6667 | 0.4373 |
| Context + background | TUnA-retrained | 0.8433 | 0.5070 | 1.0000 | 2.0000 | 0.6667 | 0.6714 |
| Context + background | Original TUnA | 0.7911 | 0.3053 | 0.5000 | 2.0000 | 0.6667 | 0.4776 |
| All U | Original iPIN | 0.7844 | 0.1240 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| All U | Optimized iPIN | 0.8074 | 0.2373 | 0.5000 | 2.0000 | 0.6667 | 0.4317 |
| All U | TUnA-retrained | 0.8511 | 0.5050 | 1.0000 | 2.0000 | 0.6667 | 0.6714 |
| All U | Original TUnA | 0.7978 | 0.3037 | 0.5000 | 2.0000 | 0.6667 | 0.4776 |

[Expanded input](../twelve_target_comparison_v2/panels/BECN1/becn1_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/BECN1/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/becn1_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
