# ISSUE-0007: The claimed original 4,100-pair universe is not publicly reconstructable

**Opened:** 2026-08-04

**State:** Open; blocks any claim of exact 4,100-pair reconstruction

The Lambourne paper reports 4,100 originally selected human prediction pairs.
The versioned archived selection table instead contains 4,133 physical
`Zhang_et_al` rows and 4,130 unique unordered ORF pairs. Three physical rows are
duplicates, leaving a discrepancy of 30 unique pairs after deduplication.

The complete 29.98 GB input archive was inventoried without extraction. No
alternate exact 4,100-pair source file or deterministic exclusion field was
found. The 4,130 public pairs reconcile as 3,222 final-analysis pairs, 824
tested pairs excluded by the later Science Data S3 intersection, and 84 pairs
without a reported assay row.

Controls:

- retain the paper claim and public reconstructed count as separate fields;
- never silently drop 30 pairs or describe the 4,130 set as the exact 4,100;
- use the exactly reconstructable 3,222 subset only under an explicitly stated
  later-filtered-subset estimand; and
- seek author/source clarification or an expert-group waiver before any
  benchmark integration.

This issue does not invalidate the exact 3,222 outcome audit. It prevents claims
about the exact original selection denominator and blocks unqualified benchmark
integration.
