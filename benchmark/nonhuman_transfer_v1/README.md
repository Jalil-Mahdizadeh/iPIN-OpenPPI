# Non-human transfer of the three frozen iPIN models

This external evaluation tests interactions **within** mouse, fly, worm,
budding yeast, Arabidopsis, and E. coli K-12. Fifty targets per species yield
1,385 P rows and 60,000 U rows. U is unreported in the archived species evidence
universe, not experimentally verified noninteraction. Counts are per target:
100 background U and a disjoint 100 length/degree-matched U, with 2–10 P.

Read [the results](REPORT.md), [protocol](PROTOCOL.md), [input freeze](INPUT_FREEZE.json),
[panel validation](PANEL_VALIDATION.json), and [independent metric validation](INDEPENDENT_VALIDATION.json).
All three versioned predictors are unchanged; original published TUnA is not
part of this study. Human protected test pair/truth files are not used.

## Files

| Files | Purpose |
|---|---|
| `config.json`, `PROTOCOL.md`, `INPUT_FREEZE.json` | Prospective panel, scoring and metric definitions |
| `SOURCES.json`, `SOURCE_PARSING_v2.json`, `*_SOURCE_AUDIT_v2.json` | Archived IntAct source identities and semantic audit |
| `initial_protocol.md`, `initial_strict_parser.py`, `SOURCE_PARSING.json`, `source_feasibility.csv`, `*_SOURCE_AUDIT.json` | Initial metadata-only feasibility pass; see the prescoring adjustment |
| `panels.csv`, `targets.csv`, `proteins.csv` | All selected rows, target coverage and endpoint metadata |
| `selected_sequences.json.gz`, `selected_evidence.json.gz` | Archived reference sequences and original evidence IDs/publications |
| `ipin_scores.csv`, `tuna_scores.csv`, `all_model_scores.csv` | Exact frozen model predictions and exposure-annotated combined table |
| `per_target_metrics.csv`, `macro_metrics.csv`, `positive_ranks.csv` | Three candidate sets and complete known-positive retrieval metrics |
| `metric_intervals.csv`, `paired_differences.csv` | 10,000-draw paired target-bootstrap summaries |
| `exact_*_exposure.csv`, `training_sequence_similarity.csv`, `EXPOSURE_AUDIT.json` | Actual human TRAIN/development exposure and pinned MMseqs2 audit |
| `target_similarity_metrics.csv`, `pair_homology_*.csv`, `analysis_coverage.csv` | Similarity and exact-exposure sensitivity, with denominators |
| `panel_coverage.csv`, `study_coverage.csv`, `degree_control_metrics.csv` | Reuse, source concentration and metadata-only diagnostic control |
| `random_ranking_reference.csv` | Analytical random-order recall@10 reference, added at reporting |
| `IPIN_RUN.json`, `TUNA_RUN.json`, `RUNTIMES.json` | Inference, native qualification, preservation and runtime identities |
| `nonhuman_transfer.png`, `.pdf`, `.svg` | Exportable scientific figure |
| `FINAL_MANIFEST.json` | Checksums of all public study artifacts |

The first feasibility pass required no participant features and MI:0407 only.
Before panel selection or inference, this was revised to allow PSI-MI tag
features and binary two-hybrid evidence. All other construct, taxid and
provenance requirements remained. See
[PRE_SCORING_EVIDENCE_ADJUSTMENT.md](PRE_SCORING_EVIDENCE_ADJUSTMENT.md).
The acquisition-time `SOURCES.json` protocol checksum resolves to
`initial_protocol.md`; the first parser checksum resolves to
`initial_strict_parser.py`. The inference freeze binds the final protocol.

## Execution and reproduction

Commands were run with the repository mounted read-only at `/project` and only
this study directory mounted writable. Production science uses the accepted
data, iPIN, and TUnA SIF images; GPU work uses one GH200. Images and preserved
weights are local execution assets, not included in a fresh Git checkout.

Each phase refuses to replace its outputs. To reproduce, copy the study's `.py`
and `.md` files plus `config.json` into a fresh sibling under `benchmark/` in a
separate working copy, with the unchanged frozen model bundles, runtime images,
human TRAIN/development source files, archived IntAct vocabulary, and pinned
MMseqs2 binary available. Use that sibling as the writable directory in these
commands. The original completed study must be kept intact. The initial strict
feasibility pass is retained history and is not required to reproduce the final
panels.

From the repository root, the completed-run command sequence was:

```bash
# Prefix for data phases (replace the final script/phase as listed below).
apptainer exec --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/nonhuman_transfer_v1:/project/benchmark/nonhuman_transfer_v1:rw" \
  containers/images/ipin-data-arm64_0.1.2.sif \
  python -B /project/benchmark/nonhuman_transfer_v1/acquire.py
```

Data phases, in dependency order:

1. `acquire.py`
2. `parse_sources.py` (final binary/feature semantics; emits `_v2` source files)
3. `build_panels.py`
4. `validate.py panels`
5. `audit_exposure.py` (can run alongside the independent panel validation)
6. `score_models.py freeze` (after panel validation, before inference)

```bash
apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/nonhuman_transfer_v1:/project/benchmark/nonhuman_transfer_v1:rw" \
  containers/images/ipin-model-arm64_0.1.0.sif \
  python -B /project/benchmark/nonhuman_transfer_v1/score_models.py ipin

apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/nonhuman_transfer_v1:/project/benchmark/nonhuman_transfer_v1:rw" \
  benchmark/containers/images/tuna-arm64-v1.sif \
  env PYTHONPATH=/opt/tuna/vendor \
  python -B /project/benchmark/nonhuman_transfer_v1/score_models.py tuna
```

After both scoring phases and the exposure audit, use the data-phase prefix for
`analyze.py`, `validate.py metrics`, `report.py render`, and `report.py finalize`
in that order. Rendering may set `MPLCONFIGDIR=/tmp/ipin-nonhuman-mpl`.

The pooled-model phase reuses the qualified historical example's inference
function with this study's checksum-checked input loader; no historical output
is edited. TUnA computes fresh full-context ESM residues and endpoint features,
checks native full-pair inference on species-spanning fixtures and the longest
pair, and keeps GP covariance and model buffers unchanged. Scores are ranking
values, not calibrated binding probabilities.

Raw ZIPs, parsed source caches, alignments, and large feature arrays remain in
ignored `local/` or ignored inference-cache files. Their identities are bound by
the public source/run records. IntAct data are attributed to EMBL-EBI IntAct /
IMEx and original publications under [CC BY 4.0](https://www.ebi.ac.uk/intact/about).
