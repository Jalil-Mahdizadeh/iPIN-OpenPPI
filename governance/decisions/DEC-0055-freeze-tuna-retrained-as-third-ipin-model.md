# DEC-0055: Freeze TUnA-retrained as the third iPIN model

Date: 2026-09-20. Status: user-authorized preservation and registration.

The user requested: "freeze tuna-retrained as the third ipin model."
Register the existing `tuna_retrained_ensemble` predictor as **iPIN model 3,
TUnA-retrained (PU-TUnA)**. Its architecture remains attributed to the published
Bernett TUnA implementation. This is the iPIN TRAIN-only PU adaptation already
evaluated in `benchmark/tuna/`, not the authors' original released checkpoint.

## Fixed model identity

Preserve the development-selected epoch-4 states for seeds 20260803, 20260817,
and 20260831, in that order. Preserve all learned parameters and buffers,
including the TRAIN-fitted GP precision and covariance. Each member produces
`logit / sqrt(1 + pi * variance / 8)` in FP32; the predictor is their equal
arithmetic mean in FP64, without sigmoid, calibration, seed selection, or
reweighting. Inference retains the full-context ESM-2 residue pipeline and
full-length native endpoint representations, without the pooled iPIN normalizer.

Create `frozen_pair_models_v2` as a three-model catalogue and a new read-only
preservation bundle for TUnA-retrained. The v1 registry, its two exact model
definitions, their private preservation bundle, and DEC-0054 remain unchanged.
The v2 registry references that existing bundle for models 1 and 2 and its
shared encoder. It records exact hashes for the third model's weights,
endpoint features, inference sources, upstream code, runtime, and evidence.

## Evidence and interpretation

This registration occurs after the completed benchmark and example results.
The earlier epoch choice was made using C3 development alone, between epochs
4 and 8 of the completed eight-epoch training schedule. Registration does not
represent a new prospective selection or independent confirmation.

The preserved C1/C2/C3 concordances are 0.948619 / 0.880401 / 0.815875.
The C3 contrast against optimized pooled iPIN is +0.007927 with paired 95%
interval [−0.028978, +0.038272]; primary superiority is not established.
Unlabeled pairs remain unlabeled, scores are not binding probabilities, and
genuine partner-specific/direct-binding generalization remains unresolved.

## Execution boundary

Authorize byte-identical preservation, checksum/state verification, synthetic
tests, and documentation/registry updates. No training, covariance refitting,
encoder inference, benchmark pair scoring, protected-truth access, metric
recomputation, or ledger reset is part of this action. Preserve the completed
TUnA selection, result, prediction freeze, and consumed evaluation reservation.
Weights and endpoint identities stay local and are not committed to Git.

See the [v2 model cards](../../docs/models/FROZEN_PAIR_MODELS_v2.md),
[status v55](../PROJECT_STATUS_v55.md), and [gate v55](../gates/gate_status_v55.yaml).
