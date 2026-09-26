# Repository deposit, 26 September 2026

The Git repository now includes the previously local completed experiments,
the human residue-model study, and the historical manuscript package. This is
a publication of existing work. It does not change the default model, fit new
models, rerun protected evaluations, or revise frozen scientific results.

## Published material

| Directory | Published content | Starting point |
|---|---|---|
| `experiments/human_ppi_data_scaling_v1/` | Corpus/training/evaluation code, audits and freezes, 12 fit histories and epoch summaries, selection, learning curves and test1/test2 results | [Final review](experiments/human_ppi_data_scaling_v1/FINAL_REVIEW.md), [scope](experiments/human_ppi_data_scaling_v1/PUBLICATION.md) |
| `experiments/test2_frozen_competitors_v1/` | All 13 predictor wrappers and evaluation code, execution amendments, completion metadata, aggregate bootstrap draws, metrics and figures | [Results](experiments/test2_frozen_competitors_v1/results/RESULTS.md), [scope](experiments/test2_frozen_competitors_v1/PUBLICATION.md) |
| `experiments/twelve_target_selected_31k_v1/` | Scoring/comparison code, public pair scores, exposure/rank/retrieval tables, plots and validation | [Report](experiments/twelve_target_selected_31k_v1/output/REPORT.md), [scope](experiments/twelve_target_selected_31k_v1/PUBLICATION.md) |
| `experiments/default_ipin_transfer_comparison_v1/` | Implementation, protocol, all public score/metric/exposure tables, comparison plots and manifests; six large CSVs losslessly compressed | [Report](experiments/default_ipin_transfer_comparison_v1/REPORT.md), [scope and decompression](experiments/default_ipin_transfer_comparison_v1/PUBLICATION.md) |
| `experiments/x_pair_test2_v1/` | Previously published implementation, protocol, aggregate results, exposure/qualification evidence and provenance; unchanged | [Interpretation](experiments/x_pair_test2_v1/results/INTERPRETATION.md), [scope](experiments/x_pair_test2_v1/PUBLICATION.md) |
| `benchmark/partner_conditioned_residue_v1/` | Four-recipe implementation, immutable code snapshots, 12 fit histories, selection and C1/C2/C3 results | [Results](benchmark/partner_conditioned_residue_v1/results/RESULTS.md), [scope](benchmark/partner_conditioned_residue_v1/PUBLICATION.md) |
| `manuscript/` | Historical authored draft and supplement, seven figure/CSV pairs, six table/CSV pairs, references, aggregate snapshots, provenance and portable regeneration/conversion scripts | [Package README](manuscript/README.md) |

The manuscript predates the 31k promotion and X-PAIR comparison. Its scientific
text and figures are retained as that historical draft; the README states its
scope. Submission metadata placeholders are still placeholders.

## Material retained locally

This deposit follows the existing separation between source/evidence and
execution assets. Nothing was deleted to prepare it.

- Protected human benchmark candidate identities/truth and per-pair prediction
  arrays remain local. Aggregate metrics, selection histories and bootstrap
  summaries are published. The already public demonstration/transfer panel
  score tables are included.
- Model weights, residue/learned embeddings, large numerical training inputs,
  raw source archives, third-party model distributions, container images and
  installed environments remain local under their existing source/license
  boundaries. Frozen manifests retain source identities, checksums and runtime
  references; this deposit does not claim a new public asset download.
- Generated SPRINT HSPs/raw score files, scratch products, scheduler logs,
  caches and locks remain local. Compact run/completion records are included.
- Six original transfer CSVs remain unchanged locally; their committed `.csv.gz`
  copies decompress byte-for-byte to the frozen originals.
- The unfinished host–pathogen screening implementation and its unpublished
  operational materials are outside this deposit. Existing tracked source
  administration records are unchanged; no completed result is claimed.
- Local knowledge-graph changes include session queries/reflections and
  references to unpublished work. That working state, dated backups and caches
  are excluded. The previously committed graph snapshot is retained.

Study-level `.gitignore` rules admit compact public evidence even inside
`runs/`, while keeping the local products excluded. `.gitattributes` preserves
the bytes of checksum-bound scientific records across platforms. Original
freeze manifests still describe the complete local run, so some of their
entries intentionally refer to assets absent from a public checkout.

## Verify the deposit

The [publication manifest](artifacts/reports/repository_deposit_v1/PUBLICATION_MANIFEST.json)
lists every deposited study/package file with SHA-256 and byte count, summarizes
each directory, and maps compressed tables to their original hashes. It also
pins the existing X-PAIR publication manifest and v3 artifact registry. Living
repository indexes and this inventory are versioned normally, outside the
scientific file manifest.

From a checkout of this deposit, verification needs only Python's standard
library and the committed files:

```bash
python3 scripts/maintenance/verify_git_deposit_v1.py
```

The verifier checks the complete public manifest, both preserved registries,
and all six decompressed table hashes. It does not load model checkpoints or
open protected benchmark data. The [validation record](artifacts/reports/repository_deposit_v1/VALIDATION.json)
describes the publication checks, original-file preservation and manuscript
validation. A full scientific rerun additionally requires the local inputs
and runtime dependencies documented by each study.
