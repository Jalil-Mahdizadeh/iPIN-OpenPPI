# DEC-0012: Accept the negative-evidence discovery audit

**Date:** 2026-08-04

**Status:** Accepted and effective as a technical M0 subgate

**Decision owner:** Codex under delegated project-execution authority

**Controlling expert decision:** `DEC-0011`

**Expert-group comment represented by this record:** None beyond the explicit
authorization in `DEC-0011`

## Decision

The production `negative_evidence_discovery_audit_v1` work package is accepted
as complete because its independent production validator passed 43 checks with
zero failures and zero warnings.

This is a technical acceptance under the execution authority delegated to
Codex. It does not falsely attribute a new scientific comment or approval event
to the expert group. The controlling scientific scope remains the group's
explicit acceptance of Blueprint Amendment 001 and its negative-evidence work
package in `DEC-0011`.

## Accepted evidence

| Evidence | SHA-256 |
|---|---|
| `artifacts/validation/negative_evidence/negative_evidence_audit_v1/AUDIT_REPORT.json` | `ccefebc920ec5c3d1a04d271babbdee044608662ef88d87615a274d82f6e6315` |
| `artifacts/validation/negative_evidence/negative_evidence_audit_v1/VALIDATION_REPORT.json` | `e3b7b8da6fbb9d6361278e9d89ab1cdd070c087279a8a821dc852cfd5f4fc155` |
| `data/staging/negative_evidence_v1/STAGING_MANIFEST.json` | `4b4c4cd9679f8bd6e6f207bbe067df75da30b38d900bc0214dcc1303095f3ec9` |
| `data/canonical/negative_evidence_audit_v1/AUDIT_MANIFEST.json` | `593b1b45ef579f4f4f403f8567510c28b0ac84b8818ac82d3b27a6d2dce9be24` |
| Implementation commit | `30220bd5e0fec5f6c259ba369f14b62a71530f3f` |

The final expert-facing interpretation is
`docs/reports/m0/M0_Negative_Evidence_Discovery_Audit_Final_v1.md`.

## Accepted findings

- The four complete Negatome datasets contain 12,720 physical source rows and
  reduce to 6,568 parent observations when stringent membership is represented
  without double-counting.
- Exactly 1,630 parent observations map both participants uniquely to frozen
  human UniProt `2026_02`: 1,408 manual and 222 structural non-contact.
- Current permitted positive evidence conflicts with 237 mapped parent
  observations. Historical stringent status is not current conflict clearance.
- All 939 frozen IntAct negative records were audited; 453 map to usable frozen
  human sequence pairs.
- Exact Negatome–IntAct negative overlap is zero by ordered accession,
  unordered accession, and frozen sequence-pair routes under the specified
  matching rules.
- Reliability tiers are accepted as evidence strata: ME-1 1,216; ME-2 192;
  SN-1 154; SN-2 68; and MX 4,938.
- A conservative protected manual diagnostic candidate contains 1,188 records,
  1,163 unique sequence pairs, and 315 publications.
- No audited source supports a universal nonbinding interpretation.

## Statistical disposition

The negative evidence is numerically adequate for a future protected,
source-/assay-stratified conditional diagnostic. It is not sufficient to
identify a population-calibrated P+N+U design because the selected, attempted,
and evaluable population, source-selection process, assay sensitivity, and
biological class prior remain unidentified.

Accordingly:

- PU-R remains the binding primary design;
- the manual conditional-negative stratum has no authorized training role;
- structure-derived non-contact remains a separate evidence family;
- positive conflicts remain overlays, not deletion rules; and
- zero source overlap is not interpreted as biological independence or
  universality.

## License disposition

Negatome internal audit and non-extractive aggregate reporting are accepted.
Raw and record-level redistribution remain prohibited pending explicit provider
permission. IntAct data retain their CC BY 4.0 attribution requirement. The
additional 2026 human Y2H panel is a follow-up candidate only; its acquisition
is not authorized by this decision.

## Next authorization

The previously queued
`benchmark_eligibility_and_sequence_component_audit_v1` is now authorized but
not started. Its scope is limited to reference-sequence eligibility and
exclusion accounting, aggregate candidate counting without pair
materialization, and 40%/30%/20% sequence-component feasibility. It must return
to governance before any construction gate advances.

## Continuing prohibitions

This decision does not authorize candidate-pair materialization, positive or
unlabeled evidence indicators, negative labels, pseudo-negative samples,
C1/C2/C3 assignments, split construction, structural training labels, model
implementation, training, selection, release, or experimental-validation
claims.
