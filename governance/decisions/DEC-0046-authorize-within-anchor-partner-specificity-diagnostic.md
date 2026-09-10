# DEC-0046: Authorize a within-anchor partner-specificity diagnostic

Date: 2026-09-11

Status: effective, bounded user authorization.

## Authority and scope

The user instructed, "act according to your recommendations", following the
proposal for a prospectively specified within-anchor comparison against
endpoint-only models, an endpoint-balanced partner-swap check, and a feasibility
census before fitting. This records that instruction, not external expert
review, a public preregistration, or approval of a scientific conclusion.

Authorize a new public-training-only internal diagnostic: freeze the protocol
and inputs, run a label/design-only census, implement and test the estimands,
then conditionally refit the specified small heads and evaluate them once.
Record reproducible artifacts, validation, limitations, and the resulting
disposition. Infrastructure corrections must be logged; no outcome-driven
changes to splits, models, candidate panels, or success criteria are allowed.

## Boundaries

- Use only the four frozen public sequence/partition/training tables and the
  already frozen raw 150M embeddings and their identity manifest.
- Development results motivated the question and choice of pair head. They
  are not fresh evidence; no development fitting, rescoring, or selection.
- No protected candidate/truth/key access, decryption, external data acquisition,
  encoder extraction/fine-tuning, gated architecture search, or biological
  negative, probability, calibration, or interface claim.
- Retain all parent inputs, checkpoints, outcomes, and original scientific
  gates unchanged. New outputs use a distinct namespace.
- Existing public training tables omit source memberships. Do not recover
  them from evaluator-only artifacts. Source robustness remains untested.
- A useful internal result authorizes no protected evaluation automatically.
- This instruction does not request a new remote push or publication.

Executable specification:
`configs/within_anchor_partner_specificity_v1.yaml`.
Protocol:
`docs/protocols/WITHIN_ANCHOR_PARTNER_SPECIFICITY_v1.md`.
