# Twelve-target application of the frozen iPIN catalogue

Current results: [REPORT.md](REPORT.md). This version extends the original six
human target panels with KRAS, CDK2, HIF1A, CTNNB1, TNFRSF1A, and BECN1, selected
for biological breadth and supported partners before inference. It evaluates
**37 P + 3,700 U = 3,737 pairs** using all three frozen iPIN models.

The [example index](../README.md) links all twelve panels and their individual
results. The [six-target comparison](../six_target_comparison_v1/README.md), its
original-TUnA comparator, and original target preparation documents remain
historical records. Existing panel CSVs/manifests and completed results are
preserved. Each target now has `*_three_model_scores.csv` and `RESULTS_v2.md`.

## Inputs and exact predictors

[panel_config.json](panel_config.json) records the six additions, their evidence,
canonical accessions, matching compartments, and deterministic salt.
[build_panels.py](build_panels.py) retrieves reviewed human UniProt records and
IntAct exclusions, checks TRAIN/development overlap, and constructs the new
panels with the original 50 context + 50 background U per positive design.
No model score is consulted. Candidate sequences are deduplicated, length windows
are not widened, and controls are unique within a target. Raw source responses
and response metadata are retained under ignored `sources/`; their hashes and
URLs are in the tracked panel manifests and [PANEL_BUILD.json](PANEL_BUILD.json).
ARAF's declared cytoplasmic context is supported by its UniProt GO annotation;
U context filtering uses UniProt subcellular-location text throughout.

The predictor definitions are exactly those of
[frozen_pair_models_v2](../../docs/models/FROZEN_PAIR_MODELS_v2.md):

| CSV model name | Registry ID | Frozen inputs |
|---|---|---|
| `ipin_baseline` | `lightweight_esm2_150m_linear__linear_lr3e-4` | Windowed ESM-2 150M pooling, TRAIN normalization, three affine heads |
| `ipin_optimized` | `esm2_150m__residual_wide__epoch04_ensemble3` | Same frozen pooling/normalization, three residual MLP heads |
| `tuna_retrained` | `tuna_retrained_ensemble` | Full-context ESM-2 residues, three epoch-4 native TUnA heads and trained GP buffers |

The first two resolve through the preserved v1 bundle; model 3 resolves through
the preserved v2 bundle. Every ensemble uses seeds 20260803, 20260817, 20260831 and
equal FP64 averaging of FP32 member scores. Model 3 averages mean-field-adjusted
logits, with no sigmoid. Normalization and GP covariance are never refitted.
Scoring verifies catalogue identity, frozen source/weights, pair-order symmetry,
TUnA native-forward agreement, and unchanged parameters/buffers.

All 3,344 unique sequences were freshly retrieved and matched to the panel
sequence hashes. Both embedding pipelines were recomputed across all twelve
targets, without loading historical embeddings or endpoint representations.
New representations are reused within this run. TUnA full-context processing
does not truncate long proteins. Raw scores are for within-target ranking.

## Execution

Production computation runs in qualified ARM64 Apptainer images on Arrhenius.
The recorded run used one allocated GH200 GPU. Frozen model images are checked
against these SHA-256 values by the scoring code:

- iPIN: `containers/images/ipin-model-arm64_0.1.0.sif`,
  `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
- TUnA: `benchmark/containers/images/tuna-arm64-v1.sif`,
  `98070c7c2d206d8421817849e11ffce308016dc982938a7d9a3ef3141ab1dec1`.
- Data/tests/reporting: `containers/images/ipin-data-arm64_0.1.2.sif`,
  pinned by the [data-image checksum](../../containers/locks/ipin-data-arm64_0.1.2.sif.sha256).

All scoring outputs are exclusive-create. **These commands describe the recorded
run; they must not overwrite this completed directory.** Reproduction requires
an isolated workspace with the same relative source/input layout, an empty
generated-output area, and access to the preserved local bundles. A public Git
checkout alone does not contain the weights, source snapshots, or SIF images.
Rebuilding panels also requires empty destinations for the six new target panels;
existing tracked panels can instead be verified and reused as fixed inputs.

| Step | Entry point and phase | Runtime |
|---|---|---|
| Panel construction | `build_panels.py --root /project --output OUTPUT` | Data SIF, network enabled |
| Input/metric freeze and fresh sequences | `run_comparison.py prepare --root /project --output OUTPUT` | Model SIF, network enabled |
| Pooled models 1 and 2 | `run_comparison.py ipin --root /project --output OUTPUT` | Model SIF, GPU, offline |
| TUnA-retrained model 3 | `run_comparison.py tuna --root /project --output OUTPUT` | TUnA SIF, GPU, offline |
| Metrics and publication | `run_comparison.py summarize --root /project --output OUTPUT` | Data SIF, CPU |
| Independent audit | `validate_results.py --root /project --output OUTPUT` | TUnA SIF, CPU; includes scikit-learn and h5py |
| Reports and figures | `render_report.py --root /project --output OUTPUT` | Data SIF, CPU |
| Final artifact manifest | `finish_run.py --root /project --output OUTPUT` | TUnA SIF, CPU; after before/after model verification |

Scripts are under `example/twelve_target_comparison_v1/` and the recorded OUTPUT
is `/project/example/twelve_target_comparison_v1`. Mount the repository read-only
and this output directory read-write; construction, summarization, and report
publication also require writable target folders under `example/`.
For GPU phases the recorded invocation pattern is:

```sh
apptainer exec --cleanenv --containall --no-home --nv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/example/twelve_target_comparison_v1:/project/example/twelve_target_comparison_v1:rw" \
  --pwd /project \
  --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONPATH=/opt/tuna/vendor \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  --env TOKENIZERS_PARALLELISM=false --env CUBLAS_WORKSPACE_CONFIG=:4096:8 \
  --env MPLCONFIGDIR=/tmp/twelve-matplotlib \
  benchmark/containers/images/tuna-arm64-v1.sif \
  python -B example/twelve_target_comparison_v1/run_comparison.py tuna \
    --root /project --output /project/example/twelve_target_comparison_v1
