# DEC-0047: Authorize the homology/interolog and source challenge

Date: 2026-09-11. Status: bounded user authorization.

The user requested: "ok! now challenge the signal with stronger homology/interolog
controls and source-aware validation, as you suggested."

Authorize the separately frozen `homology_source_challenge_v1` internal study:
public-training-only sequence searches, stronger interaction-transfer controls,
homology-purged small-head refits, and bidirectional source-exclusive recovery.
The previous study and all its artifacts remain unchanged.

For source annotation only, permit a constrained join against the three original
pre-benchmark `primary_reconciliation_v1/huri_evidence_gene_pair_projections`
files. The query must return source memberships **only for the exact 16,799
already released training-positive pairs**, using the frozen public endpoint
gene mapping. No additional positive pair or outcome may leave this projection;
no evaluator role ledger, development/source package, protected candidate,
protected truth or key may be read. This is a narrow new source-metadata
permission, not permission to reconstruct the hidden benchmark.

Freeze protocol/config before source counts, alignment results or new scores;
freeze implementation and passing tests before fitting/scoring. Feasibility
failures are reported, never repaired by outcome-driven split or threshold
search. Corrections to infrastructure must be recorded without overwriting
completed phases. Original whole-component folds and public P/U identities stay
fixed. Target-only public positives become unit-weight U during source-limited
fitting rather than being silently excluded using their hidden source label.

No new external data acquisition, encoder training/extraction, architecture
search, biological-negative construction, probability/calibration claim,
unseen-family claim, complete-assay validation, or protected evaluation is
authorized. Original model/gating stop remains. This request does not authorize
commit/push or imply external scientific review.

Protocol: `docs/protocols/HOMOLOGY_SOURCE_CHALLENGE_v1.md`.
Config: `configs/homology_source_challenge_v1.yaml`.
