---
type: "query"
date: "2026-09-11T11:23:32.291838+00:00"
question: "alright! 1- Heavily de-emphasize the BioPlex experiment. 2- Prospectively amend the repo’s one-shot protocol while preserving the original evaluation and its records. 3- Initiate model-architecture/parameter optimization experiments and try diffent models, architecture, parameters, etc., select the best performing development-based model, and re-test it on the test panel if it outperforms the baselone on the development panel. No new test set needed. First, ask questions if more clarifications needed."
contributor: "graphify"
outcome: "useful"
source_nodes: ["PairHead", "train_one", "bootstrap", "gate"]
---

# Q: alright! 1- Heavily de-emphasize the BioPlex experiment. 2- Prospectively amend the repo’s one-shot protocol while preserving the original evaluation and its records. 3- Initiate model-architecture/parameter optimization experiments and try diffent models, architecture, parameters, etc., select the best performing development-based model, and re-test it on the test panel if it outperforms the baselone on the development panel. No new test set needed. First, ask questions if more clarifications needed.

## Answer

Expanded from original query via graph vocab: [training, development, selection, architecture, optimization, embedding, checkpoint, gpu, protected, protocol, baseline, model]. Graph traversal located the frozen Stage 1 training, embedding identity correction and protected-evaluation dependencies; numerical findings below come from actual versioned run artifacts, not inferred graph edges. DEC-0052 prospectively amends the one-shot rule, preserves all 148 registered prior-study files and the original spent ledger, and de-emphasizes BioPlex as secondary cross-assay evidence. User chose a two-GPU-hour cap and stable multi-seed gain with positive paired 95% interval. New model_optimization_v1 completed 24 fixed recipes, four promoted recipes across three seeds, 36 fits and 168 epochs on NVIDIA GH200; GPU process 175.4 seconds. Search freeze c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67 preceded first fit. A pre-fit pytest plugin startup failure was preserved and repaired before any fit; no scientific rules changed. Best C3 development ensemble is esm2_150m__residual_wide at epoch 4, 498053 parameters/head: 0.799419 vs original 0.784142, gain 0.015277 with paired interval [0.002942,0.034460]. However, matched seed gains [0.018326,-0.003437,-0.005677] and range 0.021207 fail predeclared all-seed improvement and range<=0.02 conditions. No fallback, new search, protected test access, follow-up ledger, baseline replacement, commit or push. Positive ensemble result is promising development evidence, not a dead-end verdict or stable validated replacement. 11 GPU fixtures and 68 CPU tests passed; 32 full-panel paired-bootstrap reference draws agree within 3.07e-12; all 8 ensemble groups replay exactly. README/report index and governance v52 updated. See docs/reports/m1/M1_Model_Optimization_v1.md, docs/protocols/MODEL_OPTIMIZATION_v1.md, and artifacts/results/model_optimization_v1/RESULTS.json. Existing test remains previously evaluated, not fresh; conditional follow-up was not triggered.

## Outcome

- Signal: useful

## Source Nodes

- PairHead
- train_one
- bootstrap
- gate