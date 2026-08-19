# DEC-0043: Authorize FP64 local-cosine reductions

**Date:** 2026-08-19

**Status:** Accepted and effective for a pre-score arithmetic-precision correction

Authorize the local GPU scorer to promote the retained FP32 segment and matched-
global vectors to FP64 before L2 normalization, cosine matrix multiplication,
maximum, and top-four reduction.

The first scoring attempt wrote no score or metric artifact. Its deterministic
100-pair CPU/GPU audit found a maximum difference of
`0.0004219086689020157` because the GPU implementation used FP32 arithmetic and
the exact ordinary-cosine reference used FP64 arithmetic. The correction makes
the GPU implement that reference directly.

This changes no retained embedding bit, formula, scorer, pair row, weight,
metric, trigger, or scientific criterion. The retry must retain the 100-pair
audit and fail unless its maximum FP64 CPU/GPU difference is at most `2e-6`.

All DEC-0040 through DEC-0042 boundaries and prohibitions remain effective.

