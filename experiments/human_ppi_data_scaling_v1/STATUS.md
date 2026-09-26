# Status

2026-09-26: **All 12 fits and final evaluation completed successfully.**
The final review is [FINAL_REVIEW.md](FINAL_REVIEW.md). The selected ensemble
uses 31,188 P at epoch 1; the fresh 16,799-P control selects epoch 1. Expansion
improves the added test cohorts but lowers all original test1 scores relative
to the fresh control. The C3-test2 macro advantage over that control has a
paired 95% interval including zero. Original artifacts remain preserved.

The completion review verified the saved results and documented the previously
identified C1/U-policy limitations. A separate inference-only audit found a
covariance reload discrepancy with maximum tested metric impact below 0.0003;
see the final review for its measured impact and reproduction record. No new
training or model reselection was performed.

The original startup record follows.

2026-09-25: curation, nested split construction, embedding extension and GPU
qualification completed. Study moved to `experiments/human_ppi_data_scaling_v1/`.
Formal learning-curve training has been submitted; no improvement is claimed.

- Frozen training positive budgets: 16,799 / 20,000 / 25,000 / 31,188.
- Endpoints: 17,583; 583 added, 220 bridge candidates quarantined.
- Original data snapshots verified byte-for-byte; old artifacts remain unchanged.
- All new training pairs are disjoint from every held-out candidate identity.
- Original C1 dev/test candidate overlap is retained, documented, and covered by
  an additional test view that removes development candidate overlap.
- All 17,000 original residue embeddings reused; 583 added with the same frozen
  encoder. The separate pooled embedding fixtures reproduce exactly.
- Real-data gradients and optimizer/RNG restart checks passed on the GH200.
- PU metric and shared-component macro-bootstrap checks passed against independent
  brute-force calculations.

The source and corpus reports are in `audit/`. Execution/job records will be in
`audit/EXECUTION_FREEZE.json` and `runs/SUBMISSION.json`; final tables and plots will
be generated under `runs/results/` by the dependent evaluation job.

SLURM submission: array **2979721** (12 fits, concurrency 4); dependent final job **2979722**. See [STARTUP_REPORT.md](STARTUP_REPORT.md) for the corpus census and execution details.
