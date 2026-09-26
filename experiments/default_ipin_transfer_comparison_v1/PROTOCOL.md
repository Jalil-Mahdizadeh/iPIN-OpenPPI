# Default iPIN on the two frozen transfer studies

Apply the already selected, registered **iPIN-TUnA-31k** to every row of
`benchmark/nonhuman_transfer_v1` and
`benchmark/reference_organism_pu_transfer_v1`. The requested `va1` and
`transffer` spellings resolve to these existing directories. No resampling,
training, checkpoint selection, calibration, or change to original artifacts.
All new files stay in this experiment. The repository is mounted read-only
during numerical work. Existing dirty files are preserved.

Use the immutable v3 registry and bundle: three seeds 20260803, 20260817,
20260831; 31,188 training P; epoch 1. Verify the two existing full-length FP32
ESM2-150M residue caches against their archived checksums and sequence hashes.
Recompute the 64-dimensional features for every seed and endpoint. Set the
GP fitted flag before eval, preserve every saved buffer and weight, disable
AMP/TF32, and average FP32 mean-field-adjusted logits in FP64. Qualify cached
scoring against native pair inference on fixed species/length fixtures with
absolute tolerance 1e-5; check exact pair symmetry for all rows. Scores are
ranking values, not calibrated probabilities.

The six-species study retains 61,385 rows (1,385 P and 60,000 U), 50 targets per
species, and background, matched, and combined U candidate sets. Its primary
comparison is matched-U concordance, equal-target within species and then
equal-species overall. The human–laboratory-S288C study retains all 157,055 rows
(1,555 P and 155,500 globally distinct U), with 100 U per P. Its primary summary
weights P equally; the secondary summary weights yeast targets equally.

Read the three archived predictors' scores, verify pair and row identity, and
reproduce their historical metrics using the unchanged historical metric
implementation. Report concordance, AP/MAP, MRR, first-positive rank, recall,
known-positive precision, enrichment, NDCG and target success at 5/10/20 where
defined. Retain per-target/per-P tables. Use the original seeds and 10,000
paired target-bootstrap draws, preserving the historical sampling order and
target weighting. Include differences between the new default and each prior
model, plus paired target win/tie/loss counts. Intervals are exploratory,
pointwise, conditional on these panels; shared partners, homology and source
publications leave dependence. Do not infer a universal winner.

Preserve the original `all` and `no_exact_TRAIN_DEV_endpoint` cohorts exactly.
Audit exact endpoint and unordered sequence-pair matches to the expanded
31k training P, its U sampling pool, and all evaluated expanded development
partitions (C1/C2/C3, reconciled and added). Add one common sensitivity cohort
that removes the union of historical and newly audited exact TRAIN/development
endpoint exposures from **every** model. Disclose denominators and that U-pool
membership is potential training exposure. Historical homology strata, if
reported, refer only to the old training universe; no new homology search or
ESM pretraining exposure audit is claimed. The primary panels remain intact.

Validate all new concordances/AP values against independent rank/sklearn
implementations, the three-member mean, historical result reproduction, input
preservation, and finite complete predictions before publishing a comparison
report and standalone figures here. U is unreported in the archived evidence
universe, not experimentally confirmed noninteraction; PU performance is not
biological specificity or prospective assay precision. The human–yeast panel
is a laboratory reference-organism benchmark, with one source publication.

