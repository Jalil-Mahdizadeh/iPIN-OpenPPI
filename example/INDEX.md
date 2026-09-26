# Current biological examples

The latest application is the [selected-31k follow-up](../artifacts/models/frozen_pair_models_v3/evidence/twelve_targets/REPORT.md)
on the unchanged 5,587-row panel. It adds **iPIN-TUnA-31k**, the primary model
in the [four-model registry](../docs/models/FROZEN_PAIR_MODELS_v3.md), to the
four archived predictors. All-U macro concordance is 0.864008 versus 0.780305
for historical retrained TUnA, with 10/37 versus 7/37 nominated positives found
at ten candidates per target. Original TUnA still leads some retrieval metrics.
Seventeen of 37 positives occur in 31k training P; the report provides a common
exposure-excluded sensitivity. This remains a descriptive application.

The follow-up's [implementation and run records](../experiments/twelve_target_selected_31k_v1/README.md),
[full public scores](../experiments/twelve_target_selected_31k_v1/output/all_twelve_targets_scores.csv),
rank tables and figures are also deposited under `experiments/`.

The underlying [expanded twelve-target, four-model comparison](twelve_target_comparison_v2/REPORT.md) contains
37 nominated positives and 5,550 unlabeled pairs. Each positive has 50 original
context U, 50 original background U and 50 new low-plausibility U. All three frozen
iPIN models and original published TUnA score every pair with fresh embeddings.
The [run index](twelve_target_comparison_v2/README.md) links all target results.

The report compares P against context, background, low-plausibility, context +
background and all U. It includes the full previous retrieval metric suite,
matched-positive comparisons, and exposure/evidence sensitivities. The
[selection rules](twelve_target_comparison_v2/SELECTION.md) distinguish stronger
compartment separation from EGFR's weaker tier; no U is a verified negative.

The [original TUnA investigation](original_tuna_investigation_v1/REPORT.md)
verifies native scoring and examines target contributions, training exposure,
sequence relatives, query replacement, and uncertainty adjustment. EGFR dominates
the net advantage over retrained TUnA; original TRAIN contains analogous positive
pairs between relatives of all three EGFR positives. This supports a plausible
transfer explanation without establishing general superiority or causality.

| Target | P | U | Historical four-model target results |
|---|---:|---:|---|
| ERN1 | 4 | 600 | [Results v3](ERN1/RESULTS_v3.md) |
| TP53 | 3 | 450 | [Results v3](TP53/RESULTS_v3.md) |
| EGFR | 3 | 450 | [Results v3](EGFR/RESULTS_v3.md) |
| BCL2 | 3 | 450 | [Results v3](BCL2/RESULTS_v3.md) |
| KEAP1 | 3 | 450 | [Results v3](KEAP1/RESULTS_v3.md) |
| BRCA1 | 3 | 450 | [Results v3](BRCA1/RESULTS_v3.md) |
| KRAS | 3 | 450 | [Results v3](KRAS/RESULTS_v3.md) |
| CDK2 | 3 | 450 | [Results v3](CDK2/RESULTS_v3.md) |
| HIF1A | 3 | 450 | [Results v3](HIF1A/RESULTS_v3.md) |
| CTNNB1 | 3 | 450 | [Results v3](CTNNB1/RESULTS_v3.md) |
| TNFRSF1A | 3 | 450 | [Results v3](TNFRSF1A/RESULTS_v3.md) |
| BECN1 | 3 | 450 | [Results v3](BECN1/RESULTS_v3.md) |

Historical completed records remain byte-preserved:

- [Original panel index](README.md) and [twelve-target v1 report](twelve_target_comparison_v1/REPORT.md): 100 U per positive, three frozen iPIN models.
- [Six-target four-model report](six_target_comparison_v1/REPORT.md).
- [Context versus background score analysis](u_context_background_analysis_v1/REPORT.md), based on the preserved v1 scores.

The historical [three-model registry](../docs/models/FROZEN_PAIR_MODELS_v2.md) remains unchanged;
the current primary designation is recorded separately in v3.
Large raw sources and fresh embedding arrays stay local; CSV results, evidence,
protocols, figures and checksum manifests are committed.
