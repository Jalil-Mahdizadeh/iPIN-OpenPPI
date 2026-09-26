# Test policy

- `unit/` contains synthetic parser, evidence-semantics, safety, manifest,
  checksum, split, training, scoring, and publication tests. Fixtures are created
  within the tests and their temporary directories.
- `test_model_optimization_v1.py` covers the optimization models and objective.
- `test_frozen_pair_models_v3.py` checks primary/default identity, preservation
  of historical model definitions and aliases, exact seed/checkpoint membership,
  saved-covariance semantics, bounded claims and refusal to overwrite a release.
  Run it with the v1/v2 custody tests in the pinned TUnA image. The v3 freeze
  additionally qualifies actual states using synthetic residues on CPU.
- Example tests live with the applications and are collected separately from
  `tests/`: [historical comparison tests](../example/six_target_comparison_v1/test_comparison.py)
  and [twelve-target metric tests](../example/twelve_target_comparison_v1/test_metrics.py).
  The latter check exhaustive tie orderings, cutoff recovery, first-positive
  rank/MRR, and invalid inputs. The [independent result validator](../example/twelve_target_comparison_v1/validate_results.py)
  checks actual scores/metrics and exposure in the TUnA SIF, which includes h5py.
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
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -B -m pytest -q -p no:cacheprovider example/twelve_target_comparison_v1/test_metrics.py
```

CPU execution skips CUDA-only parity tests. These tests do not authorize
training, protected-truth access, or repetition of a completed evaluation.
