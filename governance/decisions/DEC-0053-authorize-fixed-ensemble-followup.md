# DEC-0053: Accept the fixed ensemble for one follow-up test comparison

Date: 2026-09-11. Authority: the user's explicit instruction to act on the
ensemble-level recommendation, apply the selected model to the existing test,
compare it with the baseline, update the repository, commit and push.

This is a **post-development, pre-follow-up-test amendment**, not a prospective
change to the completed optimization search. DEC-0052 and every frozen search
record remain unchanged. Its original gate correctly remains `passed: false`:
two matched individual-seed gains and the individual-seed range rule failed.
The rule compared corresponding seeds, not individual seeds to an ensemble.

For this authorization the prediction unit is the fixed arithmetic-mean
three-seed ensemble. The already-selected `esm2_150m__residual_wide`, epoch 4,
improved C3 development PU concordance from 0.784142246349548 to
0.7994190035230607; its paired 95% interval for the 0.015276757173512734 gain is
[0.0029423942893936103, 0.03445976176606338]. Individual-fit wins and a range
cutoff are retained as diagnostics, not mandatory ensemble-promotion vetoes.
This accepts the particular frozen predictor for testing; it does not establish
reproducible superiority across retrained ensembles or a causal architecture
advantage. Development uncertainty is post-selection, not multiplicity-adjusted.

Authorize exactly [MODEL_OPTIMIZATION_FOLLOWUP_v1](../../docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md):
one bundled evaluation of the existing selected ensemble and its members, paired
against the original baseline ensemble and members on all nine original cells.
C3 ensemble-minus-baseline PU concordance is the sole primary comparison. No
new training, seed selection, ensemble weights, recipe, epoch, data or split.

This supersedes only DEC-0052's individual-seed promotion veto and the dependent
restriction on creating the follow-up namespace. The original failed gate must
not be relabeled passed. A separate ensemble-acceptance record links both
decisions, the completed search freeze, selection and gate. Preserve all seven
completed study registries (179 registered files), original test predictions,
result, receipt, ledger and completion. Never reset the spent original ledger.

Record and freeze this amendment and the complete scorer implementation before
follow-up candidate access. Qualify on synthetic/public/development data first,
including real GPU checkpoint replay. Retain the qualified CPU protected guard,
staged mounts, token checks, prediction freeze before truth, and a new exclusive
follow-up reservation. Failure after reservation consumes this authorization;
no retry or further model/test iteration is authorized automatically.

Publish the result regardless of direction, including non-finite uncertainty
or execution failures. The existing test has already been examined for the
baseline: this is a disclosed benchmark follow-up, not a new unseen holdout or
independent replication. Unlabeled pairs are not negatives; partner specificity
and direct binding remain unresolved. BioPlex remains secondary cross-assay
evidence, outside this comparison. No new test set is required.
