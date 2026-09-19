# Graph Report - recovery_test_v1  (2026-09-17)

## Corpus Check
- 9 files · ~4,930 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 78 nodes · 239 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- common.py
- model.py
- run.py
- comparison.py
- sha
- score.py
- now
- frozen_scorer.py
- scores
- write
- .scores

## God Nodes (most connected - your core abstractions)
1. `sha()` - 20 edges
2. `read()` - 20 edges
3. `evaluate()` - 15 edges
4. `main()` - 15 edges
5. `write()` - 11 edges
6. `now()` - 10 edges
7. `session_check()` - 10 edges
8. `import_references()` - 10 edges
9. `main()` - 10 edges
10. `open_session()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `evaluate()` --calls--> `bootstrap()`  [EXTRACTED]
  comparison.py → benchmark_metrics.py
- `evaluate()` --calls--> `qualify()`  [EXTRACTED]
  comparison.py → benchmark_metrics.py
- `main()` --calls--> `qualify()`  [EXTRACTED]
  qualify_freeze.py → benchmark_metrics.py
- `evaluate()` --calls--> `now()`  [EXTRACTED]
  comparison.py → common.py
- `import_references()` --calls--> `now()`  [EXTRACTED]
  comparison.py → common.py

## Import Cycles
- None detected.

## Communities (11 total, 1 thin omitted)

### Community 0 - "common.py"
Cohesion: 0.19
Nodes (11): bootstrap(), component_counts(), qualify(), The historical weighted PU metric and paired component draws, on GPU. CPU…, atomic_json(), concordance(), Benchmark-local identities, weighted PU metric and reproducible CUDA setup., landlock() (+3 more)

### Community 1 - "model.py"
Cohesion: 0.24
Nodes (6): optimizer_auxiliary(), ranking_loss(), Fresh native RAPPPID-mult; TRAIN-only weighted PU adaptation and token RNG., restore_optimizer_auxiliary(), step(), Tokens

### Community 2 - "run.py"
Cohesion: 0.58
Nodes (9): container(), copy(), main(), now(), prepare(), read(), record(), sha() (+1 more)

### Community 3 - "comparison.py"
Cohesion: 0.57
Nodes (6): read(), decrypt_truth(), evaluate(), independent_points(), publish(), token_for()

### Community 4 - "sha"
Cohesion: 0.62
Nodes (6): record(), sha(), verify(), fresh(), main(), Build exact singleton caches and freeze this newly authorized test scorer. Only…

### Community 5 - "score.py"
Cohesion: 0.53
Nodes (5): cuda(), cell_path(), relative_record(), main(), Candidate-only scores for all selected seeds and their fixed logit ensemble.

### Community 6 - "now"
Cohesion: 0.60
Nodes (6): now(), bundle_check(), freeze_predictions(), open_session(), session_check(), verify()

### Community 7 - "frozen_scorer.py"
Cohesion: 0.47
Nodes (3): Exactly the three selected recovery states, with unchanged singleton logits., Scorer, learned_digest()

### Community 8 - "scores"
Cohesion: 0.50
Nodes (4): endpoint_cache(), inference_mode, scores(), singleton_head()

### Community 9 - "write"
Cohesion: 0.67
Nodes (3): write(), import_references(), prediction_values()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `read()` connect `comparison.py` to `common.py`, `model.py`, `sha`, `score.py`, `now`, `frozen_scorer.py`, `write`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `sha()` connect `sha` to `common.py`, `model.py`, `comparison.py`, `score.py`, `now`, `frozen_scorer.py`, `write`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `Scorer` connect `frozen_scorer.py` to `.scores`, `comparison.py`, `sha`, `score.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._