# ISSUE-0013: Local cosine GPU reduction precision

**Opened:** 2026-08-19

**Status:** Correction authorized before score production

The first nested-C3 scoring attempt failed its prespecified CPU/GPU formula
check before writing any score or metric artifact. The retained segment vectors
are FP32. The production GPU path also normalized and multiplied them in FP32,
while the frozen ordinary-cosine CPU reference promoted the retained values to
FP64. Across the deterministic 100-pair audit sample, the maximum difference
was `0.0004219086689020157`.

DEC-0043 authorizes FP64 arithmetic for cosine normalization, matrix products,
top-four reduction, and matched-global cosine on the unchanged retained FP32
vectors. This aligns execution with the exact frozen mathematical formula. No
score, metric, trigger, or Phase B artifact existed when the correction was
authorized.

