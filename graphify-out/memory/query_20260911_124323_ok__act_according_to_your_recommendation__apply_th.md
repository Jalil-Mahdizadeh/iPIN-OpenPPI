---
type: "query"
date: "2026-09-11T12:43:23.518132+00:00"
question: "ok, act according to your recommendation, apply the new model on the test set, compare it with the baseline model, update the repo, commit and push."
contributor: "graphify"
outcome: "useful"
source_nodes: ["protected_final_core_v1.py", "Scorer", "freeze_predictions()"]
---

# Q: ok, act according to your recommendation, apply the new model on the test set, compare it with the baseline model, update the repo, commit and push.

## Answer

Expanded from original query via vocab: [protected, evaluation, ensemble, scorer, freeze, ledger, baseline, test, prepare, guard]. Followed prepare_protected_final_test_v1.py, protected_final_core_v1.py, Scorer, freeze_predictions(), and paired bootstrap primitives. Completed model_optimization_followup_v1 under explicit DEC-0053 user authority. It is a post-development/pre-follow-up-test ensemble-level amendment, not retroactive passing of the original failed gate. The exact existing esm2_150m__residual_wide epoch-4 states, three seeds, and equal FP64 mean of raw FP32 scores were unchanged. No fitting, encoder inference, seed selection, weight tuning or test tuning. Actual GH200 replay of the full C3 development predictions was exact; CPU differences passed frozen tolerances. Scorer freeze 44da994b834a5db4a7c831d85b26f44607d92b7c5058e1176c03049f74b9c9ba at 12:17:58 UTC preceded test candidates; 72 predictions frozen at 12:25:22; separate irreversible ledger reserved 12:26:26; one truth evaluation entered 12:26:39 and completed 12:34:50 on 2026-09-11. Baseline predictions were imported byte-for-byte after candidate scoring. Eight scorers, nine cells, 9,028,821 rows and 2,000 paired sequence-component draws, all finite. Primary C3 baseline 0.7892487658713853, candidate 0.8079478806256634, gain 0.0186991147542781, paired 95% interval [-0.0013583484514757354, 0.049999798255339706]: higher point score, development-consistent direction, but inconclusive primary incremental improvement, not equivalence/no benefit. C2 0.8052990558636478 -> 0.85130120194772, gain 0.04600214608407216 [0.031561086588310416,0.0615592688291959]. C1 0.8434933190102009 -> 0.9160374988139083, gain 0.07254417980370742 [0.06309274546445345,0.08186932142549487]. All nine point gains positive; both C3 source intervals include zero; all C2/C1 source intervals above zero. Supporting cells are descriptive, not alternative primary endpoints. Candidate C3 seeds 0.8018133083264138, 0.7929243419541357, 0.7953788717986493; ensemble outperforms each. New C2/C1 points exceed previously highlighted network control points, so blanket network-dominance statements must not be generalized from the old linear baseline to this optimized ensemble; no new paired candidate-versus-network inference was performed, and shortcut mechanisms remain unresolved. PU concordance is not binding accuracy; partner specificity/direct binding still unresolved; BioPlex remains unchanged secondary cross-assay evidence. The test was previously examined, not a new unseen panel or independent replication. New report docs/reports/m1/M1_Model_Optimization_Followup_v1.md, status/gate v53, root/report/governance/benchmark indexes updated. New result SHA 17ee30e6960f64b3a33a87fbdf12c08d226d25b7a7e76289e8781e03b68110f9. Completed audit passed: 179 historical registered files and original gate/test/custody intact, exact original baseline metric/draw-metadata replay, 72 frozen prediction files verified, nine stored bootstrap groups rechecked. 492 CPU tests across pinned model/data SIFs plus 12 GPU tests cover all 494 repository cases; initial environment routing/scratch failures retained. Known UCX probe prefix preserved raw with a logging-only JSON extraction; no frozen guard/scientific source change. New study closes 31 registered files. Code knowledge graph updated AST-only; non-code artifact JSONs may have no AST nodes. Both tested models preserved, no automatic further model/test iteration. Repository updates are ready for the user's explicitly authorized commit and push; no private rows, weights, keys or predictions are to be committed.

## Outcome

- Signal: useful

## Source Nodes

- protected_final_core_v1.py
- Scorer
- freeze_predictions()