---
type: "query"
date: "2026-09-20T14:59:04.092485+00:00"
question: "just add the best low plausibility U pairs carefully, then re-apply all 3 frozen ipin models + original tuna model. the compare all previous metrics for P + 50 context-matched U, P + 50 background U, P + low-plausibility U, P + context-matched and backround U, P + all U."
contributor: "graphify"
outcome: "useful"
source_nodes: ["tuna()", "metrics.py", "build_panels.py"]
---

# Q: just add the best low plausibility U pairs carefully, then re-apply all 3 frozen ipin models + original tuna model. the compare all previous metrics for P + 50 context-matched U, P + 50 background U, P + low-plausibility U, P + context-matched and backround U, P + all U.

## Answer

Expanded via graph vocabulary: unlabeled context selection panel frozen original tuna comparison metrics. Completed example/twelve_target_comparison_v2: 37 P plus 5550 U, adding 50 low-plausibility U per positive to the unchanged 50 context and 50 background U. User explicitly approved evidence tiers: 1711 compartment-separation additions and 139 weaker EGFR secondary-localization-overlap candidates. Selection uses current UniProt/HPA annotations, twofold length matching, exact-sequence deduplication, IntAct and reciprocal annotation exclusions, and iPIN/original-TUnA training-validation exclusions; no scores choose candidates. Freshly fetched 4012 sequences and recomputed both embedding pipelines. Applied unchanged baseline iPIN, optimized iPIN, TUnA-retrained and original TUnA to all 5587 pairs. Five sets have complete prior retrieval metrics and matched-positive, exposure, homomer and strict-eleven-target sensitivities. Macro PU all150U is 0.7251/0.7544/0.7803/0.8042 in that model order. Adding new U raises macro concordance but lowers MAP slightly and leaves total top10 recovery at 4/7/7/10. 1640 metric rows, 560 macro rows, 740 matched and 740 rank rows, 12000 curves independently validated; all 1850 annotations source-reconciled. 527 tests passed with two core CUDA skips; native GPU scoring qualifications passed. 107 public artifacts closed and 159 historical artifacts preserved. Model registry unchanged; original TUnA remains an external comparator. Current example navigation is example/INDEX.md because the old example/README.md is checksum-bound.

## Outcome

- Signal: useful

## Source Nodes

- tuna()
- metrics.py
- build_panels.py