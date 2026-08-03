# DEC-0009: Accept primary source reconciliation with explicit scope limits

**Date:** 2026-08-03
**Status:** Accepted with downstream scientific blockers
**Decision owner:** Codex under project execution authority
**Gate effect:** Source-reconciliation subgate passes; overall evidence gate remains in progress

## Decision

Accept production run family `primary_reconciliation_v1` as the immutable,
provenance-preserving canonical reconciliation layer derived from the accepted
primary staging snapshot.

The run produced five canonical tables in 46 Parquet files, containing
4,297,000 rows across tables and 366,537,644 Parquet bytes. The independent
production validator returned 152 passes, zero failures, and four warnings.

The canonical reconciliation artifact and benchmark/estimand design are
authorized. Strict construct benchmarking, label construction, structural
mapping, and model training are not authorized.

## Scientific basis

- Every one of 2,213,524 staged participants has exactly one mapping audit row.
- Frozen reference sequences are usable for 2,054,023 participants (92.79%);
  canonical projections are usable for 2,063,972 (93.24%).
- Among 663,388 binary two-human-protein evidence records, 620,290 (93.50%)
  have usable reference-sequence pairs and 629,959 (94.96%) have usable
  canonical-sequence pairs.
- All mapping conflicts, unmapped states, nonhuman/nonprotein scope decisions,
  selected candidate routes, source identifiers, raw locators, and construct
  missingness are retained.
- Zero participants have construct confidence A or B, zero are strict-construct
  eligible, and zero rows authorize labels. This correctly reflects the absence
  of exact experimental construct sequences and boundaries.
- The HuRI audit deterministically traces detailed evidence, ordered and
  unordered ORF representations, Ensembl-gene projections, orientations,
  self-pairs, pair-view membership, and multiplicity without altering raw rows.
- SIFTS taxonomy, accession match, interval direction, bounds, and release state
  are explicit for all 1,007,697 chain mappings; zero structural mappings or
  labels are authorized.
- The production manifest records a clean Git commit and complete SHA-256
  verification of all immutable staging inputs.

## ISSUE-0004 disposition

ISSUE-0004's deterministic reconciliation requirement has been completed.
HuRI's detailed representation yields 52,649 unique gene pairs, the provider
pair view contains 52,548 rows, and their union contains 53,236 pairs: 51,961
match, 688 occur only in the detailed projection, and 587 occur only in the
pair view. HI-II-14 yields 13,432 detailed unique gene pairs, all matching its
13,633-row pair view, with 201 pair-view-only pairs.

The provider headline differences remain 21 for HuRI and 360 for HI-II-14.
Because the public records do not expose a transformation that reproduces those
headlines exactly, ISSUE-0004 is retained as a documented source limitation in
accordance with its resolution criteria. No source representation is promoted
to ground truth over another.

## Conditions

1. `data/canonical/primary_reconciliation_v1` remains immutable and outside
   Git. Any change requires a new run family, manifest, checksum, validator run,
   and decision.
2. Reference-sequence and canonical-projection identifiers must never be
   described as exact experimental constructs.
3. The blueprint's 80% A/B strict-construct threshold is unmet (observed 0%);
   the strict construct benchmark remains blocked.
4. ISSUE-0003 continues to prohibit conversion of unreported HuRI pairs into
   negatives. A positive-unlabeled or latent-observation design is required
   unless its exit criteria are satisfied.
5. ISSUE-0004 remains visible as a reconciled public-source limitation in every
   downstream artifact and release.
6. ISSUE-0005 continues to prohibit exact structure-to-sequence claims and
   structure-derived labels until release alignment or an approved exact-
   identity subset is established.
7. Source-native label-like records remain annotations; `label_authorized=false`
   is binding.
8. No label construction, split construction, or model training may occur until
   a later explicit gate decision.

## Next authorized unit

Perform benchmark and estimand design only. Freeze a scientifically supportable
reference/canonical-sequence target, positive-unlabeled or latent-observation
assumptions, admissible conditional-control policy, and leakage-control design.
Submit the benchmark-construction proposal for a new decision before creating
labels, immutable splits, or model inputs.

## Evidence

- `docs/reports/m0/M0_Primary_Source_Reconciliation_and_Construct_Mapping_Final_v1.md`
- `data/canonical/primary_reconciliation_v1/RECONCILIATION_MANIFEST.json`
- Reconciliation-manifest SHA-256: `6408c6be771ac6a957e443d8c848b66789ca47230ae372b7ec3f3390ab7a6932`
- `artifacts/validation/reconciliation/primary_reconciliation_v1/VALIDATION_REPORT.json`
- Validation-report SHA-256: `9d00b08bccb3620672ea6621cf3cb90c67de6bb1328d62b560712d65e4fa14d2`
- Reconciliation Git commit: `d66d990a16592eb469f1b58643d982cb936c9083`
- Reconciliation version: `0.1.0`
- Canonical schema SHA-256: `ae381c4e9dc94ebeb64f1ccb19f9ba2f3d86dfed5bff4fe8024625e38850fcf2`
- Accepted data-SIF SHA-256: `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`
