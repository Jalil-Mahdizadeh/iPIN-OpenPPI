# Frozen PPI transfer to published human–yeast assay confirmation

The completed study applies the three unchanged registered iPIN ensembles to
1,555 published human–S288C reference-sequence pairs. Its primary comparison
uses 75 published orthogonal-assay outcomes: 36 confirmed and 39 unconfirmed.
An unconfirmed assay call is not a verified biological noninteraction.

**Read [REPORT.md](REPORT.md)** for results, uncertainty, exposure sensitivity
and the scientific limits. [FINAL_MANIFEST.json](FINAL_MANIFEST.json) binds the
completed artifacts, and [RESULT_VALIDATION.json](RESULT_VALIDATION.json)
records independent source, metric and bootstrap checks.

The user accepted a revised scope restricted to nonpathogenic laboratory
reference organisms and already published interactions. S288C is the primary
reference organism. K-12 was reviewed but has insufficient source coverage for
a primary comparison. The study does not establish human-pathogen performance.

## Files

| Files | Purpose |
|---|---|
| `PROTOCOL.md`, `config.json`, `SOURCE_PREPARATION.json`, `VALIDATION.json` | Historical source-preparation scope and checks |
| `EVALUATION_PROTOCOL.md`, `INPUT_FREEZE.json` | Prespecified assay endpoint, metrics and immutable inference inputs |
| `COMPARISON_SOURCES.json`, `comparison_mapping_audit.csv` | Published supplement identities and every mapping decision |
| `assay_comparison.csv`, `PANEL_SELECTION.json`, `COMPARISON_VALIDATION.json` | Fixed comparison subset and mapping checks |
| `published_pairs.csv`, `published_proteins.csv`, `published_evidence.json.gz`, `published_sequences.json.gz` | Verified published reference data |
| `panels.csv`, `selected_sequences.json.gz` | Exact inference pair order and sequence inputs |
| `ipin_scores.csv`, `tuna_scores.csv`, `all_model_scores.csv` | Complete frozen-model scores for published pairs |
| `assay_model_scores.csv`, `metrics.csv`, `paired_differences.csv` | Assay outcomes, model metrics and paired comparisons |
| `EXPOSURE_AUDIT.json`, `EXPOSURE_SUMMARY.json`, `exact_*_exposure.csv`, `training_sequence_similarity.csv` | Human TRAIN/development exposure and sequence similarity |
| `bootstrap_components.csv`, `ANALYSIS.json`, `RESULT_VALIDATION.json` | Shared-endpoint uncertainty and independent validation |
| `IPIN_RUN.json`, `TUNA_RUN.json`, `RUNTIMES.json` | Execution identities, symmetry and native-model checks |
| `assay_confirmation.png`, `.pdf`, `.svg` | Exportable scientific figure |
| `FINAL_MANIFEST.json` | Completed study checksums |

The preliminary `SOURCE_REVIEW.md` records the positive-only preparation phase.
The completed comparison adds the authors' published Table EV7 assay outcomes;
the later evaluation protocol and final report describe the resulting endpoint.

## Reproduction

See [REPRODUCE.md](REPRODUCE.md). Preparation, exposure and analysis run in the
accepted data image; inference uses the accepted iPIN and TUnA images and one
GPU. The repository is mounted read-only, with this study directory writable.
Fresh embeddings are generated, frozen model parameters and normalization are
preserved, and protected human test-pair identities/truth are not opened.

Large feature caches and downloaded source archives remain local and are
checksum-bound. Source data are attributed to EMBL-EBI IntAct / IMEx and the
[original publication](https://pubmed.ncbi.nlm.nih.gov/27107014/).
