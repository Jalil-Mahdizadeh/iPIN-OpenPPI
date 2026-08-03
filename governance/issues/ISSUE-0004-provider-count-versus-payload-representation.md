# ISSUE-0004: Provider headline counts differ from downloadable gene-pair TSV rows

**Status:** Reconciled; retained as a documented public-source limitation
**Opened:** 2026-08-03
**Reconciled:** 2026-08-03
**Severity:** Medium scientific-semantics risk
**Owner:** Codex

## Observation

The immutable Interactome Atlas downloads match their audited URLs, byte
lengths, ETags, timestamps, and locally frozen SHA-256 values. However, two
portal headline counts do not equal the corresponding TSV row counts:

| Dataset | Portal-advertised interactions | Downloaded unique TSV rows | Difference |
|---|---:|---:|---:|
| HuRI | 52,569 | 52,548 | -21 |
| HI-II-14 | 13,993 | 13,633 | -360 |

Test-space screens-19 has 1,159 advertised interactions and 1,159 TSV rows.
Lit-BM has 13,441 advertised interactions and 13,441 TSV rows.

The detailed PSI-MI exports are not one-row-per-TSV-pair files: HuRI contains
171,545 complete 42-field evidence rows, while HI-II-14 contains 49,389. The
reconciliation confirms that PSI-MI evidence rows, ORF pairs, projected gene
pairs, and TSV rows are not interchangeable units.

## Binding interpretation

- Preserve provider-advertised counts and observed payload counts as separate
  fields.
- Never add, remove, duplicate, or collapse raw rows to force agreement with a
  headline count.
- Treat PSI-MI rows as evidence records and TSV rows as a provider-derived
  gene-pair view.
- Preserve mappings, orientation, self-pairs, multiplicity, and representation
  membership before any consensus-pair proposal is reviewed.
- Retain this issue as a documented limitation in every downstream artifact and
  release unless new authoritative provider records reproduce the transformation.

## Reconciliation outcome

Production run family `primary_reconciliation_v1` completed the deterministic
transition audit required by this issue.

| Metric | HuRI | HI-II-14 |
|---|---:|---:|
| Detailed evidence rows | 171,545 | 49,389 |
| Rows with a unique two-gene projection | 170,621 | 49,107 |
| Unresolved gene-projection rows | 924 | 282 |
| Unique detailed gene pairs | 52,649 | 13,432 |
| Unique unordered ORF pairs | 51,842 | 15,654 |
| Unique ordered ORF pairs | 78,886 | 23,757 |
| Pair-view rows | 52,548 | 13,633 |
| Matched detailed/pair-view gene pairs | 51,961 | 13,432 |
| Detailed-only gene pairs | 688 | 0 |
| Pair-view-only gene pairs | 587 | 201 |
| Union gene pairs | 53,236 | 13,633 |
| Pair-view self-pairs | 480 | 518 |
| Advertised minus pair-view rows | 21 | 360 |

The public transformation layers explain substantial differences caused by
evidence multiplicity, orientation, ORF/gene representation, self-pairs, and
representation membership. They still do not reproduce the portal headline
counts exactly. The public records therefore cannot establish one hidden
provider transformation as ground truth.

No source row was changed to make the representations agree. Detailed evidence,
projected pairs, pair-view membership, and provider-advertised counts remain
separate auditable objects with `label_authorized=false`.

## Impact

Raw acquisition, parsing, and canonical reconciliation remain valid. This issue
does not block benchmark/estimand design. It does block any claim that a portal
headline, TSV row, PSI-MI row, ORF pair, and unique gene pair are automatically
the same unit, and it prevents silent selection of one representation as a
consensus label.

## Resolution criteria and disposition

The required audit now traces:

1. portal dataset counts;
2. detailed PSI-MI evidence records and stable identifiers;
3. construct/isoform identifier-to-Ensembl projections;
4. orientation and assay-stage multiplicity;
5. self-pair state; and
6. final unique gene-pair TSV membership.

Because public records cannot reproduce the provider transformation exactly,
the issue is not closed as a resolved equivalence. It is **reconciled and
retained as a documented source limitation**, which is the prescribed outcome
under the original resolution criteria.

## Evidence

- `data/canonical/primary_reconciliation_v1/RECONCILIATION_MANIFEST.json`
- `artifacts/validation/reconciliation/primary_reconciliation_v1/VALIDATION_REPORT.json`
- `docs/reports/m0/M0_Primary_Source_Reconciliation_and_Construct_Mapping_Final_v1.md`
- `governance/decisions/DEC-0009-accept-primary-source-reconciliation.md`
