# DEC-0015: Authorize the bounded 2025 TF-isoform Y2H audit

**Date:** 2026-08-04

**Status:** Effective for acquisition and audit only

**Decision basis:** Explicit project-owner instruction in the active session

## Decision

Keep `benchmark_eligibility_and_sequence_component_audit_v1` paused while a
second, separate external-panel audit is performed. Authorize acquisition of
only the five assets in preacquisition index v6 and a source-faithful audit of
the Lambourne et al. 2025 TFIso1.0 pairwise Y2H dataset and its available N2H
validation observations.

The work must preserve clone sequences, construct identifiers, AD→DB
orientation, source outcomes, and technical states; independently account for
all public rows including 1,260 blanks; reconstruct selection/filtering;
retain Y2H and N2H as separate assays; map exact constructs and canonical
proteins to human UniProt 2026_02; measure exact-pair, endpoint, UniRef90,
HuRI, permitted-evidence, and future-training-exposure overlap; quantify
protected fixed-partner isoform-contrast groups; and assess licensing and a
three-way disposition.

## Fail-closed rule

No blank, unknown, autoactivation, mating/expression failure, or other
technical state may be inferred to be an assay negative. If required raw
state is absent or ambiguous, preserve `unknown` and make the disposition
conservative. The article PDF is internal-audit-only; Zenodo data are CC BY
4.0 with attribution.

## Explicit prohibitions

- Do not use study outcomes as training labels or merge them with Negatome.
- Do not construct benchmark rows or splits.
- Do not train, tune, calibrate, threshold, or select models.
- Do not change the primary PU-R design.
- Do not relabel between Y2H and N2H.
- Do not infer universal nonbinding.

## Required return and continuation

Produce immutable source, staging, canonical, validation, report, and
governance artifacts; run targeted tests; commit and push. Then resume the
previously authorized sequence-component audit under its unchanged scope.
This decision does not authorize external-panel benchmark integration.
