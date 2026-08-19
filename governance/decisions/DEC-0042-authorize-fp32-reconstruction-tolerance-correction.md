# DEC-0042: Authorize FP32 reconstruction-tolerance correction

**Date:** 2026-08-19

**Status:** Accepted and effective for a narrow pre-artifact implementation correction

Authorize replacement of the local extractor's unfrozen `2e-6` numerical audit
tolerance with `1e-4` for comparing two mathematically equivalent FP32 reduction
orders: direct residue mean versus residue-count-weighted segment means.

The failed attempt completed its forward pass but wrote no embedding artifact
and generated no pair score or metric. The observed maximum difference was
`1.52587890625e-05`. The new tolerance is an ordinary FP32 consistency bound
and matches the already implemented parent-pooled comparison tolerance.

This decision changes no representation, vector, scorer, split, input, metric,
trigger, Phase B condition, or scientific interpretation. The rerun must still
record the exact observed difference and independently reconstruct every
matched-global vector from retained segment vectors and lengths.

All prohibitions and public-only boundaries in DEC-0040 and DEC-0041 remain
effective.