```

For `ipin`, use the model image and phase `ipin`. CPU commands omit `--nv`.
Source retrieval needs network access; scoring uses offline local encoders.
GPU execution disables AMP/TF32 and dropout. No training, model selection,
protected-test operator, or ledger reset is performed.

## Metrics, audits, and artifact map

[METRICS.md](METRICS.md) was frozen before scoring and specifies P/U concordance,
AP/MAP, first-positive rank, reciprocal rank/MRR, recovered counts, recall,
known-positive precision, EF, NDCG, and target success. Cutoffs are 5, 10, 20;
curves cover K=1 through 50. All-target, original-six, and additional-six macro
summaries give each target equal weight. All/context/background U and five
exposure/homomer subsets are retained. U is never relabeled as verified negative.

| File | Contents |
|---|---|
| [INPUT_FREEZE.json](INPUT_FREEZE.json) | Panel, sequence, protocol, code, and catalogue identities recorded before scoring |
| [all_twelve_targets_scores.csv](all_twelve_targets_scores.csv) | All pairs, exposure/cohort labels, three ensemble scores, TUnA member scores, and ranks |
| [per_target_metrics.csv](per_target_metrics.csv) | 540 target/model/subset/U-stratum metric rows |
| [macro_metrics.csv](macro_metrics.csv) | 135 equal-target summaries, including MAP, MRR, and success counts |
| [positive_partner_ranks.csv](positive_partner_ranks.csv) | 111 positive/model rank records with tie credit at all cutoffs |
| [matched_positive_metrics.csv](matched_positive_metrics.csv) | 333 positive/model/control-stratum metric rows |
| [retrieval_curves.csv](retrieval_curves.csv) | 1,800 target/model/screening-budget rows |
| [ORIGINAL_SIX_CONSISTENCY.json](ORIGINAL_SIX_CONSISTENCY.json) | Fresh versus historical scores and ranks on the original panels |
| [VALIDATION.json](VALIDATION.json) | Production alignment, completeness, publication, and preservation checks |
| [INDEPENDENT_VALIDATION.json](INDEPENDENT_VALIDATION.json) | Independent numerical, exposure, matching, and artifact checks |
| [UNIT_TESTS.xml](UNIT_TESTS.xml), [METRIC_TESTS.xml](METRIC_TESTS.xml) | Core/example tests and exhaustive synthetic tie fixtures |
| [RUN_MANIFEST.json](RUN_MANIFEST.json) | Runtime identities, execution evidence, and final public output hashes |

`IPIN_RUN.json`, `TUNA_RUN.json`, and `TUNA_ESM_QUALIFICATION.json` retain detailed
numerical qualification. Sequence/pair JSON files support full alignment checks.
Large generated embeddings, HDF5 residue arrays, raw web snapshots, logs, and
scratch state remain local and are excluded from Git. A failed preparation
attempt using an alternate output mount was retained under ignored `scratch/`;
it produced no model scores and preceded the successful input freeze.

The unit suite passed **541 tests with 3 CUDA-only skips**; actual GPU scoring
also passed order symmetry, native TUnA agreement, and frozen-buffer checks.
The separate validator uses scikit-learn for AP/NDCG/reference-label AUROC and
independent combinatorial tie calculations, rather than calling the production
metric function. It also verifies all matched metrics, macro summaries, curves,
row identities, source hashes, control constraints, and TRAIN/development exposure.
The model-preservation verifier documented in the current model card is run
before and after inference. Its logs are retained locally as
`model_verification_before.log` and `model_verification_after.log`; the final
manifest embeds both successful, identical audit results and checks all three
runtime image hashes.
