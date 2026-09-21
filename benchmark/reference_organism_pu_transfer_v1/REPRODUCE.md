# Reproduce the P/U correction

Use a fresh sibling directory containing these Python files, `config.json`,
`PROTOCOL.md`, `README.md` and this file. Keep the original published-positive
study, pinned source cache/archives, model bundles and accepted images available.
Scripts reject overwriting scientific outputs. Adjust the writable bind and
script paths below to that sibling; repository root remains mounted read-only.

Data phases:

```bash
apptainer exec --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_pu_transfer_v1:/project/benchmark/reference_organism_pu_transfer_v1:rw" \
  containers/images/ipin-data-arm64_0.1.2.sif \
  python -B /project/benchmark/reference_organism_pu_transfer_v1/build_panels.py
```

With the same data-image prefix run, in order:

1. `build_panels.py`
2. `validate_panels.py`
3. `audit_exposure.py`
4. `analyze.py selftest`
5. `score_models.py freeze`

Run the unchanged models sequentially on an available GPU:

```bash
apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_pu_transfer_v1:/project/benchmark/reference_organism_pu_transfer_v1:rw" \
  containers/images/ipin-model-arm64_0.1.0.sif \
  python -B /project/benchmark/reference_organism_pu_transfer_v1/score_models.py ipin

apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_pu_transfer_v1:/project/benchmark/reference_organism_pu_transfer_v1:rw" \
  benchmark/containers/images/tuna-arm64-v1.sif \
  env PYTHONPATH=/opt/tuna/vendor \
  python -B /project/benchmark/reference_organism_pu_transfer_v1/score_models.py tuna
```

Finish with the data-image prefix:

1. `analyze.py analyze`
2. `validate_results.py`
3. `finalize.py`

The primary concordance averages per-P comparisons against that P's assigned
100 U. Equal-target summaries are supplied separately. The source set and
P labels are immutable. The secondary-assay outcomes are not used as U labels.
