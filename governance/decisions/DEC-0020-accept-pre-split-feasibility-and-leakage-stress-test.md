# DEC-0020: Accept the pre-split feasibility and leakage stress-test

**Date:** 2026-08-08

**Status:** Accepted and effective as a technical M0 subgate; split
construction remains on governance hold

**Decision owner:** Codex under delegated project-execution authority

**Controlling records:** `DEC-0018` and `DEC-0019`

## Decision

Accept `pre_split_feasibility_and_leakage_stress_test_v1` as technically
complete. Its clean-tree independent validator passed 13 checks with zero
warnings and zero failures. Production ran from clean commit
`2dcd8b3585159a5d747176d36e08a57a11cb0950`; accepted validation ran from
clean commit `f1001cc8c9bc9c16a596139f1231bfae24f74c74`.

The expert-group comment supplied in the active session was scientifically
valid as a bounded diagnostic authorization. The audit stayed within that
scope. It emitted no candidate-pair universe, positive pair rows, evidence
indicators, negative or pseudo-negative labels, endpoint/component
assignments, C1/C2/C3 labels, split, external-panel integration, structural
mapping, or model result.

The primary design remains reference-sequence positive-unlabeled ranking
(PU-R). Unreported eligible pairs remain unlabeled.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Production audit report | `5f4e655a81b70a4dd2143a81027188b692ca120b0fab7f919d18b53fd4eabb6f` |
| Independent validation report | 13 pass, 0 warning, 0 fail; `1f0f862796f1ab581ca4c3c528987cd1fdf484269d5ca932f99eb9d946e1e809` |
| Production run manifest | `a76731632f5d137d0fa2b2eab244c2e86a7a10cd4b67013d8164bb684b902755` |
| Canonical audit manifest | `8b2200b34149c1a4ecf92274cac886acbafc2d53b2cac3e8167c91610ec860f2` |
| Frozen audit configuration | `0648107f96f079b502dfce4c0c470c1199514463615c107f152a06603f75281f` |
| Canonical schema | `04fbde9975a45d8d567ea98facc470b385275db61b9e1428d1699d05b358fae5` |

The expert-facing interpretation is
`docs/reports/m0/M0_Pre_Split_Feasibility_and_Leakage_Stress_Test_Final_v1.md`.

## Accepted findings

- The immutable parent universe remains exactly 17,000 sequence endpoints,
  58,049 released-positive pairs, and 12,467/11,311/10,497 accepted components
  at 40%/30%/20% identity.
- The positive network is hub-concentrated. For the ALL union, 8,596 endpoints
  are positive-exposed, maximum endpoint degree is 603, the top 1% of
  endpoints carry 23.6% of degree, and the Gini coefficient is 0.849.
- Source membership is 7,504 HI-II-14-only pairs, 45,696 HuRI-only pairs, and
  4,849 pairs present in both sources. These are released-positive composition
  counts, not prevalence.
- The separate full-length sensitivity challenge rediscovered every accepted
  edge. It also recovered 35, 106, and 1,189 new qualifying edges at 40%, 30%,
  and 20%, respectively. At primary 30%, 42 new edges crossed accepted
  components.
- Residual local/domain similarity is substantial. At primary 30%, the
  local/domain union adds 113,190 edges relative to the accepted graph,
  including 69,112 crossing accepted components; component count falls from
  11,311 to 7,782 and largest component size rises from 362 to 1,624.
- Component-disjoint opportunity evidence is robust under frozen and
  sensitivity-union full-length graphs at all three identities. It is robust
  under the local/domain union at 40%, conditional at 30% with joint pass
  fraction 0.893, and conditional at 20% with joint pass fraction 0.614.
- Every target-valid primary-30 local/domain trial also passed the prespecified
  C1, C2, C3, component, and C3 source-diversity floors. The conditional result
  is caused by component-level sequence-balance difficulty, not loss of
  positive evidence.

## Final-split feasibility disposition

Final split construction is scientifically feasible in principle, but this
decision does not authorize it.

The accepted 30% full-length graph remains immutable parent evidence, but it
must not be used alone as the final leakage guard. A future split package must
use at least the 30% `sensitive_fl80_union` as a hard full-length component
constraint.

The 30% `local_domain_union` is the preferred stricter operational leakage
stress definition. Its conditional result requires a later constrained
allocation procedure and exact verification that any selected split meets
sequence balance, positive-evidence floors, source diversity, and zero
cross-partition leakage under the chosen hard rule. If local/domain union is
not made a hard assignment rule, residual local/domain cross-partition leakage
must be quantified and claims further limited.

The 40% local/domain graph is robust but is a less stringent identity regime.
The 20% local/domain graph is not approved as a default because its 4,932-member
component makes target balance unstable under the audited allocator.

## C3 and claim disposition

No audited regime supports an unqualified unseen-family claim. “Unseen
protein” is supportable only under the exact-endpoint definition below.

A later verified C3 split may state only that both exact frozen
reference-sequence endpoints were absent from training and component-disjoint
under an explicitly named, versioned sequence rule. “Unseen protein” is
permitted only when defined exactly this way. It may not imply unseen gene,
isoform, homolog, domain architecture, or biological family.

The following wording is prohibited:

- unseen family, novel family, or family-generalizing performance;
- proven nonhomology or exhaustively homology-free;
- universal-nonbinding, prevalence, or calibrated probability; and
- experimental validation or model performance derived from this audit.

## External-panel disposition remains binding

`DEC-0017` remains unchanged. The TF-isoform panel is external-only and
unsuitable for training negatives or any training role, universal-nonbinding
claims, prevalence, calibration, and unseen-endpoint or family benchmarking.
Neither external audit was reopened, recomputed, or extended, and neither
panel was used in this audit.

## Continuing prohibitions and next authority

This decision authorizes no next work package. In particular, it does not
authorize:

- candidate-pair materialization or sampling;
- positive/unlabeled evidence indicators, negative labels, or
  pseudo-negatives;
- selected component allocations, C1/C2/C3 assignments, or
  train/development/test split construction;
- external-panel integration or structural-label work;
- prevalence estimation, calibration, or probability interpretation; or
- model implementation, training, tuning, selection, evaluation, routing, or
  release.

Any final split-construction package requires a new explicit numbered
authorization that incorporates the leakage and claim boundaries above.
