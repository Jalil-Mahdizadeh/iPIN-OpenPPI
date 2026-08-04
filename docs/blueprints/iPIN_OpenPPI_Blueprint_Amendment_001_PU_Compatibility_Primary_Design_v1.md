# Blueprint Amendment 001: PU compatibility as the primary design

**Version:** 1.0 accepted
**Effective date:** 2026-08-04
**Status:** Accepted by the iPIN-OpenPPI expert group and effective
**Parent:** `docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md`
**Accepted decision:** `governance/decisions/DEC-0011-accept-blueprint-amendment-001-and-authorize-negative-evidence-audit.md`

## 1. Instrument incorporated

The expert group accepts and incorporates the complete reviewed proposal at:

`docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_PROPOSAL_v1.md`

The incorporated proposal SHA-256 is
`0979e4ed953f1d85e6d11f4fd1469238c9eaee082e1a5d060717647d2bff7c13`.
Its scientific target, estimands, claim ceiling, candidate semantics, benchmark
ladder, minimum sizes, uncertainty plan, activation gates, and prohibitions are
now binding. Proposal-only approval language is superseded by this acceptance
instrument.

The reviewed machine-readable proposal at
`configs/benchmark_estimand_policy_proposal_v1.yaml`, SHA-256
`b5a7aff3615fa15a612d916e6ea9c46eba65756dfd239c8236a94c450d948a78`,
is activated through `configs/benchmark_estimand_policy_v1.yaml`.

## 2. Accepted primary target

The active primary design is reference-sequence positive–unlabeled ranking.
Released qualifying direct-positive evidence is observed positive evidence;
every other eligible pair is unlabeled unless a source-specific experimental
record says otherwise. The model output, when later authorized, is a symmetric
compatibility/prioritization score and is not a binding probability.

The accepted design does not recover the missing HuRI attempted/evaluable
universe and does not authorize a biological negative class, natural-prevalence
calibration, or universal binding/nonbinding claims.

## 3. Additional work package: negative-evidence discovery audit

The expert group adds and authorizes
`negative_evidence_discovery_audit_v1` before the previously authorized
eligibility/sequence-component audit.

The work package shall:

1. acquire and version the complete Negatome 2.0 Manual,
   Manual-stringent, PDB, and PDB-stringent protein-pair datasets;
2. determine source licensing and redistribution conditions, retaining a
   conservative no-redistribution boundary wherever terms are not explicit;
3. parse every record without pair-level consensus collapse;
4. map both record participants against frozen human UniProt release `2026_02`,
   retaining the source accession, explicit isoform suffix, exact mapping path,
   frozen sequence hash, organism state, and mapping confidence;
5. calculate exact source-record and frozen-reference-pair overlap with all 939
   current frozen IntAct negative evidence records;
6. check every mapped pair against current qualifying positive evidence from
   HuRI, IntAct, and any other already permitted direct-PPI source/view whose
   pair semantics can be reproduced;
7. preserve all available assay, construct, orientation, species, publication,
   PDB, and experimental-condition provenance, with unavailable values encoded
   as missing rather than inferred;
8. keep manually observed experimental non-detections separate from
   structure-derived non-contact pairs at every data layer;
9. assign auditable reliability tiers and conflict flags rather than a single
   negative label;
10. survey further public systematic experimental screens for attempted and
    technically evaluable non-detections; and
11. report whether a positive–negative–unlabeled design is statistically and
    scientifically feasible, for what bounded estimand, and under which source
    and assay restrictions.

## 4. Binding negative-evidence semantics

No negative record may be interpreted as a universal nonbinding pair without
explicit evidence supporting that exact claim. No currently identified source
provides such universal evidence.

The minimum tier framework is:

| Tier | Evidence meaning | Permitted role |
|---|---|---|
| `ME-1` | Manual experimental record in the historical stringent subset, with both participants exactly mapped and no current direct-positive conflict | Conditional source-scoped diagnostic candidate only |
| `ME-2` | Other manual experimental record with usable mapping | Conditional evidence; descriptive or sensitivity analysis |
| `SN-1` | PDB-derived non-contact in the historical stringent subset with usable mapping | Structure-context non-contact diagnostic only |
| `SN-2` | Other PDB-derived non-contact with usable mapping | Descriptive structure-context evidence only |
| `MX` | Missing/ambiguous/nonhuman mapping, insufficient provenance, or incompatible cardinality | Out of primary human sequence scope; retain for audit |
| `CF` | Any tier with current positive evidence for the mapped pair | Explicit conflict stratum; never silently removed or treated as negative |

Historical “stringent” membership is a provider-era IntAct filter, not proof of
current absence of positive evidence. Reliability tiers can be downgraded after
audit but cannot be upgraded by assuming missing provenance.

## 5. Execution and release boundary

All scientific acquisition, parsing, mapping, reconciliation, and statistical
work must run on Arrhenius through the pinned ARM64 Apptainer image. Raw,
staged, canonical, report, validation, and governance layers remain separate
and versioned.

If Negatome redistribution terms remain unspecified, raw and record-level
derived Negatome data stay outside Git and release packages. Reproducible code,
source URLs, hashes, schemas, counts, validation summaries, and non-extractive
aggregate findings may be committed and shared.

## 6. Authorization boundary

This acceptance authorizes only:

- `negative_evidence_discovery_audit_v1`; and
- after it returns to governance, the previously specified
  `benchmark_eligibility_and_sequence_component_audit_v1` unless a later gate
  changes the order.

It does not authorize candidate-pair materialization, positive/unlabeled or
negative label construction, pseudo-negative sampling, split construction,
structure-derived training labels, model implementation, training, selection,
or public probability/experimental-validation claims.
