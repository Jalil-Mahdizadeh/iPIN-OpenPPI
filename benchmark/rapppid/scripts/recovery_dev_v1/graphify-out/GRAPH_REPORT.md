# Graph Report - recovery_dev_v1  (2026-09-17)

## Corpus Check
- 2 files · ~1,384 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 12 nodes · 15 edges · 3 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- evaluate.py
- run.sh
- evaluate

## God Nodes (most connected - your core abstractions)
1. `evaluate()` - 4 edges
2. `check_inputs()` - 3 edges
3. `snapshot()` - 3 edges
4. `copy_exclusive()` - 2 edges
5. `metric_checked()` - 2 edges
6. `save_predictions()` - 2 edges
7. `User-requested C3-DEV evaluation of the failed run's latest saved states. Never…` - 1 edges
8. `run.sh script` - 1 edges
9. `APPTAINER_CACHEDIR` - 1 edges
10. `APPTAINER_TMPDIR` - 1 edges

## Surprising Connections (you probably didn't know these)
- `evaluate()` --calls--> `check_inputs()`  [EXTRACTED]
  evaluate.py → evaluate.py  _Bridges community 0 → community 2_

## Import Cycles
- None detected.

## Communities (3 total, 0 thin omitted)

### Community 0 - "evaluate.py"
Cohesion: 0.60
Nodes (4): check_inputs(), copy_exclusive(), User-requested C3-DEV evaluation of the failed run's latest saved states. Never…, snapshot()

### Community 1 - "run.sh"
Cohesion: 0.50
Nodes (3): APPTAINER_CACHEDIR, APPTAINER_TMPDIR, run.sh script

### Community 2 - "evaluate"
Cohesion: 0.67
Nodes (3): evaluate(), metric_checked(), save_predictions()

## Knowledge Gaps
- **3 isolated node(s):** `run.sh script`, `APPTAINER_CACHEDIR`, `APPTAINER_TMPDIR`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `evaluate()` connect `evaluate` to `evaluate.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `check_inputs()` connect `evaluate.py` to `evaluate`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `run.sh script`, `APPTAINER_CACHEDIR`, `APPTAINER_TMPDIR` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._