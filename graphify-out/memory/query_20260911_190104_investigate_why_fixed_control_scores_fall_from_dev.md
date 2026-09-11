---
type: "query"
date: "2026-09-11T19:01:04.100343+00:00"
question: "Investigate why fixed control scores fall from development C3 to test C3, document it, and preserve both frozen models."
contributor: "graphify"
outcome: "useful"
source_nodes: ["deterministic_scores()", "score_interolog_gpu()", "weighted_pairwise_concordance()", "component_draws()", "favorable_mass()"]
---

# Q: Investigate why fixed control scores fall from development C3 to test C3, document it, and preserve both frozen models.

## Answer

Expanded query vocabulary: development, test, component, interolog, length, scoring, control, similarity, evaluation, baseline. Deterministic scoring and weighted concordance paths guided a development-only investigation. See docs/reports/m1/M1_C3_Control_Shift_Investigation_v1.md and artifacts/results/c3_control_shift_investigation_v1. All 1002265 development rows reproduce four deterministic controls exactly; the protected CPU scorer also matches on 10457 development rows. The largest-component-only explanation is unsupported: excluding the 643-protein component improves control point scores. Within-component positives contribute 94.0 percent of the 3-mer development excess over chance; a 61-protein component contributes 70.1 percent of interolog excess. Between-component-only development 3-mer is 0.534520 and affine PLM is 0.740051. These are post-hoc sensitivities, not causal fractions of the dev/test gap. Exact test-side mechanism remains unresolved because no test rows, truth, prediction archives or keys were opened. Actual GH200 GPU used; 38 tests pass; both frozen models and all 210 historical registered entries unchanged. AST-only index refresh used no LLM API tokens.

## Outcome

- Signal: useful

## Source Nodes

- deterministic_scores()
- score_interolog_gpu()
- weighted_pairwise_concordance()
- component_draws()
- favorable_mass()
