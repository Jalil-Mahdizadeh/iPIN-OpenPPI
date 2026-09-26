# Released X-PAIR on frozen test-2

This experiment applies the released X-PAIR default multitask model and its
interaction-only X-fair counterpart to the unchanged human C1/C2/C3 test-2
candidates. The primary X-PAIR predictor is `multitask_xfair`; the secondary
`interaction_xfair` is reported independently, without test-based selection.
The comparator is the existing iPIN-TUnA-31k ensemble, with the previous
13-predictor comparison retained for context.

All new files are contained here. Existing data, checkpoints and results are
read-only. No fitting, fine-tuning, score calibration or checkpoint selection is
performed. Inference uses full protein sequences through the upstream-supported
all-length policy; length coverage and score qualification are recorded.

The primary metric is the established equal-cohort macro of design-weighted
P-versus-U concordance, with C3 primary and C1/C2 secondary. U is unlabeled.
The original C1 development-overlap sensitivity is retained. Released X-PAIR
training/validation exposure is audited separately; original test-2 labels and
candidate membership are preserved. Test-2 remains a historical follow-up.

Upstream: https://gitlab.lcqb.upmc.fr/srescalli/X-PAIR
Pinned source commit: `897646a4a768acd488f4163ff07dd5a1183d52b1`.
Datasets: https://doi.org/10.5281/zenodo.21457017.

See `STATUS.md`, `PROTOCOL.json`, qualification and provenance records, and
`results/` for execution status and the completed comparison.

Completed comparison: [interpretation](results/INTERPRETATION.md),
[all predictor results](results/RESULTS.md), and
[C3 plot](results/C3_comparison.png). Selected 31k leads both released X-PAIR
models on the three macro scores. The added C3 cohort favors X-PAIR by point
estimate, with exploratory intervals spanning zero.
