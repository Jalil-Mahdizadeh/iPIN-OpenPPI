---
type: "query"
date: "2026-09-20T10:54:55.024848+00:00"
question: "freeze tuna-retrained as the third ipin model."
contributor: "graphify"
outcome: "useful"
source_nodes: ["FROZEN_PAIR_MODELS_v1.md", "tuna/scripts/frozen_scorer.py"]
---

# Q: freeze tuna-retrained as the third ipin model.

## Answer

Expanded query from graph vocabulary: [tuna, frozen, registry, checkpoint, ensemble, covariance, preservation]. Registered tuna_retrained_ensemble as the third frozen iPIN model under DEC-0055 in artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json, documented in docs/models/FROZEN_PAIR_MODELS_v2.md and governance/PROJECT_STATUS_v55.md. Its aliases are tuna-retrained and ipin_tuna_retrained. Preserved the epoch-4 states for seeds 20260803, 20260817, and 20260831, including trained GP covariance; prediction is the equal FP64 mean of FP32 mean-field-adjusted logits without sigmoid. New local read-only bundle: .private/frozen_pair_models_v2/bundle. Models 1 and 2 and the shared encoder remain in the unchanged v1 bundle. Both release and historical TUnA evidence checks passed. All three runtime states match the selected training tensors exactly; synthetic native/factorized maximum score error is 8.344650268554688e-7. Validation: 535 tests passed, 3 CUDA-only tests skipped. No training, encoder inference, benchmark scoring, truth access, or metric recomputation occurred. C3 concordance remains 0.8158745071491785; its paired gain over optimized pooled iPIN includes zero. The checksum-bound scripts/model/README.md is historical and must remain untouched; current model entry points are indexed in scripts/README.md.

## Outcome

- Signal: useful

## Source Nodes

- FROZEN_PAIR_MODELS_v1.md
- tuna/scripts/frozen_scorer.py