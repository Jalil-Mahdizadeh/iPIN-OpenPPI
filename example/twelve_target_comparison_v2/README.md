# Expanded twelve-target application

**Current example comparison: 37 P + 5,550 U, four predictors, five candidate sets.** Start with the [report](REPORT.md), [selection rules](SELECTION.md), and [metric definitions](METRICS.md). Original TUnA is an external comparator; TUnA-retrained remains the third frozen iPIN model.

| Target | P | U | Details |
| --- | --- | --- | --- |
| ERN1 | 4 | 600 | [Results](../ERN1/RESULTS_v3.md) |
| TP53 | 3 | 450 | [Results](../TP53/RESULTS_v3.md) |
| EGFR | 3 | 450 | [Results](../EGFR/RESULTS_v3.md) |
| BCL2 | 3 | 450 | [Results](../BCL2/RESULTS_v3.md) |
| KEAP1 | 3 | 450 | [Results](../KEAP1/RESULTS_v3.md) |
| BRCA1 | 3 | 450 | [Results](../BRCA1/RESULTS_v3.md) |
| KRAS | 3 | 450 | [Results](../KRAS/RESULTS_v3.md) |
| CDK2 | 3 | 450 | [Results](../CDK2/RESULTS_v3.md) |
| HIF1A | 3 | 450 | [Results](../HIF1A/RESULTS_v3.md) |
| CTNNB1 | 3 | 450 | [Results](../CTNNB1/RESULTS_v3.md) |
| TNFRSF1A | 3 | 450 | [Results](../TNFRSF1A/RESULTS_v3.md) |
| BECN1 | 3 | 450 | [Results](../BECN1/RESULTS_v3.md) |

## Reproduction

Run scientific Python inside the pinned data/model/TUnA Apptainer images listed in `RUN_MANIFEST.json`. GPU phases require one allocated GPU. Mount the project read-only at `/project`, with only this new output directory writable at the same path. All scientific outputs use exclusive creation; do not rerun phases over a completed run. Use a new version directory and retain exact source/implementation hashes.

1. `fetch_sources.py` retrieves annotation sources.
2. `build_panels.py --root /project --allow-secondary-overlap` selects new U without scores.
3. `run_comparison.py prepare --root /project --output /project/example/twelve_target_comparison_v2` freezes panels, fresh sequences, metrics and scoring code.
4. Run the same driver with phase `ipin` in the iPIN model SIF, then `tuna` in the TUnA SIF. Both recompute embeddings.
5. Run `summarize`, `validate_results.py`, `render_report.py`, and `finish_run.py` in the TUnA SIF.

Selection needs network access. GPU runs use `--nv`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and `PYTHONDONTWRITEBYTECODE=1`. Use `PYTHONPATH=/project/src` for pooled iPIN and `/opt/tuna/vendor` for TUnA. Fresh HDF5/NumPy embeddings, model weights and raw sources stay local and are not committed.

Historical records: [twelve-target v1](../twelve_target_comparison_v1/REPORT.md), [six-target four-model run](../six_target_comparison_v1/REPORT.md), and [context/background score analysis](../u_context_background_analysis_v1/REPORT.md).
