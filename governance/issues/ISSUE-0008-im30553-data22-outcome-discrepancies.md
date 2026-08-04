# ISSUE-0008: Two IM-30553 preview pairs disagree with Data 22 outcome states

**Opened:** 2026-08-04

**State:** Open; controlled in audit; requires disposition before integration

Exact accession-pair reconciliation between Supplementary Data 22 and the dated
IMEx `IM-30553` preview finds interaction records for all 402 positive Zhang
assay pairs and for two additional final-analysis pairs:

- `P24941`–`P61024`: Data 22 reports failed sequence confirmation; IMEx contains
  two MI:0397 human/human, yeast-host interaction records.
- `Q99471`–`Q9UHV9`: Data 22 reports negative; IMEx contains one MI:0397
  human/human, yeast-host interaction record.

All 9,595 MITAB negative flags are missing, and the preview is a whole-paper,
mixed-assay/mixed-species curation rather than an attempted-opportunity table.
The audit therefore cannot determine whether the discrepancy represents an
alternate replicate, orientation, source-table version, curator interpretation,
or curation error.

Controls:

- preserve both source representations without relabeling;
- do not infer that a missing IMEx negative flag is positive or negative for an
  attempted panel record;
- do not merge the preview into frozen IntAct Release 252;
- seek author/curator clarification if feasible; and
- require an explicit benchmark-protocol rule or expert waiver before either
  pair can enter any future evaluation set.

This issue does not change the Data 22 source counts. It blocks silent source
selection for the two discrepant pairs.
