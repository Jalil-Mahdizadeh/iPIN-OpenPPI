# Graph Report - six_target_comparison_v1  (2026-09-19)

## Corpus Check
- 16 files · ~93,112 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 49 nodes · 111 edges · 5 communities (3 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `21aae1d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Tee
- ComparisonTests
- now
- Six-target comparison: all embeddings recomputed
- run_comparison.py

## God Nodes (most connected - your core abstractions)
1. `sha()` - 13 edges
2. `summarize()` - 11 edges
3. `now()` - 10 edges
4. `read()` - 10 edges
5. `write_json()` - 10 edges
6. `record()` - 10 edges
7. `tuna()` - 9 edges
8. `ComparisonTests` - 9 edges
9. `ipin()` - 8 edges
10. `main()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `read()`  [EXTRACTED]
  audit_original_exposure.py → run_comparison.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  audit_original_exposure.py → run_comparison.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  validate_results.py → run_comparison.py
- `main()` --calls--> `read()`  [EXTRACTED]
  validate_results.py → run_comparison.py
- `main()` --calls--> `now()`  [EXTRACTED]
  audit_original_exposure.py → run_comparison.py

## Import Cycles
- None detected.

## Communities (5 total, 2 thin omitted)

### Community 2 - "now"
Cohesion: 0.49
Nodes (8): main(), ipin(), now(), record(), write_csv(), write_json(), main(), table()

### Community 3 - "Six-target comparison: all embeddings recomputed"
Cohesion: 0.18
Nodes (9): Execution, Fresh-run policy, Results and checks, Six-target fresh-embedding comparison, Interpretation and exposure limits, Main comparison, Reproducibility and files, Six-target comparison: all embeddings recomputed (+1 more)

### Community 4 - "run_comparison.py"
Cohesion: 0.44
Nodes (11): concordance(), configure_gpu(), helper(), inputs(), load_panels(), prepare(), ranks(), read() (+3 more)

## Knowledge Gaps
- **7 isolated node(s):** `Fresh-run policy`, `Execution`, `Results and checks`, `Main comparison`, `What stands out` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Tee` connect `Tee` to `run_comparison.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `Fresh-run policy`, `Execution`, `Results and checks` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._