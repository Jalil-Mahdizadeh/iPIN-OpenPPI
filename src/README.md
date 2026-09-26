# Source modules

The implementation lives in `ipin_openppi/`. Its modules follow the scientific
pipeline and its independent validation stages:

| Modules | Responsibility |
|---|---|
| `ingestion`, `reconciliation` | Acquire and parse source evidence; reconcile identities and evidence semantics |
| `negative_evidence`, `lambourne_audit`, `tf_isoform_audit` | Audit external evidence and preserve assay-specific eligibility and quarantine rules |
| `sequence_component_audit`, `pre_split_audit`, `component_split` | Audit homology/leakage and construct the frozen endpoint partition |
| `pair_protocol`, `pair_artifacts`, `benchmark` | Define and materialize the weighted positive–unlabeled benchmark |
| `model_governance`, `stage1` | Enforce model/runtime custody, prepare embeddings, and fit the original models and controls |
| `development_evaluation`, `model_optimization` | Release and score development inputs; run the bounded optimization protocol |
| `partner_specificity`, `homology_source`, `composition_order`, `local_diagnostic`, `external_bioplex` | Run separately scoped scientific diagnostics |
| `validation` | Independently check data, protocols, manifests, runtime identity, and completed results |

Core executable entry points are in [scripts/](../scripts/README.md), including
the protected final-test and fixed-ensemble evaluators. Published-method adapters
and their own runners live in [benchmark/](../benchmark/README.md); example
three-model scoring and retrieval analysis live in the
[twelve-target application](../example/twelve_target_comparison_v1/README.md).
The [v3 model cards](../docs/models/FROZEN_PAIR_MODELS_v3.md) define four
preserved predictors, with **iPIN-TUnA-31k** as primary/default for human PPI
ranking. Historical runners retain their original model scope. The
[v3 preservation entry point](../scripts/model/freeze_pair_models_v3.py)
registers the exact selected ensemble and verifies prior releases. Scientific
execution and tests require an accepted SIF.
