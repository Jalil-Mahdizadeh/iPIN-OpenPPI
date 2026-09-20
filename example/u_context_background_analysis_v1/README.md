# Context versus background U scores

[Results and interpretation](REPORT.md) compare the two unlabeled sampling groups
in the completed twelve-target example. The analysis uses 1,850 pairs per group,
37 matching anchors, and all three frozen model score columns. It performs no
new model inference. U interaction status remains unknown.

The [protocol](PROTOCOL.md) was written before computing this comparison, after
the parent results were available. Effects average matched anchors within target,
then give each of twelve targets equal weight. Whole-target bootstrap intervals
and exact sign-flip reference p-values are exploratory and have explicit
dependence/exchangeability limitations.

| Artifact | Contents |
| --- | --- |
| [summary.csv](summary.csv) | Three models, all-twelve/original-six/additional-six summaries |
| [per_target_scores.csv](per_target_scores.csv) | 36 target/model score-distribution comparisons |
| [per_anchor_scores.csv](per_anchor_scores.csv) | 111 anchor/model comparisons, raw score summaries and rank effects |
| [candidate_annotations.csv](candidate_annotations.csv) | 3,700 U identities and retained source annotations |
| [matching_diagnostics.csv](matching_diagnostics.csv) | Length balance and background context membership for 37 anchors |
| [leave_one_target_out.csv](leave_one_target_out.csv) | 36 omission-sensitivity estimates |
| [score_comparison.pdf](score_comparison.pdf) | Standalone figure, also available as PNG and SVG |
| [ANALYSIS_RUN.json](ANALYSIS_RUN.json) | Input hashes, runtime identity, code/protocol hashes, seed, output table hashes |
| [VALIDATION.json](VALIDATION.json) | Production checks, annotation alignment and parent preservation |
| [INDEPENDENT_VALIDATION.json](INDEPENDENT_VALIDATION.json) | Independent rank-sum, bootstrap, tie, and summary checks |
| [FINAL_MANIFEST.json](FINAL_MANIFEST.json) | Final artifact hashes and independent validation closure |

## Reproduce

Use an isolated copy and a new output directory. Do not overwrite this completed
analysis. Copy `PROTOCOL.md` into the new output first. The parent twelve-target
run, its target manifests, and the retained `sources/reviewed_human.tsv` snapshot
are inputs. That raw snapshot is local and Git-ignored; its required SHA-256 is
`59e4773da73e76674c46649a122f5941136f5c5e372a0e309138e53029db0755`.
The retained candidate annotations make the classification inspectable without
that complete source pool. Input CSVs and all 110 parent public artifacts are
verified against the parent manifest before analysis.

The recorded execution used the accepted data SIF, Python 3.12.3, NumPy 1.26.4,
SciPy 1.15.3, and Matplotlib 3.10.5. Run these entry points in order:

1. `analyze.py --root /project --output OUTPUT`
2. `validate.py --root /project --output OUTPUT`
3. `render_report.py --output OUTPUT`

CPU container invocation pattern, after creating an isolated output location:

```sh
ANALYSIS_OUTPUT="$PWD/example/u_context_background_reproduction"
apptainer exec --cleanenv --containall --no-home \
  --bind "$PWD:/project:ro" \
  --bind "$ANALYSIS_OUTPUT:/project/example/u_context_background_reproduction:rw" \
  --pwd /project --env PYTHONDONTWRITEBYTECODE=1 \
  --env MPLCONFIGDIR=/tmp/ipin-u-context-mpl \
  --env OPENBLAS_NUM_THREADS=1 --env OMP_NUM_THREADS=1 \
  containers/images/ipin-data-arm64_0.1.2.sif \
  python -B example/u_context_background_analysis_v1/analyze.py \
    --root /project --output /project/example/u_context_background_reproduction
```

The output stays within the isolated project tree because the run record stores
project-relative artifact paths. The validator and renderer take that same path.
The renderer can refresh the new report/figures during preparation and refuses
to overwrite them after `FINAL_MANIFEST.json` is present.
