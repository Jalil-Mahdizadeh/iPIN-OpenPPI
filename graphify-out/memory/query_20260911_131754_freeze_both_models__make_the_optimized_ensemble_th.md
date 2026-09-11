---
type: "query"
date: "2026-09-11T13:17:54.148202+00:00"
question: "freeze both models, make the optimized ensemble the best-performing model while retaining the affine model as the original confirmatory baseline. Then, commit and push"
contributor: "graphify"
outcome: "useful"
source_nodes: ["protected_final_core_v1.py", "model_optimization_followup_core_v1.py", "ensemble_columns_exact()"]
---

# Q: freeze both models, make the optimized ensemble the best-performing model while retaining the affine model as the original confirmatory baseline. Then, commit and push

## Answer

Expanded from the original query via graph vocabulary: [model, ensemble, baseline, freeze, checkpoint, registry, selection, score, performance, protected, evaluation, role]. Graph traversal located the original protected scorer and fixed-ensemble follow-up; exact claims and hashes were verified in the underlying immutable registries. DEC-0054 and status/gate v54 designate esm2_150m__residual_wide__epoch04_ensemble3 as best-performing by observed primary C3 score among the two evaluated PLM ensembles; lightweight_esm2_150m_linear__linear_lr3e-4 remains the original confirmatory baseline. Both preserve seeds 20260803, 20260817, 20260831, FP32 raw member inference with equal FP64 averaging, optimized epoch 4 and affine pass 5. No refitting, benchmark scoring, metric recomputation or test truth/pair access occurred. C3 test 0.7892487658713853 to 0.8079478806256634 remains a higher point score with paired gain interval [-0.0013583484514757354, 0.049999798255339706] crossing zero, not statistically conclusive primary superiority. Original failed gate and both earlier evaluation roles remain unchanged. Public artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json SHA256 0b742d43e7da24285a9c2b5587d08cf3c4346073e33dbcaedf604d8a66c9fd83 and its artifact registry freeze exact definitions and new versioned documents. A new local .private/frozen_pair_models_v1/bundle contains 20 byte-identical files: six safe head states, shared encoder/tokenizer, training normalization, aligned embeddings and identities, and source snapshots; files 0400 and directories 0500. Weights/identities are not committed. The freeze audit verifies all 210 registered historical entries across eight studies and both spent ledgers/completions unchanged. All 38 targeted synthetic/safety tests passed in the pinned ARM64 model image with the actual GH200 GPU available, including GPU ensemble inference. Living README, report index, governance index and model cards now distinguish best-performing from original confirmatory roles. Graph update is AST-only, no API cost; the model registry and versioned docs remain authoritative for content not represented in AST nodes. Public changes are prepared for the requested commit and push; no further experiment is authorized.

## Outcome

- Signal: useful

## Source Nodes

- protected_final_core_v1.py
- model_optimization_followup_core_v1.py
- ensemble_columns_exact()