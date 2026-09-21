# Human–S288C P-versus-unlabeled benchmark

User-directed correction: retain **all 1,555 published P pairs** and assign
**100 globally distinct U pairs to each P**. The complete panel has
**155,500 U and 157,055 total pairs**, with no U reused across panels.
All 39 published positives unconfirmed by a second assay remain P.

The candidate pool expands to eligible archived human sequences while keeping
the original 545 S288C reference sequences. The [protocol](PROTOCOL.md) defines
source exclusions, metadata matching, exact counts, frozen scoring and metrics.
U means unreported in the declared source snapshot, not verified negative.

## Status and outputs

- [Panel validation](PANEL_VALIDATION.json) records whether the requested P/U
  dataset passed identity, counts, uniqueness and source-exclusion checks.
- [Panels](panels.csv) contain one P and 100 U for each `panel_id`.
- [Positive assignments](positive_assignments.csv) give the exact per-P counts.
- [Selection and provenance](PANEL_SELECTION.json) record candidate coverage,
  matching fallbacks and all source/output checksums.
- [Input freeze](INPUT_FREEZE.json) binds the P/U design and implementations
  before inference on the new panel.
- [REPORT.md](REPORT.md) and [FINAL_MANIFEST.json](FINAL_MANIFEST.json) exist
  only after scoring, analysis and independent result validation finish.
- [Results notes](RESULTS_NOTES.md) explain concordance, the metadata control,
  training-exposure sensitivity and the limits of the model comparison.

The earlier [assay-confirmation study](../reference_organism_transfer_v1/REPORT.md)
has a different endpoint. Its 36-versus-39 comparison does not substitute for
this P/U benchmark. Its immutable artifacts are retained as history.

See [REPRODUCE.md](REPRODUCE.md) for commands. Source: IntAct/IMEx release 252
and the original published human–yeast study (PMID 27107014), CC BY 4.0.
