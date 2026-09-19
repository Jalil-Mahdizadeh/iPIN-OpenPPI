# EF-oriented training: separate, non-replacing experiment

This directory is independent of `combo/`. Existing models, checkpoints,
predictions, and reports are read-only references, not superseded artifacts.

The experiment is complete. Start with [FINDINGS.md](FINDINGS.md) for the
interpretation and concise comparison, or [REPORT.md](REPORT.md) for all models
and budgets. No existing model was promoted, replaced, or overwritten.

The prospective experiment has three parts:

1. Audit saved epoch-4/8 iPIN and retrained-TUnA C3-development predictions by
   EF/Hits/Recall@10/20/30. TUnA remains a development-only checkpoint diagnostic.
2. Train the **same optimized-iPIN architecture**, with the same frozen ESM-2
   embeddings and original hyperparameters, using query-balanced comparisons.
3. Train the matched variant with a bounded extra weight on top-ranked U in
   complete existing TRAIN query lists. No U is declared a true negative.

Three seeds and eight epochs are specified in `protocol.json`; ensemble
checkpoint selection and choice of the primary variant use only C3-development
macro EF@20. Existing candidate lists, labels, and sequence partitions remain
unchanged. No full-pool or six-target evaluation is authorized in this run.

After selection is frozen, the three prespecified iPIN ablations are scored on
C1/C2/C3 test. Compare with preserved baseline iPIN, optimized iPIN, retrained
TUnA, and the existing 55:45 combo. Test results never change the selected winner.

Both new variants start from identical per-seed random initializations and have
identical optimization budgets. Their first epoch is identical; only the
shortlist weighting differs from epoch 2 onward. Historical checkpoints have
only epoch-4/8 evaluation available, whereas new variants save all eight epochs;
this selection-budget difference will be disclosed.

Outputs are exclusive-create. The launcher mounts the repository read-only and
only this directory writable. Source/result/checkpoint hashes are checked before
and after execution. No deletion, renaming, or replacement of current results is
part of this study. A disappointing result will be retained and reported.

Phases: `qualify`, `prepare`, `checkpoint-audit`, `train`, `select`, `score`,
`evaluate`, `audit`, `report`. Logs, protocols, new checkpoints, and results all
remain here. GPU use is allowed; no new SIF or embeddings are required.
