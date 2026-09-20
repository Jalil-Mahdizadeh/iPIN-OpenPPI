# Protein-screening examples

The current application compares the **three frozen iPIN models on twelve human
targets: 37 nominated positives and 3,700 unlabeled pairs**. Start with the
[twelve-target report](twelve_target_comparison_v1/REPORT.md),
[metric definitions](twelve_target_comparison_v1/METRICS.md), and
[reproduction guide](twelve_target_comparison_v1/README.md).

| Target | Panel | Three-model results |
| --- | --- | --- |
| ERN1 | [4 P + 400 U](ERN1/ern1_ipin_panel.csv) | [Metrics and ranks](ERN1/RESULTS_v2.md) |
| TP53 | [3 P + 300 U](TP53/tp53_ipin_panel.csv) | [Metrics and ranks](TP53/RESULTS_v2.md) |
| EGFR | [3 P + 300 U](EGFR/egfr_ipin_panel.csv) | [Metrics and ranks](EGFR/RESULTS_v2.md) |
| BCL2 | [3 P + 300 U](BCL2/bcl2_ipin_panel.csv) | [Metrics and ranks](BCL2/RESULTS_v2.md) |
| KEAP1 | [3 P + 300 U](KEAP1/keap1_ipin_panel.csv) | [Metrics and ranks](KEAP1/RESULTS_v2.md) |
| BRCA1 | [3 P + 300 U](BRCA1/brca1_ipin_panel.csv) | [Metrics and ranks](BRCA1/RESULTS_v2.md) |
| KRAS | [3 P + 300 U](KRAS/kras_ipin_panel.csv) | [Metrics and ranks](KRAS/RESULTS_v2.md) |
| CDK2 | [3 P + 300 U](CDK2/cdk2_ipin_panel.csv) | [Metrics and ranks](CDK2/RESULTS_v2.md) |
| HIF1A | [3 P + 300 U](HIF1A/hif1a_ipin_panel.csv) | [Metrics and ranks](HIF1A/RESULTS_v2.md) |
| CTNNB1 | [3 P + 300 U](CTNNB1/ctnnb1_ipin_panel.csv) | [Metrics and ranks](CTNNB1/RESULTS_v2.md) |
| TNFRSF1A | [3 P + 300 U](TNFRSF1A/tnfrsf1a_ipin_panel.csv) | [Metrics and ranks](TNFRSF1A/RESULTS_v2.md) |
| BECN1 | [3 P + 300 U](BECN1/becn1_ipin_panel.csv) | [Metrics and ranks](BECN1/RESULTS_v2.md) |

KRAS, CDK2, HIF1A, CTNNB1, TNFRSF1A, and BECN1 extend the original six targets.
Each has three supported partners and 100 matched/background U controls per
partner. The original ERN1 panel retains its fourth positive, the homodimer.
Training/development exposure and homomer sensitivities are reported explicitly.
These panels measure known-partner retrieval; U is unknown and results are
descriptive biological cases.

## Historical records

The [six-target comparison](six_target_comparison_v1/REPORT.md) contains the
original four-predictor results, including the authors' original TUnA comparator.
Its files and the original six input panels are preserved. The new comparison
uses the three registered iPIN predictors; original TUnA remains in the historical
record. Original target READMEs describe their preparation; `RESULTS_v2.md` and
`*_three_model_scores.csv` contain current inference.

The older `ire1_ipin_panel*.csv` files and scoring scripts are retained examples.
`score_frozen_models.py` and `score_ire1_ipin_panel2.py` retain their historical
two-pooled-model scope. Use the twelve-target pipeline for current three-model
application and arbitrary panel-sequence embedding.
