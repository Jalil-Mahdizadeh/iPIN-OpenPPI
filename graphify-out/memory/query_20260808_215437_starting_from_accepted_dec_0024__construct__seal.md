---
type: "architecture"
date: "2026-08-08T21:54:37.053673+00:00"
question: "Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work."
contributor: "graphify"
outcome: "useful"
---

# Q: Starting from accepted DEC-0024, construct, seal, independently validate, and freeze the pair-level PU-R benchmark artifacts without model work.

## Answer

DEC-0025 authorized deterministic construction. Production package pair_level_pu_r_benchmark_artifacts_v1 was built from clean commit 043bd73, independently validated from 7dc5e0e with 13/13 checks passing, and accepted/frozen by DEC-0026. It contains public training only, separately encrypted development/candidates/truth, exact 20M sampled-unlabeled cell rows and weights, zero positive-as-unlabeled leakage, and no model work. Development release and protected evaluation remain gated.

## Outcome

- Signal: useful