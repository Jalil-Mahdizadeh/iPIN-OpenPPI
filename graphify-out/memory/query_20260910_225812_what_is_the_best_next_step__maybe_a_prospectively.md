---
type: "query"
date: "2026-09-10T22:58:12.858862+00:00"
question: "what is the best next step? maybe a prospectively designed within-anchor partner-specificity test? what do you think?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["Primary PU-retrieval metrics", "Prospective nested component test", "models.py"]
---

# Q: what is the best next step? maybe a prospectively designed within-anchor partner-specificity test? what do you think?

## Answer

Yes. A prospectively designed within-anchor partner-specificity test is my first choice—with one important addition: it must test whether the model learns which proteins belong together, beyond how attractive each protein is as a partner generally.

The corrected C3 concordance of 0.784 justifies investigating this. It does not yet establish biological partner specificity. See the corrected reassessment: docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md:9.

Why within-anchor is necessary but insufficient

Consider an endpoint-only model:
s0(a,b) = u(a) + u(b).

Holding anchor a fixed removes u(a), but u(b) can still rank common, readily assayed, or otherwise favored partners highly. Such a model could perform well without adapting its partner preferences to the anchor.

This concern is supported by sequence-based PPI shortcut analyses and work on node-versus-edge-weighted evaluation:
https://academic.oup.com/bib/article/25/2/bbae076/7621029
https://doi.org/10.1073/pnas.2416646122

The experiment I would run

1. Make the comparison pair-dependent versus endpoint-only.
Use the corrected 150M linear pair head as the principal candidate. Despite its name, it already contains pairwise products, absolute differences, and cosine similarity; it is not an endpoint-only baseline (src/ipin_openppi/stage1/models.py:22).
Compare it against a trained additive endpoint model with a small nonlinear u, under the same training data and budget. Include cheap sequence-length/similarity controls. Do not make another gated-architecture search the main experiment.

2. Freeze a public-training-only, component-blocked study.
Predeclare splits, eligible anchors, candidate pools, seeds, preprocessing, metrics, and success criteria before inspecting performance. Keep C3, with both endpoints withheld from supervised fitting, primary.
Refit the heads and training-dependent preprocessing inside each split; existing checkpoints have already seen the public training data, so simply rescoring them would invalidate a new internal holdout.
Keep protected evaluation sealed. Because this dataset has already been explored, call this a prospectively specified internal diagnostic, not an untouched external confirmation.

3. Give anchors equal weight.
Use macro-averaged within-anchor released-positive-versus-unlabeled concordance, with the benchmark's sampling-design weights. Report coverage and source-specific sensitivity, and use paired uncertainty that respects shared endpoint components.
The existing PU protocol already contains query-level retrieval machinery (docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md:192). Report Recall@K against the actual ranked universe: if candidates are sampled, it is candidate-panel recall, not proteome-wide recall. Unlabeled partners are not established negatives.

4. Add an endpoint-balanced partner-swap check.
For released-positive pairs (A,B) and (C,D), select eligible unlabeled cross-pairs (A,D) and (C,B), then examine raw-score contrast:
D = s(A,B) + s(C,D) - s(A,D) - s(C,B).
Every additive endpoint-only model has D = 0 exactly. A pair-dependent model favoring the observed pairing therefore passes a sharper check than within-anchor ranking alone.
Freeze quartet sampling and dependence-aware inference beforehand; compare against sequence-similarity/length controls and examine observed source effects. Cross-pairs remain unlabeled, and a positive result can still reflect pair-level assay or homology confounding rather than physical compatibility.

5. Decide what result would change the research direction.
Before running, set a minimum useful improvement over the strong endpoint-only baseline, informed by a coverage/synthetic-power audit. A 0.02 macro-concordance gain is an illustrative starting point, not an established threshold.
- Clear, practically useful gains plus a successful swap check: continue targeted partner-specific modeling. This does not establish a benefit from gating.
- Tight uncertainty excluding a useful gain: stop claiming demonstrated partner specificity for this model/representation and consider a different representation or data source.
- Wide uncertainty or inadequate anchor coverage: inconclusive; do not mistake insufficient data for a dead end.

My immediate recommendation is to freeze a short protocol and run an anchor/candidate/quartet feasibility census before fitting anything. The valuable next result is evidence that the score depends meaningfully on the particular pairing, not another increment in pooled concordance.

This is a proposed design only; no experiments, new scientific authorization, or protected evaluation were initiated.

Graphify expanded query tokens: [anchor, partner, endpoint, retrieval, baseline, prospective, split, unlabeled].

## Outcome

- Signal: useful

## Source Nodes

- Primary PU-retrieval metrics
- Prospective nested component test
- models.py