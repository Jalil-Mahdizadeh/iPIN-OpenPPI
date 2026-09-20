# BCL2: expanded four-model results

Version 3 target result, from the [twelve-target v2 run](../twelve_target_comparison_v2/REPORT.md). The original panel and prior results are preserved. Each nominated positive now has 50 context, 50 background and 50 low-plausibility U. U remains unknown; EGFR includes an explicitly weaker evidence tier.

| Set | Model | PU | AP | RR | Recovered P @10 | Recall @10 | NDCG @10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Context | Original iPIN | 0.9667 | 0.5055 | 1.0000 | 2.0000 | 0.6667 | 0.6257 |
| Context | Optimized iPIN | 0.9733 | 0.3278 | 0.2500 | 3.0000 | 1.0000 | 0.5249 |
| Context | TUnA-retrained | 0.8844 | 0.1511 | 0.2000 | 1.0000 | 0.3333 | 0.1815 |
| Context | Original TUnA | 0.7844 | 0.1309 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| Background | Original iPIN | 0.9533 | 0.2652 | 0.3333 | 2.0000 | 0.6667 | 0.3911 |
| Background | Optimized iPIN | 0.9711 | 0.3056 | 0.2500 | 3.0000 | 1.0000 | 0.5105 |
| Background | TUnA-retrained | 0.8333 | 0.0851 | 0.0714 | 0.0000 | 0.0000 | 0.0000 |
| Background | Original TUnA | 0.7311 | 0.0582 | 0.0769 | 0.0000 | 0.0000 | 0.0000 |
| Low plausibility | Original iPIN | 0.9467 | 0.2861 | 0.5000 | 1.0000 | 0.3333 | 0.2961 |
| Low plausibility | Optimized iPIN | 0.9911 | 0.5889 | 0.5000 | 3.0000 | 1.0000 | 0.7123 |
| Low plausibility | TUnA-retrained | 0.7978 | 0.0849 | 0.1000 | 1.0000 | 0.3333 | 0.1357 |
| Low plausibility | Original TUnA | 0.5644 | 0.0748 | 0.1667 | 1.0000 | 0.3333 | 0.1672 |
| Context + background | Original iPIN | 0.9600 | 0.2037 | 0.3333 | 1.0000 | 0.3333 | 0.2346 |
| Context + background | Optimized iPIN | 0.9722 | 0.1884 | 0.1429 | 2.0000 | 0.6667 | 0.2977 |
| Context + background | TUnA-retrained | 0.8589 | 0.0563 | 0.0556 | 0.0000 | 0.0000 | 0.0000 |
| Context + background | Original TUnA | 0.7578 | 0.0405 | 0.0625 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original iPIN | 0.9556 | 0.1395 | 0.2500 | 1.0000 | 0.3333 | 0.2021 |
| All U | Optimized iPIN | 0.9785 | 0.1672 | 0.1250 | 2.0000 | 0.6667 | 0.2837 |
| All U | TUnA-retrained | 0.8385 | 0.0350 | 0.0370 | 0.0000 | 0.0000 | 0.0000 |
| All U | Original TUnA | 0.6933 | 0.0257 | 0.0476 | 0.0000 | 0.0000 | 0.0000 |

[Expanded input](../twelve_target_comparison_v2/panels/BCL2/bcl2_ipin_panel.csv) · [Evidence manifest](../twelve_target_comparison_v2/panels/BCL2/panel_manifest.json) · [Four-model scores](../twelve_target_comparison_v2/bcl2_four_model_scores.csv) · [All metrics and sensitivities](../twelve_target_comparison_v2/per_target_metrics.csv)
