# Graph Report - six_target_comparison_v1  (2026-09-19)

## Corpus Check
- 5 files · ~87,988 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 33 nodes · 73 edges · 6 communities (4 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- summarize
- ComparisonTests
- tuna
- run_comparison.py
- sha
- test_comparison.py

## God Nodes (most connected - your core abstractions)
1. `summarize()` - 11 edges
2. `sha()` - 9 edges
3. `tuna()` - 9 edges
4. `ComparisonTests` - 9 edges
5. `ipin()` - 8 edges
6. `prepare()` - 7 edges
7. `inputs()` - 7 edges
8. `now()` - 6 edges
9. `read()` - 6 edges
10. `write_json()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `ipin()` --calls--> `now()`  [EXTRACTED]
  run_comparison.py → run_comparison.py  _Bridges community 0 → community 2_
- `prepare()` --calls--> `now()`  [EXTRACTED]
  run_comparison.py → run_comparison.py  _Bridges community 0 → community 3_
- `ipin()` --calls--> `sha()`  [EXTRACTED]
  run_comparison.py → run_comparison.py  _Bridges community 4 → community 2_
- `prepare()` --calls--> `sha()`  [EXTRACTED]
  run_comparison.py → run_comparison.py  _Bridges community 4 → community 3_
- `summarize()` --calls--> `sha()`  [EXTRACTED]
  run_comparison.py → run_comparison.py  _Bridges community 4 → community 0_

## Import Cycles
- None detected.

## Communities (6 total, 2 thin omitted)

### Community 0 - "summarize"
Cohesion: 0.28
Nodes (6): concordance(), main(), now(), ranks(), summarize(), Tee

### Community 2 - "tuna"
Cohesion: 0.60
Nodes (5): configure_gpu(), ipin(), record(), tuna(), write_csv()

### Community 3 - "run_comparison.py"
Cohesion: 0.83
Nodes (3): helper(), prepare(), write_json()

### Community 4 - "sha"
Cohesion: 0.83
Nodes (4): inputs(), load_panels(), read(), sha()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ComparisonTests` connect `ComparisonTests` to `test_comparison.py`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `Tee` connect `summarize` to `run_comparison.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `summarize()` connect `summarize` to `tuna`, `run_comparison.py`, `sha`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._