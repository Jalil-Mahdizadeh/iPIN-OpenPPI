# Data-informed component supplement

This is a **post-hoc extension**, written after inspecting the first diagnostic
`RESULTS.json`. The largest-component hypothesis was not supported: excluding
its P and U pairs increased control point performance. The first run identified
825 within-component positives (36.4%) versus 6.6% of U, and a 61-endpoint
component (third by endpoint size) touching 692 positives (30.6%).

Without accessing test rows or changing anything frozen, examine:

- An exact positive-group decomposition for within- versus between-component
  pairs, and the between-component-only P/U sensitivity.
- Removing P and U pairs touching the third-largest component; and removing
  pairs touching either the first- or third-largest components. These are
  data-informed sensitivity analyses, not independent validation or new gates.
- Within/between and first/third-component source composition; conditional
  length-score distributions and within-fixed-length-bin sensitivities.
- Descriptive influence for **every positive-participating development
  component**, ranked by endpoint size (not selectively reporting good cases).
  Per-component positive contributions can overlap; do not sum across them.
- The same 2,000 frozen component draws for the three additional sensitivities.

Retain the first analysis/code/results unchanged. Publish a separate supplement
and report all three sensitivities. The investigation can establish development
concentration and scoring parity, but cannot attribute the exact test-side
mechanism from public test aggregates alone.
