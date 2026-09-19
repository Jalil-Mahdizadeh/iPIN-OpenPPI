# Graph Report - retrained_v1  (2026-09-17)

## Corpus Check
- 13 files · ~5,874 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 77 nodes · 283 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- qualify_training.py
- pipeline.py
- common.py
- sha
- host_guard.py
- benchmark_metrics.py
- train_worker.py
- qualify_orchestration.py
- gpu_guard.py
- read
- submit_jobs.py

## God Nodes (most connected - your core abstractions)
1. `main()` - 22 edges
2. `sha()` - 20 edges
3. `main()` - 18 edges
4. `read()` - 17 edges
5. `write()` - 16 edges
6. `evaluate_development()` - 16 edges
7. `now()` - 15 edges
8. `record()` - 13 edges
9. `main()` - 13 edges
10. `arrays()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `qualify()`  [EXTRACTED]
  qualify_training.py → benchmark_metrics.py
- `main()` --calls--> `now()`  [EXTRACTED]
  freeze_training.py → common.py
- `evaluate_development()` --calls--> `now()`  [EXTRACTED]
  pipeline.py → common.py
- `main()` --calls--> `now()`  [EXTRACTED]
  qualify_orchestration.py → common.py
- `main()` --calls--> `now()`  [EXTRACTED]
  qualify_training.py → common.py

## Import Cycles
- None detected.

## Communities (11 total, 2 thin omitted)

### Community 0 - "qualify_training.py"
Cohesion: 0.25
Nodes (14): inference_mode, endpoint_cache(), optimizer(), orders(), ranking_loss(), Fresh native RAPPPID-mult; TRAIN-only weighted PU adaptation and token RNG., scores(), singleton_head() (+6 more)

### Community 1 - "pipeline.py"
Cohesion: 0.43
Nodes (7): optimizer_auxiliary(), restore_optimizer_auxiliary(), atomic_state(), load_resume(), Atomic recovery and immutable four-epoch checkpoints; C3-DEV only., recovery_payload(), save_resume()

### Community 2 - "common.py"
Cohesion: 0.48
Nodes (5): arrays(), now(), Benchmark-local identities, weighted PU metric and reproducible CUDA setup., main(), Copy fixed TRAIN/C3-DEV inputs and fit a TRAIN-only SentencePiece model.

### Community 3 - "sha"
Cohesion: 0.62
Nodes (6): record(), sha(), verify(), main(), Freeze the qualified 20-epoch TRAIN/C3-DEV-only recipe before submission., main()

### Community 4 - "host_guard.py"
Cohesion: 0.62
Nodes (6): main(), Verify the training-only execution freeze without opening test data., read(), record(), sha(), verify()

### Community 5 - "benchmark_metrics.py"
Cohesion: 0.60
Nodes (5): bootstrap(), component_counts(), qualify(), The historical weighted PU metric and paired component draws, on GPU. CPU…, concordance()

### Community 6 - "train_worker.py"
Cohesion: 0.60
Nodes (5): atomic_json(), write(), fresh(), main(), Three independent TRAIN-only runs, retained every four epochs; never test.

### Community 7 - "qualify_orchestration.py"
Cohesion: 0.60
Nodes (5): cuda(), learned_digest(), evaluate_development(), main(), Exercise retained checkpoints and full-size reports using TRAIN-only fixtures.…

### Community 8 - "gpu_guard.py"
Cohesion: 0.50
Nodes (4): landlock(), Separately qualified network/process restrictions for single-GPU scoring.…, Permit CUDA's own /proc and driver views, deny other processes' trees. Native…, restrict()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `qualify_training.py` to `pipeline.py`, `common.py`, `sha`, `benchmark_metrics.py`, `train_worker.py`, `qualify_orchestration.py`, `read`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `read()` connect `read` to `qualify_training.py`, `pipeline.py`, `common.py`, `sha`, `train_worker.py`, `qualify_orchestration.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `sha()` connect `sha` to `qualify_training.py`, `pipeline.py`, `common.py`, `train_worker.py`, `qualify_orchestration.py`, `read`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._