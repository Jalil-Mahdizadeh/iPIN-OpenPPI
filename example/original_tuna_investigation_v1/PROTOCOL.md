# Original TUnA example investigation

This is an exploratory investigation requested after inspecting the completed
twelve-target v2 comparison. It is not a new holdout evaluation, model-selection
round, or prespecified confirmatory hypothesis test. The initial inspection
already showed substantial EGFR influence and a remaining advantage after exact
pair-exposure exclusions. No models, candidate panels, labels, or completed
results are changed.

## Questions and fixed diagnostics

1. Decompose original-versus-retrained differences by target and candidate set.
   Show leave-one-target-out summaries, known-positive ranks, and paired
   target-bootstrap intervals (100,000 draws, seed 20260920) for PU concordance
   and AP. Targets receive equal weight, as in the parent comparison. These
   intervals describe instability within twelve deliberately selected targets;
   they are not population confidence guarantees. Shared partners and purposive
   target selection further limit independence assumptions.
2. Audit documented original TRAIN/validation endpoint exposure by accession and
   exact sequence, separately from exact pair exposure. Count unique TRAIN
   neighbors by label. Evaluate partner-only TRAIN positive degree, TRAIN seen
   status, and smoothed positive degree fraction, without fitting to these
   panels. An unseen protein has degree zero and smoothed fraction 0.5. These
   controls ask whether the P/U design carries endpoint-level information. They
   do not show that TUnA internally uses those statistics. Public label 0 is the
   original dataset's sampled-negative label, not an experimentally verified
   noninteraction. Inspect score/degree association within U to avoid a trivial
   correlation induced by mixing P and U.
3. Replace each target by each of the other eleven panel targets, retain its
   original partner list, and score with frozen original and retrained TUnA.
   Keep the ORIGINAL target's P/U reference labels solely to measure persistence
   of its partner ranking. Replacement pairs have no assigned biological truth.
   Report all five candidate sets, the mean over eleven replacements, rank
   correlation, and a partner-only diagnostic formed by averaging within-panel
   rank percentiles over those replacements. No replacement query is selected
   by performance. This control detects ranking information that survives a
   query change, not the fraction of predictions attributable to a causal bias.
4. Reuse the parent run's freshly computed residue and endpoint arrays for this
   diagnostic, record their hashes, and verify actual-query predictions against
   every saved TUnA score. Directly load the authors' original checkpoint, allow
   its documented native eval-time covariance calculation in memory, and compare
   unaccelerated batch-one predictions for all 37 P, the highest-scoring U for
   every target, and the longest pair. Compare trained parameters and buffers
   with the frozen runtime checkpoint. Separate raw logits, GP variance,
   mean-field-adjusted logits, and sigmoid scores on all original pairs to test
   whether uncertainty adjustment or numerical saturation explains the ranking.
5. Compare only already published aggregate repository benchmark results. Do
   not open protected test pair identities, labels, or per-pair scores. Read
   original public TRAIN/validation lists only; do not read its Intra2 test list.

## Interpretation and preservation

The primary contrast is original versus retrained TUnA, which shares the pinned
architecture but differs in training data, loss, selection, covariance fitting,
and single-model versus three-seed aggregation. Those factors are confounded:
this investigation cannot causally assign their individual contributions.
All U remain unlabeled. PU concordance and known-positive AP are retrieval
statistics, not verified-negative specificity or calibrated interaction risk.

Use accepted Apptainer images; scientific computations run inside them. Bind the
repository read-only and only this new folder writable. Freeze diagnostic inputs
before computation, verify the 107 parent scientific artifacts before and after,
independently check ranking metrics with scikit-learn, and preserve the frozen
registry and checkpoints. Store compact CSV diagnostics, provenance, and figures;
large/local arrays and raw upstream files remain outside Git.
