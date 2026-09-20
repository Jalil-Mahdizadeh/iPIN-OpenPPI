# Test policy

- `unit/` contains synthetic parser, evidence-semantics, safety, manifest,
  checksum, split, training, scoring, and publication tests. Fixtures are created
  within the tests and their temporary directories.
- `test_model_optimization_v1.py` covers the optimization models and objective.
- [Example comparison tests](../example/six_target_comparison_v1/test_comparison.py)
  live with the application and are collected separately from `tests/`.
- Published-method numerical and container qualifications are documented in
  each [benchmark directory](../benchmark/README.md).

Tests importing scientific dependencies run inside an accepted SIF. The core
data image, `containers/images/ipin-data-arm64_0.1.2.sif`, includes the ingestion
and model-test dependencies. The model image alone does not include every data
dependency. Set `PYTHONPATH=/project/src` when the repository is mounted at
`/project`, disable bytecode and external pytest plugin autoload, and use an
isolated writable temporary directory. MMseqs tests also require a writable
mount at `/project/artifacts/tmp`.

Inside that environment, the synthetic suites are:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -B -m pytest -q -p no:cacheprovider tests
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -B -m pytest -q -p no:cacheprovider example/six_target_comparison_v1/test_comparison.py
```

CPU execution skips CUDA-only parity tests. These tests do not authorize
training, protected-truth access, or repetition of a completed evaluation.
