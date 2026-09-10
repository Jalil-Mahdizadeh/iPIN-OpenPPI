# Model-governance utilities

This directory contains the governed model-runtime entry points. Stage 1 model
acquisition, frozen embedding extraction, public-only training, and training
validation are closed under `DEC-0031`. Development execution is separately
bounded by `DEC-0032`; protected evaluation remains prohibited.

- `audit_model_governance_and_baseline_training_protocol_v1.py` verifies the
  binding protocol configuration, immutable parent hashes, and 24 frozen
  scientific and custody rules.
- `validate_model_governance_and_baseline_training_protocol_v1.py` independently
  verifies the production audit and reconstructs 20 consequential rule groups
  without importing production protocol code or a model framework.

The development-only commands are:

- `audit_development_prerelease_v1.py`, which validates the release boundary,
  exact scorer census, model algebra, metrics, bootstrap, and policy fixtures
  without resolving any private key;
- `release_development_for_evaluation_v1.py`, which is disabled until a later
  committed activation gate records passing production and independent
  pre-release reports, and then resolves only the development key;
- `run_development_scoring_v1.py`, which scores the nine released-development
  cells with nine controls, 30 selected checkpoints, and ten frozen ensembles;
  and
- `evaluate_development_v1.py`, which applies the frozen metrics, diagnostics,
  model selection, complexity gates, and kill rules without training.

Run model-bearing commands inside the checksum-pinned ARM64 model SIF. Private
development identities and score rows stay below `.private/`; public outputs
contain aggregates and hashes only. None of these commands can authorize or
open protected candidates, protected truth, or either protected private key.

## Within-anchor partner-specificity diagnostic (DEC-0046)

`run_within_anchor_partner_specificity_v1.py` implements the prospectively
specified internal study in
`docs/protocols/WITHIN_ANCHOR_PARTNER_SPECIFICITY_v1.md`.
It uses only released public-training P/U rows and frozen raw 150M embeddings.
The protected test stays sealed. All outputs occupy a new namespace.

Phases, in order: `prepare`, `freeze`, `train`, `score`, `evaluate`, `validate`.
Run the complete unit suite in the data SIF before `freeze`; its passing JUnit
report is included in the execution freeze. Model fitting/scoring uses the
qualified model SIF and one GPU. For example, from the project root:

```bash
apptainer exec --nv --cleanenv --no-home \
  --bind "$PWD:/work" --pwd /work \
  containers/images/ipin-model-arm64_0.1.0.sif \
  env PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  CUBLAS_WORKSPACE_CONFIG=:4096:8 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 \
  python scripts/model/run_within_anchor_partner_specificity_v1.py train
```

The entry point refuses to overwrite closed artifacts. `--resume-preparation`
is only for the documented pre-census schema-label correction: original
preregistration hashes must match and no generated arrays may exist. It does
not resume training or allow outcome-driven retries. Do not delete existing
evidence to force an experiment rerun.

Compact protocol, census, execution freeze, fit/score registries and results
are under `artifacts/results/within_anchor_partner_specificity_v1/`.
Reference validation and unit-test evidence are under the corresponding
`artifacts/validation/` directory. Larger hash-bound arrays and checkpoints are
local generated artifacts under `artifacts/runs/within_anchor_partner_specificity_v1/`
and intentionally follow the repository's existing Git-ignore policy.

The reference validator has independent NumPy/SciPy head algebra and direct
P-by-U point/selected-bootstrap calculations. It is a same-author numerical
cross-check, not external scientific review or an independent replication.

`audit_within_anchor_supporting_metrics_v1.py` is an additional post-readout
arithmetic audit of the already frozen propensity sensitivity, panel recalls,
all quartet bootstrap replicates, supporting intervals and matched fit orders.
It was written after the readout and does not change any estimand or gate.
