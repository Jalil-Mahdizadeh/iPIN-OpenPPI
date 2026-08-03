# ISSUE-0004: Provider headline counts differ from downloadable gene-pair TSV rows

**Status:** Open for parser-level reconciliation; not a raw-integrity failure  
**Opened:** 2026-08-03  
**Severity:** Medium scientific-semantics risk  
**Owner:** Codex

## Observation

The immutable Interactome Atlas downloads match their audited URLs, byte lengths, ETags, timestamps, and locally frozen SHA-256 values. However, two portal headline counts do not equal the corresponding TSV row counts:

| Dataset | Portal-advertised interactions | Downloaded unique TSV rows | Difference |
|---|---:|---:|---:|
| HuRI | 52,569 | 52,548 | -21 |
| HI-II-14 | 13,993 | 13,633 | -360 |

Test-space screens-19 has 1,159 advertised interactions and 1,159 TSV rows. Lit-BM has 13,441 advertised interactions and 13,441 TSV rows.

The detailed PSI-MI exports are not one-row-per-TSV-pair files: HuRI contains 171,545 complete 42-field evidence rows, while HI-II-14 contains 49,389. A simple first-Ensembl-mapping comparison also shows that PSI-MI and TSV representations are not interchangeable. The discrepancy is therefore consistent with differing evidence, construct/isoform, mapping, orientation, homomer-filter, or deduplication layers, but the exact provider transformation has not yet been reconstructed.

## Binding interpretation

- Preserve provider-advertised counts and observed payload counts as separate fields.
- Never add, remove, duplicate, or collapse raw rows to force agreement with a headline count.
- Treat PSI-MI rows as evidence records and TSV rows as a provider-derived gene-pair view.
- Require the parser report to explain mapping, self-pair, orientation, and deduplication effects before a consensus pair table is approved.

## Impact

Raw acquisition remains valid: all transport, checksum, sidecar, format, and permission checks pass. This issue does not block source parsing. It blocks any claim that a portal headline, TSV row, PSI-MI row, ORF pair, and unique gene pair are automatically the same unit.

## Resolution criteria

Close this issue only after a deterministic reconciliation report traces:

1. portal dataset count;
2. detailed PSI-MI evidence records and stable identifiers;
3. construct/isoform-to-Ensembl mappings;
4. orientation and assay-stage multiplicity;
5. self-pair and heteromer filters; and
6. final unique gene-pair TSV membership.

If public records cannot reproduce the provider transformation exactly, retain the issue as a documented source limitation in every release.
