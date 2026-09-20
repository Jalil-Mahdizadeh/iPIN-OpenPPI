---
type: "query"
date: "2026-09-20T13:55:21.199733+00:00"
question: "investigate if there is a meaningful difference between two groups scores."
contributor: "graphify"
outcome: "useful"
source_nodes: ["build_panels.py", "twelve_target_comparison_v1/REPORT.md"]
---

# Q: investigate if there is a meaningful difference between two groups scores.

## Answer

Expanded from original query via graph vocabulary: [context, scores, matched, stratum, comparison, twelve].
Created example/u_context_background_analysis_v1/ as an exploratory analysis of the preserved twelve-target scores. Compared 1850 context U and 1850 background U across 37 matching anchors and 12 targets for three frozen models. Each anchor uses 50x50 context/background comparisons with half credit for ties; average anchors within target then give targets equal weight. No inference, fitting or label changes.
Context wins A: original iPIN 0.5821722222, 95% whole-target bootstrap interval 0.5533833333-0.6103056944, 12/12 targets above .5; optimized 0.5822416667, interval 0.5459611111-0.618675, 10/12; TUnA-retrained 0.5795888889, interval 0.5191775-0.6346111111, 9/12. 100000 bootstrap draws seed20260920. Exact two-sided sign-flip reference tests on 12 target effects with 4096 patterns, Holm-adjusted across models, yield p=.00146484375,.00390625,.03076171875. Independent/symmetric target-effect and exchangeable-target assumptions are approximate: 367 U partner sequences recur across targets, 3307 unique U sequences total. Deliberately selected panels and shared models limit generalization; not confirmatory biological evidence.
388/1850 background candidates (20.97%) meet their own anchor context rule. Comparing against the nonmatching remainder yields A=.60718,.60485,.60360. Both six-target cohorts and leave-one-target-out estimates retain positive average direction. Equal-target length A=.517 (exact values in report), so no exact length equality and no causal location attribution. All context rows passed annotation checks.
Main P-vs-context versus P-vs-background concordance: original .645185 vs .720648; optimized .698611 vs .747593; TUnA .722072 vs .771030. Context therefore gives harder retrieval on average. Context top20 U fraction .595833,.558333,.579167. TUnA has reverse directions for EGFR,BCL2,BECN1; optimized EGFR,CTNNB1.
Independent validator checks all111 anchor rank effects,36 target effects/top20 fractions,nine bootstrap CIs against SciPy,Holm and mixed-tie fixtures. All110 parent artifacts preserved. Newcode,CSVtables,PROTOCOL,REPORT,PNG/PDF/SVG,and finalmanifest closed18 artifacts. Findings are modest score shifts with overlap, not evidence of higher true interaction rates. Root README and docs/reports index link report. Sources: example/u_context_background_analysis_v1/REPORT.md; PROTOCOL.md; summary.csv; INDEPENDENT_VALIDATION.json; FINAL_MANIFEST.json.


## Outcome

- Signal: useful

## Source Nodes

- build_panels.py
- twelve_target_comparison_v1/REPORT.md