# DEC-0013: Authorize the bounded Lambourne human Y2H semantics audit

**Date:** 2026-08-04

**Status:** Effective for acquisition and audit only

**Decision basis:** Explicit project-owner instruction in the active session

## Decision

Pause the authorized but unstarted
`benchmark_eligibility_and_sequence_component_audit_v1`. Authorize acquisition
and a governance-bounded, source-faithful audit of the Lambourne et al. 2026
human Y2H-v1 panel under `SOURCE-POLICY-003` and preacquisition index v5.

The authorized work must reconstruct the exact 4,100 selected-pair universe
and exact 3,222 final-analysis subset; account for positive, negative, `NA`,
and technical states; preserve construct, orientation, sequence-confirmation,
assay, species, publication, and condition provenance; map deterministically
to human UniProt 2026_02; reconcile current permitted evidence; and assess
pair/sequence-family contamination, protected external-benchmark feasibility,
and claim identifiability.

## Source-state decision

IM-30553 is not integrated into current IntAct services at this date. Its
official preview representations may be acquired as a dated provider snapshot
but must not be conflated with frozen IntAct Release 252.

## Explicit prohibitions

- Do not use Lambourne outcomes as training labels.
- Do not merge them with Negatome.
- Do not construct benchmark splits.
- Do not train, tune, or select models.
- Do not classify `NA` or technical failure as negative.
- Do not claim that a negative outcome means universal nonbinding.
- Do not integrate the panel into a benchmark before a new governance decision.

## Required return

Produce immutable source, staging, and canonical audit manifests; an
independent validator and tests; a scientific report; and a governance decision
proposal. Return to governance with the audit results. This authorization is
not advance approval of benchmark use.
