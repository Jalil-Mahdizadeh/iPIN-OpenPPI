# DEC-0041: Clarify local cosine reductions before execution

**Date:** 2026-08-19

**Status:** Accepted and effective; supersedes only the executable scorer list
and cosine interpretation of `DEC-0040`

## Decision

Accept revision 2 of the public-training local-representation diagnostic before
any local embedding, pair score, metric, or model fit exists. Remove the
optional `local_bidirectional_best_match_cosine` scorer because its reduction
was not specified exactly enough in revision 1. It has no replacement.

Freeze the ordinary-cosine, matched-global, maximum-segment, and top-four-
segment formulas in the revision-2 config and protocol. Retain unchanged the
primary local score, matched global comparator, nested component split, point
trigger, metric, bootstrap, conditional training recipe, public-only boundary,
and every prohibition accepted by `DEC-0040`.

This is a fail-before-observation specification correction. It consumes no
adaptive comparison, does not respond to a result, and does not reopen the
parent benchmark or stopped development claim.

## Binding records

- `configs/public_training_local_representation_diagnostic_v1.yaml` remains the
  inherited base at SHA-256
  `63e0d4e194b5db88a51e245b2ddf767e4ce11142659ac8c24deb3afbb6be749d`.
- `configs/public_training_local_representation_diagnostic_v1_revision_2.yaml`
  is the sole executable delta.
- `docs/protocols/PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1_revision_2.md`
  is the human-readable clarification.

All continuing prohibitions in `DEC-0040` remain effective.

