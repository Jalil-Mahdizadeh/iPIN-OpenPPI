# Six-target fresh-embedding comparison

This run applies four unchanged predictors to the six previously curated input
panels: frozen iPIN baseline, frozen optimized iPIN, original Bernett TUnA, and
the previously selected epoch-4 three-seed PU-TUnA ensemble.

## Fresh-run policy

- All 1,829 unique canonical human protein sequences were freshly retrieved from
  UniProt and checked against the input manifests. No endpoint was removed.
- Every iPIN ESM embedding was recomputed. The frozen training normalizer and
  head weights were retained; normalization was not refitted to these panels.
- Every TUnA full-context ESM residue embedding and every model-specific endpoint
  representation was recomputed. No pre-existing pooled, residue, or endpoint
  feature file was loaded. Newly computed representations are shared across
  pairs within this run, without repeated encoding of the same sequence.
- Frozen GP covariance matrices are part of the TUnA predictors and remain
  unchanged. They were not estimated from the example panels.
- The two pipelines use the same sequences and frozen ESM-2 150M checkpoint,
  but retain their distinct preprocessing: windowed residue-mean pooling for
  iPIN; full-context residue representations for TUnA.
- Original CSVs, panel manifests, old example outputs, model weights, and the
  existing repository graph remain unchanged. All new files are under example/.

## Execution

`run_comparison.py` has four separate phases, all requiring `--root ROOT` and
`--output OUTPUT`. Outputs are exclusive-create and never silently overwritten.

| Phase | Runtime | Work |
|---|---|---|
| `prepare` | Existing iPIN model SIF, network enabled | Fresh UniProt snapshot and input freeze |
| `ipin` | Existing iPIN model SIF, one GPU, offline | Fresh windowed embeddings and both ensembles |
| `tuna` | Existing TUnA SIF, one GPU, offline | Fresh residue embeddings, all four endpoint encoders, native-forward qualification, original and ensemble scores |
| `summarize` | Python with NumPy | Row-aligned comparison, ranks, metrics and publication of each target's scored CSV |

GPU phases require `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
`TOKENIZERS_PARALLELISM=false`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and
`PYTHONDONTWRITEBYTECODE=1`. Both use `apptainer exec --cleanenv --containall
--no-home --nv`, mount the repository read-only as `/project`, mount this output
directory read-write as `/output`, and run, for example:

```bash
python -B example/six_target_comparison_v1/run_comparison.py ipin \
    --root /project --output /output
```

Pinned image digests are checked in the scoring code and recorded in the run
JSON files. The iPIN image is `containers/images/ipin-model-arm64_0.1.0.sif`;
the TUnA image is `benchmark/containers/images/tuna-arm64-v1.sif`.
Each phase has its own log. Repeating the analysis requires a fresh output
location and fresh publication filenames, because existing outputs are protected.

## Results and checks

The concise interpretation is in `REPORT.md`. Per-target scored CSVs are present
both here and in the respective target folders. `all_six_targets_scores.csv`
contains every pair, all four model scores, the three TUnA member scores, and
within-target midranks. `positive_partner_ranks.csv` contains the 19 positives
for each model, including tie intervals and comparisons with their own 100 U
controls. `per_target_metrics.csv` includes context/background strata and
development-exposure/homomer sensitivity analyses; `macro_metrics.csv` gives
equal-target averages.

Concordance is the fraction of P-versus-U comparisons won by P, with half credit
for exact ties. It is not discrimination against experimentally verified
negatives. Historical benchmark sampling weights are not reused. Top-10 recovery
uses fractional credit for ties crossing the cutoff, rather than an arbitrary
accession-based tie break. Sensitivity analyses remove the specified positives
but retain the same U candidate lists.

`test_comparison.py` tests input identity and the comparison metrics. Numerical
checks include iPIN/TUnA pair-order symmetry, fresh ESM implementation agreement,
TUnA agreement with native unaccelerated full-length pairwise inference, unchanged
TUnA parameters and buffers, exact three-seed ensemble arithmetic, complete
finite score coverage, and hashes of pre-existing files. Run metadata and
`VALIDATION.json` retain the checks. No training, calibration, checkpoint
selection, or protected-test evaluation is performed.

`validate_results.py` independently checks all 216 metric cells and 76 positive
rank rows using sorted-score calculations, verifies newly generated embedding
artifacts, and rechecks frozen weights and original files. Its result is
`INDEPENDENT_VALIDATION.json`. `audit_original_exposure.py` separately compares
all panel pairs with the authors' documented original-TUnA training/validation
records, by accession and exact sequence identity, in both pair orientations.
This audit does not use model scores or old embeddings.

Graphify was used to locate existing frozen scoring components. An AST-only
index of the new scripts is contained in this folder's `graphify-out/`; the
existing repository index was not updated in place.
