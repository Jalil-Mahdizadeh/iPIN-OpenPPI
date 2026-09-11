---
type: "query"
date: "2026-09-11T10:05:57.840528+00:00"
question: "since a simple PLM pair model was successful, I would like to suggest a model-architecture optimization on the train/development panel. If it showed improvment, we re-test on the test panel. What do you think?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["Protected pair-level PU-R evaluation procedure", "8. Architecture, optimization, and stopping"]
---

# Q: since a simple PLM pair model was successful, I would like to suggest a model-architecture optimization on the train/development panel. If it showed improvment, we re-test on the test panel. What do you think?

## Answer

Expanded via graph vocabulary: architecture optimization development selection protected test evaluation. Support a bounded, separately authorized Phase 2 architecture study, but do not call a second evaluation on the consumed test a new blind confirmation. Test aggregate feedback can influence research choices without test labels entering gradient training; adaptive holdout reuse risks selection bias (Dwork et al., Science 2015, DOI 10.1126/science.aaa9375; Moritz Hardt author explanation https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/). Finite development selection also overfits (Cawley and Talbot 2010 https://www.jmlr.org/papers/v11/cawley10a.html). This does not retrospectively invalidate the unchanged original one-time result, prove every later score is biased, or make the old pairs scientifically useless. Repeated evaluation could only be an explicitly disclosed exploratory/secondary benchmark comparison under a newly authorized protocol; current docs/protocols/PROTECTED_FINAL_TEST_v1.md L94-114 and DEC-0051 L31-36 prohibit reruns, new ledgers, resets and test-triggered tuning. No such action was authorized or executed in this discussion. Recommendation: preserve v1 checkpoints/results, preregister a small fixed-budget train/development-only search with frozen PLM, original linear architecture as comparator and at most two hypothesis-driven heads such as a regularized symmetric low-rank bilinear head and small residual MLP. Refit all comparators within identical training folds with matched tuning budgets/seeds; never use the all-training frozen v1 checkpoint to score held-out folds containing its training examples. Use component/homology-grouped nested validation where support permits, training-only normalization/features and consistent C3/paired/unary controls rather than random pair splits or one best seed. Existing repeatedly explored data remain development even when repartitioned; such validation is internal exploratory evidence, not newly unseen confirmation. Lock the selected model and evaluate it together with the original frozen baseline on a genuinely fresh, separately qualified independent panel. A new appropriate PU panel can confirm ranking improvement; direct-binding claims need direct-binary evidence. If no fresh data are available, report development-only gains without claiming a second protected confirmation. Best immediate next step would be a short Phase 2 protocol covering hypotheses, candidate cap, fairness, split rules, success criterion, stopping and confirmation data before fitting. Only a local graph note is saved; no model, metric, data, frozen protocol, ledger, commit or push change.

## Outcome

- Signal: useful

## Source Nodes

- Protected pair-level PU-R evaluation procedure
- 8. Architecture, optimization, and stopping