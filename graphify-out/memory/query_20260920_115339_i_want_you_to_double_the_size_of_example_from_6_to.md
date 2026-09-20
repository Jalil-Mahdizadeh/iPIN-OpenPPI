---
type: "query"
date: "2026-09-20T11:53:39.114287+00:00"
question: "i want you to double the size of example from 6 to 12, apply all three frozen ipin models, calculate all metrics you mentioned + PU concordance, update all files and docs. ask questions if clarifications needed."
contributor: "graphify"
outcome: "useful"
source_nodes: ["run_comparison.py", "analysis_outputs.py", "validate_results.py", "build_panels.py"]
---

# Q: i want you to double the size of example from 6 to 12, apply all three frozen ipin models, calculate all metrics you mentioned + PU concordance, update all files and docs. ask questions if clarifications needed.

## Answer

Expanded graph vocabulary: [six, target, comparison, panel, prepare, frozen, scorer, unlabeled, selection, model]. The user explicitly chose six biologically diverse human targets using the existing panel design. Completed example/twelve_target_comparison_v1: added KRAS, CDK2, HIF1A, CTNNB1, TNFRSF1A, BECN1, with three supported positives and 300 U each. All twelve panels contain 37 P and 3700 U (3737 pairs). Original six files and frozen v1/v2 releases preserved. Newly fetched 3344 canonical human sequences, recomputed both ESM pipelines and all endpoint features, scored all three exact frozen ensembles with no training/calibration/GP refit. Catalogue hash faf2d585dbfee34ca3fe19487bc7a821f744014cdcdb94e95e4b657097110878 verified before/after. Added tie-aware P/U concordance, threshold AP/macro MAP, first-positive rank, reciprocal rank/MRR, recovered counts/recall/known-positive precision/EF/NDCG/target success at K=5,10,20, plus K=1..50 curves. Computed all/context/background controls, five exposure/homomer subsets, all/original/additional target cohorts, and each positive's own matched controls. Explicit TRAIN-P exposures: BECN1-ATG14 and BECN1-UVRAG; existing DEV-P: KEAP1-SQSTM1. Main mean P/U concordance baseline .6829166667, optimized .7231018519, retrained TUnA .7465509259. MAP .0575587136, .1097055484, .1131992322; top20 recovered P 9/37,13/37,9/37. Independent scikit-learn/combinatorial validator checked 540 target metric rows,333 matched rows,135 macro rows,1800 curve rows,111 positive ranks,11211 model scores,source/identity/exposure/control matching and artifact hashes.541 tests passed,3 CUDA-only skips; actual GPU native-forward/order-symmetry/unchanged-buffer qualifications passed. Original six pooled scores identical; TUnA max FP32 score difference 1.13e-5 with no rank changes. Report,12 target RESULTS_v2,6 new panel READMEs,root example index,PDF/SVG/PNG figure and current project documentation updated. RUN_MANIFEST closes110 public artifacts and records all runtime hashes. Graph AST refreshed to5677 nodes13305 edges. Frozen cards and historical results must not be edited: current example results are versioned separately. No protected-test labels were opened. Useful sources: new comparison README,REPORT,METRICS,AUTHORIZATION,INDEPENDENT_VALIDATION,RUN_MANIFEST and source scripts.

## Outcome

- Signal: useful

## Source Nodes

- run_comparison.py
- analysis_outputs.py
- validate_results.py
- build_panels.py