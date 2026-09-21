# Reproduce the completed reference-organism evaluation

Use a separate working copy with the unchanged pinned source archives, model
bundles, human TRAIN/development inputs, accepted images and MMseqs2 binary.
Copy this study's Python files, `config.json`, `PROTOCOL.md`,
`EVALUATION_PROTOCOL.md`, `README.md`, and `REPRODUCE.md` into a fresh sibling
under `benchmark/`. Scripts refuse to replace scientific outputs.
Use that sibling as the writable study directory in the commands below.

Data phases use the accepted data image:

```bash
apptainer exec --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_transfer_v1:/project/benchmark/reference_organism_transfer_v1:rw" \
  containers/images/ipin-data-arm64_0.1.2.sif \
  python -B /project/benchmark/reference_organism_transfer_v1/prepare.py
```

Run these phases in order using the same data-image prefix:

1. `prepare.py`
2. `validate_preparation.py`
3. `acquire_comparison.py` (verify downloaded source hashes against this run)
4. `build_comparison.py`
5. `audit_exposure.py`
6. `analyze.py selftest`
7. `score_models.py freeze`

`VALIDATION.json` is the separate preparation export audit bound into the
inference freeze. `validate_preparation.py` reproduces that audit. Use
`--verify-only` to check an existing preparation without replacing its record.
The result validation later independently verifies worksheet mapping and the
complete evaluated outcome set.

Run inference sequentially on one available GPU:

```bash
apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_transfer_v1:/project/benchmark/reference_organism_transfer_v1:rw" \
  containers/images/ipin-model-arm64_0.1.0.sif \
  python -B /project/benchmark/reference_organism_transfer_v1/score_models.py ipin

apptainer exec --nv --cleanenv \
  --bind "$PWD:/project:ro" \
  --bind "$PWD/benchmark/reference_organism_transfer_v1:/project/benchmark/reference_organism_transfer_v1:rw" \
  benchmark/containers/images/tuna-arm64-v1.sif \
  env PYTHONPATH=/opt/tuna/vendor \
  python -B /project/benchmark/reference_organism_transfer_v1/score_models.py tuna
```

Finish with the data-image prefix:

1. `analyze.py analyze`
2. `validate_results.py`
3. `finalize.py`

The source-preparation protocol and configuration remain historical records of
that phase. `EVALUATION_PROTOCOL.md` and `INPUT_FREEZE.json` define the completed
assay-confirmation evaluation. Input sequence filtering, source identities,
model parameters, normalization, model seeds and covariance remain fixed.
