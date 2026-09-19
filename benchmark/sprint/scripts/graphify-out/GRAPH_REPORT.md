# Graph Report - scripts  (2026-09-17)

## Corpus Check
- 12 files · ~4,397 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 77 nodes · 225 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- pipeline.py
- common.py
- native.py
- read
- score_adapter.py
- comparison.py
- session_check
- scope_guard.py

## God Nodes (most connected - your core abstractions)
1. `sha()` - 15 edges
2. `read()` - 15 edges
3. `evaluate()` - 14 edges
4. `session_check()` - 11 edges
5. `write()` - 10 edges
6. `now()` - 10 edges
7. `verify()` - 10 edges
8. `import_references()` - 10 edges
9. `open_session()` - 9 edges
10. `sha()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `evaluate()` --calls--> `bootstrap()`  [EXTRACTED]
  comparison.py → benchmark_metrics.py
- `evaluate()` --calls--> `qualify()`  [EXTRACTED]
  comparison.py → benchmark_metrics.py
- `freeze_predictions()` --calls--> `sha()`  [EXTRACTED]
  comparison.py → common.py
- `import_references()` --calls--> `sha()`  [EXTRACTED]
  comparison.py → common.py
- `open_session()` --calls--> `sha()`  [EXTRACTED]
  comparison.py → common.py

## Import Cycles
- None detected.

## Communities (8 total, 1 thin omitted)

### Community 0 - "pipeline.py"
Cohesion: 0.32
Nodes (16): container(), Host-side, allowlisted container launcher; no inherited repository mounts., check_initial(), copy(), evaluate(), freeze_bundle(), hsp(), now() (+8 more)

### Community 1 - "common.py"
Cohesion: 0.20
Nodes (11): bootstrap(), component_counts(), qualify(), The historical weighted PU metric and paired component draws, on GPU. CPU…, concordance(), cuda(), Small, benchmark-local I/O and numerical helpers; no repository mutations., landlock() (+3 more)

### Community 2 - "native.py"
Cohesion: 0.29
Nodes (13): canonical(), close(), full_hsp(), hsps(), predict(), qualification(), Stdlib-only native SPRINT execution and source-level qualification., Read blocks, validate syntax and canonicalize only inter-block order. (+5 more)

### Community 3 - "read"
Cohesion: 0.39
Nodes (7): read(), sha(), decrypt_truth(), evaluate(), publish(), token_for(), Prepare TRAIN-only graph and frozen sequence features, without test pairs.

### Community 4 - "score_adapter.py"
Cohesion: 0.57
Nodes (6): now(), write(), cell_path(), collect(), prepare(), Strict candidate-identity adapter. No truth or reference mounts in either phase.

### Community 5 - "comparison.py"
Cohesion: 0.60
Nodes (5): record(), import_references(), open_session(), prediction_values(), relative_record()

### Community 6 - "session_check"
Cohesion: 0.83
Nodes (4): bundle_check(), freeze_predictions(), session_check(), verify()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cuda()` connect `common.py` to `read`, `comparison.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._