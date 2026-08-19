# ISSUE-0012: Local segment FP32 reconstruction tolerance

**Opened:** 2026-08-19

**Status:** Corrected before artifact production; regression-tested

The first DEC-0041 extraction forward pass completed all 11,900 public-training
endpoints but failed before writing any embedding file. Regrouping FP32 residue
means into segment means and then a residue-count-weighted global mean differed
from the direct FP32 residue mean by `1.52587890625e-05`. The implementation
had imposed an unfrozen `2e-6` audit tolerance.

The two expressions are identical in real arithmetic. Their small difference
is expected from FP32 reduction order and is far below the already frozen
`1e-4` parent-embedding comparison tolerance. No pair score, metric, trigger,
or model output existed.

DEC-0042 authorizes changing only this implementation audit tolerance to
`1e-4`. The segment vectors, matched-global formula, checkpoint, data, scorer
set, metric, and scientific thresholds remain unchanged.

