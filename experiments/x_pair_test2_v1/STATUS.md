# X-PAIR test-2 comparison

All 7,320 full-length Ankh embeddings are complete. Native embedding and scoring
qualification passed for both released checkpoints. The unchanged P/U macro
metric passed its independent numerical oracle. Pair exposure to released
X-fair training and validation is audited in `exposure/AUDIT.json`.

SLURM embedding array `3040577` and scoring array `3040586` completed.
Both checkpoints scored all 3,774,966 frozen candidate pairs. Each scoring
worker had 24 hours and finished well within its allocation.
The primary checkpoint is `multitask_xfair`;
`interaction_xfair` is a prespecified secondary comparison.

Comparison job `3040611` completed successfully. All predictions are frozen,
the C1/C2/C3 comparison and sensitivity analyses are complete, and all 302
original input files and released source weights passed preservation checks.
The production indexing/assembly fixture also passed against full upstream
forward inference on 52 real candidate identities, including long proteins.

The comparison retains all 13 existing competitors and includes paired
intervals against selected 31k, legacy/added cohort breakdowns, C1 development
overlap sensitivity, and exact X-PAIR pair-exposure sensitivity. All outputs
remain in this experiment folder; original inputs and results are read-only.

Selected 31k scored higher than both X-PAIR models on all three macro metrics,
with paired intervals excluding zero. X-PAIR had higher added-C3 point scores;
exploratory subgroup intervals include zero. See `results/INTERPRETATION.md`
for the conclusion and `results/RESULTS.md` for the complete comparison.
